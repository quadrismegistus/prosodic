import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic import *

def test_w_peak():
    p = Parse("poisons", "-+", constraints=['w_peak'])
    assert p.viold["w_peak"]
    assert p.positions[0].viold["w_peak"]

    p = Parse("poisons", "+-")
    assert not p.viold["w_peak"]
    assert not p.positions[0].viold["w_peak"]


def test_w_stress():
    p = Parse("door", "-", constraints=['w_stress'])
    assert p.viold["w_stress"]

    p = Parse("the", "-")
    assert not p.viold["w_stress"]


def test_s_unstress():
    p = Parse("the", "+", constraints=['s_unstress'])
    assert p.viold["s_unstress"]

    p = Parse("door", "+")
    assert not p.viold["s_unstress"]


def test_s_trough():
    p = Parse("banana", "+--", constraints=['s_trough'])
    assert p.viold["s_trough"]
    assert p.positions[0].viold["s_trough"]

    p = Parse("banana", "-+-")
    assert not p.viold["s_trough"]
    assert not p.positions[1].viold["s_trough"]


def test_foot_size():
    p = Parse("cat", "-", constraints=['foot_size'])
    assert not p.viold["foot_size"]

    p = Parse("caterpillar", "---", constraints=['foot_size'])
    assert p.viold["foot_size"]
    assert p.positions[0].viold["foot_size"]


def test_unres_within():
    p = Parse("butterfly", "+--", constraints=['unres_within'])
    assert p.viold["unres_within"]
    assert p.positions[-1].viold["unres_within"]
    assert not p.positions[-1].slots[0].viold["unres_within"]
    assert p.positions[-1].slots[1].viold["unres_within"]

    p = Parse("butter fly", "+- -", constraints=['unres_within'])
    assert not p.viold["unres_within"]
    assert not p.positions[0].viold["unres_within"]


def test_unres_across():
    p = Parse("of the", "--", constraints=['unres_across'])
    assert not p.viold["unres_across"]
    assert not p.positions[0].viold["unres_across"]

    p = Parse("the cat", "--", constraints=['unres_across'])
    assert p.viold["unres_across"] == 1
    assert p.positions[0].viold["unres_across"]
    assert not p.positions[0].slots[0].viold["unres_across"]
    assert p.positions[0].slots[1].viold["unres_across"]


# --- Entity reference-impl regressions (AUDIT C16/C17). These constraints'
# reference bodies (used by manually-built Parse objects) were no-ops or wrong;
# now they must match the vectorized parser used by TextModel.parse(). ---

def test_clash():
    # adjacent stressed syllables, at least one on a weak position
    p = Parse("big cat", "-+", constraints=['clash'])
    assert p.viold["clash"] == 1
    assert not p.positions[0].slots[0].viold["clash"]
    assert p.positions[1].slots[0].viold["clash"]  # violation on the 2nd syllable

    # no clash when the two stressed syllables are not adjacent
    p = Parse("cat in a hat", "+--+", constraints=['clash'])
    assert not p.viold["clash"]


def test_lapse():
    # adjacent unstressed syllables, at least one on a strong position
    p = Parse("in the box", "-+-", constraints=['lapse'])
    assert p.viold["lapse"] == 1
    assert p.positions[1].slots[0].viold["lapse"]  # 'the' on strong, prev unstressed

    p = Parse("the the cat", "+--", constraints=['lapse'])
    assert p.viold["lapse"] == 1


def test_word_foot():
    # a disyllabic position spanning a word boundary violates word_foot
    p = Parse("big cat", "ss", constraints=['word_foot'])
    assert p.viold["word_foot"] == 1
    assert not p.positions[0].slots[0].viold["word_foot"]
    assert p.positions[0].slots[1].viold["word_foot"]

    # a single polysyllabic word filling one position does not
    p = Parse("reason", "ss", constraints=['word_foot'])
    assert not p.viold["word_foot"]


def test_s_func():
    # a function word on a strong position violates s_func
    p = Parse("the cat", "+-", constraints=['s_func'])
    assert p.viold["s_func"] == 1
    assert p.positions[0].slots[0].viold["s_func"]

    # a content word on a strong position does not
    p = Parse("cat the", "+-", constraints=['s_func'])
    assert not p.viold["s_func"]


def test_repeated_word_is_across_boundary():
    # AUDIT C17: WordForms are shared/duck-typed across tokens of a word type,
    # so the same-word test must use the word *occurrence*. Two adjacent "the"
    # tokens sharing one metrical position must count as a WORD boundary
    # (word_foot fires) and NOT as a within-word resolution.
    p = Parse("the the", "ss", constraints=['unres_within', 'unres_across', 'word_foot'])
    slot2 = p.positions[0].slots[1]
    assert slot2.viold["word_foot"] == 1        # boundary between the two "the"s
    assert not slot2.viold["unres_within"]      # not treated as word-internal
    assert p.viold["unres_across"] == 1         # treated as across-word


def test_manual_parse_matches_vectorized_parser():
    # A manually-built Parse must produce the same per-constraint violations as
    # the vectorized parser (TextModel.parse) for the same line and scansion.
    cons = ["w_stress", "s_unstress", "w_peak", "s_trough", "unres_within",
            "unres_across", "foot_size", "clash", "lapse", "w_heavy", "s_light",
            "s_func", "word_foot"]
    line = "the the cat sat"
    manual = Parse(line, "wwss", constraints=cons)

    t = TextModel(line)
    t.parse(constraints=cons)
    df_parse = next(p for p in t.lines[0].parses if p.meter_str == manual.meter_str)
    assert dict(manual.viold) == dict(df_parse.viold)


def test_reinit_does_not_overwrite_violations():
    # AUDIT C16: re-running ParsePosition.init (as Parse.concat does) must not
    # clobber already-computed violations with zeros.
    cons = ["clash", "lapse", "word_foot", "s_func", "w_stress", "s_unstress"]
    p = Parse("big cat the the", "swss", constraints=cons)
    before = dict(p.viold)
    for pos in p.positions:
        pos.init()  # re-init: must be a no-op for already-computed constraints
    p.__dict__.pop("positions_viold", None)
    p.__dict__.pop("viold", None)
    assert dict(p.viold) == before


def test_pentameter():
    p = Parse("to be or not to be that is the question", "+-+-+-+-+-", constraints=['pentameter'], scope='line')
    assert not p.viold["pentameter"]

    p = Parse("to be or not to be that is", "+-+-+-+-", constraints=['pentameter'], scope='line')
    assert p.viold["pentameter"]


def test_multiple_constraints():
    p = Parse("the big cat sleeps", "--+-", constraints=['w_stress', 'unres_across','foot_size'])
    assert p.viold["w_stress"]
    assert p.viold["unres_across"]
    assert not p.viold["foot_size"]


def test_constraint_weights():
    meter = Meter(constraints={"w_stress": 10, "s_unstress": 2})
    p = Parse("the big cat", "-+-", meter=meter)
    assert p.viold["w_stress"] == 1
    assert p.viold["s_unstress"] == 0
    assert p.score == 10
    assert p.num_viols == 1


def test_parse_unit():
    text = TextModel("To be or not to be, that is the question.")
    parselistlist = text.parse(parse_unit='linepart', combine_by=None)
    assert len(parselistlist) == 2

    parselistlist = text.parse(parse_unit='line', combine_by=None)
    assert len(parselistlist) == 1


def test_exhaustive_parsing():
    meter = Meter(resolve_optionality=False, max_s=10, max_w=10)
    text = TextModel("my horse my horse my kingdom for a horse") # 10 sylls
    parselist = meter.parse_exhaustive(text)
    assert len(parselist) == 2**10
    # check that the expected iambic scansion is among the results
    meter_strs = {p.meter_str for p in parselist}
    assert "-+-+-+-+-+" in meter_strs


def test_resolve_optionality():
    # meter = Meter(resolve_optionality=True)
    # text = TextModel("the hour")
    # parses = meter.parse(text)
    # print(parses)
    # assert {len(p.slots) for pl in parses for p in pl} == {2,3}
    
    meter = Meter(resolve_optionality=False)
    text = TextModel("the hour")
    parses = meter.parse(text)
    assert {len(p.slots) for pl in parses for p in pl} == {2}  # hour comes first


# ============================================================================
# Coverage of constraint reference-impl bodies + helper utilities.
# The vectorized lambdas run during normal parsing; the Python function bodies
# below run only for manually-constructed Parse objects (entity path). These
# tests exercise those bodies (and the constraint_utils helpers) directly and
# assert concrete violation counts. (Appended to raise coverage of
# prosodic/parsing/constraints.py and constraint_utils.py.)
# ============================================================================

import types
import numpy as np
import pytest
from prosodic.parsing import constraints as _C
from prosodic.parsing import constraint_utils as _cu


def test_iambic():
    # Line-scope: violated when the meter does not open with a weak-strong foot.
    p = Parse("cat the", "+-", constraints=['iambic'], scope='line')
    assert p.meter_str == "+-"
    assert p.viold["iambic"] == 1

    p = Parse("the cat", "-+", constraints=['iambic'], scope='line')
    assert p.meter_str == "-+"
    assert p.viold.get("iambic", 0) == 0


def test_unres_within_light_stressed_first_syllable():
    # unres_within's else branch: a disyllabic within-word position whose first
    # syllable is LIGHT and STRESSED does NOT violate (the resolution is legal).
    p = Parse("many", "ss", constraints=['unres_within'])
    pos = p.positions[0]
    assert len(pos.slots) == 2                      # single 2-slot position
    assert not pos.slots[0].unit.is_heavy           # light...
    assert pos.slots[0].unit.is_stressed            # ...and stressed
    assert p.viold.get("unres_within", 0) == 0

    # contrast: a HEAVY stressed first syllable DOES violate
    p = Parse("baby", "ss", constraints=['unres_within'])
    assert p.positions[0].slots[0].unit.is_heavy
    assert p.viold["unres_within"] == 1


def test_unres_across_within_word_no_violation():
    # unres_across only fires ACROSS a word boundary. A disyllabic position that
    # sits entirely inside one word (same wordtoken) is a no-op.
    p = Parse("many", "--", constraints=['unres_across'])
    assert len(p.positions[0].slots) == 2
    assert p.viold.get("unres_across", 0) == 0


def test_clash_lapse_vectorized_single_syllable_noop():
    # With fewer than two syllables there are no adjacent pairs, so the
    # adjacency constraints short-circuit to an all-zero (L, S, N) array.
    for fn in (_C._clash_vectorized, _C._lapse_vectorized):
        out = fn({"L": 2, "S": 3, "N": 1})
        assert out.shape == (2, 3, 1)
        assert out.dtype == np.int8
        assert not out.any()


def test_global_slot_context_defensive_fallbacks():
    # _global_slot_context returns (parse_slots, start_index). Two defensive
    # fallbacks return start_index 0: (a) an empty position, (b) a position
    # whose first slot is not found in the parse's slot list.
    a, b, orphan = object(), object(), object()
    empty_pos = types.SimpleNamespace(parse=types.SimpleNamespace(slots=[a, b]), slots=[])
    assert _C._global_slot_context(empty_pos) == ([a, b], 0)

    orphan_pos = types.SimpleNamespace(parse=types.SimpleNamespace(slots=[a, b]), slots=[orphan])
    assert _C._global_slot_context(orphan_pos) == ([a, b], 0)

    # sanity: a slot that IS present resolves to its real index
    normal_pos = types.SimpleNamespace(parse=types.SimpleNamespace(slots=[a, b]), slots=[b])
    assert _C._global_slot_context(normal_pos) == ([a, b], 1)


def test_slot_is_functionword_fallbacks():
    # When the unit has no wordform, fall back to the unit's own is_functionword.
    slot = types.SimpleNamespace(unit=types.SimpleNamespace(is_functionword=True))
    assert _C._slot_is_functionword(slot) is True
    slot = types.SimpleNamespace(unit=types.SimpleNamespace(is_functionword=False))
    assert _C._slot_is_functionword(slot) is False

    # When wordform.is_functionword raises AttributeError, fall back likewise.
    class _RaisingWF:
        @property
        def is_functionword(self):
            raise AttributeError("boom")

    unit = types.SimpleNamespace(wordform=_RaisingWF(), is_functionword=True)
    assert _C._slot_is_functionword(types.SimpleNamespace(unit=unit)) is True


# --- Phrasal-stress constraint reference bodies (require syntax data). We build
# a plain Parse (no syntax) then attach known phrasal values to each syllable
# unit and invoke each constraint body directly, asserting per-position results.
# Line "the cat and dog" scanned "-+-+" gives 4 one-slot positions w/s/w/s. ---

def _phrasal_parse():
    p = Parse("the cat and dog", "-+-+")
    assert [pos.meter_val for pos in p.positions] == ['w', 's', 'w', 's']
    assert all(len(pos.slots) == 1 for pos in p.positions)
    vals = dict(
        phrasal_stress=[0, -2, -5, 0],
        pstress=[0.5, 0.0, 0.0, 0.8],
        tstress=[0.5, 0.0, 0.0, 0.8],
        gstress=[0.5, 0.0, 0.0, 0.8],
        pstrength=[1.0, 0.0, 0.0, 1.0],
    )
    for i, pos in enumerate(p.positions):
        u = pos.slots[0].unit
        for k, v in vals.items():
            setattr(u, k, v[i])
    return p


def test_phrasal_constraint_entity_bodies():
    p = _phrasal_parse()

    def col(fn):
        return [fn(pos) for pos in p.positions]

    # weak-position constraints: prominent syllable on a weak position violates;
    # strong positions return [None] (guarded out).
    W = [[True], [None], [False], [None]]
    # strong-position constraints: weak syllable on a strong position violates;
    # weak positions return [None].
    S = [[None], [True], [None], [False]]

    assert col(_C.w_prom) == W          # phrasal_stress >= -1 on weak
    assert col(_C.s_demoted) == S       # phrasal_stress <= -2 on strong
    assert col(_C.w_stress_p) == W      # pstress > 0 on weak
    assert col(_C.s_unstress_p) == S    # pstress == 0 on strong
    assert col(_C.w_stress_t) == W      # tstress > 0 on weak
    assert col(_C.s_unstress_t) == S    # tstress == 0 on strong
    assert col(_C.w_stress_g) == W      # gstress > 0 on weak
    assert col(_C.s_unstress_g) == S    # gstress == 0 on strong
    assert col(_C.w_peak_p) == W        # pstrength == 1 on weak
    assert col(_C.s_trough_p) == S      # pstrength == 0 on strong


_PHRASAL_WEAK_VEC = [
    _C._w_prom_vectorized, _C._w_stress_p_vectorized, _C._w_stress_t_vectorized,
    _C._w_stress_g_vectorized, _C._w_peak_p_vectorized,
]
_PHRASAL_STRONG_VEC = [
    _C._s_demoted_vectorized, _C._s_unstress_p_vectorized, _C._s_unstress_t_vectorized,
    _C._s_unstress_g_vectorized, _C._s_trough_p_vectorized,
]


def test_phrasal_vectorized_inert_without_syntax():
    # Every phrasal vectorized helper is inert (all-zero) when the feature dict
    # lacks has_phrasal / has_gradient -- matching syntax=False parsing.
    for fn in _PHRASAL_WEAK_VEC + _PHRASAL_STRONG_VEC:
        out = fn({"L": 2, "S": 3, "N": 4})
        assert out.shape == (2, 3, 4)
        assert out.dtype == np.int8
        assert not out.any(), fn.__name__


def test_phrasal_vectorized_active():
    # With phrasal/gradient features present, each helper flags the expected
    # syllable. L=S=1, N=2; syll 0 sits on a weak position, syll 1 on a strong
    # position. Weak helpers flag syll 0; strong helpers flag syll 1.
    f = dict(
        has_phrasal=True, has_gradient=True, L=1, S=1, N=2,
        phrasal_stress=np.array([[[0, -2]]]),
        pstress=np.array([[[0.5, 0.0]]]),
        tstress=np.array([[[0.5, 0.0]]]),
        gstress=np.array([[[0.5, 0.0]]]),
        pstrength=np.array([[[1.0, 0.0]]]),
        is_weak_pos=np.array([[[True, False]]]),
        is_strong_pos=np.array([[[False, True]]]),
    )
    for fn in _PHRASAL_WEAK_VEC:
        assert np.array_equal(fn(f), np.array([[[1, 0]]], dtype=np.int8)), fn.__name__
    for fn in _PHRASAL_STRONG_VEC:
        assert np.array_equal(fn(f), np.array([[[0, 1]]], dtype=np.int8)), fn.__name__


def test_phrasal_w_prom_inert_without_phrasal_data():
    # Parsing plain (non-syntax) text with w_prom produces no violations (inert),
    # mirroring the vectorized has_phrasal-guarded path. Regression: the entity
    # body used to raise TypeError because Entity.__getattr__ returns None,
    # shadowing the getattr default (now guarded explicitly). Same for s_demoted.
    assert Parse("the cat", "+-", constraints=['w_prom']).viold.get("w_prom", 0) == 0
    assert Parse("the cat", "+-", constraints=['s_demoted']).viold.get("s_demoted", 0) == 0


def test_default_constraint_helpers_logic():
    # get_default_constraint_names()/get_default_constraints() resolve the default
    # constraint set. Regression: they used to reference an undefined
    # DEFAULT_CONSTRAINT_NAMES and raise NameError (fixed to use DEFAULT_CONSTRAINTS).
    names = _cu.get_default_constraint_names()
    assert names == _cu.DEFAULT_CONSTRAINTS
    assert "w_stress" in names

    cons = _cu.get_default_constraints()
    assert len(cons) == len(names)
    assert all(callable(c) and getattr(c, "scope", None) == "position" for c in cons)
    # each returned func is the one registered under its name
    all_cons = _cu.get_all_constraints()
    assert all(c is all_cons[n] for c, n in zip(cons, names))


def test_constraint_utils_scope_helpers():
    # get_constraint_descriptions: name -> human-readable desc
    descs = _cu.get_constraint_descriptions()
    assert descs["w_stress"] == _C.w_stress.desc

    # get_constraint_scope resolves callables, name strings, and unknowns
    assert _cu.get_constraint_scope(_C.w_stress) == "position"   # callable
    assert _cu.get_constraint_scope("w_stress") == "position"    # known name
    assert _cu.get_constraint_scope("iambic") == "line"          # line-scope name
    assert _cu.get_constraint_scope("not_a_constraint") == "unknown"
    assert _cu.get_constraint_scope(123) == "unknown"            # neither

    # get_constraints() with no filter returns everything (both scopes)
    every = _cu.get_constraints()
    assert "w_stress" in every and "iambic" in every

    # scope-filtered helpers
    pos = _cu.get_position_constraints()
    assert "w_stress" in pos and all(f.scope == "position" for f in pos.values())
    # no constraint is registered with scope 'parse', so this is empty
    assert _cu.get_parse_constraints() == {}

    # parse_constraint_weights accepts a whitespace string or a list; a missing
    # weight defaults to 1.0
    assert _cu.parse_constraint_weights("w_stress/2 s_unstress") == {
        "w_stress": 2.0, "s_unstress": 1.0}
    assert _cu.parse_constraint_weights(["w_peak/3"]) == {"w_peak": 3.0}
