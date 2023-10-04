from .imports import *
SYLL_SEP='.'

@cache
@profile
def Word(token, lang=DEFAULT_LANG):
    if lang not in LANGS: 
        raise Exception(f'Language {lang} not recognized')
    lang_obj = LANGS[lang]()
    return lang_obj.get(token)

class WordToken(entity):
    child_type='WordType'

    prefix='wordtoken'
    @profile
    def __init__(self, token, lang=DEFAULT_LANG, parent=None, **kwargs):
        self.word = word = Word(token, lang=lang)
        super().__init__(
            children=[word],
            parent=parent,
            txt=token,
            **kwargs
        )


class WordType(entity):
    child_type: str = 'WordForm'
    
    prefix='word'
    @profile
    def __init__(self, token:str, children:list, parent=None, **kwargs):
        super().__init__(
            children=children, 
            parent=parent,
            txt=token,
            **kwargs
        )

    @property
    def forms(self): return self.children
    @property
    def form(self): return self.children[0] if self.children else None
    @property
    def num_forms(self): return len(self.children)
    @property
    def is_punc(self): 
        return True if not any([x.isalpha() for x in self.txt]) else None

    @cached_property
    def num_sylls(self): 
        x=np.median([form.num_sylls for form in self.forms])
        return None if np.isnan(x) else int(round(x))

    @cached_property
    def num_stressed_sylls(self): 
        x=np.median([form.num_stressed_sylls for form in self.forms])
        return None if np.isnan(x) else int(round(x))

    @cached_property
    def attrs(self):
        return {
            **super().attrs,
            'num_forms':self.num_forms,
            # 'num_sylls':self.num_sylls,
            # 'num_stressed_sylls':self.num_stressed_sylls,
            'is_punc':self.is_punc,
        }
    



class WordForm(entity):
    prefix='wordform'
    child_type: str = 'Syllable'

    @profile
    def __init__(self, txt:str, sylls_ipa=[], sylls_text=[], syll_sep='.'):
        from .syllables import Syllable
        sylls_ipa=(
            sylls_ipa.split(syll_sep) 
            if type(sylls_ipa)==str 
            else sylls_ipa
        )
        sylls_text=(
            sylls_text.split(syll_sep) 
            if type(sylls_text)==str 
            else (
                sylls_text
                if sylls_text
                else sylls_ipa
            )
        )
        children=[]
        if sylls_text and sylls_ipa:
            for syll_str,syll_ipa in zip(sylls_text, sylls_ipa):
                syll = Syllable(
                    syll_str, 
                    ipa=syll_ipa, 
                    parent=self
                )
                children.append(syll)
        super().__init__(
            # sylls_ipa=sylls_ipa, 
            # sylls_text=sylls_text, 
            txt=txt,
            children=children
        )

    @cached_property
    def token_stress(self):
        return SYLL_SEP.join(
            syll.txt.upper() if syll.is_stressed else syll.txt.lower()
            for syll in self.children
        )

    
    @cached_property
    def is_functionword(self):
        return len(self.children)==1 and not self.children[0].is_stressed
    @cached_property
    def num_sylls(self): return len(self.children)
    @cached_property
    def num_stressed_sylls(self): return len([syll for syll in self.children if syll.is_stressed])



@total_ordering
class WordFormList(UserList):
    def __repr__(self):
        return ' '.join(wf.token_stress for wf in self.data)
    
    @cached_property
    def slots(self):
        return [
            syll
            for wordform in self.data
            for syll in wordform.children
        ]

    @cached_property
    def df(self):
        l=[
            {
                k:('.'.join(v) if type(v)==list else v)
                for k,v in px.attrs.items()
            }
            for px in self.data
            if px is not None
        ]
        return pd.DataFrame(l).set_index('token')

    @cached_property
    def num_stressed_sylls(self):
        return sum(
            int(syll.is_stressed)
            for wordform in self.data
            for syll in wordform.children
        )
    
    @cached_property
    def num_sylls(self):
        return sum(
            1
            for wordform in self.data
            for syll in wordform.children
        )
    
    @cached_property
    def first_syll(self):
        for wordform in self.data:
            for syll in wordform.children:
                return syll
    
    @cached_property
    def sort_key(self):
        sylls_is_odd = int(bool(self.num_sylls % 2))
        first_syll_stressed = 2 if self.first_syll is None else int(self.first_syll.is_stressed)
        return (sylls_is_odd, self.num_sylls, self.num_stressed_sylls, first_syll_stressed)

    def __lt__(self, other): return self.sort_key<other.sort_key
    def __eq__(self, other): return self.sort_key==other.sort_key
        






def get_stress(ipa):
    if not ipa: return ''
    if ipa[0]=='`': return 'S'
    if ipa[0]=="'": return 'P'
    return 'U'



