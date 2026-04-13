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
        wf1, wf2 = unit1.parent, unit2.parent
        if wf1 is not wf2:
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
        wf1, wf2 = unit1.wordform, unit2.wordform
        if wf1 is wf2:
            ol.append(None)
        else:
            if mpos.is_prom or not wf1.is_functionword or not wf2.is_functionword:
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
    return [None] * len(mpos.slots)


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
    return [None] * len(mpos.slots)


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


@constraint(
    desc="No function word on strong position",
    scope="position",
    vectorized=lambda f: (f["func_word"] & f["is_strong_pos"]).astype(np.int8),
)
def s_func(mpos):
    if not mpos.is_prom:
        return [None] * len(mpos.slots)
    return [getattr(slot.unit, 'is_functionword', False) for slot in mpos.slots]


def _word_boundary_vectorized(f):
    """Penalize when a word boundary falls inside a metrical foot (not at a foot edge)."""
    L, S, N = f["L"], f["S"], f["N"]
    if N < 2:
        return np.zeros((L, S, N), dtype=np.int8)
    result = np.zeros((L, S, N), dtype=np.int8)
    word_ids = f["word_ids_raw"]  # (L, N) — not broadcast
    pos_ids = f["position_ids"]   # (S, N)
    # word boundary at position i: word_ids[i] != word_ids[i-1]
    # foot boundary: position_ids changes
    for li in range(L):
        wids = word_ids[li]  # (N,)
        word_boundary = np.zeros(N, dtype=bool)
        word_boundary[1:] = wids[1:] != wids[:-1]
        foot_boundary = np.zeros((S, N), dtype=bool)
        foot_boundary[:, 1:] = pos_ids[:, 1:] != pos_ids[:, :-1]
        # violation: word boundary without foot boundary
        result[li] = (word_boundary[None, :] & ~foot_boundary).astype(np.int8)
    return result

@constraint(
    desc="Word boundary should align with foot boundary",
    scope="position",
    vectorized=_word_boundary_vectorized,
)
def word_foot(mpos):
    return [None] * len(mpos.slots)


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
    return [getattr(slot.unit, 'phrasal_stress', -99) >= -1 for slot in mpos.slots]


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
    return [getattr(slot.unit, 'phrasal_stress', 0) <= -2 for slot in mpos.slots]


# === Line-scope constraints (not used in vectorized parsing) ===

@constraint(desc="Ensure the parse has exactly 5 peaks", scope="line")
def pentameter(parse):
    return parse.num_peaks != 5

@constraint(desc="Ensure the parse is iambic", scope="line")
def iambic(parse):
    return not parse.meter_str.startswith('-+')
