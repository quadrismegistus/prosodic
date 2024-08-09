from ..imports import *

class Bounding:
    """
    Represents the potential bounding relations between two parses.

    Attributes:
        bounds (int): First parse harmonically bounds the second.
        bounded (int): First parse is harmonically bounded by the second.
        equal (int): The same constraint violation scores.
        unequal (int): Unequal scores; neither set of violations is a subset of the other.
    """

    bounds: int = 0
    bounded: int = 1
    equal: int = 2
    unequal: int = 3


def get_iambic_parse(nsyll: int) -> List[str]:
    """
    Generate an iambic parse for a given number of syllables.

    Args:
        nsyll (int): Number of syllables.

    Returns:
        List[str]: A list representing the iambic parse, where 'w' represents weak
        and 's' represents strong positions.
    """
    o = []
    while len(o) < nsyll:
        x = "w" if not o or o[-1] == "s" else "s"
        o.append(x)
    return o