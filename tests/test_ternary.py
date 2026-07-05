"""Ternary (anapestic/dactylic) meter: representability, detection, MaxEnt fit.

Test corpus: Byron's "The Destruction of Sennacherib" (1815), canonical
anapestic tetrameter. Regular lines scan wws wws wws wws ("wwswwswwswws",
12 sylls); iamb-initial variant lines scan ws wws wws wws ("wswwswwswws",
11 sylls). Hand-verified expectations below follow the canonical scansion.
"""
import warnings

warnings.filterwarnings("ignore")

import os

import pytest

from prosodic.imports import *
from prosodic.parsing.utils import get_possible_scansions

CORPORA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "corpora", "corppoetry_en",
)
BYRON_PATH = os.path.join(CORPORA, "en.byron.sennacherib.txt")
BROWNING_PATH = os.path.join(CORPORA, "en.browning.goodnews.txt")

# regular 12-syll line + iamb-initial 11-syll variant
TERNARY_TARGETS = ["wwswwswwswws", "wswwswwswws"]


@pytest.fixture(scope="module")
def byron_txt():
    with open(BYRON_PATH) as f:
        return f.read()


@pytest.fixture(scope="module")
def byron_parsed(byron_txt):
    t = TextModel(byron_txt)
    t.parse()
    return t


def _meter_strs(text):
    """Best-parse scansions as w/s strings, one per line."""
    out = []
    for line in text.lines:
        bp = line.best_parse
        out.append(
            "".join("s" if ch == "+" else "w" for ch in bp.meter_str)
            if bp else ""
        )
    return out


def test_ternary_scansions_representable():
    # anapestic tetrameter fits within the default position inventory
    # (max_w=2: each wws foot = one ww position + one s position)
    for target in TERNARY_TARGETS:
        scansions = get_possible_scansions(len(target))
        joined = {"".join(scan) for scan in scansions}
        assert target in joined


def test_byron_meter_type_is_anapestic(byron_parsed):
    mt = byron_parsed.meter_type
    assert mt["foot"] == "ternary"
    assert mt["head"] == "final"
    assert mt["type"] == "anapestic"


def test_byron_regular_lines_scan_anapestic(byron_parsed):
    # hand-verified pure-anapestic lines with unambiguous lexical stress;
    # the default weights alone should find wws wws wws wws
    expected = {
        "And his cohorts were gleaming in purple and gold": "wwswwswwswws",
        "And the sheen of their spears was like stars on the sea": "wwswwswwswws",
        "And the widows of Ashur are loud in their wail": "wwswwswwswws",
    }
    by_txt = {
        line.txt.strip().rstrip(",;:.!?"): ms
        for line, ms in zip(byron_parsed.lines, _meter_strs(byron_parsed))
    }
    for txt, target in expected.items():
        assert by_txt[txt] == target, f"{txt!r} scanned {by_txt[txt]!r}"


def test_browning_meter_type_is_anapestic():
    # second poem, much rougher (heavy substitution): detection should
    # still land on anapestic
    with open(BROWNING_PATH) as f:
        t = TextModel(f.read())
    t.parse()
    mt = t.meter_type
    assert mt["foot"] == "ternary"
    assert mt["type"] == "anapestic"


def test_load_text_accepts_target_list(byron_txt):
    from prosodic.parsing.maxent import MaxEntTrainer

    # single uniform target only matches the 12-syll lines
    tr1 = MaxEntTrainer(Meter(), zones=None)
    tr1.load_text(byron_txt, TERNARY_TARGETS[0])
    matched1 = sum(1 for ld in tr1._line_data if ld["observed"].sum() > 0)

    # target list matches 11-syll iamb-initial lines too
    tr2 = MaxEntTrainer(Meter(), zones=None)
    tr2.load_text(byron_txt, TERNARY_TARGETS)
    matched2 = sum(1 for ld in tr2._line_data if ld["observed"].sum() > 0)

    assert matched2 > matched1
    assert matched2 >= 18  # 22/24 on CMU; leave slack for TTS variation


def test_fit_ternary_learns_strict_strong_positions(byron_txt):
    # the ternary signature (Hanson & Kiparsky): strong positions must be
    # stressed (s_unstress strict) while stressed monosyllables sit freely
    # in weak positions (w_stress ~free)
    meter = Meter()
    meter.fit(byron_txt, TERNARY_TARGETS, zones=None, regularization=10.0)
    w = meter.zone_weights
    assert w["s_unstress"] > 1.0
    assert w["s_unstress"] > w["w_stress"]
    assert w["w_stress"] < 0.5


def test_fit_zones_none_weights_are_used(byron_txt):
    # regression: fit(zones=None) stored weights but LazyParseList only
    # honored them when zones was non-None, silently scoring with defaults
    from prosodic.parsing.vectorized import parse_batch_from_df

    meter = Meter()
    meter.fit(byron_txt, TERNARY_TARGETS, zones=None, regularization=10.0)
    results = parse_batch_from_df(TextModel(byron_txt)._syll_df, meter)
    lpl = next(iter(results.values()))
    assert lpl._is_zone_scored


def test_fit_ternary_improves_target_agreement(byron_txt):
    t0 = TextModel(byron_txt)
    t0.parse()
    hits_default = sum(1 for ms in _meter_strs(t0) if ms in TERNARY_TARGETS)

    meter = Meter()
    meter.fit(byron_txt, TERNARY_TARGETS, zones=3, regularization=10.0)
    t1 = TextModel(byron_txt)
    t1.parse(meter=meter)
    hits_fit = sum(1 for ms in _meter_strs(t1) if ms in TERNARY_TARGETS)

    assert hits_fit >= hits_default
    assert hits_fit >= 12  # 15/24 on CMU; leave slack for TTS variation
