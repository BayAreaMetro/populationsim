"""
Debug individual controls to understand interpolation and scaling behavior.
"""
import os
import sys
import pandas as pd
import numpy as np

# Add the current directory to path so we can import from tm2_control_utils
sys.path.insert(0, os.getcwd())

# Import functions from the main script
exec(open('create_baseyear_controls_23_tm2.py').read())

def test_simple_control(control_name, control_def):
    """Test a simple control (like num_hh, tot_pop, gq_pop)."""
    print(f"\n=== TESTING SIMPLE CONTROL: {control_name} ===")
    print(f"Definition: {control_def}")
    
    try:
        # Simulate the process_control function for this control
        control_geo = 'MAZ'  # All these are MAZ controls
        temp_controls = {}
        final_control_dfs = {}
        
        # Call process_control
        process_control(
            control_geo, control_name, control_def, 
            crosswalk_df['maz_taz'], maz_taz_def_df, crosswalk_df, 
            temp_controls, final_control_dfs
        )
        
        # Check results
        if control_geo in final_control_dfs and control_name in final_control_dfs[control_geo].columns:
            result_series = final_control_dfs[control_geo][control_name]
            print(f"SUCCESS! Results:")
            print(f"  Count: {len(result_series)}")
            print(f"  Sum: {result_series.sum():,.0f}")
            print(f"  Mean: {result_series.mean():.1f}")
            print(f"  Min: {result_series.min()}")
            print(f"  Max: {result_series.max()}")
            print(f"  First 5 values: {result_series.head().tolist()}")
            return result_series
        else:
            print(f"FAILED! Column {control_name} not found in results")
            return None
            
    except Exception as e:
        print(f"ERROR processing {control_name}: {e}")
        return None

def test_complex_control(control_name, control_def):
    """Test a complex control with scaling (like hh_size_1)."""
    print(f"\n=== TESTING COMPLEX CONTROL: {control_name} ===")
    print(f"Definition: {control_def}")
    print(f"Length: {len(control_def)} parameters")
    
    # Break down the parameters
    if len(control_def) >= 7:
        data_source = control_def[0]  # 'acs5'
        year = control_def[1]         # ACS_EST_YEAR
        table = control_def[2]        # 'B11016'  
        geography = control_def[3]    # 'block group'
        filters = control_def[4]      # [OrderedDict([('pers_min',1),('pers_max',1)])]
        scale_num = control_def[5]    # 'temp_base_num_hh_b'
        scale_denom = control_def[6]  # 'temp_base_num_hh_bg'
        
        print(f"  Data source: {data_source}")
        print(f"  Year: {year}")
        print(f"  Table: {table}")
        print(f"  Geography: {geography}")
        print(f"  Filters: {filters}")
        print(f"  Scale numerator: {scale_num}")
        print(f"  Scale denominator: {scale_denom}")
    
    try:
        # Simulate the process_control function for this control
        control_geo = 'MAZ'  # All these are MAZ controls
        temp_controls = {}
        final_control_dfs = {}
        
        # Call process_control
        process_control(
            control_geo, control_name, control_def, 
            crosswalk_df['maz_taz'], maz_taz_def_df, crosswalk_df, 
            temp_controls, final_control_dfs
        )
        
        # Check results
        if control_geo in final_control_dfs and control_name in final_control_dfs[control_geo].columns:
            result_series = final_control_dfs[control_geo][control_name]
            print(f"SUCCESS! Results:")
            print(f"  Count: {len(result_series)}")
            print(f"  Sum: {result_series.sum():,.0f}")
            print(f"  Mean: {result_series.mean():.1f}")
            print(f"  Min: {result_series.min()}")
            print(f"  Max: {result_series.max()}")
            print(f"  First 5 values: {result_series.head().tolist()}")
            return result_series
        else:
            print(f"FAILED! Column {control_name} not found in results")
            if control_geo in final_control_dfs:
                print(f"Available columns: {list(final_control_dfs[control_geo].columns)}")
            return None
            
    except Exception as e:
        print(f"ERROR processing {control_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("Loading data and configuration...")
    
    # Load the control definitions
    from tm2_control_utils.config import CONTROLS, ACS_EST_YEAR
    maz_controls = CONTROLS[ACS_EST_YEAR]['MAZ']
    
    print(f"Found {len(maz_controls)} MAZ controls for year {ACS_EST_YEAR}")
    
    # Test simple controls first
    simple_controls = ['num_hh', 'tot_pop', 'gq_pop']
    simple_results = {}
    
    for control_name in simple_controls:
        if control_name in maz_controls:
            control_def = maz_controls[control_name]
            result = test_simple_control(control_name, control_def)
            simple_results[control_name] = result
    
    # Test one complex control
    complex_controls = ['hh_size_1']
    complex_results = {}
    
    for control_name in complex_controls:
        if control_name in maz_controls:
            control_def = maz_controls[control_name]
            result = test_complex_control(control_name, control_def)
            complex_results[control_name] = result
    
    # Compare results
    print(f"\n=== COMPARISON ===")
    
    if 'tot_pop' in simple_results and simple_results['tot_pop'] is not None:
        tot_pop_sum = simple_results['tot_pop'].sum()
        print(f"tot_pop sum: {tot_pop_sum:,.0f}")
    
    if 'num_hh' in simple_results and simple_results['num_hh'] is not None:
        num_hh_sum = simple_results['num_hh'].sum()
        print(f"num_hh sum: {num_hh_sum:,.0f}")
        
    if 'gq_pop' in simple_results and simple_results['gq_pop'] is not None:
        gq_pop_sum = simple_results['gq_pop'].sum()
        print(f"gq_pop sum: {gq_pop_sum:,.0f}")
    
    if 'hh_size_1' in complex_results and complex_results['hh_size_1'] is not None:
        hh_size_1_sum = complex_results['hh_size_1'].sum()
        print(f"hh_size_1 sum: {hh_size_1_sum:,.0f}")
        
        # Check if hh_size_1 > tot_pop
        if 'tot_pop' in simple_results and simple_results['tot_pop'] is not None:
            if hh_size_1_sum > tot_pop_sum:
                print(f"❌ PROBLEM: hh_size_1 sum ({hh_size_1_sum:,.0f}) > tot_pop sum ({tot_pop_sum:,.0f})")
            else:
                print(f"✅ OK: hh_size_1 sum ({hh_size_1_sum:,.0f}) <= tot_pop sum ({tot_pop_sum:,.0f})")
