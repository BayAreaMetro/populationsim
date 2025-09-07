#!/usr/bin/env python3
"""
Investigate WKWN to WKW mapping issue
"""

import pandas as pd
import numpy as np

def main():
    print("INVESTIGATING WKWN TO WKW MAPPING")
    print("=" * 50)
    
    # Load the 2023 data to check WKWN distribution
    print("Loading 2023 synthetic persons data...")
    persons_2023 = pd.read_csv('output_2023/populationsim_working_dir/output/persons_2023_tm2.csv')
    
    # Check if WKWN column exists
    if 'WKWN' in persons_2023.columns:
        print(f"\n✅ WKWN column found in 2023 data")
        
        # Show WKWN distribution
        print(f"\nWKWN (raw weeks worked) Distribution:")
        wkwn_counts = persons_2023['WKWN'].value_counts(dropna=False).sort_index()
        
        total_non_null = persons_2023['WKWN'].notna().sum()
        total_null = persons_2023['WKWN'].isna().sum()
        
        print(f"Total records: {len(persons_2023):,}")
        print(f"Non-null WKWN: {total_non_null:,}")
        print(f"Null WKWN: {total_null:,}")
        
        print(f"\nWKWN Value Distribution (top 20):")
        for val, count in wkwn_counts.head(20).items():
            pct = (count / len(persons_2023)) * 100
            print(f"  {val}: {count:,} ({pct:.2f}%)")
        
        # Check the 50-52 week range specifically
        wkwn_50_52 = persons_2023[(persons_2023['WKWN'] >= 50) & (persons_2023['WKWN'] <= 52)]
        print(f"\nWKWN 50-52 weeks: {len(wkwn_50_52):,} ({len(wkwn_50_52)/len(persons_2023)*100:.1f}%)")
        
        # Show the distribution within 50-52 range
        if len(wkwn_50_52) > 0:
            print("Distribution within 50-52 weeks:")
            for val in [50, 51, 52]:
                count = (persons_2023['WKWN'] == val).sum()
                print(f"  WKWN={val}: {count:,}")
        
        # Manually apply the mapping to see what we get
        print(f"\nMANUAL WKW MAPPING TEST:")
        
        # Count what would go into each WKW category
        wkw_test = pd.Series(-9, index=persons_2023.index)  # Default to -9
        
        wkw_test.loc[persons_2023['WKWN'].isna()] = -9                                              # Non-workers
        wkw_test.loc[(persons_2023['WKWN'] >= 1) & (persons_2023['WKWN'] <= 13)] = 1               # 1-13 weeks
        wkw_test.loc[(persons_2023['WKWN'] >= 14) & (persons_2023['WKWN'] <= 26)] = 2              # 14-26 weeks
        wkw_test.loc[(persons_2023['WKWN'] >= 27) & (persons_2023['WKWN'] <= 39)] = 3              # 27-39 weeks
        wkw_test.loc[(persons_2023['WKWN'] >= 40) & (persons_2023['WKWN'] <= 47)] = 4              # 40-47 weeks
        wkw_test.loc[(persons_2023['WKWN'] >= 48) & (persons_2023['WKWN'] <= 49)] = 5              # 48-49 weeks
        wkw_test.loc[(persons_2023['WKWN'] >= 50) & (persons_2023['WKWN'] <= 52)] = 6              # 50-52 weeks
        
        wkw_test_counts = wkw_test.value_counts().sort_index()
        
        print("Expected WKW distribution based on WKWN mapping:")
        for val, count in wkw_test_counts.items():
            pct = (count / len(persons_2023)) * 100
            print(f"  WKW={val}: {count:,} ({pct:.1f}%)")
            
        # Compare with actual WKW in the file
        if 'WKW' in persons_2023.columns:
            print(f"\nACTUAL WKW DISTRIBUTION IN FILE:")
            wkw_actual_counts = persons_2023['WKW'].value_counts().sort_index()
            for val, count in wkw_actual_counts.items():
                pct = (count / len(persons_2023)) * 100
                print(f"  WKW={val}: {count:,} ({pct:.1f}%)")
                
            # Check for differences
            print(f"\nCOMPARISON (Expected vs Actual):")
            all_vals = sorted(set(wkw_test_counts.index) | set(wkw_actual_counts.index))
            for val in all_vals:
                expected = wkw_test_counts.get(val, 0)
                actual = wkw_actual_counts.get(val, 0)
                diff = actual - expected
                if diff != 0:
                    print(f"  WKW={val}: Expected={expected:,}, Actual={actual:,}, Diff={diff:+,} ⚠️")
                else:
                    print(f"  WKW={val}: Expected={expected:,}, Actual={actual:,}, Diff=0 ✅")
    else:
        print(f"❌ WKWN column NOT found in 2023 data")
        print(f"Available columns: {list(persons_2023.columns)}")
        
    # Also check what WKWN values we actually have in the seed data
    print(f"\n" + "="*50)
    print("CHECKING SEED POPULATION WKWN VALUES")
    print("="*50)
    
    try:
        seed_persons = pd.read_csv('output_2023/populationsim_working_dir/seed_persons.csv')
        print(f"Seed persons data loaded: {len(seed_persons):,} records")
        
        if 'WKWN' in seed_persons.columns:
            print(f"\n✅ WKWN found in seed data")
            
            seed_wkwn_counts = seed_persons['WKWN'].value_counts(dropna=False).sort_index()
            seed_total_non_null = seed_persons['WKWN'].notna().sum()
            seed_total_null = seed_persons['WKWN'].isna().sum()
            
            print(f"Seed WKWN - Non-null: {seed_total_non_null:,}, Null: {seed_total_null:,}")
            
            print(f"\nSeed WKWN Distribution (top 15):")
            for val, count in seed_wkwn_counts.head(15).items():
                pct = (count / len(seed_persons)) * 100
                print(f"  {val}: {count:,} ({pct:.2f}%)")
                
            # Check 50-52 range in seed
            seed_50_52 = seed_persons[(seed_persons['WKWN'] >= 50) & (seed_persons['WKWN'] <= 52)]
            print(f"\nSeed WKWN 50-52 weeks: {len(seed_50_52):,} ({len(seed_50_52)/len(seed_persons)*100:.1f}%)")
        else:
            print(f"❌ WKWN column NOT found in seed data")
            print(f"Available columns in seed: {list(seed_persons.columns)}")
            
    except FileNotFoundError:
        print("❌ Seed persons file not found")

if __name__ == "__main__":
    main()
