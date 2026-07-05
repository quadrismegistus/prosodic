"""Hayes-style metrical grid over a parsed line.

A metrical grid (Liberman & Prince 1977; Hayes 1983) stacks marks over
syllables: column height encodes linguistic prominence. Here the grid rows
are, bottom-up: every syllable, lexically stressed syllables (primary or
secondary), primary-stressed syllables. The metrical template is NOT mixed
into the mark columns (that would put gaps in them); it appears as a w/s
annotation row beneath the syllable text, so a stress/meter mismatch reads
as a tall column over a ``w`` — exactly the mismatch the parser's
constraints penalize. Positions whose best parse incurred violations are
flagged with ``*`` after the meter letter.

Ported in spirit from cadence's ``sent.grid()`` (see ROADMAP.md).
"""
from __future__ import annotations

from typing import List, Optional


def grid_data(parse, phrasal: Optional[List] = None) -> List[dict]:
    """Per-syllable grid rows for a parse.

    Args:
        parse: a Parse object.
        phrasal: optional per-syllable gradient phrasal prominence values
            (``tstress`` in [0,1], NaN/None where unavailable), same order
            as the parse's syllables. Extends the columns of each word's
            primary-stressed syllable: +1 level for phrasally prominent
            words (>= 0.5), +1 more for the nuclear-stress word (~1.0) —
            the Liberman & Prince projection of phrasal prominence onto
            the word's strongest syllable.

    Returns a list of dicts, one per syllable in order:
    ``txt``, ``stress`` ('P'/'S'/'U'), ``meter`` ('s'/'w'),
    ``height`` (1=syllable, 2=+stressed, 3=+primary, 4=+phrasal,
    5=nuclear), ``phrasal`` (float or None), ``viol`` (bool: the
    containing position has violations).
    """
    rows = []
    syll_i = 0
    for pos in parse.positions:
        viol = bool(pos.violset)
        for slot in pos.slots:
            unit = slot.unit
            stress = getattr(unit, "stress", "U") or "U"
            height = 1 + (stress in ("P", "S")) + (stress == "P")
            ph = None
            if phrasal is not None and syll_i < len(phrasal):
                v = phrasal[syll_i]
                ph = None if v is None or v != v else float(v)  # NaN-safe
            if ph is not None and stress == "P":
                height += (ph >= 0.5) + (ph >= 0.999)
            rows.append({
                # slot.txt renders case by metrical prominence (STRONG/weak)
                "txt": slot.txt.strip(),
                "stress": stress,
                "meter": pos.meter_val,
                "height": height,
                "phrasal": ph,
                "viol": viol,
            })
            syll_i += 1
    return rows


def phrasal_values(parse, text) -> Optional[List]:
    """Per-syllable gradient phrasal prominence (tstress) for a parse.

    Reads the ``tstress`` column computed by ``syntax=True`` from the
    text's syllable DataFrame and maps it onto the parse's syllables via
    word identity (SyllData.word_num on the DF path; the wordtoken parent
    chain on the entity path). Returns None when no gradient data exists.
    """
    df = getattr(text, "_syll_df", None)
    if df is None or "tstress" not in df.columns:
        return None
    tmap = (
        df.drop_duplicates("word_num")
        .set_index("word_num")["tstress"].to_dict()
    )

    def find_word_num(unit):
        wn = getattr(unit, "word_num", None)
        if wn is not None:
            return wn
        ent = unit
        for _ in range(8):
            ent = getattr(ent, "parent", None)
            if ent is None:
                return None
            if ent.__class__.__name__ == "WordToken":
                return ent.num
        return None

    vals = []
    for slot in parse.slots:
        v = tmap.get(find_word_num(slot.unit))
        vals.append(None if v is None or v != v else float(v))
    return vals


def grid_str(parse, mark: str = "*", viols: bool = True,
             phrasal: Optional[List] = None) -> str:
    """Render the grid as monospace text.

    Example::

                                *
            *       *       *   *        *
        *   *   *   *   *   *   *   *    *   *
        when IN  the CHRO ni  CLE  of  WA sted TIME
        w    s   w   s    w   s   w   s  w    s
    """
    rows = grid_data(parse, phrasal=phrasal)
    if not rows:
        return ""
    widths = [max(len(r["txt"]), 1) for r in rows]
    max_h = max(r["height"] for r in rows)

    def cell(content, w):
        return content.ljust(w)

    lines = []
    for level in range(max_h, 0, -1):
        lines.append(" ".join(
            cell(mark if r["height"] >= level else "", w)
            for r, w in zip(rows, widths)
        ).rstrip())
    lines.append(" ".join(cell(r["txt"], w) for r, w in zip(rows, widths)).rstrip())
    lines.append(" ".join(
        cell(r["meter"] + ("*" if viols and r["viol"] else ""), w)
        for r, w in zip(rows, widths)
    ).rstrip())
    return "\n".join(lines)


def grid_df(parse, phrasal=None):
    """Grid as a DataFrame: one row per syllable with prominence levels."""
    import pandas as pd

    df = pd.DataFrame(grid_data(parse, phrasal=phrasal))
    df.index.name = "syll_i"
    return df


def grid_plot(parse, mark_size: int = 6, phrasal=None):
    """Grid as a plotnine figure: mark stacks over syllable labels.

    Returns a ``plotnine.ggplot``; display it in a notebook or ``.save()`` it.
    """
    import pandas as pd
    from plotnine import (
        aes, element_blank, geom_point, geom_text, ggplot, labs,
        scale_x_continuous, scale_y_continuous, theme, theme_minimal,
    )

    rows = grid_data(parse, phrasal=phrasal)
    marks = [
        {"x": i, "y": level, "meter": r["meter"]}
        for i, r in enumerate(rows)
        for level in range(1, r["height"] + 1)
    ]
    labels = [
        {"x": i, "y": 0,
         "label": r["txt"] + ("\n" + r["meter"] + ("*" if r["viol"] else ""))}
        for i, r in enumerate(rows)
    ]
    p = (
        ggplot(pd.DataFrame(marks), aes("x", "y"))
        + geom_point(size=mark_size, shape="*")
        + geom_text(aes("x", "y", label="label"), data=pd.DataFrame(labels), size=8)
        + scale_y_continuous(limits=(-0.5, max(r["height"] for r in rows) + 0.5))
        + scale_x_continuous(limits=(-0.5, len(rows) - 0.5))
        + theme_minimal()
        + theme(
            axis_text=element_blank(),
            axis_ticks=element_blank(),
            panel_grid=element_blank(),
        )
        + labs(x="", y="")
    )
    return p
