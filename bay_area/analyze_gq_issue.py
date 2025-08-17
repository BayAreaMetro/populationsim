#!/usr/bin/env python3
"""
Group Quarters Issue Analysis
Investigate why MAZs with GQ populations are getting excessive household allocations
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_gq_issue():
    """Analyze the group quarters allocation issue"""
    
    # Paths
    base_dir = Path("output_2023/populationsim_working_dir")
    data_dir = base_dir / "data"
    output_dir = base_dir / "output"
    
    logger.info("Loading data for GQ analysis...")
    
    # Load MAZ controls and results
    maz_controls = pd.read_csv(data_dir / "maz_marginals_hhgq.csv")
    synthetic_hh = pd.read_csv(output_dir / "synthetic_households.csv")
    synthetic_persons = pd.read_csv(output_dir / "synthetic_persons.csv")
    
    logger.info(f"Loaded: {len(maz_controls)} MAZ controls, {len(synthetic_hh)} synthetic households, {len(synthetic_persons)} synthetic persons")
    
    # Count households and persons by MAZ
    hh_by_maz = synthetic_hh.groupby('MAZ').size().reset_index(name='result_households')
    persons_by_maz = synthetic_persons.groupby('MAZ').agg({
        'hhgqtype': ['count', lambda x: (x >= 2).sum()],  # total persons, GQ persons
        'person_id': 'count'
    }).reset_index()
    persons_by_maz.columns = ['MAZ', 'result_persons', 'result_gq_persons', 'person_count_check']
    
    # Merge all data
    analysis_df = pd.merge(
        maz_controls[['MAZ', 'num_hh', 'total_pop', 'gq_pop', 'gq_military', 'gq_university', 'gq_other']], 
        hh_by_maz, 
        on='MAZ', 
        how='left'
    ).fillna(0)
    
    analysis_df = pd.merge(analysis_df, persons_by_maz, on='MAZ', how='left').fillna(0)
    
    # Calculate ratios and differences
    analysis_df['hh_over_allocation'] = analysis_df['result_households'] - analysis_df['num_hh']
    analysis_df['gq_pop_ratio'] = analysis_df['gq_pop'] / (analysis_df['total_pop'] + 0.001)
    analysis_df['hh_inflation_ratio'] = analysis_df['result_households'] / (analysis_df['num_hh'] + 0.001)
    
    # Focus on problematic MAZs
    problem_mazs = analysis_df[
        (analysis_df['gq_pop'] > 100) | 
        (analysis_df['hh_over_allocation'] > 100)
    ].copy()
    
    logger.info(f"Found {len(problem_mazs)} problematic MAZs with GQ issues")
    
    return analysis_df, problem_mazs

def investigate_specific_mazs(analysis_df, problem_mazs):
    """Look at specific MAZs to understand the issue"""
    
    logger.info("Investigating specific problematic MAZs...")
    
    # Get worst 10 by household over-allocation
    worst_mazs = problem_mazs.nlargest(10, 'hh_over_allocation')
    
    print("\nWORST 10 MAZs BY HOUSEHOLD OVER-ALLOCATION:")
    print("=" * 80)
    print(f"{'MAZ':<8} {'Target':<8} {'Result':<8} {'Over':<6} {'GQ Pop':<8} {'Total Pop':<10} {'GQ %':<8}")
    print("-" * 80)
    
    for _, row in worst_mazs.iterrows():
        gq_pct = row['gq_pop_ratio'] * 100
        print(f"{row['MAZ']:<8.0f} {row['num_hh']:<8.0f} {row['result_households']:<8.0f} {row['hh_over_allocation']:<6.0f} "
              f"{row['gq_pop']:<8.0f} {row['total_pop']:<10.0f} {gq_pct:<8.1f}")
    
    return worst_mazs

def check_synthetic_population_gq(worst_mazs):
    """Check how GQ is handled in the synthetic population for problematic MAZs"""
    
    logger.info("Checking synthetic population GQ handling...")
    
    # Load synthetic data
    base_dir = Path("output_2023/populationsim_working_dir/output")
    synthetic_hh = pd.read_csv(base_dir / "synthetic_households.csv")
    synthetic_persons = pd.read_csv(base_dir / "synthetic_persons.csv")
    
    # Check a few specific problematic MAZs
    test_mazs = worst_mazs.head(5)['MAZ'].values
    
    print(f"\nCHECKING SYNTHETIC POPULATION FOR MAZs: {test_mazs}")
    print("=" * 80)
    
    for maz in test_mazs:
        print(f"\nMAZ {maz}:")
        print("-" * 40)
        
        # Households in this MAZ
        maz_hh = synthetic_hh[synthetic_hh['MAZ'] == maz]
        print(f"Synthetic households: {len(maz_hh)}")
        
        # Check household types
        if 'hhgqtype' in maz_hh.columns:
            hh_types = maz_hh['hhgqtype'].value_counts().sort_index()
            print("Household types:")
            for hhgq_type, count in hh_types.items():
                type_name = {0: 'Regular HH', 1: 'University GQ', 2: 'Military GQ', 3: 'Other GQ'}.get(hhgq_type, f'Unknown ({hhgq_type})')
                print(f"  {type_name}: {count}")
        
        # Persons in this MAZ
        maz_persons = synthetic_persons[synthetic_persons['MAZ'] == maz]
        print(f"Synthetic persons: {len(maz_persons)}")
        
        # Check person GQ types
        if 'hhgqtype' in maz_persons.columns:
            person_types = maz_persons['hhgqtype'].value_counts().sort_index()
            print("Person GQ types:")
            for hhgq_type, count in person_types.items():
                type_name = {0: 'Household', 1: 'University GQ', 2: 'Military GQ', 3: 'Other GQ'}.get(hhgq_type, f'Unknown ({hhgq_type})')
                print(f"  {type_name}: {count}")
        
        print()

def check_seed_population_gq():
    """Check how GQ is set up in the seed population"""
    
    logger.info("Checking seed population GQ setup...")
    
    base_dir = Path("output_2023/populationsim_working_dir/data")
    
    # Check if seed files exist and their GQ handling
    seed_hh_file = base_dir / "seed_households.csv"
    seed_persons_file = base_dir / "seed_persons.csv"
    
    if seed_hh_file.exists():
        seed_hh = pd.read_csv(seed_hh_file)
        print(f"\nSEED HOUSEHOLDS: {len(seed_hh)} records")
        
        if 'hhgqtype' in seed_hh.columns:
            seed_hh_types = seed_hh['hhgqtype'].value_counts().sort_index()
            print("Seed household types:")
            for hhgq_type, count in seed_hh_types.items():
                type_name = {0: 'Regular HH', 1: 'University GQ', 2: 'Military GQ', 3: 'Other GQ'}.get(hhgq_type, f'Unknown ({hhgq_type})')
                pct = count / len(seed_hh) * 100
                print(f"  {type_name}: {count:,} ({pct:.1f}%)")
    
    if seed_persons_file.exists():
        # Sample persons to avoid memory issues
        seed_persons = pd.read_csv(seed_persons_file, nrows=100000)
        print(f"\nSEED PERSONS (sample): {len(seed_persons)} records")
        
        if 'hhgqtype' in seed_persons.columns:
            seed_person_types = seed_persons['hhgqtype'].value_counts().sort_index()
            print("Seed person GQ types:")
            for hhgq_type, count in seed_person_types.items():
                type_name = {0: 'Household', 1: 'University GQ', 2: 'Military GQ', 3: 'Other GQ'}.get(hhgq_type, f'Unknown ({hhgq_type})')
                pct = count / len(seed_persons) * 100
                print(f"  {type_name}: {count:,} ({pct:.1f}%)")

def check_populationsim_gq_controls():
    """Check PopulationSim GQ control setup"""
    
    logger.info("Checking PopulationSim GQ control configuration...")
    
    base_dir = Path("output_2023/populationsim_working_dir")
    
    # Check controls.csv
    controls_file = base_dir / "configs" / "controls.csv"
    if controls_file.exists():
        controls = pd.read_csv(controls_file)
        
        gq_controls = controls[controls['control_field'].str.contains('gq_', na=False)]
        print(f"\nGQ CONTROLS in controls.csv: {len(gq_controls)} found")
        
        for _, row in gq_controls.iterrows():
            print(f"  {row['control_field']}: {row['expression']} (importance: {row['importance']})")
    
    # Check settings.yaml for GQ configuration
    settings_file = base_dir / "configs" / "settings.yaml"
    if settings_file.exists():
        with open(settings_file, 'r') as f:
            settings_content = f.read()
        
        # Look for GQ-related settings
        gq_lines = [line.strip() for line in settings_content.split('\n') if 'gq' in line.lower() or 'hhgqtype' in line.lower()]
        
        if gq_lines:
            print(f"\nGQ-RELATED SETTINGS in settings.yaml:")
            for line in gq_lines:
                print(f"  {line}")

def create_gq_analysis_report(analysis_df, problem_mazs):
    """Create comprehensive GQ analysis report"""
    
    logger.info("Creating GQ analysis report...")
    
    report_lines = [
        "GROUP QUARTERS ISSUE ANALYSIS REPORT",
        "=" * 50,
        f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "SUMMARY STATISTICS",
        "-" * 30,
        f"Total MAZs: {len(analysis_df):,}",
        f"MAZs with GQ population > 0: {(analysis_df['gq_pop'] > 0).sum():,}",
        f"MAZs with GQ population > 100: {(analysis_df['gq_pop'] > 100).sum():,}",
        f"MAZs with household over-allocation > 100: {(analysis_df['hh_over_allocation'] > 100).sum():,}",
        f"Total GQ population in controls: {analysis_df['gq_pop'].sum():,.0f}",
        f"Total GQ persons in results: {analysis_df['result_gq_persons'].sum():,.0f}",
        "",
        "GQ POPULATION DISTRIBUTION",
        "-" * 30
    ]
    
    # GQ distribution analysis
    gq_bins = [0, 1, 10, 50, 100, 500, 1000, np.inf]
    gq_labels = ['0', '1-10', '11-50', '51-100', '101-500', '501-1000', '1000+']
    analysis_df['gq_size_category'] = pd.cut(analysis_df['gq_pop'], bins=gq_bins, labels=gq_labels, include_lowest=True)
    
    gq_dist = analysis_df['gq_size_category'].value_counts().sort_index()
    for category, count in gq_dist.items():
        pct = count / len(analysis_df) * 100
        report_lines.append(f"{str(category):<10}: {count:>6,} MAZs ({pct:>5.1f}%)")
    
    # Correlation analysis
    corr_hh_over_gq = analysis_df['hh_over_allocation'].corr(analysis_df['gq_pop'])
    report_lines.extend([
        "",
        "CORRELATION ANALYSIS",
        "-" * 30,
        f"Correlation (HH over-allocation vs GQ population): {corr_hh_over_gq:.3f}",
        "",
        "HYPOTHESIS",
        "-" * 30,
        "If correlation > 0.5, it suggests GQ persons are being",
        "converted to households instead of being handled as GQ.",
        ""
    ])
    
    # Save report
    report_file = Path("output_2023/populationsim_working_dir/gq_issue_analysis_report.txt")
    with open(report_file, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"GQ analysis report saved to {report_file}")

def main():
    """Main GQ analysis function"""
    
    logger.info("Starting Group Quarters issue analysis...")
    
    try:
        # Analyze GQ allocation
        analysis_df, problem_mazs = analyze_gq_issue()
        
        # Investigate specific problematic MAZs
        worst_mazs = investigate_specific_mazs(analysis_df, problem_mazs)
        
        # Check synthetic population for these MAZs
        check_synthetic_population_gq(worst_mazs)
        
        # Check seed population setup
        check_seed_population_gq()
        
        # Check PopulationSim configuration
        check_populationsim_gq_controls()
        
        # Create comprehensive report
        create_gq_analysis_report(analysis_df, problem_mazs)
        
        # Save detailed analysis
        analysis_df.to_csv("output_2023/populationsim_working_dir/gq_issue_detailed_analysis.csv", index=False)
        
        # Key findings
        corr_value = analysis_df['hh_over_allocation'].corr(analysis_df['gq_pop'])
        print(f"\n{'='*60}")
        print("KEY FINDINGS - GROUP QUARTERS ISSUE")
        print(f"{'='*60}")
        print(f"Correlation (HH over-allocation vs GQ pop): {corr_value:.3f}")
        if corr_value > 0.5:
            print("🚨 ISSUE CONFIRMED: Strong positive correlation suggests")
            print("   GQ persons are being converted to households!")
        elif corr_value > 0.2:
            print("⚠️  POSSIBLE ISSUE: Moderate correlation suggests")
            print("   some GQ persons may be converted to households")
        else:
            print("✅ No strong correlation - GQ handling may be correct")
        
        print(f"\nMAZs with large GQ populations: {(analysis_df['gq_pop'] > 100).sum():,}")
        print(f"MAZs with excessive household over-allocation: {(analysis_df['hh_over_allocation'] > 100).sum():,}")
        
        logger.info("GQ issue analysis completed successfully!")
        
    except Exception as e:
        logger.error(f"GQ analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
