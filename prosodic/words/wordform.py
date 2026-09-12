from . import *


class WordForm(Entity):
    """Represents a specific form of a word."""

    prefix = "wordform"
    child_type: str = "Syllable"

    @profile
    def __init__(
        self,
        children: List["Syllable"] = [],
        txt: str = None,
        sylls_ipa: Union[str, List[str]] = [],
        sylls_text: Union[str, List[str]] = [],
        syll_sep: str = ".",
        num=None,
        text=None,
        key=None,
        parent=None,
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
        from .syllables import Syllable
        from ..langs import syll_ipa_str_is_stressed

        super().__init__(
            txt=txt,
            num=num,
            children=children,
            text=text,
            key=key,
            parent=parent,
            **kwargs,
        )

        if not self.children:
            assert sylls_text and sylls_ipa, "must provide sylls_text and sylls_ipa"
            sylls_ipa = (
                sylls_ipa.split(syll_sep) if type(sylls_ipa) == str else sylls_ipa
            )
            sylls_text = (
                sylls_text.split(syll_sep)
                if type(sylls_text) == str
                else (sylls_text if sylls_text else sylls_ipa)
            )
            for syll_str, syll_ipa in zip(sylls_text, sylls_ipa):
                self.children.append(
                    Syllable(
                        txt=syll_str,
                        ipa=syll_ipa,
                        text=text,
                    )
                )
        
        self.sylls_ipa = [syll.ipa for syll in self.children]
        self.sylls_text = [syll.txt for syll in self.children]
        self.ipa=".".join(self.sylls_ipa)
        self.stress="".join(syll.stress for syll in self.children)
        self.weight="".join(syll.weight for syll in self.children)
        self.stress_text=".".join(
            [
                (
                    syll_text.upper()
                    if syll_ipa_str_is_stressed(syll_ipa)
                    else syll_text.lower()
                )
                for syll_text, syll_ipa in zip(self.sylls_text, self.sylls_ipa)
            ]
        )

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

    def to_dict(self, incl_attrs=True, **kwargs) -> dict:
        return super().to_dict(incl_attrs=incl_attrs, **kwargs)

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

        if not len(self.children): return
        last_syll = self.children[-1]
        sylls = [last_syll]
        if not last_syll.is_stressed and len(self.children)>1:
            second_to_last_syll = self.children[-2]
            if second_to_last_syll.is_stressed:
                sylls.insert(0,second_to_last_syll)

        # print(sylls)
        # for syll_num_r, syll in enumerate(reversed(self.children)):
        #     sylls.insert(0, syll)
        #     if syll.stress == "P":
        #         break
        #     print(syll_num_r,syll)
        #     if syll_num_r>1:
        #         break
        if not sylls:
            return
        o = sylls[0].rime.data + [phon for syll in sylls[1:] for phon in syll.children]
        return PhonemeList(o, parent=self)


    @cache
    def rime_distance(self, wordform: "WordForm", max_dist=RHYME_MAX_DIST) -> float:
        """
        Calculate the rime distance between this word form and another.

        Uses feature-weighted edit distance on rime phonemes (via panphon),
        which properly aligns phonemes of different lengths and weights
        substitution cost by phonetic similarity. Returns a value in [0, 1]
        where 0 is a perfect rhyme.

        Args:
            wordform (WordForm): The word form to compare with.
            max_dist: Maximum distance threshold. Distances above this return
                np.nan. 0 = exact match only. None = no limit.

        Returns:
            float: The rime distance (0-1), or np.nan if above max_dist
                or comparing identical words.
        """
        if self.txt == wordform.txt:
            return np.nan

        phons1 = self.rime
        phons2 = wordform.rime
        if phons1 is None or phons2 is None:
            return np.nan

        if phons1.txt == phons2.txt:
            return 0.0

        if max_dist == 0:
            return np.nan

        dist = phons1.feature_edit_distance(phons2)
        if max_dist is not None and dist > max_dist:
            return np.nan
        return dist

    def _has_coda(self) -> bool:
        """Whether the rime closes on a consonant.

        The slant band is coda identity with the nucleus left free, which is the
        consonance of love/prove and gone/alone. Two open syllables share no coda
        to be identical about, so without this they collect that licence for free
        and any vowel-final word half-rhymes any other: away/tree, so/me.
        """
        rime = self.rime
        return bool(rime) and not all(p.is_vowel for p in rime)

    @cache
    def rime_distance_nc(self, wordform: "WordForm"):
        """Decompose rime distance into (nucleus, coda) components.

        The nucleus is the leading vowel run of the rime (the stressed
        syllable's vowel); the coda component is everything after it,
        including any unstressed tail syllables. Each component is a
        feature-weighted edit distance in [0, 1]; a present-vs-absent
        mismatch (one word open, the other closed) scores 1.0. The 2-D
        decomposition separates rhyme types a single scalar conflates:
        consonance (gone/alone: nucleus drifts, coda identical) vs
        assonance (day/late: nucleus identical, coda differs).

        Returns:
            (nucleus_dist, coda_dist) floats, or (nan, nan) for identical
            words or missing rimes.
        """
        from .phonemes import PhonemeList

        if self.txt == wordform.txt:
            return (np.nan, np.nan)
        r1, r2 = self.rime, wordform.rime
        if r1 is None or r2 is None:
            return (np.nan, np.nan)

        def split(rime):
            phons = list(rime)
            i = 0
            while i < len(phons) and phons[i].is_vowel:
                i += 1
            return phons[:i], phons[i:]

        def part_dist(p1, p2):
            if p1 and p2:
                return float(PhonemeList(p1).feature_edit_distance(
                    PhonemeList(p2)))
            if not p1 and not p2:
                return 0.0
            return 1.0

        n1, c1 = split(r1)
        n2, c2 = split(r2)
        return (part_dist(n1, n2), part_dist(c1, c2))

    def rime_type(
        self,
        wordform: "WordForm",
        perfect_nuc_max=RHYME_PERFECT_NUC_MAX,
        perfect_coda_max=RHYME_PERFECT_CODA_MAX,
        slant_coda_max=RHYME_SLANT_CODA_MAX,
        assonance_nuc_max=RHYME_ASSONANCE_NUC_MAX,
    ):
        """Classify the rhyme between this word form and another.

        Works in the 2-D (nucleus, coda) distance space of
        rime_distance_nc, with regions calibrated against Walker's (1775)
        rhyming dictionary (scripts/rime_eval.py, 2-D section; macro-F1
        0.758 vs 0.679 for the 1-D scalar). The calibration independently
        recovers the classical taxonomy:

        - 'perfect': nucleus match (dn <= 0.05) + near-coda (dc <= 0.15)
        - 'slant': coda identity (dc <= 0.05), nucleus free — consonance
          / half-rhyme (love/prove, gone/alone)
        - 'assonance': nucleus identity (dn <= 0.05) with coda mismatch
          (day/late). Linguistically real but NOT Walker-validated (his
          taxonomy has no assonance class) — treat as a weaker signal.
        - None otherwise (also for identical words, which do not rhyme
          with themselves).

        Independently validated on real verse (sonnet-scheme-derived
        positives AND true negatives, scripts/rime_eval.py): counting
        perfect+slant as rhyme gives F1 0.912, precision 0.944, FPR
        0.041 — vs FPR 0.226 for the 1-D scalar at 0.35. Counting
        assonance as rhyme trades +0.004 TPR for 3x the FPR; don't.
        """
        dn, dc = self.rime_distance_nc(wordform)
        if np.isnan(dn) or np.isnan(dc):
            return None
        if dn <= perfect_nuc_max and dc <= perfect_coda_max:
            return "perfect"
        if dc <= slant_coda_max and self._has_coda() and wordform._has_coda():
            return "slant"
        if dn <= assonance_nuc_max:
            return "assonance"
        return None




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
