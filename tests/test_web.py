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
    assert set(tree) == {'tag', 'tstress', 'text', 'children'}
    assert any(row['phrasal'] is not None for row in data['parses'][0]['grid'])


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
