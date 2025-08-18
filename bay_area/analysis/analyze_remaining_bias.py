#!/usr/bin/env python3
"""
Deep dive analysis to find additional sources of vehicle ownership bias
beyond the ADJINC income conversion issue.
"""

import pandas as pd
import numpy as np

def analyze_additional_bias_sources():
    """Find other factors contributing to high zero-vehicle rates"""
    
    print("=" * 80)
    print("DEEP DIVE: ADDITIONAL SOURCES OF VEHICLE OWNERSHIP BIAS")
    print("=" * 80)
    
    # Load the current PopulationSim output
    hh_file = "output_2023/populationsim_working_dir/output/households_2023_tm2.csv"
    df = pd.read_csv(hh_file, usecols=['HHID', 'HHINCADJ', 'VEH', 'MTCCountyID', 'NP', 'HHT', 'TEN', 'BLD'])
    
    print(f"Loaded {len(df):,} households")
    print()
    
    # 1. DETAILED ZERO-VEHICLE ANALYSIS BY MULTIPLE FACTORS
    print("1. ZERO-VEHICLE RATES BY HOUSEHOLD CHARACTERISTICS")
    print("=" * 60)
    
    zero_veh = df[df['VEH'] == 0]
    total_zero_rate = len(zero_veh) / len(df) * 100
    
    print(f"Overall zero-vehicle rate: {total_zero_rate:.1f}%")
    print()
    
    # By income and household size combined
    print("By Income and Household Size:")
    income_bins = [0, 25000, 50000, 75000, 100000, 150000, 10000000]
    income_labels = ['<$25k', '$25-50k', '$50-75k', '$75-100k', '$100-150k', '$150k+']
    df['income_cat'] = pd.cut(df['HHINCADJ'], bins=income_bins, labels=income_labels, right=False)
    
    for size in [1, 2, 3, 4, 5]:
        size_label = f"{size}+" if size == 5 else str(size)
        size_mask = (df['NP'] >= size) if size == 5 else (df['NP'] == size)
        size_data = df[size_mask]
        
        print(f"  {size_label}-person households:")
        for income_cat in income_labels:
            cat_data = size_data[size_data['income_cat'] == income_cat]
            if len(cat_data) > 100:  # Only show if sufficient sample
                zero_rate = (cat_data['VEH'] == 0).mean() * 100
                count = len(cat_data)
                print(f"    {income_cat}: {zero_rate:5.1f}% ({count:,} households)")
        print()
    
    # 2. TENURE (OWN/RENT) ANALYSIS
    print("2. ZERO-VEHICLE RATES BY TENURE")
    print("=" * 40)
    
    tenure_map = {1: 'Owned', 2: 'Rented', 3: 'No cash rent', 4: 'No cash rent'}
    for tenure_code, tenure_name in tenure_map.items():
        if tenure_code in df['TEN'].values:
            tenure_data = df[df['TEN'] == tenure_code]
            zero_rate = (tenure_data['VEH'] == 0).mean() * 100
            count = len(tenure_data)
            print(f"  {tenure_name}: {zero_rate:5.1f}% ({count:,} households)")
    print()
    
    # 3. BUILDING TYPE ANALYSIS
    print("3. ZERO-VEHICLE RATES BY BUILDING TYPE")
    print("=" * 45)
    
    # BLD codes (Units in structure)
    bld_map = {
        1: 'Mobile home',
        2: 'One-family detached',
        3: 'One-family attached', 
        4: '2 apartments',
        5: '3-4 apartments',
        6: '5-9 apartments',
        7: '10-19 apartments',
        8: '20-49 apartments',
        9: '50+ apartments',
        10: 'Boat/RV/van'
    }
    
    for bld_code, bld_name in bld_map.items():
        if bld_code in df['BLD'].values:
            bld_data = df[df['BLD'] == bld_code]
            zero_rate = (bld_data['VEH'] == 0).mean() * 100
            count = len(bld_data)
            if count > 1000:  # Only show significant categories
                print(f"  {bld_name}: {zero_rate:5.1f}% ({count:,} households)")
    print()
    
    # 4. HOUSEHOLD TYPE ANALYSIS
    print("4. ZERO-VEHICLE RATES BY HOUSEHOLD TYPE")
    print("=" * 45)
    
    hht_map = {
        1: 'Married couple family',
        2: 'Other family, male householder',
        3: 'Other family, female householder', 
        4: 'Male householder nonfamily',
        5: 'Female householder nonfamily',
        6: 'Group quarters',
        7: 'Group quarters'
    }
    
    for hht_code, hht_name in hht_map.items():
        if hht_code in df['HHT'].values:
            hht_data = df[df['HHT'] == hht_code]
            zero_rate = (hht_data['VEH'] == 0).mean() * 100
            count = len(hht_data)
            print(f"  {hht_name}: {zero_rate:5.1f}% ({count:,} households)")
    print()
    
    # 5. COMPARISON TO EXPECTED PATTERNS
    print("5. POTENTIAL BIAS IDENTIFICATION")
    print("=" * 40)
    
    # Single-person households
    single_person = df[df['NP'] == 1]
    single_person_zero_rate = (single_person['VEH'] == 0).mean() * 100
    single_person_pct = len(single_person) / len(df) * 100
    
    print(f"Single-person households:")
    print(f"  Percentage of all households: {single_person_pct:.1f}%")
    print(f"  Zero-vehicle rate: {single_person_zero_rate:.1f}%")
    print(f"  Expected for Bay Area: ~30% zero-vehicle for singles")
    print()
    
    # Renters vs owners
    renters = df[df['TEN'] == 2] 
    owners = df[df['TEN'] == 1]
    
    if len(renters) > 0 and len(owners) > 0:
        renter_zero_rate = (renters['VEH'] == 0).mean() * 100
        owner_zero_rate = (owners['VEH'] == 0).mean() * 100
        renter_pct = len(renters) / len(df) * 100
        
        print(f"Tenure patterns:")
        print(f"  Renters: {renter_pct:.1f}% of households, {renter_zero_rate:.1f}% zero-vehicle")
        print(f"  Owners: {100-renter_pct:.1f}% of households, {owner_zero_rate:.1f}% zero-vehicle")
        print()
    
    # High-density housing
    high_density = df[df['BLD'] >= 7]  # 10+ unit buildings
    if len(high_density) > 0:
        high_density_zero_rate = (high_density['VEH'] == 0).mean() * 100
        high_density_pct = len(high_density) / len(df) * 100
        
        print(f"High-density housing (10+ units):")
        print(f"  Percentage of households: {high_density_pct:.1f}%")
        print(f"  Zero-vehicle rate: {high_density_zero_rate:.1f}%")
        print()
    
    # 6. CALCULATE REMAINING BIAS SOURCES
    print("6. QUANTIFYING REMAINING BIAS")
    print("=" * 35)
    
    # Current rates vs expected rates for different household types
    expected_rates = {
        'single_low_income': 60.0,    # Single person, low income
        'single_high_income': 20.0,   # Single person, high income  
        'family_low_income': 40.0,    # Family, low income
        'family_high_income': 3.0,    # Family, high income
        'high_density': 35.0,         # High-density building
        'suburban_family': 2.0        # Suburban family
    }
    
    # Calculate actual composition effects
    single_low = df[(df['NP'] == 1) & (df['HHINCADJ'] < 50000)]
    single_high = df[(df['NP'] == 1) & (df['HHINCADJ'] >= 50000)]
    family_low = df[(df['NP'] > 1) & (df['HHINCADJ'] < 50000)]
    family_high = df[(df['NP'] > 1) & (df['HHINCADJ'] >= 50000)]
    
    actual_rates = {
        'single_low_income': (single_low['VEH'] == 0).mean() * 100 if len(single_low) > 0 else 0,
        'single_high_income': (single_high['VEH'] == 0).mean() * 100 if len(single_high) > 0 else 0,
        'family_low_income': (family_low['VEH'] == 0).mean() * 100 if len(family_low) > 0 else 0,
        'family_high_income': (family_high['VEH'] == 0).mean() * 100 if len(family_high) > 0 else 0,
    }
    
    compositions = {
        'single_low_income': len(single_low) / len(df) * 100,
        'single_high_income': len(single_high) / len(df) * 100,
        'family_low_income': len(family_low) / len(df) * 100,
        'family_high_income': len(family_high) / len(df) * 100,
    }
    
    print("Category-specific analysis:")
    total_bias = 0
    for category in ['single_low_income', 'single_high_income', 'family_low_income', 'family_high_income']:
        actual = actual_rates[category]
        expected = expected_rates[category]
        composition = compositions[category]
        bias_contribution = (actual - expected) * composition / 100
        total_bias += bias_contribution
        
        print(f"  {category.replace('_', ' ').title()}:")
        print(f"    Composition: {composition:.1f}%")
        print(f"    Actual zero-veh rate: {actual:.1f}%")
        print(f"    Expected zero-veh rate: {expected:.1f}%") 
        print(f"    Bias contribution: {bias_contribution:+.2f}pp")
        print()
    
    print(f"Total estimated remaining bias: {total_bias:+.1f}pp")
    print(f"ADJINC fix reduces bias by: ~2.4pp") 
    print(f"Additional bias to address: {total_bias - 2.4:+.1f}pp")
    print()
    
    # 7. ROOT CAUSE HYPOTHESES
    print("7. LIKELY ADDITIONAL ROOT CAUSES")
    print("=" * 40)
    
    print("A. HOUSEHOLD COMPOSITION BIAS:")
    single_person_bias = compositions['single_low_income'] + compositions['single_high_income'] - 27.5
    print(f"   - Single-person household rate: {single_person_pct:.1f}% vs ~27% expected")
    if single_person_pct > 30:
        print(f"   - LIKELY ISSUE: Too many single-person households")
    
    print()
    print("B. TENURE BIAS (rent vs own):")
    if len(renters) > 0:
        print(f"   - Renter percentage: {renter_pct:.1f}%")
        print(f"   - Renter zero-vehicle rate: {renter_zero_rate:.1f}%")
        if renter_pct > 60 or renter_zero_rate > 25:
            print(f"   - LIKELY ISSUE: Too many renters or renter rates too high")
    
    print()
    print("C. BUILDING TYPE BIAS:")
    if len(high_density) > 0:
        print(f"   - High-density housing: {high_density_pct:.1f}%")
        print(f"   - High-density zero-vehicle: {high_density_zero_rate:.1f}%")
        if high_density_pct > 15 or high_density_zero_rate > 40:
            print(f"   - POSSIBLE ISSUE: High-density allocation")
    
    print()
    print("D. CONTROLS MISSING:")
    print("   - PopulationSim may lack vehicle ownership controls")
    print("   - Income controls may be insufficient even with ADJINC fix")
    print("   - Need direct vehicle ownership targets by geography/demographics")

if __name__ == "__main__":
    analyze_additional_bias_sources()
