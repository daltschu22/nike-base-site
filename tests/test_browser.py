"""Real browser regressions. Enable with RUN_BROWSER_TESTS=1 after installing Chromium."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

import pytest

from app.database import SQLiteAdapter

pytestmark = pytest.mark.skipif(os.environ.get('RUN_BROWSER_TESTS') != '1', reason='Browser tests are opt-in')


@pytest.fixture(scope='module')
def server(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp('browser')
    db = SQLiteAdapter(tmp_path / 'sites.db')
    db.initialize()
    db.import_sites([
        {'site_code': 'SF-88', 'name': 'Sausalito — Launch area', 'state': 'California', 'site_type': 'Launch',
         'latitude': 37.82, 'longitude': -122.52, 'wiki_url': 'https://en.wikipedia.org/wiki/List_of_Nike_missile_sites'},
        {'site_code': 'C-47', 'name': 'Porter — Control area', 'state': 'Indiana', 'site_type': 'Control',
         'latitude': 41.6, 'longitude': -87.1, 'wiki_url': 'javascript:alert(1)'},
        {'site_code': 'Missing', 'state': 'California', 'latitude': None, 'longitude': None},
        {'site_code': 'Invalid', 'state': 'California', 'latitude': None, 'longitude': None},
    ])
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    env = {**os.environ, 'DATABASE_PATH': str(db.db_path), 'DB_BACKEND': 'sqlite', 'AUTO_IMPORT_DATA': 'false', 'GOOGLE_MAPS_API_KEY': 'test-invalid-key'}
    log = (tmp_path / 'server.log').open('w')
    process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', str(port)], env=env, stdout=log, stderr=log)
    url = f'http://127.0.0.1:{port}'
    try:
        for _ in range(100):
            if process.poll() is not None:
                pytest.fail((tmp_path / 'server.log').read_text())
            try:
                with urlopen(f'{url}/healthz', timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.05)
        else:
            pytest.fail('Server did not start')
        yield url
    finally:
        process.terminate()
        process.wait(timeout=10)
        log.close()


@pytest.fixture(scope='module')
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    # Tests exercise actual Leaflet code with deterministic network responses.
    page.route('https://maps.googleapis.com/**', lambda route: route.abort())
    page.route('https://*.tile.openstreetmap.org/**', lambda route: route.fulfill(status=200, content_type='image/png', body=Path('app/static/vendor/leaflet/images/marker-shadow.png').read_bytes()))
    page.route('https://fonts.googleapis.com/**', lambda route: route.abort())
    yield page
    page.close()


def ready(page, server):
    page.goto(server)
    page.wait_for_function("document.querySelector('#data-status').textContent.includes('Showing')")


def test_markers_filters_details_and_reset(page, server):
    errors = []
    page.on('pageerror', lambda error: errors.append(error))
    ready(page, server)
    assert page.locator('.leaflet-marker-icon').count() == 2
    assert '2 of 4' in page.locator('#data-status').inner_text()
    assert '2 locations have no valid coordinates' in page.locator('#data-status').inner_text()
    assert 'Using OpenStreetMap' in page.locator('#map-status').inner_text()
    assert page.locator('a[aria-current="page"]').inner_text() == 'Map'
    page.select_option('#state-filter', 'California')
    page.click('#apply-filters')
    assert page.locator('.leaflet-marker-icon').count() == 1
    page.locator('.leaflet-marker-icon').click()
    assert page.locator('#site-info').is_visible()
    assert 'SF-88' in page.locator('#site-code').inner_text()
    assert page.locator('#site-wiki').is_visible()
    # The panel must receive clicks above the Leaflet tile panes.
    page.locator('#close-info').scroll_into_view_if_needed()
    panel = page.locator('#close-info').bounding_box()
    assert page.evaluate('([x, y]) => document.elementFromPoint(x, y).id', [panel['x'] + 5, panel['y'] + 5]) == 'close-info'
    page.click('#close-info')
    assert page.locator('#site-info').is_hidden()
    page.select_option('#type-filter', 'Control')
    page.click('#apply-filters')
    assert page.locator('.leaflet-marker-icon').count() == 0
    assert 'No mapped locations match' in page.locator('#data-status').inner_text()
    page.click('#reset-filters')
    assert page.locator('.leaflet-marker-icon').count() == 2
    page.select_option('#state-filter', 'Indiana')
    page.click('#apply-filters')
    page.locator('.leaflet-marker-icon').click()
    assert page.locator('#site-wiki').is_hidden()
    assert not errors


def test_failed_data_request_can_retry(page, server):
    page.route('**/api/sites', lambda route: route.fulfill(status=500, content_type='application/json', body='{"success":false}'))
    page.goto(server)
    page.wait_for_selector('#retry-load', state='visible')
    assert 'Could not load site data' in page.locator('#data-status').inner_text()
    assert page.locator('#loading').is_hidden()
    page.unroute('**/api/sites')
    page.click('#retry-load')
    page.wait_for_function("document.querySelector('#data-status').textContent.includes('Showing')")
    assert page.locator('.leaflet-marker-icon').count() == 2


def test_empty_data_is_visible_without_alert(page, server):
    page.route('**/api/sites', lambda route: route.fulfill(status=200, content_type='application/json', body='{"success":true,"sites":[]}'))
    page.goto(server)
    page.wait_for_function("document.querySelector('#data-status').textContent.includes('No site data')")
    assert page.locator('#loading').is_hidden()
    assert page.locator('.leaflet-marker-icon').count() == 0


def test_mobile_layout(page, server):
    page.set_viewport_size({'width': 390, 'height': 844})
    ready(page, server)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.select_option('#state-filter', 'California')
    page.click('#apply-filters')
    page.locator('.leaflet-marker-icon').click()
    assert page.locator('#site-info').is_visible()
    map_box = page.locator('#map').bounding_box()
    panel_box = page.locator('#site-info').bounding_box()
    assert panel_box['y'] >= map_box['y'] + map_box['height']
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.click('#close-info')
    assert page.locator('#site-info').is_hidden()
