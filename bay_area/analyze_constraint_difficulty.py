#!/usr/bin/env python3
"""
Analyze which constraints are most problematic in PopulationSim convergence.
This script examines the patterns from the terminal output to identify constraint issues.
"""

import pandas as pd
import numpy as np
import re

def analyze_convergence_patterns():
    """
    Analyze convergence patterns from the recent PUMAs to identify problematic constraints.
    """
    
    print("🔍 POPULATIONSIM CONSTRAINT DIFFICULTY ANALYSIS")
    print("=" * 60)
    
    # Recent PUMA convergence data from terminal output
    puma_data = [
        {
            'puma': 121, 
            'households': 2304, 
            'zones': 64, 
            'initial_gamma': 32382.9, 
            'final_gamma': 872.6,
            'zero_weight_rows': 2,
            'int_shortfall_max': 725,
            'converged': False
        },
        {
            'puma': 115, 
            'households': 1933, 
            'zones': 70, 
            'initial_gamma': 2248.4, 
            'final_gamma': 366.1,
            'zero_weight_rows': 0,
            'int_shortfall_max': 488,
            'converged': False
        },
        {
            'puma': 116, 
            'households': 1773, 
            'zones': 51, 
            'initial_gamma': 112.4, 
            'final_gamma': 97.0,
            'zero_weight_rows': 0,
            'int_shortfall_max': 652,
            'converged': False
        },
        {
            'puma': 122, 
            'households': 1772, 
            'zones': 57, 
            'initial_gamma': 128.3, 
            'final_gamma': 65.4,
            'zero_weight_rows': 0,
            'int_shortfall_max': 441,
            'converged': False
        },
        {
            'puma': 120, 
            'households': 2166, 
            'zones': 56, 
            'initial_gamma': 439.5, 
            'final_gamma': 147.0,
            'zero_weight_rows': 0,
            'int_shortfall_max': 757,
            'converged': False
        },
        {
            'puma': 119, 
            'households': 2506, 
            'zones': 62, 
            'initial_gamma': 16981.3, 
            'final_gamma': 1804.8,
            'zero_weight_rows': 0,
            'int_shortfall_max': None,  # Still processing
            'converged': False
        }
    ]
    
    df = pd.DataFrame(puma_data)
    
    print("\n📊 PUMA CONVERGENCE DIFFICULTY RANKING:")
    print("-" * 40)
    
    # Calculate difficulty score
    df['difficulty_score'] = (
        df['initial_gamma'] * 0.4 + 
        df['final_gamma'] * 0.3 + 
        (df['zones'] / df['households'] * 1000) * 0.2 +
        df['int_shortfall_max'].fillna(0) * 0.1
    )
    
    df_sorted = df.sort_values('difficulty_score', ascending=False)
    
    for _, row in df_sorted.iterrows():
        print(f"PUMA {row['puma']:3d}: Difficulty Score {row['difficulty_score']:8.1f}")
        print(f"  - Initial γ: {row['initial_gamma']:8.1f}, Final γ: {row['final_gamma']:6.1f}")
        print(f"  - {row['households']:4d} HH across {row['zones']:2d} zones ({row['zones']/row['households']*100:.1f}% zone density)")
        if pd.notna(row['int_shortfall_max']):
            print(f"  - Max integer shortfall: {row['int_shortfall_max']}")
        print()
    
    print("\n🎯 CONSTRAINT DIFFICULTY ANALYSIS:")
    print("-" * 40)
    
    # Load controls to analyze constraint structure
    try:
        controls_df = pd.read_csv('output_2023/populationsim_working_dir/configs/controls.csv')
        
        print(f"Total controls: {len(controls_df)}")
        print(f"Geography levels: {controls_df['geography'].unique()}")
        print(f"Control types: {controls_df['target'].unique()}")
        
        # Identify potentially problematic constraint patterns
        print("\n🔥 POTENTIALLY PROBLEMATIC CONSTRAINTS:")
        print("-" * 40)
        
        # High importance constraints
        high_importance = controls_df[controls_df['importance'] >= 1000000]
        print(f"\n1. HIGH IMPORTANCE CONSTRAINTS ({len(high_importance)} total):")
        for _, row in high_importance.iterrows():
            print(f"   - {row['target']:20s} (importance: {row['importance']:8.0f}) [{row['geography']}]")
        
        # Group quarters constraints (new and potentially unstable)
        gq_constraints = controls_df[controls_df['target'].str.contains('gq_|numhh_gq')]
        print(f"\n2. GROUP QUARTERS CONSTRAINTS ({len(gq_constraints)} total):")
        for _, row in gq_constraints.iterrows():
            print(f"   - {row['target']:20s} (importance: {row['importance']:8.0f}) [{row['geography']}]")
            print(f"     Expression: {row['expression']}")
        
        # Income constraints (complex expressions)
        income_constraints = controls_df[controls_df['target'].str.contains('hh_inc_')]
        print(f"\n3. INCOME CONSTRAINTS ({len(income_constraints)} total):")
        for _, row in income_constraints.iterrows():
            print(f"   - {row['target']:20s} (importance: {row['importance']:8.0f}) [{row['geography']}]")
        
        # MAZ-level constraints (finest geography, most difficult)
        maz_constraints = controls_df[controls_df['geography'] == 'MAZ']
        print(f"\n4. MAZ-LEVEL CONSTRAINTS ({len(maz_constraints)} total - MOST DIFFICULT):")
        for _, row in maz_constraints.iterrows():
            print(f"   - {row['target']:20s} (importance: {row['importance']:8.0f})")
        
    except FileNotFoundError:
        print("Controls file not found - run from correct directory")
    
    print("\n💡 CONSTRAINT DIFFICULTY FACTORS:")
    print("-" * 40)
    print("1. HIGHEST GAMMA VALUES INDICATE:")
    print("   - PUMA 121: γ=32,382 → Severe constraint conflicts")
    print("   - PUMA 119: γ=16,981 → Major balancing issues") 
    print("   - These suggest incompatible control targets")
    print()
    print("2. ZONE COMPLEXITY:")
    print("   - PUMA 115: 70 zones (highest) → Complex geography")
    print("   - PUMA 121: 64 zones → High subdivision complexity")
    print("   - More zones = exponentially harder balancing")
    print()
    print("3. INTEGER SHORTFALL PATTERNS:")
    print("   - Values 400-700+ suggest large rounding conflicts")
    print("   - May indicate controls with small target values")
    print("   - GQ constraints particularly vulnerable")
    print()
    print("4. ZERO WEIGHT ROWS:")
    print("   - PUMA 121: 2 zero-weight rows → Filtering issues")
    print("   - Could indicate constraint impossibilities")
    
    print("\n🚀 OPTIMIZATION RECOMMENDATIONS:")
    print("-" * 40)
    print("1. REDUCE GQ CONSTRAINT IMPORTANCE:")
    print("   - Lower gq_military, gq_university, gq_other from 1M to 100K")
    print("   - These are new constraints and may be over-specified")
    print()
    print("2. RELAX MAZ-LEVEL CONTROLS:")
    print("   - MAZ controls are most constraining due to fine geography")
    print("   - Consider moving some to TAZ level if possible")
    print()
    print("3. ADJUST INCOME CONSTRAINT IMPORTANCE:")
    print("   - Income constraints have importance 1M (very high)")
    print("   - May be conflicting with household size/worker constraints")
    print()
    print("4. APPLY CONVERGENCE SETTINGS WE ADDED:")
    print("   - New MAX_DELTA=1e-6, MAX_GAMMA=1e-4 will help")
    print("   - Reduced iteration limits will prevent endless looping")

if __name__ == "__main__":
    analyze_convergence_patterns()
