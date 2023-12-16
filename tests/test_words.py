import os,sys; sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
from pandas.testing import assert_frame_equal
disable_caching()
def test_WordFormList():
    # parsing not done yet so these are just testing the ordering of slot/word combos

    l = Line('in door')
    assert len(l.wordform_matrix)==2
    assert not l.wordform_matrix[0][0].children[0].is_stressed

    l = Line('in duty')
    assert len(l.wordform_matrix)==2
    assert not l.wordform_matrix[0][0].children[0].is_stressed

    l = Line('disaster in embrace')
    assert len(l.wordform_matrix)==2
    assert not l.wordform_matrix[0][0].children[0].is_stressed

    wfl = l.wordforms
    wfl2 = Line('disaster in embrace').wordforms
    assert wfl != wfl2
    assert wfl is not wfl2
    
def test_word():
    try:
        Word('szia',lang='hu')
        assert 0, 'Testing exception failed'
    except Exception:
        assert 1

    word = Word('hello')
    assert word.num_sylls == 2
    assert word.num_stressed_sylls == 1
    