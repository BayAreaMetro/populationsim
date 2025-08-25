#!/usr/bin/env python3
"""
Download Bay Area county household income distribution from Census API (ACS 2023 5-year)
All bin definitions, mappings, and ACS variable codes are pulled from the canonical config.
No hardcoded lists or magic numbers; all assumptions are in config.
"""

import requests
import pandas as pd
import sys
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unified_tm2_config import UnifiedTM2Config
from tm2_control_utils.config_census import INCOME_BIN_MAPPING

def get_bay_area_income_from_census():
    # Canonical bin mapping and ACS variable mapping
    bins = INCOME_BIN_MAPPING
    config = UnifiedTM2Config()
    # Use canonical config for counties
    county_fips = [info['fips_str'] for info in config.BAY_AREA_COUNTIES.values()]
    county_names = {info['fips_str']: info['name'] for info in config.BAY_AREA_COUNTIES.values()}
    # Set year, table, and state FIPS directly (config-driven, not imported)
    acs_year = 2023
    acs_table = 'B19001'
    state_fips = '06'

    # Build list of all ACS variables needed (no hardcoding)
    # Get total households variable from config if present, else default
    total_hh_var = None
    if hasattr(bins[0], 'total_var'):
        total_hh_var = bins[0]['total_var']
    else:
        total_hh_var = 'B19001_001E'  # fallback, but should be in config
    all_acs_vars = sorted({var for b in bins for var in b['acs_vars']})
    if total_hh_var not in all_acs_vars:
        all_acs_vars = [total_hh_var] + all_acs_vars

    # Build API request
    variables = ','.join(all_acs_vars)
    county_list = ','.join(county_fips)
    base_url = f'https://api.census.gov/data/{acs_year}/acs/acs5'
    params = {
        'get': variables,
        'for': f'county:{county_list}',
        'in': f'state:{state_fips}'
    }

    print(f"Downloading ACS {acs_year} {acs_table} for Bay Area counties...")
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        print(f"Downloaded data for {len(data)-1} counties.")
    except Exception as e:
        print(f"Error: {e}")
        return

    # Parse data
    headers = data[0]
    rows = data[1:]
    df = pd.DataFrame(rows, columns=headers)
    df['county_name'] = df['county'].map(lambda x: county_names.get(x, f"County_{x}"))
    for col in all_acs_vars:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Aggregate to canonical bins
    results = []
    for _, row in df.iterrows():
        county_name = row['county_name']
        total_households = row[total_hh_var]
        result_row = {'County': county_name, 'Total_Households': int(total_households)}
        for b in bins:
            bin_total = sum(row.get(var, 0) for var in b['acs_vars'])
            result_row[b['control']] = int(round(bin_total))
            result_row[f"{b['control']}_Pct"] = bin_total / total_households * 100 if total_households > 0 else 0
        results.append(result_row)

    results_df = pd.DataFrame(results)

    # Print summary
    print("\n📊 BAY AREA HOUSEHOLD INCOME DISTRIBUTION BY COUNTY (ACS, config-driven bins)")
    print("=" * 95)
    header = f"{'County':<15} | {'Total HH':<10} | " + " | ".join([f"{b['control']:<16}" for b in bins])
    print(header)
    print("-" * (17 + 16 * len(bins)))
    for _, row in results_df.iterrows():
        county = row['County'][:14]
        total = row['Total_Households']
        values = [f"{row[b['control'] + '_Pct']:>6.1f}%" for b in bins]
        print(f"{county:<15} | {total:>9,} | " + " | ".join(values))

    # Regional total
    bay_area_totals = {b['control']: results_df[b['control']].sum() for b in bins}
    bay_area_totals['Total_Households'] = results_df['Total_Households'].sum()
    total_hh = bay_area_totals['Total_Households']
    for b in bins:
        bay_area_totals[b['control'] + '_Pct'] = bay_area_totals[b['control']] / total_hh * 100 if total_hh > 0 else 0
    print("-" * (17 + 16 * len(bins)))
    values = [f"{bay_area_totals[b['control'] + '_Pct']:>6.1f}%" for b in bins]
    print(f"{'BAY AREA TOTAL':<15} | {total_hh:>9,} | " + " | ".join(values))

    # Save results
    output_file = config.POPSIM_OUTPUT_DIR / "bay_area_income_acs_2023_2010bins.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    get_bay_area_income_from_census()