#!/usr/bin/env python3
"""
Debug hierarchical consistency enforcement to understand the large adjustments
"""
import pandas as pd
import sys
import os

# Add the config path
sys.path.append('tm2_control_utils')
from config import HIERARCHICAL_CONSISTENCY

def debug_enforcement():
    """Debug the hierarchical consistency enforcement to understand large adjustments"""
    
    # Use existing files in hh_gq/data
    data_dir = 'hh_gq/data'
    maz_file = os.path.join(data_dir, 'maz_marginals_hhgq.csv')
    taz_file = os.path.join(data_dir, 'taz_marginals_hhgq.csv')
    crosswalk_file = os.path.join('output_2023', 'geo_cross_walk_tm2.csv')
    
    print("Loading control files...")
    maz_controls = pd.read_csv(maz_file)
    taz_controls = pd.read_csv(taz_file)
    crosswalk = pd.read_csv(crosswalk_file)
    
    print(f"MAZ controls: {maz_controls.shape}")
    print(f"TAZ controls: {taz_controls.shape}")
    print(f"Crosswalk: {crosswalk.shape}")
    
    # Add MAZ column to TAZ data
    print("Adding MAZ column to TAZ data...")
    taz_data = taz_controls.merge(crosswalk[['TAZ', 'MAZ']], on='TAZ', how='left')
    
    missing_maz = taz_data['MAZ'].isna().sum()
    print(f"TAZ records missing MAZ: {missing_maz}")
    
    if missing_maz > 0:
        taz_data = taz_data.dropna(subset=['MAZ'])
    
    # Debug specific MAZs that show large adjustments
    problem_mazs = [330870, 311913, 330012, 329071, 331431]
    
    for maz_id in problem_mazs:
        print(f"\n=== DEBUG MAZ {maz_id} ===")
        
        # Check MAZ current total population
        maz_pop = maz_controls[maz_controls['MAZ'] == maz_id]['total_pop']
        if len(maz_pop) > 0:
            print(f"Current MAZ total_pop: {maz_pop.iloc[0]}")
        else:
            print(f"MAZ {maz_id} not found in maz_controls")
            continue
        
        # Check TAZs within this MAZ
        tazs_in_maz = taz_data[taz_data['MAZ'] == maz_id]
        print(f"TAZs in MAZ {maz_id}: {len(tazs_in_maz)}")
        
        if len(tazs_in_maz) > 0:
            print("TAZ IDs:", list(tazs_in_maz['TAZ'].values))
            
            # Check age controls in these TAZs
            age_cols = ['pers_age_00_19', 'pers_age_20_34', 'pers_age_35_64', 'pers_age_65_plus']
            existing_age_cols = [col for col in age_cols if col in tazs_in_maz.columns]
            
            if existing_age_cols:
                taz_age_totals = tazs_in_maz[existing_age_cols].sum()
                print("TAZ age totals:")
                for col in existing_age_cols:
                    print(f"  {col}: {taz_age_totals[col]}")
                
                total_persons_from_taz = taz_age_totals.sum()
                print(f"Total persons from TAZ sum: {total_persons_from_taz}")
            else:
                print("No age columns found in TAZ data")
        else:
            print(f"No TAZs found for MAZ {maz_id}")
    
    # Check some sample TAZ data
    print("\n=== SAMPLE TAZ DATA ===")
    print("First 5 TAZ records:")
    sample_cols = ['TAZ', 'MAZ'] + [col for col in ['pers_age_00_19', 'pers_age_20_34', 'pers_age_35_64', 'pers_age_65_plus'] if col in taz_data.columns]
    print(taz_data[sample_cols].head())
    
    # Check age control totals across all TAZs
    age_cols = ['pers_age_00_19', 'pers_age_20_34', 'pers_age_35_64', 'pers_age_65_plus']
    existing_age_cols = [col for col in age_cols if col in taz_data.columns]
    
    if existing_age_cols:
        print(f"\n=== TOTAL AGE CONTROLS ACROSS ALL TAZs ===")
        for col in existing_age_cols:
            total = taz_data[col].sum()
            print(f"{col}: {total:,.0f}")
        
        grand_total = taz_data[existing_age_cols].sum().sum()
        print(f"Grand total persons from all TAZs: {grand_total:,.0f}")

if __name__ == "__main__":
    debug_enforcement()
