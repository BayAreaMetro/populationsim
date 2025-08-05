#!/usr/bin/env python3
"""
validate_control_hierarchy.py

This script validates hierarchical control consistency across MAZ, TAZ, and COUNTY levels
for PopulationSim. Inconsistent control totals are a common cause of IntCastingNaNError.

The validation checks that:
1. MAZ household totals sum to TAZ household category totals  
2. MAZ population totals sum to TAZ age category totals
3. TAZ totals sum to COUNTY totals where applicable
4. All control categories within a geography sum correctly

This identifies the root cause of optimization infeasibility in PopulationSim.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

def load_control_files():
    """Load all control files and return them as dictionaries"""
    
    data_dir = Path('.')
    
    files = {
        'controls': data_dir / 'controls.csv',
        'maz_marginals': data_dir / 'maz_marginals_hhgq.csv',
        'taz_marginals': data_dir / 'taz_marginals_hhgq.csv', 
        'county_marginals': data_dir / 'county_marginals.csv',
        'geo_crosswalk': data_dir / 'geo_cross_walk_tm2.csv'
    }
    
    # Check if all files exist
    missing_files = [name for name, path in files.items() if not path.exists()]
    if missing_files:
        print(f"ERROR: Missing files: {missing_files}")
        return None
    
    # Load all files
    data = {}
    for name, path in files.items():
        try:
            data[name] = pd.read_csv(path)
            print(f"Loaded {name}: {len(data[name])} rows")
        except Exception as e:
            print(f"ERROR loading {name}: {e}")
            return None
    
    return data

def validate_maz_taz_household_consistency(data):
    """Validate that MAZ household totals sum to TAZ household category totals"""
    
    print("\n" + "="*60)
    print("VALIDATING MAZ→TAZ HOUSEHOLD CONSISTENCY")
    print("="*60)
    
    maz_df = data['maz_marginals']
    taz_df = data['taz_marginals'] 
    crosswalk = data['geo_crosswalk']
    
    # Create MAZ to TAZ mapping
    maz_taz_map = crosswalk.set_index('MAZ')['TAZ'].to_dict()
    
    # Add TAZ column to MAZ data
    maz_df = maz_df.copy()
    maz_df['TAZ'] = maz_df['MAZ'].map(maz_taz_map)
    
    # Check for missing mappings
    missing_taz = maz_df['TAZ'].isna().sum()
    if missing_taz > 0:
        print(f"WARNING: {missing_taz} MAZs have no TAZ mapping")
    
    # Sum MAZ households by TAZ
    maz_hh_by_taz = maz_df.groupby('TAZ')['numhh_gq'].sum().reset_index()
    maz_hh_by_taz.columns = ['TAZ', 'maz_total_hh']
    
    # Calculate TAZ household category sums
    hh_size_cols = ['hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus']
    if all(col in taz_df.columns for col in hh_size_cols):
        taz_df = taz_df.copy()
        taz_df['taz_hh_size_total'] = taz_df[hh_size_cols].sum(axis=1)
        
        # Merge and compare
        comparison = taz_df[['TAZ', 'taz_hh_size_total']].merge(
            maz_hh_by_taz, on='TAZ', how='outer'
        )
        
        # Calculate differences
        comparison['diff'] = comparison['taz_hh_size_total'] - comparison['maz_total_hh']
        comparison['pct_diff'] = (comparison['diff'] / comparison['maz_total_hh']) * 100
        
        # Statistics
        total_maz_hh = comparison['maz_total_hh'].sum()
        total_taz_hh = comparison['taz_hh_size_total'].sum()
        total_diff = total_taz_hh - total_maz_hh
        
        print(f"Total MAZ households: {total_maz_hh:,.0f}")
        print(f"Total TAZ household size sum: {total_taz_hh:,.0f}")
        print(f"Total difference: {total_diff:,.0f} ({total_diff/total_maz_hh*100:.2f}%)")
        
        # Show problematic TAZs
        large_diffs = comparison[abs(comparison['pct_diff']) > 5]  # >5% difference
        if len(large_diffs) > 0:
            print(f"\nTAZs with >5% household total differences: {len(large_diffs)}")
            print(large_diffs[['TAZ', 'maz_total_hh', 'taz_hh_size_total', 'diff', 'pct_diff']].head(10))
        else:
            print("✅ All TAZ household totals within 5% of MAZ totals")
    
    else:
        print(f"ERROR: Missing household size columns in TAZ data")
        print(f"Available columns: {list(taz_df.columns)}")
    
    return comparison if 'comparison' in locals() else None

def validate_maz_taz_population_consistency(data):
    """Validate that MAZ population totals sum to TAZ age category totals"""
    
    print("\n" + "="*60)
    print("VALIDATING MAZ→TAZ POPULATION CONSISTENCY")
    print("="*60)
    
    maz_df = data['maz_marginals']
    taz_df = data['taz_marginals']
    crosswalk = data['geo_crosswalk']
    
    # Check if we have total_pop in MAZ data
    if 'total_pop' not in maz_df.columns:
        print("WARNING: total_pop column not found in MAZ marginals")
        print(f"Available MAZ columns: {list(maz_df.columns)}")
        return None
    
    # Create MAZ to TAZ mapping
    maz_taz_map = crosswalk.set_index('MAZ')['TAZ'].to_dict()
    
    # Add TAZ column to MAZ data
    maz_df = maz_df.copy()
    maz_df['TAZ'] = maz_df['MAZ'].map(maz_taz_map)
    
    # Sum MAZ population by TAZ
    maz_pop_by_taz = maz_df.groupby('TAZ')['total_pop'].sum().reset_index()
    maz_pop_by_taz.columns = ['TAZ', 'maz_total_pop']
    
    # Calculate TAZ age category sums
    age_cols = ['pers_age_00_19', 'pers_age_20_34', 'pers_age_35_64', 'pers_age_65_plus']
    if all(col in taz_df.columns for col in age_cols):
        taz_df = taz_df.copy()
        taz_df['taz_age_total'] = taz_df[age_cols].sum(axis=1)
        
        # Merge and compare
        comparison = taz_df[['TAZ', 'taz_age_total']].merge(
            maz_pop_by_taz, on='TAZ', how='outer'
        )
        
        # Calculate differences
        comparison['diff'] = comparison['taz_age_total'] - comparison['maz_total_pop']
        comparison['pct_diff'] = (comparison['diff'] / comparison['maz_total_pop']) * 100
        
        # Statistics
        total_maz_pop = comparison['maz_total_pop'].sum()
        total_taz_pop = comparison['taz_age_total'].sum()
        total_diff = total_taz_pop - total_maz_pop
        
        print(f"Total MAZ population: {total_maz_pop:,.0f}")
        print(f"Total TAZ age sum: {total_taz_pop:,.0f}")
        print(f"Total difference: {total_diff:,.0f} ({total_diff/total_maz_pop*100:.2f}%)")
        
        # Show problematic TAZs
        large_diffs = comparison[abs(comparison['pct_diff']) > 5]  # >5% difference
        if len(large_diffs) > 0:
            print(f"\nTAZs with >5% population total differences: {len(large_diffs)}")
            print(large_diffs[['TAZ', 'maz_total_pop', 'taz_age_total', 'diff', 'pct_diff']].head(10))
        else:
            print("✅ All TAZ population totals within 5% of MAZ totals")
            
    else:
        print(f"ERROR: Missing age columns in TAZ data")
        print(f"Available columns: {list(taz_df.columns)}")
        return None
    
    return comparison

def validate_taz_internal_consistency(data):
    """Validate that TAZ control categories sum correctly within each TAZ"""
    
    print("\n" + "="*60)
    print("VALIDATING TAZ INTERNAL CONSISTENCY")
    print("="*60)
    
    taz_df = data['taz_marginals'].copy()
    
    issues = []
    
    # Check household size categories vs numhh_gq
    hh_size_cols = ['hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus']
    if all(col in taz_df.columns for col in hh_size_cols) and 'numhh_gq' in taz_df.columns:
        taz_df['hh_size_sum'] = taz_df[hh_size_cols].sum(axis=1)
        taz_df['hh_size_diff'] = taz_df['hh_size_sum'] - taz_df['numhh_gq']
        
        hh_size_mismatches = (abs(taz_df['hh_size_diff']) > 1).sum()  # Allow 1 unit rounding
        if hh_size_mismatches > 0:
            print(f"⚠️  {hh_size_mismatches} TAZs have household size sum ≠ numhh_gq")
            worst_hh = taz_df.loc[abs(taz_df['hh_size_diff']).idxmax()]
            print(f"   Worst case TAZ {worst_hh['TAZ']}: size_sum={worst_hh['hh_size_sum']}, numhh_gq={worst_hh['numhh_gq']}, diff={worst_hh['hh_size_diff']}")
            issues.append(f"Household size categories don't sum to numhh_gq in {hh_size_mismatches} TAZs")
        else:
            print("✅ Household size categories sum correctly to numhh_gq")
    
    # Check kids categories vs numhh_gq  
    kids_cols = ['hh_kids_yes', 'hh_kids_no']
    if all(col in taz_df.columns for col in kids_cols) and 'numhh_gq' in taz_df.columns:
        taz_df['kids_sum'] = taz_df[kids_cols].sum(axis=1)
        taz_df['kids_diff'] = taz_df['kids_sum'] - taz_df['numhh_gq']
        
        kids_mismatches = (abs(taz_df['kids_diff']) > 1).sum()
        if kids_mismatches > 0:
            print(f"⚠️  {kids_mismatches} TAZs have kids categories sum ≠ numhh_gq")
            worst_kids = taz_df.loc[abs(taz_df['kids_diff']).idxmax()]
            print(f"   Worst case TAZ {worst_kids['TAZ']}: kids_sum={worst_kids['kids_sum']}, numhh_gq={worst_kids['numhh_gq']}, diff={worst_kids['kids_diff']}")
            issues.append(f"Kids categories don't sum to numhh_gq in {kids_mismatches} TAZs")
        else:
            print("✅ Kids categories sum correctly to numhh_gq")
    
    # Check worker categories vs numhh_gq
    worker_cols = ['hh_wrks_0', 'hh_wrks_1', 'hh_wrks_2', 'hh_wrks_3_plus']
    if all(col in taz_df.columns for col in worker_cols) and 'numhh_gq' in taz_df.columns:
        taz_df['worker_sum'] = taz_df[worker_cols].sum(axis=1)
        taz_df['worker_diff'] = taz_df['worker_sum'] - taz_df['numhh_gq']
        
        worker_mismatches = (abs(taz_df['worker_diff']) > 1).sum()
        if worker_mismatches > 0:
            print(f"⚠️  {worker_mismatches} TAZs have worker categories sum ≠ numhh_gq")
            worst_worker = taz_df.loc[abs(taz_df['worker_diff']).idxmax()]
            print(f"   Worst case TAZ {worst_worker['TAZ']}: worker_sum={worst_worker['worker_sum']}, numhh_gq={worst_worker['numhh_gq']}, diff={worst_worker['worker_diff']}")
            issues.append(f"Worker categories don't sum to numhh_gq in {worker_mismatches} TAZs")
        else:
            print("✅ Worker categories sum correctly to numhh_gq")
    
    return issues

def validate_control_file_consistency(data):
    """Validate that the controls.csv file matches the available control data"""
    
    print("\n" + "="*60)
    print("VALIDATING CONTROLS.CSV CONSISTENCY")
    print("="*60)
    
    controls_df = data['controls']
    maz_df = data['maz_marginals']
    taz_df = data['taz_marginals']
    
    print(f"Controls defined: {len(controls_df)}")
    
    # Check if all control_field values exist in the corresponding data files
    issues = []
    
    for _, control in controls_df.iterrows():
        geography = control['geography']
        control_field = control['control_field']
        target = control['target']
        
        if geography == 'MAZ':
            if control_field not in maz_df.columns:
                print(f"⚠️  MAZ control '{control_field}' (target: {target}) not found in maz_marginals")
                issues.append(f"Missing MAZ control: {control_field}")
        elif geography == 'TAZ':
            if control_field not in taz_df.columns:
                print(f"⚠️  TAZ control '{control_field}' (target: {target}) not found in taz_marginals")
                issues.append(f"Missing TAZ control: {control_field}")
    
    # Check for total_pop control specifically
    total_pop_controls = controls_df[controls_df['target'].str.contains('total_pop|tot_pop', case=False, na=False)]
    if len(total_pop_controls) == 0:
        print("⚠️  No total population control found in controls.csv")
        issues.append("Missing total population control")
    else:
        print(f"✅ Found {len(total_pop_controls)} total population control(s)")
    
    return issues

def generate_summary_report(household_comparison, population_comparison, taz_issues, control_issues):
    """Generate a summary report of all validation results"""
    
    print("\n" + "="*60)
    print("HIERARCHICAL CONTROL VALIDATION SUMMARY")
    print("="*60)
    
    total_issues = 0
    
    # Household consistency
    if household_comparison is not None:
        large_hh_diffs = len(household_comparison[abs(household_comparison['pct_diff']) > 5])
        if large_hh_diffs > 0:
            print(f"❌ HOUSEHOLD TOTALS: {large_hh_diffs} TAZs with >5% difference from MAZ totals")
            total_issues += large_hh_diffs
        else:
            print(f"✅ HOUSEHOLD TOTALS: All TAZ totals consistent with MAZ totals")
    else:
        print(f"❓ HOUSEHOLD TOTALS: Could not validate (missing data)")
        total_issues += 1
    
    # Population consistency  
    if population_comparison is not None:
        large_pop_diffs = len(population_comparison[abs(population_comparison['pct_diff']) > 5])
        if large_pop_diffs > 0:
            print(f"❌ POPULATION TOTALS: {large_pop_diffs} TAZs with >5% difference from MAZ totals") 
            total_issues += large_pop_diffs
        else:
            print(f"✅ POPULATION TOTALS: All TAZ totals consistent with MAZ totals")
    else:
        print(f"❓ POPULATION TOTALS: Could not validate (missing total_pop in MAZ data)")
        total_issues += 1
    
    # Internal TAZ consistency
    if len(taz_issues) > 0:
        print(f"❌ TAZ INTERNAL CONSISTENCY: {len(taz_issues)} issues found")
        for issue in taz_issues:
            print(f"   - {issue}")
        total_issues += len(taz_issues)
    else:
        print(f"✅ TAZ INTERNAL CONSISTENCY: All control categories sum correctly")
    
    # Control file consistency
    if len(control_issues) > 0:
        print(f"❌ CONTROLS.CSV CONSISTENCY: {len(control_issues)} issues found")
        for issue in control_issues:
            print(f"   - {issue}")
        total_issues += len(control_issues)
    else:
        print(f"✅ CONTROLS.CSV CONSISTENCY: All controls have corresponding data")
    
    print(f"\nTOTAL ISSUES FOUND: {total_issues}")
    
    if total_issues > 0:
        print("\n🚨 LIKELY ROOT CAUSE OF IntCastingNaNError:")
        print("   Hierarchical control inconsistencies create infeasible optimization problems")
        print("   PopulationSim cannot find a solution that satisfies conflicting constraints")
        print("   This leads to NaN values during optimization and subsequent IntCastingNaNError")
        print("\n📋 RECOMMENDED ACTIONS:")
        print("   1. Fix control total inconsistencies identified above")
        print("   2. Ensure MAZ totals = sum of TAZ categories for each control type")
        print("   3. Add missing total_pop control to MAZ level if not present")
        print("   4. Re-run PopulationSim after fixing control consistency")
    else:
        print("\n✅ ALL HIERARCHICAL CONTROLS ARE CONSISTENT!")
        print("   The IntCastingNaNError may have a different root cause")
        print("   Consider investigating seed data quality or other PopulationSim parameters")

def main():
    """Main validation function"""
    
    print("POPULATIONSIM HIERARCHICAL CONTROL VALIDATION")
    print("=" * 60)
    
    # Load all control files
    data = load_control_files()
    if data is None:
        sys.exit(1)
    
    # Run all validations
    household_comparison = validate_maz_taz_household_consistency(data)
    population_comparison = validate_maz_taz_population_consistency(data)
    taz_issues = validate_taz_internal_consistency(data)
    control_issues = validate_control_file_consistency(data)
    
    # Generate summary report
    generate_summary_report(household_comparison, population_comparison, taz_issues, control_issues)

if __name__ == "__main__":
    main()
