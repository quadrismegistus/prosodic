from .imports import *

class Syllable(Subtext):
    child_type = 'Phoneme'
    
    def init(self):
        from .phonemes import Phoneme
        from gruut_ipa import Pronunciation
        
        if self._init: return
        self._init=True
        
        self.children = []
        if self.syll_ipa:
            sipa=''.join(x for x in self.syll_ipa if x.isalpha())
            pron = Pronunciation.from_string(sipa)
            phones = [p.text for p in pron if p.text]
            for phon in phones:
                phonobj = Phoneme(phon)
                self.children.append(phonobj)
        return self
    
    @cached_property
    def attrs(self):
        return {
            **self._attrs, 
            **dict(syll_weight='H' if self.is_heavy else 'L'),
            **dict(
                is_stressed=self.is_stressed,
                is_heavy=self.is_heavy,
                is_strong=self.is_strong,
                is_weak=self.is_weak,
            )
        }

    
    @cached_property
    def has_consonant_ending(self):
        return self.children[-1].phon_cons
    
    @cached_property
    def num_vowels(self):
        return sum(1 for phon in self.children if phon.phon_cons<=0)
    
    @cached_property
    def has_dipthong(self):
        return self.num_vowels>1
    
    @cached_property
    def is_stressed(self):
        return self.syll_stress in {'S','P'}
    
    @cached_property
    def is_heavy(self):
        return bool(self.has_consonant_ending or self.has_dipthong)
    
    
    @cached_property
    def is_strong(self):
        if not len(self.parent.children)>1: return None
        if not self.is_stressed: return False
        if self.prev and not self.prev.is_stressed: return True
        if self.next and not self.next.is_stressed: return True

    @cached_property
    def is_weak(self):
        if not len(self.parent.children)>1: return None
        if self.is_stressed: return False
        if self.prev and self.prev.is_stressed: return True
        if self.next and self.next.is_stressed: return True
