#!/usr/bin/env python3
"""
Diagnostic script to investigate the block group to TAZ mapping issue.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tm2_control_utils'))

def diagnose_bg_taz_mapping():
    """Diagnose the block group to TAZ mapping issue"""
    import pandas as pd
    from tm2_control_utils.config_census import BLOCKS_MAZ_TAZ_FILE
    from tm2_control_utils.geog_utils import add_aggregate_geography_colums
    
    print("=== DIAGNOSING BLOCK GROUP TO TAZ MAPPING ===")
    
    # Load the blocks file
    print("\n1. LOADING BLOCKS FILE...")
    blocks_df = pd.read_csv(BLOCKS_MAZ_TAZ_FILE)
    print(f"   - Loaded {len(blocks_df)} block records")
    
    # Standardize columns and create GEOIDs
    blocks_df.rename(columns={'maz': 'MAZ', 'taz': 'TAZ'}, inplace=True)
    blocks_df['GEOID_block'] = blocks_df['GEOID10'].astype(str).str.zfill(15)
    add_aggregate_geography_colums(blocks_df)
    
    print(f"   - Created {blocks_df['GEOID_block group'].nunique()} unique block groups")
    print(f"   - TAZs: {blocks_df['TAZ'].nunique()} unique")
    
    # Analyze block group to TAZ relationships
    print("\n2. ANALYZING BLOCK GROUP TO TAZ RELATIONSHIPS...")
    
    # Count how many TAZs each block group touches
    bg_taz_counts = blocks_df.groupby('GEOID_block group')['TAZ'].nunique().reset_index()
    bg_taz_counts.columns = ['GEOID_block group', 'num_tazs']
    
    # Summary statistics
    single_taz_bgs = (bg_taz_counts['num_tazs'] == 1).sum()
    multi_taz_bgs = (bg_taz_counts['num_tazs'] > 1).sum()
    
    print(f"   - Block groups in single TAZ: {single_taz_bgs}")
    print(f"   - Block groups spanning multiple TAZs: {multi_taz_bgs}")
    print(f"   - Percentage spanning multiple TAZs: {multi_taz_bgs / len(bg_taz_counts) * 100:.1f}%")
    
    # Look at the distribution of TAZs per block group
    print(f"\n3. DISTRIBUTION OF TAZS PER BLOCK GROUP:")
    taz_distribution = bg_taz_counts['num_tazs'].value_counts().sort_index()
    for num_tazs, count in taz_distribution.head(10).items():
        print(f"   - {count} block groups span {num_tazs} TAZ(s)")
    
    if len(taz_distribution) > 10:
        print(f"   - ... (showing top 10, max TAZs per BG: {taz_distribution.index.max()})")
    
    # Examine some examples of problematic block groups
    print(f"\n4. EXAMPLES OF BLOCK GROUPS SPANNING MANY TAZS:")
    worst_cases = bg_taz_counts.nlargest(5, 'num_tazs')
    
    for _, row in worst_cases.iterrows():
        bg_geoid = row['GEOID_block group']
        num_tazs = row['num_tazs']
        
        # Get the TAZs for this block group
        bg_data = blocks_df[blocks_df['GEOID_block group'] == bg_geoid]
        tazs = sorted(bg_data['TAZ'].unique())
        blocks_per_taz = bg_data.groupby('TAZ').size().to_dict()
        
        print(f"   - Block Group {bg_geoid}: {num_tazs} TAZs")
        print(f"     TAZs: {tazs[:10]}{'...' if len(tazs) > 10 else ''}")
        print(f"     Blocks per TAZ: {dict(list(blocks_per_taz.items())[:5])}{'...' if len(blocks_per_taz) > 5 else ''}")
    
    # Check if there's a pattern with specific counties
    print(f"\n5. CHECKING BY COUNTY:")
    blocks_df['GEOID_county'] = blocks_df['GEOID_block'].str[:5]
    
    county_bg_analysis = blocks_df.groupby('GEOID_county').agg({
        'GEOID_block group': 'nunique',
        'TAZ': 'nunique'
    }).reset_index()
    county_bg_analysis.columns = ['GEOID_county', 'num_block_groups', 'num_tazs']
    
    for _, row in county_bg_analysis.iterrows():
        county = row['GEOID_county']
        county_data = blocks_df[blocks_df['GEOID_county'] == county]
        county_bg_taz = county_data.groupby('GEOID_block group')['TAZ'].nunique()
        multi_taz_in_county = (county_bg_taz > 1).sum()
        
        print(f"   - County {county}: {multi_taz_in_county}/{row['num_block_groups']} BGs span multiple TAZs ({multi_taz_in_county/row['num_block_groups']*100:.1f}%)")
    
    # Check for potential GEOID issues
    print(f"\n6. CHECKING FOR GEOID ISSUES:")
    
    # Look at some sample GEOIDs
    sample_blocks = blocks_df[['GEOID10', 'GEOID_block', 'GEOID_block group']].head(10)
    print("   Sample GEOID conversions:")
    for _, row in sample_blocks.iterrows():
        print(f"     {row['GEOID10']} → {row['GEOID_block']} → {row['GEOID_block group']}")
    
    # Check for any malformed block group GEOIDs
    bg_lengths = blocks_df['GEOID_block group'].str.len()
    if not (bg_lengths == 12).all():
        bad_bg_geoids = blocks_df[bg_lengths != 12]['GEOID_block group'].unique()[:5]
        print(f"   WARNING: Found malformed block group GEOIDs: {bad_bg_geoids}")
    else:
        print("   ✅ All block group GEOIDs are 12 digits")
    
    return blocks_df, bg_taz_counts

if __name__ == "__main__":
    try:
        blocks_df, bg_taz_counts = diagnose_bg_taz_mapping()
        print(f"\n=== DIAGNOSIS COMPLETE ===")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
