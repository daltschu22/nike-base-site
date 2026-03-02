import os
import logging
import sqlite3
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters."""

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


class InMemoryAdapter(DatabaseAdapter):
    """In-memory adapter for ephemeral deployments."""

    _sites = []
    _initialized = False

    def __init__(self):
        logger.info("Using In-Memory database adapter")

    def initialize(self):
        if not InMemoryAdapter._initialized:
            InMemoryAdapter._sites = []
            InMemoryAdapter._initialized = True
            logger.info("In-Memory database initialized")

    def get_all_sites(self):
        return InMemoryAdapter._sites

    def get_site_by_id(self, site_id):
        for site in InMemoryAdapter._sites:
            if str(site.get('id')) == str(site_id):
                return site
        return None

    def add_site(self, site_data):
        if InMemoryAdapter._sites:
            max_id = max(int(site['id']) for site in InMemoryAdapter._sites if 'id' in site)
            new_id = str(max_id + 1)
        else:
            new_id = "1"

        site_data['id'] = new_id
        InMemoryAdapter._sites.append(site_data)
        return new_id

    def update_site(self, site_id, site_data):
        for i, site in enumerate(InMemoryAdapter._sites):
            if str(site.get('id')) == str(site_id):
                InMemoryAdapter._sites[i].update(site_data)
                return True
        return False

    def delete_site(self, site_id):
        for i, site in enumerate(InMemoryAdapter._sites):
            if str(site.get('id')) == str(site_id):
                InMemoryAdapter._sites.pop(i)
                return True
        return False

    def import_sites(self, sites):
        InMemoryAdapter._sites = []
        for i, site in enumerate(sites):
            site_copy = site.copy()
            site_copy['id'] = str(i + 1)
            InMemoryAdapter._sites.append(site_copy)

        logger.info("Imported %s sites into In-Memory database", len(sites))
        return len(sites)


class SQLiteAdapter(DatabaseAdapter):
    """SQLite adapter for local and Render deployments."""

    def __init__(self, db_path=None):
        if db_path is None:
            configured_path = os.environ.get('DATABASE_PATH')
            if configured_path:
                self.db_path = configured_path
            elif os.environ.get('RENDER') == 'true':
                self.db_path = '/tmp/nike_sites.db'
            else:
                self.db_path = os.path.join(os.getcwd(), 'nike_sites.db')
        else:
            self.db_path = db_path

        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        logger.info("Using SQLite database at %s", self.db_path)

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
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

        conn.commit()
        conn.close()
        logger.info("SQLite database initialized")

    def get_all_sites(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM nike_sites')
        sites = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return sites

    def get_site_by_id(self, site_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM nike_sites WHERE id = ?', (site_id,))
        site = cursor.fetchone()
        conn.close()
        return dict(site) if site else None

    def add_site(self, site_data):
        conn = self.get_connection()
        cursor = conn.cursor()

        columns = ', '.join(site_data.keys())
        placeholders = ', '.join(['?' for _ in site_data])
        values = tuple(site_data.values())

        query = f'INSERT INTO nike_sites ({columns}) VALUES ({placeholders})'
        cursor.execute(query, values)

        site_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return site_id

    def update_site(self, site_id, site_data):
        conn = self.get_connection()
        cursor = conn.cursor()

        set_clause = ', '.join([f'{key} = ?' for key in site_data])
        values = tuple(site_data.values()) + (site_id,)

        query = f'UPDATE nike_sites SET {set_clause} WHERE id = ?'
        cursor.execute(query, values)

        conn.commit()
        rowcount = cursor.rowcount
        conn.close()
        return rowcount > 0

    def delete_site(self, site_id):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM nike_sites WHERE id = ?', (site_id,))

        conn.commit()
        rowcount = cursor.rowcount
        conn.close()
        return rowcount > 0

    def import_sites(self, sites):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM nike_sites')

        for site in sites:
            columns = ', '.join(site.keys())
            placeholders = ', '.join(['?' for _ in site])
            values = tuple(site.values())
            query = f'INSERT INTO nike_sites ({columns}) VALUES ({placeholders})'
            cursor.execute(query, values)

        conn.commit()
        conn.close()

        logger.info("Imported %s sites into SQLite database", len(sites))
        return len(sites)


def get_db():
    """Get database adapter based on DB_BACKEND env var."""
    backend = os.environ.get('DB_BACKEND', 'sqlite').lower()
    if backend == 'memory':
        return InMemoryAdapter()
    return SQLiteAdapter()
