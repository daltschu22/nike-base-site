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
    
    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    with app.app_context():
        # Import parts of our application
        from . import routes
        from .database import get_db
        
        try:
            # Initialize the database
            db_adapter = get_db()
            db_adapter.initialize()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")

        return app 
