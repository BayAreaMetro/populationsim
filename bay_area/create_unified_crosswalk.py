
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UNIFIED TM2 CROSSWALK CREATOR
Creates a single, canonical crosswalk CSV linking Census blocks, block groups, tracts, MAZ, TAZ, county, and PUMA for use in the TM2 PopulationSim pipeline.

- Requires ALL inputs: MAZ/TAZ shapefile, PUMA shapefile, County shapefile, and block-level CSV (blocks_mazs_tazs_2.5.csv)
- Output: geo_crosswalk_unified.csv (with columns: GEOID_block, GEOID_block_group, GEOID_tract, MAZ, TAZ, COUNTY, PUMA)
- This script is the only source of truth for crosswalks and should be referenced in the config.
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
from unified_tm2_config import config
import os

BLOCKS_FILE = config.EXTERNAL_PATHS['blocks_file']
MAZ_TAZ_COUNTY_PUMA_FILE = config.EXTERNAL_PATHS['maz_taz_county_puma_file']
OUTPUT_CROSSWALK = config.CROSSWALK_FILES['main_crosswalk']

# Ensure all required files exist
for f, name in zip([BLOCKS_FILE, MAZ_TAZ_COUNTY_PUMA_FILE],
                   ['blocks_file', 'maz_taz_county_puma_file']):
    if not Path(f).exists():
        raise FileNotFoundError(f"Required input {name} not found: {f}")

# Ensure output directory exists
OUTPUT_CROSSWALK.parent.mkdir(parents=True, exist_ok=True)


# Load block-level crosswalk
blocks = pd.read_csv(BLOCKS_FILE, dtype=str)

# Map columns to expected names, robustly handle missing columns
rename_map = {}
if 'GEOID10' in blocks.columns:
    rename_map['GEOID10'] = 'GEOID_block'
if 'maz' in blocks.columns:
    rename_map['maz'] = 'MAZ'
if 'taz' in blocks.columns:
    rename_map['taz'] = 'TAZ'
blocks = blocks.rename(columns=rename_map)

# Ensure types are string for merge
for col in ['MAZ', 'TAZ', 'GEOID_block']:
    if col in blocks.columns:
        blocks[col] = blocks[col].astype(str)




# Derive block group and tract from block GEOID if present
if 'GEOID_block' in blocks.columns:
    blocks['GEOID_block_group'] = blocks['GEOID_block'].str[:12]
    blocks['GEOID_tract'] = blocks['GEOID_block'].str[:11]
else:
    print("[FATAL] 'GEOID_block' column missing from blocks input after renaming. Check input file and column mapping.")
    raise RuntimeError("'GEOID_block' column missing from blocks input after renaming.")


# --- Load authoritative MAZ/TAZ/COUNTY/PUMA file ---
maz_with_counties = pd.read_csv(MAZ_TAZ_COUNTY_PUMA_FILE, dtype=str)
# Map columns to expected names for merge
maz_with_counties = maz_with_counties.rename(columns={
    'MAZ': 'MAZ',
    'TAZ': 'TAZ',
    'COUNTY': 'COUNTY',
    'county_name': 'COUNTY_NAME',
    'COUNTYFP10': 'COUNTY_FIPS',
    'TRACTCE10': 'TRACTCE10',
    'PUMA10': 'PUMA'
})
# Ensure types are string for merge
maz_with_counties['MAZ'] = maz_with_counties['MAZ'].astype(str)
maz_with_counties['TAZ'] = maz_with_counties['TAZ'].astype(str)
maz_with_counties['PUMA'] = maz_with_counties['PUMA'].astype(str)
maz_with_counties['COUNTY'] = maz_with_counties['COUNTY'].astype(str)



# Join blocks and maz_with_counties on MAZ
maz_col_blocks = 'MAZ'
maz_col_counties = 'MAZ'
print(f"[DEBUG] blocks rows: {len(blocks)}; unique MAZ: {blocks['MAZ'].nunique()}; unique TAZ: {blocks['TAZ'].nunique()}")
print(f"[DEBUG] maz_with_counties rows: {len(maz_with_counties)}; unique MAZ: {maz_with_counties['MAZ'].nunique()}; unique TAZ: {maz_with_counties['TAZ'].nunique()}")
crosswalk = blocks.merge(
    maz_with_counties,
    left_on=maz_col_blocks,
    right_on=maz_col_counties,
    how='left',
    suffixes=('', '_maz')
)
print(f"[DEBUG] crosswalk rows after merge: {len(crosswalk)} (should match number of blocks)")
print(f"[DEBUG] crosswalk columns after merge: {list(crosswalk.columns)}")

# Check for missing GEOID_block
if 'GEOID_block' not in crosswalk.columns:
    print(f"[ERROR] 'GEOID_block' column missing from crosswalk after merge. Columns present: {list(crosswalk.columns)}")
    print(f"[DEBUG] Sample rows: {crosswalk.head()}")
    raise RuntimeError("'GEOID_block' column missing from crosswalk after merge.")

# Check for unmatched blocks (rows with missing TAZ or COUNTY info)
unmatched = crosswalk[crosswalk['TAZ'].isna() | crosswalk['COUNTY'].isna()]
if not unmatched.empty:
    print(f"[ERROR] {len(unmatched)} rows in blocks did not match any TAZ in maz_with_counties. Example TAZs: {unmatched['TAZ'].unique()[:10]}")
    print(f"[DEBUG] Sample unmatched rows:\n{unmatched.head()}\n")

# Diagnostics: check for unmatched blocks
unmatched = crosswalk['COUNTY'].isna().sum()
if unmatched > 0:
    print(f"[WARN] {unmatched} blocks could not be matched to a MAZ in the county file.")

# Select and order output columns for the unified crosswalk
output_columns = [
    'GEOID_block',
    'GEOID_block_group',
    'GEOID_tract',
    'MAZ',
    'TAZ',
    'COUNTY',
    'COUNTY_NAME',
    'COUNTY_FIPS',
    'PUMA'
]
crosswalk_out = crosswalk[output_columns].copy()

# Write to output
crosswalk_out.to_csv(OUTPUT_CROSSWALK, index=False)
print(f"[INFO] Wrote unified crosswalk to {OUTPUT_CROSSWALK} ({len(crosswalk_out)} rows)")




# --- Load authoritative MAZ/TAZ/COUNTY/PUMA file ---
maz_with_counties = pd.read_csv(MAZ_TAZ_COUNTY_PUMA_FILE, dtype=str)
# Map columns to expected names for merge
maz_with_counties = maz_with_counties.rename(columns={
    'MAZ': 'MAZ',
    'TAZ': 'TAZ',
    'COUNTY': 'COUNTY',
    'county_name': 'COUNTY_NAME',
    'COUNTYFP10': 'COUNTY_FIPS',
    'TRACTCE10': 'TRACTCE10',
    'PUMA10': 'PUMA'
})

# Ensure types are string for merge
maz_with_counties['MAZ'] = maz_with_counties['MAZ'].astype(str)
maz_with_counties['TAZ'] = maz_with_counties['TAZ'].astype(str)
maz_with_counties['PUMA'] = maz_with_counties['PUMA'].astype(str)
maz_with_counties['COUNTY'] = maz_with_counties['COUNTY'].astype(str)

# --- Merge block-level data with MAZ/TAZ/PUMA/COUNTY assignments ---

# Ensure TAZ columns are string for join
blocks['TAZ'] = blocks['TAZ'].astype(str)

# Diagnostics: print unique PUMAs in maz_with_counties before merge
print(f"[DIAG] Unique PUMAs in maz_with_counties before merge: {sorted(maz_with_counties['PUMA'].unique())}")


# --- Canonical merge on MAZ with robust diagnostics ---
print("[INFO] Preparing to merge block-level and MAZ/TAZ/PUMA/COUNTY assignments (canonical join on MAZ)...")
print(f"[INFO] Columns in blocks DataFrame: {list(blocks.columns)}")
print(f"[INFO] Columns in maz_with_counties DataFrame: {list(maz_with_counties.columns)}")
print(f"[DEBUG] Sample blocks DataFrame:\n{blocks.head()}\n")
print(f"[DEBUG] Sample maz_with_counties DataFrame:\n{maz_with_counties.head()}\n")

merge_cols = ['MAZ', 'TAZ', 'COUNTY_FIPS', 'COUNTY_NAME', 'PUMA']
print(f"[INFO] Merging blocks (left) with MAZ/TAZ/PUMA/COUNTY assignments on 'MAZ' with columns: {merge_cols}")
crosswalk = pd.merge(
    blocks,
    maz_with_counties[merge_cols].drop_duplicates(),
    on='MAZ',
    how='left',
    indicator=True
)
print(f"[DEBUG] crosswalk rows after merge: {len(crosswalk)} (should match number of blocks)")
unmatched = crosswalk['_merge'] == 'left_only'
if unmatched.any():
    print(f"[ERROR] {unmatched.sum()} rows in blocks did not match any MAZ in maz_with_counties. Example MAZs: {crosswalk.loc[unmatched, 'MAZ'].unique()[:5]}")
crosswalk.drop(columns=['_merge'], inplace=True)
print(f"[INFO] Merge complete. Final crosswalk columns: {list(crosswalk.columns)}")

# Diagnostics: print unique PUMAs in final crosswalk
print(f"[DIAG] Unique PUMAs in final crosswalk: {sorted(crosswalk['PUMA'].dropna().unique())}")

# --- Finalize columns and output ---

# --- Unify TAZ columns after merge ---
if 'TAZ_x' in crosswalk.columns and 'TAZ_y' in crosswalk.columns:
    crosswalk['TAZ'] = crosswalk['TAZ_x'].combine_first(crosswalk['TAZ_y'])
    crosswalk = crosswalk.drop(columns=['TAZ_x', 'TAZ_y'])
elif 'TAZ_x' in crosswalk.columns:
    crosswalk = crosswalk.rename(columns={'TAZ_x': 'TAZ'})
    crosswalk = crosswalk.drop(columns=[col for col in ['TAZ_y'] if col in crosswalk.columns])
elif 'TAZ_y' in crosswalk.columns:
    crosswalk = crosswalk.rename(columns={'TAZ_y': 'TAZ'})
    crosswalk = crosswalk.drop(columns=[col for col in ['TAZ_x'] if col in crosswalk.columns])

# Add/rename columns for output as needed
crosswalk = crosswalk.rename(columns={
    'COUNTY_FIPS': 'COUNTY',
    'COUNTY_NAME': 'county_name'
})

# Output columns in requested order (add GEOID columns if present)
needed_cols = [
    col for col in [
        'GEOID_block', 'GEOID_block_group', 'GEOID_tract',
        'MAZ', 'TAZ', 'COUNTY', 'county_name', 'PUMA'
    ] if col in crosswalk.columns
]
crosswalk = crosswalk[needed_cols].drop_duplicates()

# Enforce correct types
for col in ['GEOID_block', 'GEOID_block_group', 'GEOID_tract', 'county_name']:
    if col in crosswalk.columns:
        crosswalk[col] = crosswalk[col].astype(str)
for col in ['MAZ', 'TAZ', 'COUNTY', 'PUMA']:
    if col in crosswalk.columns:
        crosswalk[col] = pd.to_numeric(crosswalk[col], errors='coerce').astype('Int64')

crosswalk.to_csv(OUTPUT_CROSSWALK, index=False)

# Diagnostics for missing or zero PUMA
if 'PUMA' in crosswalk.columns:
    missing_puma = crosswalk['PUMA'].isna().sum()
    zero_puma = (crosswalk['PUMA'] == 0).sum()
    if missing_puma > 0:
        print(f"[WARNING] {missing_puma} rows have missing (null) PUMA values. These will be dropped from the output crosswalk.")
    if zero_puma > 0:
        print(f"[WARNING] {zero_puma} rows have PUMA=0. These will be dropped from the output crosswalk.")
    crosswalk = crosswalk[~crosswalk['PUMA'].isna()]
    crosswalk = crosswalk[crosswalk['PUMA'] != 0]

# Remove any rows with TAZ of 0
if 'TAZ' in crosswalk.columns:
    zero_taz = (crosswalk['TAZ'] == 0).sum()
    if zero_taz > 0:
        print(f"[WARNING] {zero_taz} rows have TAZ=0. These will be dropped from the output crosswalk.")
    crosswalk = crosswalk[crosswalk['TAZ'] != 0]

# Convert Int64 columns to int for output (optional: if controls require strict int)
for col in ['MAZ', 'TAZ', 'COUNTY', 'PUMA']:
    if col in crosswalk.columns:
        crosswalk[col] = crosswalk[col].astype(int)

crosswalk.to_csv(OUTPUT_CROSSWALK, index=False)
print(f"Wrote unified crosswalk: {OUTPUT_CROSSWALK} ({len(crosswalk)} rows)")

# --- Summary: number of TAZs and MAZs by PUMA ID ---
if 'PUMA' in crosswalk.columns:
    maz_summary = crosswalk.groupby('PUMA')['MAZ'].nunique().reset_index(name='num_mazs')
    taz_summary = crosswalk.groupby('PUMA')['TAZ'].nunique().reset_index(name='num_tazs')
    summary = pd.merge(maz_summary, taz_summary, on='PUMA', how='outer').sort_values('PUMA')
    print("\nSummary: Number of TAZs and MAZs by PUMA ID")
    print(summary.to_string(index=False))
