from flask import current_app as app
from flask import render_template, jsonify, request, abort
from .database import get_db
from .scraper import scrape_nike_sites
import logging
import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Context processor to add current datetime to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

@app.route('/')
def index():
    """Render the homepage with the map."""
    # Get Google Maps API key from environment or config
    google_maps_api_key = os.environ.get('GOOGLE_MAPS_API_KEY') or app.config.get('GOOGLE_MAPS_API_KEY', '')
    
    if not google_maps_api_key:
        logger.warning("Google Maps API key not set. Map functionality will be limited.")
    
    return render_template('index.html', google_maps_api_key=google_maps_api_key)

@app.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')

@app.route('/api/sites')
def get_sites():
    """API endpoint to get all Nike missile sites."""
    try:
        # Get database adapter
        db_adapter = get_db()
        
        # Get query parameters for filtering
        state = request.args.get('state')
        site_type = request.args.get('site_type')
        
        # Get all sites
        sites = db_adapter.get_all_sites()
        
        # Apply filters if provided
        if state:
            state = state.lower()
            sites = [site for site in sites if site['state'] and state in site['state'].lower()]
        if site_type:
            sites = [site for site in sites if site['site_type'] == site_type]
            
        return jsonify({
            'success': True,
            'count': len(sites),
            'sites': sites
        })
    except Exception as e:
        logger.error(f"Error retrieving sites: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sites/<site_id>')
def get_site(site_id):
    """API endpoint to get a specific Nike missile site."""
    try:
        # Get database adapter
        db_adapter = get_db()
        
        # Get the site
        site = db_adapter.get_site_by_id(site_id)
        
        if not site:
            return jsonify({
                'success': False,
                'error': 'Site not found'
            }), 404
            
        return jsonify({
            'success': True,
            'site': site
        })
    except Exception as e:
        logger.error(f"Error retrieving site {site_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/import-data', methods=['POST'])
def import_data():
    """Import Nike missile site data from Wikipedia."""
    try:
        # Get database adapter
        db_adapter = get_db()
        
        # Initialize the database
        db_adapter.initialize()
        
        # Scrape data from Wikipedia
        sites_data = scrape_nike_sites()
        
        if not sites_data:
            return jsonify({
                'success': False,
                'message': 'No data found or error occurred during scraping.'
            }), 500
            
        # Import data into database
        imported_count = db_adapter.import_sites(sites_data)
        
        return jsonify({
            'success': True,
            'message': f'Successfully imported {imported_count} Nike missile sites.'
        })
    except Exception as e:
        logger.error(f"Error importing data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/clear-data', methods=['POST'])
def clear_data():
    """Clear all Nike missile site data from the database."""
    try:
        # Get database adapter
        db_adapter = get_db()
        
        # Get all sites
        sites = db_adapter.get_all_sites()
        
        # Delete each site
        for site in sites:
            db_adapter.delete_site(site['id'])
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {len(sites)} Nike missile sites.'
        })
    except Exception as e:
        logger.error(f"Error clearing data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 
