import sqlite3

import pytest

from app.database import InMemoryAdapter, SQLiteAdapter, get_db
from import_sites import import_to_sqlite


@pytest.fixture(params=['sqlite', 'memory'])
def db(request, tmp_path):
    adapter = SQLiteAdapter(tmp_path / 'sites.db') if request.param == 'sqlite' else InMemoryAdapter()
    adapter.initialize()
    adapter.clear_sites()
    yield adapter
    adapter.clear_sites()


def test_crud_does_not_mutate_inputs_or_reads(db):
    data = {'site_code': 'SF-88', 'name': 'Test site'}
    site_id = db.add_site(data)
    assert 'id' not in data
    read = db.get_all_sites()
    read[0]['name'] = 'Changed outside the adapter'
    assert db.get_site_by_id(site_id)['name'] == 'Test site'
    assert db.update_site(site_id, {'name': 'Updated'})
    assert db.get_site_by_id(site_id)['name'] == 'Updated'
    assert db.update_site(site_id, {})
    assert not db.update_site('999999', {})
    assert db.delete_site(site_id)
    assert not db.delete_site(site_id)


def test_clear_deletes_all_records(db):
    db.import_sites([{'site_code': f'SF-{i}'} for i in range(5)])
    assert db.clear_sites() == 5
    assert db.get_all_sites() == []


def test_failed_or_empty_import_preserves_data(db):
    db.import_sites([{'site_code': 'Existing'}])
    for invalid in ([], [{'site_code': 'Valid'}, {'site_code': None}], [{'site_code': 'X', 'id': 3}]):
        with pytest.raises(ValueError):
            db.import_sites(invalid)
        assert [site['site_code'] for site in db.get_all_sites()] == ['Existing']
    db.add_site({'site_code': 'Still writable'})
    assert len(db.get_all_sites()) == 2


def test_import_sql_error_rolls_back_and_closes_connection(tmp_path):
    adapter = SQLiteAdapter(tmp_path / 'db.sqlite')
    adapter.initialize()
    adapter.add_site({'site_code': 'Original'})
    with sqlite3.connect(adapter.db_path) as conn:
        conn.execute("""CREATE TRIGGER reject_bad BEFORE INSERT ON nike_sites
                        WHEN NEW.site_code = 'Bad'
                        BEGIN SELECT RAISE(ABORT, 'rejected site'); END""")
    with pytest.raises(sqlite3.IntegrityError):
        adapter.import_sites([{'site_code': 'Valid'}, {'site_code': 'Bad'}])
    assert adapter.get_all_sites()[0]['site_code'] == 'Original'
    adapter.clear_sites()


@pytest.mark.parametrize('data', [
    {'site_code': 'X', 'latitude': float('nan')},
    {'site_code': 'X', 'longitude': 181},
    {'site_code': 'X', 'latitude': True},
    {'site_code': 'X', 'name': object()},
    {'site_code': 'X', 'name = NULL; --': 'malicious column'},
])
def test_invalid_data_is_rejected(db, data):
    with pytest.raises(ValueError):
        db.add_site(data)
    assert db.get_all_sites() == []


def test_import_cli_honors_database_path(monkeypatch, tmp_path):
    path = tmp_path / 'nested' / 'configured.db'
    monkeypatch.setenv('DATABASE_PATH', str(path))
    assert import_to_sqlite([{'site_code': 'CLI'}]) == 1
    assert SQLiteAdapter(path).get_all_sites()[0]['site_code'] == 'CLI'


def test_unknown_backend_is_rejected(monkeypatch):
    monkeypatch.setenv('DB_BACKEND', 'typo')
    with pytest.raises(ValueError, match='Unsupported'):
        get_db()
