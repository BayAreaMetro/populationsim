"""Fetch B25003 household data from Census API and save to cache."""
from census import Census
import os
import pandas as pd

# Get API key
api_key = os.environ.get('CENSUS_API_KEY')
if not api_key:
    print('CENSUS_API_KEY not set')
    exit(1)

c = Census(api_key)

# Fetch B25003 for Bay Area counties
# B25003_001E = Total occupied housing units (this is household count)
data = c.acs1.get(('B25003_001E',), {'for': 'county:001,013,041,055,075,081,085,095,097', 'in': 'state:06'}, year=2023)

print('B25003_001E (Total Occupied Housing Units = Households):')
total = 0
for row in data:
    hh = int(row['B25003_001E'])
    total += hh
    print(f"  County {row['county']}: {hh:,}")

print(f"\nTotal Bay Area Households: {total:,}")

# Save to cache file
cache_file = r"M:\Data\Census\NewCachedTablesForPopulationSimControls\acs1_2023_B25003_county.csv"
df = pd.DataFrame(data)
df.to_csv(cache_file, index=False)
print(f"\nSaved to: {cache_file}")
