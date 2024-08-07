from .imports import *


class PhonemeClass(Entity):
    prefix = "phon"

    @profile
    def __init__(self, txt, **kwargs):
        super().__init__(txt, **kwargs)

    @cached_property
    def is_vowel(self):
        if not hasattr(self, "cons") or self.cons is None:
            return None
        if self.cons > 0:
            return False
        if self.cons < 1:
            return True
        return None

    def to_json(self):
        resd = super().to_json()
        resd["_class"] = "Phoneme"
        resd.pop("children")
        return resd

    @property
    def is_onset(self):
        return self._attrs.get("is_onset")

    @property
    def is_rime(self):
        return self._attrs.get("is_rime")

    @property
    def is_nucleus(self):
        return self._attrs.get("is_nucleus")

    @property
    def is_coda(self):
        return self._attrs.get("is_coda")


@cache
@profile
def get_phoneme_featuretable():
    ft = panphon.FeatureTable()
    return ft


# @cache
@profile
def Phoneme(txt, **kwargs):
    phon = txt
    ft = get_phoneme_featuretable()
    phonl = ft.word_fts(phon)
    if not phonl:
        # logger.error(f'What is this phoneme? {phon}')
        if phon in get_ipa_info():
            phond = get_ipa_info().get(phon, {})
        else:
            # logger.error(f"What is this phoneme? No features found for it: {phon}")
            phond = {}
    else:
        phond = phonl[0].data
    phonobj = PhonemeClass(phon, **phond)
    return phonobj


FEATS_PANPHON = [
    "num",
    "txt",
    "syl",
    "son",
    "cons",
    "cont",
    "delrel",
    "lat",
    "nas",
    "strid",
    "voi",
    "sg",
    "cg",
    "ant",
    "cor",
    "distr",
    "lab",
    "hi",
    "lo",
    "back",
    "round",
    "velaric",
    "tense",
    "long",
    "hitone",
    "hireg",
]


@cache
def get_ipa_info():
    with open(PATH_PHONS) as f:
        return json.load(f)