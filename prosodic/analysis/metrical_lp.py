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


# Penn/Stanza punctuation preterminal tags — dropped, never metrical terminals
_PUNCT_TAGS = frozenset({
    ",", ".", ":", ";", "``", "''", "\"", "'", "-LRB-", "-RRB-", "-LSB-",
    "-RSB-", "-LCB-", "-RCB-", "HYPH", "NFP", "SYM", "$", "#",
})


def _is_punct_tag(tag: str) -> bool:
    return tag in _PUNCT_TAGS or not any(c.isalnum() for c in tag)


def _convert_constituency(node, ctx) -> Optional[tuple]:
    """Recurse a Stanza constituency ``Tree`` → ``(LPTree, is_nominal, kind)``.

    ``ctx`` = ``{'i': int, 'lclass': [...]}`` consumes one token per
    preterminal in surface order (constituency leaves == ``sent.words``),
    so each word leaf gets its lexical class without a fragile post-hoc
    alignment. ``kind`` ∈ {'word','punct','clitic'}:

    - punctuation preterminals are dropped (never metrical terminals — fixes
      commas being handed nuclear stress);
    - the possessive clitic ``'s`` (POS tag ``POS``) is merged onto its host
      word's last syllable rather than standing as its own NSR-strong
      terminal (fixes *summer 's* with stress landing on *'s*).
    """
    if node.is_leaf():
        return LPTree(label=node.label), False, "word"
    if _is_preterminal(node):
        tag = node.label
        word = list(node.children)[0].label
        i = ctx["i"]
        ctx["i"] += 1
        if _is_punct_tag(tag):
            return None, False, "punct"
        if tag == "POS":
            return LPTree(label=word), False, "clitic"
        cls = ctx["lclass"][i] if i < len(ctx["lclass"]) else 0.0
        # Compound (CSR) nominality = COMMON nouns only. Proper nouns (NNP)
        # modifying a noun are phrasal, not compounds — "Montana cowboy" is
        # [Montana(w) cowboy(s)] (NSR), not a left-strong compound.
        return LPTree(label=word, lclass=cls), tag in ("NN", "NNS"), "word"

    raw = [_convert_constituency(c, ctx) for c in node.children if not c.is_leaf()]
    cleaned: List[list] = []
    for tree, nom, kind in raw:
        if kind == "punct" or tree is None:
            continue
        if kind == "clitic":
            if cleaned:  # attach 's to the host's last syllable
                host = cleaned[-1][0]
                host.leaves()[-1].label += tree.label
            continue
        cleaned.append([tree, nom, kind])
    if not cleaned:
        return None, False, "punct"
    if len(cleaned) == 1:
        return cleaned[0][0], cleaned[0][1], "word"
    subs = [(t, n) for t, n, _ in cleaned]
    return _binarize_nsr_csr(subs), all(n for _, n in subs), "word"


def _lclass_for_sentence(sent) -> list:
    """Per-token lexical stress class (0 / -0.5 / -1) in surface order."""
    import numpy as np
    from ..texts.phrasal_stress import _mt_lstress_base

    words = list(sent.words)
    return list(_mt_lstress_base(
        np.array([w.text for w in words]),
        np.array([w.xpos or "" for w in words]),
        np.array([w.deprel or "" for w in words]),
        len(words),
    ))


def constituency_to_lptree(stanza_constituency, lclass=None) -> Optional[LPTree]:
    """Convert one Stanza ``sent.constituency`` tree to a binary ``LPTree``.

    Leaves are words (punctuation dropped, possessive ``'s`` merged).
    ``lclass`` is an optional per-token lexical-class list. Returns None on
    an empty parse.
    """
    ctx = {"i": 0, "lclass": lclass or []}
    result = _convert_constituency(stanza_constituency, ctx)
    return result[0] if result else None


_STRESS_NUM = {"P": 1.0, "S": 0.5, "U": 0.0}


def _word_syllable_tree(sylls: List[tuple]) -> LPTree:
    """Within-word binary metrical tree from syllables (Phase 2b).

    ``sylls`` is ``[(text, stress_num)]`` with stress_num 1.0 (P) / 0.5 (S) /
    0.0 (U). Builds L&P-style feet: each stressed syllable heads a
    left-branching foot ``[s w w …]`` (head + following unstressed); the
    primary foot (rightmost max-stress head) is the word's DTE, absorbing
    the feet to its right as weak (``[s w]``) and to its left as weak
    (``[w s]``); leading unstressed syllables adjoin weak on the left.

    Reproduces L&P's own word grids: *thirteen* → thir 1 · teen 2;
    *execute* (116a) → ex 2 · e 1 · cute 1; *Tennessee* → Ten 2 · nes 1 ·
    see 3 (secondary Ten sits between unstressed and primary).
    """
    if len(sylls) == 1:
        return LPTree(label=sylls[0][0])
    heads = [i for i, (_, sn) in enumerate(sylls) if sn > 0]
    if not heads:  # unstressed word (rare); left-branching, first = DTE
        t = LPTree(label=sylls[0][0])
        for txt, _ in sylls[1:]:
            t = sw(t, txt)
        return t
    feet, foot_head = [], []
    for hi, h in enumerate(heads):
        end = heads[hi + 1] if hi + 1 < len(heads) else len(sylls)
        foot = LPTree(label=sylls[h][0])
        for txt, _ in sylls[h + 1:end]:
            foot = sw(foot, txt)            # head strong, following weak
        feet.append(foot)
        foot_head.append(h)
    maxsn = max(sn for _, sn in sylls)
    prim = max(i for i, h in enumerate(foot_head) if sylls[h][1] == maxsn)
    tree = feet[prim]
    for f in feet[prim + 1:]:
        tree = sw(tree, f)                  # primary strong-left over right feet
    for f in reversed(feet[:prim]):
        tree = ws(f, tree)                  # primary strong-right over left feet
    for txt, _ in reversed(sylls[:heads[0]]):
        tree = ws(LPTree(label=txt), tree)  # leading unstressed, weak-left
    return tree


_SYLL_CACHE: dict = {}


def _prosodic_sylls(word: str) -> Optional[List[tuple]]:
    """Syllables + stress numbers for a word, via prosodic's own pronunciation.

    Returns ``[(syll_text, stress_num)]`` or None. Cached per word.
    """
    key = word.lower()
    if key in _SYLL_CACHE:
        return _SYLL_CACHE[key]
    result = None
    try:
        import prosodic
        line = prosodic.Text(word).lines[0]
        if line.wordtokens:
            form = line.wordtokens[0].wordform
            result = [
                (s.txt, _STRESS_NUM.get(getattr(s, "stress", "U"), 0.0))
                for s in form.syllables
            ]
            if not result:
                result = None
    except Exception:
        result = None
    _SYLL_CACHE[key] = result
    return result


def expand_to_syllables(tree: LPTree, syll_fn=None) -> LPTree:
    """Graft each word-leaf's within-word syllable tree onto the phrasal tree.

    ``syll_fn(word) -> [(syll, stress_num)]`` supplies pronunciations
    (defaults to prosodic's). A word-leaf's ``lclass`` is carried onto every
    syllable leaf of its subtree, so the lexical (114) floor still applies.
    The result is one binary tree over syllables; feed it to ``grid_heights``.
    """
    if syll_fn is None:
        syll_fn = _prosodic_sylls

    def rec(node):
        if node.is_leaf:
            sylls = syll_fn(node.label)
            if not sylls:
                return node
            sub = _word_syllable_tree(sylls)
            # L&P (114) is a per-word provision: the content-word minimum
            # attaches to the word's DTE (its primary syllable), not to every
            # syllable. Other syllables stay lexically unmarked (floor 1).
            sub.dte.lclass = node.lclass
            return sub
        return LPTree(left=rec(node.left), right=rec(node.right),
                      strong=node.strong)

    return rec(tree)


def parse_lptree(text: str, lang: str = "en", lexical: bool = True) -> Optional[LPTree]:
    """Parse ``text`` with Stanza and return its L&P metrical tree.

    Word-level (phrasal) tree; requires stanza + the constituency model.
    With ``lexical=True`` (default) each word leaf is tagged with its lexical
    stress class during conversion (see :func:`lexical_floors`). Punctuation
    is dropped and the possessive ``'s`` merged into its host.
    """
    nlp = _get_stanza(lang)
    doc = nlp(text)
    if not doc.sentences:
        return None
    sent = doc.sentences[0]
    lclass = _lclass_for_sentence(sent) if lexical else None
    return constituency_to_lptree(sent.constituency, lclass=lclass)


# ------------------------------------------------- web serialization (Phase 3)

def _lptree_to_json(node: LPTree, role: Optional[str], heights: dict) -> dict:
    """Binary tree → nested JSON preserving left/right order and s/w roles.

    ``role`` is the node's role in its parent ("s"/"w"; None at the root R).
    Leaves carry their grid ``height``. Because the L&P tree is binary, every
    edge has a genuine s/w label — the thing a dependency projection cannot
    provide.
    """
    if node.is_leaf:
        return {
            "text": node.label, "role": role, "height": heights.get(id(node)),
            "is_function": node.lclass in (-1.0, -0.5),
            "children": [],
        }
    lrole = "s" if node.strong == "l" else "w"
    rrole = "s" if node.strong == "r" else "w"
    return {
        "text": None, "role": role, "height": None, "is_function": False,
        "children": [
            _lptree_to_json(node.left, lrole, heights),
            _lptree_to_json(node.right, rrole, heights),
        ],
    }


def lp_line_data(text: str, lang: str = "en") -> Optional[dict]:
    """Full faithful-L&P analysis of one line, JSON-ready for the web view.

    Returns ``{grid, tree, nuclear, max_height}`` or None if unparsable /
    stanza unavailable. ``grid`` is one row per syllable in surface order
    (``txt``, ``height``, ``is_function``, ``nuclear``, ``word_num``);
    ``tree`` is the binary metrical tree with s/w edge roles and syllable
    leaves. Heights already include the L&P (114) lexical floor.
    """
    phrasal = parse_lptree(text, lang=lang)
    if phrasal is None:
        return None
    tree = expand_to_syllables(phrasal)
    leaves = tree.leaves()
    if not leaves:
        return None
    heights_list = grid_heights(tree, lexical_floors(tree))
    heights = {id(lf): h for lf, h in zip(leaves, heights_list)}
    dte = tree.dte
    # word_num: group syllables by contiguous runs that came from one word —
    # a new run starts at each foot whose leftmost descends from a word DTE.
    # Simpler + robust: number by the phrasal leaf order isn't recoverable
    # post-graft, so bucket syllables into words by re-deriving from surface
    # contiguity is unreliable; expose per-syllable only (word_num omitted).
    grid = [
        {
            "txt": lf.label,
            "height": heights[id(lf)],
            "is_function": lf.lclass in (-1.0, -0.5),
            "nuclear": lf is dte,
        }
        for lf in leaves
    ]
    return {
        "grid": grid,
        "tree": _lptree_to_json(tree, None, heights),
        "nuclear": dte.label,
        "max_height": max(heights_list),
    }
