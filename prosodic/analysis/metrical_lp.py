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

    __slots__ = ("label", "left", "right", "strong", "lclass", "word_num")

    def __init__(self, label=None, left=None, right=None, strong=None,
                 lclass=None, word_num=None):
        self.label = label
        self.left = left
        self.right = right
        self.strong = strong  # "l" or "r" on internal nodes; None on leaves
        # lexical stress class on leaves (Dozat/MetricalTree): 0 = content,
        # -0.5 = ambiguous function word, -1 = unstressed function word,
        # None = unknown. Drives the L&P (114) grid floor.
        self.lclass = lclass
        # reference word_num on leaves (set by the syntax=True backend so
        # per-word grid values map back to the syllable DataFrame); None else.
        self.word_num = word_num

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
                # prosodic owns sentence segmentation — feed it pre-split units
                # (one prosodic sentence, or one line) and don't re-split, so
                # 1 prosodic sentence = 1 tree, matching the spaCy path exactly.
                tokenize_no_ssplit=True,
                verbose=False,
            )
    return _NLP_CACHE[lang]


# Bump when the pipeline config above changes materially (processors,
# no_ssplit, model) — the cache stores the raw Stanza parse, so changing the
# L&P tree/grid logic on top of it does NOT require a bump.
_STANZA_CACHE_VERSION = "constituency+no_ssplit+depparse-v1"
_STANZA_STASH = None


def _get_stanza_stash():
    """Lazily open a HashStash for serialized Stanza parses, under prosodic's
    cache dir."""
    global _STANZA_STASH
    if _STANZA_STASH is None:
        import os
        from hashstash import HashStash
        from ..imports import PATH_HOME_DATA_CACHE
        _STANZA_STASH = HashStash(
            os.path.join(PATH_HOME_DATA_CACHE, "stanza_constituency"))
    return _STANZA_STASH


def _stanza_parse(texts, lang: str = "en"):
    """Parse a list of texts with the Stanza constituency pipeline, caching
    serialized ``stanza.Document`` objects in a HashStash keyed by
    ``(lang, config-version, text)``. Cache hits reconstruct via
    ``Document.from_serialized`` (~0.5 ms); only misses hit the pipeline, and
    those are batched in one call. Returns one ``Document`` per input text.

    Caching the raw parse (not our L&P trees) means Stanza's expensive
    constituency parse is paid once per unique text ever, while all the
    prosodic-side tree/grid/stress logic still runs fresh on top."""
    import stanza
    stash = _get_stanza_stash()
    out = [None] * len(texts)
    todo = []
    for i, t in enumerate(texts):
        key = (lang, _STANZA_CACHE_VERSION, t)
        if key in stash:
            out[i] = stanza.Document.from_serialized(stash[key])
        else:
            todo.append(i)
    if todo:
        nlp = _get_stanza(lang)
        parsed = nlp([stanza.Document([], text=texts[i]) for i in todo])
        if not isinstance(parsed, list):
            parsed = [parsed]
        for j, i in enumerate(todo):
            out[i] = parsed[j]
            stash[(lang, _STANZA_CACHE_VERSION, texts[i])] = parsed[j].to_serialized()
    return out


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


def _ref_text_spans(raw_tokens: List[str]):
    """Reconstruct prosodic's normalized text and each token's exact span from
    the *unstripped* ``word_txt`` values. prosodic prepends inter-token
    whitespace to each token, so ``"".join(raw_tokens)`` is byte-identical to
    the normalized text it tokenized (``['From',' fairest',',', ...]``), and
    the spans are just cumulative lengths. Exact and deterministic — no
    greedy search, no stored offsets, faithful to real spacing/punctuation."""
    text = ""
    spans = []
    for r in raw_tokens:
        start = len(text)
        text += r
        spans.append((start, len(text)))
    return text, spans


def _word_span(w):
    """Character span of a Stanza word; falls back to its parent token's span
    (multi-word-token expansions — do/n't from don't — have None offsets)."""
    s, e = w.start_char, w.end_char
    if s is None or e is None:
        p = getattr(w, "parent", None)
        if p is not None:
            s, e = p.start_char, p.end_char
    return s, e


def _align_stanza(sent, spans) -> List[int]:
    """Map each Stanza word → reference-token index by max char-span overlap.

    Sub-word Stanza tokens both land in one reference span: ``summer``[2,8]
    and ``'s``[8,10] both map to ``summer's``[2,10]; ``wo``+``n't`` both to
    ``won't``. Returns -1 for a Stanza token overlapping no reference token.
    """
    out = []
    for w in sent.words:
        ws, we = _word_span(w)
        if ws is None or we is None:
            out.append(-1)
            continue
        best, best_ov = -1, 0
        for i, (rs, re) in enumerate(spans):
            ov = min(we, re) - max(ws, rs)
            if ov > best_ov:
                best_ov, best = ov, i
        out.append(best)
    return out


def _build_tok(sent, ref_tokens, ref_ispunc, ref_wordnums, spans, lexical):
    """Per-Stanza-token descriptor: which reference word it belongs to, plus
    that word's text/punct/word_num and this token's lexical class + nominal
    tag. The collapse in :func:`_convert_constituency` keeps the FIRST token
    of each reference word, so its class/nominal (the content-bearing host,
    e.g. ``summer`` in ``summer's``) wins."""
    idx = _align_stanza(sent, spans)
    lcls = _lclass_for_sentence(sent) if lexical else [0.0] * len(sent.words)
    tok = []
    for si, w in enumerate(sent.words):
        ri = idx[si]
        if ri < 0:
            tok.append({"wn": None, "text": w.text, "punct": True,
                        "lclass": 0.0, "nominal": False})
            continue
        tok.append({
            "wn": ref_wordnums[ri],
            "text": ref_tokens[ri],
            "punct": bool(ref_ispunc[ri]),
            "lclass": float(lcls[si]) if si < len(lcls) else 0.0,
            # Compound (CSR) nominality = COMMON nouns only (NN/NNS). Proper
            # nouns modifying a noun are phrasal, not compounds — "Montana
            # cowboy" is [Montana(w) cowboy(s)] (NSR), not left-strong.
            "nominal": (w.xpos or "") in ("NN", "NNS"),
        })
    return tok


def _convert_constituency(node, ctx):
    """Recurse a Stanza constituency ``Tree`` → a node dict, consuming one
    ``ctx['tok']`` descriptor per preterminal in surface order.

    Leaf identity is the *reference* word: contiguous preterminals sharing a
    ``word_num`` (the sub-word pieces of one reference token, e.g. ``summer``
    + ``'s``) collapse to a single leaf labelled with the reference word, so
    ``'s`` / ``n't`` never appear as tree/grid nodes. Punctuation is dropped.
    """
    if node.is_leaf():
        return None
    if _is_preterminal(node):
        i = ctx["i"]
        ctx["i"] += 1
        t = ctx["tok"][i] if i < len(ctx["tok"]) else None
        if t is None or t["punct"]:
            return {"kind": "punct"}
        return {"kind": "word",
                "tree": LPTree(label=t["text"], lclass=t["lclass"],
                               word_num=t["wn"]),
                "nominal": t["nominal"], "wn": t["wn"]}

    kept = []
    for c in node.children:
        if c.is_leaf():
            continue
        r = _convert_constituency(c, ctx)
        if r is None or r["kind"] == "punct":
            continue
        # collapse a sub-word piece sharing the previous kept leaf's word_num
        if (r["kind"] == "word" and r["wn"] is not None and kept
                and kept[-1].get("wn") == r["wn"]):
            continue
        kept.append(r)
    if not kept:
        return {"kind": "punct"}
    if len(kept) == 1:
        return kept[0]
    subs = [(k["tree"], k["nominal"]) for k in kept]
    return {"kind": "word", "tree": _binarize_nsr_csr(subs),
            "nominal": all(k["nominal"] for k in kept), "wn": None}


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


def build_lptree(sent, spans, ref_labels, ref_ispunc, ref_wordnums,
                 lexical=True) -> Optional[LPTree]:
    """Build a binary ``LPTree`` from a parsed Stanza sentence aligned to a
    reference tokenization. ``sent`` must be a Stanza parse of the
    reconstructed normalized text (see :func:`_ref_text_spans`); ``spans`` are
    that text's exact per-token spans; ``ref_labels`` are the stripped token
    strings; Stanza tokens map to reference tokens by char-offset overlap.
    Returns None on an empty parse."""
    tok = _build_tok(sent, ref_labels, ref_ispunc, ref_wordnums, spans, lexical)
    r = _convert_constituency(sent.constituency, {"i": 0, "tok": tok})
    return r["tree"] if r and r.get("kind") == "word" else None


def _prosodic_raw_tokens(text: str):
    """Prosodic's own tokenization of ``text`` → (raw_tokens, is_punc,
    word_nums), in order. ``raw_tokens`` are UNstripped (whitespace-prefixed)
    so :func:`_ref_text_spans` reconstructs the normalized text exactly."""
    import prosodic
    df = prosodic.Text(text)._syll_df
    if df is None or df.empty:
        return [], [], []
    sub = (df[df.form_idx.isin([0, -1])]
           .drop_duplicates("word_num").sort_values("word_num"))
    return ([str(w) for w in sub.word_txt],
            [bool(p) for p in sub.is_punc],
            [int(x) for x in sub.word_num])


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

    Word-level (phrasal) tree; requires stanza + the constituency model. The
    *original* text is handed to Stanza (faithful to its spacing/punctuation);
    prosodic's own tokenization is the reference the tree is built over, so
    clitics (``'s``, ``n't``) collapse into their host word and punctuation is
    dropped. Multi-sentence input uses the first sentence only.
    """
    raw, ref_ispunc, ref_wordnums = _prosodic_raw_tokens(text)
    if not raw:
        return None
    rtext, spans = _ref_text_spans(raw)
    ref_labels = [r.strip() for r in raw]
    doc = _stanza_parse([rtext], lang)[0]
    if not doc.sentences:
        return None
    return build_lptree(doc.sentences[0], spans, ref_labels, ref_ispunc,
                        ref_wordnums, lexical)


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


# ------------------------------------------- syntax=True backend (Phase 4)
# Produce the same four _syll_df columns as the shipping spaCy path
# (phrasal_stress, pstress, tstress, pstrength), but from the faithful L&P
# constituency tree — with tstress defined as the normalized RPPR grid (the
# theoretically-correct gradient for weighting metrical constraints). Opt-in
# via syntax_model="stanza"; spaCy stays the default.

def lp_word_stress(tree: LPTree) -> dict:
    """Per-word phrasal-stress values from a word-level LPTree.

    L&P's two representations, both normalized to [0,1] with 1.0 = nuclear:

    - ``tstress`` (**tree stress**): normalized cumulative stress numbers
      (their eq-12) — fine-grained.
    - ``gstress`` (**grid stress**): normalized RPPR grid height — coarse, the
      representation L&P prefer.

    Plus ``pstress`` (1.0 if the word is the strong child of its parent, a
    local phrasal peak), ``phrasal_stress`` (grid height − max; 0 = nuclear),
    and ``pstrength`` (local peaks/valleys, reuses ``_mt_pstrength``).

    Returns ``{word_num: {phrasal_stress, pstress, tstress, gstress,
    pstrength}}``.
    """
    import numpy as np
    from ..texts.phrasal_stress import _mt_pstrength

    leaves = tree.leaves()
    if not leaves:
        return {}
    heights = grid_heights(tree, lexical_floors(tree))
    maxh, minh = max(heights), min(heights)
    gspan = (maxh - minh) or 1                      # grid stress: min-max
    snums = stress_numbers(tree)                     # 1 = strongest (nuclear)
    smax, smin = max(snums), min(snums)
    sspan = (smax - smin) or 1                        # tree stress: inverted
    strong = set()

    def walk(node):
        if node.is_leaf:
            return
        if node.strong_child.is_leaf:
            strong.add(id(node.strong_child))
        walk(node.left)
        walk(node.right)

    walk(tree)
    ps = np.array([1.0 if id(lf) in strong else 0.0 for lf in leaves])
    pstr = _mt_pstrength(ps, len(leaves))
    out = {}
    for i, lf in enumerate(leaves):
        if lf.word_num is None:
            continue
        out[lf.word_num] = {
            "phrasal_stress": int(heights[i] - maxh),
            "pstress": float(ps[i]),
            "tstress": (smax - snums[i]) / sspan,     # tree stress (cumulative)
            "gstress": (heights[i] - minh) / gspan,   # grid stress (RPPR)
            "pstrength": None if np.isnan(pstr[i]) else float(pstr[i]),
        }
    return out


def _lp_trees_by_sentence(syll_df, lang: str = "en") -> dict:
    """Build faithful ``LPTree``(s) per PROSODIC sentence, keyed by ``sent_num``.

    Grouping by prosodic ``sent_num`` (rather than Stanza's own segmentation)
    matches the spaCy path's scoping, so tstress normalizes over the same
    sentence units and the two engines differ only in the parser. Each prosodic
    sentence is reconstructed from its unstripped tokens (``"".join`` is
    byte-identical to what prosodic tokenized), its newlines flattened to
    spaces (harmless for Stanza, uniform with spaCy), and all sentences are
    batch-parsed (and cached) in one Stanza call. Returns
    ``{sent_num: [LPTree, ...]}`` — usually one tree per sentence, more only
    if Stanza splits it further."""
    wdf = (syll_df[syll_df["form_idx"].isin([0, -1])]
           .drop_duplicates("word_num").sort_values("word_num"))
    texts, metas = [], []
    for sent_num, g in wdf.groupby("sent_num"):
        g = g.sort_values("word_num")
        raw = [str(w) for w in g["word_txt"]]
        rtext, spans = _ref_text_spans(raw)
        rtext = rtext.replace("\n", " ").replace("\r", " ")
        texts.append(rtext)
        metas.append((int(sent_num), spans, [r.strip() for r in raw],
                      [bool(p) for p in g["is_punc"]],
                      [int(x) for x in g["word_num"]]))
    if not texts:
        return {}
    docs = _stanza_parse(texts, lang)
    out = {}
    for doc, (sent_num, spans, labels, isp, wns) in zip(docs, metas):
        trees = []
        for sent in doc.sentences:
            tok = _build_tok(sent, labels, isp, wns, spans, True)
            r = _convert_constituency(sent.constituency, {"i": 0, "tok": tok})
            if r and r.get("kind") == "word":
                trees.append(r["tree"])
        out[sent_num] = trees
    return out


def add_phrasal_stress_stanza(syll_df, text=None, lang: str = "en"):
    """Stanza-constituency backend for ``syntax=True``: write the four
    phrasal-stress columns from the faithful L&P tree, grouped by prosodic
    ``sent_num`` (same sentence units as the spaCy path). ``text`` is unused
    (reconstructed from ``syll_df``). Modifies ``syll_df`` in place."""
    import pandas as pd

    cols_f = ("pstress", "tstress", "gstress", "pstrength")
    if syll_df.empty:
        syll_df["phrasal_stress"] = pd.array([], dtype=pd.Int32Dtype())
        for c in cols_f:
            syll_df[c] = pd.array([], dtype=pd.Float64Dtype())
        return syll_df

    ref_wordnums = [int(x) for x in
                    syll_df[syll_df["form_idx"].isin([0, -1])]
                    .drop_duplicates("word_num")["word_num"]]
    values = {}
    for trees in _lp_trees_by_sentence(syll_df, lang).values():
        for tree in trees:
            values.update(lp_word_stress(tree))

    def col(key):
        return {wn: (values[wn][key] if wn in values else None)
                for wn in ref_wordnums}

    syll_df["phrasal_stress"] = syll_df["word_num"].map(
        col("phrasal_stress")).astype(pd.Int32Dtype())
    for c in cols_f:
        syll_df[c] = syll_df["word_num"].map(col(c)).astype(pd.Float64Dtype())
    return syll_df


def _lptree_to_nltk(tree: LPTree):
    """Convert an ``LPTree`` to an ``nltk.Tree`` — the L&P binary s/w tree.
    Each node is labelled with its metrical role relative to its parent: ``R``
    (root), ``s`` (strong), ``w`` (weak). Word preterminals are labelled
    ``role/tstress`` with tstress the normalized RPPR grid height, so
    ``tree_to_dict`` reads them just like the dependency trees."""
    from nltk.tree import Tree

    heights = grid_heights(tree, lexical_floors(tree))
    maxh, minh = max(heights), min(heights)
    span = (maxh - minh) or 1
    hmap = {id(lf): heights[i] for i, lf in enumerate(tree.leaves())}

    def rec(node, role):
        if node.is_leaf:
            ts = (hmap[id(node)] - minh) / span
            return Tree(f"{role}/{ts}", [node.label])
        lrole = "s" if node.strong == "l" else "w"
        rrole = "s" if node.strong == "r" else "w"
        return Tree(role, [rec(node.left, lrole), rec(node.right, rrole)])

    return rec(tree, "R")


def lp_nltk_trees(syll_df, lang: str = "en"):
    """Faithful L&P binary trees as ``nltk.Tree`` objects — one per sentence,
    grouped by prosodic ``sent_num`` — backing ``text.syntax_trees()`` under
    the stanza engine. ``import svgling`` renders them as SVG s/w trees in a
    notebook. Each tree carries ``_word_nums`` (leaf order) for tree_to_dict."""
    out = []
    by_sent = _lp_trees_by_sentence(syll_df, lang)
    for sent_num in sorted(by_sent):
        for tree in by_sent[sent_num]:
            nt = _lptree_to_nltk(tree)
            nt._word_nums = [lf.word_num for lf in tree.leaves()]
            out.append(nt)
    return out
