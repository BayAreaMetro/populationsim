"""
Analyze SCHL and SCHG field differences between 2015 and 2023 synthetic populations.
Compare patterns by age, employment status, and ESR to understand encoding differences.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_education_patterns():
    print('=== LOADING DATA ===')
    
    # Load 2015 data
    old_persons = pd.read_csv('example_2015_outputs/hh_persons_model/persons.csv')
    print(f'2015 data loaded: {len(old_persons):,} records')
    
    # Load 2023 PUMS data (since we may not have final output yet)
    pums_file = Path('M:/Data/Census/PUMS_2023_5Year_Crosswalked/bay_area_persons_2019_2023_crosswalked.csv')
    if pums_file.exists():
        persons_2023 = pd.read_csv(pums_file, nrows=200000)  # Sample for faster analysis
        print(f'2023 PUMS data loaded: {len(persons_2023):,} records')
    else:
        print('Could not find 2023 PUMS file')
        return
    
    print('\n=== BASIC FIELD RANGES ===')
    print('2015 SCHL range:', sorted(old_persons['SCHL'].unique()))
    print('2023 SCHL range:', sorted(persons_2023['SCHL'].unique()))
    print('2015 SCHG range:', sorted(old_persons['SCHG'].unique()))
    print('2023 SCHG range:', sorted(persons_2023['SCHG'].unique()))
    
    # Age group analysis
    print('\n=== SCHL BY AGE GROUPS ===')
    age_bins = [0, 5, 12, 18, 25, 35, 50, 65, 100]
    age_labels = ['0-4', '5-11', '12-17', '18-24', '25-34', '35-49', '50-64', '65+']
    
    old_persons['age_group'] = pd.cut(old_persons['AGEP'], bins=age_bins, labels=age_labels, right=False)
    persons_2023['age_group'] = pd.cut(persons_2023['AGEP'], bins=age_bins, labels=age_labels, right=False)
    
    print('\n2015 SCHL by Age Group:')
    schl_age_2015 = old_persons.groupby(['age_group', 'SCHL']).size().unstack(fill_value=0)
    print(schl_age_2015)
    
    print('\n2023 SCHL by Age Group:')
    schl_age_2023 = persons_2023.groupby(['age_group', 'SCHL']).size().unstack(fill_value=0)
    print(schl_age_2023)
    
    print('\n=== SCHG BY AGE GROUPS ===')
    print('\n2015 SCHG by Age Group:')
    schg_age_2015 = old_persons.groupby(['age_group', 'SCHG']).size().unstack(fill_value=0)
    print(schg_age_2015)
    
    print('\n2023 SCHG by Age Group:')
    schg_age_2023 = persons_2023.groupby(['age_group', 'SCHG']).size().unstack(fill_value=0)
    print(schg_age_2023)
    
    # Employment analysis
    if 'EMPLOYED' in old_persons.columns and 'EMPLOYED' in persons_2023.columns:
        print('\n=== SCHL BY EMPLOYED STATUS ===')
        print('\n2015 SCHL by EMPLOYED:')
        schl_emp_2015 = old_persons.groupby(['EMPLOYED', 'SCHL']).size().unstack(fill_value=0)
        print(schl_emp_2015)
        
        print('\n2023 SCHL by EMPLOYED:')
        schl_emp_2023 = persons_2023.groupby(['EMPLOYED', 'SCHL']).size().unstack(fill_value=0)
        print(schl_emp_2023)
        
        print('\n=== SCHG BY EMPLOYED STATUS ===')
        print('\n2015 SCHG by EMPLOYED:')
        schg_emp_2015 = old_persons.groupby(['EMPLOYED', 'SCHG']).size().unstack(fill_value=0)
        print(schg_emp_2015)
        
        print('\n2023 SCHG by EMPLOYED:')
        schg_emp_2023 = persons_2023.groupby(['EMPLOYED', 'SCHG']).size().unstack(fill_value=0)
        print(schg_emp_2023)
    
    # ESR analysis
    if 'ESR' in old_persons.columns and 'ESR' in persons_2023.columns:
        print('\n=== SCHL BY ESR ===')
        print('\n2015 SCHL by ESR:')
        schl_esr_2015 = old_persons.groupby(['ESR', 'SCHL']).size().unstack(fill_value=0)
        print(schl_esr_2015)
        
        print('\n2023 SCHL by ESR:')
        schl_esr_2023 = persons_2023.groupby(['ESR', 'SCHL']).size().unstack(fill_value=0)
        print(schl_esr_2023)
        
        print('\n=== SCHG BY ESR ===')
        print('\n2015 SCHG by ESR:')
        schg_esr_2015 = old_persons.groupby(['ESR', 'SCHG']).size().unstack(fill_value=0)
        print(schg_esr_2015)
        
        print('\n2023 SCHG by ESR:')
        schg_esr_2023 = persons_2023.groupby(['ESR', 'SCHG']).size().unstack(fill_value=0)
        print(schg_esr_2023)
    
    # Key insights
    print('\n=== KEY PATTERNS ===')
    print('1. SCHL=-9 patterns (should be for young children):')
    print(f'   2015: {(old_persons["SCHL"] == -9).sum():,} records')
    print(f'   2023: {(persons_2023["SCHL"] == -9).sum():,} records')
    
    print('\n2. SCHG=-9 patterns (should be for non-students):')
    print(f'   2015: {(old_persons["SCHG"] == -9).sum():,} records')
    print(f'   2023: {(persons_2023["SCHG"] == -9).sum():,} records')
    
    print('\n3. Young children (age 0-4) education coding:')
    young_2015 = old_persons[old_persons['AGEP'] <= 4]
    young_2023 = persons_2023[persons_2023['AGEP'] <= 4]
    print(f'   2015 young SCHL values: {sorted(young_2015["SCHL"].unique())}')
    print(f'   2023 young SCHL values: {sorted(young_2023["SCHL"].unique())}')
    print(f'   2015 young SCHG values: {sorted(young_2015["SCHG"].unique())}')
    print(f'   2023 young SCHG values: {sorted(young_2023["SCHG"].unique())}')
    
    print('\n4. School-age children (age 5-17) education coding:')
    school_2015 = old_persons[(old_persons['AGEP'] >= 5) & (old_persons['AGEP'] <= 17)]
    school_2023 = persons_2023[(persons_2023['AGEP'] >= 5) & (persons_2023['AGEP'] <= 17)]
    print(f'   2015 school SCHL values: {sorted(school_2015["SCHL"].unique())}')
    print(f'   2023 school SCHL values: {sorted(school_2023["SCHL"].unique())}')
    print(f'   2015 school SCHG values: {sorted(school_2015["SCHG"].unique())}')
    print(f'   2023 school SCHG values: {sorted(school_2023["SCHG"].unique())}')

if __name__ == '__main__':
    analyze_education_patterns()
