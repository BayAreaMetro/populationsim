#!/usr/bin/env python3
"""
Debug the actual WKWN to WKW mapping logic
"""

import pandas as pd
import numpy as np

def main():
    print("DEBUGGING ACTUAL WKWN TO WKW MAPPING LOGIC")
    print("=" * 55)
    
    # Load raw PopulationSim output
    raw = pd.read_csv('output_2023/populationsim_working_dir/output/synthetic_persons.csv')
    print(f"Raw data loaded: {len(raw):,} persons")
    
    # Show the actual WKWN values distribution
    print(f"\nActual WKWN values in raw synthetic data:")
    wkwn_counts = raw['WKWN'].value_counts(dropna=False).sort_index()
    print(f"Total values: {len(wkwn_counts)}")
    
    # Show all unique WKWN values
    non_null_wkwn = raw['WKWN'].dropna().unique()
    print(f"Non-null WKWN values: {sorted(non_null_wkwn)}")
    
    # Check max WKWN value
    max_wkwn = raw['WKWN'].max()
    min_wkwn = raw['WKWN'].min()
    print(f"WKWN range: {min_wkwn} to {max_wkwn}")
    
    # Check if there are any values > 52
    over_52 = (raw['WKWN'] > 52).sum()
    print(f"WKWN values > 52: {over_52}")
    
    # Check specific ranges
    print(f"\nDetailed WKWN distribution:")
    for i in range(int(min_wkwn) if not pd.isna(min_wkwn) else 1, int(max_wkwn) + 1 if not pd.isna(max_wkwn) else 53):
        count = (raw['WKWN'] == i).sum()
        if count > 0:
            print(f"  WKWN {i}: {count:,}")
    
    print(f"  WKWN NaN: {raw['WKWN'].isna().sum():,}")
    
    # Now manually apply the mapping to see what should happen
    print(f"\n" + "="*55)
    print("MANUAL MAPPING TEST")
    print("="*55)
    
    # Create a copy for testing
    test_df = raw.copy()
    test_df['WKW_TEST'] = -9  # Default
    
    # Apply the exact same logic as in postprocess_recode.py
    test_df.loc[test_df['WKWN'].isna(), 'WKW_TEST'] = -9
    test_df.loc[(test_df['WKWN'] >= 1) & (test_df['WKWN'] <= 13), 'WKW_TEST'] = 1
    test_df.loc[(test_df['WKWN'] >= 14) & (test_df['WKWN'] <= 26), 'WKW_TEST'] = 2
    test_df.loc[(test_df['WKWN'] >= 27) & (test_df['WKWN'] <= 39), 'WKW_TEST'] = 3
    test_df.loc[(test_df['WKWN'] >= 40) & (test_df['WKWN'] <= 47), 'WKW_TEST'] = 4
    test_df.loc[(test_df['WKWN'] >= 48) & (test_df['WKWN'] <= 49), 'WKW_TEST'] = 5
    test_df.loc[(test_df['WKWN'] >= 50) & (test_df['WKWN'] <= 52), 'WKW_TEST'] = 6
    
    # Check results
    wkw_test_counts = test_df['WKW_TEST'].value_counts().sort_index()
    print(f"Manual mapping results:")
    for val, count in wkw_test_counts.items():
        pct = (count / len(test_df)) * 100
        print(f"  WKW {val}: {count:,} ({pct:.1f}%)")
    
    # Load actual final output to compare
    final = pd.read_csv('output_2023/populationsim_working_dir/output/persons_2023_tm2.csv')
    wkw_final_counts = final['WKW'].value_counts().sort_index()
    
    print(f"\nActual final output:")
    for val, count in wkw_final_counts.items():
        pct = (count / len(final)) * 100
        print(f"  WKW {val}: {count:,} ({pct:.1f}%)")
    
    # Compare
    print(f"\nCOMPARISON (Expected vs Actual):")
    all_vals = sorted(set(wkw_test_counts.index) | set(wkw_final_counts.index))
    for val in all_vals:
        expected = wkw_test_counts.get(val, 0)
        actual = wkw_final_counts.get(val, 0)
        diff = actual - expected
        status = "✅" if diff == 0 else "❌"
        print(f"  WKW {val}: Expected={expected:,}, Actual={actual:,}, Diff={diff:+,} {status}")
    
    # If there's a mismatch in WKW=6, investigate further
    if wkw_final_counts.get(6, 0) != wkw_test_counts.get(6, 0):
        print(f"\n🔍 INVESTIGATING WKW=6 MISMATCH:")
        
        # Check if there's something weird in the data
        final_wkw6 = final[final['WKW'] == 6]
        print(f"Final WKW=6 count: {len(final_wkw6):,}")
        
        # Check other columns that might indicate the source
        if 'WKHP' in final.columns:
            wkhp_dist = final_wkw6['WKHP'].value_counts().sort_index()
            print(f"WKHP distribution for WKW=6 records (top 10):")
            for val, count in wkhp_dist.head(10).items():
                print(f"  WKHP {val}: {count:,}")

if __name__ == "__main__":
    main()
