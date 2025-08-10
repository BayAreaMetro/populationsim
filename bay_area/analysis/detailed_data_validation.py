#!/usr/bin/env python3
"""
Comprehensive Data Validation for PopulationSim with Detailed Distributions
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import warnings
warnings.filterwarnings('ignore')

def main():
    """Main validation function"""
    output_file = Path.cwd() / "data_validation_detailed_report.txt"
    
    with open(output_file, 'w') as f:
        class TeeOutput:
            def __init__(self, *files):
                self.files = files
            def write(self, text):
                for file in self.files:
                    file.write(text)
                    file.flush()
            def flush(self):
                for file in self.files:
                    file.flush()
        
        original_stdout = sys.stdout
        sys.stdout = TeeOutput(sys.stdout, f)
        
        try:
            print("COMPREHENSIVE POPULATIONSIM DATA VALIDATION - DETAILED REPORT")
            print("=" * 80)
            print(f"Report saved to: {output_file}")
            print("=" * 80)
            
            # Load data
            base_dir = Path.cwd()
            hh_gq_data_dir = base_dir / "hh_gq" / "data"
            hh_gq_configs_dir = base_dir / "hh_gq" / "configs_TM2"
            
            print("Loading data files...")
            households_df = pd.read_csv(hh_gq_data_dir / "seed_households.csv")
            persons_df = pd.read_csv(hh_gq_data_dir / "seed_persons.csv")
            maz_marginals_df = pd.read_csv(hh_gq_configs_dir / "maz_marginals_hhgq.csv")
            taz_marginals_df = pd.read_csv(hh_gq_configs_dir / "taz_marginals_hhgq.csv")
            county_marginals_df = pd.read_csv(hh_gq_configs_dir / "county_marginals.csv")
            geo_crosswalk_df = pd.read_csv(hh_gq_data_dir / "geo_cross_walk_tm2.csv")
            
            # Analyze each dataset with detailed distributions
            analyze_dataset_detailed(households_df, "SEED HOUSEHOLDS")
            analyze_dataset_detailed(persons_df, "SEED PERSONS")
            analyze_dataset_detailed(maz_marginals_df, "MAZ MARGINALS")
            analyze_dataset_detailed(taz_marginals_df, "TAZ MARGINALS")
            analyze_dataset_detailed(county_marginals_df, "COUNTY MARGINALS")
            analyze_dataset_detailed(geo_crosswalk_df, "GEOGRAPHIC CROSSWALK")
            
            # Cross-dataset analysis
            print("\\n" + "="*80)
            print("CROSS-DATASET ANALYSIS")
            print("="*80)
            
            # Geographic ID consistency
            analyze_geographic_consistency(households_df, persons_df, geo_crosswalk_df, maz_marginals_df, taz_marginals_df)
            
            # Control vs seed population comparison
            analyze_control_seed_comparison(households_df, persons_df, maz_marginals_df, taz_marginals_df)
            
            print("\\nDetailed validation complete!")
            
        except Exception as e:
            print(f"\\n❌ Error during validation: {e}")
            import traceback
            traceback.print_exc()
        finally:
            sys.stdout = original_stdout

def analyze_dataset_detailed(df, name):
    """Analyze a dataset with detailed distributions"""
    print(f"\\n{'='*80}")
    print(f"DETAILED ANALYSIS: {name}")
    print(f"{'='*80}")
    
    print(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    
    # Column types
    print(f"\\nColumn Types:")
    for col, dtype in df.dtypes.items():
        print(f"  {col}: {dtype}")
    
    # Missing values analysis
    missing = df.isnull().sum()
    if missing.sum() > 0:
        print(f"\\nMissing Values:")
        for col, count in missing[missing > 0].items():
            pct = count / len(df) * 100
            print(f"  {col}: {count:,} ({pct:.1f}%)")
    else:
        print(f"\\nMissing Values: None")
    
    # Analyze numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        print(f"\\nNUMERIC COLUMNS DETAILED ANALYSIS:")
        for col in numeric_cols:
            analyze_numeric_column_detailed(df[col], col)
    
    # Analyze categorical/text columns
    categorical_cols = df.select_dtypes(include=['object']).columns
    if len(categorical_cols) > 0:
        print(f"\\nCATEGORICAL COLUMNS DETAILED ANALYSIS:")
        for col in categorical_cols:
            analyze_categorical_column_detailed(df[col], col)

def analyze_numeric_column_detailed(series, col_name):
    """Detailed analysis of a numeric column"""
    print(f"\\n  {col_name}:")
    print(f"    Count: {series.count():,}")
    print(f"    Missing: {series.isnull().sum():,}")
    
    if series.count() == 0:
        print(f"    ⚠️  No non-null values")
        return
    
    # Basic statistics
    print(f"    Mean: {series.mean():.3f}")
    print(f"    Std: {series.std():.3f}")
    print(f"    Min: {series.min()}")
    print(f"    Max: {series.max()}")
    
    # Percentiles
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    print(f"    Percentiles:")
    for p in percentiles:
        val = series.quantile(p/100)
        print(f"      {p:2d}%: {val:10.3f}")
    
    # Check for infinite values
    inf_count = np.isinf(series).sum()
    if inf_count > 0:
        print(f"    ⚠️  Infinite values: {inf_count:,}")
    
    # Value distribution
    unique_count = series.nunique()
    print(f"    Unique values: {unique_count:,}")
    
    if unique_count <= 50:
        print(f"    Value Distribution (all {unique_count} values):")
        value_counts = series.value_counts().sort_index()
        for val, count in value_counts.items():
            pct = count / len(series) * 100
            print(f"      {val:10}: {count:8,} ({pct:5.1f}%)")
    else:
        # Histogram for continuous variables
        print(f"    Distribution (histogram - 10 bins):")
        try:
            hist, bin_edges = np.histogram(series.dropna(), bins=10)
            for i in range(len(hist)):
                bin_start = bin_edges[i]
                bin_end = bin_edges[i+1]
                count = hist[i]
                pct = count / series.count() * 100
                print(f"      [{bin_start:8.1f}, {bin_end:8.1f}): {count:8,} ({pct:5.1f}%)")
        except:
            print(f"      Could not create histogram")
        
        # Top values
        print(f"    Top 10 most frequent values:")
        top_values = series.value_counts().head(10)
        for val, count in top_values.items():
            pct = count / len(series) * 100
            print(f"      {val:10}: {count:8,} ({pct:5.1f}%)")
    
    # Outlier detection
    if series.std() > 0:
        outlier_threshold = 3 * series.std()
        mean_val = series.mean()
        outliers = series[(series < mean_val - outlier_threshold) | (series > mean_val + outlier_threshold)]
        if len(outliers) > 0:
            print(f"    ⚠️  Potential outliers (>3σ): {len(outliers):,} ({len(outliers)/series.count()*100:.1f}%)")
            print(f"      Range: {outliers.min()} to {outliers.max()}")
    
    # Check for negative values (might be problematic for certain fields)
    if (series < 0).any():
        neg_count = (series < 0).sum()
        print(f"    📊 Negative values: {neg_count:,}")
    
    # Check for zero values
    zero_count = (series == 0).sum()
    if zero_count > 0:
        print(f"    📊 Zero values: {zero_count:,} ({zero_count/len(series)*100:.1f}%)")

def analyze_categorical_column_detailed(series, col_name):
    """Detailed analysis of a categorical column"""
    print(f"\\n  {col_name}:")
    total_count = len(series)
    unique_count = series.nunique()
    missing_count = series.isnull().sum()
    
    print(f"    Total values: {total_count:,}")
    print(f"    Unique values: {unique_count:,}")
    print(f"    Missing values: {missing_count:,} ({missing_count/total_count*100:.1f}%)")
    
    if unique_count == 0:
        print(f"    ⚠️  No non-null values")
        return
    
    # Value distribution
    value_counts = series.value_counts(dropna=False)
    print(f"    Value Distribution:")
    
    if unique_count <= 30:
        # Show all values for small sets
        for val, count in value_counts.items():
            pct = count / total_count * 100
            val_str = str(val) if pd.notna(val) else "NULL/NaN"
            print(f"      '{val_str}': {count:,} ({pct:.1f}%)")
    else:
        # Show top 20 for large sets
        print(f"    Top 20 values:")
        for val, count in value_counts.head(20).items():
            pct = count / total_count * 100
            val_str = str(val) if pd.notna(val) else "NULL/NaN"
            print(f"      '{val_str}': {count:,} ({pct:.1f}%)")
        print(f"      ... and {unique_count - 20} more unique values")
    
    # String length analysis (if text)
    if series.dtype == 'object' and not series.isnull().all():
        str_lengths = series.astype(str).str.len()
        print(f"    String Length Analysis:")
        print(f"      Min length: {str_lengths.min()}")
        print(f"      Max length: {str_lengths.max()}")
        print(f"      Mean length: {str_lengths.mean():.1f}")
        
        if str_lengths.max() > 100:
            print(f"      ⚠️  Very long strings detected")
        
        # Check for numeric-like strings
        non_null_series = series.dropna()
        if len(non_null_series) > 0:
            numeric_like = non_null_series.astype(str).str.match(r'^-?\\d+\\.?\\d*$').sum()
            if numeric_like > 0:
                pct_numeric = numeric_like / len(non_null_series) * 100
                print(f"      📊 Numeric-like strings: {numeric_like:,} ({pct_numeric:.1f}%)")

def analyze_geographic_consistency(households_df, persons_df, geo_crosswalk_df, maz_marginals_df, taz_marginals_df):
    """Analyze consistency of geographic IDs across datasets"""
    print(f"\\nGEOGRAPHIC ID CONSISTENCY ANALYSIS:")
    
    # Get geographic columns from each dataset
    datasets = {
        'Households': households_df,
        'Persons': persons_df,
        'Geo Crosswalk': geo_crosswalk_df,
        'MAZ Marginals': maz_marginals_df,
        'TAZ Marginals': taz_marginals_df
    }
    
    geo_fields = ['MAZ', 'TAZ', 'COUNTY', 'PUMA']
    
    for geo_field in geo_fields:
        print(f"\\n  {geo_field} Analysis:")
        geo_sets = {}
        
        for dataset_name, df in datasets.items():
            geo_cols = [col for col in df.columns if geo_field in col.upper()]
            if geo_cols:
                col = geo_cols[0]  # Take first matching column
                unique_vals = set(df[col].dropna().unique())
                geo_sets[dataset_name] = unique_vals
                print(f"    {dataset_name} ({col}): {len(unique_vals):,} unique values")
        
        # Find overlaps and differences
        if len(geo_sets) > 1:
            all_values = set()
            for vals in geo_sets.values():
                all_values.update(vals)
            
            print(f"    Total unique {geo_field}s across all datasets: {len(all_values):,}")
            
            # Check for values in one dataset but not others
            for dataset_name, vals in geo_sets.items():
                for other_name, other_vals in geo_sets.items():
                    if dataset_name != other_name:
                        missing_in_other = vals - other_vals
                        if missing_in_other:
                            print(f"    ⚠️  {len(missing_in_other):,} {geo_field}s in {dataset_name} but not in {other_name}")

def analyze_control_seed_comparison(households_df, persons_df, maz_marginals_df, taz_marginals_df):
    """Compare control totals with seed population characteristics"""
    print(f"\\nCONTROL vs SEED POPULATION COMPARISON:")
    
    # Household size comparison
    if 'hhsize' in households_df.columns:
        print(f"\\n  Household Size Distribution (Seed Population):")
        hh_size_dist = households_df['hhsize'].value_counts().sort_index()
        for size, count in hh_size_dist.items():
            pct = count / len(households_df) * 100
            print(f"    Size {size}: {count:,} households ({pct:.1f}%)")
        
        # Look for corresponding controls
        hh_size_controls = [col for col in maz_marginals_df.columns if 'hh_size' in col.lower() or 'hhsize' in col.lower()]
        if hh_size_controls:
            print(f"\\n  Household Size Controls Found:")
            for col in hh_size_controls:
                total = maz_marginals_df[col].sum()
                print(f"    {col}: {total:,} total")
    
    # Age distribution comparison
    age_cols = [col for col in persons_df.columns if 'age' in col.lower()]
    if age_cols:
        age_col = age_cols[0]
        print(f"\\n  Age Distribution (Seed Population - {age_col}):")
        
        # Create age groups
        age_bins = [0, 18, 25, 35, 45, 55, 65, 75, 85, 120]
        age_labels = ['0-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65-74', '75-84', '85+']
        persons_df['age_group'] = pd.cut(persons_df[age_col], bins=age_bins, labels=age_labels, right=False)
        age_dist = persons_df['age_group'].value_counts().sort_index()
        
        for group, count in age_dist.items():
            pct = count / len(persons_df) * 100
            print(f"    {group}: {count:,} persons ({pct:.1f}%)")
        
        # Look for age-related controls
        age_controls = [col for col in maz_marginals_df.columns if 'age' in col.lower()]
        if age_controls:
            print(f"\\n  Age-related Controls Found:")
            for col in age_controls[:10]:  # Show first 10
                total = maz_marginals_df[col].sum()
                print(f"    {col}: {total:,} total")

if __name__ == "__main__":
    main()
