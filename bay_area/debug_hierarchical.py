#!/usr/bin/env python3
"""
Debug the hierarchical consistency function
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(''), 'tm2_control_utils'))

from tm2_control_utils.config import *

print('=== Debugging Hierarchical Consistency Function ===')

# Load the data
print('Loading data...')
maz_df = pd.read_csv('output_2023/maz_marginals.csv')
taz_df = pd.read_csv('output_2023/taz_marginals.csv')
crosswalk_df = pd.read_csv('output_2023/geo_cross_walk_tm2_updated.csv')

print(f'Original TAZ shape: {taz_df.shape}')
print(f'Original TAZ index: {taz_df.index}')
print(f'TAZ columns: {list(taz_df.columns)}')

# Merge TAZ data with crosswalk to get MAZ mapping
taz_updated = taz_df.merge(crosswalk_df[['TAZ', 'MAZ']], on='TAZ', how='left')
print(f'After merge TAZ shape: {taz_updated.shape}')
print(f'After merge TAZ index: {taz_updated.index}')
print(f'After merge TAZ columns: {list(taz_updated.columns)}')

# Check the data types and sample data
print(f'TAZ MAZ column dtype: {taz_updated["MAZ"].dtype}')
print(f'Sample TAZ data:')
print(taz_updated[['TAZ', 'MAZ', 'hh_size_1']].head())

# Check for missing MAZs
missing_maz = taz_updated['MAZ'].isna().sum()
print(f'Missing MAZ count: {missing_maz}')

if missing_maz > 0:
    print('Dropping records with missing MAZ...')
    taz_updated = taz_updated.dropna(subset=['MAZ'])
    print(f'After dropping missing MAZ shape: {taz_updated.shape}')
    print(f'After dropping missing MAZ index: {taz_updated.index}')

# Test the specific problematic operation
print('\n=== Testing Problematic Operations ===')

# Group TAZ data by MAZ and sum the categories
existing_taz_controls = ['hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus']
taz_by_maz = taz_updated.groupby('MAZ')[existing_taz_controls].sum()
print(f'TAZ by MAZ shape: {taz_by_maz.shape}')
print(f'TAZ by MAZ index: {taz_by_maz.index}')

# Calculate current sums
current_sums = taz_by_maz.sum(axis=1)
print(f'Current sums shape: {current_sums.shape}')
print(f'Current sums index: {current_sums.index}')

# Try the map operation
print('\n=== Testing Map Operation ===')
maz_scale_lookup = pd.Series([1.0] * len(current_sums.index), index=current_sums.index)
print(f'MAZ scale lookup shape: {maz_scale_lookup.shape}')
print(f'MAZ scale lookup index: {maz_scale_lookup.index}')

try:
    taz_scale_factors = taz_updated['MAZ'].map(maz_scale_lookup)
    print(f'TAZ scale factors shape: {taz_scale_factors.shape}')
    print(f'TAZ scale factors index: {taz_scale_factors.index}')
    print('Map operation successful!')
except Exception as e:
    print(f'Map operation failed: {e}')
    
# Test the boolean mask operation
print('\n=== Testing Boolean Mask ===')
try:
    normal_scaling_mask = taz_scale_factors != 0.0
    print(f'Boolean mask shape: {normal_scaling_mask.shape}')
    print(f'Boolean mask index: {normal_scaling_mask.index}')
    
    # Test the actual problematic line
    test_result = taz_updated.loc[normal_scaling_mask, 'hh_size_1'] * taz_scale_factors[normal_scaling_mask]
    print('Boolean mask operation successful!')
except Exception as e:
    print(f'Boolean mask operation failed: {e}')
    import traceback
    traceback.print_exc()
