#!/usr/bin/env python3
"""
Verify that household size columns sum to total household count.
This script checks if hh_size_1 + hh_size_2 + hh_size_3 + hh_size_4_plus equals the total households.
"""

import sys
import os
import logging
import pandas as pd

# Add the tm2_control_utils directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tm2_control_utils'))

from controls import create_control_table, get_census_data, add_geoid_columns
from config import CENSUS_DEFINITIONS, ACS_EST_YEAR
import collections

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def verify_household_totals():
    """Verify that household size columns sum to total households"""
    
    print("=== Verifying Household Size Totals ===")
    
    # Get the ACS B11016 data (household size by type)
    print("Getting B11016 household size data...")
    df = get_census_data('acs5', ACS_EST_YEAR, 'B11016', 'block group')
    df = add_geoid_columns(df, 'block group')
    
    print(f"Data shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    # Create individual household size controls
    print("\n=== Creating individual household size controls ===")
    
    # hh_size_1 (1-person households)
    hh_size_1_def = [collections.OrderedDict([('pers_min', 1), ('pers_max', 1)])]
    hh_size_1_df = create_control_table(df, 'B11016', hh_size_1_def, 'hh_size_1')
    
    # hh_size_2 (2-person households) 
    hh_size_2_def = [collections.OrderedDict([('pers_min', 2), ('pers_max', 2)])]
    hh_size_2_df = create_control_table(df, 'B11016', hh_size_2_def, 'hh_size_2')
    
    # hh_size_3 (3-person households)
    hh_size_3_def = [collections.OrderedDict([('pers_min', 3), ('pers_max', 3)])]
    hh_size_3_df = create_control_table(df, 'B11016', hh_size_3_def, 'hh_size_3')
    
    # hh_size_4_plus (4+ person households)
    hh_size_4_plus_def = [collections.OrderedDict([('pers_min', 4), ('pers_max', 10)])]
    hh_size_4_plus_df = create_control_table(df, 'B11016', hh_size_4_plus_def, 'hh_size_4_plus')
    
    # Create total households control (all households regardless of size)
    total_hh_def = [collections.OrderedDict([('pers_min', 1), ('pers_max', 10)])]
    total_hh_df = create_control_table(df, 'B11016', total_hh_def, 'total_hh')
    
    print("\n=== Sample values ===")
    print(f"hh_size_1 sample: {hh_size_1_df['hh_size_1'].head().tolist()}")
    print(f"hh_size_2 sample: {hh_size_2_df['hh_size_2'].head().tolist()}")
    print(f"hh_size_3 sample: {hh_size_3_df['hh_size_3'].head().tolist()}")
    print(f"hh_size_4_plus sample: {hh_size_4_plus_df['hh_size_4_plus'].head().tolist()}")
    print(f"total_hh sample: {total_hh_df['total_hh'].head().tolist()}")
    
    # Merge all controls on GEOID_block group
    print("\n=== Merging household size controls ===")
    merged_df = hh_size_1_df[['GEOID_block group', 'hh_size_1']].copy()
    merged_df = merged_df.merge(hh_size_2_df[['GEOID_block group', 'hh_size_2']], on='GEOID_block group', how='outer')
    merged_df = merged_df.merge(hh_size_3_df[['GEOID_block group', 'hh_size_3']], on='GEOID_block group', how='outer')
    merged_df = merged_df.merge(hh_size_4_plus_df[['GEOID_block group', 'hh_size_4_plus']], on='GEOID_block group', how='outer')
    merged_df = merged_df.merge(total_hh_df[['GEOID_block group', 'total_hh']], on='GEOID_block group', how='outer')
    
    # Fill NaN values with 0
    for col in ['hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus', 'total_hh']:
        merged_df[col] = merged_df[col].fillna(0)
    
    print(f"Merged data shape: {merged_df.shape}")
    
    # Calculate sum of household size categories
    merged_df['calculated_total'] = (merged_df['hh_size_1'] + 
                                   merged_df['hh_size_2'] + 
                                   merged_df['hh_size_3'] + 
                                   merged_df['hh_size_4_plus'])
    
    # Calculate difference
    merged_df['difference'] = merged_df['total_hh'] - merged_df['calculated_total']
    
    print("\n=== Verification Results ===")
    print(f"Total rows: {len(merged_df)}")
    print(f"Rows with perfect match (difference = 0): {(merged_df['difference'] == 0).sum()}")
    print(f"Rows with differences: {(merged_df['difference'] != 0).sum()}")
    
    # Show statistics about differences
    print(f"\nDifference statistics:")
    print(f"Mean difference: {merged_df['difference'].mean():.2f}")
    print(f"Max difference: {merged_df['difference'].max():.2f}")
    print(f"Min difference: {merged_df['difference'].min():.2f}")
    print(f"Standard deviation: {merged_df['difference'].std():.2f}")
    
    # Show some examples
    print(f"\n=== Sample comparisons (first 10 rows) ===")
    sample_df = merged_df.head(10)[['GEOID_block group', 'hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus', 'calculated_total', 'total_hh', 'difference']]
    print(sample_df.to_string(index=False))
    
    # Show rows with largest discrepancies
    if (merged_df['difference'] != 0).any():
        print(f"\n=== Rows with largest discrepancies ===")
        discrepancy_df = merged_df[merged_df['difference'] != 0].nlargest(5, 'difference')[['GEOID_block group', 'hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus', 'calculated_total', 'total_hh', 'difference']]
        print(discrepancy_df.to_string(index=False))
    
    # Save detailed results
    output_file = 'household_totals_verification.csv'
    merged_df.to_csv(output_file, index=False)
    print(f"\nDetailed results saved to: {output_file}")
    
    # Summary
    total_sum_difference = merged_df['difference'].sum()
    print(f"\n=== SUMMARY ===")
    print(f"Total households from B11016_001E: {merged_df['total_hh'].sum():.0f}")
    print(f"Sum of all household size categories: {merged_df['calculated_total'].sum():.0f}")
    print(f"Overall difference: {total_sum_difference:.0f}")
    
    if abs(total_sum_difference) < 1:
        print("✅ PASSED: Household size categories sum correctly to total households")
    else:
        print("❌ FAILED: Household size categories do not sum to total households")
        print(f"   Difference of {total_sum_difference:.0f} households found")

if __name__ == "__main__":
    verify_household_totals()
