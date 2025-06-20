import os
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

        # Save for future use
        maz_taz_def_df.to_csv(MAZ_TAZ_ALL_GEOG_FILE, index=False)

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
    Create a GEOID column matching NHGIS crosswalk format for the specified geography.
    """
    df = df.copy()
    geo = geo.lower().replace("_", " ")
    geo_specs = {
        "block":       [("county", 3), ("tract", 6), ("block", 4)],
        "block group": [("county", 3), ("tract", 6), ("block group", 1)],
        "tract":       [("county", 3), ("tract", 6)],
        "county":      [("county", 3)],
    }
    crosswalk_col_map = {
        "block": "blk2020ge",
        "block group": "bg2020ge",
        "tract": "tr2020ge",
        "county": "cty2020ge"
    }
    if geo not in geo_specs:
        raise ValueError(f"Unsupported geography: {geo}")

    state_fips = str(state_fips).zfill(2)
    parts = [state_fips]
    for col, width in geo_specs[geo]:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame for geography '{geo}'")
        parts.append(df[col].astype(str).str.zfill(width))
    geoid_col = crosswalk_col_map[geo]
    df[geoid_col] = parts[0] + df[geo_specs[geo][0][0]].astype(str).str.zfill(geo_specs[geo][0][1])
    for i, (col, width) in enumerate(geo_specs[geo][1:], start=1):
        df[geoid_col] += df[col].astype(str).str.zfill(width)
    return df

def interpolate_est(control_df, geo, target_geo_year, source_geo_year):
    """
    Interpolate a control DataFrame from one geography vintage to another,
    using a pre-downloaded NHGIS crosswalk with weights.
    """
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
    if "weight" in cw.columns:
        cw["weight"] = cw["weight"].astype(float)
        weight_col = "weight"
    elif "WEIGHT" in cw.columns:
        cw["WEIGHT"] = cw["WEIGHT"].astype(float)
        weight_col = "WEIGHT"
    else:
        raise ValueError("Crosswalk file missing 'weight' column.")

    print("crosswalk columns:", cw.columns)
    print(cw.head())

    control_df_reset = control_df.reset_index()
    # Rename columns if they are integers (from MultiIndex)
    if set([0, 1, 2, 3]).issubset(control_df_reset.columns):
        control_df_reset = control_df_reset.rename(columns={
            0: 'state',
            1: 'county',
            2: 'tract',
            3: 'block'
        })

    # Add correct GEOID column to control_df
    control_df_with_geoid = make_geoid_column(control_df_reset.reset_index(), geo=geo_key)

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

    return result