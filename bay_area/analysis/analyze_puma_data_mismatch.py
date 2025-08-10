#!/usr/bin/env python3
"""
Analyze PUMA data consistency between seed population and controls
Compare seed population characteristics with control targets by PUMA
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_puma_consistency():
    """Compare seed population vs control data by PUMA"""
    
    print("=" * 80)
    print("PUMA DATA CONSISTENCY ANALYSIS")
    print("=" * 80)
    
    # Load data files
    data_dir = Path("hh_gq/tm2_working_dir/data")
    
    try:
        # Load seed data
        households = pd.read_csv(data_dir / "seed_households.csv")
        persons = pd.read_csv(data_dir / "seed_persons.csv")
        
        # Load control data
        crosswalk = pd.read_csv(data_dir / "geo_cross_walk_tm2.csv")
        maz_controls = pd.read_csv(data_dir / "maz_marginals_hhgq.csv")
        taz_controls = pd.read_csv(data_dir / "taz_marginals_hhgq.csv")
        county_controls = pd.read_csv(data_dir / "county_marginals.csv")
        
        print(f"Loaded seed data: {len(households):,} households, {len(persons):,} persons")
        print(f"Loaded control data: {len(maz_controls):,} MAZ, {len(taz_controls):,} TAZ, {len(county_controls):,} County")
        print()
        
        # 1. PUMA COMPARISON
        print("1. PUMA ID COMPARISON")
        print("-" * 50)
        
        seed_pumas = set(households['PUMA'].unique())
        crosswalk_pumas = set(crosswalk['PUMA'].unique())
        
        print(f"Seed PUMAs: {len(seed_pumas)} unique values")
        print(f"Crosswalk PUMAs: {len(crosswalk_pumas)} unique values")
        
        missing_from_seed = crosswalk_pumas - seed_pumas
        missing_from_crosswalk = seed_pumas - crosswalk_pumas
        
        if missing_from_seed:
            print(f"⚠️  PUMAs in crosswalk but NOT in seed: {sorted(missing_from_seed)}")
        if missing_from_crosswalk:
            print(f"⚠️  PUMAs in seed but NOT in crosswalk: {sorted(missing_from_crosswalk)}")
        
        common_pumas = sorted(seed_pumas & crosswalk_pumas)
        print(f"✅ Common PUMAs: {len(common_pumas)}")
        print()
        
        # 2. SEED POPULATION SUMMARY BY PUMA
        print("2. SEED POPULATION BY PUMA")
        print("-" * 50)
        
        seed_summary = households.groupby('PUMA').agg({
            'unique_hh_id': 'count',
            'NP': 'sum',
            'HINCP': ['count', 'mean', 'median'],
            'VEH': 'mean',
            'hh_workers_from_esr': 'mean',
            'hhgqtype': lambda x: (x == 0).sum()  # Regular households
        }).round(2)
        
        seed_summary.columns = ['HH_Count', 'Total_Pop', 'Income_Count', 'Income_Mean', 'Income_Median', 'Avg_Vehicles', 'Avg_Workers', 'Regular_HH']
        
        # Add person-level data
        person_summary = persons.groupby('PUMA').agg({
            'unique_person_id': 'count',
            'AGEP': 'mean',
            'employed': 'mean',
            'occupation': lambda x: x.value_counts().to_dict() if len(x) > 0 else {}
        }).round(2)
        person_summary.columns = ['Person_Count', 'Avg_Age', 'Employment_Rate', 'Occupations']
        
        # Combine seed summaries
        seed_combined = seed_summary.join(person_summary, how='outer')
        
        print("Sample of seed population by PUMA:")
        print(seed_combined.head(10).to_string())
        print(f"\nTotal seed households: {seed_combined['HH_Count'].sum():,}")
        print(f"Total seed persons: {seed_combined['Person_Count'].sum():,}")
        print()
        
        # 3. CONTROL TARGETS BY PUMA
        print("3. CONTROL TARGETS BY PUMA")
        print("-" * 50)
        
        # Get PUMA controls from crosswalk aggregation
        crosswalk_summary = crosswalk.groupby('PUMA').agg({
            'MAZ': 'count',
            'TAZ': 'nunique'
        })
        crosswalk_summary.columns = ['MAZ_Count', 'TAZ_Count']
        
        # MAZ controls aggregated by PUMA
        maz_with_puma = maz_controls.merge(crosswalk[['MAZ', 'PUMA']], on='MAZ', how='left')
        maz_puma_controls = maz_with_puma.groupby('PUMA').agg({
            'num_hh': 'sum',
            'total_pop': 'sum',
            'gq_pop': 'sum',
            'gq_military': 'sum',
            'gq_university': 'sum',
            'gq_other': 'sum',
            'numhh_gq': 'sum'
        })
        
        # TAZ controls aggregated by PUMA
        taz_with_puma = taz_controls.merge(crosswalk[['TAZ', 'PUMA']].drop_duplicates(), on='TAZ', how='left')
        taz_puma_controls = taz_with_puma.groupby('PUMA').agg({
            'hh_inc_30': 'sum',
            'hh_inc_30_60': 'sum',
            'hh_inc_60_100': 'sum',
            'hh_inc_100_plus': 'sum',
            'hh_wrks_0': 'sum',
            'hh_wrks_1': 'sum',
            'hh_wrks_2': 'sum',
            'hh_wrks_3_plus': 'sum',
            'pers_age_00_19': 'sum',
            'pers_age_20_34': 'sum',
            'pers_age_35_64': 'sum',
            'pers_age_65_plus': 'sum',
            'hh_kids_no': 'sum',
            'hh_kids_yes': 'sum',
            'hh_size_1': 'sum',
            'hh_size_2': 'sum',
            'hh_size_3': 'sum',
            'hh_size_4_plus': 'sum'
        })
        
        # Combine control summaries
        control_combined = crosswalk_summary.join([maz_puma_controls, taz_puma_controls], how='outer')
        
        print("Sample of control targets by PUMA:")
        print(control_combined.head(10).to_string())
        print()
        
        # 4. DETAILED COMPARISON FOR PROBLEM PUMAS
        print("4. DETAILED COMPARISON - SEED vs CONTROLS")
        print("-" * 50)
        
        comparison_data = []
        
        for puma in sorted(common_pumas):
            # Seed data for this PUMA
            puma_households = households[households['PUMA'] == puma]
            puma_persons = persons[persons['PUMA'] == puma]
            
            # Control data for this PUMA
            puma_controls = control_combined.loc[puma] if puma in control_combined.index else None
            
            if puma_controls is None:
                print(f"⚠️  PUMA {puma}: No control data found")
                continue
                
            # Calculate seed statistics
            seed_hh_count = len(puma_households)
            seed_person_count = len(puma_persons)
            seed_gq_count = len(puma_households[puma_households['hhgqtype'] > 0])
            
            # Control statistics
            control_hh_count = puma_controls.get('num_hh', 0)
            control_person_count = puma_controls.get('total_pop', 0)
            control_gq_count = puma_controls.get('gq_pop', 0)
            
            # Calculate ratios
            hh_ratio = seed_hh_count / max(control_hh_count, 1)
            person_ratio = seed_person_count / max(control_person_count, 1)
            
            comparison_data.append({
                'PUMA': puma,
                'Seed_HH': seed_hh_count,
                'Control_HH': control_hh_count,
                'HH_Ratio': round(hh_ratio, 3),
                'Seed_Persons': seed_person_count,
                'Control_Persons': control_person_count,
                'Person_Ratio': round(person_ratio, 3),
                'Seed_GQ': seed_gq_count,
                'Control_GQ': control_gq_count
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # Find problematic PUMAs
        problematic = comparison_df[
            (comparison_df['HH_Ratio'] < 0.5) | 
            (comparison_df['HH_Ratio'] > 2.0) |
            (comparison_df['Person_Ratio'] < 0.5) |
            (comparison_df['Person_Ratio'] > 2.0)
        ]
        
        print("All PUMA comparison (first 20):")
        print(comparison_df.head(20).to_string(index=False))
        print()
        
        if len(problematic) > 0:
            print("🚨 PROBLEMATIC PUMAs (ratio < 0.5 or > 2.0):")
            print(problematic.to_string(index=False))
        else:
            print("✅ No severely problematic PUMAs found")
        print()
        
        # 5. HOUSEHOLD CHARACTERISTICS COMPARISON
        print("5. HOUSEHOLD CHARACTERISTICS COMPARISON")
        print("-" * 50)
        
        # Income distribution comparison
        seed_income_dist = households.groupby('PUMA').apply(lambda x: {
            'inc_0_30k': len(x[(x['hh_income_2023'] >= 0) & (x['hh_income_2023'] < 30000)]),
            'inc_30_60k': len(x[(x['hh_income_2023'] >= 30000) & (x['hh_income_2023'] < 60000)]),
            'inc_60_100k': len(x[(x['hh_income_2023'] >= 60000) & (x['hh_income_2023'] < 100000)]),
            'inc_100k_plus': len(x[x['hh_income_2023'] >= 100000])
        }).apply(pd.Series)
        
        # Worker distribution
        seed_worker_dist = households.groupby('PUMA').apply(lambda x: {
            'wrk_0': len(x[x['hh_workers_from_esr'] == 0]),
            'wrk_1': len(x[x['hh_workers_from_esr'] == 1]),
            'wrk_2': len(x[x['hh_workers_from_esr'] == 2]),
            'wrk_3_plus': len(x[x['hh_workers_from_esr'] >= 3])
        }).apply(pd.Series)
        
        print("Sample income distribution by PUMA (seed):")
        print(seed_income_dist.head(10).to_string())
        print()
        
        print("Sample worker distribution by PUMA (seed):")
        print(seed_worker_dist.head(10).to_string())
        print()
        
        # 6. OCCUPATION COMPARISON
        print("6. OCCUPATION COMPARISON")
        print("-" * 50)
        
        # Get employed persons by PUMA and occupation
        employed_persons = persons[persons['employed'] == 1]
        if len(employed_persons) > 0:
            occupation_dist = employed_persons.groupby(['PUMA', 'occupation']).size().unstack(fill_value=0)
            
            print("Sample occupation distribution by PUMA (first 10 PUMAs):")
            if len(occupation_dist) > 0:
                print(occupation_dist.head(10).to_string())
            else:
                print("No employment data found")
        else:
            print("No employed persons found in seed data")
        print()
        
        # 7. SUMMARY AND RECOMMENDATIONS
        print("7. SUMMARY AND RECOMMENDATIONS")
        print("-" * 50)
        
        total_seed_hh = comparison_df['Seed_HH'].sum()
        total_control_hh = comparison_df['Control_HH'].sum()
        total_seed_persons = comparison_df['Seed_Persons'].sum()
        total_control_persons = comparison_df['Control_Persons'].sum()
        
        print(f"TOTALS:")
        print(f"Seed households: {total_seed_hh:,}")
        print(f"Control households: {total_control_hh:,}")
        print(f"Household ratio: {total_seed_hh/max(total_control_hh,1):.3f}")
        print()
        print(f"Seed persons: {total_seed_persons:,}")
        print(f"Control persons: {total_control_persons:,}")
        print(f"Person ratio: {total_seed_persons/max(total_control_persons,1):.3f}")
        print()
        
        # Check for NaN values in key fields
        print("NaN VALUE CHECK:")
        print(f"Seed households NaN in PUMA: {households['PUMA'].isna().sum()}")
        print(f"Seed households NaN in income: {households['hh_income_2023'].isna().sum()}")
        print(f"Seed households NaN in workers: {households['hh_workers_from_esr'].isna().sum()}")
        print(f"Control MAZ NaN in num_hh: {maz_controls['num_hh'].isna().sum()}")
        print(f"Control TAZ NaN in total controls: {taz_controls.isna().sum().sum()}")
        print()
        
        # Save detailed comparison
        output_file = "puma_comparison_analysis.csv"
        comparison_df.to_csv(output_file, index=False)
        print(f"✅ Detailed comparison saved to: {output_file}")
        
        return comparison_df, problematic
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    comparison_df, problematic = analyze_puma_consistency()
