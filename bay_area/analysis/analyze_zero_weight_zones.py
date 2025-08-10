#!/usr/bin/env python3
"""
Analyze exactly which zones have zero seed weights for occupations
This will tell us if it's a data issue or a legitimate geographic pattern
"""
import pandas as pd
import numpy as np

print("ANALYZING ZERO SEED WEIGHT ZONES FOR OCCUPATIONS")
print("="*60)

# Load seed data
try:
    persons = pd.read_csv('output_2023/seed_persons.csv')
    print(f"✅ Loaded {len(persons):,} persons")
    
    # Check required columns
    required_cols = ['PUMA', 'occupation', 'employed']
    missing_cols = [col for col in required_cols if col not in persons.columns]
    if missing_cols:
        print(f"❌ Missing columns: {missing_cols}")
        print(f"Available columns: {list(persons.columns)}")
        exit(1)
    
    print("✅ All required columns present")
    
    # Filter to employed people only (matching the control expressions)
    employed_persons = persons[persons['employed'] == 1]
    print(f"📊 Employed persons: {len(employed_persons):,}")
    
    # Create occupation-employment combinations by PUMA
    print(f"\n🗺️  OCCUPATION DISTRIBUTION BY PUMA:")
    occupation_by_puma = employed_persons.groupby(['PUMA', 'occupation']).size().unstack(fill_value=0)
    
    print(f"Shape: {occupation_by_puma.shape} (PUMAs × Occupations)")
    print("\nFirst 10 PUMAs:")
    print(occupation_by_puma.head(10))
    
    # Find PUMAs with zero counts for each occupation
    print(f"\n❌ PUMAs WITH ZERO EMPLOYED PEOPLE BY OCCUPATION:")
    for occ in [1, 2, 3, 4, 5, 6]:
        if occ in occupation_by_puma.columns:
            zero_pumas = occupation_by_puma[occupation_by_puma[occ] == 0].index.tolist()
            print(f"  Occupation {occ}: {len(zero_pumas)} PUMAs with zero")
            if len(zero_pumas) <= 20:  # Show all if not too many
                print(f"    Zero PUMAs: {zero_pumas}")
            else:
                print(f"    First 20: {zero_pumas[:20]}")
        else:
            print(f"  Occupation {occ}: No data found")
    
    # Check if there are exactly 18 PUMAs with issues (matching diagnostic output)
    total_pumas = len(occupation_by_puma)
    print(f"\n📈 SUMMARY:")
    print(f"  Total PUMAs in seed data: {total_pumas}")
    
    # Look for pattern that explains "18 zones with zero weights"
    for occ in [1, 2, 3, 4, 5, 6]:
        if occ in occupation_by_puma.columns:
            nonzero_pumas = (occupation_by_puma[occ] > 0).sum()
            zero_pumas = (occupation_by_puma[occ] == 0).sum()
            print(f"  Occupation {occ}: {nonzero_pumas} PUMAs with data, {zero_pumas} PUMAs with zero")
    
    # Show actual totals by occupation
    print(f"\n📊 TOTAL EMPLOYED BY OCCUPATION:")
    occ_totals = employed_persons['occupation'].value_counts().sort_index()
    for occ, count in occ_totals.items():
        print(f"  Occupation {occ}: {count:,} employed persons")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
