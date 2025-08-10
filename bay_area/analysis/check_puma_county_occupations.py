#!/usr/bin/env python3
"""
Check which counties the problematic PUMAs belong to
and if zero occupation counts make geographic sense
"""
import pandas as pd

print("CHECKING PUMA-COUNTY MAPPING FOR OCCUPATION ZEROS")
print("="*60)

try:
    # Load crosswalk to see PUMA-County mapping
    crosswalk = pd.read_csv('hh_gq/data/geo_cross_walk_tm2.csv')
    
    # Get unique PUMA-County combinations
    puma_county = crosswalk[['PUMA', 'COUNTY']].drop_duplicates().sort_values('PUMA')
    print(f"PUMA-County mapping:")
    print(puma_county.head(20))
    
    print(f"\nTotal PUMAs: {len(puma_county)}")
    print(f"Counties represented: {sorted(puma_county['COUNTY'].unique())}")
    
    # Load county marginals to see the occupation targets
    county_controls = pd.read_csv('output_2023/county_marginals.csv')
    print(f"\nCounty occupation control totals:")
    occ_cols = [col for col in county_controls.columns if 'pers_occ_' in col]
    for col in occ_cols:
        print(f"  {col}: {county_controls[col].sum():,} total")
    
    # Show county breakdown
    print(f"\nOccupation targets by county:")
    county_controls_display = county_controls[['COUNTY'] + occ_cols]
    print(county_controls_display)
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
print("ANALYSIS:")
print("If some PUMAs within a county have zero people in certain")
print("occupations in the PUMS sample, PopulationSim can't distribute")
print("the county-level targets to those PUMAs (division by zero).")
print("This could be either:")
print("1. Realistic (rural PUMAs with no military/management)")
print("2. PUMS sampling artifact (small occupation categories)")
print("="*60)
