import requests
from bs4 import BeautifulSoup
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_coordinates(coord_text):
    """
    Extract latitude and longitude from Wikipedia coordinate format.
    Example inputs: 
    - "41°15′36″N 73°58′42″W" (DMS format)
    - "55.90806; 12.43083" (decimal format with semicolon)
    - "55.90806, 12.43083" (decimal format with comma)
    """
    try:
        # First, try the simple decimal format with semicolon separator (most common in the data)
        semicolon_pattern = r'(\d+\.\d+)\s*;\s*(-?\d+\.\d+)'
        semicolon_match = re.search(semicolon_pattern, coord_text)
        
        if semicolon_match:
            latitude, longitude = semicolon_match.groups()
            return float(latitude), float(longitude)
            
        # Pattern for degrees, minutes, seconds format
        dms_pattern = r'(\d+)°(\d+)′(\d+)″([NS])\s+(\d+)°(\d+)′(\d+)″([EW])'
        dms_match = re.search(dms_pattern, coord_text)
        
        if dms_match:
            lat_deg, lat_min, lat_sec, lat_dir, lon_deg, lon_min, lon_sec, lon_dir = dms_match.groups()
            
            # Convert to decimal degrees
            latitude = float(lat_deg) + float(lat_min)/60 + float(lat_sec)/3600
            longitude = float(lon_deg) + float(lon_min)/60 + float(lon_sec)/3600
            
            # Apply direction
            if lat_dir == 'S':
                latitude = -latitude
            if lon_dir == 'W':
                longitude = -longitude
                
            return latitude, longitude
        else:
            # Try general decimal format (comma or space separated)
            decimal_pattern = r'(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)'
            decimal_match = re.search(decimal_pattern, coord_text)
            
            if decimal_match:
                latitude, longitude = decimal_match.groups()
                return float(latitude), float(longitude)
            
            logger.warning(f"Could not parse coordinates: {coord_text}")
            return None, None
    except Exception as e:
        logger.error(f"Error extracting coordinates from '{coord_text}': {str(e)}")
        return None, None

def is_us_state(state_name):
    """
    Check if the given state name is a US state or territory.
    """
    us_states = [
        "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", 
        "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", 
        "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", 
        "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", 
        "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", 
        "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", 
        "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", 
        "Wisconsin", "Wyoming", "District of Columbia", "Puerto Rico", "Guam", "American Samoa",
        "U.S. Virgin Islands", "Northern Mariana Islands"
    ]
    
    # Clean up the state name for comparison
    clean_state = re.sub(r'\[\d+\]', '', state_name).strip()
    
    # Check if it's in our list of US states/territories
    return any(state.lower() in clean_state.lower() for state in us_states)

def scrape_nike_sites():
    """
    Scrape Nike missile site data from Wikipedia.
    Returns a list of dictionaries with site information.
    Focus on US sites only.
    """
    url = "https://en.wikipedia.org/wiki/List_of_Nike_missile_sites"
    logger.info(f"Fetching data from {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        soup = BeautifulSoup(response.text, 'html.parser')
        sites = []
        
        # Find all tables with class wikitable
        tables = soup.find_all('table', class_='wikitable')
        
        # Process each table (each state has its own table)
        for table in tables:
            # Try to find the state name from the preceding heading
            state_heading = table.find_previous(['h2', 'h3', 'h4'])
            state = state_heading.get_text().strip() if state_heading else "Unknown"
            
            # Remove any "[edit]" text that might be in the heading
            state = re.sub(r'\[\w+\]', '', state).strip()
            
            # Skip non-US states
            if not is_us_state(state):
                logger.info(f"Skipping non-US location: {state}")
                continue
                
            logger.info(f"Processing sites for US state: {state}")
            
            # Process rows in the table
            rows = table.find_all('tr')
            
            # Skip header row
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                
                # Skip rows with insufficient data
                if len(cells) < 3:
                    continue
                
                try:
                    # Extract site information (column structure may vary)
                    site_code = cells[0].get_text().strip()
                    site_name = cells[1].get_text().strip() if len(cells) > 1 else ""
                    
                    # Look for coordinates in any cell
                    coordinates = None
                    description = ""
                    
                    for cell in cells:
                        # Check for coordinates
                        coord_span = cell.find('span', class_='geo')
                        if coord_span:
                            coordinates = coord_span.get_text().strip()
                        
                        # Collect text as potential description
                        cell_text = cell.get_text().strip()
                        if cell_text and len(cell_text) > len(description):
                            description = cell_text
                    
                    # Skip entries without coordinates
                    if not coordinates:
                        continue
                    
                    # Extract latitude and longitude
                    latitude, longitude = extract_coordinates(coordinates)
                    
                    if latitude is None or longitude is None:
                        continue
                    
                    # Create site entry
                    site = {
                        'site_code': site_code,
                        'name': site_name,
                        'state': state,
                        'latitude': latitude,
                        'longitude': longitude,
                        'description': description,
                        'site_type': "Unknown",  # Would need more parsing to determine
                        'status': "Unknown",     # Would need more parsing to determine
                        'wiki_url': url
                    }
                    
                    sites.append(site)
                    logger.info(f"Extracted site: {site_code} - {site_name}")
                
                except Exception as e:
                    logger.error(f"Error processing row: {str(e)}")
                    continue
        
        logger.info(f"Extracted {len(sites)} Nike missile sites")
        return sites
    
    except Exception as e:
        logger.error(f"Error scraping Nike sites: {str(e)}")
        return []

if __name__ == "__main__":
    # Test the scraper
    sites = scrape_nike_sites()
    print(f"Found {len(sites)} sites")
    for i, site in enumerate(sites[:5]):
        print(f"Site {i+1}: {site['site_code']} - {site['name']} ({site['latitude']}, {site['longitude']})") 
