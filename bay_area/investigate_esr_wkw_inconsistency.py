#!/usr/bin/env python3
"""
Investigate the ESR vs WKW inconsistency
"""

import pandas as pd

def main():
    print("INVESTIGATING ESR vs WKW INCONSISTENCY")
    print("=" * 45)
    
    # Load current output
    df = pd.read_csv('output_2023/populationsim_working_dir/output/persons_2023_tm2.csv')
    print(f"Loaded {len(df):,} persons")
    
    # Find the problematic records
    non_working_esr_has_wkw = df[df['ESR'].isin([0, 6]) & (df['WKW'] != -9)]
    
    print(f"\nPROBLEMATIC RECORDS: {len(non_working_esr_has_wkw):,}")
    print("ESR codes 0 (under 16) or 6 (not in labor force) but WKW ≠ -9")
    
    # Break down by ESR code
    print(f"\nBreakdown by ESR:")
    esr_breakdown = non_working_esr_has_wkw['ESR'].value_counts().sort_index()
    for esr, count in esr_breakdown.items():
        if esr == 0:
            desc = "Under 16"
        elif esr == 6:
            desc = "Not in labor force"
        else:
            desc = "Other"
        print(f"  ESR {esr} ({desc}): {count:,}")
    
    # Check WKW distribution for these records
    print(f"\nWKW distribution for problematic records:")
    wkw_breakdown = non_working_esr_has_wkw['WKW'].value_counts().sort_index()
    for wkw, count in wkw_breakdown.items():
        pct = (count / len(non_working_esr_has_wkw)) * 100
        if wkw == 1:
            desc = "50-52 weeks"
        elif wkw == 2:
            desc = "48-49 weeks"
        elif wkw == 3:
            desc = "40-47 weeks"
        elif wkw == 4:
            desc = "27-39 weeks"
        elif wkw == 5:
            desc = "14-26 weeks"
        elif wkw == 6:
            desc = "1-13 weeks"
        else:
            desc = "Other"
        print(f"  WKW {wkw} ({desc}): {count:,} ({pct:.1f}%)")
    
    # Check age distribution for ESR=0 cases
    if 'AGEP' in df.columns:
        esr_0_cases = non_working_esr_has_wkw[non_working_esr_has_wkw['ESR'] == 0]
        if len(esr_0_cases) > 0:
            print(f"\nESR=0 cases with work weeks:")
            print(f"  Count: {len(esr_0_cases):,}")
            print(f"  Age range: {esr_0_cases['AGEP'].min()}-{esr_0_cases['AGEP'].max()}")
            print(f"  Ages under 16: {(esr_0_cases['AGEP'] < 16).sum():,}")
            print(f"  Ages 16+: {(esr_0_cases['AGEP'] >= 16).sum():,}")
    
    # Check if these people are employed according to EMPLOYED flag
    if 'EMPLOYED' in df.columns:
        employed_count = (non_working_esr_has_wkw['EMPLOYED'] == 1).sum()
        print(f"\nOf the {len(non_working_esr_has_wkw):,} problematic records:")
        print(f"  Have EMPLOYED=1: {employed_count:,}")
        print(f"  Have EMPLOYED=0: {len(non_working_esr_has_wkw) - employed_count:,}")
    
    # Check what the raw data looks like
    print(f"\nRAW DATA INVESTIGATION:")
    raw_df = pd.read_csv('output_2023/populationsim_working_dir/output/synthetic_persons.csv')
    
    # Sample a few records to see what's in the raw data
    sample_indices = non_working_esr_has_wkw.index[:5]
    print(f"\nSample of problematic records (raw vs processed):")
    
    for idx in sample_indices:
        if idx < len(raw_df):
            raw_wkwn = raw_df.loc[idx, 'WKWN'] if 'WKWN' in raw_df.columns else 'N/A'
            raw_esr = raw_df.loc[idx, 'ESR'] if 'ESR' in raw_df.columns else 'N/A' 
            processed_wkw = df.loc[idx, 'WKW']
            processed_esr = df.loc[idx, 'ESR']
            age = df.loc[idx, 'AGEP'] if 'AGEP' in df.columns else 'N/A'
            
            print(f"  Record {idx}: Age={age}, Raw ESR={raw_esr}→{processed_esr}, Raw WKWN={raw_wkwn}→WKW={processed_wkw}")
    
    print(f"\nPOSSIBLE CAUSES:")
    print(f"1. ESR recoding issue - people who should have ESR changed but weren't")
    print(f"2. WKW mapping issue - WKWN values being mapped when they should be -9")
    print(f"3. Age recoding issue - people under 16 not getting ESR=0")
    print(f"4. Data inconsistency from source PUMS data")
    
    print(f"\nRECOMMENDED SOLUTIONS:")
    print(f"1. Force WKW=-9 for all ESR=0 and ESR=6 cases")
    print(f"2. Force ESR=0 for all people under 16")
    print(f"3. Investigate source data for logical inconsistencies")

if __name__ == "__main__":
    main()
