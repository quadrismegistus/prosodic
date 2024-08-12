from typing import List, Optional, Union
from ..imports import *

SYLL_SEP = "."


# @cache
@profile
def Word(token: str, lang: str = DEFAULT_LANG) -> 'WordType':
    """
    Create a WordType object for the given token in the specified language.

    Args:
        token (str): The word token to create a WordType for.
        lang (str, optional): The language code. Defaults to DEFAULT_LANG.

    Returns:
        WordType: A WordType object for the given token.

    Raises:
        Exception: If the specified language is not recognized.
    """
    if lang not in LANGS:
        raise Exception(f"Language {lang} not recognized")
    lang_obj = LANGS[lang]()
    return lang_obj.get(token)


class WordToken(Entity):
    """Represents a word token in text."""

    child_type = "WordType"
    list_type = 'WordTypeList'
    prefix = "wordtoken"

    @profile
    def __init__(self, txt: str, lang: str = DEFAULT_LANG, parent: Optional['Entity'] = None, children: List['WordType'] = [], **kwargs):
        """
        Initialize a WordToken object.

        Args:
            txt (str): The text of the word token.
            lang (str, optional): The language code. Defaults to DEFAULT_LANG.
            parent (Entity, optional): The parent entity. Defaults to None.
            children (List[WordType], optional): List of child WordType objects. Defaults to [].
            **kwargs: Additional keyword arguments.
        """
        # if txt.startswith("\n"):
            # txt = txt[1:]
        if not children:
            children = WordTypeList([Word(txt.strip(), lang=lang)])
        self.word = children[0]
        super().__init__(children=children, parent=parent, txt=txt, lang=lang, **kwargs)

    def to_json(self) -> dict:
        """
        Convert the WordToken to a JSON-serializable dictionary.

        Returns:
            dict: A dictionary representation of the WordToken.
        """
        return super().to_json(**self.attrs)


class WordType(Entity):
    """Represents a word type (lexeme)."""

    child_type: str = "WordForm"
    list_type = 'list'
    prefix = "word"

    @profile
    def __init__(self, txt: str, children: List['WordForm'], parent: Optional['Entity'] = None, **kwargs):
        """
        Initialize a WordType object.

        Args:
            txt (str): The text of the word type.
            children (List[WordForm]): List of child WordForm objects.
            parent (Entity, optional): The parent entity. Defaults to None.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(children=children, parent=parent, txt=txt, **kwargs)

    def to_json(self) -> dict:
        """
        Convert the WordType to a JSON-serializable dictionary.

        Returns:
            dict: A dictionary representation of the WordType.
        """
        return super().to_json(lang=self.lang)

    @property
    def wtoken(self) -> 'WordToken':
        return WordToken(self.txt, lang=self.lang, children=self.children)

    @property
    def forms(self) -> List['WordForm']:
        return self.children

    @property
    def form(self) -> Optional['WordForm']:
        return self.children[0] if self.children else None

    @property
    def num_forms(self) -> int:
        return len(self.children)

    @property
    def is_punc(self) -> Optional[bool]:
        return True if not any([x.isalpha() for x in self.txt]) else None

    @cached_property
    def num_sylls(self) -> Optional[int]:
        x = np.median([form.num_sylls for form in self.forms])
        return None if np.isnan(x) else int(round(x))

    @cached_property
    def num_stressed_sylls(self) -> Optional[int]:
        x = np.median([form.num_stressed_sylls for form in self.forms])
        return None if np.isnan(x) else int(round(x))

    @cached_property
    def attrs(self) -> dict:
        return {
            **super().attrs,
            "num_forms": self.num_forms,
            # 'num_sylls':self.num_sylls,
            # 'num_stressed_sylls':self.num_stressed_sylls,
            "is_punc": self.is_punc,
        }

    def rime_distance(self, word: 'WordType') -> float:
        """
        Calculate the rime distance between this word and another.

        Args:
            word (WordType): The word to compare with.

        Returns:
            float: The rime distance between the two words.
        """
        return self.children[0].rime_distance(word.children[0])


class WordForm(Entity):
    """Represents a specific form of a word."""

    prefix = "wordform"
    child_type: str = "Syllable"
    list_type = 'SyllableList'

    @profile
    def __init__(
        self, txt: str, sylls_ipa: Union[str, List[str]] = [], sylls_text: Union[str, List[str]] = [], 
        children: List['Syllable'] = [], syll_sep: str = "."
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

        sylls_ipa = sylls_ipa.split(syll_sep) if type(sylls_ipa) == str else sylls_ipa
        sylls_text = (
            sylls_text.split(syll_sep)
            if type(sylls_text) == str
            else (sylls_text if sylls_text else sylls_ipa)
        )
        if not children:
            if sylls_text and sylls_ipa:
                children = [
                    Syllable(
                        syll_str,
                        ipa=syll_ipa,
                    )
                    for syll_str, syll_ipa in zip(sylls_text, sylls_ipa)
                ]
        super().__init__(
            # sylls_ipa=sylls_ipa,
            # sylls_text=sylls_text,
            txt=txt,
            children=children,
        )
        self.sylls_ipa = sylls_ipa
        self.sylls_text = sylls_text

    def to_json(self) -> dict:
        """
        Convert the WordForm to a JSON-serializable dictionary.

        Returns:
            dict: A dictionary representation of the WordForm.
        """
        return super().to_json(
            sylls_ipa=self.sylls_ipa,
            sylls_text=self.sylls_text,
        )

    @property
    def wtoken(self) -> 'WordToken':
        if self.parent:
            return self.parent.wtoken
        return WordToken(self.txt, lang=self.parent.lang, children=self.parent.children)

    @cached_property
    def syllables(self) -> List['Syllable']:
        return self.children

    @cached_property
    def token_stress(self) -> str:
        return SYLL_SEP.join(
            syll.txt.upper() if syll.is_stressed else syll.txt.lower()
            for syll in self.children
        )

    @cached_property
    def is_functionword(self) -> bool:
        return len(self.children) == 1 and not self.children[0].is_stressed

    @cached_property
    def num_sylls(self) -> int:
        return len(self.children)

    @cached_property
    def num_stressed_sylls(self) -> int:
        return len([syll for syll in self.children if syll.is_stressed])

    @cached_property
    def key(self) -> str:
        return hashstr(
            self._txt,
            self.sylls_ipa,
            self.sylls_text,
        )

    def to_hash(self) -> str:
        return hashstr(self.key)

    @cached_property
    def rime(self) -> Optional['PhonemeList']:
        """
        Get the rime of the word form.

        Returns:
            PhonemeList: The rime of the word form, or None if no rime can be determined.
        """
        from .phonemes import PhonemeList

        sylls = []
        for syll in reversed(self.children):
            sylls.insert(0, syll)
            if syll.stress == "P":
                break
        if not sylls:
            return
        o = sylls[0].rime.data + [phon for syll in sylls[1:] for phon in syll.children]
        return PhonemeList(o)

    @cache
    def rime_distance(self, wordform: 'WordForm') -> float:
        """
        Calculate the rime distance between this word form and another.

        Args:
            wordform (WordForm): The word form to compare with.

        Returns:
            float: The rime distance between the two word forms.
        """
        from scipy.spatial.distance import euclidean

        if self.txt == wordform.txt:
            return np.nan
        # return self.syllables[-1].rime_distance(wordform.syllables[-1])

        df1 = self.rime.df
        df2 = wordform.rime.df

        if list(df1.reset_index().phon_txt) == list(df2.reset_index().phon_txt):
            return 0

        s1 = df1.mean(numeric_only=True)
        s2 = df2.mean(numeric_only=True)
        keys = [
            k
            for k in set(s1.index) & set(s2.index)
            if k.startswith("phon_")
            and not k.endswith("_num")
            and not k.startswith("phon_is_")
        ]
        s1x = s1.loc[keys]
        s2x = s2.loc[keys]
        dist = euclidean(s1x, s2x)
        return dist



class WordTypeList(EntityList):
    """A list of WordType objects."""
    pass


@total_ordering
class WordFormList(EntityList):
    """A list of WordForm objects with additional properties and comparison methods."""

    def __repr__(self) -> str:
        """
        Get a string representation of the WordFormList.

        Returns:
            str: A string representation of the WordFormList.
        """
        return " ".join(wf.token_stress for wf in self.data)

    @cached_property
    def slots(self) -> List['Syllable']:
        return [syll for wordform in self.data for syll in wordform.children]

    @cached_property
    def num_stressed_sylls(self) -> int:
        return sum(
            int(syll.is_stressed)
            for wordform in self.data
            for syll in wordform.children
        )

    @cached_property
    def num_sylls(self) -> int:
        return sum(1 for wordform in self.data for syll in wordform.children)

    @cached_property
    def first_syll(self) -> Optional['Syllable']:
        for wordform in self.data:
            for syll in wordform.children:
                return syll

    @cached_property
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

    def __lt__(self, other: 'WordFormList') -> bool:
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




class WordTokenList(EntityList):
    """A list of WordToken objects."""
    pass