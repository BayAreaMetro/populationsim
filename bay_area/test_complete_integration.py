#!/usr/bin/env python3
"""
Integration test showing how to rebuild and use the complete maz_taz_all_geog file
in the control generation system.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tm2_control_utils'))

def test_complete_integration():
    """Test the complete workflow: rebuild → configure → verify"""
    from tm2_control_utils.config_census import (
        rebuild_maz_taz_all_geog_file, 
        configure_to_use_rebuilt_geog_file
    )
    import tm2_control_utils.config_census as config
    
    print("=== COMPLETE INTEGRATION TEST ===")
    
    # Step 1: Rebuild the geography file
    print("\n1. REBUILDING GEOGRAPHY FILE...")
    blocks_file = "output_2023/blocks_mazs_tazs_2.5.csv"
    result_df = rebuild_maz_taz_all_geog_file(blocks_file)
    
    if result_df is None:
        print("❌ Failed to rebuild geography file")
        return False
    
    print(f"✅ Successfully rebuilt geography file with {len(result_df)} records")
    
    # Step 2: Configure system to use the rebuilt file
    print("\n2. CONFIGURING SYSTEM TO USE REBUILT FILE...")
    rebuilt_path = configure_to_use_rebuilt_geog_file()
    
    if rebuilt_path is None:
        print("❌ Failed to configure system to use rebuilt file")
        return False
    
    # Step 3: Verify the file is now being used
    print("\n3. VERIFYING CONFIGURATION...")
    print(f"Active MAZ_TAZ_ALL_GEOG_FILE: {config.MAZ_TAZ_ALL_GEOG_FILE}")
    print(f"Expected rebuilt file path: {rebuilt_path}")
    
    if config.MAZ_TAZ_ALL_GEOG_FILE != rebuilt_path:
        print("❌ Configuration failed - still using old file!")
        return False
        
    if os.path.exists(config.MAZ_TAZ_ALL_GEOG_FILE):
        import pandas as pd
        test_df = pd.read_csv(config.MAZ_TAZ_ALL_GEOG_FILE)
        print(f"✅ File loaded successfully: {len(test_df)} records")
        print(f"✅ Columns available: {list(test_df.columns)}")
        
        # Check for the crucial block group column
        if 'GEOID_block group' in test_df.columns:
            bg_count = test_df['GEOID_block group'].nunique()
            print(f"✅ Block group mapping available: {bg_count} unique block groups")
            
            # Verify this is our rebuilt file, not the network one
            if len(test_df) == 109228:  # Our rebuilt file has this many records
                print("✅ Confirmed: Using our rebuilt file (109,228 records)!")
                print("✅ This should resolve the Census control aggregation issues!")
                return True
            else:
                print(f"⚠️  WARNING: File has {len(test_df)} records, expected 109,228 from rebuilt file")
                print("⚠️  May still be using network file instead of rebuilt file")
                return False
        else:
            print("❌ GEOID_block group column missing!")
            return False
    else:
        print(f"❌ File not found: {config.MAZ_TAZ_ALL_GEOG_FILE}")
        return False

if __name__ == "__main__":
    try:
        success = test_complete_integration()
        if success:
            print("\n🎉 INTEGRATION TEST PASSED!")
            print("The system is now configured to use the complete geographic hierarchy.")
            print("This should fix the income control aggregation issues.")
        else:
            print("\n❌ INTEGRATION TEST FAILED!")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
