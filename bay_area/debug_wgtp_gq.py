#!/usr/bin/env python3
"""
Debug script to check WGTP values for group quarters households
"""

import pandas as pd
import numpy as np

print("=" * 60)
print("DEBUGGING WGTP VALUES FOR GROUP QUARTERS HOUSEHOLDS")
print("=" * 60)

# Load the generated household seed data
households_file = "output_2023/households_2023_tm2.csv"
print(f"Loading: {households_file}")

try:
    df = pd.read_csv(households_file)
    print(f"Loaded {len(df):,} households")
    
    # Check WGTP distribution by hhgqtype
    print("\n" + "=" * 40)
    print("WGTP DISTRIBUTION BY HHGQTYPE")
    print("=" * 40)
    
    gq_labels = {0: 'Household', 1: 'University GQ', 2: 'Military GQ', 3: 'Other GQ'}
    
    for gq_type in sorted(df['hhgqtype'].unique()):
        subset = df[df['hhgqtype'] == gq_type]
        label = gq_labels.get(gq_type, f'Type {gq_type}')
        
        print(f"\n{label} (hhgqtype={gq_type}):")
        print(f"  Count: {len(subset):,}")
        
        # Check WGTP values
        wgtp_stats = subset['WGTP'].describe()
        print(f"  WGTP min: {wgtp_stats['min']}")
        print(f"  WGTP max: {wgtp_stats['max']}")
        print(f"  WGTP mean: {wgtp_stats['mean']:.1f}")
        
        # Count zero weights
        zero_weights = len(subset[subset['WGTP'] == 0])
        print(f"  Zero weights: {zero_weights:,} ({zero_weights/len(subset)*100:.1f}%)")
        
        # Count NaN weights
        nan_weights = subset['WGTP'].isna().sum()
        print(f"  NaN weights: {nan_weights:,}")
    
    # Summary
    print("\n" + "=" * 40)
    print("SUMMARY")
    print("=" * 40)
    
    total_households = len(df)
    total_gq = len(df[df['hhgqtype'] != 0])
    total_zero_wgtp = len(df[df['WGTP'] == 0])
    gq_zero_wgtp = len(df[(df['hhgqtype'] != 0) & (df['WGTP'] == 0)])
    
    print(f"Total households: {total_households:,}")
    print(f"Total GQ households: {total_gq:,}")
    print(f"Total zero WGTP: {total_zero_wgtp:,}")
    print(f"GQ with zero WGTP: {gq_zero_wgtp:,}")
    print(f"% of GQ with zero WGTP: {gq_zero_wgtp/total_gq*100:.1f}%")
    
    if gq_zero_wgtp == total_gq:
        print("\n🚨 PROBLEM IDENTIFIED: ALL GQ households have zero WGTP!")
        print("   This explains why PopulationSim filters them out.")
    
    # Check original TYPEHUGQ source
    print("\n" + "=" * 40)
    print("TYPEHUGQ vs WGTP ANALYSIS")
    print("=" * 40)
    
    if 'TYPEHUGQ' in df.columns:
        typehugq_wgtp = df.groupby('TYPEHUGQ')['WGTP'].agg(['count', 'min', 'max', 'mean', lambda x: (x==0).sum()])
        typehugq_wgtp.columns = ['count', 'min_wgtp', 'max_wgtp', 'mean_wgtp', 'zero_wgtp']
        print(typehugq_wgtp)
        
        typehugq_labels = {1: 'Household', 2: 'Institutional GQ', 3: 'Noninstitutional GQ'}
        for typ in sorted(df['TYPEHUGQ'].unique()):
            subset = df[df['TYPEHUGQ'] == typ]
            zero_pct = (subset['WGTP'] == 0).sum() / len(subset) * 100
            label = typehugq_labels.get(typ, f'Type {typ}')
            print(f"{label}: {zero_pct:.1f}% zero weights")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
