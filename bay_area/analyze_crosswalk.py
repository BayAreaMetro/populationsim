#!/usr/bin/env python3
"""
Quick analysis of the created crosswalk file
"""

import pandas as pd
from pathlib import Path

def analyze_crosswalk():
    crosswalk_file = Path("output_2023/geo_cross_walk_tm2_updated.csv")
    
    if not crosswalk_file.exists():
        print(f"❌ Crosswalk file not found: {crosswalk_file}")
        return
    
    print("🔍 ANALYZING CROSSWALK FILE")
    print("=" * 50)
    
    # Load the crosswalk
    df = pd.read_csv(crosswalk_file)
    
    print(f"📊 Total records: {len(df):,}")
    print(f"🌍 Unique MAZs: {df['MAZ'].nunique():,}")
    print(f"🗺️  Unique TAZs: {df['TAZ'].nunique():,}")
    print(f"🏛️  Unique PUMAs: {df['PUMA'].nunique():,}")
    print()
    
    # Show PUMA distribution
    puma_counts = df['PUMA'].value_counts().sort_index()
    print("🏛️  PUMA Distribution (first 20):")
    print(puma_counts.head(20))
    print()
    
    # Show all unique PUMAs
    all_pumas = sorted(df['PUMA'].unique())
    print(f"🏛️  All {len(all_pumas)} unique PUMAs:")
    for i in range(0, len(all_pumas), 10):
        print("   ", all_pumas[i:i+10])
    print()
    
    # County analysis based on PUMA prefixes
    county_analysis = {}
    for puma in all_pumas:
        prefix = str(puma)[:2]
        if prefix == '00':
            county_analysis.setdefault('Alameda (001)', []).append(puma)
        elif prefix == '01':
            county_analysis.setdefault('Alameda (001)', []).append(puma)
        elif prefix == '13':
            county_analysis.setdefault('Contra Costa (013)', []).append(puma)
        elif prefix == '04':
            county_analysis.setdefault('Marin (041)', []).append(puma)
        elif prefix == '05':
            county_analysis.setdefault('Napa (055)', []).append(puma)
        elif prefix == '07':
            county_analysis.setdefault('San Francisco (075)', []).append(puma)
        elif prefix == '08':
            county_analysis.setdefault('San Mateo (081) / Santa Clara (085)', []).append(puma)
        elif prefix == '09':
            county_analysis.setdefault('Solano (095)', []).append(puma)
        elif prefix == '11':
            county_analysis.setdefault('Sonoma (097)', []).append(puma)
        else:
            county_analysis.setdefault('Other', []).append(puma)
    
    print("🏛️  County Analysis:")
    for county, pumas in county_analysis.items():
        print(f"   {county}: {len(pumas)} PUMAs")
        if len(pumas) <= 10:
            print(f"      {pumas}")
        else:
            print(f"      {pumas[:5]} ... {pumas[-5:]}")
    print()
    
    print("✅ Crosswalk analysis complete!")
    print(f"✅ Found {len(all_pumas)} PUMAs covering Bay Area TAZ network")

if __name__ == "__main__":
    analyze_crosswalk()
