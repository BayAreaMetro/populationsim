
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
OUTPUT_CROSSWALK = config.CROSSWALK_FILES['main_crosswalk']

required_files = [
    config.EXTERNAL_PATHS['blocks_file'],
    config.EXTERNAL_PATHS['maz_taz_county_file'],
    config.EXTERNAL_PATHS['taz_shapefile'],
    config.EXTERNAL_PATHS['puma_shapefile']
]
required_names = ['blocks_file', 'maz_taz_county_file', 'taz_shapefile', 'puma_shapefile']
for f, name in zip(required_files, required_names):
    if not Path(f).exists():
        raise FileNotFoundError(f"Required input {name} not found: {f}")

# Ensure output directory exists
OUTPUT_CROSSWALK.parent.mkdir(parents=True, exist_ok=True)



# 1. Load MAZ/TAZ/COUNTY file (from config), keep only MAZ, TAZ, COUNTY, drop others
COUNTY_FILE = config.EXTERNAL_PATHS['maz_taz_county_file']
county_df = pd.read_csv(COUNTY_FILE, dtype=str)
county_cols = [col for col in county_df.columns]
# Try to find the right columns (case-insensitive)
maz_col = next((c for c in county_cols if c.lower() == 'maz'), None)
taz_col = next((c for c in county_cols if c.lower() == 'taz'), None)
county_col = next((c for c in county_cols if c.lower() == 'county'), None)
if not (maz_col and taz_col and county_col):
    raise RuntimeError(f"Could not find required columns in county file: {COUNTY_FILE}")
maz_taz_county_df = county_df[[maz_col, taz_col, county_col]].copy()
maz_taz_county_df = maz_taz_county_df.rename(columns={maz_col: 'MAZ', taz_col: 'TAZ', county_col: 'COUNTY'})
maz_taz_county_df['MAZ'] = maz_taz_county_df['MAZ'].astype(str)
maz_taz_county_df['TAZ'] = maz_taz_county_df['TAZ'].astype(str)
maz_taz_county_df['COUNTY'] = maz_taz_county_df['COUNTY'].astype(str)

# 2. Spatial join TAZ to PUMA (shapefiles from config)
taz_shp = config.EXTERNAL_PATHS['taz_shapefile']
puma_shp = config.EXTERNAL_PATHS['puma_shapefile']
import geopandas as gpd
import time
print(f"[SPATIAL] Loading TAZ shapefile: {taz_shp}", flush=True)
taz_gdf = gpd.read_file(taz_shp)
print(f"[SPATIAL] Loading PUMA shapefile: {puma_shp}", flush=True)
puma_gdf = gpd.read_file(puma_shp)
taz_crs = taz_gdf.crs
if puma_gdf.crs != taz_crs:
    print(f"[SPATIAL] Reprojecting PUMA from {puma_gdf.crs} to {taz_crs}", flush=True)
    puma_gdf = puma_gdf.to_crs(taz_crs)
taz_id_col = next((c for c in taz_gdf.columns if c.lower() == 'taz'), taz_gdf.columns[0])
puma_id_col = next((c for c in puma_gdf.columns if c.lower().startswith('puma')), puma_gdf.columns[0])
taz_gdf[taz_id_col] = taz_gdf[taz_id_col].astype(str)
puma_gdf[puma_id_col] = puma_gdf[puma_id_col].astype(str)
taz_groups = taz_gdf.groupby(taz_id_col)
taz_assignments = {}

# --- Fast vectorized TAZ→PUMA assignment using overlay ---
print("[SPATIAL] Computing TAZ-PUMA intersections (vectorized)...", flush=True)
overlays = gpd.overlay(
    taz_gdf[[taz_id_col, 'geometry']],
    puma_gdf[[puma_id_col, 'geometry']],
    how='intersection'
)
overlays['overlap_area'] = overlays.geometry.area
idx = overlays.groupby(taz_id_col)['overlap_area'].idxmax()
taz_puma_df = overlays.loc[idx, [taz_id_col, puma_id_col]].copy()
taz_puma_df[taz_id_col] = taz_puma_df[taz_id_col].astype(str)
taz_puma_df[puma_id_col] = taz_puma_df[puma_id_col].astype(str)
taz_puma_df = taz_puma_df.rename(columns={taz_id_col: 'TAZ', puma_id_col: 'PUMA'})

# 3. Join maz_taz_county_df to taz_puma_df (left join on TAZ)
maz_taz_county_puma_df = maz_taz_county_df.merge(taz_puma_df, on='TAZ', how='left')

# 4. Read blocks file (from config), extract block, MAZ, TAZ, derive block group/tract
blocks_file = config.EXTERNAL_PATHS['blocks_file']
blocks = pd.read_csv(blocks_file, dtype=str)
rename_map = {}
if 'GEOID10' in blocks.columns:
    rename_map['GEOID10'] = 'GEOID_block'
if 'maz' in blocks.columns:
    rename_map['maz'] = 'MAZ'
if 'taz' in blocks.columns:
    rename_map['taz'] = 'TAZ'
blocks = blocks.rename(columns=rename_map)
for col in ['MAZ', 'TAZ', 'GEOID_block']:
    if col in blocks.columns:
        blocks[col] = blocks[col].astype(str)
if 'GEOID_block' in blocks.columns:
    blocks['GEOID_block_group'] = blocks['GEOID_block'].str[:12]
    blocks['GEOID_tract'] = blocks['GEOID_block'].str[:11]
else:
    print("[FATAL] 'GEOID_block' column missing from blocks input after renaming. Check input file and column mapping.", flush=True)
    raise RuntimeError("'GEOID_block' column missing from blocks input after renaming.")

# 5. Join maz_taz_county_puma_df to blocks on MAZ (left join)
crosswalk = blocks.merge(
    maz_taz_county_puma_df,
    on='MAZ',
    how='left',
    suffixes=('', '_maz')
)

# 6. Carefully check/align column names and types for output
output_columns = [
    'GEOID_block',
    'GEOID_block_group',
    'GEOID_tract',
    'MAZ',
    'TAZ',
    'COUNTY',
    'PUMA'
]
for col in output_columns:
    if col in crosswalk.columns:
        crosswalk[col] = crosswalk[col].astype(str)
crosswalk_out = crosswalk[output_columns].copy()

# 7. Write to output

# Remove rows with TAZ == 0 or NaN
before = len(crosswalk_out)
crosswalk_out = crosswalk_out[~crosswalk_out['TAZ'].isna()]
crosswalk_out = crosswalk_out[crosswalk_out['TAZ'] != '0']
after = len(crosswalk_out)
removed = before - after
if removed > 0:
    print(f"[CLEANUP] Removed {removed} rows with TAZ=0 or NaN", flush=True)

crosswalk_out.to_csv(OUTPUT_CROSSWALK, index=False)
print(f"[INFO] Wrote unified crosswalk to {OUTPUT_CROSSWALK} ({len(crosswalk_out)} rows)", flush=True)




