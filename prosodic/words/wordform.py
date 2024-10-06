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

        print(sylls)
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
    def rime_distance(self, wordform: "WordForm") -> float:
        """
        Calculate the rime distance between this word form and another.

        Args:
            wordform (WordForm): The word form to compare with.

        Returns:
            float: The rime distance between the two word forms.
        """
        if self.txt == wordform.txt:
            return np.nan

        phons1 = self.rime
        phons2 = wordform.rime
        return phons1.feature_distance(phons2)




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
