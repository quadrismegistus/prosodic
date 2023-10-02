import os,sys; sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
from pandas.testing import assert_frame_equal


def test_WordFormList():
    # parsing not done yet so these are just testing the ordering of slot/word combos

    l = Line('of door')
    lp = Meter().parse(l)
    assert len(lp.wordform_matrix)==2
    assert len(lp.slot_matrix)==2
    assert not lp.wordform_matrix[0][0].children[0].is_stressed

    l = Line('of duty')
    lp = Meter(resolve_optionality=True).parse(l)
    assert len(lp.wordform_matrix)==2
    assert len(lp.slot_matrix)==2
    assert not lp.wordform_matrix[0][0].children[0].is_stressed

    l = Line('disaster of embrace')
    lp = Meter(resolve_optionality=True).parse(l)
    assert len(lp.wordform_matrix)==2
    assert len(lp.slot_matrix)==2
    syll = lp.slot_matrix[0][3]
    assert not syll.is_stressed
    