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
    