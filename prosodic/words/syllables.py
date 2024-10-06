from . import *


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
            from gruut_ipa import Pronunciation

            sipa = "".join(x for x in ipa if x.isalpha())
            pron = Pronunciation.from_string(sipa)
            phones = [p.text for p in pron if p.text]
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

        Returns:
            True if the syllable is heavy, False otherwise.
        """
        return bool(self.has_consonant_ending or self.has_dipthong)

    @property
    def is_strong(self) -> Optional[bool]:
        """
        Check if the syllable is strong.

        Returns:
            True if the syllable is strong, False if weak, None if undetermined.
        """
        if not len(self.parent.children) > 1:
            return None
        if not self.is_stressed:
            return False
        if self.prev and not self.prev.is_stressed:
            return True
        if self.next and not self.next.is_stressed:
            return True

    @property
    def is_weak(self) -> Optional[bool]:
        """
        Check if the syllable is weak.

        Returns:
            True if the syllable is weak, False if strong, None if undetermined.
        """
        if not len(self.parent.children) > 1:
            return None
        if self.is_stressed:
            return False
        if self.prev and self.prev.is_stressed:
            return True
        if self.next and self.next.is_stressed:
            return True

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
