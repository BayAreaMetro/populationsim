#!/usr/bin/env python3
"""
Check ESR (Employment Status Recode) implementation
"""

import pandas as pd

def main():
    print("ESR (Employment Status Recode) IMPLEMENTATION CHECK")
    print("=" * 50)
    
    # Load current output
    df = pd.read_csv('output_2023/populationsim_working_dir/output/persons_2023_tm2.csv')
    print(f"Loaded {len(df):,} persons")
    
    # Check ESR values
    if 'ESR' in df.columns:
        print(f"\n1. ESR VALUE ANALYSIS:")
        esr_counts = df['ESR'].value_counts().sort_index()
        
        for val, count in esr_counts.items():
            pct = (count / len(df)) * 100
            if val == 0:
                desc = "N/A (under 16)"
            elif val == 1:
                desc = "Civilian employed, at work"
            elif val == 2:
                desc = "Civilian employed, not at work" 
            elif val == 3:
                desc = "Unemployed"
            elif val == 4:
                desc = "Armed forces, at work"
            elif val == 5:
                desc = "Armed forces, not at work"
            elif val == 6:
                desc = "Not in labor force"
            else:
                desc = "Unknown code"
            
            print(f"   ESR {val}: {count:,} ({pct:.1f}%) - {desc}")
    else:
        print("❌ ESR column not found!")
        return
    
    # Check age consistency
    if 'AGEP' in df.columns:
        print(f"\n2. AGE vs ESR CONSISTENCY:")
        under_16 = (df['AGEP'] < 16).sum()
        print(f"   People under 16: {under_16:,}")
        
        # Check if people under 16 have ESR=0
        under_16_esr_0 = ((df['AGEP'] < 16) & (df['ESR'] == 0)).sum()
        under_16_esr_not_0 = ((df['AGEP'] < 16) & (df['ESR'] != 0)).sum()
        
        print(f"   People under 16 with ESR=0: {under_16_esr_0:,}")
        print(f"   People under 16 with ESR≠0: {under_16_esr_not_0:,}")
        
        if under_16_esr_not_0 > 0:
            print("   ❌ ISSUE: Some people under 16 don't have ESR=0")
            under_16_bad_esr = df[(df['AGEP'] < 16) & (df['ESR'] != 0)]['ESR'].value_counts()
            print(f"   Under-16 non-zero ESR values: {dict(under_16_bad_esr)}")
        else:
            print("   ✅ All people under 16 correctly have ESR=0")
            
        # Check if people 16+ with ESR=0
        over_16_esr_0 = ((df['AGEP'] >= 16) & (df['ESR'] == 0)).sum()
        if over_16_esr_0 > 0:
            print(f"   ⚠️  People 16+ with ESR=0: {over_16_esr_0:,} (may be valid if N/A for other reasons)")
    else:
        print("❌ AGEP column not found!")
    
    # Check ESR vs EMPLOYED consistency
    if 'EMPLOYED' in df.columns:
        print(f"\n3. ESR vs EMPLOYED CONSISTENCY:")
        
        # ESR 1,2,4,5 should be EMPLOYED=1
        employed_esr = df['ESR'].isin([1, 2, 4, 5])
        employed_flag = (df['EMPLOYED'] == 1)
        
        print(f"   ESR employed (1,2,4,5): {employed_esr.sum():,}")
        print(f"   EMPLOYED flag = 1: {employed_flag.sum():,}")
        
        # Check mismatches
        esr_employed_not_flagged = employed_esr & (df['EMPLOYED'] != 1)
        esr_not_employed_but_flagged = (~employed_esr) & (df['EMPLOYED'] == 1)
        
        print(f"   ESR employed but EMPLOYED≠1: {esr_employed_not_flagged.sum():,}")
        print(f"   ESR not employed but EMPLOYED=1: {esr_not_employed_but_flagged.sum():,}")
        
        if esr_employed_not_flagged.sum() > 0 or esr_not_employed_but_flagged.sum() > 0:
            print("   ❌ ISSUE: ESR and EMPLOYED flag are inconsistent")
        else:
            print("   ✅ ESR and EMPLOYED flag are consistent")
    
    # Check ESR vs WKW consistency  
    if 'WKW' in df.columns:
        print(f"\n4. ESR vs WKW CONSISTENCY:")
        
        # People not in labor force (ESR=6) or under 16 (ESR=0) should have WKW=-9
        not_working_esr = df['ESR'].isin([0, 6])
        no_work_wkw = (df['WKW'] == -9)
        
        print(f"   ESR not working (0,6): {not_working_esr.sum():,}")
        print(f"   WKW = -9 (didn't work): {no_work_wkw.sum():,}")
        
        # Check for people with working ESR but no WKW
        working_esr_no_wkw = df['ESR'].isin([1, 2, 3, 4, 5]) & (df['WKW'] == -9)
        not_working_esr_has_wkw = df['ESR'].isin([0, 6]) & (df['WKW'] != -9)
        
        print(f"   Working ESR but WKW=-9: {working_esr_no_wkw.sum():,}")
        print(f"   Non-working ESR but WKW≠-9: {not_working_esr_has_wkw.sum():,}")
        
        if working_esr_no_wkw.sum() > 0:
            print("   ⚠️  Some people with working ESR have no work weeks (may be valid for unemployed)")
        if not_working_esr_has_wkw.sum() > 0:
            print("   ❌ ISSUE: Some non-working people have work weeks")
    
    print(f"\n5. DOCUMENTATION REQUIREMENTS:")
    print(f"   ESR should be:")
    print(f"   - 0 for persons under 16 years old")
    print(f"   - 1-6 based on employment/labor force status for 16+")
    
    print(f"\n6. RECOMMENDED FIXES:")
    if 'AGEP' in df.columns and 'ESR' in df.columns:
        under_16_bad = ((df['AGEP'] < 16) & (df['ESR'] != 0)).sum()
        if under_16_bad > 0:
            print(f"   - Set ESR = 0 for {under_16_bad:,} people under 16")
        else:
            print(f"   ✅ ESR coding appears correct for age requirements")

if __name__ == "__main__":
    main()
