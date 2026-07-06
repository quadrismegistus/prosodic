"""Faithful Liberman & Prince (1977) grid engine, checked vs published figures.

The point of these tests: hand-encode L&P's own metrical trees from the
figures and confirm ``grid_heights`` reproduces the grid column heights they
print, and ``stress_numbers`` reproduces their (12) stress numbers. This
validates the grid engine independently of any parser.
"""
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from prosodic.analysis.metrical_lp import (
    figure_montana_cowboy,
    figure_thirteen_men,
    grid_heights,
    leaf,
    stress_numbers,
    sw,
    ws,
)


def test_thirteen_men_grid_105():
    # (105b): [thirteen[thir w, teen s]  men]  → thir 1, teen 2, men 3
    tree = figure_thirteen_men()
    assert [lf.label for lf in tree.leaves()] == ["thir", "teen", "men"]
    assert grid_heights(tree) == [1, 2, 3]
    assert stress_numbers(tree) == [3, 2, 1]
    assert tree.dte.label == "men"


def test_montana_cowboy_grid_108():
    # (108): Montana [[Mon w, tan s] s, a w]  cowboy [cow s, boy w]
    # grid: Mon 1, tan 2, a 1, cow 3, boy 1  (cow = nuclear)
    tree = figure_montana_cowboy()
    assert [lf.label for lf in tree.leaves()] == ["Mon", "tan", "a", "cow", "boy"]
    assert grid_heights(tree) == [1, 2, 1, 3, 1]
    # eq (12) counts domination depth, so it distinguishes Mon (4) from a (3)
    assert stress_numbers(tree) == [4, 2, 3, 1, 3]
    assert tree.dte.label == "cow"


def test_grid_is_a_coarsening_of_stress_numbers():
    # L&P (116): the grid does NOT over-differentiate weak syllables the way
    # stress numbers do — it is a consistent *coarsening*. So a strictly
    # taller grid column implies a strictly lower (stronger) stress number,
    # but equal grid heights may hide unequal stress numbers (e.g. Montana's
    # Mon vs a: both grid-height 1, but stress numbers 4 vs 3).
    for tree in (figure_thirteen_men(), figure_montana_cowboy()):
        h = grid_heights(tree)
        sn = stress_numbers(tree)
        for i in range(len(h)):
            for j in range(len(h)):
                if h[i] < h[j]:
                    assert sn[i] > sn[j], "taller column must be stronger"
        # and the nuclear DTE is the unique tallest column / stress number 1
        assert h.count(max(h)) == 1
        assert sn.count(1) == 1
        assert h.index(max(h)) == sn.index(1)


def test_dte_and_leaf_order():
    # a small synthetic balanced tree: [[a b][c d]] with root strong-left
    #   left  = [a s, b w]   (a strong)
    #   right = [c s, d w]   (c strong)
    #   root  = [left s, right w]  → DTE = a
    tree = sw(sw("a", "b"), sw("c", "d"))
    assert [lf.label for lf in tree.leaves()] == ["a", "b", "c", "d"]
    assert tree.dte.label == "a"
    h = grid_heights(tree)
    # a is nuclear (tallest); c is strong within its own pair so > b, d
    assert h[0] == max(h)               # a tallest
    assert h[2] > h[1] and h[2] > h[3]  # c above b and d
