from .imports import *


class PhonemeList(EntityList):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def do_phons(phons):
            vowel_yet = False
            for phon in phons:
                if not phon.is_vowel:
                    if not vowel_yet:
                        phon._attrs["is_onset"] = True
                        phon._attrs["is_rime"] = False
                        phon._attrs["is_nucleus"] = False
                        phon._attrs["is_coda"] = False
                    else:
                        phon._attrs["is_onset"] = False
                        phon._attrs["is_rime"] = True
                        phon._attrs["is_nucleus"] = False
                        phon._attrs["is_coda"] = True
                else:
                    vowel_yet = True
                    phon._attrs["is_onset"] = False
                    phon._attrs["is_rime"] = True
                    phon._attrs["is_nucleus"] = True
                    phon._attrs["is_coda"] = False

        # get syll specific feats
        phons_by_syll = group_ents(self.children, "syllable")

        for phons in phons_by_syll:
            do_phons(phons)


class Syllable(Entity):
    prefix = "syll"
    child_type = "Phoneme"
    list_type = PhonemeList

    @profile
    def __init__(self, txt: str, ipa=None, parent=None, children=[], **kwargs):
        from .phonemes import Phoneme
        from gruut_ipa import Pronunciation

        assert ipa or children
        if ipa and not children:
            sipa = "".join(x for x in ipa if x.isalpha())
            pron = Pronunciation.from_string(sipa)
            phones = [p.text for p in pron if p.text]
            children = [Phoneme(phon) for phon in phones]
        super().__init__(txt=txt, ipa=ipa, children=children, parent=parent, **kwargs)

    def to_json(self):
        return super().to_json(ipa=self.ipa)

    @cached_property
    def stress(self):
        return get_stress(self.ipa)

    @cached_property
    def attrs(self):
        return {
            **self._attrs,
            "num": self.num,
            "txt": self.txt,
            "is_stressed": self.is_stressed,
            "is_heavy": self.is_heavy,
            "is_strong": self.is_strong,
            "is_weak": self.is_weak,
        }

    @cached_property
    def has_consonant_ending(self):
        return self.children[-1].cons > 0

    @cached_property
    def num_vowels(self):
        return sum(1 for phon in self.children if phon.cons <= 0)

    @cached_property
    def has_dipthong(self):
        return self.num_vowels > 1

    @cached_property
    def is_stressed(self):
        return self.stress in {"S", "P"}

    @cached_property
    def is_heavy(self):
        return bool(self.has_consonant_ending or self.has_dipthong)

    @cached_property
    def is_strong(self):
        if not len(self.parent.children) > 1:
            return None
        if not self.is_stressed:
            return False
        if self.prev and not self.prev.is_stressed:
            return True
        if self.next and not self.next.is_stressed:
            return True

    @cached_property
    def is_weak(self):
        if not len(self.parent.children) > 1:
            return None
        if self.is_stressed:
            return False
        if self.prev and self.prev.is_stressed:
            return True
        if self.next and self.next.is_stressed:
            return True

    @cached_property
    def onset(self):
        return PhonemeList(p for p in self.children if p.is_onset)

    @cached_property
    def rime(self):
        return PhonemeList(p for p in self.children if p.is_rime)

    @cached_property
    def nucleus(self):
        return PhonemeList(p for p in self.children if p.is_nucleus)

    @cached_property
    def coda(self):
        return PhonemeList(p for p in self.children if p.is_coda)

    @cache
    def rime_distance(self, syllable):
        return self.wordform.rime_distance(syllable.wordform)
