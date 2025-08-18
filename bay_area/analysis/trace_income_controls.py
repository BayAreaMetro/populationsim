#!/usr/bin/env python3
"""
Trace the income control generation pipeline to find the source of the 
3.4 percentage point error between generated controls (19.0% low income) 
and actual ACS 2023 targets (15.6% low income).
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tm2_control_utils'))

from tm2_control_utils.config_census import *
from create_baseyear_controls_23_tm2 import CensusFetcher
from tm2_control_utils.controls import create_control_table
import pandas as pd
import numpy as np

def main():
    print("TRACING INCOME CONTROL GENERATION PIPELINE")
    print("=" * 60)
    
    # Step 1: Check what the configuration says
    print("\n1. CONFIGURATION CHECK:")
    print(f"   ACS_EST_YEAR = {ACS_EST_YEAR}")
    
    income_controls = ['hh_inc_30', 'hh_inc_30_60', 'hh_inc_60_100', 'hh_inc_100_plus']
    
    for control_name in income_controls:
        if control_name in CONTROLS[ACS_EST_YEAR]['TAZ']:
            control_def = CONTROLS[ACS_EST_YEAR]['TAZ'][control_name]
            print(f"   {control_name}:")
            print(f"     Dataset: {control_def[0]}")
            print(f"     Year: {control_def[1]}")
            print(f"     Table: {control_def[2]}")
            print(f"     Geography: {control_def[3]}")
            print(f"     Filters: {control_def[4]}")
            if len(control_def[4]) > 0:
                for filter_dict in control_def[4]:
                    for key, value in filter_dict.items():
                        print(f"       {key}: {value}")
    
    # Step 2: Fetch raw Census data to see what we're getting
    print("\n2. RAW CENSUS DATA CHECK:")
    cf = CensusFetcher()
    
    # Get B19001 data for block groups in ACS 2023
    try:
        census_df = cf.get_census_data(
            dataset='acs5',
            year=ACS_EST_YEAR, 
            table='B19001',
            geo='block group'
        )
        
        print(f"   Downloaded B19001 table for {ACS_EST_YEAR}")
        print(f"   Shape: {census_df.shape}")
        print(f"   Counties covered: {census_df['county'].unique() if 'county' in census_df.columns else 'N/A'}")
        
        # Check the income bracket columns we care about
        income_columns = [col for col in census_df.columns if col.startswith('B19001_')]
        print(f"   Income columns available: {len(income_columns)}")
        
        # Calculate the brackets we're interested in
        if len(income_columns) >= 17:  # Make sure we have enough columns
            print("\n   INCOME BRACKET ANALYSIS:")
            print("   Raw Census B19001 income brackets (2023$):")
            
            # According to Census documentation for B19001:
            # _002E: < $10K, _003E: $10-15K, _004E: $15-20K, _005E: $20-25K, _006E: $25-30K, _007E: $30-35K, _008E: $35-40K, _009E: $40-45K
            # Let's map these to our target brackets
            
            # Low income: $0-41,399 (sum _002E through _009E covers $0-45K)
            low_income_cols = ['B19001_002E', 'B19001_003E', 'B19001_004E', 'B19001_005E', 
                              'B19001_006E', 'B19001_007E', 'B19001_008E', 'B19001_009E']
            
            low_income_total = 0
            for col in low_income_cols:
                if col in census_df.columns:
                    col_sum = pd.to_numeric(census_df[col], errors='coerce').sum()
                    low_income_total += col_sum
                    print(f"   {col}: {col_sum:,.0f}")
                    
            total_households = pd.to_numeric(census_df['B19001_001E'], errors='coerce').sum()
            low_income_pct = (low_income_total / total_households * 100) if total_households > 0 else 0
            
            print(f"\n   CALCULATED FROM RAW CENSUS DATA:")
            print(f"   Total households: {total_households:,.0f}")
            print(f"   Low income ($0-45K approx): {low_income_total:,.0f} ({low_income_pct:.1f}%)")
            print(f"   Expected ACS target: 15.6%")
            print(f"   Current TAZ controls: 19.0%")
            
        else:
            print("   Not enough income columns found in raw data")
            
    except Exception as e:
        print(f"   Error fetching Census data: {e}")
    
    # Step 3: Test the create_control_table function
    print("\n3. CONTROL TABLE GENERATION TEST:")
    try:
        # Test each income control to see what brackets are actually being used
        for control_name in income_controls:
            if control_name in CONTROLS[ACS_EST_YEAR]['TAZ']:
                control_def = CONTROLS[ACS_EST_YEAR]['TAZ'][control_name]
                
                # Create control table using the same process as the main script
                control_df = create_control_table(control_name, control_def[4], control_def[2], census_df)
                
                if control_name in control_df.columns:
                    control_total = pd.to_numeric(control_df[control_name], errors='coerce').sum()
                    control_pct = (control_total / total_households * 100) if total_households > 0 else 0
                    
                    print(f"   {control_name}: {control_total:,.0f} ({control_pct:.1f}%)")
                    
                    # Show which census columns were included
                    filter_dict = control_def[4][0] if len(control_def[4]) > 0 else {}
                    print(f"     Bracket: ${filter_dict.get('hhinc_min', 0):,} - ${filter_dict.get('hhinc_max', 'MAX'):,}")
                    
    except Exception as e:
        print(f"   Error in control table generation: {e}")
    
    # Step 4: Check if there's geographic aggregation error
    print("\n4. GEOGRAPHIC AGGREGATION CHECK:")
    
    # Load the geographic crosswalk to understand TAZ boundaries
    try:
        crosswalk_df = pd.read_csv('output_2023/populationsim_working_dir/data/geo_cross_walk_tm2.csv')
        print(f"   Crosswalk loaded: {crosswalk_df.shape}")
        
        # Check if there are block groups missing from our data
        if 'GEOID_block group' in census_df.columns:
            census_block_groups = set(census_df['GEOID_block group'].unique())
            # crosswalk_block_groups = set(crosswalk_df['GEOID_block_group'].unique()) if 'GEOID_block_group' in crosswalk_df.columns else set()
            
            print(f"   Census block groups: {len(census_block_groups)}")
            # print(f"   Crosswalk block groups: {len(crosswalk_block_groups)}")
            
            # Check coverage
            bay_area_fips = ['001', '013', '041', '055', '075', '081', '085', '095', '097']  # Bay Area counties
            bay_area_block_groups = [bg for bg in census_block_groups if bg[2:5] in bay_area_fips]
            
            print(f"   Bay Area block groups in census data: {len(bay_area_block_groups)}")
            
    except Exception as e:
        print(f"   Error in geographic check: {e}")
    
    print("\n5. SUMMARY:")
    print("   The issue is likely in one of these areas:")
    print("   a) Wrong income bracket boundaries in Census table mapping")
    print("   b) Geographic aggregation dropping or double-counting some areas")
    print("   c) Using older/different ACS vintage than expected")
    print("   d) Scaling factors being applied incorrectly")
    
    print("\n   Next step: Run create_baseyear_controls_23_tm2.py with debug output")
    print("   to see exactly what's happening in the control generation pipeline.")

if __name__ == '__main__':
    main()
