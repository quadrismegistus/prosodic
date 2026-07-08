from ..imports import *
import numpy as np


def constraint(desc, scope, vectorized=None):
    """Decorator that marks a function as a metrical constraint.

    Args:
        desc: human-readable description.
        scope: "position" (per-syllable) or "line" (per-parse).
        vectorized: optional function(features, scansion) -> (L, S, N) int8.
            If provided, evaluate_constraints_batch uses this instead of
            hardcoded logic. The function receives a dict of broadcast arrays:
                stressed:      (L, 1, N) bool
                heavy:         (L, 1, N) bool
                strong:        (L, 1, N) int8 (polysyllabic stress)
                weak:          (L, 1, N) int8 (polysyllabic unstress)
                func_word:     (L, 1, N) bool
                word_ids:      (L, 1, N) int32
                is_strong_pos: (1, S, N) bool
                is_weak_pos:   (1, S, N) bool
                position_ids:  (S, N) int32
                position_sizes:(S, N) int32
                L, S, N:       ints
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.desc = desc
        wrapper.scope = scope
        wrapper.vectorized = vectorized
        return wrapper
    return decorator


# === Simple position constraints (boolean per syllable) ===

@constraint(
    desc="No stressed syllables on weak position",
    scope="position",
    vectorized=lambda f: (f["stressed"] & f["is_weak_pos"]).astype(np.int8),
)
def w_stress(mpos):
    if mpos.is_prom:
        return [None] * len(mpos.slots)
    return [slot.is_stressed for slot in mpos.slots]


@constraint(
    desc="No unstressed syllable on strong position",
    scope="position",
    vectorized=lambda f: (~f["stressed"] & f["is_strong_pos"]).astype(np.int8),
)
def s_unstress(mpos):
    if not mpos.is_prom:
        return [None] * len(mpos.slots)
    return [not slot.is_stressed for slot in mpos.slots]


@constraint(
    desc="No polysyllabic stress on weak position",
    scope="position",
    vectorized=lambda f: (f["strong"].astype(bool) & f["is_weak_pos"]).astype(np.int8),
)
def w_peak(mpos):
    if mpos.is_prom:
        return [None] * len(mpos.slots)
    return [slot.is_strong for slot in mpos.slots]


@constraint(
    desc="No polysyllabic unstress on strong position",
    scope="position",
    vectorized=lambda f: (f["weak"].astype(bool) & f["is_strong_pos"]).astype(np.int8),
)
def s_trough(mpos):
    if not mpos.is_prom:
        return [None] * len(mpos.slots)
    return [slot.is_weak for slot in mpos.slots]


# === Resolution constraints (per-line eval in vectorized path) ===

@constraint(
    desc="Disyllabic positions within words must start with a light and stressed syllable",
    scope="position",
)
def unres_within(mpos):
    slots = mpos.slots
    if len(slots) < 2:
        return [None] * len(mpos.slots)
    ol = [None]
    for si in range(1, len(slots)):
        slot1, slot2 = slots[si - 1], slots[si]
        unit1, unit2 = slot1.unit, slot2.unit
        # Same-word test must use the word *occurrence* (wordtoken), not the
        # WordForm: WordForms are shared across repeated tokens of a word type
        # (cached get_word), so `wf1 is wf2` misclassified adjacent repeats
        # (e.g. "the the") as word-internal. This mirrors the DF path's
        # per-syllable word_num comparison. (AUDIT C17)
        wt1, wt2 = getattr(unit1, "wordtoken", None), getattr(unit2, "wordtoken", None)
        if wt1 is not wt2:
            ol.append(None)
        else:
            if unit1.is_heavy or not unit1.is_stressed:
                ol.append(True)
            else:
                ol.append(False)
    return ol


@constraint(
    desc="Disyllabic positions crossing words can only contain function words",
    scope="position",
)
def unres_across(mpos):
    slots = mpos.slots
    if len(slots) < 2:
        return [None] * len(mpos.slots)
    ol = [None]
    for si in range(1, len(slots)):
        slot1, slot2 = slots[si - 1], slots[si]
        unit1, unit2 = slot1.unit, slot2.unit
        # Word-boundary test uses the word *occurrence* (wordtoken), not the
        # shared WordForm, so adjacent repeats of the same word type (e.g.
        # "the the") count as a boundary. Matches the DF path's word_num
        # comparison. (AUDIT C17)
        wt1, wt2 = getattr(unit1, "wordtoken", None), getattr(unit2, "wordtoken", None)
        if wt1 is wt2:
            ol.append(None)
        else:
            func1, func2 = _slot_is_functionword(slot1), _slot_is_functionword(slot2)
            if mpos.is_prom or not func1 or not func2:
                ol.append(True)
            else:
                ol.append(False)
    return ol


@constraint(
    desc="Do not allow positions to exceed two syllables",
    scope="position",
    vectorized=lambda f: (f["position_sizes"][None, :, :] > 2).astype(np.int8),
)
def foot_size(mpos):
    res = bool(len(mpos.slots) > 2) or bool(len(mpos.slots) < 1)
    return [res] * len(mpos.slots)


# === Adjacency constraints (shifted arrays) ===

def _global_slot_context(mpos):
    """Return ``(all_slots, start_index)`` for a position.

    ``all_slots`` is the parent parse's full ordered slot list and
    ``start_index`` is the global index of ``mpos``'s first slot. Adjacency
    constraints (clash/lapse) compare each syllable to its predecessor, which
    may live in the *previous* position, so they need the parse-wide sequence
    rather than just ``mpos.slots``.
    """
    all_slots = list(mpos.parse.slots)
    if not mpos.slots:
        return all_slots, 0
    first = mpos.slots[0]
    for i, slot in enumerate(all_slots):
        if slot is first:
            return all_slots, i
    return all_slots, 0


def _clash_vectorized(f):
    N = f["N"]
    if N < 2:
        return np.zeros((f["L"], f["S"], N), dtype=np.int8)
    result = np.zeros((f["L"], f["S"], N), dtype=np.int8)
    str_curr = f["stressed"][:, :, :-1]
    str_next = f["stressed"][:, :, 1:]
    weak_curr = f["is_weak_pos"][:, :, :-1]
    weak_next = f["is_weak_pos"][:, :, 1:]
    result[:, :, 1:] = (str_curr & str_next & (weak_curr | weak_next)).astype(np.int8)
    return result

@constraint(
    desc="Adjacent stressed syllables with at least one in weak position",
    scope="position",
    vectorized=_clash_vectorized,
)
def clash(mpos):
    # Entity reference impl mirroring ``_clash_vectorized`` (AUDIT C16): mark a
    # violation on syllable j (global order, j>=1) when j-1 and j are both
    # stressed and at least one of the two positions is weak.
    all_slots, start = _global_slot_context(mpos)
    out = []
    for k, slot in enumerate(mpos.slots):
        j = start + k
        if j <= 0:
            out.append(None)
            continue
        prev = all_slots[j - 1]
        both_stressed = bool(slot.unit.is_stressed) and bool(prev.unit.is_stressed)
        one_weak = (not slot.is_prom) or (not prev.is_prom)
        out.append(bool(both_stressed and one_weak))
    return out


def _lapse_vectorized(f):
    N = f["N"]
    if N < 2:
        return np.zeros((f["L"], f["S"], N), dtype=np.int8)
    result = np.zeros((f["L"], f["S"], N), dtype=np.int8)
    unstr_curr = ~f["stressed"][:, :, :-1]
    unstr_next = ~f["stressed"][:, :, 1:]
    str_curr = f["is_strong_pos"][:, :, :-1]
    str_next = f["is_strong_pos"][:, :, 1:]
    result[:, :, 1:] = (unstr_curr & unstr_next & (str_curr | str_next)).astype(np.int8)
    return result

@constraint(
    desc="Adjacent unstressed syllables with at least one in strong position",
    scope="position",
    vectorized=_lapse_vectorized,
)
def lapse(mpos):
    # Entity reference impl mirroring ``_lapse_vectorized`` (AUDIT C16): mark a
    # violation on syllable j (global order, j>=1) when j-1 and j are both
    # unstressed and at least one of the two positions is strong.
    all_slots, start = _global_slot_context(mpos)
    out = []
    for k, slot in enumerate(mpos.slots):
        j = start + k
        if j <= 0:
            out.append(None)
            continue
        prev = all_slots[j - 1]
        both_unstressed = (not slot.unit.is_stressed) and (not prev.unit.is_stressed)
        one_strong = bool(slot.is_prom) or bool(prev.is_prom)
        out.append(bool(both_unstressed and one_strong))
    return out


# === New constraints ===

@constraint(
    desc="No heavy syllable on weak position",
    scope="position",
    vectorized=lambda f: (f["heavy"] & f["is_weak_pos"]).astype(np.int8),
)
def w_heavy(mpos):
    if mpos.is_prom:
        return [None] * len(mpos.slots)
    return [slot.unit.is_heavy for slot in mpos.slots]


@constraint(
    desc="No light syllable on strong position",
    scope="position",
    vectorized=lambda f: (~f["heavy"] & f["is_strong_pos"]).astype(np.int8),
)
def s_light(mpos):
    if not mpos.is_prom:
        return [None] * len(mpos.slots)
    return [not slot.unit.is_heavy for slot in mpos.slots]


def _slot_is_functionword(slot):
    """Whether the word occupying ``slot`` is a function word.

    ``is_functionword`` lives on WordForm; reading it off the Syllable
    (``slot.unit.is_functionword``) goes through ``Entity.__getattr__``'s
    ``is_*`` branch, which returns ``False`` for every syllable — silently
    turning ``s_func`` into a no-op. Resolve via the wordform instead. (AUDIT C16)
    """
    wf = getattr(slot.unit, "wordform", None)
    if wf is not None:
        try:
            return bool(wf.is_functionword)
        except AttributeError:
            pass
    return bool(getattr(slot.unit, "is_functionword", False))


@constraint(
    desc="No function word on strong position",
    scope="position",
    vectorized=lambda f: (f["func_word"] & f["is_strong_pos"]).astype(np.int8),
)
def s_func(mpos):
    if not mpos.is_prom:
        return [None] * len(mpos.slots)
    return [_slot_is_functionword(slot) for slot in mpos.slots]


def _word_boundary_vectorized(f):
    """Penalize when a word boundary falls inside a metrical foot (not at a foot edge)."""
    L, S, N = f["L"], f["S"], f["N"]
    if N < 2:
        return np.zeros((L, S, N), dtype=np.int8)
    word_ids = f["word_ids_raw"]  # (L, N) — not broadcast
    pos_ids = f["position_ids"]   # (S, N)
    # word boundary (per line): word_ids[j] != word_ids[j-1]
    word_boundary = np.zeros((L, N), dtype=bool)
    word_boundary[:, 1:] = word_ids[:, 1:] != word_ids[:, :-1]
    # foot boundary (per scansion): position_ids changes
    foot_boundary = np.zeros((S, N), dtype=bool)
    foot_boundary[:, 1:] = pos_ids[:, 1:] != pos_ids[:, :-1]
    # violation: word boundary without a coincident foot boundary
    return (word_boundary[:, None, :] & ~foot_boundary[None, :, :]).astype(np.int8)

@constraint(
    desc="Word boundary should align with foot boundary",
    scope="position",
    vectorized=_word_boundary_vectorized,
)
def word_foot(mpos):
    # Entity reference impl mirroring ``_word_boundary_vectorized`` (AUDIT C16):
    # a violation falls on a syllable that shares a metrical position with the
    # preceding syllable (no foot boundary) but belongs to a different word
    # occurrence (word boundary). A position's first slot always sits at a foot
    # boundary, so it never violates.
    out = []
    prev_wt = None
    for k, slot in enumerate(mpos.slots):
        wt = getattr(slot.unit, "wordtoken", None)
        if k == 0:
            out.append(None)  # foot boundary (or line start): not applicable
        else:
            out.append(bool(wt is not prev_wt))
        prev_wt = wt
    return out


# === Phrasal stress constraints (require syntax=True) ===

def _w_prom_vectorized(f):
    if not f.get("has_phrasal"):
        return np.zeros((f["L"], f["S"], f["N"]), dtype=np.int8)
    return ((f["phrasal_stress"] >= -1) & f["is_weak_pos"]).astype(np.int8)

@constraint(
    desc="No phrasally prominent word on weak position",
    scope="position",
    vectorized=_w_prom_vectorized,
)
def w_prom(mpos):
    if mpos.is_prom:
        return [None] * len(mpos.slots)
    # Entity.__getattr__ returns None (never raises) for an absent attribute, so
    # the getattr default is shadowed — guard None explicitly (else None >= -1
    # raises). None = no phrasal data -> inert, matching the vectorized guard.
    return [((x := getattr(slot.unit, 'phrasal_stress', None)) is not None and x >= -1)
            for slot in mpos.slots]


def _s_demoted_vectorized(f):
    if not f.get("has_phrasal"):
        return np.zeros((f["L"], f["S"], f["N"]), dtype=np.int8)
    return ((f["phrasal_stress"] <= -2) & f["is_strong_pos"]).astype(np.int8)

@constraint(
    desc="No phrasally demoted word on strong position",
    scope="position",
    vectorized=_s_demoted_vectorized,
)
def s_demoted(mpos):
    if not mpos.is_prom:
        return [None] * len(mpos.slots)
    # guard None (see w_prom): absent phrasal data -> inert, not a TypeError.
    return [((x := getattr(slot.unit, 'phrasal_stress', None)) is not None and x <= -2)
            for slot in mpos.slots]


# --- Gradient phrasal variants (cadence's *_p / *_t constraints) ---
# Score w/s violations against the MetricalTree gradient values (pstress =
# within-phrase strength, tstress = cumulative sentence prominence; both
# min-max normalized per sentence, -1 sentinel where absent). Thresholds
# follow cadence: prominent = value > 0, unprominent = value == 0.
# Require syntax=True; inert otherwise.

def _w_stress_p_vectorized(f):
    if not f.get("has_gradient"):
        return np.zeros((f["L"], f["S"], f["N"]), dtype=np.int8)
    return ((f["pstress"] > 0) & f["is_weak_pos"]).astype(np.int8)

@constraint(
    desc="No syllable of a phrasally strong word (pstress>0) on weak position",
    scope="position",
    vectorized=_w_stress_p_vectorized,
)
def w_stress_p(mpos):
    if mpos.is_prom:
        return [None] * len(mpos.slots)
    return [(getattr(slot.unit, 'pstress', None) or 0) > 0 for slot in mpos.slots]


def _s_unstress_p_vectorized(f):
    if not f.get("has_gradient"):
        return np.zeros((f["L"], f["S"], f["N"]), dtype=np.int8)
    return ((f["pstress"] == 0) & f["is_strong_pos"]).astype(np.int8)

@constraint(
    desc="No syllable of a phrasally weak word (pstress==0) on strong position",
    scope="position",
    vectorized=_s_unstress_p_vectorized,
)
def s_unstress_p(mpos):
    if not mpos.is_prom:
        return [None] * len(mpos.slots)
    return [getattr(slot.unit, 'pstress', None) == 0 for slot in mpos.slots]


def _w_stress_t_vectorized(f):
    if not f.get("has_gradient"):
        return np.zeros((f["L"], f["S"], f["N"]), dtype=np.int8)
    return ((f["tstress"] > 0) & f["is_weak_pos"]).astype(np.int8)

@constraint(
    desc="No syllable of a sentence-prominent word (tstress>0) on weak position",
    scope="position",
    vectorized=_w_stress_t_vectorized,
)
def w_stress_t(mpos):
    if mpos.is_prom:
        return [None] * len(mpos.slots)
    return [(getattr(slot.unit, 'tstress', None) or 0) > 0 for slot in mpos.slots]


def _s_unstress_t_vectorized(f):
    if not f.get("has_gradient"):
        return np.zeros((f["L"], f["S"], f["N"]), dtype=np.int8)
    return ((f["tstress"] == 0) & f["is_strong_pos"]).astype(np.int8)

@constraint(
    desc="No syllable of a sentence-weak word (tstress==0) on strong position",
    scope="position",
    vectorized=_s_unstress_t_vectorized,
)
def s_unstress_t(mpos):
    if not mpos.is_prom:
        return [None] * len(mpos.slots)
    return [getattr(slot.unit, 'tstress', None) == 0 for slot in mpos.slots]


# Grid stress (gstress = RPPR grid height, L&P's preferred representation;
# the coarse coarsening of tstress). Same shape as w_stress_t/s_unstress_t but
# weighted against the grid instead of the cumulative tree stress.
def _w_stress_g_vectorized(f):
    if not f.get("has_gradient"):
        return np.zeros((f["L"], f["S"], f["N"]), dtype=np.int8)
    return ((f["gstress"] > 0) & f["is_weak_pos"]).astype(np.int8)

@constraint(
    desc="No syllable of a grid-prominent word (gstress>0) on weak position",
    scope="position",
    vectorized=_w_stress_g_vectorized,
)
def w_stress_g(mpos):
    if mpos.is_prom:
        return [None] * len(mpos.slots)
    return [(getattr(slot.unit, 'gstress', None) or 0) > 0 for slot in mpos.slots]


def _s_unstress_g_vectorized(f):
    if not f.get("has_gradient"):
        return np.zeros((f["L"], f["S"], f["N"]), dtype=np.int8)
    return ((f["gstress"] == 0) & f["is_strong_pos"]).astype(np.int8)

@constraint(
    desc="No syllable of a grid-weak word (gstress==0) on strong position",
    scope="position",
    vectorized=_s_unstress_g_vectorized,
)
def s_unstress_g(mpos):
    if not mpos.is_prom:
        return [None] * len(mpos.slots)
    return [getattr(slot.unit, 'gstress', None) == 0 for slot in mpos.slots]


def _w_peak_p_vectorized(f):
    if not f.get("has_gradient"):
        return np.zeros((f["L"], f["S"], f["N"]), dtype=np.int8)
    return ((f["pstrength"] == 1) & f["is_weak_pos"]).astype(np.int8)

@constraint(
    desc="No local phrasal peak on weak position",
    scope="position",
    vectorized=_w_peak_p_vectorized,
)
def w_peak_p(mpos):
    if mpos.is_prom:
        return [None] * len(mpos.slots)
    return [getattr(slot.unit, 'pstrength', None) == 1 for slot in mpos.slots]


def _s_trough_p_vectorized(f):
    if not f.get("has_gradient"):
        return np.zeros((f["L"], f["S"], f["N"]), dtype=np.int8)
    return ((f["pstrength"] == 0) & f["is_strong_pos"]).astype(np.int8)

@constraint(
    desc="No local phrasal valley on strong position",
    scope="position",
    vectorized=_s_trough_p_vectorized,
)
def s_trough_p(mpos):
    if not mpos.is_prom:
        return [None] * len(mpos.slots)
    return [getattr(slot.unit, 'pstrength', None) == 0 for slot in mpos.slots]


# === Line-scope constraints (not used in vectorized parsing) ===

@constraint(desc="Ensure the parse has exactly 5 peaks", scope="line")
def pentameter(parse):
    return parse.num_peaks != 5

@constraint(desc="Ensure the parse is iambic", scope="line")
def iambic(parse):
    return not parse.meter_str.startswith('-+')
