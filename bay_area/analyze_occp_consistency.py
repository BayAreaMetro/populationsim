#!/usr/bin/env python3
"""
Analyze OCCP (Occupation) consistency with employment indicators
"""

import pandas as pd

def main():
    print("OCCP (OCCUPATION) CONSISTENCY ANALYSIS")
    print("=" * 45)
    
    # Load current output
    df = pd.read_csv('output_2023/populationsim_working_dir/output/persons_2023_tm2.csv')
    print(f"Loaded {len(df):,} persons")
    
    # Check OCCP coding
    if 'OCCP' not in df.columns:
        print("❌ OCCP column not found!")
        return
    
    print(f"\n1. OCCP VALUE ANALYSIS:")
    print("=" * 25)
    
    # Define what constitutes "has occupation" vs "no occupation"
    has_occp = (df['OCCP'].notna()) & (df['OCCP'] != 999) & (df['OCCP'] != -9)
    no_occp = (df['OCCP'].isna()) | (df['OCCP'] == 999) | (df['OCCP'] == -9)
    
    print(f"Has valid OCCP: {has_occp.sum():,} ({has_occp.sum()/len(df)*100:.1f}%)")
    print(f"No OCCP (999/-9/NaN): {no_occp.sum():,} ({no_occp.sum()/len(df)*100:.1f}%)")
    
    # Show OCCP value distribution
    occp_counts = df['OCCP'].value_counts(dropna=False).sort_index()
    print(f"\nOCCP value distribution:")
    for val, count in occp_counts.items():
        pct = (count / len(df)) * 100
        if pd.isna(val):
            desc = "NaN"
        elif val == 999:
            desc = "N/A (standard PUMS code)"
        elif val == -9:
            desc = "N/A (recoded)"
        else:
            desc = f"Occupation code"
        print(f"  OCCP {val}: {count:,} ({pct:.1f}%) - {desc}")
    
    print(f"\n2. OCCP vs EMPLOYED CONSISTENCY:")
    print("=" * 35)
    
    if 'EMPLOYED' in df.columns:
        # Cross-tabulation
        employed = (df['EMPLOYED'] == 1)
        not_employed = (df['EMPLOYED'] == 0)
        
        # Case 1: Has OCCP but not employed
        has_occp_not_employed = has_occp & not_employed
        print(f"Has OCCP but EMPLOYED=0: {has_occp_not_employed.sum():,}")
        if has_occp_not_employed.sum() > 0:
            print("   ⚠️  These could be people with past occupation or unemployed with skill")
        
        # Case 2: Employed but no OCCP
        employed_no_occp = employed & no_occp
        print(f"EMPLOYED=1 but no OCCP: {employed_no_occp.sum():,}")
        if employed_no_occp.sum() > 0:
            print("   ❌ PROBLEMATIC: Currently employed people should have occupation")
            
            # Check what ESR codes these people have
            if 'ESR' in df.columns:
                esr_dist = df[employed_no_occp]['ESR'].value_counts().sort_index()
                print("   ESR distribution for employed without OCCP:")
                for esr, count in esr_dist.items():
                    print(f"     ESR {esr}: {count:,}")
        
        # Case 3: Both employed and have OCCP
        employed_has_occp = employed & has_occp
        print(f"EMPLOYED=1 and has OCCP: {employed_has_occp.sum():,}")
        print("   ✅ This is expected")
        
        # Case 4: Neither employed nor have OCCP
        not_employed_no_occp = not_employed & no_occp
        print(f"EMPLOYED=0 and no OCCP: {not_employed_no_occp.sum():,}")
        print("   ✅ This is expected for non-workers")
    
    print(f"\n3. OCCP vs ESR CONSISTENCY:")
    print("=" * 30)
    
    if 'ESR' in df.columns:
        # People with working ESR should generally have OCCP
        working_esr = df['ESR'].isin([1, 2, 4, 5])  # Employed ESR codes
        unemployed_esr = (df['ESR'] == 3)  # Unemployed
        not_in_lf_esr = (df['ESR'] == 6)   # Not in labor force
        under_16_esr = (df['ESR'] == 0)    # Under 16
        
        print(f"Working ESR (1,2,4,5) with OCCP: {(working_esr & has_occp).sum():,}")
        print(f"Working ESR (1,2,4,5) without OCCP: {(working_esr & no_occp).sum():,}")
        
        print(f"Unemployed ESR (3) with OCCP: {(unemployed_esr & has_occp).sum():,}")
        print(f"Unemployed ESR (3) without OCCP: {(unemployed_esr & no_occp).sum():,}")
        print("   ✅ Unemployed can have OCCP (past/target occupation)")
        
        print(f"Not in LF ESR (6) with OCCP: {(not_in_lf_esr & has_occp).sum():,}")
        print(f"Not in LF ESR (6) without OCCP: {(not_in_lf_esr & no_occp).sum():,}")
        print("   ✅ Not in LF can have OCCP (past occupation)")
        
        print(f"Under 16 ESR (0) with OCCP: {(under_16_esr & has_occp).sum():,}")
        print(f"Under 16 ESR (0) without OCCP: {(under_16_esr & no_occp).sum():,}")
        if (under_16_esr & has_occp).sum() > 0:
            print("   ❌ PROBLEMATIC: People under 16 shouldn't have occupation")
    
    print(f"\n4. OCCP vs WKW CONSISTENCY:")
    print("=" * 30)
    
    if 'WKW' in df.columns:
        worked_last_year = (df['WKW'] != -9)
        no_work_last_year = (df['WKW'] == -9)
        
        # People who worked should generally have OCCP
        worked_has_occp = worked_last_year & has_occp
        worked_no_occp = worked_last_year & no_occp
        
        print(f"Worked last year (WKW≠-9) with OCCP: {worked_has_occp.sum():,}")
        print(f"Worked last year (WKW≠-9) without OCCP: {worked_no_occp.sum():,}")
        if worked_no_occp.sum() > 0:
            print("   ❌ PROBLEMATIC: People who worked should have occupation")
        
        # People who didn't work may or may not have OCCP
        no_work_has_occp = no_work_last_year & has_occp
        no_work_no_occp = no_work_last_year & no_occp
        
        print(f"Didn't work (WKW=-9) with OCCP: {no_work_has_occp.sum():,}")
        print(f"Didn't work (WKW=-9) without OCCP: {no_work_no_occp.sum():,}")
        print("   ✅ Non-workers may have OCCP from previous experience")
    
    print(f"\n5. CROSS-TABULATION SUMMARY:")
    print("=" * 30)
    
    if all(col in df.columns for col in ['EMPLOYED', 'ESR', 'WKW']):
        # Create summary table
        summary_data = []
        
        categories = [
            ("Currently Employed", df['EMPLOYED'] == 1),
            ("Working ESR", df['ESR'].isin([1, 2, 4, 5])),
            ("Worked Last Year", df['WKW'] != -9),
            ("Unemployed", df['ESR'] == 3),
            ("Not in Labor Force", df['ESR'] == 6),
            ("Under 16", df['ESR'] == 0)
        ]
        
        print(f"{'Category':<20} {'Total':<10} {'Has OCCP':<10} {'No OCCP':<10} {'% with OCCP':<12}")
        print("-" * 65)
        
        for category_name, condition in categories:
            total = condition.sum()
            with_occp = (condition & has_occp).sum()
            without_occp = (condition & no_occp).sum()
            pct_with_occp = (with_occp / total * 100) if total > 0 else 0
            
            print(f"{category_name:<20} {total:<10,} {with_occp:<10,} {without_occp:<10,} {pct_with_occp:<12.1f}%")
    
    print(f"\n6. POTENTIAL DATA ISSUES:")
    print("=" * 25)
    
    issues = []
    if 'EMPLOYED' in df.columns:
        employed_no_occp_count = ((df['EMPLOYED'] == 1) & no_occp).sum()
        if employed_no_occp_count > 0:
            issues.append(f"Currently employed without occupation: {employed_no_occp_count:,}")
    
    if 'WKW' in df.columns:
        worked_no_occp_count = ((df['WKW'] != -9) & no_occp).sum()
        if worked_no_occp_count > 0:
            issues.append(f"Worked last year without occupation: {worked_no_occp_count:,}")
    
    if 'ESR' in df.columns:
        under_16_occp_count = ((df['ESR'] == 0) & has_occp).sum()
        if under_16_occp_count > 0:
            issues.append(f"Under 16 with occupation: {under_16_occp_count:,}")
    
    if issues:
        for issue in issues:
            print(f"❌ {issue}")
    else:
        print("✅ No major issues detected")

if __name__ == "__main__":
    main()
