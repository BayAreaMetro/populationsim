#!/usr/bin/env python3
"""
Comprehensive Data Validation for PopulationSim
Analyzes control files, seed population, and data quality issues
to identify sources of NaN values and data inconsistencies.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import warnings
warnings.filterwarnings('ignore')

def analyze_dataframe_summary(df, name):
    """Generate comprehensive summary statistics for a dataframe"""
    print(f"\n{'='*60}")
    print(f"DATAFRAME ANALYSIS: {name}")
    print(f"{'='*60}")
    
    print(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    
    # Basic info
    print(f"\nColumn Data Types:")
    for col, dtype in df.dtypes.items():
        print(f"  {col}: {dtype}")
    
    # Missing values
    missing = df.isnull().sum()
    if missing.sum() > 0:
        print(f"\nMissing Values:")
        for col, count in missing[missing > 0].items():
            pct = count / len(df) * 100
            print(f"  {col}: {count:,} ({pct:.1f}%)")
    else:
        print(f"\nMissing Values: None")
    
    # Infinite values
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    inf_summary = {}
    for col in numeric_cols:
        inf_count = np.isinf(df[col]).sum()
        if inf_count > 0:
            inf_summary[col] = inf_count
    
    if inf_summary:
        print(f"\nInfinite Values:")
        for col, count in inf_summary.items():
            pct = count / len(df) * 100
            print(f"  {col}: {count:,} ({pct:.1f}%)")
    else:
        print(f"\nInfinite Values: None")
    
    # Numeric summary
    if len(numeric_cols) > 0:
        print(f"\nNumeric Summary:")
        summary = df[numeric_cols].describe()
        print(summary.round(2))
        
        # Detailed distribution analysis for each numeric column
        print(f"\nDetailed Numeric Distributions:")
        for col in numeric_cols[:10]:  # Limit to first 10 numeric columns
            print(f"\n  {col}:")
            series = df[col]
            
            # Basic stats
            print(f"    Count: {series.count():,}")
            print(f"    Mean: {series.mean():.3f}")
            print(f"    Std: {series.std():.3f}")
            print(f"    Min: {series.min()}")
            print(f"    Max: {series.max()}")
            
            # Percentiles
            percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
            print(f"    Percentiles:")
            for p in percentiles:
                val = series.quantile(p/100)
                print(f"      {p}%: {val:.3f}")
            
            # Value distribution (for discrete values)
            unique_count = series.nunique()
            if unique_count <= 50:
                print(f"    Value Distribution ({unique_count} unique values):")
                value_counts = series.value_counts().sort_index().head(20)
                for val, count in value_counts.items():
                    pct = count / len(series) * 100
                    print(f"      {val}: {count:,} ({pct:.1f}%)")
                if len(value_counts) < series.nunique():
                    print(f"      ... and {series.nunique() - len(value_counts)} more values")
            else:
                # For continuous variables, show histogram-like bins
                print(f"    Distribution (10 bins):")
                try:
                    hist, bin_edges = np.histogram(series.dropna(), bins=10)
                    for i in range(len(hist)):
                        bin_start = bin_edges[i]
                        bin_end = bin_edges[i+1]
                        count = hist[i]
                        pct = count / len(series) * 100
                        print(f"      [{bin_start:.1f}, {bin_end:.1f}): {count:,} ({pct:.1f}%)")
                except:
                    print(f"      Could not create histogram")
            
            # Check for outliers (values beyond 3 standard deviations)
            if series.std() > 0:
                outlier_threshold = 3 * series.std()
                mean_val = series.mean()
                outliers = series[(series < mean_val - outlier_threshold) | (series > mean_val + outlier_threshold)]
                if len(outliers) > 0:
                    print(f"    ⚠️  Potential outliers (>3σ): {len(outliers):,} ({len(outliers)/len(series)*100:.1f}%)")
                    if len(outliers) <= 10:
                        print(f"      Values: {sorted(outliers.unique())}")
                    else:
                        print(f"      Range: {outliers.min()} to {outliers.max()}")
        
        if len(numeric_cols) > 10:
            print(f"\n  ... and {len(numeric_cols) - 10} more numeric columns")
    
    # Value counts for categorical/ID columns
    categorical_cols = df.select_dtypes(include=['object']).columns
    print(f"\nCategorical/Text Column Analysis:")
    for col in categorical_cols:
        unique_count = df[col].nunique()
        total_count = len(df[col])
        missing_count = df[col].isnull().sum()
        
        print(f"\n  {col}:")
        print(f"    Total values: {total_count:,}")
        print(f"    Unique values: {unique_count:,}")
        print(f"    Missing values: {missing_count:,}")
        print(f"    Data type: {df[col].dtype}")
        
        if unique_count > 0:
            # Show value distribution
            if unique_count <= 50:
                print(f"    Complete Distribution:")
                value_counts = df[col].value_counts(dropna=False).head(20)
                for val, count in value_counts.items():
                    pct = count / total_count * 100
                    val_str = str(val) if pd.notna(val) else "NaN"
                    print(f"      '{val_str}': {count:,} ({pct:.1f}%)")
                if len(value_counts) < unique_count:
                    print(f"      ... and {unique_count - len(value_counts)} more unique values")
            else:
                print(f"    Top 20 Values:")
                value_counts = df[col].value_counts(dropna=False).head(20)
                for val, count in value_counts.items():
                    pct = count / total_count * 100
                    val_str = str(val) if pd.notna(val) else "NaN"
                    print(f"      '{val_str}': {count:,} ({pct:.1f}%)")
                print(f"      ... and {unique_count - len(value_counts)} more unique values")
            
            # Sample values
            sample_vals = df[col].dropna().unique()[:10]
            print(f"    Sample values: {sample_vals}")
            
            # Check for potential issues
            if missing_count > 0:
                pct_missing = missing_count / total_count * 100
                print(f"    ⚠️  Missing data: {missing_count:,} ({pct_missing:.1f}%)")
            
            # Check for very long strings (potential data quality issues)
            if df[col].dtype == 'object':
                str_lengths = df[col].astype(str).str.len()
                max_length = str_lengths.max()
                mean_length = str_lengths.mean()
                if max_length > 100:
                    print(f"    ⚠️  Very long strings detected - max length: {max_length}, mean: {mean_length:.1f}")
                
                # Check for numeric-like strings
                numeric_like = df[col].dropna().astype(str).str.match(r'^-?\d+\.?\d*$').sum()
                if numeric_like > 0:
                    pct_numeric = numeric_like / (total_count - missing_count) * 100
                    print(f"    📊 Numeric-like strings: {numeric_like:,} ({pct_numeric:.1f}%)")
    
    if len(categorical_cols) == 0:
        print(f"\nCategorical/Text Column Analysis: No categorical columns found")

def analyze_geographic_ids(df, name):
    """Analyze geographic ID fields for completeness and validity"""
    print(f"\n{'='*60}")
    print(f"GEOGRAPHIC ID ANALYSIS: {name}")
    print(f"{'='*60}")
    
    # Common geographic columns
    geo_cols = []
    for col in df.columns:
        if any(geo_id in col.upper() for geo_id in ['MAZ', 'TAZ', 'COUNTY', 'PUMA', 'TRACT', 'BLOCK']):
            geo_cols.append(col)
    
    if not geo_cols:
        print("No geographic ID columns detected")
        return
    
    for col in geo_cols:
        print(f"\n{col}:")
        print(f"  Data type: {df[col].dtype}")
        print(f"  Total values: {len(df):,}")
        print(f"  Unique values: {df[col].nunique():,}")
        print(f"  Missing values: {df[col].isnull().sum():,}")
        
        if df[col].dtype in ['int64', 'float64']:
            print(f"  Min: {df[col].min()}")
            print(f"  Max: {df[col].max()}")
            print(f"  Mean: {df[col].mean():.2f}")
            print(f"  Std: {df[col].std():.2f}")
            
            # Check for negative or zero values (usually invalid for IDs)
            neg_count = (df[col] <= 0).sum()
            if neg_count > 0:
                print(f"  ⚠️  Negative/zero values: {neg_count:,}")
            
            # Check for gaps in ID sequences
            unique_vals = sorted(df[col].dropna().unique())
            if len(unique_vals) > 1:
                gaps = []
                for i in range(1, len(unique_vals)):
                    if unique_vals[i] - unique_vals[i-1] > 1:
                        gaps.append((unique_vals[i-1], unique_vals[i]))
                if gaps:
                    print(f"  📊 ID sequence gaps: {len(gaps)} gaps found")
                    if len(gaps) <= 5:
                        for start, end in gaps:
                            print(f"      Gap: {start} -> {end}")
                    else:
                        print(f"      First gap: {gaps[0][0]} -> {gaps[0][1]}")
                        print(f"      Last gap: {gaps[-1][0]} -> {gaps[-1][1]}")
            
            # Distribution analysis for geographic IDs
            print(f"  Distribution Analysis:")
            if df[col].nunique() <= 20:
                # Show all values for small sets
                value_counts = df[col].value_counts().sort_index()
                for val, count in value_counts.items():
                    pct = count / len(df) * 100
                    print(f"    {val}: {count:,} ({pct:.1f}%)")
            else:
                # Show summary statistics for large sets
                value_counts = df[col].value_counts()
                print(f"    Most common: {value_counts.index[0]} ({value_counts.iloc[0]:,} records)")
                print(f"    Least common: {value_counts.index[-1]} ({value_counts.iloc[-1]:,} records)")
                print(f"    Median frequency: {value_counts.median():.0f} records per ID")
                
                # Check for highly unbalanced distributions
                max_count = value_counts.max()
                min_count = value_counts.min()
                ratio = max_count / min_count if min_count > 0 else float('inf')
                if ratio > 100:
                    print(f"    ⚠️  Highly unbalanced: {ratio:.1f}x difference between max and min")
        
        # Show sample values
        sample_vals = df[col].dropna().unique()[:10]
        print(f"  Sample values: {list(sample_vals)}")
        
        # Check for duplicate records per ID (if meaningful)
        if col.upper() in ['MAZ', 'TAZ', 'COUNTY', 'PUMA']:
            duplicate_ids = df[col].value_counts()
            max_duplicates = duplicate_ids.max()
            if max_duplicates > 1:
                dup_count = (duplicate_ids > 1).sum()
                print(f"  📊 IDs with multiple records: {dup_count:,}")
                print(f"  📊 Max records per ID: {max_duplicates:,}")
                if dup_count <= 10:
                    top_dups = duplicate_ids[duplicate_ids > 1].head()
                    for id_val, count in top_dups.items():
                        print(f"      {col} {id_val}: {count} records")

def analyze_control_categories(controls_df, seed_df, name):
    """Analyze how seed population maps to control categories"""
    print(f"\n{'='*60}")
    print(f"CONTROL CATEGORY MAPPING: {name}")
    print(f"{'='*60}")
    
    # Get control columns (exclude geographic IDs and totals)
    control_cols = []
    exclude_patterns = ['maz', 'taz', 'county', 'puma', 'tract', 'block', 'total', 'pop']
    
    for col in controls_df.columns:
        if not any(pattern in col.lower() for pattern in exclude_patterns):
            control_cols.append(col)
    
    print(f"Control categories found: {len(control_cols)}")
    for col in control_cols[:10]:  # Show first 10
        print(f"  {col}")
    
    if len(control_cols) > 10:
        print(f"  ... and {len(control_cols) - 10} more")
    
    # Try to find corresponding columns in seed data
    print(f"\nSeed population columns:")
    for col in seed_df.columns[:20]:  # Show first 20
        print(f"  {col}")
    
    if len(seed_df.columns) > 20:
        print(f"  ... and {len(seed_df.columns) - 20} more")

def analyze_seed_population_categories(households_df, persons_df):
    """Analyze seed population by potential control categories"""
    print(f"\n{'='*60}")
    print(f"SEED POPULATION CATEGORY ANALYSIS")
    print(f"{'='*60}")
    
    print(f"Households: {len(households_df):,}")
    print(f"Persons: {len(persons_df):,}")
    
    # Household size analysis
    if 'hhsize' in households_df.columns:
        print(f"\nHousehold Size Distribution:")
        size_dist = households_df['hhsize'].value_counts().sort_index()
        for size, count in size_dist.items():
            pct = count / len(households_df) * 100
            print(f"  Size {size}: {count:,} ({pct:.1f}%)")
    
    # Age analysis
    age_cols = [col for col in persons_df.columns if 'age' in col.lower()]
    if age_cols:
        age_col = age_cols[0]
        print(f"\nAge Distribution ({age_col}):")
        age_stats = persons_df[age_col].describe()
        print(f"  Min: {age_stats['min']:.0f}")
        print(f"  Max: {age_stats['max']:.0f}")
        print(f"  Mean: {age_stats['mean']:.1f}")
        print(f"  Missing: {persons_df[age_col].isnull().sum():,}")
        
        # Age groups
        age_bins = [0, 5, 18, 25, 35, 45, 55, 65, 75, 85, 120]
        age_labels = ['0-4', '5-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65-74', '75-84', '85+']
        persons_df['age_group'] = pd.cut(persons_df[age_col], bins=age_bins, labels=age_labels, right=False)
        age_group_dist = persons_df['age_group'].value_counts().sort_index()
        for group, count in age_group_dist.items():
            pct = count / len(persons_df) * 100
            print(f"  {group}: {count:,} ({pct:.1f}%)")
    
    # Income analysis
    income_cols = [col for col in households_df.columns if 'income' in col.lower() or 'hinc' in col.lower()]
    if income_cols:
        income_col = income_cols[0]
        print(f"\nIncome Distribution ({income_col}):")
        income_stats = households_df[income_col].describe()
        print(f"  Min: ${income_stats['min']:,.0f}")
        print(f"  Max: ${income_stats['max']:,.0f}")
        print(f"  Mean: ${income_stats['mean']:,.0f}")
        print(f"  Missing: {households_df[income_col].isnull().sum():,}")

def check_group_id_generation(households_df, persons_df):
    """Simulate PopulationSim group_id generation to find issues"""
    print(f"\n{'='*60}")
    print(f"GROUP_ID GENERATION SIMULATION")
    print(f"{'='*60}")
    
    # Try to create group_ids like PopulationSim does
    try:
        # Common grouping columns
        potential_group_cols = []
        
        # Household grouping columns
        hh_group_cols = []
        for col in households_df.columns:
            if any(pattern in col.lower() for pattern in ['hhsize', 'income', 'workers', 'vehicles', 'type']):
                if households_df[col].dtype in ['int64', 'float64', 'object']:
                    hh_group_cols.append(col)
        
        print(f"Potential household grouping columns: {hh_group_cols}")
        
        # Test group_id creation for households
        if hh_group_cols:
            test_col = hh_group_cols[0]
            print(f"\nTesting group_id creation with {test_col}:")
            
            # Check for problematic values
            test_series = households_df[test_col]
            print(f"  Data type: {test_series.dtype}")
            print(f"  Null values: {test_series.isnull().sum():,}")
            print(f"  Infinite values: {np.isinf(test_series).sum() if test_series.dtype in ['float64'] else 0}")
            
            # Try to convert to category codes (like PopulationSim does)
            try:
                if test_series.dtype == 'object':
                    categorical = pd.Categorical(test_series)
                    group_ids = categorical.codes
                    print(f"  ✓ Successfully created group_ids")
                    print(f"  Unique group_ids: {len(np.unique(group_ids))}")
                else:
                    # For numeric, try direct conversion
                    group_ids = test_series.astype('int32')
                    print(f"  ✓ Successfully converted to int32")
                    print(f"  Unique values: {len(np.unique(group_ids))}")
                    
            except Exception as e:
                print(f"  ❌ Failed to create group_ids: {e}")
                
                # Find problematic values
                problematic_mask = test_series.isnull() | np.isinf(test_series)
                problematic_count = problematic_mask.sum()
                if problematic_count > 0:
                    print(f"  Problematic values found: {problematic_count:,}")
                    problematic_values = test_series[problematic_mask].unique()[:10]
                    print(f"  Sample problematic values: {problematic_values}")
    
    except Exception as e:
        print(f"Error in group_id simulation: {e}")

def main():
    """Main validation function"""
    # Set up output file
    output_file = Path.cwd() / "data_validation_report.txt"
    
    # Redirect stdout to both console and file
    import sys
    class TeeOutput:
        def __init__(self, *files):
            self.files = files
        def write(self, text):
            for f in self.files:
                f.write(text)
                f.flush()
        def flush(self):
            for f in self.files:
                f.flush()
    
    with open(output_file, 'w') as f:
        tee = TeeOutput(sys.stdout, f)
        original_stdout = sys.stdout
        sys.stdout = tee
        
        try:
            print("COMPREHENSIVE POPULATIONSIM DATA VALIDATION")
            print("=" * 80)
            print(f"Report saved to: {output_file}")
            print("=" * 80)
            
            # Paths
            base_dir = Path.cwd()
            output_dir = base_dir / "output_2023"
            hh_gq_data_dir = base_dir / "hh_gq" / "data"
            hh_gq_configs_dir = base_dir / "hh_gq" / "configs_TM2"
    
    # Check if files exist
    seed_households_file = hh_gq_data_dir / "seed_households.csv"
    seed_persons_file = hh_gq_data_dir / "seed_persons.csv"
    maz_marginals_file = hh_gq_configs_dir / "maz_marginals_hhgq.csv"
    taz_marginals_file = hh_gq_configs_dir / "taz_marginals_hhgq.csv"
    county_marginals_file = hh_gq_configs_dir / "county_marginals.csv"
    geo_crosswalk_file = hh_gq_data_dir / "geo_cross_walk_tm2.csv"
    
    files_to_check = {
        "Seed Households": seed_households_file,
        "Seed Persons": seed_persons_file,
        "MAZ Marginals": maz_marginals_file,
        "TAZ Marginals": taz_marginals_file,
        "County Marginals": county_marginals_file,
        "Geo Crosswalk": geo_crosswalk_file
    }
    
    print("File Existence Check:")
    missing_files = []
    for name, file_path in files_to_check.items():
        exists = file_path.exists()
        status = "✓" if exists else "❌"
        print(f"  {status} {name}: {file_path}")
        if not exists:
            missing_files.append(name)
    
    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
        print("Cannot proceed with validation.")
        return
    
    print(f"\n✓ All required files found. Proceeding with analysis...")
    
    try:
        # Load data
        print(f"\nLoading data files...")
        households_df = pd.read_csv(seed_households_file)
        persons_df = pd.read_csv(seed_persons_file)
        maz_marginals_df = pd.read_csv(maz_marginals_file)
        taz_marginals_df = pd.read_csv(taz_marginals_file)
        county_marginals_df = pd.read_csv(county_marginals_file)
        geo_crosswalk_df = pd.read_csv(geo_crosswalk_file)
        
        # 1. Analyze control files
        analyze_dataframe_summary(maz_marginals_df, "MAZ Marginals (Controls)")
        analyze_dataframe_summary(taz_marginals_df, "TAZ Marginals (Controls)")
        analyze_dataframe_summary(county_marginals_df, "County Marginals (Controls)")
        
        # 2. Analyze seed population
        analyze_dataframe_summary(households_df, "Seed Households")
        analyze_dataframe_summary(persons_df, "Seed Persons")
        
        # 3. Analyze geographic crosswalk
        analyze_dataframe_summary(geo_crosswalk_df, "Geographic Crosswalk")
        analyze_geographic_ids(geo_crosswalk_df, "Geographic Crosswalk")
        
        # 4. Analyze geographic IDs in all files
        analyze_geographic_ids(households_df, "Seed Households")
        analyze_geographic_ids(persons_df, "Seed Persons")
        analyze_geographic_ids(maz_marginals_df, "MAZ Marginals")
        
        # 5. Analyze seed population categories
        analyze_seed_population_categories(households_df, persons_df)
        
        # 6. Analyze control category mapping
        analyze_control_categories(maz_marginals_df, households_df, "MAZ Controls vs Households")
        analyze_control_categories(taz_marginals_df, households_df, "TAZ Controls vs Households")
        
        # 7. Simulate group_id generation
        check_group_id_generation(households_df, persons_df)
        
        # 8. Final summary
        print(f"\n{'='*80}")
        print(f"VALIDATION SUMMARY")
        print(f"{'='*80}")
        
        total_households = len(households_df)
        total_persons = len(persons_df)
        total_mazs = len(maz_marginals_df)
        total_tazs = len(taz_marginals_df)
        
        print(f"Data Scale:")
        print(f"  Households: {total_households:,}")
        print(f"  Persons: {total_persons:,}")
        print(f"  MAZs with controls: {total_mazs:,}")
        print(f"  TAZs with controls: {total_tazs:,}")
        
        # Check for obvious data quality issues
        issues_found = []
        
        # Check for missing geographic IDs
        if 'MAZ' in households_df.columns and households_df['MAZ'].isnull().sum() > 0:
            issues_found.append(f"Missing MAZ assignments in households: {households_df['MAZ'].isnull().sum():,}")
        
        # Check for negative control values
        numeric_controls = maz_marginals_df.select_dtypes(include=[np.number])
        for col in numeric_controls.columns:
            if (numeric_controls[col] < 0).sum() > 0:
                issues_found.append(f"Negative control values in {col}: {(numeric_controls[col] < 0).sum():,}")
        
        if issues_found:
            print(f"\n⚠️  POTENTIAL ISSUES DETECTED:")
            for issue in issues_found:
                print(f"  • {issue}")
        else:
            print(f"\n✓ No obvious data quality issues detected")
        
            print(f"\nValidation complete. Check output above for detailed analysis.")
        
        except Exception as e:
            print(f"\n❌ Error during validation: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            sys.stdout = original_stdout

if __name__ == "__main__":
    main()
