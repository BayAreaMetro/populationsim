#!/usr/bin/env python3
"""
Analyze 2015 SCHL patterns to understand educational attainment mapping
"""
import pandas as pd

print('=== ANALYZING 2015 SCHL PATTERNS ===')
print('Loading 2015 data...')
df_2015 = pd.read_csv('example_2015_outputs/hh_persons_model/persons.csv', nrows=100000)

print()
print('2015 SCHL by Age Patterns:')
for schl_val in sorted(df_2015['SCHL'].unique()):
    ages = df_2015[df_2015['SCHL'] == schl_val]['AGEP']
    if len(ages) > 0:
        count = len(ages)
        print(f'SCHL {schl_val:2d}: ages {ages.min():2d}-{ages.max():2d}, median {ages.median():4.1f}, count {count:5d}')

print()
print('=== INFERRING SCHL MAPPING LOGIC ===')
print('Based on age patterns, 2015 SCHL seems to represent:')
print('SCHL -9: N/A (very young children)')
print('SCHL 1-2: Minimal education (broad age range)')  
print('SCHL 3-8: Elementary through some high school')
print('SCHL 9: Major category (wide age range - likely "some high school")')
print('SCHL 10-16: Different education completion levels')

print()
print('Need to map 2023 PUMS detailed codes (0-24) to these 2015 categories (1-16)')



