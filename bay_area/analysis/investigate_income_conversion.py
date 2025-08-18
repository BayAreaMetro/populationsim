#!/usr/bin/env python3
"""
Carefully investigate the actual income conversion in our seed data
Let's not jump to conclusions and see what's really happening
"""

import pandas as pd
import numpy as np

def investigate_actual_conversion():
    """Look at the actual data to understand what happened"""
    
    print("=" * 80)
    print("INVESTIGATING THE ACTUAL INCOME CONVERSION")
    print("=" * 80)
    print()
    
    # Load the actual seed data
    seed_file = "output_2023/populationsim_working_dir/data/seed_households.csv"
    
    print("Loading seed data...")
    # Load only the income-related columns to avoid memory issues
    income_cols = ['HINCP', 'ADJINC', 'hh_income_2010', 'hh_income_2023', 'hhgqtype', 'unique_hh_id']
    df = pd.read_csv(seed_file, usecols=income_cols)
    
    print(f"Loaded {len(df):,} households")
    print()
    
    # Filter to households only (not group quarters) with valid income
    households = df[(df['hhgqtype'] == 0) & (df['HINCP'] > 0) & (df['ADJINC'] > 0)].copy()
    print(f"Analyzing {len(households):,} households with valid income data")
    print()
    
    print("STEP 1: Check if ADJINC was actually applied")
    print("=" * 50)
    print()
    
    # Take a sample to examine
    sample = households.sample(10, random_state=42)
    
    print("Sample of raw data:")
    print(f"{'HINCP (raw)':<12} | {'ADJINC':<10} | {'hh_income_2023':<15} | {'hh_income_2010':<15}")
    print("-" * 65)
    
    for idx, row in sample.iterrows():
        hincp = row['HINCP']
        adjinc = row['ADJINC']
        income_2023 = row['hh_income_2023']
        income_2010 = row['hh_income_2010']
        print(f"{hincp:>11,.0f} | {adjinc:>9,.0f} | {income_2023:>14,.0f} | {income_2010:>14,.0f}")
    
    print()
    
    print("STEP 2: Calculate what the values SHOULD be if ADJINC was applied")
    print("=" * 70)
    print()
    
    # Calculate what they should be
    sample['calculated_2021'] = (sample['ADJINC'] / 1_000_000) * sample['HINCP']
    sample['calculated_2023'] = sample['calculated_2021'] * (310.0 / 270.970)  # CPI adjustment
    sample['calculated_2010'] = sample['calculated_2021'] * (218.056 / 270.970)  # CPI adjustment
    
    print("Comparison: Actual vs Expected:")
    print(f"{'HINCP':<8} | {'Actual 2023':<12} | {'Expected 2023':<13} | {'Actual 2010':<12} | {'Expected 2010':<13} | {'Match?'}")
    print("-" * 90)
    
    matches_2023 = 0
    matches_2010 = 0
    
    for idx, row in sample.iterrows():
        hincp = row['HINCP']
        actual_2023 = row['hh_income_2023']
        expected_2023 = row['calculated_2023']
        actual_2010 = row['hh_income_2010']
        expected_2010 = row['calculated_2010']
        
        # Check if they match (within 1% tolerance)
        match_2023 = abs(actual_2023 - expected_2023) / expected_2023 < 0.01
        match_2010 = abs(actual_2010 - expected_2010) / expected_2010 < 0.01
        
        if match_2023: matches_2023 += 1
        if match_2010: matches_2010 += 1
        
        match_str = f"2023:{match_2023} 2010:{match_2010}"
        
        print(f"{hincp:>7,.0f} | {actual_2023:>11,.0f} | {expected_2023:>12,.0f} | {actual_2010:>11,.0f} | {expected_2010:>12,.0f} | {match_str}")
    
    print()
    print(f"Summary: {matches_2023}/10 match for 2023$, {matches_2010}/10 match for 2010$")
    print()
    
    if matches_2023 >= 8 and matches_2010 >= 8:
        print("✅ ADJINC conversion appears to be working correctly!")
        conversion_working = True
    elif matches_2023 == 0 and matches_2010 == 0:
        print("❌ ADJINC conversion is NOT working - values are still raw HINCP!")  
        conversion_working = False
    else:
        print("⚠️  ADJINC conversion is partially working or has issues")
        conversion_working = False
    
    print()
    
    print("STEP 3: Check the overall distribution")
    print("=" * 42)
    print()
    
    # Overall statistics
    print("Overall income statistics:")
    print(f"Raw HINCP median: ${households['HINCP'].median():,.0f}")
    print(f"hh_income_2023 median: ${households['hh_income_2023'].median():,.0f}")  
    print(f"hh_income_2010 median: ${households['hh_income_2010'].median():,.0f}")
    print()
    
    # What should the median be if ADJINC was applied?
    expected_2021_median = ((households['ADJINC'] / 1_000_000) * households['HINCP']).median()
    expected_2023_median = expected_2021_median * (310.0 / 270.970)
    expected_2010_median = expected_2021_median * (218.056 / 270.970)
    
    print("Expected if ADJINC applied correctly:")
    print(f"Expected 2023$ median: ${expected_2023_median:,.0f}")
    print(f"Expected 2010$ median: ${expected_2010_median:,.0f}")
    print()
    
    # Check the ratio
    actual_2023_median = households['hh_income_2023'].median()
    actual_2010_median = households['hh_income_2010'].median()
    
    ratio_2023 = actual_2023_median / expected_2023_median
    ratio_2010 = actual_2010_median / expected_2010_median
    
    print(f"Ratio actual/expected for 2023$: {ratio_2023:.3f}")
    print(f"Ratio actual/expected for 2010$: {ratio_2010:.3f}")
    print()
    
    if 0.95 <= ratio_2023 <= 1.05 and 0.95 <= ratio_2010 <= 1.05:
        print("✅ Overall medians match expected values - ADJINC is working!")
    else:
        print("❌ Overall medians don't match - ADJINC conversion has issues")
        
    print()
    
    print("STEP 4: So what's causing the vehicle ownership problem?")
    print("=" * 60)
    print()
    
    if conversion_working:
        print("If ADJINC conversion IS working, then the problem might be:")
        print("1. Control matching issue (2010$ vs 2023$ bracket mismatch)")  
        print("2. Different issue entirely (not income-related)")
        print("3. PopulationSim control expressions using wrong income field")
        print()
        
        # Check which income field PopulationSim is actually using
        controls_file = "output_2023/populationsim_working_dir/configs/controls.csv"
        try:
            controls_df = pd.read_csv(controls_file)
            income_controls = controls_df[controls_df['control_description'].str.contains('hh_inc', na=False)]
            print("PopulationSim income control expressions:")
            for idx, row in income_controls.iterrows():
                print(f"  {row['control_description']}: {row['expression']}")
            print()
        except:
            print("Could not load controls.csv to check expressions")
        
    else:
        print("ADJINC conversion is broken - that's definitely the main problem!")
        print("Need to fix the seed generation first.")
    
    print()
    print("STEP 5: Income distribution analysis")  
    print("=" * 40)
    print()
    
    # Show income brackets using the field that PopulationSim actually uses
    # Let's check both 2010 and 2023 brackets
    
    print("Income distribution using 2010$ brackets on hh_income_2010:")
    brackets_2010 = [
        ("$0-30k", (0, 29999)),
        ("$30k-60k", (30000, 59999)), 
        ("$60k-100k", (60000, 99999)),
        ("$100k+", (100000, 999999))
    ]
    
    for label, (min_val, max_val) in brackets_2010:
        count = len(households[(households['hh_income_2010'] >= min_val) & (households['hh_income_2010'] <= max_val)])
        pct = count / len(households) * 100
        print(f"  {label}: {count:,} ({pct:.1f}%)")
    
    print()
    
    print("Income distribution using 2023$ brackets on hh_income_2023:")  
    brackets_2023 = [
        ("$0-41k", (0, 41399)),
        ("$41k-83k", (41400, 82799)),
        ("$83k-138k", (82800, 137999)), 
        ("$138k+", (138000, 999999))
    ]
    
    for label, (min_val, max_val) in brackets_2023:
        count = len(households[(households['hh_income_2023'] >= min_val) & (households['hh_income_2023'] <= max_val)])
        pct = count / len(households) * 100
        print(f"  {label}: {count:,} ({pct:.1f}%)")

if __name__ == "__main__":
    investigate_actual_conversion()
