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
