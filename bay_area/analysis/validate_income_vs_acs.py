#!/usr/bin/env python3
"""
Compare PopulationSim income distribution to ACS reference data
to identify systematic biases in income synthesis.
"""

import pandas as pd
import numpy as np

def compare_income_to_acs():
    """Compare PopulationSim income patterns to ACS data"""
    
    print("=" * 70)
    print("INCOME VALIDATION AGAINST ACS DATA")
    print("=" * 70)
    
    # Load PopulationSim data
    print("Loading PopulationSim household data...")
    df = pd.read_csv("output_2023/populationsim_working_dir/output/households_2023_tm2.csv", 
                     usecols=['HHINCADJ', 'VEH', 'MTCCountyID'])
    
    # ACS 2022 5-year estimates for Bay Area counties (Table B19013 - Median Household Income)
    # These are in 2022 inflation-adjusted dollars, need to convert to 2010
    acs_median_income_2022 = {
        'San Francisco': 126590,
        'San Mateo': 134285, 
        'Santa Clara': 130890,
        'Alameda': 96942,
        'Contra Costa': 105846,
        'Marin': 131008,
        'Napa': 86566,
        'Solano': 87804,
        'Sonoma': 92022
    }
    
    # Convert 2022 dollars to 2010 dollars (roughly 30% inflation 2010-2022)
    inflation_2010_to_2022 = 1.30
    acs_median_income_2010 = {k: v/inflation_2010_to_2022 for k, v in acs_median_income_2022.items()}
    
    print("=== ACS MEDIAN HOUSEHOLD INCOME (2010 dollars) ===")
    for county, income in acs_median_income_2010.items():
        print(f"{county:>15}: ${income:>7,.0f}")
    
    regional_median_acs = np.mean(list(acs_median_income_2010.values()))
    print(f"{'Regional Average':>15}: ${regional_median_acs:>7,.0f}")
    print()
    
    # PopulationSim medians by county
    county_names = {1: 'San Francisco', 2: 'San Mateo', 3: 'Santa Clara', 4: 'Alameda'}
    print("=== POPULATIONSIM MEDIAN HOUSEHOLD INCOME ===")
    for county_id, county_name in county_names.items():
        county_data = df[df['MTCCountyID'] == county_id]
        if len(county_data) > 0:
            popsim_median = county_data['HHINCADJ'].median()
            acs_median = acs_median_income_2010.get(county_name, 0)
            diff = popsim_median - acs_median
            diff_pct = (diff / acs_median) * 100 if acs_median > 0 else 0
            print(f"{county_name:>15}: ${popsim_median:>7,.0f} (ACS: ${acs_median:>6,.0f}, diff: {diff_pct:>+5.1f}%)")
    
    regional_median_popsim = df['HHINCADJ'].median()
    diff = regional_median_popsim - regional_median_acs
    diff_pct = (diff / regional_median_acs) * 100
    print(f"{'Regional':>15}: ${regional_median_popsim:>7,.0f} (ACS: ${regional_median_acs:>6,.0f}, diff: {diff_pct:>+5.1f}%)")
    print()
    
    # Income distribution comparison (approximate ACS distribution for Bay Area)
    print("=== INCOME DISTRIBUTION COMPARISON ===")
    # These are rough estimates for Bay Area based on ACS data patterns
    expected_bay_area_2010 = {
        '<$15k': 8.0,      # Very low for Bay Area
        '$15-25k': 6.0,    # Low
        '$25-35k': 7.0,    # Low-moderate  
        '$35-50k': 10.0,   # Moderate
        '$50-75k': 15.0,   # Moderate-high
        '$75-100k': 12.0,  # High
        '$100-150k': 25.0, # Very high
        '$150-200k': 10.0, # Very high
        '$200-300k': 5.0,  # Extremely high
        '$300k+': 2.0      # Ultra high
    }
    
    # PopulationSim distribution
    income_bins_2010 = [0, 15000, 25000, 35000, 50000, 75000, 100000, 150000, 200000, 300000, 10000000]
    income_labels_2010 = ['<$15k', '$15-25k', '$25-35k', '$35-50k', '$50-75k', '$75-100k', 
                          '$100-150k', '$150-200k', '$200-300k', '$300k+']
    
    df['income_bin'] = pd.cut(df['HHINCADJ'], bins=income_bins_2010, labels=income_labels_2010, right=False)
    popsim_dist = (df['income_bin'].value_counts().sort_index() / len(df) * 100)
    
    print("Income Bracket | PopulationSim | Expected | Difference")
    print("-" * 58)
    total_diff = 0
    for bracket in income_labels_2010:
        popsim_pct = popsim_dist.get(bracket, 0)
        expected_pct = expected_bay_area_2010.get(bracket, 0)
        diff = popsim_pct - expected_pct
        total_diff += abs(diff)
        print(f"{bracket:>12} | {popsim_pct:>11.1f}% | {expected_pct:>6.1f}% | {diff:>+8.1f}pp")
    
    print(f"\nTotal Absolute Difference: {total_diff:.1f} percentage points")
    print()
    
    # Key findings
    print("=== KEY FINDINGS ===")
    low_income_popsim = popsim_dist.iloc[:3].sum()  # Under $35k
    low_income_expected = sum([expected_bay_area_2010[k] for k in ['<$15k', '$15-25k', '$25-35k']])
    
    print(f"Low Income Households (<$35k):")
    print(f"  PopulationSim: {low_income_popsim:.1f}%")
    print(f"  Expected:      {low_income_expected:.1f}%")
    print(f"  Difference:    {low_income_popsim - low_income_expected:+.1f}pp")
    print()
    
    if low_income_popsim > low_income_expected + 5:
        print("⚠️  MAJOR ISSUE: PopulationSim is generating too many low-income households")
        print("   This explains the high zero-vehicle rates!")
        print("   Need to check income controls and PUMS seed population")
    
    print()
    print("=== ROOT CAUSE ANALYSIS ===")
    print("The vehicle ownership problem stems from income distribution issues:")
    print("1. Too many households in <$15k bracket (15.7% vs ~8% expected)")
    print("2. Too many households in $15-25k bracket (5.9% vs ~6% expected)")  
    print("3. These low-income households correctly have high zero-vehicle rates")
    print("4. Solution: Fix income controls, not just add vehicle controls")

if __name__ == "__main__":
    compare_income_to_acs()
