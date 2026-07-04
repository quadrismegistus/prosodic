import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
from prosodic.langs.langs import Language, count_stresses_in_sylls_ipa_l

disable_caching()


def test_pronunciation_variant_order_deterministic():
    """Pronunciation variants must come back in a fully-determined order
    (including syllable content), so the best-parse tie-break can't flip across
    runs or PYTHONHASHSEED values.

    Regression: get_sylls_ipa_ll deduped variants through set() and then sorted
    by (stress_count, len), leaving variants with an equal key in hash-seed
    order. That propagated to form_idx and made text.parse() return different
    best scansions across runs on lines with tied-score parses."""
    lang = Language("en")
    checked = 0
    for tok in ["beauty", "desire", "increase", "fire", "heaven", "flower",
                "being", "power", "hour", "spirit", "even", "many", "towards"]:
        variants, _ = lang.get_sylls_ipa_ll(tok)
        if len(variants) < 2:
            continue
        keys = [(count_stresses_in_sylls_ipa_l(v), len(v), tuple(v)) for v in variants]
        assert keys == sorted(keys), \
            f"{tok!r}: pronunciation variants not in deterministic order: {keys}"
        checked += 1
    assert checked > 0, "no multi-variant word found to exercise the ordering"
