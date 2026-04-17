"""Tests for prosodic.client remote API.

Uses FastAPI TestClient — no running server or network needed.
Works on GitHub Actions with just espeak installed.
"""
import pytest
from fastapi.testclient import TestClient
from prosodic.web.api import app
from prosodic.client import (
    RemoteText, RemoteLine, RemoteParse, RemoteParseList,
    set_server, get_server,
)

SONNET_LINE = "From fairest creatures we desire increase"
SONNET_2LINES = """From fairest creatures we desire increase,
That thereby beauty's rose might never die"""


@pytest.fixture(scope="module")
def api():
    """FastAPI TestClient — same as test_web.py but shared across tests."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_server():
    """Reset global server between tests."""
    set_server(None)
    yield
    set_server(None)


# --- set_server / get_server ---

def test_set_server_string():
    set_server("https://prosodic.app")
    assert get_server() == "https://prosodic.app"


def test_set_server_strips_trailing_slash():
    set_server("https://prosodic.app/")
    assert get_server() == "https://prosodic.app"


def test_set_server_none():
    set_server("https://prosodic.app")
    set_server(None)
    assert get_server() is None


def test_set_server_test_client(api):
    set_server(api)
    assert get_server() is api


# --- RemoteText construction ---

def test_remote_text_no_server():
    with pytest.raises(RuntimeError, match="No server configured"):
        RemoteText("hello")


def test_remote_text_explicit_server(api):
    t = RemoteText(SONNET_LINE, server=api)
    assert t.txt == SONNET_LINE


def test_remote_text_global_server(api):
    set_server(api)
    t = RemoteText(SONNET_LINE)
    assert t.txt == SONNET_LINE


def test_remote_text_lines(api):
    t = RemoteText(SONNET_2LINES, server=api)
    assert len(t.lines) == 2
    assert t.lines[0].txt == "From fairest creatures we desire increase,"
    assert t.lines[1].num == 2


# --- Parsing ---

def test_parse_single_line(api):
    t = RemoteText(SONNET_LINE, server=api)
    t.parse()
    assert t.parsed
    assert len(t.lines) == 1
    line = t.lines[0]
    assert line._parses is not None
    assert line.best_parse is not None
    assert isinstance(line.best_parse, RemoteParse)
    assert line.best_parse.meter_str  # non-empty
    assert isinstance(line.best_parse.score, float)


def test_parse_multi_line(api):
    t = RemoteText(SONNET_2LINES, server=api)
    t.parse()
    assert len(t.lines) == 2
    for line in t.lines:
        assert line.best_parse is not None
        assert line.best_parse.meter_str


def test_parse_best_parses(api):
    t = RemoteText(SONNET_2LINES, server=api)
    bps = t.best_parses  # triggers parse
    assert len(bps) == 2
    assert all(isinstance(p, RemoteParse) for p in bps)


def test_parse_returns_self(api):
    t = RemoteText(SONNET_LINE, server=api)
    result = t.parse()
    assert result is t


def test_parse_render(api):
    t = RemoteText(SONNET_LINE, server=api)
    html = t.render()
    assert '<span' in html


# --- Line-level parsing (all scansions) ---

def test_line_parse_all_scansions(api):
    t = RemoteText(SONNET_LINE, server=api)
    t.parse()
    line = t.lines[0]
    pl = line.parse()
    assert isinstance(pl, RemoteParseList)
    assert pl.num_unbounded >= 1
    assert len(pl) > pl.num_unbounded  # should have bounded parses too
    assert pl.best_parse.score <= min(p.score for p in pl.bounded)


def test_line_parse_bounded_flag(api):
    t = RemoteText(SONNET_LINE, server=api)
    t.parse()
    line = t.lines[0]
    line.parse()
    for p in line.parses.unbounded:
        assert not p.is_bounded
    for p in line.parses.bounded:
        assert p.is_bounded


def test_line_parse_positions(api):
    """Line parse returns position/slot details."""
    t = RemoteText(SONNET_LINE, server=api)
    t.parse()
    line = t.lines[0]
    line.parse()
    bp = line.best_parse
    assert len(bp.positions) > 0
    for pos in bp.positions:
        assert pos.mtr in ('s', 'w')
        assert len(pos.slots) > 0
        for slot in pos.slots:
            assert slot.txt  # non-empty syllable text


def test_line_parse_viol_summary(api):
    """Bounded parses should have violations."""
    t = RemoteText(SONNET_LINE, server=api)
    t.parse()
    line = t.lines[0]
    line.parse()
    # At least some bounded parses should have violations
    bounded_with_viols = [p for p in line.parses.bounded if p.viol_summary]
    assert len(bounded_with_viols) > 0


def test_parse_lines(api):
    """parse_lines() fetches all scansions for every line."""
    t = RemoteText(SONNET_2LINES, server=api)
    t.parse_lines()
    assert t.parsed
    for line in t.lines:
        assert line.parses is not None
        assert len(line.parses) > 1  # should have bounded parses


# --- MaxEnt ---

def test_maxent_fit(api):
    t = RemoteText(SONNET_2LINES, server=api)
    result = t.fit(target_scansion='wswswswsws', zones=3)
    assert result.weights  # non-empty dict
    assert result.accuracy >= 0
    assert result.num_lines > 0
    assert result.elapsed > 0


# --- Meter defaults ---

def test_meter_defaults(api):
    t = RemoteText(SONNET_LINE, server=api)
    data = t.meter_defaults()
    assert 'all_constraints' in data
    assert 'w_stress' in data['all_constraints']
    assert 'defaults' in data


# --- Parse ordering ---

def test_parse_sorted_by_score(api):
    t = RemoteText(SONNET_LINE, server=api)
    t.parse()
    line = t.lines[0]
    line.parse()
    scores = [p.score for p in line.parses]
    assert scores == sorted(scores)


def test_parse_comparison(api):
    """RemoteParse supports < comparison."""
    p1 = RemoteParse({'score': 1.0, 'meter_str': 'a'})
    p2 = RemoteParse({'score': 2.0, 'meter_str': 'b'})
    assert p1 < p2
    assert min(p1, p2) is p1


# --- Interface parity with local prosodic ---

def test_text_factory_uses_server(api):
    """prosodic.Text() should return RemoteText when server is set."""
    set_server(api)
    from prosodic.texts.texts import Text
    t = Text(SONNET_LINE)
    assert isinstance(t, RemoteText)


# --- Save / Load ---

def test_save_load_roundtrip(api, tmp_path):
    t = RemoteText(SONNET_2LINES, server=api)
    t.parse()
    save_dir = str(tmp_path / "saved")
    t.save(save_dir)

    # Load without server
    t2 = RemoteText.load(save_dir)
    assert t2.parsed
    assert len(t2.lines) == 2
    assert t2.lines[0].txt == t.lines[0].txt
    assert t2.lines[0].best_parse.meter_str == t.lines[0].best_parse.meter_str
    assert t2.lines[0].best_parse.score == t.lines[0].best_parse.score


def test_save_load_with_line_parses(api, tmp_path):
    t = RemoteText(SONNET_LINE, server=api)
    t.parse_lines()
    save_dir = str(tmp_path / "saved_detail")
    t.save(save_dir)

    t2 = RemoteText.load(save_dir)
    assert len(t2.lines[0].parses) > 1
    assert any(p.is_bounded for p in t2.lines[0].parses)


def test_save_creates_parquet(api, tmp_path):
    """If pandas is available, save also writes parsed.parquet."""
    import os
    t = RemoteText(SONNET_LINE, server=api)
    t.parse_lines()  # need positions for parquet
    save_dir = str(tmp_path / "saved_pq")
    t.save(save_dir)
    assert os.path.exists(os.path.join(save_dir, 'parsed.parquet'))

    import pandas as pd
    df = pd.read_parquet(os.path.join(save_dir, 'parsed.parquet'))
    assert 'meter_val' in df.columns
    assert 'syll_txt' in df.columns
    assert len(df) > 0


def test_load_no_server_needed(api, tmp_path):
    """Loaded RemoteText works without a server for accessing cached results."""
    t = RemoteText(SONNET_LINE, server=api)
    t.parse()
    t.save(str(tmp_path / "s"))
    t2 = RemoteText.load(str(tmp_path / "s"))
    # Can access everything without a server
    assert t2.lines[0].best_parse is not None
    assert t2.render()


def test_text_factory_local_without_server():
    """prosodic.Text() should return TextModel when no server is set."""
    from prosodic.texts.texts import Text, TextModel
    t = Text(SONNET_LINE)
    assert isinstance(t, TextModel)
