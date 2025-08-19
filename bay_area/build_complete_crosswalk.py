"""
build_complete_crosswalk.py

This script builds a complete geographic crosswalk that includes the missing
block group to TAZ/MAZ mappings needed for income control aggregation.

The issue: Income controls are at block group level but the crosswalk only
has MAZ→TAZ→COUNTY→PUMA mapping, missing the block group geographic information.

Solution: Build the complete geographic hierarchy by:
1. Loading the full MAZ/TAZ definitions with block-level GEOIDs
2. Creating block group GEOIDs from block GEOIDs  
3. Mapping block groups to TAZs through block→MAZ→TAZ relationships
4. Creating the missing block group to TAZ crosswalk
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tm2_control_utils'))

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from tm2_control_utils.config_census import *
from tm2_control_utils.geog_utils import add_aggregate_geography_colums

def build_complete_crosswalk():
    """Build complete geographic crosswalk with block group mappings."""
    
    print("=== BUILDING COMPLETE GEOGRAPHIC CROSSWALK ===")
    
    # Step 1: Try to load the full MAZ/TAZ definitions with block-level data
    print("\n1. LOADING MAZ/TAZ DEFINITIONS...")
    
    maz_taz_def_df = None
    
    # Try the network location first (full geography file)
    if os.path.exists(MAZ_TAZ_ALL_GEOG_FILE):
        print(f"   - Loading full geography file: {MAZ_TAZ_ALL_GEOG_FILE}")
        maz_taz_def_df = pd.read_csv(MAZ_TAZ_ALL_GEOG_FILE)
        print(f"   - Loaded {len(maz_taz_def_df)} records")
        print(f"   - Columns: {list(maz_taz_def_df.columns)}")
    else:
        # Fall back to the basic file and build block GEOIDs
        print(f"   - Full geography file not found, using basic file: {MAZ_TAZ_DEF_FILE}")
        if os.path.exists(MAZ_TAZ_DEF_FILE):
            maz_taz_def_df = pd.read_csv(MAZ_TAZ_DEF_FILE)
            print(f"   - Loaded {len(maz_taz_def_df)} records")
            print(f"   - Original columns: {list(maz_taz_def_df.columns)}")
            
            # Convert to standard format
            maz_taz_def_df.rename(columns={"maz": "MAZ", "taz": "TAZ"}, inplace=True)
            
            # Create block GEOID from GEOID10 if available
            if 'GEOID10' in maz_taz_def_df.columns:
                maz_taz_def_df["GEOID_block"] = "0" + maz_taz_def_df["GEOID10"].astype(str)
                print(f"   - Created GEOID_block from GEOID10")
            else:
                print("   ERROR: No GEOID10 column found to create block GEOIDs!")
                return
                
        else:
            print(f"   ERROR: Neither full nor basic MAZ/TAZ definition file found!")
            return
    
    # Step 2: Create aggregate geography columns if not present
    print("\n2. CREATING AGGREGATE GEOGRAPHY COLUMNS...")
    
    if 'GEOID_block' in maz_taz_def_df.columns:
        # Make sure GEOID_block is properly formatted (15 digits)
        maz_taz_def_df['GEOID_block'] = maz_taz_def_df['GEOID_block'].astype(str).str.zfill(15)
        
        # Create higher-level geography columns
        if 'GEOID_block group' not in maz_taz_def_df.columns:
            add_aggregate_geography_colums(maz_taz_def_df)
            print(f"   - Created aggregate geography columns")
        
        print(f"   - Block groups: {maz_taz_def_df['GEOID_block group'].nunique()} unique")
        print(f"   - Tracts: {maz_taz_def_df['GEOID_tract'].nunique()} unique")
        print(f"   - Counties: {maz_taz_def_df['GEOID_county'].nunique()} unique")
    else:
        print("   ERROR: No GEOID_block column found!")
        return
    
    # Step 3: Create block group to TAZ mapping
    print("\n3. CREATING BLOCK GROUP TO TAZ MAPPING...")
    
    # Group by block group and determine the dominant TAZ for each block group
    # This handles cases where a block group spans multiple TAZs
    bg_taz_mapping = maz_taz_def_df.groupby(['GEOID_block group', 'TAZ']).size().reset_index(name='block_count')
    
    # For each block group, find the TAZ with the most blocks
    dominant_taz = bg_taz_mapping.loc[bg_taz_mapping.groupby('GEOID_block group')['block_count'].idxmax()]
    
    print(f"   - Created mappings for {len(dominant_taz)} block groups")
    print(f"   - Block groups with multiple TAZs: {len(bg_taz_mapping) - len(dominant_taz)}")
    
    # Step 4: Build the complete crosswalk
    print("\n4. BUILDING COMPLETE CROSSWALK...")
    
    # Start with the original simplified crosswalk
    original_crosswalk_file = "output_2023/populationsim_working_dir/data/geo_cross_walk_tm2.csv"
    if os.path.exists(original_crosswalk_file):
        crosswalk_df = pd.read_csv(original_crosswalk_file)
        print(f"   - Loaded original crosswalk: {len(crosswalk_df)} records")
    else:
        print("   ERROR: Original crosswalk file not found!")
        return
    
    # Add block and block group information to the crosswalk
    # Map through MAZ since that's the finest level in the original crosswalk
    if 'MAZ' in crosswalk_df.columns and 'MAZ' in maz_taz_def_df.columns:
        # Get unique MAZ→block group mapping
        maz_bg_mapping = maz_taz_def_df[['MAZ', 'GEOID_block', 'GEOID_block group', 'GEOID_tract', 'GEOID_county']].drop_duplicates()
        
        # Merge with crosswalk
        enhanced_crosswalk = pd.merge(
            crosswalk_df,
            maz_bg_mapping,
            on='MAZ',
            how='left'
        )
        
        print(f"   - Enhanced crosswalk: {len(enhanced_crosswalk)} records")
        print(f"   - New columns: {list(set(enhanced_crosswalk.columns) - set(crosswalk_df.columns))}")
        
        # Step 5: Save the enhanced crosswalk
        print("\n5. SAVING ENHANCED CROSSWALK...")
        
        output_file = "output_2023/populationsim_working_dir/data/geo_cross_walk_tm2_enhanced.csv"
        enhanced_crosswalk.to_csv(output_file, index=False)
        print(f"   - Saved enhanced crosswalk to: {output_file}")
        
        # Also create a backup of the original
        backup_file = "output_2023/populationsim_working_dir/data/geo_cross_walk_tm2_original.csv"
        if not os.path.exists(backup_file):
            crosswalk_df.to_csv(backup_file, index=False)
            print(f"   - Backed up original crosswalk to: {backup_file}")
        
        # Step 6: Create block group summary for validation
        print("\n6. CREATING VALIDATION SUMMARY...")
        
        bg_summary = enhanced_crosswalk.groupby(['GEOID_block group', 'TAZ']).agg({
            'MAZ': 'count',
            'COUNTY': 'first',
            'county_name': 'first',
            'PUMA': 'first'
        }).reset_index()
        
        bg_summary.rename(columns={'MAZ': 'num_mazs'}, inplace=True)
        
        summary_file = "output_2023/bg_taz_mapping_summary.csv"
        bg_summary.to_csv(summary_file, index=False)
        print(f"   - Saved block group mapping summary to: {summary_file}")
        
        # Print statistics
        print(f"\n   CROSSWALK STATISTICS:")
        print(f"   - Total records: {len(enhanced_crosswalk)}")
        print(f"   - MAZs: {enhanced_crosswalk['MAZ'].nunique()}")
        print(f"   - TAZs: {enhanced_crosswalk['TAZ'].nunique()}")
        print(f"   - Block groups: {enhanced_crosswalk['GEOID_block group'].nunique()}")
        print(f"   - Blocks: {enhanced_crosswalk['GEOID_block'].nunique()}")
        
        # Check for missing mappings
        missing_bg = enhanced_crosswalk['GEOID_block group'].isna().sum()
        if missing_bg > 0:
            print(f"   - WARNING: {missing_bg} records missing block group mapping")
        
        return enhanced_crosswalk
        
    else:
        print("   ERROR: Cannot merge - MAZ column missing from one of the dataframes!")
        return None

if __name__ == "__main__":
    result = build_complete_crosswalk()
    if result is not None:
        print("\n=== CROSSWALK BUILD COMPLETE ===")
        print("Enhanced crosswalk now includes block group geographic mappings.")
        print("This should resolve the income control aggregation issues.")
    else:
        print("\n=== CROSSWALK BUILD FAILED ===")
        print("Could not create enhanced crosswalk due to missing data.")
