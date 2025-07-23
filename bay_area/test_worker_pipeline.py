"""
Targeted test to debug worker control doubling issue.
Run just the essential parts to track the exact pipeline flow.
"""

import sys
import os
import pandas as pd
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import necessary modules
from create_baseyear_controls_23_tm2 import *
from tm2_control_utils.config import CONTROLS, ACS_EST_YEAR
from tm2_control_utils.census_fetcher import CensusFetcher
from tm2_control_utils.geog_utils import prepare_geography_dfs
from tm2_control_utils.controls import create_control_table, match_control_to_geography

def test_single_worker_control():
    """Test the processing of a single worker control to identify where doubling occurs."""
    
    print("="*80)
    print("TESTING SINGLE WORKER CONTROL PROCESSING")
    print("="*80)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    logger = logging.getLogger()
    
    # Load geography data
    print("Loading geography data...")
    maz_taz_def_df, crosswalk_df = prepare_geography_dfs()
    cf = CensusFetcher()
    
    # Get worker control configuration
    control_name = 'hh_wrks_0'
    control_geo = 'TAZ'
    control_def = CONTROLS[ACS_EST_YEAR][control_geo][control_name]
    
    print(f"Testing control: {control_name}")
    print(f"Control definition: {control_def}")
    print(f"Scale denominator: {control_def[6]}")
    
    # Step 1: Create temp controls (need temp_hh_bg_for_tract_weights)
    print("\nStep 1: Creating temp_hh_bg_for_tract_weights...")
    temp_controls = {}
    
    # Get the temp control definition
    temp_control_name = 'temp_hh_bg_for_tract_weights'
    temp_control_def = CONTROLS[ACS_EST_YEAR]['TAZ'][temp_control_name]
    
    print(f"Temp control definition: {temp_control_def}")
    
    # Create temp control
    temp_census_data = cf.get_census_data(
        dataset=temp_control_def[0],
        year=temp_control_def[1], 
        table=temp_control_def[2],
        geo=temp_control_def[3]
    )
    
    temp_control_table = create_control_table(temp_control_name, temp_control_def[4], temp_control_def[2], temp_census_data)
    
    # Process temp control to block group level  
    # Since match_control_to_geography doesn't support block group, use the raw data directly
    # temp_final_df = match_control_to_geography(
    #     temp_control_name, temp_control_table, temp_control_def[3], temp_control_def[3],
    #     maz_taz_def_df, {},
    #     scale_numerator=None, scale_denominator=None, subtract_table=None
    # )
    
    # For temp control at block group level, use the control table directly
    temp_final_df = temp_control_table.copy()
    if 'GEOID_block group' in temp_final_df.columns:
        temp_final_df = temp_final_df.set_index('GEOID_block group')
    
    temp_controls[temp_control_name] = temp_final_df
    print(f"Created temp control: {len(temp_final_df)} records, total = {temp_final_df[temp_control_name].sum():,.0f}")
    
    # Step 2: Create worker control
    print(f"\nStep 2: Creating worker control {control_name}...")
    
    # Fetch census data for worker control
    census_data = cf.get_census_data(
        dataset=control_def[0],
        year=control_def[1],
        table=control_def[2], 
        geo=control_def[3]
    )
    
    control_table_df = create_control_table(control_name, control_def[4], control_def[2], census_data)
    print(f"Raw control table: {len(control_table_df)} records, total = {control_table_df[control_name].sum():,.0f}")
    
    # Step 2.5: Add geographic interpolation like the full pipeline
    print("\nStep 2.5: Applying geographic interpolation (2023 → 2010)...")
    from tm2_control_utils.geog_utils import interpolate_est
    from tm2_control_utils.config import CENSUS_GEOG_YEAR, CENSUS_EST_YEAR
    
    print(f"Before interpolation: {len(control_table_df)} records, total = {control_table_df[control_name].sum():,.0f}")
    
    if CENSUS_GEOG_YEAR != CENSUS_EST_YEAR:
        print(f"GEOGRAPHIC INTERPOLATION: {CENSUS_EST_YEAR} → {CENSUS_GEOG_YEAR}")
        control_table_df = interpolate_est(
            control_table_df,
            geo=control_def[3],  # 'tract'
            target_geo_year=CENSUS_GEOG_YEAR,
            source_geo_year=CENSUS_EST_YEAR
        )
        print(f"After interpolation: {len(control_table_df)} records, total = {control_table_df[control_name].sum():,.0f}")
        print(f"Interpolation ratio: {control_table_df[control_name].sum() / 1221884:.6f}")
    else:
        print(f"No interpolation needed: both years are {CENSUS_GEOG_YEAR}")

    # Step 3: Process worker control through the full pipeline
    print(f"\nStep 3: Processing {control_name} through geographic matching...")
    scale_numerator = control_def[5]
    scale_denominator = control_def[6]
    
    print(f"Using scale_numerator: {scale_numerator}")
    print(f"Using scale_denominator: {scale_denominator}")
    
    final_df = match_control_to_geography(
        control_name, control_table_df, control_geo, control_def[3],
        maz_taz_def_df, temp_controls,
        scale_numerator=scale_numerator, scale_denominator=scale_denominator,
        subtract_table=None
    )
    
    print(f"\nFINAL RESULTS:")
    print(f"Final df shape: {final_df.shape}")
    print(f"Final df total: {final_df[control_name].sum():,.0f}")
    print(f"Input vs Final ratio: {final_df[control_name].sum() / control_table_df[control_name].sum():.6f}")
    
    # Compare with existing TAZ controls
    print(f"\nCOMPARISON WITH EXISTING CONTROLS:")
    try:
        existing_taz = pd.read_csv('output_2023/taz_marginals.csv')
        if control_name in existing_taz.columns:
            existing_total = existing_taz[control_name].sum()
            print(f"Existing {control_name} total: {existing_total:,.0f}")
            print(f"New vs Existing ratio: {final_df[control_name].sum() / existing_total:.6f}")
        
        # Check against size controls
        size_cols = ['hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus']
        size_total = sum(existing_taz[col].sum() for col in size_cols if col in existing_taz.columns)
        print(f"Size controls total: {size_total:,.0f}")
        print(f"New worker vs Size ratio: {final_df[control_name].sum() / size_total:.6f}")
        
    except Exception as e:
        print(f"Could not compare with existing: {e}")

if __name__ == '__main__':
    test_single_worker_control()
