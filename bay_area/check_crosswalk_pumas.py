#!/usr/bin/env python3
"""
Check which PUMAs are actually in our crosswalk
"""

import pandas as pd

def main():
    # Load crosswalk
    df = pd.read_csv('output_2023/geo_cross_walk_tm2_updated.csv')
    
    # Get unique PUMAs
    unique_pumas = sorted(df['PUMA'].unique())
    
    print(f"Crosswalk contains {len(unique_pumas)} unique PUMAs:")
    print()
    
    # Group by county
    counties = df.groupby('county_name')['PUMA'].nunique().sort_index()
    print("PUMAs by county:")
    for county, count in counties.items():
        county_pumas = sorted(df[df['county_name'] == county]['PUMA'].unique())
        print(f"  {county}: {count} PUMAs - {county_pumas}")
    
    print()
    print("All PUMAs as list:")
    formatted_pumas = [f"'{puma}'" for puma in unique_pumas]
    
    # Print in groups of 10 for readability
    for i in range(0, len(formatted_pumas), 10):
        chunk = formatted_pumas[i:i+10]
        print(f"  {', '.join(chunk)},")

if __name__ == "__main__":
    main()
