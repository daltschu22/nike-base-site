"""Extract control and launch locations from Wikipedia's US site tables."""
import copy
import logging
import math
import re
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
SOURCE_URL = 'https://en.wikipedia.org/wiki/List_of_Nike_missile_sites'
US_STATES = (
    'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut',
    'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa',
    'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan',
    'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire',
    'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio',
    'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
    'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia',
    'Wisconsin', 'Wyoming', 'District of Columbia', 'Puerto Rico', 'Guam', 'American Samoa',
    'U.S. Virgin Islands', 'Northern Mariana Islands',
)
NUMBER = r'[+-]?\d+(?:\.\d+)?'


def _valid_coordinates(latitude, longitude):
    if math.isfinite(latitude) and math.isfinite(longitude) and -90 <= latitude <= 90 and -180 <= longitude <= 180:
        return latitude, longitude
    return None, None


def extract_coordinates(coord_text):
    if not isinstance(coord_text, str):
        return None, None
    text = coord_text.replace('\ufeff', '').strip()
    # Match direction formats first so a south/west hemisphere sign is not lost.
    component = r'(\d+(?:\.\d+)?)\s*°\s*(?:(\d+(?:\.\d+)?)\s*[′\']\s*)?(?:(\d+(?:\.\d+)?)\s*[″"]\s*)?'
    match = re.search(component + r'([NS])\s*[,;]?\s*' + component + r'([EW])', text, re.I)
    if match:
        lat_deg, lat_min, lat_sec, lat_dir, lon_deg, lon_min, lon_sec, lon_dir = match.groups()
        lat_min, lat_sec, lon_min, lon_sec = (float(x or 0) for x in (lat_min, lat_sec, lon_min, lon_sec))
        if any(x >= 60 for x in (lat_min, lat_sec, lon_min, lon_sec)):
            return None, None
        lat = (float(lat_deg) + lat_min / 60 + lat_sec / 3600) * (-1 if lat_dir.upper() == 'S' else 1)
        lon = (float(lon_deg) + lon_min / 60 + lon_sec / 3600) * (-1 if lon_dir.upper() == 'W' else 1)
        return _valid_coordinates(lat, lon)
    match = re.search(rf'(?<![\d.+-])({NUMBER})\s*(?:[;,]\s*|\s+)({NUMBER})(?![\d.])', text)
    if match:
        return _valid_coordinates(*(float(value) for value in match.groups()))
    return None, None


def _states_in(text):
    # Prefer longer names to avoid matching Virginia inside West Virginia.
    found = []
    remaining = text
    for state in sorted(US_STATES, key=len, reverse=True):
        pattern = rf'(?<!\w){re.escape(state)}(?!\w)'
        if re.search(pattern, remaining, re.I):
            found.append(state)
            remaining = re.sub(pattern, '', remaining, flags=re.I)
    return found


def is_us_state(state_name):
    return bool(_states_in(state_name))


def _clean_text(element, *, remove_coordinates=False):
    element = copy.deepcopy(element)
    for node in element.select('sup, .mw-editsection'):
        node.decompose()
    if remove_coordinates:
        for node in element.select('.geo-inline, .geo-default, .geo-nondefault, .geo-multi-punct, .geo, .geo-dec, .geo-dms'):
            node.decompose()
    return re.sub(r'\s+', ' ', element.get_text(' ', strip=True)).replace('\ufeff', '').strip()


def _table_rows(table):
    """Expand row/column spans without absorbing rows from nested tables."""
    pending = {}
    for row in table.find_all('tr'):
        if row.find_parent('table') is not table:
            continue
        cells, column = [], 0
        for cell in row.find_all(['td', 'th'], recursive=False):
            while column in pending:
                node, count = pending.pop(column)
                cells.append(node)
                if count > 1:
                    pending[column] = (node, count - 1)
                column += 1
            for _ in range(int(cell.get('colspan', 1))):
                cells.append(cell)
                if int(cell.get('rowspan', 1)) > 1:
                    pending[column] = (cell, int(cell['rowspan']) - 1)
                column += 1
        while column in pending:
            node, count = pending.pop(column)
            cells.append(node)
            if count > 1:
                pending[column] = (node, count - 1)
            column += 1
        yield cells


def parse_nike_sites(html):
    soup = BeautifulSoup(html, 'html.parser')
    sites, seen = [], set()
    for table in soup.select('table.wikitable'):
        country_heading = table.find_previous('h2')
        state_heading = table.find_previous(['h3', 'h4'])
        if not country_heading or _clean_text(country_heading) != 'United States' or not state_heading:
            continue
        state = _clean_text(state_heading)
        if not is_us_state(state):
            continue
        rows = iter(_table_rows(table))
        headers = [_clean_text(cell).lower() for cell in next(rows, [])]
        if not headers or headers[0] not in ('site name', 'code & location'):
            continue
        location_column = headers.index('site location') if 'site location' in headers else 0
        area_columns = [(i, 'Control' if header.startswith('control') else 'Launch')
                        for i, header in enumerate(headers) if header.startswith(('control site', 'launch site'))]
        for cells in rows:
            if len(cells) < len(headers):
                logger.debug('Skipping incomplete site row in %s', state)
                continue
            code_and_name = _clean_text(cells[0])
            if not code_and_name:
                continue
            site_code = code_and_name.split(' ', 1)[0] if headers[0] == 'code & location' else code_and_name
            location = _clean_text(cells[location_column])
            explicit_states = _states_in(location)
            site_state = explicit_states[0] if len(explicit_states) == 1 else state
            for column, site_type in area_columns:
                cell = cells[column]
                for geo in cell.select('.geo'):
                    latitude, longitude = extract_coordinates(geo.get_text(' ', strip=True))
                    if latitude is None:
                        continue
                    identity = (site_code, site_type, latitude, longitude)
                    if identity in seen:
                        continue
                    seen.add(identity)
                    sites.append({
                        'site_code': site_code,
                        'name': f'{location or site_code} — {site_type} area',
                        'state': site_state,
                        'latitude': latitude,
                        'longitude': longitude,
                        'description': _clean_text(cell, remove_coordinates=True),
                        'site_type': site_type,
                        'status': 'Unknown',
                        'wiki_url': f'{SOURCE_URL}#{quote(state.replace(" ", "_"), safe="/_")}',
                    })
    return sites


def scrape_nike_sites():
    try:
        response = requests.get(SOURCE_URL, headers={
            'User-Agent': 'nike-base-site/1.0 (+https://github.com/daltschu22/nike-base-site)',
            'Accept': 'text/html',
        }, timeout=30)
        response.raise_for_status()
        sites = parse_nike_sites(response.text)
        logger.info('Extracted %s Nike site locations', len(sites))
        return sites
    except requests.RequestException:
        logger.exception('Failed to fetch Nike sites')
        return []


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print(f'Found {len(scrape_nike_sites())} site locations')
