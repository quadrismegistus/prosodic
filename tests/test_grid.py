import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from prosodic.imports import *
from prosodic.analysis import grid_data, grid_df, grid_str

disable_caching()

LINE = "When in the chronicle of wasted time"


@pytest.fixture(scope="module")
def parsed_line():
    t = TextModel(LINE)
    t.parse()
    return t.lines[0]


def test_grid_data_rows(parsed_line):
    rows = grid_data(parsed_line.best_parse)
    assert len(rows) == 10  # pentameter line
    assert [r["meter"] for r in rows] == list("wswswswsws")
    # primary-stressed syllables get full-height columns
    by_txt = {r["txt"]: r for r in rows}
    assert by_txt["IN"]["height"] == 3
    assert by_txt["when"]["height"] == 1
    # the s_unstress violation on "CLE" is flagged on its position
    assert by_txt["CLE"]["viol"] is True


def test_grid_str_shape(parsed_line):
    s = parsed_line.grid_str()
    lines = s.split("\n")
    # marks rows + syllable text row + meter row
    assert lines[-2].split() == ["when", "IN", "the", "CHRO", "ni", "CLE", "of", "WA", "sted", "TIME"]
    meter_row = lines[-1].split()
    assert meter_row[0] == "w" and meter_row[1] == "s"
    assert "s*" in meter_row  # violation marker
    # bottom marks row has one mark per syllable
    assert lines[-3].count("*") == 10


def test_grid_str_no_viols_flag(parsed_line):
    s = parsed_line.grid_str(viols=False)
    assert "s*" not in s.split("\n")[-1]


def test_grid_df(parsed_line):
    df = parsed_line.grid_df()
    assert list(df.columns) == ["txt", "stress", "meter", "height", "phrasal", "viol"]
    assert len(df) == 10
    assert df["height"].between(1, 3).all()


def test_grid_entity_path_matches_df_path(parsed_line):
    from prosodic.parsing.meter import Meter
    from prosodic.parsing.vectorized import parse_batch

    t2 = TextModel(LINE)
    parse_batch(t2.lines, Meter())
    assert t2.lines[0].best_parse.grid_str() == parsed_line.grid_str()


def test_grid_plot(parsed_line):
    plotnine = pytest.importorskip("plotnine")
    p = parsed_line.grid_plot()
    assert isinstance(p, plotnine.ggplot)
