"""
Test what the household size controls look like when processed in isolation.
"""
import os
import sys
import pandas as pd
import numpy as np

# Add the current directory to path so we can import from tm2_control_utils
sys.path.insert(0, os.getcwd())

from tm2_control_utils.geog_utils import prepare_geography_dfs
from tm2_control_utils.config import ACS_EST_YEAR, CONTROLS
from tm2_control_utils.census_fetcher import CensusFetcher
from tm2_control_utils.controls import create_control_table, match_control_to_geography, integerize_control

if __name__ == "__main__":
    print("Testing household size control processing...")
    
    # Set up like the main script
    maz_taz_def_df, crosswalk_df = prepare_geography_dfs()
    cf = CensusFetcher() 
    temp_controls = {}
    
    # Test hh_size_1 control
    control_name = 'hh_size_1'
    control_def = CONTROLS[ACS_EST_YEAR]['MAZ'][control_name]
    print(f"Control definition for {control_name}: {control_def}")
    
    # Step 1: Fetch census data
    census_table_df = cf.get_census_data(
        dataset=control_def[0],
        year=control_def[1],
        table=control_def[2],
        geo=control_def[3]
    )
    print(f"Census data shape: {census_table_df.shape}")
    print(f"Census data sample:\n{census_table_df.head()}")
    
    # Step 2: Create control table
    control_table_df = create_control_table(control_name, control_def[4], control_def[2], census_table_df)
    print(f"Control table shape: {control_table_df.shape}")
    print(f"Control table sample:\n{control_table_df.head()}")
    
    # Step 3: Get scaling parameters
    scale_numerator = control_def[5] if len(control_def) > 5 else None
    scale_denominator = control_def[6] if len(control_def) > 6 else None
    subtract_table = control_def[7] if len(control_def) > 7 else None
    
    print(f"Scaling parameters:")
    print(f"  scale_numerator: {scale_numerator}")
    print(f"  scale_denominator: {scale_denominator}")
    print(f"  subtract_table: {subtract_table}")
    
    # Step 4: Match control to geography
    final_df = match_control_to_geography(
        control_name, control_table_df, 'MAZ', control_def[3],
        maz_taz_def_df, temp_controls,
        scale_numerator=scale_numerator, scale_denominator=scale_denominator,
        subtract_table=subtract_table
    )
    
    print(f"Final DataFrame shape: {final_df.shape}")
    print(f"Final DataFrame columns: {list(final_df.columns)}")
    print(f"Final DataFrame sample:\n{final_df.head()}")
    print(f"Final DataFrame index sample: {final_df.index[:10].tolist()}")
    
    # Check for anomalies
    if control_name in final_df.columns:
        values = final_df[control_name]
        print(f"Value statistics:")
        print(f"  Count: {len(values)}")
        print(f"  Sum: {values.sum()}")
        print(f"  Mean: {values.mean():.2f}")
        print(f"  Max: {values.max()}")
        print(f"  Min: {values.min()}")
        
        # Check for very high values
        high_values = values[values > 10000]
        if len(high_values) > 0:
            print(f"  ⚠️ HIGH VALUES DETECTED! {len(high_values)} MAZs with {control_name} > 10,000:")
            print(high_values.head(10))
        
        # Check for duplicate indices
        if final_df.index.duplicated().any():
            print(f"  ⚠️ DUPLICATE INDICES DETECTED!")
            duplicates = final_df.index[final_df.index.duplicated(keep=False)]
            print(f"  Duplicate indices: {duplicates.unique()[:10].tolist()}")
    else:
        print(f"Column {control_name} not found in final DataFrame!")
