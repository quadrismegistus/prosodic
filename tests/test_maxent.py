"""Tests for prosodic.parsing.maxent — MaxEnt constraint weight learning.

Targets the module's public surface and the previously-uncovered branches:
the zone helpers ("initial" / "foot" / int N / invalid), the foot-zone
padding path in _build_line_data, load_annotations (list / DataFrame /
pre-built-TextModel), the train() no-data guard, predict() / report() /
apply_to_meter(), mixed-N (ragged) line training +
warning.

Kept fast by training on 1-2 short lines with light regularization; the
optimizer converges in well under a second on inputs this size.
"""
import warnings

# Pre-import torch (if installed) before prosodic so that, under `pytest --cov`,
# torch's C docstrings register exactly once (importing prosodic while coverage's
# tracer is active otherwise raises "function '_has_torch_function' already has a
# docstring" at collection). torch is optional (GPU-only) and absent on e.g.
# Windows CI, so guard it — the tests themselves don't require torch.
try:
    import torch  # noqa: F401
except ModuleNotFoundError:
    pass

import numpy as np
import pandas as pd
import pytest

warnings.filterwarnings("ignore")

from prosodic.imports import *  # noqa: F401,F403  (TextModel, sonnet, ...)
from prosodic.parsing.meter import Meter
from prosodic.parsing.maxent import (
    MaxEntTrainer,
    make_zone_names,
    zone_boundaries,
    zone_split,
)
import prosodic.parsing.maxent as maxent_mod

IAMBIC = "wswswswsws"
LINE1 = "Shall I compare thee to a summers day"           # clean iambic pentameter
LINE2 = "Rough winds do shake the darling buds of May"    # 10 sylls
SHORT = "Rough winds do shake the buds"                   # ~6 sylls: fewer feet
RAGGED = "A flower and a fire and a tower"                # mixed-N pool -> ragged


# ---------------------------------------------------------------------------
# Zone helpers (pure functions) — exact boundary/name/shape contracts
# ---------------------------------------------------------------------------

def test_zone_boundaries_initial():
    # "initial" = first 2 syllables vs the rest.
    assert zone_boundaries("initial", 10) == [(0, 2), (2, 10)]


def test_zone_boundaries_foot_even():
    # one zone per 2-syllable foot.
    assert zone_boundaries("foot", 10) == [(0, 2), (2, 4), (4, 6), (6, 8), (8, 10)]


def test_zone_boundaries_foot_odd_clamps_last():
    # a trailing odd syllable makes a length-1 final foot (min clamp).
    assert zone_boundaries("foot", 9) == [(0, 2), (2, 4), (4, 6), (6, 8), (8, 9)]


def test_zone_boundaries_int_last_zone_absorbs_remainder():
    # int N: N equal zones, last one absorbs the remainder (10 // 3 == 3).
    assert zone_boundaries(3, 10) == [(0, 3), (3, 6), (6, 10)]


def test_zone_boundaries_invalid_raises():
    with pytest.raises(ValueError, match="Unknown zones"):
        zone_boundaries("bogus", 10)


def test_make_zone_names_none_returns_base():
    assert make_zone_names(["w_stress", "s_unstress"], 10, None) == [
        "w_stress", "s_unstress"
    ]


def test_make_zone_names_initial():
    assert make_zone_names(["a", "b"], 10, "initial") == [
        "a_init", "b_init", "a_rest", "b_rest"
    ]


def test_make_zone_names_foot():
    # (nsylls + 1) // 2 == 5 feet for a 10-syllable line.
    assert make_zone_names(["a", "b"], 10, "foot") == [
        "a_f1", "b_f1", "a_f2", "b_f2", "a_f3", "b_f3",
        "a_f4", "b_f4", "a_f5", "b_f5",
    ]


def test_make_zone_names_int():
    assert make_zone_names(["a", "b"], 10, 3) == [
        "a_z1", "b_z1", "a_z2", "b_z2", "a_z3", "b_z3"
    ]


def test_make_zone_names_invalid_raises():
    with pytest.raises(ValueError, match="Unknown zones"):
        make_zone_names(["a"], 10, "bogus")


def test_zone_split_shapes_and_sums():
    # 2 candidates, 10 syllables, 3 constraints, every cell a single violation.
    viols = np.ones((2, 10, 3), dtype=np.int8)

    # None: collapse the whole syllable axis -> (S, C), each == 10.
    flat = zone_split(viols, None)
    assert flat.shape == (2, 3)
    assert np.all(flat == 10)

    # "initial": [0:2] then [2:10] -> (S, C*2), first C cols == 2, next == 8.
    init = zone_split(viols, "initial")
    assert init.shape == (2, 6)
    assert np.all(init[:, :3] == 2)
    assert np.all(init[:, 3:] == 8)

    # int 2: two equal zones of 5 -> (S, C*2), all == 5.
    two = zone_split(viols, 2)
    assert two.shape == (2, 6)
    assert np.all(two == 5)

    # "foot": five 2-syllable zones -> (S, C*5), all == 2.
    foot = zone_split(viols, "foot")
    assert foot.shape == (2, 15)
    assert np.all(foot == 2)


# ---------------------------------------------------------------------------
# Training lifecycle: guard, learned_weights, predict, report, apply_to_meter
# ---------------------------------------------------------------------------

def test_train_before_load_raises():
    tr = MaxEntTrainer(Meter())
    with pytest.raises(ValueError, match="load_annotations|load_text"):
        tr.train()


@pytest.fixture(scope="module")
def trained():
    """A trainer fit on one clean iambic line with zones=None (read-only)."""
    tr = MaxEntTrainer(Meter(), regularization=10.0, zones=None)
    tr.load_text(LINE1, IAMBIC)
    tr.train()
    return tr


def test_learned_weights_keys_are_base_constraints(trained):
    weights = trained.learned_weights()
    # zones=None -> one weight per default constraint, no zone suffix.
    assert set(weights) == {
        "w_stress", "s_unstress", "unres_within", "unres_across",
        "w_peak", "foot_size",
    }
    # weights are returned as non-negative floats (negated from internal <=0).
    assert all(isinstance(v, float) for v in weights.values())
    assert all(v >= 0 for v in weights.values())


def test_train_converged(trained):
    assert trained._train_params["converged"] is True
    assert trained._train_params["method"] == "L-BFGS-B"


def test_predict_columns_and_normalization(trained):
    pred = trained.predict()
    assert list(pred.columns) == ["text", "scansion", "observed", "predicted"]
    assert len(pred) > 1  # many candidate scansions for a pentameter line
    # predicted is a proper distribution per line: sums to 1.
    for _, group in pred.groupby("text", sort=False):
        assert np.isclose(group["predicted"].sum(), 1.0)
        # observed is the normalized target frequency; also a distribution.
        assert np.isclose(group["observed"].sum(), 1.0)


def test_predict_target_becomes_most_probable(trained):
    # A meaningful learning check: after training, the annotated (target)
    # scansion is the single most probable one the model predicts.
    pred = trained.predict()
    top = pred.loc[pred["predicted"].idxmax()]
    observed = pred.loc[pred["observed"].idxmax()]
    assert top["scansion"] == observed["scansion"] == IAMBIC


def test_report_prints_sections(trained, capsys):
    trained.report()
    out = capsys.readouterr().out
    for chunk in (
        "MaxEnt Training Report",
        "Learned Constraint Weights",
        "Predictions",
        "Log-likelihood",
        f"Regularization: {trained.regularization}",
    ):
        assert chunk in out
    # every base constraint is listed in the weights block
    for name in ("w_stress", "s_unstress", "foot_size"):
        assert name in out


def test_apply_to_meter_sets_constraints_and_resets_key():
    meter = Meter()
    tr = MaxEntTrainer(meter, regularization=10.0, zones=None)
    tr.load_text(LINE1, IAMBIC)
    tr.train()
    # prime the cached constraint-func property + key so we can see them cleared
    _ = meter.constraint_funcs
    _ = meter.key
    assert "constraint_funcs" in meter.__dict__

    learned = tr.learned_weights()
    tr.apply_to_meter()

    assert meter.constraints == learned
    assert meter._key is None                    # key invalidated
    assert "constraint_funcs" not in meter.__dict__  # cached prop cleared


# ---------------------------------------------------------------------------
# load_annotations: list / DataFrame / pre-built TextModel inputs
# ---------------------------------------------------------------------------

def test_load_annotations_list_matches_scansion():
    tr = MaxEntTrainer(Meter(), regularization=10.0)
    tr.load_annotations([(LINE1, IAMBIC, 1.0)])
    matched = [ld for ld in tr._line_data if ld["observed"].sum() > 0]
    assert len(matched) == 1
    assert IAMBIC in matched[0]["scansions"]
    # the DataFrame form of the annotations is stored on the trainer
    assert list(tr._annotations.columns) == ["text", "scansion", "frequency"]


def test_load_annotations_dataframe_input():
    # DataFrame branch: load_annotations copies rather than rebuilds the frame.
    df = pd.DataFrame(
        [(LINE1, IAMBIC, 3.0)], columns=["text", "scansion", "frequency"]
    )
    tr = MaxEntTrainer(Meter(), regularization=10.0)
    tr.load_annotations(df)
    matched = [ld for ld in tr._line_data if ld["observed"].sum() > 0]
    assert len(matched) == 1
    # a defensive copy was taken (mutating the trainer's frame won't touch ours)
    assert tr._annotations is not df


def test_load_annotations_friendly_columns_and_path(tmp_path):
    # (a) DataFrame with `line` (not `text`), no frequency, extra columns -> normalized
    df = pd.DataFrame({"meter": ["iambic"], "line": [LINE1], "scansion": [IAMBIC],
                       "note": [""]})
    tr = MaxEntTrainer(Meter(), regularization=10.0)
    tr.load_annotations(df)
    assert list(tr._annotations.columns) == ["text", "scansion", "frequency"]
    assert tr._annotations["frequency"].tolist() == [1.0]
    assert [ld for ld in tr._line_data if ld["observed"].sum() > 0]

    # (b) a 2-tuple (text, scansion) with no frequency defaults to 1.0
    tr2 = MaxEntTrainer(Meter(), regularization=10.0)
    tr2.load_annotations([(LINE1, IAMBIC)])
    assert tr2._annotations["frequency"].tolist() == [1.0]

    # (c) a CSV file path loads directly (line/scansion columns, extras ignored)
    p = tmp_path / "ann.csv"
    df.to_csv(p, index=False)
    tr3 = MaxEntTrainer(Meter(), regularization=10.0)
    tr3.load_annotations(str(p))
    assert list(tr3._annotations.columns) == ["text", "scansion", "frequency"]
    assert len(tr3._annotations) == 1


def test_load_annotations_with_prebuilt_text():
    # text= branch: annotations attach to a pre-built (e.g. syntax) TextModel
    # instead of re-parsing the unique annotation strings.
    text = TextModel(f"{LINE1}\n{LINE2}")
    tr = MaxEntTrainer(Meter(), regularization=10.0)
    tr.load_annotations(
        [(LINE1, IAMBIC, 1.0), (LINE2, IAMBIC, 1.0)], text=text
    )
    assert len(tr._line_data) == 2
    matched = sum(1 for ld in tr._line_data if ld["observed"].sum() > 0)
    assert matched == 2


# ---------------------------------------------------------------------------
# Zone splitting through a real fit: initial / int / foot(+padding)
# ---------------------------------------------------------------------------

def _base_constraint_count(tr):
    return len(tr._base_constraint_names)


def test_fit_zones_initial_doubles_features():
    tr = MaxEntTrainer(Meter(), regularization=10.0, zones="initial")
    tr.load_text(LINE1, IAMBIC)
    tr.train()
    c = _base_constraint_count(tr)
    assert len(tr._constraint_names) == c * 2
    w = tr.learned_weights()
    assert any(k.endswith("_init") for k in w)
    assert any(k.endswith("_rest") for k in w)


def test_fit_zones_int_creates_n_zones():
    tr = MaxEntTrainer(Meter(), regularization=10.0, zones=3)
    tr.load_text(LINE1, IAMBIC)
    tr.train()
    c = _base_constraint_count(tr)
    assert len(tr._constraint_names) == c * 3
    w = tr.learned_weights()
    for z in ("_z1", "_z2", "_z3"):
        assert any(k.endswith(z) for k in w)


def test_fit_zones_foot_pads_shorter_lines():
    # Mixed-length lines under "foot" zones exercise the padding branch: the
    # 10-syllable line yields 5 feet (the max), the shorter line fewer, so the
    # shorter line's feature row is zero-padded up to 5-feet width.
    tr = MaxEntTrainer(Meter(), regularization=10.0, zones="foot")
    tr.load_text(f"{LINE1}\n{SHORT}", IAMBIC)
    tr.train()
    c = _base_constraint_count(tr)
    # max is a 5-foot (10-syll) line -> C * 5 features overall.
    assert len(tr._constraint_names) == c * 5
    assert any(k.endswith("_f5") for k in tr.learned_weights())
    # both lines are retained (short line kept, just padded), not dropped.
    assert len(tr._line_data) == 2
    # padding proof: every line's feature row is widened to the full C*5, even
    # the short line whose own foot count is < 5.
    assert all(ld["viols"].shape[1] == c * 5 for ld in tr._line_data)


# ---------------------------------------------------------------------------
# Ragged (mixed-syllable-count) lines: trained, not skipped
# ---------------------------------------------------------------------------

def test_ragged_line_trains():
    # "fire"/"flower" carry an elided 1-syllable variant alongside the
    # 2-syllable one; a line built from them pools parses of different lengths
    # and comes back ragged. MaxEnt consumes the syllable axis immediately
    # (zone_split -> a (C*Z) feature vector whose names are N-independent), so
    # each candidate zone-splits by its OWN length and mixed-N candidates stack
    # into the ordinary softmax. Ragged lines used to be dropped wholesale,
    # which excluded exactly the elision lines from every gold set (12/120 of
    # the foot gold).
    tr = MaxEntTrainer(Meter(), regularization=10.0, zones=None)
    tr.load_text([LINE1, RAGGED], IAMBIC)
    assert len(tr._line_data) == 2                   # BOTH lines kept
    # the ragged line's candidates include multiple syllable counts, and its
    # feature matrix is rectangular (stacked per-row zone splits)
    ragged_ld = next(ld for ld in tr._line_data if ld["text"] == RAGGED)
    lens = {len(s) for s in ragged_ld["scansions"]}
    assert len(lens) > 1
    assert ragged_ld["viols"].ndim == 2
    tr.train()
    assert tr._train_params["converged"] is True

    # same under zones (per-row boundaries shift with each candidate's N)
    trz = MaxEntTrainer(Meter(), regularization=10.0, zones=3)
    trz.load_text([LINE1, RAGGED], IAMBIC)
    assert len(trz._line_data) == 2
    trz.train()
    assert trz._train_params["converged"] is True


# ---------------------------------------------------------------------------
# Oversized/empty lines, unmatched annotations, list targets
# ---------------------------------------------------------------------------

def test_oversized_line_skipped_as_empty():
    # A prose line longer than the parse-unit cap comes back as a bare
    # ParseList with no violation matrix; it's counted as empty-skipped and
    # dropped, while the clean pentameter line still trains.
    prose = (
        "this is a very long prose sentence that exceeds the maximum syllable "
        "parse unit limit and falls well outside the normal single line path"
    )
    tr = MaxEntTrainer(Meter(), regularization=10.0, zones=None)
    tr.load_text([LINE1, prose], IAMBIC)
    assert tr._n_skipped_empty == 1
    assert len(tr._line_data) == 1
    tr.train()  # still trainable on the surviving line
    assert tr._train_params["converged"] is True


def test_unmatched_annotation_scores_zero_and_warns(monkeypatch):
    # A wrong-length scansion matches no parser candidate: the line stays in
    # _line_data with an all-zero observed vector (contributing nothing), and
    # the "no matching scansion" warning fires.
    captured = []
    monkeypatch.setattr(
        maxent_mod.log, "warning", lambda msg, *a, **k: captured.append(msg)
    )
    tr = MaxEntTrainer(Meter(), regularization=10.0)
    tr.load_annotations([(LINE1, "wswsws", 1.0)])  # 6 chars: cannot match a 10-syll line
    assert sum(ld["observed"].sum() for ld in tr._line_data) == 0.0
    assert any("no matching scansion" in m for m in captured)


def test_load_text_list_targets_match_by_length():
    # A list of targets exercises the list branch; each line takes only the
    # target(s) whose length matches its candidate scansions.
    tr = MaxEntTrainer(Meter(), regularization=10.0, zones=None)
    tr.load_text(LINE1, [IAMBIC, "wswswswsw"])  # 10-len and 9-len targets
    matched = [ld for ld in tr._line_data if ld["observed"].sum() > 0]
    assert len(matched) == 1
    # only the length-matching (10) target got observed mass.
    observed_scan = matched[0]["scansions"][int(np.argmax(matched[0]["observed"]))]
    assert observed_scan == IAMBIC


# ---------------------------------------------------------------------------
# Meter.fit_annotations end-to-end integration
# ---------------------------------------------------------------------------

def test_meter_fit_annotations_records_zone_weights():
    meter = Meter()
    out = meter.fit_annotations(
        [(LINE1, IAMBIC, 2.0), (LINE2, IAMBIC, 1.0)],
        zones="initial",
        regularization=10.0,
    )
    assert out is meter                               # chainable
    assert meter.zones == "initial"
    assert meter.zone_weights is not None
    # 6 default constraints x 2 zones = 12 zone weights.
    assert len(meter.zone_weights) == 12
    assert any(k.endswith("_init") for k in meter.zone_weights)
    assert any(k.endswith("_rest") for k in meter.zone_weights)
    # a stored trainer is kept for downstream reporting/prediction.
    assert isinstance(meter._trainer, MaxEntTrainer)
