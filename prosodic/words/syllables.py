from . import *

_ipa_phone_cache = {}

def _parse_ipa_cached(ipa):
    """Cache gruut_ipa Pronunciation.from_string() results."""
    sipa = "".join(x for x in ipa if x.isalpha())
    if sipa in _ipa_phone_cache:
        return _ipa_phone_cache[sipa]
    from gruut_ipa import Pronunciation
    pron = Pronunciation.from_string(sipa)
    phones = tuple(p.text for p in pron if p.text)
    _ipa_phone_cache[sipa] = phones
    return phones


class Syllable(Entity):
    """
    Represents a syllable in a word.

    Attributes:
        prefix (str): Prefix for the syllable.
        child_type (str): Type of child entities (Phoneme).
    """

    prefix: str = "syll"
    child_type: str = "Phoneme"

    def __init__(
        self,
        children: List[Entity] = [],
        txt: str = None,
        ipa: Optional[str] = None,
        parent: Optional[Any] = None,
        text=None,
        key=None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a Syllable object.

        Args:
            txt: The text representation of the syllable.
            ipa: The IPA representation of the syllable.
            parent: The parent entity of the syllable.
            children: List of child entities (Phonemes).
            **kwargs: Additional keyword arguments.
        """
        assert ipa or children
        
        super().__init__(
            txt=txt,
            children=children,
            parent=parent,
            text=text,
            key=key,
            ipa=ipa,
            **kwargs,
        )
        
        if self.ipa and not self.children:
            phones = _parse_ipa_cached(ipa)
            for phon in phones:
                self.children.append(Phoneme(txt=phon))
        

    def to_dict(self, incl_txt=True, incl_attrs=True, **kwargs) -> dict:
        return super().to_dict(incl_txt=incl_txt, incl_attrs=incl_attrs, **kwargs)

    @property
    def stress(self) -> str:
        """
        Get the stress level of the syllable.

        Returns:
            The stress level as a string.
        """
        return get_syll_ipa_stress(self.ipa)

    @property
    def weight(self):
        return "L" if not self.is_heavy else "H"

    @property
    def stress_num(self) -> float:
        if self.stress == "P":
            return 1.0
        elif self.stress == "S":
            return 0.5
        else:
            return 0.0

    # @property
    # def attrs(self) -> dict:
    #     """
    #     Get the attributes of the syllable.

    #     Returns:
    #         A dictionary of syllable attributes.
    #     """
    #     return {
    #         **self._attrs,
    #         # "num": self.num,
    #         # "txt": self.txt,
    #         "is_stressed": self.is_stressed,
    #         "is_heavy": self.is_heavy,
    #         "is_strong": self.is_strong,
    #         "is_weak": self.is_weak,
    #     }

    @property
    def has_consonant_ending(self) -> bool:
        """
        Check if the syllable ends with a consonant.

        Returns:
            True if the syllable ends with a consonant, False otherwise.
        """
        return self.children[-1].is_cons

    @property
    def num_vowels(self) -> int:
        """
        Get the number of vowels in the syllable.

        Returns:
            The number of vowels.
        """
        return sum(1 for phon in self.children if phon.is_vowel)

    @property
    def has_dipthong(self) -> bool:
        """
        Check if the syllable contains a diphthong.

        Returns:
            True if the syllable has a diphthong, False otherwise.
        """
        return self.num_vowels > 1

    @property
    def has_long_vowel(self) -> bool:
        """
        Check if the syllable contains a long monophthong (iː, uː, ...).

        Returns:
            True if any vowel phoneme carries panphon's `long` feature.
        """
        return any(p.is_vowel and p.feats.get("long", -1) == 1
                   for p in self.children)

    @property
    def is_stressed(self) -> bool:
        """
        Check if the syllable is stressed.

        Returns:
            True if the syllable is stressed, False otherwise.
        """
        return self.stress in {"S", "P"}

    @property
    def is_heavy(self) -> bool:
        """
        Check if the syllable is heavy.

        Heavy = branching rime: a coda, OR a long/complex nucleus (diphthong
        or long monophthong). Long monophthongs (iː/uː/...) were previously
        missed, mis-scoring e.g. "see"/"too" as light.

        Returns:
            True if the syllable is heavy, False otherwise.
        """
        return bool(self.has_consonant_ending or self.has_dipthong
                    or self.has_long_vowel)

    def _prominence_neighbours(self):
        """Within-word neighbours' prominence levels (stress_num: primary 1.0 >
        secondary 0.5 > unstressed 0.0), for is_strong / is_weak."""
        sibs = self.parent.children
        # EntityList.index (ents.py) returns None on not-found — it does NOT
        # raise ValueError — so guard explicitly. (A bare `if i > 0` on None
        # would TypeError; the old try/except never fired.)
        i = sibs.index(self)
        if i is None:
            return []
        neigh = []
        if i > 0:
            neigh.append(sibs[i - 1].stress_num)
        if i < len(sibs) - 1:
            neigh.append(sibs[i + 1].stress_num)
        return neigh

    def _strong_weak(self) -> Optional[tuple]:
        """(is_strong, is_weak) from the single shared rule
        (texts/syll_df.py:strong_weak_from_levels) — the SAME function the DF
        parse path calls, so the two paths cannot disagree. None for a
        monosyllable, where strength is undefined.
        """
        from ..texts.syll_df import strong_weak_from_levels
        if not len(self.parent.children) > 1:
            return None
        # a level list of this syllable + its within-word neighbours (siblings'
        # stress_num). Centre self so BOTH neighbours are the positional
        # neighbours of levels[idx]; neighbour order is irrelevant to the rule.
        neigh = self._prominence_neighbours()
        if len(neigh) == 2:
            levels, idx = [neigh[0], self.stress_num, neigh[1]], 1
        else:
            levels, idx = [self.stress_num, *neigh], 0
        return strong_weak_from_levels(levels, idx)

    @property
    def is_strong(self) -> Optional[bool]:
        """
        Strong = a local prominence MAXIMUM within the word: more prominent than
        a neighbour (primary > secondary > unstressed), lower than none. Shares
        the DF path's rule (texts/syll_df.py:strong_weak_from_levels); a
        "shoulder" in a monotonic run (a mid secondary) or a plateau is neither
        — is_strong and is_weak never both.

        Returns:
            True if the syllable is a prominence peak, else False (None for a
            monosyllable, where strength is undefined).
        """
        sw = self._strong_weak()
        return None if sw is None else sw[0]

    @property
    def is_weak(self) -> Optional[bool]:
        """
        Weak = a local prominence MINIMUM within the word: less prominent than a
        neighbour, more prominent than none. See is_strong.

        Returns:
            True if the syllable is a prominence trough, else False (None for a
            monosyllable).
        """
        sw = self._strong_weak()
        return None if sw is None else sw[1]

    @property
    def onset(self) -> PhonemeList:
        """
        Get the onset of the syllable.

        Returns:
            A PhonemeList containing the onset phonemes.
        """
        return PhonemeList(p for p in self.children if p.is_onset)

    @property
    def rime(self) -> PhonemeList:
        """
        Get the rime of the syllable.

        Returns:
            A PhonemeList containing the rime phonemes.
        """
        self.children._annotate_phons()
        return PhonemeList([p for p in self.children if p.is_rime], parent=self)

    @property
    def nucleus(self) -> PhonemeList:
        """
        Get the nucleus of the syllable.

        Returns:
            A PhonemeList containing the nucleus phonemes.
        """
        return PhonemeList(p for p in self.children if p.is_nucleus)

    @property
    def coda(self) -> PhonemeList:
        """
        Get the coda of the syllable.

        Returns:
            A PhonemeList containing the coda phonemes.
        """
        return PhonemeList(p for p in self.children if p.is_coda)

    @cache
    def rime_distance(self, syllable: "Syllable") -> float:
        """
        Calculate the rime distance between this syllable and another.

        Args:
            syllable: The syllable to compare with.

        Returns:
            The rime distance as a float.
        """
        return self.wordform.rime_distance(syllable.wordform)


class SyllableList(EntityList):
    """A list of Syllable objects."""

    pass
