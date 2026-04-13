import os, sys, json, time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
from flask import Flask, render_template, request, Response, stream_with_context

app = Flask(__name__)
app.config['SECRET_KEY'] = '0f m@ns dis0b3d13nc3'

linelim = 1000
_text_cache = {}


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


def _extract_meter_kwargs(form):
    """Extract meter configuration from form data."""
    constraints = []
    meter_kwargs = {}
    for key in form:
        if key.startswith('*'):
            constraints.append(key[1:])
        elif key in ('max_s', 'max_w'):
            meter_kwargs[key] = int(form[key])
        elif key == 'resolve_optionality':
            meter_kwargs[key] = True
    if 'resolve_optionality' not in form:
        meter_kwargs['resolve_optionality'] = False
    if constraints:
        meter_kwargs['constraints'] = constraints
    return meter_kwargs


def _parse_text(text_str, meter_kwargs, syntax=False):
    """Parse text and return list of row dicts for the results table."""
    from prosodic.parsing.vectorized import parse_batch
    from prosodic.parsing.meter import Meter

    t = get_text(text_str, syntax=syntax)
    meter = Meter(**meter_kwargs)
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
        for pi, p in enumerate(unbounded):
            rows.append({
                'line_num': line.num,
                'rank': pi + 1,
                'parse_html': render_parse_html(p),
                'meter_str': p.meter_str,
                'score': round(p.score, 1),
                'num_unbounded': pl.num_unbounded,
            })
    return rows, t, meter


@app.route("/")
def index():
    from prosodic.parsing.meter import Meter
    m = Meter()
    return render_template(
        "index.html",
        all_constraints=list(get_all_constraints().keys()),
        constraint_descs=get_constraint_descriptions(),
        **m.attrs,
    )


@app.route("/parse", methods=["POST"])
def parse():
    text_str = request.form.get('text', '').strip()
    if not text_str:
        return '<div class="empty">No text provided</div>'

    lines = text_str.split('\n')[:linelim]
    text_str = '\n'.join(lines)
    syntax = 'syntax' in request.form
    meter_kwargs = _extract_meter_kwargs(request.form)

    t0 = time.time()
    rows, text_obj, meter = _parse_text(text_str, meter_kwargs, syntax=syntax)
    elapsed = time.time() - t0

    return render_template(
        "fragments/parse_results.html",
        rows=rows,
        elapsed=elapsed,
        num_lines=len([l for l in text_obj.lines if l._parses]),
    )


@app.route("/maxent/fit", methods=["POST"])
def maxent_fit():
    from prosodic.parsing.meter import Meter

    text_str = request.form.get('text', '').strip()
    if not text_str:
        return '<div class="empty">No text provided</div>'

    target = request.form.get('target_scansion', 'wswswswsws').strip().lower()
    zones = request.form.get('zones', '3')
    zones = int(zones) if zones.isdigit() else (None if zones == 'none' else zones)
    regularization = float(request.form.get('regularization', '100.0'))
    syntax = 'syntax' in request.form

    lines = text_str.split('\n')[:linelim]
    text_str = '\n'.join(lines)

    meter_kwargs = _extract_meter_kwargs(request.form)
    meter = Meter(**meter_kwargs)

    t = get_text(text_str, syntax=syntax)
    t0 = time.time()
    meter.fit(t, target, zones=zones, regularization=regularization)
    elapsed = time.time() - t0

    weights = meter.zone_weights or {}
    sorted_weights = sorted(weights.items(), key=lambda x: -x[1])

    return render_template(
        "fragments/maxent_results.html",
        weights=sorted_weights,
        elapsed=elapsed,
        zones=zones,
        regularization=regularization,
        target=target,
        num_lines=len(t.lines),
    )


@app.route("/maxent/fit-annotations", methods=["POST"])
def maxent_fit_annotations():
    from prosodic.parsing.meter import Meter

    file = request.files.get('annotations_file')
    if not file:
        return '<div class="empty">No file uploaded</div>'

    import pandas as pd
    df = pd.read_csv(file, sep='\t')
    # expect columns: text, scansion, frequency (or auto-detect)
    if 'text' not in df.columns:
        # try common column names
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
            return f'<div class="empty">Cannot find text column. Columns: {list(df.columns)}</div>'
        df = df.rename(columns=col_map)
    if 'frequency' not in df.columns:
        df['frequency'] = 1.0
    if 'scansion' not in df.columns:
        return f'<div class="empty">Cannot find scansion column. Columns: {list(df.columns)}</div>'

    annotations = list(zip(df['text'], df['scansion'], df['frequency']))

    zones = request.form.get('zones', '3')
    zones = int(zones) if zones.isdigit() else (None if zones == 'none' else zones)
    regularization = float(request.form.get('regularization', '100.0'))
    syntax = 'syntax' in request.form

    meter_kwargs = _extract_meter_kwargs(request.form)
    meter = Meter(**meter_kwargs)

    # optionally build syntax-enabled text for training
    text_obj = None
    if syntax:
        unique_lines = list(dict.fromkeys(a[0] for a in annotations))
        text_obj = TextModel("\n".join(unique_lines), syntax=True)

    t0 = time.time()
    meter.fit_annotations(annotations, zones=zones, regularization=regularization, text=text_obj)
    elapsed = time.time() - t0

    weights = meter.zone_weights or {}
    sorted_weights = sorted(weights.items(), key=lambda x: -x[1])

    return render_template(
        "fragments/maxent_results.html",
        weights=sorted_weights,
        elapsed=elapsed,
        zones=zones,
        regularization=regularization,
        target="(from annotations)",
        num_lines=len(annotations),
    )


@app.route("/maxent/reparse", methods=["POST"])
def maxent_reparse():
    """Re-parse the text using stored MaxEnt weights."""
    from prosodic.parsing.meter import Meter

    text_str = request.form.get('text', '').strip()
    if not text_str:
        return '<div class="empty">No text provided</div>'

    lines = text_str.split('\n')[:linelim]
    text_str = '\n'.join(lines)
    syntax = 'syntax' in request.form

    # reconstruct meter with zone weights from form
    meter_kwargs = _extract_meter_kwargs(request.form)
    meter = Meter(**meter_kwargs)

    target = request.form.get('target_scansion', 'wswswswsws').strip().lower()
    zones = request.form.get('zones', '3')
    zones = int(zones) if zones.isdigit() else (None if zones == 'none' else zones)
    regularization = float(request.form.get('regularization', '100.0'))

    t = get_text(text_str, syntax=syntax)
    meter.fit(t, target, zones=zones, regularization=regularization)

    t0 = time.time()
    rows, text_obj, meter = _parse_text(text_str, meter_kwargs, syntax=syntax)
    # re-parse with the fitted meter
    from prosodic.parsing.vectorized import parse_batch_from_df
    results = parse_batch_from_df(t._syll_df, meter)

    # build rows from DF results (no entity HTML, use meter_str comparison)
    rows_fitted = []
    text_lines = t.lines
    for line in text_lines:
        ln = line._num if line._num else getattr(line.children[0], 'line_num', None) if line.children else None
        if ln is None:
            continue
        lpl = results.get(ln)
        if not lpl or not hasattr(lpl, 'best_parse') or not lpl.best_parse:
            continue
        bp = lpl.best_parse
        rows_fitted.append({
            'line_num': line.num,
            'line_txt': line.txt.strip(),
            'meter_str': bp.meter_str,
            'score': round(bp.score, 1),
        })

    elapsed = time.time() - t0
    return render_template(
        "fragments/reparse_results.html",
        rows=rows_fitted,
        elapsed=elapsed,
    )


def main(port=None, host=None, debug=True, **kwargs):
    if port is None:
        port = 5111
    if debug:
        logmap.enable()
    app.run(port=port, debug=debug, host=host, **kwargs)


if __name__ == "__main__":
    main()
