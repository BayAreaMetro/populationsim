#!/usr/bin/env python3

"""
Minimal version of create_baseyear_controls_23_tm2.py that processes only a few working controls to verify output writing.
"""

import pandas as pd
import os
import sys
import logging
import collections

# Add tm2_control_utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tm2_control_utils'))

from config import *
from controls import *
from census_fetcher import CensusFetcher

def prepare_geography_dfs():
    """Load geography crosswalks and definitions"""
    from create_baseyear_controls_23_tm2 import prepare_geography_dfs as orig_prepare
    return orig_prepare()

def process_control(control_geo, control_name, control_def, cf, maz_taz_def_df, crosswalk_df, temp_controls, final_control_dfs):
    """Process a single control"""
    from create_baseyear_controls_23_tm2 import process_control as orig_process
    return orig_process(control_geo, control_name, control_def, cf, maz_taz_def_df, crosswalk_df, temp_controls, final_control_dfs)

def write_outputs(control_geo, out_df, crosswalk_df):
    """Write outputs"""
    from create_baseyear_controls_23_tm2 import write_outputs as orig_write
    return orig_write(control_geo, out_df, crosswalk_df)

def main():
    pd.set_option("display.width", 500)
    pd.set_option("display.float_format", "{:,.2f}".format)

    LOG_FILE = f"create_baseyear_controls_{ACS_EST_YEAR}_minimal.log"

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
    cf = CensusFetcher() 
    final_control_dfs = {}

    # Only process MAZ controls, and only the first few that work
    working_controls = collections.OrderedDict([
        ('temp_base_num_hh_b',    ('pl',  CENSUS_EST_YEAR, 'H1_002N',       'block', [])),
        ('temp_base_num_hh_bg',   ('pl',  CENSUS_EST_YEAR, 'H1_002N',       'block group', [])),
        ('temp_num_hh_bg_to_b',   ('acs5', ACS_EST_YEAR,    'B11016',       'block group',
                                   [collections.OrderedDict([('pers_min',1),('pers_max',NPER_MAX)])],
                                   'temp_base_num_hh_b','temp_base_num_hh_bg')),
        # Add a simple final control to test output writing
        ('num_hh',                ('pl',  CENSUS_EST_YEAR, 'H1_002N',       'block', [])),
    ])
    
    control_geo = 'MAZ'
    temp_controls = collections.OrderedDict()
    
    for control_name, control_def in working_controls.items():
        logger.info(f"Processing control {control_name}")
        try:
            process_control(
                control_geo, control_name, control_def,
                cf, maz_taz_def_df, crosswalk_df, temp_controls, final_control_dfs
            )
            logger.info(f"Successfully processed control {control_name}")
        except Exception as e:
            logger.error(f"Failed to process control {control_name}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            break

    if control_geo in final_control_dfs:
        logger.info(f"Preparing final controls files for {control_geo}")
        out_df = final_control_dfs[control_geo].copy()
        write_outputs(control_geo, out_df, crosswalk_df)
        logger.info(f"Successfully wrote outputs for {control_geo}")
    else:
        logger.warning(f"No final controls found for {control_geo}")
        logger.info(f"Available temp controls: {list(temp_controls.keys())}")
        logger.info(f"Available final control geographies: {list(final_control_dfs.keys())}")

    # Write crosswalk files
    for hh_gq in [HOUSEHOLDS_DIR, GROUP_QUARTERS_DIR]:
        crosswalk_file = os.path.join(hh_gq, DATA_SUBDIR, GEO_CROSSWALK_FILE)
        crosswalk_df.to_csv(crosswalk_file, index=False)
        logger.info(f"Wrote geographic cross walk file {crosswalk_file}")

if __name__ == '__main__':
    main()
