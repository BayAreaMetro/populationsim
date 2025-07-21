#!/usr/bin/env python3
"""
Script to display the region targets configuration from config.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tm2_control_utils'))

from config import CONTROLS, ACS_EST_YEAR
import pandas as pd

def show_region_targets():
    """Display the region targets configuration as a formatted table"""
    
    print("="*80)
    print("REGION TARGETS CONFIGURATION")
    print("="*80)
    
    region_targets = CONTROLS[ACS_EST_YEAR]['REGION_TARGETS']
    
    # Create a list to store the target information
    target_data = []
    
    for target_name, target_config in region_targets.items():
        data_source, year, table, geography, variables = target_config
        
        # Format variables if they exist
        var_str = ""
        if variables:
            var_str = ", ".join([var[0] if isinstance(var, tuple) else str(var) for var in variables])
        else:
            var_str = f"{table}_001E (total)"
            
        target_data.append({
            'Target Name': target_name,
            'Data Source': data_source.upper(),
            'Year': year,
            'Table': table,
            'Geography': geography,
            'Variables': var_str,
            'Description': get_target_description(target_name, table, var_str)
        })
    
    # Create DataFrame and display
    df = pd.DataFrame(target_data)
    
    # Print with nice formatting
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 50)
    
    print(df.to_string(index=False))
    print("\n")
    
    # Summary
    print("SUMMARY:")
    print(f"- Total targets: {len(target_data)}")
    print(f"- Data sources: {', '.join(set([t['Data Source'] for t in target_data]))}")
    print(f"- Year: {target_data[0]['Year']}")
    print(f"- Geography level: {target_data[0]['Geography']}")
    print("\n")
    
    # Show the actual configuration format
    print("RAW CONFIGURATION:")
    print("-" * 50)
    for target_name, target_config in region_targets.items():
        print(f"'{target_name}': {target_config}")
    
    return df

def get_target_description(target_name, table, variables):
    """Get human-readable description for each target"""
    descriptions = {
        'num_hh_target': 'Total occupied housing units (households)',
        'tot_pop_target': 'Total population',
        'pop_gq_target': 'Total group quarters population',
        'gq_military_target': 'Military group quarters population',
        'gq_university_target': 'University/college group quarters population'
    }
    
    return descriptions.get(target_name, f'{table} - {variables}')

if __name__ == "__main__":
    df = show_region_targets()
