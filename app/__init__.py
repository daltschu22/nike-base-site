from flask import Flask
from config import get_config
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    """Initialize the core application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(get_config())
    
    # No filesystem operations - we'll use in-memory storage only
    # This is important for Vercel deployment which has a read-only filesystem

    with app.app_context():
        # Import parts of our application
        from . import routes
        from .database import get_db
        from .scraper import scrape_nike_sites
        
        try:
            # Initialize the database
            db_adapter = get_db()
            db_adapter.initialize()
            logger.info("Database initialized successfully")
            
            # Check if there's data in the database
            sites = db_adapter.get_all_sites()
            if not sites:
                logger.info("No Nike missile sites found in database. Loading data automatically...")
                try:
                    # Scrape data from Wikipedia
                    sites_data = scrape_nike_sites()
                    if sites_data:
                        # Import data into database
                        imported_count = db_adapter.import_sites(sites_data)
                        logger.info(f"Successfully imported {imported_count} Nike missile sites on startup.")
                    else:
                        logger.warning("No data found during automatic scraping.")
                except Exception as e:
                    logger.error(f"Error during automatic data import: {str(e)}")
            else:
                logger.info(f"Found {len(sites)} Nike missile sites in database.")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")

        return app

# Create the application instance
app = create_app() 
