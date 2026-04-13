"""Vectorized metrical parser using numpy for batch constraint evaluation."""

import numpy as np
from collections import defaultdict
from ..imports import *


def parse_batch_from_df(syll_df, meter, line_col='line_num'):
    """Parse all lines from a syllable DataFrame without constructing Entity objects.

    Groups lines by syllable count, evaluates constraints in batch,
    returns results keyed by line number.
    """
    from .parselists import ParseList
    from ..texts.syll_df import SyllData

    # extract all non-punc rows as numpy arrays (single pass)
    non_punc_mask = syll_df['is_punc'].values == 0
    non_punc_idx = np.where(non_punc_mask)[0]

    all_ipa = syll_df['syll_ipa'].values
    all_txt = syll_df['syll_text'].values
    all_stressed = syll_df['is_stressed'].values
    all_heavy = syll_df['is_heavy'].values
    all_strong = syll_df['is_strong'].values
    all_weak = syll_df['is_weak'].values
    all_wnum = syll_df['word_num'].values
    all_func = syll_df['is_functionword'].values
    all_line = syll_df[line_col].values
    all_form = syll_df['form_idx'].values
    all_nforms = syll_df['num_forms'].values
    has_phrasal = 'phrasal_stress' in syll_df.columns and syll_df['phrasal_stress'].notna().any()
    if has_phrasal:
        # fill NaN with 0 for vectorized ops
        all_phrasal = syll_df['phrasal_stress'].fillna(0).values.astype(np.int32)
    else:
        all_phrasal = np.zeros(len(syll_df), dtype=np.int32)

    # subset arrays for non-punc rows
    np_line = all_line[non_punc_idx]
    np_form = all_form[non_punc_idx]
    np_wnum = all_wnum[non_punc_idx]
    np_nforms = all_nforms[non_punc_idx]

    # --- Build form 0 data per line (fast numpy grouping) ---
    form0_mask = np_form == 0
    f0_idx = non_punc_idx[form0_mask]
    f0_line = np_line[form0_mask]

    # group form0 by line
    f0_sort = np.argsort(f0_line, kind='stable')
    f0_line_s = f0_line[f0_sort]
    f0_idx_s = f0_idx[f0_sort]
    f0_breaks = np.where(np.diff(f0_line_s, prepend=f0_line_s[0]-1) != 0)[0]
    f0_breaks = np.append(f0_breaks, len(f0_line_s))

    # line_data: line_num -> (feats, sylls, has_ambig, form_variants)
    # form_variants: list of row-index arrays for each form combination
    line_data = {}

    for i in range(len(f0_breaks) - 1):
        ln = int(f0_line_s[f0_breaks[i]])
        rows = f0_idx_s[f0_breaks[i]:f0_breaks[i+1]]
        n = len(rows)
        if n < 2:
            continue

        sylls = [
            SyllData(ipa=all_ipa[r], txt=all_txt[r],
                     is_stressed=bool(all_stressed[r]), is_heavy=bool(all_heavy[r]),
                     is_strong=bool(all_strong[r]), is_weak=bool(all_weak[r]))
            for r in rows
        ]
        feats = {
            "sylls": sylls,
            "stressed": all_stressed[rows].astype(bool),
            "heavy": all_heavy[rows].astype(bool),
            "strong": all_strong[rows].astype(np.int8),
            "weak": all_weak[rows].astype(np.int8),
            "word_ids": all_wnum[rows].astype(np.int32),
            "func_word": all_func[rows].astype(bool),
            "phrasal_stress": all_phrasal[rows].astype(np.int32),
        }

        # check if any word in this line has multiple forms
        line_np_mask = np_line == ln
        has_ambig = bool(meter.resolve_optionality and (np_nforms[line_np_mask] > 1).any())
        line_data[ln] = (feats, sylls, has_ambig, rows)

    # --- Pre-build ambiguous form variants using numpy ---
    ambig_form_variants = {}  # line_num -> list of row-index arrays
    for ln, (feats, sylls, has_ambig, f0_rows) in line_data.items():
        if not has_ambig:
            continue
        line_mask = np_line == ln
        line_rows = non_punc_idx[line_mask]
        line_wn = np_wnum[line_mask]
        line_fi = np_form[line_mask]
        max_fi = int(line_fi.max())
        forms = [f0_rows]  # form 0 already computed
        for fi in range(1, max_fi + 1):
            selected = []
            for wn in np.unique(line_wn):
                wmask = line_wn == wn
                wrows = line_rows[wmask]
                wfi = line_fi[wmask]
                if fi in wfi:
                    selected.append(wrows[wfi == fi])
                else:
                    selected.append(wrows[wfi == 0])
            forms.append(np.concatenate(selected))
        ambig_form_variants[ln] = forms

    # --- Group by nsylls and process ---
    nsyll_groups = defaultdict(list)
    for ln, (feats, sylls, has_ambig, _) in line_data.items():
        nsylls = len(feats["stressed"])
        nsyll_groups[nsylls].append(ln)

    results = {}
    constraint_names = list(meter.constraints.keys())

    for nsylls, line_nums in nsyll_groups.items():
        scansions = meter.get_possible_scansions(nsylls)
        if not scansions:
            for ln in line_nums:
                results[ln] = ParseList([], parse_unit=meter.parse_unit)
            continue

        meter_vals, position_ids, position_sizes = encode_scansions(scansions, nsylls)

        simple_lines = [ln for ln in line_nums if not line_data[ln][2]]
        ambig_lines = [ln for ln in line_nums if line_data[ln][2]]
        constraint_index = None

        # batch simple lines: evaluate ALL constraints in one vectorized call
        if simple_lines:
            feats_list = [line_data[ln][0] for ln in simple_lines]
            all_viols_4d, ci = evaluate_constraints_batch(
                feats_list, meter_vals, position_ids, position_sizes, constraint_names
            )
            constraint_index = ci
            # all_viols_4d is (L, S, N, C) — sum over N for bounding
            all_viol_sums = all_viols_4d.sum(axis=2)  # (L, S, C)
            unbounded_masks = compute_bounding_batch(all_viol_sums)

            for i, ln in enumerate(simple_lines):
                pl = LazyParseList(
                    None, meter, scansions, all_viols_4d[i], constraint_index,
                    unbounded_masks[i], line_data[ln][1], parse_unit=meter.parse_unit,
                )
                pl._unit_num = int(ln)
                results[ln] = pl

        # handle ambiguous lines: batch constraint eval, then batch bounding
        if ambig_lines:
            # Phase 1: collect all same-nsylls form variants, eval constraints
            same_nsylls_viols = []  # viols for forms matching this nsylls
            same_nsylls_meta = []   # (ln, form_idx, sylls) per entry
            diff_nsylls_items = []  # (ln, rows) for forms with different nsylls

            # collect same-nsylls and diff-nsylls form variants
            same_feats_list = []
            for ln in ambig_lines:
                form_variants = ambig_form_variants[ln]
                for fi, rows in enumerate(form_variants):
                    wnsylls = len(rows)
                    if wnsylls < 2:
                        continue
                    feats = {
                        "stressed": all_stressed[rows].astype(bool),
                        "heavy": all_heavy[rows].astype(bool),
                        "strong": all_strong[rows].astype(np.int8),
                        "weak": all_weak[rows].astype(np.int8),
                        "word_ids": all_wnum[rows].astype(np.int32),
                        "func_word": all_func[rows].astype(bool),
                        "phrasal_stress": all_phrasal[rows].astype(np.int32),
                    }
                    if wnsylls == nsylls:
                        same_feats_list.append(feats)
                        same_nsylls_meta.append((ln, fi, rows))
                    else:
                        diff_nsylls_items.append((ln, fi, rows, feats, wnsylls))
                    if not meter.resolve_optionality:
                        break

            # Phase 2: batch eval + bounding for same-nsylls ambig forms
            ambig_unbounded = {}
            if same_feats_list:
                ambig_viols_4d, ci = evaluate_constraints_batch(
                    same_feats_list, meter_vals, position_ids, position_sizes, constraint_names
                )
                if constraint_index is None:
                    constraint_index = ci
                same_nsylls_viols = [ambig_viols_4d[i] for i in range(len(same_feats_list))]
                ambig_viol_sums = ambig_viols_4d.sum(axis=2)  # (L, S, C)
                ambig_masks = compute_bounding_batch(ambig_viol_sums)
                for i in range(len(same_feats_list)):
                    ambig_unbounded[i] = ambig_masks[i]

            # Phase 3: batch eval + bounding for diff-nsylls forms
            diff_by_nsylls = defaultdict(list)
            for item in diff_nsylls_items:
                ln, fi, rows, feats, wnsylls = item
                diff_by_nsylls[wnsylls].append(item)

            diff_results = {}
            for dns, items in diff_by_nsylls.items():
                wscans = meter.get_possible_scansions(dns)
                if not wscans:
                    continue
                wmv, wpi, wps = encode_scansions(wscans, dns)
                d_feats = [item[3] for item in items]
                d_viols_4d, ci2 = evaluate_constraints_batch(
                    d_feats, wmv, wpi, wps, constraint_names
                )
                d_viol_sums = d_viols_4d.sum(axis=2)
                d_masks = compute_bounding_batch(d_viol_sums)
                for i, item in enumerate(items):
                    diff_results[id(item)] = (d_viols_4d[i], d_masks[i], wscans)

            # Phase 4: pick best form per ambig line
            # collect all candidates per line
            line_candidates = defaultdict(list)  # ln -> [(viols, unbounded, scansions, rows)]

            for i, (ln, fi, rows) in enumerate(same_nsylls_meta):
                line_candidates[ln].append((
                    same_nsylls_viols[i], ambig_unbounded[i], scansions, rows
                ))

            for item in diff_nsylls_items:
                ln, fi, rows, feats, wnsylls = item
                if id(item) in diff_results:
                    v, unb, ws = diff_results[id(item)]
                    line_candidates[ln].append((v, unb, ws, rows))

            constraint_weights = meter.constraints
            weight_arr = np.array([constraint_weights.get(c, 1) for c in constraint_names])

            for ln in ambig_lines:
                candidates = line_candidates.get(ln, [])
                best_result = None
                best_score = float('inf')
                for viols, unbounded_mask, cand_scansions, rows in candidates:
                    unb_idx = np.where(unbounded_mask)[0]
                    if len(unb_idx) == 0:
                        continue
                    scores = (viols.sum(axis=1) * weight_arr[None, :]).sum(axis=1)
                    unb_scores = scores[unb_idx]
                    ms = float(unb_scores.min())
                    if ms < best_score:
                        best_score = ms
                        sylls = [
                            SyllData(ipa=all_ipa[r], txt=all_txt[r],
                                     is_stressed=bool(all_stressed[r]), is_heavy=bool(all_heavy[r]),
                                     is_strong=bool(all_strong[r]), is_weak=bool(all_weak[r]))
                            for r in rows
                        ]
                        ci_use = constraint_index if constraint_index is not None else {c: i for i, c in enumerate(constraint_names)}
                        best_result = LazyParseList(
                            None, meter, cand_scansions, viols, ci_use,
                            unbounded_mask, sylls, parse_unit=meter.parse_unit,
                        )
                pl = best_result if best_result else ParseList([], parse_unit=meter.parse_unit)
                pl._unit_num = int(ln)
                results[ln] = pl

    return results


def parse_batch(parse_units, meter, syll_df=None):
    """Parse all units in a single batched operation.

    Groups lines by syllable count to share scansion encodings,
    then evaluates constraints and bounding for each group.

    Args:
        parse_units: list of WordTokenList objects (lines/lineparts)
        meter: Meter object
        syll_df: optional syllable DataFrame from TextModel._syll_df.
            When provided, features are read from the DF instead of
            walking Entity objects (faster).

    Returns:
        list of (wordtokens, LazyParseList) pairs in original order
    """
    from .parselists import ParseList

    # choose feature extraction strategy
    use_df = syll_df is not None and len(syll_df) > 0

    # extract features for all lines and group by nsylls
    groups = defaultdict(list)  # nsylls -> [(idx, wordtokens, features, sylls)]
    all_features = []
    for idx, wt in enumerate(parse_units):
        if wt.num_sylls < 2:
            all_features.append(None)
            continue

        if use_df:
            # read numpy arrays from the DF (fast), but keep real Syllable objects
            line_num = wt[0].line_num if hasattr(wt[0], 'line_num') else None
            if line_num is not None:
                feats = _extract_features_hybrid(wt, syll_df, line_num)
            else:
                feats = extract_features(wt)
        else:
            feats = extract_features(wt)

        nsylls = len(feats["stressed"])
        sylls = feats["sylls"]
        groups[nsylls].append((idx, wt, feats, sylls))
        all_features.append(feats)

    # process each syllable-count group
    results = [None] * len(parse_units)

    for nsylls, group in groups.items():
        scansions = meter.get_possible_scansions(nsylls)
        if not scansions:
            for idx, wt, _, _ in group:
                results[idx] = (wt, ParseList([], parse_unit=meter.parse_unit, parent=wt))
            continue

        meter_vals, position_ids, position_sizes = encode_scansions(scansions, nsylls)
        constraint_names = list(meter.constraints.keys())

        # split group into simple (no ambiguity) and ambiguous lines
        simple_lines = []
        ambig_lines = []
        for item in group:
            idx, wt, feats, sylls = item
            needs_matrix = meter.resolve_optionality and any(
                w.wordtype.num_forms > 1 for w in wt if w.has_wordform
            )
            if needs_matrix:
                ambig_lines.append(item)
            else:
                simple_lines.append(item)

        # batch simple lines: evaluate constraints, then batch bounding on GPU
        if simple_lines:
            all_viols = []
            constraint_index = None
            for idx, wt, feats, sylls in simple_lines:
                viols, ci = evaluate_constraints(
                    feats, meter_vals, position_ids, position_sizes, constraint_names
                )
                all_viols.append(viols)
                if constraint_index is None:
                    constraint_index = ci

            # batch bounding
            all_viol_sums = np.stack([v.sum(axis=1) for v in all_viols])  # (L, S, C)
            unbounded_masks = compute_bounding_batch(all_viol_sums)  # (L, S)

            for i, (idx, wt, feats, sylls) in enumerate(simple_lines):
                pl = LazyParseList(
                    wt, meter, scansions, all_viols[i], constraint_index,
                    unbounded_masks[i], sylls, parse_unit=meter.parse_unit,
                )
                results[idx] = (wt, pl)

        # handle ambiguous lines individually
        for idx, wt, feats, sylls in ambig_lines:
            best_result = None
            best_score = float('inf')
            for wtl in wt.iter_wordtoken_matrix():
                wfeats = extract_features(wtl)
                wnsylls = len(wfeats["stressed"])
                if wnsylls != nsylls:
                    wscans = meter.get_possible_scansions(wnsylls)
                    if not wscans:
                        continue
                    wmv, wpi, wps = encode_scansions(wscans, wnsylls)
                else:
                    wscans, wmv, wpi, wps = scansions, meter_vals, position_ids, position_sizes
                wviols, wci = evaluate_constraints(
                    wfeats, wmv, wpi, wps, constraint_names
                )
                wunb = compute_bounding(wviols, wci)
                wsylls = wfeats["sylls"]
                wpl = LazyParseList(
                    wtl, meter, wscans, wviols, wci, wunb, wsylls,
                    parse_unit=meter.parse_unit,
                )
                if wpl._scores.size > 0:
                    ms = float(wpl._scores.min())
                    if ms < best_score:
                        best_score = ms
                        best_result = wpl
                if not meter.resolve_optionality:
                    break
            if best_result:
                best_result.parent = wt  # ensure parent is original line, not copy
                pl = best_result
            else:
                pl = ParseList([], parse_unit=meter.parse_unit, parent=wt)
            results[idx] = (wt, pl)

    # fill in empty results for lines with < 2 syllables
    for idx in range(len(parse_units)):
        if results[idx] is None:
            wt = parse_units[idx]
            results[idx] = (wt, ParseList([], parse_unit=meter.parse_unit, parent=wt))

    return results


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
        "phrasal_stress": np.zeros(n, dtype=np.int32),
    }


def _extract_features_hybrid(wordtokens, syll_df, line_num):
    """Extract features using DF for arrays but Entity objects for sylls.

    Reads pre-computed numpy arrays from the syllable DataFrame (fast),
    but keeps real Syllable objects for Parse construction (compatibility).
    """
    # get real Syllable objects from Entity tree
    sylls = []
    for wt in wordtokens:
        if not wt.has_wordform:
            continue
        wf = wt.wordtype.children[0]
        for syll in wf:
            sylls.append(syll)

    # read arrays from DF (form_idx=0 only, non-punc)
    line_df = syll_df[(syll_df['line_num'] == line_num) &
                      (syll_df['form_idx'] == 0) &
                      (syll_df['is_punc'] == 0)]

    n = len(line_df)
    if n != len(sylls):
        # mismatch — fall back to Entity-based extraction
        return extract_features(wordtokens)

    phrasal = np.zeros(n, dtype=np.int32)
    if 'phrasal_stress' in line_df.columns:
        phrasal = line_df['phrasal_stress'].fillna(0).values.astype(np.int32)

    return {
        "sylls": sylls,
        "stressed": line_df['is_stressed'].values.astype(bool),
        "heavy": line_df['is_heavy'].values.astype(bool),
        "strong": line_df['is_strong'].values.astype(np.int8),
        "weak": line_df['is_weak'].values.astype(np.int8),
        "word_ids": line_df['word_num'].values.astype(np.int32),
        "func_word": line_df['is_functionword'].values.astype(bool),
        "phrasal_stress": phrasal,
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
    """Batch-evaluate all constraints across all scansions for a single line.

    Args:
        features: dict with arrays of shape (N,)
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

    stressed = features["stressed"][None, :]   # (1, N)
    heavy = features["heavy"][None, :]
    strong = features["strong"][None, :]
    weak = features["weak"][None, :]
    word_ids = features["word_ids"][None, :]
    func_word = features["func_word"][None, :]

    is_strong_pos = meter_vals
    is_weak_pos = ~meter_vals

    for cname in constraint_names:
        ci = constraint_index[cname]
        if cname == "w_stress":
            viols[:, :, ci] = (stressed & is_weak_pos).astype(np.int8)
        elif cname == "s_unstress":
            viols[:, :, ci] = (~stressed & is_strong_pos).astype(np.int8)
        elif cname == "w_peak":
            viols[:, :, ci] = (strong.astype(bool) & is_weak_pos).astype(np.int8)
        elif cname == "s_trough":
            viols[:, :, ci] = (weak.astype(bool) & is_strong_pos).astype(np.int8)
        elif cname == "foot_size":
            viols[:, :, ci] = (position_sizes > 2).astype(np.int8)
        elif cname == "unres_within":
            _eval_unres_within(viols, ci, position_ids, position_sizes,
                               word_ids, heavy, stressed, S, N)
        elif cname == "unres_across":
            _eval_unres_across(viols, ci, position_ids, position_sizes,
                                word_ids, func_word, is_strong_pos, S, N)

    return viols, constraint_index


def evaluate_constraints_batch(features_list, meter_vals, position_ids, position_sizes, constraint_names):
    """Evaluate constraints for multiple lines at once.

    Constraints with a `.vectorized` attribute are dispatched automatically.
    The unres_within/unres_across constraints use legacy per-line evaluation.

    Args:
        features_list: list of L feature dicts, each with arrays of shape (N,)
        meter_vals: (S, N) bool
        position_ids: (S, N) int
        position_sizes: (S, N) int
        constraint_names: list of constraint name strings

    Returns:
        all_viols: (L, S, N, C) int8
        constraint_index: dict
    """
    from .constraint_utils import get_all_constraints

    S, N = meter_vals.shape
    L = len(features_list)
    C = len(constraint_names)
    constraint_index = {name: i for i, name in enumerate(constraint_names)}

    # stack features: (L, N)
    stressed = np.stack([f["stressed"] for f in features_list])
    heavy = np.stack([f["heavy"] for f in features_list])
    strong = np.stack([f["strong"] for f in features_list])
    weak = np.stack([f["weak"] for f in features_list])
    word_ids = np.stack([f["word_ids"] for f in features_list])
    func_word = np.stack([f["func_word"] for f in features_list])
    phrasal_stress = np.stack([f["phrasal_stress"] for f in features_list])
    has_phrasal = bool(np.any(phrasal_stress != 0))

    all_viols = np.zeros((L, S, N, C), dtype=np.int8)

    # build feature dict for vectorized constraints
    features = {
        "stressed": stressed[:, None, :],     # (L, 1, N)
        "heavy": heavy[:, None, :],
        "strong": strong[:, None, :],
        "weak": weak[:, None, :],
        "func_word": func_word[:, None, :],
        "word_ids": word_ids[:, None, :],
        "phrasal_stress": phrasal_stress[:, None, :],  # (L, 1, N)
        "has_phrasal": has_phrasal,
        "word_ids_raw": word_ids,              # (L, N) for per-line ops
        "is_strong_pos": meter_vals[None, :, :],  # (1, S, N)
        "is_weak_pos": ~meter_vals[None, :, :],
        "position_ids": position_ids,          # (S, N)
        "position_sizes": position_sizes,      # (S, N)
        "L": L, "S": S, "N": N,
    }

    all_constraints = get_all_constraints()

    for cname in constraint_names:
        ci = constraint_index[cname]
        cfunc = all_constraints.get(cname)

        # use vectorized implementation if available
        if cfunc is not None and cfunc.vectorized is not None:
            all_viols[:, :, :, ci] = cfunc.vectorized(features)
        elif cname in ("unres_within", "unres_across"):
            # legacy per-line evaluation for word-boundary constraints
            for li in range(L):
                feats_i = features_list[li]
                wi = feats_i["word_ids"][None, :]
                hi = feats_i["heavy"][None, :]
                si = feats_i["stressed"][None, :]
                fi = feats_i["func_word"][None, :]
                if cname == "unres_within":
                    _eval_unres_within(all_viols[li], ci, position_ids, position_sizes,
                                       wi, hi, si, S, N)
                else:
                    _eval_unres_across(all_viols[li], ci, position_ids, position_sizes,
                                        wi, fi, meter_vals, S, N)

    return all_viols, constraint_index


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


def _get_torch_device():
    """Get the best available torch device (MPS, CUDA, or None for CPU-only)."""
    try:
        import torch
        if torch.cuda.is_available():
            return torch.device("cuda")
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
    except ImportError:
        pass
    return None

_torch_device = None
_torch_checked = False

def get_device():
    global _torch_device, _torch_checked
    if not _torch_checked:
        _torch_device = _get_torch_device()
        _torch_checked = True
    return _torch_device

# eagerly initialize on import to avoid cold-start penalty during first parse
get_device()


def compute_bounding(viols, constraint_index):
    """Compute harmonic bounding: mark scansions dominated by others."""
    v = viols.sum(axis=1)  # (S, C)
    return _bound_viol_sums(v)


def _bound_viol_sums(v):
    """Bound a single (S, C) violation-sum matrix. Returns (S,) bool mask."""
    S = v.shape[0]
    if S <= 1:
        return np.ones(S, dtype=bool)

    # fast path: if any scansion has 0 on all constraints, it bounds everything else
    totals = v.sum(axis=1)  # (S,)
    perfect = totals == 0
    if perfect.any():
        # perfect scansions are unbounded; everything with >0 total is bounded
        # but among perfect scansions, none bounds another (all equal)
        return perfect

    device = get_device()
    if device is not None:
        return _compute_bounding_torch(v, device)
    return _compute_bounding_numpy(v)


def compute_bounding_batch(viol_sums):
    """Batch bounding for multiple lines at once.

    Args:
        viol_sums: (L, S, C) — violation sums per constraint per scansion per line

    Returns:
        (L, S) bool — unbounded mask per line
    """
    L, S, C = viol_sums.shape
    if S <= 1:
        return np.ones((L, S), dtype=bool)

    # fast path: lines with a perfect (all-zero) scansion
    totals = viol_sums.sum(axis=2)  # (L, S)
    has_perfect = (totals == 0).any(axis=1)  # (L,) bool

    if has_perfect.all():
        # all lines have at least one perfect parse — shortcut
        return totals == 0

    if not has_perfect.any():
        # no shortcuts possible, full pairwise
        device = get_device()
        if device is not None:
            return _compute_bounding_batch_torch(viol_sums, device)
        return _compute_bounding_batch_numpy(viol_sums)

    # mixed: shortcut some lines, full pairwise for others
    result = np.zeros((L, S), dtype=bool)

    # perfect lines: unbounded = score 0
    perfect_idx = np.where(has_perfect)[0]
    result[perfect_idx] = (totals[perfect_idx] == 0)

    # non-perfect lines: full pairwise bounding
    nonperfect_idx = np.where(~has_perfect)[0]
    if len(nonperfect_idx) > 0:
        sub = viol_sums[nonperfect_idx]
        device = get_device()
        if device is not None:
            sub_result = _compute_bounding_batch_torch(sub, device)
        else:
            sub_result = _compute_bounding_batch_numpy(sub)
        result[nonperfect_idx] = sub_result

    return result


def _compute_bounding_batch_numpy(viol_sums):
    """Numpy batched bounding for L lines."""
    L, S, C = viol_sums.shape
    # (L, S, 1, C) - (L, 1, S, C) -> (L, S, S, C)
    diff = viol_sums[:, :, None, :] - viol_sums[:, None, :, :]
    i_leq_j = (diff <= 0).all(axis=3)  # (L, S, S)
    i_lt_j = i_leq_j & (diff < 0).any(axis=3)
    bounded = i_lt_j.any(axis=1)  # (L, S)
    return ~bounded


def _compute_bounding_batch_torch(viol_sums, device):
    """GPU batched bounding for L lines in a single kernel launch."""
    import torch
    vt = torch.tensor(viol_sums, dtype=torch.int16, device=device)  # (L, S, C)
    diff = vt[:, :, None, :] - vt[:, None, :, :]  # (L, S, S, C)
    i_leq_j = (diff <= 0).all(dim=3)
    i_lt_j = i_leq_j & (diff < 0).any(dim=3)
    bounded = i_lt_j.any(dim=1)  # (L, S)
    return ~bounded.cpu().numpy()


def _compute_bounding_numpy(v):
    """Numpy fallback for harmonic bounding (single line)."""
    diff = v[:, None, :] - v[None, :, :]  # (S, S, C)
    i_leq_j = (diff <= 0).all(axis=2)
    i_lt_j = i_leq_j & (diff < 0).any(axis=2)
    bounded = i_lt_j.any(axis=0)
    return ~bounded


def _compute_bounding_torch(v, device):
    """GPU-accelerated harmonic bounding via PyTorch (single line)."""
    import torch
    vt = torch.tensor(v, dtype=torch.int16, device=device)
    diff = vt[:, None, :] - vt[None, :, :]  # (S, S, C)
    i_leq_j = (diff <= 0).all(dim=2)
    i_lt_j = i_leq_j & (diff < 0).any(dim=2)
    bounded = i_lt_j.any(dim=0)
    return ~bounded.cpu().numpy()


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

        # store ALL scansions with their bounded status
        self._all_scansions = list(scansions)
        self._all_viols = viols  # (S, N, C)
        self._unbounded_mask = unbounded_mask  # (S,) bool
        self._constraint_index = constraint_index
        self._constraint_names = list(constraint_index.keys())
        self._sylls = sylls
        self._built_parses = {}  # cache: scansion index -> Parse
        self._best_idx = None
        self._bound_init = True
        self._num = None

        # unbounded indices for fast access
        self._unbounded_indices = np.where(unbounded_mask)[0]

        # compute scores for ranking (weighted violation sums)
        zones = getattr(meter, 'zones', None)
        zone_weights = getattr(meter, 'zone_weights', None)

        if zones is not None and zone_weights is not None:
            # zone-aware scoring: split (S, N, C) -> (S, C*Z), weight with zone weights
            from .maxent import zone_split, make_zone_names
            zone_viols = zone_split(viols, zones)  # (S, C*Z)
            zone_names = make_zone_names(self._constraint_names, viols.shape[1], zones)
            weights = np.array([zone_weights.get(c, 1) for c in zone_names])
            self._all_scores = (zone_viols * weights[None, :]).sum(axis=1)  # (S,)
        else:
            constraint_weights = meter.constraints
            weights = np.array([constraint_weights.get(c, 1) for c in self._constraint_names])
            all_viols_sum = viols.sum(axis=1)  # (S, C)
            self._all_scores = (all_viols_sum * weights[None, :]).sum(axis=1)  # (S,)

        # scores for unbounded only
        self._scores = self._all_scores[self._unbounded_indices]

    def __len__(self):
        return len(self._all_scansions)

    def __bool__(self):
        return len(self._all_scansions) > 0

    @property
    def num_parses(self):
        return len(self._unbounded_indices)

    @property
    def num_unbounded(self):
        return len(self._unbounded_indices)

    @property
    def best_parse(self):
        if len(self._unbounded_indices) == 0:
            return None
        if self._best_idx is None:
            # best among unbounded
            self._best_idx = int(self._unbounded_indices[self._scores.argmin()])
        return self._get_parse(self._best_idx, rank=1)

    @property
    def best_parses(self):
        from .parselists import ParseList
        bp = self.best_parse
        return ParseList([bp], parse_unit=self.parse_unit, parent=self.parent) if bp else ParseList([], parse_unit=self.parse_unit, parent=self.parent)

    @property
    def unbounded(self):
        """Unbounded parses sorted by score (best first)."""
        from .parselists import ParseList
        sorted_idx = self._unbounded_indices[np.argsort(self._scores)]
        return ParseList(
            [self._get_parse(int(i)) for i in sorted_idx],
            parse_unit=self.parse_unit, parent=self.parent,
        )

    @property
    def bounded(self):
        from .parselists import ParseList
        bounded_indices = np.where(~self._unbounded_mask)[0]
        bounded_scores = self._all_scores[bounded_indices]
        sorted_idx = bounded_indices[np.argsort(bounded_scores)]
        return ParseList(
            [self._get_parse(int(i), is_bounded=True) for i in sorted_idx],
            parse_unit=self.parse_unit, parent=self.parent,
        )

    @property
    def data(self):
        """All parses sorted by score (best first), unbounded before bounded."""
        sorted_idx = np.argsort(self._all_scores)
        return [self._get_parse(int(i), is_bounded=not self._unbounded_mask[i])
                for i in sorted_idx]

    def __iter__(self):
        """Iterate all parses sorted by score."""
        sorted_idx = np.argsort(self._all_scores)
        for i in sorted_idx:
            yield self._get_parse(int(i), is_bounded=not self._unbounded_mask[i])

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            indices = range(*idx.indices(len(self._all_scansions)))
            return [self._get_parse(i, is_bounded=not self._unbounded_mask[i]) for i in indices]
        return self._get_parse(idx, is_bounded=not self._unbounded_mask[idx])

    @property
    def scope(self):
        return self.parse_unit

    @property
    def line(self):
        """Get the line this parse list belongs to."""
        if self.parent is not None:
            return getattr(self.parent, 'line', self.parent)
        # DF path: find line from text's _line_parse_results
        unit_num = getattr(self, '_unit_num', None)
        text = getattr(self, '_text', None)
        if unit_num is not None and text is not None:
            for line in text.lines:
                if line.num == unit_num:
                    return line
        return None

    @property
    def all(self):
        """Alias for data — all parses including bounded."""
        return self.data

    def _repr_html_(self):
        from .parselists import ParseList
        return ParseList(self.data, parse_unit=self.parse_unit, parent=self.parent)._repr_html_()

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

    def _get_parse(self, idx, rank=None, is_bounded=False):
        """Build a Parse object for the given index, caching the result."""
        if idx in self._built_parses:
            p = self._built_parses[idx]
            if is_bounded:
                p.is_bounded = True
            return p

        parse = _build_single_parse(
            idx, self._all_scansions[idx], self._all_viols, self._constraint_index,
            self._constraint_names, self._sylls, self.wordtokens, self.meter,
            rank=rank,
        )
        parse.is_bounded = is_bounded
        parse.parent = self
        self._built_parses[idx] = parse
        return parse

    # ParseList interface compatibility
    def stats_d(self, **kwargs):
        from .parselists import ParseList
        return ParseList(self.data, parse_unit=self.parse_unit, parent=self.parent).stats_d(**kwargs)

    def stats(self, **kwargs):
        from .parselists import ParseList
        df = ParseList(self.data, parse_unit=self.parse_unit, parent=self.parent).stats(**kwargs)
        # inject unit num (e.g. line_num) for DF-path results
        unit_num = getattr(self, '_unit_num', None)
        if unit_num is not None and self.parse_unit + '_num' not in df.columns:
            df.insert(0, self.parse_unit + '_num', unit_num)
        return df

    def to_html(self, as_str=False, css=None, **kwargs):
        """Render HTML via wordtokens, not through Parse (avoids recursion)."""
        bp = self.best_parse
        if bp is None:
            return ""
        from ..imports import HTML_CSS, to_html, get_attr_str
        if css is None:
            css = HTML_CSS
        out = self.wordtokens.to_html(as_str=True, css=css) if self.wordtokens and hasattr(self.wordtokens, 'to_html') else str(self.wordtokens)
        reprstr = get_attr_str(bp.attrs, bad_keys={"txt", "line_txt"})
        out += f'<div class="miniquote">⎿ {reprstr}</div>'
        return to_html(out, as_str=as_str)

    def render(self, **kwargs):
        bp = self.best_parse
        return bp.render(**kwargs) if bp else ""

    @property
    def num_all(self):
        """Total unique scansions (for compatibility with ParseList)."""
        return len(self._all_scansions)

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
    wordforms = wordtokens.wordforms if wordtokens is not None else None
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
