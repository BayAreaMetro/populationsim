#!/usr/bin/env python3
"""
Compare SCHL and SCHG distributions between 2015 and 2023
"""
import pandas as pd

print('=== SCHL COUNTS BY YEAR ===')

# Load 2015 data 
old_persons = pd.read_csv('example_2015_outputs/hh_persons_model/persons.csv')
schl_2015 = old_persons['SCHL'].value_counts().sort_index()

# Load 2023 data
persons_2023 = pd.read_csv('output_2023/populationsim_working_dir/output/persons_2023_tm2.csv')
schl_2023 = persons_2023['SCHL'].value_counts().sort_index()

# Create comparison dataframe for SCHL
schl_comparison = pd.DataFrame({
    '2015': schl_2015,
    '2023': schl_2023
}).fillna(0).astype(int)

print(schl_comparison)

print()
print('=== SCHG COUNTS BY YEAR ===')

# SCHG comparison
schg_2015 = old_persons['SCHG'].value_counts().sort_index()
schg_2023 = persons_2023['SCHG'].value_counts().sort_index()

schg_comparison = pd.DataFrame({
    '2015': schg_2015, 
    '2023': schg_2023
}).fillna(0).astype(int)

print(schg_comparison)
