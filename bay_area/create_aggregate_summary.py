"""
PopulationSim Summary Generator for tm2py-utils Dashboard Format
==============================================================

Generate summary CSV files that match the tm2py-utils validation dashboard format
for comparison between 2015, 2023, and ACS control data.

This script:
1. Examines the structure of 2015 and 2023 PopulationSim outputs
2. Processes control data (ACS) for comparison
3. Generates dashboard-compatible CSV summaries
4. Handles group quarters (GQ) vs household distinctions
5. Creates regional and county-level summaries

Based on tm2py-utils validation framework pattern:
- CSV files with standardized columns (share, households, dataset)
- Both absolute counts and percentage shares
- Consistent categorical variable naming
- Multi-dataset comparison support
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuration
OUTPUT_DIR = Path("output_2023/dashboard_summaries")
OUTPUT_DIR.mkdir(exist_ok=True)

# County mapping
COUNTY_NAMES = {
    1: "San Francisco",
    2: "San Mateo", 
    3: "Santa Clara",
    4: "Alameda",
    5: "Contra Costa",
    6: "Solano",
    7: "Napa",
    8: "Sonoma",
    9: "Marin"
}

def examine_data_structure():
    """Examine the structure of available data files"""
    print("=== DATA STRUCTURE EXAMINATION ===")
    
    # Check 2023 outputs
    files_2023 = {
        'households': "output_2023/populationsim_working_dir/output/households_2023_tm2.csv",
        'persons': "output_2023/populationsim_working_dir/output/persons_2023_tm2.csv",
        'synthetic_hh': "output_2023/populationsim_working_dir/output/synthetic_households.csv",
        'synthetic_persons': "output_2023/populationsim_working_dir/output/synthetic_persons.csv"
    }
    
    # Check 2015 outputs  
    files_2015 = {
        'households': "example_2015_outputs/outputs/synthetic_households.csv",
        'persons': "example_2015_outputs/outputs/synthetic_persons.csv"
    }
    
    for year, files in [("2023", files_2023), ("2015", files_2015)]:
        print(f"\\n{year} Files:")
        for name, path in files.items():
            if Path(path).exists():
                # Read just first few rows to check structure
                try:
                    df = pd.read_csv(path, nrows=5)
                    print(f"  {name}: {len(df.columns)} columns - {list(df.columns)[:10]}...")
                    file_size = Path(path).stat().st_size / (1024**2)  # MB
                    print(f"    Size: {file_size:.1f} MB")
                except Exception as e:
                    print(f"  {name}: Error reading - {e}")
            else:
                print(f"  {name}: NOT FOUND - {path}")

def load_sample_data():
    """Load small samples to understand data structure"""
    print("\\n=== LOADING SAMPLE DATA ===")
    
    # Try to load samples from each dataset
    data = {}
    
    # 2023 data - try multiple sources
    for file_suffix in ['households_2023_tm2.csv', 'synthetic_households.csv']:
        path_2023 = f"output_2023/populationsim_working_dir/output/{file_suffix}"
        if Path(path_2023).exists():
            try:
                data['hh_2023'] = pd.read_csv(path_2023, nrows=1000)
                print(f"Loaded 2023 households sample from {file_suffix}: {len(data['hh_2023'])} rows")
                print(f"  Columns: {list(data['hh_2023'].columns)}")
                break
            except Exception as e:
                print(f"Error loading {path_2023}: {e}")
    
    # 2015 data
    path_2015 = "example_2015_outputs/outputs/synthetic_households.csv"
    if Path(path_2015).exists():
        try:
            data['hh_2015'] = pd.read_csv(path_2015, nrows=1000)
            print(f"Loaded 2015 households sample: {len(data['hh_2015'])} rows")
            print(f"  Columns: {list(data['hh_2015'].columns)}")
        except Exception as e:
            print(f"Error loading 2015 data: {e}")
    
    return data

def analyze_household_structure(data):
    """Analyze household data structure to understand available variables"""
    print("\\n=== HOUSEHOLD STRUCTURE ANALYSIS ===")
    
    for dataset_name, df in data.items():
        if 'hh_' in dataset_name:
            print(f"\\n{dataset_name.upper()} Structure:")
            print(f"  Total columns: {len(df.columns)}")
            
            # Look for key variables
            key_vars = {
                'geography': [col for col in df.columns if col.upper() in ['COUNTY', 'TAZ', 'TAZ_NODE', 'MAZ', 'MAZ_NODE', 'PUMA']],
                'household_type': [col for col in df.columns if 'HHT' in col.upper() or 'TYPE' in col],
                'size': [col for col in df.columns if 'SIZE' in col.upper() or col.upper() in ['NP', 'HHSIZE']],
                'income': [col for col in df.columns if 'INC' in col.upper() or 'HINCP' in col.upper()],
                'vehicles': [col for col in df.columns if 'VEH' in col.upper() or 'AUTO' in col.upper()],
                'tenure': [col for col in df.columns if 'TEN' in col.upper() or 'OWN' in col.upper()],
                'gq_type': [col for col in df.columns if 'GQ' in col.upper() or 'HHGQ' in col.upper()]
            }
            
            for var_type, cols in key_vars.items():
                if cols:
                    print(f"    {var_type}: {cols}")
                    
            # Sample values for key columns
            if 'COUNTY' in df.columns:
                print(f"    County distribution: {df['COUNTY'].value_counts().to_dict()}")
            
            if any('SIZE' in col.upper() for col in df.columns):
                size_col = next(col for col in df.columns if 'SIZE' in col.upper())
                print(f"    Household size distribution ({size_col}): {df[size_col].value_counts().sort_index().to_dict()}")

def load_control_data():
    """Load ACS control data for comparison"""
    print("\\n=== LOADING CONTROL DATA ===")
    
    control_files = [
        "output_2023/populationsim_working_dir/data/taz_marginals.csv",
        "output_2023/populationsim_working_dir/data/county_marginals.csv",
        "output_2023/populationsim_working_dir/data/puma_marginals.csv",
        "output_2023/populationsim_working_dir/data/maz_marginals_hhgq.csv"
    ]
    
    controls = {}
    for file_path in control_files:
        if Path(file_path).exists():
            try:
                df = pd.read_csv(file_path, nrows=100)
                file_name = Path(file_path).name
                controls[file_name] = df
                print(f"Loaded {file_name}: {len(df)} sample rows, {len(df.columns)} columns")
                print(f"  Columns: {list(df.columns)[:15]}...")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    
    return controls

def create_household_size_summary(hh_data, dataset_name):
    """Create household size summary matching tm2py-utils format"""
    print(f"\\nCreating household size summary for {dataset_name}")
    
    # Find household size column
    size_cols = [col for col in hh_data.columns if 'SIZE' in col.upper() or col.upper() in ['NP', 'HHSIZE']]
    if not size_cols:
        print(f"  No household size column found in {dataset_name}")
        return None
        
    size_col = size_cols[0]
    print(f"  Using size column: {size_col}")
    
    # Filter for households only (exclude GQ if possible)
    working_data = hh_data.copy()
    
    # Try to filter out group quarters
    gq_cols = [col for col in hh_data.columns if 'GQ' in col.upper() or 'HHGQ' in col.upper()]
    if gq_cols:
        gq_col = gq_cols[0]
        # Typically, hhgqtype 0 or 1 = households, 2/3 = group quarters
        household_mask = working_data[gq_col].isin([0, 1])
        working_data = working_data[household_mask]
        print(f"  Filtered to {len(working_data)} households (from {len(hh_data)} total)")
    
    # Create size bins
    working_data['household_size'] = working_data[size_col]
    
    # Cap at reasonable size
    working_data['household_size'] = working_data['household_size'].clip(upper=7)
    working_data.loc[working_data['household_size'] >= 7, 'household_size'] = '7+'
    
    # Create summary
    summary = working_data.groupby('household_size').size().reset_index(name='households')
    summary['share'] = summary['households'] / summary['households'].sum()
    summary['dataset'] = dataset_name
    
    return summary

def create_county_summary(hh_data, dataset_name):
    """Create county-level summary"""
    print(f"\\nCreating county summary for {dataset_name}")
    
    if 'COUNTY' not in hh_data.columns:
        print(f"  No COUNTY column found in {dataset_name}")
        return None
    
    # Filter for households only
    working_data = hh_data.copy()
    gq_cols = [col for col in hh_data.columns if 'GQ' in col.upper() or 'HHGQ' in col.upper()]
    if gq_cols:
        gq_col = gq_cols[0]
        household_mask = working_data[gq_col].isin([0, 1])
        working_data = working_data[household_mask]
    
    # Create county summary
    summary = working_data.groupby('COUNTY').size().reset_index(name='households')
    summary['county_name'] = summary['COUNTY'].map(COUNTY_NAMES)
    summary['share'] = summary['households'] / summary['households'].sum()
    summary['dataset'] = dataset_name
    
    return summary

def main():
    """Main execution function"""
    print("PopulationSim Summary Generator Starting...")
    print("=" * 50)
    
    # Step 1: Examine data structure
    examine_data_structure()
    
    # Step 2: Load sample data
    sample_data = load_sample_data()
    
    if not sample_data:
        print("ERROR: No data could be loaded. Check file paths.")
        return
    
    # Step 3: Analyze structure
    analyze_household_structure(sample_data)
    
    # Step 4: Load control data
    controls = load_control_data()
    
    # Step 5: Create initial summaries
    summaries = {}
    
    # Household size summaries
    for dataset_name, hh_data in sample_data.items():
        if 'hh_' in dataset_name:
            year = dataset_name.split('_')[1]
            summary = create_household_size_summary(hh_data, f"PopSim_{year}")
            if summary is not None:
                summaries[f'household_size_{year}'] = summary
    
    # County summaries  
    for dataset_name, hh_data in sample_data.items():
        if 'hh_' in dataset_name:
            year = dataset_name.split('_')[1] 
            summary = create_county_summary(hh_data, f"PopSim_{year}")
            if summary is not None:
                summaries[f'county_{year}'] = summary
    
    # Step 6: Save summaries
    print("\\n=== SAVING SUMMARIES ===")
    for name, df in summaries.items():
        output_path = OUTPUT_DIR / f"{name}.csv"
        df.to_csv(output_path, index=False)
        print(f"Saved {name}: {len(df)} rows → {output_path}")
        print(f"  Sample: {df.head(3).to_dict('records')}")
    
    # Step 7: Create combined files for dashboard
    if summaries:
        # Combine household size data
        size_summaries = [df for name, df in summaries.items() if 'household_size' in name]
        if size_summaries:
            combined_size = pd.concat(size_summaries, ignore_index=True)
            size_output = OUTPUT_DIR / "household_size_regional.csv"
            combined_size.to_csv(size_output, index=False)
            print(f"\\nSaved combined household size: {len(combined_size)} rows → {size_output}")
        
        # Combine county data
        county_summaries = [df for name, df in summaries.items() if 'county' in name]  
        if county_summaries:
            combined_county = pd.concat(county_summaries, ignore_index=True)
            county_output = OUTPUT_DIR / "households_by_county.csv"
            combined_county.to_csv(county_output, index=False)
            print(f"Saved combined county: {len(combined_county)} rows → {county_output}")
    
    print(f"\\nSummary generation complete! Output directory: {OUTPUT_DIR}")
    print("\\nNext steps:")
    print("1. Review generated CSV files")
    print("2. Extend to create additional summary types (income, household type, etc.)")
    print("3. Add full dataset processing (beyond samples)")
    print("4. Create dashboard YAML configurations")

if __name__ == "__main__":
    main()