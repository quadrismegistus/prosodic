import os
import pytest
import json
import time
import random
import threading
from multiprocessing import Process, Queue

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


# -- Selenium browser tests (skip if no browser available) --

NAPTIME = int(os.environ.get('NAPTIME', 5))
PORT = random.randint(5111, 5211)
BASE_URL = f"http://localhost:{PORT}"

def _run_app(q):
    import uvicorn
    from prosodic.web.api import app
    def start_server():
        uvicorn.run(app, port=PORT, log_level="warning")
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
