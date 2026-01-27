# ACS Data Fetcher

A standalone Python tool for fetching American Community Survey (ACS) data from the U.S. Census Bureau API.

## Features

- Fetch ACS 1-year and 5-year estimates for Bay Area counties
- Support for any ACS table (B08006, B19001, etc.)
- Automatic calculation of derived metrics (percentages, rates)
- Export to CSV for analysis and visualization
- Simple configuration for API keys and geographic areas

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd acs-data-fetcher
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Census API key:
   - Get a free API key from https://api.census.gov/data/key_signup.html
   - Create a file at the path specified in `config.py` (default: `api-key.txt`)
   - Paste your API key into the file

## Usage

### Fetch Commute Data

```bash
python examples/fetch_commute_data.py
```

This fetches work-from-home statistics (B08006_017/B08006_001) for Bay Area counties for 2019 and 2023.

### Fetch Custom Data

```python
from src.acs_fetcher import ACSDataFetcher
from src.config import CENSUS_API_KEY_FILE, BAY_AREA_COUNTIES

# Initialize fetcher
fetcher = ACSDataFetcher(CENSUS_API_KEY_FILE)

# Fetch data
data = fetcher.fetch_table(
    table_code='B19001',  # Household income
    years=[2019, 2023],
    counties=BAY_AREA_COUNTIES,
    dataset='acs1'  # or 'acs5'
)

# Save results
data.to_csv('output/income_data.csv', index=False)
```

## Configuration

Edit `src/config.py` to customize:
- API key file location
- County definitions (FIPS codes)
- Output directory
- State FIPS code

## Project Structure

```
acs-data-fetcher/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration settings
│   └── acs_fetcher.py     # Main data fetching class
├── examples/
│   └── fetch_commute_data.py  # Example: work from home data
└── output/                # Generated CSV files
```

## ACS Tables

Common ACS tables you can fetch:

- **B08006**: Means of Transportation to Work
  - B08006_001: Total workers
  - B08006_017: Worked from home
  
- **B19001**: Household Income in the Past 12 Months
  
- **B25024**: Units in Structure
  
- **B01001**: Sex by Age

Find more tables at: https://api.census.gov/data.html

## Output

Data is saved to the `output/` directory with:
- Individual year files: `table_YEAR.csv`
- Combined file: `table_combined.csv`
- Summary statistics printed to console

## Requirements

- Python 3.8+
- census >= 0.8.19
- pandas >= 1.3.0

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
