#!/usr/bin/env python3
"""
Clean Household Comparison Analysis
==================================

Simple, direct comparison of household controls vs synthetic outputs:
- Control Total HH (including GQ) vs Synthetic Total HH
- Control GQ (Uni + Noninst) vs Synthetic GQ
- Proper scatter plots showing actual performance

Files used:
- Controls: maz_marginals_hhgq.csv
- Synthetic: households_2023_tm2.csv
- Household types: 1=Regular, 3=GQ
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def load_clean_data():
    """Load and prepare the data correctly"""
    print("Loading data...")
    
    # Load controls
    controls = pd.read_csv('output_2023/populationsim_working_dir/data/maz_marginals_hhgq.csv')
    print(f"Loaded {len(controls):,} MAZ controls")
    print(f"Control columns: {list(controls.columns)}")
    
    # Load synthetic households  
    synthetic = pd.read_csv('output_2023/populationsim_working_dir/output/households_2023_tm2.csv')
    print(f"Loaded {len(synthetic):,} synthetic households")
    
    # Check household types
    print(f"Household types in synthetic data:")
    print(synthetic['TYPE'].value_counts().sort_index())
    
    return controls, synthetic

def create_comparison_table(controls, synthetic):
    """Create the comparison table with all metrics"""
    print("\nCreating comparison table...")
    
    # Aggregate controls by MAZ
    control_summary = controls.groupby('MAZ_NODE').agg({
        'numhh_gq': 'sum',        # Total households (including GQ)
        'gq_type_univ': 'sum',    # University GQ
        'gq_type_noninst': 'sum'  # Non-institutional GQ  
    }).reset_index()
    
    # Calculate total GQ and regular households in controls
    control_summary['control_total_gq'] = control_summary['gq_type_univ'] + control_summary['gq_type_noninst']
    control_summary['control_regular_hh'] = control_summary['numhh_gq'] - control_summary['control_total_gq']
    
    # Aggregate synthetic by MAZ and TYPE
    synthetic_by_maz_type = synthetic.groupby(['MAZ', 'TYPE']).size().reset_index(name='count')
    synthetic_pivot = synthetic_by_maz_type.pivot(index='MAZ', columns='TYPE', values='count').fillna(0)
    
    # Ensure we have both types
    if 1 not in synthetic_pivot.columns:
        synthetic_pivot[1] = 0
    if 3 not in synthetic_pivot.columns:
        synthetic_pivot[3] = 0
        
    synthetic_pivot.columns = ['synthetic_regular_hh', 'synthetic_gq_hh']
    synthetic_pivot['synthetic_total_hh'] = synthetic_pivot['synthetic_regular_hh'] + synthetic_pivot['synthetic_gq_hh']
    synthetic_pivot = synthetic_pivot.reset_index()
    synthetic_pivot = synthetic_pivot.rename(columns={'MAZ': 'MAZ_NODE'})
    
    # Merge controls and synthetic
    comparison = pd.merge(control_summary, synthetic_pivot, on='MAZ_NODE', how='outer')
    comparison = comparison.fillna(0)
    
    # Calculate differences
    comparison['diff_total_hh'] = comparison['synthetic_total_hh'] - comparison['numhh_gq']
    comparison['diff_gq_hh'] = comparison['synthetic_gq_hh'] - comparison['control_total_gq']
    comparison['diff_regular_hh'] = comparison['synthetic_regular_hh'] - comparison['control_regular_hh']
    comparison['diff_uni_gq'] = comparison['synthetic_gq_hh'] - comparison['gq_type_univ']  # Simplified for now
    
    # Calculate percentage differences (avoid division by zero)
    comparison['pct_diff_total_hh'] = np.where(
        comparison['numhh_gq'] > 0,
        (comparison['diff_total_hh'] / comparison['numhh_gq']) * 100,
        0
    )
    comparison['pct_diff_gq_hh'] = np.where(
        comparison['control_total_gq'] > 0,
        (comparison['diff_gq_hh'] / comparison['control_total_gq']) * 100,
        0
    )
    
    return comparison

def create_summary_stats(comparison):
    """Print summary statistics"""
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    
    # Total counts
    total_control_hh = comparison['numhh_gq'].sum()
    total_synthetic_hh = comparison['synthetic_total_hh'].sum()
    total_control_gq = comparison['control_total_gq'].sum()
    total_synthetic_gq = comparison['synthetic_gq_hh'].sum()
    total_control_regular = comparison['control_regular_hh'].sum()
    total_synthetic_regular = comparison['synthetic_regular_hh'].sum()
    
    print(f"\nREGION-WIDE TOTALS:")
    print(f"Total Households:")
    print(f"  Control: {total_control_hh:,}")
    print(f"  Synthetic: {total_synthetic_hh:,}")
    print(f"  Difference: {total_synthetic_hh - total_control_hh:,}")
    print(f"  % Difference: {((total_synthetic_hh - total_control_hh) / total_control_hh) * 100:.3f}%")
    
    print(f"\nRegular Households:")
    print(f"  Control: {total_control_regular:,}")
    print(f"  Synthetic: {total_synthetic_regular:,}")
    print(f"  Difference: {total_synthetic_regular - total_control_regular:,}")
    print(f"  % Difference: {((total_synthetic_regular - total_control_regular) / total_control_regular) * 100:.3f}%")
    
    print(f"\nGroup Quarters Households:")
    print(f"  Control: {total_control_gq:,}")
    print(f"  Synthetic: {total_synthetic_gq:,}")
    print(f"  Difference: {total_synthetic_gq - total_control_gq:,}")
    if total_control_gq > 0:
        print(f"  % Difference: {((total_synthetic_gq - total_control_gq) / total_control_gq) * 100:.3f}%")
    
    # MAZ-level statistics
    perfect_total = (comparison['diff_total_hh'] == 0).sum()
    perfect_gq = (comparison['diff_gq_hh'] == 0).sum()
    total_mazs = len(comparison)
    
    print(f"\nMAZ-LEVEL PERFORMANCE:")
    print(f"Total MAZs: {total_mazs:,}")
    print(f"Perfect total HH matches: {perfect_total:,} ({perfect_total/total_mazs*100:.1f}%)")
    print(f"Perfect GQ HH matches: {perfect_gq:,} ({perfect_gq/total_mazs*100:.1f}%)")
    
    # Error metrics
    mae_total = comparison['diff_total_hh'].abs().mean()
    mae_gq = comparison['diff_gq_hh'].abs().mean()
    rmse_total = np.sqrt((comparison['diff_total_hh'] ** 2).mean())
    
    print(f"\nERROR METRICS:")
    print(f"Total HH - MAE: {mae_total:.3f}, RMSE: {rmse_total:.3f}")
    print(f"GQ HH - MAE: {mae_gq:.3f}")

def create_scatter_plots(comparison):
    """Create scatter plots showing performance"""
    print("\nCreating scatter plots...")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('PopulationSim Household Performance Analysis', fontsize=16, fontweight='bold')
    
    # 1. Total Households
    ax1 = axes[0, 0]
    ax1.scatter(comparison['numhh_gq'], comparison['synthetic_total_hh'], alpha=0.6, s=20)
    max_val = max(comparison['numhh_gq'].max(), comparison['synthetic_total_hh'].max())
    ax1.plot([0, max_val], [0, max_val], 'r--', linewidth=2, label='Perfect Match')
    ax1.set_xlabel('Control Total Households')
    ax1.set_ylabel('Synthetic Total Households')
    ax1.set_title('Total Households (Regular + GQ)')
    ax1.legend()
    
    # Calculate R²
    r_total = np.corrcoef(comparison['numhh_gq'], comparison['synthetic_total_hh'])[0, 1] ** 2
    ax1.text(0.05, 0.95, f'R² = {r_total:.6f}', transform=ax1.transAxes, 
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # 2. GQ Households
    ax2 = axes[0, 1]
    mask_gq = comparison['control_total_gq'] > 0  # Only plot MAZs with GQ
    if mask_gq.sum() > 0:
        ax2.scatter(comparison.loc[mask_gq, 'control_total_gq'], 
                   comparison.loc[mask_gq, 'synthetic_gq_hh'], alpha=0.6, s=20)
        max_val_gq = max(comparison.loc[mask_gq, 'control_total_gq'].max(), 
                        comparison.loc[mask_gq, 'synthetic_gq_hh'].max())
        ax2.plot([0, max_val_gq], [0, max_val_gq], 'r--', linewidth=2, label='Perfect Match')
        
        # Calculate R² for GQ
        r_gq = np.corrcoef(comparison.loc[mask_gq, 'control_total_gq'], 
                          comparison.loc[mask_gq, 'synthetic_gq_hh'])[0, 1] ** 2
        ax2.text(0.05, 0.95, f'R² = {r_gq:.6f}', transform=ax2.transAxes,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax2.set_xlabel('Control GQ Households')
    ax2.set_ylabel('Synthetic GQ Households')
    ax2.set_title('Group Quarters Households')
    ax2.legend()
    
    # 3. Error distribution - Total HH
    ax3 = axes[1, 0]
    ax3.hist(comparison['diff_total_hh'], bins=50, alpha=0.7, edgecolor='black')
    ax3.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Perfect Match')
    ax3.set_xlabel('Difference (Synthetic - Control)')
    ax3.set_ylabel('Number of MAZs')
    ax3.set_title('Total HH Error Distribution')
    ax3.legend()
    
    # 4. Error distribution - GQ HH
    ax4 = axes[1, 1]
    ax4.hist(comparison['diff_gq_hh'], bins=50, alpha=0.7, edgecolor='black')
    ax4.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Perfect Match')
    ax4.set_xlabel('Difference (Synthetic - Control)')
    ax4.set_ylabel('Number of MAZs')
    ax4.set_title('GQ HH Error Distribution')
    ax4.legend()
    
    plt.tight_layout()
    
    # Save plot
    output_dir = Path('output_2023/charts')
    output_dir.mkdir(exist_ok=True)
    plot_file = output_dir / 'clean_household_performance.png'
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"Scatter plots saved to: {plot_file}")
    
    return fig

def main():
    """Main analysis function"""
    print("Clean Household Comparison Analysis")
    print("=" * 50)
    
    # Load data
    controls, synthetic = load_clean_data()
    
    # Create comparison table
    comparison = create_comparison_table(controls, synthetic)
    
    # Save comparison table
    output_dir = Path('output_2023/charts')
    output_dir.mkdir(exist_ok=True)
    comparison_file = output_dir / 'clean_household_comparison.csv'
    comparison.to_csv(comparison_file, index=False)
    print(f"\nComparison table saved to: {comparison_file}")
    
    # Print summary statistics
    create_summary_stats(comparison)
    
    # Create scatter plots
    create_scatter_plots(comparison)
    
    # Show some examples
    print(f"\nEXAMPLE MAZs WITH DISCREPANCIES:")
    discrepancies = comparison[comparison['diff_total_hh'] != 0].head(10)
    if len(discrepancies) > 0:
        print(discrepancies[['MAZ_NODE', 'numhh_gq', 'synthetic_total_hh', 'diff_total_hh',
                           'control_total_gq', 'synthetic_gq_hh', 'diff_gq_hh']].to_string())
    else:
        print("No discrepancies found in total households!")
    
    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()