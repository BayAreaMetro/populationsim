#!/usr/bin/env python3
"""
Quick fix to add missing num_hh column to MAZ marginals
"""
import pandas as pd
import numpy as np

# Read the current MAZ marginals
maz = pd.read_csv('output_2023/maz_marginals.csv')
print('Original columns:', list(maz.columns))

# Estimate households from population (using typical 2.5 persons per household)
# Subtract group quarters population first to get household population
household_pop = maz['total_pop'] - maz['gq_pop']
maz['num_hh'] = np.maximum(0, (household_pop / 2.5).round().astype(int))

print('Added num_hh column')
print('num_hh stats: min={}, max={}, sum={:,.0f}'.format(maz['num_hh'].min(), maz['num_hh'].max(), maz['num_hh'].sum()))

# Reorder columns to put num_hh after MAZ
cols = ['MAZ', 'num_hh'] + [col for col in maz.columns if col not in ['MAZ', 'num_hh']]
maz = maz[cols]

# Save the updated file
maz.to_csv('output_2023/maz_marginals.csv', index=False)
print('Updated maz_marginals.csv with num_hh column')
print('Final columns:', list(maz.columns))

# Also copy to the hh_gq working directory
maz.to_csv('hh_gq/tm2_working_dir/data/maz_marginals.csv', index=False)
print('Also updated hh_gq/tm2_working_dir/data/maz_marginals.csv')
