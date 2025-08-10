#!/usr/bin/env python3
"""
Quick check of employed column and occupation combinations
"""
import pandas as pd

persons = pd.read_csv('output_2023/seed_persons.csv')

print("Checking employed column:")
if 'employed' in persons.columns:
    print("✅ Employed column exists")
    print("Employed value counts:")
    print(persons['employed'].value_counts())
    
    print("\nOccupation by employed status:")
    print(persons.groupby(['employed', 'occupation']).size().unstack(fill_value=0))
    
    print("\nEmployed people by occupation:")
    employed_only = persons[persons['employed'] == 1]
    print(employed_only['occupation'].value_counts().sort_index())
else:
    print("❌ No employed column found")
    print("Available columns:", [col for col in persons.columns if 'employ' in col.lower()])
