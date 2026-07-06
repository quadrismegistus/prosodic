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

    __slots__ = ("label", "left", "right", "strong", "lclass")

    def __init__(self, label=None, left=None, right=None, strong=None,
                 lclass=None):
        self.label = label
        self.left = left
        self.right = right
        self.strong = strong  # "l" or "r" on internal nodes; None on leaves
        # lexical stress class on leaves (Dozat/MetricalTree): 0 = content,
        # -0.5 = ambiguous function word, -1 = unstressed function word,
        # None = unknown. Drives the L&P (114) grid floor.
        self.lclass = lclass

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


def grid_heights(tree: LPTree, floors=None) -> List[int]:
    """Grid column height per terminal, in surface order.

    The minimal metrical grid satisfying the RPPR: a terminal's height is
    1 + the longest descending chain of 'stronger-than' relations beneath
    it. The DTE of the whole tree is the unique tallest column (nuclear
    stress); a terminal that is nobody's superior gets height 1.

    ``floors`` optionally maps ``id(leaf) -> minimum height`` — this is how
    L&P's (114) provision enters (content words guaranteed ≥ 2 levels, even
    when structurally weak; unstressed function words left at 1). A floor
    only raises a column, and because superiors are computed as
    ``1 + max(below)``, a raised weak terminal correctly pushes its strong
    relatives up too, so the RPPR still holds. See :func:`lexical_floors`.
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
        base = 1 + max((height(w) for w in below), default=0)
        floor = floors.get(id(lf), 1) if floors else 1
        memo[id(lf)] = max(base, floor)
        return memo[id(lf)]

    return [height(lf) for lf in tree.leaves()]


# L&P (114): a #-level lexical unit (content word) gets ≥ 2 grid levels;
# unstressed/ambiguous function words are left at the structural floor of 1.
CONTENT_FLOOR = 2
FUNCTION_FLOOR = 1


def lexical_floors(tree: LPTree) -> Dict[int, int]:
    """Per-leaf grid floor from lexical class — L&P's (114) provision.

    Content leaves (``lclass == 0``) floor at 2; function words (ambiguous
    or unstressed) and unknowns floor at 1. Feed the result to
    :func:`grid_heights` as ``floors``.
    """
    return {
        id(lf): (CONTENT_FLOOR if lf.lclass == 0 else FUNCTION_FLOOR)
        for lf in tree.leaves()
    }


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


# ---------------------------------------------------- constituency → LPTree
# Phase 1: derive the phrasal binary metrical tree from a real constituency
# parse (Stanza), binarizing per L&P's NSR/CSR. Leaves are WORDS; word-internal
# syllable structure (Phase 2) grafts on separately. Stanza is imported lazily
# (heavy, optional). Trees from Stanza are n-ary (flat NPs), so the work here
# is faithful binarization: right-branching + [w s] (NSR) for phrases,
# left-branching + [s w] (CSR) for maximal adjacent-noun compound runs.

_NLP_CACHE: dict = {}


def _get_stanza(lang: str = "en"):
    """Lazily build/cache a Stanza constituency pipeline."""
    if lang not in _NLP_CACHE:
        import warnings
        import stanza
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _NLP_CACHE[lang] = stanza.Pipeline(
                lang,
                processors="tokenize,pos,lemma,constituency,depparse",
                verbose=False,
            )
    return _NLP_CACHE[lang]


def _is_preterminal(node) -> bool:
    ch = list(node.children)
    return len(ch) == 1 and ch[0].is_leaf()


def _binarize_nsr_csr(subs: List[tuple]) -> LPTree:
    """Binarize a node's children per L&P's NSR/CSR.

    ``subs`` is a list of ``(LPTree, is_nominal)``. Two regimes, keyed off
    whether the whole node is nominal (all children nominal — a compound in
    the L&P sense, whatever Penn label Stanza happened to assign):

    - **Compound** (all children nominal): left-branching, each node ``[s w]``.
      Leftmost is the DTE — *LAW degree requirement*, *KITCHEN towel rack*
      (CSR; nested all-noun structures percolate left-strength).
    - **Phrasal** (otherwise): maximal runs of ≥2 adjacent nominal children
      collapse into left-strong compounds first (so a flat ``JJ NN NN`` still
      gets *history teacher* as a unit), then the groups combine
      right-branching under ``[w s]`` — the rightmost is strong (NSR).
    """
    if all(nom for _, nom in subs):
        node = subs[0][0]
        for t, _ in subs[1:]:
            node = sw(node, t)              # left-strong compound
        return node

    groups: List[LPTree] = []
    i = 0
    while i < len(subs):
        j = i
        while j < len(subs) and subs[j][1]:
            j += 1
        if j - i >= 2:                      # adjacent nominal run → compound
            comp = subs[i][0]
            for t, _ in subs[i + 1:j]:
                comp = sw(comp, t)
            groups.append(comp)
            i = j
        else:
            groups.append(subs[i][0])
            i += 1
    node = groups[-1]
    for t in reversed(groups[:-1]):
        node = ws(t, node)                  # [w s], NSR rightmost strong
    return node


def _convert_constituency(node) -> Optional[tuple]:
    """Recurse a Stanza constituency ``Tree`` → ``(LPTree, is_nominal)``.

    Preterminals become word leaves (nominal iff POS starts ``NN``); unary
    nodes collapse; branching nodes binarize via :func:`_binarize_nsr_csr`
    and are nominal iff every child is nominal.
    """
    if node.is_leaf():
        return LPTree(label=node.label), False
    if _is_preterminal(node):
        word = list(node.children)[0].label
        return LPTree(label=word), node.label.startswith("NN")
    subs = [_convert_constituency(c) for c in node.children if not c.is_leaf()]
    subs = [s for s in subs if s is not None]
    if not subs:
        return None
    if len(subs) == 1:
        return subs[0]
    tree = _binarize_nsr_csr(subs)
    return tree, all(nom for _, nom in subs)


def constituency_to_lptree(stanza_constituency) -> Optional[LPTree]:
    """Convert one Stanza ``sent.constituency`` tree to a binary ``LPTree``.

    Leaves are words. Returns None on an empty parse.
    """
    result = _convert_constituency(stanza_constituency)
    return result[0] if result else None


def _attach_lexical_classes(tree: LPTree, sent) -> None:
    """Tag each word-leaf with its lexical stress class from a Stanza sentence.

    Uses ``_mt_lstress_base`` (the shipping MetricalTree port's classifier:
    word list → POS tag → dep label, giving 0 / -0.5 / -1). Leaves and
    ``sent.words`` are both in surface order; if they don't align 1:1
    (rare tokenization mismatch) lexical classes are left as None and the
    grid falls back to structural heights.
    """
    import numpy as np
    from ..texts.phrasal_stress import _mt_lstress_base

    leaves = tree.leaves()
    words = list(sent.words)
    if len(leaves) != len(words):
        return
    texts = np.array([w.text for w in words])
    tags = np.array([w.xpos or "" for w in words])
    deps = np.array([w.deprel or "" for w in words])
    lstress = _mt_lstress_base(texts, tags, deps, len(words))
    for lf, cls in zip(leaves, lstress):
        lf.lclass = float(cls)


def parse_lptree(text: str, lang: str = "en", lexical: bool = True) -> Optional[LPTree]:
    """Parse ``text`` with Stanza and return its L&P metrical tree.

    Word-level (phrasal) tree; requires stanza + the constituency model.
    With ``lexical=True`` (default) each leaf is tagged with its lexical
    stress class (see :func:`lexical_floors` for how that reaches the grid).
    """
    nlp = _get_stanza(lang)
    doc = nlp(text)
    if not doc.sentences:
        return None
    sent = doc.sentences[0]
    tree = constituency_to_lptree(sent.constituency)
    if tree is not None and lexical:
        _attach_lexical_classes(tree, sent)
    return tree
