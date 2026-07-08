import os
import pytest
import json
import time
import random
import threading

# -- FastAPI test client tests (no browser needed) --

@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from prosodic.web.api import app
    return TestClient(app)


def test_meter_defaults(client):
    resp = client.get('/api/meter/defaults')
    assert resp.status_code == 200
    data = resp.json()
    assert 'all_constraints' in data
    assert 'constraint_descriptions' in data
    assert 'defaults' in data
    assert 'constraints' in data['defaults']
    assert 'max_s' in data['defaults']
    assert 'max_w' in data['defaults']
    for cname in ['w_stress', 's_unstress', 'w_peak', 'unres_across', 'unres_within', 'foot_size']:
        assert cname in data['all_constraints'], f"Constraint {cname} not found"


def test_meter_defaults_descriptions(client):
    resp = client.get('/api/meter/defaults')
    data = resp.json()
    descs = data['constraint_descriptions']
    assert isinstance(descs, dict)
    assert len(descs) > 0
    assert 'w_stress' in descs


def _default_parse_data(**overrides):
    data = {
        'text': 'To be or not to be',
        'constraints': ['w_stress', 's_unstress', 'w_peak', 'unres_across', 'unres_within', 'foot_size'],
        'max_s': 2,
        'max_w': 2,
        'resolve_optionality': True,
    }
    data.update(overrides)
    return data


def test_parse_route(client):
    resp = client.post('/api/parse', json=_default_parse_data())
    assert resp.status_code == 200
    data = resp.json()
    assert 'rows' in data
    assert 'elapsed' in data
    assert 'num_lines' in data
    assert data['num_lines'] >= 1
    assert len(data['rows']) >= 1


def test_parse_row_structure(client):
    resp = client.post('/api/parse', json=_default_parse_data(
        text='The world is too much with us'
    ))
    data = resp.json()
    assert len(data['rows']) >= 1
    row = data['rows'][0]
    assert 'parse_html' in row
    assert 'meter_str' in row
    assert 'score' in row
    assert 'rank' in row
    assert 'num_unbounded' in row
    assert 'mtr_s' in row['parse_html'] or 'mtr_w' in row['parse_html']


def test_parse_multiline(client):
    resp = client.post('/api/parse', json=_default_parse_data(
        text='Shall I compare thee to a summers day\nThou art more lovely and more temperate'
    ))
    assert resp.status_code == 200
    data = resp.json()
    assert data['num_lines'] == 2


def test_parse_empty_text(client):
    resp = client.post('/api/parse', json=_default_parse_data(text=''))
    assert resp.status_code == 400


def test_maxent_fit(client):
    resp = client.post('/api/maxent/fit', json={
        'text': 'From fairest creatures we desire increase\nThat thereby beautys rose might never die',
        'target_scansion': 'wswswswsws',
        'zones': 3,
        'regularization': 100,
        'constraints': ['w_stress', 's_unstress', 'w_peak'],
        'max_s': 2,
        'max_w': 2,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert 'weights' in data
    assert 'elapsed' in data
    assert 'config' in data
    assert isinstance(data['weights'], list)


def test_maxent_fit_accuracy(client):
    resp = client.post('/api/maxent/fit', json={
        'text': 'From fairest creatures we desire increase\nThat thereby beautys rose might never die',
        'target_scansion': 'wswswswsws',
        'zones': 3,
        'regularization': 100,
        'constraints': ['w_stress', 's_unstress', 'w_peak'],
        'max_s': 2,
        'max_w': 2,
    })
    data = resp.json()
    assert 'accuracy' in data
    assert 'num_lines' in data
    assert 'num_matched' in data
    assert 'log_likelihood' in data
    assert isinstance(data['accuracy'], float)
    assert 0 <= data['accuracy'] <= 1


def test_corpora_list(client):
    resp = client.get('/api/corpora')
    assert resp.status_code == 200
    data = resp.json()
    assert 'files' in data
    names = [f['name'] for f in data['files']]
    assert any('shakespeare' in n for n in names)


def test_maxent_fit_no_text(client):
    resp = client.post('/api/maxent/fit', json={'text': ''})
    assert resp.status_code == 400


def test_static_files(client):
    resp = client.get('/')
    assert resp.status_code == 200
    assert 'Prosodic' in resp.text


# -- Security headers / output escaping (F8 prerequisites) --

def test_csp_and_security_headers(client):
    resp = client.get('/api/meter/defaults')
    csp = resp.headers.get('content-security-policy')
    assert csp and "default-src 'self'" in csp
    assert resp.headers.get('x-content-type-options') == 'nosniff'
    assert resp.headers.get('x-frame-options') == 'DENY'


def test_parse_html_escapes_markup(client):
    # Output escaping must be present before permalinks are safe: injected
    # markup in the text must be escaped in the {@html} sink fields.
    resp = client.post('/api/parse', json=_default_parse_data(
        text='a <script>alert(1)</script> b'))
    assert resp.status_code == 200
    for row in resp.json()['rows']:
        assert '<script>' not in row['parse_html']
        assert '</script>' not in row['parse_html']
        assert '&lt;' in row['parse_html']  # angle bracket escaped


# -- F6: per-request wall-clock parse timeout --

def _fresh_multiline(prefix):
    # Unique, uncached, multi-line text so parsing reliably exceeds a 1ms budget.
    return "\n".join(f"{prefix} probe line number {i} zeta omega delta" for i in range(6))


def test_parse_timeout_returns_504(client):
    import time as _t
    t0 = _t.time()
    resp = client.post('/api/parse', json=_default_parse_data(
        text=_fresh_multiline('parse504'), parse_timeout=0.001))
    dt = _t.time() - t0
    assert resp.status_code == 504, (resp.status_code, resp.text)
    assert 'timed out' in resp.json()['detail'].lower()
    assert dt < 10, f"timeout was not timely: {dt:.2f}s"  # returned promptly, not a hang


def test_parse_normal_still_succeeds(client):
    resp = client.post('/api/parse', json=_default_parse_data(
        text='To be or not to be', parse_timeout=60))
    assert resp.status_code == 200
    assert len(resp.json()['rows']) >= 1


def test_parse_line_grid_data(client):
    resp = client.post('/api/parse/line', json=_default_parse_data(text='To be or not to be'))
    assert resp.status_code == 200
    data = resp.json()
    assert data['syntax_trees'] == []
    assert len(data['grid_palette']) == 5
    assert len(data['grid_level_names']) == 5
    grid = data['parses'][0]['grid']
    assert len(grid) > 0
    assert all(set(row) >= {'txt', 'height', 'level', 'color', 'phrasal', 'viol'} for row in grid)


def test_parse_line_syntax_tree(client):
    pytest.importorskip("spacy")
    try:
        resp = client.post('/api/parse/line', json=_default_parse_data(
            text='Shall I compare thee to a summer\'s day', syntax=True))
    except OSError:
        pytest.skip("spaCy model not installed")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data['syntax_trees']) == 1
    tree = data['syntax_trees'][0]
    assert set(tree) == {'tag', 'tstress', 'text', 'word_num', 'children'}
    assert any(row['phrasal'] is not None for row in data['parses'][0]['grid'])
    # tree leaves and grid rows share the same word_num space, so a frontend
    # can align a tree leaf's x-position to its word's grid column span
    def leaves(node):
        if not node['children']:
            yield node
        for c in node['children']:
            yield from leaves(c)
    leaf_word_nums = {n['word_num'] for n in leaves(tree)}
    grid_word_nums = {row['word_num'] for row in data['parses'][0]['grid']}
    assert leaf_word_nums and leaf_word_nums <= grid_word_nums


def test_parse_lp_endpoint(client):
    # Faithful L&P view endpoint (experimental). Skips if stanza / the
    # constituency model isn't installed on the server.
    pytest.importorskip("stanza")
    resp = client.post('/api/parse/lp', json={'text': 'thirteen men'})
    assert resp.status_code == 200
    data = resp.json()
    if not data.get('available'):
        pytest.skip(f"stanza constituency unavailable: {data.get('reason')}")
    assert data['nuclear'] == 'men'
    assert [(g['txt'], g['height']) for g in data['grid']] == [
        ('thir', 1), ('teen', 2), ('men', 3)
    ]
    # binary tree: every non-root node carries an s/w role
    def walk(node):
        for c in node['children']:
            assert c['role'] in ('s', 'w')
            walk(c)
    assert data['tree']['role'] is None  # root R
    walk(data['tree'])


def test_parse_line_timeout_returns_504(client):
    resp = client.post('/api/parse/line', json=_default_parse_data(
        text=_fresh_multiline('line504'), parse_timeout=0.001))
    assert resp.status_code == 504
    assert 'timed out' in resp.json()['detail'].lower()


def test_parse_stream_timeout_emits_error(client):
    resp = client.post('/api/parse/stream', json=_default_parse_data(
        text=_fresh_multiline('stream504'), parse_timeout=0.001))
    assert resp.status_code == 200  # SSE opens 200, error is delivered mid-stream
    assert 'timed out' in resp.text.lower()


# -- F8: shareable parse permalinks --

def _share_payload(text, **over):
    p = {
        'v': 1,
        'text': text,
        'meter': {
            'constraints': ['w_stress', 's_unstress', 'w_peak', 'unres_across', 'unres_within', 'foot_size'],
            'max_s': 2, 'max_w': 2, 'resolve_optionality': True,
        },
        'weights': {}, 'zoneWeights': None, 'zones': 3,
        'syntax': False, 'syntax_model': 'en_core_web_sm',
    }
    p.update(over)
    return p


def test_permalink_encode_decode_roundtrip():
    from prosodic.web.api import _encode_permalink, _decode_permalink
    for compress in (False, True):
        enc = _encode_permalink(_share_payload('To be or not to be'), compress=compress)
        req = _decode_permalink(enc)
        assert req['text'] == 'To be or not to be'
        assert 'w_stress' in req['constraints']
        assert req['max_s'] == 2 and req['max_w'] == 2


def test_permalink_endpoint_roundtrip(client):
    from prosodic.web.api import _encode_permalink
    for compress in (False, True):
        enc = _encode_permalink(_share_payload('Shall I compare thee to a summers day'),
                                compress=compress)
        resp = client.get('/api/parse/permalink', params={'data': enc})
        assert resp.status_code == 200, (compress, resp.text)
        data = resp.json()
        assert len(data['rows']) >= 1
        html = data['rows'][0]['parse_html']
        assert 'mtr_s' in html or 'mtr_w' in html


def test_permalink_matches_direct_parse(client):
    from prosodic.web.api import _encode_permalink
    text = 'Shall I compare thee to a summers day'
    enc = _encode_permalink(_share_payload(text), compress=True)
    plink = client.get('/api/parse/permalink', params={'data': enc}).json()
    direct = client.post('/api/parse', json=_default_parse_data(text=text)).json()
    pb = next(r for r in plink['rows'] if r['rank'] == 1)
    db = next(r for r in direct['rows'] if r['rank'] == 1)
    assert pb['meter_str'] == db['meter_str']


def test_permalink_no_new_xss_sink(client):
    from prosodic.web.api import _encode_permalink
    enc = _encode_permalink(_share_payload('a <script>alert(1)</script> b'), compress=False)
    resp = client.get('/api/parse/permalink', params={'data': enc})
    assert resp.status_code == 200
    for row in resp.json()['rows']:
        assert '<script>' not in row['parse_html']
        assert '</script>' not in row['parse_html']
        assert '&lt;' in row['parse_html']


def test_permalink_invalid_data(client):
    resp = client.get('/api/parse/permalink', params={'data': '!!!not-base64!!!'})
    assert resp.status_code in (400, 413)


def test_permalink_too_large_rejected():
    # Tested at the helper level: httpx (and real HTTP servers) cap URL length
    # far below this, so an over-long ?data= can't reach the handler via GET.
    from fastapi import HTTPException
    from prosodic.web.api import _decode_permalink, _PERMALINK_MAX_ENCODED
    with pytest.raises(HTTPException) as ei:
        _decode_permalink('A' * (_PERMALINK_MAX_ENCODED + 1))
    assert ei.value.status_code == 413


def test_permalink_gzip_bomb_rejected():
    # A tiny gzip that expands past the decoded cap must be refused (413), not
    # decompressed into memory.
    import base64
    import zlib
    from fastapi import HTTPException
    from prosodic.web.api import (_decode_permalink, _PERMALINK_MAX_DECODED,
                                  _PERMALINK_MAX_ENCODED)
    raw = b'{"text":"' + b'a' * (_PERMALINK_MAX_DECODED + 1000) + b'"}'
    co = zlib.compressobj(9, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
    gz = co.compress(raw) + co.flush()
    data = base64.urlsafe_b64encode(gz).decode('ascii').rstrip('=')
    assert len(data) < _PERMALINK_MAX_ENCODED  # passes the encoded-length gate
    with pytest.raises(HTTPException) as ei:
        _decode_permalink(data)
    assert ei.value.status_code == 413


# -- Playwright browser tests --
# Migrated off Selenium: Selenium 4's Selenium Manager auto-provisions a driver
# over the network at test time, which in CI hung/retried for ~400s instead of
# failing fast (flaking unrelated PRs). Playwright uses a pinned, pre-installed
# browser (`playwright install chromium`), so launch() either works or raises
# immediately — no network hang. The test runs in CI (see unit-tests.yml) and
# skips cleanly if the browser binary isn't present locally. (AUDIT R11)

NAPTIME = int(os.environ.get('NAPTIME', 30))

def _wait_for_server(url, timeout=NAPTIME):
    """Poll until the server answers, instead of a fixed sleep (AUDIT R11)."""
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError(f"server did not come up within {timeout}s at {url}")

@pytest.fixture(scope="module")
def app_server():
    # Run uvicorn in an in-process DAEMON THREAD, not multiprocessing. On Linux
    # multiprocessing forks, and forking a process that has already imported
    # torch/numpy + background threads deadlocks the child, so the server never
    # binds; a failed setup then leaks the child and pytest hangs at exit. A
    # daemon thread has neither problem (no fork; dies with the process).
    import socket
    import uvicorn
    from prosodic.web.api import app
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    base_url = f"http://127.0.0.1:{port}"
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None  # can't set signals off-main-thread
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        _wait_for_server(base_url)
    except Exception:
        server.should_exit = True
        raise
    yield base_url
    server.should_exit = True
    thread.join(timeout=5)

@pytest.fixture(scope="module")
def page(app_server):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("playwright not installed (pip install playwright)")
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(headless=True)
        except Exception as e:
            # browser binary not installed — fail fast to a skip (no network hang)
            pytest.skip(f"playwright chromium not available: {e} "
                        "(run: playwright install chromium)")
        pg = browser.new_page()
        try:
            yield pg
        finally:
            browser.close()

def test_browser_homepage(page, app_server):
    page.goto(app_server)
    assert "Prosodic" in page.title()


if __name__ == "__main__":
    pytest.main([__file__])


def test_stanza_missing_returns_clean_400(client, monkeypatch):
    # syntax_model='stanza' without Stanza installed must degrade to a clean
    # 400 (actionable message), not an opaque 500. The stanza path needs no
    # spaCy, so this runs even where spaCy is absent.
    import prosodic.analysis.metrical_lp as M

    def _boom():
        raise ImportError("Stanza not installed. Install with: "
                          "pip install 'prosodic[constituency]'")

    monkeypatch.setattr(M, "_require_stanza", _boom)
    monkeypatch.setattr(M, "_NLP_CACHE", {})
    monkeypatch.setattr(M, "_STANZA_STASH", None)
    resp = client.post('/api/parse', json=_default_parse_data(
        text='an uncached distinctive phrase for the stanza guard test',
        syntax=True, syntax_model='stanza'))
    assert resp.status_code == 400
    assert 'stanza' in resp.json()['detail'].lower()


# ============================================================================
# Coverage expansion for prosodic/web/api.py: endpoints + branches that the
# suite above didn't reach. Uses the module-scoped `client` fixture defined at
# the top of this file (FastAPI TestClient over prosodic.web.api.app).
# ============================================================================

# canonical iambic pentameter — stable scansion, used as a concrete oracle
_PENTAMETER = 'Shall I compare thee to a summers day'
_PENTAMETER2 = 'Thou art more lovely and more temperate'
# a single line that exceeds MAX_SYLL_IN_PARSE_UNIT (18) canonical syllables,
# with commas so it splits into short, parseable lineparts (prose fallback).
_PROSE_LINE = ('the cat sat on the mat, and the dog ran in the fog, '
               'while a bird flew over the far third hill')


# -- /api/parse/export : CSV / TSV / JSON download --------------------------

def test_export_csv(client):
    import csv
    import io
    resp = client.post('/api/parse/export', json=_default_parse_data(
        text=f'{_PENTAMETER}\n{_PENTAMETER2}', format='csv'))
    assert resp.status_code == 200
    assert resp.headers['content-type'].startswith('text/csv')
    assert resp.headers['content-disposition'] == \
        'attachment; filename="prosodic-parse.csv"'
    rows = list(csv.DictReader(io.StringIO(resp.text)))
    assert len(rows) == 2  # one export row per line
    r0 = rows[0]
    # required stat columns present
    for col in ('line_num', 'line_text', 'meter_str', 'num_sylls', 'num_viols',
                'num_parses', 'score', 'score_unbounded', 'num_sylls_unbounded'):
        assert col in r0, col
    assert r0['line_num'] == '1'
    assert r0['meter_str'] == '-+-+-+-+-+'   # iambic pentameter
    assert r0['num_sylls'] == '10'
    # unbounded sum >= best-parse score (sum over >=1 parses)
    assert float(r0['score_unbounded']) >= float(r0['score'])


def test_export_tsv(client):
    resp = client.post('/api/parse/export', json=_default_parse_data(
        text=_PENTAMETER, format='tsv'))
    assert resp.status_code == 200
    assert 'tab-separated-values' in resp.headers['content-type']
    assert resp.headers['content-disposition'].endswith('prosodic-parse.tsv"')
    header = resp.text.splitlines()[0]
    assert '\t' in header and ',' not in header.split('\t')[0]
    assert 'meter_str' in header.split('\t')


def test_export_json(client):
    resp = client.post('/api/parse/export', json=_default_parse_data(
        text=f'{_PENTAMETER}\n{_PENTAMETER2}', format='json'))
    assert resp.status_code == 200
    assert resp.headers['content-type'].startswith('application/json')
    assert resp.headers['content-disposition'].endswith('prosodic-parse.json"')
    data = json.loads(resp.text)
    assert isinstance(data, list) and len(data) == 2
    assert data[0]['meter_str'] == '-+-+-+-+-+'
    assert data[0]['num_sylls'] == 10
    # per-constraint violation columns are emitted with a '*' prefix
    assert any(k.startswith('*') for k in data[0])


def test_export_default_format_is_csv(client):
    # format omitted -> defaults to csv (req.get('format') or 'csv')
    resp = client.post('/api/parse/export', json=_default_parse_data(text=_PENTAMETER))
    assert resp.status_code == 200
    assert resp.headers['content-type'].startswith('text/csv')


def test_export_bad_format_400(client):
    resp = client.post('/api/parse/export', json=_default_parse_data(
        text=_PENTAMETER, format='xml'))
    assert resp.status_code == 400
    assert 'csv' in resp.json()['detail'].lower()


def test_export_no_text_400(client):
    resp = client.post('/api/parse/export', json=_default_parse_data(text='   '))
    assert resp.status_code == 400


def test_export_prose_meter_pipe_separated(client):
    # A prose (long) line exports best-only, with lineparts joined by ' | '
    # in meter_str (the <br> the HTML view uses is rewritten for flat export).
    resp = client.post('/api/parse/export', json=_default_parse_data(
        text=_PROSE_LINE, format='json'))
    assert resp.status_code == 200
    data = json.loads(resp.text)
    assert len(data) == 1
    assert ' | ' in data[0]['meter_str']
    assert data[0]['num_parses'] >= 1


# -- /api/parse prose fallback (long line -> linepart parsing) ---------------

def test_parse_prose_fallback_lineparts(client):
    resp = client.post('/api/parse', json=_default_parse_data(text=_PROSE_LINE))
    assert resp.status_code == 200
    data = resp.json()
    assert data['prose_mode'] is True
    assert data['num_lines'] == 1
    row = data['rows'][0]
    # multiple lineparts, all parsed; parse + meter strings break on <br>
    assert row['num_parts'] >= 3
    assert row['num_parts_parsed'] == row['num_parts']
    assert '<br>' in row['meter_str']
    assert '<br>' in row['parse_html']
    assert 'mtr_s' in row['parse_html']


def test_parse_prose_single_overlong_linepart_unparsed(client):
    # A long line with NO punctuation is a single linepart still over the cap:
    # it can't be parsed and renders as an <span class="unparsed"> clause with
    # an em-dash meter marker.
    text = ('one two three four five six seven eight nine ten eleven twelve '
            'more words here to push this well over the syllable cap now')
    resp = client.post('/api/parse', json=_default_parse_data(text=text))
    assert resp.status_code == 200
    data = resp.json()
    assert data['prose_mode'] is True
    row = data['rows'][0]
    assert row['num_parts_parsed'] == 0
    assert 'unparsed' in row['parse_html']
    assert '—' in row['meter_str']


def test_parse_prose_syntax_subsplit(client):
    # syntax=True lets an over-cap, punctuation-free clause be sub-split at
    # dependency clause boundaries (cc/advcl/relcl...) via _syntax_subsplit.
    pytest.importorskip("spacy")
    text = ('the hungry cat sat on the mat and the lazy dog ran through the '
            'field while a bird flew away')
    try:
        resp = client.post('/api/parse', json=_default_parse_data(text=text, syntax=True))
    except OSError:
        pytest.skip("spaCy model not installed")
    assert resp.status_code == 200
    data = resp.json()
    assert data['prose_mode'] is True
    row = data['rows'][0]
    # sub-split produced multiple parseable clauses (more than the 1 raw linepart)
    assert row['num_parts'] >= 2
    assert row['num_parts_parsed'] >= 2


# -- /api/parse zone-weighted scoring ---------------------------------------

def test_parse_with_zone_weights(client):
    # Fit to obtain zone-expanded weights, then feed them back to /api/parse:
    # exercises the zone_weights branch and the _scores (has_zone) scoring path.
    text = f'{_PENTAMETER}\n{_PENTAMETER2}'
    cons = ['w_stress', 's_unstress', 'w_peak']
    fit = client.post('/api/maxent/fit', json={
        'text': text, 'target_scansion': 'wswswswsws', 'zones': 3,
        'regularization': 100, 'constraints': cons, 'max_s': 2, 'max_w': 2,
    }).json()
    zw = {w['name']: w['weight'] for w in fit['weights']}
    assert zw  # fit produced some weights
    resp = client.post('/api/parse', json=_default_parse_data(
        text=text, constraints=cons, zone_weights=zw, zones=3))
    assert resp.status_code == 200
    rows = resp.json()['rows']
    assert len(rows) >= 2
    assert all(isinstance(r['score'], (int, float)) for r in rows)


# -- /api/parse/stream : successful SSE run ----------------------------------

def _parse_sse(body):
    """Return the list of decoded data payloads from an SSE response body."""
    out = []
    for line in body.splitlines():
        if line.startswith('data: '):
            out.append(json.loads(line[len('data: '):]))
    return out


def test_parse_stream_success_phases(client):
    resp = client.post('/api/parse/stream', json=_default_parse_data(
        text=f'{_PENTAMETER}\n{_PENTAMETER2}'))
    assert resp.status_code == 200
    assert resp.headers['content-type'].startswith('text/event-stream')
    events = _parse_sse(resp.text)
    phases = [e['phase'] for e in events]
    assert phases[0] == 'progress'
    assert 'rows' in phases
    assert phases[-1] == 'done'
    # the 'rows' event carries server-rendered parse HTML
    rows_ev = next(e for e in events if e['phase'] == 'rows')
    assert rows_ev['rows']
    assert any('mtr_' in r['parse_html'] for r in rows_ev['rows'])
    # the terminal 'done' event summarizes the run
    done = events[-1]
    assert done['num_lines'] == 2
    assert done['prose_mode'] is False
    assert 'w_stress' in done['constraints']


def test_parse_stream_no_text_400(client):
    resp = client.post('/api/parse/stream', json=_default_parse_data(text='   '))
    assert resp.status_code == 400


def test_parse_stream_oversized_413(client):
    from prosodic.web.api import MAX_INPUT_CHARS
    resp = client.post('/api/parse/stream', json={'text': 'a ' * (MAX_INPUT_CHARS // 2 + 50)})
    assert resp.status_code == 413


# -- /api/parse/line : prose (multi-part) + error branches -------------------

def test_parse_line_prose_parts(client):
    resp = client.post('/api/parse/line', json=_default_parse_data(text=_PROSE_LINE))
    assert resp.status_code == 200
    data = resp.json()
    # long line -> top-level parses empty, per-linepart detail in `parts`
    assert data['parses'] == []
    assert len(data['parts']) >= 3
    part = data['parts'][0]
    assert set(part) >= {'part_text', 'num_sylls', 'parses', 'num_parses', 'num_unbounded'}
    assert part['num_parses'] == len(part['parses'])
    assert data['num_parses'] == sum(p['num_parses'] for p in data['parts'])
    # every part parse still carries a grid
    assert all(p['grid'] for p in part['parses'])


def test_parse_line_no_text_400(client):
    resp = client.post('/api/parse/line', json=_default_parse_data(text='   '))
    assert resp.status_code == 400


def test_parse_line_oversized_413(client):
    from prosodic.web.api import MAX_INPUT_CHARS
    resp = client.post('/api/parse/line', json={'text': 'a ' * (MAX_INPUT_CHARS // 2 + 50)})
    assert resp.status_code == 413


def test_parse_oversized_413(client):
    from prosodic.web.api import MAX_INPUT_CHARS
    resp = client.post('/api/parse', json={'text': 'a ' * (MAX_INPUT_CHARS // 2 + 50)})
    assert resp.status_code == 413
    assert 'too large' in resp.json()['detail'].lower()


# -- /api/maxent/reparse -----------------------------------------------------

def test_maxent_reparse(client):
    resp = client.post('/api/maxent/reparse', json={
        'text': 'From fairest creatures we desire increase\n'
                'That thereby beautys rose might never die',
        'target_scansion': 'wswswswsws', 'zones': 3, 'regularization': 100,
        'constraints': ['w_stress', 's_unstress', 'w_peak'], 'max_s': 2, 'max_w': 2,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert 'elapsed' in data
    assert len(data['rows']) == 2
    r0 = data['rows'][0]
    assert set(r0) == {'line_num', 'line_txt', 'meter_str', 'score'}
    assert r0['line_num'] == 1
    assert set(r0['meter_str']) <= {'+', '-'}


def test_maxent_reparse_no_text_400(client):
    resp = client.post('/api/maxent/reparse', json={'text': '  '})
    assert resp.status_code == 400


# -- /api/maxent/fit-annotations (file upload) -------------------------------

def _anno_tsv(header_rows):
    return ''.join(header_rows)


def test_maxent_fit_annotations_tsv(client):
    tsv = ('text\tscansion\tfrequency\n'
           'From fairest creatures we desire increase\twswswswsws\t1\n'
           'That thereby beautys rose might never die\twswswswsws\t1\n')
    resp = client.post(
        '/api/maxent/fit-annotations',
        files={'annotations_file': ('anno.tsv', tsv, 'text/tab-separated-values')},
        data={'constraints': 'w_stress,s_unstress,w_peak', 'zones': '3',
              'regularization': '100'})
    assert resp.status_code == 200
    data = resp.json()
    assert data['config']['target'] == '(from annotations)'
    assert data['config']['zones'] == '3'
    assert isinstance(data['weights'], list)
    assert isinstance(data['accuracy'], float)
    assert 0 <= data['accuracy'] <= 1
    assert data['num_lines'] >= 1


def test_maxent_fit_annotations_zones_none(client):
    # zones='none' -> _normalize_zones -> None -> flat weighted training
    tsv = ('text\tscansion\n'
           'From fairest creatures we desire increase\twswswswsws\n'
           'That thereby beautys rose might never die\twswswswsws\n')
    resp = client.post(
        '/api/maxent/fit-annotations',
        files={'annotations_file': ('anno.tsv', tsv, 'text/tsv')},
        data={'zones': 'none'})
    assert resp.status_code == 200
    assert resp.json()['config']['zones'] == 'none'


def test_maxent_fit_annotations_missing_text_column_400(client):
    # No column resembling text/line -> can't map a text column.
    tsv = 'foo\tscan\nhello world\twsws\n'
    resp = client.post(
        '/api/maxent/fit-annotations',
        files={'annotations_file': ('a.tsv', tsv, 'text/tsv')}, data={})
    assert resp.status_code == 400
    assert 'text column' in resp.json()['detail'].lower()


def test_maxent_fit_annotations_missing_scansion_column_400(client):
    # Literal `text` column present (skips mapping), but no scansion column.
    tsv = 'text\tfoo\nhello world\tbar\n'
    resp = client.post(
        '/api/maxent/fit-annotations',
        files={'annotations_file': ('a.tsv', tsv, 'text/tsv')}, data={})
    assert resp.status_code == 400
    assert 'scansion column' in resp.json()['detail'].lower()


def test_maxent_fit_annotations_fuzzy_columns(client):
    # Non-canonical headers (line/parse/count) are auto-detected and remapped to
    # text/scansion/frequency (col_map is {old: new}; see fit-annotations).
    tsv = ('line\tparse\tcount\n'
           'From fairest creatures we desire increase\twswswswsws\t2\n'
           'That thereby beautys rose might never die\twswswswsws\t1\n')
    resp = client.post(
        '/api/maxent/fit-annotations',
        files={'annotations_file': ('a.tsv', tsv, 'text/tsv')}, data={'zones': 'none'})
    assert resp.status_code == 200
    assert 'weights' in resp.json()


def test_maxent_fit_annotations_syntax(client):
    # syntax=True builds a syntax-enabled TextModel and threads it through fit.
    pytest.importorskip("spacy")
    tsv = ('text\tscansion\n'
           'From fairest creatures we desire increase\twswswswsws\n'
           'That thereby beautys rose might never die\twswswswsws\n')
    try:
        resp = client.post(
            '/api/maxent/fit-annotations',
            files={'annotations_file': ('a.tsv', tsv, 'text/tsv')},
            data={'syntax': 'true', 'zones': '3'})
    except OSError:
        pytest.skip("spaCy model not installed")
    assert resp.status_code == 200
    assert resp.json()['config']['target'] == '(from annotations)'


# -- /api/corpora/read -------------------------------------------------------

def test_read_corpus_ok(client):
    listing = client.get('/api/corpora').json()['files']
    target = next(f for f in listing if f['name'] == 'en.shakespeare.txt')
    resp = client.get('/api/corpora/read', params={'path': target['path']})
    assert resp.status_code == 200
    data = resp.json()
    assert data['name'] == 'en.shakespeare.txt'
    assert 'Shall I compare' in data['text'] or len(data['text']) > 1000


def test_read_corpus_path_traversal_rejected(client):
    resp = client.get('/api/corpora/read', params={'path': '../../etc/passwd'})
    assert resp.status_code == 400
    assert resp.json()['detail'] == 'Invalid path'


def test_read_corpus_not_found(client):
    resp = client.get('/api/corpora/read',
                      params={'path': 'corppoetry_en/does-not-exist.txt'})
    assert resp.status_code == 404


def test_corpora_list_counts_lines(client):
    # num_lines is a positive count of non-blank lines (glob + read branch).
    files = client.get('/api/corpora').json()['files']
    sh = next(f for f in files if f['name'] == 'en.shakespeare.txt')
    assert sh['num_lines'] > 100
    assert sh['lang'] == 'en'


# -- /api/parse/lp error / unavailable branches ------------------------------

def test_parse_lp_no_text_400(client):
    resp = client.post('/api/parse/lp', json={'text': '   '})
    assert resp.status_code == 400


def test_parse_lp_unavailable_on_exception(client, monkeypatch):
    # lp_line_data raising -> {available: False, reason: <msg>} (not a 500).
    import prosodic.analysis.metrical_lp as M

    def _boom(_line):
        raise RuntimeError("no constituency backend")

    monkeypatch.setattr(M, "lp_line_data", _boom)
    resp = client.post('/api/parse/lp', json={'text': 'thirteen men'})
    assert resp.status_code == 200
    data = resp.json()
    assert data['available'] is False
    assert 'no constituency backend' in data['reason']


def test_parse_lp_unavailable_on_none(client, monkeypatch):
    # lp_line_data returning None -> {available: False, reason: 'no parse'}.
    import prosodic.analysis.metrical_lp as M
    monkeypatch.setattr(M, "lp_line_data", lambda _line: None)
    resp = client.post('/api/parse/lp', json={'text': 'thirteen men'})
    assert resp.status_code == 200
    assert resp.json() == {'available': False, 'reason': 'no parse',
                           'line_text': None} or resp.json()['available'] is False


# -- Helper-level branch coverage -------------------------------------------

def test_normalize_zones():
    from prosodic.web.api import _normalize_zones
    assert _normalize_zones(None) is None
    assert _normalize_zones("none") is None
    assert _normalize_zones("3") == 3 and isinstance(_normalize_zones("3"), int)
    assert _normalize_zones(3) == 3
    assert _normalize_zones("foot") == "foot"   # non-digit string passes through


def test_clamp_timeout():
    from prosodic.web.api import (_clamp_timeout, PARSE_TIMEOUT_DEFAULT,
                                  PARSE_TIMEOUT_MAX)
    assert _clamp_timeout({}) == PARSE_TIMEOUT_DEFAULT           # missing
    assert _clamp_timeout({'parse_timeout': 'abc'}) == PARSE_TIMEOUT_DEFAULT  # unparsable
    assert _clamp_timeout({'parse_timeout': -5}) == PARSE_TIMEOUT_DEFAULT     # <= 0
    assert _clamp_timeout({'parse_timeout': 99999}) == PARSE_TIMEOUT_MAX      # capped
    assert _clamp_timeout({'parse_timeout': 12}) == 12.0                      # normal


def test_permalink_to_req_non_dict():
    from fastapi import HTTPException
    from prosodic.web.api import _permalink_to_req
    with pytest.raises(HTTPException) as ei:
        _permalink_to_req(['not', 'a', 'dict'])
    assert ei.value.status_code == 400


def test_permalink_to_req_weight_folding():
    from prosodic.web.api import _permalink_to_req
    req = _permalink_to_req({
        'text': 'hi',
        'meter': {'constraints': ['w_stress', 'w_peak'], 'max_s': 2, 'max_w': 2},
        'weights': {'w_stress': 2.5, 'w_peak': 1.0},   # 1.0 not folded
        'parse_timeout': 7,
    })
    assert req['constraints'] == ['w_stress/2.5', 'w_peak']
    assert req['parse_timeout'] == 7


def test_permalink_to_req_zone_weights():
    from prosodic.web.api import _permalink_to_req
    req = _permalink_to_req({
        'text': 'hi',
        'meter': {'constraints': ['w_stress']},
        'weights': {'w_stress': 2.0},
        'zoneWeights': {'w_stress_z1': 1.0},
        'zones': 2,
    })
    # zoneWeights present -> weights are NOT folded into constraints
    assert req['constraints'] == ['w_stress']
    assert req['zone_weights'] == {'w_stress_z1': 1.0}
    assert req['zones'] == 2


def test_decode_permalink_empty():
    from fastapi import HTTPException
    from prosodic.web.api import _decode_permalink
    with pytest.raises(HTTPException) as ei:
        _decode_permalink('')
    assert ei.value.status_code == 400


def test_decode_permalink_bad_json():
    import base64
    from fastapi import HTTPException
    from prosodic.web.api import _decode_permalink
    bad = base64.urlsafe_b64encode(b'not json at all {{{').decode('ascii').rstrip('=')
    with pytest.raises(HTTPException) as ei:
        _decode_permalink(bad)
    assert ei.value.status_code == 400


def test_render_parse_html_no_line_fallback():
    # render_parse_html(parse) with no line falls back to space-joining slots.
    from prosodic.web.api import render_parse_html
    from prosodic.parsing.vectorized import parse_batch
    from prosodic.parsing.meter import Meter
    from prosodic.imports import TextModel
    t = TextModel('To be or not to be')
    _wt, pl = parse_batch(t.lines, Meter())[0]
    html_out = render_parse_html(pl.best_parse)   # no `line` argument
    assert 'mtr_s' in html_out and 'mtr_w' in html_out
    assert '<span' in html_out


def test_decode_permalink_bad_gzip():
    # gzip magic bytes but a corrupt body -> "Invalid permalink compression" 400.
    import base64
    from fastapi import HTTPException
    from prosodic.web.api import _decode_permalink
    data = base64.urlsafe_b64encode(b'\x1f\x8b' + b'\x00' * 20).decode('ascii').rstrip('=')
    with pytest.raises(HTTPException) as ei:
        _decode_permalink(data)
    assert ei.value.status_code == 400


# -- /api/parse/stream : batching + prose progress ---------------------------

def test_parse_stream_batches_over_fifty(client):
    # >50 result rows are flushed in multiple 'rows' events (BATCH_SIZE=50).
    text = '\n'.join([_PENTAMETER] * 60)
    resp = client.post('/api/parse/stream', json=_default_parse_data(text=text))
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    rows_events = [e for e in events if e['phase'] == 'rows']
    assert len(rows_events) >= 2                       # more than one batch
    assert all(len(e['rows']) <= 50 for e in rows_events)
    total = sum(len(e['rows']) for e in rows_events)
    assert total > 50
    assert events[-1]['phase'] == 'done'
    assert events[-1]['num_lines'] == 60


def test_parse_stream_prose_progress(client):
    # A long line makes the stream emit a "long line(s) detected" progress event.
    resp = client.post('/api/parse/stream', json=_default_parse_data(text=_PROSE_LINE))
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    msgs = [e.get('message', '') for e in events if e['phase'] == 'progress']
    assert any('long line' in m for m in msgs)
    assert events[-1]['phase'] == 'done'
    assert events[-1]['prose_mode'] is True


def test_parse_stream_with_zone_weights(client):
    text = f'{_PENTAMETER}\n{_PENTAMETER2}'
    cons = ['w_stress', 's_unstress', 'w_peak']
    fit = client.post('/api/maxent/fit', json={
        'text': text, 'target_scansion': 'wswswswsws', 'zones': 3,
        'regularization': 100, 'constraints': cons, 'max_s': 2, 'max_w': 2,
    }).json()
    zw = {w['name']: w['weight'] for w in fit['weights']}
    resp = client.post('/api/parse/stream', json=_default_parse_data(
        text=text, constraints=cons, zone_weights=zw, zones=3))
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    assert events[-1]['phase'] == 'done'
    assert any(e['phase'] == 'rows' for e in events)


# -- zone-weighted export + line detail --------------------------------------

def test_export_with_zone_weights(client):
    text = f'{_PENTAMETER}\n{_PENTAMETER2}'
    cons = ['w_stress', 's_unstress', 'w_peak']
    fit = client.post('/api/maxent/fit', json={
        'text': text, 'target_scansion': 'wswswswsws', 'zones': 3,
        'regularization': 100, 'constraints': cons, 'max_s': 2, 'max_w': 2,
    }).json()
    zw = {w['name']: w['weight'] for w in fit['weights']}
    resp = client.post('/api/parse/export', json=_default_parse_data(
        text=text, format='json', constraints=cons, zone_weights=zw, zones=3))
    assert resp.status_code == 200
    data = json.loads(resp.text)
    assert len(data) == 2
    assert all('score_unbounded' in r for r in data)


def test_parse_line_with_zone_weights(client):
    text = _PENTAMETER
    cons = ['w_stress', 's_unstress', 'w_peak']
    fit = client.post('/api/maxent/fit', json={
        'text': f'{_PENTAMETER}\n{_PENTAMETER2}', 'target_scansion': 'wswswswsws',
        'zones': 3, 'regularization': 100, 'constraints': cons, 'max_s': 2, 'max_w': 2,
    }).json()
    zw = {w['name']: w['weight'] for w in fit['weights']}
    resp = client.post('/api/parse/line', json=_default_parse_data(
        text=text, constraints=cons, zone_weights=zw, zones=3))
    assert resp.status_code == 200
    parses = resp.json()['parses']
    assert parses
    assert all(isinstance(p['score'], (int, float)) for p in parses)


def test_parse_line_syntax_prose_subsplit(client):
    # Line View on an over-cap, punctuation-free clause with syntax=True routes
    # through the multi-part branch + _syntax_subsplit, returning per-part detail.
    pytest.importorskip("spacy")
    text = ('the hungry cat sat on the mat and the lazy dog ran through the '
            'field while a bird flew away')
    try:
        resp = client.post('/api/parse/line', json=_default_parse_data(text=text, syntax=True))
    except OSError:
        pytest.skip("spaCy model not installed")
    assert resp.status_code == 200
    data = resp.json()
    assert data['parses'] == []
    assert len(data['parts']) >= 2


# -- main() launcher entrypoint (uvicorn mocked) -----------------------------

def test_main_invokes_uvicorn(monkeypatch):
    # main() should resolve default host/port and hand app to uvicorn.run.
    import uvicorn
    called = {}
    monkeypatch.setattr(uvicorn, 'run',
                        lambda app, **kw: called.update(host=kw.get('host'),
                                                        port=kw.get('port')))
    from prosodic.web.api import main
    main(debug=False)   # debug=False skips logmap.enable(); dev=False default
    assert called['host'] == '127.0.0.1'
    assert called['port'] == 8181


def test_main_debug_enables_logmap(monkeypatch):
    import uvicorn
    import prosodic.web.api as api
    seen = {}
    monkeypatch.setattr(uvicorn, 'run', lambda app, **kw: seen.update(kw))
    monkeypatch.setattr(api.logmap, 'enable', lambda: seen.update(logmap=True))
    api.main(debug=True, port=4321)
    assert seen.get('logmap') is True
    assert seen['port'] == 4321


def test_main_dev_delegates_to_run_dev(monkeypatch):
    import prosodic.web.api as api
    seen = {}
    monkeypatch.setattr(api, '_run_dev', lambda **kw: seen.update(kw))
    api.main(dev=True, port=1234, host='0.0.0.0', debug=False)
    assert seen == {'host': '0.0.0.0', 'port': 1234, 'debug': False}


def test_parse_stream_surfaces_mid_stream_error(client, monkeypatch):
    # A non-timeout failure during parsing is surfaced as an SSE 'error' event
    # (not a crash / silent hang). W8 in the source.
    import prosodic.web.api as api

    def _boom(t, meter):
        raise ValueError("synthetic parse failure")

    monkeypatch.setattr(api, '_parse_and_build_rows', _boom)
    resp = client.post('/api/parse/stream', json=_default_parse_data(text=_PENTAMETER))
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    err = [e for e in events if e['phase'] == 'error']
    assert err and 'synthetic parse failure' in err[0]['message']


def test_get_text_cache_is_bounded():
    # The TextModel LRU cache evicts once it exceeds _TEXT_CACHE_MAX (line 126).
    from prosodic.web.api import get_text, _text_cache, _TEXT_CACHE_MAX
    for i in range(_TEXT_CACHE_MAX + 5):
        get_text(f'unique cache probe line number {i} alpha')
    assert len(_text_cache) <= _TEXT_CACHE_MAX
