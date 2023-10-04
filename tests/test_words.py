import os,sys; sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
from pandas.testing import assert_frame_equal

def test_WordFormList():
    # parsing not done yet so these are just testing the ordering of slot/word combos

    l = Line('of door')
    assert len(l.wordform_matrix)==2
    assert not l.wordform_matrix[0][0].children[0].is_stressed

    l = Line('of duty')
    assert len(l.wordform_matrix)==2
    assert not l.wordform_matrix[0][0].children[0].is_stressed

    l = Line('disaster of embrace')
    assert len(l.wordform_matrix)==2
    assert not l.wordform_matrix[0][0].children[0].is_stressed
    