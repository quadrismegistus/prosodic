import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from prosodic.imports import *
from prosodic.langs.g2p_align import align_syllable_text

disable_caching()


# The words from issue #47, plus regression cases. Each pairs a token with
# its dictionary/TTS syllable IPA and the expected orthographic split.
ISSUE_47_CASES = [
    ("within", ("wɪ", "'ðɪn"), ["wi", "thin"]),
    ("thereby", ("'ðɛr", "'baɪ"), ["there", "by"]),
    ("substantial", ("sʌb", "'stæn", "ʧəl"), ["sub", "stan", "tial"]),
    ("beauty's", ("'bjuː", "ɾiz"), ["beau", "ty's"]),
    ("cruel", ("'kruːl",), ["cruel"]),
    ("niggarding", ("'nɪ", "ɡəɹ", "dɪŋ"), ["nig", "gar", "ding"]),
    ("glutton", ("'ɡlʌ", "ʔn"), ["glut", "ton"]),
    ("increase", ("ɪn", "'kriːs"), ["in", "crease"]),
    ("memory", ("'mɛ", "mə", "riː"), ["me", "mo", "ry"]),
    ("abundance", ("ə", "'bʌn", "dəns"), ["a", "bun", "dance"]),
    ("creatures", ("'kriː", "ʧərz"), ["crea", "tures"]),
    ("Making", ("'meɪ", "kɪŋ"), ["Ma", "king"]),  # case preserved
    ("tucker", ("'tʌ", "kər"), ["tuc", "ker"]),   # ck split, not tu|cker
]


@pytest.mark.parametrize("token,sylls_ipa,expected", ISSUE_47_CASES)
def test_align_examples(token, sylls_ipa, expected):
    assert align_syllable_text(token, sylls_ipa) == expected


def test_align_invariants_join_and_count():
    for token, sylls_ipa, _ in ISSUE_47_CASES:
        result = align_syllable_text(token, sylls_ipa)
        assert "".join(result) == token
        assert len(result) == len(sylls_ipa)
        assert all(result)


def test_align_rejects_letter_by_letter_initialisms():
    # "gmbh" is pronounced as four spelled-out letters; there is no sane
    # orthographic split, so the aligner must decline (caller falls back).
    assert align_syllable_text("gmbh", ("'ʤiː", "'ɛm", "'biː", "'eɪʧ")) is None


def test_pipeline_syllable_text_matches_phonology():
    # End-to-end reproduction of issue #47 through the real pipeline.
    t = TextModel("thereby beauty's within glutton")
    got = {}
    for w in t.wordtokens:
        if not w.children or not w.children[0].children:
            continue
        wf = w.children[0].children[0]
        got[w.txt.strip()] = [s.txt for s in wf.children]
    assert got["within"] == ["wi", "thin"]
    assert got["thereby"] == ["there", "by"]
    assert got["beauty's"] == ["beau", "ty's"]
    assert got["glutton"] == ["glut", "ton"]


def test_pipeline_syllable_text_joins_to_token():
    # Syllable labels must always reassemble the word exactly.
    t = TextModel("From fairest creatures we desire increase")
    for w in t.wordtokens:
        if not w.children or not w.children[0].children:
            continue
        for wf in w.children[0].children:
            joined = "".join(s.txt for s in wf.children)
            assert joined.lower() == w.txt.strip().lower()
