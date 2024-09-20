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
    prefix = 'stanza'

    def __repr__(self, **kwargs):
        return f"Stanza(num={self.num}, txt={repr(self.txt)})"


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
        return self.lines.get_rhyming_lines(max_dist=max_dist)
    
    @property
    def rhyming_lines(self):
        return self.get_rhyming_lines(max_dist=RHYME_MAX_DIST)

    @property
    def num_rhyming_lines(self) -> int:
        """
        Get the number of rhyming lines in the stanza.

        Returns:
            int: The number of rhyming lines.
        """
        return len(self.rhyming_lines)

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