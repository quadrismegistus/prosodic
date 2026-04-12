import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_socketio import send, emit
from gevent import time as gtime

app = Flask(__name__)
app.config['SECRET_KEY'] = '0f m@ns dis0b3d13nc3'
socketio = SocketIO(app, ping_timeout=60 * 5, ping_interval=5)

linelim = 1000
_text_cache = {}


def get_text(txt):
    if txt not in _text_cache:
        _text_cache[txt] = TextModel(txt)
    return _text_cache[txt]


def render_parse_html(parse):
    """Render a parse as HTML with meter/stress/violation CSS classes."""
    parts = []
    last_word_id = None
    for pos in parse.positions:
        for slot in pos.children:
            # detect word boundary via syllable parent chain
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


@socketio.on('parse')
def parse(data):
    data = unjsonify(data)
    data = {
        d['name']: (
            int(d['value'])
            if d['value'].isdigit() and d['name'] != 'text' else d['value']
        )
        for d in data
    }
    text_str = data.pop('text')
    lines = text_str.split('\n')[:linelim]
    text_str = '\n'.join(lines)

    constraints = tuple(x[1:] for x in list(data.keys()) if x and x[0] == '*')
    for c in constraints:
        data.pop('*' + c)
    meter_kwargs = data
    meter_kwargs['constraints'] = constraints

    t = get_text(text_str)

    # parse with Entity-based path (needed for HTML rendering with word boundaries)
    from prosodic.parsing.vectorized import parse_batch
    from prosodic.parsing.meter import Meter
    meter = Meter(**meter_kwargs)
    text_lines = t.lines  # triggers entity construction
    results = parse_batch(text_lines, meter)
    # attach results to lines
    for i, (wt, pl) in enumerate(results):
        pl.parent = wt
        wt._parses = pl
        text_lines[i]._parses = pl

    started = time.time()
    numtoiter = len(text_lines)
    numrows = 0

    for i, line in enumerate(text_lines):
        pl = line._parses
        if not pl:
            continue

        data_out_l = []
        unbounded = pl.unbounded if hasattr(pl, 'unbounded') else []
        for pi, p in enumerate(unbounded):
            parse_html = render_parse_html(p)
            row = {
                'line_num': line.num,
                'rank': pi + 1,
                'parse_html': parse_html,
                'parse_txt': p.txt,
                'meter_str': p.meter_str,
                'score': round(p.score, 1),
                'num_sylls': p.num_sylls,
                'num_unbounded': pl.num_unbounded,
                'progress': (i + 1) / max(numtoiter, 1),
                'numdone': i + 1,
                'numtodo': numtoiter - (i + 1),
                'numlines': numtoiter,
            }
            data_out_l.append(row)
            numrows += 1

        gtime.sleep(.005)
        emit('parse_result', jsonify(data_out_l))

    gtime.sleep(.05)
    emit('parse_done', {'duration': time.time() - started, 'numrows': numrows})


@app.route("/")
def index():
    return render_template(
        "index.html",
        all_constraints=list(get_all_constraints().keys()),
        enumerate=enumerate,
        constraint_descs=get_constraint_descriptions(),
        **Meter().attrs
    )


def main(port=None, host=None, debug=True, **kwargs):
    if port is None: port = 5111
    if debug: logmap.enable()
    socketio.run(app, port=port, debug=debug, host=host, **kwargs)


def jsonify(x):
    return orjson.dumps(x, option=orjson.OPT_SERIALIZE_NUMPY).decode('utf-8')


def unjsonify(x):
    return orjson.loads(x)


if __name__ == "__main__":
    main()
