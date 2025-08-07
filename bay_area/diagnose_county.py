#!/usr/bin/env python3
"""
Diagnose county mapping issue
"""

import pandas as pd

def diagnose_county_mapping():
    # Load crosswalk
    df = pd.read_csv('output_2023/geo_cross_walk_tm2_updated.csv')
    
    print("=== COUNTY MAPPING DIAGNOSIS ===")
    print(f"Total records: {len(df):,}")
    print(f"Unique PUMAs: {df.PUMA.nunique()}")
    print(f"Unique Counties: {df.COUNTY.nunique()}")
    print()
    
    print("County distribution:")
    county_dist = df.groupby(['COUNTY', 'county_name']).size().reset_index(name='count')
    print(county_dist)
    print()
    
    print("Sample PUMAs:")
    sample_pumas = sorted(df.PUMA.unique())[:20]
    print(sample_pumas)
    print()
    
    print("PUMA-County mapping check:")
    puma_county = df[['PUMA', 'COUNTY', 'county_name']].drop_duplicates().sort_values('PUMA')
    print(puma_county.head(20))
    print()
    
    # Check if all PUMAs are being mapped to county 1 (San Francisco)
    sf_only = (df['COUNTY'] == 1).all()
    print(f"All records mapped to San Francisco: {sf_only}")
    
    if sf_only:
        print("PROBLEM: All PUMAs are being mapped to San Francisco!")
        print("This suggests the PUMA format doesn't match our mapping dictionary")
        
        # Show actual PUMA values
        print(f"Actual PUMA format examples: {df.PUMA.head().tolist()}")
        print(f"PUMA data type: {df.PUMA.dtype}")

if __name__ == "__main__":
    diagnose_county_mapping()
