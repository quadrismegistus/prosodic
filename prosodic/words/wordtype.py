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

        if not children:
            from ..langs import Language
            lang_obj = Language(lang)
            sylls_ll, meta = lang_obj.get(
                tokenx,
                force_unstress=force_unstress,
                force_ambig_stress=force_ambig_stress,
            )

            children = WordFormList(parent=self)
            for wordform_sylls in sylls_ll:
                wordform_sylls_ipa, wordform_sylls_text = zip(*wordform_sylls)
                wordform = WordForm(
                    txt=tokenx,
                    sylls_ipa=tuple(wordform_sylls_ipa),
                    sylls_text=tuple(wordform_sylls_text),
                    num=len(children)+1,
                    text=text,
                    parent=children,
                    **meta,
                )
                children.append(wordform)

        ## make object
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
        

    def to_dict(self) -> dict:
        """
        Convert the WordType to a JSON-serializable dictionary.

        Returns:
            dict: A dictionary representation of the WordType.
        """
        return super().to_dict(incl_attrs=True, incl_txt=True)

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




# @cache
# @profile
# @stash.stashed_result
def Word(
    token: str,
    lang: str = DEFAULT_LANG,
    force_unstress: bool = None,
    force_ambig_stress: bool = None,
    parent=None,
    text=None,
) -> "WordType":
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
    #log.debug("making wordtype")
    wordtype = None

    empty_wordtype = WordType(token, children=[], lang=lang, parent=parent, text=text)
    wordtype = None
    if token_is_punc(token):
        wordtype = empty_wordtype

    if not wordtype:
        ## get from lang?
        lang_obj = Language(lang)
        tokenx = get_wordform_token(token)
        sylls_ll, meta = lang_obj.get(
            tokenx,
            force_unstress=force_unstress,
            force_ambig_stress=force_ambig_stress,
        )

        wordforms = []
        for wordform_sylls in sylls_ll:
            wordform_sylls_ipa, wordform_sylls_text = zip(*wordform_sylls)
            wordform = WordForm(
                tokenx,
                sylls_ipa=tuple(wordform_sylls_ipa),
                sylls_text=tuple(wordform_sylls_text),
                num=len(wordforms)+1,
                text=text,
                **meta,
            )
            wordforms.append(wordform)

        ## make object
        wordtype = WordType(
            token,
            children=wordforms,
            lang=lang,
            parent=parent,
            text=text,
        )

    return wordtype
