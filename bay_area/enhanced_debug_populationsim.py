#!/usr/bin/env python3
"""
Advanced debug script for PopulationSim IntCastingNaNError
Patches the problematic function to add detailed logging
"""

import pandas as pd
import numpy as np
import sys
import os
import traceback
from pathlib import Path

def create_debug_patch():
    """Create a patch for the PopulationSim function that's failing"""
    
    # First, let's examine the exact data that's causing the problem
    print("=" * 80)
    print("ADVANCED PopulationSim DEBUG ANALYSIS")
    print("=" * 80)
    
    # Load the data files that PopulationSim uses
    data_dir = Path('hh_gq/data')
    
    print("\n1. Loading and analyzing seed data...")
    
    # Load households with the same processing PopulationSim would do
    hh_file = data_dir / 'seed_households.csv'
    households = pd.read_csv(hh_file)
    
    # Apply the same dtype conversions as in settings.yaml
    dtype_conversions = {
        'HUPAC': 'int64',
        'NP': 'int64', 
        'hhgqtype': 'int64',
        'hh_workers_from_esr': 'int64',
        'PUMA': 'int64'
    }
    
    print(f"Original households shape: {households.shape}")
    
    # Check for problematic values before conversion
    print("\n2. Checking for problematic values before dtype conversion...")
    for col, target_dtype in dtype_conversions.items():
        if col in households.columns:
            current_dtype = households[col].dtype
            nan_count = households[col].isna().sum()
            inf_count = np.isinf(households[col]).sum() if households[col].dtype in ['float64', 'float32'] else 0
            
            print(f"  {col}: {current_dtype} -> {target_dtype}")
            print(f"    NaN: {nan_count}, Inf: {inf_count}")
            
            if nan_count > 0:
                print(f"    NaN locations: {households[households[col].isna()].index[:5].tolist()}")
                print(f"    Sample non-NaN values: {households[col].dropna().head(5).tolist()}")
            
            if inf_count > 0:
                inf_mask = np.isinf(households[col])
                print(f"    Inf locations: {households[inf_mask].index[:5].tolist()}")
    
    # Try the conversions manually to see what fails
    print("\n3. Testing dtype conversions manually...")
    for col, target_dtype in dtype_conversions.items():
        if col in households.columns:
            try:
                print(f"  Converting {col} to {target_dtype}...")
                if households[col].isna().any():
                    print(f"    WARNING: {col} has NaN values - filling with 0")
                    households[col] = households[col].fillna(0)
                
                if households[col].dtype in ['float64', 'float32'] and np.isinf(households[col]).any():
                    print(f"    WARNING: {col} has inf values - replacing with 0")
                    households[col] = households[col].replace([np.inf, -np.inf], 0)
                
                converted = households[col].astype(target_dtype)
                print(f"    SUCCESS: {col} converted to {target_dtype}")
                
            except Exception as e:
                print(f"    ERROR converting {col}: {e}")
                print(f"    Problematic values: {households[col][households[col].isna() | np.isinf(households[col])].head()}")
    
    # Now test the actual merge operation that's failing
    print("\n4. Testing merge operations...")
    
    # Load control specifications
    controls_file = data_dir / 'controls.csv'
    if controls_file.exists():
        controls = pd.read_csv(controls_file)
        print(f"Controls loaded: {controls.shape[0]} controls")
        
        # Look for household controls that would be used in grouping
        hh_controls = controls[controls['seed_table'] == 'households']
        print(f"Household controls: {len(hh_controls)}")
        
        print("\n   Household control expressions:")
        for _, control in hh_controls.iterrows():
            print(f"     {control['target']}: {control['expression']}")
    
    print("\n5. Checking geo_cross_walk...")
    geo_file = data_dir / 'geo_cross_walk_tm2.csv'
    if geo_file.exists():
        geo_data = pd.read_csv(geo_file)
        print(f"Geo crosswalk shape: {geo_data.shape}")
        print(f"Geo columns: {geo_data.columns.tolist()}")
        
        # Check for NaN values in geography columns
        for col in geo_data.columns:
            nan_count = geo_data[col].isna().sum()
            if nan_count > 0:
                print(f"  {col}: {nan_count} NaN values")
    
    return households

def run_populationsim_with_enhanced_debug():
    """Run PopulationSim with monkey-patched debugging"""
    
    # First run our analysis
    households = create_debug_patch()
    
    print("\n" + "=" * 80)
    print("RUNNING PopulationSim WITH ENHANCED ERROR HANDLING")
    print("=" * 80)
    
    # Change to the hh_gq directory
    os.chdir('hh_gq')
    
    try:
        # Import and run PopulationSim
        import populationsim.run_populationsim as run_ps
        
        # Monkey patch to add debugging to the failing function
        original_merge = pd.DataFrame.merge
        
        def debug_merge(self, *args, **kwargs):
            print(f"\nDEBUG MERGE: DataFrame shape {self.shape}, columns: {self.columns.tolist()[:10]}")
            print(f"  Data types: {dict(self.dtypes)}")
            
            # Check for NaN/inf values in merge keys
            for col in self.columns:
                if self[col].dtype in ['float64', 'float32', 'int64', 'int32']:
                    nan_count = self[col].isna().sum()
                    inf_count = np.isinf(self[col]).sum() if self[col].dtype in ['float64', 'float32'] else 0
                    if nan_count > 0 or inf_count > 0:
                        print(f"    PROBLEM COLUMN {col}: {nan_count} NaN, {inf_count} inf")
            
            try:
                result = original_merge(self, *args, **kwargs)
                print(f"  MERGE SUCCESS: result shape {result.shape}")
                return result
            except Exception as e:
                print(f"  MERGE FAILED: {e}")
                print(f"  Self dtypes: {dict(self.dtypes)}")
                if args:
                    print(f"  Other dtypes: {dict(args[0].dtypes) if hasattr(args[0], 'dtypes') else 'N/A'}")
                raise
        
        # Apply the monkey patch
        pd.DataFrame.merge = debug_merge
        
        print("Starting PopulationSim with debug patches...")
        run_ps.main()
        
        print("PopulationSim completed successfully!")
        return True
        
    except Exception as e:
        print(f"\nPopulationSim failed: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False
    
    finally:
        # Restore original merge function
        pd.DataFrame.merge = original_merge

if __name__ == "__main__":
    success = run_populationsim_with_enhanced_debug()
    sys.exit(0 if success else 1)
