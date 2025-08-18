#!/usr/bin/env python3
"""
Work through the income control mismatch problem with concrete examples
Show exactly why PopulationSim is creating too many low-income households
"""

import pandas as pd
import numpy as np

def demonstrate_income_mismatch():
    """Show the income control mismatch problem step by step"""
    
    print("=" * 80)
    print("DEMONSTRATING THE INCOME CONTROL MISMATCH PROBLEM")
    print("=" * 80)
    print()
    
    print("STEP 1: Understanding the Problem")
    print("=" * 40)
    print("We have TWO different income systems that don't match:")
    print()
    
    # Show the census control brackets (what ACS data provides)
    print("📊 CENSUS CONTROLS (ACS 2023 data in 2023 dollars):")
    census_brackets_2023 = {
        'hh_inc_30': (0, 41399),
        'hh_inc_30_60': (41400, 82799), 
        'hh_inc_60_100': (82800, 137999),
        'hh_inc_100_plus': (138000, 999999)
    }
    
    for bracket, (min_val, max_val) in census_brackets_2023.items():
        print(f"  {bracket}: ${min_val:,} - ${max_val:,} (2023 dollars)")
    print()
    
    # Show the PopulationSim control expressions (what seed matching uses)
    print("🔧 POPULATIONSIM CONTROL EXPRESSIONS (expecting 2010 dollars):")
    popsim_brackets_2010 = {
        'hh_inc_30': (0, 29999),
        'hh_inc_30_60': (30000, 59999),
        'hh_inc_60_100': (60000, 99999), 
        'hh_inc_100_plus': (100000, 999999)
    }
    
    for bracket, (min_val, max_val) in popsim_brackets_2010.items():
        print(f"  {bracket}: ${min_val:,} - ${max_val:,} (2010 dollars)")
    print()
    
    print("❌ THE MISMATCH: Census provides 2023$ targets, PopulationSim matches using 2010$ ranges!")
    print()
    
    print("STEP 2: Concrete Example - San Francisco TAZ")
    print("=" * 50)
    print()
    print("Let's say ACS data shows for a San Francisco TAZ:")
    print("  - 100 households earning $0-$41,399 (2023$)")
    print("  - 150 households earning $41,400-$82,799 (2023$)")  
    print("  - 200 households earning $82,800-$137,999 (2023$)")
    print("  - 250 households earning $138,000+ (2023$)")
    print("  TOTAL: 700 households")
    print()
    
    # Create example control data
    taz_controls = {
        'hh_inc_30': 100,
        'hh_inc_30_60': 150,
        'hh_inc_60_100': 200,
        'hh_inc_100_plus': 250
    }
    
    print("But PopulationSim tries to match these targets using WRONG dollar brackets:")
    print()
    
    # Show what PopulationSim actually does
    print("🔍 WHAT POPULATIONSIM ACTUALLY DOES:")
    print()
    print("PopulationSim looks at seed households and asks:")
    print("  'How many households earn $0-$29,999 in 2010$?'  → Should match 100 target")
    print("  'How many households earn $30,000-$59,999 in 2010$?' → Should match 150 target")
    print("  'How many households earn $60,000-$99,999 in 2010$?' → Should match 200 target") 
    print("  'How many households earn $100,000+ in 2010$?' → Should match 250 target")
    print()
    
    print("💸 THE CURRENCY CONVERSION PROBLEM:")
    print()
    print("$30,000 in 2010 dollars = ~$41,400 in 2023 dollars")
    print("$60,000 in 2010 dollars = ~$82,800 in 2023 dollars")
    print("$100,000 in 2010 dollars = ~$138,000 in 2023 dollars")
    print()
    
    print("So PopulationSim is really asking:")
    print("  'How many households earn $0-$41,400 in 2023$?' → To match target of 100")
    print("  'How many households earn $41,400-$82,800 in 2023$?' → To match target of 150")
    print("  'But ACS target of 100 is for $0-$41,399 (almost same!)'")
    print("  'And ACS target of 150 is for $41,400-$82,799 (almost same!)'")
    print()
    print("✅ Wait, that seems like it should work... Let me check the actual numbers!")
    print()
    
    print("STEP 3: Let's Check The Actual Seed Data")
    print("=" * 45)
    print()
    
    # Load actual seed data to see what's happening
    seed_file = "output_2023/populationsim_working_dir/data/seed_households.csv"
    df = pd.read_csv(seed_file, usecols=['hh_income_2010', 'hh_income_2023', 'HINCP', 'ADJINC'])
    
    # Filter to valid incomes
    valid_df = df[(df['hh_income_2010'] > 0) & (df['hh_income_2023'] > 0)].copy()
    
    print(f"Looking at {len(valid_df):,} seed households with valid income...")
    print()
    
    # Current income distribution using 2010$ brackets
    print("🏠 SEED HOUSEHOLDS BY INCOME (using 2010$ brackets):")
    
    current_2010_dist = {}
    for bracket, (min_val, max_val) in popsim_brackets_2010.items():
        count = len(valid_df[(valid_df['hh_income_2010'] >= min_val) & (valid_df['hh_income_2010'] <= max_val)])
        pct = count / len(valid_df) * 100
        current_2010_dist[bracket] = count
        print(f"  {bracket}: {count:,} households ({pct:.1f}%)")
    print()
    
    # What if we used 2023$ brackets on 2023$ income?
    print("💰 SEED HOUSEHOLDS BY INCOME (using 2023$ brackets on 2023$ income):")
    
    correct_2023_dist = {}
    for bracket, (min_val, max_val) in census_brackets_2023.items():
        count = len(valid_df[(valid_df['hh_income_2023'] >= min_val) & (valid_df['hh_income_2023'] <= max_val)])
        pct = count / len(valid_df) * 100
        correct_2023_dist[bracket] = count
        print(f"  {bracket}: {count:,} households ({pct:.1f}%)")
    print()
    
    # Show the difference
    print("📊 COMPARISON: Current vs Correct Matching")
    print("=" * 55)
    print()
    print(f"{'Bracket':<15} | {'Current (2010$)':<15} | {'Correct (2023$)':<15} | {'Difference':<12}")
    print("-" * 70)
    
    for bracket in popsim_brackets_2010.keys():
        current = current_2010_dist[bracket]
        correct = correct_2023_dist[bracket]
        diff = correct - current
        print(f"{bracket:<15} | {current:>13,} | {correct:>13,} | {diff:>+10,}")
    print()
    
    print("STEP 4: The Real Problem - ADJINC Conversion Issue")
    print("=" * 60)
    print()
    
    print("But wait, there's an even bigger issue! Let's check if our 2023$ values are correct...")
    print()
    
    # Test ADJINC conversion on a sample
    sample = valid_df.sample(5)
    
    print("🧮 ADJINC CONVERSION TEST (sample households):")
    print()
    print(f"{'Raw HINCP':<10} | {'ADJINC Factor':<12} | {'Should Be 2021$':<15} | {'Should Be 2023$':<15} | {'Actual 2023$':<15}")
    print("-" * 90)
    
    for idx, row in sample.iterrows():
        hincp_raw = row['HINCP']
        adjinc_factor = row['ADJINC'] / 1_000_000
        should_be_2021 = hincp_raw * adjinc_factor
        
        # Convert 2021$ to 2023$ using CPI (2021: 270.970, 2023: 310.0)
        should_be_2023 = should_be_2021 * (310.0 / 270.970)
        actual_2023 = row['hh_income_2023']
        
        print(f"{hincp_raw:>9,.0f} | {adjinc_factor:>11.6f} | ${should_be_2021:>13,.0f} | ${should_be_2023:>13,.0f} | ${actual_2023:>13,.0f}")
    print()
    
    # Check if our current 2023$ values are wrong
    median_should_be_2023 = valid_df.apply(lambda row: (row['HINCP'] * row['ADJINC'] / 1_000_000) * (310.0 / 270.970), axis=1).median()
    median_actual_2023 = valid_df['hh_income_2023'].median()
    
    print(f"Median income should be: ${median_should_be_2023:,.0f} (2023$)")
    print(f"Median income actually is: ${median_actual_2023:,.0f} (2023$)")
    print()
    
    if abs(median_should_be_2023 - median_actual_2023) > 10000:
        print("❌ MAJOR PROBLEM: Our 2023$ income conversion is WRONG!")
        print("   The seed generation is not using ADJINC properly.")
        print("   This is why we have too many low-income households!")
    else:
        print("✅ 2023$ income conversion looks correct.")
        print("   The problem is just the bracket mismatch.")
    
    print()
    print("STEP 5: The Solution")
    print("=" * 25)
    print()
    print("We need to fix TWO things:")
    print()
    print("1. 🔧 FIX SEED GENERATION:")
    print("   - Use ADJINC properly: (ADJINC/1,000,000) × HINCP = 2021$")
    print("   - Then convert 2021$ to 2010$ and 2023$ using CPI")
    print()
    print("2. 🎯 FIX CONTROL MATCHING:")
    print("   - Either: Use 2023$ brackets with 2023$ income")
    print("   - Or: Use 2010$ brackets with 2010$ income") 
    print("   - Currently we're mixing 2023$ controls with 2010$ expressions!")
    print()
    print("STEP 6: Expected Impact")
    print("=" * 30)
    print()
    
    # Calculate expected improvement
    current_low_income_2010 = (current_2010_dist['hh_inc_30'] / len(valid_df)) * 100
    correct_low_income_2023 = (correct_2023_dist['hh_inc_30'] / len(valid_df)) * 100
    
    print(f"Current low-income rate (using wrong brackets): {current_low_income_2010:.1f}%")
    print(f"Corrected low-income rate (using right brackets): {correct_low_income_2023:.1f}%")
    print(f"Expected improvement: {current_low_income_2010 - correct_low_income_2023:+.1f} percentage points")
    print()
    
    # Estimate vehicle impact
    print("🚗 VEHICLE OWNERSHIP IMPACT:")
    print("   - Low-income households have ~60% zero-vehicle rate")
    print("   - Reducing low-income households should reduce zero-vehicle rate")
    print(f"   - Current zero-vehicle: 16.1%")
    print(f"   - Expected after fix: ~{16.1 - ((current_low_income_2010 - correct_low_income_2023) * 0.6):.1f}%")
    print(f"   - ACS target: ~10.2%")
    
    if (current_low_income_2010 - correct_low_income_2023) * 0.6 >= 4:
        print("   ✅ This fix should get us close to the ACS target!")
    else:
        print("   ⚠️  This fix helps but may not be sufficient")

if __name__ == "__main__":
    demonstrate_income_mismatch()
