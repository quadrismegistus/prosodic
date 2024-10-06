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


def split_scansion(wsws: str) -> List[str]:
    """Split a scansion string into positions.

    Args:
        wsws: The scansion string.

    Returns:
        A list of scansion positions.
    """
    wsws = wsws.replace(" ","").replace("-", "w").replace("+", "s")
    positions = []
    position = []
    last_x = None
    for x in wsws:
        if last_x and last_x != x and position:
            positions.append(position)
            position = []
        position.append(x)
        last_x = x
    if position:
        positions.append(position)
    return ["".join(pos) for pos in positions]


@cache
def get_possible_scansions(nsyll: int, max_s: Optional[int] = METER_MAX_S, max_w: Optional[int] = METER_MAX_W) -> List[List[str]]:
    """Get all possible scansions for a given number of syllables.

    Args:
        nsyll: Number of syllables.
        max_s: Maximum number of strong positions.
        max_w: Maximum number of weak positions.

    Returns:
        A list of possible scansions.
    """
    if max_s is None:
        max_s = nsyll
    if max_w is None:
        max_w = nsyll
    return [
        l for l in iter_mpos(nsyll, max_s=max_s, max_w=max_w) if getlenparse(l) == nsyll
    ]


def getlenparse(l: List[str]) -> int:
    """Get the total length of parsed positions.

    Args:
        l: List of parsed positions.

    Returns:
        The total length of all positions.
    """
    return sum(len(x) for x in l)


def iter_mpos(nsyll: int, starter: List[str] = [], pos_types: Optional[List[List[str]]] = None, max_s: int = METER_MAX_S, max_w: int = METER_MAX_W) -> Iterator[List[str]]:
    """Iterate over possible metrical positions.

    Args:
        nsyll: Number of syllables.
        starter: Initial list of positions.
        pos_types: List of possible position types.
        max_s: Maximum number of strong positions.
        max_w: Maximum number of weak positions.

    Yields:
        Lists of metrical positions.
    """
    if pos_types is None:
        wtypes = ["w" * n for n in range(1, max_w + 1)]
        stypes = ["s" * n for n in range(1, max_s + 1)]
        pos_types = [[x] for x in wtypes + stypes]

    news = []
    for pos_type in pos_types:
        if starter and starter[-1][-1] == pos_type[0][0]:
            continue
        new = starter + pos_type
        if getlenparse(new) <= nsyll:
            news.append(new)

    if news:
        yield from news
    for new in news:
        yield from iter_mpos(nsyll, starter=new, pos_types=pos_types)

