#!/usr/bin/env python3
"""
Compare employment field distributions between 2015 and 2023 synthetic populations
Analyzes: EMPLOYED, ESR, WKW, WKHP, OCCP
"""

import pandas as pd
import numpy as np
import sys
from io import StringIO
import os

def load_data():
    """Load both 2015 and 2023 synthetic population data"""
    print("Loading synthetic population data...")
    
    # 2015 data - corrected path to hh_persons_model
    df_2015 = pd.read_csv('example_2015_outputs/hh_persons_model/persons.csv')
    df_2015['year'] = 2015
    
    # 2023 data - corrected path
    df_2023 = pd.read_csv('output_2023/populationsim_working_dir/output/persons_2023_tm2.csv')
    df_2023['year'] = 2023
    
    print(f"2015 population: {len(df_2015):,}")
    print(f"2023 population: {len(df_2023):,}")
    
    return df_2015, df_2023

def analyze_field_distributions(df_2015, df_2023):
    """Compare field value distributions between years"""
    print("\n" + "="*60)
    print("FIELD DISTRIBUTION COMPARISON")
    print("="*60)
    
    fields = ['EMPLOYED', 'ESR', 'WKW', 'WKHP', 'OCCP']
    
    for field in fields:
        print(f"\n--- {field} DISTRIBUTION ---")
        
        if field in df_2015.columns and field in df_2023.columns:
            # Get value counts for both years
            dist_2015 = df_2015[field].value_counts().sort_index()
            dist_2023 = df_2023[field].value_counts().sort_index()
            
            # Combine into comparison table
            comparison = pd.DataFrame({
                '2015_count': dist_2015,
                '2023_count': dist_2023
            }).fillna(0).astype(int)
            
            comparison['2015_pct'] = (comparison['2015_count'] / len(df_2015) * 100).round(2)
            comparison['2023_pct'] = (comparison['2023_count'] / len(df_2023) * 100).round(2)
            comparison['pct_change'] = (comparison['2023_pct'] - comparison['2015_pct']).round(2)
            
            print(comparison)
            
            # Highlight major changes
            major_changes = comparison[abs(comparison['pct_change']) > 1.0]
            if not major_changes.empty:
                print(f"\n⚠️  Major changes (>1% shift):")
                for idx, row in major_changes.iterrows():
                    direction = "↑" if row['pct_change'] > 0 else "↓"
                    print(f"   {field}={idx}: {row['pct_change']:+.2f}% {direction}")
        else:
            missing_2015 = field not in df_2015.columns
            missing_2023 = field not in df_2023.columns
            print(f"❌ Field missing: 2015={missing_2015}, 2023={missing_2023}")

def analyze_employment_consistency(df_2015, df_2023):
    """Check employment field consistency within each year"""
    print("\n" + "="*60)
    print("EMPLOYMENT FIELD CONSISTENCY ANALYSIS")
    print("="*60)
    
    for year, df in [('2015', df_2015), ('2023', df_2023)]:
        print(f"\n--- {year} CONSISTENCY ---")
        
        # Check required fields exist
        req_fields = ['EMPLOYED', 'ESR', 'WKW', 'WKHP', 'OCCP']
        missing = [f for f in req_fields if f not in df.columns]
        if missing:
            print(f"❌ Missing fields: {missing}")
            continue
            
        total = len(df)
        
        # EMPLOYED vs ESR consistency
        employed_1 = len(df[df['EMPLOYED'] == 1])
        esr_employed = len(df[df['ESR'].isin([1, 2, 4, 5])])  # ESR employed categories
        print(f"EMPLOYED=1: {employed_1:,} ({employed_1/total*100:.1f}%)")
        print(f"ESR employed: {esr_employed:,} ({esr_employed/total*100:.1f}%)")
        if employed_1 != esr_employed:
            diff = abs(employed_1 - esr_employed)
            print(f"⚠️  EMPLOYED/ESR mismatch: {diff:,} records ({diff/total*100:.2f}%)")
        
        # Employed people with missing occupation
        employed_no_occp = len(df[(df['EMPLOYED'] == 1) & (df['OCCP'].isin([0, 999]))])
        print(f"Employed without occupation: {employed_no_occp:,} ({employed_no_occp/total*100:.2f}%)")
        
        # People with work history (WKW) but not currently employed
        worked_not_employed = len(df[(df['WKW'].between(1, 6)) & (df['EMPLOYED'] == 0)])
        print(f"Worked last year, not employed now: {worked_not_employed:,} ({worked_not_employed/total*100:.2f}%)")
        
        # Children (AGEP < 16) with employment fields
        if 'AGEP' in df.columns:
            children = df[df['AGEP'] < 16]
            child_employed = len(children[children['EMPLOYED'] == 1])
            child_wkw = len(children[children['WKW'].between(1, 6)])
            child_occp = len(children[~children['OCCP'].isin([0, 999])])
            print(f"Children (<16) employed: {child_employed:,}")
            print(f"Children (<16) with WKW: {child_wkw:,}")
            print(f"Children (<16) with occupation: {child_occp:,}")

def analyze_wkw_distributions(df_2015, df_2023):
    """Deep dive into WKW (weeks worked) distributions"""
    print("\n" + "="*60)
    print("WKW (WEEKS WORKED) DETAILED ANALYSIS")
    print("="*60)
    
    wkw_labels = {
        1: "50-52 weeks (full year)",
        2: "48-49 weeks", 
        3: "40-47 weeks",
        4: "27-39 weeks",
        5: "14-26 weeks", 
        6: "1-13 weeks (minimal)",
        0: "Did not work",
        -9: "Not applicable"
    }
    
    for year, df in [('2015', df_2015), ('2023', df_2023)]:
        if 'WKW' not in df.columns:
            print(f"❌ {year}: WKW field missing")
            continue
            
        print(f"\n--- {year} WKW DISTRIBUTION ---")
        wkw_dist = df['WKW'].value_counts().sort_index()
        
        for value, count in wkw_dist.items():
            pct = count / len(df) * 100
            label = wkw_labels.get(value, f"Unknown ({value})")
            print(f"WKW {value}: {count:6,} ({pct:5.1f}%) - {label}")

def analyze_occp_categories(df_2015, df_2023):
    """Analyze OCCP occupation category distributions"""
    print("\n" + "="*60)
    print("OCCP (OCCUPATION) CATEGORY ANALYSIS")
    print("="*60)
    
    occp_labels = {
        0: "Not applicable",
        1: "Management/Business/Science/Arts",
        2: "Professional", 
        3: "Service",
        4: "Sales/Office",
        5: "Manual/Military",
        6: "Unknown category",
        999: "N/A (Census code)"
    }
    
    for year, df in [('2015', df_2015), ('2023', df_2023)]:
        if 'OCCP' not in df.columns:
            print(f"❌ {year}: OCCP field missing")
            continue
            
        print(f"\n--- {year} OCCP DISTRIBUTION ---")
        occp_dist = df['OCCP'].value_counts().sort_index()
        
        for value, count in occp_dist.items():
            pct = count / len(df) * 100
            label = occp_labels.get(value, f"Detailed code ({value})")
            print(f"OCCP {value}: {count:6,} ({pct:5.1f}%) - {label}")
            
        # Check for detailed OCCP codes (10-9830)
        detailed_codes = df[(df['OCCP'] >= 10) & (df['OCCP'] <= 9830) & (~df['OCCP'].isin([999]))]['OCCP'].unique()
        if len(detailed_codes) > 0:
            print(f"📊 Found {len(detailed_codes)} detailed OCCP codes (sample: {sorted(detailed_codes)[:5]}...)")
        else:
            print("📊 No detailed OCCP codes found - using categorical mapping")

def analyze_employment_crosstabs(df_2015, df_2023):
    """Analyze cross-tabulations between employment fields"""
    print("\n" + "="*60)
    print("EMPLOYMENT FIELD CROSS-TABULATIONS")
    print("="*60)
    
    # Key cross-tabs to analyze
    crosstabs = [
        ('EMPLOYED', 'ESR', 'Employment Status vs Employment Status Recode'),
        ('EMPLOYED', 'OCCP', 'Employment Status vs Occupation'),
        ('ESR', 'WKW', 'Employment Status vs Weeks Worked'),
        ('ESR', 'WKHP', 'Employment Status vs Hours Worked'),
        ('OCCP', 'WKW', 'Occupation vs Weeks Worked'),
    ]
    
    for field1, field2, title in crosstabs:
        print(f"\n--- {title} ---")
        
        for year, df in [('2015', df_2015), ('2023', df_2023)]:
            if field1 not in df.columns or field2 not in df.columns:
                print(f"❌ {year}: Missing fields {field1} or {field2}")
                continue
                
            print(f"\n{year} Cross-tab: {field1} vs {field2}")
            crosstab = pd.crosstab(df[field1], df[field2], margins=True)
            print(crosstab)
            
            # Calculate percentages for employed/not employed vs occupation
            if field1 == 'EMPLOYED' and field2 == 'OCCP':
                print(f"\n{year} Employment vs OCCP (percentages):")
                pct_crosstab = pd.crosstab(df[field1], df[field2], normalize='index') * 100
                print(pct_crosstab.round(1))
                
                # Key metrics
                employed = df[df['EMPLOYED'] == 1]
                if len(employed) > 0:
                    occp_0_pct = (employed['OCCP'] == 0).mean() * 100
                    occp_999_pct = (employed['OCCP'] == 999).mean() * 100
                    print(f"📊 {year} Employed with OCCP=0: {occp_0_pct:.1f}%")
                    print(f"📊 {year} Employed with OCCP=999: {occp_999_pct:.1f}%")

def main():
    """Run comprehensive employment field comparison"""
    # Set up output file
    output_dir = 'output_2023/populationsim_working_dir/output/'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'employment_fields_comparison_2015_2023.txt')
    
    # Capture all print output
    original_stdout = sys.stdout
    captured_output = StringIO()
    
    try:
        # Redirect print to capture output
        sys.stdout = captured_output
        
        print("EMPLOYMENT FIELD COMPARISON: 2015 vs 2023")
        print("="*60)
        
        # Load data
        df_2015, df_2023 = load_data()
        
        # Run analyses
        analyze_field_distributions(df_2015, df_2023)
        analyze_employment_consistency(df_2015, df_2023)
        analyze_wkw_distributions(df_2015, df_2023)
        analyze_occp_categories(df_2015, df_2023)
        analyze_employment_crosstabs(df_2015, df_2023)
        
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        
        # Get captured output
        output_content = captured_output.getvalue()
        
        # Restore stdout and print to console
        sys.stdout = original_stdout
        print(f"Analysis complete! Results saved to: {output_file}")
        print(f"Output directory: {os.path.abspath(output_dir)}")
        
        # Also show summary to console
        print("\n--- QUICK SUMMARY ---")
        print(f"2015 population: {len(df_2015):,}")
        print(f"2023 population: {len(df_2023):,}")
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Generated on: {pd.Timestamp.now()}\n")
            f.write(f"Analysis: Employment Field Comparison 2015 vs 2023\n")
            f.write("="*60 + "\n\n")
            f.write(output_content)
        
        print(f"✅ Full analysis saved to: {output_file}")
        
    except FileNotFoundError as e:
        sys.stdout = original_stdout
        print(f"❌ Error loading data: {e}")
        print("Make sure both synthetic_persons.csv files exist:")
        print("  - example_2015_outputs/hh_persons_model/persons.csv")
        print("  - output_2023/populationsim_working_dir/output/persons_2023_tm2.csv")
    except Exception as e:
        sys.stdout = original_stdout
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
