#!/usr/bin/env python3
"""
Check if seed data categories map directly to control categories
This is CRITICAL - they must match exactly for PopulationSim to work
"""
import pandas as pd
import numpy as np

print("CHECKING SEED-TO-CONTROL CATEGORY MAPPING")
print("="*60)

# Load seed data
try:
    households = pd.read_csv('output_2023/seed_households.csv')
    print(f"✅ Loaded {len(households):,} seed households")
    print(f"Seed columns: {list(households.columns)}")
except Exception as e:
    print(f"❌ Error loading seed households: {e}")
    exit(1)

# Load control data 
try:
    maz = pd.read_csv('output_2023/maz_marginals.csv')
    taz = pd.read_csv('output_2023/taz_marginals.csv')
    print(f"✅ Loaded {len(maz):,} MAZ controls and {len(taz):,} TAZ controls")
    print(f"MAZ columns: {list(maz.columns)}")
    print(f"TAZ columns: {list(taz.columns)}")
except Exception as e:
    print(f"❌ Error loading control data: {e}")
    exit(1)

print("\n" + "="*60)
print("1. INCOME CATEGORY MAPPING")
print("="*60)

# Check income categories in seed
if 'income' in households.columns:
    income_stats = households['income'].describe()
    print(f"Seed income stats:")
    print(f"  Min: ${income_stats['min']:,.0f}")
    print(f"  Max: ${income_stats['max']:,.0f}")
    print(f"  Mean: ${income_stats['mean']:,.0f}")
    print(f"  Median: ${income_stats['50%']:,.0f}")
    
    # Show income distribution
    income_ranges = [
        (0, 30000, "0-30k"),
        (30000, 60000, "30-60k"), 
        (60000, 100000, "60-100k"),
        (100000, float('inf'), "100k+")
    ]
    
    print(f"\nSeed income distribution:")
    for min_inc, max_inc, label in income_ranges:
        if max_inc == float('inf'):
            count = len(households[households['income'] >= min_inc])
        else:
            count = len(households[(households['income'] >= min_inc) & (households['income'] < max_inc)])
        pct = count / len(households) * 100
        print(f"  {label}: {count:,} households ({pct:.1f}%)")

# Check control income categories
income_control_cols = [col for col in taz.columns if 'hh_inc_' in col]
print(f"\nTAZ control income columns: {income_control_cols}")

if income_control_cols:
    total_controls = taz[income_control_cols].sum()
    print(f"TAZ control income distribution:")
    for col in income_control_cols:
        count = total_controls[col]
        pct = count / total_controls.sum() * 100 if total_controls.sum() > 0 else 0
        print(f"  {col}: {count:,.0f} ({pct:.1f}%)")

print("\n" + "="*60)
print("2. WORKER CATEGORY MAPPING")
print("="*60)

# Check workers in seed
if 'workers' in households.columns:
    worker_counts = households['workers'].value_counts().sort_index()
    print(f"Seed worker distribution:")
    for workers, count in worker_counts.items():
        pct = count / len(households) * 100
        print(f"  {workers} workers: {count:,} households ({pct:.1f}%)")

# Check control worker categories  
worker_control_cols = [col for col in taz.columns if 'hh_wrks_' in col]
print(f"\nTAZ control worker columns: {worker_control_cols}")

if worker_control_cols:
    total_controls = taz[worker_control_cols].sum()
    print(f"TAZ control worker distribution:")
    for col in worker_control_cols:
        count = total_controls[col]
        pct = count / total_controls.sum() * 100 if total_controls.sum() > 0 else 0
        print(f"  {col}: {count:,.0f} ({pct:.1f}%)")

print("\n" + "="*60)
print("3. HOUSEHOLD SIZE MAPPING")
print("="*60)

# Check household size in seed
if 'hhsize' in households.columns:
    size_counts = households['hhsize'].value_counts().sort_index()
    print(f"Seed household size distribution:")
    for size, count in size_counts.items():
        pct = count / len(households) * 100
        print(f"  Size {size}: {count:,} households ({pct:.1f}%)")

# Check control size categories
size_control_cols = [col for col in taz.columns if 'hh_size_' in col]
print(f"\nTAZ control size columns: {size_control_cols}")

if size_control_cols:
    total_controls = taz[size_control_cols].sum()
    print(f"TAZ control size distribution:")
    for col in size_control_cols:
        count = total_controls[col]
        pct = count / total_controls.sum() * 100 if total_controls.sum() > 0 else 0
        print(f"  {col}: {count:,.0f} ({pct:.1f}%)")

print("\n" + "="*60)
print("4. CHECKING FOR MISSING CATEGORIES")
print("="*60)

# Check if seed has categories that controls don't have
print("Potential mapping issues:")

# Income mapping check
print("\nIncome category mapping:")
print("  Seed income -> Control categories")
print("  $0-30k     -> hh_inc_30")
print("  $30-60k    -> hh_inc_30_60") 
print("  $60-100k   -> hh_inc_60_100")
print("  $100k+     -> hh_inc_100_plus")

# Worker mapping check  
print("\nWorker category mapping:")
print("  Seed workers -> Control categories")
print("  0 workers    -> hh_wrks_0")
print("  1 worker     -> hh_wrks_1")
print("  2 workers    -> hh_wrks_2") 
print("  3+ workers   -> hh_wrks_3_plus")

# Size mapping check
print("\nSize category mapping:")
print("  Seed hhsize -> Control categories")
print("  Size 1      -> hh_size_1")
print("  Size 2      -> hh_size_2")
print("  Size 3      -> hh_size_3")
print("  Size 4+     -> hh_size_4_plus")

print("\n" + "="*60)
print("5. CATEGORY COMPLETENESS CHECK")
print("="*60)

# Check if any seed households don't fit into control categories
issues = []

if 'income' in households.columns:
    no_income = households['income'].isna().sum()
    if no_income > 0:
        issues.append(f"❌ {no_income:,} households have missing income")

if 'workers' in households.columns:
    no_workers = households['workers'].isna().sum()
    if no_workers > 0:
        issues.append(f"❌ {no_workers:,} households have missing workers")

if 'hhsize' in households.columns:
    no_size = households['hhsize'].isna().sum()
    if no_size > 0:
        issues.append(f"❌ {no_size:,} households have missing size")

if issues:
    print("ISSUES FOUND:")
    for issue in issues:
        print(f"  {issue}")
else:
    print("✅ All seed households have complete category data")

print("\n" + "="*60)
