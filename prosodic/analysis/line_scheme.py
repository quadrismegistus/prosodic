"""Line-length scheme detection.

Given a sequence of line lengths (in feet or syllables), find the best-fitting
repeating template. E.g. ``[5,5,5,5,...]`` → invariable pentameter,
``[4,3,4,3,...]`` → ballad meter, etc.

Ported from poesy's ``Poem.get_scheme``. The original used ``np.median`` /
``np.mean``; this version uses statistics from the standard library.
"""
from __future__ import annotations

import statistics
from itertools import product
from typing import List, Optional, Tuple

BEAT_NAMES = {
    1: "Monometer", 2: "Dimeter", 3: "Trimeter", 4: "Tetrameter",
    5: "Pentameter", 6: "Hexameter", 7: "Heptameter", 8: "Octameter",
    9: "Enneameter", 10: "Decameter", 11: "Hendecameter", 12: "Dodecameter",
}


def _measure_diff(observed: List[int], model: List[int], beat: bool) -> int:
    n = min(len(observed), len(model))
    diff = sum(abs(a - b) for a, b in zip(observed[:n], model[:n]))
    return diff * 2 if beat else diff


def detect_line_scheme(
    lengths: List[int],
    beat: bool = True,
    stanza_length: Optional[int] = None,
    encourage_invariable: bool = True,
) -> Tuple[Optional[Tuple[int, ...]], Optional[int]]:
    """Find the repeating template that best fits a sequence of line lengths.

    Args:
        lengths: per-line metric lengths (number of feet, or syllables).
        beat: whether ``lengths`` is in beats (feet) or syllables. Affects
            tolerance — beat schemes are stricter.
        stanza_length: if known, restrict candidate templates to lengths
            that divide the stanza evenly.
        encourage_invariable: penalize variable templates by 1.

    Returns:
        ``(best_combo, best_diff)``. ``best_combo`` is a tuple of integer
        positions (the repeating template). ``best_diff`` is the total
        per-position difference of the model vs observed lengths.
    """
    if not lengths:
        return None, None

    num_lines = len(lengths)
    min_len, max_len = min(lengths), max(lengths)
    abs_diff = abs(min_len - max_len)
    is_variable = abs_diff > (2 if beat else 4)
    del is_variable  # currently informational; kept for parity with poesy

    min_seq_length = 1
    try_lim = 10
    max_seq_length = stanza_length if stanza_length else 12

    best_combo: Optional[Tuple[int, ...]] = None
    best_diff: Optional[int] = None

    for seq_len in range(min_seq_length, int(max_seq_length) + 1):
        if seq_len > num_lines:
            break
        if stanza_length and stanza_length % seq_len:
            continue
        if num_lines and num_lines % seq_len:
            continue
        if seq_len > try_lim:
            break

        # Median length per position in the repeating template
        per_pos: dict[int, list[int]] = {i: [] for i in range(seq_len)}
        for i, length in enumerate(lengths):
            per_pos[i % seq_len].append(length)
        median_per_pos = {
            i: int(statistics.median(v)) if len(v) > 1 else v[0]
            for i, v in per_pos.items()
        }

        # Try candidates ±1 around the median at each position
        per_pos_options = [
            list(range(median_per_pos[i] - 1, median_per_pos[i] + 2))
            for i in range(seq_len)
        ]
        for combo in product(*per_pos_options):
            if len(combo) > 1 and len(set(combo)) == 1:
                continue  # collapses to a shorter template

            # Repeat to cover all observed lines
            model = []
            while len(model) < num_lines:
                model.extend(combo)
            model = model[:num_lines]

            diff = _measure_diff(lengths, model, beat=beat)
            if not beat:
                diff += sum(5 if x % 2 else 0 for x in combo)
            if encourage_invariable:
                diff += 1 if len(set(combo)) > 1 else 0

            if best_diff is None or diff < best_diff:
                best_diff = diff
                best_combo = combo
            elif best_combo is not None and diff <= best_diff:
                if len(combo) < len(best_combo):
                    best_combo = combo
                    best_diff = diff

    return best_combo, best_diff


def scheme_type(scheme: Tuple[int, ...]) -> str:
    if len(scheme) == 1:
        return "Invariable"
    if len(scheme) == 2:
        return "Alternating"
    return "Complex"


def scheme_repr(scheme: Tuple[int, ...], beat: bool = False) -> str:
    """Render a scheme as a human-readable label."""
    stype = scheme_type(scheme)
    if beat and stype != "Complex":
        labels = [BEAT_NAMES.get(s, str(s)) for s in scheme]
    else:
        labels = [str(s) for s in scheme]
    if stype == "Invariable":
        return labels[0]
    return f"{stype} ({'-'.join(labels).lower()})"
