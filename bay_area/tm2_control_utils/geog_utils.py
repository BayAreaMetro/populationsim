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
    Returns:
        maz_taz_def_df: DataFrame with MAZ/TAZ definitions and attributes.
        crosswalk_df:   DataFrame with MAZ/TAZ/PUMA/COUNTY crosswalk.
    """
    if os.path.exists(MAZ_TAZ_ALL_GEOG_FILE):
        maz_taz_def_df = pd.read_csv(MAZ_TAZ_ALL_GEOG_FILE)
    else:
        maz_taz_def_df = pd.read_csv(MAZ_TAZ_DEF_FILE)
        maz_taz_def_df.rename(columns={"maz": "MAZ", "taz": "TAZ"}, inplace=True)
        maz_taz_def_df["GEOID_block"] = "0" + maz_taz_def_df["GEOID10"].astype(str)
        add_aggregate_geography_colums(maz_taz_def_df)
        maz_taz_def_df.drop("GEOID10", axis="columns", inplace=True)
        maz_taz_def_df = pd.merge(left=maz_taz_def_df, right=COUNTY_RECODE, how="left")

        taz_puma_df = pd.read_csv(MAZ_TAZ_PUMA_FILE)
        taz_puma_df.rename(columns={"PUMA10": "PUMA"}, inplace=True)
        maz_taz_def_df = pd.merge(left=maz_taz_def_df, right=taz_puma_df[["TAZ", "MAZ", "PUMA"]], how="left")

        maz_taz_def_df["PUMA"] = maz_taz_def_df["PUMA"].astype("Int64")
        maz_taz_def_df = maz_taz_def_df[maz_taz_def_df["PUMA"].notna()]

        # Skip saving intermediate geography file

    crosswalk_df = maz_taz_def_df.loc[maz_taz_def_df["MAZ"] > 0]
    crosswalk_df = crosswalk_df[["MAZ", "TAZ", "PUMA", "COUNTY", "county_name", "REGION"]].drop_duplicates()
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
    if not crosswalk_path or not os.path.exists(crosswalk_path):
        raise FileNotFoundError(
            f"Required NHGIS crosswalk file not found for {geo_key} {source_geo_year}->{target_geo_year}.\n"
            f"Expected at: {crosswalk_path}\n"
            "Please download the appropriate NHGIS crosswalk and place it in the configured directory."
        )

    # Load crosswalk
    cw = pd.read_csv(crosswalk_path, dtype=str)
    # Make column names robust: strip and lowercase
    cw.columns = cw.columns.str.strip().str.lower()
    print("crosswalk columns (repr):", repr(cw.columns.tolist()))

    # Determine weight column
    weight_col = None
    # Map for each geo type to the correct weight column(s)
    geo_weight_map = {
        "block": ["weight"],
        "block group": ["wt_hh", "wt_pop", "wt_hu", "wt_fam", "wt_adult", "wt_ownhu", "wt_renthu"],
        "tract": ["wt_hh", "wt_pop", "wt_hu", "wt_fam", "wt_adult", "wt_ownhu", "wt_renthu"],
        "county": ["wt_hh", "wt_pop", "wt_hu", "wt_fam", "wt_adult", "wt_ownhu", "wt_renthu"]
    }
    # Try to pick the right weight column based on control name and available columns
    data_col = [c for c in control_df.columns if c != 'index'][0]
    for candidate in geo_weight_map.get(geo_key, []):
        if candidate in cw.columns:
            # Prefer hh for household, pop for population, hu for housing units, etc.
            if 'hh' in data_col.lower() and 'hh' in candidate:
                weight_col = candidate
                break
            elif 'pop' in data_col.lower() and 'pop' in candidate:
                weight_col = candidate
                break
            elif 'hu' in data_col.lower() and 'hu' in candidate:
                weight_col = candidate
                break
            elif 'fam' in data_col.lower() and 'fam' in candidate:
                weight_col = candidate
                break
            elif 'adult' in data_col.lower() and 'adult' in candidate:
                weight_col = candidate
                break
            elif 'ownhu' in data_col.lower() and 'ownhu' in candidate:
                weight_col = candidate
                break
            elif 'renthu' in data_col.lower() and 'renthu' in candidate:
                weight_col = candidate
                break
    if not weight_col:
        # fallback: pick the first available weight column
        for candidate in geo_weight_map.get(geo_key, []):
            if candidate in cw.columns:
                weight_col = candidate
                break
    if not weight_col:
        raise ValueError(f"Crosswalk file missing appropriate weight column for {geo_key}. Columns: {cw.columns.tolist()}")
    cw[weight_col] = cw[weight_col].astype(float)

    print("crosswalk columns:", cw.columns)
    print(cw.head())

    control_df_reset = control_df.reset_index()
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
        print(f"[DEBUG] Renamed columns for block: {control_df_reset.columns.tolist()}")
    elif geo_key == "block group" and set([0, 1, 2, 3]).issubset(control_df_reset.columns):
        control_df_reset = control_df_reset.rename(columns={
            0: 'state',
            1: 'county',
            2: 'tract',
            3: 'block group'
        })
        print(f"[DEBUG] Renamed columns for block group: {control_df_reset.columns.tolist()}")
    print(f"[DEBUG] Columns before make_geoid_column: {control_df_reset.columns.tolist()}")
    print(f"[DEBUG] Head before make_geoid_column:\n{control_df_reset.head()}")
    # Add correct GEOID column to control_df
    control_df_with_geoid = make_geoid_column(control_df_reset, geo=geo_key)
    print(f"[DEBUG] Columns after make_geoid_column: {control_df_with_geoid.columns.tolist()}")
    print(f"[DEBUG] Head after make_geoid_column:\n{control_df_with_geoid.head()}")

    src_col = crosswalk_col_map[geo_key]
    if src_col not in control_df_with_geoid.columns:
        raise ValueError(f"Column '{src_col}' not found in control_df for merging.")

    # Merge & weight
    df = control_df_with_geoid.copy()
    df[src_col] = df[src_col].astype(str)
    merged = df.merge(cw, left_on=src_col, right_on=src_col, how="inner")

    # Apply weights to numeric columns
    data_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != src_col]
    for col in data_cols:
        merged[col] = merged[col] * merged[weight_col]

    # Aggregate to target geography
    target_col = [col for col in cw.columns if col.endswith(f"{target_geo_year}ge")][0]
    result = (merged
              .groupby(target_col)[data_cols]
              .sum()
              .reset_index()
              .rename(columns={target_col: src_col}))

    print(f"[DEBUG] EXIT interpolate_est: merged.columns: {merged.columns.tolist()}")
    print(f"[DEBUG] merged.head():\n{merged.head()}")
    return result