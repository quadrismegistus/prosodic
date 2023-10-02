import os,sys; sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *





def test_feet():
    # iambic test
    tstr = 'embrace ' * 5
    l = Line(tstr)
    assert l.num_parses == 1
    assert l.best_parse.is_rising == True
    assert l.best_parse.nary_feet == 2
    assert l.best_parse.foot_type == 'iambic'

    # trochaic test
    tstr = 'dungeon ' * 5
    l = Line(tstr)
    assert l.num_parses == 1
    assert l.best_parse.is_rising == False
    assert l.best_parse.nary_feet == 2
    assert l.best_parse.foot_type == 'trochaic'

    # anapestic
    tstr = 'disembark ' * 4
    l = Line(tstr)
    assert l.best_parse.is_rising == True
    assert l.best_parse.nary_feet == 3
    assert l.best_parse.foot_type == 'anapestic'

    # dactylic test
    tstr = 'dangerous ' * 4
    l = Line(tstr)
    assert l.best_parse.is_rising == False
    assert l.best_parse.nary_feet == 3
    assert l.best_parse.foot_type == 'dactylic'
    

