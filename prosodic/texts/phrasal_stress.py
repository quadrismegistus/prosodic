"""Compute phrasal stress from dependency parse (Liberman & Prince 1977).

Uses spaCy dependency parsing to assign prominence levels per word.

Two computations share the parse:

1. ``phrasal_stress`` (discrete, original v3): vectorized depth in the dep
   tree with NSR/CSR adjustments. 0 = sentence root, negative = embedded.

2. ``pstress``/``tstress`` (gradient, MetricalTree port): Dozat's (2015)
   metrical-tree algorithm — as used by Anttila et al. and cadence — run
   over head-projection trees derived from the dependency parse instead of
   constituency parses. Lexical stress classes (content 0 / ambiguous
   function word -0.5 / unstressed function word -1) are resolved three
   ways (all stressed; monosyllables unstressed; all unstressed), the NSR
   assigns strong/weak within each projection (with Dozat's noun-compound
   rule keyed off the ``compound`` dep relation), total stress accumulates
   down the tree, the ensemble is averaged, and each sentence is min-max
   normalized: 1.0 = nuclear stress, 0.0 = least prominent, NaN = punct.

   Cross-validated against cadence's MetricalTree (Stanza constituency) on
   a 9-sentence differential (2026-07-05): identical nuclear placement and
   orderings throughout. One deliberate divergence: in coordination
   ("dogs and cats"), Dozat's flat-NP scan demotes non-final conjuncts to
   pstress -1; here each conjunct projects and keeps its strength (both
   conjuncts carry accent in speech), while tstress still orders the final
   conjunct above the first, matching the reference.
"""

import numpy as np
import pandas as pd

# POS tags for content words (Universal POS)
CONTENT_UPOS = frozenset({'NOUN', 'VERB', 'ADJ', 'ADV', 'PROPN', 'INTJ', 'NUM'})

# spaCy xpos tags for noun compounds (CSR)
NN_XPOS = frozenset({'NN', 'NNS', 'NNP', 'NNPS'})

# ---- MetricalTree lexical stress classes (Dozat 2015, PTB tags) ----
MT_UNSTRESSED_WORDS = frozenset({'it'})
MT_UNSTRESSED_TAGS = frozenset({'CC', 'PRP$', 'TO', 'UH', 'DT'})
MT_UNSTRESSED_DEPS = frozenset({'det', 'expl', 'cc', 'mark'})
MT_AMBIGUOUS_WORDS = frozenset({'this', 'that', 'these', 'those'})
MT_AMBIGUOUS_TAGS = frozenset({'MD', 'IN', 'PRP', 'WP$', 'PDT', 'WDT', 'WP', 'WRB'})
MT_AMBIGUOUS_DEPS = frozenset({'cop', 'neg', 'aux', 'auxpass'})

_NLP_CACHE = {}


def _get_nlp(model="en_core_web_sm"):
    """Load spaCy model, lazy + cached. Disable unused components."""
    if model not in _NLP_CACHE:
        try:
            import spacy
        except ImportError:
            raise ImportError(
                "spacy is required for syntax=True. "
                "Install with: pip install spacy && python -m spacy download en_core_web_sm"
            )
        try:
            nlp = spacy.load(model, disable=["ner", "lemmatizer"])
        except OSError:
            raise OSError(
                f"spaCy model '{model}' not found. "
                f"Install with: python -m spacy download {model}"
            )
        _NLP_CACHE[model] = nlp
    return _NLP_CACHE[model]


def _compute_depth(heads, n):
    """Vectorized depth computation. Converges in O(max_depth) iterations."""
    depth = np.zeros(n, dtype=np.int32)
    current = heads.copy()
    mask = current >= 0
    while mask.any():
        depth[mask] += 1
        current[mask] = heads[current[mask]]
        mask = current >= 0
    return depth


def _compute_phrasal_stress(heads, pos, xpos, n):
    """Compute L&P phrasal stress from dependency arrays.

    Args:
        heads: int array, head index per word (-1 = root)
        pos: str array, universal POS tags
        xpos: str array, language-specific POS tags
        n: number of words

    Returns:
        int array of phrasal stress values (0 = most prominent, negative = demoted)
    """
    depth = _compute_depth(heads, n)

    # Base prominence = negative depth (root=0, deeper=more negative)
    stress = -depth.astype(np.int32)

    # NSR: among siblings (same head), rightmost content word gets +1
    # CSR: among NN siblings in same NP, leftmost NN gets +1 instead
    is_content = np.array([p in CONTENT_UPOS for p in pos])
    is_nn = np.array([p in NN_XPOS for p in xpos])

    for h in range(n):
        siblings = np.where(heads == h)[0]
        if len(siblings) < 2:
            continue

        # CSR: check for NN compound (2+ adjacent NN siblings)
        nn_sibs = siblings[is_nn[siblings]]
        if len(nn_sibs) >= 2:
            # leftmost NN gets the promotion (compound stress rule)
            stress[nn_sibs[0]] += 1
            continue

        # NSR: rightmost content-word sibling gets promotion
        content_sibs = siblings[is_content[siblings]]
        if len(content_sibs) >= 2:
            stress[content_sibs[-1]] += 1

    return stress


def _mt_lstress_base(words, tags, deps, n):
    """Base lexical stress per word: 0 / -0.5 (ambiguous) / -1 (unstressed).

    Priority follows Dozat's MetricalTree: word lists beat tag lists beat
    dep lists. (Punctuation never reaches here; it's filtered upstream.)
    """
    lstress = np.zeros(n)
    for i in range(n):
        w = words[i].lower().strip()
        if w in MT_UNSTRESSED_WORDS:
            lstress[i] = -1
        elif w in MT_AMBIGUOUS_WORDS:
            lstress[i] = -0.5
        elif tags[i] in MT_UNSTRESSED_TAGS:
            lstress[i] = -1
        elif tags[i] in MT_AMBIGUOUS_TAGS:
            lstress[i] = -0.5
        elif deps[i] in MT_UNSTRESSED_DEPS:
            lstress[i] = -1
        elif deps[i] in MT_AMBIGUOUS_DEPS:
            lstress[i] = -0.5
    return lstress


class _MTNode:
    """Phrase node in the dep-projection tree. children: ('pre', word_i) or
    ('node', _MTNode), ordered by linear position."""
    __slots__ = ('cat', 'children', 'p', 'total')

    def __init__(self, cat, children):
        self.cat = cat
        self.children = children
        self.p = 0.0      # phrasal stress of this node
        self.total = 0.0  # cumulative stress (set top-down)


# Dependents that sit as bare preterminals inside their head's phrase, like
# the flat Penn NP (NP (DT the) (JJ quick) (NN fox)). Everything else — even
# a single-word subject or object — projects its own phrase node, the way
# constituency wraps arguments (NP(Jack), WHADVP(When)), which shields the
# preterminal from sibling NSR demotion.
# NOTE: 'poss' deliberately absent — a possessor is an inner NP in
# constituency (NP(NP(Beauty 's) rose)), so it must project; bare-joining
# it as an NN sibling would wrongly trigger the compound rule
# (BEAUTY'S rose instead of beauty's ROSE).
MT_BARE_DEPS = frozenset({
    'det', 'amod', 'compound', 'nummod', 'predet',
    'neg', 'aux', 'auxpass',
})


def _mt_project(h, deps_of, tags, deps):
    """Project word h's phrase, constituency-style.

    Topology rules keep Dozat's NSR faithful to what it does on
    constituency trees (verified differentially against cadence):

    - NP-internal prenominal modifiers (det/amod/compound/...) join as bare
      preterminals — NSR demotion reaches them directly, as in a flat NP.
    - All other dependents project a phrase node even when single words
      (constituency wraps arguments: NP(Jack)), shielding their preterminal.
    - An NN-headed phrase with right-side dependents wraps its left
      material + head in an inner core — NP(NP(the house) SBAR) — so the
      head noun's preterminal is shielded from the complement's NSR win.
    """
    left = [d for d in deps_of[h] if d < h]
    right = [d for d in deps_of[h] if d > h]

    def child_of(d):
        if not deps_of[d] and deps[d] in MT_BARE_DEPS:
            return ('pre', d)
        return ('node', _mt_project(d, deps_of, tags, deps))

    inner = [child_of(d) for d in left] + [('pre', h)]
    right_children = [child_of(d) for d in right]
    if right_children and tags[h].startswith('NN'):
        core = _MTNode(tags[h], inner)
        return _MTNode(tags[h], [('node', core)] + right_children)
    return _MTNode(tags[h], inner + right_children)


def _mt_variant(heads, tags, deps, lstress, n):
    """One disambiguated MetricalTree pass over the dep-projection tree.

    ``lstress`` must already be resolved to {0, -1}.

    Returns (pstress, tstress): per-word preterminal phrasal stress
    ({0, -1}) and cumulative total stress (Dozat's set_stress).
    """
    deps_of = [[] for _ in range(n)]
    roots = []
    for i in range(n):
        h = heads[i]
        (deps_of[h] if h >= 0 else roots).append(i)

    pre_p = lstress.astype(float).copy()  # preterminal pstress
    trees = [_mt_project(r, deps_of, tags, deps) for r in roots]

    def child_p(kind, c):
        return pre_p[c] if kind == 'pre' else c.p

    def set_child_p(kind, c, v):
        if kind == 'pre':
            pre_p[c] = v
        else:
            c.p = v

    def set_pstress(node):
        for kind, c in node.children:
            if kind == 'node':
                set_pstress(c)
        children = node.children
        assigned = False
        # Dozat's noun-compound rule: within an NN-headed phrase, scanning
        # right-to-left, the rightmost NN preterminal is provisionally weak
        # and the next NN is strong: TIME machine, not time MACHINE. A
        # single NN gets its strength back at the first non-NN sibling.
        if node.cat.startswith('NN'):
            skip = None
            broke = False
            for ci in range(len(children) - 1, -1, -1):
                kind, c = children[ci]
                is_nn = kind == 'pre' and tags[c].startswith('NN')
                if is_nn:
                    if not assigned and skip is None:
                        skip = ci
                        set_child_p(kind, c, -1)
                    elif not assigned:
                        set_child_p(kind, c, 0)
                        assigned = True
                    else:
                        set_child_p(kind, c, -1)
                elif assigned:
                    set_child_p(kind, c, -1)
                else:
                    if skip is not None:
                        sk, sc = children[skip]
                        set_child_p(sk, sc, 0)
                        assigned = True
                        set_child_p(kind, c, -1)
                    else:
                        broke = True
                        break
            if not assigned and not broke and skip is not None:
                sk, sc = children[skip]
                set_child_p(sk, sc, 0)
                assigned = True
        # Standard NSR: rightmost child with pstress 0 is strong; all other
        # children are demoted to -1.
        if not assigned:
            for ci in range(len(children) - 1, -1, -1):
                kind, c = children[ci]
                if not assigned and child_p(kind, c) == 0:
                    assigned = True
                else:
                    set_child_p(kind, c, -1)
        node.p = 0 if assigned else -1

    tstress = np.zeros(n)

    def set_stress(node, acc):
        node.total = node.p + acc
        for kind, c in node.children:
            if kind == 'pre':
                tstress[c] = lstress[c] + pre_p[c] + node.total
            else:
                set_stress(c, node.total)

    for tree in trees:
        set_pstress(tree)
        set_stress(tree, 0.0)
    return pre_p, tstress


def _mt_pstrength(pstress, n):
    """Local phrasal peaks/valleys over adjacent words (cadence's
    set_phrasal_peaks): where a word's pstress exceeds an adjacent
    neighbor's, the word is a peak (1.0) and the neighbor a valley (0.0).
    Words that are neither stay NaN. Comparisons on the ensemble-mean
    pstress; only ordering matters, so normalization is irrelevant."""
    ps = np.full(n, np.nan)
    for i in range(n):
        if np.isnan(pstress[i]):
            continue
        for j in (i - 1, i + 1):
            if 0 <= j < n and not np.isnan(pstress[j]) and pstress[j] < pstress[i]:
                ps[j] = 0.0
                ps[i] = 1.0
    return ps


def _mt_gradient(heads, words, tags, deps, nsylls, n):
    """Ensemble-averaged, min-max normalized MetricalTree stress.

    Runs Dozat's three disambiguations of ambiguous (-0.5) words — all
    stressed; monosyllables unstressed; all unstressed — averages
    pstress/tstress across them, and normalizes each within the sentence.

    Returns (pstress_norm, tstress_norm, pstrength). The first two are in
    [0, 1]; 1 = most prominent; sentences with no variation normalize to
    NaN (as in cadence/mtree). pstrength is 1.0 (local peak), 0.0 (local
    valley), or NaN (neither).
    """
    base = _mt_lstress_base(words, tags, deps, n)
    amb = base == -0.5
    variants = []
    for resolve in ('max', 'min_syll', 'min'):
        lstress = base.copy()
        if resolve == 'max':
            lstress[amb] = 0
        elif resolve == 'min_syll':
            lstress[amb & (nsylls == 1)] = -1
            lstress[amb & (nsylls != 1)] = 0
        else:
            lstress[amb] = -1
        variants.append(_mt_variant(heads, tags, deps, lstress, n))

    pstress = np.mean([v[0] for v in variants], axis=0)
    tstress = np.mean([v[1] for v in variants], axis=0)
    pstrength = _mt_pstrength(pstress, n)

    def norm(v):
        vmin, vmax = float(v.min()), float(v.max())
        if vmax == vmin:
            return np.full(n, np.nan)
        return (v - vmin) / (vmax - vmin)

    return norm(pstress), norm(tstress), pstrength


# Readable phrase labels for projected nodes (fallback: TAG + "P")
_PHRASE_LABELS = (
    ('NN', 'NP'), ('VB', 'VP'), ('JJ', 'ADJP'), ('RB', 'ADVP'),
    ('IN', 'PP'), ('CD', 'QP'), ('PRP', 'NP'), ('DT', 'NP'),
    ('W', 'WHP'), ('MD', 'VP'),
)


def _phrase_label(tag):
    for prefix, label in _PHRASE_LABELS:
        if tag.startswith(prefix):
            return label
    return tag + 'P'


def _mt_nltk_trees(heads, words, tags, deps, tstress=None):
    """One nltk.Tree per dependency root, mirroring the projection topology
    the stress computation runs on (``_mt_project``) — the rendered tree IS
    the tree the pstress/tstress numbers came from. Preterminal labels are
    the PTB tag, suffixed with the word's tstress when provided
    (``NN/0.75``); phrase labels are constituency-style (NP/VP/...).
    """
    from nltk.tree import Tree

    n = len(words)
    deps_of = [[] for _ in range(n)]
    roots = []
    for i in range(n):
        h = heads[i]
        (deps_of[h] if h >= 0 else roots).append(i)

    def convert(node):
        kids = []
        for kind, c in node.children:
            if kind == 'pre':
                label = tags[c]
                if tstress is not None and not np.isnan(tstress[c]):
                    label += f"/{tstress[c]:.2f}"
                kids.append(Tree(label, [words[c]]))
            else:
                kids.append(convert(c))
        return Tree(_phrase_label(node.cat), kids)

    return [convert(_mt_project(r, deps_of, tags, deps)) for r in roots]


def syntax_trees(text, model="en_core_web_sm"):
    """nltk.Tree projections for every sentence of a text.

    Returns a flat list of ``nltk.tree.Tree`` (usually one per sentence),
    with preterminals labeled ``TAG/tstress``. In a Jupyter notebook,
    ``pip install svgling`` + ``import svgling`` makes these render as
    SVG trees automatically; ``print(tree)`` gives the bracketed form.
    """
    from spacy.tokens import Doc
    nlp = _get_nlp(model)
    syll_df = text._syll_df
    word_df = syll_df[syll_df['form_idx'].isin([0, -1])].drop_duplicates('word_num')
    nsyll_by_word = (
        syll_df[(syll_df['form_idx'] == 0) & (~syll_df['is_punc'])]
        .groupby('word_num').size().to_dict()
    )

    docs, doc_meta = [], []
    for sent_num, group in word_df.groupby('sent_num'):
        mask = ~group['is_punc'].values.astype(bool)
        parse_words = [w.strip() for w in group['word_txt'].values[mask]]
        if not parse_words:
            continue
        spaces = [True] * len(parse_words)
        spaces[-1] = False
        docs.append(Doc(nlp.vocab, words=parse_words, spaces=spaces))
        doc_meta.append(group['word_num'].values[mask])

    trees = []
    for doc, word_nums in zip(nlp.pipe(docs), doc_meta):
        n = len(doc)
        heads = np.array([
            tok.head.i if tok.head.i != tok.i else -1 for tok in doc
        ], dtype=np.int32)
        tags = np.array([tok.tag_ for tok in doc])
        deps = np.array([tok.dep_ for tok in doc])
        words = np.array([tok.text for tok in doc])
        nsylls = np.array([nsyll_by_word.get(wn, 1) for wn in word_nums],
                          dtype=np.int32)
        _, tstress, _ = _mt_gradient(heads, words, tags, deps, nsylls, n)
        trees.extend(_mt_nltk_trees(heads, words, tags, deps, tstress))
    return trees


def add_phrasal_stress(syll_df, model="en_core_web_sm"):
    """Add phrasal_stress column to syll_df.

    Groups words by sentence, runs spaCy dep parsing, computes L&P
    phrasal stress, and broadcasts word-level values to syllable rows.

    Args:
        syll_df: DataFrame with word_num, sent_num, word_txt, is_punc columns
        model: spaCy model name

    Returns:
        syll_df with phrasal_stress column added (modified in place)
    """
    if syll_df.empty:
        syll_df['phrasal_stress'] = pd.array([], dtype=pd.Int32Dtype())
        syll_df['pstress'] = pd.array([], dtype=pd.Float64Dtype())
        syll_df['tstress'] = pd.array([], dtype=pd.Float64Dtype())
        syll_df['pstrength'] = pd.array([], dtype=pd.Float64Dtype())
        return syll_df

    from spacy.tokens import Doc
    nlp = _get_nlp(model)

    # get unique words per sentence (form_idx 0 or -1, no duplicates)
    word_df = syll_df[syll_df['form_idx'].isin([0, -1])].drop_duplicates('word_num')

    # canonical syllable count per word (for the monosyllable disambiguation)
    nsyll_by_word = (
        syll_df[(syll_df['form_idx'] == 0) & (~syll_df['is_punc'])]
        .groupby('word_num').size().to_dict()
    )

    stress_by_word = {}
    pstress_by_word = {}
    tstress_by_word = {}
    pstrength_by_word = {}

    # First pass: build one pre-tokenized Doc per sentence, collecting the
    # word_num bookkeeping in parallel. All-punctuation sentences produce no
    # Doc; their words get None directly.
    docs = []
    doc_meta = []  # parallel to docs: (parse_word_nums, punc_word_nums)
    for sent_num, group in word_df.groupby('sent_num'):
        words = group['word_txt'].values
        word_nums = group['word_num'].values
        is_punc = group['is_punc'].values.astype(bool)

        # filter to non-punctuation for parsing, strip whitespace
        parse_mask = ~is_punc
        parse_words = [w.strip() for w in words[parse_mask]]
        parse_word_nums = word_nums[parse_mask]

        if len(parse_words) == 0:
            for wn in word_nums:
                stress_by_word[wn] = None
                pstress_by_word[wn] = None
                tstress_by_word[wn] = None
                pstrength_by_word[wn] = None
            continue

        # pre-tokenized Doc; the spaCy pipeline runs on it below via nlp.pipe
        spaces = [True] * len(parse_words)
        spaces[-1] = False
        docs.append(Doc(nlp.vocab, words=list(parse_words), spaces=spaces))
        doc_meta.append((parse_word_nums, word_nums[is_punc]))

    # Second pass: a single batched pipeline call over all sentence Docs
    # instead of one nlp() call per sentence. nlp.pipe preserves input order,
    # so zipping with doc_meta keeps each Doc aligned with its word_nums.
    for doc, (parse_word_nums, punc_word_nums) in zip(nlp.pipe(docs), doc_meta):
        n = len(doc)
        # extract head indices (-1 for root)
        heads = np.array([
            tok.head.i if tok.head.i != tok.i else -1
            for tok in doc
        ], dtype=np.int32)
        pos = np.array([tok.pos_ for tok in doc])
        xpos = np.array([tok.tag_ for tok in doc])
        deprels = np.array([tok.dep_ for tok in doc])
        words = np.array([tok.text for tok in doc])

        stress = _compute_phrasal_stress(heads, pos, xpos, n)

        nsylls = np.array([
            nsyll_by_word.get(wn, 1) for wn in parse_word_nums
        ], dtype=np.int32)
        pstress, tstress, pstrength = _mt_gradient(heads, words, xpos, deprels, nsylls, n)

        for i, wn in enumerate(parse_word_nums):
            stress_by_word[wn] = int(stress[i])
            pstress_by_word[wn] = None if np.isnan(pstress[i]) else float(pstress[i])
            tstress_by_word[wn] = None if np.isnan(tstress[i]) else float(tstress[i])
            pstrength_by_word[wn] = None if np.isnan(pstrength[i]) else float(pstrength[i])

        # punctuation gets None
        for wn in punc_word_nums:
            stress_by_word[wn] = None
            pstress_by_word[wn] = None
            tstress_by_word[wn] = None
            pstrength_by_word[wn] = None

    # broadcast to syllable rows
    syll_df['phrasal_stress'] = syll_df['word_num'].map(stress_by_word).astype(pd.Int32Dtype())
    syll_df['pstress'] = syll_df['word_num'].map(pstress_by_word).astype(pd.Float64Dtype())
    syll_df['tstress'] = syll_df['word_num'].map(tstress_by_word).astype(pd.Float64Dtype())
    syll_df['pstrength'] = syll_df['word_num'].map(pstrength_by_word).astype(pd.Float64Dtype())
    return syll_df
