#!/usr/bin/env python3
"""
Comprehensive PUMA code format analysis across all PopulationSim files
"""
import pandas as pd
import os

print("PUMA CODE FORMAT ANALYSIS")
print("="*60)

def analyze_puma_codes(file_path, file_description, puma_columns=None):
    """Analyze PUMA codes in a given file"""
    print(f"\n{file_description.upper()}:")
    try:
        if not os.path.exists(file_path):
            print(f"   ❌ File not found: {file_path}")
            return set()
        
        df = pd.read_csv(file_path)
        print(f"   File: {file_path}")
        print(f"   Columns: {list(df.columns)}")
        
        # Find PUMA-like columns
        if puma_columns is None:
            puma_cols = [col for col in df.columns if 'puma' in col.lower()]
        else:
            puma_cols = [col for col in puma_columns if col in df.columns]
        
        puma_values = set()
        
        if puma_cols:
            for col in puma_cols:
                print(f"   PUMA column: '{col}'")
                print(f"   Data type: {df[col].dtype}")
                print(f"   Sample values: {df[col].head(3).tolist()}")
                unique_vals = df[col].dropna().unique()
                print(f"   Unique count: {len(unique_vals)}")
                print(f"   All values: {sorted(unique_vals)[:10]}{'...' if len(unique_vals) > 10 else ''}")
                
                # Check format consistency
                string_vals = df[col].astype(str).str.replace('.0', '', regex=False)
                formats = {
                    'with_leading_zeros': string_vals.str.match(r'^\d{5}$').sum(),
                    'without_leading_zeros': string_vals.str.match(r'^\d{1,4}$').sum(),
                    'mixed_format': len(string_vals) - string_vals.str.match(r'^\d{1,5}$').sum()
                }
                print(f"   Format analysis: {formats}")
                
                puma_values.update(unique_vals)
        else:
            print("   ❌ No PUMA columns found")
            
        return puma_values
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return set()

# 1. Unified Config
print("\n1. UNIFIED CONFIG (BAY_AREA_PUMAS):")
try:
    import sys
    sys.path.append('.')
    from unified_tm2_config import UnifiedTM2Config
    config = UnifiedTM2Config()
    pumas = config.BAY_AREA_PUMAS
    print(f"   Source: unified_tm2_config.py")
    print(f"   Count: {len(pumas)}")
    print(f"   Format: All 5-digit strings with leading zeros")
    print(f"   Sample: {pumas[:5]}")
    print(f"   Data type: {type(pumas[0])}")
    config_pumas = set(pumas)
except Exception as e:
    print(f"   ❌ Error loading config: {e}")
    config_pumas = set()

# 2. Crosswalk file
crosswalk_pumas = analyze_puma_codes(
    'hh_gq/tm2_working_dir/data/geo_cross_walk_tm2.csv',
    '2. Crosswalk (Active)',
    ['PUMA']
)

# Also check the updated crosswalk
crosswalk_updated_pumas = analyze_puma_codes(
    'output_2023/geo_cross_walk_tm2_updated.csv',
    '3. Crosswalk (Updated)',
    ['PUMA']
)

# 4. Seed households
seed_hh_pumas = analyze_puma_codes(
    'output_2023/seed_households.csv',
    '4. Seed households',
    ['PUMA']
)

# 5. Seed persons  
seed_persons_pumas = analyze_puma_codes(
    'output_2023/seed_persons.csv',
    '5. Seed persons',
    ['PUMA']
)

# 6. Check if there are PUMA controls
puma_control_files = [
    ('output_2023/maz_marginals.csv', '6. MAZ marginals (check for PUMA refs)'),
    ('output_2023/taz_marginals.csv', '7. TAZ marginals (check for PUMA refs)'),
]

for file_path, description in puma_control_files:
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        puma_cols = [col for col in df.columns if 'puma' in col.lower()]
        if puma_cols:
            analyze_puma_codes(file_path, description, puma_cols)
        else:
            print(f"\n{description.upper()}:")
            print(f"   No PUMA columns found (expected for MAZ/TAZ controls)")

# 7. Check original PUMS data if accessible
print("\n8. ORIGINAL PUMS DATA:")
pums_files = [
    'M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23/hbayarea1923.csv',
    'M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23/pbayarea1923.csv'
]
for pums_file in pums_files:
    if os.path.exists(pums_file):
        print(f"   Checking: {os.path.basename(pums_file)}")
        try:
            # Read just first few rows to check format
            sample_df = pd.read_csv(pums_file, nrows=1000)
            puma_cols = [col for col in sample_df.columns if 'puma' in col.lower()]
            if puma_cols:
                for col in puma_cols:
                    unique_vals = sample_df[col].dropna().unique()
                    print(f"     {col}: {unique_vals[:5]}... (sample from first 1000 rows)")
        except Exception as e:
            print(f"     ❌ Error reading PUMS: {e}")
    else:
        print(f"   ❌ PUMS file not found: {os.path.basename(pums_file)}")

# COMPARISON ANALYSIS
print("\n" + "="*60)
print("PUMA FORMAT COMPARISON ANALYSIS:")

# Compare all PUMA sets
puma_sets = {
    'Config': config_pumas,
    'Crosswalk': crosswalk_pumas,
    'Crosswalk_Updated': crosswalk_updated_pumas,
    'Seed_HH': seed_hh_pumas,
    'Seed_Persons': seed_persons_pumas
}

# Remove empty sets
puma_sets = {k: v for k, v in puma_sets.items() if v}

print(f"\nDatasets with PUMA codes: {list(puma_sets.keys())}")

# Check for mismatches
for name1, pumas1 in puma_sets.items():
    for name2, pumas2 in puma_sets.items():
        if name1 < name2:  # Avoid duplicate comparisons
            # Convert to strings for comparison (handle mixed int/string)
            str_pumas1 = {str(p).zfill(5) for p in pumas1}
            str_pumas2 = {str(p).zfill(5) for p in pumas2}
            
            if str_pumas1 == str_pumas2:
                print(f"✅ {name1} and {name2} MATCH")
            else:
                print(f"❌ {name1} and {name2} MISMATCH")
                print(f"   In {name1} but not {name2}: {str_pumas1 - str_pumas2}")
                print(f"   In {name2} but not {name1}: {str_pumas2 - str_pumas1}")

# Format consistency check
print(f"\nPUMA FORMAT CONSISTENCY:")
for name, pumas in puma_sets.items():
    print(f"\n{name}:")
    sample_pumas = list(pumas)[:5]
    print(f"   Sample: {sample_pumas}")
    print(f"   Types: {[type(p).__name__ for p in sample_pumas]}")
    
    # Check if all are 5-digit format
    str_pumas = [str(p) for p in pumas]
    five_digit = [p for p in str_pumas if len(p) == 5 and p.isdigit()]
    other_format = [p for p in str_pumas if not (len(p) == 5 and p.isdigit())]
    
    print(f"   5-digit format: {len(five_digit)}/{len(str_pumas)}")
    if other_format:
        print(f"   Other formats: {other_format[:5]}{'...' if len(other_format) > 5 else ''}")

print("\n" + "="*60)
print("RECOMMENDATION:")
print("All PUMA codes should be:")
print("1. String format with leading zeros (e.g., '00101')")
print("2. Exactly 5 digits")
print("3. Consistent across all files")
print("4. Match the unified config BAY_AREA_PUMAS list")
print("="*60)
