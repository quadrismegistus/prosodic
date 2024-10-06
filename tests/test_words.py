import os,sys; sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
from pandas.testing import assert_frame_equal
disable_caching()
def test_WordFormList():
    # parsing not done yet so these are just testing the ordering of slot/word combos

    l = TextModel('in door').line1
    assert len(l.wordtoken_matrix)==2
    assert l.wordtoken_matrix[0].sylls[0].is_stressed is False

    l = TextModel('in duty').line1
    assert len(l.wordtoken_matrix)==2
    assert l.wordtoken_matrix[0].sylls[0].is_stressed is False

    l = TextModel('disaster in embrace').line1
    assert len(l.wordtoken_matrix)==2
    assert l.wordtoken_matrix[0].sylls[0].is_stressed is False

def test_word():
    try:
        TextModel('szia',lang='hu').wordtype1
        assert 0, 'Testing exception failed'
    except Exception:
        assert 1

    word = TextModel('hello').wordtype1
    assert word.num_sylls == 2
    assert word.num_stressed_sylls == 1
    