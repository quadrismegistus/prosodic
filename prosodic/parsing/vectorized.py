"""Vectorized metrical parser using numpy for batch constraint evaluation."""

import numpy as np
from collections import defaultdict
from ..imports import *

# Cap on how many pronunciation-variant combinations to enumerate per line in
# the DF parse path. Real verse lines stay well under this (a line needs ~12
# binary-ambiguous words to exceed it); beyond it we fall back to a diagonal
# subset with a warning rather than risk a combinatorial blowup on the batch path.
MAX_FORM_COMBOS = 4096


def _pool_meter_str(lpl, i):
    """+/- meter string for scansion i of a LazyParseList (matches Parse.meter_str)."""
    if lpl._meter_vals is not None:
        return "".join("+" if v else "-" for v in lpl._meter_vals[i])
    return "".join("+" if x == "s" else "-" for x in lpl._all_scansions[i])


def _pool_combo_parses(combo_lpls, meter, parse_unit, bound_zones, parent=None,
                       syll_builder=None):
    """Pool unbounded parses across pronunciation-variant combos (Prosodic v1/v2
    semantics: the unbounded set = scansions optimal under ANY pronunciation).

    Unions each combo's unbounded parses, cross-bounds them on the (zone-aware)
    violation-count vector, dedups by meter string keeping the min-score
    representative, and returns a LazyParseList carrying the pooled survivors so
    the numpy-backed consumers (``get_parses_df`` etc.) keep working. Each
    survivor keeps its OWN combo's syllables (``sylls_by_scansion``) so a parse
    realized under a stressed pronunciation reports that pronunciation's
    form_idx / stress, not the primary combo's.

    Only each combo's *unbounded* parses need pooling: a parse bounded within its
    own combo is dominated by a combo-mate, which is itself either kept or
    dominated by a cross-combo parse — so by transitivity it stays bounded.
    Domination matches ``compute_bounding``: ``vk <= vj`` on all constraints and
    ``vk < vj`` on at least one.

    ``syll_builder(row_idx) -> [SyllData,...]`` (optional) defers SyllData
    construction: combos pass ``sylls=None`` and only the combos that actually
    surface a surviving parse get their syllables built, so lines with many
    pronunciation combos don't pay to materialize syllables for all of them.
    """
    from .parselists import ParseList
    combo_lpls = [l for l in combo_lpls if l is not None]
    if not combo_lpls:
        return ParseList([], parse_unit=parse_unit, parent=parent)

    def ensure_sylls(lpl):
        # build (and memoize on the combo) SyllData only when a combo is returned
        # or contributes a surviving parse
        if lpl._sylls is None and syll_builder is not None:
            lpl._sylls = syll_builder(lpl._syll_row_idx)
        return lpl._sylls

    # Mixed syllable counts across pronunciations can't share one (S, N, C)
    # array; pooling is rare there, so fall back to the best single combo (a
    # valid LazyParseList) for that line.
    if len({l._all_viols.shape[1] for l in combo_lpls}) != 1:
        best = min(combo_lpls,
                   key=lambda l: float(l._scores.min()) if l._scores.size else float('inf'))
        ensure_sylls(best)
        best.parent = parent
        return best

    ci = combo_lpls[0]._constraint_index
    S = len(combo_lpls[0]._all_scansions)

    # Meter strings depend only on the scansion, which is shared across same-N
    # combos — compute the S strings ONCE (not per combo x scansion).
    mv0 = combo_lpls[0]._meter_vals
    if mv0 is not None:
        ms_arr = ["".join("+" if v else "-" for v in mv0[i]) for i in range(S)]
    else:
        ms_arr = ["".join("+" if x == "s" else "-" for x in combo_lpls[0]._all_scansions[i])
                  for i in range(S)]

    # Cross-bound ONLY the combos' unbounded parses (pure numpy, tiny): a parse
    # bounded within its combo stays bounded by transitivity, so the full
    # per-line compute_bounding is unnecessary. A (combo, scansion) is pooled-
    # unbounded iff within-combo unbounded AND not dominated by another combo's
    # unbounded parse.
    # Domination: ZONE-aware within the same syllable count (fitted meters bound
    # on the feature space they score on), FLAT (C,) across different N (zone
    # boundaries shift with N). Identical rule to _pool_candidates. Unfitted
    # meter (bound_zones=None): zone == flat.
    urank, uidx, fvecs, zvecs, uN = [], [], [], [], []
    for rank, lpl in enumerate(combo_lpls):
        for i in lpl._unbounded_indices:
            i = int(i)
            urank.append(rank); uidx.append(i)
            fvecs.append(lpl._all_viols[i].sum(axis=0))
            zvecs.append(_zone_split_batch(lpl._all_viols[None, i:i + 1], bound_zones)[0, 0])
            uN.append(lpl._all_viols.shape[1])
    pool_unb = set()  # {(rank, scan_idx)} surviving cross-bounding
    if fvecs:
        fv = np.array(fvecs); zv = np.array(zvecs); nn = np.array(uN)
        same_n = nn[:, None] == nn[None, :]
        zdom = (zv[:, None, :] <= zv[None, :, :]).all(axis=2) & (zv[:, None, :] < zv[None, :, :]).any(axis=2)
        fdom = (fv[:, None, :] <= fv[None, :, :]).all(axis=2) & (fv[:, None, :] < fv[None, :, :]).any(axis=2)
        dom = np.where(same_n, zdom, fdom)
        np.fill_diagonal(dom, False)
        alive = ~dom.any(axis=0)
        pool_unb = {(urank[k], uidx[k]) for k in range(len(urank)) if alive[k]}

    # Fast path: if the canonical combo (rank 0) already accounts for the entire
    # pooled unbounded set — no alternate pronunciation adds or bounds anything —
    # pooling is a no-op; return combo 0 directly and skip the rebuild. This is
    # the common case (natural pronunciations usually dominate) and keeps the
    # ambiguous-line cost near the non-pooled path.
    if pool_unb == {(0, int(i)) for i in combo_lpls[0]._unbounded_indices}:
        ensure_sylls(combo_lpls[0])
        combo_lpls[0].parent = parent
        return combo_lpls[0]

    # Dedup by meter string, combo-0-base + overlay (identical rule to
    # _pool_candidates so the DF and entity paths agree): every meter string is
    # represented by the CANONICAL combo (rank 0); a meter string that is
    # pool-unbounded via another pronunciation is upgraded to that combo's
    # (better) parse. Ties thus keep the canonical pronunciation rather than
    # flipping function words to strong-first.
    l0 = combo_lpls[0]
    best_rep = {}  # meter_str -> (sortkey, lpl, scan_idx)
    for i in range(l0._all_viols.shape[0]):
        ms = ms_arr[i]
        sortkey = ((0, i) not in pool_unb, float(l0._all_scores[i]), 0, i)
        cur = best_rep.get(ms)
        if cur is None or sortkey < cur[0]:
            best_rep[ms] = (sortkey, l0, i)
    for rank, lpl in enumerate(combo_lpls):
        if rank == 0:
            continue
        for i in lpl._unbounded_indices:
            i = int(i)
            if (rank, i) not in pool_unb:
                continue
            ms = ms_arr[i]
            sortkey = (False, float(lpl._all_scores[i]), rank, i)
            cur = best_rep.get(ms)
            if cur is None or sortkey < cur[0]:
                best_rep[ms] = (sortkey, lpl, i)
    reps = sorted(best_rep.values(), key=lambda r: r[0])  # unbounded first, then score, canonical

    scans = [lpl._all_scansions[i] for _, lpl, i in reps]
    viols = np.stack([lpl._all_viols[i] for _, lpl, i in reps])          # (P, N, C)
    unb_mask = np.array([not sk[0] for sk, _, _ in reps], dtype=bool)    # sk[0] = is_bounded
    sylls_by = [ensure_sylls(lpl) for _, lpl, i in reps]                 # SyllData built here only
    rowidx_by = [lpl._syll_row_idx for _, lpl, i in reps]
    # entity combos have no DF row indices (_syll_row_idx is None), which yields a
    # list of Nones. Collapse it to a single None so get_parses_df's
    # `_syll_row_idx_by_scansion is not None` branch isn't tripped into iterating a
    # None element (TypeError). Same for sylls_by if a combo yielded none.
    rowidx0 = rowidx_by[0]
    if all(r is None for r in rowidx_by):
        rowidx_by = None
    if all(s is None for s in sylls_by):
        sylls_by = None
    have = lambda a: all(getattr(lpl, a) is not None for _, lpl, _ in reps)
    mv = np.stack([lpl._meter_vals[i] for _, lpl, i in reps]) if have('_meter_vals') else None
    pi = np.stack([lpl._position_ids[i] for _, lpl, i in reps]) if have('_position_ids') else None
    ps = np.stack([lpl._position_sizes[i] for _, lpl, i in reps]) if have('_position_sizes') else None
    # carry the canonical combo's wordtokens (entity path) so pooled parses can
    # walk to WordTokens for rendering / Parse.concat; None on the DF path.
    pooled = LazyParseList(
        combo_lpls[0].wordtokens, meter, scans, viols, ci, unb_mask,
        sylls_by[0] if sylls_by is not None else ensure_sylls(reps[0][1]),
        parse_unit=parse_unit,
        syll_row_idx=rowidx0, meter_vals=mv, position_ids=pi, position_sizes=ps,
        sylls_by_scansion=sylls_by, syll_row_idx_by_scansion=rowidx_by,
    )
    pooled.parent = parent
    return pooled


def _pool_candidates(candidates, meter, ci_use, bound_zones, build_sylls, parse_unit):
    """DF-path pooling from RAW candidate tuples (viols, mask, scansions, rows,
    meter_vals, position_ids, position_sizes) — one per pronunciation combo.

    Same semantics as ``_pool_combo_parses`` but avoids constructing a
    LazyParseList (and its per-combo score/scansion setup) for every combo: the
    cross-bound is computed straight from the raw viol arrays, and a combo's
    LazyParseList is materialized only when it is actually returned or overlays a
    surviving parse. Lines with many pronunciation combos (a cartesian blow-up)
    thus stay close to the non-pooled cost. Combo 0 is the canonical (all
    form_idx 0) pronunciation.
    """
    from .parselists import ParseList
    candidates = [c for c in candidates if c is not None]
    if not candidates:
        return ParseList([], parse_unit=parse_unit)

    lpl_cache = {}
    def get_lpl(rank):
        lpl = lpl_cache.get(rank)
        if lpl is None:
            v, m, scans, rows, mv, pi, ps = candidates[rank]
            lpl = LazyParseList(None, meter, scans, v, ci_use, m, None,
                                parse_unit=parse_unit, syll_row_idx=rows,
                                meter_vals=mv, position_ids=pi, position_sizes=ps)
            lpl_cache[rank] = lpl
        if lpl._sylls is None:
            lpl._sylls = build_sylls(lpl._syll_row_idx)
        return lpl

    N_of = {r: candidates[r][0].shape[1] for r in range(len(candidates))}

    # Cross-bound the combos' unbounded parses straight from raw viols.
    # Domination uses the ZONE-aware vector between parses of the SAME syllable
    # count (a fitted/zoned meter must bound on the same (constraint x zone)
    # feature space it scores on — see test_zone_aware_bounding_mechanism), and
    # the FLAT (C,) vector between parses of DIFFERENT N (zone boundaries shift
    # with N, so zone vectors are not comparable across lengths; flat counts are
    # N-independent, so a 1-syllable "fire" parse can still dominate a 2-syllable
    # one, exactly as v1). For an unfitted meter (bound_zones=None) zone==flat.
    urank, uidx, fvecs, zvecs, uN = [], [], [], [], []
    for rank, c in enumerate(candidates):
        ui = np.where(c[1])[0]
        if not len(ui):
            continue
        fsum = c[0][ui].sum(axis=1)                               # (len(ui), C) flat
        zsum = _zone_split_batch(c[0][ui][None], bound_zones)[0]  # (len(ui), C[*Z]) zone
        N = c[0].shape[1]
        for j, i in enumerate(ui):
            urank.append(rank); uidx.append(int(i))
            fvecs.append(fsum[j]); zvecs.append(zsum[j]); uN.append(N)
    pool_unb = set()
    if fvecs:
        fv = np.array(fvecs); zv = np.array(zvecs); nn = np.array(uN)
        same_n = nn[:, None] == nn[None, :]
        zdom = (zv[:, None, :] <= zv[None, :, :]).all(axis=2) & (zv[:, None, :] < zv[None, :, :]).any(axis=2)
        fdom = (fv[:, None, :] <= fv[None, :, :]).all(axis=2) & (fv[:, None, :] < fv[None, :, :]).any(axis=2)
        dom = np.where(same_n, zdom, fdom)
        np.fill_diagonal(dom, False)
        alive = ~dom.any(axis=0)
        pool_unb = {(urank[k], uidx[k]) for k in range(len(urank)) if alive[k]}
    if not pool_unb:
        return get_lpl(0)

    def build_for_N(N, full_ok=True):
        """Pooled LazyParseList over the combos whose scansions have N syllables
        (they share a scansion space): combo-base + overlay, exactly as the
        single-N path. `pool_unb` already reflects cross-N domination. `full_ok`
        permits the fast-path shortcut (return the base combo's full scansion
        set); the mixed-N caller passes full_ok=False so every length goes through
        the same dedup-by-meter-string overlay, keeping the ragged list's
        per-length representation symmetric (bounded reporting / sylls_by_scansion
        set on every length, not just the overlaid ones)."""
        group = sorted(r for r in range(len(candidates)) if N_of[r] == N)
        base = group[0]
        pool_unb_N = {(r, i) for (r, i) in pool_unb if N_of[r] == N}
        if full_ok and pool_unb_N == {(base, int(i)) for i in np.where(candidates[base][1])[0]}:
            return get_lpl(base)                       # base combo accounts for all of N
        l0 = get_lpl(base)
        best_rep = {}  # meter_str -> (sortkey, rank, scan_idx)
        for i in range(l0._all_viols.shape[0]):
            ms = _pool_meter_str(l0, i)
            sk = ((base, i) not in pool_unb, float(l0._all_scores[i]), base, i)
            cur = best_rep.get(ms)
            if cur is None or sk < cur[0]:
                best_rep[ms] = (sk, base, i)
        for rank in group[1:]:
            for i in np.where(candidates[rank][1])[0]:
                i = int(i)
                if (rank, i) not in pool_unb:
                    continue
                lr = get_lpl(rank)
                ms = _pool_meter_str(lr, i)
                sk = (False, float(lr._all_scores[i]), rank, i)
                cur = best_rep.get(ms)
                if cur is None or sk < cur[0]:
                    best_rep[ms] = (sk, rank, i)
        reps = sorted(best_rep.values(), key=lambda r: r[0])
        scans = [get_lpl(rank)._all_scansions[i] for _, rank, i in reps]
        viols = np.stack([get_lpl(rank)._all_viols[i] for _, rank, i in reps])
        unb_mask = np.array([not sk[0] for sk, _, _ in reps], dtype=bool)
        sylls_by = [get_lpl(rank)._sylls for _, rank, i in reps]
        rowidx_by = [get_lpl(rank)._syll_row_idx for _, rank, i in reps]
        mv = np.stack([get_lpl(rank)._meter_vals[i] for _, rank, i in reps])
        pi = np.stack([get_lpl(rank)._position_ids[i] for _, rank, i in reps])
        ps = np.stack([get_lpl(rank)._position_sizes[i] for _, rank, i in reps])
        return LazyParseList(
            None, meter, scans, viols, ci_use, unb_mask, sylls_by[0], parse_unit=parse_unit,
            syll_row_idx=rowidx_by[0], meter_vals=mv, position_ids=pi, position_sizes=ps,
            sylls_by_scansion=sylls_by, syll_row_idx_by_scansion=rowidx_by,
        )

    # Survivors may span multiple syllable counts (e.g. "fire" 1~2). Build one
    # pooled LazyParseList per length; a single length is the common case.
    surv_Ns = sorted({N_of[rank] for (rank, i) in pool_unb},
                     key=lambda N: (N != N_of[0], N))   # canonical combo's N first
    if len(surv_Ns) == 1:
        return build_for_N(surv_Ns[0])

    # Survivors span multiple syllable counts (e.g. "fire" 1~2). A single
    # (P, N, C) array can't hold both lengths, so concatenate each length's
    # pooled scansions into a RAGGED LazyParseList (per-scansion viols/meter_vals
    # of different N). The unbounded set thus keeps co-optimal parses of BOTH
    # lengths — matching v1. Cross-length domination is already in pool_unb, so
    # each sub-list's mask is correct.
    scans, viols, mv, pi, ps, sylls_by, rowidx_by, unb = [], [], [], [], [], [], [], []
    for N in surv_Ns:
        sub = build_for_N(N, full_ok=False)
        sbs, rbs = sub._sylls_by_scansion, sub._syll_row_idx_by_scansion
        for i in range(len(sub._all_scansions)):
            scans.append(sub._all_scansions[i])
            viols.append(sub._all_viols[i])              # (N, C)
            mv.append(sub._meter_vals[i])
            pi.append(sub._position_ids[i])
            ps.append(sub._position_sizes[i])
            sylls_by.append(sbs[i] if sbs is not None else sub._sylls)
            rowidx_by.append(rbs[i] if rbs is not None else sub._syll_row_idx)
            unb.append(bool(sub._unbounded_mask[i]))
    return LazyParseList(
        None, meter, scans, viols, ci_use, np.array(unb, dtype=bool), sylls_by[0],
        parse_unit=parse_unit, syll_row_idx=rowidx_by[0], meter_vals=mv,
        position_ids=pi, position_sizes=ps,
        sylls_by_scansion=sylls_by, syll_row_idx_by_scansion=rowidx_by,
    )


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
    # gradient phrasal stress (MetricalTree port): -1 sentinel for NaN /
    # absent, so both `> 0` and `== 0` threshold tests stay silent there
    has_gradient = 'tstress' in syll_df.columns and syll_df['tstress'].notna().any()
    if has_gradient:
        all_pstress = syll_df['pstress'].astype(float).fillna(-1.0).values.astype(np.float32)
        all_tstress = syll_df['tstress'].astype(float).fillna(-1.0).values.astype(np.float32)
    else:
        all_pstress = np.full(len(syll_df), -1.0, dtype=np.float32)
        all_tstress = np.full(len(syll_df), -1.0, dtype=np.float32)
    # grid stress (RPPR grid): -1 sentinel where NaN/absent, same as tstress
    if has_gradient and 'gstress' in syll_df.columns:
        all_gstress = syll_df['gstress'].astype(float).fillna(-1.0).values.astype(np.float32)
    else:
        all_gstress = np.full(len(syll_df), -1.0, dtype=np.float32)
    if has_gradient and 'pstrength' in syll_df.columns:
        all_pstrength = syll_df['pstrength'].astype(float).fillna(-1.0).values.astype(np.float32)
    else:
        all_pstrength = np.full(len(syll_df), -1.0, dtype=np.float32)

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
    if len(f0_line_s) == 0:
        # No parseable (non-punctuation) syllables, e.g. all-punctuation input.
        # Leave line_data empty so the function returns no per-line results.
        f0_breaks = np.array([0], dtype=int)
    else:
        f0_breaks = np.where(np.diff(f0_line_s, prepend=f0_line_s[0]-1) != 0)[0]
        f0_breaks = np.append(f0_breaks, len(f0_line_s))

    # line_data: line_num -> (feats, sylls, has_ambig, form_variants)
    # form_variants: list of row-index arrays for each form combination
    line_data = {}
    short_lines = []  # <2 syllables: can't form a foot, but must not vanish (C8)

    for i in range(len(f0_breaks) - 1):
        ln = int(f0_line_s[f0_breaks[i]])
        rows = f0_idx_s[f0_breaks[i]:f0_breaks[i+1]]
        n = len(rows)
        if n < 2:
            short_lines.append(ln)
            continue

        sylls = [
            SyllData(ipa=all_ipa[r], txt=all_txt[r],
                     is_stressed=bool(all_stressed[r]), is_heavy=bool(all_heavy[r]),
                     is_strong=bool(all_strong[r]), is_weak=bool(all_weak[r]),
                     word_num=int(all_wnum[r]))
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
            "pstress": all_pstress[rows].astype(np.float32),
            "tstress": all_tstress[rows].astype(np.float32),
            "gstress": all_gstress[rows].astype(np.float32),
            "pstrength": all_pstrength[rows].astype(np.float32),
        }

        # check if any word in this line has multiple forms
        line_np_mask = np_line == ln
        has_ambig = bool(meter.resolve_optionality and (np_nforms[line_np_mask] > 1).any())
        line_data[ln] = (feats, sylls, has_ambig, rows)

    # --- Pre-build ambiguous form variants using numpy ---
    # Enumerate the FULL cartesian product of per-word pronunciation choices,
    # matching the entity path's iter_wordtoken_matrix. The previous code built
    # only "diagonal" combos (every word simultaneously at form fi), which
    # missed most combinations and could make text.parse() return a suboptimal
    # best parse on lines with several ambiguous words (AUDIT C9/M3). The
    # (0,0,...,0) combo is enumerated first, so variant 0 stays == f0_rows.
    ambig_form_variants = {}  # line_num -> list of row-index arrays
    for ln, (feats, sylls, has_ambig, f0_rows) in line_data.items():
        if not has_ambig:
            continue
        line_mask = np_line == ln
        line_rows = non_punc_idx[line_mask]
        line_wn = np_wnum[line_mask]
        line_fi = np_form[line_mask]
        # per word (in line order): available form_idx -> that form's syllable rows
        per_word_forms = []
        for wn in np.unique(line_wn):
            wmask = line_wn == wn
            wrows = line_rows[wmask]
            wfi = line_fi[wmask]
            per_word_forms.append({int(f): wrows[wfi == f] for f in np.unique(wfi)})
        choices = [sorted(fw.keys()) for fw in per_word_forms]
        n_combos = 1
        for c in choices:
            n_combos *= len(c)
        if n_combos > MAX_FORM_COMBOS:
            # Pathological ambiguity: fall back to the diagonal set so the batch
            # path can't blow up. Rare; flagged so it isn't silent.
            log.warning(
                f"line {ln}: {n_combos} pronunciation combinations exceed "
                f"MAX_FORM_COMBOS={MAX_FORM_COMBOS}; using diagonal subset "
                f"(best parse may be approximate for this line)"
            )
            max_fi = int(line_fi.max())
            variants = [f0_rows]
            for fi in range(1, max_fi + 1):
                sel = []
                for wi, wn in enumerate(np.unique(line_wn)):
                    fw = per_word_forms[wi]
                    sel.append(fw[fi] if fi in fw else fw[0])
                variants.append(np.concatenate(sel))
        else:
            variants = [
                np.concatenate([per_word_forms[wi][c] for wi, c in enumerate(combo)])
                for combo in itertools.product(*choices)
            ]
        ambig_form_variants[ln] = variants

    # --- Group by nsylls and process ---
    nsyll_groups = defaultdict(list)
    results = {}
    # single-syllable (or empty) units get an empty parse list rather than
    # silently disappearing from results (AUDIT C8)
    for ln in short_lines:
        results[ln] = ParseList([], parse_unit=meter.parse_unit)
    oversized = []
    for ln, (feats, sylls, has_ambig, _) in line_data.items():
        nsylls = len(feats["stressed"])
        if nsylls > MAX_SYLL_IN_PARSE_UNIT:
            oversized.append((ln, nsylls))
            results[ln] = ParseList([], parse_unit=meter.parse_unit)
            continue
        nsyll_groups[nsylls].append(ln)
    if oversized:
        unit_name = line_col.split('_')[0]
        tail = "; falling back to linepart parsing" if unit_name == 'line' else ""
        log.warning(
            f"{len(oversized)} {unit_name}(s) exceed MAX_SYLL_IN_PARSE_UNIT="
            f"{MAX_SYLL_IN_PARSE_UNIT} and were not parsed "
            f"(max={max(n for _, n in oversized)} sylls){tail}"
        )


    constraint_names = list(meter.constraints.keys())
    bound_zones = _bounding_zones(meter)  # zone-aware bounding when zone_weights set

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
            all_viol_sums = _zone_split_batch(all_viols_4d, bound_zones)
            unbounded_masks = compute_bounding_batch(all_viol_sums)

            for i, ln in enumerate(simple_lines):
                pl = LazyParseList(
                    None, meter, scansions, all_viols_4d[i], constraint_index,
                    unbounded_masks[i], line_data[ln][1], parse_unit=meter.parse_unit,
                    syll_row_idx=line_data[ln][3],
                    meter_vals=meter_vals, position_ids=position_ids,
                    position_sizes=position_sizes,
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
            "pstress": all_pstress[rows].astype(np.float32),
            "tstress": all_tstress[rows].astype(np.float32),
            "gstress": all_gstress[rows].astype(np.float32),
            "pstrength": all_pstrength[rows].astype(np.float32),
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
                ambig_viol_sums = _zone_split_batch(ambig_viols_4d, bound_zones)
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
                d_viol_sums = _zone_split_batch(d_viols_4d, bound_zones)
                d_masks = compute_bounding_batch(d_viol_sums)
                for i, item in enumerate(items):
                    diff_results[id(item)] = (d_viols_4d[i], d_masks[i], wscans,
                                              wmv, wpi, wps)

            # Phase 4: pick best form per ambig line
            # ln -> [(viols, unbounded, scansions, rows, mv, pi, ps)]
            line_candidates = defaultdict(list)

            for i, (ln, fi, rows) in enumerate(same_nsylls_meta):
                line_candidates[ln].append((
                    same_nsylls_viols[i], ambig_unbounded[i], scansions, rows,
                    meter_vals, position_ids, position_sizes,
                ))

            for item in diff_nsylls_items:
                ln, fi, rows, feats, wnsylls = item
                if id(item) in diff_results:
                    v, unb, ws, mv, pi_, ps = diff_results[id(item)]
                    line_candidates[ln].append((v, unb, ws, rows, mv, pi_, ps))

            constraint_weights = meter.constraints
            weight_arr = np.array([constraint_weights.get(c, 1) for c in constraint_names])

            pool_forms = getattr(meter, 'pool_forms', True)
            ci_use = constraint_index if constraint_index is not None else {c: i for i, c in enumerate(constraint_names)}

            def _build_sylls(rows):
                return [
                    SyllData(ipa=all_ipa[r], txt=all_txt[r],
                             is_stressed=bool(all_stressed[r]), is_heavy=bool(all_heavy[r]),
                             is_strong=bool(all_strong[r]), is_weak=bool(all_weak[r]),
                             word_num=int(all_wnum[r]))
                    for r in rows
                ]

            def _combo_lpl(viols, unbounded_mask, cand_scansions, rows, mv, pi_, ps, sylls=None):
                return LazyParseList(
                    None, meter, cand_scansions, viols, ci_use,
                    unbounded_mask, sylls, parse_unit=meter.parse_unit,
                    syll_row_idx=rows, meter_vals=mv, position_ids=pi_, position_sizes=ps,
                )

            for ln in ambig_lines:
                candidates = line_candidates.get(ln, [])
                if pool_forms:
                    # v1/v2 semantics: pool + cross-bound all pronunciation combos
                    # straight from the raw candidate arrays. LazyParseLists (and
                    # their syllables) are built lazily — only combo 0 in the
                    # common "canonical pronunciation dominates" case.
                    pl = _pool_candidates(candidates, meter, ci_use, bound_zones,
                                          _build_sylls, meter.parse_unit)
                else:
                    # legacy: report only the single best-scoring combination
                    best_result = None
                    best_score = float('inf')
                    for viols, unbounded_mask, cand_scansions, rows, mv, pi_, ps in candidates:
                        unb_idx = np.where(unbounded_mask)[0]
                        if len(unb_idx) == 0:
                            continue
                        scores = (viols.sum(axis=1) * weight_arr[None, :]).sum(axis=1)
                        ms = float(scores[unb_idx].min())
                        if ms < best_score:
                            best_score = ms
                            best_result = _combo_lpl(viols, unbounded_mask, cand_scansions,
                                                     rows, mv, pi_, ps, sylls=_build_sylls(rows))
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
        if nsylls > MAX_SYLL_IN_PARSE_UNIT:
            all_features.append(None)
            continue
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
        bound_zones = _bounding_zones(meter)  # zone-aware bounding when zone_weights set

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

        # batch simple lines: evaluate ALL constraints at once (self-describing
        # vectorized dispatch), then batch bounding on GPU
        if simple_lines:
            feats_list = [feats for (_, _, feats, _) in simple_lines]
            all_viols_4d, constraint_index = evaluate_constraints_batch(
                feats_list, meter_vals, position_ids, position_sizes, constraint_names
            )  # (L, S, N, C)

            # batch bounding
            all_viol_sums = _zone_split_batch(all_viols_4d, bound_zones)
            unbounded_masks = compute_bounding_batch(all_viol_sums)  # (L, S)

            for i, (idx, wt, feats, sylls) in enumerate(simple_lines):
                pl = LazyParseList(
                    wt, meter, scansions, all_viols_4d[i], constraint_index,
                    unbounded_masks[i], sylls, parse_unit=meter.parse_unit,
                )
                results[idx] = (wt, pl)

        # handle ambiguous lines individually
        pool_forms = getattr(meter, 'pool_forms', True)
        for idx, wt, feats, sylls in ambig_lines:
            combo_lpls = []
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
                wviols_4d, wci = evaluate_constraints_batch(
                    [wfeats], wmv, wpi, wps, constraint_names
                )
                wviols = wviols_4d[0]  # (S, N, C)
                wunb = compute_bounding(wviols, wci, zones=bound_zones)
                wsylls = wfeats["sylls"]
                wpl = LazyParseList(
                    wtl, meter, wscans, wviols, wci, wunb, wsylls,
                    parse_unit=meter.parse_unit, meter_vals=wmv,
                )
                combo_lpls.append(wpl)
                if wpl._scores.size > 0:
                    ms = float(wpl._scores.min())
                    if ms < best_score:
                        best_score = ms
                        best_result = wpl
                if not meter.resolve_optionality:
                    break
            if pool_forms and combo_lpls:
                # v1/v2 semantics: pool + cross-bound all pronunciation combos
                pl = _pool_combo_parses(combo_lpls, meter, meter.parse_unit, bound_zones, parent=wt)
            elif best_result:
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
        "pstress": np.full(n, -1.0, dtype=np.float32),
        "tstress": np.full(n, -1.0, dtype=np.float32),
        "gstress": np.full(n, -1.0, dtype=np.float32),
        "pstrength": np.full(n, -1.0, dtype=np.float32),
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
    pstress = np.full(n, -1.0, dtype=np.float32)
    tstress = np.full(n, -1.0, dtype=np.float32)
    gstress = np.full(n, -1.0, dtype=np.float32)
    pstrength = np.full(n, -1.0, dtype=np.float32)
    if 'tstress' in line_df.columns:
        pstress = line_df['pstress'].astype(float).fillna(-1.0).values.astype(np.float32)
        tstress = line_df['tstress'].astype(float).fillna(-1.0).values.astype(np.float32)
    if 'gstress' in line_df.columns:
        gstress = line_df['gstress'].astype(float).fillna(-1.0).values.astype(np.float32)
    if 'pstrength' in line_df.columns:
        pstrength = line_df['pstrength'].astype(float).fillna(-1.0).values.astype(np.float32)

    return {
        "sylls": sylls,
        "stressed": line_df['is_stressed'].values.astype(bool),
        "heavy": line_df['is_heavy'].values.astype(bool),
        "strong": line_df['is_strong'].values.astype(np.int8),
        "weak": line_df['is_weak'].values.astype(np.int8),
        "word_ids": line_df['word_num'].values.astype(np.int32),
        "func_word": line_df['is_functionword'].values.astype(bool),
        "phrasal_stress": phrasal,
        "pstress": pstress,
        "tstress": tstress,
        "gstress": gstress,
        "pstrength": pstrength,
    }


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
    pstress = np.stack([f.get("pstress", np.full(f["stressed"].shape, -1.0, dtype=np.float32)) for f in features_list])
    tstress = np.stack([f.get("tstress", np.full(f["stressed"].shape, -1.0, dtype=np.float32)) for f in features_list])
    gstress = np.stack([f.get("gstress", np.full(f["stressed"].shape, -1.0, dtype=np.float32)) for f in features_list])
    pstrength = np.stack([f.get("pstrength", np.full(f["stressed"].shape, -1.0, dtype=np.float32)) for f in features_list])
    has_gradient = bool(np.any(tstress >= 0))

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
        "pstress": pstress[:, None, :],       # (L, 1, N) gradient, -1 = absent
        "tstress": tstress[:, None, :],
        "gstress": gstress[:, None, :],       # RPPR grid stress, -1 = absent
        "pstrength": pstrength[:, None, :],   # 1=peak, 0=valley, -1=neither/absent
        "has_gradient": has_gradient,
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
        elif cname == "unres_within":
            all_viols[:, :, :, ci] = _unres_within_batch(
                position_ids, position_sizes, word_ids, heavy, stressed)
        elif cname == "unres_across":
            all_viols[:, :, :, ci] = _unres_across_batch(
                position_ids, position_sizes, word_ids, func_word, meter_vals)

    return all_viols, constraint_index


def _in_multisyll_position(position_ids, position_sizes):
    """(S, N) bool: syllable j is a 2nd+ syllable sharing a multi-syllable
    metrical position with syllable j-1 (the site of a resolution violation)."""
    S, N = position_ids.shape
    same_pos = np.zeros((S, N), dtype=bool)
    same_pos[:, 1:] = position_ids[:, 1:] == position_ids[:, :-1]
    return same_pos & (position_sizes >= 2)


def _unres_within_batch(position_ids, position_sizes, word_ids, heavy, stressed):
    """(L, S, N) int8 unres_within violations, fully vectorized over lines.

    Violation on syllable j iff it resolves within a word (same word_id as j-1)
    and the first syllable of the position is heavy or unstressed. Byte-identical
    to the former per-line/per-syllable loop.
    """
    S, N = position_ids.shape
    L = word_ids.shape[0]
    if N < 2:
        return np.zeros((L, S, N), dtype=np.int8)
    in_position = _in_multisyll_position(position_ids, position_sizes)  # (S, N)
    same_word = np.zeros((L, N), dtype=bool)
    same_word[:, 1:] = word_ids[:, 1:] == word_ids[:, :-1]
    bad_first = np.zeros((L, N), dtype=bool)  # prev syll heavy OR unstressed
    bad_first[:, 1:] = heavy[:, :-1].astype(bool) | ~stressed[:, :-1].astype(bool)
    line_mask = same_word & bad_first  # (L, N)
    return (in_position[None, :, :] & line_mask[:, None, :]).astype(np.int8)


def _unres_across_batch(position_ids, position_sizes, word_ids, func_word, meter_vals):
    """(L, S, N) int8 unres_across violations, fully vectorized over lines.

    Violation on syllable j iff it resolves across a word boundary (different
    word_id from j-1) AND the position is strong OR the two syllables are not
    both function words. Byte-identical to the former per-line loop.
    """
    S, N = position_ids.shape
    L = word_ids.shape[0]
    if N < 2:
        return np.zeros((L, S, N), dtype=np.int8)
    in_position = _in_multisyll_position(position_ids, position_sizes)  # (S, N)
    diff_word = np.zeros((L, N), dtype=bool)
    diff_word[:, 1:] = word_ids[:, 1:] != word_ids[:, :-1]
    fw = func_word.astype(bool)
    not_both_func = np.zeros((L, N), dtype=bool)
    not_both_func[:, 1:] = ~(fw[:, :-1] & fw[:, 1:])
    strong = meter_vals.astype(bool)  # (S, N)
    viol = in_position[None, :, :] & diff_word[:, None, :] & (
        strong[None, :, :] | not_both_func[:, None, :])
    return viol.astype(np.int8)


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


def _bounding_zones(meter):
    """Zones to use for harmonic bounding, or None for flat bounding.

    Bounding must operate in the SAME feature space as scoring. Zone-aware
    scoring (LazyParseList) kicks in only when the meter carries learned
    zone_weights; otherwise scoring is flat, so bounding stays flat too and the
    default parser path is unchanged/byte-identical.
    """
    zones = getattr(meter, 'zones', None)
    if zones is not None and getattr(meter, 'zone_weights', None):
        return zones
    return None


def _zone_split_batch(viols_4d, zones):
    """(L, S, N, C) -> (L, S, C*Z) zone-summed violation COUNTS.

    Harmonic bounding is dominance on the feature-count vector. With zone
    weights the feature space is (constraint x zone), so bounding must dominate
    on the zone-split counts, not the flat per-constraint totals — otherwise a
    parse whose violations sit in low-weight zones can be flat-dominated (and
    dropped) even though it's the zone-optimal parse. zones=None returns the
    flat (L, S, C) sum, identical to the previous bounding input.
    """
    if zones is None:
        return viols_4d.sum(axis=2)
    from .maxent import zone_boundaries
    L, S, N, C = viols_4d.shape
    boundaries = zone_boundaries(zones, N)
    Z = len(boundaries)
    out = np.zeros((L, S, C * Z), dtype=np.int64)
    for z, (start, end) in enumerate(boundaries):
        out[:, :, z * C:(z + 1) * C] = viols_4d[:, :, start:end, :].sum(axis=2)
    return out


def compute_bounding(viols, constraint_index, zones=None):
    """Compute harmonic bounding: mark scansions dominated by others.

    With `zones` set, dominance is computed on the zone-split (S, C*Z) counts
    so it matches zone-aware scoring; otherwise on the flat (S, C) sums.
    """
    if zones is not None:
        from .maxent import zone_split
        return _bound_viol_sums(zone_split(viols, zones))
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


# Elite pre-screen for bounding. Most candidates are dominated by one of the
# few lowest-total candidates; screening against the top-K first cuts the
# exact O(S^2) pairwise kernel down to the handful of survivors (mean ~3 of
# ~180 on the sonnets corpus). EXACT, not approximate: dominance is
# transitive, so any dominator of a screen survivor would itself have to
# survive the elite screen — pairwise among the survivors therefore
# reproduces the full-set result byte-for-byte.
BOUNDING_ELITE_K = 16
# Pad value for ragged survivor rows: never dominates a real vector and is
# always dominated. Must fit int16 (the torch kernel's dtype) incl. diffs.
_BOUNDING_PAD = 8192


def _elite_screen(viol_sums, K=BOUNDING_ELITE_K, block=512):
    """(L, S) bool: candidate is strictly dominated by one of its line's K
    best-total candidates. Chunked over lines to bound the (block, K, S, C)
    difference tensor."""
    L, S, C = viol_sums.shape
    totals = viol_sums.sum(axis=2)
    elite_idx = np.argpartition(totals, K - 1, axis=1)[:, :K]  # (L, K)
    dominated = np.zeros((L, S), dtype=bool)
    for l0 in range(0, L, block):
        l1 = min(l0 + block, L)
        v = viol_sums[l0:l1]
        elite = np.take_along_axis(v, elite_idx[l0:l1, :, None], axis=1)
        diff = elite[:, :, None, :] - v[:, None, :, :]  # (lc, K, S, C)
        dominated[l0:l1] = ((diff <= 0).all(3) & (diff < 0).any(3)).any(1)
    return dominated


def _bounding_exact(viol_sums):
    """Dispatch the exact pairwise kernel (GPU if available)."""
    device = get_device()
    if device is not None:
        return _compute_bounding_batch_torch(viol_sums, device)
    return _compute_bounding_batch_numpy(viol_sums)


def _bounding_screened(viol_sums):
    """Exact bounding via elite screen, then pairwise on the survivors."""
    L, S, C = viol_sums.shape
    if S <= 2 * BOUNDING_ELITE_K:
        return _bounding_exact(viol_sums)
    dominated = _elite_screen(viol_sums)
    surv = ~dominated
    counts = surv.sum(axis=1)
    s_max = int(counts.max())
    if s_max >= S:  # screen eliminated nothing; skip the gather
        return _bounding_exact(viol_sums)
    # gather survivors into a padded (L, s_max, C) tensor
    order = np.argsort(~surv, axis=1, kind="stable")[:, :s_max]  # (L, s_max)
    gathered = np.take_along_axis(
        viol_sums.astype(np.int16, copy=False), order[:, :, None], axis=1
    ).copy()
    pad = np.arange(s_max)[None, :] >= counts[:, None]  # (L, s_max)
    gathered[pad] = _BOUNDING_PAD
    unb_small = _bounding_exact(gathered) & ~pad
    result = np.zeros((L, S), dtype=bool)
    np.put_along_axis(result, order, unb_small, axis=1)
    return result


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
        # no shortcut: elite screen + exact pairwise on the survivors
        return _bounding_screened(viol_sums)

    # mixed: shortcut some lines, screened pairwise for others
    result = np.zeros((L, S), dtype=bool)

    # perfect lines: unbounded = score 0
    perfect_idx = np.where(has_perfect)[0]
    result[perfect_idx] = (totals[perfect_idx] == 0)

    # non-perfect lines: screened pairwise bounding
    nonperfect_idx = np.where(~has_perfect)[0]
    if len(nonperfect_idx) > 0:
        result[nonperfect_idx] = _bounding_screened(viol_sums[nonperfect_idx])

    return result


# Peak-memory budget (bytes) for the largest pairwise-difference intermediate
# built during harmonic bounding. The pre-tiling implementation materialized a
# single (L, S, S, C) tensor — ~1 GB (GPU int16) / ~4 GB (numpy int64) per
# non-perfect line at the syllable cap (S ~ 8000+). The chunked/tiled path below
# keeps the (Lc, Ti, Tj, C) diff tensor under this budget (derived boolean
# masks add a small constant multiple). Tiling is a pure reassociation of the
# same per-pair AND/OR dominance reduction, so the unbounded/bounded RESULT is
# byte-identical to the untiled computation.
BOUNDING_MEM_BUDGET = 128 * 1024 * 1024  # 128 MB


def _bounding_block_sizes(L, S, C, bytes_per_elem, budget=None):
    """Pick (Lc, Ti, Tj) block sizes so the (Lc, Ti, Tj, C) diff intermediate
    stays within ``budget`` bytes.

    Purely a memory-vs-speed tradeoff — it changes how the S x S comparison is
    decomposed into tiles, never the bounded/unbounded result. When the whole
    (L, S, S) comparison already fits the budget, returns (L, S, S) so the
    computation is done in a single allocation (identical to the untiled path).
    """
    import math
    if budget is None:
        budget = BOUNDING_MEM_BUDGET
    C = max(1, int(C))
    # number of (line, i, j) triples whose diff (times C, times bytes) fits
    max_elems = max(1, int(budget) // (int(bytes_per_elem) * C))
    if L * S * S <= max_elems:
        return L, S, S
    # tile the S x S plane into square-ish tiles, then batch as many lines as
    # the remaining budget allows.
    tile = max(1, min(S, math.isqrt(max_elems)))
    per_line_pairs = tile * tile
    Lc = max(1, min(L, max_elems // per_line_pairs))
    return int(Lc), int(tile), int(tile)


def _compute_bounding_batch_numpy(viol_sums, budget=None):
    """Numpy batched bounding for L lines (chunked over L, tiled over S x S).

    Result is byte-identical to the untiled version: bounded[l, j] is the OR
    over all i of (i dominates j), computed here by ORing partial reductions
    over i-tiles.
    """
    L, S, C = viol_sums.shape
    if S <= 1:
        return np.ones((L, S), dtype=bool)
    Lc, Ti, Tj = _bounding_block_sizes(L, S, C, bytes_per_elem=8, budget=budget)
    bounded = np.zeros((L, S), dtype=bool)
    for l0 in range(0, L, Lc):
        l1 = min(l0 + Lc, L)
        vL = viol_sums[l0:l1]  # (lc, S, C)
        for j0 in range(0, S, Tj):
            j1 = min(j0 + Tj, S)
            vj = vL[:, j0:j1, :]  # (lc, tj, C)
            acc = np.zeros((l1 - l0, j1 - j0), dtype=bool)  # bounded within j-tile
            for i0 in range(0, S, Ti):
                i1 = min(i0 + Ti, S)
                vi = vL[:, i0:i1, :]  # (lc, ti, C)
                diff = vi[:, :, None, :] - vj[:, None, :, :]  # (lc, ti, tj, C)
                i_leq_j = (diff <= 0).all(axis=3)
                i_lt_j = i_leq_j & (diff < 0).any(axis=3)
                acc |= i_lt_j.any(axis=1)  # reduce over this i-tile
            bounded[l0:l1, j0:j1] = acc
    return ~bounded


def _compute_bounding_batch_torch(viol_sums, device, budget=None):
    """GPU batched bounding for L lines (chunked over L, tiled over S x S).

    Only the (Lc, Ti, Tj, C) diff tensor is tiled; the (L, S, C) input tensor is
    uploaded once. Result is byte-identical to the untiled kernel.
    """
    import torch
    L, S, C = viol_sums.shape
    if S <= 1:
        return np.ones((L, S), dtype=bool)
    vt = torch.tensor(viol_sums, dtype=torch.int16, device=device)  # (L, S, C)
    Lc, Ti, Tj = _bounding_block_sizes(L, S, C, bytes_per_elem=2, budget=budget)
    bounded = torch.zeros((L, S), dtype=torch.bool, device=device)
    for l0 in range(0, L, Lc):
        l1 = min(l0 + Lc, L)
        vL = vt[l0:l1]  # (lc, S, C)
        for j0 in range(0, S, Tj):
            j1 = min(j0 + Tj, S)
            vj = vL[:, j0:j1, :]  # (lc, tj, C)
            acc = torch.zeros((l1 - l0, j1 - j0), dtype=torch.bool, device=device)
            for i0 in range(0, S, Ti):
                i1 = min(i0 + Ti, S)
                vi = vL[:, i0:i1, :]  # (lc, ti, C)
                diff = vi[:, :, None, :] - vj[:, None, :, :]  # (lc, ti, tj, C)
                i_leq_j = (diff <= 0).all(dim=3)
                i_lt_j = i_leq_j & (diff < 0).any(dim=3)
                acc |= i_lt_j.any(dim=1)  # reduce over this i-tile
            bounded[l0:l1, j0:j1] = acc
    return ~bounded.cpu().numpy()


def _compute_bounding_numpy(v, budget=None):
    """Numpy fallback for harmonic bounding (single line). Tiled for large S."""
    S = v.shape[0]
    if S <= 1:
        return np.ones(S, dtype=bool)
    return _compute_bounding_batch_numpy(v[None, :, :], budget=budget)[0]


def _compute_bounding_torch(v, device, budget=None):
    """GPU-accelerated harmonic bounding (single line). Tiled for large S."""
    S = v.shape[0]
    if S <= 1:
        return np.ones(S, dtype=bool)
    return _compute_bounding_batch_torch(v[None, :, :], device, budget=budget)[0]


class LazyParseList:
    """Lightweight parse list that defers Parse object construction.

    Stores numpy violation data and scansion lists. Parse objects are
    only built when accessed (e.g., via best_parse, iteration, or indexing).
    """

    def __init__(self, wordtokens, meter, scansions, viols, constraint_index,
                 unbounded_mask, sylls, parse_unit="line", syll_row_idx=None,
                 meter_vals=None, position_ids=None, position_sizes=None,
                 sylls_by_scansion=None, syll_row_idx_by_scansion=None):
        self.wordtokens = wordtokens
        self.meter = meter
        self.parse_unit = parse_unit
        self.parent = wordtokens

        # store ALL scansions with their bounded status.
        # RAGGED results (mixed-syllable-count pool_forms): `viols` is a LIST of
        # per-scansion (N_k, C) arrays (scansions differ in length), and
        # meter_vals/position_ids/position_sizes are parallel lists. The fast
        # rectangular path (one (S, N, C) array) is untouched for normal lines;
        # only per-scansion consumers (_get_parse, get_parses_df) special-case it.
        self._ragged = isinstance(viols, list)
        self._all_scansions = list(scansions)
        self._all_viols = viols  # (S, N, C), or a list of (N_k, C) when ragged
        self._unbounded_mask = unbounded_mask  # (S,) bool
        self._constraint_index = constraint_index
        self._constraint_names = list(constraint_index.keys())
        self._sylls = sylls
        # row indices into the source syll_df for each syll in _sylls (DF path)
        self._syll_row_idx = syll_row_idx
        # Pooled results (pool_forms): survivors come from different pronunciation
        # combos, so each scansion carries its OWN syllables / DF row indices.
        # When set, these override _sylls / _syll_row_idx per scansion index so a
        # parse realized under a stressed variant reports that variant's
        # form_idx / stress. Stays numpy — no Entity construction.
        self._sylls_by_scansion = sylls_by_scansion
        self._syll_row_idx_by_scansion = syll_row_idx_by_scansion
        # scansion encoding, shape (S, N) each
        self._meter_vals = meter_vals
        self._position_ids = position_ids
        self._position_sizes = position_sizes
        # Parity: some construction paths (pooling; the entity path) don't pass the
        # encoding. Compute it once here from the scansion strings so the regularity
        # tie-break — and get_parses_df — work on every LazyParseList (DF and entity
        # alike), not just where it happened to be supplied. Cached in
        # encode_scansions; a position like 'ss' spans two syllables, so N is the
        # sum of position lengths.
        if self._meter_vals is None and not self._ragged and self._all_scansions:
            nsylls = sum(len(p) for p in self._all_scansions[0])
            self._meter_vals, self._position_ids, self._position_sizes = \
                encode_scansions(self._all_scansions, nsylls)
        self._built_parses = {}  # cache: scansion index -> Parse
        self._best_idx = None
        self._bound_init = True
        self._num = None

        # unbounded indices for fast access
        self._unbounded_indices = np.where(unbounded_mask)[0]

        # compute scores for ranking (weighted violation sums)
        zones = getattr(meter, 'zones', None)
        zone_weights = getattr(meter, 'zone_weights', None)
        # when learned weights are active, built Parse objects get their .score
        # overridden with the learned score (see _get_parse). zones=None with
        # learned weights = flat weighted scoring (zone_split sums over N).
        self._is_zone_scored = bool(zone_weights)

        if self._ragged:
            if zone_weights and viols:
                # Each ragged parse has its OWN N_k, so zone-split it individually.
                # make_zone_names' C*Z names are N-independent (only the zone
                # boundaries shift with N), so the learned zone weights apply
                # per parse — a mixed-N line is ranked by the same objective as
                # its rectangular neighbours, not silently dropped to flat.
                from .maxent import zone_split, make_zone_names
                scores = []
                for v in viols:  # v is (N_k, C)
                    zv = zone_split(v[None], zones)[0]  # (C*Z,)
                    znames = make_zone_names(self._constraint_names, v.shape[0], zones)
                    zw = np.array([zone_weights.get(c, 1) for c in znames])
                    scores.append(float((zv * zw).sum()))
                self._all_scores = np.array(scores)
            else:
                constraint_weights = meter.constraints
                weights = np.array([constraint_weights.get(c, 1) for c in self._constraint_names])
                all_viols_sum = np.array([v.sum(axis=0) for v in viols]) if viols else np.zeros((0, len(weights)))
                self._all_scores = (all_viols_sum * weights[None, :]).sum(axis=1)  # (S,)
        elif zone_weights:
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
    def num_cooptimal(self):
        """How many DISTINCT best scansions (meter strings) tie at the minimum score.

        1 = the reported best scansion is unique. >1 = the grammar is indifferent
        among that many distinct co-optimal scansions, and best_parse's meter_str
        is an arbitrary (but deterministic) pick among them — surfaced so a tie
        isn't read as a decisive result.

        Distinct *meter strings*: two scansions yielding the same +/- pattern
        (e.g. via resolution) count once. This is metrical indifference *given
        the pronunciation the parser chose* — it does not fold in ties between
        different pronunciations (that's a separate, pronunciation-choice axis;
        the pick there is made deterministic by variant ordering, not here).
        """
        if len(self._scores) == 0:
            return 0
        coopt_idx = self._unbounded_indices[np.isclose(self._scores, self._scores.min())]
        if self._meter_vals is not None:
            meters = {"".join("+" if v else "-" for v in self._meter_vals[i]) for i in coopt_idx}
        else:
            meters = {self._get_parse(int(i)).meter_str for i in coopt_idx}
        return len(meters)

    def _regularity_key(self):
        """Per-scansion IRREGULARITY (lower = more regular): 1 minus the best
        period-k (k in {2,3}) self-similarity of the s/w string. A pure iamb
        (period 2) OR a pure anapest (period 3) -> ~0; a ragged line -> higher. A
        cheap, vectorized, meter-AGNOSTIC proxy for foot regularity — unlike a raw
        bigram count it does NOT favour binary over ternary (which would break
        anapestic/dactylic detection). Cached; no DP, no Parse objects."""
        bc = getattr(self, "_reg_cache", None)
        if bc is not None:
            return bc
        def _one(a):
            a = np.asarray(a, dtype=np.int8).ravel()
            best = 0.0
            for k in (2, 3):
                if a.size > k:
                    best = max(best, float((a[k:] == a[:-k]).mean()))
            return 1.0 - best
        if getattr(self, "_ragged", False):
            bc = np.asarray([_one(mv) for mv in self._meter_vals], dtype=np.float32)
        else:
            mv = self._meter_vals
            if mv is None or getattr(mv, "ndim", 0) < 2 or mv.shape[1] < 3:
                bc = np.zeros(len(self._all_scores), dtype=np.float32)
            else:
                a = mv.astype(np.int8)
                best = np.zeros(a.shape[0], dtype=np.float32)
                for k in (2, 3):
                    if a.shape[1] > k:
                        best = np.maximum(best, (a[:, k:] == a[:, :-k]).mean(axis=1))
                bc = (1.0 - best).astype(np.float32)
        self._reg_cache = bc
        return bc

    def _pseudo_foot_key(self):
        """Per-scansion count of distinct 'pseudo-feet' — segments cut after each
        strong-run (rising pseudo-feet), e.g. 'wswwswwsw' -> ws|wws|wws|w -> 3
        distinct. A cheap, deterministic, foot-FLAVORED regularity signal (a regular
        line has few distinct pseudo-feet) computed straight from the scansion — no
        DP, no foot-parser — so, unlike the real foot key, it does NOT couple
        best_parse to the evolving foot layer. Cached; used as the tertiary sort key
        to break residual (same score + same period-k) ties deterministically."""
        bc = getattr(self, "_pf_cache", None)
        if bc is not None:
            return bc
        def _one(mv):
            s = "".join("s" if v else "w" for v in np.asarray(mv, dtype=bool))
            feet, start, i, n = [], 0, 0, len(s)
            while i < n:
                if s[i] == "s":
                    j = i
                    while j < n and s[j] == "s":
                        j += 1
                    feet.append(s[start:j]); start = i = j
                else:
                    i += 1
            if start < n:
                feet.append(s[start:])
            return len(set(feet))
        if self._meter_vals is None:
            bc = np.zeros(len(self._all_scores), dtype=np.int16)
        else:
            bc = np.asarray([_one(mv) for mv in self._meter_vals], dtype=np.int16)
        self._pf_cache = bc
        return bc

    def _doubled_keys(self):
        """Per-scansion counts of doubled positions, `(#ss, #ww)` — resolutions
        (two strong syllables in one beat) and dips (two weaks in one position).
        Parses tied on (score, period-k, pseudo-feet) — which on the sonnets differ
        ONLY in WHERE a resolution or a dip sits — are then ranked fewest-ss, then
        fewest-ww: a resolution crams two stresses into one beat, so it's the more
        marked departure from pure `wsws…` alternation than a dip is. Pure scansion
        statistics (no foot-parser), yet the resulting pick matches the DP foot
        reading ~90% of the time — best_parse tracks the foot layer without coupling
        to it. On the sonnets fewest-ss breaks 59 of 90 residual ties; fewest-ww is
        a redundant-but-principled tiebreak after it. Cached; quaternary/quinary
        sort keys."""
        bc = getattr(self, "_dbl_cache", None)
        if bc is not None:
            return bc
        def _one(mv):
            a = np.asarray(mv, dtype=bool)
            if a.size < 2:
                return (0, 0)
            return (int((a[1:] & a[:-1]).sum()), int((~a[1:] & ~a[:-1]).sum()))
        if self._meter_vals is None:
            n = len(self._all_scores)
            bc = (np.zeros(n, dtype=np.int16), np.zeros(n, dtype=np.int16))
        else:
            pairs = [_one(mv) for mv in self._meter_vals]
            bc = (np.asarray([p[0] for p in pairs], dtype=np.int16),
                  np.asarray([p[1] for p in pairs], dtype=np.int16))
        self._dbl_cache = bc
        return bc

    def _order(self, idxs, scores):
        """The shared parse comparator: sort scansion indices by (score, then
        fewest resolutions `ss`, period-k regularity, distinct pseudo-feet, fewest
        dips `ww`), with a stable position fallback for a fully deterministic order.
        `ss` is the PRIMARY tie-break (after score): among co-optimal parses a
        resolution — two stresses crammed into one beat — is the most marked
        departure from `wsws…`, so minimising resolutions first best matches human
        scansion (57.1% vs 56.3% for a regularity-first order on the litlab tagged
        sample; +1% on iambic/trochaic/dactylic, tied on anapestic). It also fixes
        forced initial inversions like 'Pity the world' — reg-first preferred the
        resolution `(ss)(ws)…` (stressing 'ty') for its cleaner tail; ss-first takes
        the truer dip `(sw*)(ws)…`. `ww` stays LAST (putting it early costs ~7pts).
        Every key is cheap and computed from the scansion — NOT the DP foot-parser —
        so best_parse stays decoupled from the churning foot layer (web, parsed_df,
        meter_type, save/load, cmp_prosodics read it). Applied everywhere parses are
        ranked so best_parse / unbounded / parse_rank / get_parses_df agree."""
        reg = self._regularity_key()[idxs]
        pf = self._pseudo_foot_key()[idxs]
        ss, ww = self._doubled_keys()
        ss, ww = ss[idxs], ww[idxs]
        return idxs[np.lexsort((np.arange(len(idxs)), ww, pf, reg, ss, np.asarray(scores)))]

    @property
    def best_parse(self):
        if len(self._unbounded_indices) == 0:
            return None
        if self._best_idx is None:
            self._best_idx = int(self._order(self._unbounded_indices, self._scores)[0])
        bp = self._get_parse(self._best_idx, rank=1)
        if bp is not None:
            bp.num_cooptimal = self.num_cooptimal
            bp.is_tied = bp.num_cooptimal > 1
        return bp

    @property
    def best_parses(self):
        from .parselists import ParseList
        bp = self.best_parse
        return ParseList([bp], parse_unit=self.parse_unit, parent=self.parent) if bp else ParseList([], parse_unit=self.parse_unit, parent=self.parent)

    @property
    def unbounded(self):
        """Unbounded parses sorted by score (best first)."""
        from .parselists import ParseList
        sorted_idx = self._order(self._unbounded_indices, self._scores)
        return ParseList(
            [self._get_parse(int(i)) for i in sorted_idx],
            parse_unit=self.parse_unit, parent=self.parent,
        )

    @property
    def bounded(self):
        from .parselists import ParseList
        bounded_indices = np.where(~self._unbounded_mask)[0]
        bounded_scores = self._all_scores[bounded_indices]
        sorted_idx = self._order(bounded_indices, bounded_scores)
        return ParseList(
            [self._get_parse(int(i), is_bounded=True) for i in sorted_idx],
            parse_unit=self.parse_unit, parent=self.parent, show_bounded=True,
        )

    @property
    def data(self):
        """All parses sorted by score ascending (best first); bounded and unbounded interleaved by score."""
        sorted_idx = self._order(np.arange(len(self._all_scores)), self._all_scores)
        return [self._get_parse(int(i), is_bounded=not self._unbounded_mask[i])
                for i in sorted_idx]

    def __iter__(self):
        """Iterate all parses sorted by score."""
        sorted_idx = self._order(np.arange(len(self._all_scores)), self._all_scores)
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
        # normalize negatives so idx and idx-S don't cache the same parse twice (C20)
        if idx < 0:
            idx += len(self._all_scansions)
        if idx in self._built_parses:
            p = self._built_parses[idx]
            if is_bounded:
                p.is_bounded = True
            if rank is not None:  # refresh rank on a cache hit (C20)
                p.parse_rank = rank
            return p

        sylls = (self._sylls_by_scansion[idx]
                 if self._sylls_by_scansion is not None else self._sylls)
        parse = _build_single_parse(
            idx, self._all_scansions[idx], self._all_viols[idx], self._constraint_index,
            self._constraint_names, sylls, self.wordtokens, self.meter,
            rank=rank,
        )
        parse.is_bounded = is_bounded
        parse.parent = self
        # Under zone weights, ranking uses the zone-aware _all_scores; surface
        # that on the Parse so parse.score matches the score it was ranked by
        # (a flat parse.score would contradict the zone-aware best_parse).
        if self._is_zone_scored:
            parse._score_override = float(self._all_scores[idx])
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
        if self.wordtokens is not None and hasattr(self.wordtokens, 'to_html'):
            out = self.wordtokens.to_html(as_str=True, css=css)
        else:
            out = bp.meter_str  # DF path: no wordtoken entities; show the scansion
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
        # A ParseList of ALL candidate scansions (show_bounded=True), so
        # .scansions.get_df()/.df/.stats() surface every parse — matching
        # ParseList.scansions. Returning `self` (a LazyParseList) made
        # .scansions.get_df() route through get_df's show_bounded=False path
        # and silently collapse to the unbounded parses only.
        from .parselists import ParseList
        return ParseList(self.data, parse_unit=self.parse_unit, parent=self.parent,
                         is_scansions=True, show_bounded=True)

    def get_df(self, **kwargs):
        from .parselists import ParseList
        return ParseList(self.data, parse_unit=self.parse_unit, parent=self.parent).get_df(**kwargs)

    def to_df(self, mode='all', by='line', line_num=None):
        """Entity-free per-parse DataFrame, built straight from the numpy arrays —
        constructs NO Parse objects (unlike ``.get_df``/``.scansions``, which
        materialize one Parse per scansion). ``by='line'``: one row per parse
        (meter, score, per-constraint violation totals), with an ``is_bounded``
        column. Default ``mode='all'`` returns EVERY parse (matching ``.parses``);
        ``mode='unbounded'`` gives just the Pareto frontier (the rows
        ``TextModel.get_parses_df(by='line')`` produces), ``mode='best'`` the top
        one. Use ``TextModel.get_parses_df(by='syll')`` for the syllable frame (it
        needs the text's syllable DataFrame)."""
        import pandas as pd
        if by != 'line':
            raise NotImplementedError(
                "LazyParseList.to_df supports by='line'; use "
                "TextModel.get_parses_df(by='syll') for the syllable-level frame.")
        unbounded_mask = self._unbounded_mask
        all_scores = self._all_scores
        unb_idx = self._unbounded_indices
        rank_of = np.full(len(unbounded_mask), -1, dtype=np.int32)
        if len(unb_idx) > 0:
            ub_sorted = self._order(unb_idx, self._scores)
            rank_of[ub_sorted] = np.arange(1, len(ub_sorted) + 1, dtype=np.int32)
            best_idx = int(ub_sorted[0])
        else:
            best_idx = -1
        if mode == 'best':
            parse_indices = np.array([best_idx], dtype=np.int64) if best_idx >= 0 else np.empty(0, dtype=np.int64)
        elif mode == 'unbounded':
            parse_indices = self._order(unb_idx, self._scores)
        else:
            parse_indices = self._order(np.arange(len(all_scores)), all_scores)
        P = len(parse_indices)
        if P == 0:
            return pd.DataFrame()
        line_num = int(line_num if line_num is not None
                       else (getattr(self.parent, 'num', 0) or 0))
        if self._ragged:
            meter_strs = [_pool_meter_str(self, int(i)) for i in parse_indices]
            pp_viols = np.stack([self._all_viols[int(i)].sum(axis=0) for i in parse_indices]).astype(np.int32)
            num_sylls = np.array([self._all_viols[int(i)].shape[0] for i in parse_indices], dtype=np.int32)
        else:
            mv_arr = self._meter_vals
            if mv_arr is None:
                mv_arr, _, _ = encode_scansions(self._all_scansions, self._all_viols.shape[1])
            meter_strs = [''.join('+' if v else '-' for v in mv_arr[i]) for i in parse_indices]
            pp_viols = self._all_viols[parse_indices].sum(axis=1).astype(np.int32)
            num_sylls = np.full(P, self._all_viols.shape[1], dtype=np.int32)
        df = pd.DataFrame({
            'line_num': np.full(P, line_num, dtype=np.int32),
            'parse_idx': parse_indices.astype(np.int32),
            'parse_rank': pd.array(rank_of[parse_indices], dtype='Int32'),
            'parse_score': all_scores[parse_indices].astype(np.float64),
            'is_best': parse_indices == best_idx,
            'is_bounded': ~unbounded_mask[parse_indices],
            'num_sylls': num_sylls,
            'num_viols': pp_viols.sum(axis=1).astype(np.int32),
            'meter': meter_strs,
        })
        df.loc[df['parse_rank'] < 0, 'parse_rank'] = pd.NA
        for ci, cname in enumerate(self._constraint_names):
            col = pp_viols[:, ci]
            if col.any():
                df[f'*{cname}'] = col.astype(np.int32)
        return df

    @property
    def df(self):
        """Entity-free per-parse DataFrame (see ``to_df``); builds no Parse objects."""
        return self.to_df()

    def get_ld(self, **kwargs):
        from .parselists import ParseList
        return ParseList(self.data, parse_unit=self.parse_unit, parent=self.parent).get_ld(**kwargs)


def _build_single_parse(idx, scansion, viols, constraint_index, constraint_names,
                          sylls, wordtokens, meter, rank=None):
    """Build a single Parse object from numpy data. `viols` is the per-parse
    (N, C) slice (works for both a rectangular-array slice and a ragged list
    element)."""
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
                v = int(viols[syll_idx, constraint_index[cname]])
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
