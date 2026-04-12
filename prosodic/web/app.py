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


@cache(maxsize=10)
def get_text(txt):
    return TextModel(txt)


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

    # web app needs full entities for HTML rendering, so parse via Entity path
    text_lines = t.lines  # triggers entity construction
    from prosodic.parsing.meter import Meter
    meter = Meter(**meter_kwargs)
    for line in text_lines:
        line.parse(**meter_kwargs)

    started = time.time()
    numtoiter = len(text_lines)
    numrows = 0
    remainings = []
    rates = []

    for i, line in enumerate(text_lines):
        line_num = line.num
        pl = line._parses
        if not pl:
            continue

        data_out_l = []
        parses_to_show = pl.unbounded if hasattr(pl, 'unbounded') else []
        for pi, parse in enumerate(parses_to_show):
            html = line.to_html(
                parse=parse,
                blockquote=False,
                as_str=True,
                tooltip=True
            ) if hasattr(line, 'to_html') else str(parse)

            resd = parse.stats_d() if hasattr(parse, 'stats_d') else {}
            stanza_num = line.stanza.num if hasattr(line, 'stanza') and line.stanza else 1

            row_data = {}
            row_data['row'] = [
                stanza_num,
                line_num,
                line.txt.strip(),
                parse.parse_rank or (pi + 1),
                f'<div class="parsestr">{html}</div>',
                parse.txt,
                parse.meter_str,
                parse.stress_str,
                parse.num_sylls,
                round(resd.get('ambig', 0), 1),
                round(resd.get('*total', -1), 1),
            ] + [
                round(resd.get(f'*{cname}', 0), 1)
                for cname in get_all_constraints()
            ]
            row_data['row'] = ['' if not x else x for x in row_data['row']]

            def ctype(pi):
                return 'otherparse' if pi else 'bestparse'

            row_data['row'] = [
                f'<span class="{ctype(pi)}">{x}</span>' for x in row_data['row']
            ]
            sofar = time.time() - started
            rate = sofar / (i + 1) if i > 0 else 0
            remaining = (numtoiter - i - 1) * rate if rate else 0
            remainings.append(remaining)
            rates.append(rate)
            row_data['progress'] = (i + 1) / max(numtoiter, 1)
            row_data['remaining'] = float(np.median(remainings[-10:]))
            row_data['rate'] = float(np.median(rates[-10:])) if rates else 0
            row_data['rownum'] = numrows
            row_data['numdone'] = i + 1
            row_data['numtodo'] = numtoiter - (i + 1)
            row_data['numlines'] = numtoiter
            row_data['duration'] = sofar
            data_out_l.append(row_data)
            numrows += 1

        gtime.sleep(.01)
        out = jsonify(data_out_l)
        emit('parse_result', out)

    gtime.sleep(.1)
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
