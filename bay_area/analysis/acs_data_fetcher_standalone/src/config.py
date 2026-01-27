"""
Configuration settings for ACS data fetcher.
"""
from pathlib import Path

# Project directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Census API key location
# Get your free API key from: https://api.census.gov/data/key_signup.html
CENSUS_API_KEY_FILE = PROJECT_ROOT / "api-key.txt"

# Geographic definitions
CA_STATE_FIPS = "06"

# Bay Area counties (name: FIPS code)
BAY_AREA_COUNTIES = {
    'Alameda': '001',
    'Contra Costa': '013',
    'Marin': '041',
    'Napa': '055',
    'San Francisco': '075',
    'San Mateo': '081',
    'Santa Clara': '085',
    'Solano': '095',
    'Sonoma': '097',
}

# API settings
API_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
