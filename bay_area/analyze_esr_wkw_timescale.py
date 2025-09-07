#!/usr/bin/env python3
"""
Analyze ESR vs WKW time scale differences
"""

import pandas as pd

def main():
    print("ESR vs WKW TIME SCALE ANALYSIS")
    print("=" * 40)
    print("ESR = Current employment status")
    print("WKW = Weeks worked in PAST 12 MONTHS")
    print()
    
    # Load current output
    df = pd.read_csv('output_2023/populationsim_working_dir/output/persons_2023_tm2.csv')
    print(f"Loaded {len(df):,} persons")
    
    # Create a detailed cross-tabulation
    print(f"\nDETAILED ESR vs WKW CROSS-TABULATION:")
    print("=" * 50)
    
    # Define ESR descriptions
    esr_desc = {
        0: "N/A (under 16)",
        1: "Civilian employed, at work", 
        2: "Civilian employed, not at work",
        3: "Unemployed",
        4: "Armed forces, at work",
        5: "Armed forces, not at work", 
        6: "Not in labor force"
    }
    
    # Define WKW descriptions
    wkw_desc = {
        -9: "N/A (didn't work)",
        1: "50-52 weeks",
        2: "48-49 weeks", 
        3: "40-47 weeks",
        4: "27-39 weeks",
        5: "14-26 weeks",
        6: "1-13 weeks"
    }
    
    # Create cross-tab
    crosstab = pd.crosstab(df['ESR'], df['WKW'], margins=True)
    
    print("ESR \\ WKW      ", end="")
    for wkw in sorted(df['WKW'].unique()):
        print(f"{wkw:>8}", end="")
    print(f"{'Total':>10}")
    print("-" * 70)
    
    for esr in sorted(df['ESR'].unique()):
        print(f"{esr} {esr_desc.get(esr, 'Unknown')[:15]:15}", end="")
        for wkw in sorted(df['WKW'].unique()):
            count = crosstab.loc[esr, wkw] if (esr in crosstab.index and wkw in crosstab.columns) else 0
            print(f"{count:8,}", end="")
        total = crosstab.loc[esr, 'All'] if esr in crosstab.index else 0
        print(f"{total:10,}")
    
    print("-" * 70)
    print("Total               ", end="")
    for wkw in sorted(df['WKW'].unique()):
        total = crosstab.loc['All', wkw] if wkw in crosstab.columns else 0
        print(f"{total:8,}", end="")
    grand_total = len(df)
    print(f"{grand_total:10,}")
    
    # Analyze specific cases that seem inconsistent
    print(f"\nANALYSIS OF 'INCONSISTENT' CASES:")
    print("=" * 40)
    
    # Case 1: ESR=3 (Unemployed) with WKW ≠ -9
    unemployed_worked = df[(df['ESR'] == 3) & (df['WKW'] != -9)]
    print(f"1. UNEMPLOYED but worked in past 12 months: {len(unemployed_worked):,}")
    if len(unemployed_worked) > 0:
        wkw_dist = unemployed_worked['WKW'].value_counts().sort_index()
        for wkw, count in wkw_dist.items():
            pct = (count / len(unemployed_worked)) * 100
            print(f"   WKW {wkw} ({wkw_desc[wkw]}): {count:,} ({pct:.1f}%)")
        print("   ✅ This is NORMAL - people can be currently unemployed but worked earlier in year")
    
    # Case 2: ESR=6 (Not in labor force) with WKW ≠ -9  
    not_in_lf_worked = df[(df['ESR'] == 6) & (df['WKW'] != -9)]
    print(f"\n2. NOT IN LABOR FORCE but worked in past 12 months: {len(not_in_lf_worked):,}")
    if len(not_in_lf_worked) > 0:
        wkw_dist = not_in_lf_worked['WKW'].value_counts().sort_index()
        for wkw, count in wkw_dist.items():
            pct = (count / len(not_in_lf_worked)) * 100
            print(f"   WKW {wkw} ({wkw_desc[wkw]}): {count:,} ({pct:.1f}%)")
        print("   ✅ This is NORMAL - people can retire/leave workforce but worked earlier in year")
    
    # Case 3: ESR=0 (Under 16) with WKW ≠ -9 - This SHOULD be inconsistent
    under_16_worked = df[(df['ESR'] == 0) & (df['WKW'] != -9)]
    print(f"\n3. UNDER 16 but worked in past 12 months: {len(under_16_worked):,}")
    if len(under_16_worked) > 0:
        print("   ❌ This IS PROBLEMATIC - people under 16 shouldn't have work weeks")
        if 'AGEP' in df.columns:
            age_dist = under_16_worked['AGEP'].value_counts().sort_index()
            print(f"   Age distribution:")
            for age, count in age_dist.head(10).items():
                print(f"     Age {age}: {count:,}")
    else:
        print("   ✅ No issues found")
    
    # Case 4: Currently employed (ESR 1,2,4,5) but WKW = -9
    employed_no_work = df[df['ESR'].isin([1, 2, 4, 5]) & (df['WKW'] == -9)]
    print(f"\n4. CURRENTLY EMPLOYED but WKW = -9 (no work in past 12 months): {len(employed_no_work):,}")
    if len(employed_no_work) > 0:
        esr_dist = employed_no_work['ESR'].value_counts().sort_index()
        for esr, count in esr_dist.items():
            print(f"   ESR {esr} ({esr_desc[esr]}): {count:,}")
        print("   ⚠️  This could be problematic - currently employed but no work in past year?")
    else:
        print("   ✅ No issues found")
    
    print(f"\nCONCLUSION:")
    print("=" * 15)
    print("✅ Most 'inconsistencies' are actually NORMAL due to time scale differences")
    print("✅ ESR=3 (unemployed) + WKW≠-9 = worked earlier, now unemployed")  
    print("✅ ESR=6 (not in labor force) + WKW≠-9 = worked earlier, now retired/out of workforce")
    if len(under_16_worked) > 0:
        print("❌ ESR=0 (under 16) + WKW≠-9 = needs fixing")
    if len(employed_no_work) > 0:
        print("⚠️  Currently employed + WKW=-9 = investigate further")

if __name__ == "__main__":
    main()
