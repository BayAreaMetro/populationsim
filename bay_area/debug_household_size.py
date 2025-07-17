#!/usr/bin/env python3
"""
Debug household size controls specifically.
This script focuses only on the household size controls to understand why they have identical values.
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
from tm2_control_utils.geog_utils import prepare_geography_dfs, add_aggregate_geography_colums, interpolate_est
from tm2_control_utils.controls import create_control_table, census_col_is_in_control, match_control_to_geography, integerize_control


def debug_household_size_controls():
    """Debug just the household size controls to understand the distribution issue."""
    
    # Set up logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
    logger.addHandler(ch)
    
    logger.info("Starting household size controls debug")
    
    # Prepare geography data
    maz_taz_def_df, crosswalk_df = prepare_geography_dfs()
    cf = CensusFetcher()
    
    # Get temp controls needed for scaling
    temp_controls = collections.OrderedDict()
    
    # First create the temp base controls
    logger.info("Creating temp_base_num_hh_b control")
    temp_base_b_def = ('pl', 2020, 'H1_002N', 'block', [])
    temp_base_b_data = cf.get_census_data(
        dataset=temp_base_b_def[0],
        year=temp_base_b_def[1], 
        table=temp_base_b_def[2],
        geo=temp_base_b_def[3]
    )
    temp_base_b_control = create_control_table('temp_base_num_hh_b', temp_base_b_def[4], temp_base_b_def[2], temp_base_b_data)
    
    # Match to MAZ geography
    temp_base_b_final = match_control_to_geography(
        'temp_base_num_hh_b', temp_base_b_control, 'MAZ', 'block',
        maz_taz_def_df, temp_controls
    )
    temp_controls['temp_base_num_hh_b'] = temp_base_b_final
    
    logger.info("Creating temp_base_num_hh_bg control")
    temp_base_bg_def = ('acs5', 2023, 'B11016', 'block group', [collections.OrderedDict([('pers_min',1),('pers_max',NPER_MAX)])])
    temp_base_bg_data = cf.get_census_data(
        dataset=temp_base_bg_def[0],
        year=temp_base_bg_def[1],
        table=temp_base_bg_def[2], 
        geo=temp_base_bg_def[3]
    )
    temp_base_bg_control = create_control_table('temp_base_num_hh_bg', temp_base_bg_def[4], temp_base_bg_def[2], temp_base_bg_data)
    
    # Match to MAZ geography 
    temp_base_bg_final = match_control_to_geography(
        'temp_base_num_hh_bg', temp_base_bg_control, 'MAZ', 'block group',
        maz_taz_def_df, temp_controls
    )
    temp_controls['temp_base_num_hh_bg'] = temp_base_bg_final
    
    # Now debug the household size controls
    household_size_controls = ['hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus']
    
    for control_name in household_size_controls:
        logger.info(f"\n=== Debugging {control_name} ===")
        
        # Get control definition from config
        control_def = None
        for name, definition in CONTROLS[ACS_EST_YEAR]['MAZ'].items():
            if name == control_name:
                control_def = definition
                break
                
        if not control_def:
            logger.error(f"Could not find definition for {control_name}")
            continue
            
        logger.info(f"Control definition: {control_def}")
        
        # Step 1: Get census data
        census_data = cf.get_census_data(
            dataset=control_def[0],
            year=control_def[1],
            table=control_def[2],
            geo=control_def[3]
        )
        
        # Step 2: Create control table  
        control_table_df = create_control_table(control_name, control_def[4], control_def[2], census_data)
        logger.info(f"Control table shape: {control_table_df.shape}")
        logger.info(f"Control table columns: {list(control_table_df.columns)}")
        logger.info(f"Control table head:\\n{control_table_df.head()}")
        
        # Step 3: Write distribution weights debug file
        if len(control_def) > 6:  # Has scaling parameters
            logger.info(f"Writing distribution weights debug file for {control_name}")
            from tm2_control_utils.controls import write_distribution_weights_debug
            write_distribution_weights_debug(
                control_name, control_table_df,
                control_def[5] if len(control_def) > 5 else None,  # scale_numerator  
                control_def[6] if len(control_def) > 6 else None,  # scale_denominator
                temp_controls, maz_taz_def_df, control_def[3]
            )
            logger.info(f"Debug file written for {control_name}")
        else:
            logger.info(f"No scaling parameters for {control_name}, skipping debug file")


if __name__ == "__main__":
    debug_household_size_controls()
