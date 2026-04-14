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
from fastapi.responses import FileResponse, StreamingResponse
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


def render_parse_html(parse):
    """Render a parse as HTML with meter/stress/violation CSS classes."""
    parts = []
    last_word_id = None
    for pos in parse.positions:
        for slot in pos.children:
            unit = slot.unit
            word_id = None
            if hasattr(unit, 'parent') and unit.parent is not None:
                word_id = id(unit.parent)
            if last_word_id is not None and word_id != last_word_id:
                parts.append(' ')
            last_word_id = word_id

            mtr = 'mtr_s' if slot.is_prom else 'mtr_w'
            strs = 'str_s' if unit.is_stressed else 'str_w'
            viols = list(slot.violset)
            viol = 'viol_y' if viols else 'viol_n'
            classes = f'{mtr} {strs} {viol}'
            if viols:
                tip = ', '.join(f'*{v}' for v in viols)
                parts.append(f'<span class="{classes}"><span class="tip">{tip}</span>{unit.txt}</span>')
            else:
                parts.append(f'<span class="{classes}">{unit.txt}</span>')
    return ''.join(parts)


def _build_meter_kwargs(constraints=None, max_s=2, max_w=2, resolve_optionality=True):
    kwargs = dict(max_s=max_s, max_w=max_w, resolve_optionality=resolve_optionality)
    if constraints:
        kwargs['constraints'] = constraints
    return kwargs


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
    meter_kwargs = _build_meter_kwargs(
        req.get('constraints'), req.get('max_s', 2),
        req.get('max_w', 2), req.get('resolve_optionality', True))

    t0 = time.time()
    t = get_text(text_str, syntax=syntax)
    meter = Meter(**meter_kwargs)

    # Apply zone weights from MaxEnt if provided
    zw = req.get('zone_weights')
    if zw:
        meter.zone_weights = zw
        meter.zones = _normalize_zones(req.get('zones', 3))

    text_lines = t.lines
    results = parse_batch(text_lines, meter)
    for i, (wt, pl) in enumerate(results):
        pl.parent = wt
        wt._parses = pl
        text_lines[i]._parses = pl

    rows = []
    for line in text_lines:
        pl = line._parses
        if not pl:
            continue
        unbounded = pl.unbounded if hasattr(pl, 'unbounded') else []
        has_zone_scores = hasattr(pl, '_scores') and pl._scores is not None
        for pi, p in enumerate(unbounded):
            score = float(pl._scores[pi]) if has_zone_scores and pi < len(pl._scores) else p.score
            rows.append({
                'line_num': line.num,
                'rank': pi + 1,
                'parse_html': render_parse_html(p),
                'meter_str': p.meter_str,
                'score': round(score, 2),
                'num_unbounded': pl.num_unbounded,
            })
    elapsed = time.time() - t0

    return {
        'rows': rows,
        'elapsed': round(elapsed, 3),
        'num_lines': len([l for l in text_lines if l._parses]),
    }


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
    meter_kwargs = _build_meter_kwargs(
        req.get('constraints'), req.get('max_s', 2),
        req.get('max_w', 2), req.get('resolve_optionality', True))

    def sse(data):
        return f"data: {json.dumps(data)}\n\n"

    async def event_stream():
        yield sse({'phase': 'progress', 'message': f'Tokenizing {len(input_lines)} lines...'})
        await asyncio.sleep(0)

        t0 = time.time()
        t = get_text(text_str, syntax=syntax)

        yield sse({'phase': 'progress', 'message': f'Parsing {len(t.lines)} lines...'})
        await asyncio.sleep(0)

        meter = Meter(**meter_kwargs)
        zw = req.get('zone_weights')
        if zw:
            meter.zone_weights = zw
            meter.zones = _normalize_zones(req.get('zones', 3))

        text_lines = t.lines
        results = parse_batch(text_lines, meter)
        for i, (wt, pl) in enumerate(results):
            pl.parent = wt
            wt._parses = pl
            text_lines[i]._parses = pl

        parse_elapsed = time.time() - t0
        yield sse({'phase': 'progress', 'message': f'Parsed in {parse_elapsed:.1f}s. Rendering...'})
        await asyncio.sleep(0)

        # Stream rows in batches
        num_lines = 0
        batch = []
        BATCH_SIZE = 50
        for line in text_lines:
            pl = line._parses
            if not pl:
                continue
            num_lines += 1
            unbounded = pl.unbounded if hasattr(pl, 'unbounded') else []
            has_zone_scores = hasattr(pl, '_scores') and pl._scores is not None
            for pi, p in enumerate(unbounded):
                score = float(pl._scores[pi]) if has_zone_scores and pi < len(pl._scores) else p.score
                batch.append({
                    'line_num': line.num,
                    'rank': pi + 1,
                    'parse_html': render_parse_html(p),
                    'meter_str': p.meter_str,
                    'score': round(score, 2),
                    'num_unbounded': pl.num_unbounded,
                })
            if len(batch) >= BATCH_SIZE:
                yield sse({'phase': 'rows', 'rows': batch})
                batch = []
                await asyncio.sleep(0)

        if batch:
            yield sse({'phase': 'rows', 'rows': batch})

        elapsed = time.time() - t0
        yield sse({'phase': 'done', 'elapsed': round(elapsed, 3), 'num_lines': num_lines})

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


def main(port=None, host=None, debug=True, **kwargs):
    import uvicorn
    if port is None:
        port = 8181
    if host is None:
        host = "127.0.0.1"
    if debug:
        logmap.enable()
    uvicorn.run(app, host=host, port=port, log_level="info" if debug else "warning")


if __name__ == "__main__":
    main()
