"""Vectorized metrical parser using numpy for batch constraint evaluation."""

import numpy as np
from ..imports import *


def extract_features(wordtokens):
    """Extract syllable features as numpy arrays from a WordTokenList.

    Returns dict of arrays, all shape (N,) where N = number of syllables.
    """
    sylls = []
    word_ids = []
    func_word = []

    for wt in wordtokens:
        if not wt.has_wordform:
            continue
        wf = wt.wordtype.children[0]  # first wordform
        is_func = wf.is_functionword
        for syll in wf:
            sylls.append(syll)
            word_ids.append(wt.num)
            func_word.append(is_func)

    n = len(sylls)
    stressed = np.array([s.is_stressed for s in sylls], dtype=bool)
    heavy = np.array([s.is_heavy for s in sylls], dtype=bool)

    # is_strong/is_weak: polysyllabic stress context (within-word neighbors)
    # None for monosyllabic words, True/False otherwise
    strong = np.zeros(n, dtype=np.int8)  # 0=False/None, 1=True
    weak = np.zeros(n, dtype=np.int8)
    for i, s in enumerate(sylls):
        v = s.is_strong
        if v is True:
            strong[i] = 1
        v = s.is_weak
        if v is True:
            weak[i] = 1

    return {
        "sylls": sylls,
        "stressed": stressed,
        "heavy": heavy,
        "strong": strong,
        "weak": weak,
        "word_ids": np.array(word_ids, dtype=np.int32),
        "func_word": np.array(func_word, dtype=bool),
    }


def prefilter_scansions(scansions, num_stressed):
    """Remove scansions that can't possibly be optimal.

    Filters out scansions where the number of strong positions differs
    from the number of stressed syllables by more than a threshold.
    """
    if not scansions or num_stressed == 0:
        return scansions

    filtered = []
    for scan in scansions:
        num_strong = sum(1 for pos in scan if pos[0] == 's')
        # allow some mismatch but skip extreme cases
        if abs(num_strong - num_stressed) <= num_stressed:
            filtered.append(scan)

    return filtered if filtered else scansions


_scansion_cache = {}

def encode_scansions(scansions, nsylls):
    """Convert list of scansion lists to numpy arrays.

    Args:
        scansions: List[List[str]] e.g. [["w","s","w","s"], ["s","w","ss","w"], ...]
        nsylls: Total number of syllables

    Returns:
        meter_vals: (S, N) bool — True=strong, False=weak per syllable
        position_ids: (S, N) int — which position index each syllable belongs to
        position_sizes: (S, N) int — size of the position each syllable belongs to
    """
    # cache key: tuple of tuples (immutable)
    cache_key = tuple(tuple(s) for s in scansions)
    if cache_key in _scansion_cache:
        return _scansion_cache[cache_key]

    S = len(scansions)
    N = nsylls

    meter_vals = np.zeros((S, N), dtype=bool)
    position_ids = np.zeros((S, N), dtype=np.int32)
    position_sizes = np.zeros((S, N), dtype=np.int32)

    for si, scansion in enumerate(scansions):
        syll_idx = 0
        for pos_idx, pos_str in enumerate(scansion):
            is_strong = pos_str[0] == "s"
            pos_size = len(pos_str)
            for _ in range(pos_size):
                if syll_idx < N:
                    meter_vals[si, syll_idx] = is_strong
                    position_ids[si, syll_idx] = pos_idx
                    position_sizes[si, syll_idx] = pos_size
                    syll_idx += 1

    result = (meter_vals, position_ids, position_sizes)
    _scansion_cache[cache_key] = result
    return result


def evaluate_constraints(features, meter_vals, position_ids, position_sizes, constraint_names):
    """Batch-evaluate all constraints across all scansions.

    Args:
        features: dict from extract_features()
        meter_vals: (S, N) bool
        position_ids: (S, N) int
        position_sizes: (S, N) int
        constraint_names: list of constraint name strings

    Returns:
        viols: (S, N, C) int8 — violation matrix
        constraint_index: dict mapping constraint name to index in C dimension
    """
    S, N = meter_vals.shape
    C = len(constraint_names)
    viols = np.zeros((S, N, C), dtype=np.int8)
    constraint_index = {name: i for i, name in enumerate(constraint_names)}

    # broadcast features to (1, N) for operations against (S, N)
    stressed = features["stressed"][None, :]   # (1, N)
    heavy = features["heavy"][None, :]
    strong = features["strong"][None, :]
    weak = features["weak"][None, :]
    word_ids = features["word_ids"][None, :]   # (1, N)
    func_word = features["func_word"][None, :] # (1, N)

    is_strong_pos = meter_vals   # (S, N) True = strong/prominent
    is_weak_pos = ~meter_vals    # (S, N) True = weak

    for cname in constraint_names:
        ci = constraint_index[cname]

        if cname == "w_stress":
            # stressed syllable on weak position
            viols[:, :, ci] = (stressed & is_weak_pos).astype(np.int8)

        elif cname == "s_unstress":
            # unstressed syllable on strong position
            viols[:, :, ci] = (~stressed & is_strong_pos).astype(np.int8)

        elif cname == "w_peak":
            # polysyllabic stress on weak position
            viols[:, :, ci] = (strong.astype(bool) & is_weak_pos).astype(np.int8)

        elif cname == "s_trough":
            # polysyllabic unstress on strong position
            viols[:, :, ci] = (weak.astype(bool) & is_strong_pos).astype(np.int8)

        elif cname == "foot_size":
            # position exceeds 2 syllables
            viols[:, :, ci] = (position_sizes > 2).astype(np.int8)

        elif cname == "unres_within":
            # disyllabic position within same word: first syll must be light+stressed
            # only applies to 2nd+ syllable in a multi-syll position
            _eval_unres_within(viols, ci, position_ids, position_sizes,
                               word_ids, heavy, stressed, S, N)

        elif cname == "unres_across":
            # disyllabic position crossing words: both must be function words, pos must be weak
            _eval_unres_across(viols, ci, position_ids, position_sizes,
                                word_ids, func_word, is_strong_pos, S, N)

    return viols, constraint_index


def _eval_unres_within(viols, ci, position_ids, position_sizes, word_ids, heavy, stressed, S, N):
    """Evaluate unres_within constraint for all scansions."""
    if N < 2:
        return
    for j in range(1, N):
        # is this syllable in a multi-syll position AND same position as previous syll?
        same_pos = position_ids[:, j] == position_ids[:, j - 1]  # (S,)
        multi_syll = position_sizes[:, j] >= 2  # (S,)
        same_word = word_ids[0, j] == word_ids[0, j - 1]  # scalar

        if not same_word:
            continue  # unres_within only applies within same word

        in_position = same_pos & multi_syll  # (S,)
        if not in_position.any():
            continue

        # first syll of position must be light AND stressed, else violation on 2nd syll
        prev_heavy = heavy[0, j - 1]  # scalar
        prev_stressed = stressed[0, j - 1]  # scalar
        if prev_heavy or not prev_stressed:
            viols[:, j, ci] |= in_position.astype(np.int8)


def _eval_unres_across(viols, ci, position_ids, position_sizes, word_ids, func_word, is_strong_pos, S, N):
    """Evaluate unres_across constraint for all scansions."""
    if N < 2:
        return
    for j in range(1, N):
        same_pos = position_ids[:, j] == position_ids[:, j - 1]  # (S,)
        multi_syll = position_sizes[:, j] >= 2  # (S,)
        diff_word = word_ids[0, j] != word_ids[0, j - 1]  # scalar

        if not diff_word:
            continue  # unres_across only applies across word boundaries

        in_position = same_pos & multi_syll  # (S,)
        if not in_position.any():
            continue

        # violation if: strong position, OR not both function words
        prev_func = func_word[0, j - 1]  # scalar
        curr_func = func_word[0, j]  # scalar

        if is_strong_pos.ndim > 0:
            # strong position always violates for across-word resolution
            strong_viol = is_strong_pos[:, j]  # (S,)
            not_both_func = not (prev_func and curr_func)
            violation = in_position & (strong_viol | not_both_func)
        else:
            violation = in_position

        viols[:, j, ci] |= violation.astype(np.int8)


def compute_bounding(viols, constraint_index):
    """Compute harmonic bounding: mark scansions dominated by others.

    Uses vectorized pairwise comparison: for each pair (i,j), check if
    i's violations are a strict subset of j's (i bounds j) or vice versa.

    Args:
        viols: (S, N, C) violation matrix
        constraint_index: dict of constraint name -> index

    Returns:
        unbounded: (S,) bool mask — True for unbounded scansions
    """
    # Sum violations per constraint per scansion: (S, C)
    v = viols.sum(axis=1)  # (S, C)
    S = v.shape[0]

    if S <= 1:
        return np.ones(S, dtype=bool)

    # Pairwise comparison: (S, 1, C) vs (1, S, C) -> (S, S, C)
    # i_leq_j[i,j] = True if v[i] <= v[j] for all constraints
    diff = v[:, None, :] - v[None, :, :]  # (S, S, C)
    i_leq_j = (diff <= 0).all(axis=2)     # (S, S)
    i_lt_j = i_leq_j & (diff < 0).any(axis=2)  # (S, S) strict subset

    # i bounds j means i_lt_j[i,j] is True -> j is bounded
    # j is bounded if ANY i strictly dominates it
    bounded = i_lt_j.any(axis=0)  # (S,) — True if bounded by at least one other

    return ~bounded


class LazyParseList:
    """Lightweight parse list that defers Parse object construction.

    Stores numpy violation data and scansion lists. Parse objects are
    only built when accessed (e.g., via best_parse, iteration, or indexing).
    """

    def __init__(self, wordtokens, meter, scansions, viols, constraint_index,
                 unbounded_mask, sylls, parse_unit="line"):
        self.wordtokens = wordtokens
        self.meter = meter
        self.parse_unit = parse_unit
        self.parent = wordtokens

        # filter to unbounded only
        unbounded_indices = np.where(unbounded_mask)[0]
        self._scansions = [scansions[i] for i in unbounded_indices]
        self._viols = viols[unbounded_indices]  # (U, N, C)
        self._constraint_index = constraint_index
        self._constraint_names = list(constraint_index.keys())
        self._sylls = sylls
        self._built_parses = {}  # cache: local index -> Parse
        self._best_idx = None
        self._bound_init = True
        self._num = None

        # compute scores for ranking (weighted violation sums)
        constraint_weights = meter.constraints
        weights = np.array([constraint_weights.get(c, 1) for c in self._constraint_names])
        viols_per_scansion = self._viols.sum(axis=1)  # (U, C)
        self._scores = (viols_per_scansion * weights[None, :]).sum(axis=1)  # (U,)
        self._viols_per_scansion = viols_per_scansion

    def __len__(self):
        return len(self._scansions)

    def __bool__(self):
        return len(self._scansions) > 0

    @property
    def num_parses(self):
        return len(self._scansions)

    @property
    def num_unbounded(self):
        return len(self._scansions)

    @property
    def best_parse(self):
        if not self._scansions:
            return None
        if self._best_idx is None:
            self._best_idx = int(self._scores.argmin())
        return self._get_parse(self._best_idx, rank=1)

    @property
    def best_parses(self):
        if self.best_parse is None:
            return self
        return self

    @property
    def unbounded(self):
        return self

    @property
    def bounded(self):
        from .parselists import ParseList
        return ParseList([], parse_unit=self.parse_unit, parent=self.parent)

    @property
    def data(self):
        return [self._get_parse(i) for i in range(len(self._scansions))]

    def __iter__(self):
        for i in range(len(self._scansions)):
            yield self._get_parse(i)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            indices = range(*idx.indices(len(self._scansions)))
            return [self._get_parse(i) for i in indices]
        return self._get_parse(idx)

    def bound(self, progress=False):
        return self  # already bounded in numpy

    def rank(self):
        pass  # ranking is implicit via _scores

    def register_objects(self):
        pass  # not needed for vectorized path

    def _iter_all(self):
        yield self
        # don't iterate into Parse objects — they're lazy

    def iter_all(self):
        yield from self._iter_all()

    def _get_parse(self, idx, rank=None):
        """Build a Parse object for the given index, caching the result."""
        if idx in self._built_parses:
            return self._built_parses[idx]

        parse = _build_single_parse(
            idx, self._scansions[idx], self._viols, self._constraint_index,
            self._constraint_names, self._sylls, self.wordtokens, self.meter,
            rank=rank,
        )
        parse.parent = self
        self._built_parses[idx] = parse
        return parse

    # ParseList interface compatibility
    def stats_d(self, **kwargs):
        from .parselists import ParseList
        return ParseList(self.data, parse_unit=self.parse_unit, parent=self.parent).stats_d(**kwargs)

    def stats(self, **kwargs):
        from .parselists import ParseList
        return ParseList(self.data, parse_unit=self.parse_unit, parent=self.parent).stats(**kwargs)

    def to_html(self, **kwargs):
        bp = self.best_parse
        return bp.to_html(**kwargs) if bp else ""

    def render(self, **kwargs):
        bp = self.best_parse
        return bp.render(**kwargs) if bp else ""

    @property
    def scansions(self):
        return self

    def get_df(self, **kwargs):
        from .parselists import ParseList
        return ParseList(self.data, parse_unit=self.parse_unit, parent=self.parent).get_df(**kwargs)

    def get_ld(self, **kwargs):
        from .parselists import ParseList
        return ParseList(self.data, parse_unit=self.parse_unit, parent=self.parent).get_ld(**kwargs)


def _build_single_parse(idx, scansion, viols, constraint_index, constraint_names,
                          sylls, wordtokens, meter, rank=None):
    """Build a single Parse object from numpy data."""
    from .parses import Parse
    from .positions import ParsePosition, ParsePositionList
    from .slots import ParseSlot

    nsylls = len(sylls)
    wordforms = wordtokens.wordforms
    constraint_weights = meter.constraints
    parse_constraint_funcs = meter.parse_constraint_funcs

    syll_idx = 0
    positions = []
    for pos_str in scansion:
        mval = pos_str[0]

        mpos = ParsePosition.__new__(ParsePosition)
        mpos._attrs = {"meter_val": mval}
        mpos.meter_val = mval
        mpos.parent = None
        mpos._num = None
        mpos._text = None
        mpos._key = None
        mpos._txt = ""
        mpos._mtr = None
        mpos._init = True

        slots = []
        for _ in pos_str:
            if syll_idx >= nsylls:
                break
            slot = ParseSlot.__new__(ParseSlot)
            slot.unit = sylls[syll_idx]
            slot.parent = mpos
            slot._attrs = {}
            slot._num = None
            slot._text = None
            slot._key = None
            slot._txt = ""
            slot._mtr = None
            slot.children = []
            slot_viold = {}
            for cname in constraint_names:
                v = int(viols[idx, syll_idx, constraint_index[cname]])
                if v:
                    slot_viold[cname] = v
            slot.viold = slot_viold
            slot.constraint_weights = constraint_weights
            slots.append(slot)
            syll_idx += 1

        mpos.children = slots
        positions.append(mpos)

    parse = Parse.__new__(Parse)
    parse._attrs = {}
    parse._num = None
    parse._text = None
    parse._key = None
    parse._txt = ""
    parse._mtr = None
    parse.parent = None
    parse.meter_obj = meter
    parse._scope = None
    parse.constraint_names = constraint_names
    parse.parse_constraints = parse_constraint_funcs
    parse.position_constraints = meter.position_constraint_funcs
    parse.constraint_weights = constraint_weights
    parse.wordtokens = wordtokens
    parse.wordforms = wordforms
    parse.slot_units = sylls
    parse.scansion = list(scansion)
    parse.is_bounded = False
    parse.bounded_by = []
    parse.unmetrical = False
    parse.comparison_nums = set()
    parse.comparison_parses = []
    parse.parse_num = 0
    parse.total_score = None
    parse.pause_comparisons = False
    parse.parse_rank = rank
    parse.num_slots_positioned = syll_idx
    parse.parse_viold = Counter()

    pos_list = ParsePositionList.__new__(ParsePositionList)
    pos_list.children = positions
    pos_list.parent = parse
    pos_list._attrs = {}
    pos_list._num = None
    pos_list._text = None
    pos_list._key = None
    pos_list._txt = ""
    pos_list._mtr = None
    parse.children = pos_list

    for mpos in positions:
        mpos.parent = pos_list

    for cname, cfunc in parse_constraint_funcs.items():
        res = cfunc(parse)
        if isinstance(res, bool) and res:
            parse.parse_viold[cname] = 1

    return parse


def build_parses(wordtokens, meter, scansions, viols, constraint_index, unbounded_mask):
    """Build a LazyParseList from vectorized results.

    Returns a lazy wrapper that defers Parse object construction until
    accessed. Only best_parse triggers construction of a single Parse.
    """
    sylls = []
    for wt in wordtokens:
        if not wt.has_wordform:
            continue
        wf = wt.wordtype.children[0]
        for syll in wf:
            sylls.append(syll)

    return LazyParseList(
        wordtokens, meter, scansions, viols, constraint_index,
        unbounded_mask, sylls, parse_unit=meter.parse_unit,
    )
