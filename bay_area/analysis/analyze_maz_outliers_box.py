#!/usr/bin/env python3
"""
Analyze MAZ density data for real outliers and data quality issues
This version analyzes the Box location files
"""

import pandas as pd
import numpy as np
import os

def analyze_maz_outliers():
    """Comprehensive analysis of MAZ density outliers"""
    
    # Read the data from Box location
    box_dir = r"C:\Box\Modeling and Surveys\Development\Travel Model Two Conversion\Model Inputs\2023-tm22-dev-test\landuse"
    
    # Try both possible files (prioritize UPDATED version)
    possible_files = [
        os.path.join(box_dir, "maz_data_withDensity_UPDATED.csv"),
        os.path.join(box_dir, "maz_data_withDensity.csv"),
        os.path.join(box_dir, "maz_data_UPDATED.csv"),
        os.path.join(box_dir, "maz_data.csv")
    ]
    
    print("COMPREHENSIVE MAZ DENSITY OUTLIER ANALYSIS - BOX LOCATION")
    print("="*70)
    
    # Find which file exists
    input_file = None
    for file_path in possible_files:
        if os.path.exists(file_path):
            input_file = file_path
            break
    
    if input_file is None:
        print("❌ No MAZ data files found in Box location!")
        print("Looked for:")
        for file_path in possible_files:
            print(f"  - {file_path}")
        return
    
    try:
        # Read the data
        print(f"Reading: {input_file}")
        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        print()
        
        # Basic info
        print("COLUMN COUNT ANALYSIS:")
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
        
        # Analyze density fields for extreme outliers (if they exist)
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
                    id_col = 'MAZ_ORIGINAL' if 'MAZ_ORIGINAL' in df.columns else 'MAZ'
                    county_col = 'CountyName' if 'CountyName' in df.columns else 'CountyID'
                    
                    top_outliers = outliers.nlargest(5, col)[[id_col, col, county_col]]
                    for _, row in top_outliers.iterrows():
                        print(f"      MAZ {row[id_col]}: {row[col]:.2f} ({row[county_col]})")
                print()
            else:
                print(f"  {col}: Not found in dataset")
        
        # Check coordinate outliers (if they exist)
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
                    id_col = 'MAZ_ORIGINAL' if 'MAZ_ORIGINAL' in df.columns else 'MAZ'
                    county_col = 'CountyName' if 'CountyName' in df.columns else 'CountyID'
                    
                    for _, row in outliers.head(10).iterrows():
                        print(f"      MAZ {row[id_col]}: {row[col]:.0f} ({row[county_col]})")
                print()
            else:
                print(f"  {col}: Not found in dataset")
        
        # Check for duplicate MAZs
        print("DUPLICATE MAZ ANALYSIS:")
        id_col = 'MAZ_ORIGINAL' if 'MAZ_ORIGINAL' in df.columns else 'MAZ'
        seq_col = 'MAZ' if 'MAZ' in df.columns else None
        
        dup_original = df[df.duplicated([id_col], keep=False)]
        
        print(f"  Duplicate {id_col}: {len(dup_original)} rows")
        
        if seq_col:
            dup_sequential = df[df.duplicated([seq_col], keep=False)]
            print(f"  Duplicate {seq_col}: {len(dup_sequential)} rows")
        
        if len(dup_original) > 0:
            print(f"  Duplicate {id_col} values:")
            for maz in dup_original[id_col].unique()[:10]:
                count = len(dup_original[dup_original[id_col] == maz])
                print(f"    MAZ {maz}: {count} occurrences")
        print()
        
        # Check employment totals vs sum of sectors (if employment data exists)
        print("EMPLOYMENT CONSISTENCY ANALYSIS:")
        if 'emp_total' in df.columns:
            # Employment sector columns (common ones)
            emp_sectors = ['ag', 'art_rec', 'constr', 'eat', 'ed_high', 'ed_k12', 'ed_oth', 
                          'fire', 'gov', 'health', 'hotel', 'info', 'lease', 'logis', 
                          'man_bio', 'man_lgt', 'man_hvy', 'man_tech', 'natres', 'prof', 
                          'ret_loc', 'ret_reg', 'serv_bus', 'serv_pers', 'serv_soc', 
                          'transp', 'util']
            
            # Calculate sum of sectors
            available_sectors = [col for col in emp_sectors if col in df.columns]
            if available_sectors:
                df['emp_sectors_sum'] = df[available_sectors].sum(axis=1)
                
                # Find mismatches
                df['emp_diff'] = abs(df['emp_total'] - df['emp_sectors_sum'])
                mismatches = df[df['emp_diff'] > 1]  # Allow for rounding
                
                print(f"  Available employment sectors: {len(available_sectors)}")
                print(f"  Employment total vs sectors mismatch: {len(mismatches)} MAZs")
                if len(mismatches) > 0:
                    print("  Top mismatches:")
                    id_col = 'MAZ_ORIGINAL' if 'MAZ_ORIGINAL' in df.columns else 'MAZ'
                    top_mismatches = mismatches.nlargest(5, 'emp_diff')[[id_col, 'emp_total', 'emp_sectors_sum', 'emp_diff']]
                    for _, row in top_mismatches.iterrows():
                        print(f"    MAZ {row[id_col]}: total={row['emp_total']}, sectors={row['emp_sectors_sum']}, diff={row['emp_diff']}")
            else:
                print("  No employment sector columns found")
        else:
            print("  No emp_total column found")
        print()
        
        # Summary
        print("SUMMARY:")
        print(f"  File analyzed: {os.path.basename(input_file)}")
        print(f"  Total rows: {len(df)}")
        print(f"  Total columns: {len(df.columns)}")
        print(f"  'inf' values: {inf_count}")
        print(f"  Missing values: {missing_summary.sum()}")
        
        # Count density columns present
        density_present = [col for col in density_cols if col in df.columns]
        print(f"  Density columns present: {len(density_present)}/{len(density_cols)}")
        
        # Count coordinate columns present  
        coord_present = [col for col in coord_cols if col in df.columns]
        print(f"  Coordinate columns present: {len(coord_present)}/{len(coord_cols)}")
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    analyze_maz_outliers()
