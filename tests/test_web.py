import os
import pytest
import json
import time
import random
import threading
from multiprocessing import Process, Queue

# -- Flask test client tests (no browser needed) --

@pytest.fixture(scope="module")
def flask_app():
    from prosodic.web.app import app
    app.config['TESTING'] = True
    return app


def test_index_route(flask_app):
    with flask_app.test_client() as client:
        resp = client.get('/')
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        assert '<title>Prosodic</title>' in html
        assert 'inputtext' in html
        assert 'htmx' in html


def test_index_has_constraints(flask_app):
    with flask_app.test_client() as client:
        html = client.get('/').data.decode('utf-8')
        for cname in ['w_stress', 's_unstress', 'w_peak', 'unres_across', 'unres_within', 'foot_size']:
            assert f'*{cname}' in html, f"Constraint {cname} not found in HTML"


def test_index_has_meter_config(flask_app):
    with flask_app.test_client() as client:
        html = client.get('/').data.decode('utf-8')
        assert 'max_w' in html
        assert 'max_s' in html
        assert 'resolve_optionality' in html


def test_index_has_tabs(flask_app):
    with flask_app.test_client() as client:
        html = client.get('/').data.decode('utf-8')
        assert 'Parse' in html
        assert 'MaxEnt' in html
        assert 'maxent-config' in html


def test_index_has_default_text(flask_app):
    with flask_app.test_client() as client:
        html = client.get('/').data.decode('utf-8')
        assert 'From fairest creatures we desire increase' in html


def _default_form_data(**overrides):
    data = {
        'text': 'To be or not to be',
        '*w_stress': '1',
        '*s_unstress': '1',
        '*w_peak': '1',
        '*unres_across': '1',
        '*unres_within': '1',
        '*foot_size': '1',
        'max_s': '2',
        'max_w': '2',
        'resolve_optionality': '1',
    }
    data.update(overrides)
    return data


def test_parse_route(flask_app):
    with flask_app.test_client() as client:
        resp = client.post('/parse', data=_default_form_data())
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        assert 'parse-text' in html
        assert 'Parsed' in html


def test_parse_multiline(flask_app):
    with flask_app.test_client() as client:
        resp = client.post('/parse', data=_default_form_data(
            text='Shall I compare thee to a summers day\nThou art more lovely and more temperate'
        ))
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        assert 'Parsed 2 lines' in html


def test_parse_html_has_classes(flask_app):
    with flask_app.test_client() as client:
        resp = client.post('/parse', data=_default_form_data(
            text='The world is too much with us'
        ))
        html = resp.data.decode('utf-8')
        assert 'mtr_s' in html or 'mtr_w' in html
        assert 'str_s' in html or 'str_w' in html


def test_parse_empty_text(flask_app):
    with flask_app.test_client() as client:
        resp = client.post('/parse', data=_default_form_data(text=''))
        assert resp.status_code == 200
        assert b'No text' in resp.data


def test_maxent_fit(flask_app):
    with flask_app.test_client() as client:
        resp = client.post('/maxent/fit', data={
            'text': 'From fairest creatures we desire increase\nThat thereby beautys rose might never die',
            'target_scansion': 'wswswswsws',
            'zones': '3',
            'regularization': '100',
            '*w_stress': '1',
            '*s_unstress': '1',
            '*w_peak': '1',
            'max_s': '2',
            'max_w': '2',
        })
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        assert 'Trained' in html
        assert 'weights-table' in html or 'No weights' in html


def test_maxent_fit_no_text(flask_app):
    with flask_app.test_client() as client:
        resp = client.post('/maxent/fit', data={'text': ''})
        assert resp.status_code == 200
        assert b'No text' in resp.data


# -- Selenium browser tests (skip if no browser available) --

NAPTIME = int(os.environ.get('NAPTIME', 5))
PORT = random.randint(5111, 5211)
BASE_URL = f"http://localhost:{PORT}"

def _run_app(q):
    from prosodic.web.app import app
    def start_server():
        app.run(port=PORT, debug=False)
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
