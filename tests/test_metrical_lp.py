"""Faithful Liberman & Prince (1977) grid engine, checked vs published figures.

The point of these tests: hand-encode L&P's own metrical trees from the
figures and confirm ``grid_heights`` reproduces the grid column heights they
print, and ``stress_numbers`` reproduces their (12) stress numbers. This
validates the grid engine independently of any parser.
"""
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from prosodic.analysis.metrical_lp import (
    figure_montana_cowboy,
    figure_thirteen_men,
    grid_heights,
    leaf,
    parse_lptree,
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


# ------------------------------------------- Phase 1: constituency → LPTree
# Nuclear-placement checks on real Stanza constituency parses. Skips cleanly
# if stanza / the constituency model is unavailable.

_NUCLEAR_CASES = [
    ("thirteen men", "men"),               # NSR: phrasal, rightmost strong
    ("red cows", "cows"),                  # (6a) phrasal
    ("John left", "left"),                 # (6b) phrasal
    ("American history teacher", "history"),  # flat JJ NN NN; NN-run compound
    ("law degree requirement", "law"),     # (9) nested all-noun compound
    ("kitchen towel rack", "kitchen"),     # nested all-noun compound
    ("the cat sat on the mat", "mat"),     # sentence NSR, skip function words
    ("the boy saw the dog", "dog"),        # ditransitive-ish, object nuclear
    ("reports of threats of violence", "violence"),  # PP recursion, rightmost
]


@pytest.mark.parametrize("text,nuclear", _NUCLEAR_CASES)
def test_constituency_nuclear_placement(text, nuclear):
    try:
        tree = parse_lptree(text)
    except Exception as e:  # stanza missing / model not downloaded
        pytest.skip(f"stanza constituency unavailable: {e}")
    if tree is None:
        pytest.skip("no parse")
    assert tree.dte.label == nuclear, (
        f"{text!r}: DTE {tree.dte.label!r}, expected {nuclear!r}"
    )
    # grid is well-formed: the nuclear word is the unique tallest column
    h = grid_heights(tree)
    labels = [lf.label for lf in tree.leaves()]
    assert h[labels.index(nuclear)] == max(h)
    assert h.count(max(h)) == 1


# --------------------------------------- Phase 2a: lexical stress tier (114)

def _grid_map(text):
    """(labels, structural grid, lexical-floored grid) for a parsed sentence."""
    from prosodic.analysis.metrical_lp import lexical_floors
    tree = parse_lptree(text)
    if tree is None:
        return None
    labels = [lf.label for lf in tree.leaves()]
    struct = dict(zip(labels, grid_heights(tree)))
    lex = dict(zip(labels, grid_heights(tree, lexical_floors(tree))))
    classes = {lf.label: lf.lclass for lf in tree.leaves()}
    return labels, struct, lex, classes


def test_lexical_floor_lifts_content_verb():
    # L&P (114): a content word gets >=2 grid levels even when structurally
    # weak. Structurally "sat" ties the function words at 1; the floor lifts it.
    try:
        got = _grid_map("the cat sat on the mat")
    except Exception as e:
        pytest.skip(f"stanza unavailable: {e}")
    if got is None:
        pytest.skip("no parse")
    _, struct, lex, _ = got
    assert struct["sat"] == 1                 # structurally weak
    assert struct["sat"] == struct["the"]     # ... tied with function words
    assert lex["sat"] == 2                     # ... lifted to content minimum
    assert lex["the"] == 1 and lex["on"] == 1  # function words stay at 1
    assert lex["mat"] == 3                     # nuclear preserved above them


def test_deps_demote_copula_and_aux():
    # The case that PROVES constituency+deps: copulas/auxiliaries are tagged
    # as content verbs (VBZ/VBD) by POS, but their dep labels (cop, aux) mark
    # them reducible. Without deps they'd wrongly floor to 2.
    try:
        cop = _grid_map("the cat is happy")
        aux = _grid_map("she has eaten the fish")
    except Exception as e:
        pytest.skip(f"stanza unavailable: {e}")
    if cop is None or aux is None:
        pytest.skip("no parse")
    _, _, cop_lex, cop_cls = cop
    assert cop_cls["is"] == -0.5     # ambiguous via dep 'cop', not content 0
    assert cop_lex["is"] == 1        # so NOT lifted to the content floor
    assert cop_lex["happy"] == max(cop_lex.values())  # predicate nuclear

    _, _, aux_lex, aux_cls = aux
    assert aux_cls["has"] == -0.5    # ambiguous via dep 'aux'
    assert aux_lex["has"] == 1
    assert aux_lex["eaten"] == 2     # the real (content) verb keeps its level


# ------------------------------------ Phase 2b: within-word syllable trees

def test_word_syllable_tree_grids():
    from prosodic.analysis.metrical_lp import _word_syllable_tree
    # hand-fed (text, stress_num): P=1.0, S=0.5, U=0.0 — vs L&P word grids
    cases = {
        # execute (116a): primary on first syllable → 2 · 1 · 1
        "execute": ([("e", 1.0), ("xe", 0.0), ("cute", 0.5)],
                    {"e": 2, "xe": 1, "cute": 1}, "e"),
        # Tennessee: secondary Ten sits between unstressed and primary
        "Tennessee": ([("Ten", 0.5), ("nes", 0.0), ("see", 1.0)],
                      {"Ten": 2, "nes": 1, "see": 3}, "see"),
        # Montana: leading unstressed adjoins weak, primary is the DTE
        "Montana": ([("Mon", 0.0), ("ta", 1.0), ("na", 0.0)],
                    {"Mon": 1, "ta": 2, "na": 1}, "ta"),
    }
    for word, (sylls, exp_grid, exp_dte) in cases.items():
        tree = _word_syllable_tree(sylls)
        labels = [lf.label for lf in tree.leaves()]
        assert dict(zip(labels, grid_heights(tree))) == exp_grid, word
        assert tree.dte.label == exp_dte, word


_SYLL_FIGURES = [
    # end-to-end: raw text → constituency → binarize → syllable expansion →
    # grid, checked against L&P's published *syllable* grids
    ("thirteen men", {"thir": 1, "teen": 2, "men": 3}),        # (105)
    ("Montana cowboy", {"Mon": 1, "ta": 2, "na": 1, "cow": 3, "boy": 1}),  # (108)
]


@pytest.mark.parametrize("text,expected", _SYLL_FIGURES)
def test_end_to_end_syllable_grid_matches_LP(text, expected):
    from prosodic.analysis.metrical_lp import expand_to_syllables
    try:
        phrasal = parse_lptree(text)
    except Exception as e:
        pytest.skip(f"stanza unavailable: {e}")
    if phrasal is None:
        pytest.skip("no parse")
    syll_tree = expand_to_syllables(phrasal)
    labels = [lf.label for lf in syll_tree.leaves()]
    assert dict(zip(labels, grid_heights(syll_tree))) == expected


# ------------------------------------------ punctuation + possessive clitics

def test_punctuation_is_not_a_metrical_terminal():
    # a comma must never become a grid column / receive stress
    try:
        tree = parse_lptree("From fairest creatures we desire increase,")
    except Exception as e:
        pytest.skip(f"stanza unavailable: {e}")
    if tree is None:
        pytest.skip("no parse")
    labels = [lf.label for lf in tree.leaves()]
    assert "," not in labels
    assert all(any(c.isalnum() for c in w) for w in labels)
    assert tree.dte.label == "increase"


def test_possessive_clitic_merged_not_stressed():
    # "summer's" must be one host word, not a separate NSR-strong 's terminal
    try:
        tree = parse_lptree("a summer's day")
    except Exception as e:
        pytest.skip(f"stanza unavailable: {e}")
    if tree is None:
        pytest.skip("no parse")
    labels = [lf.label for lf in tree.leaves()]
    assert "'s" not in labels
    assert any(w.endswith("'s") for w in labels)   # merged onto its host
    assert tree.dte.label == "day"                 # head noun nuclear, not 's
