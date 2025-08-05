#!/usr/bin/env python3
"""
Create the geo_cross_walk_tm2_updated.csv file needed for control generation.
This file contains MAZ-TAZ-PUMA-County mappings with 2020 PUMA definitions.
"""

import pandas as pd
import sys
import os

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tm2_control_utils.config import (
    MAZ_TAZ_ALL_GEOG_FILE, MAZ_TAZ_DEF_FILE, 
    PRIMARY_OUTPUT_DIR, GEO_CROSSWALK_TM2_FILE,
    COUNTY_RECODE
)
from tm2_control_utils.geog_utils import add_aggregate_geography_colums

def create_crosswalk_file():
    """Create the updated crosswalk file with 2020 PUMA definitions."""
    
    print("Creating geo_cross_walk_tm2_updated.csv file...")
    
    # Load MAZ/TAZ definitions
    if os.path.exists(MAZ_TAZ_ALL_GEOG_FILE):
        print(f"Using MAZ/TAZ all geography file: {MAZ_TAZ_ALL_GEOG_FILE}")
        maz_taz_df = pd.read_csv(MAZ_TAZ_ALL_GEOG_FILE)
    else:
        print(f"Using basic MAZ/TAZ definitions: {MAZ_TAZ_DEF_FILE}")
        maz_taz_df = pd.read_csv(MAZ_TAZ_DEF_FILE)
        maz_taz_df.rename(columns={"maz": "MAZ", "taz": "TAZ"}, inplace=True)
        maz_taz_df["GEOID_block"] = "0" + maz_taz_df["GEOID10"].astype(str)
        add_aggregate_geography_colums(maz_taz_df)
        maz_taz_df.drop("GEOID10", axis="columns", inplace=True)
        maz_taz_df = pd.merge(left=maz_taz_df, right=COUNTY_RECODE, how="left")

    print(f"Loaded {len(maz_taz_df)} MAZ records")
    
    # Ensure required columns exist
    required_cols = ['MAZ', 'TAZ', 'PUMA', 'COUNTY', 'county_name']
    missing_cols = [col for col in required_cols if col not in maz_taz_df.columns]
    
    if missing_cols:
        print(f"Missing columns: {missing_cols}")
        print(f"Available columns: {list(maz_taz_df.columns)}")
        
        # Add county_name if missing
        if 'county_name' in missing_cols and 'COUNTY' in maz_taz_df.columns:
            county_mapping = {
                1: "San Francisco",
                2: "San Mateo", 
                3: "Santa Clara",
                4: "Alameda",
                5: "Contra Costa",
                6: "Solano",
                7: "Napa",
                8: "Sonoma",
                9: "Marin"
            }
            maz_taz_df['county_name'] = maz_taz_df['COUNTY'].map(county_mapping)
    
    # Select and clean the crosswalk data
    crosswalk_cols = [col for col in required_cols if col in maz_taz_df.columns]
    crosswalk_df = maz_taz_df[crosswalk_cols].copy()
    
    # Ensure PUMA is properly typed and filter out missing values
    crosswalk_df["PUMA"] = crosswalk_df["PUMA"].astype("Int64")
    crosswalk_df = crosswalk_df[crosswalk_df["PUMA"].notna()]
    
    print(f"Final crosswalk: {len(crosswalk_df)} records")
    print(f"Unique PUMAs: {sorted(crosswalk_df['PUMA'].dropna().unique())}")
    print(f"Unique Counties: {sorted(crosswalk_df['county_name'].unique())}")
    
    # Create output directory if needed
    os.makedirs(PRIMARY_OUTPUT_DIR, exist_ok=True)
    
    # Save the crosswalk file
    output_path = os.path.join(PRIMARY_OUTPUT_DIR, GEO_CROSSWALK_TM2_FILE)
    crosswalk_df.to_csv(output_path, index=False)
    
    print(f"✅ Created crosswalk file: {output_path}")
    print(f"   Records: {len(crosswalk_df)}")
    print(f"   Columns: {list(crosswalk_df.columns)}")
    
    return output_path

if __name__ == "__main__":
    create_crosswalk_file()
