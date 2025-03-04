import os
import json
import logging
import sqlite3
from abc import ABC, abstractmethod
from flask import current_app

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseAdapter(ABC):
    """Abstract base class for database adapters"""
    
    @abstractmethod
    def initialize(self):
        """Initialize the database"""
        pass
    
    @abstractmethod
    def get_all_sites(self):
        """Get all Nike sites"""
        pass
    
    @abstractmethod
    def get_site_by_id(self, site_id):
        """Get a Nike site by ID"""
        pass
    
    @abstractmethod
    def add_site(self, site_data):
        """Add a new Nike site"""
        pass
    
    @abstractmethod
    def update_site(self, site_id, site_data):
        """Update an existing Nike site"""
        pass
    
    @abstractmethod
    def delete_site(self, site_id):
        """Delete a Nike site"""
        pass
    
    @abstractmethod
    def import_sites(self, sites):
        """Import multiple sites at once"""
        pass

class InMemoryAdapter(DatabaseAdapter):
    """In-memory database adapter for simple deployments"""
    
    # Class variable to store data across requests
    _sites = []
    _initialized = False
    
    def __init__(self):
        logger.info("Using In-Memory database adapter")
    
    def initialize(self):
        """Initialize the in-memory database"""
        if not InMemoryAdapter._initialized:
            InMemoryAdapter._sites = []
            InMemoryAdapter._initialized = True
            logger.info("In-Memory database initialized")
    
    def get_all_sites(self):
        """Get all Nike sites"""
        return InMemoryAdapter._sites
    
    def get_site_by_id(self, site_id):
        """Get a Nike site by ID"""
        for site in InMemoryAdapter._sites:
            if str(site['id']) == str(site_id):
                return site
        return None
    
    def add_site(self, site_data):
        """Add a new Nike site"""
        # Generate a new ID
        if InMemoryAdapter._sites:
            max_id = max(int(site['id']) for site in InMemoryAdapter._sites if 'id' in site)
            new_id = str(max_id + 1)
        else:
            new_id = "1"
        
        # Add ID to site data
        site_data['id'] = new_id
        
        # Add to sites list
        InMemoryAdapter._sites.append(site_data)
        
        return new_id
    
    def update_site(self, site_id, site_data):
        """Update an existing Nike site"""
        for i, site in enumerate(InMemoryAdapter._sites):
            if str(site['id']) == str(site_id):
                # Update the site
                InMemoryAdapter._sites[i].update(site_data)
                return True
        return False
    
    def delete_site(self, site_id):
        """Delete a Nike site"""
        for i, site in enumerate(InMemoryAdapter._sites):
            if str(site['id']) == str(site_id):
                # Remove the site
                InMemoryAdapter._sites.pop(i)
                return True
        return False
    
    def import_sites(self, sites):
        """Import multiple sites at once"""
        # Clear existing sites
        InMemoryAdapter._sites = []
        
        # Add new sites with IDs
        for i, site in enumerate(sites):
            site_copy = site.copy()
            site_copy['id'] = str(i + 1)
            InMemoryAdapter._sites.append(site_copy)
        
        logger.info(f"Imported {len(sites)} sites into In-Memory database")
        return len(sites)

class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter for local development"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            # Use the instance folder for the database
            self.db_path = os.path.join(current_app.instance_path, 'nike_sites.db')
            # Don't try to create directories - they should already exist in local dev
        else:
            self.db_path = db_path
        
        logger.info(f"Using SQLite database at {self.db_path}")
    
    def get_connection(self):
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    
    def initialize(self):
        """Initialize the SQLite database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create the nike_sites table if it doesn't exist
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
        """Get all Nike sites"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM nike_sites')
        sites = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return sites
    
    def get_site_by_id(self, site_id):
        """Get a Nike site by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM nike_sites WHERE id = ?', (site_id,))
        site = cursor.fetchone()
        
        conn.close()
        return dict(site) if site else None
    
    def add_site(self, site_data):
        """Add a new Nike site"""
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
        """Update an existing Nike site"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clause = ', '.join([f'{key} = ?' for key in site_data])
        values = tuple(site_data.values()) + (site_id,)
        
        query = f'UPDATE nike_sites SET {set_clause} WHERE id = ?'
        cursor.execute(query, values)
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
    
    def delete_site(self, site_id):
        """Delete a Nike site"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM nike_sites WHERE id = ?', (site_id,))
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
    
    def import_sites(self, sites):
        """Import multiple sites at once"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # First, clear existing data
        cursor.execute('DELETE FROM nike_sites')
        
        # Then insert all new sites
        for site in sites:
            columns = ', '.join(site.keys())
            placeholders = ', '.join(['?' for _ in site])
            values = tuple(site.values())
            
            query = f'INSERT INTO nike_sites ({columns}) VALUES ({placeholders})'
            cursor.execute(query, values)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Imported {len(sites)} sites into SQLite database")
        return len(sites)

class VercelKVAdapter(DatabaseAdapter):
    """Vercel KV database adapter for production"""
    
    def __init__(self):
        try:
            # Import the Vercel KV client
            from vercel_kv import VercelKV
            
            # Check if Vercel KV credentials are available
            if not os.environ.get('KV_REST_API_URL') or not os.environ.get('KV_REST_API_TOKEN'):
                raise ValueError("Vercel KV credentials not found in environment variables")
            
            self.kv = VercelKV()
            logger.info("Using Vercel KV database")
        except (ImportError, ValueError) as e:
            logger.error(f"Failed to initialize Vercel KV: {str(e)}")
            raise
    
    def initialize(self):
        """Initialize the Vercel KV database"""
        # No initialization needed for Vercel KV
        logger.info("Vercel KV database initialized")
    
    def get_all_sites(self):
        """Get all Nike sites"""
        try:
            # Get the list of site IDs
            site_ids = self.kv.get('nike_site_ids')
            if not site_ids:
                return []
            
            # Convert from JSON string if needed
            if isinstance(site_ids, str):
                site_ids = json.loads(site_ids)
            
            # Get each site by ID
            sites = []
            for site_id in site_ids:
                site_key = f'nike_site:{site_id}'
                site_data = self.kv.get(site_key)
                if site_data:
                    # Convert from JSON string if needed
                    if isinstance(site_data, str):
                        site_data = json.loads(site_data)
                    sites.append(site_data)
            
            return sites
        except Exception as e:
            logger.error(f"Error getting all sites from Vercel KV: {str(e)}")
            return []
    
    def get_site_by_id(self, site_id):
        """Get a Nike site by ID"""
        try:
            site_key = f'nike_site:{site_id}'
            site_data = self.kv.get(site_key)
            
            # Convert from JSON string if needed
            if isinstance(site_data, str):
                site_data = json.loads(site_data)
            
            return site_data
        except Exception as e:
            logger.error(f"Error getting site {site_id} from Vercel KV: {str(e)}")
            return None
    
    def add_site(self, site_data):
        """Add a new Nike site"""
        try:
            # Get the current list of site IDs
            site_ids = self.kv.get('nike_site_ids')
            if not site_ids:
                site_ids = []
            elif isinstance(site_ids, str):
                site_ids = json.loads(site_ids)
            
            # Generate a new site ID
            site_id = str(max([int(id) for id in site_ids] + [0]) + 1)
            
            # Add the ID to the site data
            site_data['id'] = site_id
            
            # Store the site data
            site_key = f'nike_site:{site_id}'
            self.kv.set(site_key, json.dumps(site_data))
            
            # Update the list of site IDs
            site_ids.append(site_id)
            self.kv.set('nike_site_ids', json.dumps(site_ids))
            
            return site_id
        except Exception as e:
            logger.error(f"Error adding site to Vercel KV: {str(e)}")
            return None
    
    def update_site(self, site_id, site_data):
        """Update an existing Nike site"""
        try:
            site_key = f'nike_site:{site_id}'
            
            # Check if the site exists
            existing_site = self.kv.get(site_key)
            if not existing_site:
                return False
            
            # Update the site data
            if isinstance(existing_site, str):
                existing_site = json.loads(existing_site)
            
            existing_site.update(site_data)
            self.kv.set(site_key, json.dumps(existing_site))
            
            return True
        except Exception as e:
            logger.error(f"Error updating site {site_id} in Vercel KV: {str(e)}")
            return False
    
    def delete_site(self, site_id):
        """Delete a Nike site"""
        try:
            site_key = f'nike_site:{site_id}'
            
            # Check if the site exists
            if not self.kv.get(site_key):
                return False
            
            # Delete the site
            self.kv.delete(site_key)
            
            # Update the list of site IDs
            site_ids = self.kv.get('nike_site_ids')
            if site_ids:
                if isinstance(site_ids, str):
                    site_ids = json.loads(site_ids)
                
                if site_id in site_ids:
                    site_ids.remove(site_id)
                    self.kv.set('nike_site_ids', json.dumps(site_ids))
            
            return True
        except Exception as e:
            logger.error(f"Error deleting site {site_id} from Vercel KV: {str(e)}")
            return False
    
    def import_sites(self, sites):
        """Import multiple sites at once"""
        try:
            # Clear existing data
            site_ids = self.kv.get('nike_site_ids')
            if site_ids:
                if isinstance(site_ids, str):
                    site_ids = json.loads(site_ids)
                
                for site_id in site_ids:
                    site_key = f'nike_site:{site_id}'
                    self.kv.delete(site_key)
            
            # Create new site IDs
            new_site_ids = [str(i+1) for i in range(len(sites))]
            
            # Store each site
            for i, site in enumerate(sites):
                site_id = new_site_ids[i]
                site['id'] = site_id
                site_key = f'nike_site:{site_id}'
                self.kv.set(site_key, json.dumps(site))
            
            # Update the list of site IDs
            self.kv.set('nike_site_ids', json.dumps(new_site_ids))
            
            logger.info(f"Imported {len(sites)} sites into Vercel KV database")
            return len(sites)
        except Exception as e:
            logger.error(f"Error importing sites to Vercel KV: {str(e)}")
            return 0

def get_db():
    """Get the appropriate database adapter based on the environment"""
    # Always use InMemoryAdapter for Vercel environment
    if os.environ.get('VERCEL_ENV') is not None:
        return InMemoryAdapter()
    else:
        return SQLiteAdapter() 
