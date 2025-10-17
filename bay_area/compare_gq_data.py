#!/usr/bin/env python3

import pandas as pd

# Read both files
univ = pd.read_csv('M:/Data/Census/NewCachedTablesForPopulationSimControls/pl_2020_P5_008N_block.csv')
mil = pd.read_csv('M:/Data/Census/NewCachedTablesForPopulationSimControls/pl_2020_P5_009N_block.csv')

print('UNIVERSITY GQ (P5_008N):')
print(f'  Total: {univ["P5_008N"].sum():,}')
print(f'  Non-zero blocks: {(univ["P5_008N"] > 0).sum():,}')
print(f'  Max value: {univ["P5_008N"].max():,}')
if (univ['P5_008N'] > 0).sum() > 0:
    print(f'  Mean (non-zero): {univ[univ["P5_008N"] > 0]["P5_008N"].mean():.1f}')

print()
print('MILITARY GQ (P5_009N):')  
print(f'  Total: {mil["P5_009N"].sum():,}')
print(f'  Non-zero blocks: {(mil["P5_009N"] > 0).sum():,}')
print(f'  Max value: {mil["P5_009N"].max():,}')
if (mil['P5_009N'] > 0).sum() > 0:
    print(f'  Mean (non-zero): {mil[mil["P5_009N"] > 0]["P5_009N"].mean():.1f}')

# Check concentration - are university blocks highly concentrated?
print()
print('CONCENTRATION ANALYSIS:')
univ_nonzero = univ[univ['P5_008N'] > 0]['P5_008N']
mil_nonzero = mil[mil['P5_009N'] > 0]['P5_009N']

if len(univ_nonzero) > 0:
    print(f'University GQ - Top 10 blocks: {sorted(univ_nonzero, reverse=True)[:10]}')
if len(mil_nonzero) > 0:
    print(f'Military GQ - Top 10 blocks: {sorted(mil_nonzero, reverse=True)[:10]}')

# Check geographic distribution by county
print()
print('COUNTY DISTRIBUTION:')
univ_by_county = univ.groupby('county')['P5_008N'].sum()
mil_by_county = mil.groupby('county')['P5_009N'].sum()

print('University GQ by county:')
for county, total in univ_by_county[univ_by_county > 0].items():
    print(f'  County {county:03d}: {total:,}')
    
print('Military GQ by county:')
for county, total in mil_by_county[mil_by_county > 0].items():
    print(f'  County {county:03d}: {total:,}')