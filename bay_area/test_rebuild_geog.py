#!/usr/bin/env python3
"""
Test script to rebuild the maz_taz_all_geog file using the verified 2010 Census blocks.
This will create the complete geographic hierarchy needed for Census control aggregation.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tm2_control_utils'))

from tm2_control_utils.config_census import rebuild_maz_taz_all_geog_file

if __name__ == "__main__":
    # Path to the verified blocks file
    blocks_file = "output_2023/blocks_mazs_tazs_2.5.csv"
    
    # Let function use default output path (will go to PRIMARY_OUTPUT_DIR)
    output_file = None
    
    try:
        print("Testing the rebuild_maz_taz_all_geog_file function...")
        result_df = rebuild_maz_taz_all_geog_file(blocks_file, output_file)
        
        if result_df is not None:
            print(f"\n✅ SUCCESS: Rebuilt geographic file with {len(result_df)} records")
            print(f"Columns created: {list(result_df.columns)}")
            
            # Quick validation - check some block group GEOIDs for proper format
            sample_bg = result_df['GEOID_block group'].head(3).tolist()
            print(f"\nSample block group GEOIDs (should be 12 digits):")
            for bg in sample_bg:
                print(f"  {bg} (length: {len(str(bg))})")
                
        else:
            print("❌ FAILED: Function returned None")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
