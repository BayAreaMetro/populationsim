#!/usr/bin/env python3
"""
Quick test script to verify MAZ_NODE/TAZ_NODE column naming changes
"""

import sys
sys.path.append('.')

def test_column_naming():
    """Quick test of our column naming changes"""
    print("="*60)
    print("QUICK TEST: MAZ_NODE/TAZ_NODE COLUMN NAMING CHANGES")
    print("="*60)
    
    # Test 1: Config initialization
    try:
        from unified_tm2_config import UnifiedTM2Config
        config = UnifiedTM2Config()
        print("✓ Config initialization successful")
    except Exception as e:
        print(f"✗ Config initialization failed: {e}")
        return False
    
    # Test 2: Check existing crosswalk format
    try:
        import pandas as pd
        crosswalk_file = config.CROSSWALK_FILES['popsim_crosswalk']
        print(f"\nChecking existing crosswalk: {crosswalk_file}")
        
        if crosswalk_file.exists():
            df = pd.read_csv(crosswalk_file)
            print(f"Current columns: {list(df.columns)}")
            print(f"Shape: {df.shape}")
            print("Sample data:")
            print(df.head(2))
            
            # Check if we have old or new format
            has_old_format = 'MAZ' in df.columns and 'TAZ' in df.columns
            has_new_format = 'MAZ_NODE' in df.columns and 'TAZ_NODE' in df.columns
            
            if has_old_format:
                print("⚠️  Currently using OLD format (MAZ, TAZ)")
                print("   Need to regenerate crosswalk with new naming")
            elif has_new_format:
                print("✓ Already using NEW format (MAZ_NODE, TAZ_NODE)")
            else:
                print("? Unknown format - neither old nor new columns found")
                
        else:
            print(f"✗ Crosswalk file not found: {crosswalk_file}")
            
    except Exception as e:
        print(f"✗ Crosswalk check failed: {e}")
        return False
    
    # Test 3: Check postprocess_recode column mapping
    try:
        from postprocess_recode import HOUSING_COLUMNS
        tm2_columns = HOUSING_COLUMNS['TM2']
        print(f"\nTM2 Housing column mapping:")
        for pop_col, activity_col in tm2_columns.items():
            if 'MAZ' in pop_col or 'TAZ' in pop_col:
                print(f"  {pop_col} → {activity_col}")
        
        # Check if we have the new format
        has_maz_node = any('MAZ_NODE' in col for col in tm2_columns.keys())
        has_taz_node = any('TAZ_NODE' in col for col in tm2_columns.keys())
        
        if has_maz_node and has_taz_node:
            print("✓ PostProcess uses NEW format (MAZ_NODE, TAZ_NODE)")
        else:
            print("⚠️  PostProcess still uses OLD format (MAZ, TAZ)")
            
    except Exception as e:
        print(f"✗ PostProcess check failed: {e}")
        return False
    
    print("\n" + "="*60)
    print("QUICK TEST COMPLETE")
    print("="*60)
    return True

if __name__ == "__main__":
    success = test_column_naming()
    sys.exit(0 if success else 1)