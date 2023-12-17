import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
from quart import websocket, Quart, render_template, jsonify

logging.getLogger('asyncio').setLevel(logging.ERROR)


def jsonify(x):
    return orjson.dumps(x, option=orjson.OPT_SERIALIZE_NUMPY).decode('utf-8')


def unjsonify(x):
    return orjson.loads(x)


app = Quart(
    __name__,
    static_url_path="/static",
    static_folder=os.path.join(os.path.dirname(__file__),
                               'static')
)


@app.websocket("/ws")
async def ws():
    await websocket.accept()
    while True:
        data_s = await websocket.receive()
        data_l = unjsonify(data_s)
        data = {d['name']: d['value'] for d in data_l}
        text = data.pop('text')
        constraints = data.keys()

        t = Text(text)
        started = time.time()
        numtoiter = len(t.parseable_units)
        remainings = []
        for i, parsed_line in enumerate(t.parse_iter(constraints=constraints)):
            for i, parse in enumerate(parsed_line.parses.unbounded):
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
                    parse.parse_rank,
                    f'<div class="parsestr">{html}</div>',
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
                    ) for cname in CONSTRAINTS
                ]
                data['row'] = ['' if not x else x for x in data['row']]
                data['row'] = [
                    f'<span class="{'otherparse' if i else 'bestparse'}">{x}</span>'
                    for x in data['row']
                ]
                data['progress'] = (i + 1) / len(t.parseable_units)
                sofar = time.time() - started
                rate = sofar / (i + 1)
                remaining = (numtoiter - i - 1) * rate
                remainings.append(remaining)
                data['remaining'] = float(np.median(remainings[-2:]))
                await websocket.send(jsonify(data))


@app.get("/")
async def index():
    return await render_template(
        "index.html",
        constraints=list(CONSTRAINTS.keys()),
        active_constraints=DEFAULT_CONSTRAINTS_NAMES,
        enumerate=enumerate
    )


def main(port=5000, debug=True):
    if debug: logmap.enable()
    app.run(port=port, debug=debug)


if __name__ == "__main__":
    main()
