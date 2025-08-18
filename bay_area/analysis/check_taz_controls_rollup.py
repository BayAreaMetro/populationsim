#!/usr/bin/env python3
"""
Check if TAZ-level household income controls roll up correctly to match
the county-level Census ACS 2023 targets we retrieved.
"""

import pandas as pd
import numpy as np

def main():
    print("Checking TAZ-level income controls rollup to county level...")
    print("=" * 60)
    
    # Load TAZ marginals (income controls)
    print("\nLoading TAZ marginals...")
    taz_marginals = pd.read_csv('output_2023/populationsim_working_dir/data/taz_marginals.csv')
    
    # Load geographic crosswalk
    print("Loading geographic crosswalk...")
    geo_crosswalk = pd.read_csv('output_2023/populationsim_working_dir/data/geo_cross_walk_tm2.csv')
    
    # Create TAZ to county mapping
    taz_to_county = geo_crosswalk[['TAZ', 'COUNTY', 'county_name']].drop_duplicates()
    
    # Load our Census API reference data
    print("Loading Census ACS 2023 reference data...")
    census_data = pd.read_csv('bay_area_income_acs_2023.csv')
    
    print(f"\nTAZ marginals columns: {list(taz_marginals.columns)}")
    print(f"Income control columns: {[col for col in taz_marginals.columns if 'hh_inc' in col]}")
    
    # Merge TAZ marginals with county information
    taz_with_county = taz_marginals.merge(taz_to_county, on='TAZ', how='left')
    
    print(f"\nTAZ marginals shape: {taz_marginals.shape}")
    print(f"TAZ with county shape: {taz_with_county.shape}")
    print(f"Missing county mappings: {taz_with_county['COUNTY'].isna().sum()}")
    
    # Aggregate income controls by county
    income_cols = ['hh_inc_30', 'hh_inc_30_60', 'hh_inc_60_100', 'hh_inc_100_plus']
    
    county_rollup = taz_with_county.groupby(['COUNTY', 'county_name'])[income_cols].sum().reset_index()
    
    # Calculate total households and percentages
    county_rollup['total_households'] = county_rollup[income_cols].sum(axis=1)
    
    for col in income_cols:
        county_rollup[f'{col}_pct'] = (county_rollup[col] / county_rollup['total_households'] * 100).round(1)
    
    print("\n" + "="*80)
    print("TAZ CONTROLS ROLLED UP TO COUNTY LEVEL")
    print("="*80)
    
    # Define county code to name mapping based on our Census data
    county_mapping = {
        1: 'San Francisco',
        13: 'Contra Costa', 
        41: 'Marin',
        55: 'Napa',
        75: 'San Francisco',  # Alternative code
        81: 'San Mateo',
        85: 'Santa Clara',
        95: 'Solano',
        97: 'Sonoma'
    }
    
    for _, row in county_rollup.iterrows():
        county_code = row['COUNTY']
        county_name = row['county_name']
        total_hh = int(row['total_households'])
        
        print(f"\n{county_name} (County {county_code}): {total_hh:,} households")
        print(f"  0-30K:     {row['hh_inc_30']:7.0f} ({row['hh_inc_30_pct']:5.1f}%)")
        print(f"  30K-60K:   {row['hh_inc_30_60']:7.0f} ({row['hh_inc_30_60_pct']:5.1f}%)")
        print(f"  60K-100K:  {row['hh_inc_60_100']:7.0f} ({row['hh_inc_60_100_pct']:5.1f}%)")
        print(f"  100K+:     {row['hh_inc_100_plus']:7.0f} ({row['hh_inc_100_plus_pct']:5.1f}%)")
    
    # Calculate regional totals from TAZ controls
    regional_totals = county_rollup[income_cols].sum()
    regional_total_hh = regional_totals.sum()
    
    print("\n" + "="*80)
    print("REGIONAL TOTALS FROM TAZ CONTROLS")
    print("="*80)
    print(f"Total households: {regional_total_hh:,.0f}")
    print(f"0-30K:     {regional_totals['hh_inc_30']:8.0f} ({regional_totals['hh_inc_30']/regional_total_hh*100:5.1f}%)")
    print(f"30K-60K:   {regional_totals['hh_inc_30_60']:8.0f} ({regional_totals['hh_inc_30_60']/regional_total_hh*100:5.1f}%)")
    print(f"60K-100K:  {regional_totals['hh_inc_60_100']:8.0f} ({regional_totals['hh_inc_60_100']/regional_total_hh*100:5.1f}%)")
    print(f"100K+:     {regional_totals['hh_inc_100_plus']:8.0f} ({regional_totals['hh_inc_100_plus']/regional_total_hh*100:5.1f}%)")
    
    print("\n" + "="*80)
    print("COMPARISON WITH ACS 2023 CENSUS DATA")
    print("="*80)
    
    # Load and display Census reference data
    census_total = census_data['Total_Households'].sum()
    census_0_41k = census_data['$0-41K'].sum()
    census_41_83k = census_data['$41K-83K'].sum()
    census_83_138k = census_data['$83K-138K'].sum()
    census_138k_plus = census_data['$138K+'].sum()
    
    print(f"\nACS 2023 Census (2023 dollars):")
    print(f"Total households: {census_total:,.0f}")
    print(f"0-41K:     {census_0_41k:8.0f} ({census_0_41k/census_total*100:5.1f}%)")
    print(f"41K-83K:   {census_41_83k:8.0f} ({census_41_83k/census_total*100:5.1f}%)")
    print(f"83K-138K:  {census_83_138k:8.0f} ({census_83_138k/census_total*100:5.1f}%)")
    print(f"138K+:     {census_138k_plus:8.0f} ({census_138k_plus/census_total*100:5.1f}%)")
    
    print(f"\nTAZ Controls (labeled as if 2010 dollars?):")
    print(f"Total households: {regional_total_hh:,.0f}")
    print(f"0-30K:     {regional_totals['hh_inc_30']:8.0f} ({regional_totals['hh_inc_30']/regional_total_hh*100:5.1f}%)")
    print(f"30K-60K:   {regional_totals['hh_inc_30_60']:8.0f} ({regional_totals['hh_inc_30_60']/regional_total_hh*100:5.1f}%)")
    print(f"60K-100K:  {regional_totals['hh_inc_60_100']:8.0f} ({regional_totals['hh_inc_60_100']/regional_total_hh*100:5.1f}%)")
    print(f"100K+:     {regional_totals['hh_inc_100_plus']:8.0f} ({regional_totals['hh_inc_100_plus']/regional_total_hh*100:5.1f}%)")
    
    print("\n" + "="*80)
    print("POTENTIAL DOLLAR YEAR MISMATCH ANALYSIS")
    print("="*80)
    
    print("\nIf TAZ controls are actually in 2023 dollars but mislabeled:")
    print("Then 0-30K bracket would capture much less than 0-41K ACS bracket")
    print("And 100K+ bracket would capture much less than 138K+ ACS bracket")
    
    print(f"\nObserved differences:")
    print(f"Low income:  TAZ {regional_totals['hh_inc_30']/regional_total_hh*100:5.1f}% vs ACS {census_0_41k/census_total*100:5.1f}% (diff: {(regional_totals['hh_inc_30']/regional_total_hh - census_0_41k/census_total)*100:+5.1f}pp)")
    print(f"High income: TAZ {regional_totals['hh_inc_100_plus']/regional_total_hh*100:5.1f}% vs ACS {census_138k_plus/census_total*100:5.1f}% (diff: {(regional_totals['hh_inc_100_plus']/regional_total_hh - census_138k_plus/census_total)*100:+5.1f}pp)")
    
    # Check if the bracket alignment makes more sense
    print(f"\nBracket alignment check:")
    print(f"TAZ 0-30K + 30K-60K = {(regional_totals['hh_inc_30'] + regional_totals['hh_inc_30_60'])/regional_total_hh*100:5.1f}% vs ACS 0-41K = {census_0_41k/census_total*100:5.1f}%")
    print(f"This suggests the TAZ brackets may indeed be in different dollar years")
    
    # Save detailed comparison
    comparison_df = pd.DataFrame({
        'source': ['TAZ_Controls', 'ACS_2023'],
        'total_households': [regional_total_hh, census_total],
        'low_income_pct': [regional_totals['hh_inc_30']/regional_total_hh*100, census_0_41k/census_total*100],
        'mid_low_pct': [regional_totals['hh_inc_30_60']/regional_total_hh*100, census_41_83k/census_total*100],
        'mid_high_pct': [regional_totals['hh_inc_60_100']/regional_total_hh*100, census_83_138k/census_total*100],
        'high_income_pct': [regional_totals['hh_inc_100_plus']/regional_total_hh*100, census_138k_plus/census_total*100]
    })
    
    comparison_df.to_csv('taz_controls_vs_census_comparison.csv', index=False)
    print(f"\nDetailed comparison saved to: taz_controls_vs_census_comparison.csv")

if __name__ == '__main__':
    main()
