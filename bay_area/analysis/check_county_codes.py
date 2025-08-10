#!/usr/bin/env python3
"""
Comprehensive county code format analysis across all PopulationSim files
"""
import pandas as pd

print("COUNTY CODE FORMAT ANALYSIS")
print("="*60)

# 1. County Marginals (Controls file)
print("\n1. COUNTY MARGINALS (Controls):")
try:
    county_marginals = pd.read_csv('output_2023/county_marginals.csv')
    county_col = county_marginals.columns[0]  # First column is county
    print(f"   Column name: '{county_col}'")
    print(f"   Data type: {county_marginals[county_col].dtype}")
    print(f"   Sample values: {county_marginals[county_col].head(3).tolist()}")
    print(f"   All values: {sorted(county_marginals[county_col].unique())}")
    county_controls = set(county_marginals[county_col].unique())
except Exception as e:
    print(f"   ❌ Error: {e}")
    county_controls = set()

# 2. Crosswalk file
print("\n2. CROSSWALK (Geography mapping):")
try:
    crosswalk = pd.read_csv('hh_gq/tm2_working_dir/data/geo_cross_walk_tm2.csv')
    print(f"   Columns: {list(crosswalk.columns)}")
    print(f"   COUNTY dtype: {crosswalk['COUNTY'].dtype}")
    print(f"   COUNTY sample: {crosswalk['COUNTY'].head(3).tolist()}")
    print(f"   COUNTY unique: {sorted(crosswalk['COUNTY'].unique())}")
    county_crosswalk = set(crosswalk['COUNTY'].unique())
except Exception as e:
    print(f"   ❌ Error: {e}")
    county_crosswalk = set()

# 3. Seed households
print("\n3. SEED HOUSEHOLDS:")
try:
    seed_households = pd.read_csv('output_2023/seed_households.csv')
    county_cols = [c for c in seed_households.columns if 'county' in c.lower()]
    if county_cols:
        county_col = county_cols[0]
        print(f"   Column name: '{county_col}'")
        print(f"   Data type: {seed_households[county_col].dtype}")
        print(f"   Sample values: {seed_households[county_col].head(3).tolist()}")
        print(f"   Unique values: {sorted(seed_households[county_col].unique())}")
        county_seed = set(seed_households[county_col].unique())
    else:
        print("   ❌ No county column found")
        county_seed = set()
except Exception as e:
    print(f"   ❌ Error: {e}")
    county_seed = set()

# 4. Seed persons (check if occupation data exists per county)
print("\n4. SEED PERSONS (Occupation data):")
try:
    seed_persons = pd.read_csv('output_2023/seed_persons.csv')
    county_cols = [c for c in seed_persons.columns if 'county' in c.lower()]
    if county_cols and 'occupation' in seed_persons.columns:
        county_col = county_cols[0]
        print(f"   County column: '{county_col}' (dtype: {seed_persons[county_col].dtype})")
        print(f"   Occupation column exists: YES")
        
        # Check occupation distribution by county
        occ_by_county = seed_persons.groupby([county_col, 'occupation']).size().unstack(fill_value=0)
        print(f"   Counties with occupation data: {list(occ_by_county.index)}")
        print(f"   Occupation codes: {list(occ_by_county.columns)}")
        
        # Check for counties with zero occupation counts
        zero_occ_counties = []
        for county in occ_by_county.index:
            if occ_by_county.loc[county].sum() == 0:
                zero_occ_counties.append(county)
        
        if zero_occ_counties:
            print(f"   ⚠️ Counties with ZERO occupation data: {zero_occ_counties}")
        
        county_persons = set(seed_persons[county_col].unique())
    else:
        print("   ❌ Missing county or occupation column")
        county_persons = set()
except Exception as e:
    print(f"   ❌ Error: {e}")
    county_persons = set()

# 5. Format Comparison
print("\n" + "="*60)
print("FORMAT COMPARISON ANALYSIS:")

# Check for mismatches
if county_controls and county_crosswalk:
    if county_controls == county_crosswalk:
        print("✅ County controls and crosswalk MATCH")
    else:
        print("❌ County controls and crosswalk MISMATCH")
        print(f"   In controls but not crosswalk: {county_controls - county_crosswalk}")
        print(f"   In crosswalk but not controls: {county_crosswalk - county_controls}")

if county_seed and county_crosswalk:
    if county_seed == county_crosswalk:
        print("✅ Seed households and crosswalk MATCH")
    else:
        print("❌ Seed households and crosswalk MISMATCH")
        print(f"   In seed but not crosswalk: {county_seed - county_crosswalk}")
        print(f"   In crosswalk but not seed: {county_crosswalk - county_seed}")

# 6. PopulationSim Meta Control Issue Analysis
print("\n" + "="*60)
print("META CONTROL FACTORING ISSUE ANALYSIS:")

if 'crosswalk' in locals() and 'county_marginals' in locals():
    try:
        # Check PUMA counts per county
        puma_counts = crosswalk.groupby('COUNTY')['PUMA'].nunique()
        print(f"\nPUMA counts per county:")
        for county, count in puma_counts.items():
            print(f"   County {county}: {count} PUMAs")
        
        # Check if any county controls don't have corresponding PUMAs
        counties_in_controls = set(county_marginals[county_marginals.columns[0]].unique())
        counties_in_crosswalk = set(crosswalk['COUNTY'].unique())
        
        missing_pumas = counties_in_controls - counties_in_crosswalk
        if missing_pumas:
            print(f"\n❌ Counties in controls WITHOUT PUMAs: {missing_pumas}")
            
        # This is likely the root cause of NaN errors in meta_control_factoring
        print(f"\nRoot cause analysis:")
        print(f"- Counties with controls: {len(counties_in_controls)}")
        print(f"- Counties with PUMAs: {len(counties_in_crosswalk)}")
        print(f"- Total PUMAs: {len(crosswalk)}")
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")

print("\n" + "="*60)
