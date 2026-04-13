import os
import pytest
import json
import time
import random
import threading
from multiprocessing import Process, Queue

# ── Flask / SocketIO test client tests (no browser needed) ────���─────────

@pytest.fixture(scope="module")
def flask_app():
    from prosodic.web.app import app, socketio
    app.config['TESTING'] = True
    return app, socketio


def test_index_route(flask_app):
    app, socketio = flask_app
    with app.test_client() as client:
        resp = client.get('/')
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        assert '<title>Prosodic</title>' in html
        assert 'inputtext' in html
        assert 'parsebtn' in html


def test_index_has_constraints(flask_app):
    app, socketio = flask_app
    with app.test_client() as client:
        html = client.get('/').data.decode('utf-8')
        # all default constraints should appear as checkboxes
        for cname in ['w_stress', 's_unstress', 'w_peak', 'unres_across', 'unres_within', 'foot_size']:
            assert f'*{cname}' in html, f"Constraint {cname} not found in HTML"


def test_index_has_meter_config(flask_app):
    app, socketio = flask_app
    with app.test_client() as client:
        html = client.get('/').data.decode('utf-8')
        assert 'meter-config' in html
        assert 'max_w' in html
        assert 'max_s' in html
        assert 'resolve_optionality' in html


def test_index_has_default_text(flask_app):
    app, socketio = flask_app
    with app.test_client() as client:
        html = client.get('/').data.decode('utf-8')
        assert 'From fairest creatures we desire increase' in html


def test_index_has_view_toggles(flask_app):
    app, socketio = flask_app
    with app.test_client() as client:
        html = client.get('/').data.decode('utf-8')
        assert 'btn-best' in html
        assert 'btn-unbounded' in html


def test_socketio_parse(flask_app):
    app, socketio = flask_app
    client = socketio.test_client(app)
    assert client.is_connected()

    # send parse request (mimics the form serialization from the frontend)
    form_data = [
        {'name': 'text', 'value': 'To be or not to be'},
        {'name': '*w_stress', 'value': '1'},
        {'name': '*s_unstress', 'value': '1'},
        {'name': '*w_peak', 'value': '1'},
        {'name': '*unres_across', 'value': '1'},
        {'name': '*unres_within', 'value': '1'},
        {'name': '*foot_size', 'value': '1'},
        {'name': 'max_s', 'value': '2'},
        {'name': 'max_w', 'value': '2'},
    ]
    from prosodic.web.app import jsonify
    client.emit('parse', jsonify(form_data))

    # collect responses
    received = client.get_received()
    events = {r['name']: r['args'] for r in received}

    assert 'parse_result' in events, f"No parse_result event. Got: {list(events.keys())}"
    assert 'parse_done' in events, f"No parse_done event. Got: {list(events.keys())}"

    # parse_result should contain parse data
    result_data = json.loads(events['parse_result'][0])
    assert len(result_data) > 0, "No parse results returned"
    row = result_data[0]
    assert 'parse_html' in row
    assert 'meter_str' in row
    assert 'score' in row
    assert row['line_num'] == 1

    client.disconnect()


def test_socketio_parse_multiline(flask_app):
    app, socketio = flask_app
    client = socketio.test_client(app)

    form_data = [
        {'name': 'text', 'value': 'Shall I compare thee to a summers day\nThou art more lovely and more temperate'},
        {'name': '*w_stress', 'value': '1'},
        {'name': '*s_unstress', 'value': '1'},
        {'name': '*w_peak', 'value': '1'},
        {'name': '*unres_across', 'value': '1'},
        {'name': '*unres_within', 'value': '1'},
        {'name': '*foot_size', 'value': '1'},
        {'name': 'max_s', 'value': '2'},
        {'name': 'max_w', 'value': '2'},
    ]
    from prosodic.web.app import jsonify
    client.emit('parse', jsonify(form_data))

    received = client.get_received()
    parse_results = [r for r in received if r['name'] == 'parse_result']
    done_events = [r for r in received if r['name'] == 'parse_done']

    # should get results for 2 lines
    assert len(parse_results) == 2, f"Expected 2 parse_result events, got {len(parse_results)}"
    assert len(done_events) == 1

    # check line numbers
    line_nums = set()
    for pr in parse_results:
        rows = json.loads(pr['args'][0])
        for row in rows:
            line_nums.add(row['line_num'])
    assert line_nums == {1, 2}, f"Expected line_nums {{1, 2}}, got {line_nums}"

    client.disconnect()


def test_socketio_parse_html_has_classes(flask_app):
    app, socketio = flask_app
    client = socketio.test_client(app)

    form_data = [
        {'name': 'text', 'value': 'The world is too much with us'},
        {'name': '*w_stress', 'value': '1'},
        {'name': '*s_unstress', 'value': '1'},
        {'name': '*w_peak', 'value': '1'},
        {'name': '*unres_across', 'value': '1'},
        {'name': '*unres_within', 'value': '1'},
        {'name': '*foot_size', 'value': '1'},
        {'name': 'max_s', 'value': '2'},
        {'name': 'max_w', 'value': '2'},
    ]
    from prosodic.web.app import jsonify
    client.emit('parse', jsonify(form_data))

    received = client.get_received()
    parse_results = [r for r in received if r['name'] == 'parse_result']
    rows = json.loads(parse_results[0]['args'][0])
    html = rows[0]['parse_html']

    # HTML should contain metrical position classes
    assert 'mtr_s' in html or 'mtr_w' in html, f"No meter classes in HTML: {html}"
    # and stress classes
    assert 'str_s' in html or 'str_w' in html, f"No stress classes in HTML: {html}"

    client.disconnect()


def test_socketio_parse_done_has_duration(flask_app):
    app, socketio = flask_app
    client = socketio.test_client(app)

    form_data = [
        {'name': 'text', 'value': 'To be or not to be'},
        {'name': '*w_stress', 'value': '1'},
        {'name': '*s_unstress', 'value': '1'},
        {'name': '*w_peak', 'value': '1'},
        {'name': '*unres_across', 'value': '1'},
        {'name': '*unres_within', 'value': '1'},
        {'name': '*foot_size', 'value': '1'},
        {'name': 'max_s', 'value': '2'},
        {'name': 'max_w', 'value': '2'},
    ]
    from prosodic.web.app import jsonify
    client.emit('parse', jsonify(form_data))

    received = client.get_received()
    done = [r for r in received if r['name'] == 'parse_done']
    assert len(done) == 1
    done_data = done[0]['args'][0]
    assert 'duration' in done_data
    assert 'numrows' in done_data
    assert done_data['numrows'] > 0

    client.disconnect()


# ── Selenium browser tests (skip if no browser available) ───────────────

NAPTIME = int(os.environ.get('NAPTIME', 5))
PORT = random.randint(5111, 5211)
BASE_URL = f"http://localhost:{PORT}"

def _run_app(q):
    from prosodic.web.app import app, socketio
    def start_server():
        socketio.run(app, port=PORT, debug=False)
    server_thread = threading.Thread(target=start_server)
    server_thread.start()
    q.put("Server started")
    server_thread.join()

@pytest.fixture(scope="module")
def app_server():
    queue = Queue()
    p = Process(target=_run_app, args=(queue,))
    p.start()
    assert queue.get(timeout=30) == "Server started"
    time.sleep(NAPTIME)
    yield
    p.terminate()
    p.join()

@pytest.fixture(scope="module")
def driver(app_server):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        d = webdriver.Chrome(options=options)
    except Exception:
        try:
            from selenium import webdriver
            options = webdriver.FirefoxOptions()
            options.add_argument('--headless')
            d = webdriver.Firefox(options=options)
        except Exception:
            pytest.skip("No browser driver available")
    yield d
    d.quit()

def test_browser_homepage(driver):
    driver.get(BASE_URL)
    assert "Prosodic" in driver.title


if __name__ == "__main__":
    pytest.main([__file__])
