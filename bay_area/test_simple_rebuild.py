#!/usr/bin/env python3
"""
Simple test to rebuild the maz_taz_all_geog file using only the verified blocks file.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tm2_control_utils'))

def test_simple_rebuild():
    """Test the simplified rebuild process"""
    from tm2_control_utils.config_census import rebuild_maz_taz_all_geog_file
    import tm2_control_utils.config_census as config
    
    print("=== SIMPLE REBUILD TEST ===")
    
    # Rebuild using default paths
    print("\n1. REBUILDING GEOGRAPHY FILE...")
    result_df = rebuild_maz_taz_all_geog_file()  # Uses defaults
    
    if result_df is None:
        print("❌ Failed to rebuild geography file")
        return False
    
    print(f"✅ Successfully rebuilt geography file with {len(result_df)} records")
    
    # Check that the active file is now set correctly
    print("\n2. VERIFYING ACTIVE FILE...")
    print(f"Active MAZ_TAZ_ALL_GEOG_FILE: {config.MAZ_TAZ_ALL_GEOG_FILE}")
    
    if config.MAZ_TAZ_ALL_GEOG_FILE and os.path.exists(config.MAZ_TAZ_ALL_GEOG_FILE):
        import pandas as pd
        test_df = pd.read_csv(config.MAZ_TAZ_ALL_GEOG_FILE)
        print(f"✅ File loaded successfully: {len(test_df)} records")
        print(f"✅ Columns available: {list(test_df.columns)}")
        
        # Check for the crucial block group column
        if 'GEOID_block group' in test_df.columns:
            bg_count = test_df['GEOID_block group'].nunique()
            print(f"✅ Block group mapping available: {bg_count} unique block groups")
            
            # Verify this is our rebuilt file with correct record count
            if len(test_df) == 109228:  # Our rebuilt file has this many records
                print("✅ Confirmed: Using our rebuilt file (109,228 records)!")
                print("✅ Ready for Census control aggregation!")
                return True
            else:
                print(f"⚠️  WARNING: File has {len(test_df)} records, expected 109,228")
                return False
        else:
            print("❌ GEOID_block group column missing!")
            return False
    else:
        print(f"❌ Active file not found or not set: {config.MAZ_TAZ_ALL_GEOG_FILE}")
        return False

if __name__ == "__main__":
    try:
        success = test_simple_rebuild()
        if success:
            print("\n🎉 REBUILD TEST PASSED!")
            print("The system is ready to use the rebuilt geography file for control generation.")
        else:
            print("\n❌ REBUILD TEST FAILED!")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
