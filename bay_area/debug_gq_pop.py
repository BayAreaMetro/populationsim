#!/usr/bin/env python3
"""
Debug script to test gq_pop control processing in isolation
"""

import sys
sys.path.append('.')
import collections
from tm2_control_utils.census_fetcher import CensusFetcher
from tm2_control_utils.controls import create_control_table, match_control_to_geography
from tm2_control_utils.geog_utils import interpolate_est, prepare_geography_dfs

def test_gq_pop():
    # Initialize
    cf = CensusFetcher()
    maz_taz_def_df, crosswalk_df = prepare_geography_dfs()
    temp_controls = collections.OrderedDict()
    
    # gq_pop control definition
    control_def = ('pl', 2020, 'P1_003N', 'block', [])
    control_name = 'gq_pop'
    control_geo = 'MAZ'
    
    print(f"Testing {control_name} control...")
    print(f"Control definition: {control_def}")
    
    # Step 1: Fetch census data
    census_table_df = cf.get_census_data(
        dataset=control_def[0],
        year=control_def[1],
        table=control_def[2],
        geo=control_def[3]
    )
    
    print(f"Raw census data shape: {census_table_df.shape}")
    print(f"Raw census data head:\n{census_table_df.head()}")
    print(f"P1_003N statistics:")
    print(census_table_df['P1_003N'].astype(float).describe())
    
    # Step 2: Create control table
    control_table_df = create_control_table(control_name, control_def[4], control_def[2], census_table_df)
    
    print(f"Control table shape: {control_table_df.shape}")
    print(f"Control table head:\n{control_table_df.head()}")
    print(f"Control values statistics:")
    print(control_table_df[control_name].astype(float).describe())
    
    # Step 3: Interpolate if needed
    control_table_df = interpolate_est(
        control_table_df,
        geo=control_def[3],
        target_geo_year=2010,
        source_geo_year=2020
    )
    
    print(f"After interpolation shape: {control_table_df.shape}")
    print(f"After interpolation head:\n{control_table_df.head()}")
    
    # Step 4: Match control to geography
    final_df = match_control_to_geography(
        control_name, control_table_df, control_geo, control_def[3],
        maz_taz_def_df, temp_controls,
        scale_numerator=None, scale_denominator=None,
        subtract_table=None
    )
    
    print(f"Final MAZ aggregation shape: {final_df.shape}")
    print(f"Final MAZ aggregation head:\n{final_df.head()}")
    print(f"Final values statistics:")
    print(final_df[control_name].astype(float).describe())
    print(f"Total sum: {final_df[control_name].astype(float).sum()}")
    
    # Check for extreme values
    extreme_df = final_df.nlargest(10, control_name)
    print(f"Top 10 highest values:\n{extreme_df}")

if __name__ == "__main__":
    test_gq_pop()
