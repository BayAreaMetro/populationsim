#!/usr/bin/env python3
"""
Debug script to test county scaling function
"""
import pandas as pd
import os
import sys

# Add the current directory to path to import the scaling function
sys.path.append(os.path.dirname(__file__))
from create_baseyear_controls_23_tm2 import scale_maz_households_to_county_targets

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_scaling():
    """Test the scaling function with current files"""
    
    output_dir = "output_2023"
    maz_file = os.path.join(output_dir, "maz_marginals.csv")
    county_file = os.path.join(output_dir, "county_summary_2020_2023.csv")
    crosswalk_file = os.path.join(output_dir, "geo_cross_walk_tm2.csv")
    
    print("Debug: Checking if files exist:")
    for name, filepath in [("MAZ marginals", maz_file), ("County summary", county_file), ("Crosswalk", crosswalk_file)]:
        exists = os.path.exists(filepath)
        print(f"  {name}: {filepath} - {'EXISTS' if exists else 'MISSING'}")
    
    if not all(os.path.exists(f) for f in [maz_file, county_file, crosswalk_file]):
        print("ERROR: Missing required files for scaling test")
        return
    
    # Check MAZ file before scaling
    maz_df = pd.read_csv(maz_file)
    print(f"\nBefore scaling:")
    print(f"  MAZ households: {maz_df['num_hh'].sum():,.0f}")
    print(f"  MAZ population: {maz_df['total_pop'].sum():,.0f}")
    
    # Check targets
    targets_file = os.path.join(output_dir, "county_targets_acs2023.csv")
    if os.path.exists(targets_file):
        targets_df = pd.read_csv(targets_file)
        hh_target = targets_df[targets_df['target_name'] == 'num_hh_target_by_county']['target_value'].sum()
        pop_target = targets_df[targets_df['target_name'] == 'tot_pop_target_by_county']['target_value'].sum()
        print(f"\nTargets:")
        print(f"  Household target: {hh_target:,.0f}")
        print(f"  Population target: {pop_target:,.0f}")
        print(f"  HH Gap: {maz_df['num_hh'].sum() - hh_target:+,.0f}")
        print(f"  Pop Gap: {maz_df['total_pop'].sum() - pop_target:+,.0f}")
    
    # Run scaling
    print(f"\nRunning county scaling function...")
    result = scale_maz_households_to_county_targets(maz_file, county_file, crosswalk_file, logger)
    print(f"Scaling function returned: {result}")
    
    # Check MAZ file after scaling
    maz_df_after = pd.read_csv(maz_file)
    print(f"\nAfter scaling:")
    print(f"  MAZ households: {maz_df_after['num_hh'].sum():,.0f}")
    print(f"  MAZ population: {maz_df_after['total_pop'].sum():,.0f}")
    
    if os.path.exists(targets_file):
        print(f"\nFinal gaps:")
        print(f"  HH Gap: {maz_df_after['num_hh'].sum() - hh_target:+,.0f}")
        print(f"  Pop Gap: {maz_df_after['total_pop'].sum() - pop_target:+,.0f}")

if __name__ == "__main__":
    debug_scaling()
