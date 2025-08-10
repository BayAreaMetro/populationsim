#!/usr/bin/env python3
"""
Check PUMA mismatch between crosswalk and seed population.
The seed population should only contain PUMAs that exist in the crosswalk.
"""

import pandas as pd
import sys
import os

def check_puma_consistency():
    """Check PUMA consistency between crosswalk and seed population."""
    
    # Load crosswalk PUMAs
    crosswalk_path = 'hh_gq/data/geo_cross_walk_tm2.csv'
    if not os.path.exists(crosswalk_path):
        print(f"Error: {crosswalk_path} not found")
        return
    
    print("Loading crosswalk...")
    crosswalk = pd.read_csv(crosswalk_path)
    crosswalk_pumas = set(crosswalk['PUMA'].unique())
    
    # Load seed household PUMAs
    seed_hh_path = 'hh_gq/data/seed_households.csv'
    if not os.path.exists(seed_hh_path):
        print(f"Error: {seed_hh_path} not found")
        return
        
    print("Loading seed households (PUMA column only)...")
    seed_hh = pd.read_csv(seed_hh_path, usecols=['PUMA'])
    seed_hh_pumas = set(seed_hh['PUMA'].unique())
    
    # Load seed person PUMAs
    seed_persons_path = 'hh_gq/data/seed_persons.csv'
    if not os.path.exists(seed_persons_path):
        print(f"Error: {seed_persons_path} not found")
        return
        
    print("Loading seed persons (PUMA column only)...")
    seed_persons = pd.read_csv(seed_persons_path, usecols=['PUMA'])
    seed_persons_pumas = set(seed_persons['PUMA'].unique())
    
    # Analysis
    print("\n" + "="*60)
    print("PUMA CONSISTENCY ANALYSIS")
    print("="*60)
    
    print(f"Crosswalk PUMAs: {len(crosswalk_pumas)}")
    print(f"Seed household PUMAs: {len(seed_hh_pumas)}")
    print(f"Seed person PUMAs: {len(seed_persons_pumas)}")
    
    # Find mismatches
    extra_hh_pumas = seed_hh_pumas - crosswalk_pumas
    extra_person_pumas = seed_persons_pumas - crosswalk_pumas
    missing_hh_pumas = crosswalk_pumas - seed_hh_pumas
    missing_person_pumas = crosswalk_pumas - seed_persons_pumas
    
    print(f"\nExtra PUMAs in seed households (not in crosswalk): {len(extra_hh_pumas)}")
    if extra_hh_pumas:
        print(f"  {sorted(extra_hh_pumas)}")
    
    print(f"\nExtra PUMAs in seed persons (not in crosswalk): {len(extra_person_pumas)}")
    if extra_person_pumas:
        print(f"  {sorted(extra_person_pumas)}")
    
    print(f"\nMissing PUMAs in seed households (in crosswalk but not seed): {len(missing_hh_pumas)}")
    if missing_hh_pumas:
        print(f"  {sorted(missing_hh_pumas)}")
    
    print(f"\nMissing PUMAs in seed persons (in crosswalk but not seed): {len(missing_person_pumas)}")
    if missing_person_pumas:
        print(f"  {sorted(missing_person_pumas)}")
    
    # Count records with invalid PUMAs
    if extra_hh_pumas:
        invalid_hh_count = seed_hh[seed_hh['PUMA'].isin(extra_hh_pumas)].shape[0]
        total_hh_count = seed_hh.shape[0]
        print(f"\nHouseholds with invalid PUMAs: {invalid_hh_count:,} / {total_hh_count:,} ({invalid_hh_count/total_hh_count*100:.2f}%)")
    
    if extra_person_pumas:
        invalid_person_count = seed_persons[seed_persons['PUMA'].isin(extra_person_pumas)].shape[0]
        total_person_count = seed_persons.shape[0]
        print(f"Persons with invalid PUMAs: {invalid_person_count:,} / {total_person_count:,} ({invalid_person_count/total_person_count*100:.2f}%)")
    
    print("\n" + "="*60)
    print("RECOMMENDATION:")
    if extra_hh_pumas or extra_person_pumas:
        print("❌ PUMA MISMATCH DETECTED!")
        print("The seed population creation process needs to filter PUMAs using the crosswalk.")
        print("Only PUMAs present in geo_cross_walk_tm2.csv should be included in seed data.")
    else:
        print("✅ PUMA consistency verified - all seed PUMAs exist in crosswalk.")
    print("="*60)

if __name__ == "__main__":
    check_puma_consistency()
