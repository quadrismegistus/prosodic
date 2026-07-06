"""Maximally faithful Liberman & Prince (1977) metrical trees and grids.

EXPERIMENTAL / alongside the existing MetricalTree (Dozat) path in
``phrasal_stress.py`` — this module implements L&P's theory as literally as
possible, for comparison and study. Nothing here touches the shipping
``grid_data``/``phrasal_stress`` code.

The object here is L&P's binary **metrical tree**: every branching node has
exactly two daughters, one *strong* and one *weak* (their relation is
defined only on pairs of sisters — [ss], [ww], and an isolated [s] are
"meaningless", p.256). From such a tree two things are read off:

- the **designated terminal element** (DTE) of any node — the terminal
  reached by following strong branches down (p.259);
- the **metrical grid** — column heights over terminals, governed by the
  Relative Prominence Projection Rule (RPPR, their (104)): in any
  constituent, the DTE of the strong subconstituent is metrically stronger
  (taller column) than the DTE of the weak subconstituent.

The grid produced here is the *minimal* one satisfying the RPPR, which is
equivalent to inverting the stress-number algorithm of their (12). Both
derivations are implemented; ``tests/test_metrical_lp.py`` checks the grid
against L&P's own published figures (thirteen men (105), Montana cowboy
(108), ...).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Union


class LPTree:
    """A binary metrical tree node (Liberman & Prince 1977).

    A *leaf* carries a ``label`` (a syllable/terminal) and no children. An
    *internal* node carries ``left`` and ``right`` children and ``strong``
    ∈ {"l", "r"} naming which child is metrically strong (the other is
    weak). The root of a whole tree is conventionally neither strong nor
    weak (their footnote 6), which is simply the case of a node no parent
    labels.
    """

    __slots__ = ("label", "left", "right", "strong")

    def __init__(self, label=None, left=None, right=None, strong=None):
        self.label = label
        self.left = left
        self.right = right
        self.strong = strong  # "l" or "r" on internal nodes; None on leaves

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None

    @property
    def strong_child(self) -> "LPTree":
        return self.left if self.strong == "l" else self.right

    @property
    def weak_child(self) -> "LPTree":
        return self.right if self.strong == "l" else self.left

    def leaves(self) -> List["LPTree"]:
        """Terminals in left-to-right (surface) order."""
        if self.is_leaf:
            return [self]
        return self.left.leaves() + self.right.leaves()

    @property
    def dte(self) -> "LPTree":
        """Designated terminal element: descend through strong branches."""
        node = self
        while not node.is_leaf:
            node = node.strong_child
        return node

    def __repr__(self) -> str:
        if self.is_leaf:
            return f"{self.label!r}"
        ls = "s" if self.strong == "l" else "w"
        rs = "s" if self.strong == "r" else "w"
        return f"[{ls}:{self.left!r} {rs}:{self.right!r}]"


def _coerce(x: Union[str, LPTree]) -> LPTree:
    return x if isinstance(x, LPTree) else LPTree(label=x)


def leaf(label: str) -> LPTree:
    """A terminal node."""
    return LPTree(label=label)


def sw(left, right) -> LPTree:
    """Left-strong node [s w] — a trochaic pair (strings become leaves)."""
    return LPTree(left=_coerce(left), right=_coerce(right), strong="l")


def ws(left, right) -> LPTree:
    """Right-strong node [w s] — an iambic pair (strings become leaves)."""
    return LPTree(left=_coerce(left), right=_coerce(right), strong="r")


def _rppr_edges(tree: LPTree) -> List[tuple]:
    """Immediate 'metrically stronger than' relations induced by the RPPR.

    One per internal node: DTE(strong child) ▷ DTE(weak child).
    """
    edges = []

    def walk(node):
        if node.is_leaf:
            return
        edges.append((node.strong_child.dte, node.weak_child.dte))
        walk(node.left)
        walk(node.right)

    walk(tree)
    return edges


def grid_heights(tree: LPTree) -> List[int]:
    """Grid column height per terminal, in surface order.

    The minimal metrical grid satisfying the RPPR: a terminal's height is
    1 + the longest descending chain of 'stronger-than' relations beneath
    it. The DTE of the whole tree is the unique tallest column (nuclear
    stress); a terminal that is nobody's superior gets height 1.
    """
    edges = _rppr_edges(tree)
    weaker_than = defaultdict(list)  # id(stronger) -> [weaker leaf, ...]
    for stronger, weaker in edges:
        weaker_than[id(stronger)].append(weaker)

    memo: Dict[int, int] = {}

    def height(lf: LPTree) -> int:
        if id(lf) in memo:
            return memo[id(lf)]
        below = weaker_than.get(id(lf), ())
        memo[id(lf)] = 1 + max((height(w) for w in below), default=0)
        return memo[id(lf)]

    return [height(lf) for lf in tree.leaves()]


def stress_numbers(tree: LPTree) -> List[int]:
    """Terminal stress numbers per L&P's (12) (1 = strongest), surface order.

    - a terminal labelled ``w``: (# nodes dominating it) + 1;
    - a terminal labelled ``s``: (# nodes dominating the lowest ``w`` that
      dominates it) + 1; if no ``w`` dominates it (it is the tree's DTE),
      the count is 0 → stress number 1.

    Provided as an independent cross-check on ``grid_heights``: the two are
    order-inverses (taller grid column ⇔ lower stress number).
    """
    nums: List[int] = []

    def walk(node, ancestors, node_is_weak):
        # ancestors: (node, is_weak) for each node strictly dominating `node`,
        #   root-first; is_weak = "is this node the weak child of its parent".
        # node_is_weak: same, for `node` itself.
        if node.is_leaf:
            if node_is_weak:
                # (# nodes dominating it) + 1
                nums.append(len(ancestors) + 1)
            else:
                # strong (or root-attached) terminal: (# nodes dominating the
                # lowest weak ancestor) + 1; no weak ancestor ⇒ tree DTE ⇒ 1
                weak_idx = [i for i, (_, w) in enumerate(ancestors) if w]
                if weak_idx:
                    # nodes dominating the lowest weak ancestor = its own
                    # ancestors = its index in the root-first list
                    nums.append(weak_idx[-1] + 1)
                else:
                    nums.append(1)
            return
        for child in (node.left, node.right):
            walk(
                child,
                ancestors + [(node, node_is_weak)],
                node.weak_child is child,
            )

    walk(tree, [], False)
    return nums


# ------------------------------------------------------------------ figures
# L&P's own published trees, hand-encoded from the figures, so the engine
# can be checked against their published grid numbers. Terminals are
# syllables in surface order. See tests/test_metrical_lp.py.

def figure_thirteen_men() -> LPTree:
    """(105b): [thirteen[w s]  men]  → grid thir 1, teen 2, men 3."""
    thirteen = ws("thir", "teen")           # thir(w) teen(s)
    return ws(thirteen, "men")              # thirteen(w) men(s)


def figure_montana_cowboy() -> LPTree:
    """(108): Montana [[Mon w tan s] a w]  cowboy [cow s boy w].

    grid: Mon 1, tan 2, a 1, cow 3, boy 1.
    """
    montana = sw(ws("Mon", "tan"), "a")     # [[Mon(w) tan(s)](s) a(w)]
    cowboy = sw("cow", "boy")               # cow(s) boy(w)
    return ws(montana, cowboy)              # Montana(w) cowboy(s)
