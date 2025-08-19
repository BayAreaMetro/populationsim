
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

# Input and output paths from config
BLOCKS_FILE = config.EXTERNAL_PATHS['blocks_file']
MAZ_SHAPEFILE = config.SHAPEFILES['maz_shapefile']
PUMA_SHAPEFILE = config.SHAPEFILES['puma_shapefile']
COUNTY_SHAPEFILE = config.SHAPEFILES['county_shapefile']
OUTPUT_CROSSWALK = config.CROSSWALK_FILES['main_crosswalk']

# Ensure all required files exist
for f, name in zip([BLOCKS_FILE, MAZ_SHAPEFILE, PUMA_SHAPEFILE, COUNTY_SHAPEFILE],
                   ['blocks_file', 'maz_shapefile', 'puma_shapefile', 'county_shapefile']):
    if not Path(f).exists():
        raise FileNotFoundError(f"Required input {name} not found: {f}")

# Ensure output directory exists
OUTPUT_CROSSWALK.parent.mkdir(parents=True, exist_ok=True)

# Load block-level crosswalk
blocks = pd.read_csv(BLOCKS_FILE, dtype=str)

# Standardize column names
blocks.rename(columns={
    'GEOID10': 'GEOID_block',
    'maz': 'MAZ',
    'taz': 'TAZ',
    'county': 'COUNTY',
    'puma': 'PUMA'
}, inplace=True)

# Derive block group and tract from block GEOID
blocks['GEOID_block_group'] = blocks['GEOID_block'].str[:12]
blocks['GEOID_tract'] = blocks['GEOID_block'].str[:11]


# --- Load MAZ shapefile (contains TAZ relationships) ---
maz_gdf = gpd.read_file(MAZ_SHAPEFILE)
maz_col = next((col for col in maz_gdf.columns if col.upper() in ['MAZ', 'MAZ_ID', 'MAZ_ID_']), None)
taz_col = next((col for col in maz_gdf.columns if col.upper() in ['TAZ', 'TAZ_ID', 'TAZ1454']), None)
if not maz_col or not taz_col:
    raise ValueError(f"Could not identify MAZ and TAZ columns in MAZ shapefile: {list(maz_gdf.columns)}")

# --- Load PUMA shapefile ---
puma_gdf = gpd.read_file(PUMA_SHAPEFILE)
puma_col = next((col for col in puma_gdf.columns if col.upper() in ['PUMA', 'PUMACE20', 'PUMA20']), None)
if not puma_col:
    raise ValueError(f"Could not identify PUMA column in PUMA shapefile: {list(puma_gdf.columns)}")


# --- Area-based TAZ-PUMA assignment with progress reporting ---
import time
taz_groups = maz_gdf.groupby(taz_col)
taz_assignments = {}
total_taz = len(taz_groups)
print(f"[INFO] Starting TAZ-PUMA assignment for {total_taz} TAZs...")
start_time = time.time()
for i, (taz_id, taz_group) in enumerate(taz_groups, 1):
    if i % 25 == 0 or i == 1 or i == total_taz:
        elapsed = time.time() - start_time
        print(f"  Processing TAZ {i}/{total_taz} (ID: {taz_id}) - Elapsed: {elapsed:.1f}s")
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
print(f"[INFO] Finished TAZ-PUMA assignment in {time.time() - start_time:.1f}s.")

maz_gdf['PUMA'] = maz_gdf[taz_col].map(taz_assignments)

# --- Load County shapefile and assign COUNTY to MAZ using centroid spatial join ---
county_gdf = gpd.read_file(COUNTY_SHAPEFILE)
county_name_col = next((col for col in county_gdf.columns if col.upper() in ['NAME', 'COUNTY_NAME', 'COUNTYNAME']), None)
county_fips_col = next((col for col in county_gdf.columns if col.upper() in ['FIPS', 'COUNTYFP', 'FIPSCODE', 'CNTY_FIPS', 'COUNTY_FIP']), None)
if not county_name_col or not county_fips_col:
    raise ValueError(f"Could not identify county name and FIPS columns in county shapefile: {list(county_gdf.columns)}")


# Reproject for spatial join
target_crs = 'EPSG:3857'
print("[INFO] Reprojecting for county spatial join...")
maz_projected = maz_gdf.to_crs(target_crs)
maz_centroids = maz_projected.copy()
maz_centroids['geometry'] = maz_centroids.geometry.centroid
county_projected = county_gdf.to_crs(target_crs)

print("[INFO] Performing spatial join for MAZ-county assignment...")
maz_with_counties = gpd.sjoin(
    maz_centroids[[maz_col, taz_col, 'PUMA', 'geometry']],
    county_projected[[county_name_col, county_fips_col, 'geometry']],
    how='left',
    predicate='intersects'
)

maz_with_counties = maz_with_counties.rename(columns={county_fips_col: 'COUNTY_FIPS', county_name_col: 'COUNTY_NAME'})
print(f"[INFO] Spatial join complete. Assigned counties to {len(maz_with_counties)} MAZs.")

# --- Merge block-level data with MAZ/TAZ/PUMA/COUNTY assignments ---
blocks['MAZ'] = blocks['MAZ'].astype(str)
maz_with_counties['MAZ'] = maz_with_counties[maz_col].astype(str)
maz_with_counties['TAZ'] = maz_with_counties[taz_col].astype(str)

crosswalk = pd.merge(
    blocks,
    maz_with_counties[['MAZ', 'TAZ', 'PUMA', 'COUNTY_FIPS', 'COUNTY_NAME']],
    on='MAZ',
    how='left'
)
# Ensure TAZ column is present and named correctly
if 'TAZ' not in crosswalk.columns and taz_col in crosswalk.columns:
    crosswalk['TAZ'] = crosswalk[taz_col]

# --- Finalize columns and output ---
needed_cols = [
    'GEOID_block', 'GEOID_block_group', 'GEOID_tract',
    'MAZ', 'TAZ', 'COUNTY_FIPS', 'COUNTY_NAME', 'PUMA'
]
crosswalk = crosswalk[needed_cols].drop_duplicates()
crosswalk.to_csv(OUTPUT_CROSSWALK, index=False)
print(f"Wrote unified crosswalk: {OUTPUT_CROSSWALK} ({len(crosswalk)} rows)")
