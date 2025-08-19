
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


# --- Two-step process: Use or create temp MAZ-TAZ-PUMA-COUNTY file ---
TEMP_MAZ_FILE = Path("maz_taz_puma_county_temp.csv")
if TEMP_MAZ_FILE.exists():
    print(f"[INFO] Temp file {TEMP_MAZ_FILE} found. Loading instead of recomputing spatial joins...")
    maz_with_counties = gpd.read_file(TEMP_MAZ_FILE)
else:
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
    print(f"[INFO] Loading County shapefile: {COUNTY_SHAPEFILE}")
    county_gdf = gpd.read_file(COUNTY_SHAPEFILE)
    print(f"[INFO] Loaded {len(county_gdf)} counties. CRS: {county_gdf.crs}")
    county_name_col = next((col for col in county_gdf.columns if col.upper() in ['NAME', 'COUNTY_NAME', 'COUNTYNAME']), None)
    county_fips_col = next((col for col in county_gdf.columns if col.upper() in ['FIPS', 'COUNTYFP', 'FIPSCODE', 'CNTY_FIPS', 'COUNTY_FIP']), None)
    if not county_name_col or not county_fips_col:
        raise ValueError(f"Could not identify county name and FIPS columns in county shapefile: {list(county_gdf.columns)}")

    # Filter to Bay Area counties using FIPS codes
    bay_area_fips = ['001', '013', '041', '055', '075', '081', '085', '095', '097']
    county_gdf['FIPS_STR'] = county_gdf[county_fips_col].astype(str).str.zfill(3)
    county_gdf = county_gdf[county_gdf['FIPS_STR'].isin(bay_area_fips)]
    print(f"[INFO] Filtered to Bay Area: {len(county_gdf)} counties. Names: {sorted(county_gdf[county_name_col].tolist())}")

    # Reproject for spatial join
    target_crs = 'EPSG:3857'
    print(f"[INFO] Reprojecting MAZ and County to {target_crs} for spatial join...")
    print(f"[DEBUG] MAZ CRS before: {maz_gdf.crs}")
    print(f"[DEBUG] County CRS before: {county_gdf.crs}")
    maz_projected = maz_gdf.to_crs(target_crs)
    maz_centroids = maz_projected.copy()
    maz_centroids['geometry'] = maz_centroids.geometry.centroid
    county_projected = county_gdf.to_crs(target_crs)
    print(f"[DEBUG] MAZ CRS after: {maz_projected.crs}")
    print(f"[DEBUG] County CRS after: {county_projected.crs}")

    print(f"[DEBUG] MAZ count before join: {len(maz_centroids)}; County count: {len(county_projected)}")
    print(f"[DEBUG] MAZ CRS: {maz_centroids.crs}; County CRS: {county_projected.crs}")
    print("[INFO] Performing spatial join for MAZ-county assignment...")
    maz_with_counties = gpd.sjoin(
        maz_centroids[[maz_col, taz_col, 'PUMA', 'geometry']],
        county_projected[[county_name_col, county_fips_col, 'geometry']],
        how='left',
        predicate='intersects'
    )

    maz_with_counties = maz_with_counties.rename(columns={county_fips_col: 'COUNTY_FIPS', county_name_col: 'COUNTY_NAME'})
    print(f"[INFO] Spatial join complete. Assigned counties to {len(maz_with_counties)} MAZs.")
    if len(maz_with_counties) == 0:
        print("[FATAL] Spatial join produced zero rows! Not writing temp file. Check input shapefiles and CRS.")
        print(f"[DEBUG] MAZ columns: {list(maz_centroids.columns)}")
        print(f"[DEBUG] County columns: {list(county_projected.columns)}")
        raise RuntimeError("Spatial join failed: no MAZs assigned to counties.")

    # Fallback: assign nearest county to unmatched MAZs
    unmatched = maz_with_counties['COUNTY_FIPS'].isna()
    if unmatched.any():
        print(f"[WARN] {unmatched.sum()} MAZs not matched to a county. Assigning nearest county...")
        from shapely.ops import nearest_points
        for idx in maz_with_counties[unmatched].index:
            maz_geom = maz_with_counties.at[idx, 'geometry']
            # Find nearest county polygon
            min_dist = float('inf')
            nearest_name = None
            nearest_fips = None
            for _, county_row in county_projected.iterrows():
                dist = maz_geom.distance(county_row.geometry)
                if dist < min_dist:
                    min_dist = dist
                    nearest_name = county_row[county_name_col]
                    nearest_fips = county_row[county_fips_col]
            maz_with_counties.at[idx, 'COUNTY_NAME'] = nearest_name
            maz_with_counties.at[idx, 'COUNTY_FIPS'] = nearest_fips
        print(f"[INFO] All MAZs now have a county assignment.")

    # Save temp file for future runs
    if str(TEMP_MAZ_FILE).endswith('.csv'):
        maz_with_counties.to_csv(TEMP_MAZ_FILE, index=False)
    elif str(TEMP_MAZ_FILE).endswith('.geojson'):
        maz_with_counties.to_file(TEMP_MAZ_FILE, driver='GeoJSON')
    elif str(TEMP_MAZ_FILE).endswith('.shp'):
        maz_with_counties.to_file(TEMP_MAZ_FILE, driver='ESRI Shapefile')

# --- Merge block-level data with MAZ/TAZ/PUMA/COUNTY assignments ---
blocks['MAZ'] = blocks['MAZ'].astype(str)
maz_with_counties['MAZ'] = maz_with_counties[maz_col].astype(str)
maz_with_counties['TAZ'] = maz_with_counties[taz_col].astype(str)

# Extensive error catching and diagnostics for merge
try:
    print("[INFO] Preparing to merge block-level and MAZ/TAZ/PUMA/COUNTY assignments...")
    print(f"[INFO] Columns in blocks DataFrame: {list(blocks.columns)}")
    print(f"[INFO] Columns in maz_with_counties DataFrame: {list(maz_with_counties.columns)}")
    # Check for required columns before merge
    for col in ['MAZ']:
        if col not in blocks.columns:
            raise KeyError(f"Column '{col}' missing from blocks DataFrame. Columns: {list(blocks.columns)}")
        if col not in maz_with_counties.columns:
            raise KeyError(f"Column '{col}' missing from maz_with_counties DataFrame. Columns: {list(maz_with_counties.columns)}")
    # Check for duplicate MAZs in either input
    if blocks['MAZ'].duplicated().any():
        print(f"[WARN] Duplicate MAZ values found in blocks DataFrame.")
    if maz_with_counties['MAZ'].duplicated().any():
        print(f"[WARN] Duplicate MAZ values found in maz_with_counties DataFrame.")
    # Print row counts before merge
    print(f"[DEBUG] blocks rows: {len(blocks)}, maz_with_counties rows: {len(maz_with_counties)}")
    # Perform merge
    merge_cols = ['MAZ', 'TAZ', 'PUMA', 'COUNTY_FIPS', 'COUNTY_NAME'] if 'TAZ' in maz_with_counties.columns else ['MAZ', taz_col, 'PUMA', 'COUNTY_FIPS', 'COUNTY_NAME']
    print(f"[INFO] Merging on column 'MAZ' with columns: {merge_cols}")
    crosswalk = pd.merge(
        blocks,
        maz_with_counties[merge_cols],
        on='MAZ',
        how='left',
        indicator=True
    )
    # Print diagnostics after merge
    print(f"[DEBUG] crosswalk rows after merge: {len(crosswalk)}")
    unmatched = crosswalk['_merge'] == 'left_only'
    if unmatched.any():
        print(f"[ERROR] {unmatched.sum()} rows in blocks did not match any MAZ in maz_with_counties. Example MAZs: {crosswalk.loc[unmatched, 'MAZ'].unique()[:5]}")
    crosswalk.drop(columns=['_merge'], inplace=True)
    # After merge, handle TAZ columns (from both dataframes)
    if 'TAZ_y' in crosswalk.columns:
        crosswalk['TAZ'] = crosswalk['TAZ_y']
        crosswalk.drop(columns=[col for col in ['TAZ_x', 'TAZ_y'] if col in crosswalk.columns], inplace=True)
    elif 'TAZ' not in crosswalk.columns:
        if taz_col in crosswalk.columns:
            crosswalk['TAZ'] = crosswalk[taz_col]
        else:
            raise KeyError(f"Neither 'TAZ' nor '{taz_col}' found in crosswalk columns after merge. Columns: {list(crosswalk.columns)}")
    print(f"[INFO] Merge complete. Final crosswalk columns: {list(crosswalk.columns)}")
except Exception as e:
    print(f"[FATAL] Error during merge: {e}")
    print(f"[DEBUG] blocks columns: {list(blocks.columns)}")
    print(f"[DEBUG] maz_with_counties columns: {list(maz_with_counties.columns)}")
    raise

# --- Finalize columns and output ---
needed_cols = [
    'GEOID_block', 'GEOID_block_group', 'GEOID_tract',
    'MAZ', 'TAZ', 'COUNTY_FIPS', 'COUNTY_NAME', 'PUMA'
]
crosswalk = crosswalk[needed_cols].drop_duplicates()
crosswalk.to_csv(OUTPUT_CROSSWALK, index=False)
print(f"Wrote unified crosswalk: {OUTPUT_CROSSWALK} ({len(crosswalk)} rows)")
