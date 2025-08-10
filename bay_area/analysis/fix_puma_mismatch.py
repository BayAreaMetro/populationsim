#!/usr/bin/env python3
"""
Fix PUMA mismatch between seed population and crosswalk
Remove the 4 extra PUMAs from seed data that don't exist in crosswalk
"""
import pandas as pd
import numpy as np

# Valid PUMAs from crosswalk (the 62 we identified)
crosswalk = pd.read_csv('hh_gq/data/geo_cross_walk_tm2.csv')
valid_pumas = set(crosswalk['PUMA'].unique())
print(f"Valid PUMAs from crosswalk: {len(valid_pumas)}")
print(f"Valid PUMAs: {sorted(valid_pumas)}")

# Extra PUMAs that need to be removed
extra_pumas = [5303, 7707, 8701, 11301]
print(f"\nRemoving extra PUMAs: {extra_pumas}")

# Fix household seed data
print("\n1. Fixing household seed data...")
hh_seed = pd.read_csv('output_2023/households.csv')
print(f"Original households: {len(hh_seed):,}")
print(f"Original PUMAs: {sorted(hh_seed['PUMA'].unique())}")

# Remove households from invalid PUMAs
hh_seed_filtered = hh_seed[hh_seed['PUMA'].isin(valid_pumas)]
print(f"Filtered households: {len(hh_seed_filtered):,}")
print(f"Removed households: {len(hh_seed) - len(hh_seed_filtered):,}")

# Save backup and updated file
hh_seed.to_csv('output_2023/households_backup.csv', index=False)
hh_seed_filtered.to_csv('output_2023/households.csv', index=False)
print("Updated households.csv")

# Fix persons seed data
print("\n2. Fixing persons seed data...")
persons_seed = pd.read_csv('output_2023/persons.csv')
print(f"Original persons: {len(persons_seed):,}")

# Remove persons from invalid PUMAs
persons_seed_filtered = persons_seed[persons_seed['PUMA'].isin(valid_pumas)]
print(f"Filtered persons: {len(persons_seed_filtered):,}")
print(f"Removed persons: {len(persons_seed) - len(persons_seed_filtered):,}")

# Save backup and updated file
persons_seed.to_csv('output_2023/persons_backup.csv', index=False)
persons_seed_filtered.to_csv('output_2023/persons.csv', index=False)
print("Updated persons.csv")

# Also update the working directory copies
import shutil
shutil.copy('output_2023/households.csv', 'hh_gq/tm2_working_dir/data/households.csv')
shutil.copy('output_2023/persons.csv', 'hh_gq/tm2_working_dir/data/persons.csv')
print("\nUpdated working directory copies")

print(f"\nFinal verification:")
print(f"Households PUMAs: {sorted(hh_seed_filtered['PUMA'].unique())}")
print(f"Persons PUMAs: {sorted(persons_seed_filtered['PUMA'].unique())}")
print(f"All PUMAs valid: {set(hh_seed_filtered['PUMA'].unique()).issubset(valid_pumas)}")
