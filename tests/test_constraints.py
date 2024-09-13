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
    meter = Meter(exhaustive=True, resolve_optionality=False, max_s=10, max_w=10)
    text = TextModel("my horse my horse my kingdom for a horse") # 10 sylls
    parselist = meter.parse_exhaustive(text)
    assert len(parselist) == 2**10
    assert parselist[0].meter_str == "-+" * 5


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
    