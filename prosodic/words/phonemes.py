from ..imports import *


class Phoneme(Entity):
    """
    Represents a phoneme with various attributes.

    Attributes:
        prefix (str): The prefix for the phoneme class.
    """

    prefix: str = "phon"

    @cached_property
    def feats(self):
        return get_phoneme_feats(self.txt)

    @property
    def is_vowel(self) -> Optional[bool]:
        """
        Determine if the phoneme is a vowel.

        Returns:
            Optional[bool]: True if vowel, False if consonant, None if undetermined.
        """
        cons = self.feats.get('cons')
        if cons is None:
            return None
        if cons > 0:
            return False
        if cons < 1:
            return True
        return None
    
    @property
    def is_cons(self):
        return not self.is_vowel

    def to_dict(self, **kwargs) -> dict:
        return super().to_dict(incl_txt=True, **kwargs)

    @property
    def is_onset(self) -> Optional[bool]:
        """
        Check if the phoneme is part of the syllable onset.

        Returns:
            Optional[bool]: True if onset, False otherwise, None if not set.
        """
        return self._feats.get("is_onset")

    @property
    def is_rime(self) -> Optional[bool]:
        """
        Check if the phoneme is part of the syllable rime.

        Returns:
            Optional[bool]: True if rime, False otherwise, None if not set.
        """
        return self._feats.get("is_rime")

    @property
    def is_nucleus(self) -> Optional[bool]:
        """
        Check if the phoneme is the syllable nucleus.

        Returns:
            Optional[bool]: True if nucleus, False otherwise, None if not set.
        """
        return self._feats.get("is_nucleus")

    @property
    def is_coda(self) -> Optional[bool]:
        """
        Check if the phoneme is part of the syllable coda.

        Returns:
            Optional[bool]: True if coda, False otherwise, None if not set.
        """
        return self._feats.get("is_coda")


@cache
@profile
def get_phoneme_featuretable() -> panphon.FeatureTable:
    """
    Get the phoneme feature table.

    Returns:
        panphon.FeatureTable: The feature table for phonemes.
    """
    ft = panphon.FeatureTable()
    return ft

@cache
def get_phoneme_feats(phon: str) -> Dict[str, Any]:
    """
    Get the features of a phoneme.

    Args:
        phon (str): The phoneme.

    Returns:
        Dict[str, Any]: The features of the phoneme.
    """
    ft = get_phoneme_featuretable()
    phonl = ft.word_fts(phon)
    if not phonl:
        # log.error(f'What is this phoneme? {phon}')
        if phon in get_ipa_info():
            phond = get_ipa_info().get(phon, {})
        else:
            # log.error(f"What is this phoneme? No features found for it: {phon}")
            phond = {}
    else:
        phond = phonl[0].data
    return phond


FEATS_PANPHON: List[str] = [
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
def get_ipa_info() -> Dict[str, Any]:
    """
    Get IPA information from a JSON file.

    Returns:
        Dict[str, Any]: A dictionary containing IPA information.
    """
    with open(PATH_PHONS) as f:
        return json.load(f)


class PhonemeList(EntityList):
    """
    A list of phonemes with additional functionality.
    """

    # def __init__(self, *args: Any, **kwargs: Any) -> None:
    #     """
    #     Initialize a PhonemeList instance.

    #     Args:
    #         *args: Variable length argument list.
    #         **kwargs: Arbitrary keyword arguments.
    #     """
    #     super().__init__(*args, **kwargs)

    #     def do_phons(phons: List[Phoneme]) -> None:
    #         """
    #         Process a list of phonemes to set syllable position attributes.

    #         Args:
    #             phons (List[Phoneme]): A list of phonemes to process.
    #         """
    #         vowel_yet = False
    #         for phon in phons:
    #             if not phon.is_vowel:
    #                 if not vowel_yet:
    #                     phon._feats["is_onset"] = True
    #                     phon._feats["is_rime"] = False
    #                     phon._feats["is_nucleus"] = False
    #                     phon._feats["is_coda"] = False
    #                 else:
    #                     phon._feats["is_onset"] = False
    #                     phon._feats["is_rime"] = True
    #                     phon._feats["is_nucleus"] = False
    #                     phon._feats["is_coda"] = True
    #             else:
    #                 vowel_yet = True
    #                 phon._feats["is_onset"] = False
    #                 phon._feats["is_rime"] = True
    #                 phon._feats["is_nucleus"] = True
    #                 phon._feats["is_coda"] = False

    #     # get syll specific feats
    #     phons_by_syll = group_ents(self.children, "syllable")

    #     for phons in phons_by_syll:
    #         do_phons(phons)