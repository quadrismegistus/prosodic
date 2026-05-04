"""Tests for prosodic.analysis (poesy port).

Covers rhyme scheme matching, line-length scheme detection, meter-type
classification, and the integrated TextModel properties (text.meter_type,
text.rhyme_scheme, text.summary, text.is_sonnet).
"""
import pytest

from prosodic.analysis import (
    classify_meter_type,
    compute_rhyme_ids,
    detect_line_scheme,
    is_sonnet,
    match_rhyme_scheme,
    nums_to_scheme,
    scheme_repr,
    scheme_to_nums,
)
from prosodic.imports import *  # noqa: F401,F403

SHAKESPEARE_106 = """When in the chronicle of wasted time
I see descriptions of the fairest wights,
And beauty making beautiful old rhyme
In praise of ladies dead and lovely knights,
Then, in the blazon of sweet beauty's best,
Of hand, of foot, of lip, of eye, of brow,
I see their antique pen would have express'd
Even such a beauty as you master now.
So all their praises are but prophecies
Of this our time, all you prefiguring;
And, for they look'd but with divining eyes,
They had not skill enough your worth to sing:
For we, which now behold these present days,
Had eyes to wonder, but lack tongues to praise."""


@pytest.fixture(scope="module")
def sonnet():
    t = TextModel(SHAKESPEARE_106)
    t.parse()
    return t


# ---------------------------------------------------------------- pure helpers


def test_scheme_to_nums_simple():
    assert scheme_to_nums("aa") == [1, 1]
    assert scheme_to_nums("ab") == [0, 0]  # singletons → 0
    assert scheme_to_nums("abab") == [1, 2, 1, 2]
    assert scheme_to_nums("abab cdcd") == [1, 2, 1, 2, 3, 4, 3, 4]


def test_nums_to_scheme_roundtrip():
    assert nums_to_scheme([0, 1, 1]) == ["-", "a", "a"]
    assert nums_to_scheme([1, 2, 1, 2]) == ["a", "b", "a", "b"]


def test_match_rhyme_scheme_couplet():
    # Two pairs of couplets: aabb
    result = match_rhyme_scheme([1, 1, 2, 2])
    assert result is not None
    # "Couplet" is one of the named schemes; it should at least appear
    # in the candidates with non-zero score
    names = [c[0] for c in result["candidates"]]
    assert any("Couplet" in n for n in names)


def test_match_rhyme_scheme_empty():
    assert match_rhyme_scheme([]) is None


# ----------------------------------------------------------- line scheme


def test_detect_line_scheme_invariable():
    combo, diff = detect_line_scheme([5] * 10, beat=True)
    assert combo == (5,)


def test_detect_line_scheme_alternating():
    # Ballad meter: 4-3-4-3
    combo, diff = detect_line_scheme([4, 3, 4, 3, 4, 3, 4, 3], beat=True)
    assert combo == (4, 3)


def test_detect_line_scheme_empty():
    combo, diff = detect_line_scheme([], beat=True)
    assert combo is None


def test_scheme_repr():
    assert scheme_repr((5,), beat=True) == "Pentameter"
    assert "Alternating" in scheme_repr((4, 3), beat=True)


# ----------------------------------------------------------- meter type


def test_meter_type_iambic(sonnet):
    mt = classify_meter_type(sonnet)
    assert mt["foot"] == "binary"
    assert mt["head"] == "final"
    assert mt["type"] == "iambic"


# ----------------------------------------------------------- TextModel wiring


def test_text_meter_type(sonnet):
    assert sonnet.meter_type["type"] == "iambic"


def test_text_line_scheme(sonnet):
    assert sonnet.line_scheme["combo"] == (5,)


def test_text_syllable_scheme(sonnet):
    # Shakespeare's sonnets are pentameter → ~10 syllables per line
    combo = sonnet.syllable_scheme["combo"]
    assert combo is not None
    # With canonical (form_idx==0) sylls, sonnet is invariable 10
    assert combo == (10,)


def test_text_rhyme_scheme(sonnet):
    rs = sonnet.rhyme_scheme
    assert rs is not None
    # Best match should be a sonnet form (Shakespearean ideal, but the close
    # variants also score high — accept any sonnet)
    assert "sonnet" in rs["name"].lower() or "rhyme royal" in rs["name"].lower()


def test_text_is_sonnet(sonnet):
    assert sonnet.is_sonnet is True


def test_text_summary(sonnet):
    s = sonnet.summary()
    assert isinstance(s, str)
    assert "estimated schema" in s
    assert "Iambic" in s
    assert "Pentameter" in s


# ----------------------------------------------------------- non-sonnet


def test_non_sonnet_text():
    t = TextModel("The cat\nsat on the mat.\nThe dog\nlay on the log.")
    t.parse()
    assert t.is_sonnet is False
    assert t.is_shakespearean_sonnet is False
    # Has rhymes (mat/cat, dog/log)
    ids = compute_rhyme_ids(t)
    assert len(ids) == 4
    assert any(i > 0 for i in ids)


def test_empty_text_does_not_crash():
    """Edge case: text with no parseable lines."""
    t = TextModel("hello")
    t.parse()
    # These should all return without error
    _ = t.meter_type
    _ = t.line_scheme
    _ = t.syllable_scheme
    _ = t.rhyme_scheme
    _ = t.is_sonnet
