#!/usr/bin/env python3
from app.scraper import scrape_nike_sites

# Run the scraper
sites = scrape_nike_sites()

# Print summary
print(f"Total sites found: {len(sites)}")

# Print first 5 sites
print("\nFirst 5 sites:")
for i, site in enumerate(sites[:5]):
    print(f"{i+1}. {site['site_code']} - {site['name']} ({site['state']}): {site['latitude']}, {site['longitude']}")

# Check for sites with negative coordinates (likely in the US)
us_sites = [site for site in sites if site['longitude'] < 0]
print(f"\nSites with negative longitude (likely US): {len(us_sites)}")

# Print distribution by state
states = {}
for site in sites:
    state = site['state']
    if state not in states:
        states[state] = 0
    states[state] += 1

print("\nSites by state/country:")
for state, count in sorted(states.items()):
    print(f"{state}: {count}") 
