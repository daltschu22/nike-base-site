#!/usr/bin/env python3
"""Import site data using the same configuration and transactions as the web app."""
import logging
import sys

from config import get_config
from app.database import SQLiteAdapter, get_db
from app.scraper import scrape_nike_sites

logger = logging.getLogger(__name__)


def import_to_sqlite(sites, db_path=None):
    db = SQLiteAdapter(db_path)
    db.initialize()
    return db.import_sites(sites)


def main():
    get_config()  # Load local .env before selecting the database.
    sites = scrape_nike_sites()
    if not sites:
        logger.error('No sites were scraped. Import aborted; existing data preserved.')
        return 1
    try:
        db = get_db()
        db.initialize()
        count = db.import_sites(sites)
    except Exception:
        logger.exception('Import failed')
        return 1
    logger.info('Imported %s site locations', count)
    return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
