#!/usr/bin/env python

import pandas as pd

# Read the corrected crosswalk
df = pd.read_csv('output_2023/geo_cross_walk_tm2_updated.csv')

print("County distribution in corrected crosswalk:")
county_counts = df.groupby(['COUNTY', 'county_name']).size().reset_index(name='count')
print(county_counts.to_string(index=False))

print(f"\nTotal counties: {len(county_counts)}")
print(f"Total MAZ records: {len(df)}")

# Check PUMA format
print(f"\nPUMA format check:")
print(f"Sample PUMAs: {df['PUMA'].head(10).tolist()}")
print(f"PUMA data type: {df['PUMA'].dtype}")
print(f"Unique PUMAs: {df['PUMA'].nunique()}")
