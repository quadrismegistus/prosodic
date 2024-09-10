from typing import List, Optional, Union
from ..imports import *
from ..langs import Language
from ..ents import Entity

SYLL_SEP = "."


class WordToken(Entity):
    """Represents a word token in text."""

    prefix = "wordtoken"

    # @#log.debug
    def __init__(
        self,
        txt: str = None,
        lang: str = DEFAULT_LANG,
        parent: Optional["Entity"] = None,
        children: List["WordType"] = [],
        text=None,
        num=None,
        **kwargs,
    ):
        """
        Initialize a WordToken object.

        Args:
            txt (str): The text of the word token.
            lang (str, optional): The language code. Defaults to DEFAULT_LANG.
            parent (Entity, optional): The parent entity. Defaults to None.
            children (List[WordType], optional): List of child WordType objects. Defaults to [].
            **kwargs: Additional keyword arguments.
        """
        # if txt.startswith("\n"):
        # txt = txt[1:]
        if not children:
            wordtype = Word(txt.strip(), lang=lang)
            children = WordTypeList([wordtype], parent=self, text=text)
            # renum?

        self.word = children[0] if children else None
        # self.sent_num = kwargs.pop('sent_num',None)
        # self.sentpart_num = kwargs.pop('sentpart_num',None)
        super().__init__(
            children=children,
            parent=parent,
            txt=txt,
            lang=lang,
            text=text,
            num=num,
            **kwargs,
        )
        self._preterm = None
        #log.debug(f"Initialized word with txt {[self.txt]}")

    @property
    def preterm(self):
        return self._preterm
    
    @cached_property
    def key(self):
        return f'{self.text.key+"." if self.text else ""}{self.nice_type_name}{self.num}'

    def to_dict(
        self,
        incl_num=True,
        incl_children=False,
        incl_txt=True,
        incl_attrs=True,
        **kwargs,
    ) -> dict:
        """
        Convert the WordToken to a JSON-serializable dictionary.

        Returns:
            dict: A dictionary representation of the WordToken.
        """
        return super().to_dict(
            incl_num=incl_num,
            incl_children=incl_children,
            incl_txt=incl_txt,
            incl_attrs=incl_attrs,
            **kwargs,
        )
    
    @property
    def has_wordform(self):
        return bool(self.wordtype and self.wordtype.children and len(self.wordtype.children))


    @property
    def attrs(self):
        return {**super().attrs, **({} if not self.preterm else self.preterm.attrs)}

    @property
    def wordtype(self):
        return self.children[0] if self.children else None

    @property
    def is_punc(self):
        return self.wordtype.is_punc

    def force_unstress(self):
        wordtype = Word(self._txt, lang=self.lang, force_unstress=True)
        self.children = [wordtype]
        wordtype.parent = self

    def force_ambig_stress(self):
        wordtype = Word(self._txt, lang=self.lang, force_ambig_stress=True)
        self.children = [wordtype]
        wordtype.parent = self


class WordType(Entity):
    """Represents a word type (lexeme)."""

    child_type: str = "WordForm"
    prefix = "wordtype"

    @profile
    def __init__(
        self,
        txt: str = None,
        children: List["WordForm"] = None,
        parent: Optional["Entity"] = None,
        lang: str = DEFAULT_LANG,
        **kwargs,
    ):
        """
        Initialize a WordType object.

        Args:
            txt (str): The text of the word type.
            children (List[WordForm]): List of child WordForm objects.
            parent (Entity, optional): The parent entity. Defaults to None.
            **kwargs: Additional keyword arguments.
        """
        #log.debug([txt, children, parent, lang])
        super().__init__(txt=txt, lang=lang, children=children, parent=parent, **kwargs)

    def to_dict(self) -> dict:
        """
        Convert the WordType to a JSON-serializable dictionary.

        Returns:
            dict: A dictionary representation of the WordType.
        """
        return super().to_dict(incl_attrs=True, incl_txt=True)

    def unstress(self) -> None:
        if self.num_forms > 1:
            wf = min(self.children, key=lambda wf: wf.num_stressed_sylls)
            self.children = [wf]
            self.clear_cached_properties()

    @property
    def wtoken(self) -> "WordToken":
        return WordToken(self.txt, lang=self.lang, children=self.children)

    @property
    def forms(self) -> List["WordForm"]:
        return self.children

    @property
    def form(self) -> Optional["WordForm"]:
        return self.children[0] if self.children else None

    @property
    def num_forms(self) -> int:
        return len(self.children)

    @property
    def is_punc(self) -> Optional[bool]:
        return True if token_is_punc(self.txt) else None

    @property
    def num_sylls(self) -> Optional[int]:
        x = np.median([form.num_sylls for form in self.forms])
        return None if np.isnan(x) else int(round(x))

    @property
    def num_stressed_sylls(self) -> Optional[int]:
        x = np.median([form.num_stressed_sylls for form in self.forms])
        return None if np.isnan(x) else int(round(x))

    @property
    def attrs(self) -> dict:
        return {
            **super().attrs,
            "num_forms": self.num_forms,
            # 'num_sylls':self.num_sylls,
            # 'num_stressed_sylls':self.num_stressed_sylls,
            "is_punc": self.is_punc,
        }

    def rime_distance(self, word: "WordType") -> float:
        """
        Calculate the rime distance between this word and another.

        Args:
            word (WordType): The word to compare with.

        Returns:
            float: The rime distance between the two words.
        """
        return self.children[0].rime_distance(word.children[0])


class WordForm(Entity):
    """Represents a specific form of a word."""

    prefix = "wordform"
    child_type: str = "Syllable"

    @profile
    def __init__(
        self,
        txt: str = None,
        sylls_ipa: Union[str, List[str]] = [],
        sylls_text: Union[str, List[str]] = [],
        children: List["Syllable"] = [],
        syll_sep: str = ".",
        num=None,
        **kwargs,
    ):
        """
        Initialize a WordForm object.

        Args:
            txt (str): The text of the word form.
            sylls_ipa (Union[str, List[str]], optional): IPA representation of syllables. Defaults to [].
            sylls_text (Union[str, List[str]], optional): Text representation of syllables. Defaults to [].
            children (List[Syllable], optional): List of child Syllable objects. Defaults to [].
            syll_sep (str, optional): Syllable separator. Defaults to ".".
        """
        from .syllables import Syllable, SyllableList
        from ..langs import syll_ipa_str_is_stressed

        if not children:
            if sylls_text and sylls_ipa:
                sylls_ipa = (
                    sylls_ipa.split(syll_sep) if type(sylls_ipa) == str else sylls_ipa
                )
                sylls_text = (
                    sylls_text.split(syll_sep)
                    if type(sylls_text) == str
                    else (sylls_text if sylls_text else sylls_ipa)
                )
                children = [
                    Syllable(
                        syll_str,
                        ipa=syll_ipa,
                    )
                    for syll_str, syll_ipa in zip(sylls_text, sylls_ipa)
                ]
        else:
            sylls_ipa = [syll.ipa for syll in children]
            sylls_text = [syll.txt for syll in children]

        super().__init__(
            txt=txt,
            num=num,
            # txt_stress=sylls_text_str,
            # ipa=sylls_ipa_str,
            # stress=stress_str,
            # weight=weight_str,
            children=children,
            ipa=".".join(sylls_ipa),
            stress="".join(syll.stress for syll in children),
            weight="".join(syll.weight for syll in children),
            sylls_ipa=[syll.ipa for syll in children],
            sylls_text=[syll.txt for syll in children],
            stress_text=".".join(
                [
                    (
                        syll_text.upper()
                        if syll_ipa_str_is_stressed(syll_ipa)
                        else syll_text.lower()
                    )
                    for syll_text, syll_ipa in zip(sylls_text, sylls_ipa)
                ]
            ),
        )

    # def to_dict(self) -> dict:
    #     """
    #     Convert the WordForm to a JSON-serializable dictionary.

    #     Returns:
    #         dict: A dictionary representation of the WordForm.
    #     """
    #     return super().to_dict(
    #         # sylls_ipa=self.sylls_ipa,
    #         # sylls_text=self.sylls_text,
    #         # no_children=True
    #     )

    # @property
    # def wtoken(self) -> 'WordToken':
    #     if self.parent:
    #         return self.parent.wtoken
    #     return WordToken(self.txt, lang=self.parent.lang, children=self.parent.children)

    @property
    def syllables(self) -> List["Syllable"]:
        return self.children

    @property
    def token_stress(self) -> str:
        return SYLL_SEP.join(
            syll.txt.upper() if syll.is_stressed else syll.txt.lower()
            for syll in self.children
        )

    @property
    def is_functionword(self) -> bool:
        return len(self.children) == 1 and not self.children[0].is_stressed

    @property
    def num_sylls(self) -> int:
        return len(self.children)

    @property
    def num_stressed_sylls(self) -> int:
        return len([syll for syll in self.children if syll.is_stressed])

    @property
    def is_stressed(self):
        return self.num_stressed_sylls > 0


    def to_hash(self) -> str:
        return hashstr(self.key)

    @property
    def rime(self) -> Optional["PhonemeList"]:
        """
        Get the rime of the word form.

        Returns:
            PhonemeList: The rime of the word form, or None if no rime can be determined.
        """
        from .phonemes import PhonemeList

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
    def rime_distance(self, wordform: "WordForm") -> float:
        """
        Calculate the rime distance between this word form and another.

        Args:
            wordform (WordForm): The word form to compare with.

        Returns:
            float: The rime distance between the two word forms.
        """
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


class WordTypeList(EntityList):
    """A list of WordType objects."""

    pass


@total_ordering
class WordFormList(EntityList):
    """A list of WordForm objects with additional properties and comparison methods."""

    # def __repr__(self) -> str:
    #     """
    #     Get a string representation of the WordFormList.

    #     Returns:
    #         str: A string representation of the WordFormList.
    #     """
    #     return " ".join(wf.token_stress for wf in self.data)

    @property
    def sents(self):
        return unique_list(wtok.sent for wtok in self)

    @property
    def slots(self) -> List["Syllable"]:
        return self.wordforms.sylls.data

    @property
    def num_stressed_sylls(self) -> int:
        return sum(
            int(syll.is_stressed)
            for wordform in self.data
            for syll in wordform.children
        )

    @property
    def num_sylls(self) -> int:
        return sum(1 for wordform in self.data for syll in wordform.children)

    @property
    def first_syll(self) -> Optional["Syllable"]:
        for wordform in self.data:
            for syll in wordform.children:
                return syll

    @property
    def sort_key(self) -> tuple:
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

    def __lt__(self, other: "WordFormList") -> bool:
        """
        Compare this WordFormList with another for ordering.

        Args:
            other (WordFormList): The WordFormList to compare with.

        Returns:
            bool: True if this WordFormList is less than the other, False otherwise.
        """
        return self.sort_key < other.sort_key

    def __eq__(self, other: object) -> bool:
        """
        Check if this WordFormList is equal to another object.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """
        # return self.sort_key==other.sort_key
        return self is other


# @cache
# @profile
@stash.stashed_result
def Word(
    token: str,
    lang: str = DEFAULT_LANG,
    force_unstress: bool = None,
    force_ambig_stress: bool = None,
    use_cache: bool = False,
) -> "WordType":
    """
    Create a WordType object for the given token in the specified language.

    Args:
        token (str): The word token to create a WordType for.
        lang (str, optional): The language code. Defaults to DEFAULT_LANG.

    Returns:
        WordType: A WordType object for the given token.

    Raises:
        Exception: If the specified language is not recognized.
    """
    #log.debug("making wordtype")
    wordtype = None

    empty_wordtype = WordType(token, children=[], lang=lang)
    wordtype = None
    if token_is_punc(token):
        wordtype = empty_wordtype

    if not wordtype:
        ## get from lang?
        lang_obj = Language(lang)
        tokenx = get_wordform_token(token)
        sylls_ll, meta = lang_obj.get(
            tokenx,
            force_unstress=force_unstress,
            force_ambig_stress=force_ambig_stress,
        )

        wordforms = []
        for wordform_sylls in sylls_ll:
            wordform_sylls_ipa, wordform_sylls_text = zip(*wordform_sylls)
            wordform = WordForm(
                tokenx,
                sylls_ipa=tuple(wordform_sylls_ipa),
                sylls_text=tuple(wordform_sylls_text),
                num=len(wordforms)+1,
                **meta,
            )
            wordforms.append(wordform)

        ## make object
        wordtype = WordType(
            token,
            children=wordforms,
            lang=lang,
        )

    return wordtype


def get_wordform_token(token):
    tokenx = token.strip()
    if any(x.isspace() for x in tokenx):
        log.warning(
            f'Word "{tokenx}" has spaces in it, replacing them with hyphens for parsing'
        )
        tokenx = "".join(x if not x.isspace() else "-" for x in tokenx)
    return tokenx


def token_is_punc(token):
    tokenx = get_wordform_token(token)
    return not any(x.isalpha() for x in tokenx)
