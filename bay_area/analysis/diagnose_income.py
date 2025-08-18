#!/usr/bin/env python3
"""
Diagnose Income Distribution Issues in PopulationSim Output
Check if income values are properly adjusted to 2010 dollars and examine
relationship with vehicle ownership patterns.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_income_issues():
    """Analyze income distribution and its relationship to vehicle ownership"""
    
    print("=" * 70)
    print("INCOME DISTRIBUTION DIAGNOSTIC")
    print("=" * 70)
    
    # Load household data
    hh_file = Path("output_2023/populationsim_working_dir/output/households_2023_tm2.csv")
    if not hh_file.exists():
        print(f"Error: {hh_file} not found!")
        return
    
    print("Loading household data...")
    df = pd.read_csv(hh_file, usecols=['HHINCADJ', 'VEH', 'MTCCountyID'])
    
    print(f"Total households: {len(df):,}")
    print()
    
    # Basic income statistics
    print("=== INCOME STATISTICS (HHINCADJ) ===")
    print(f"Mean Income: ${df['HHINCADJ'].mean():,.0f}")
    print(f"Median Income: ${df['HHINCADJ'].median():,.0f}")
    print(f"25th percentile: ${df['HHINCADJ'].quantile(0.25):,.0f}")
    print(f"75th percentile: ${df['HHINCADJ'].quantile(0.75):,.0f}")
    print(f"Min Income: ${df['HHINCADJ'].min():,.0f}")
    print(f"Max Income: ${df['HHINCADJ'].max():,.0f}")
    print()
    
    # Income distribution
    print("=== INCOME DISTRIBUTION ===")
    # Use 2010 dollar brackets for comparison
    income_bins_2010 = [0, 15000, 25000, 35000, 50000, 75000, 100000, 150000, 200000, 300000, 10000000]
    income_labels_2010 = ['<$15k', '$15-25k', '$25-35k', '$35-50k', '$50-75k', '$75-100k', 
                          '$100-150k', '$150-200k', '$200-300k', '$300k+']
    
    df['income_bin'] = pd.cut(df['HHINCADJ'], bins=income_bins_2010, labels=income_labels_2010, right=False)
    income_dist = df['income_bin'].value_counts().sort_index()
    
    print("Income Distribution (assuming 2010 dollars):")
    for income, count in income_dist.items():
        pct = (count / len(df)) * 100
        print(f"{income:>12}: {count:>8,} ({pct:>5.1f}%)")
    print()
    
    # Compare to known Bay Area income patterns
    print("=== COMPARISON TO EXPECTED BAY AREA PATTERNS ===")
    print("Bay Area is high-income region. In 2010 dollars, we'd expect:")
    print("- Very few households under $25k (except SF due to subsidized housing)")
    print("- Strong concentration in $75k-200k range")
    print("- Significant tail above $200k due to tech industry")
    print()
    
    low_income_pct = (income_dist.iloc[:3].sum() / len(df)) * 100  # Under $35k
    mid_income_pct = (income_dist.iloc[4:7].sum() / len(df)) * 100  # $50k-150k  
    high_income_pct = (income_dist.iloc[7:].sum() / len(df)) * 100  # $150k+
    
    print(f"PopulationSim Results:")
    print(f"- Low income (<$35k): {low_income_pct:.1f}%")
    print(f"- Middle income ($50k-150k): {mid_income_pct:.1f}%") 
    print(f"- High income ($150k+): {high_income_pct:.1f}%")
    print()
    
    # Vehicle ownership by income
    print("=== ZERO VEHICLES BY INCOME BRACKET ===")
    zero_veh = df[df['VEH'] == 0]
    zero_by_income = zero_veh['income_bin'].value_counts().sort_index()
    total_by_income = df['income_bin'].value_counts().sort_index()
    
    print("Income Bracket | Zero-Veh HH | Total HH | Zero-Veh %")
    print("-" * 55)
    for income in income_labels_2010:
        if income in total_by_income.index:
            zero_count = zero_by_income.get(income, 0)
            total_count = total_by_income[income]
            zero_pct = (zero_count / total_count) * 100
            print(f"{income:>12} | {zero_count:>9,} | {total_count:>7,} | {zero_pct:>7.1f}%")
    print()
    
    # County-specific income analysis
    print("=== INCOME BY COUNTY (San Francisco focus) ===")
    county_names = {1: 'San Francisco', 2: 'San Mateo', 3: 'Santa Clara', 4: 'Alameda'}
    
    for county_id, county_name in county_names.items():
        county_data = df[df['MTCCountyID'] == county_id]
        if len(county_data) > 0:
            county_low_pct = (county_data['HHINCADJ'] < 35000).mean() * 100
            county_zero_veh = (county_data['VEH'] == 0).mean() * 100
            print(f"{county_name}: {county_low_pct:.1f}% low income (<$35k), {county_zero_veh:.1f}% zero vehicles")
    print()
    
    # Inflation adjustment check
    print("=== INFLATION ADJUSTMENT CHECK ===")
    # CPI inflation from 2010 to 2023: approximately 40%
    # So $100k in 2010 ≈ $140k in 2023
    inflation_factor = 1.40  # Rough 2010 to 2023 inflation
    
    print(f"If income values are in 2023 dollars instead of 2010:")
    print(f"- Mean in 2010$: ${df['HHINCADJ'].mean() / inflation_factor:,.0f}")
    print(f"- Median in 2010$: ${df['HHINCADJ'].median() / inflation_factor:,.0f}")
    print()
    
    # Check against PUMS source
    print("=== POTENTIAL ISSUES ===")
    median_income = df['HHINCADJ'].median()
    
    if median_income > 120000:
        print("⚠️  POTENTIAL ISSUE: Median income seems high for 2010 dollars")
        print("   This suggests income may not be properly adjusted to 2010$")
        print("   Bay Area 2010 median household income was ~$75k-85k")
    elif median_income < 50000:
        print("⚠️  POTENTIAL ISSUE: Median income seems low")
        print("   This could explain high zero-vehicle rates")
    else:
        print("✓ Income levels appear reasonable for 2010 dollars")
    
    print()
    print("=== RECOMMENDATIONS ===")
    print("1. Verify PUMS income adjustment in seed population creation")
    print("2. Check if ADJINC factor is being applied correctly")
    print("3. Compare seed population income to ACS median household income")
    print("4. If income is correct, vehicle ownership controls are definitely needed")

if __name__ == "__main__":
    analyze_income_issues()
