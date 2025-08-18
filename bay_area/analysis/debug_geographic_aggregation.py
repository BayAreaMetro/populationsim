"""
debug_geographic_aggregation.py

This script debugs the geographic aggregation process that's causing the income 
distribution distortion from 15.2% to 19.0% low-income households.

We've identified that the issue occurs during block group → TAZ aggregation 
in the match_control_to_geography function.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tm2_control_utils'))

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from tm2_control_utils.config_census import *
from tm2_control_utils.census_fetcher import CensusFetcher
from tm2_control_utils.geog_utils import prepare_geography_dfs
from tm2_control_utils.controls import create_control_table, match_control_to_geography

def debug_income_aggregation():
    """Debug the geographic aggregation process for income controls."""
    
    print("=== DEBUGGING GEOGRAPHIC AGGREGATION FOR INCOME CONTROLS ===")
    
    # Step 1: Load geographic crosswalk
    print("\n1. LOADING GEOGRAPHIC CROSSWALK...")
    maz_taz_file = os.path.join("output_2023", "populationsim_working_dir", "data", "geo_cross_walk_tm2.csv")
    
    if not os.path.exists(maz_taz_file):
        print(f"ERROR: Geographic crosswalk file not found at {maz_taz_file}!")
        return
    
    maz_taz_df = pd.read_csv(maz_taz_file)
    print(f"   - Loaded {len(maz_taz_df)} geographic mapping records")
    print(f"   - Columns: {list(maz_taz_df.columns)}")
    
    # Step 2: Load cached Census income data from M drive
    print("\n2. LOADING CACHED CENSUS INCOME DATA...")
    
    # Use the network census cache location from unified_tm2_config
    census_cache_dir = Path("M:/Data/Census/NewCachedTablesForPopulationSimControls")
    
    # Look for B19001 (household income) files
    b19001_files = list(census_cache_dir.glob("*B19001*.csv"))
    print(f"   - Found {len(b19001_files)} B19001 files in cache")
    
    if not b19001_files:
        print("   ERROR: No B19001 files found in census cache!")
        return
    
    # Load the most relevant B19001 file (block group level)
    income_file = None
    for file in b19001_files:
        if 'block_group' in file.name or 'bg' in file.name.lower():
            income_file = file
            break
    
    if not income_file:
        # Just use the first B19001 file if we can't find block group specific
        income_file = b19001_files[0]
    
    print(f"   - Loading income data from: {income_file.name}")
    combined_income = pd.read_csv(income_file)
    print(f"   - Loaded {len(combined_income)} income records")
    
    # Step 3: Create income control table (just for low-income category)
    print("\n3. CREATING INCOME CONTROL TABLE...")
    
    # Create control table for hh_inc_30 (low-income households)
    control_dict_list = [collections.OrderedDict([('hhinc_min',0), ('hhinc_max',41399)])]
    
    control_table_df = create_control_table(
        'hh_inc_30', control_dict_list, 'B19001', combined_income
    )
    
    bg_total_hh = control_table_df['hh_inc_30'].sum()
    print(f"   - Block group total low-income households: {bg_total_hh:,.0f}")
    
    # Also get total households for percentage calculation
    total_hh_bg = combined_income['B19001_001E'].sum()  # Total households from B19001
    bg_percentage = (bg_total_hh / total_hh_bg) * 100
    print(f"   - Block group total households: {total_hh_bg:,.0f}")
    print(f"   - Block group low-income percentage: {bg_percentage:.1f}%")
    
    # Step 4: Debug the geographic aggregation process
    print("\n4. DEBUGGING GEOGRAPHIC AGGREGATION...")
    
    # Examine the block group → TAZ mapping
    if 'GEOID_block group' in maz_taz_df.columns and 'TAZ' in maz_taz_df.columns:
        bg_taz_mapping = maz_taz_df[['GEOID_block group', 'TAZ']].drop_duplicates()
        print(f"   - Block group → TAZ mappings: {len(bg_taz_mapping)}")
        
        # Check for one-to-many relationships (one BG mapping to multiple TAZs)
        bg_counts = bg_taz_mapping['GEOID_block group'].value_counts()
        multiple_taz_bgs = bg_counts[bg_counts > 1]
        print(f"   - Block groups mapped to multiple TAZs: {len(multiple_taz_bgs)}")
        
        if len(multiple_taz_bgs) > 0:
            print(f"   - Example: BG {multiple_taz_bgs.index[0]} → {bg_counts.iloc[0]} TAZs")
            example_mappings = bg_taz_mapping[
                bg_taz_mapping['GEOID_block group'] == multiple_taz_bgs.index[0]
            ]
            print(f"     TAZs: {example_mappings['TAZ'].tolist()}")
        
        # Check for many-to-one relationships (multiple BGs mapping to one TAZ)
        taz_counts = bg_taz_mapping['TAZ'].value_counts()
        print(f"   - TAZs receiving data from multiple BGs: {len(taz_counts[taz_counts > 1])}")
        print(f"   - Average BGs per TAZ: {taz_counts.mean():.1f}")
        print(f"   - Max BGs per TAZ: {taz_counts.max()}")
    
    # Step 5: Perform the actual aggregation and compare
    print("\n5. PERFORMING AGGREGATION...")
    
    try:
        # Use the same aggregation logic as the main pipeline
        aggregated_df = match_control_to_geography(
            'hh_inc_30', control_table_df, 'TAZ', 'block group',
            maz_taz_df, {},
            scale_numerator=None, scale_denominator=None,
            subtract_table=None
        )
        
        taz_total_hh = aggregated_df['hh_inc_30'].sum()
        print(f"   - TAZ total low-income households: {taz_total_hh:,.0f}")
        
        # Calculate the scaling factor
        scaling_factor = taz_total_hh / bg_total_hh
        print(f"   - BG → TAZ scaling factor: {scaling_factor:.6f}")
        print(f"   - Change: {((scaling_factor - 1.0) * 100):+.2f}%")
        
        # Now we need total households at TAZ level for percentage
        # Let's get the TAZ marginals from the actual output to compare
        marginals_file = os.path.join("output_2023", "taz_marginals.csv")
        if os.path.exists(marginals_file):
            taz_marginals = pd.read_csv(marginals_file, index_col='TAZ')
            if 'hh_inc_30' in taz_marginals.columns:
                marginals_low_income = taz_marginals['hh_inc_30'].sum()
                print(f"   - TAZ marginals low-income households: {marginals_low_income:,.0f}")
                
                if 'num_hh' in taz_marginals.columns:
                    marginals_total_hh = taz_marginals['num_hh'].sum()
                    marginals_percentage = (marginals_low_income / marginals_total_hh) * 100
                    print(f"   - TAZ marginals total households: {marginals_total_hh:,.0f}")
                    print(f"   - TAZ marginals low-income percentage: {marginals_percentage:.1f}%")
    
    except Exception as e:
        print(f"   - ERROR during aggregation: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 6: Examine specific problematic areas
    print("\n6. IDENTIFYING PROBLEMATIC MAPPINGS...")
    
    try:
        # Look for block groups with high income households that might be 
        # getting distributed to low-income TAZs
        
        # Add GEOID column to control table if not present
        if 'GEOID_block group' not in control_table_df.columns:
            # Extract GEOID from index or create it
            if control_table_df.index.name and 'bg' in control_table_df.index.name.lower():
                control_table_df['GEOID_block group'] = control_table_df.index
            else:
                print("   - Cannot identify block group GEOIDs for detailed analysis")
                return
        
        # Merge control data with geographic mapping
        merged_analysis = pd.merge(
            control_table_df.reset_index(),
            maz_taz_df[['GEOID_block group', 'TAZ']].drop_duplicates(),
            on='GEOID_block group',
            how='inner'
        )
        
        print(f"   - Successfully merged {len(merged_analysis)} BG→TAZ mappings")
        
        # Look at the distribution by TAZ
        taz_analysis = merged_analysis.groupby('TAZ').agg({
            'hh_inc_30': 'sum',
            'GEOID_block group': 'count'
        }).rename(columns={'GEOID_block group': 'num_bgs'})
        
        # Sort by low-income households to see which TAZs have the most
        taz_analysis = taz_analysis.sort_values('hh_inc_30', ascending=False)
        
        print("   - Top 10 TAZs by low-income households:")
        for taz, row in taz_analysis.head(10).iterrows():
            print(f"     TAZ {taz}: {row['hh_inc_30']:,.0f} low-income HH from {row['num_bgs']} BGs")
    
    except Exception as e:
        print(f"   - ERROR in detailed analysis: {e}")
    
    print("\n=== DEBUGGING COMPLETE ===")

if __name__ == "__main__":
    debug_income_aggregation()
