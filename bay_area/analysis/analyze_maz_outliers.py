#!/usr/bin/env python3
"""
Analyze MAZ density data for real outliers and data quality issues
"""

import pandas as pd
import numpy as np
import os

def analyze_maz_outliers():
    """Comprehensive analysis of MAZ density outliers"""
    
    # Read the data from Box location
    input_file = r"C:\Box\Modeling and Surveys\Development\Travel Model Two Conversion\Model Inputs\2023-tm22-dev-test\landuse\maz_data_withDensity.csv"
    
    print("COMPREHENSIVE MAZ DENSITY OUTLIER ANALYSIS")
    print("="*60)
    print(f"Analyzing Box location: {input_file}")
    print()
    
    try:
        # Read the data
        print(f"Reading: {input_file}")
        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        
        # Determine which MAZ column to use
        if 'MAZ_ORIGINAL' in df.columns:
            maz_col = 'MAZ_ORIGINAL'
        elif 'MAZ' in df.columns:
            maz_col = 'MAZ'
        else:
            maz_col = df.columns[0]  # Use first column as fallback
            
        print(f"Using MAZ identifier column: {maz_col}")
        print()
        
        # Basic info
        print("COLUMN COUNT ANALYSIS:")
        print(f"Expected columns: 77")
        print(f"Actual columns: {len(df.columns)}")
        print(f"Column names: {list(df.columns)}")
        print()
        
        # Check for 'inf' values
        print("INFINITE VALUES ANALYSIS:")
        inf_count = 0
        inf_columns = []
        
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64', 'object']:
                inf_mask = df[col].astype(str).str.lower() == 'inf'
                col_inf_count = inf_mask.sum()
                if col_inf_count > 0:
                    inf_count += col_inf_count
                    inf_columns.append((col, col_inf_count))
                    print(f"  {col}: {col_inf_count} 'inf' values")
        
        if inf_count == 0:
            print("  ✅ No 'inf' values found")
        else:
            print(f"  ⚠️  Total 'inf' values: {inf_count}")
        print()
        
        # Check for missing values
        print("MISSING VALUES ANALYSIS:")
        missing_summary = df.isnull().sum()
        missing_cols = missing_summary[missing_summary > 0]
        
        if len(missing_cols) == 0:
            print("  ✅ No missing values found")
        else:
            print("  ⚠️  Missing values by column:")
            for col, count in missing_cols.items():
                pct = (count / len(df)) * 100
                print(f"    {col}: {count} ({pct:.1f}%)")
        print()
        
        # Analyze density fields for extreme outliers
        print("DENSITY OUTLIERS ANALYSIS:")
        density_cols = ['EmpDen', 'RetEmpDen', 'DUDen', 'PopDen', 'PopEmpDenPerMi']
        
        for col in density_cols:
            if col in df.columns:
                # Convert to numeric, handling any string issues
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Basic stats
                mean_val = df[col].mean()
                median_val = df[col].median()
                std_val = df[col].std()
                max_val = df[col].max()
                min_val = df[col].min()
                
                # Find extreme outliers (>3 standard deviations)
                outlier_threshold = mean_val + (3 * std_val)
                outliers = df[df[col] > outlier_threshold]
                
                print(f"  {col}:")
                print(f"    Range: {min_val:.2f} to {max_val:.2f}")
                print(f"    Mean: {mean_val:.2f}, Median: {median_val:.2f}")
                print(f"    Outliers (>3σ): {len(outliers)} MAZs")
                
                if len(outliers) > 0:
                    print(f"    Top 5 outlier MAZs:")
                    top_outliers = outliers.nlargest(5, col)[[maz_col, col, 'CountyName']]
                    for _, row in top_outliers.iterrows():
                        print(f"      MAZ {row[maz_col]}: {row[col]:.2f} ({row['CountyName']})")
                print()
        
        # Check coordinate outliers
        print("COORDINATE OUTLIERS ANALYSIS:")
        coord_cols = ['MAZ_X', 'MAZ_Y']
        
        for col in coord_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                mean_val = df[col].mean()
                std_val = df[col].std()
                outlier_threshold_high = mean_val + (3 * std_val)
                outlier_threshold_low = mean_val - (3 * std_val)
                
                outliers = df[(df[col] > outlier_threshold_high) | (df[col] < outlier_threshold_low)]
                
                print(f"  {col}:")
                print(f"    Range: {df[col].min():.0f} to {df[col].max():.0f}")
                print(f"    Mean: {mean_val:.0f} ± {std_val:.0f}")
                print(f"    Coordinate outliers: {len(outliers)} MAZs")
                
                if len(outliers) > 0:
                    print(f"    Outlier MAZs:")
                    for _, row in outliers.head(10).iterrows():
                        print(f"      MAZ {row[maz_col]}: {row[col]:.0f} ({row['CountyName']})")
                print()
        
        # Check for duplicate MAZs
        print("DUPLICATE MAZ ANALYSIS:")
        dup_original = df[df.duplicated([maz_col], keep=False)]
        dup_sequential = df[df.duplicated(['MAZ'], keep=False)] if 'MAZ' in df.columns else pd.DataFrame()
        
        print(f"  Duplicate {maz_col}: {len(dup_original)} rows")
        if 'MAZ' in df.columns and maz_col != 'MAZ':
            print(f"  Duplicate MAZ (sequential): {len(dup_sequential)} rows")
        
        if len(dup_original) > 0:
            print(f"  Duplicate {maz_col} values:")
            for maz in dup_original[maz_col].unique()[:10]:
                count = len(dup_original[dup_original[maz_col] == maz])
                print(f"    MAZ {maz}: {count} occurrences")
        print()
        
        # Check employment totals vs sum of sectors
        print("EMPLOYMENT CONSISTENCY ANALYSIS:")
        if 'emp_total' in df.columns:
            # Employment sector columns (based on what I saw in the log)
            emp_sectors = ['ag', 'art_rec', 'constr', 'eat', 'ed_high', 'ed_k12', 'ed_oth', 
                          'fire', 'gov', 'health', 'hotel', 'info', 'lease', 'logis', 
                          'man_bio', 'man_lgt', 'man_hvy', 'man_tech', 'natres', 'prof', 
                          'ret_loc', 'ret_reg', 'serv_bus', 'serv_pers', 'serv_soc', 
                          'transp', 'util']
            
            # Calculate sum of sectors
            available_sectors = [col for col in emp_sectors if col in df.columns]
            df['emp_sectors_sum'] = df[available_sectors].sum(axis=1)
            
            # Find mismatches
            df['emp_diff'] = abs(df['emp_total'] - df['emp_sectors_sum'])
            mismatches = df[df['emp_diff'] > 1]  # Allow for rounding
            
            print(f"  Employment total vs sectors mismatch: {len(mismatches)} MAZs")
            if len(mismatches) > 0:
                print("  Top mismatches:")
                top_mismatches = mismatches.nlargest(5, 'emp_diff')[[maz_col, 'emp_total', 'emp_sectors_sum', 'emp_diff']]
                for _, row in top_mismatches.iterrows():
                    print(f"    MAZ {row[maz_col]}: total={row['emp_total']}, sectors={row['emp_sectors_sum']}, diff={row['emp_diff']}")
        print()
        
        # Summary
        print("SUMMARY:")
        print(f"  Total rows: {len(df)}")
        print(f"  Column padding needed: All rows (76→77 columns)")
        print(f"  'inf' values: {inf_count}")
        print(f"  Missing values: {missing_summary.sum()}")
        print(f"  Extreme density outliers: Check individual fields above")
        print(f"  Coordinate outliers: Check X/Y analysis above")
        print(f"  Duplicate MAZs: {len(dup_original)} rows")
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")

if __name__ == '__main__':
    analyze_maz_outliers()
