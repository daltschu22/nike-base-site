import logging
import os
import sqlite3
from abc import ABC, abstractmethod
from contextlib import closing
from threading import RLock

logger = logging.getLogger(__name__)
SITE_FIELDS = frozenset({
    'site_code', 'name', 'state', 'latitude', 'longitude', 'description',
    'site_type', 'status', 'wiki_url',
})


def validate_fields(site_data, *, partial=False):
    """Only allow writable columns; never interpolate caller-supplied SQL names."""
    unknown = set(site_data) - SITE_FIELDS
    if unknown:
        raise ValueError(f"Unknown site fields: {', '.join(sorted(unknown))}")
    if not partial or 'site_code' in site_data:
        if not isinstance(site_data.get('site_code'), str) or not site_data['site_code'].strip():
            raise ValueError('site_code must be a nonempty string')
    for field in SITE_FIELDS - {'latitude', 'longitude'}:
        value = site_data.get(field)
        if value is not None and not isinstance(value, str):
            raise ValueError(f'{field} must be text or null')
    for field, limit in (('latitude', 90), ('longitude', 180)):
        value = site_data.get(field)
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not -limit <= value <= limit:
                raise ValueError(f'{field} is outside its valid range')
    return dict(site_data)


class DatabaseAdapter(ABC):
    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def get_all_sites(self):
        pass

    @abstractmethod
    def get_site_by_id(self, site_id):
        pass

    @abstractmethod
    def add_site(self, site_data):
        pass

    @abstractmethod
    def update_site(self, site_id, site_data):
        pass

    @abstractmethod
    def delete_site(self, site_id):
        pass

    @abstractmethod
    def import_sites(self, sites):
        pass

    @abstractmethod
    def clear_sites(self):
        pass


class InMemoryAdapter(DatabaseAdapter):
    """One process-wide store, shared by the adapters created for each request."""

    _sites = []
    _next_id = 1
    _lock = RLock()

    def initialize(self):
        pass

    def get_all_sites(self):
        with self._lock:
            return [site.copy() for site in self._sites]

    def get_site_by_id(self, site_id):
        with self._lock:
            for site in self._sites:
                if str(site['id']) == str(site_id):
                    return site.copy()
        return None

    def add_site(self, site_data):
        site = validate_fields(site_data)
        with self._lock:
            site_id = str(InMemoryAdapter._next_id)
            InMemoryAdapter._next_id += 1
            site['id'] = site_id
            self._sites.append(site)
        return site_id

    def update_site(self, site_id, site_data):
        data = validate_fields(site_data, partial=True)
        with self._lock:
            for site in self._sites:
                if str(site['id']) == str(site_id):
                    site.update(data)
                    return True
        return False

    def delete_site(self, site_id):
        with self._lock:
            for i, site in enumerate(self._sites):
                if str(site['id']) == str(site_id):
                    self._sites.pop(i)
                    return True
        return False

    def import_sites(self, sites):
        validated = [validate_fields(site) for site in sites]
        if not validated:
            raise ValueError('Refusing to replace site data with an empty import')
        with self._lock:
            for site in validated:
                site['id'] = str(InMemoryAdapter._next_id)
                InMemoryAdapter._next_id += 1
            InMemoryAdapter._sites = validated
        logger.info('Imported %s sites into memory', len(validated))
        return len(validated)

    def clear_sites(self):
        with self._lock:
            count = len(self._sites)
            InMemoryAdapter._sites = []
        return count


class SQLiteAdapter(DatabaseAdapter):
    def __init__(self, db_path=None):
        self.db_path = os.fspath(db_path or os.environ.get('DATABASE_PATH') or 'nike_sites.db')
        if self.db_path == ':memory:':
            raise ValueError('Use DB_BACKEND=memory for an in-memory database')
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self):
        with closing(self.get_connection()) as conn, conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS nike_sites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_code TEXT NOT NULL,
                    name TEXT,
                    state TEXT,
                    latitude REAL,
                    longitude REAL,
                    description TEXT,
                    site_type TEXT,
                    status TEXT,
                    wiki_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    def get_all_sites(self):
        with closing(self.get_connection()) as conn:
            return [dict(row) for row in conn.execute('SELECT * FROM nike_sites ORDER BY id')]

    def get_site_by_id(self, site_id):
        with closing(self.get_connection()) as conn:
            row = conn.execute('SELECT * FROM nike_sites WHERE id = ?', (site_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def _insert(conn, data):
        columns = ', '.join(data)
        placeholders = ', '.join('?' for _ in data)
        return conn.execute(
            f'INSERT INTO nike_sites ({columns}) VALUES ({placeholders})', tuple(data.values())
        ).lastrowid

    def add_site(self, site_data):
        data = validate_fields(site_data)
        with closing(self.get_connection()) as conn, conn:
            return self._insert(conn, data)

    def update_site(self, site_id, site_data):
        data = validate_fields(site_data, partial=True)
        if not data:
            return self.get_site_by_id(site_id) is not None
        assignments = ', '.join(f'{key} = ?' for key in data)
        with closing(self.get_connection()) as conn, conn:
            cursor = conn.execute(
                f'UPDATE nike_sites SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (*data.values(), site_id),
            )
            return cursor.rowcount > 0

    def delete_site(self, site_id):
        with closing(self.get_connection()) as conn, conn:
            return conn.execute('DELETE FROM nike_sites WHERE id = ?', (site_id,)).rowcount > 0

    def import_sites(self, sites):
        validated = [validate_fields(site) for site in sites]
        if not validated:
            raise ValueError('Refusing to replace site data with an empty import')
        # A failed insert rolls back the entire replacement and releases the connection.
        with closing(self.get_connection()) as conn, conn:
            conn.execute('DELETE FROM nike_sites')
            for site in validated:
                self._insert(conn, site)
        logger.info('Imported %s sites into SQLite', len(validated))
        return len(validated)

    def clear_sites(self):
        with closing(self.get_connection()) as conn, conn:
            return conn.execute('DELETE FROM nike_sites').rowcount


def get_db():
    backend = os.environ.get('DB_BACKEND', 'sqlite').lower()
    if backend == 'memory':
        return InMemoryAdapter()
    if backend == 'sqlite':
        return SQLiteAdapter()
    raise ValueError(f'Unsupported DB_BACKEND: {backend}')
