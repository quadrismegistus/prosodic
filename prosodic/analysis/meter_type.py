"""Meter-type classification (iambic / trochaic / anapestic / dactylic).

Aggregates parse statistics across all best parses in a text:

- **foot type** (binary vs ternary): fraction of weak positions that span
  two syllables (``ww``). High fraction → ternary.
- **head type** (initial vs final): whether the 4th syllable tends to be
  strong or weak across lines.

Combined: (binary, final) → iambic; (binary, initial) → trochaic;
(ternary, final) → anapestic; (ternary, initial) → dactylic.

Ported from poesy's ``Poem.meterd``, but reads from the v3 parse
representation (``parse.positions`` / ``meter_val``) rather than v1's
``mpos.mstr`` / ``constraintScores``.
"""
from __future__ import annotations

from collections import Counter
from typing import Dict, Optional

# Threshold (fraction of `ww` positions) above which a poem is ternary.
# Inherited from poesy; tuned on Stanford LitLab corpus.
TERNARY_WW_THRESHOLD = 0.175


def _position_label(pos) -> str:
    """Return string like 's', 'w', 'ww', 'ss' for a parse position."""
    return pos.meter_val * pos.num_slots


def classify_meter_type(text) -> Dict[str, object]:
    """Classify the dominant meter of a parsed text.

    Args:
        text: a parsed ``TextModel`` (call ``.parse()`` first).

    Returns:
        dict with:
            ``foot`` — ``'binary'`` or ``'ternary'``
            ``head`` — ``'initial'`` or ``'final'``
            ``type`` — ``'iambic'`` | ``'trochaic'`` | ``'anapestic'`` | ``'dactylic'``
            ``mpos_freqs`` — frequency dict of position labels
            ``perc_lines_starting_s`` etc. — head-position frequencies
            ``ambiguity`` — geometric mean (per line) of parse counts (NaN-tolerant)
    """
    all_labels: list[str] = []
    line_starts: list[str] = []
    line_ends: list[str] = []
    fourth_pos: list[str] = []
    parse_counts: list[int] = []

    for line in text.lines:
        try:
            best = line.best_parse
        except Exception:
            best = None
        if best is None:
            continue
        labels = [_position_label(p) for p in best.positions]
        if not labels:
            continue
        all_labels.extend(labels)

        scansion = "".join(labels)
        line_starts.append(scansion[0])
        line_ends.append(scansion[-1])
        if len(scansion) >= 4:
            fourth_pos.append(scansion[3])

        try:
            n_parses = len(line.parses.unbounded)
        except Exception:
            n_parses = 1
        if n_parses > 0:
            parse_counts.append(n_parses)

    def freq(seq):
        c = Counter(seq)
        total = sum(c.values()) or 1
        return {k: v / total for k, v in c.items()}

    mpos_freqs = freq(all_labels)
    start_freqs = freq(line_starts)
    end_freqs = freq(line_ends)
    fourth_freqs = freq(fourth_pos)

    foot = "ternary" if mpos_freqs.get("ww", 0) > TERNARY_WW_THRESHOLD else "binary"
    if foot == "ternary":
        head = "initial" if fourth_freqs.get("s", 0) > 0.5 else "final"
    else:
        head = "initial" if fourth_freqs.get("s", 0) < 0.5 else "final"

    type_label = {
        ("ternary", "final"): "anapestic",
        ("ternary", "initial"): "dactylic",
        ("binary", "initial"): "trochaic",
        ("binary", "final"): "iambic",
    }[(foot, head)]

    # Geometric mean of per-line parse counts (closer to poesy than arithmetic
    # mean — ambiguity is multiplicative, not additive)
    if parse_counts:
        log_total = sum(_safe_log(n) for n in parse_counts)
        ambiguity = _safe_exp(log_total / len(parse_counts))
    else:
        ambiguity = None

    return {
        "foot": foot,
        "head": head,
        "type": type_label,
        "mpos_freqs": mpos_freqs,
        "perc_lines_starting": start_freqs,
        "perc_lines_ending": end_freqs,
        "perc_lines_fourth": fourth_freqs,
        "ambiguity": ambiguity,
    }


def _safe_log(x: float) -> float:
    import math
    return math.log(x) if x > 0 else 0.0


def _safe_exp(x: float) -> float:
    import math
    return math.exp(x)


def text_foot_type(text) -> Optional[str]:
    """Convenience: just the meter type label."""
    if not text.lines:
        return None
    return classify_meter_type(text)["type"]
