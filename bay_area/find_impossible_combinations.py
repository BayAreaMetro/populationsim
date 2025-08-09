#!/usr/bin/env python3
"""
Find impossible control combinations where targets > 0 but seed records = 0
This is the root cause of PopulationSim NaN errors
"""
import pandas as pd
import numpy as np

print("="*80)
print("IMPOSSIBLE CONTROL COMBINATIONS ANALYSIS")
print("Finding targets > 0 with zero seed records available")
print("="*80)

# Load seed data
print("Loading seed data...")
try:
    # Try different possible file names and locations
    seed_files = [
        ('output_2023/seed_households.csv', 'output_2023/seed_persons.csv'),
        ('output_2023/households_2023_tm2.csv', 'output_2023/persons_2023_tm2.csv'),
        ('hh_gq/tm2_working_dir/data/seed_households.csv', 'hh_gq/tm2_working_dir/data/seed_persons.csv'),
        ('output_2023/households.csv', 'output_2023/persons.csv')
    ]
    
    for hh_file, per_file in seed_files:
        try:
            households = pd.read_csv(hh_file)
            persons = pd.read_csv(per_file)
            print(f"✅ Found seed data: {hh_file}")
            break
        except:
            continue
    else:
        print("❌ Could not find seed data files")
        print("Looking for files...")
        import os
        for root, dirs, files in os.walk('.'):
            for file in files:
                if 'household' in file.lower() and file.endswith('.csv'):
                    print(f"  Found: {os.path.join(root, file)}")
        exit(1)
        
    print(f"Seed: {len(households):,} households, {len(persons):,} persons")
    
except Exception as e:
    print(f"Error loading seed data: {e}")
    exit(1)

# Load control data
print("\nLoading control data...")
try:
    maz = pd.read_csv('output_2023/maz_marginals.csv')
    taz = pd.read_csv('output_2023/taz_marginals.csv') 
    crosswalk = pd.read_csv('hh_gq/data/geo_cross_walk_tm2.csv')
    print(f"Controls: {len(maz):,} MAZ, {len(taz):,} TAZ")
except Exception as e:
    print(f"Error loading control data: {e}")
    exit(1)

# Add PUMA to MAZ data
maz_with_puma = maz.merge(crosswalk[['MAZ', 'PUMA']], on='MAZ', how='left')

print("\n1. CHECKING INCOME COMBINATIONS BY PUMA")
print("-" * 50)

# Aggregate controls by PUMA for income
income_controls = maz_with_puma.groupby('PUMA').agg({
    'hh_inc_30': 'sum',
    'hh_inc_30_60': 'sum', 
    'hh_inc_60_100': 'sum',
    'hh_inc_100_plus': 'sum'
}).reset_index()

# Create income categories in seed data
def categorize_income(income):
    if income < 30000:
        return 'inc_0_30'
    elif income < 60000:
        return 'inc_30_60'
    elif income < 100000:
        return 'inc_60_100'
    else:
        return 'inc_100_plus'

households['income_cat'] = households['income'].apply(categorize_income)

# Count seed households by PUMA and income
seed_income = households.groupby(['PUMA', 'income_cat']).size().unstack(fill_value=0)

print("Checking for income mismatches...")
problems = []

for _, row in income_controls.iterrows():
    puma = row['PUMA']
    
    # Check each income category
    income_checks = [
        ('hh_inc_30', 'inc_0_30'),
        ('hh_inc_30_60', 'inc_30_60'), 
        ('hh_inc_60_100', 'inc_60_100'),
        ('hh_inc_100_plus', 'inc_100_plus')
    ]
    
    for control_col, seed_col in income_checks:
        control_target = row[control_col]
        seed_available = seed_income.loc[puma, seed_col] if puma in seed_income.index and seed_col in seed_income.columns else 0
        
        if control_target > 0 and seed_available == 0:
            problems.append({
                'PUMA': puma,
                'Category': f'Income {seed_col}',
                'Control_Target': control_target,
                'Seed_Available': seed_available,
                'Problem': 'No seed records for non-zero target'
            })

print(f"Income combination problems found: {len([p for p in problems if 'Income' in p['Category']])}")

print("\n2. CHECKING WORKER COMBINATIONS BY PUMA")
print("-" * 50)

# Aggregate worker controls by PUMA
worker_controls = maz_with_puma.groupby('PUMA').agg({
    'hh_wrks_0': 'sum',
    'hh_wrks_1': 'sum',
    'hh_wrks_2': 'sum', 
    'hh_wrks_3_plus': 'sum'
}).reset_index()

# Count seed households by PUMA and workers
def categorize_workers(workers):
    if workers == 0:
        return 'wrk_0'
    elif workers == 1:
        return 'wrk_1'
    elif workers == 2:
        return 'wrk_2'
    else:
        return 'wrk_3_plus'

households['worker_cat'] = households['workers'].apply(categorize_workers)
seed_workers = households.groupby(['PUMA', 'worker_cat']).size().unstack(fill_value=0)

print("Checking for worker mismatches...")

for _, row in worker_controls.iterrows():
    puma = row['PUMA']
    
    worker_checks = [
        ('hh_wrks_0', 'wrk_0'),
        ('hh_wrks_1', 'wrk_1'),
        ('hh_wrks_2', 'wrk_2'),
        ('hh_wrks_3_plus', 'wrk_3_plus')
    ]
    
    for control_col, seed_col in worker_checks:
        control_target = row[control_col]
        seed_available = seed_workers.loc[puma, seed_col] if puma in seed_workers.index and seed_col in seed_workers.columns else 0
        
        if control_target > 0 and seed_available == 0:
            problems.append({
                'PUMA': puma,
                'Category': f'Workers {seed_col}',
                'Control_Target': control_target,
                'Seed_Available': seed_available,
                'Problem': 'No seed records for non-zero target'
            })

print(f"Worker combination problems found: {len([p for p in problems if 'Workers' in p['Category']])}")

print("\n3. CHECKING HOUSEHOLD SIZE COMBINATIONS")
print("-" * 50)

# Aggregate household size controls
size_controls = maz_with_puma.groupby('PUMA').agg({
    'hh_size_1': 'sum',
    'hh_size_2': 'sum',
    'hh_size_3': 'sum',
    'hh_size_4_plus': 'sum'
}).reset_index()

# Count seed households by size
def categorize_size(size):
    if size == 1:
        return 'size_1'
    elif size == 2:
        return 'size_2'
    elif size == 3:
        return 'size_3'
    else:
        return 'size_4_plus'

households['size_cat'] = households['hhsize'].apply(categorize_size)
seed_sizes = households.groupby(['PUMA', 'size_cat']).size().unstack(fill_value=0)

for _, row in size_controls.iterrows():
    puma = row['PUMA']
    
    size_checks = [
        ('hh_size_1', 'size_1'),
        ('hh_size_2', 'size_2'),
        ('hh_size_3', 'size_3'),
        ('hh_size_4_plus', 'size_4_plus')
    ]
    
    for control_col, seed_col in size_checks:
        control_target = row[control_col]
        seed_available = seed_sizes.loc[puma, seed_col] if puma in seed_sizes.index and seed_col in seed_sizes.columns else 0
        
        if control_target > 0 and seed_available == 0:
            problems.append({
                'PUMA': puma,
                'Category': f'Size {seed_col}',
                'Control_Target': control_target,
                'Seed_Available': seed_available,
                'Problem': 'No seed records for non-zero target'
            })

print(f"Household size problems found: {len([p for p in problems if 'Size' in p['Category']])}")

# Summary of all problems
print("\n" + "="*80)
print("SUMMARY OF IMPOSSIBLE COMBINATIONS")
print("="*80)

if problems:
    problems_df = pd.DataFrame(problems)
    print(f"Total impossible combinations found: {len(problems)}")
    
    # Group by category
    by_category = problems_df.groupby('Category').size().sort_values(ascending=False)
    print("\nBreakdown by category:")
    for category, count in by_category.items():
        print(f"  {category}: {count} problems")
    
    # Show worst PUMAs
    by_puma = problems_df.groupby('PUMA').size().sort_values(ascending=False)
    print(f"\nWorst PUMAs (top 10):")
    for puma, count in by_puma.head(10).items():
        print(f"  PUMA {puma}: {count} impossible combinations")
    
    # Show examples
    print("\nFirst 20 impossible combinations:")
    print(problems_df.head(20).to_string(index=False))
    
else:
    print("✅ No impossible combinations found!")
    print("The NaN error must be caused by something else.")

print("\n" + "="*80)
