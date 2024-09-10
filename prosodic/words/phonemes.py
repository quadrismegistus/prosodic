from ..imports import *


class PhonemeClass(Entity):
    """
    Represents a phoneme with various attributes.

    Attributes:
        prefix (str): The prefix for the phoneme class.
    """

    prefix: str = "phon"

    @profile
    def __init__(self, txt: str, **kwargs: Any) -> None:
        """
        Initialize a PhonemeClass instance.

        Args:
            txt (str): The text representation of the phoneme.
            **kwargs: Additional keyword arguments.
        """
        self._feats = {}
        super().__init__(txt=txt)
        for k,v in kwargs.items():
            try:
                setattr(self,k,v)
            except Exception:
                pass
        

    @property
    def is_vowel(self) -> Optional[bool]:
        """
        Determine if the phoneme is a vowel.

        Returns:
            Optional[bool]: True if vowel, False if consonant, None if undetermined.
        """
        if not hasattr(self, "cons") or self.cons is None:
            return None
        if self.cons > 0:
            return False
        if self.cons < 1:
            return True
        return None
    
    @property
    def is_cons(self):
        return not self.is_vowel

    def to_dict(self) -> dict:
        return super().to_dict(incl_txt=True)

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


@profile
def Phoneme(txt: str, **kwargs: Any) -> PhonemeClass:
    """
    Create a Phoneme object from text.

    Args:
        txt (str): The text representation of the phoneme.
        **kwargs: Additional keyword arguments.

    Returns:
        PhonemeClass: A PhonemeClass instance representing the phoneme.
    """
    phon = txt
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
    phonobj = PhonemeClass(phon, **phond)
    return phonobj


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

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize a PhonemeList instance.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)

        def do_phons(phons: List[PhonemeClass]) -> None:
            """
            Process a list of phonemes to set syllable position attributes.

            Args:
                phons (List[PhonemeClass]): A list of phonemes to process.
            """
            vowel_yet = False
            for phon in phons:
                if not phon.is_vowel:
                    if not vowel_yet:
                        phon._feats["is_onset"] = True
                        phon._feats["is_rime"] = False
                        phon._feats["is_nucleus"] = False
                        phon._feats["is_coda"] = False
                    else:
                        phon._feats["is_onset"] = False
                        phon._feats["is_rime"] = True
                        phon._feats["is_nucleus"] = False
                        phon._feats["is_coda"] = True
                else:
                    vowel_yet = True
                    phon._feats["is_onset"] = False
                    phon._feats["is_rime"] = True
                    phon._feats["is_nucleus"] = True
                    phon._feats["is_coda"] = False

        # get syll specific feats
        phons_by_syll = group_ents(self.children, "syllable")

        for phons in phons_by_syll:
            do_phons(phons)