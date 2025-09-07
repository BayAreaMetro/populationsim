#!/usr/bin/env python3
"""
Quick Employment Fields Inconsistency Check
Focus on OCCP vs other employment fields
"""

import pandas as pd
import numpy as np

def main():
    print("QUICK EMPLOYMENT FIELDS INCONSISTENCY CHECK")
    print("=" * 60)
    
    # Load data
    print("Loading data...")
    persons_2015 = pd.read_csv('example_2015_outputs/hh_persons_model/persons.csv')
    persons_2023 = pd.read_csv('output_2023/populationsim_working_dir/output/persons_2023_tm2.csv')
    
    print(f"2015: {len(persons_2015):,} persons")
    print(f"2023: {len(persons_2023):,} persons")
    
    # Key finding: Check OCCP vs other employment indicators
    def check_occp_consistency(df, year):
        print(f"\n{year} OCCP CONSISTENCY CHECK:")
        print("-" * 40)
        
        # People with valid OCCP (not 999)
        has_occp = (df['OCCP'] != 999) & (df['OCCP'].notna())
        no_occp = (df['OCCP'] == 999) | (df['OCCP'].isna())
        
        print(f"Has valid OCCP: {has_occp.sum():,} ({(has_occp.sum()/len(df)*100):.1f}%)")
        print(f"No OCCP (999): {no_occp.sum():,} ({(no_occp.sum()/len(df)*100):.1f}%)")
        
        # Cross-check with EMPLOYED
        has_occp_employed = has_occp & (df['EMPLOYED'] == 1)
        has_occp_unemployed = has_occp & (df['EMPLOYED'] == 0)
        no_occp_employed = no_occp & (df['EMPLOYED'] == 1)
        no_occp_unemployed = no_occp & (df['EMPLOYED'] == 0)
        
        print(f"\nOCCP vs EMPLOYED Cross-check:")
        print(f"  Has OCCP + Employed: {has_occp_employed.sum():,}")
        print(f"  Has OCCP + Not Employed: {has_occp_unemployed.sum():,} ⚠️")
        print(f"  No OCCP + Employed: {no_occp_employed.sum():,} ⚠️")  
        print(f"  No OCCP + Not Employed: {no_occp_unemployed.sum():,}")
        
        # Cross-check with WKW (worked last year)
        worked_last_year = (df['WKW'] != -9) & (df['WKW'].notna())
        
        has_occp_worked = has_occp & worked_last_year
        has_occp_no_work = has_occp & ~worked_last_year
        no_occp_worked = no_occp & worked_last_year
        no_occp_no_work = no_occp & ~worked_last_year
        
        print(f"\nOCCP vs WKW (worked last year) Cross-check:")
        print(f"  Has OCCP + Worked last year: {has_occp_worked.sum():,}")
        print(f"  Has OCCP + Didn't work: {has_occp_no_work.sum():,} ⚠️")
        print(f"  No OCCP + Worked last year: {no_occp_worked.sum():,} ⚠️")
        print(f"  No OCCP + Didn't work: {no_occp_no_work.sum():,}")
        
        # Cross-check with WKHP (hours worked)
        worked_hours = (df['WKHP'] != -9) & (df['WKHP'].notna()) & (df['WKHP'] > 0)
        
        has_occp_hours = has_occp & worked_hours
        has_occp_no_hours = has_occp & ~worked_hours
        no_occp_hours = no_occp & worked_hours
        no_occp_no_hours = no_occp & ~worked_hours
        
        print(f"\nOCCP vs WKHP (hours worked) Cross-check:")
        print(f"  Has OCCP + Has hours: {has_occp_hours.sum():,}")
        print(f"  Has OCCP + No hours: {has_occp_no_hours.sum():,} ⚠️")
        print(f"  No OCCP + Has hours: {no_occp_hours.sum():,} ⚠️")
        print(f"  No OCCP + No hours: {no_occp_no_hours.sum():,}")
        
        # Summary of potential issues
        issues = []
        if has_occp_unemployed.sum() > 0:
            issues.append(f"Has OCCP but not employed: {has_occp_unemployed.sum():,}")
        if no_occp_employed.sum() > 0:
            issues.append(f"Employed but no OCCP: {no_occp_employed.sum():,}")
        if has_occp_no_work.sum() > 0:
            issues.append(f"Has OCCP but didn't work last year: {has_occp_no_work.sum():,}")
        if no_occp_worked.sum() > 0:
            issues.append(f"Worked last year but no OCCP: {no_occp_worked.sum():,}")
        if no_occp_hours.sum() > 0:
            issues.append(f"Has work hours but no OCCP: {no_occp_hours.sum():,}")
            
        if issues:
            print(f"\n⚠️  POTENTIAL ISSUES FOUND:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print(f"\n✅ No major inconsistencies found")
            
        return {
            'has_occp_unemployed': has_occp_unemployed.sum(),
            'no_occp_employed': no_occp_employed.sum(),
            'has_occp_no_work': has_occp_no_work.sum(),
            'no_occp_worked': no_occp_worked.sum(),
            'no_occp_hours': no_occp_hours.sum()
        }
    
    # Check both years
    issues_2015 = check_occp_consistency(persons_2015, "2015")
    issues_2023 = check_occp_consistency(persons_2023, "2023")
    
    # Compare issues between years
    print(f"\n{'='*60}")
    print("COMPARISON OF ISSUES BETWEEN 2015 AND 2023")
    print("=" * 60)
    
    for issue_type in issues_2015.keys():
        change = issues_2023[issue_type] - issues_2015[issue_type]
        print(f"{issue_type}: 2015={issues_2015[issue_type]:,}, 2023={issues_2023[issue_type]:,}, Change={change:+,}")
    
    # Quick WKW distribution check
    print(f"\n{'='*60}")
    print("WKW DISTRIBUTION COMPARISON")
    print("=" * 60)
    
    print("\n2015 WKW Distribution:")
    wkw_2015 = persons_2015['WKW'].value_counts().sort_index()
    for val, count in wkw_2015.items():
        pct = (count / len(persons_2015)) * 100
        print(f"  {val}: {count:,} ({pct:.1f}%)")
    
    print("\n2023 WKW Distribution:")
    wkw_2023 = persons_2023['WKW'].value_counts().sort_index()
    for val, count in wkw_2023.items():
        pct = (count / len(persons_2023)) * 100
        print(f"  {val}: {count:,} ({pct:.1f}%)")
    
    # Check the big WKW=6 category in 2023
    wkw6_2023 = persons_2023[persons_2023['WKW'] == 6]
    print(f"\n2023 WKW=6 Analysis (50-52 weeks worked):")
    print(f"  Total with WKW=6: {len(wkw6_2023):,}")
    print(f"  Of those, employed now: {(wkw6_2023['EMPLOYED'] == 1).sum():,}")
    print(f"  Of those, have OCCP: {(wkw6_2023['OCCP'] != 999).sum():,}")
    print(f"  Of those, have work hours: {(wkw6_2023['WKHP'] > 0).sum():,}")

if __name__ == "__main__":
    main()
