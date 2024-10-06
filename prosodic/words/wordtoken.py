from . import *


class WordToken(Entity):
    """Represents a word token in text."""

    prefix = "wordtoken"

    # @#log.debug
    def __init__(
        self,
        children: List["WordType"] = [],
        txt: str = None,
        lang: str = DEFAULT_LANG,
        parent: Optional["Entity"] = None,
        text=None,
        num=None,
        key=None,
        **kwargs,
    ):
        """
        Initialize a WordToken object.

        Args:
            txt (str): The text of the word token.
            lang (str, optional): The language code. Defaults to DEFAULT_LANG.
            parent (Entity, optional): The parent entity. Defaults to None.
            children (List[WordType], optional): List of child WordType objects. Defaults to [].
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            children=children,
            parent=parent,
            txt=txt,
            lang=lang,
            text=text,
            num=num,
            key=key,
            **kwargs,
        )
        self._preterm = None

        if not self.children:
            self.children.append(WordType(txt=txt,lang=lang))


    @property
    def preterm(self):
        return self._preterm

    def to_dict(
        self,
        incl_num=True,
        incl_children=False,
        incl_txt=True,
        incl_attrs=True,
        **kwargs,
    ) -> dict:
        """
        Convert the WordToken to a JSON-serializable dictionary.

        Returns:
            dict: A dictionary representation of the WordToken.
        """
        return super().to_dict(
            incl_num=incl_num,
            incl_children=incl_children,
            incl_txt=incl_txt,
            incl_attrs=incl_attrs,
            **kwargs,
        )

    @property
    def has_wordform(self):
        return bool(
            self.wordtype and self.wordtype.children and len(self.wordtype.children)
        )

    @property
    def attrs(self):
        return {**super().attrs, **({} if not self.preterm else self.preterm.attrs)}

    @property
    def wordtype(self):
        return self.children[0] if self.children else None

    @property
    def is_punc(self):
        return self.wordtype.is_punc

    def force_unstress(self):
        from .wordtype import WordType, WordTypeList

        wordtype = WordType(
            txt=self._txt, lang=self.lang, force_unstress=True
        )
        self.children = WordTypeList([wordtype], parent=self, )
        wordtype.parent = self

    def force_ambig_stress(self):
        from .wordtype import WordType, WordTypeList

        wordtype = WordType(
            txt=self._txt, lang=self.lang, force_ambig_stress=True
        )
        self.children = WordTypeList([wordtype], parent=self)
        wordtype.parent = self
