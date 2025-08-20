
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
taz_id_col = next((c for c in taz_gdf.columns if c.lower() == 'taz'), taz_gdf.columns[0])
puma_id_col = next((c for c in puma_gdf.columns if c.lower().startswith('puma')), puma_gdf.columns[0])
taz_gdf[taz_id_col] = taz_gdf[taz_id_col].astype(str)
puma_gdf[puma_id_col] = puma_gdf[puma_id_col].astype(str)
taz_groups = taz_gdf.groupby(taz_id_col)
taz_assignments = {}
total_taz = len(taz_groups)
print(f"[INFO] Starting TAZ-PUMA assignment for {total_taz} TAZs...", flush=True)
start_time = time.time()
for i, (taz_id, taz_group) in enumerate(taz_groups, 1):
    if i % 25 == 0 or i == 1 or i == total_taz:
        elapsed = time.time() - start_time
        print(f"  Processing TAZ {i}/{total_taz} (ID: {taz_id}) - Elapsed: {elapsed:.1f}s", flush=True)
    taz_geom = taz_group.geometry.unary_union
    intersecting_pumas = []
    for idx, puma_row in puma_gdf.iterrows():
        if taz_geom.intersects(puma_row.geometry):
            intersecting_pumas.append((idx, puma_row[puma_id_col], puma_row.geometry))
    if len(intersecting_pumas) == 0:
        distances = [(idx, taz_geom.distance(puma_row.geometry), puma_row[puma_id_col]) for idx, puma_row in puma_gdf.iterrows()]
        nearest_idx, _, nearest_puma = min(distances, key=lambda x: x[1])
        taz_assignments[taz_id] = nearest_puma
    elif len(intersecting_pumas) == 1:
        _, puma_id, _ = intersecting_pumas[0]
        taz_assignments[taz_id] = puma_id
    else:
        max_area = 0
        best_puma = None
        for _, puma_id, puma_geom in intersecting_pumas:
            intersection = taz_geom.intersection(puma_geom)
            area = intersection.area
            if area > max_area:
                max_area = area
                best_puma = puma_id
        taz_assignments[taz_id] = best_puma if best_puma else intersecting_pumas[0][1]
print(f"[INFO] Finished TAZ-PUMA assignment in {time.time() - start_time:.1f}s.", flush=True)
taz_puma_df = pd.DataFrame(list(taz_assignments.items()), columns=['TAZ', 'PUMA'])
taz_puma_df['TAZ'] = taz_puma_df['TAZ'].astype(str)
taz_puma_df['PUMA'] = taz_puma_df['PUMA'].astype(str)

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
crosswalk_out.to_csv(OUTPUT_CROSSWALK, index=False)
print(f"[INFO] Wrote unified crosswalk to {OUTPUT_CROSSWALK} ({len(crosswalk_out)} rows)", flush=True)




# --- Two-step process: Use or create temp MAZ-TAZ-PUMA-COUNTY file ---
import geopandas as gpd
from pathlib import Path
TEMP_MAZ_FILE = Path("maz_taz_puma_county_temp.csv")
taz_shp = config.EXTERNAL_PATHS['taz_shapefile']
puma_shp = config.EXTERNAL_PATHS['puma_shapefile']

if TEMP_MAZ_FILE.exists():
    print(f"[INFO] Temp file {TEMP_MAZ_FILE} found. Loading instead of recomputing spatial joins...", flush=True)
    if str(TEMP_MAZ_FILE).endswith('.csv'):
        import pandas as pd
        taz_puma_df = pd.read_csv(TEMP_MAZ_FILE, dtype=str)
    else:
        taz_puma_df = gpd.read_file(TEMP_MAZ_FILE)
    # Ensure TAZ column is uppercase for merge
    if 'taz' in taz_puma_df.columns and 'TAZ' not in taz_puma_df.columns:
        taz_puma_df = taz_puma_df.rename(columns={'taz': 'TAZ'})
else:
    import time
    print(f"[SPATIAL] Loading TAZ shapefile: {taz_shp}", flush=True)
    taz_gdf = gpd.read_file(taz_shp)
    print(f"[SPATIAL] Loading PUMA shapefile: {puma_shp}", flush=True)
    puma_gdf = gpd.read_file(puma_shp)
    taz_col = 'TAZ' if 'TAZ' in taz_gdf.columns else taz_gdf.columns[0]
    puma_col = 'PUMA20' if 'PUMA20' in puma_gdf.columns else (
        'PUMACE20' if 'PUMACE20' in puma_gdf.columns else puma_gdf.columns[0])
    taz_gdf[taz_col] = taz_gdf[taz_col].astype(str)
    puma_gdf[puma_col] = puma_gdf[puma_col].astype(str)
    taz_groups = taz_gdf.groupby(taz_col)
    taz_assignments = {}
    total_taz = len(taz_groups)
    print(f"[INFO] Starting TAZ-PUMA assignment for {total_taz} TAZs...", flush=True)
    start_time = time.time()
    for i, (taz_id, taz_group) in enumerate(taz_groups, 1):
        if i % 25 == 0 or i == 1 or i == total_taz:
            elapsed = time.time() - start_time
            print(f"  Processing TAZ {i}/{total_taz} (ID: {taz_id}) - Elapsed: {elapsed:.1f}s", flush=True)
        taz_geom = taz_group.geometry.unary_union
        intersecting_pumas = []
        for idx, puma_row in puma_gdf.iterrows():
            if taz_geom.intersects(puma_row.geometry):
                intersecting_pumas.append((idx, puma_row[puma_col], puma_row.geometry))
        if len(intersecting_pumas) == 0:
            distances = [(idx, taz_geom.distance(puma_row.geometry), puma_row[puma_col]) for idx, puma_row in puma_gdf.iterrows()]
            nearest_idx, _, nearest_puma = min(distances, key=lambda x: x[1])
            taz_assignments[taz_id] = nearest_puma
        elif len(intersecting_pumas) == 1:
            _, puma_id, _ = intersecting_pumas[0]
            taz_assignments[taz_id] = puma_id
        else:
            max_area = 0
            best_puma = None
            for _, puma_id, puma_geom in intersecting_pumas:
                intersection = taz_geom.intersection(puma_geom)
                area = intersection.area
                if area > max_area:
                    max_area = area
                    best_puma = puma_id
            taz_assignments[taz_id] = best_puma if best_puma else intersecting_pumas[0][1]
    print(f"[INFO] Finished TAZ-PUMA assignment in {time.time() - start_time:.1f}s.", flush=True)
    taz_puma_df = pd.DataFrame(list(taz_assignments.items()), columns=['TAZ', 'PUMA'])
    # If TAZ column is lower case, rename to upper for consistency
    if 'taz' in taz_puma_df.columns and 'TAZ' not in taz_puma_df.columns:
        taz_puma_df = taz_puma_df.rename(columns={'taz': 'TAZ'})
    taz_puma_df.to_csv(TEMP_MAZ_FILE, index=False)
    print(f"[INFO] Saved TAZ-PUMA mapping to {TEMP_MAZ_FILE}", flush=True)


# (Removed all legacy maz_taz_county_puma_file logic; only config-driven files and new county file logic are used.)




# (Removed all legacy maz_with_counties and MAZ_TAZ_COUNTY_PUMA_FILE logic. Only config-driven county file logic is used.)




# --- Load authoritative MAZ/TAZ/COUNTY/PUMA file ---

# (Removed reference to needed_cols, which is now undefined. Use only config-driven logic above.)
crosswalk.to_csv(OUTPUT_CROSSWALK, index=False)
crosswalk.to_csv(OUTPUT_CROSSWALK, index=False)

# (Removed all legacy maz_with_counties and MAZ_TAZ_COUNTY_PUMA_FILE logic. Only config-driven county file logic is used.)
