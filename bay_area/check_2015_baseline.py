#!/usr/bin/env python3
"""
Check the 2015 baseline file that compare_synthetic_populations actually uses
"""
import pandas as pd

# Load the 2015 file used by compare_synthetic_populations  
print("Loading full 2015 file...")
old_persons = pd.read_csv('example_2015_outputs/hh_persons_model/persons.csv')
print('Total records in 2015 file:', len(old_persons))

print()
print('SCHG value counts from 2015 file (compare_synthetic_populations uses):')
schg_counts = old_persons['SCHG'].value_counts().sort_index()
print(schg_counts)

print()
print('SCHL value counts from 2015 file:')  
schl_counts = old_persons['SCHL'].value_counts().sort_index()
print(schl_counts)
