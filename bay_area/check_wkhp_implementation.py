#!/usr/bin/env python3
"""
Check WKHP implementation and requirements
"""

import pandas as pd

def main():
    print("WKHP (Hours Worked) IMPLEMENTATION CHECK")
    print("=" * 45)
    
    # Load current output
    df = pd.read_csv('output_2023/populationsim_working_dir/output/persons_2023_tm2.csv')
    print(f"Loaded {len(df):,} persons")
    
    # Check available columns
    print(f"\nColumns available: {list(df.columns)}")
    
    # Check WKHP values
    if 'WKHP' in df.columns:
        print(f"\n1. WKHP VALUE ANALYSIS:")
        print(f"   Min WKHP: {df['WKHP'].min()}")
        print(f"   Max WKHP: {df['WKHP'].max()}")
        print(f"   People with WKHP=-9: {(df['WKHP'] == -9).sum():,}")
        print(f"   People with WKHP=0: {(df['WKHP'] == 0).sum():,}")
        print(f"   People with WKHP>0: {(df['WKHP'] > 0).sum():,}")
        
        # Show distribution of negative values
        negative_vals = [v for v in df['WKHP'].unique() if v < 0]
        print(f"   Negative WKHP values: {sorted(negative_vals)}")
        
        # Show top 10 WKHP values
        print(f"\n   Top 10 WKHP values:")
        wkhp_counts = df['WKHP'].value_counts().head(10)
        for val, count in wkhp_counts.items():
            pct = (count / len(df)) * 100
            print(f"     WKHP {val}: {count:,} ({pct:.1f}%)")
    else:
        print("❌ WKHP column not found!")
    
    # Check age distribution
    if 'AGEP' in df.columns:
        print(f"\n2. AGE ANALYSIS:")
        under_16 = (df['AGEP'] < 16).sum()
        print(f"   People under 16: {under_16:,}")
        
        if 'WKHP' in df.columns:
            under_16_with_hours = ((df['AGEP'] < 16) & (df['WKHP'] != -9)).sum()
            print(f"   People under 16 with WKHP != -9: {under_16_with_hours:,}")
            
            if under_16_with_hours > 0:
                print("   ❌ ISSUE: Some people under 16 have work hours (should be -9)")
                under_16_hours = df[(df['AGEP'] < 16) & (df['WKHP'] != -9)]['WKHP'].value_counts()
                print(f"   Under-16 WKHP values: {dict(under_16_hours)}")
            else:
                print("   ✅ All people under 16 have WKHP = -9")
    else:
        print("❌ AGEP column not found!")
    
    # Check consistency with WKW
    if 'WKHP' in df.columns and 'WKW' in df.columns:
        print(f"\n3. WKHP vs WKW CONSISTENCY:")
        
        # People who didn't work (WKW=-9) should have WKHP=-9
        no_work = (df['WKW'] == -9)
        no_work_with_hours = no_work & (df['WKHP'] != -9)
        print(f"   People with WKW=-9 (didn't work): {no_work.sum():,}")
        print(f"   Of those, have WKHP != -9: {no_work_with_hours.sum():,}")
        
        if no_work_with_hours.sum() > 0:
            print("   ❌ ISSUE: Some non-workers have work hours")
        else:
            print("   ✅ Non-workers correctly have WKHP = -9")
        
        # People who worked should have positive WKHP
        worked = (df['WKW'] != -9)
        worked_no_hours = worked & (df['WKHP'] <= 0)
        print(f"   People with WKW != -9 (worked): {worked.sum():,}")
        print(f"   Of those, have WKHP <= 0: {worked_no_hours.sum():,}")
        
        if worked_no_hours.sum() > 0:
            print("   ❌ ISSUE: Some workers have no work hours")
        else:
            print("   ✅ Workers correctly have positive WKHP")
    
    print(f"\n4. DOCUMENTATION REQUIREMENTS:")
    print(f"   WKHP should be:")
    print(f"   - -9 for persons under 16 years old")
    print(f"   - -9 for persons who did not work during past 12 months")  
    print(f"   - 1-99 for persons who worked")
    
    print(f"\n5. RECOMMENDED FIXES:")
    if 'AGEP' in df.columns and 'WKHP' in df.columns:
        under_16_bad = ((df['AGEP'] < 16) & (df['WKHP'] != -9)).sum()
        if under_16_bad > 0:
            print(f"   - Set WKHP = -9 for {under_16_bad:,} people under 16")
    
    if 'WKW' in df.columns and 'WKHP' in df.columns:
        non_workers_bad = ((df['WKW'] == -9) & (df['WKHP'] != -9)).sum()
        if non_workers_bad > 0:
            print(f"   - Set WKHP = -9 for {non_workers_bad:,} non-workers")

if __name__ == "__main__":
    main()
