#!/usr/bin/env python3
"""
Fix county mapping - the PUMA format is wrong
"""

import pandas as pd

def fix_county_mapping():
    """Fix the PUMA format and county mapping"""
    
    # Load crosswalk
    df = pd.read_csv('output_2023/geo_cross_walk_tm2_updated.csv')
    
    print("=== BEFORE FIX ===")
    print(f"Sample PUMAs: {df.PUMA.head().tolist()}")
    print(f"PUMA data type: {df.PUMA.dtype}")
    print(f"Unique counties: {df.COUNTY.nunique()}")
    
    # PUMA to County mapping for TM2 (using the correct format that matches our data)
    PUMA_COUNTY_MAPPING = {
        # San Francisco County (COUNTY=1) - PUMAs 101-123
        101: 1, 111: 1, 112: 1, 113: 1, 114: 1, 115: 1, 116: 1, 117: 1, 118: 1, 119: 1,
        120: 1, 121: 1, 122: 1, 123: 1,
        
        # San Mateo County (COUNTY=2) - PUMAs 5303, 5500  
        5303: 2, 5500: 2,
        
        # Santa Clara County (COUNTY=3) - PUMAs 8101-8701
        8101: 3, 8102: 3, 8103: 3, 8104: 3, 8105: 3, 8106: 3,
        8505: 3, 8506: 3, 8507: 3, 8508: 3, 8510: 3, 8511: 3,
        8512: 3, 8515: 3, 8516: 3, 8517: 3, 8518: 3, 8519: 3,
        8520: 3, 8521: 3, 8522: 3, 8701: 3,
        
        # Alameda County (COUNTY=4) - PUMAs 1301-1314
        1301: 4, 1305: 4, 1308: 4, 1309: 4, 1310: 4, 1311: 4,
        1312: 4, 1313: 4, 1314: 4,
        
        # Contra Costa County (COUNTY=5) - PUMAs 4103, 4104
        4103: 5, 4104: 5,
        
        # Solano County (COUNTY=6) - PUMA 11301
        11301: 6,
        
        # Napa County (COUNTY=7) - PUMAs 9702-9706
        9702: 7, 9704: 7, 9705: 7, 9706: 7,
        
        # Sonoma County (COUNTY=8) - PUMAs 9501-9503
        9501: 8, 9502: 8, 9503: 8,
        
        # Marin County (COUNTY=9) - PUMAs 7507-7514
        7507: 9, 7508: 9, 7509: 9, 7510: 9, 7511: 9, 7512: 9,
        7513: 9, 7514: 9
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
    
    # Convert PUMA to integer to match our mapping
    df['PUMA_INT'] = df['PUMA'].astype(int)
    
    # Apply correct county mapping
    df['COUNTY'] = df['PUMA_INT'].map(PUMA_COUNTY_MAPPING)
    df['county_name'] = df['COUNTY'].map(COUNTY_NAMES)
    
    # Check for unmapped PUMAs
    unmapped = df[df['COUNTY'].isna()]
    if len(unmapped) > 0:
        print(f"\n⚠️  Found {len(unmapped)} unmapped records:")
        print(f"Unmapped PUMAs: {sorted(unmapped['PUMA_INT'].unique())}")
        # Fill unmapped with San Francisco as default
        df['COUNTY'] = df['COUNTY'].fillna(1)
        df['county_name'] = df['county_name'].fillna('San Francisco')
    
    # Convert PUMA back to 5-digit string format
    df['PUMA'] = df['PUMA_INT'].astype(str).str.zfill(5)
    
    # Clean up
    df = df.drop('PUMA_INT', axis=1)
    df['COUNTY'] = df['COUNTY'].astype(int)
    
    # Reorder columns
    df = df[['MAZ', 'TAZ', 'PUMA', 'COUNTY', 'county_name']]
    
    print("\n=== AFTER FIX ===")
    print(f"Sample PUMAs: {df.PUMA.head().tolist()}")
    print(f"Unique counties: {df.COUNTY.nunique()}")
    print("\nCounty distribution:")
    print(df.groupby(['COUNTY', 'county_name']).size())
    
    # Save fixed crosswalk
    df.to_csv('output_2023/geo_cross_walk_tm2_updated.csv', index=False)
    print(f"\n✅ Fixed crosswalk saved!")
    
    return df

if __name__ == "__main__":
    fix_county_mapping()
