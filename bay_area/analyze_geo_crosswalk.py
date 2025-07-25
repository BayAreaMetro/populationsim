#!/usr/bin/env python3
"""
Analyze geography crosswalk file and compare to 2020 Bay Area PUMAs
"""

import pandas as pd
import os

def analyze_geo_crosswalk():
    """Analyze the geography crosswalk file"""
    
    # Our 2020 Bay Area PUMAs (54 total)
    bay_area_pumas_2020 = [
        # San Francisco County (7 PUMAs)
        '00101', '00102', '00103', '00104', '00105', '00106', '00107',
        
        # Alameda County (13 PUMAs)
        '01301', '01302', '01303', '01304', '01305', '01306', '01307', 
        '01308', '01309', '01310', '01311', '01312', '01313',
        
        # Contra Costa County (4 PUMAs)
        '04101', '04102', '04103', '04104',
        
        # San Mateo County (1 PUMA)
        '05500',
        
        # Marin County (7 PUMAs)
        '07501', '07502', '07503', '07504', '07505', '07506', '07507',
        
        # Santa Clara County (18 PUMAs)
        '08101', '08102', '08103', '08104', '08105', '08106',
        '08501', '08502', '08503', '08504', '08505', '08506', '08507', 
        '08508', '08509', '08510', '08511', '08512',
        
        # Sonoma County (3 PUMAs)
        '09501', '09502', '09503',
        
        # Napa County (1 PUMA)
        '09702'
    ]
    
    # County mapping
    county_names = {
        1: 'San Francisco',
        13: 'Alameda', 
        7: 'Contra Costa',
        41: 'Marin',
        81: 'San Mateo',
        85: 'Santa Clara',
        97: 'Sonoma',
        55: 'Napa'
    }
    
    print("="*80)
    print("GEOGRAPHY CROSSWALK ANALYSIS - TM2")
    print("="*80)
    
    # Load geography crosswalk
    geo_file = "output_2023/geo_cross_walk_tm2.csv"
    
    if not os.path.exists(geo_file):
        print(f"❌ Geography file not found: {geo_file}")
        return
    
    print(f"📊 Loading geography crosswalk: {geo_file}")
    
    geo_df = pd.read_csv(geo_file, dtype={'PUMA': str, 'COUNTY': int})
    geo_df['PUMA'] = geo_df['PUMA'].astype(str).str.zfill(5)
    
    print(f"   Total MAZ records: {len(geo_df):,}")
    print(f"   Unique MAZs: {geo_df['MAZ'].nunique():,}")
    print(f"   Unique TAZs: {geo_df['TAZ'].nunique():,}")
    print(f"   Unique Counties: {geo_df['COUNTY'].nunique()}")
    print(f"   Unique PUMAs: {geo_df['PUMA'].nunique()}")
    
    # Get unique PUMAs in geography
    geo_pumas = sorted(geo_df['PUMA'].unique())
    
    print(f"\n📋 GEOGRAPHY CROSSWALK PUMAs ({len(geo_pumas)} total):")
    print("="*60)
    
    # Group by county and show PUMAs
    geo_summary = geo_df.groupby(['COUNTY', 'county_name']).agg({
        'PUMA': lambda x: sorted(x.unique()),
        'MAZ': 'nunique',
        'TAZ': 'nunique'
    }).reset_index()
    
    for _, row in geo_summary.iterrows():
        county_code = row['COUNTY']
        county_name = row['county_name']
        pumas = row['PUMA']
        maz_count = row['MAZ']
        taz_count = row['TAZ']
        
        print(f"{county_name} (County {county_code}):")
        print(f"  PUMAs ({len(pumas)}): {pumas}")
        print(f"  MAZs: {maz_count:,}, TAZs: {taz_count:,}")
        print()
    
    print(f"📋 ALL GEOGRAPHY PUMAs:")
    print(geo_pumas)
    print()
    
    # Compare with our 2020 Bay Area PUMAs
    print(f"🔍 COMPARISON WITH 2020 BAY AREA PUMAs:")
    print("="*60)
    
    print(f"Expected 2020 Bay Area PUMAs ({len(bay_area_pumas_2020)} total):")
    print(sorted(bay_area_pumas_2020))
    print()
    
    print(f"Geography crosswalk PUMAs ({len(geo_pumas)} total):")
    print(geo_pumas)
    print()
    
    # Set comparison
    expected_set = set(bay_area_pumas_2020)
    geo_set = set(geo_pumas)
    
    missing_in_geo = expected_set - geo_set
    extra_in_geo = geo_set - expected_set
    common = expected_set & geo_set
    
    print(f"📊 COMPARISON RESULTS:")
    print("="*40)
    print(f"Common PUMAs: {len(common)}")
    print(f"Missing from geography: {len(missing_in_geo)}")
    print(f"Extra in geography: {len(extra_in_geo)}")
    print()
    
    if missing_in_geo:
        print(f"❌ PUMAs in 2020 Bay Area but MISSING from geography:")
        print(f"   {sorted(missing_in_geo)}")
        print()
    
    if extra_in_geo:
        print(f"⚠️  PUMAs in geography but NOT in 2020 Bay Area:")
        print(f"   {sorted(extra_in_geo)}")
        print()
    
    if not missing_in_geo and not extra_in_geo:
        print("✅ Perfect match! Geography crosswalk contains exactly the 2020 Bay Area PUMAs.")
    else:
        print("❌ Mismatch found between geography crosswalk and 2020 Bay Area PUMAs.")
        
        # Show impact
        print(f"\n📈 IMPACT ANALYSIS:")
        if missing_in_geo:
            print(f"   - Seed population has {len(missing_in_geo)} PUMAs not in geography")
            print(f"   - PopulationSim may fail or skip these PUMAs")
        if extra_in_geo:
            print(f"   - Geography has {len(extra_in_geo)} PUMAs not in seed population")  
            print(f"   - These areas will have no seed population data")
    
    # Check for potential year mismatch
    print(f"\n🔍 POTENTIAL YEAR ISSUES:")
    print("="*40)
    
    # Look for patterns that suggest different PUMA years
    puma_patterns = {}
    for puma in geo_pumas:
        prefix = puma[:2]
        if prefix not in puma_patterns:
            puma_patterns[prefix] = []
        puma_patterns[prefix].append(puma)
    
    for prefix, pumas in puma_patterns.items():
        print(f"PUMA prefix {prefix}: {len(pumas)} PUMAs")
        print(f"  {sorted(pumas)}")
    
    return geo_df

if __name__ == "__main__":
    analyze_geo_crosswalk()
