"""High-level form detection: sonnets, etc.

Currently sonnet-aware only. Extends naturally to other named forms (villanelle,
ode, sestina) once their detection logic is added.
"""
from __future__ import annotations

from typing import Dict, Optional


def _canonical_sylls(text):
    df = text._syll_df
    canonical = df[(df["form_idx"] == 0) & (~df["is_punc"])]
    return canonical.groupby("line_num").size().to_dict()


def is_sonnet(text, meter_type: Optional[Dict] = None,
              rhyme_match: Optional[Dict] = None) -> bool:
    """A 14-line poem with iambic-pentameter-ish lines and a sonnet rhyme scheme."""
    if len(text.lines) != 14:
        return False
    syll_map = _canonical_sylls(text)
    sylls = [syll_map.get(line.num, 0) for line in text.lines]
    median_sylls = _median(sylls)
    if median_sylls is None or int(median_sylls) not in (9, 10, 11):
        return False
    if rhyme_match is None:
        from .rhyme_scheme import compute_rhyme_ids, match_rhyme_scheme
        rhyme_match = match_rhyme_scheme(compute_rhyme_ids(text))
    if not rhyme_match:
        return False
    return "sonnet" in rhyme_match["name"].lower()


def is_shakespearean_sonnet(text, rhyme_match: Optional[Dict] = None) -> bool:
    if not is_sonnet(text, rhyme_match=rhyme_match):
        return False
    if rhyme_match is None:
        from .rhyme_scheme import compute_rhyme_ids, match_rhyme_scheme
        rhyme_match = match_rhyme_scheme(compute_rhyme_ids(text))
    return rhyme_match is not None and "shakespeare" in rhyme_match["name"].lower()


def _median(xs):
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
