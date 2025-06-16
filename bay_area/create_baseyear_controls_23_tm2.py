USAGE = """
Create baseyear controls for MTC Bay Area populationsim.

This script does the following:

1) Downloads the relevant 2020 Census tables to a local cache specified by CensusFetcher.LOCAL_CACHE_FOLDER,
   one table per file in CSV format. These files are the raw tables at a census geography appropriate
   for the control geographies in this script, although the column headers have additional variables
   that are more descriptive of what the columns mean.

   To re-download the data using the Census API, remove the cache file.

2) Translates 2020 Census estimates to 2010 Census geographies, which were used to create the MTC model geographies.

3) Combines the columns in the Census tables to match the control definitions in the CONTROLS structure.

4) Transforms the control tables from the Census geographies to the desired control geography using the MAZ_TAZ_DEF_FILE.
   The Census geographies and model geographies are many to many, so we have to handle the percent of each census geography
   that falls into each model geography and vice versa.

5) Creates a simple file, output_[model_year]/maz_data_hh_pop.csv with 3 columns:
   MAZ,hh,tot_pop for use in the maz_data.csv that will be consistent with these controls, where
   these "hh" include the 1-person group quarters households and the tot_pop includes both household
   and group quarter persons.

6) Joins the MAZs and TAZs to the 2020 PUMAs and saves these crosswalks as well.

   Outputs:
       households    /data/[model_year]_[maz,taz,county]_controls.csv
       households    /data/geo_cross_walk.csv
       group_quarters/data/[model_year]_maz_controls.csv
       group_quarters/data/geo_cross_walk.csv
       output_[model_year]/maz_data_hh_pop.csv
       create_baseyear_controls_[model_year].log
"""

import argparse
import collections
import logging
import os
import sys
import numpy
import pandas as pd

from tm2_control_utils.config import *
from tm2_control_utils.census_fetcher import CensusFetcher
from tm2_control_utils.geog_utils import prepare_geography_dfs, add_aggregate_geography_colums, fetch_nhgis_crosswalk, interpolate_est
from tm2_control_utils.controls import create_control_table, census_col_is_in_control, match_control_to_geography, integerize_control


def process_control(
    control_geo, control_name, control_def, cf, maz_taz_def_df, crosswalk_df, temp_controls, final_control_dfs
):
    logger = logging.getLogger()
    logger.info(f"Creating control [{control_name}] for geography [{control_geo}]")
    logger.info("=" * 80)

    # Special case for REGION/gq_num_hh_region
    if control_geo == "REGION" and control_name == "gq_num_hh_region":
        final_control_dfs[control_geo] = pd.DataFrame.from_dict(
            data={'REGION': [1], "gq_num_hh_region": [final_control_dfs["MAZ"]["gq_num_hh"].sum()]}
        ).set_index("REGION")
        logger.debug(f"\n{final_control_dfs[control_geo]}")
        return
    
    print("dataset:", control_def[0])
    print("year:", control_def[1])
    print("table:", control_def[2])
    print("geo:", control_def[3])
    # Step 1: Fetch census data
    census_table_df = cf.get_census_data(
        dataset=control_def[0],
        year=control_def[1],
        table=control_def[2],
        geo=control_def[3]
    )

    # Step 2: Create control table
    control_table_df = create_control_table(control_name, control_def[4], control_def[2], census_table_df)

    # Step 3: Interpolate if needed
    if CENSUS_GEOG_YEAR != CENSUS_EST_YEAR:
        control_table_df = interpolate_est(
            control_table_df,
            dataset=control_def[0],
            year=control_def[1],
            table=control_def[2],
            geo=control_def[3],
            target_geo_year=CENSUS_GEOG_YEAR,
            source_geo_year=CENSUS_EST_YEAR,
            crosswalk_dir=LOCAL_CACHE_FOLDER,
            api_key=IPUMS_API_KEY_FILE
        )

    # Step 4: Prepare scaling and subtraction
    scale_numerator = control_def[5] if len(control_def) > 5 else None
    scale_denominator = control_def[6] if len(control_def) > 6 else None
    subtract_table = control_def[7] if len(control_def) > 7 else None

    # Step 5: Match control to geography
    final_df = match_control_to_geography(
        control_name, control_table_df, control_geo, control_def[3],
        maz_taz_def_df, temp_controls,
        scale_numerator=scale_numerator, scale_denominator=scale_denominator,
        subtract_table=subtract_table
    )

    # Step 6: Handle temp controls
    if control_name.startswith("temp_"):
        temp_controls[control_name] = final_df
        return

    # Step 7: Integerize if needed
    if control_name in ["num_hh", "gq_num_hh", "tot_pop"]:
        final_df = integerize_control(final_df, crosswalk_df, control_name)

    # Step 8: Merge into final_control_dfs
    if control_geo not in final_control_dfs:
        final_control_dfs[control_geo] = final_df
    else:
        final_control_dfs[control_geo] = pd.merge(
            left=final_control_dfs[control_geo],
            right=final_df,
            how="left",
            left_index=True,
            right_index=True
        )


def write_outputs(control_geo, out_df, crosswalk_df):
    logger = logging.getLogger()
    out_df.reset_index(drop=False, inplace=True)

    if len(out_df.loc[out_df[control_geo] == 0]) > 0:
        logger.info(f"Dropping {control_geo}=0\n{out_df.loc[out_df[control_geo] == 0, :].T.squeeze()}")
        out_df = out_df.loc[out_df[control_geo] > 0, :]

    if control_geo == "COUNTY":
        out_df = pd.merge(left=COUNTY_RECODE[["COUNTY", "county_name"]], right=out_df, how="right")
    elif control_geo == "MAZ":
        maz_df = out_df[["MAZ", "num_hh", "gq_num_hh", "tot_pop"]].copy()
        maz_df["hh"] = maz_df["num_hh"] + maz_df["gq_num_hh"]
        maz_df["pop_minus_hh"] = maz_df["tot_pop"] - maz_df["hh"]
        maz_df.loc[maz_df["pop_minus_hh"] >= 0, "pop_minus_hh"] = 0
        logger.info(f"pop_minus_hh.sum: {maz_df['pop_minus_hh'].sum()}")
        logger.info(f"pop_minus_hh < 0 :\n{maz_df.loc[maz_df['pop_minus_hh'] < 0]}")
        maz_df.loc[maz_df["pop_minus_hh"] < 0, "tot_pop"] = maz_df["hh"]
        maz_df = maz_df[["MAZ", "hh", "tot_pop"]]
        maz_hh_pop_file = os.path.join(OUTPUT_DIR_FMT.format(ACS_EST_YEAR), MAZ_HH_POP_FILE)
        maz_df.to_csv(maz_hh_pop_file, index=False)
        logger.info(f"Wrote {maz_hh_pop_file}")

    hh_control_names = []
    gq_control_names = []
    for control_name in list(out_df.columns):
        if control_name == control_geo:
            continue
        if control_name.startswith("gq_"):
            gq_control_names.append(control_name)
        else:
            hh_control_names.append(control_name)

    if hh_control_names:
        hh_control_df = out_df[[control_geo] + hh_control_names]
        hh_control_file = os.path.join(HOUSEHOLDS_DIR, DATA_SUBDIR, CONTROL_FILE_FMT.format(ACS_EST_YEAR, control_geo))
        hh_control_df.to_csv(hh_control_file, index=False, float_format="%.5f")
        logger.info(f"Wrote control file {hh_control_file}")

    if gq_control_names:
        gq_control_df = out_df[[control_geo] + gq_control_names]
        gq_control_file = os.path.join(GROUP_QUARTERS_DIR, DATA_SUBDIR, CONTROL_FILE_FMT.format(ACS_EST_YEAR, control_geo))
        gq_control_df.to_csv(gq_control_file, index=False, float_format="%.5f")
        logger.info(f"Wrote control file {gq_control_file}")


def main():
    pd.set_option("display.width", 500)
    pd.set_option("display.float_format", "{:,.2f}".format)

    LOG_FILE = f"create_baseyear_controls_{ACS_EST_YEAR}.log"

    # create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
    logger.addHandler(ch)
    fh = logging.FileHandler(LOG_FILE, mode='w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
    logger.addHandler(fh)

    logger.info("Preparing geography lookups")
    maz_taz_def_df, crosswalk_df = prepare_geography_dfs()
    for src_year, tgt_year, geo in REQUIRED_CROSSWALKS:
        if src_year == tgt_year:
            print(f"Skipping crosswalk for {src_year} → {tgt_year} at {geo} (years are the same).")
            continue
        try:
            print(f"Fetching crosswalk: {src_year} → {tgt_year} at {geo} level...")
            fetch_nhgis_crosswalk(
                source_year=src_year,
                target_year=tgt_year,
                geography=geo,
                download_dir=LOCAL_CACHE_FOLDER,
                api_key=IPUMS_API_KEY_FILE
            )
        except Exception as e:
            print(f"Failed to fetch crosswalk for {src_year} → {tgt_year} at {geo}: {e}")

    cf = CensusFetcher() 
    final_control_dfs = {}

    #for control_geo, control_dict in CONTROLS[ACS_EST_YEAR].items():
    for control_geo, control_dict in list(CONTROLS[ACS_EST_YEAR].items())[:1]:
        temp_controls = collections.OrderedDict()
        for control_name, control_def in control_dict.items():
            process_control(
                control_geo, control_name, control_def,
                cf, maz_taz_def_df, crosswalk_df, temp_controls, final_control_dfs
            )

        logger.info(f"Preparing final controls files for {control_geo}")
        out_df = final_control_dfs[control_geo].copy()
        write_outputs(control_geo, out_df, crosswalk_df)

    for hh_gq in [HOUSEHOLDS_DIR, GROUP_QUARTERS_DIR]:
        crosswalk_file = os.path.join(hh_gq, DATA_SUBDIR, GEO_CROSSWALK_FILE)
        crosswalk_df.to_csv(crosswalk_file, index=False)
        logger.info(f"Wrote geographic cross walk file {crosswalk_file}")


if __name__ == '__main__':

    main()
