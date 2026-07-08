"""Tests for prosodic/utils.py — the small stateless helpers.

These functions have no linguistic dependencies, so every assertion here is on
an exact, hand-computed output. conftest.py puts the repo root on sys.path.
"""
import json
import os
import tempfile

import pytest

from prosodic.imports import pd, np, logmap, GLOBALS
import prosodic.utils as U


# ---------------------------------------------------------------------------
# retry_on_io_error
# ---------------------------------------------------------------------------

def test_retry_succeeds_after_transient_failures():
    calls = {"n": 0}

    @U.retry_on_io_error(max_attempts=3, delay=0)
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise IOError("transient")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 3  # failed twice, succeeded on the third


def test_retry_reraises_after_exhausting_attempts():
    calls = {"n": 0}

    @U.retry_on_io_error(max_attempts=2, delay=0)
    def always_fails():
        calls["n"] += 1
        raise IOError("permanent")

    with pytest.raises(IOError):
        always_fails()
    assert calls["n"] == 2  # tried exactly max_attempts times


def test_retry_does_not_catch_other_exceptions():
    calls = {"n": 0}

    @U.retry_on_io_error(max_attempts=3, delay=0)
    def value_error():
        calls["n"] += 1
        raise ValueError("nope")

    with pytest.raises(ValueError):
        value_error()
    assert calls["n"] == 1  # non-IOError propagates immediately, no retry


# ---------------------------------------------------------------------------
# group_ents
# ---------------------------------------------------------------------------

class _Ent:
    def __init__(self, g):
        self.g = g


def test_group_ents_groups_consecutive_by_feature():
    a, b = "a", "b"  # shared objects so identity (`is not`) comparison holds
    ents = [_Ent(a), _Ent(a), _Ent(b), _Ent(a)]
    groups = U.group_ents(ents, "g")
    assert [len(g) for g in groups] == [2, 1, 1]
    assert [g[0].g for g in groups] == ["a", "b", "a"]


def test_group_ents_empty_list():
    assert U.group_ents([], "g") == []


# ---------------------------------------------------------------------------
# groupby
# ---------------------------------------------------------------------------

def test_groupby_valid_column():
    df = pd.DataFrame({"k": ["x", "x", "y"], "v": [1, 2, 3]})
    g = U.groupby(df, "k")
    assert sorted(g.groups.keys()) == ["x", "y"]
    assert g.get_group(("x",))["v"].tolist() == [1, 2]


def test_groupby_filters_missing_columns_then_uses_valid_one():
    df = pd.DataFrame({"k": ["x", "y"], "v": [1, 2]})
    # only "k" exists; "missing" is dropped by the in-allcols filter
    g = U.groupby(df, ["missing", "k"])
    assert sorted(g.groups.keys()) == ["x", "y"]


def test_groupby_raises_when_no_valid_columns():
    df = pd.DataFrame({"k": ["x"], "v": [1]})
    with pytest.raises(Exception, match="No group"):
        U.groupby(df, "nonexistent")


# ---------------------------------------------------------------------------
# get_txt
# ---------------------------------------------------------------------------

def test_get_txt_from_string_strips_whitespace():
    assert U.get_txt("  hello world  ", None) == "hello world"


def test_get_txt_from_file_reads_and_strips():
    with tempfile.TemporaryDirectory() as d:
        fn = os.path.join(d, "poem.txt")
        with open(fn, "w", encoding="utf-8") as f:
            f.write("  line one\nline two  ")
        assert U.get_txt(None, fn) == "line one\nline two"


def test_get_txt_empty_when_nothing_given():
    assert U.get_txt(None, None) == ""


def test_get_txt_empty_when_file_missing():
    assert U.get_txt(None, "/no/such/path/xyz.txt") == ""


def test_get_txt_from_url_filename(monkeypatch):
    class FakeResp:
        text = "  fetched body  "

    monkeypatch.setattr(U.requests, "get", lambda url: FakeResp())
    assert U.get_txt(None, "http://example.com/poem") == "fetched body"


def test_get_txt_string_starting_http_recurses_to_fetch(monkeypatch):
    class FakeResp:
        text = "  fetched body  "

    monkeypatch.setattr(U.requests, "get", lambda url: FakeResp())
    # txt that looks like a URL is treated as one (recurses with fn=txt)
    assert U.get_txt("http://example.com/poem", None) == "fetched body"


# ---------------------------------------------------------------------------
# get_attr_str
# ---------------------------------------------------------------------------

def test_get_attr_str_skips_none_values_and_reprs():
    assert U.get_attr_str({"a": 1, "b": None, "c": "x"}) == "a=1, c='x'"


def test_get_attr_str_excludes_bad_keys_and_custom_sep():
    assert U.get_attr_str({"a": 1, "b": 2}, sep="|", bad_keys=["b"]) == "a=1"


# ---------------------------------------------------------------------------
# safesum
# ---------------------------------------------------------------------------

def test_safesum_ignores_non_numeric_values():
    assert U.safesum([1, 2, "x", 3.0, None, np.float64(4.0)]) == 10.0


def test_safesum_empty_is_zero():
    assert U.safesum([]) == 0


# ---------------------------------------------------------------------------
# setindex / niceindex / nicedict
# ---------------------------------------------------------------------------

def test_setindex_sets_index_and_casts_num_columns_to_int():
    df = pd.DataFrame(
        {"line_num": [1.0, 2.0], "line_txt": ["a", "b"], "other": [9, 10]}
    )
    out = U.setindex(df, ["line_num", "line_txt"])
    assert list(out.index.names) == ["line_num", "line_txt"]
    # _num columns are filled and cast to int
    assert list(out.index.get_level_values("line_num")) == [1, 2]
    assert out.index.get_level_values("line_num").dtype.kind == "i"


def test_setindex_empty_cols_returns_input():
    df = pd.DataFrame({"a": [1]})
    assert U.setindex(df, []).equals(df)


def test_setindex_no_matching_cols_returns_unchanged_shape():
    df = pd.DataFrame({"a": [1], "b": [2]})
    out = U.setindex(df, ["zzz"])
    assert out.shape == (1, 2)
    assert list(out.columns) == ["a", "b"]


def test_niceindex_drops_badcols_renames_and_sorts():
    df = pd.DataFrame(
        {
            "wordtoken_line_num": [2, 1],  # renamed to line_num
            "word_num": [9, 9],            # DF_BADCOLS -> dropped
            "syll_num": [1, 1],            # index col
            "is_stressed": [True, False],  # ordinary data col survives
        }
    )
    out = U.niceindex(df)
    assert "word_num" not in out.columns and "word_num" not in out.index.names
    assert list(out.index.names) == ["line_num", "syll_num"]
    assert list(out.columns) == ["is_stressed"]
    # sorted by index -> line_num ascending
    assert list(out.index.get_level_values("line_num")) == [1, 2]


def test_nicedict_orders_index_keys_first_and_drops_badcols():
    out = U.nicedict(
        {"syll_txt": "x", "line_num": 1, "word_txt": "drop", "zzz": 9}
    )
    # word_txt is a DF_BADCOL -> dropped; index keys ordered before extras
    assert list(out.keys()) == ["line_num", "syll_txt", "zzz"]
    assert "word_txt" not in out


# ---------------------------------------------------------------------------
# format_syll_ipa_str / get_syll_ipa_stress
# ---------------------------------------------------------------------------

def test_format_syll_ipa_str_empty():
    assert U.format_syll_ipa_str("") == ""


def test_format_syll_ipa_str_primary_stress_normalized_to_leading_mark():
    # primary "'" wins: strip all marks, prepend a single "'"
    assert U.format_syll_ipa_str("'kat") == "'kat"
    assert U.format_syll_ipa_str("'k`at") == "'kat"


def test_format_syll_ipa_str_secondary_stress():
    assert U.format_syll_ipa_str("`kat") == "`kat"


def test_format_syll_ipa_str_unstressed_passthrough():
    assert U.format_syll_ipa_str("kat") == "kat"


def test_get_syll_ipa_stress_levels():
    assert U.get_syll_ipa_stress("") == ""
    assert U.get_syll_ipa_stress("`ka") == "S"   # secondary mark -> S
    assert U.get_syll_ipa_stress("'ka") == "P"   # primary mark -> P
    assert U.get_syll_ipa_stress("ka") == "U"    # none -> U


# ---------------------------------------------------------------------------
# get_initial_whitespace
# ---------------------------------------------------------------------------

def test_get_initial_whitespace():
    assert U.get_initial_whitespace("  hi") == "  "
    assert U.get_initial_whitespace("hi") == ""
    assert U.get_initial_whitespace("\t\nx") == "\t\n"
    assert U.get_initial_whitespace("") == ""


# ---------------------------------------------------------------------------
# unique / unique_list / is_listlike
# ---------------------------------------------------------------------------

def test_unique_preserves_first_seen_order():
    assert U.unique([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_is_listlike_variants():
    assert U.is_listlike([1, 2]) is True
    assert U.is_listlike((1, 2)) is True          # tuple has __iter__
    assert U.is_listlike({"a": 1}) is True         # dict has __iter__
    assert U.is_listlike("abc") is True            # str has __iter__
    assert U.is_listlike(x for x in range(3)) is True  # generator
    assert U.is_listlike(5) is False               # int is not iterable
    assert U.is_listlike(None) is False


def test_unique_list_dedups_preserving_order():
    assert U.unique_list([1, 1, 2, 3, 2]) == [1, 2, 3]


def test_unique_list_non_listlike_returns_empty(caplog):
    # non-listlike input logs an error and returns []
    assert U.unique_list(5) == []


# ---------------------------------------------------------------------------
# hashstr
# ---------------------------------------------------------------------------

def test_hashstr_is_deterministic():
    assert U.hashstr("a") == U.hashstr("a")
    assert U.hashstr("a") != U.hashstr("b")


def test_hashstr_default_is_full_sha256_hex():
    h = U.hashstr("anything")
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_hashstr_respects_length_argument():
    assert len(U.hashstr("a", length=8)) == 8


# ---------------------------------------------------------------------------
# read_json / from_dict / load
# ---------------------------------------------------------------------------

def test_read_json_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        fn = os.path.join(d, "a.json")
        with open(fn, "w", encoding="utf-8") as f:
            f.write(json.dumps({"k": 1, "nested": [1, 2]}))
        assert U.read_json(fn) == {"k": 1, "nested": [1, 2]}


def test_read_json_missing_file_returns_empty_dict():
    assert U.read_json("/no/such/file.json") == {}


def test_from_dict_raises_without_class_key():
    with pytest.raises(Exception):
        U.from_dict({"no_class_key": 1})


@pytest.fixture
def stub_class():
    """Register a stub class in GLOBALS so from_dict can dispatch to it."""

    class Stub:
        @classmethod
        def from_dict(cls, d, **kw):
            return ("built", d.get("v"), kw.get("extra"))

    GLOBALS["Stub"] = Stub
    try:
        yield Stub
    finally:
        GLOBALS.pop("Stub", None)


def test_from_dict_dispatches_via_globals(stub_class):
    result = U.from_dict({"_class": "Stub", "v": 7}, extra="E")
    assert result == ("built", 7, "E")


def test_load_reads_file_then_dispatches(stub_class):
    with tempfile.TemporaryDirectory() as d:
        fn = os.path.join(d, "obj.json")
        with open(fn, "w", encoding="utf-8") as f:
            f.write(json.dumps({"_class": "Stub", "v": 42}))
        assert U.load(fn) == ("built", 42, None)


# ---------------------------------------------------------------------------
# ensure_dir
# ---------------------------------------------------------------------------

def test_ensure_dir_creates_nested_directories():
    with tempfile.TemporaryDirectory() as d:
        target = os.path.join(d, "sub", "deep", "file.txt")
        U.ensure_dir(target)
        assert os.path.isdir(os.path.join(d, "sub", "deep"))


def test_ensure_dir_bare_filename_is_noop():
    # dirname("file.txt") == "" -> no makedirs, must not raise
    U.ensure_dir("file.txt")


# ---------------------------------------------------------------------------
# to_html
# ---------------------------------------------------------------------------

def test_to_html_string_as_str_returns_string():
    assert U.to_html("<b>hi</b>", as_str=True) == "<b>hi</b>"


def test_to_html_string_renders_ipython_object():
    out = U.to_html("<b>hi</b>", as_str=False)
    # IPython is installed in this env -> returns an HTML display object
    assert type(out).__name__ == "HTML"
    assert out.data == "<b>hi</b>"


def test_to_html_delegates_to_object_method():
    class WithHtml:
        def to_html(self, as_str=False, **kw):
            return "STR" if as_str else "OBJ"

    assert U.to_html(WithHtml(), as_str=True) == "STR"
    assert U.to_html(WithHtml(), as_str=False) == "OBJ"


def test_to_html_unknown_type_logs_and_returns_none():
    assert U.to_html(12345) is None


# ---------------------------------------------------------------------------
# force_int
# ---------------------------------------------------------------------------

def test_force_int_variants():
    assert U.force_int("5") == 5
    assert U.force_int(3.7) == 3
    assert U.force_int("not a number") == 0
    assert U.force_int(None) == 0
    assert U.force_int("bad", errors=-1) == -1


# ---------------------------------------------------------------------------
# tokenize_agnostic
# ---------------------------------------------------------------------------

def test_tokenize_agnostic_keeps_apostrophe_words_and_splits_punct():
    assert U.tokenize_agnostic("don't stop, please") == [
        "don't", " ", "stop", ",", " ", "please"
    ]


def test_tokenize_agnostic_splits_on_hyphen_and_period():
    assert U.tokenize_agnostic("a-b.") == ["a", "-", "b", "."]


# ---------------------------------------------------------------------------
# clean_text
# ---------------------------------------------------------------------------

def test_clean_text_replaces_html_entities():
    assert U.clean_text("Tom &amp; Jerry") == "Tom & Jerry"
    assert U.clean_text("caf&eacute") == "café"
    assert U.clean_text("a&mdash;b") == "a -- b"


def test_clean_text_ftfy_straightens_curly_quotes():
    # ftfy.fix_text uncurls quotes to ASCII
    assert U.clean_text("don’t") == "don't"
    assert U.clean_text("“x”") == '"x"'


def test_clean_text_normalizes_newlines():
    assert U.clean_text("a\r\nb\rc") == "a\nb\nc"


# ---------------------------------------------------------------------------
# eprint
# ---------------------------------------------------------------------------

def test_eprint_writes_to_stderr(capsys):
    U.eprint("hello", "there")
    captured = capsys.readouterr()
    assert captured.err == "hello there\n"
    assert captured.out == ""


# ---------------------------------------------------------------------------
# caching / logging no-op flags and context managers
# ---------------------------------------------------------------------------

def test_caching_is_always_disabled():
    assert U.caching_is_enabled() is False
    # the enable/disable functions are no-ops that must not raise
    U.enable_caching()
    U.disable_caching()
    assert U.caching_is_enabled() is False


def test_caching_context_managers_are_noops():
    with U.caching_enabled():
        assert U.caching_is_enabled() is False
    with U.caching_disabled():
        assert U.caching_is_enabled() is False
    # still disabled afterwards
    assert U.caching_is_enabled() is False


def test_logging_disabled_toggles_and_restores():
    before = logmap.is_quiet
    with U.logging_disabled():
        assert logmap.is_quiet is True
    assert logmap.is_quiet == before


def test_logging_enabled_toggles_and_restores():
    before = logmap.is_quiet
    with U.logging_enabled():
        assert logmap.is_quiet is False
    assert logmap.is_quiet == before
