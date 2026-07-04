import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
import tempfile
import pytest

disable_caching()


def test_Text():
    x = "Hello world!?!?!?!? !? ?!? –––_  -—- — “‘‘’ ewr ewr ’"
    t = TextModel(x, init=False)
    print([t._txt, t.txt])
    assert t._txt == clean_text(x)
    assert t.txt == clean_text(x)

    y = "This is a reasonably sized english text"
    assert TextModel(y, lang=None, init=False).lang == "en"

    y = "Dieser Text ist nicht so klug"
    assert TextModel(y, lang=None, init=False).lang == "de"
    assert TextModel(y, init=False).lang == DEFAULT_LANG

    with tempfile.TemporaryDirectory() as tdir:
        oline = "A slumber did my spirit seal"
        fn = os.path.join(tdir, "test.txt")
        with open(fn, "w", encoding='utf-8') as of:
            of.write(oline)
        assert TextModel(fn=fn)._txt == oline

    with pytest.raises(ValueError):
        TextModel()

    t = TextModel("    ererer e   e  ")
    assert t.txt == "ererer e   e"
    assert len(t.wordtokens) == 3
    assert t.attrs


LINE = "From fairest creatures we desire increase"


def test_empty_text_raises():
    # T10: whitespace-only / empty text should raise a clear ValueError,
    # not build a (0, 0) frame that later crashes in .save().
    for bad in ("   ", "\t\n ", "", "     "):
        with pytest.raises(ValueError):
            TextModel(bad)


def test_text_factory_syntax_kwarg():
    # T17: the documented Text() factory must accept syntax= without TypeError.
    from prosodic.texts.texts import Text
    t = Text(LINE, syntax=False)
    assert isinstance(t, TextModel)
    assert t._syntax is False
    # syntax_model also passes through
    t2 = Text(LINE, syntax=False, syntax_model="en_core_web_sm")
    assert t2._syntax_model == "en_core_web_sm"


def test_hash_cached():
    # T16: .hash should be cached (cached_property), not recomputed every call.
    from functools import cached_property
    assert isinstance(TextModel.__dict__["hash"], cached_property)
    t = TextModel(LINE)
    h = t.hash
    assert "hash" in t.__dict__ and t.__dict__["hash"] == h
    assert t.hash == h


def test_get_parses_df_correct_meter():
    # T3: get_parses_df(**kwargs) must return the meter implied by kwargs,
    # not simply the most-recently-parsed meter.
    t = TextModel(LINE)
    b1 = len(t.get_parses_df(mode="all", max_w=1))   # strict meter B
    a1 = len(t.get_parses_df(mode="all", max_w=2))   # default-ish meter A
    assert b1 != a1, "meters should produce different parse spaces"
    # A is now the most-recently-inserted key; querying B by kwargs must
    # still return B's results, not A's.
    b2 = len(t.get_parses_df(mode="all", max_w=1))
    assert b2 == b1


def test_load_lineparts_roundtrip():
    # T5: TextModel.load(path).lineparts must work (previously RecursionError
    # because _linepart_parse_results / _syntax / _syntax_model were unset).
    t = TextModel(LINE + "\nWhen forty winters shall besiege thy brow")
    t.parse()
    with tempfile.TemporaryDirectory() as d:
        path = t.save(d)
        loaded = TextModel.load(path)
        assert loaded._linepart_parse_results == {}
        assert loaded._syntax is DEFAULT_SYNTAX
        assert isinstance(loaded._syntax_model, str)
        lineparts = loaded.lineparts  # must not raise
        assert len(lineparts) >= 1


def test_parse_attaches_after_lines():
    # T7: parse results must attach to Line entities even when .lines was
    # accessed before parse() ran.
    t = TextModel(LINE)
    _ = t.lines            # build lines first
    t.parse()              # then parse (DF path)
    assert t.lines[0]._parses is not None
    assert t.lines[0].best_parse is not None
    # pre-access path (parse before lines) still works
    t2 = TextModel(LINE)
    t2.parse()
    assert t2.lines[0]._parses is not None
