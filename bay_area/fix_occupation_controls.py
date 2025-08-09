#!/usr/bin/env python3
"""
Fix occupation control issue by removing granular occupation controls
These controls are causing NaN errors due to insufficient seed representation
"""
import pandas as pd
import shutil

print("="*80)
print("FIXING OCCUPATION CONTROL ISSUE")
print("="*80)

# Backup original county marginals
original_file = 'output_2023/county_marginals.csv'
backup_file = 'output_2023/county_marginals_with_occupations.csv'

print(f"Backing up {original_file} to {backup_file}")
shutil.copy2(original_file, backup_file)

# Read current county marginals
county = pd.read_csv(original_file)
print(f"Original county marginals shape: {county.shape}")
print(f"Original columns: {list(county.columns)}")

# Remove problematic occupation columns
occupation_cols = [
    'pers_occ_management',
    'pers_occ_professional', 
    'pers_occ_services',
    'pers_occ_retail',
    'pers_occ_manual',
    'pers_occ_military'
]

# Check which occupation columns exist
existing_occ_cols = [col for col in occupation_cols if col in county.columns]
print(f"\nOccupation columns to remove: {existing_occ_cols}")

if existing_occ_cols:
    # Show the values being removed
    print("\nOccupation control totals being removed:")
    for col in existing_occ_cols:
        total = county[col].sum()
        print(f"  {col}: {total:,} total persons")
    
    # Remove occupation columns
    county_fixed = county.drop(columns=existing_occ_cols)
    print(f"\nFixed county marginals shape: {county_fixed.shape}")
    print(f"Fixed columns: {list(county_fixed.columns)}")
    
    # Save fixed file
    county_fixed.to_csv(original_file, index=False)
    print(f"✅ Saved fixed county marginals to {original_file}")
    
    # Also update the working directory
    working_file = 'hh_gq/tm2_working_dir/data/county_marginals.csv'
    county_fixed.to_csv(working_file, index=False)
    print(f"✅ Updated working directory: {working_file}")
    
    print(f"\n🎯 SOLUTION APPLIED:")
    print(f"   Removed {len(existing_occ_cols)} granular occupation controls")
    print(f"   These were causing NaN errors due to insufficient seed representation")
    print(f"   PopulationSim should now complete successfully!")
    
else:
    print("❌ No occupation columns found to remove")

print("\n" + "="*80)
