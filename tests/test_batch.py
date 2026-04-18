"""Tests for prosodic.parse_corpus (batch parsing to disk)."""
import os
import sys
import shutil
import tempfile

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import prosodic
from prosodic.imports import *

disable_caching()


TEXTS = [
    ("t001", "Shall I compare thee to a summer's day?"),
    ("t002", "Rough winds do shake the darling buds of May"),
    ("t003", "And summer's lease hath all too short a date"),
]


@pytest.fixture
def tmp_out():
    d = tempfile.mkdtemp(prefix="prosodic_batch_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


# --- basic serial ---

def test_serial_basic(tmp_out):
    stats = prosodic.parse_corpus(TEXTS, tmp_out, progress=False)
    assert stats['n_done'] == 3
    assert stats['n_skipped'] == 0
    assert stats['n_failed'] == 0
    for tid, _ in TEXTS:
        assert os.path.isfile(os.path.join(tmp_out, tid, "meta.json"))
        assert os.path.isfile(os.path.join(tmp_out, tid, "syll.parquet"))


def test_dict_items(tmp_out):
    items = [{"id": tid, "txt": txt} for tid, txt in TEXTS]
    stats = prosodic.parse_corpus(items, tmp_out, progress=False)
    assert stats['n_done'] == 3


def test_roundtrip_load(tmp_out):
    prosodic.parse_corpus(TEXTS[:1], tmp_out, progress=False)
    t = prosodic.TextModel.load(os.path.join(tmp_out, "t001"))
    assert t._syll_df is not None
    assert len(t._syll_df) > 0
    assert t._cached_parsed_df is not None


def test_save_kwargs_propagates(tmp_out):
    # 'all' mode includes bounded parses; default 'unbounded' excludes them.
    prosodic.parse_corpus(TEXTS[:1], tmp_out, progress=False)
    default_df = prosodic.TextModel.load(os.path.join(tmp_out, "t001"))._cached_parsed_df
    assert not default_df['is_bounded'].any()

    all_out = tempfile.mkdtemp(prefix="prosodic_batch_all_")
    try:
        prosodic.parse_corpus(
            TEXTS[:1], all_out, progress=False,
            save_kwargs={'save_parses': 'all'},
        )
        all_df = prosodic.TextModel.load(os.path.join(all_out, "t001"))._cached_parsed_df
        assert len(all_df) > len(default_df)
        assert all_df['is_bounded'].any()
    finally:
        shutil.rmtree(all_out, ignore_errors=True)


# --- resume ---

def test_resume_skips(tmp_out):
    prosodic.parse_corpus(TEXTS, tmp_out, progress=False)
    stats = prosodic.parse_corpus(TEXTS, tmp_out, progress=False)
    assert stats['n_skipped'] == 3
    assert stats['n_done'] == 0


def test_resume_false_reparses(tmp_out):
    prosodic.parse_corpus(TEXTS, tmp_out, progress=False)
    stats = prosodic.parse_corpus(TEXTS, tmp_out, resume=False, progress=False)
    assert stats['n_done'] == 3
    assert stats['n_skipped'] == 0


# --- device ---

def test_device_cpu(tmp_out):
    stats = prosodic.parse_corpus(TEXTS, tmp_out, device='cpu', progress=False)
    assert stats['n_done'] == 3


def test_device_invalid():
    with pytest.raises(ValueError):
        prosodic.parse_corpus([], "/tmp/x", device='tpu')


# --- error handling ---

def test_on_error_log_continues(tmp_out):
    # empty string triggers ValueError in TextModel
    items = [("ok", "hello world"), ("bad", ""), ("ok2", "goodbye now")]
    stats = prosodic.parse_corpus(items, tmp_out, progress=False, on_error='log')
    assert stats['n_done'] == 2
    assert stats['n_failed'] == 1
    assert stats['errors'][0][0] == 'bad'


def test_on_error_raise(tmp_out):
    items = [("bad", "")]
    with pytest.raises(RuntimeError):
        prosodic.parse_corpus(items, tmp_out, progress=False, on_error='raise')


# --- multiprocessing ---

# Skipped in CI: spawned workers re-import prosodic (torch + espeak) which
# can hang on GitHub-hosted runners. Works fine locally.
@pytest.mark.skipif(
    bool(os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS')),
    reason='multiprocessing spawn can hang in CI',
)
def test_multiprocessing(tmp_out):
    stats = prosodic.parse_corpus(
        TEXTS, tmp_out, n_workers=2, device='cpu', progress=False,
    )
    assert stats['n_done'] == 3
    for tid, _ in TEXTS:
        assert os.path.isfile(os.path.join(tmp_out, tid, "meta.json"))


def test_gpu_forces_single_worker(tmp_out, capsys):
    # only meaningful if GPU available; otherwise resolve_device returns 'cpu'
    import prosodic.parsing.vectorized as vp
    if vp.get_device() is None:
        pytest.skip("no GPU available")
    prosodic.parse_corpus(
        TEXTS[:1], tmp_out, n_workers=4, device='gpu', progress=False,
    )
    captured = capsys.readouterr()
    assert 'n_workers=1' in captured.err
