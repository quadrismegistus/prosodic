import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.constraints import *
from pandas.testing import assert_frame_equal
from prosodic.imports import *

disable_caching()


def test_feet():
    # iambic test
    tstr = "embrace " * 5
    l = Line(tstr).parse()
    assert l.num_parses == 1
    assert l.best_parse.is_rising == True
    assert l.best_parse.nary_feet == 2
    assert l.best_parse.foot_type == "iambic"

    # trochaic test
    tstr = "dungeon " * 5
    l = Line(tstr).parse()
    assert l.num_parses == 1
    assert l.best_parse.is_rising == False
    assert l.best_parse.nary_feet == 2
    assert l.best_parse.foot_type == "trochaic"

    # anapestic
    tstr = "disembark " * 4
    l = Line(tstr).parse()
    assert l.best_parse.is_rising == True
    assert l.best_parse.nary_feet == 3
    assert l.best_parse.foot_type == "anapestic"

    # dactylic test
    tstr = "dangerous " * 4
    l = Line(tstr).parse()
    assert l.best_parse.is_rising == False
    assert l.best_parse.nary_feet == 3
    assert l.best_parse.foot_type == "dactylic"

    lx = Line(tstr)
    assert not lx._parses
    mopts1 = dict(max_s=1, max_w=1)
    lx.parse(**mopts1)
    assert lx._parses
    p1 = lx._parses
    m1 = lx.meter
    lx.parse(**mopts1)
    m2 = lx.meter
    assert m1 is m2
    assert lx._parses is p1

    lx.parse(max_s=2, max_w=2)
    m3 = lx.meter
    p2 = lx._parses
    assert m2 is not m3
    assert p1 is not p2


def test_text_parsing():
    t = Text(sonnet)
    assert len(t.lines) == 14
    t.parse(num_proc=1)
    assert len(t.parses.unbounded) >= 14
    assert t.parses.num_lines == 14
    assert len(t.parses.stats(by="line")) == 14
    assert len(t.parses.stats(by="syll")) > 14


def test_exhaustive():
    t = Text(sonnet)
    parses2 = t.line1.parse(exhaustive=True)
    parses3 = t.line1.parse(exhaustive=True)
    parses1 = t.line1.parse(exhaustive=False)
    assert parses1 is not parses2
    assert parses2 is parses3

    line = Line("A horse, a horse, my kingdom for a horse!")
    line.parse(exhaustive=True, max_s=10, max_w=10)
    assert line.parses.num_all == 1024

    line.parse(exhaustive=False, max_s=10, max_w=10)
    assert line.parses.num_all < 1024

    # ?
    # assert len(parses1.unbounded) < len(parses2.unbounded)


def test_bounding():
    s = "A horse a horse my kingdom for a horse"
    p1 = Parse(s, "ws" * 5)
    p2 = Parse(s, "sw" * 5)
    assert p1.bounds(p2)


def test_html():
    html = Text("disaster disaster disaster").line1.best_parse.to_html(
        as_str=True
    )
    assert "mtr_s" in html
    assert "viol_y" in html


def test_categorical_constraints():
    line = Line("dangerous " * 3)
    line.parse(categorical_constraints="foot_size", max_s=None, max_w=None)

    assert not any([px.meter_str.count("---") for px in line.parses.unbounded])
    assert not any([px.meter_str.count("+++") for px in line.parses.unbounded])


def test_standalone_parsing():
    p1 = Parse("my horse my horse my kingdom for a horse")
    assert p1.num_peaks == 5
    p2 = Parse("the horse the horse the kingdom for a horse")
    assert p2.num_peaks == 5
    assert set(p1.violset) == {"s_unstress"}  # my is currently stressed!?
    assert set(p2.violset) == {"s_unstress"}

    l = Text("the horse the horse the kingdom for a horse").wordforms
    p3 = Parse(l)
    assert p3.score == p2.score

    l = list(Text("the horse the horse the kingdom for a horse").wordforms)
    p4 = Parse(l)
    assert p3.score == p4.score

    l = list(
        Text("the horse the horse the kingdom for a horse").wordforms.data
    )
    p5 = Parse(l)
    assert p5.score == p4.score
    assert p5 != p4
    assert p5 is not p4

    assert (
        len(p5.slots) == len(p4.slots) == len(p3.slots) == len(p2.slots) ==
        len(p1.slots) == 10
    )

    p6 = Parse("my horse my horse my kingdom for a horse", "sw" * 5)
    assert p1 < p6
    assert p1.score < p6.score

    p7 = Parse("my horse my horse my kingdom for a horse", "ww" * 5)
    assert p7.foot_type == ""


def test_parselist():
    parses = Line("a horse " * 5).parse()
    assert parses.bounded
    assert parses.unbounded
    assert len(parses) == len(parses.all)
    assert len(parses.bounded) < len(parses)

    parses = Text(sonnet).parses
    ps1 = parses.stats_d(norm=False)
    ps2 = parses.stats_d(norm=True)
    assert set(ps1.keys()) == set(ps2.keys())
    assert set(ps1.values()) != set(ps2.values())

    html = parses._repr_html_()
    assert "</table>" in html

    l = Line("my horse my horse my kingdom for a horse")
    l.parse()
    assert l.best_parse.meter_str == "-+" * 5

    l = Line("my horse my horse my kingdom for a horse")
    # assert len(l.parses.unbounded)==1
    # assert len(l.bounded_parses)>1
    assert l.best_parse.meter_str == "-+" * 5


def test_constraints():
    l = Line("hello world " * 3)
    ckey = tuple(CONSTRAINTS.keys())
    l.parse(constraints=ckey)
    assert len(l.parses.unbounded)


def test_parse_iter():
    text = Text(sonnet)
    for parsed_line in text.parse_iter():
        break
    assert parsed_line.is_parseable
    assert parsed_line._parses
    assert parsed_line is text.lines[0]


def test_scansion():
    t = Text("into " * 3)
    t.parse(exhaustive=True, force=True)
    assert len(t.parses.data) > len(t.parses.scansions.data)
