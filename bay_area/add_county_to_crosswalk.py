#!/usr/bin/env python3
"""
Add county mapping to our 62-PUMA crosswalk
"""

import pandas as pd
from pathlib import Path

def add_county_mapping():
    """Add county and county_name columns to crosswalk"""
    
    # PUMA to County mapping for TM2 (62 Bay Area PUMAs)
    PUMA_COUNTY_MAPPING = {
        # San Francisco County (COUNTY=1)
        '00101': 1, '00111': 1, '00112': 1, '00113': 1, '00114': 1, '00115': 1, 
        '00116': 1, '00117': 1, '00118': 1, '00119': 1, '00120': 1, '00121': 1, 
        '00122': 1, '00123': 1,
        # San Mateo County (COUNTY=2)  
        '05303': 2, '05500': 2,
        # Santa Clara County (COUNTY=3)
        '08101': 3, '08102': 3, '08103': 3, '08104': 3, '08105': 3, '08106': 3,
        '08505': 3, '08506': 3, '08507': 3, '08508': 3, '08510': 3, '08511': 3,
        '08512': 3, '08515': 3, '08516': 3, '08517': 3, '08518': 3, '08519': 3,
        '08520': 3, '08521': 3, '08522': 3, '08701': 3,
        # Alameda County (COUNTY=4)
        '01301': 4, '01305': 4, '01308': 4, '01309': 4, '01310': 4, '01311': 4,
        '01312': 4, '01313': 4, '01314': 4,
        # Contra Costa County (COUNTY=5)
        '04103': 5, '04104': 5,
        # Solano County (COUNTY=6)
        '11301': 6,
        # Napa County (COUNTY=7)
        '09702': 7, '09704': 7, '09705': 7, '09706': 7,
        # Sonoma County (COUNTY=8)
        '09501': 8, '09502': 8, '09503': 8,
        # Marin County (COUNTY=9)
        '07507': 9, '07508': 9, '07509': 9, '07510': 9, '07511': 9, '07512': 9,
        '07513': 9, '07514': 9
    }
    
    COUNTY_NAMES = {
        1: 'San Francisco',
        2: 'San Mateo', 
        3: 'Santa Clara',
        4: 'Alameda',
        5: 'Contra Costa',
        6: 'Solano',
        7: 'Napa',
        8: 'Sonoma',
        9: 'Marin'
    }
    
    # Load current crosswalk
    crosswalk_path = Path("output_2023/geo_cross_walk_tm2_updated.csv")
    print(f"Loading crosswalk: {crosswalk_path}")
    
    df = pd.read_csv(crosswalk_path)
    print(f"Original shape: {df.shape}")
    print(f"Original PUMAs: {df.PUMA.nunique()}")
    
    # Add county mapping
    df['COUNTY'] = df['PUMA'].map(PUMA_COUNTY_MAPPING)
    df['county_name'] = df['COUNTY'].map(COUNTY_NAMES)
    
    # Check for missing mappings
    missing_pumas = df[df['COUNTY'].isna()]['PUMA'].unique()
    if len(missing_pumas) > 0:
        print(f"⚠️  Missing county mapping for PUMAs: {missing_pumas}")
        # Fill with default (San Francisco)
        df['COUNTY'] = df['COUNTY'].fillna(1)
        df['county_name'] = df['county_name'].fillna('San Francisco')
    
    # Ensure integer types
    df['COUNTY'] = df['COUNTY'].astype(int)
    
    # Reorder columns
    df = df[['MAZ', 'TAZ', 'PUMA', 'COUNTY', 'county_name']]
    
    # Save updated crosswalk
    df.to_csv(crosswalk_path, index=False)
    
    print(f"✅ Updated crosswalk saved: {crosswalk_path}")
    print(f"Final shape: {df.shape}")
    print(f"Final PUMAs: {df.PUMA.nunique()}")
    print(f"Final counties: {df.COUNTY.nunique()}")
    print("County distribution:")
    print(df.groupby(['COUNTY', 'county_name']).size().head(10))
    
    return True

if __name__ == "__main__":
    add_county_mapping()
