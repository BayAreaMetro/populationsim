#!/usr/bin/env python3
"""
Add total population control to MAZ marginals file

This script adds a total_pop column to the MAZ marginals file using the 
population data from maz_data.csv. This is necessary for hierarchical 
control consistency in PopulationSim.

The total population at MAZ level will serve as the base constraint that
TAZ-level age controls must sum to.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def add_population_control_to_maz():
    """Add total population control to MAZ marginals file"""
    
    data_dir = Path('.')
    
    print("=== ADDING TOTAL POPULATION CONTROL TO MAZ MARGINALS ===")
    
    # Load the MAZ data (has population totals)
    maz_data_file = data_dir / 'maz_data.csv'
    maz_marginals_file = data_dir / 'maz_marginals_hhgq.csv'
    
    if not maz_data_file.exists():
        print(f"ERROR: {maz_data_file} not found")
        return False
    
    if not maz_marginals_file.exists():
        print(f"ERROR: {maz_marginals_file} not found")
        return False
    
    # Load the data
    print(f"Loading MAZ data from {maz_data_file}")
    maz_data = pd.read_csv(maz_data_file)
    
    print(f"Loading MAZ marginals from {maz_marginals_file}")
    maz_marginals = pd.read_csv(maz_marginals_file)
    
    print(f"MAZ data shape: {maz_data.shape}")
    print(f"MAZ marginals shape: {maz_marginals.shape}")
    
    # Check if we have the right columns
    if 'POP' not in maz_data.columns:
        print("ERROR: POP column not found in maz_data.csv")
        return False
    
    if 'MAZ' not in maz_marginals.columns:
        print("ERROR: MAZ column not found in maz_marginals_hhgq.csv")
        return False
    
    # The MAZ data uses MAZ_ORIGINAL, but marginals uses MAZ
    # Let me check what the actual column names are
    print("MAZ data columns:", list(maz_data.columns)[:10])  # First 10 columns
    print("MAZ marginals columns:", list(maz_marginals.columns))
    
    # Map the MAZ data to marginals
    # First, let's see what the MAZ identifiers look like
    print(f"MAZ data MAZ range: {maz_data['MAZ_ORIGINAL'].min()} to {maz_data['MAZ_ORIGINAL'].max()}")
    print(f"MAZ marginals MAZ range: {maz_marginals['MAZ'].min()} to {maz_marginals['MAZ'].max()}")
    
    # Create a mapping from MAZ_ORIGINAL to POP
    maz_pop_mapping = maz_data.set_index('MAZ_ORIGINAL')['POP'].to_dict()
    
    # Add total_pop column to marginals
    print("Adding total_pop column to MAZ marginals...")
    maz_marginals['total_pop'] = maz_marginals['MAZ'].map(maz_pop_mapping)
    
    # Check for any missing mappings
    missing_pop = maz_marginals['total_pop'].isna().sum()
    if missing_pop > 0:
        print(f"WARNING: {missing_pop} MAZs have missing population data")
        print("MAZs with missing population:")
        missing_mazs = maz_marginals[maz_marginals['total_pop'].isna()]['MAZ'].values
        print(missing_mazs[:10])  # Show first 10
        
        # Fill missing with 0 (or you could interpolate/estimate)
        maz_marginals['total_pop'] = maz_marginals['total_pop'].fillna(0)
        print("Filled missing population values with 0")
    
    # Verify the results
    total_pop_maz = maz_marginals['total_pop'].sum()
    total_pop_data = maz_data['POP'].sum()
    print(f"Total population from MAZ data: {total_pop_data:,}")
    print(f"Total population in MAZ marginals: {total_pop_maz:,}")
    
    if abs(total_pop_maz - total_pop_data) < 100:  # Allow small rounding differences
        print("✅ Population totals match!")
    else:
        print(f"⚠️  Population totals don't match (difference: {abs(total_pop_maz - total_pop_data):,})")
    
    # Show some sample data
    print("\nSample of updated MAZ marginals:")
    print(maz_marginals[['MAZ', 'numhh_gq', 'total_pop']].head(10))
    
    # Save the updated marginals file
    backup_file = data_dir / 'maz_marginals_hhgq_backup.csv'
    if not backup_file.exists():
        print(f"Creating backup: {backup_file}")
        maz_marginals_original = pd.read_csv(maz_marginals_file)
        maz_marginals_original.to_csv(backup_file, index=False)
    
    print(f"Saving updated MAZ marginals to {maz_marginals_file}")
    maz_marginals.to_csv(maz_marginals_file, index=False)
    
    print("=== TOTAL POPULATION CONTROL ADDED SUCCESSFULLY ===")
    return True

if __name__ == "__main__":
    add_population_control_to_maz()
