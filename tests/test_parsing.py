import os,sys; sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
from pandas.testing import assert_frame_equal
from prosodic.constraints import *





def test_feet():
    # iambic test
    tstr = 'embrace ' * 5
    l = Line(tstr).parse()
    assert l.num_parses == 1
    assert l.best_parse.is_rising == True
    assert l.best_parse.nary_feet == 2
    assert l.best_parse.foot_type == 'iambic'

    # trochaic test
    tstr = 'dungeon ' * 5
    l = Line(tstr).parse()
    assert l.num_parses == 1
    assert l.best_parse.is_rising == False
    assert l.best_parse.nary_feet == 2
    assert l.best_parse.foot_type == 'trochaic'

    # anapestic
    tstr = 'disembark ' * 4
    l = Line(tstr).parse()
    assert l.best_parse.is_rising == True
    assert l.best_parse.nary_feet == 3
    assert l.best_parse.foot_type == 'anapestic'

    # dactylic test
    tstr = 'dangerous ' * 4
    l = Line(tstr).parse()
    assert l.best_parse.is_rising == False
    assert l.best_parse.nary_feet == 3
    assert l.best_parse.foot_type == 'dactylic'
    
    # feet nums
    tstr = 'disembark ' * 4
    l = Line(tstr).parse(max_s=1, max_w=1)
    assert l.best_parse.nary_feet == 2
    tstr = 'dangerous ' * 4
    l = Line(tstr).parse(max_s=1, max_w=1)
    assert l.best_parse.nary_feet == 2

    # parsing higher max s and max w will still yield same best parses
    lx = Line(tstr)
    l1 = lx.parse(max_s=2, max_w=2)
    l2 = lx.parse(max_s=None, max_w=None)
    assert len(l1.all_parses) < len(l2.all_parses)
    assert len(l1.best_parses) == len(l2.best_parses)
    assert_frame_equal(l1.best_parses.df, l2.best_parses.df)

    # test out dfparses
    assert l1.parse_stats
    assert l2.parse_stats
    pkeys = ['parse','nsylls','ncombo','nparse','nviols']
    for pk in pkeys: 
        assert l1.parse_stats.get(pk)
        assert l2.parse_stats.get(pk)

    # # parsing higher max s and max w will still yield same best parses
    # # even without categorical constraints
    # lx = Line(tstr)
    # constraints = [w_peak, w_stress, s_unstress, unres_across, unres_within]
    # m1 = Meter(max_s=2, max_w=2, constraints=constraints)
    # m2 = Meter(max_s=None, max_w=None, constraints=constraints)
    # l1 = lx.parse(meter=m1)
    # l2 = lx.parse(meter=m2)
    # assert len(l1.all_parses) < len(l2.all_parses)
    # assert len(l1.best_parses) == len(l2.best_parses)
    # assert_frame_equal(l1.best_parses.df, l2.best_parses.df)