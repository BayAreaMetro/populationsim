#!/usr/bin/env python3
"""
Fix county code format mismatch between controls and crosswalk
"""
import pandas as pd

print("FIXING COUNTY CODE FORMAT MISMATCH")
print("="*50)

# Read the files
print("1. Reading county marginals...")
county_marginals = pd.read_csv('output_2023/county_marginals.csv')
print(f"   Original county codes: {sorted(county_marginals['COUNTY'].unique())}")

print("\n2. Reading crosswalk...")
crosswalk = pd.read_csv('hh_gq/tm2_working_dir/data/geo_cross_walk_tm2.csv')
print(f"   Crosswalk county codes: {sorted(crosswalk['COUNTY'].unique())}")

# Create mapping from full FIPS to last 2 digits
# California FIPS codes: 6001=Alameda, 6013=Contra Costa, etc.
fips_to_last2 = {}
for fips in county_marginals['COUNTY'].unique():
    if pd.notna(fips):
        last2 = int(fips) % 100  # Get last 2 digits
        fips_to_last2[fips] = last2

print(f"\n3. FIPS to last-2-digits mapping:")
for fips, last2 in sorted(fips_to_last2.items()):
    print(f"   {int(fips)} -> {last2}")

# Fix the county marginals to use last 2 digits
print(f"\n4. Converting county marginals to use last 2 digits...")
county_marginals_fixed = county_marginals.copy()
county_marginals_fixed['COUNTY'] = county_marginals_fixed['COUNTY'].map(
    lambda x: int(x) % 100 if pd.notna(x) else x
)

print(f"   Fixed county codes: {sorted(county_marginals_fixed['COUNTY'].unique())}")

# Verify they now match
crosswalk_counties = set(crosswalk['COUNTY'].unique())
fixed_counties = set(county_marginals_fixed['COUNTY'].unique())

print(f"\n5. Verification:")
if crosswalk_counties == fixed_counties:
    print("   ✅ County codes now MATCH between files!")
else:
    print("   ❌ Still have mismatches:")
    print(f"      In controls but not crosswalk: {fixed_counties - crosswalk_counties}")
    print(f"      In crosswalk but not controls: {crosswalk_counties - fixed_counties}")

# Save the fixed file
output_file = 'output_2023/county_marginals_fixed.csv'
county_marginals_fixed.to_csv(output_file, index=False)
print(f"\n6. Saved fixed county marginals to: {output_file}")

# Also check if we need to fix seed files
print(f"\n7. Checking seed files...")
try:
    seed_households = pd.read_csv('output_2023/seed_households.csv')
    county_cols = [c for c in seed_households.columns if 'county' in c.lower()]
    if county_cols:
        county_col = county_cols[0]
        seed_counties = seed_households[county_col].unique()
        print(f"   Seed household counties: {sorted(seed_counties)}")
        
        # Check if seed also needs fixing
        if any(c > 100 for c in seed_counties if pd.notna(c)):
            print("   ⚠️ Seed households also need county code fixing")
        else:
            print("   ✅ Seed households already use correct format")
    else:
        print("   No county column found in seed households")
except Exception as e:
    print(f"   Error checking seed households: {e}")

print(f"\n" + "="*50)
print("NEXT STEPS:")
print("1. Replace county_marginals.csv with county_marginals_fixed.csv")
print("2. Or update the crosswalk to use full FIPS codes")
print("3. Ensure all files use consistent county code format")
print("="*50)
