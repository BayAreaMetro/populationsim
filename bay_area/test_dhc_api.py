#!/usr/bin/env python3
"""Quick check of census library capabilities."""

from census import Census

# Read API key
with open('M:/Data/Census/API/new_key/api-key.txt') as f:
    key = f.read().strip()

c = Census(key)

print("Available attributes in Census object:")
attrs = [attr for attr in dir(c) if not attr.startswith('_')]
for attr in attrs:
    attr_obj = getattr(c, attr)
    if hasattr(attr_obj, '__call__'):
        print(f"  {attr} (method)")
    else:
        print(f"  {attr} (attribute)")

print("\n\nTrying direct API call to DHC...")
import requests
dhc_url = f"https://api.census.gov/data/2020/dec/dhc?get=PCT20_001N&for=county:*&in=state:06&key={key}"
print(f"URL: {dhc_url}")

try:
    response = requests.get(dhc_url)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("DHC API is accessible!")
        print(f"Sample data: {response.json()[:3]}")  # Show first 3 rows
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
