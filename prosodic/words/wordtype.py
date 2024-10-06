from . import *


class WordType(Entity):
    """Represents a word type (lexeme)."""

    child_type: str = "WordForm"
    prefix = "wordtype"

    @profile
    def __init__(
        self,
        children: List["WordForm"] = None,
        txt: str = None,
        parent: Optional["Entity"] = None,
        lang: str = DEFAULT_LANG,
        text = None,
        key = None,
        force_unstress: bool = None,
        force_ambig_stress: bool = None,
        num = None,
        **kwargs,
    ):
        """
        Initialize a WordType object.

        Args:
            txt (str): The text of the word type.
            children (List[WordForm]): List of child WordForm objects.
            parent (Entity, optional): The parent entity. Defaults to None.
            **kwargs: Additional keyword arguments.
        """

        ## get from lang?
        tokenx = get_wordform_token(txt)
        super().__init__(
            txt = tokenx,
            children=children,
            lang=lang,
            parent=parent,
            text=text,
            key = key,
            num = num,
            **kwargs,
        )

        if not self.children and not token_is_punc(tokenx):
            from ..langs import get_word
            sylls_ll, meta = get_word(
                tokenx,
                lang=lang,
                force_unstress=force_unstress,
                force_ambig_stress=force_ambig_stress,
            )
            # print([tokenx, sylls_ll, meta])
            for wordform_sylls in sylls_ll:
                wordform_sylls_ipa, wordform_sylls_text = zip(*wordform_sylls)
                wordform = WordForm(
                    txt=tokenx,
                    sylls_ipa=tuple(wordform_sylls_ipa),
                    sylls_text=tuple(wordform_sylls_text),
                    **meta,
                )
                self.children.append(wordform)


        

    def to_dict(self, incl_attrs=True, incl_txt=True, **kwargs) -> dict:
        """
        Convert the WordType to a JSON-serializable dictionary.

        Returns:
            dict: A dictionary representation of the WordType.
        """
        return super().to_dict(incl_attrs=incl_attrs, incl_txt=incl_txt, **kwargs)

    def unstress(self) -> None:
        if self.num_forms > 1:
            wf = min(self.children, key=lambda wf: wf.num_stressed_sylls)
            self.children = [wf]
            self.clear_cached_properties()

    @property
    def wtoken(self) -> "WordToken":
        return WordToken(self.txt, lang=self.lang, children=self.children)

    @property
    def forms(self) -> List["WordForm"]:
        return self.children

    @property
    def form(self) -> Optional["WordForm"]:
        return self.children[0] if self.children else None

    @property
    def num_forms(self) -> int:
        return len(self.children)

    @property
    def is_punc(self) -> Optional[bool]:
        return True if token_is_punc(self.txt) else None

    @property
    def num_sylls(self) -> Optional[int]:
        x = np.median([form.num_sylls for form in self.forms])
        return None if np.isnan(x) else int(round(x))

    @property
    def num_stressed_sylls(self) -> Optional[int]:
        x = np.median([form.num_stressed_sylls for form in self.forms])
        return None if np.isnan(x) else int(round(x))

    @property
    def attrs(self) -> dict:
        return {
            **super().attrs,
            "num_forms": self.num_forms,
            # 'num_sylls':self.num_sylls,
            # 'num_stressed_sylls':self.num_stressed_sylls,
            "is_punc": self.is_punc,
        }

    def rime_distance(self, word: "WordType") -> float:
        """
        Calculate the rime distance between this word and another.

        Args:
            word (WordType): The word to compare with.

        Returns:
            float: The rime distance between the two words.
        """
        return self.children[0].rime_distance(word.children[0])




class WordTypeList(EntityList):
    """A list of WordType objects."""

    pass






def get_wordform_token(token):
    tokenx = token.strip()
    if any(x.isspace() for x in tokenx):
        log.warning(
            f'Word "{tokenx}" has spaces in it, replacing them with hyphens for parsing'
        )
        tokenx = "".join(x if not x.isspace() else "-" for x in tokenx)
    return tokenx


def token_is_punc(token):
    tokenx = get_wordform_token(token)
    return not any(x.isalpha() for x in tokenx)


def Word(token, lang=DEFAULT_LANG, **kwargs):
    from ..texts import TextModel
    return TextModel(txt=token, lang=lang, **kwargs).wordtype