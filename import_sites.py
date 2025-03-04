#!/usr/bin/env python3
import os
import sys
import logging
import sqlite3
from app.scraper import scrape_nike_sites

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_to_sqlite(sites, db_path='instance/nike_sites.db'):
    """Import Nike sites into SQLite database"""
    # Ensure the instance directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the table if it doesn't exist
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
    
    # Clear existing data
    cursor.execute('DELETE FROM nike_sites')
    
    # Insert the sites
    for site in sites:
        columns = ', '.join(site.keys())
        placeholders = ', '.join(['?' for _ in site])
        values = tuple(site.values())
        
        query = f'INSERT INTO nike_sites ({columns}) VALUES ({placeholders})'
        cursor.execute(query, values)
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    
    logger.info(f"Imported {len(sites)} sites into SQLite database at {db_path}")
    return len(sites)

def main():
    """Main function to scrape and import Nike sites"""
    logger.info("Starting Nike site import process")
    
    # Scrape the Nike sites
    sites = scrape_nike_sites()
    
    if not sites:
        logger.error("No sites were scraped. Import aborted.")
        return 1
    
    logger.info(f"Scraped {len(sites)} Nike sites")
    
    # Import the sites into the database
    import_to_sqlite(sites)
    
    logger.info("Import process completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
