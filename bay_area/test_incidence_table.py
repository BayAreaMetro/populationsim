#!/usr/bin/env python3
"""
Standalone test for PopulationSim incidence table building
Tests the household/person filtering and incidence table index alignment
"""

import pandas as pd
import numpy as np
import sys
import os

# Add populationsim to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from populationsim.steps.setup_data_structures import filter_households, build_incidence_table

def test_incidence_table_fix():
    """Test the incidence table building with our fixes"""
    
    print("=" * 60)
    print("TESTING POPULATIONSIM INCIDENCE TABLE FIXES")
    print("=" * 60)
    
    # Load the actual data files
    data_dir = "output_2023/populationsim_working_dir/data"
    
    print(f"\n1. Loading data files from {data_dir}...")
    households_df = pd.read_csv(f"{data_dir}/seed_households.csv")
    persons_df = pd.read_csv(f"{data_dir}/seed_persons.csv")
    crosswalk_df = pd.read_csv(f"{data_dir}/geo_cross_walk_tm2.csv")
    control_spec = pd.read_csv(f"{data_dir}/../configs/controls.csv")
    
    print(f"   Loaded {len(households_df)} households, {len(persons_df)} persons")
    print(f"   Crosswalk: {len(crosswalk_df)} records")
    print(f"   Control spec: {len(control_spec)} controls")
    
    # Mock the settings that PopulationSim uses
    from activitysim.core.config import setting
    
    # Set up mock settings
    settings = {
        'household_weight_col': 'WGTP',
        'household_id_col': 'unique_hh_id',
        'seed_geography': 'PUMA',
        'geographies': ['COUNTY', 'PUMA', 'TAZ', 'MAZ']
    }
    
    # Override the setting function  
    import activitysim.core.config as config_module
    original_setting = config_module.setting
    def mock_setting(key):
        return settings.get(key, original_setting(key))
    config_module.setting = mock_setting
    
    print(f"\n2. Testing filter_households function...")
    print(f"   Original households: {len(households_df)}")
    print(f"   Original persons: {len(persons_df)}")
    print(f"   Households with WGTP <= 0: {(households_df['WGTP'] <= 0).sum()}")
    
    # Test the filtering
    filtered_households, filtered_persons = filter_households(households_df, persons_df, crosswalk_df)
    
    print(f"   Filtered households: {len(filtered_households)}")
    print(f"   Filtered persons: {len(filtered_persons)}")
    print(f"   Households index range: {filtered_households.index.min()} to {filtered_households.index.max()}")
    print(f"   Persons index range: {filtered_persons.index.min()} to {filtered_persons.index.max()}")
    
    # Check household ID alignment
    hh_ids_households = set(filtered_households['unique_hh_id'])
    hh_ids_persons = set(filtered_persons['unique_hh_id'])
    
    missing_from_persons = hh_ids_households - hh_ids_persons
    missing_from_households = hh_ids_persons - hh_ids_households
    
    print(f"   Household IDs in households but not persons: {len(missing_from_persons)}")
    print(f"   Household IDs in persons but not households: {len(missing_from_households)}")
    
    if missing_from_persons or missing_from_households:
        print("   ❌ ERROR: Household ID mismatch between filtered households and persons!")
        return False
    else:
        print("   ✅ SUCCESS: Household IDs perfectly aligned between households and persons")
    
    print(f"\n3. Testing incidence table building...")
    
    # Test incidence table creation
    try:
        incidence_table = build_incidence_table(control_spec, filtered_households, filtered_persons, crosswalk_df)
        
        print(f"   Incidence table shape: {incidence_table.shape}")
        print(f"   Incidence table index type: {type(incidence_table.index[0])}")
        print(f"   Incidence table index sample: {incidence_table.index[:5].tolist()}")
        print(f"   Household ID sample: {filtered_households['unique_hh_id'].head().tolist()}")
        
        # Check for NaN values
        nan_columns = []
        for col in incidence_table.columns:
            nan_count = incidence_table[col].isna().sum()
            if nan_count > 0:
                nan_columns.append(f"{col}: {nan_count}")
        
        if nan_columns:
            print(f"   ❌ ERROR: Incidence table has NaN values:")
            for nan_info in nan_columns[:10]:  # Show first 10
                print(f"      {nan_info}")
            if len(nan_columns) > 10:
                print(f"      ... and {len(nan_columns) - 10} more columns with NaN values")
            return False
        else:
            print("   ✅ SUCCESS: No NaN values in incidence table!")
            
        # Check index alignment  
        incidence_index_set = set(incidence_table.index)
        household_id_set = set(filtered_households['unique_hh_id'])
        
        missing_from_incidence = household_id_set - incidence_index_set
        missing_from_households = incidence_index_set - household_id_set
        
        print(f"   Household IDs in households but not incidence table: {len(missing_from_incidence)}")
        print(f"   Household IDs in incidence table but not households: {len(missing_from_households)}")
        
        if missing_from_incidence or missing_from_households:
            print("   ❌ ERROR: Index mismatch between incidence table and households!")
            print(f"      Sample missing from incidence: {list(missing_from_incidence)[:5]}")
            print(f"      Sample missing from households: {list(missing_from_households)[:5]}")
            return False
        else:
            print("   ✅ SUCCESS: Perfect index alignment between incidence table and households!")
            
        return True
        
    except Exception as e:
        print(f"   ❌ ERROR: Exception building incidence table: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Restore original setting function
        config_module.setting = original_setting

if __name__ == "__main__":
    success = test_incidence_table_fix()
    if success:
        print(f"\n🎉 ALL TESTS PASSED! The incidence table fixes are working correctly.")
        sys.exit(0)
    else:
        print(f"\n💥 TESTS FAILED! There are still issues with the incidence table.")
        sys.exit(1)
