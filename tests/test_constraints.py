import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic import *
from pandas.testing import assert_frame_equal

disable_caching()


def test_w_peak():
    p = Parse("poison", "-+")
    assert p.constraint_scores["w_peak"]
    assert p.positions[0].constraint_scores["w_peak"]

    p = Parse("poison", "+-")
    assert not p.constraint_scores["w_peak"]
    assert not p.positions[0].constraint_scores["w_peak"]


def test_w_stress():
    p = Parse("door", "-")
    assert p.constraint_scores["w_stress"]

    p = Parse("the", "-")
    assert not p.constraint_scores["w_stress"]


def test_s_unstress():
    p = Parse("the", "+")
    assert p.constraint_scores["s_unstress"]

    p = Parse("door", "+")
    assert not p.constraint_scores["s_unstress"]
