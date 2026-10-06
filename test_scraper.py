from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from app.scraper import extract_coordinates, is_us_state, parse_nike_sites, scrape_nike_sites


@pytest.mark.parametrize('text,expected', [
    ('41°15′36″N 73°58′42″W', (41.26, -73.97833333333333)),
    ('55.90806; 12.43083', (55.90806, 12.43083)),
    ('-33.5; -70.5', (-33.5, -70.5)),
    ('0; 0', (0, 0)),
    ('41, -73', (41, -73)),
    ('41.5 -73.5', (41.5, -73.5)),
    ('33°30\'0"S 70°30\'0"W', (-33.5, -70.5)),
    ('33.5°S 70.5°W', (-33.5, -70.5)),
    ('41°30′N 73°30′W', (41.5, -73.5)),
    ('91; -73', (None, None)),
    ('41; 181', (None, None)),
    ('41°61′0″N 73°0′0″W', (None, None)),
    ('not coordinates', (None, None)),
    (None, (None, None)),
])
def test_coordinates(text, expected):
    actual = extract_coordinates(text)
    assert actual == pytest.approx(expected) if expected[0] is not None else actual == expected


def test_states_use_word_boundaries():
    assert is_us_state('Illinois and Northwest Indiana')
    assert is_us_state('West Virginia [edit]')
    assert not is_us_state('New Yorkshire')
    assert not is_us_state('Denmark')


def test_source_columns_and_distinct_areas():
    sites = parse_nike_sites(Path('tests/fixtures/sites.html').read_text())
    assert len(sites) == 5
    assert [site['site_type'] for site in sites[:2]] == ['Control', 'Launch']
    assert sites[0]['name'] == 'Sausalito, California — Control area'
    assert sites[0]['description'] == 'Radar remains.'
    assert sites[1]['description'] == 'Preserved.'
    assert sites[2]['state'] == 'Indiana'
    assert sites[3]['site_code'] == 'M-02'
    assert 'Brown Deer Rd' in sites[3]['name']
    assert all(site['site_code'] not in ('Foreign', 'SF-00') for site in sites)


def test_row_spans_do_not_shift_columns():
    html = '''<h2>United States</h2><h3>California</h3><table class="wikitable">
    <tr><th>Site Name</th><th>Site Location</th><th>Control Site condition/owner</th></tr>
    <tr><td rowspan="2">SF-1</td><td>A</td><td><span class="geo">37; -122</span></td></tr>
    <tr><td>B</td><td><span class="geo">38; -122</span></td></tr></table>'''
    sites = parse_nike_sites(html)
    assert len(sites) == 2
    assert sites[1]['site_code'] == 'SF-1'
    assert sites[1]['name'] == 'B — Control area'


def test_network_failure_returns_empty_without_live_requests():
    with patch('app.scraper.requests.get', side_effect=requests.Timeout):
        assert scrape_nike_sites() == []


def test_http_failure_returns_empty():
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError('503')
    with patch('app.scraper.requests.get', return_value=response):
        assert scrape_nike_sites() == []
