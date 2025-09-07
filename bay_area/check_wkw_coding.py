#!/usr/bin/env python3
"""
Check WKW coding standards and compare our mapping
"""

import pandas as pd

def main():
    print("WKW CODING VERIFICATION")
    print("=" * 40)
    
    # Load 2015 baseline to see what WKW coding was used
    print("1. 2015 BASELINE WKW DISTRIBUTION:")
    df2015 = pd.read_csv('example_2015_outputs/hh_persons_model/persons.csv')
    wkw_2015 = df2015['WKW'].value_counts().sort_index()
    
    for val, count in wkw_2015.items():
        pct = (count / len(df2015)) * 100
        print(f"  WKW {val}: {count:,} ({pct:.1f}%)")
    
    # Load current 2023 output
    print("\n2. 2023 CURRENT WKW DISTRIBUTION:")
    df2023 = pd.read_csv('output_2023/populationsim_working_dir/output/persons_2023_tm2.csv')
    wkw_2023 = df2023['WKW'].value_counts().sort_index()
    
    for val, count in wkw_2023.items():
        pct = (count / len(df2023)) * 100
        print(f"  WKW {val}: {count:,} ({pct:.1f}%)")
    
    # Check what the Census PUMS WKW codes actually mean
    print("\n3. CENSUS PUMS WKW CODING (from documentation):")
    print("  -9 or blank = N/A (not in labor force)")
    print("  1 = 50-52 weeks worked")  # ← This might be the issue!
    print("  2 = 48-49 weeks worked")
    print("  3 = 40-47 weeks worked") 
    print("  4 = 27-39 weeks worked")
    print("  5 = 14-26 weeks worked")
    print("  6 = 1-13 weeks worked")
    
    print("\n4. OUR CURRENT MAPPING (what we implemented):")
    print("  WKWN 1-13 weeks → WKW 1")
    print("  WKWN 14-26 weeks → WKW 2") 
    print("  WKWN 27-39 weeks → WKW 3")
    print("  WKWN 40-47 weeks → WKW 4")
    print("  WKWN 48-49 weeks → WKW 5")
    print("  WKWN 50-52 weeks → WKW 6")
    
    print("\n5. WHAT THE MAPPING SHOULD BE (if Census standard):")
    print("  WKWN 1-13 weeks → WKW 6")
    print("  WKWN 14-26 weeks → WKW 5")
    print("  WKWN 27-39 weeks → WKW 4") 
    print("  WKWN 40-47 weeks → WKW 3")
    print("  WKWN 48-49 weeks → WKW 2")
    print("  WKWN 50-52 weeks → WKW 1")
    
    # Check raw WKWN in synthetic data
    print("\n6. RAW WKWN DISTRIBUTION IN SYNTHETIC DATA:")
    raw = pd.read_csv('output_2023/populationsim_working_dir/output/synthetic_persons.csv')
    
    # Show WKWN mapping ranges
    print(f"  NaN: {raw['WKWN'].isna().sum():,}")
    print(f"  1-13 weeks: {((raw['WKWN'] >= 1) & (raw['WKWN'] <= 13)).sum():,}")
    print(f"  14-26 weeks: {((raw['WKWN'] >= 14) & (raw['WKWN'] <= 26)).sum():,}")
    print(f"  27-39 weeks: {((raw['WKWN'] >= 27) & (raw['WKWN'] <= 39)).sum():,}")
    print(f"  40-47 weeks: {((raw['WKWN'] >= 40) & (raw['WKWN'] <= 47)).sum():,}")
    print(f"  48-49 weeks: {((raw['WKWN'] >= 48) & (raw['WKWN'] <= 49)).sum():,}")
    print(f"  50-52 weeks: {((raw['WKWN'] >= 50) & (raw['WKWN'] <= 52)).sum():,}")
    
    print("\n7. DIAGNOSIS:")
    if wkw_2023[1] < wkw_2023[6]:
        print("  ❌ Most people have WKW=6 instead of WKW=1")
        print("  ❌ This suggests our mapping is BACKWARDS from Census standard")
        print("  ❌ We need to REVERSE the WKW mapping")
    else:
        print("  ✅ WKW distribution looks reasonable")

if __name__ == "__main__":
    main()
