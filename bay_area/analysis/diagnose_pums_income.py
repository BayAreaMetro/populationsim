#!/usr/bin/env python3
"""
Diagnose PUMS income conversion issues.
Check if ADJINC factor is being used correctly and if income conversion is working.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def diagnose_income_conversion():
    """Diagnose the income conversion process"""
    
    print("=" * 80)
    print("PUMS INCOME CONVERSION DIAGNOSTIC")
    print("=" * 80)
    
    # Check if we can find the source seed population files
    print("1. Checking for source PUMS files...")
    
    # Check potential PUMS locations
    pums_locations = [
        Path("M:/Data/Census/PUMS/PUMS 2023 5-Year/bay_area_households_2019_2023_crosswalked.csv"),
        Path("data/bay_area_households_2019_2023_crosswalked.csv"),
        Path("hh_gq/data/seed_households.csv"),
    ]
    
    source_file = None
    for location in pums_locations:
        if location.exists():
            source_file = location
            print(f"   Found: {location}")
            break
        else:
            print(f"   Not found: {location}")
    
    if not source_file:
        print("   No source PUMS files found. Checking preprocessed seed files...")
        
        # Check for preprocessed seed files
        seed_locations = [
            Path("hh_gq/data/seed_households.csv"),
            Path("output_2023/populationsim_working_dir/data/seed_households.csv"),
        ]
        
        for location in seed_locations:
            if location.exists():
                source_file = location
                print(f"   Found preprocessed: {location}")
                break
    
    if not source_file:
        print("   ERROR: Cannot find any seed population files!")
        return
    
    print()
    print("2. Loading seed population data...")
    
    # Load the data
    try:
        df = pd.read_csv(source_file)
        print(f"   Loaded {len(df):,} households from {source_file}")
        print(f"   Columns: {list(df.columns)}")
        print()
        
        # Check for income-related columns
        income_cols = [col for col in df.columns if 'income' in col.lower() or 'hincp' in col.lower()]
        adjinc_cols = [col for col in df.columns if 'adjinc' in col.lower()]
        
        print("3. Income-related columns found:")
        for col in income_cols:
            print(f"   {col}")
        
        print()
        print("4. ADJINC-related columns found:")
        for col in adjinc_cols:
            print(f"   {col}")
        if not adjinc_cols:
            print("   ⚠️  NO ADJINC COLUMNS FOUND!")
        
        print()
        
        # Analyze income distributions if income columns exist
        if income_cols:
            print("5. Income distribution analysis:")
            
            for col in income_cols:
                if col in df.columns:
                    valid_income = df[df[col] > 0][col]
                    if len(valid_income) > 0:
                        print(f"   {col}:")
                        print(f"     Count: {len(valid_income):,}")
                        print(f"     Mean:  ${valid_income.mean():,.0f}")
                        print(f"     Median: ${valid_income.median():,.0f}")
                        print(f"     Min:   ${valid_income.min():,.0f}")
                        print(f"     Max:   ${valid_income.max():,.0f}")
                        print()
        
        # Check if this matches our final output
        print("6. Comparison to final PopulationSim output:")
        output_file = Path("output_2023/populationsim_working_dir/output/households_2023_tm2.csv")
        
        if output_file.exists():
            output_df = pd.read_csv(output_file, usecols=['HHINCADJ'])
            
            print(f"   Final output median: ${output_df['HHINCADJ'].median():,.0f}")
            
            # If we have hh_income_2010 in seed, compare
            if 'hh_income_2010' in df.columns:
                seed_median = df[df['hh_income_2010'] > 0]['hh_income_2010'].median()
                print(f"   Seed hh_income_2010 median: ${seed_median:,.0f}")
                
                if abs(seed_median - output_df['HHINCADJ'].median()) < 1000:
                    print("   ✓ Seed and output medians match - using hh_income_2010")
                else:
                    print("   ⚠️  Seed and output medians don't match")
            
            # If we have HINCP, check if it's being converted properly  
            if 'HINCP' in df.columns:
                hincp_median = df[df['HINCP'] > 0]['HINCP'].median()
                print(f"   Raw HINCP median: ${hincp_median:,.0f}")
                
                # Test CPI conversion
                from cpi_conversion import convert_2023_to_2010_dollars
                converted_median = convert_2023_to_2010_dollars(hincp_median)
                print(f"   HINCP → 2010$ median: ${converted_median:,.0f}")
                
                output_median = output_df['HHINCADJ'].median()
                if abs(converted_median - output_median) < 1000:
                    print("   ✓ CPI conversion working correctly")
                else:
                    print(f"   ⚠️  CPI conversion issue: {converted_median:,.0f} vs {output_median:,.0f}")
        
        print()
        print("7. ADJINC Analysis:")
        
        if adjinc_cols and 'HINCP' in df.columns:
            adjinc_col = adjinc_cols[0]
            
            # Check ADJINC values
            adjinc_values = df[adjinc_col].value_counts().head(10)
            print(f"   Top 10 {adjinc_col} values:")
            for value, count in adjinc_values.items():
                factor = value / 1000000
                print(f"     {value:>8} ({factor:.6f}) - {count:,} households")
            
            # Test proper ADJINC application
            print()
            print("   Testing proper ADJINC income conversion:")
            test_sample = df[(df['HINCP'] > 0) & (df[adjinc_col] > 0)].head(5)
            
            for idx, row in test_sample.iterrows():
                hincp_raw = row['HINCP']
                adjinc = row[adjinc_col]
                
                # Proper PUMS adjustment: (ADJINC/1000000) * HINCP gives 2021$ 
                income_2021 = (adjinc / 1000000) * hincp_raw
                
                # Then convert 2021$ to 2010$ using CPI
                # CPI 2010 = 218.056, CPI 2021 ≈ 270.970
                cpi_2010_to_2021 = 270.970 / 218.056
                income_2010_correct = income_2021 / cpi_2010_to_2021
                
                # Compare to what's actually in our output (if available)
                if 'hh_income_2010' in df.columns:
                    actual_2010 = row['hh_income_2010']
                    print(f"     HINCP {hincp_raw:>6.0f} × ADJINC {adjinc/1000000:.6f} = ${income_2021:>7.0f} (2021$) → ${income_2010_correct:>7.0f} (2010$) [actual: ${actual_2010:>7.0f}]")
                else:
                    print(f"     HINCP {hincp_raw:>6.0f} × ADJINC {adjinc/1000000:.6f} = ${income_2021:>7.0f} (2021$) → ${income_2010_correct:>7.0f} (2010$)")
        
        else:
            if not adjinc_cols:
                print("   ⚠️  CRITICAL: No ADJINC column found!")
                print("   This means PUMS income is not being properly adjusted!")
                print("   Raw HINCP values are in survey year dollars, not constant dollars.")
            
            if 'HINCP' not in df.columns:
                print("   ⚠️  No HINCP column found in seed data")
        
        print()
        print("8. DIAGNOSIS SUMMARY:")
        
        if not adjinc_cols:
            print("   🔴 MAJOR ISSUE: Missing ADJINC factor")
            print("      - PUMS income (HINCP) must be adjusted with ADJINC")
            print("      - Each household's income is in the survey year it was collected")
            print("      - Without ADJINC, incomes are inconsistent across years")
            print("      - This could explain income distribution problems")
            
        elif 'hh_income_2010' in df.columns and income_cols:
            print("   🟡 Income conversion appears to be implemented")
            print("   Need to verify ADJINC is being used correctly in seed creation")
            
        else:
            print("   🔴 Unable to determine income conversion status")
            print("   Need to check seed population creation process")
    
    except Exception as e:
        print(f"   ERROR loading data: {e}")

if __name__ == "__main__":
    diagnose_income_conversion()
