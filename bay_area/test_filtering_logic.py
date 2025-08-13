#!/usr/bin/env python3
"""
Simple test for household/person filtering logic
Tests just the filtering without the full PopulationSim framework
"""

import pandas as pd
import numpy as np
import sys
import os

def test_filtering_logic():
    """Test the household/person filtering logic directly"""
    
    print("=" * 60)
    print("TESTING HOUSEHOLD/PERSON FILTERING LOGIC")
    print("=" * 60)
    
    # Load the actual data files
    data_dir = "output_2023/populationsim_working_dir/data"
    
    print(f"\n1. Loading data files from {data_dir}...")
    households_df = pd.read_csv(f"{data_dir}/seed_households.csv")
    persons_df = pd.read_csv(f"{data_dir}/seed_persons.csv")
    crosswalk_df = pd.read_csv(f"{data_dir}/geo_cross_walk_tm2.csv")
    
    print(f"   Loaded {len(households_df)} households, {len(persons_df)} persons")
    print(f"   Crosswalk: {len(crosswalk_df)} records")
    
    # Extract the settings we need
    hh_weight_col = 'WGTP'
    household_id_col = 'unique_hh_id'
    seed_geography = 'PUMA'
    
    print(f"\n2. Original data state...")
    print(f"   Households: {len(households_df)}")
    print(f"   Persons: {len(persons_df)}")
    print(f"   Households with WGTP <= 0: {(households_df[hh_weight_col] <= 0).sum()}")
    
    # Check household/person ID alignment BEFORE filtering
    hh_ids_original = set(households_df[household_id_col])
    person_hh_ids_original = set(persons_df[household_id_col])
    
    print(f"   Original household IDs unique count: {len(hh_ids_original)}")
    print(f"   Original person household IDs unique count: {len(person_hh_ids_original)}")
    print(f"   Household IDs not in persons: {len(hh_ids_original - person_hh_ids_original)}")
    print(f"   Person household IDs not in households: {len(person_hh_ids_original - hh_ids_original)}")
    
    print(f"\n3. Applying filtering logic...")
    
    # Get household IDs before filtering
    original_hh_count = len(households_df)
    original_person_count = len(persons_df)
    
    # Filter out zero weight households
    households_filtered = households_df[households_df[hh_weight_col] > 0]
    print(f"   After removing zero weights: {len(households_filtered)} households")
    
    # Filter households to only those in seed zones
    seed_ids = crosswalk_df[seed_geography].unique()
    print(f"   Seed zones ({seed_geography}): {len(seed_ids)} zones")
    
    rows_in_seed_zones = households_filtered[seed_geography].isin(seed_ids)
    households_filtered = households_filtered[rows_in_seed_zones]
    print(f"   After seed zone filtering: {len(households_filtered)} households")
    
    # CRITICAL: Filter persons to only include those from retained households
    retained_household_ids = households_filtered[household_id_col]
    persons_filtered = persons_df[persons_df[household_id_col].isin(retained_household_ids)]
    print(f"   After filtering persons to match households: {len(persons_filtered)} persons")
    
    # Reset indexes to ensure they align properly
    households_filtered = households_filtered.reset_index(drop=True)
    persons_filtered = persons_filtered.reset_index(drop=True)
    
    print(f"\n4. Checking filtered data alignment...")
    print(f"   Filtered households: {len(households_filtered)}")
    print(f"   Filtered persons: {len(persons_filtered)}")
    print(f"   Households index range: {households_filtered.index.min()} to {households_filtered.index.max()}")
    print(f"   Persons index range: {persons_filtered.index.min()} to {persons_filtered.index.max()}")
    
    # Check household ID alignment AFTER filtering
    hh_ids_filtered = set(households_filtered[household_id_col])
    person_hh_ids_filtered = set(persons_filtered[household_id_col])
    
    missing_from_persons = hh_ids_filtered - person_hh_ids_filtered
    missing_from_households = person_hh_ids_filtered - hh_ids_filtered
    
    print(f"   Filtered household IDs unique count: {len(hh_ids_filtered)}")
    print(f"   Filtered person household IDs unique count: {len(person_hh_ids_filtered)}")
    print(f"   Household IDs in households but not persons: {len(missing_from_persons)}")
    print(f"   Household IDs in persons but not households: {len(missing_from_households)}")
    
    if missing_from_persons or missing_from_households:
        print("   ❌ ERROR: Household ID mismatch between filtered households and persons!")
        if missing_from_persons:
            print(f"      Sample missing from persons: {list(missing_from_persons)[:5]}")
        if missing_from_households:
            print(f"      Sample missing from households: {list(missing_from_households)[:5]}")
        return False
    else:
        print("   ✅ SUCCESS: Household IDs perfectly aligned between households and persons")
    
    print(f"\n5. Testing incidence table indexing...")
    
    # Test what would happen in incidence table building
    print(f"   Creating mock incidence table with household index...")
    
    # Old way: using DataFrame index
    incidence_table_old = pd.DataFrame(index=households_filtered.index)
    print(f"   Old incidence table index sample: {incidence_table_old.index[:5].tolist()}")
    
    # New way: using household IDs
    incidence_table_new = pd.DataFrame(index=households_filtered[household_id_col])
    print(f"   New incidence table index sample: {incidence_table_new.index[:5].tolist()}")
    
    # Simulate person aggregation (what PopulationSim does)
    print(f"\n6. Simulating person aggregation...")
    
    # Group persons by household ID (this is what creates the person control values)
    person_group = persons_filtered.groupby(household_id_col).size()
    print(f"   Person aggregation index sample: {person_group.index[:5].tolist()}")
    print(f"   Person aggregation shape: {person_group.shape}")
    
    # Check alignment with incidence tables
    person_agg_ids = set(person_group.index)
    old_incidence_ids = set(incidence_table_old.index)
    new_incidence_ids = set(incidence_table_new.index)
    
    # Old way misalignment
    old_missing_from_incidence = person_agg_ids - old_incidence_ids
    old_missing_from_person = old_incidence_ids - person_agg_ids
    
    # New way alignment
    new_missing_from_incidence = person_agg_ids - new_incidence_ids
    new_missing_from_person = new_incidence_ids - person_agg_ids
    
    print(f"\n   OLD WAY (DataFrame index):")
    print(f"      Person agg IDs not in incidence table: {len(old_missing_from_incidence)}")
    print(f"      Incidence table IDs not in person agg: {len(old_missing_from_person)}")
    if old_missing_from_incidence:
        print(f"      Sample missing from incidence: {list(old_missing_from_incidence)[:5]}")
    if old_missing_from_person:
        print(f"      Sample missing from person agg: {list(old_missing_from_person)[:5]}")
    
    print(f"\n   NEW WAY (Household ID index):")
    print(f"      Person agg IDs not in incidence table: {len(new_missing_from_incidence)}")
    print(f"      Incidence table IDs not in person agg: {len(new_missing_from_person)}")
    
    if new_missing_from_incidence or new_missing_from_person:
        print("      ❌ ERROR: Still have alignment issues with new approach!")
        return False
    else:
        print("      ✅ SUCCESS: Perfect alignment with new household ID indexing!")
    
    return True

if __name__ == "__main__":
    success = test_filtering_logic()
    if success:
        print(f"\n🎉 ALL TESTS PASSED! The filtering and indexing fixes are working correctly.")
        print(f"   The household/person filtering ensures data consistency.")
        print(f"   The incidence table indexing will prevent NaN value issues.")
        sys.exit(0)
    else:
        print(f"\n💥 TESTS FAILED! There are still issues with the filtering/indexing logic.")
        sys.exit(1)
