#!/usr/bin/env python3
"""
Check zero weight households in PopulationSim input data
to debug the IntCastingNaNError during incidence table processing.
"""

import pandas as pd
import numpy as np
import os

def check_zero_weights():
    """Check for zero weight households in PopulationSim input files"""
    
    print("=== CHECKING ZERO WEIGHT HOUSEHOLDS IN POPULATIONSIM DATA ===")
    
    data_dir = "c:/GitHub/populationsim/bay_area/hh_gq/data"
    
    # Check households file
    hh_file = os.path.join(data_dir, "seed_households.csv")
    if os.path.exists(hh_file):
        print(f"\nReading households from: {hh_file}")
        households = pd.read_csv(hh_file)
        
        print(f"Total households in file: {len(households):,}")
        print(f"Households columns: {list(households.columns)}")
        
        if 'WGTP' in households.columns:
            wgtp_stats = households['WGTP'].describe()
            print(f"\nWGTP statistics:")
            print(wgtp_stats)
            
            zero_weight = households['WGTP'] == 0
            print(f"\nZero weight households: {zero_weight.sum():,} ({zero_weight.sum()/len(households)*100:.1f}%)")
            
            if zero_weight.any():
                print(f"Sample zero weight households:")
                sample_zeros = households[zero_weight].head(3)
                print(sample_zeros[['unique_hh_id', 'WGTP', 'COUNTY', 'PUMA']].to_string())
                
            # Check for other problematic values
            inf_weight = np.isinf(households['WGTP'])
            nan_weight = households['WGTP'].isna()
            
            print(f"Infinite weight households: {inf_weight.sum():,}")
            print(f"NaN weight households: {nan_weight.sum():,}")
            
            # Check if households file has already been filtered
            valid_weight = (households['WGTP'] > 0) & (households['WGTP'] < np.inf)
            print(f"Valid weight households: {valid_weight.sum():,} ({valid_weight.sum()/len(households)*100:.1f}%)")
            
        else:
            print("ERROR: WGTP column not found in households file!")
            
    else:
        print(f"ERROR: Households file not found: {hh_file}")
        print("Available files in data directory:")
        try:
            files = os.listdir(data_dir)
            for f in sorted(files):
                if f.endswith('.csv'):
                    print(f"  {f}")
        except Exception as e:
            print(f"  Error listing files: {e}")
    
    # Check crosswalk file
    crosswalk_file = os.path.join(data_dir, "geo_cross_walk_tm2.csv")
    if os.path.exists(crosswalk_file):
        print(f"\nReading crosswalk from: {crosswalk_file}")
        crosswalk = pd.read_csv(crosswalk_file)
        print(f"Crosswalk shape: {crosswalk.shape}")
        print(f"Crosswalk columns: {list(crosswalk.columns)}")
        
        # Check for unique zones
        if 'MAZ' in crosswalk.columns:
            print(f"Unique MAZs in crosswalk: {crosswalk['MAZ'].nunique():,}")
        if 'TAZ' in crosswalk.columns:
            print(f"Unique TAZs in crosswalk: {crosswalk['TAZ'].nunique():,}")
        if 'COUNTY' in crosswalk.columns:
            print(f"Unique COUNTYs in crosswalk: {crosswalk['COUNTY'].nunique():,}")
    else:
        print(f"ERROR: Crosswalk file not found: {crosswalk_file}")
    
    print("\n=== RECOMMENDATION ===")
    if 'households' in locals() and 'zero_weight' in locals() and zero_weight.any():
        print("ISSUE IDENTIFIED: Zero weight households present in PopulationSim input data")
        print("SOLUTION: PopulationSim should filter these out, but the filtering may not be working correctly")
        print("NEXT STEP: Check PopulationSim configuration and data preprocessing")
    else:
        print("Zero weight households properly filtered from PopulationSim input data")

if __name__ == "__main__":
    check_zero_weights()
