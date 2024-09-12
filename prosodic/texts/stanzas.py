from ..imports import *
from .texts import TextModel
from .lines import Line
from typing import List, Optional, Any

from ..words import WordTokenList

class Stanza(WordTokenList):
    """
    A class representing a stanza in a poem or text.

    This class inherits from Text and represents a group of lines in a poem or text.
    It provides methods for initializing, converting to JSON, and analyzing rhyme patterns.

    Attributes:
        sep (str): Separator string used between lines. Default is an empty string.
        child_type (str): The type of child entities. Default is "Line".
        prefix (str): Prefix used for identification. Default is "stanza".
    """

    def __repr__(self, **kwargs):
        return f"Stanza(num={self.num}, txt={repr(self.txt)})"


    # @#log.debug
    # def __init__(
    #     self,
    #     txt: str = "",
    #     children: List[Any] = [],
    #     parent: Optional[Any] = None,
    #     tokens_df: Optional[pd.DataFrame] = None,
    #     lang: str = DEFAULT_LANG,
    #     **kwargs
    # ) -> None:
    #     """
    #     Initialize a Stanza object.

    #     Args:
    #         txt (str): The text content of the stanza.
    #         children (List[Any]): List of child entities (usually Lines).
    #         parent (Optional[Any]): The parent entity of this stanza.
    #         tokens_df (Optional[pd.DataFrame]): DataFrame containing tokenized data.
    #         lang (str): The language of the stanza. Defaults to DEFAULT_LANG.
    #         **kwargs: Additional keyword arguments.

    #     Raises:
    #         Exception: If neither txt, children, nor tokens_df is provided.
    #     """
    #     from .lines import Line

    #     if not txt and not children and tokens_df is None:
    #         raise ValueError("Must provide either txt, children, or tokens_df")
    #     #log.debug(f"Checking input: txt={bool(txt)}, children={bool(children)}, tokens_df={tokens_df is not None}")

    #     if not children:
    #         #log.debug("No children provided, creating from tokens_df or txt")
            
    #         if tokens_df is None:
    #             tokens_df = tokenize_sentwords_df(txt)
    #             #log.debug(f"Tokenized text into DataFrame with shape {tokens_df.shape}")
            
    #         children = [
    #             Line(parent=self, tokens_df=line_df)
    #             for line_i, line_df in tokens_df.groupby("line_i")
    #         ]
    #         #log.debug(f"Created {len(children)} Line objects from tokens_df")

    #     if not txt:
    #         txt=''.join(x._txt for x in children)
    #     super().__init__(txt=txt, children=children, parent=parent, **kwargs)
    #     #log.debug(f"Initialized Stanza object with text: {txt}")

    # def to_dict(self) -> Dict[str, Any]:
    #     """
    #     Convert the Stanza object to a JSON-serializable dictionary.

    #     Returns:
    #         Dict[str, Any]: A dictionary representation of the Stanza object.
    #     """
    #     return Entity.to_dict(self, no_txt=True)

    def _repr_html_(self, as_df: bool = False, df: Optional[pd.DataFrame] = None) -> str:
        """
        Generate an HTML representation of the Stanza.

        Args:
            as_df (bool): If True, represent as a DataFrame. Default is False.
            df (Optional[pd.DataFrame]): An optional DataFrame to use for representation.

        Returns:
            str: HTML representation of the Stanza.
        """
        return super()._repr_html_(df=df) if as_df else self.to_html(as_str=True)

    def get_rhyming_lines(self, max_dist: int = RHYME_MAX_DIST) -> Dict[Any, Any]:
        """
        Get the rhyming lines within the stanza.

        Args:
            max_dist (int): Maximum distance between rhyming lines. Default is RHYME_MAX_DIST.

        Returns:
            Dict[Any, Any]: A dictionary of rhyming lines.
        """
        return self.children.get_rhyming_lines(max_dist=max_dist)

    @property
    def num_rhyming_lines(self) -> int:
        """
        Get the number of rhyming lines in the stanza.

        Returns:
            int: The number of rhyming lines.
        """
        return len(self.get_rhyming_lines(max_dist=RHYME_MAX_DIST))

    @property
    def is_rhyming(self) -> bool:
        """
        Check if the stanza contains rhyming lines.

        Returns:
            bool: True if the stanza contains rhyming lines, False otherwise.
        """
        return self.num_rhyming_lines > 0
    


class StanzaList(EntityList):
    
    @classmethod
    def from_wordtokens(cls, wordtokens, text=None):
        return WordTokenList._from_wordtokens(wordtokens, 'stanza', 'para_num', text=text)