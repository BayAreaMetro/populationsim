#!/usr/bin/env python3
"""
Compare PopulationSim TM2 household income (2010$) to 
ACS 2023 5-year estimates converted to 2010 dollars
"""

import pandas as pd
import numpy as np

def compare_income_2010_dollars():
    """Compare PopulationSim vs ACS, both in 2010 dollars"""
    
    print("=" * 80)
    print("INCOME COMPARISON: POPULATIONSIM vs ACS 2023 5-YEAR (both in 2010$)")
    print("=" * 80)
    
    # Load PopulationSim data (should already be in 2010$)
    print("Loading PopulationSim household data...")
    popsim_file = "output_2023/populationsim_working_dir/output/households_2023_tm2.csv"
    df = pd.read_csv(popsim_file, usecols=['HHID', 'HHINCADJ', 'VEH', 'MTCCountyID'])
    
    print(f"PopulationSim households: {len(df):,}")
    print()
    
    # ACS 2023 5-year median household income by Bay Area county (in 2023$)
    # Source: ACS Table B19013
    acs_2023_median = {
        'San Francisco': 136692,
        'San Mateo': 144370, 
        'Santa Clara': 140258,
        'Alameda': 103817,
        'Contra Costa': 113412,
        'Marin': 140347,
        'Napa': 92567,
        'Solano': 94013,
        'Sonoma': 98542
    }
    
    # Convert 2023$ to 2010$ using CPI inflation
    # CPI-U: 2010 = 218.056, 2023 = 307.026 (December values)
    # Inflation factor = 307.026 / 218.056 = 1.408
    inflation_2010_to_2023 = 1.408
    
    acs_2010_median = {county: income / inflation_2010_to_2023 
                       for county, income in acs_2023_median.items()}
    
    print("=== ACS 2023 5-YEAR MEDIAN HOUSEHOLD INCOME (converted to 2010$) ===")
    for county, income in acs_2010_median.items():
        print(f"{county:>15}: ${income:>7,.0f}")
    
    # Calculate regional weighted average
    # Using rough household counts for weighting
    county_weights = {
        'San Francisco': 350000,
        'San Mateo': 280000, 
        'Santa Clara': 650000,
        'Alameda': 580000,
        'Contra Costa': 400000,
        'Marin': 105000,
        'Napa': 50000,
        'Solano': 150000,
        'Sonoma': 200000
    }
    
    weighted_median = sum(acs_2010_median[county] * county_weights[county] 
                         for county in acs_2010_median.keys()) / sum(county_weights.values())
    
    print(f"{'Regional Weighted':>15}: ${weighted_median:>7,.0f}")
    print()
    
    # PopulationSim income statistics
    print("=== POPULATIONSIM INCOME STATISTICS (2010$) ===")
    print(f"{'Mean':>15}: ${df['HHINCADJ'].mean():>7,.0f}")
    print(f"{'Median':>15}: ${df['HHINCADJ'].median():>7,.0f}")
    print(f"{'25th percentile':>15}: ${df['HHINCADJ'].quantile(0.25):>7,.0f}")
    print(f"{'75th percentile':>15}: ${df['HHINCADJ'].quantile(0.75):>7,.0f}")
    print()
    
    # County-level comparison
    county_id_map = {1: 'San Francisco', 2: 'San Mateo', 3: 'Santa Clara', 4: 'Alameda',
                     5: 'Contra Costa', 6: 'Marin', 7: 'Napa', 8: 'Solano', 9: 'Sonoma'}
    
    print("=== COUNTY-LEVEL MEDIAN INCOME COMPARISON ===")
    print(f"{'County':>15} | {'PopSim':>8} | {'ACS':>8} | {'Diff':>7} | {'Diff%':>6}")
    print("-" * 65)
    
    for county_id, county_name in county_id_map.items():
        county_data = df[df['MTCCountyID'] == county_id]
        if len(county_data) > 0 and county_name in acs_2010_median:
            popsim_median = county_data['HHINCADJ'].median()
            acs_median = acs_2010_median[county_name]
            diff = popsim_median - acs_median
            diff_pct = (diff / acs_median) * 100
            
            print(f"{county_name:>15} | ${popsim_median:>7,.0f} | ${acs_median:>7,.0f} | ${diff:>6,.0f} | {diff_pct:>5.1f}%")
    
    # Regional comparison
    popsim_regional_median = df['HHINCADJ'].median()
    regional_diff = popsim_regional_median - weighted_median
    regional_diff_pct = (regional_diff / weighted_median) * 100
    
    print("-" * 65)
    print(f"{'REGIONAL':>15} | ${popsim_regional_median:>7,.0f} | ${weighted_median:>7,.0f} | ${regional_diff:>6,.0f} | {regional_diff_pct:>5.1f}%")
    print()
    
    # Income distribution analysis
    print("=== INCOME DISTRIBUTION COMPARISON (2010$) ===")
    
    # Define income brackets in 2010 dollars
    income_bins = [0, 15000, 25000, 35000, 50000, 75000, 100000, 150000, 200000, 300000, 10000000]
    income_labels = ['<$15k', '$15-25k', '$25-35k', '$35-50k', '$50-75k', '$75-100k', 
                     '$100-150k', '$150-200k', '$200-300k', '$300k+']
    
    df['income_bin'] = pd.cut(df['HHINCADJ'], bins=income_bins, labels=income_labels, right=False)
    popsim_dist = df['income_bin'].value_counts().sort_index()
    
    # Expected Bay Area distribution in 2010$ (rough estimates based on ACS patterns)
    # Bay Area is high-income, so very few under $25k, concentration in $75k-200k
    expected_bay_area_2010 = {
        '<$15k': 6.0,      # Very low for Bay Area (mostly subsidized housing)
        '$15-25k': 5.0,    # Low
        '$25-35k': 6.5,    # Low-moderate  
        '$35-50k': 9.0,    # Moderate
        '$50-75k': 15.5,   # Moderate-high
        '$75-100k': 14.0,  # High
        '$100-150k': 26.0, # Very high (largest bracket)
        '$150-200k': 11.0, # Very high
        '$200-300k': 5.5,  # Extremely high
        '$300k+': 1.5      # Ultra high
    }
    
    print(f"{'Income Bracket':>12} | {'PopSim':>8} | {'PopSim%':>8} | {'Expected%':>9} | {'Diff':>7}")
    print("-" * 70)
    
    total_diff = 0
    for bracket in income_labels:
        count = popsim_dist.get(bracket, 0)
        popsim_pct = (count / len(df)) * 100
        expected_pct = expected_bay_area_2010.get(bracket, 0)
        diff = popsim_pct - expected_pct
        total_diff += abs(diff)
        
        print(f"{bracket:>12} | {count:>8,} | {popsim_pct:>7.1f}% | {expected_pct:>8.1f}% | {diff:>+6.1f}pp")
    
    print("-" * 70)
    print(f"{'TOTAL ABS DIFF':>12} |          |          |           | {total_diff:>6.1f}pp")
    print()
    
    # Key findings
    print("=== KEY FINDINGS ===")
    
    # Low income analysis
    low_income_popsim = popsim_dist.iloc[:3].sum() / len(df) * 100  # Under $35k
    low_income_expected = sum([expected_bay_area_2010[k] for k in ['<$15k', '$15-25k', '$25-35k']])
    
    print(f"Low Income Households (<$35k in 2010$):")
    print(f"  PopulationSim: {low_income_popsim:.1f}%")
    print(f"  Expected:      {low_income_expected:.1f}%")
    print(f"  Difference:    {low_income_popsim - low_income_expected:+.1f} percentage points")
    print()
    
    # Vehicle ownership correlation
    zero_veh_rate = (df['VEH'] == 0).mean() * 100
    print(f"Zero-vehicle household rate: {zero_veh_rate:.1f}%")
    print(f"Expected for Bay Area: ~8-10%")
    print()
    
    # Assessment
    if abs(regional_diff_pct) < 10:
        print("✓ Regional median income reasonably close to ACS")
    else:
        print("⚠️  Regional median income significantly different from ACS")
    
    if low_income_popsim > low_income_expected + 8:
        print("⚠️  MAJOR ISSUE: Too many low-income households")
        print("   This explains high zero-vehicle rates")
        print("   Income controls may need adjustment")
    elif low_income_popsim < low_income_expected - 5:
        print("⚠️  Possible issue: Too few low-income households")
    else:
        print("✓ Low-income distribution appears reasonable")
    
    print()
    print("=== RECOMMENDATIONS ===")
    print("1. If PopulationSim income is actually in 2023$, convert to 2010$")
    print("2. Check seed population ADJINC application")
    print("3. Review income controls by county")
    print("4. Consider income-specific vehicle ownership controls")

if __name__ == "__main__":
    compare_income_2010_dollars()
