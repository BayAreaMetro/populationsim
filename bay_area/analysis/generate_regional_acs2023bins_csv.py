"""
generate_regional_acs2023bins_csv.py

Fetches ACS 2023 5-year B19001 data for all Bay Area counties, aggregates to canonical 2023$ bins using INCOME_BIN_MAPPING,
and outputs the regional total as required for validation.

Usage:
    python analysis/generate_regional_acs2023bins_csv.py
"""

import os
import pandas as pd
from pathlib import Path

# Ensure tm2_control_utils is on the path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tm2_control_utils.config_census import INCOME_BIN_MAPPING, BAY_AREA_COUNTY_FIPS, CA_STATE_FIPS
from tm2_control_utils.census_fetcher import CensusFetcher

output_path = Path("output_2023/populationsim_working_dir/bay_area_income_acs_2023_bins.csv")

# Fetch B19001 for all counties
fetcher = CensusFetcher()
year = 2023
table = "B19001"
dataset = "acs1"
geo = "county"

county_fips_list = list(BAY_AREA_COUNTY_FIPS.values())
state_fips = CA_STATE_FIPS

# Download ACS5 B19001 for all Bay Area counties
acs_df = fetcher.get_census_data(dataset, year, table, geo)

# Debug: print columns and index
print("[DEBUG] acs_df.columns:", acs_df.columns)
print("[DEBUG] acs_df.index:", acs_df.index)

# Try to filter by 'county' column or index
if 'county' in acs_df.columns:
    acs_df = acs_df[acs_df['county'].isin(county_fips_list)]
elif 'county' in acs_df.index.names:
    acs_df = acs_df.loc[acs_df.index.get_level_values('county').isin(county_fips_list)]
else:
    print("[WARNING] 'county' not found in columns or index; skipping county filter.")


# Handle MultiIndex columns (variable, hhinc_min, hhinc_max) for ACS1
if isinstance(acs_df.columns, pd.MultiIndex):
    # Map from variable name to full MultiIndex columns
    col_map = {var: [col for col in acs_df.columns if col[0] == var] for var in set(sum([b['acs_vars'] for b in INCOME_BIN_MAPPING], []))}
else:
    col_map = {var: [var] for var in set(sum([b['acs_vars'] for b in INCOME_BIN_MAPPING], []))}

# Aggregate to region by summing across counties
bin_labels = []
counts = []
for bin_def in INCOME_BIN_MAPPING:
    acs_vars = bin_def['acs_vars']
    control = bin_def['control']
    label = control + '_2023$'
    # For each acs_var, get all matching columns (MultiIndex or single)
    cols = sum([col_map.get(var, []) for var in acs_vars], [])
    count = acs_df[cols].sum().sum()
    bin_labels.append(label)
    counts.append(count)

total = sum(counts)
shares = [c / total if total > 0 else 0 for c in counts]

# Create pivoted DataFrame
out_df = pd.DataFrame({
    'income': bin_labels,
    'count': counts,
    'share': shares
})

os.makedirs(output_path.parent, exist_ok=True)
out_df.to_csv(output_path, index=False)
print(f"✓ Wrote regional ACS 2023$ bin counts to {output_path} (pivoted)")
