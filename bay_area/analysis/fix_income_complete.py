#!/usr/bin/env python3
"""
Fix both the ADJINC problem and the dollar year mismatch
"""

import pandas as pd
import numpy as np

def fix_both_problems():
    """Fix seed generation AND control matching"""
    
    print("=" * 80)
    print("IMPLEMENTING THE COMPLETE INCOME FIX")
    print("=" * 80)
    print()
    
    print("STEP 1: Fix ADJINC in Seed Generation")
    print("=" * 45)
    print()
    print("We need to update create_seed_population_tm2_refactored.py")
    print("Current code probably does: hh_income_2023 = HINCP")  
    print("Should do: hh_income_2023 = HINCP * (ADJINC/1,000,000) * (310.0/270.970)")
    print()
    
    print("STEP 2: Fix Control Expressions")
    print("=" * 35)
    print()
    print("We need to update the controls.csv file")
    print("Option A: Change control expressions to use hh_income_2023 field")
    print("Option B: Change census controls to use 2010$ brackets")
    print()
    print("Let's go with Option A - update controls.csv to use 2023$ matching")
    print()
    
    # Show what the control expressions should become
    print("📝 REQUIRED CHANGES TO controls.csv:")
    print()
    
    current_expressions = [
        "hh_income_2010 <= 29999",
        "(hh_income_2010 >= 30000) & (hh_income_2010 <= 59999)", 
        "(hh_income_2010 >= 60000) & (hh_income_2010 <= 99999)",
        "hh_income_2010 >= 100000"
    ]
    
    new_expressions = [
        "hh_income_2023 <= 41399",
        "(hh_income_2023 >= 41400) & (hh_income_2023 <= 82799)",
        "(hh_income_2023 >= 82800) & (hh_income_2023 <= 137999)", 
        "hh_income_2023 >= 138000"
    ]
    
    print("CURRENT (wrong):")
    for i, expr in enumerate(current_expressions):
        print(f"  hh_inc_{['30', '30_60', '60_100', '100_plus'][i]}: {expr}")
    print()
    
    print("NEW (correct):")  
    for i, expr in enumerate(new_expressions):
        print(f"  hh_inc_{['30', '30_60', '60_100', '100_plus'][i]}: {expr}")
    print()
    
    print("STEP 3: Estimate the Combined Impact")
    print("=" * 40)
    print()
    
    # Load current data to estimate impact
    seed_file = "output_2023/populationsim_working_dir/data/seed_households.csv"
    df = pd.read_csv(seed_file, usecols=['hh_income_2010', 'hh_income_2023', 'HINCP', 'ADJINC'])
    
    # Filter to valid incomes
    valid_df = df[(df['hh_income_2010'] > 0) & (df['hh_income_2023'] > 0)].copy()
    
    print(f"Analyzing {len(valid_df):,} seed households...")
    print()
    
    # Calculate what corrected 2023$ income should be
    valid_df['corrected_income_2023'] = valid_df.apply(
        lambda row: (row['HINCP'] * row['ADJINC'] / 1_000_000) * (310.0 / 270.970), 
        axis=1
    )
    
    # Current distribution (wrong)
    current_low_income = len(valid_df[valid_df['hh_income_2023'] <= 41399]) / len(valid_df) * 100
    
    # Corrected distribution  
    corrected_low_income = len(valid_df[valid_df['corrected_income_2023'] <= 41399]) / len(valid_df) * 100
    
    print(f"💰 INCOME DISTRIBUTION COMPARISON:")
    print(f"   Current low-income rate (<=$41,399): {current_low_income:.1f}%")
    print(f"   Corrected low-income rate (<=$41,399): {corrected_low_income:.1f}%") 
    print(f"   Expected improvement: {current_low_income - corrected_low_income:+.1f} percentage points")
    print()
    
    # Estimate vehicle impact
    vehicle_improvement = (current_low_income - corrected_low_income) * 0.6  # 60% of low-income have 0 vehicles
    
    print(f"🚗 ESTIMATED VEHICLE OWNERSHIP IMPACT:")
    print(f"   Current zero-vehicle rate: 16.1%")
    print(f"   Expected reduction: {vehicle_improvement:.1f} percentage points")
    print(f"   Estimated new zero-vehicle rate: {16.1 - vehicle_improvement:.1f}%")
    print(f"   ACS target: ~10.2%")
    print()
    
    if vehicle_improvement >= 5:
        print("   ✅ This should get us very close to the ACS target!")
    elif vehicle_improvement >= 3:
        print("   ✅ This should be a major improvement!")
    else:
        print("   ⚠️  This helps but we may need additional fixes")
    
    print()
    print("STEP 4: Implementation Plan")
    print("=" * 32)
    print()
    print("1. Update create_seed_population_tm2_refactored.py:")
    print("   - Fix the _create_income_fields function to use ADJINC properly")
    print()
    print("2. Update controls.csv:")
    print("   - Change all income expressions from hh_income_2010 to hh_income_2023")
    print("   - Use 2023$ brackets: 41399, 82799, 137999")
    print() 
    print("3. Regenerate seed population with corrected income")
    print()
    print("4. Run PopulationSim with updated controls")
    print()
    print("5. Validate results against ACS targets")

if __name__ == "__main__":
    fix_both_problems()
