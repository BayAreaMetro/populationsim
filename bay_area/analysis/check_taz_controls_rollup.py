#!/usr/bin/env python3
"""
Check if TAZ-level household income controls roll up correctly to match
the county-level Census ACS 2023 targets we retrieved.
"""

import pandas as pd
import numpy as np

import sys
import os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)
from unified_tm2_config import config
from tm2_control_utils.config_census import INCOME_BIN_MAPPING

def main():
    # Use unified config for output path

    output_dir = config.POPSIM_OUTPUT_DIR

    print("\nINCOME BIN MAPPING (Canonical, from config_census.py)")
    print("="*80)
    for bin_def in INCOME_BIN_MAPPING:
        acs_vars_str = ', '.join(bin_def['acs_vars']) if 'acs_vars' in bin_def else ''
        print(f"{bin_def['control']}: 2010$ {bin_def['2010_bin']} | 2023$ {bin_def['2023_bin']} | ACS vars: {acs_vars_str}")
    print("\nAll mapping, reporting, and rollup use this config. No CPI logic or relabeling.")
    print("Checking TAZ-level income controls rollup to county level...")
    print("=" * 60)
    
    # Load TAZ marginals (income controls)
    print("\nLoading TAZ marginals...")
    taz_marginals = pd.read_csv('output_2023/populationsim_working_dir/data/taz_marginals.csv')
    
    # Load geographic crosswalk
    print("Loading geographic crosswalk...")
    from unified_tm2_config import config
    geo_crosswalk = pd.read_csv(config.CROSSWALK_FILES['main_crosswalk'])
    
    # Create TAZ to county mapping
    taz_to_county = geo_crosswalk[['TAZ', 'COUNTY', 'county_name']].drop_duplicates()
    
    # Load our Census API reference data
    print("Loading Census ACS 2023 reference data...")
    # Use ACS 2023 $2010-bins file from config
    census_data = pd.read_csv(config.ACS_2010BINS_FILE)
    
    print(f"\nTAZ marginals columns: {list(taz_marginals.columns)}")
    print(f"Income control columns: {[col for col in taz_marginals.columns if 'hh_inc' in col]}")
    
    # Merge TAZ marginals with county information
    taz_with_county = taz_marginals.merge(taz_to_county, on='TAZ', how='left')
    
    print(f"\nTAZ marginals shape: {taz_marginals.shape}")
    print(f"TAZ with county shape: {taz_with_county.shape}")
    print(f"Missing county mappings: {taz_with_county['COUNTY'].isna().sum()}")
    

    # Use canonical bin order and labels from INCOME_BIN_MAPPING
    income_cols = [b['control'] for b in INCOME_BIN_MAPPING]
    acs_vars_list = [b['acs_vars'] for b in INCOME_BIN_MAPPING]
    bin_labels = [f"{b['2023_bin'][0]:,.0f}-{b['2023_bin'][1]:,.0f}" if b['2023_bin'][1] < 2e6 else f"{b['2023_bin'][0]:,.0f}+" for b in INCOME_BIN_MAPPING]

    county_rollup = taz_with_county.groupby(['COUNTY', 'county_name'])[income_cols].sum().reset_index()

    # Calculate total households and percentages
    county_rollup['total_households'] = county_rollup[income_cols].sum(axis=1)
    for col in income_cols:
        county_rollup[f'{col}_pct'] = (county_rollup[col] / county_rollup['total_households'] * 100).round(1)
    
    print("\n" + "="*80)
    print("TAZ CONTROLS ROLLED UP TO COUNTY LEVEL (Canonical bins)")
    print("="*80)
    for _, row in county_rollup.iterrows():
        county_code = row['COUNTY']
        county_name = row['county_name']
        total_hh = int(row['total_households'])
        print(f"\n{county_name} (County {county_code}): {total_hh:,} households")
        for col, label in zip(income_cols, bin_labels):
            print(f"  {col} [{label}]: {row[col]:7.0f} ({row[col + '_pct']:5.1f}%)")
    

    # Calculate regional totals from TAZ controls
    regional_totals = county_rollup[income_cols].sum()
    regional_total_hh = regional_totals.sum()
    print("\n" + "="*80)
    print("REGIONAL TOTALS FROM TAZ CONTROLS (Canonical bins)")
    print("="*80)
    print(f"Total households: {regional_total_hh:,.0f}")
    for col, label in zip(income_cols, bin_labels):
        print(f"{col} [{label}]: {regional_totals[col]:8.0f} ({regional_totals[col]/regional_total_hh*100:5.1f}%)")
    

    print("\n" + "="*80)
    print("COMPARISON WITH ACS 2023 CENSUS DATA (Canonical bins)")
    print("="*80)
    # Use canonical income_cols for ACS comparison (these are the columns in the 2010bins file)
    census_total = census_data['Total_Households'].sum()
    print(f"Total households: {census_total:,.0f}")
    for col, label in zip(income_cols, bin_labels):
        total = census_data[col].sum() if col in census_data.columns else 0
        pct = total / census_total * 100 if census_total > 0 else 0
        print(f"{col} [{label}]: {total:8.0f} ({pct:5.1f}%)")
    
    

    print("\n" + "="*80)
    print("SIDE-BY-SIDE SUMMARY: TAZ vs ACS (Canonical bins)")
    print("="*80)
    print(f"{'Bin (2023$)':<18} | {'TAZ %':>10} | {'ACS %':>10}")
    print("-"*44)
    taz_pcts = [regional_totals[col]/regional_total_hh*100 if regional_total_hh > 0 else 0 for col in income_cols]
    acs_pcts = [census_data[col].sum() / census_total * 100 if census_total > 0 else 0 for col in income_cols]
    for label, taz_pct, acs_pct in zip(bin_labels, taz_pcts, acs_pcts):
        print(f"{label:<18} | {taz_pct:10.2f} | {acs_pct:10.2f}")
    print("-"*44)
    print("\nNote: All bins, mapping, and reporting are from INCOME_BIN_MAPPING in config_census.py. No CPI logic or relabeling.")
    # Save detailed comparison
    comparison_df = pd.DataFrame({
        'bin_label': bin_labels,
        'taz_pct': taz_pcts,
        'acs_pct': acs_pcts
    })
    output_path = output_dir / 'taz_controls_vs_census_comparison.csv'
    comparison_df.to_csv(output_path, index=False)
    print(f"\nDetailed comparison saved to: {output_path}")

if __name__ == '__main__':
    main()
