import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_socketio import send, emit
from gevent import time as gtime
# disable_caching()

app = Flask(__name__)
app.config['SECRET_KEY'] = '0f m@ns dis0b3d13nc3'
socketio = SocketIO(app, ping_timeout=60 * 5, ping_interval=5)

linelim = 1000


@cache(maxsize=10)
def get_text(txt):
    return TextModel(txt)


# @app.websocket("/ws")
@socketio.on('parse')
def parse(data):
    data = unjsonify(data)
    print(data)
    data = {
        d['name']: (
            int(d['value'])
            if d['value'].isdigit() and d['name'] != 'text' else d['value']
        )
        for d in data
    }
    text = data.pop('text')
    lines = text.split('\n')[:linelim]
    text = '\n'.join(lines)

    constraints = tuple(x[1:] for x in list(data.keys()) if x and x[0] == '*')
    for c in constraints:
        data.pop('*' + c)
    meter_kwargs = data
    meter_kwargs['constraints'] = constraints
    t = get_text(text)
    t.set_meter(**meter_kwargs)
    started = time.time()
    numtoiter = len(t.get_parseable_units())
    remainings = []
    rates = []
    numrows = 0
    for i, line_parses in enumerate(t.parse_iter()):
        parsed_line = line_parses.line
        data_out_l = []
        for pi, parse in enumerate(parsed_line.parses.unbounded):
            html = parsed_line.to_html(
                parse=parse,
                blockquote=False,
                as_str=True,
                tooltip=True
            )
            resd = parse.stats_d()
            data = {}
            data['row'] = [
                parsed_line.stanza.num,
                parsed_line.num,
                parsed_line.txt,
                parse.parse_rank,
                f'<div class="parsestr">{html}</div>',
                parse.txt,
                parse.meter_str,
                parse.stress_str,
                parse.num_sylls,
                round(
                    resd.get(
                        'ambig',
                        0,
                    ),
                    1,
                ),
                round(
                    resd.get(
                        '*total',
                        -1,
                    ),
                    1,
                ),
            ] + [
                round(
                    resd.get(
                        f'*{cname}',
                        0,
                    ),
                    1,
                ) for cname in get_all_constraints()
            ]
            data['row'] = ['' if not x else x for x in data['row']]

            def ctype(pi):
                return 'otherparse' if pi else 'bestparse'

            data['row'] = [
                f'<span class="{ctype(pi)}">{x}</span>' for x in data['row']
            ]
            data['progress'] = (i + 1) / numtoiter
            sofar = time.time() - started
            rate = sofar / (i + 1)
            remaining = (numtoiter - i - 1) * rate
            remainings.append(remaining)
            rates.append(rate)
            data['remaining'] = float(np.median(remainings[-10:]))
            data['rate'] = float(np.median(rates[-10:]))
            data['rownum'] = numrows
            data['numdone'] = numdone = i + 1
            data['numtodo'] = numtoiter - numdone
            data['numlines'] = numtoiter
            data['duration'] = sofar
            data_out_l.append(data)
            numrows += 1
        gtime.sleep(.01)
        # out = encode_cache(data_out_l)
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
    # app.run(port=port, debug=debug, host=host, **kwargs)
    socketio.run(app, port=port, debug=debug, host=host, **kwargs)


def jsonify(x):
    return orjson.dumps(x, option=orjson.OPT_SERIALIZE_NUMPY).decode('utf-8')


def unjsonify(x):
    return orjson.loads(x)


if __name__ == "__main__":
    main()
