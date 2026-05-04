"""Per-line + estimated-schema summary table for a parsed text."""
from __future__ import annotations

from typing import List, Optional

from .line_scheme import detect_line_scheme, scheme_repr
from .meter_type import classify_meter_type
from .rhyme_scheme import compute_rhyme_ids, match_rhyme_scheme, nums_to_scheme


def _line_metadata(text):
    """Per-line stanza number + canonical syll count from _syll_df.

    Canonical = form_idx==0 (first pronunciation). Avoids over-counting from
    pronunciation variants, which would otherwise inflate ``num_sylls``.
    """
    df = text._syll_df
    canonical = df[(df["form_idx"] == 0) & (~df["is_punc"])]
    syll_counts = canonical.groupby("line_num").size().to_dict()
    stanza_map = df.groupby("line_num")["para_num"].first().to_dict()
    return syll_counts, stanza_map


def per_line_rows(text) -> List[dict]:
    """Per-line annotations: parse string, syllable/foot counts, rhyme letter, ambiguity."""
    rhyme_ids = compute_rhyme_ids(text)
    rhyme_letters = nums_to_scheme(rhyme_ids)
    syll_counts, stanza_map = _line_metadata(text)
    rows: List[dict] = []
    for i, line in enumerate(text.lines):
        ln = line.num
        try:
            best = line.best_parse
        except Exception:
            best = None
        try:
            n_parses = len(line.parses.unbounded)
        except Exception:
            n_parses = 0
        rows.append({
            "stanza_num": int(stanza_map.get(ln, 1)),
            "line_num": ln,
            "line": line.txt.strip(),
            "parse": best.meter_str if best else "",
            "num_sylls": int(syll_counts.get(ln, 0)),
            "num_feet": best.num_peaks if best else None,
            "num_parses": n_parses,
            "rhyme": rhyme_letters[i] if i < len(rhyme_letters) else "?",
            "score": float(best.score) if best is not None else None,
        })
    return rows


def summary(text, header: Optional[List[str]] = None) -> str:
    """Render a tabular summary of metrical + rhyme annotations.

    Args:
        text: a parsed ``TextModel``.
        header: optional list of column keys from :func:`per_line_rows`.

    Returns:
        A multi-line string: per-line table + estimated schema block.
    """
    from tabulate import tabulate

    if header is None:
        header = ["stanza_num", "line_num", "parse", "rhyme",
                  "num_feet", "num_sylls", "num_parses"]
    col_labels = {
        "stanza_num": "#st",
        "line_num": "#ln",
        "parse": "parse",
        "rhyme": "rhyme",
        "num_feet": "#feet",
        "num_sylls": "#syll",
        "num_parses": "#parse",
        "score": "score",
        "line": "line",
    }

    rows = per_line_rows(text)
    data = []
    cur_stanza = None
    for r in rows:
        if cur_stanza is None:
            cur_stanza = r["stanza_num"]
        if r["stanza_num"] != cur_stanza:
            data.append([""] * len(header))
            cur_stanza = r["stanza_num"]
        data.append([r.get(h, "") for h in header])
    cols = [col_labels.get(h, h) for h in header]
    table = tabulate(data, headers=cols)

    # Estimated schema
    mtype = classify_meter_type(text)
    beat_lengths = [r["num_feet"] for r in rows if r["num_feet"] is not None]
    syll_lengths = [r["num_sylls"] for r in rows]
    beat_combo, _ = detect_line_scheme(beat_lengths, beat=True)
    syll_combo, _ = detect_line_scheme(syll_lengths, beat=False)
    rmatch = match_rhyme_scheme(compute_rhyme_ids(text))

    schema_lines = [
        f"meter: {mtype['type'].title()}",
        f"feet: {scheme_repr(beat_combo, beat=True) if beat_combo else '?'}",
        f"syllables: {scheme_repr(syll_combo, beat=False) if syll_combo else '?'}",
    ]
    if rmatch:
        rhy = f"rhyme: {rmatch['name']}"
        if rmatch["form"]:
            rhy += f" ({rmatch['form']})"
        schema_lines.append(rhy)

    return table + "\n\n\nestimated schema\n----------\n" + "\n".join(schema_lines)
