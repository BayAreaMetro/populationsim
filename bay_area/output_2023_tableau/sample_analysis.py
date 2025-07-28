#!/usr/bin/env python3
"""
Sample analysis of 2015-2023 TAZ changes
"""

import pandas as pd

# Load the comparison data
df = pd.read_csv('taz_marginals_tableau.csv')

print("=== SAMPLE 2015-2023 TAZ COMPARISON ANALYSIS ===\n")

# Show basic stats
print(f"Total TAZ zones: {len(df):,}")
print(f"Data columns: {len(df.columns)}")

# Look at high-income household changes
print(f"\n📈 HIGH INCOME HOUSEHOLDS (>$100K):")
print(f"2015 total: {df['hh_inc_100_plus_2015'].sum():,}")
print(f"2023 total: {df['hh_inc_100_plus'].sum():,}")
print(f"Net change: {df['hh_inc_100_plus_2023-2015_diff'].sum():,}")
print(f"Percent change: {(df['hh_inc_100_plus_2023-2015_diff'].sum() / df['hh_inc_100_plus_2015'].sum() * 100):.1f}%")

# Look at low-income household changes  
print(f"\n📉 LOW INCOME HOUSEHOLDS (<$30K):")
print(f"2015 total: {df['hh_inc_30_2015'].sum():,}")
print(f"2023 total: {df['hh_inc_30'].sum():,}")
print(f"Net change: {df['hh_inc_30_2023-2015_diff'].sum():,}")
print(f"Percent change: {(df['hh_inc_30_2023-2015_diff'].sum() / df['hh_inc_30_2015'].sum() * 100):.1f}%")

# Look at age distribution changes
print(f"\n👥 POPULATION AGE CHANGES:")
age_groups = [
    ('0-19', 'pers_age_00_19'),
    ('20-34', 'pers_age_20_34'), 
    ('35-64', 'pers_age_35_64'),
    ('65+', 'pers_age_65_plus')
]

for age_name, age_col in age_groups:
    change = df[f'{age_col}_2023-2015_diff'].sum()
    pct_change = change / df[f'{age_col}_2015'].sum() * 100
    print(f"Age {age_name}: {change:+,} ({pct_change:+.1f}%)")

# Show top TAZs with biggest high-income gains
print(f"\n🏆 TOP 10 TAZs WITH BIGGEST HIGH-INCOME GAINS:")
top_gains = df.nlargest(10, 'hh_inc_100_plus_2023-2015_diff')[['TAZ_ID', 'hh_inc_100_plus_2015', 'hh_inc_100_plus', 'hh_inc_100_plus_2023-2015_diff']]
for _, row in top_gains.iterrows():
    print(f"TAZ {int(row['TAZ_ID'])}: {row['hh_inc_100_plus_2015']:.0f} → {row['hh_inc_100_plus']:.0f} (+{row['hh_inc_100_plus_2023-2015_diff']:.0f})")

print(f"\n🔻 TOP 10 TAZs WITH BIGGEST HIGH-INCOME LOSSES:")
top_losses = df.nsmallest(10, 'hh_inc_100_plus_2023-2015_diff')[['TAZ_ID', 'hh_inc_100_plus_2015', 'hh_inc_100_plus', 'hh_inc_100_plus_2023-2015_diff']]
for _, row in top_losses.iterrows():
    print(f"TAZ {int(row['TAZ_ID'])}: {row['hh_inc_100_plus_2015']:.0f} → {row['hh_inc_100_plus']:.0f} ({row['hh_inc_100_plus_2023-2015_diff']:.0f})")
