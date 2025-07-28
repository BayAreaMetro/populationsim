import os
import logging
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
from tm2_control_utils.config import *


def prepare_geography_dfs():
    """
    Reads and prepares MAZ/TAZ definition and crosswalk DataFrames.
    Uses the updated geo_cross_walk_tm2_updated.csv file with 2020 PUMA definitions.
    Returns:
        maz_taz_def_df: DataFrame with MAZ/TAZ definitions and attributes.
        crosswalk_df:   DataFrame with MAZ/TAZ/PUMA/COUNTY crosswalk.
    """
    logger = logging.getLogger(__name__)
    
    # Check if the updated crosswalk file exists in the output directory
    # Since GEO_CROSSWALK_TM2_FILE is just the filename, we need to construct the full path
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output_2023')
    updated_crosswalk_path = os.path.join(output_dir, GEO_CROSSWALK_TM2_FILE)
    
    if os.path.exists(updated_crosswalk_path):
        logger.info(f"Using updated crosswalk file with 2020 PUMA definitions: {updated_crosswalk_path}")
        crosswalk_df = pd.read_csv(updated_crosswalk_path)
        
        # Load MAZ/TAZ definitions
        if os.path.exists(MAZ_TAZ_ALL_GEOG_FILE):
            maz_taz_def_df = pd.read_csv(MAZ_TAZ_ALL_GEOG_FILE)
        else:
            maz_taz_def_df = pd.read_csv(MAZ_TAZ_DEF_FILE)
            maz_taz_def_df.rename(columns={"maz": "MAZ", "taz": "TAZ"}, inplace=True)
            maz_taz_def_df["GEOID_block"] = "0" + maz_taz_def_df["GEOID10"].astype(str)
            add_aggregate_geography_colums(maz_taz_def_df)
            maz_taz_def_df.drop("GEOID10", axis="columns", inplace=True)
            maz_taz_def_df = pd.merge(left=maz_taz_def_df, right=COUNTY_RECODE, how="left")
        
        # Merge with updated crosswalk to get 2020 PUMA definitions
        maz_taz_def_df = pd.merge(
            left=maz_taz_def_df,
            right=crosswalk_df[["MAZ", "TAZ", "PUMA", "COUNTY", "county_name"]],
            on=["MAZ", "TAZ"],
            how="left",
            suffixes=('_def', '_crosswalk')
        )
        
        # Use crosswalk PUMA values (2020 definitions) over original PUMA values
        if 'PUMA_crosswalk' in maz_taz_def_df.columns:
            maz_taz_def_df['PUMA'] = maz_taz_def_df['PUMA_crosswalk']
            maz_taz_def_df.drop(['PUMA_crosswalk'], axis=1, inplace=True)
        
        if 'COUNTY_crosswalk' in maz_taz_def_df.columns:
            maz_taz_def_df['COUNTY'] = maz_taz_def_df['COUNTY_crosswalk'] 
            maz_taz_def_df.drop(['COUNTY_crosswalk'], axis=1, inplace=True)
            
        if 'county_name_crosswalk' in maz_taz_def_df.columns:
            maz_taz_def_df['county_name'] = maz_taz_def_df['county_name_crosswalk']
            maz_taz_def_df.drop(['county_name_crosswalk'], axis=1, inplace=True)
        
        # Ensure PUMA is properly typed and filter out missing values
        maz_taz_def_df["PUMA"] = maz_taz_def_df["PUMA"].astype("Int64")
        maz_taz_def_df = maz_taz_def_df[maz_taz_def_df["PUMA"].notna()]
        
        logger.info(f"Loaded {len(maz_taz_def_df)} MAZ records with updated 2020 PUMA definitions")
        logger.info(f"Unique PUMAs in dataset: {sorted(maz_taz_def_df['PUMA'].dropna().unique())}")
        
    else:
        # Updated crosswalk file is required for 2020 PUMA definitions
        logger.error(f"Updated crosswalk file required but not found at {updated_crosswalk_path}")
        logger.error("The static PUMA file process has been deprecated to ensure 2020 PUMA definitions are used")
        logger.error("Please ensure the updated crosswalk file is available in the output directory")
        raise FileNotFoundError(
            f"Required updated crosswalk file not found: {updated_crosswalk_path}\n"
            "This file contains the 2020 PUMA definitions including PUMA 07707.\n"
            "The old static PUMA file process has been deprecated to avoid using outdated 2010 PUMA definitions."
        )

    # Ensure crosswalk has consistent structure
    if 'REGION' not in crosswalk_df.columns and 'REGION' in maz_taz_def_df.columns:
        # Add REGION to crosswalk if available in maz_taz_def_df
        region_map = maz_taz_def_df[['MAZ', 'REGION']].drop_duplicates()
        crosswalk_df = crosswalk_df.merge(region_map, on='MAZ', how='left')
    
    # Final crosswalk structure
    available_cols = [col for col in ["MAZ", "TAZ", "PUMA", "COUNTY", "county_name", "REGION"] if col in crosswalk_df.columns]
    crosswalk_df = crosswalk_df[available_cols].drop_duplicates()
    crosswalk_df.sort_values(by="MAZ", inplace=True)

    return maz_taz_def_df, crosswalk_df



def add_aggregate_geography_colums(table_df):
    """
    Given a table with column GEOID_block, creates columns for GEOID_[county,tract,block group]
    """
    if "GEOID_block" in table_df.columns:
        table_df["GEOID_county"     ] = table_df["GEOID_block"].str[:5 ]
        table_df["GEOID_tract"      ] = table_df["GEOID_block"].str[:11]
        table_df["GEOID_block group"] = table_df["GEOID_block"].str[:12]

def make_geoid_column(df, geo, state_fips='06'):
    """
    Robustly create or use a GEOID column for the specified geography.
    If a suitable GEOID column already exists, use it. Otherwise, try to build from components.
    """
    df = df.copy()
    geo = geo.lower().replace("_", " ")
    crosswalk_col_map = {
        "block": "blk2020ge",
        "block group": "bg2020ge",
        "tract": "tr2020ge",
        "county": "cty2020ge"
    }
    # Use existing GEOID column if present
    geoid_col = crosswalk_col_map.get(geo)
    # Try all reasonable alternatives for GEOID columns
    alt_cols = [
        geoid_col,
        f"GEOID_{geo}",
        "GEOID",
        geo.replace(" ", "") + "2020ge",
        geo.replace(" ", "_") + "2020ge",
        geo.replace(" ", "").upper() + "2020GE"
    ]
    for alt in alt_cols:
        if alt and alt in df.columns:
            df[geoid_col] = df[alt]
            return df
    # Otherwise, try to build from components
    geo_specs = {
        "block":       [("state", 2), ("county", 3), ("tract", 6), ("block", 4)],
        "block group": [("state", 2), ("county", 3), ("tract", 6), ("block group", 1)],
        "tract":       [("state", 2), ("county", 3), ("tract", 6)],
        "county":      [("state", 2), ("county", 3)],
    }
    if geo not in geo_specs:
        raise ValueError(f"Unsupported geography: {geo}")
    
    # Check if required columns exist
    missing_cols = []
    for col, _ in geo_specs[geo]:
        if col not in df.columns:
            missing_cols.append(col)
    
    # If columns are missing, handle special cases
    if missing_cols:
        # Special case: For files with incorrect geography headers (like C24010 occupation data), 
        # try to reconstruct from index if we're dealing with tract-level data
        if geo == 'tract' and 'index' in df.columns:
            logger = logging.getLogger(__name__)
            logger.warning(f"Geography columns {missing_cols} missing for '{geo}', creating placeholder GEOID from index")
            # Create a simple GEOID based on index - this is a fallback for occupation data
            # We'll use California state code (06) + Alameda County (001) + incrementing tract numbers
            df[geoid_col] = state_fips + '001' + df['index'].astype(str).str.zfill(6)
            return df
        else:
            raise ValueError(f"Column '{missing_cols[0]}' not found in DataFrame for geography '{geo}' and no suitable GEOID column present.")
    
    # Build GEOID from components
    parts = [df[col].astype(str).str.zfill(width) for col, width in geo_specs[geo]]
    df[geoid_col] = parts[0].str.cat(parts[1:], sep='') if len(parts) > 1 else parts[0]
    return df

def interpolate_est(control_df, geo, target_geo_year, source_geo_year):
    logger = logging.getLogger()
    logger.info(f"GEOGRAPHIC INTERPOLATION START: {geo} from {source_geo_year} to {target_geo_year}")
    logger.info(f"Input control data: {len(control_df)} rows, columns: {list(control_df.columns)}")
    
    # Calculate input totals for comparison
    numeric_cols = [col for col in control_df.columns if pd.api.types.is_numeric_dtype(control_df[col])]
    input_totals = {col: control_df[col].sum() for col in numeric_cols}
    logger.info(f"Input totals: {input_totals}")
    
    print(f"[DEBUG] ENTER interpolate_est: geo={geo}")
    print(f"[DEBUG] control_df.columns: {list(control_df.columns)}")
    print(f"[DEBUG] control_df.head():\n{control_df.head()}")
    geo_key = geo.lower().replace("_", " ")
    crosswalk_col_map = {
        "block": "blk2020ge",
        "block group": "bg2020ge",
        "tract": "tr2020ge",
        "county": "cty2020ge"
    }
    crosswalk_path = NHGIS_CROSSWALK_PATHS.get((geo_key, source_geo_year, target_geo_year))
    logger.info(f"Using crosswalk file: {crosswalk_path}")
    
    if not crosswalk_path or not os.path.exists(crosswalk_path):
        logger.error(f"NHGIS crosswalk file not found: {crosswalk_path}")
        raise FileNotFoundError(
            f"Required NHGIS crosswalk file not found for {geo_key} {source_geo_year}->{target_geo_year}.\n"
            f"Expected at: {crosswalk_path}\n"
            "Please download the appropriate NHGIS crosswalk and place it in the configured directory."
        )

    # Load crosswalk
    logger.info(f"Loading crosswalk file with {geo_key} geography mapping")
    cw = pd.read_csv(crosswalk_path, dtype=str)
    logger.info(f"Crosswalk loaded: {len(cw)} rows, {len(cw.columns)} columns")
    
    # Make column names robust: strip and lowercase
    cw.columns = cw.columns.str.strip().str.lower()
    logger.info(f"Crosswalk columns: {list(cw.columns)}")
    print("crosswalk columns (repr):", repr(cw.columns.tolist()))

    # Determine weight column
    weight_col = None
    # Map for each geo type to the correct weight column(s)
    # Modified to always prefer household weights (wt_hh) for all geography levels
    # Note: Block-level NHGIS crosswalks only have 'weight' column, so will fall back to that
    geo_weight_map = {
        "block": ["wt_hh", "weight"],  # Will use "weight" since wt_hh not available in block crosswalks
        "block group": ["wt_hh", "wt_pop", "wt_hu", "wt_fam", "wt_adult", "wt_ownhu", "wt_renthu"],
        "tract": ["wt_hh", "wt_pop", "wt_hu", "wt_fam", "wt_adult", "wt_ownhu", "wt_renthu"],
        "county": ["wt_hh", "wt_pop", "wt_hu", "wt_fam", "wt_adult", "wt_ownhu", "wt_renthu"]
    }
    # Simplified logic: always use the first available weight column (now wt_hh is first for all levels)
    data_col = [c for c in control_df.columns if c != 'index'][0]
    logger.info(f"Primary data column identified: {data_col}")
    
    # Pick the first available weight column from the ordered list
    for candidate in geo_weight_map.get(geo_key, []):
        if candidate in cw.columns:
            weight_col = candidate
            logger.info(f"Selected weight column '{weight_col}' (prioritizing household weights)")
            break
    
    if not weight_col:
        logger.error(f"No appropriate weight column found in crosswalk for {geo_key}")
        raise ValueError(f"Crosswalk file missing appropriate weight column for {geo_key}. Columns: {cw.columns.tolist()}")
    
    cw[weight_col] = cw[weight_col].astype(float)
    logger.info(f"Weight column statistics: min={cw[weight_col].min():.6f}, max={cw[weight_col].max():.6f}, mean={cw[weight_col].mean():.6f}")

    print("crosswalk columns:", cw.columns)
    print(cw.head())

    control_df_reset = control_df.reset_index()
    logger.info(f"Preparing control data for merge: {len(control_df_reset)} rows")
    print(f"[DEBUG] Columns after reset_index: {control_df_reset.columns.tolist()}")
    print(f"[DEBUG] Head after reset_index:\n{control_df_reset.head()}")
    
    # Robustly rename columns for block and block group geographies
    if geo_key == "block" and set([0, 1, 2, 3]).issubset(control_df_reset.columns):
        control_df_reset = control_df_reset.rename(columns={
            0: 'state',
            1: 'county',
            2: 'tract',
            3: 'block'
        })
        logger.info(f"Renamed numeric columns for block geography: {control_df_reset.columns.tolist()}")
        print(f"[DEBUG] Renamed columns for block: {control_df_reset.columns.tolist()}")
    elif geo_key == "block group" and set([0, 1, 2, 3]).issubset(control_df_reset.columns):
        control_df_reset = control_df_reset.rename(columns={
            0: 'state',
            1: 'county',
            2: 'tract',
            3: 'block group'
        })
        logger.info(f"Renamed numeric columns for block group geography: {control_df_reset.columns.tolist()}")
        print(f"[DEBUG] Renamed columns for block group: {control_df_reset.columns.tolist()}")
    
    print(f"[DEBUG] Columns before make_geoid_column: {control_df_reset.columns.tolist()}")
    print(f"[DEBUG] Head before make_geoid_column:\n{control_df_reset.head()}")
    
    # Add correct GEOID column to control_df
    logger.info(f"Creating GEOID column for {geo_key} geography")
    control_df_with_geoid = make_geoid_column(control_df_reset, geo=geo_key)
    logger.info(f"GEOID column created successfully: {list(control_df_with_geoid.columns)}")
    print(f"[DEBUG] Columns after make_geoid_column: {control_df_with_geoid.columns.tolist()}")
    print(f"[DEBUG] Head after make_geoid_column:\n{control_df_with_geoid.head()}")

    src_col = crosswalk_col_map[geo_key]
    if src_col not in control_df_with_geoid.columns:
        logger.error(f"Required source column '{src_col}' not found for merging")
        raise ValueError(f"Column '{src_col}' not found in control_df for merging.")

    # Merge & weight
    logger.info(f"Merging control data with crosswalk on column '{src_col}'")
    df = control_df_with_geoid.copy()
    df[src_col] = df[src_col].astype(str)
    
    # Log merge statistics
    before_merge_count = len(df)
    unique_source_geoids = df[src_col].nunique()
    unique_crosswalk_geoids = cw[src_col].nunique()
    logger.info(f"Merge preparation: {before_merge_count} control records, {unique_source_geoids} unique source GEOIDs")
    logger.info(f"Crosswalk contains {unique_crosswalk_geoids} unique source GEOIDs")
    
    merged = df.merge(cw, left_on=src_col, right_on=src_col, how="inner")
    after_merge_count = len(merged)
    logger.info(f"Merge completed: {after_merge_count} records after merge ({after_merge_count/before_merge_count*100:.1f}% match rate)")
    
    if after_merge_count == 0:
        logger.error("No records matched in merge - check GEOID formats and geography alignment")
        raise ValueError("No records found after merging with crosswalk")

    # Apply weights to numeric columns
    data_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != src_col]
    logger.info(f"Applying areal interpolation weights to {len(data_cols)} data columns: {data_cols}")
    
    for col in data_cols:
        original_total = merged[col].sum()
        merged[col] = merged[col] * merged[weight_col]
        weighted_total = merged[col].sum()
        logger.info(f"Column '{col}': original total = {original_total:,.0f}, weighted total = {weighted_total:,.0f}")

    # Aggregate to target geography
    target_col = [col for col in cw.columns if col.endswith(f"{target_geo_year}ge")][0]
    logger.info(f"Aggregating to target geography using column '{target_col}'")
    
    # Count unique target geographies before aggregation
    unique_targets = merged[target_col].nunique()
    logger.info(f"Aggregating {len(merged)} records to {unique_targets} target geographies")
    
    result = (merged
              .groupby(target_col)[data_cols]
              .sum()
              .reset_index()
              .rename(columns={target_col: src_col}))

    # Calculate output totals for comparison
    output_totals = {col: result[col].sum() for col in data_cols}
    logger.info(f"Output totals: {output_totals}")
    
    # Log conservation check
    for col in data_cols:
        input_total = input_totals.get(col, 0)
        output_total = output_totals.get(col, 0)
        if input_total > 0:
            conservation_rate = output_total / input_total
            logger.info(f"Conservation check '{col}': {conservation_rate:.4f} ({output_total:,.0f}/{input_total:,.0f})")
            if abs(conservation_rate - 1.0) > 0.01:  # More than 1% difference
                logger.warning(f"Significant total change in '{col}' during interpolation: {conservation_rate:.4f}")
    
    logger.info(f"GEOGRAPHIC INTERPOLATION COMPLETE: {len(result)} output geographies")

    print(f"[DEBUG] EXIT interpolate_est: merged.columns: {merged.columns.tolist()}")
    print(f"[DEBUG] merged.head():\n{merged.head()}")
    return result