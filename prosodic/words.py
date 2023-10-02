from .imports import *
SYLL_SEP='.'


class Word(Subtext):
	child_type: str = 'WordForm'

class WordForm(entity):
	child_type: str = 'Syllable'
	def __init__(self, sylls_ipa, sylls_text=[], syll_sep='.'):
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
					syll_ipa=syll_ipa, 
					syll_stress=get_stress(syll_ipa), 
					parent=self
				)
				children.append(syll)
		token=''.join(sylls_text)
		super().__init__(
			sylls_ipa=sylls_ipa, 
			sylls_text=sylls_text, 
			token=token, 
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



