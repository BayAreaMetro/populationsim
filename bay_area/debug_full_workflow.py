"""
Debug the full workflow to see what happens to gq_pop values.
"""
import os
import sys
import pandas as pd
import numpy as np

# Add the current directory to path so we can import from tm2_control_utils
sys.path.insert(0, os.getcwd())

import collections
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from tm2_control_utils.geog_utils import prepare_geography_dfs, interpolate_est
from tm2_control_utils.config import ACS_EST_YEAR, CONTROLS
from tm2_control_utils.census_fetcher import CensusFetcher
from tm2_control_utils.controls import create_control_table, interpolate_control, match_control_to_geography, integerize_control

def debug_process_control(control_geo, control_name, control_def, cf, maz_taz_def_df, crosswalk_df, temp_controls, final_control_dfs):
    """Debug version of process_control that tracks gq_pop specifically."""
    
    print(f"\n=== PROCESSING CONTROL: {control_name} ===")
    print(f"Control definition: {control_def}")
    
    if control_name == 'gq_pop':
        print("🎯 FOUND GQ_POP! Tracking this closely...")
    
    # Following the same logic as the original process_control
    if isinstance(control_def, str) and control_def == 'special':
        print(f"Special control {control_name}, handling via region controls")
        return
        
    if len(control_def) > 4:
        # Step 1: Create control table
        control_table_df = create_control_table(
            control_name, control_def[1], control_def[2], 
            control_def[3], cf
        )
        
        if control_name == 'gq_pop':
            print(f"GQ_POP after create_control_table:")
            print(f"  Shape: {control_table_df.shape}")
            print(f"  Sample values: {control_table_df.head()}")
            print(f"  Sum: {control_table_df.sum().sum()}")
        
        # Step 2: Interpolate
        control_table_df = interpolate_control(control_name, control_table_df, control_def[3])
        
        if control_name == 'gq_pop':
            print(f"GQ_POP after interpolate_control:")
            print(f"  Shape: {control_table_df.shape}")
            print(f"  Sample values: {control_table_df.head()}")
            print(f"  Sum: {control_table_df.sum().sum()}")
        
        # Step 3: Handle scaling
        scale_numerator = control_def[5] if len(control_def) > 5 else None
        scale_denominator = control_def[6] if len(control_def) > 6 else None
        subtract_table = control_def[7] if len(control_def) > 7 else None
        
        if control_name == 'gq_pop':
            print(f"GQ_POP scaling parameters:")
            print(f"  scale_numerator: {scale_numerator}")
            print(f"  scale_denominator: {scale_denominator}")
            print(f"  subtract_table: {subtract_table}")
        
        # Step 4: Match to geography
        final_df = match_control_to_geography(
            control_name, control_table_df, control_geo, control_def[3],
            maz_taz_def_df, temp_controls,
            scale_numerator=scale_numerator, scale_denominator=scale_denominator,
            subtract_table=subtract_table
        )
        
        if control_name == 'gq_pop':
            print(f"GQ_POP after match_control_to_geography:")
            print(f"  Shape: {final_df.shape}")
            print(f"  Columns: {list(final_df.columns)}")
            print(f"  Sample values: {final_df.head()}")
            if 'gq_pop' in final_df.columns:
                print(f"  gq_pop sum: {final_df['gq_pop'].sum()}")
                print(f"  gq_pop max: {final_df['gq_pop'].max()}")
                print(f"  gq_pop mean: {final_df['gq_pop'].mean():.2f}")
        
        # Step 5: Handle temp controls
        if control_name.startswith("temp_"):
            temp_controls[control_name] = final_df
            return
        
        # Step 6: Integerize if needed
        if control_name in ["num_hh", "gq_pop", "tot_pop"]:
            final_df = integerize_control(final_df, crosswalk_df, control_name)
            
            if control_name == 'gq_pop':
                print(f"GQ_POP after integerize_control:")
                print(f"  Shape: {final_df.shape}")
                print(f"  Sample values: {final_df.head()}")
                if 'gq_pop' in final_df.columns:
                    print(f"  gq_pop sum: {final_df['gq_pop'].sum()}")
                    print(f"  gq_pop max: {final_df['gq_pop'].max()}")
                    print(f"  gq_pop mean: {final_df['gq_pop'].mean():.2f}")
        
        # Step 7: Merge into final_control_dfs
        if control_geo not in final_control_dfs:
            final_control_dfs[control_geo] = final_df
            if control_name == 'gq_pop':
                print(f"GQ_POP: First control for {control_geo}, setting directly")
        else:
            if control_name == 'gq_pop':
                print(f"GQ_POP: Merging with existing controls for {control_geo}")
                print(f"  Existing DataFrame shape: {final_control_dfs[control_geo].shape}")
                print(f"  Existing columns: {list(final_control_dfs[control_geo].columns)}")
                print(f"  New DataFrame shape: {final_df.shape}")
                print(f"  New columns: {list(final_df.columns)}")
                
                # Check for common indices
                existing_index = set(final_control_dfs[control_geo].index)
                new_index = set(final_df.index)
                common_indices = existing_index.intersection(new_index)
                only_existing = existing_index - new_index
                only_new = new_index - existing_index
                
                print(f"  Common indices: {len(common_indices)} (e.g., {list(common_indices)[:5]})")
                print(f"  Only in existing: {len(only_existing)} (e.g., {list(only_existing)[:5]})")
                print(f"  Only in new: {len(only_new)} (e.g., {list(only_new)[:5]})")
            
            final_control_dfs[control_geo] = pd.merge(
                left=final_control_dfs[control_geo],
                right=final_df,
                how="left",
                left_index=True,
                right_index=True
            )
            
            if control_name == 'gq_pop':
                print(f"GQ_POP after merge:")
                print(f"  Final shape: {final_control_dfs[control_geo].shape}")
                print(f"  Final columns: {list(final_control_dfs[control_geo].columns)}")
                if 'gq_pop' in final_control_dfs[control_geo].columns:
                    print(f"  gq_pop values sample: {final_control_dfs[control_geo]['gq_pop'].head()}")
                    print(f"  gq_pop sum: {final_control_dfs[control_geo]['gq_pop'].sum()}")
                    print(f"  gq_pop max: {final_control_dfs[control_geo]['gq_pop'].max()}")
                    print(f"  gq_pop mean: {final_control_dfs[control_geo]['gq_pop'].mean():.2f}")
                    
                    # Check for anomalies
                    high_values = final_control_dfs[control_geo][final_control_dfs[control_geo]['gq_pop'] > 10000]
                    if len(high_values) > 0:
                        print(f"  ⚠️ HIGH VALUES DETECTED! {len(high_values)} MAZs with gq_pop > 10,000:")
                        print(high_values[['gq_pop']])

if __name__ == "__main__":
    print("Starting debug run of full workflow...")
    
    # Set up exactly like the main script
    maz_taz_def_df, crosswalk_df = prepare_geography_dfs()
    cf = CensusFetcher() 
    final_control_dfs = {}

    # Process only MAZ controls to focus on where gq_pop appears
    control_geo = 'MAZ'
    control_dict = CONTROLS[ACS_EST_YEAR][control_geo]
    
    temp_controls = collections.OrderedDict()
    for control_name, control_def in control_dict.items():
        debug_process_control(
            control_geo, control_name, control_def,
            cf, maz_taz_def_df, crosswalk_df, temp_controls, final_control_dfs
        )
        
        # Stop after gq_pop is processed to see what happens
        if control_name == 'gq_pop':
            print("\n🔍 STOPPING AFTER GQ_POP TO ANALYZE...")
            break
    
    print("\n=== FINAL ANALYSIS ===")
    if 'MAZ' in final_control_dfs and 'gq_pop' in final_control_dfs['MAZ'].columns:
        gq_values = final_control_dfs['MAZ']['gq_pop']
        print(f"Final gq_pop statistics:")
        print(f"  Count: {len(gq_values)}")
        print(f"  Sum: {gq_values.sum()}")
        print(f"  Mean: {gq_values.mean():.2f}")
        print(f"  Max: {gq_values.max()}")
        print(f"  Min: {gq_values.min()}")
        
        # Show top values
        top_values = gq_values.nlargest(10)
        print(f"  Top 10 values: {top_values.tolist()}")
