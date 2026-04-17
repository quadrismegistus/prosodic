import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
from prosodic.web.models import (
    MaxEntFitRequest, MaxEntFitResponse, WeightEntry,
    MaxEntReparseRequest, MaxEntReparseResponse, ReparseRow,
    MeterDefaultsResponse, MeterDefaults,
    CorpusFile, CorpusListResponse,
)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse, Response
from typing import Optional
import json
import asyncio
import glob as globmod

app = FastAPI(title="Prosodic", description="Metrical parser for English and Finnish")

linelim = 15000
_text_cache = {}

STATIC_BUILD_DIR = os.path.join(os.path.dirname(__file__), "static_build")
CORPORA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "corpora")


def get_text(txt, **kwargs):
    key = (txt, tuple(sorted(kwargs.items())))
    if key not in _text_cache:
        _text_cache[key] = TextModel(txt, **kwargs)
    return _text_cache[key]


def _render_slot(slot):
    unit = slot.unit
    mtr = 'mtr_s' if slot.is_prom else 'mtr_w'
    strs = 'str_s' if unit.is_stressed else 'str_w'
    viols = list(slot.violset)
    viol = 'viol_y' if viols else 'viol_n'
    classes = f'{mtr} {strs} {viol}'
    if viols:
        tip = ', '.join(f'*{v}' for v in viols)
        return f'<span class="{classes}"><span class="tip">{tip}</span>{unit.txt}</span>'
    return f'<span class="{classes}">{unit.txt}</span>'


def render_parse_html(parse, line=None):
    """Render a parse as HTML with meter/stress/violation CSS classes.

    If `line` is provided, interleaves punctuation tokens so the original
    surface form is preserved. Otherwise falls back to word-space joining
    of parsed syllables only.
    """
    # Group slots by their containing wordtoken (walk up parent chain
    # until we find a WordToken — chain is Syllable → SyllableList →
    # WordForm → WordFormList → WordType → WordTypeList → WordToken).
    def _find_wordtoken(unit):
        ent = unit
        for _ in range(8):
            ent = getattr(ent, 'parent', None)
            if ent is None:
                return None
            if ent.__class__.__name__ == 'WordToken':
                return ent
        return None

    slots_by_wt = {}
    ordered_wt_ids = []
    for pos in parse.positions:
        for slot in pos.children:
            wt = _find_wordtoken(slot.unit)
            key = id(wt) if wt is not None else None
            if key not in slots_by_wt:
                slots_by_wt[key] = []
                ordered_wt_ids.append(key)
            slots_by_wt[key].append(slot)

    # If we have a line with wordtokens (incl. punctuation), interleave
    if line is not None and hasattr(line, 'wordtokens'):
        parts = []
        for wt in line.wordtokens:
            txt = wt.txt
            # preserve any leading whitespace from the original tokenization
            stripped = txt.lstrip()
            lead = txt[:len(txt) - len(stripped)]
            if lead:
                parts.append(lead)
            if getattr(wt, 'is_punc', False):
                parts.append(stripped)
                continue
            slots = slots_by_wt.get(id(wt))
            if slots:
                parts.extend(_render_slot(s) for s in slots)
            else:
                parts.append(stripped)
        return ''.join(parts)

    # Fallback: just join by word boundary using slot-side parents
    parts = []
    for i, key in enumerate(ordered_wt_ids):
        if i > 0:
            parts.append(' ')
        parts.extend(_render_slot(s) for s in slots_by_wt[key])
    return ''.join(parts)


def _build_meter_kwargs(constraints=None, max_s=2, max_w=2, resolve_optionality=True):
    kwargs = dict(max_s=max_s, max_w=max_w, resolve_optionality=resolve_optionality)
    if constraints:
        kwargs['constraints'] = constraints
    return kwargs


def _syntax_subsplit(linepart, t):
    """Split an oversized linepart into sub-WordTokenLists at clause boundaries
    inferred via spaCy's dependency parse. Returns a list of WordTokenList
    sub-units (or [linepart] if splitting failed/wasn't possible).

    Splits BEFORE tokens with these dep relations: cc, mark, advcl, ccomp,
    relcl, conj, parataxis, prep (when long).
    """
    try:
        from spacy.tokens import Doc
        from prosodic.texts.phrasal_stress import _get_nlp
        from prosodic.words.wordtokenlist import WordTokenList
    except Exception:
        return [linepart]

    # Filter out pure-punc tokens for spaCy
    content_idx = [i for i, wt in enumerate(linepart) if not getattr(wt, 'is_punc', False)]
    if len(content_idx) < 2:
        return [linepart]
    words = [linepart[i].txt.strip() for i in content_idx]
    if not all(words):
        return [linepart]

    try:
        nlp = _get_nlp()
        spaces = [True] * len(words)
        spaces[-1] = False
        doc = Doc(nlp.vocab, words=words, spaces=spaces)
        for _, proc in nlp.pipeline:
            doc = proc(doc)
    except Exception:
        return [linepart]

    SPLIT_DEPS = {'cc', 'mark', 'advcl', 'ccomp', 'relcl', 'conj', 'parataxis'}
    # split BEFORE these tokens (in content_idx terms)
    split_at_content = set()
    for tok_i, tok in enumerate(doc):
        if tok_i == 0:
            continue
        if tok.dep_ in SPLIT_DEPS:
            split_at_content.add(tok_i)

    if not split_at_content:
        return [linepart]

    # Translate content-token splits → linepart-index splits
    boundaries = sorted(content_idx[i] for i in split_at_content)

    # Build sub-units using all linepart indices, splitting at the boundaries.
    # Punctuation between content words sticks with the preceding chunk.
    sub_units = []
    start = 0
    for b in boundaries:
        if b > start:
            chunk = list(linepart[start:b])
            if chunk:
                sub_units.append(WordTokenList(children=chunk, parent=linepart.parent))
        start = b
    chunk = list(linepart[start:])
    if chunk:
        sub_units.append(WordTokenList(children=chunk, parent=linepart.parent))
    return sub_units if len(sub_units) > 1 else [linepart]


def _long_line_nums(t):
    """Set of line_nums that exceed MAX_SYLL_IN_PARSE_UNIT syllables.

    Counts canonical (form_idx=0) pronunciation only — variant pronunciations
    in the syll_df would otherwise inflate the syllable count.
    """
    df = getattr(t, '_syll_df', None)
    if df is None or len(df) == 0:
        return set()
    canonical = df[(df['is_punc'] == 0) & (df['form_idx'] == 0)]
    per_line = canonical.groupby('line_num').size()
    return set(int(ln) for ln, n in per_line.items() if n > MAX_SYLL_IN_PARSE_UNIT)


def _raw_linepart_html(unit):
    """Render a linepart's raw text (no parse styling) by concatenating
    its wordtokens — used when the linepart is too short/long to parse."""
    parts = []
    for wt in unit:
        parts.append(wt.txt)
    return ''.join(parts)


def _aggregate_lineparts(line_to_parts, render_html_fn):
    """Aggregate ordered (linepart, ParseList|None) pairs per line into rows.

    line_to_parts: dict[line_num] -> list of (linepart_unit, parse_list_or_none),
        in original linepart order. Lineparts without a parse list still get
        their raw text emitted so no content is silently dropped.
    """
    rows = []
    for line_num, parts in line_to_parts.items():
        if not parts:
            continue
        meter_strs = []
        html_parts = []  # list of (html_str, kind)
        total_score = 0.0
        ambig_product = 1
        line_text_parts = []
        n_parsed = 0
        total_sylls = 0
        total_viols = 0
        agg_viols = {}
        for unit, pl in parts:
            line_text_parts.append(unit.txt.strip())
            bp = pl.best_parse if pl else None
            if bp is None:
                # Pure-punctuation lineparts render as plain interstitial text
                # (no italic, no separator). Content lineparts that couldn't
                # parse get italic styling so the user sees they were skipped.
                if unit.num_sylls < 1:
                    html_parts.append((_raw_linepart_html(unit), 'punc'))
                else:
                    meter_strs.append('—')
                    html_parts.append((f'<span class="unparsed">{_raw_linepart_html(unit)}</span>', 'unparsed'))
                continue
            has_zone = hasattr(pl, '_scores') and pl._scores is not None
            score = float(pl._scores[0]) if has_zone and len(pl._scores) > 0 else bp.score
            meter_strs.append(bp.meter_str)
            html_parts.append((render_html_fn(bp, unit), 'parsed'))
            total_score += score
            ambig_product *= max(1, pl.num_unbounded)
            n_parsed += 1
            ns, nv, vs = _parse_viol_stats(bp)
            total_sylls += ns
            total_viols += nv
            for k, v in vs.items():
                agg_viols[k] = agg_viols.get(k, 0) + v

        # Stitch html: each new parsed (or unparsed) clause starts on its own
        # line within the table row via <br>. Punctuation lineparts attach to
        # whichever clause they fall after (no break before/after them).
        out = []
        seen_clause = False  # has any 'parsed' or 'unparsed' been emitted yet?
        for h, kind in html_parts:
            if kind in ('parsed', 'unparsed'):
                if seen_clause:
                    out.append('<br>')
                seen_clause = True
            out.append(h)

        rows.append({
            'line_num': int(line_num),
            'rank': 1,
            'line_text': ' '.join(line_text_parts),
            'parse_html': ''.join(out),
            'meter_str': '<br>'.join(meter_strs),
            'score': round(total_score, 2),
            'num_unbounded': ambig_product,
            'num_parts': len(parts),
            'num_parts_parsed': n_parsed,
            'num_sylls': total_sylls,
            'num_viols': total_viols,
            'viols': agg_viols,
        })
    return rows


def _normalize_zones(zones):
    if zones is None or zones == "none":
        return None
    if isinstance(zones, str) and zones.isdigit():
        return int(zones)
    if isinstance(zones, int):
        return zones
    return zones


def _compute_accuracy(trainer):
    """Compute accuracy from a trained MaxEntTrainer."""
    import numpy as np
    n_correct = 0
    n_total = 0
    for ld in trainer._line_data:
        if ld["observed"].sum() == 0:
            continue
        n_total += 1
        probs = trainer._softmax_probs(ld["viols"], trainer._weights)
        if int(np.argmax(probs)) == int(np.argmax(ld["observed"])):
            n_correct += 1
    return n_correct / n_total if n_total > 0 else 0.0, n_total


# --- Endpoints ---

@app.get("/api/meter/defaults", response_model=MeterDefaultsResponse)
def meter_defaults():
    from prosodic.parsing.meter import Meter
    m = Meter()
    all_c = list(get_all_constraints().keys())
    descs = get_constraint_descriptions()
    return MeterDefaultsResponse(
        all_constraints=all_c,
        constraint_descriptions=descs,
        defaults=MeterDefaults(
            constraints=list(m.constraints.keys()) if isinstance(m.constraints, dict) else list(m.constraints),
            max_s=m.max_s,
            max_w=m.max_w,
            resolve_optionality=m.resolve_optionality,
        ),
    )


@app.get("/api/corpora", response_model=CorpusListResponse)
def list_corpora():
    corpora_dir = os.path.normpath(CORPORA_DIR)
    files = []
    for path in sorted(globmod.glob(os.path.join(corpora_dir, "**", "*.txt"), recursive=True)):
        name = os.path.basename(path)
        parts = name.split(".")
        lang = parts[0] if len(parts) >= 2 else "?"
        with open(path, encoding="utf-8", errors="ignore") as f:
            num_lines = sum(1 for line in f if line.strip())
        rel_path = os.path.relpath(path, corpora_dir)
        files.append(CorpusFile(name=name, path=rel_path, lang=lang, num_lines=num_lines))
    return CorpusListResponse(files=files)


@app.get("/api/corpora/read")
def read_corpus(path: str):
    corpora_dir = os.path.normpath(CORPORA_DIR)
    full_path = os.path.normpath(os.path.join(corpora_dir, path))
    if not full_path.startswith(corpora_dir):
        raise HTTPException(status_code=400, detail="Invalid path")
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    with open(full_path, encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return {"text": text, "name": os.path.basename(full_path)}


@app.post("/api/parse")
def parse_text(req: dict):
    """Parse text and return rows with server-rendered HTML."""
    text_str = req.get('text', '').strip()
    if not text_str:
        raise HTTPException(status_code=400, detail="No text provided")

    from prosodic.parsing.vectorized import parse_batch
    from prosodic.parsing.meter import Meter

    lines = text_str.split('\n')[:linelim]
    text_str = '\n'.join(lines)
    syntax = req.get('syntax', False)
    syntax_model = req.get('syntax_model') or DEFAULT_SYNTAX_MODEL
    meter_kwargs = _build_meter_kwargs(
        req.get('constraints'), req.get('max_s', 2),
        req.get('max_w', 2), req.get('resolve_optionality', True))

    t0 = time.time()
    t = get_text(text_str, syntax=syntax, syntax_model=syntax_model)
    meter = Meter(**meter_kwargs)

    # Apply zone weights from MaxEnt if provided
    zw = req.get('zone_weights')
    if zw:
        meter.zone_weights = zw
        meter.zones = _normalize_zones(req.get('zones', 3))

    rows, num_lines, prose_mode = _parse_and_build_rows(t, meter)
    elapsed = time.time() - t0

    return {
        'rows': rows,
        'elapsed': round(elapsed, 3),
        'num_lines': num_lines,
        'prose_mode': prose_mode,
        'constraints': list(meter.constraints.keys()),
    }


def _parse_viol_stats(p):
    """Extract violation stats from a Parse: num_sylls, num_viols, per-constraint counts."""
    num_sylls = 0
    num_viols = 0
    viols = {}
    for pos in p.positions:
        for slot in pos.children:
            num_sylls += 1
            for k, v in (getattr(slot, 'viold', {}) or {}).items():
                try:
                    vi = int(v)
                except (TypeError, ValueError):
                    vi = 0
                viols[k] = viols.get(k, 0) + vi
                num_viols += vi
    return num_sylls, num_viols, viols


def _parse_and_build_rows(t, meter):
    """Parse lines + (for any long line) its lineparts. Return combined rows,
    sorted by line_num, rank. Returns (rows, num_lines, prose_mode_flag).
    """
    from prosodic.parsing.vectorized import parse_batch

    long_lnums = _long_line_nums(t)
    prose_mode = len(long_lnums) > 0

    # Pass 1: parse short lines normally
    short_lines = [ln for ln in t.lines if ln.num not in long_lnums]
    if short_lines:
        meter.parse_unit = 'line'
        results = parse_batch(short_lines, meter)
        for i, (wt, pl) in enumerate(results):
            if pl is None:
                continue
            pl.parent = wt
            wt._parses = pl
            short_lines[i]._parses = pl

    # Pass 2: for long lines, parse their lineparts (with optional syntax sub-split)
    from collections import OrderedDict
    long_lineparts_by_line = OrderedDict()  # line_num -> [(unit, ParseList|None), ...]
    if long_lnums:
        raw_lineparts = [lp for lp in t.lineparts if lp[0].line_num in long_lnums]
        # Expand any over-cap lineparts into syntax-derived sub-units when
        # spaCy is enabled on the text.
        use_syntax = getattr(t, '_syntax', False)
        expanded = []  # list of (line_num, unit)
        for lp in raw_lineparts:
            if lp.num_sylls > MAX_SYLL_IN_PARSE_UNIT and use_syntax:
                subs = _syntax_subsplit(lp, t)
            else:
                subs = [lp]
            for u in subs:
                expanded.append((lp[0].line_num, u))

        units_to_parse = [u for _, u in expanded]
        if units_to_parse:
            meter.parse_unit = 'linepart'
            lp_results = parse_batch(units_to_parse, meter)
            for i, (ln, u) in enumerate(expanded):
                long_lineparts_by_line.setdefault(ln, []).append((u, None))
            for i, (wt, pl) in enumerate(lp_results):
                if pl is None:
                    continue
                pl.parent = wt
                wt._parses = pl
                units_to_parse[i]._parses = pl
                ln = expanded[i][0]
                for j, (u_in_list, _) in enumerate(long_lineparts_by_line[ln]):
                    if u_in_list is units_to_parse[i]:
                        long_lineparts_by_line[ln][j] = (u_in_list, pl)
                        break

    rows = []
    # Short lines: one row per unbounded parse
    for line in short_lines:
        pl = getattr(line, '_parses', None)
        if not pl:
            continue
        unbounded = pl.unbounded if hasattr(pl, 'unbounded') else []
        has_zone = hasattr(pl, '_scores') and pl._scores is not None
        for pi, p in enumerate(unbounded):
            score = float(pl._scores[pi]) if has_zone and pi < len(pl._scores) else p.score
            num_sylls, num_viols, viols = _parse_viol_stats(p)
            rows.append({
                'line_num': line.num,
                'rank': pi + 1,
                'line_text': line.txt.strip(),
                'parse_html': render_parse_html(p, line),
                'meter_str': p.meter_str,
                'score': round(score, 2),
                'num_unbounded': pl.num_unbounded,
                'num_sylls': num_sylls,
                'num_viols': num_viols,
                'viols': viols,
            })

    # Long lines: aggregate lineparts into one row per line
    if long_lineparts_by_line:
        rows.extend(_aggregate_lineparts(long_lineparts_by_line, render_parse_html))

    rows.sort(key=lambda r: (r['line_num'], r['rank']))
    num_lines = len({r['line_num'] for r in rows})
    return rows, num_lines, prose_mode


@app.post("/api/parse/export")
def parse_export(req: dict):
    """Parse text and export per-line stats as CSV, TSV, or JSON.

    Uses the same prose-fallback parsing as /api/parse. Returns one row per
    line with best-parse stats + mean-over-unbounded stats.
    """
    text_str = req.get('text', '').strip()
    if not text_str:
        raise HTTPException(status_code=400, detail="No text provided")

    fmt = (req.get('format') or 'csv').lower()
    if fmt not in ('csv', 'tsv', 'json'):
        raise HTTPException(status_code=400, detail="format must be csv, tsv, or json")

    from prosodic.parsing.meter import Meter

    input_lines = text_str.split('\n')[:linelim]
    text_str = '\n'.join(input_lines)
    syntax = req.get('syntax', False)
    syntax_model = req.get('syntax_model') or DEFAULT_SYNTAX_MODEL
    meter_kwargs = _build_meter_kwargs(
        req.get('constraints'), req.get('max_s', 2),
        req.get('max_w', 2), req.get('resolve_optionality', True))

    t = get_text(text_str, syntax=syntax, syntax_model=syntax_model)
    meter = Meter(**meter_kwargs)
    zw = req.get('zone_weights')
    if zw:
        meter.zone_weights = zw
        meter.zones = _normalize_zones(req.get('zones', 3))

    # Parse (handles prose fallback)
    display_rows, _, _ = _parse_and_build_rows(t, meter)

    # Build export rows: one per line (best-parse only) + unbounded averages.
    # Group display_rows by line_num, take rank=1.
    best_by_line = {}
    for r in display_rows:
        if r.get('rank', 1) == 1 and r['line_num'] not in best_by_line:
            best_by_line[r['line_num']] = r

    # For unbounded averages, walk parse lists on short lines.
    # For prose (long) lines, best-only (no per-linepart unbounded aggregation).
    long_lnums = _long_line_nums(t)

    def _unbounded_sums(pl):
        """Sum score, viols, sylls across all unbounded parses of a ParseList."""
        unbounded = pl.unbounded if hasattr(pl, 'unbounded') else []
        has_zone = hasattr(pl, '_scores') and pl._scores is not None
        total_score = 0.0
        total_viols = 0
        total_sylls = 0
        viol_sums = {}
        for pi, p in enumerate(unbounded):
            sc = float(pl._scores[pi]) if has_zone and pi < len(pl._scores) else p.score
            total_score += sc
            ns, nv, vs = _parse_viol_stats(p)
            total_sylls += ns
            total_viols += nv
            for k, v in vs.items():
                viol_sums[k] = viol_sums.get(k, 0) + v
        return total_score, total_viols, total_sylls, viol_sums

    rows = []
    all_viol_keys = set()
    for line_num, best in sorted(best_by_line.items()):
        viols = best.get('viols') or {}
        all_viol_keys.update(viols.keys())

        row = {
            'line_num': line_num,
            'line_text': best['line_text'],
            'num_sylls': best.get('num_sylls', 0),
            'ambiguity': best.get('num_unbounded', 1),
            'meter_str': best['meter_str'].replace('<br>', ' | '),
            'score': best['score'],
            'num_viols': best.get('num_viols', 0),
        }
        for k, v in viols.items():
            row[f'*{k}'] = v
            all_viol_keys.add(k)

        # Sum across all unbounded parses
        unb_score = 0.0
        unb_viols = 0
        unb_sylls = 0
        unb_vs = {}

        if line_num not in long_lnums:
            # Short line: single parse list on the line entity
            line_ent = next((l for l in t.lines if l.num == line_num), None)
            pl = getattr(line_ent, '_parses', None) if line_ent else None
            if pl:
                s, v, sy, vs = _unbounded_sums(pl)
                unb_score += s
                unb_viols += v
                unb_sylls += sy
                for k, val in vs.items():
                    unb_vs[k] = unb_vs.get(k, 0) + val
        else:
            # Long (prose) line: sum across lineparts' parse lists
            for lp in t.lineparts:
                if lp[0].line_num != line_num:
                    continue
                pl = getattr(lp, '_parses', None)
                if not pl:
                    continue
                s, v, sy, vs = _unbounded_sums(pl)
                unb_score += s
                unb_viols += v
                unb_sylls += sy
                for k, val in vs.items():
                    unb_vs[k] = unb_vs.get(k, 0) + val

        row['score_unbounded'] = round(unb_score, 4)
        row['num_viols_unbounded'] = round(unb_viols, 4) if unb_viols else row.get('num_viols', 0)
        row['num_sylls_unbounded'] = unb_sylls if unb_sylls else row.get('num_sylls', 0)
        for k, val in unb_vs.items():
            row[f'*{k}_unbounded'] = round(val, 4)
            all_viol_keys.add(k)
        rows.append(row)

    # Rename ambiguity → num_parses
    for r in rows:
        r['num_parses'] = r.pop('ambiguity', 1)

    sorted_constraints = sorted(all_viol_keys)
    best_viol_cols = [f'*{k}' for k in sorted_constraints]
    unb_viol_cols = [f'*{k}_unbounded' for k in sorted_constraints]
    cols = [
        'line_num', 'line_text', 'meter_str',
        'num_sylls', 'num_viols', 'num_parses', 'score',
        *best_viol_cols,
        'num_sylls_unbounded', 'num_viols_unbounded', 'score_unbounded',
        *unb_viol_cols,
    ]
    viol_cols = best_viol_cols + unb_viol_cols
    for r in rows:
        for c in viol_cols:
            r.setdefault(c, 0)

    if fmt == 'json':
        return Response(
            content=json.dumps(rows),
            media_type='application/json',
            headers={'Content-Disposition': 'attachment; filename="prosodic-parse.json"'},
        )

    # CSV / TSV
    import csv as _csv
    import io
    buf = io.StringIO()
    delim = '\t' if fmt == 'tsv' else ','
    writer = _csv.DictWriter(buf, fieldnames=cols, delimiter=delim, extrasaction='ignore')
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    filename = f"prosodic-parse.{fmt}"
    return Response(
        content=buf.getvalue(),
        media_type='text/tab-separated-values' if fmt == 'tsv' else 'text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@app.post("/api/parse/stream")
async def parse_stream(req: dict):
    """SSE: stream progress messages, then results in batches."""
    text_str = req.get('text', '').strip()
    if not text_str:
        raise HTTPException(status_code=400, detail="No text provided")

    from prosodic.parsing.vectorized import parse_batch
    from prosodic.parsing.meter import Meter

    input_lines = text_str.split('\n')[:linelim]
    text_str = '\n'.join(input_lines)
    syntax = req.get('syntax', False)
    syntax_model = req.get('syntax_model') or DEFAULT_SYNTAX_MODEL
    meter_kwargs = _build_meter_kwargs(
        req.get('constraints'), req.get('max_s', 2),
        req.get('max_w', 2), req.get('resolve_optionality', True))

    def sse(data):
        return f"data: {json.dumps(data)}\n\n"

    async def event_stream():
        yield sse({'phase': 'progress', 'message': f'Tokenizing {len(input_lines)} lines...'})
        await asyncio.sleep(0)

        t0 = time.time()
        t = get_text(text_str, syntax=syntax, syntax_model=syntax_model)

        yield sse({'phase': 'progress', 'message': f'Parsing {len(t.lines)} lines...'})
        await asyncio.sleep(0)

        meter = Meter(**meter_kwargs)
        zw = req.get('zone_weights')
        if zw:
            meter.zone_weights = zw
            meter.zones = _normalize_zones(req.get('zones', 3))

        long_lnums = _long_line_nums(t)
        if long_lnums:
            yield sse({'phase': 'progress',
                       'message': f'{len(long_lnums)} long line(s) detected — parsing by linepart...'})
            await asyncio.sleep(0)

        rows, num_lines, prose_mode = _parse_and_build_rows(t, meter)

        parse_elapsed = time.time() - t0
        yield sse({'phase': 'progress', 'message': f'Parsed in {parse_elapsed:.1f}s. Rendering...'})
        await asyncio.sleep(0)

        BATCH_SIZE = 50
        batch = []
        for r in rows:
            batch.append(r)
            if len(batch) >= BATCH_SIZE:
                yield sse({'phase': 'rows', 'rows': batch})
                batch = []
                await asyncio.sleep(0)

        if batch:
            yield sse({'phase': 'rows', 'rows': batch})

        elapsed = time.time() - t0
        yield sse({'phase': 'done', 'elapsed': round(elapsed, 3), 'num_lines': num_lines, 'prose_mode': prose_mode, 'constraints': list(meter.constraints.keys())})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/maxent/fit", response_model=MaxEntFitResponse)
def maxent_fit(req: MaxEntFitRequest):
    from prosodic.parsing.meter import Meter

    text_str = req.text.strip()
    if not text_str:
        raise HTTPException(status_code=400, detail="No text provided")

    lines = text_str.split('\n')[:linelim]
    text_str = '\n'.join(lines)
    zones = _normalize_zones(req.zones)
    meter_kwargs = _build_meter_kwargs(req.constraints, req.max_s, req.max_w, req.resolve_optionality)
    meter = Meter(**meter_kwargs)

    t = get_text(text_str, syntax=req.syntax)
    t0 = time.time()
    meter.fit(t, req.target_scansion, zones=zones, regularization=req.regularization)
    elapsed = time.time() - t0

    weights = meter.zone_weights or {}
    sorted_weights = sorted(weights.items(), key=lambda x: -x[1])

    accuracy, num_matched = _compute_accuracy(meter._trainer)
    import numpy as np
    neg_ll, _ = meter._trainer._neg_log_likelihood_and_grad(meter._trainer._weights)
    num_lines = len(meter._trainer._line_data)

    return MaxEntFitResponse(
        weights=[WeightEntry(name=n, weight=round(w, 4)) for n, w in sorted_weights if w > 0.001],
        elapsed=round(elapsed, 3),
        config=dict(
            target=req.target_scansion,
            zones=str(zones) if zones is not None else "none",
            regularization=req.regularization,
        ),
        accuracy=round(accuracy, 4),
        num_lines=num_lines,
        num_matched=num_matched,
        log_likelihood=round(-neg_ll, 2),
    )


@app.post("/api/maxent/fit-annotations", response_model=MaxEntFitResponse)
async def maxent_fit_annotations(
    annotations_file: UploadFile = File(...),
    constraints: Optional[str] = Form(None),
    max_s: int = Form(2),
    max_w: int = Form(2),
    resolve_optionality: bool = Form(True),
    zones: str = Form("3"),
    regularization: float = Form(100.0),
    syntax: bool = Form(False),
):
    from prosodic.parsing.meter import Meter
    import pandas as pd
    import io

    content = await annotations_file.read()
    df = pd.read_csv(io.BytesIO(content), sep='\t')

    if 'text' not in df.columns:
        col_map = {}
        for col in df.columns:
            cl = col.lower()
            if 'line' in cl or 'text' in cl:
                col_map['text'] = col
            elif 'parse' in cl or 'scan' in cl:
                col_map['scansion'] = col
            elif 'freq' in cl or 'count' in cl:
                col_map['frequency'] = col
        if 'text' not in col_map:
            raise HTTPException(status_code=400, detail=f"Cannot find text column. Columns: {list(df.columns)}")
        df = df.rename(columns=col_map)
    if 'frequency' not in df.columns:
        df['frequency'] = 1.0
    if 'scansion' not in df.columns:
        raise HTTPException(status_code=400, detail=f"Cannot find scansion column. Columns: {list(df.columns)}")

    annotations = list(zip(df['text'], df['scansion'], df['frequency']))

    constraint_list = constraints.split(',') if constraints else None
    zones_val = _normalize_zones(zones)
    meter_kwargs = _build_meter_kwargs(constraint_list, max_s, max_w, resolve_optionality)
    meter = Meter(**meter_kwargs)

    text_obj = None
    if syntax:
        unique_lines = list(dict.fromkeys(a[0] for a in annotations))
        text_obj = TextModel("\n".join(unique_lines), syntax=True)

    t0 = time.time()
    meter.fit_annotations(annotations, zones=zones_val, regularization=regularization, text=text_obj)
    elapsed = time.time() - t0

    weights = meter.zone_weights or {}
    sorted_weights = sorted(weights.items(), key=lambda x: -x[1])

    accuracy, num_matched = _compute_accuracy(meter._trainer)
    import numpy as np
    neg_ll, _ = meter._trainer._neg_log_likelihood_and_grad(meter._trainer._weights)
    num_lines = len(meter._trainer._line_data)

    return MaxEntFitResponse(
        weights=[WeightEntry(name=n, weight=round(w, 4)) for n, w in sorted_weights if w > 0.001],
        elapsed=round(elapsed, 3),
        config=dict(
            target="(from annotations)",
            zones=str(zones_val) if zones_val is not None else "none",
            regularization=regularization,
        ),
        accuracy=round(accuracy, 4),
        num_lines=num_lines,
        num_matched=num_matched,
        log_likelihood=round(-neg_ll, 2),
    )


@app.post("/api/maxent/reparse", response_model=MaxEntReparseResponse)
def maxent_reparse(req: MaxEntReparseRequest):
    from prosodic.parsing.meter import Meter
    from prosodic.parsing.vectorized import parse_batch_from_df

    text_str = req.text.strip()
    if not text_str:
        raise HTTPException(status_code=400, detail="No text provided")

    lines = text_str.split('\n')[:linelim]
    text_str = '\n'.join(lines)
    zones = _normalize_zones(req.zones)
    meter_kwargs = _build_meter_kwargs(req.constraints, req.max_s, req.max_w, req.resolve_optionality)
    meter = Meter(**meter_kwargs)

    t = get_text(text_str, syntax=req.syntax)
    meter.fit(t, req.target_scansion, zones=zones, regularization=req.regularization)

    t0 = time.time()
    results = parse_batch_from_df(t._syll_df, meter)

    rows = []
    text_lines = t.lines
    for line in text_lines:
        ln = line._num if line._num else getattr(line.children[0], 'line_num', None) if line.children else None
        if ln is None:
            continue
        lpl = results.get(ln)
        if not lpl or not hasattr(lpl, 'best_parse') or not lpl.best_parse:
            continue
        bp = lpl.best_parse
        rows.append(ReparseRow(
            line_num=line.num,
            line_txt=line.txt.strip(),
            meter_str=bp.meter_str,
            score=round(bp.score, 1),
        ))

    elapsed = time.time() - t0
    return MaxEntReparseResponse(rows=rows, elapsed=round(elapsed, 3))


@app.post("/api/parse/line")
def parse_line(req: dict):
    """Parse a single line and return ALL scansions sorted by score."""
    text_str = req.get('text', '').strip()
    if not text_str:
        raise HTTPException(status_code=400, detail="No text provided")

    from prosodic.parsing.vectorized import parse_batch
    from prosodic.parsing.meter import Meter

    # Take first line only
    line_text = text_str.split('\n')[0].strip()
    if not line_text:
        raise HTTPException(status_code=400, detail="Empty line")

    syntax = req.get('syntax', False)
    syntax_model = req.get('syntax_model') or DEFAULT_SYNTAX_MODEL
    meter_kwargs = _build_meter_kwargs(
        req.get('constraints'), req.get('max_s', 2),
        req.get('max_w', 2), req.get('resolve_optionality', True))

    t0 = time.time()
    t = get_text(line_text, syntax=syntax)
    meter = Meter(**meter_kwargs)

    zw = req.get('zone_weights')
    if zw:
        meter.zone_weights = zw
        meter.zones = _normalize_zones(req.get('zones', 3))

    text_lines = t.lines
    if not text_lines:
        return {'parses': [], 'elapsed': 0, 'line_text': line_text, 'parts': []}

    def _build_parses_for_pl(pl, context_unit):
        """Build parse detail dicts from a ParseList."""
        import numpy as np
        if not pl or not hasattr(pl, '_all_scores') or pl._all_scores is None:
            return []
        sorted_indices = np.argsort(pl._all_scores)
        out = []
        for pi, idx in enumerate(sorted_indices):
            p = pl._get_parse(int(idx), is_bounded=not pl._unbounded_mask[idx])
            score = round(float(pl._all_scores[idx]), 2)
            is_bounded = not pl._unbounded_mask[idx]
            positions = []
            for pos in p.positions:
                slots = []
                for slot in pos.children:
                    unit = slot.unit
                    slots.append({
                        'text': unit.txt,
                        'is_stressed': bool(unit.is_stressed),
                        'is_prom': bool(slot.is_prom),
                        'violations': list(slot.violset),
                    })
                positions.append({
                    'mtr': 's' if pos.is_prom else 'w',
                    'slots': slots,
                })
            viol_counts = {}
            for pos in positions:
                for s in pos['slots']:
                    for v in s['violations']:
                        viol_counts[v] = viol_counts.get(v, 0) + 1
            out.append({
                'rank': pi + 1,
                'parse_html': render_parse_html(p, context_unit),
                'meter_str': p.meter_str,
                'score': score,
                'is_bounded': is_bounded,
                'positions': positions,
                'num_viols': sum(len(s['violations']) for pos in positions for s in pos['slots']),
                'viol_summary': viol_counts,
            })
        return out

    long_lnums = _long_line_nums(t)
    is_long = bool(long_lnums)

    if not is_long:
        # Normal single-line parse
        results = parse_batch(text_lines, meter)
        for i, (wt, pl) in enumerate(results):
            pl.parent = wt
            wt._parses = pl
            text_lines[i]._parses = pl
        line = text_lines[0]
        parses = _build_parses_for_pl(line._parses, line)
        elapsed = time.time() - t0
        num_unbounded = sum(1 for p in parses if not p['is_bounded'])
        return {
            'parses': parses,
            'elapsed': round(elapsed, 3),
            'line_text': line_text,
            'num_parses': len(parses),
            'num_unbounded': num_unbounded,
            'parts': [],
        }
    else:
        # Multi-part: parse each linepart, return per-part results
        use_syntax = getattr(t, '_syntax', False)
        raw_lineparts = list(t.lineparts)
        expanded = []
        for lp in raw_lineparts:
            if lp.num_sylls > MAX_SYLL_IN_PARSE_UNIT and use_syntax:
                expanded.extend(_syntax_subsplit(lp, t))
            else:
                expanded.append(lp)

        meter.parse_unit = 'linepart'
        units_to_parse = [u for u in expanded if u.num_sylls >= 2]
        if units_to_parse:
            lp_results = parse_batch(units_to_parse, meter)
            for i, (wt, pl) in enumerate(lp_results):
                if pl is None:
                    continue
                pl.parent = wt
                wt._parses = pl
                units_to_parse[i]._parses = pl

        parts = []
        for lp in expanded:
            pl = getattr(lp, '_parses', None)
            part_parses = _build_parses_for_pl(pl, lp) if pl else []
            num_unb = sum(1 for p in part_parses if not p['is_bounded'])
            parts.append({
                'part_text': lp.txt.strip(),
                'num_sylls': lp.num_sylls,
                'parses': part_parses,
                'num_parses': len(part_parses),
                'num_unbounded': num_unb,
            })

        elapsed = time.time() - t0
        return {
            'parses': [],
            'elapsed': round(elapsed, 3),
            'line_text': line_text,
            'num_parses': sum(p['num_parses'] for p in parts),
            'num_unbounded': sum(p['num_unbounded'] for p in parts),
            'parts': parts,
        }


# Serve built SvelteKit frontend
if os.path.isdir(STATIC_BUILD_DIR):
    @app.get("/{path:path}")
    async def serve_frontend(path: str = ""):
        file_path = os.path.join(STATIC_BUILD_DIR, path)
        if path and os.path.isfile(file_path):
            return FileResponse(file_path)
        index = os.path.join(STATIC_BUILD_DIR, "index.html")
        if os.path.isfile(index):
            return FileResponse(index)
        raise HTTPException(status_code=404, detail="Frontend not built")
else:
    @app.get("/")
    async def no_frontend():
        return {"message": "Frontend not built. Run 'npm run build' in prosodic/web/frontend/"}


def main(port=None, host=None, debug=True, dev=False, **kwargs):
    import uvicorn
    if port is None:
        port = 8181
    if host is None:
        host = "127.0.0.1"
    if debug:
        logmap.enable()

    if dev:
        _run_dev(host=host, port=port, debug=debug)
        return

    uvicorn.run(app, host=host, port=port, log_level="info" if debug else "warning")


def _run_dev(host, port, debug):
    """Run backend with uvicorn --reload + frontend vite build --watch.

    Runs uvicorn in a subprocess (rather than uvicorn.run in-process) so its
    multiprocessing-based reloader starts from a clean entry point on macOS.
    """
    import atexit
    import signal
    import subprocess

    frontend_dir = os.path.join(PATH_WEB, "frontend")
    procs = []

    def cleanup(*_):
        for p in procs:
            if p.poll() is None:
                try:
                    p.terminate()
                except Exception:
                    pass
        for p in procs:
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()

    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda *_: (cleanup(), sys.exit(0)))
    signal.signal(signal.SIGTERM, lambda *_: (cleanup(), sys.exit(0)))

    if os.path.isdir(os.path.join(frontend_dir, "node_modules")):
        print("[dev] starting frontend watcher (vite build --watch)...")
        procs.append(subprocess.Popen(
            ["npm", "run", "build", "--", "--watch"],
            cwd=frontend_dir,
        ))
    else:
        print(
            "[dev] frontend/node_modules not found — skipping frontend watch. "
            f"Run `cd {frontend_dir} && npm install` to enable."
        )

    print("[dev] starting uvicorn with --reload (watching prosodic/)...")
    uvicorn_proc = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "prosodic.web.api:app",
        "--host", str(host),
        "--port", str(port),
        "--reload",
        "--reload-dir", PATH_PROSODIC,
        "--log-level", "info" if debug else "warning",
    ])
    procs.append(uvicorn_proc)

    try:
        uvicorn_proc.wait()
    finally:
        cleanup()


if __name__ == "__main__":
    main()
