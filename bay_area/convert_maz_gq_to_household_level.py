#!/usr/bin/env python3
"""
Simple script to convert MAZ GQ controls from person-level to household-level
for PopulationSim compatibility.
"""

import pandas as pd
import os

def main():
    print("Converting MAZ GQ controls from person-level to household-level...")
    
    # Input and output files
    input_file = "output_2023/populationsim_working_dir/data/maz_marginals_hhgq.csv"
    output_file = "output_2023/populationsim_working_dir/data/maz_marginals.csv"
    
    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}")
        return
    
    # Read the existing MAZ data with person-level GQ
    print(f"Reading {input_file}")
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} MAZ zones")
    
    # Convert person-level GQ to household-level GQ
    # University dorms: ~2.5 people per household
    # Military barracks: ~3.0 people per household  
    # Other noninstitutional: ~2.0 people per household
    
    print("Converting person-level to household-level GQ...")
    df['hh_gq_university'] = (df['gq_university'] / 2.5).round().astype(int)
    df['hh_gq_noninstitutional'] = ((df['gq_military'] / 3.0) + (df['gq_noninstitutional'] / 2.0)).round().astype(int) 
    df['hh_gq_total'] = df['hh_gq_university'] + df['hh_gq_noninstitutional']
    
    # Update numhh_gq to include GQ households
    df['numhh_gq'] = df['num_hh'] + df['hh_gq_total']
    
    # Select only the columns PopulationSim expects
    output_cols = ['MAZ', 'num_hh', 'total_pop', 'numhh_gq', 'hh_gq_total', 'hh_gq_university', 'hh_gq_noninstitutional']
    df_output = df[output_cols].copy()
    
    print("Conversion results:")
    print(f"  University GQ households: {df_output['hh_gq_university'].sum():,}")
    print(f"  Noninstitutional GQ households: {df_output['hh_gq_noninstitutional'].sum():,}")
    print(f"  Total GQ households: {df_output['hh_gq_total'].sum():,}")
    print(f"  Regular households: {df_output['num_hh'].sum():,}")
    print(f"  Total households (numhh_gq): {df_output['numhh_gq'].sum():,}")
    
    # Write the converted file
    print(f"Writing {output_file}")
    df_output.to_csv(output_file, index=False)
    print("✅ MAZ controls converted successfully!")
    
    # Show a sample of the output
    print("\nSample output:")
    print(df_output.head())

if __name__ == "__main__":
    main()