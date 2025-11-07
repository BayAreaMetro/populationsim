#!/usr/bin/env python3
"""
Quick summary of household counts by MAZ (both new and original IDs)
"""
import pandas as pd

# Read the households file
df = pd.read_csv(r'output_2023\populationsim_working_dir\output\households_2023_tm2.csv')

print('=== HOUSEHOLD COUNT BY MAZ (NEW AND ORIGINAL) ===')
print(f'Total households: {len(df):,}')
print()

# Count households by both new and original MAZ
maz_summary = df.groupby(['MAZ_SEQ', 'MAZ_NODE']).size().reset_index(name='household_count')
maz_summary = maz_summary.sort_values('household_count', ascending=False)

print('Top 20 MAZ by household count:')
print('MAZ_SEQ  MAZ_NODE      Households')
print('-' * 35)
for _, row in maz_summary.head(20).iterrows():
    print(f'{row.MAZ_SEQ:7d}  {row.MAZ_NODE:11.0f}  {row.household_count:10d}')
print()

# Summary statistics
new_maz_counts = df.groupby('MAZ_SEQ').size()
print('Summary Statistics:')
print(f'Unique MAZ_SEQ zones: {len(new_maz_counts):,}')
print(f'Unique MAZ_NODE zones: {df.MAZ_NODE.nunique():,}')
print()

# ID Range Information
print('MAZ ID Ranges:')
print(f'MAZ_SEQ range: {df.MAZ_SEQ.min():,} to {df.MAZ_SEQ.max():,}')
print(f'MAZ_NODE range: {df.MAZ_NODE.min():,.0f} to {df.MAZ_NODE.max():,.0f}')
print()

# Household distribution statistics
print('Household Distribution:')
print(f'Average households per MAZ: {new_maz_counts.mean():.1f}')
print(f'Median households per MAZ: {new_maz_counts.median():.1f}')
print(f'Max households in single MAZ: {new_maz_counts.max():,}')
print(f'Min households in single MAZ: {new_maz_counts.min():,}')
print()

# Distribution
print('Household count distribution:')
print(f'MAZ with 1-10 households: {(new_maz_counts <= 10).sum():,}')
print(f'MAZ with 11-50 households: {((new_maz_counts > 10) & (new_maz_counts <= 50)).sum():,}')
print(f'MAZ with 51-100 households: {((new_maz_counts > 50) & (new_maz_counts <= 100)).sum():,}')
print(f'MAZ with 100+ households: {(new_maz_counts > 100).sum():,}')



