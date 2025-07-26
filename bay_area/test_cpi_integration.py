#!/usr/bin/env python3
"""
Test CPI integration in seed population
"""

import pandas as pd
from cpi_conversion import convert_2023_to_2010_dollars

# Test with sample PUMS-like data
print("Testing CPI conversion integration...")

# Simulate PUMS household data
test_data = pd.DataFrame({
    'HINCP': [50000, 75000, 120000, 200000],  # Raw income values
    'ADJINC': [1000000, 1000000, 1000000, 1000000],  # Standard ADJINC (no adjustment)
    'PUMA': ['01301', '01305', '08101', '00101']
})

print("Sample PUMS data:")
print(test_data)

# Apply the same logic as in create_seed_population_final.py
ONE_MILLION = 1000000
test_data['hh_income_2023'] = (test_data['ADJINC'] / ONE_MILLION) * test_data['HINCP'].fillna(0)
test_data['hh_income_2010'] = convert_2023_to_2010_dollars(test_data['hh_income_2023'])

print("\nAfter income conversion:")
print(f"2023$: {test_data['hh_income_2023'].tolist()}")
print(f"2010$: {test_data['hh_income_2010'].round().astype(int).tolist()}")

# Verify against our breakpoints
print(f"\nIncome distribution analysis (2010$ purchasing power):")
print(f"<$30K:   {(test_data['hh_income_2010'] < 30000).sum()} households")
print(f"$30-60K: {((test_data['hh_income_2010'] >= 30000) & (test_data['hh_income_2010'] < 60000)).sum()} households") 
print(f"$60-100K: {((test_data['hh_income_2010'] >= 60000) & (test_data['hh_income_2010'] < 100000)).sum()} households")
print(f"$100K+:  {(test_data['hh_income_2010'] >= 100000).sum()} households")

print("\n✅ CPI conversion integration test completed successfully!")
