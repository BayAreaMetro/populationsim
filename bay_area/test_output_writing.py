#!/usr/bin/env python3

"""
Test script to verify output writing logic works correctly.
"""

import pandas as pd
import os
import sys
import logging

# Add tm2_control_utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tm2_control_utils'))

from config import *

def test_write_outputs():
    """Test the write_outputs function with dummy data"""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
    logger.addHandler(ch)
    
    # Import write_outputs function
    sys.path.append('.')
    from create_baseyear_controls_23_tm2 import write_outputs
    
    # Create dummy MAZ control data
    dummy_maz_data = pd.DataFrame({
        'MAZ': [10001, 10002, 10003, 10004, 10005],
        'num_hh': [55, 64, 69, 72, 62],
        'gq_num_hh': [5, 3, 2, 8, 4],
        'tot_pop': [150, 180, 200, 220, 175],
        'hh_inc_30': [15, 20, 25, 30, 18],
        'hh_inc_30_60': [25, 30, 28, 25, 30],
        'hh_inc_60_100': [10, 10, 12, 12, 10],
        'hh_inc_100_plus': [5, 4, 4, 5, 4]
    }).set_index('MAZ')
    
    print("Dummy MAZ data:")
    print(dummy_maz_data)
    
    # Create dummy crosswalk data
    dummy_crosswalk = pd.DataFrame({
        'MAZ': [10001, 10002, 10003, 10004, 10005],
        'TAZ': [301001, 301002, 301003, 301004, 301005],
        'COUNTY': [4, 4, 4, 4, 4]
    })
    
    print("\nAttempting to write MAZ outputs...")
    
    # Test output writing
    try:
        write_outputs('MAZ', dummy_maz_data, dummy_crosswalk)
        print("MAZ output writing completed successfully!")
    except Exception as e:
        print(f"Error writing MAZ outputs: {e}")
        import traceback
        traceback.print_exc()
    
    # Check what files were created
    print("\nChecking output directories:")
    output_dir = OUTPUT_DIR_FMT.format(ACS_EST_YEAR)
    households_dir = os.path.join(HOUSEHOLDS_DIR, DATA_SUBDIR)
    group_quarters_dir = os.path.join(GROUP_QUARTERS_DIR, DATA_SUBDIR)
    
    print(f"Output directory: {output_dir}")
    if os.path.exists(output_dir):
        print(f"  Contents: {os.listdir(output_dir)}")
    else:
        print(f"  Directory does not exist")
        
    print(f"Households directory: {households_dir}")
    if os.path.exists(households_dir):
        print(f"  Contents: {os.listdir(households_dir)}")
    else:
        print(f"  Directory does not exist")
        
    print(f"Group quarters directory: {group_quarters_dir}")
    if os.path.exists(group_quarters_dir):
        print(f"  Contents: {os.listdir(group_quarters_dir)}")
    else:
        print(f"  Directory does not exist")

if __name__ == '__main__':
    test_write_outputs()
