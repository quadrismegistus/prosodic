from .imports import *

SYLL_SEP = "."


class SyllableList(EntityList):
    pass


class WordTypeList(EntityList):
    pass


@total_ordering
class WordFormList(EntityList):
    def __repr__(self):
        return " ".join(wf.token_stress for wf in self.data)

    @cached_property
    def slots(self):
        return [syll for wordform in self.data for syll in wordform.children]

    # @cached_property
    # def df(self):
    #     l=[
    #         {
    #             k:('.'.join(v) if type(v)==list else v)
    #             for k,v in px.attrs.items()
    #         }
    #         for px in self.data
    #         if px is not None
    #     ]
    #     return setindex(pd.DataFrame(l))

    @cached_property
    def num_stressed_sylls(self):
        return sum(
            int(syll.is_stressed)
            for wordform in self.data
            for syll in wordform.children
        )

    @cached_property
    def num_sylls(self):
        return sum(1 for wordform in self.data for syll in wordform.children)

    @cached_property
    def first_syll(self):
        for wordform in self.data:
            for syll in wordform.children:
                return syll

    @cached_property
    def sort_key(self):
        sylls_is_odd = int(bool(self.num_sylls % 2))
        first_syll_stressed = (
            2 if self.first_syll is None else int(self.first_syll.is_stressed)
        )
        return (
            sylls_is_odd,
            self.num_sylls,
            self.num_stressed_sylls,
            first_syll_stressed,
        )

    def __lt__(self, other):
        return self.sort_key < other.sort_key

    def __eq__(self, other):
        # return self.sort_key==other.sort_key
        return self is other


# @cache
@profile
def Word(token, lang=DEFAULT_LANG):
    if lang not in LANGS:
        raise Exception(f"Language {lang} not recognized")
    lang_obj = LANGS[lang]()
    return lang_obj.get(token)


class WordToken(Entity):
    child_type = "WordType"
    list_type = WordTypeList

    prefix = "wordtoken"

    @profile
    def __init__(self, txt, lang=DEFAULT_LANG, parent=None, children=[], **kwargs):
        if txt.startswith("\n"):
            txt = txt[1:]
        self.lang = lang
        if not children:
            children = WordTypeList([Word(txt, lang=lang)])
        self.word = children[0]
        super().__init__(children=children, parent=parent, txt=txt, **kwargs)

    def to_json(self):
        return super().to_json(lang=self.lang)


class WordType(Entity):
    child_type: str = "WordForm"
    list_type = list

    prefix = "word"

    @profile
    def __init__(self, txt: str, children: list, parent=None, **kwargs):
        super().__init__(children=children, parent=parent, txt=txt, **kwargs)

    def to_json(self):
        return super().to_json(lang=self.lang)

    @property
    def wtoken(self):
        return WordToken(self.txt, lang=self.lang, children=self.children)

    @property
    def forms(self):
        return self.children

    @property
    def form(self):
        return self.children[0] if self.children else None

    @property
    def num_forms(self):
        return len(self.children)

    @property
    def is_punc(self):
        return True if not any([x.isalpha() for x in self.txt]) else None

    @cached_property
    def num_sylls(self):
        x = np.median([form.num_sylls for form in self.forms])
        return None if np.isnan(x) else int(round(x))

    @cached_property
    def num_stressed_sylls(self):
        x = np.median([form.num_stressed_sylls for form in self.forms])
        return None if np.isnan(x) else int(round(x))

    @cached_property
    def attrs(self):
        return {
            **super().attrs,
            "num_forms": self.num_forms,
            # 'num_sylls':self.num_sylls,
            # 'num_stressed_sylls':self.num_stressed_sylls,
            "is_punc": self.is_punc,
        }

    def rime_distance(self, word):
        return self.children[0].rime_distance(word.children[0])


class WordForm(Entity):
    prefix = "wordform"
    child_type: str = "Syllable"
    list_type = SyllableList

    @profile
    def __init__(
        self, txt: str, sylls_ipa=[], sylls_text=[], children=[], syll_sep="."
    ):
        from .syllables import Syllable

        sylls_ipa = sylls_ipa.split(syll_sep) if type(sylls_ipa) == str else sylls_ipa
        sylls_text = (
            sylls_text.split(syll_sep)
            if type(sylls_text) == str
            else (sylls_text if sylls_text else sylls_ipa)
        )
        if not children:
            if sylls_text and sylls_ipa:
                children = [
                    Syllable(
                        syll_str,
                        ipa=syll_ipa,
                    )
                    for syll_str, syll_ipa in zip(sylls_text, sylls_ipa)
                ]
        super().__init__(
            # sylls_ipa=sylls_ipa,
            # sylls_text=sylls_text,
            txt=txt,
            children=children,
        )
        self.sylls_ipa = sylls_ipa
        self.sylls_text = sylls_text

    def to_json(self):
        return super().to_json(
            sylls_ipa=self.sylls_ipa,
            sylls_text=self.sylls_text,
        )

    @property
    def wtoken(self):
        if self.parent:
            return self.parent.wtoken
        return WordToken(self.txt, lang=self.parent.lang, children=self.parent.children)

    @cached_property
    def syllables(self):
        return self.children

    @cached_property
    def token_stress(self):
        return SYLL_SEP.join(
            syll.txt.upper() if syll.is_stressed else syll.txt.lower()
            for syll in self.children
        )

    @cached_property
    def is_functionword(self):
        return len(self.children) == 1 and not self.children[0].is_stressed

    @cached_property
    def num_sylls(self):
        return len(self.children)

    @cached_property
    def num_stressed_sylls(self):
        return len([syll for syll in self.children if syll.is_stressed])

    @cached_property
    def key(self):
        return hashstr(
            self._txt,
            self.sylls_ipa,
            self.sylls_text,
        )

    def to_hash(self):
        return hashstr(self.key)

    @cached_property
    def rime(self):
        from .syllables import PhonemeList

        sylls = []
        for syll in reversed(self.children):
            sylls.insert(0, syll)
            if syll.stress == "P":
                break
        if not sylls:
            return
        o = sylls[0].rime.data + [phon for syll in sylls[1:] for phon in syll.children]
        return PhonemeList(o)

    @cache
    def rime_distance(self, wordform):
        from scipy.spatial.distance import euclidean

        if self.txt == wordform.txt:
            return np.nan
        # return self.syllables[-1].rime_distance(wordform.syllables[-1])

        df1 = self.rime.df
        df2 = wordform.rime.df

        if list(df1.reset_index().phon_txt) == list(df2.reset_index().phon_txt):
            return 0

        s1 = df1.mean(numeric_only=True)
        s2 = df2.mean(numeric_only=True)
        keys = [
            k
            for k in set(s1.index) & set(s2.index)
            if k.startswith("phon_")
            and not k.endswith("_num")
            and not k.startswith("phon_is_")
        ]
        s1x = s1.loc[keys]
        s2x = s2.loc[keys]
        dist = euclidean(s1x, s2x)
        return dist
