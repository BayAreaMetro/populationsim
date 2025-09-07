#!/usr/bin/env python3
"""
Compare Employment Fields Between 2015 and 2023 Synthetic Populations
Analyzes ESR, EMPLOYED, OCCP, WKW, WKHP fields and their cross-tabulations
to identify inconsistencies and differences between the two datasets.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data():
    """Load 2015 and 2023 synthetic persons data"""
    
    # 2015 data path
    persons_2015_path = Path('example_2015_outputs/hh_persons_model/persons.csv')
    
    # 2023 data path  
    persons_2023_path = Path('output_2023/populationsim_working_dir/output/persons_2023_tm2.csv')
    
    logging.info("Loading 2015 synthetic persons data...")
    if not persons_2015_path.exists():
        raise FileNotFoundError(f"2015 data not found: {persons_2015_path}")
    
    persons_2015 = pd.read_csv(persons_2015_path)
    logging.info(f"Loaded 2015 data: {len(persons_2015):,} persons")
    
    logging.info("Loading 2023 synthetic persons data...")
    if not persons_2023_path.exists():
        raise FileNotFoundError(f"2023 data not found: {persons_2023_path}")
    
    persons_2023 = pd.read_csv(persons_2023_path)
    logging.info(f"Loaded 2023 data: {len(persons_2023):,} persons")
    
    return persons_2015, persons_2023

def analyze_field_distributions(df_2015, df_2023, field):
    """Analyze distribution of a single field between 2015 and 2023"""
    
    print(f"\n{'='*80}")
    print(f"FIELD ANALYSIS: {field}")
    print(f"{'='*80}")
    
    # Basic field statistics
    print(f"\n{field} BASIC STATISTICS:")
    print(f"2015 - Total: {len(df_2015):,}, Non-null: {df_2015[field].notna().sum():,}, Null: {df_2015[field].isna().sum():,}")
    print(f"2023 - Total: {len(df_2023):,}, Non-null: {df_2023[field].notna().sum():,}, Null: {df_2023[field].isna().sum():,}")
    
    # Value distributions
    print(f"\n{field} VALUE DISTRIBUTIONS:")
    
    print("\n2015 Distribution:")
    dist_2015 = df_2015[field].value_counts(dropna=False).sort_index()
    for val, count in dist_2015.items():
        pct = (count / len(df_2015)) * 100
        print(f"  {val}: {count:,} ({pct:.2f}%)")
    
    print("\n2023 Distribution:")
    dist_2023 = df_2023[field].value_counts(dropna=False).sort_index()
    for val, count in dist_2023.items():
        pct = (count / len(df_2023)) * 100
        print(f"  {val}: {count:,} ({pct:.2f}%)")
    
    # Compare percentages
    print(f"\n{field} PERCENTAGE COMPARISON:")
    all_values = set(dist_2015.index) | set(dist_2023.index)
    
    for val in sorted(all_values, key=lambda x: (pd.isna(x), x)):
        pct_2015 = (dist_2015.get(val, 0) / len(df_2015)) * 100
        pct_2023 = (dist_2023.get(val, 0) / len(df_2023)) * 100
        diff = pct_2023 - pct_2015
        
        status = ""
        if abs(diff) > 5:
            status = " *** LARGE DIFFERENCE ***"
        elif abs(diff) > 1:
            status = " ** Notable difference **"
        
        print(f"  {val}: 2015={pct_2015:.2f}%, 2023={pct_2023:.2f}%, Diff={diff:+.2f}%{status}")

def create_crosstab_comparison(df_2015, df_2023, field1, field2):
    """Create and compare cross-tabulations between two fields for 2015 vs 2023"""
    
    print(f"\n{'='*80}")
    print(f"CROSS-TABULATION: {field1} × {field2}")
    print(f"{'='*80}")
    
    # Create crosstabs with percentages
    ct_2015 = pd.crosstab(df_2015[field1], df_2015[field2], margins=True, dropna=False)
    ct_2023 = pd.crosstab(df_2023[field1], df_2023[field2], margins=True, dropna=False)
    
    # Convert to percentages
    ct_2015_pct = (ct_2015 / len(df_2015)) * 100
    ct_2023_pct = (ct_2023 / len(df_2023)) * 100
    
    print(f"\n2015 Cross-tabulation ({field1} × {field2}) - Percentages:")
    print(ct_2015_pct.round(2))
    
    print(f"\n2023 Cross-tabulation ({field1} × {field2}) - Percentages:")
    print(ct_2023_pct.round(2))
    
    # Calculate differences
    print(f"\nDifference (2023 - 2015) - Percentage Points:")
    
    # Align indices for comparison
    all_rows = sorted(set(ct_2015_pct.index) | set(ct_2023_pct.index))
    all_cols = sorted(set(ct_2015_pct.columns) | set(ct_2023_pct.columns))
    
    diff_data = []
    for row in all_rows:
        row_data = []
        for col in all_cols:
            val_2015 = ct_2015_pct.loc[row, col] if (row in ct_2015_pct.index and col in ct_2015_pct.columns) else 0
            val_2023 = ct_2023_pct.loc[row, col] if (row in ct_2023_pct.index and col in ct_2023_pct.columns) else 0
            diff = val_2023 - val_2015
            row_data.append(diff)
        diff_data.append(row_data)
    
    diff_df = pd.DataFrame(diff_data, index=all_rows, columns=all_cols)
    print(diff_df.round(2))
    
    # Highlight significant differences
    print(f"\nSIGNIFICANT DIFFERENCES (>1 percentage point):")
    for row in diff_df.index:
        for col in diff_df.columns:
            if abs(diff_df.loc[row, col]) > 1:
                print(f"  {field1}={row}, {field2}={col}: {diff_df.loc[row, col]:+.2f} percentage points")

def analyze_employment_consistency(df, year):
    """Analyze consistency of employment-related fields within a dataset"""
    
    print(f"\n{'='*80}")
    print(f"EMPLOYMENT CONSISTENCY ANALYSIS - {year}")
    print(f"{'='*80}")
    
    # Check for potentially inconsistent combinations
    inconsistencies = []
    
    # Case 1: Has OCCP but EMPLOYED=0
    case1 = df[(df['OCCP'].notna()) & (df['OCCP'] != -999) & (df['EMPLOYED'] == 0)]
    if len(case1) > 0:
        inconsistencies.append(f"Has OCCP but EMPLOYED=0: {len(case1):,} cases")
    
    # Case 2: EMPLOYED=1 but no OCCP
    case2 = df[(df['EMPLOYED'] == 1) & ((df['OCCP'].isna()) | (df['OCCP'] == -999))]
    if len(case2) > 0:
        inconsistencies.append(f"EMPLOYED=1 but no OCCP: {len(case2):,} cases")
    
    # Case 3: Has WKW (worked) but EMPLOYED=0
    case3 = df[(df['WKW'].notna()) & (df['WKW'] != -9) & (df['EMPLOYED'] == 0)]
    if len(case3) > 0:
        inconsistencies.append(f"Has WKW (worked) but EMPLOYED=0: {len(case3):,} cases")
    
    # Case 4: EMPLOYED=1 but WKW=-9 (didn't work)
    case4 = df[(df['EMPLOYED'] == 1) & (df['WKW'] == -9)]
    if len(case4) > 0:
        inconsistencies.append(f"EMPLOYED=1 but WKW=-9 (didn't work): {len(case4):,} cases")
    
    # Case 5: Has WKHP (hours) but EMPLOYED=0
    case5 = df[(df['WKHP'].notna()) & (df['WKHP'] > 0) & (df['EMPLOYED'] == 0)]
    if len(case5) > 0:
        inconsistencies.append(f"Has WKHP (hours worked) but EMPLOYED=0: {len(case5):,} cases")
    
    # Case 6: EMPLOYED=1 but no WKHP
    case6 = df[(df['EMPLOYED'] == 1) & ((df['WKHP'].isna()) | (df['WKHP'] == 0))]
    if len(case6) > 0:
        inconsistencies.append(f"EMPLOYED=1 but no WKHP: {len(case6):,} cases")
    
    # Case 7: ESR employment status vs EMPLOYED flag mismatches
    # ESR 1,2,4,5 should correspond to EMPLOYED=1, ESR 3,6 to EMPLOYED=0
    employed_esr = df['ESR'].isin([1, 2, 4, 5])
    unemployed_esr = df['ESR'].isin([3, 6])
    
    case7a = df[employed_esr & (df['EMPLOYED'] == 0)]
    case7b = df[unemployed_esr & (df['EMPLOYED'] == 1)]
    
    if len(case7a) > 0:
        inconsistencies.append(f"ESR indicates employed but EMPLOYED=0: {len(case7a):,} cases")
    if len(case7b) > 0:
        inconsistencies.append(f"ESR indicates unemployed but EMPLOYED=1: {len(case7b):,} cases")
    
    if inconsistencies:
        print("POTENTIAL INCONSISTENCIES FOUND:")
        for inc in inconsistencies:
            print(f"  - {inc}")
    else:
        print("No major inconsistencies detected.")
    
    # Summary statistics
    total_employed = (df['EMPLOYED'] == 1).sum()
    total_with_occp = (df['OCCP'].notna() & (df['OCCP'] != -999)).sum()
    total_with_wkw = (df['WKW'].notna() & (df['WKW'] != -9)).sum()
    total_with_wkhp = (df['WKHP'].notna() & (df['WKHP'] > 0)).sum()
    
    print(f"\nSUMMARY STATISTICS:")
    print(f"  Total persons: {len(df):,}")
    print(f"  EMPLOYED=1: {total_employed:,} ({(total_employed/len(df)*100):.2f}%)")
    print(f"  Has OCCP: {total_with_occp:,} ({(total_with_occp/len(df)*100):.2f}%)")
    print(f"  Has WKW: {total_with_wkw:,} ({(total_with_wkw/len(df)*100):.2f}%)")
    print(f"  Has WKHP: {total_with_wkhp:,} ({(total_with_wkhp/len(df)*100):.2f}%)")

def main():
    """Main analysis function"""
    
    print("EMPLOYMENT FIELDS COMPARISON: 2015 vs 2023 SYNTHETIC POPULATIONS")
    print("=" * 80)
    
    # Load data
    persons_2015, persons_2023 = load_data()
    
    # Fields to analyze
    fields = ['ESR', 'EMPLOYED', 'OCCP', 'WKW', 'WKHP']
    
    # 1. Individual field distributions
    print("\n" + "="*80)
    print("PART 1: INDIVIDUAL FIELD DISTRIBUTIONS")
    print("="*80)
    
    for field in fields:
        if field in persons_2015.columns and field in persons_2023.columns:
            analyze_field_distributions(persons_2015, persons_2023, field)
        else:
            print(f"\nWARNING: Field {field} not found in one or both datasets")
    
    # 2. Cross-tabulations
    print("\n" + "="*80)
    print("PART 2: CROSS-TABULATIONS")
    print("="*80)
    
    # Key cross-tabulations to analyze
    crosstab_pairs = [
        ('ESR', 'EMPLOYED'),
        ('EMPLOYED', 'OCCP'),
        ('EMPLOYED', 'WKW'),
        ('EMPLOYED', 'WKHP'),
        ('ESR', 'OCCP'),
        ('ESR', 'WKW'),
        ('OCCP', 'WKW'),
        ('OCCP', 'WKHP'),
        ('WKW', 'WKHP')
    ]
    
    for field1, field2 in crosstab_pairs:
        if (field1 in persons_2015.columns and field2 in persons_2015.columns and
            field1 in persons_2023.columns and field2 in persons_2023.columns):
            create_crosstab_comparison(persons_2015, persons_2023, field1, field2)
        else:
            print(f"\nWARNING: Fields {field1} or {field2} not found in one or both datasets")
    
    # 3. Consistency analysis
    print("\n" + "="*80)
    print("PART 3: EMPLOYMENT CONSISTENCY ANALYSIS")
    print("="*80)
    
    analyze_employment_consistency(persons_2015, "2015")
    analyze_employment_consistency(persons_2023, "2023")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("\nSummary saved to: employment_fields_comparison_2015_2023.txt")

if __name__ == "__main__":
    # Redirect output to file as well as console
    import sys
    
    class Tee:
        def __init__(self, *files):
            self.files = files
        def write(self, obj):
            for f in self.files:
                f.write(obj)
                f.flush()
        def flush(self):
            for f in self.files:
                f.flush()
    
    with open('employment_fields_comparison_2015_2023.txt', 'w') as f:
        original_stdout = sys.stdout
        sys.stdout = Tee(sys.stdout, f)
        
        try:
            main()
        finally:
            sys.stdout = original_stdout
