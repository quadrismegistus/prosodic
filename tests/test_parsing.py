from prosodic.imports import *

def test_parsing():
    # iambic test
    tstr = 'embrace ' * 5
    l = Line(tstr)
    assert l.num_parses == 1
    assert l.best_parse.is_rising == True
    assert l.best_parse.nary_feet == 2

    # trochaic test
    tstr = 'dungeon ' * 5
    l = Line(tstr)
    assert l.num_parses == 1
    assert l.best_parse.is_rising == False
    assert l.best_parse.nary_feet == 2

    # anapestic
    tstr = 'disembark ' * 4
    l = Line(tstr)
    assert l.best_parse.is_rising == True
    assert l.best_parse.nary_feet == 3

    # dactylic test
    tstr = 'dangerous ' * 4
    l = Line(tstr)
    assert l.best_parse.is_rising == False
    assert l.best_parse.nary_feet == 3
    

    