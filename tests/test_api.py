from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import main
from app.database import get_db


@pytest.fixture(params=['sqlite', 'memory'])
def client(request, monkeypatch, tmp_path):
    monkeypatch.setenv('DB_BACKEND', request.param)
    monkeypatch.setenv('DATABASE_PATH', str(tmp_path / 'sites.db'))
    monkeypatch.setenv('AUTO_IMPORT_DATA', 'false')
    monkeypatch.setenv('ADMIN_API_TOKEN', 'test-token')
    if request.param == 'memory':
        get_db().clear_sites()
    with TestClient(main.app) as test_client:
        yield test_client
    if request.param == 'memory':
        get_db().clear_sites()


def test_pages_and_assets(client):
    for url in ('/', '/about', '/static/js/map.js', '/static/css/style.css', '/healthz'):
        assert client.get(url).status_code == 200
    assert 'aria-label="Map of Nike missile sites"' in client.get('/').text


def test_exact_filters_and_missing_site(client):
    get_db().import_sites([
        {'site_code': 'V-1', 'state': 'Virginia', 'site_type': 'Control'},
        {'site_code': 'WV-1', 'state': 'West Virginia', 'site_type': 'Launch'},
    ])
    data = client.get('/api/sites', params={'state': ' virginia ', 'site_type': 'Control'}).json()
    assert data['count'] == 1
    site = data['sites'][0]
    assert client.get(f'/api/sites/{site["id"]}').json()['site']['site_code'] == 'V-1'
    assert client.get('/api/sites/999999').status_code == 404


@pytest.mark.parametrize('endpoint', ['/api/clear-data', '/api/import-data'])
def test_admin_rejections_do_not_modify_data(client, endpoint, monkeypatch):
    get_db().add_site({'site_code': 'Existing'})
    with patch.object(main, 'scrape_nike_sites') as scrape:
        for auth in ('', 'Basic test-token', 'Bearer wrong-token'):
            response = client.post(endpoint, headers={'Authorization': auth})
            assert response.status_code == 401
            assert response.headers['www-authenticate'] == 'Bearer'
        monkeypatch.delenv('ADMIN_API_TOKEN')
        assert client.post(endpoint).status_code == 503
        scrape.assert_not_called()
    assert len(get_db().get_all_sites()) == 1


def test_import_failure_preserves_data_and_clear_removes_all(client):
    get_db().import_sites([{'site_code': str(i)} for i in range(5)])
    headers = {'Authorization': 'Bearer test-token'}
    with patch.object(main, 'scrape_nike_sites', return_value=[]):
        assert client.post('/api/import-data', headers=headers).status_code == 500
    assert len(get_db().get_all_sites()) == 5
    with patch.object(main, 'scrape_nike_sites', return_value=[{'site_code': 'New'}]):
        assert client.post('/api/import-data', headers=headers).status_code == 200
    assert get_db().get_all_sites()[0]['site_code'] == 'New'
    get_db().import_sites([{'site_code': str(i)} for i in range(5)])
    response = client.post('/api/clear-data', headers=headers)
    assert response.status_code == 200
    assert 'deleted 5' in response.json()['message']
    assert client.get('/api/sites').json()['count'] == 0


def test_unicode_token_is_rejected_without_server_error(client):
    # Encode headers as bytes because HTTPX validates str headers as ASCII.
    response = client.post('/api/clear-data', headers=[(b'Authorization', b'Bearer \xff')])
    assert response.status_code == 401


def test_database_errors_are_not_exposed(client):
    with patch.object(main, 'get_db', side_effect=RuntimeError('/private/path secret')):
        assert client.get('/healthz').status_code == 503
        response = client.get('/api/sites')
        assert response.status_code == 500
        assert 'secret' not in response.text


def test_startup_auto_import_and_database_failure(monkeypatch):
    monkeypatch.setenv('DB_BACKEND', 'memory')
    monkeypatch.setenv('AUTO_IMPORT_DATA', 'true')
    get_db().clear_sites()
    with patch.object(main, 'scrape_nike_sites', return_value=[{'site_code': 'Auto'}]) as scrape:
        with TestClient(main.app):
            assert get_db().get_all_sites()[0]['site_code'] == 'Auto'
        with TestClient(main.app):
            pass
        assert scrape.call_count == 1
    get_db().clear_sites()
    with patch.object(main, 'get_db', side_effect=RuntimeError('DB broken')):
        with pytest.raises(RuntimeError, match='DB broken'):
            with TestClient(main.app):
                pass
