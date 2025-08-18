#!/usr/bin/env python3
"""
Diagnostic script to verify which Census vintage (2010 vs 2020) we're actually using.
This is critical because the control generation system expects 2010 geography.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tm2_control_utils'))

def check_census_vintage():
    """Check if we're using 2010 or 2020 Census geography"""
    import pandas as pd
    from tm2_control_utils.config_census import BLOCKS_MAZ_TAZ_FILE
    
    print("=== CHECKING CENSUS VINTAGE ===")
    
    # Load the blocks file
    print(f"\n1. LOADING BLOCKS FILE: {BLOCKS_MAZ_TAZ_FILE}")
    blocks_df = pd.read_csv(BLOCKS_MAZ_TAZ_FILE)
    print(f"   - Loaded {len(blocks_df)} block records")
    print(f"   - Columns: {list(blocks_df.columns)}")
    
    # Examine the GEOID structure
    print(f"\n2. EXAMINING GEOID STRUCTURE...")
    sample_geoids = blocks_df['GEOID10'].head(10).tolist()
    
    for geoid in sample_geoids:
        geoid_str = str(geoid).zfill(15)
        state = geoid_str[0:2]
        county = geoid_str[2:5]
        tract = geoid_str[5:11]
        block = geoid_str[11:15]
        
        print(f"   GEOID: {geoid_str}")
        print(f"     State: {state}, County: {county}, Tract: {tract}, Block: {block}")
        
        # Check if this looks like 2010 or 2020 format
        # 2010 blocks are 15 digits: SSCCCTTTTTTBBBB
        # 2020 blocks are also 15 digits but tract structure changed
        
        if len(geoid_str) == 15:
            print(f"     ✅ 15-digit format (could be 2010 or 2020)")
        else:
            print(f"     ❌ Unexpected length: {len(geoid_str)}")
        
        break  # Just check the first one for now
    
    # Check for specific indicators of 2010 vs 2020
    print(f"\n3. CHECKING FOR CENSUS VINTAGE INDICATORS...")
    
    # Look at tract codes - 2010 and 2020 may have different tract numbering
    blocks_df['geoid_str'] = blocks_df['GEOID10'].astype(str).str.zfill(15)
    blocks_df['tract_code'] = blocks_df['geoid_str'].str[5:11]
    
    # Sample tract codes by county
    print("   Sample tract codes by county:")
    for county_fips in ['001', '075', '085']:  # Alameda, SF, Santa Clara
        county_mask = blocks_df['geoid_str'].str[2:5] == county_fips
        if county_mask.any():
            county_tracts = blocks_df[county_mask]['tract_code'].unique()[:5]
            print(f"     County {county_fips}: {list(county_tracts)}")
    
    # Check if the file name or metadata gives us hints
    print(f"\n4. CHECKING FILE METADATA...")
    print(f"   - File path: {BLOCKS_MAZ_TAZ_FILE}")
    print(f"   - Column name: GEOID10 (suggests 2010 vintage)")
    
    # Load a known 2010 reference if available
    print(f"\n5. CROSS-REFERENCE CHECK...")
    
    # Check if we can find any documentation or verify against known 2010 tracts
    # Let's check the total number of tracts - this varies between 2010 and 2020
    unique_tracts = blocks_df['tract_code'].nunique()
    print(f"   - Total unique tracts in file: {unique_tracts}")
    
    # Bay Area had approximately 1,580 tracts in 2010 Census
    # This number changed in 2020 due to tract boundary updates
    if 1570 <= unique_tracts <= 1590:
        print(f"     ✅ Tract count suggests 2010 Census (~1,580 expected)")
    elif 1590 <= unique_tracts <= 1620:
        print(f"     ⚠️  Tract count might suggest 2020 Census")
    else:
        print(f"     ❓ Tract count doesn't match expected ranges")
    
    # Check for any obvious 2020-specific tract codes
    # 2020 Census introduced some new tract numbering patterns
    print(f"\n6. CHECKING FOR 2020-SPECIFIC PATTERNS...")
    
    # In 2020, some areas got new tract codes that weren't in 2010
    # Let's look for any tract codes that might be 2020-specific
    
    # Check block counts per tract - this can be an indicator
    tract_block_counts = blocks_df.groupby('tract_code').size()
    avg_blocks_per_tract = tract_block_counts.mean()
    max_blocks_per_tract = tract_block_counts.max()
    
    print(f"   - Average blocks per tract: {avg_blocks_per_tract:.1f}")
    print(f"   - Max blocks per tract: {max_blocks_per_tract}")
    
    # 2010 tracts typically had different block count distributions than 2020
    
    # Final assessment
    print(f"\n7. ASSESSMENT:")
    print(f"   - File name suggests: 2010 (GEOID10 column)")
    print(f"   - Tract count suggests: {'2010' if 1570 <= unique_tracts <= 1590 else '2020 or uncertain'}")
    print(f"   - Total records: {len(blocks_df)} (2010 Bay Area had ~108K blocks)")
    
    if len(blocks_df) >= 108000 and len(blocks_df) <= 111000:
        print(f"     ✅ Block count consistent with 2010 Bay Area")
    else:
        print(f"     ⚠️  Block count might indicate different vintage")
    
    return blocks_df

if __name__ == "__main__":
    try:
        blocks_df = check_census_vintage()
        print(f"\n=== CENSUS VINTAGE CHECK COMPLETE ===")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
