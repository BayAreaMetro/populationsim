#!/usr/bin/env python3
"""
Debug the income control vs seed population mismatch step by step.
"""

import pandas as pd
import numpy as np

def main():
    print("DEBUGGING INCOME CONTROL VS SEED POPULATION MISMATCH")
    print("=" * 60)
    
    # Step 1: Check what the census config is actually doing
    print("\n1. CENSUS CONFIG INCOME BRACKETS:")
    print("   According to config_census.py lines 134-139:")
    print("   hh_inc_30:      $0 - $41,399     (2023$)")
    print("   hh_inc_30_60:   $41,400 - $82,799 (2023$)")  
    print("   hh_inc_60_100:  $82,800 - $137,999 (2023$)")
    print("   hh_inc_100_plus: $138,000+        (2023$)")
    print("   These are labeled as '30', '30_60' etc but use 2023$ brackets")
    
    # Step 2: Check what PopulationSim expressions expect
    print("\n2. POPULATIONSIM CONTROL EXPRESSIONS:")
    print("   From controls.csv:")
    print("   hh_inc_30:      households.hh_income_2010 <= 29999")
    print("   hh_inc_30_60:   households.hh_income_2010 >= 30000 & <= 59999")  
    print("   hh_inc_60_100:  households.hh_income_2010 >= 60000 & <= 99999")
    print("   hh_inc_100_plus: households.hh_income_2010 >= 100000")
    print("   These use hh_income_2010 field with 2010$ brackets")
    
    # Step 3: Check TAZ marginals
    print("\n3. TAZ MARGINALS (what controls are actually targeting):")
    taz_marginals = pd.read_csv('output_2023/populationsim_working_dir/data/taz_marginals.csv')
    total_hh = taz_marginals[['hh_inc_30', 'hh_inc_30_60', 'hh_inc_60_100', 'hh_inc_100_plus']].sum().sum()
    
    print(f"   hh_inc_30:      {taz_marginals['hh_inc_30'].sum():8.0f} ({taz_marginals['hh_inc_30'].sum()/total_hh*100:5.1f}%)")
    print(f"   hh_inc_30_60:   {taz_marginals['hh_inc_30_60'].sum():8.0f} ({taz_marginals['hh_inc_30_60'].sum()/total_hh*100:5.1f}%)")
    print(f"   hh_inc_60_100:  {taz_marginals['hh_inc_60_100'].sum():8.0f} ({taz_marginals['hh_inc_60_100'].sum()/total_hh*100:5.1f}%)")
    print(f"   hh_inc_100_plus:{taz_marginals['hh_inc_100_plus'].sum():8.0f} ({taz_marginals['hh_inc_100_plus'].sum()/total_hh*100:5.1f}%)")
    print(f"   Total:          {total_hh:8.0f}")
    
    # Step 4: Check what Census ACS 2023 actually shows
    print("\n4. ACTUAL ACS 2023 CENSUS DATA (ground truth):")
    census_data = pd.read_csv('bay_area_income_acs_2023.csv')
    census_total = census_data['Total_Households'].sum()
    
    print(f"   $0-41K:         {census_data['$0-41K'].sum():8.0f} ({census_data['$0-41K'].sum()/census_total*100:5.1f}%)")
    print(f"   $41K-83K:       {census_data['$41K-83K'].sum():8.0f} ({census_data['$41K-83K'].sum()/census_total*100:5.1f}%)")
    print(f"   $83K-138K:      {census_data['$83K-138K'].sum():8.0f} ({census_data['$83K-138K'].sum()/census_total*100:5.1f}%)")
    print(f"   $138K+:         {census_data['$138K+'].sum():8.0f} ({census_data['$138K+'].sum()/census_total*100:5.1f}%)")
    print(f"   Total:          {census_total:8.0f}")
    
    # Step 5: Check seed population income fields
    print("\n5. SEED POPULATION INCOME DISTRIBUTION:")
    try:
        # Look for seed population file
        seed_files = ['synthetic_households.csv', 'households_2023_tm2.csv']
        seed_df = None
        
        for file in seed_files:
            try:
                seed_df = pd.read_csv(f'output_2023/{file}', nrows=50000)  # Sample for speed
                print(f"   Using {file} (50k sample)")
                break
            except:
                continue
                
        if seed_df is None:
            print("   Could not find seed population file")
            return
            
        # Check what income fields exist
        income_cols = [col for col in seed_df.columns if 'income' in col.lower() or 'hincp' in col.lower()]
        print(f"   Available income columns: {income_cols}")
        
        # If we have hh_income_2010, check its distribution vs 2010$ brackets
        if 'hh_income_2010' in seed_df.columns:
            income_2010 = seed_df['hh_income_2010'].dropna()
            print(f"\n   hh_income_2010 distribution (2010$ brackets):")
            print(f"   <= $29,999:     {(income_2010 <= 29999).sum():8.0f} ({(income_2010 <= 29999).mean()*100:5.1f}%)")
            print(f"   $30K-59,999:    {((income_2010 >= 30000) & (income_2010 <= 59999)).sum():8.0f} ({((income_2010 >= 30000) & (income_2010 <= 59999)).mean()*100:5.1f}%)")
            print(f"   $60K-99,999:    {((income_2010 >= 60000) & (income_2010 <= 99999)).sum():8.0f} ({((income_2010 >= 60000) & (income_2010 <= 99999)).mean()*100:5.1f}%)")
            print(f"   >= $100,000:    {(income_2010 >= 100000).sum():8.0f} ({(income_2010 >= 100000).mean()*100:5.1f}%)")
            print(f"   Total non-null: {len(income_2010):8.0f}")
            
        # If we have HINCP or HHINCADJ, check it too
        hincp_col = None
        if 'HINCP' in seed_df.columns:
            hincp_col = 'HINCP'
        elif 'HHINCADJ' in seed_df.columns:
            hincp_col = 'HHINCADJ'
            
        if hincp_col:
            hincp = seed_df[hincp_col].dropna()
            print(f"\n   {hincp_col} distribution (assuming 2023$ based on ADJINC conversion):")
            print(f"   <= $41,399:     {(hincp <= 41399).sum():8.0f} ({(hincp <= 41399).mean()*100:5.1f}%)")
            print(f"   $41,400-82,799: {((hincp >= 41400) & (hincp <= 82799)).sum():8.0f} ({((hincp >= 41400) & (hincp <= 82799)).mean()*100:5.1f}%)")
            print(f"   $82,800-137,999:{((hincp >= 82800) & (hincp <= 137999)).sum():8.0f} ({((hincp >= 82800) & (hincp <= 137999)).mean()*100:5.1f}%)")
            print(f"   >= $138,000:    {(hincp >= 138000).sum():8.0f} ({(hincp >= 138000).mean()*100:5.1f}%)")
            print(f"   Total non-null: {len(hincp):8.0f}")
            
    except Exception as e:
        print(f"   Error reading seed data: {e}")
    
    print("\n6. THE MISMATCH ANALYSIS:")
    print("   If TAZ controls were generated using 2023$ brackets (0-41K, etc):")
    print("   But PopulationSim expressions use 2010$ brackets (0-30K, etc):")
    print("   Then PopulationSim can't match the targets!")
    
    print(f"\n   TAZ Controls target (supposedly 2023$ brackets): {taz_marginals['hh_inc_30'].sum()/total_hh*100:5.1f}% in lowest bracket")
    print(f"   ACS 2023 actual (2023$ 0-41K bracket):           {census_data['$0-41K'].sum()/census_total*100:5.1f}% in lowest bracket")
    print(f"   Difference: {taz_marginals['hh_inc_30'].sum()/total_hh*100 - census_data['$0-41K'].sum()/census_total*100:+5.1f} percentage points")
    
    print("\n   If the TAZ controls don't match ACS 2023, then either:")
    print("   A) The control generation is using wrong brackets")
    print("   B) The control generation is using old data") 
    print("   C) There's a scaling/aggregation issue")

if __name__ == '__main__':
    main()
