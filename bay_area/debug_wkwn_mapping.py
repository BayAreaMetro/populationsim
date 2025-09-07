#!/usr/bin/env python3
"""
Debug WKWN to WKW mapping issue
"""

import pandas as pd
import numpy as np

def main():
    print("DEBUGGING WKWN TO WKW MAPPING ISSUE")
    print("=" * 50)
    
    # 1. Check seed data WKWN
    print("1. CHECKING SEED DATA...")
    seed = pd.read_csv('output_2023/populationsim_working_dir/data/seed_persons.csv')
    print(f"Seed shape: {seed.shape}")
    print(f"Seed has WKWN: {'WKWN' in seed.columns}")
    print(f"Seed has WKW: {'WKW' in seed.columns}")
    
    if 'WKWN' in seed.columns:
        wkwn_seed = seed['WKWN'].value_counts(dropna=False).sort_index()
        print(f"\nSeed WKWN - Non-null: {seed['WKWN'].notna().sum():,}, Null: {seed['WKWN'].isna().sum():,}")
        
        # Show distribution of WKWN values in ranges that map to WKW categories
        print("\nSeed WKWN distribution by WKW mapping ranges:")
        print(f"  NaN (→ WKW -9): {seed['WKWN'].isna().sum():,}")
        print(f"  1-13 weeks (→ WKW 1): {((seed['WKWN'] >= 1) & (seed['WKWN'] <= 13)).sum():,}")
        print(f"  14-26 weeks (→ WKW 2): {((seed['WKWN'] >= 14) & (seed['WKWN'] <= 26)).sum():,}")
        print(f"  27-39 weeks (→ WKW 3): {((seed['WKWN'] >= 27) & (seed['WKWN'] <= 39)).sum():,}")
        print(f"  40-47 weeks (→ WKW 4): {((seed['WKWN'] >= 40) & (seed['WKWN'] <= 47)).sum():,}")
        print(f"  48-49 weeks (→ WKW 5): {((seed['WKWN'] >= 48) & (seed['WKWN'] <= 49)).sum():,}")
        print(f"  50-52 weeks (→ WKW 6): {((seed['WKWN'] >= 50) & (seed['WKWN'] <= 52)).sum():,}")
    
    # 2. Check raw PopulationSim output (before postprocessing)
    print(f"\n2. CHECKING RAW POPULATIONSIM OUTPUT...")
    try:
        raw_synth = pd.read_csv('output_2023/populationsim_working_dir/output/synthetic_persons.csv')
        print(f"Raw synthetic shape: {raw_synth.shape}")
        print(f"Raw has WKWN: {'WKWN' in raw_synth.columns}")
        print(f"Raw has WKW: {'WKW' in raw_synth.columns}")
        
        # Check what work-related columns exist
        work_cols = [c for c in raw_synth.columns if 'WK' in c.upper()]
        print(f"Work-related columns in raw output: {work_cols}")
        
        if 'WKWN' in raw_synth.columns:
            print(f"\nRaw WKWN - Non-null: {raw_synth['WKWN'].notna().sum():,}, Null: {raw_synth['WKWN'].isna().sum():,}")
            
            # Show distribution
            print("\nRaw synthetic WKWN distribution by WKW mapping ranges:")
            print(f"  NaN (→ WKW -9): {raw_synth['WKWN'].isna().sum():,}")
            print(f"  1-13 weeks (→ WKW 1): {((raw_synth['WKWN'] >= 1) & (raw_synth['WKWN'] <= 13)).sum():,}")
            print(f"  14-26 weeks (→ WKW 2): {((raw_synth['WKWN'] >= 14) & (raw_synth['WKWN'] <= 26)).sum():,}")
            print(f"  27-39 weeks (→ WKW 3): {((raw_synth['WKWN'] >= 27) & (raw_synth['WKWN'] <= 39)).sum():,}")
            print(f"  40-47 weeks (→ WKW 4): {((raw_synth['WKWN'] >= 40) & (raw_synth['WKWN'] <= 47)).sum():,}")
            print(f"  48-49 weeks (→ WKW 5): {((raw_synth['WKWN'] >= 48) & (raw_synth['WKWN'] <= 49)).sum():,}")
            print(f"  50-52 weeks (→ WKW 6): {((raw_synth['WKWN'] >= 50) & (raw_synth['WKWN'] <= 52)).sum():,}")
            
        if 'WKW' in raw_synth.columns:
            print(f"\nRaw synthetic already has WKW column!")
            wkw_raw = raw_synth['WKW'].value_counts().sort_index()
            for val, count in wkw_raw.items():
                print(f"  WKW {val}: {count:,}")
    
    except FileNotFoundError:
        print("Raw synthetic_persons.csv not found")
    
    # 3. Check final postprocessed output
    print(f"\n3. CHECKING FINAL POSTPROCESSED OUTPUT...")
    final = pd.read_csv('output_2023/populationsim_working_dir/output/persons_2023_tm2.csv')
    print(f"Final shape: {final.shape}")
    print(f"Final has WKWN: {'WKWN' in final.columns}")
    print(f"Final has WKW: {'WKW' in final.columns}")
    
    work_cols_final = [c for c in final.columns if 'WK' in c.upper()]
    print(f"Work-related columns in final output: {work_cols_final}")
    
    if 'WKW' in final.columns:
        print(f"\nFinal WKW distribution:")
        wkw_final = final['WKW'].value_counts().sort_index()
        for val, count in wkw_final.items():
            pct = (count / len(final)) * 100
            print(f"  WKW {val}: {count:,} ({pct:.1f}%)")
    
    if 'WKWN' in final.columns:
        print(f"\nFinal still has WKWN column - Non-null: {final['WKWN'].notna().sum():,}")

if __name__ == "__main__":
    main()
