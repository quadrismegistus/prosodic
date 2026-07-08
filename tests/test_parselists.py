"""Tests for prosodic/parsing/parselists.py — the ParseList and ParseListList
containers.

These exercise the *realized* ParseList path (real Parse entities with a
parent chain, so parse.line / parse.sent / parse.stanza resolve), reached via
`line.parse().unbounded` / `.bounded` / `.scansions` / `.best_parses` (each of
which returns a real ParseList) and via ParseList.from_combinations. This is the
container layer that the web/HTML path and the analysis summaries build on, so
the assertions target observable structure (partition complements, dedup,
ranking, stats columns, HTML) rather than internal state.
"""
import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
from prosodic.parsing.parselists import ParseList, ParseListList
from prosodic.parsing.parses import Parse

disable_caching()

TWO_LINES = ("Shall I compare thee to a summers day\n"
             "When forty winters shall besiege thy brow")
HORSE = "a horse a horse my kingdom for a horse"


def _line_parses(txt="Shall I compare thee to a summers day"):
    """A parsed single line -> its LazyParseList (line._parses is set, so
    downstream ParseList.to_html can re-render each line)."""
    return TextModel(txt).line1.parse()


def _entity_pll(txt=TWO_LINES):
    """A ParseListList of entity-path parses (real .line/.sent/.stanza), built
    the way TextModel would if combining — one LazyParseList per line."""
    t = TextModel(txt)
    return ParseListList([ln.parse() for ln in t.lines], parent=t)


# ---------------------------------------------------------------------------
# ParseList
# ---------------------------------------------------------------------------

def test_append_rejects_non_parse():
    # ParseList only holds Parse objects; ParseListList only holds parse lists.
    with pytest.raises(ValueError):
        ParseList([]).append("not a parse")
    with pytest.raises(ValueError):
        ParseListList([]).append("not a parse list")
    # a real Parse appends fine
    pl = ParseList([])
    pl.append(Parse(HORSE, "ws" * 5))
    assert len(pl) == 1


def test_key_is_cached():
    # .key builds "<parent.key>.<TypeName>.<meter.key>" once, then returns the
    # memoized string on the second access (identity, not just equality).
    ub = _line_parses().unbounded
    k1 = ub.key
    k2 = ub.key
    assert k1 is k2
    assert "ParseList" in k1 and "Meter(" in k1

    pll = _entity_pll()
    pk1 = pll.key
    assert pk1 is pll.key
    assert "ParseListList" in pk1 and "Meter(" in pk1


def test_meter_and_empty_fallback():
    # a populated ParseList reports the meter of its parses...
    ub = _line_parses().unbounded
    m = ub.meter
    assert m is not None and m.__class__.__name__ == "Meter"
    # ...and an empty one has no parse and no line, so .meter is None (falls
    # through the parse loop and the `if self.line` guard without raising).
    empty = ParseList([])
    assert empty.meter is None
    assert empty.line is None
    assert empty.best_parse is None


def test_all_and_best_are_aliases():
    # .all == .scansions (every distinct candidate), .best == .best_parses.
    lp = _line_parses()
    ub = lp.unbounded
    assert list(ub.all) == list(ub.scansions)
    assert list(ub.best) == list(ub.best_parses)
    # best_parses is exactly the rank-1 scansions
    assert all(p.parse_rank == 1 for p in ub.best_parses)


def test_unbounded_bounded_partition():
    # scansions = unbounded ⊎ bounded, disjoint by is_bounded, and .bounded
    # carries show_bounded=True so its df/render actually render.
    lp = _line_parses("A horse, a horse, my kingdom for a horse!")
    scans = lp.scansions
    unb, bnd = lp.unbounded, lp.bounded
    assert unb.num_unbounded + bnd.num_bounded == scans.num_all
    assert all(not p.is_bounded for p in unb)
    assert all(p.is_bounded for p in bnd)
    assert bnd.show_bounded is True
    # unbounded parses are sorted best-first by score
    scores = [p.score for p in unb]
    assert scores == sorted(scores)
    if len(bnd):
        assert len(bnd.get_df()) > 0        # show_bounded flag lets df populate


def test_best_parse_reports_cooptimal():
    # best_parse = min score; num_cooptimal counts DISTINCT best meter strings
    # among the unbounded parses tying at that score; is_tied iff > 1.
    for txt in ("Shall I compare thee to a summers day",
                "Were an all-eating shame and thriftless praise"):
        pl = _line_parses(txt).unbounded
        bp = pl.best_parse
        assert bp is not None
        indep = len({p.meter_str for p in pl.data
                     if not p.is_bounded and abs(p.score - bp.score) < 1e-9})
        assert bp.num_cooptimal == indep >= 1
        assert bp.is_tied == (bp.num_cooptimal > 1)
    # best_parse over a mixed (bounded+unbounded) scansion list still selects an
    # unbounded winner and its cooptimal count stays >= 1
    sc = _line_parses().scansions
    assert sc.best_parse.num_cooptimal >= 1


def test_count_properties():
    ub = _line_parses().unbounded
    assert ub.num_unbounded == len(ub.unbounded) == ub.num_parses
    assert ub.num_bounded == len(ub.bounded)
    assert ub.num_all == len(ub.scansions)
    assert ub.num_all_with_combos == len(ub.data)
    # scansions dedup by meter string, so num_all never exceeds the raw combo count
    assert 0 < ub.num_all <= ub.num_all_with_combos
    assert ub.parses is ub                   # .parses returns self


def test_line_lines_num_lines():
    # entity parses expose their Line; the ParseList aggregates unique lines.
    pll_lines = _entity_pll().scansions
    assert pll_lines.line is not None
    assert pll_lines.num_lines == len(pll_lines.lines) == 2
    # a single-line ParseList reports one line
    one = _line_parses().unbounded
    assert one.num_lines == 1
    assert one.line.txt.startswith("Shall")


def test_bound_marks_dominated_and_ranks():
    # Harmonic bounding on a hand-built list: iambic "ws"*5 dominates trochaic
    # "sw"*5 for "a horse a horse ...". Ordering [sw, ws] makes the FIRST parse
    # get bounded by a later one (the `Bounding.bounded` branch).
    pl = ParseList([Parse(HORSE, "sw" * 5), Parse(HORSE, "ws" * 5)])
    unbounded = pl.bound(progress=False)
    by_meter = {p.meter_str: p for p in pl.data}
    assert by_meter["+-+-+-+-+-"].is_bounded is True          # trochaic bounded
    assert by_meter["+-+-+-+-+-"].bounded_by                   # records the bounder
    assert by_meter["-+-+-+-+-+"].is_bounded is False          # iambic survives
    assert list(unbounded) == [by_meter["-+-+-+-+-+"]]

    # rank() sorts in place and assigns 1..n parse_rank
    pl.rank()
    assert [p.parse_rank for p in pl.data] == [1, 2]
    assert pl.data[0].score <= pl.data[1].score

    # can_compare guard: parses of different syllable counts are never compared,
    # so neither is bounded (covers the `continue` skip in bound()).
    mixed = ParseList([Parse("a horse", "ws"), Parse(HORSE, "ws" * 5)])
    mixed.bound(progress=False)
    assert all(not p.is_bounded for p in mixed.data)

    # cascade ordering [ws, ww, sw]: the FIRST parse bounds a LATER one (the
    # `Bounding.bounds` branch), then the now-bounded parse is skipped both as
    # an outer item and as an inner comparison target.
    casc = ParseList([Parse(HORSE, "ws" * 5), Parse(HORSE, "ww" * 5),
                      Parse(HORSE, "sw" * 5)])
    casc.bound(progress=False)
    d = {p.meter_str: p for p in casc.data}
    assert d["+-+-+-+-+-"].is_bounded and d["+-+-+-+-+-"].bounded_by  # bounded by ws
    assert not d["-+-+-+-+-+"].is_bounded                              # iambic survives


def test_from_combinations_builds_ranked_bounded_list():
    # from_combinations takes the cartesian product of per-unit parse lists,
    # concatenates each combo into one Parse, then bounds + ranks. With a single
    # line's parselist and that Line as parent, each combo is one whole-line
    # parse.
    line1 = TextModel("Shall I compare thee to a summers day").line1
    pl1 = line1.parse().unbounded
    combo = ParseList.from_combinations([pl1], parent=line1)
    assert combo.parent is line1
    assert len(combo) == len(pl1)
    assert combo.best_parse.meter_str == "-+-+-+-+-+"
    # ranked contiguously from 1
    assert sorted(p.parse_rank for p in combo.data) == list(range(1, len(combo) + 1))


def test_get_groupby():
    # _get_groupby maps a `by` scope to the DataFrame grouping columns.
    ub = _line_parses().unbounded
    assert ub._get_groupby(None) == []               # default "parse" -> no grouping
    assert ub._get_groupby("stanza") == ["stanza_num"]
    assert ub._get_groupby("line") == ["stanza_num", "line_num", "line_txt"]
    assert ub._get_groupby("bogus") == []            # unknown scope -> no grouping


def test_stats_norm_and_raw():
    ub = _line_parses().unbounded
    df_norm = ub.df_norm
    df_raw = ub.df_raw
    # one row per unbounded parse in both
    assert len(df_norm) == len(df_raw) == ub.num_unbounded
    # constraint columns are prefixed and present
    assert any(c.startswith("*") for c in df_raw.columns)
    # raw and normalized totals differ (norm averages per-syllable)
    assert "*total" in df_raw.columns
    # stats_d aggregates each numeric stat to a single float; norm vs raw share
    # keys but differ in values.
    d_raw = ub.stats_d(norm=False)
    d_norm = ub.stats_d(norm=True)
    assert isinstance(d_raw, dict)
    assert isinstance(d_raw["*total"], float)
    assert set(d_raw) == set(d_norm)
    assert set(d_raw.values()) != set(d_norm.values())


def test_dataframe_surfaces():
    # the DataFrame accessors on a ParseList: .df (one row per unbounded parse),
    # .df_syll / stats(by="syll") (one row per syllable slot), and the HTML repr.
    ub = _line_parses().unbounded
    assert len(ub.df) == ub.num_unbounded
    syll = ub.df_syll
    assert len(syll) == len(ub.stats(by="syll")) > ub.num_unbounded  # per-syllable
    assert "</table>" in ub._repr_html_()


def test_render_and_to_html():
    # render() delegates to to_html(); the HTML wraps each line in <ol
    # class="parselist">. Requires line._parses (set by line.parse()).
    ub = _line_parses().unbounded
    html = ub.render(as_str=True)
    assert '<ol class="parselist">' in html
    assert "<li>" in html
    # to_html directly, and over a multi-line list -> one <li> per line
    multi = _entity_pll().scansions
    multi_html = multi.to_html(as_str=True)
    assert multi_html.count("<li>") >= 2


def test_empty_parselist_is_safe():
    empty = ParseList([])
    assert empty.best_parse is None
    assert empty.num_all == 0
    assert empty.num_unbounded == 0
    assert empty.get_df().empty
    assert len(empty.lines) == 0
    assert empty.num_lines == 0


# ---------------------------------------------------------------------------
# ParseListList
# ---------------------------------------------------------------------------

def test_parselistlist_entity_groupings():
    # Over entity parses, the *List aggregators return the unique prosodic units
    # spanning the two lines: one sentence / stanza / sentpart, two lineparts.
    pll = _entity_pll()
    assert pll.num_sents == len(pll.sents) == 1
    assert pll.num_stanzas == len(pll.stanzas) == 1
    assert pll.num_sentparts == len(pll.sentparts) == 1
    assert pll.num_lineparts == len(pll.lineparts) == 2
    # scansions flattens every unit's scansions into one ParseList
    scans = pll.scansions
    assert scans.__class__.__name__ == "ParseList"
    assert len(scans) == sum(len(pl.scansions) for pl in pll)
    assert scans.is_scansions and scans.show_bounded


def test_parselistlist_num_lines_entity_and_df_fallback():
    # entity path: real lines -> normal count
    assert _entity_pll().num_lines == 2
    # DF path (text.parse): parses carry no .line, so .lines is empty and
    # num_lines falls back to the number of parse units.
    df_pll = TextModel(TWO_LINES).parse()
    assert df_pll.__class__.__name__ == "ParseListList"
    assert len(df_pll.lines) == 0
    assert df_pll.num_lines == len(df_pll) == 2


def test_parselistlist_get_df_and_stats():
    pll = _entity_pll()
    df = pll.get_df()
    assert not df.empty
    # stats() with no `by` falls back to the list's scope ("line") and dedups to
    # one row per line.
    s = pll.stats()
    assert len(s) == 2
    # a `by` whose *_num column isn't in the per-parse stats logs an error but
    # still returns a (non-deduped) frame rather than raising.
    s_para = pll.stats(by="para")
    assert isinstance(s_para, pd.DataFrame) and not s_para.empty
    # an empty list yields an empty frame
    assert ParseListList([], parent=pll.parent).stats().empty


def test_parselistlist_bounded_unbounded_best():
    pll = _entity_pll()
    assert pll.unbounded.__class__.__name__ == "ParseListList"
    assert pll.bounded.__class__.__name__ == "ParseListList"
    # best / best_parses collapse to one best Parse per line
    best = pll.best_parses
    assert best.__class__.__name__ == "ParseList"
    assert len(best) == 2
    assert list(pll.best) == list(best)
    assert all(bp is not None for bp in best)


def test_parselistlist_render_and_html():
    pll = _entity_pll()
    html = pll.to_html(as_str=True)
    assert '<ol class="parselist">' in html
    assert html.count("<li>") >= 2
    assert '<ol class="parselist">' in pll.render(as_str=True)
