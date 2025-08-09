#!/usr/bin/env python3
"""
Check occupation data in seed population to understand the NaN factor issue
"""
import pandas as pd
import numpy as np

print("CHECKING OCCUPATION DATA IN SEED POPULATION")
print("="*60)

try:
    # Load seed persons data
    persons = pd.read_csv('output_2023/seed_persons.csv')
    print(f"✅ Loaded {len(persons):,} seed persons")
    print(f"Columns: {list(persons.columns)}")
    
    # Check for occupation column
    if 'occupation' in persons.columns:
        print(f"\n📊 Occupation value counts:")
        occ_counts = persons['occupation'].value_counts().sort_index()
        print(occ_counts)
        
        print(f"\n📈 Occupation distribution by PUMA (first 10 PUMAs):")
        if 'PUMA' in persons.columns:
            occ_by_puma = persons.groupby(['PUMA', 'occupation']).size().unstack(fill_value=0)
            print(occ_by_puma.head(10))
            
            # Check for PUMAs with zero in any occupation
            zero_counts = (occ_by_puma == 0).sum(axis=0)
            print(f"\n⚠️  PUMAs with zero counts by occupation:")
            for occ, zero_count in zero_counts.items():
                if zero_count > 0:
                    print(f"  Occupation {occ}: {zero_count} PUMAs have zero")
        else:
            print("❌ No PUMA column found in persons data")
    else:
        print("❌ No 'occupation' column found")
        print("Available columns:", list(persons.columns))
        
        # Check for similar columns
        similar_cols = [col for col in persons.columns if 'occ' in col.lower()]
        if similar_cols:
            print(f"Found similar columns: {similar_cols}")
            
except Exception as e:
    print(f"❌ Error loading seed persons data: {e}")

print("\n" + "="*60)
