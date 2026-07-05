"""Tests for gradient phrasal stress (MetricalTree port) + grid integration.

The algorithm tests run on hand-built dependency arrays (no spaCy needed,
so they run in CI). The integration tests require spaCy + en_core_web_sm
and skip gracefully without them.
"""
import os
import sys

import numpy as np
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from prosodic.imports import *
from prosodic.texts.phrasal_stress import _mt_gradient, _mt_lstress_base

disable_caching()


# ------------------------------------------------- algorithm (no spaCy)

# Expected values below are cross-validated against cadence's MetricalTree
# (Dozat's algorithm over Stanza constituency parses, ambiguity ensemble
# enabled) — identical output on these sentences, 2026-07-05 differential.

def test_nsr_nuclear_stress_rightmost():
    # "the dog saw the cat": nuclear stress on the rightmost content word
    heads = np.array([1, 2, -1, 4, 2], dtype=np.int32)
    tags = np.array(['DT', 'NN', 'VBD', 'DT', 'NN'])
    deps = np.array(['det', 'nsubj', 'ROOT', 'det', 'dobj'])
    words = np.array(['the', 'dog', 'saw', 'the', 'cat'])
    nsyll = np.ones(5, dtype=np.int32)
    p, t = _mt_gradient(heads, words, tags, deps, nsyll, 5)
    assert np.allclose(t, [0.0, 2/3, 2/3, 1/3, 1.0])
    assert p.tolist() == [0.0, 1.0, 0.0, 0.0, 1.0]


def test_compound_stress_rule():
    # "the time machine broke": compound stress falls on TIME, not machine
    heads = np.array([2, 2, 3, -1], dtype=np.int32)
    tags = np.array(['DT', 'NN', 'NN', 'VBD'])
    deps = np.array(['det', 'compound', 'nsubj', 'ROOT'])
    words = np.array(['the', 'time', 'machine', 'broke'])
    nsyll = np.array([1, 1, 2, 1], dtype=np.int32)
    p, t = _mt_gradient(heads, words, tags, deps, nsyll, 4)
    assert np.allclose(t, [0.0, 2/3, 1/3, 1.0])
    assert p.tolist() == [0.0, 1.0, 0.0, 1.0]


def test_ambiguous_word_ensemble_is_gradient():
    # 'this' as a subject: the argument projection shields its preterminal,
    # so the 3-variant ensemble shows through as a gradient pstress
    heads = np.array([1, -1, 1], dtype=np.int32)
    tags = np.array(['DT', 'VBZ', 'JJ'])
    deps = np.array(['nsubj', 'ROOT', 'acomp'])
    words = np.array(['this', 'is', 'red'])
    nsyll = np.ones(3, dtype=np.int32)
    p, t = _mt_gradient(heads, words, tags, deps, nsyll, 3)
    assert abs(p[0] - 1/3) < 1e-9  # ensemble mean, not 0 or 1
    assert t[2] == 1.0             # nuclear on the predicate
    assert 0.0 < t[1] < 1.0        # intermediate value exists


def test_np_internal_modifiers_demoted():
    # prenominal amods sit bare in the NP: NSR demotion reaches them
    # ("the quick brown fox jumps": fox strong, adjectives weak)
    heads = np.array([3, 3, 3, 4, -1], dtype=np.int32)
    tags = np.array(['DT', 'JJ', 'JJ', 'NN', 'VBZ'])
    deps = np.array(['det', 'amod', 'amod', 'nsubj', 'ROOT'])
    words = np.array(['the', 'quick', 'brown', 'fox', 'jumps'])
    nsyll = np.ones(5, dtype=np.int32)
    p, _ = _mt_gradient(heads, words, tags, deps, nsyll, 5)
    assert p[3] == 1.0 and p[1] == 0.0 and p[2] == 0.0


def test_noun_head_shielded_from_right_complement():
    # "the house that Jack built": the inner NP core shields the head noun
    # from the relative clause's NSR win — house keeps pstress 1.0
    heads = np.array([1, -1, 3, 1, 5, 3], dtype=np.int32)
    #                the house that jack built(relcl of house)... simplified:
    # words: the(det->house) house(ROOT) that(dobj->built) Jack(nsubj->built) built(relcl->house)
    heads = np.array([1, -1, 4, 4, 1], dtype=np.int32)
    tags = np.array(['DT', 'NN', 'WDT', 'NNP', 'VBD'])
    deps = np.array(['det', 'ROOT', 'dobj', 'nsubj', 'relcl'])
    words = np.array(['the', 'house', 'that', 'Jack', 'built'])
    nsyll = np.ones(5, dtype=np.int32)
    p, t = _mt_gradient(heads, words, tags, deps, nsyll, 5)
    assert p[1] == 1.0  # house shielded (inner core)
    assert p[3] == 1.0  # Jack shielded (argument projection)
    assert t[4] == 1.0  # nuclear on built


def test_lstress_classes():
    words = np.array(['it', 'this', 'quickly', 'to'])
    tags = np.array(['PRP', 'DT', 'RB', 'TO'])
    deps = np.array(['nsubj', 'det', 'advmod', 'aux'])
    ls = _mt_lstress_base(words, tags, deps, 4)
    assert ls.tolist() == [-1.0, -0.5, 0.0, -1.0]


# Batch-2 differential regressions (cadence cross-validation, 2026-07-05).

def test_ditransitive_exact():
    # "She gave the boy a book" — exact match with cadence, every value
    heads = np.array([1, -1, 3, 1, 5, 1], dtype=np.int32)
    tags = np.array(['PRP', 'VBD', 'DT', 'NN', 'DT', 'NN'])
    deps = np.array(['nsubj', 'ROOT', 'det', 'dative', 'det', 'dobj'])
    words = np.array(['She', 'gave', 'the', 'boy', 'a', 'book'])
    p, t = _mt_gradient(heads, words, tags, deps, np.ones(6, dtype=np.int32), 6)
    assert np.allclose(p, [1/3, 0, 0, 1, 0, 1])
    assert np.allclose(t, [2/9, 2/3, 0, 2/3, 1/3, 1])


def test_pp_attachment_exact():
    # "Time flies like an arrow" — exact match with cadence, every value
    heads = np.array([1, -1, 1, 4, 2], dtype=np.int32)
    tags = np.array(['NN', 'VBZ', 'IN', 'DT', 'NN'])
    deps = np.array(['nsubj', 'ROOT', 'prep', 'det', 'pobj'])
    words = np.array(['Time', 'flies', 'like', 'an', 'arrow'])
    p, t = _mt_gradient(heads, words, tags, deps, np.ones(5, dtype=np.int32), 5)
    assert np.allclose(p, [1, 0, 0, 0, 1])
    assert np.allclose(t, [0.5, 0.5, 1/6, 0, 1])


def test_possessive_projects_no_compound_hit():
    # "His mother called the doctor": possessors project as inner NPs and
    # must not trigger the compound rule (beauty's ROSE, not BEAUTY'S rose)
    heads = np.array([1, 2, -1, 4, 2], dtype=np.int32)
    tags = np.array(['PRP$', 'NN', 'VBD', 'DT', 'NN'])
    deps = np.array(['poss', 'nsubj', 'ROOT', 'det', 'dobj'])
    words = np.array(['His', 'mother', 'called', 'the', 'doctor'])
    p, t = _mt_gradient(heads, words, tags, deps, np.ones(5, dtype=np.int32), 5)
    assert p.tolist() == [0.0, 1.0, 0.0, 0.0, 1.0]
    assert t[4] == 1.0  # nuclear on doctor


def test_coordination_conjuncts_stay_strong():
    # DELIBERATE divergence from Dozat/cadence (documented in the module):
    # both conjuncts keep pstress strength (cadence demotes the first);
    # tstress still orders the final conjunct above the first, matching.
    heads = np.array([3, 0, 0, -1], dtype=np.int32)
    tags = np.array(['NNS', 'CC', 'NNS', 'VBP'])
    deps = np.array(['nsubj', 'cc', 'conj', 'ROOT'])
    words = np.array(['Dogs', 'and', 'cats', 'fight'])
    p, t = _mt_gradient(heads, words, tags, deps, np.ones(4, dtype=np.int32), 4)
    assert p[0] == 1.0 and p[2] == 1.0   # conjuncts strong (ours)
    assert t[2] > t[0]                   # cats > Dogs (matches cadence)
    assert t[3] == 1.0                   # nuclear on fight


def test_flat_sentence_normalizes_nan():
    # single word: no variation -> NaN (as in cadence)
    heads = np.array([-1], dtype=np.int32)
    p, t = _mt_gradient(
        heads, np.array(['dog']), np.array(['NN']), np.array(['ROOT']),
        np.ones(1, dtype=np.int32), 1,
    )
    assert np.isnan(t[0]) and np.isnan(p[0])


# ------------------------------------------------- grid quantization (no spaCy)

def test_grid_phrasal_heights():
    from prosodic.analysis import grid_data

    t = TextModel("When in the chronicle of wasted time")
    t.parse()
    bp = t.lines[0].best_parse
    n = len(grid_data(bp))
    # nuclear on the last syllable's word, mid prominence on another primary
    phrasal = [None] * n
    phrasal[-1] = 1.0   # TIME (primary, nuclear) -> height 5
    phrasal[1] = 0.6    # IN (primary) -> height 4
    phrasal[2] = 1.0    # the (unstressed): phrasal must NOT extend it
    rows = grid_data(bp, phrasal=phrasal)
    assert rows[-1]["height"] == 5
    assert rows[1]["height"] == 4
    assert rows[2]["height"] == 1


# ------------------------------------------------- gradient constraints

def _fake_features(pstress_row, tstress_row, weak_pos_row):
    L, S, N = 1, 1, len(pstress_row)
    weak = np.array(weak_pos_row, dtype=bool)[None, None, :]
    return {
        "pstress": np.array(pstress_row, dtype=np.float32)[None, None, :],
        "tstress": np.array(tstress_row, dtype=np.float32)[None, None, :],
        "is_weak_pos": weak,
        "is_strong_pos": ~weak,
        "has_gradient": True,
        "L": L, "S": S, "N": N,
    }


def test_gradient_constraint_lambdas():
    from prosodic.parsing.constraints import (
        _s_unstress_p_vectorized, _s_unstress_t_vectorized,
        _w_stress_p_vectorized, _w_stress_t_vectorized,
    )
    # sylls:      A     B     C     D
    # pstress:    1.0   0.0   0.5   -1(absent)
    # position:   weak  strong weak strong
    f = _fake_features([1.0, 0.0, 0.5, -1.0], [1.0, 0.0, 0.5, -1.0],
                       [True, False, True, False])
    assert _w_stress_p_vectorized(f).ravel().tolist() == [1, 0, 1, 0]
    assert _s_unstress_p_vectorized(f).ravel().tolist() == [0, 1, 0, 0]
    assert _w_stress_t_vectorized(f).ravel().tolist() == [1, 0, 1, 0]
    assert _s_unstress_t_vectorized(f).ravel().tolist() == [0, 1, 0, 0]
    # -1 sentinel (absent/NaN) never violates either polarity
    f_off = dict(f, has_gradient=False)
    assert _w_stress_p_vectorized(f_off).sum() == 0


def test_gradient_constraints_inert_without_syntax():
    t = TextModel("When in the chronicle of wasted time")
    t.parse(constraints=('w_stress', 's_unstress', 'w_stress_t', 's_unstress_p'))
    bp = t.lines[0].best_parse
    assert all(
        v == 0 for k, v in bp.viold.items()
        if k.endswith('_t') or k.endswith('_p')
    )


# ------------------------------------------------- integration (needs spaCy)

def _syntax_text(txt):
    pytest.importorskip("spacy")
    try:
        return TextModel(txt, syntax=True)
    except OSError:
        pytest.skip("spaCy model en_core_web_sm not installed")


def test_syntax_columns():
    t = _syntax_text("When in the chronicle of wasted time, I see descriptions.")
    df = t._syll_df
    assert "pstress" in df.columns and "tstress" in df.columns
    vals = df["tstress"].dropna()
    assert ((vals >= 0) & (vals <= 1)).all()
    assert (vals == 1.0).any()  # some word carries nuclear stress
    # punctuation rows are NaN
    assert df.loc[df["is_punc"] == 1, "tstress"].isna().all()


def test_gradient_constraints_active_with_syntax():
    t = _syntax_text("When in the chronicle of wasted time")
    t.parse(constraints=(
        'w_stress', 's_unstress',
        'w_stress_p', 's_unstress_p', 'w_stress_t', 's_unstress_t',
    ))
    # some parse among the candidates must incur gradient violations
    parses = t.lines[0].parses
    total = sum(
        p.viold.get(c, 0)
        for p in parses.unbounded
        for c in ('w_stress_p', 's_unstress_p', 'w_stress_t', 's_unstress_t')
    )
    assert total > 0


def test_grid_str_includes_phrasal_rows():
    t = _syntax_text("When in the chronicle of wasted time\nI see descriptions of the fairest wights")
    t.parse()
    s0 = t.lines[0].grid_str()
    s1 = t.lines[1].grid_str()
    # lexical-only grids max out at 3 mark rows (+text+meter = 5 lines);
    # phrasal rows push at least one of these lines beyond that
    assert max(len(s0.split("\n")), len(s1.split("\n"))) >= 6
    # explicit opt-out returns to lexical-only heights
    s0_plain = t.lines[0].grid_str(phrasal=None)
    assert len(s0_plain.split("\n")) == 5
