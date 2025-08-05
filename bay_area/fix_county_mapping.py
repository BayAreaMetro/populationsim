import pandas as pd

# Define the correct mapping from crosswalk COUNTY numbers to FIPS codes
# Based on Bay Area county FIPS codes
county_fips_mapping = {
    1: '075',  # San Francisco
    2: '081',  # San Mateo  
    3: '085',  # Santa Clara
    4: '001',  # Alameda
    5: '013',  # Contra Costa
    6: '095',  # Solano
    7: '055',  # Napa
    8: '097',  # Sonoma
    9: '041'   # Marin
}

print("Fixed county mapping:")
for county_num, fips in county_fips_mapping.items():
    print(f"County {county_num} -> FIPS {fips}")

# Test if this fixes the scaling
print("\nChecking if targets exist for these FIPS codes:")
targets_df = pd.read_csv('output_2023/county_targets_acs2023.csv')
available_fips = targets_df['county_fips'].unique()
print("Available FIPS codes in targets:", sorted(available_fips))

print("\nMapping validation:")
for county_num, fips in county_fips_mapping.items():
    if fips in available_fips:
        print(f"✓ County {county_num} -> FIPS {fips} (target exists)")
    else:
        print(f"✗ County {county_num} -> FIPS {fips} (NO TARGET)")
