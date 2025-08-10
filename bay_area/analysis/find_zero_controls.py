#!/usr/bin/env python3
"""
Find zero values in control files that could cause NaN errors in PopulationSim
Focus on key control totals that PopulationSim uses for scaling
"""
import pandas as pd
import numpy as np

print("="*70)
print("ZERO VALUES ANALYSIS IN CONTROL FILES")
print("="*70)

# 1. Check MAZ marginals for zeros
print("\n1. MAZ MARGINALS - Checking for zero values...")
try:
    maz = pd.read_csv('output_2023/maz_marginals.csv')
    print(f"Loaded {len(maz):,} MAZ records")
    
    # Key columns that could cause issues if zero
    key_cols = ['num_hh', 'total_pop']
    for col in key_cols:
        if col in maz.columns:
            zero_count = (maz[col] == 0).sum()
            print(f"  {col}: {zero_count:,} zeros out of {len(maz):,} records ({zero_count/len(maz)*100:.1f}%)")
            if zero_count > 0:
                print(f"    First 10 MAZs with zero {col}: {maz[maz[col] == 0]['MAZ'].head(10).tolist()}")
        else:
            print(f"  {col}: Column not found")
    
    # Check for MAZs with zero households but non-zero population (might indicate GQ-only areas)
    if 'num_hh' in maz.columns and 'total_pop' in maz.columns:
        zero_hh_nonzero_pop = maz[(maz['num_hh'] == 0) & (maz['total_pop'] > 0)]
        print(f"  MAZs with 0 households but >0 population: {len(zero_hh_nonzero_pop):,}")
        if len(zero_hh_nonzero_pop) > 0:
            print(f"    Examples: {zero_hh_nonzero_pop[['MAZ', 'num_hh', 'total_pop']].head().to_dict('records')}")

except Exception as e:
    print(f"Error reading MAZ marginals: {e}")

# 2. Check TAZ marginals for zeros
print("\n2. TAZ MARGINALS - Checking for zero values...")
try:
    taz = pd.read_csv('output_2023/taz_marginals.csv')
    print(f"Loaded {len(taz):,} TAZ records")
    
    # Check all numeric columns for zeros
    numeric_cols = taz.select_dtypes(include=[np.number]).columns
    numeric_cols = [col for col in numeric_cols if col not in ['TAZ', 'PUMA']]  # Exclude ID columns
    
    for col in numeric_cols:
        zero_count = (taz[col] == 0).sum()
        if zero_count > 0:
            print(f"  {col}: {zero_count:,} zeros out of {len(taz):,} records ({zero_count/len(taz)*100:.1f}%)")
            if zero_count < 20:  # Show examples if not too many
                zero_tazs = taz[taz[col] == 0]['TAZ'].head(10).tolist()
                print(f"    Example TAZs with zero {col}: {zero_tazs}")

except Exception as e:
    print(f"Error reading TAZ marginals: {e}")

# 3. Check county marginals for zeros
print("\n3. COUNTY MARGINALS - Checking for zero values...")
try:
    county = pd.read_csv('output_2023/county_marginals.csv')
    print(f"Loaded {len(county):,} county records")
    
    # Check all numeric columns for zeros
    numeric_cols = county.select_dtypes(include=[np.number]).columns
    numeric_cols = [col for col in numeric_cols if col not in ['county_id']]  # Exclude ID columns
    
    for col in numeric_cols:
        zero_count = (county[col] == 0).sum()
        if zero_count > 0:
            print(f"  {col}: {zero_count:,} zeros out of {len(county):,} records")
            zero_counties = county[county[col] == 0]['county_id'].tolist()
            print(f"    Counties with zero {col}: {zero_counties}")

except Exception as e:
    print(f"Error reading county marginals: {e}")

# 4. Check for PUMA-level zeros by aggregating controls
print("\n4. PUMA-LEVEL AGGREGATION - Checking for zero totals...")
try:
    # Load crosswalk to get PUMA mappings
    crosswalk = pd.read_csv('hh_gq/data/geo_cross_walk_tm2.csv')
    
    # Aggregate MAZ data by PUMA
    if 'maz' in locals():
        maz_with_puma = maz.merge(crosswalk[['MAZ', 'PUMA']], on='MAZ', how='left')
        maz_puma_totals = maz_with_puma.groupby('PUMA').agg({
            'num_hh': 'sum',
            'total_pop': 'sum'
        }).reset_index()
        
        print(f"PUMA totals from MAZ aggregation:")
        zero_hh_pumas = maz_puma_totals[maz_puma_totals['num_hh'] == 0]['PUMA'].tolist()
        zero_pop_pumas = maz_puma_totals[maz_puma_totals['total_pop'] == 0]['PUMA'].tolist()
        
        if zero_hh_pumas:
            print(f"  PUMAs with zero households: {zero_hh_pumas}")
        if zero_pop_pumas:
            print(f"  PUMAs with zero population: {zero_pop_pumas}")
        
        # Show PUMA totals summary
        print(f"  PUMA household totals: min={maz_puma_totals['num_hh'].min():,}, max={maz_puma_totals['num_hh'].max():,}")
        print(f"  PUMA population totals: min={maz_puma_totals['total_pop'].min():,}, max={maz_puma_totals['total_pop'].max():,}")

except Exception as e:
    print(f"Error in PUMA aggregation: {e}")

# 5. Check for negative values that could also cause issues
print("\n5. NEGATIVE VALUES CHECK...")
try:
    if 'maz' in locals():
        for col in ['num_hh', 'total_pop']:
            if col in maz.columns:
                neg_count = (maz[col] < 0).sum()
                if neg_count > 0:
                    print(f"  MAZ {col}: {neg_count:,} negative values")
    
    if 'taz' in locals():
        numeric_cols = taz.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col not in ['TAZ', 'PUMA']:
                neg_count = (taz[col] < 0).sum()
                if neg_count > 0:
                    print(f"  TAZ {col}: {neg_count:,} negative values")

except Exception as e:
    print(f"Error checking negative values: {e}")

print("\n" + "="*70)
print("ANALYSIS COMPLETE")
print("="*70)
