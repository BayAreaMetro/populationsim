#!/usr/bin/env python3
"""
MAZ Household Comparison Analysis
================================

Clean analysis comparing MAZ-level household controls vs synthetic outputs:
- Control Total HH (including GQ) vs Synthetic Total HH
- Control GQ HH (uni +            r2_gq = np.corrcoef(x_vals_gq, y_vals_gq)[0, 1] ** 2
            eqn_gq = f'y = {m_gq:.3f}x + {b_gq:.1f}'
            ax3.text(0.5, 0.5, f'R² = {r2_gq:.4f}\n{eqn_gq}', transform=ax3.transAxes,
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, pad=0.5, edgecolor='black'),
                     fontsize=10, ha='center', va='center', fontweight='bold')
        else:
            ax3.text(0.5, 0.5, 'Insufficient data for regression', transform=ax3.transAxes,
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, pad=0.5, edgecolor='black'),
                     ha='center', va='center', fontweight='bold') vs Synthetic GQ HH  
- Control Uni HH vs Synthetic Uni HH
- Control Noninst HH vs Synthetic Noninst HH

Data Sources:
- Controls: maz_marginals_hhgq.csv
- Synthetic: households_2023_tm2.csv

Expected TYPE values:
- TYPE=1: Regular households
- TYPE=3: Group quarters households
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def load_data():
    """Load control and synthetic data"""
    print("Loading data...")
    
    # Get the script directory and determine paths relative to workspace root
    script_dir = Path(__file__).parent
    workspace_root = script_dir.parent
    
    # Load controls
    controls_file = workspace_root / "output_2023/populationsim_working_dir/data/maz_marginals_hhgq.csv"
    controls = pd.read_csv(controls_file)
    print(f"Loaded {len(controls):,} MAZ controls")
    print(f"Control columns: {list(controls.columns)}")
    
    # Load synthetic households
    synthetic_file = workspace_root / "output_2023/populationsim_working_dir/output/households_2023_tm2.csv"
    synthetic = pd.read_csv(synthetic_file)
    print(f"Loaded {len(synthetic):,} synthetic households")
    print(f"Synthetic columns: {list(synthetic.columns)}")
    
    # Check TYPE values
    print(f"\\nSynthetic TYPE values:")
    print(synthetic['TYPE'].value_counts().sort_index())
    
    return controls, synthetic

def create_comparison_table(controls, synthetic):
    """Create comparison table with controls vs synthetic outputs"""
    print("\\nCreating comparison table...")
    
    # Aggregate synthetic households by MAZ_NODE and TYPE
    synthetic_agg = synthetic.groupby(['MAZ_NODE', 'TYPE']).size().reset_index(name='count')
    
    # Pivot to get TYPE columns
    synthetic_pivot = synthetic_agg.pivot(index='MAZ_NODE', columns='TYPE', values='count').fillna(0)
    synthetic_pivot.columns = [f'syn_type_{int(col)}' for col in synthetic_pivot.columns]
    
    # Calculate totals
    if 'syn_type_1' not in synthetic_pivot.columns:
        synthetic_pivot['syn_type_1'] = 0
    if 'syn_type_3' not in synthetic_pivot.columns:
        synthetic_pivot['syn_type_3'] = 0
        
    synthetic_pivot['syn_total_hh'] = synthetic_pivot['syn_type_1'] + synthetic_pivot['syn_type_3']  # Sum only household types
    synthetic_pivot['syn_gq_hh'] = synthetic_pivot['syn_type_3']  # TYPE=3 for GQ
    synthetic_pivot['syn_regular_hh'] = synthetic_pivot['syn_type_1']  # TYPE=1 for regular
    
    # Reset index to get MAZ_NODE as column
    synthetic_pivot = synthetic_pivot.reset_index()
    
    # Prepare controls
    controls_clean = controls[['MAZ_NODE', 'numhh_gq', 'gq_type_univ', 'gq_type_noninst']].copy()
    controls_clean['control_total_hh'] = controls_clean['numhh_gq']
    controls_clean['control_gq_hh'] = controls_clean['gq_type_univ'] + controls_clean['gq_type_noninst']
    controls_clean['control_regular_hh'] = controls_clean['numhh_gq'] - controls_clean['control_gq_hh']
    controls_clean['control_uni_hh'] = controls_clean['gq_type_univ']
    controls_clean['control_noninst_hh'] = controls_clean['gq_type_noninst']
    
    # Merge controls and synthetic
    comparison = pd.merge(controls_clean, synthetic_pivot, on='MAZ_NODE', how='outer')
    comparison = comparison.fillna(0)
    
    # Calculate differences and percentages
    comparison['diff_total_hh'] = comparison['syn_total_hh'] - comparison['control_total_hh']
    comparison['diff_gq_hh'] = comparison['syn_gq_hh'] - comparison['control_gq_hh']
    comparison['diff_regular_hh'] = comparison['syn_regular_hh'] - comparison['control_regular_hh']
    comparison['diff_uni_hh'] = comparison['syn_gq_hh'] - comparison['control_uni_hh']  # All synthetic GQ vs control university GQ
    comparison['diff_noninst_hh'] = comparison['syn_gq_hh'] - comparison['control_noninst_hh']  # All synthetic GQ vs control non-institutional GQ
    
    # Calculate percentage differences (handle division by zero)
    comparison['pct_diff_total_hh'] = np.where(
        comparison['control_total_hh'] > 0,
        (comparison['diff_total_hh'] / comparison['control_total_hh']) * 100,
        0
    )
    
    comparison['pct_diff_gq_hh'] = np.where(
        comparison['control_gq_hh'] > 0,
        (comparison['diff_gq_hh'] / comparison['control_gq_hh']) * 100,
        0
    )
    
    comparison['pct_diff_regular_hh'] = np.where(
        comparison['control_regular_hh'] > 0,
        (comparison['diff_regular_hh'] / comparison['control_regular_hh']) * 100,
        0
    )
    
    comparison['pct_diff_uni_hh'] = np.where(
        comparison['control_uni_hh'] > 0,
        (comparison['diff_uni_hh'] / comparison['control_uni_hh']) * 100,
        0
    )
    
    comparison['pct_diff_noninst_hh'] = np.where(
        comparison['control_noninst_hh'] > 0,
        (comparison['diff_noninst_hh'] / comparison['control_noninst_hh']) * 100,
        0
    )
    
    print(f"Comparison table created with {len(comparison):,} MAZs")
    
    return comparison

def print_summary_stats(comparison):
    """Print summary statistics"""
    print("\\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    
    print(f"\\nTotal Households (Regular + GQ):")
    total_control = comparison['control_total_hh'].sum()
    total_synthetic = comparison['syn_total_hh'].sum()
    total_diff = total_synthetic - total_control
    total_pct = (total_diff / total_control) * 100 if total_control > 0 else 0
    print(f"  Control: {total_control:,}")
    print(f"  Synthetic: {total_synthetic:,}")
    print(f"  Difference: {total_diff:,} ({total_pct:.3f}%)")
    
    print(f"\\nRegular Households:")
    reg_control = comparison['control_regular_hh'].sum()
    reg_synthetic = comparison['syn_regular_hh'].sum()
    reg_diff = reg_synthetic - reg_control
    reg_pct = (reg_diff / reg_control) * 100 if reg_control > 0 else 0
    print(f"  Control: {reg_control:,}")
    print(f"  Synthetic: {reg_synthetic:,}")
    print(f"  Difference: {reg_diff:,} ({reg_pct:.3f}%)")
    
    print(f"\\nGroup Quarters Households:")
    gq_control = comparison['control_gq_hh'].sum()
    gq_synthetic = comparison['syn_gq_hh'].sum()
    gq_diff = gq_synthetic - gq_control
    gq_pct = (gq_diff / gq_control) * 100 if gq_control > 0 else 0
    print(f"  Control: {gq_control:,}")
    print(f"  Synthetic: {gq_synthetic:,}")
    print(f"  Difference: {gq_diff:,} ({gq_pct:.3f}%)")
    
    print(f"\\nMAZ-Level Performance:")
    perfect_total = (comparison['diff_total_hh'] == 0).sum()
    perfect_gq = (comparison['diff_gq_hh'] == 0).sum()
    total_mazs = len(comparison)
    print(f"  Perfect Total HH matches: {perfect_total:,}/{total_mazs:,} ({perfect_total/total_mazs*100:.1f}%)")
    print(f"  Perfect GQ HH matches: {perfect_gq:,}/{total_mazs:,} ({perfect_gq/total_mazs*100:.1f}%)")

def create_scatter_plots(comparison):
    """Create scatter plots comparing controls vs synthetic"""
    print("\\nCreating scatter plots...")
    
    # Create output directory relative to workspace root
    script_dir = Path(__file__).parent
    workspace_root = script_dir.parent
    output_dir = workspace_root / "output_2023/charts"
    output_dir.mkdir(exist_ok=True)
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('MAZ Household Controls vs Synthetic Outputs', fontsize=16, fontweight='bold')
    
    # 1. Total Households
    ax1 = axes[0, 0]
    ax1.scatter(comparison['control_total_hh'], comparison['syn_total_hh'], alpha=0.6, s=20)
    
    # Perfect match line
    max_val = max(comparison['control_total_hh'].max(), comparison['syn_total_hh'].max())
    ax1.plot([0, max_val], [0, max_val], 'r--', linewidth=2, label='Perfect Match')
    
    # Best fit line and equation
    x_vals = comparison['control_total_hh']
    y_vals = comparison['syn_total_hh']
    coeffs = np.polyfit(x_vals, y_vals, 1)
    m, b = coeffs
    ax1.plot(x_vals, m * x_vals + b, 'orange', linewidth=2, alpha=0.8, label='Best Fit')
    
    # Calculate R² and show equation
    r2_total = np.corrcoef(x_vals, y_vals)[0, 1] ** 2
    eqn = f'y = {m:.3f}x + {b:.1f}'
    ax1.text(0.5, 0.5, f'R² = {r2_total:.4f}\n{eqn}', transform=ax1.transAxes, 
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, pad=0.5, edgecolor='black'),
             fontsize=10, ha='center', va='center', fontweight='bold')
    
    ax1.set_xlabel('Control Total Households')
    ax1.set_ylabel('Synthetic Total Households')
    ax1.set_title('Total Households (Regular + GQ)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Regular Households
    ax2 = axes[0, 1]
    ax2.scatter(comparison['control_regular_hh'], comparison['syn_regular_hh'], alpha=0.6, s=20, color='green')
    
    max_val_reg = max(comparison['control_regular_hh'].max(), comparison['syn_regular_hh'].max())
    ax2.plot([0, max_val_reg], [0, max_val_reg], 'r--', linewidth=2, label='Perfect Match')
    
    # Best fit line and equation
    x_vals_reg = comparison['control_regular_hh']
    y_vals_reg = comparison['syn_regular_hh']
    coeffs_reg = np.polyfit(x_vals_reg, y_vals_reg, 1)
    m_reg, b_reg = coeffs_reg
    ax2.plot(x_vals_reg, m_reg * x_vals_reg + b_reg, 'orange', linewidth=2, alpha=0.8, label='Best Fit')
    
    r2_reg = np.corrcoef(x_vals_reg, y_vals_reg)[0, 1] ** 2
    eqn_reg = f'y = {m_reg:.3f}x + {b_reg:.1f}'
    ax2.text(0.5, 0.5, f'R² = {r2_reg:.4f}\n{eqn_reg}', transform=ax2.transAxes,
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, pad=0.5, edgecolor='black'),
             fontsize=10, ha='center', va='center', fontweight='bold')
    
    ax2.set_xlabel('Control Regular Households')
    ax2.set_ylabel('Synthetic Regular Households')
    ax2.set_title('Regular Households Only')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Group Quarters Households
    ax3 = axes[1, 0]
    # Only plot MAZs with GQ households
    gq_data = comparison[comparison['control_gq_hh'] > 0]
    if len(gq_data) > 0:
        ax3.scatter(gq_data['control_gq_hh'], gq_data['syn_gq_hh'], alpha=0.6, s=20, color='orange')
        
        max_val_gq = max(gq_data['control_gq_hh'].max(), gq_data['syn_gq_hh'].max())
        ax3.plot([0, max_val_gq], [0, max_val_gq], 'r--', linewidth=2, label='Perfect Match')
        
        # Best fit line and equation for GQ households
        if len(gq_data) > 1:  # Need at least 2 points for regression
            x_vals_gq = gq_data['control_gq_hh']
            y_vals_gq = gq_data['syn_gq_hh']
            coeffs_gq = np.polyfit(x_vals_gq, y_vals_gq, 1)
            m_gq, b_gq = coeffs_gq
            ax3.plot(x_vals_gq, m_gq * x_vals_gq + b_gq, 'orange', linewidth=2, alpha=0.8, label='Best Fit')
            
            r2_gq = np.corrcoef(x_vals_gq, y_vals_gq)[0, 1] ** 2
            eqn_gq = f'y = {m_gq:.3f}x + {b_gq:.1f}'
            ax3.text(0.05, 0.95, f'R² = {r2_gq:.4f}\n{eqn_gq}', transform=ax3.transAxes,
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, pad=0.5),
                     fontsize=10, verticalalignment='top')
        else:
            ax3.text(0.05, 0.95, 'Insufficient data for regression', transform=ax3.transAxes,
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, pad=0.5),
                     fontsize=10, verticalalignment='top')
    
    ax3.set_xlabel('Control GQ Households')
    ax3.set_ylabel('Synthetic GQ Households')
    ax3.set_title('Group Quarters Households Only')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Difference Distribution
    ax4 = axes[1, 1]
    ax4.hist(comparison['diff_total_hh'], bins=50, alpha=0.7, color='blue', edgecolor='black')
    ax4.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Perfect Match')
    ax4.set_xlabel('Difference (Synthetic - Control)')
    ax4.set_ylabel('Number of MAZs')
    ax4.set_title('Total Household Difference Distribution')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot
    plot_file = output_dir / "MAZ_household_comparison.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"Scatter plots saved to: {plot_file}")
    plt.show()

def save_comparison_table(comparison):
    """Save the comparison table to CSV"""
    script_dir = Path(__file__).parent
    workspace_root = script_dir.parent
    output_dir = workspace_root / "output_2023/charts"
    output_dir.mkdir(exist_ok=True)
    
    # Select key columns for output - include all relevant columns for comparison
    output_cols = [
        'MAZ_NODE',
        'control_total_hh', 'syn_total_hh', 'diff_total_hh', 'pct_diff_total_hh',
        'control_regular_hh', 'syn_regular_hh', 'diff_regular_hh', 'pct_diff_regular_hh',
        'control_gq_hh', 'syn_gq_hh', 'diff_gq_hh', 'pct_diff_gq_hh',
        'control_uni_hh', 'control_noninst_hh',
        'diff_uni_hh', 'pct_diff_uni_hh',
        'diff_noninst_hh', 'pct_diff_noninst_hh'
    ]
    
    output_table = comparison[output_cols].copy()
    
    # Save to CSV
    csv_file = output_dir / "MAZ_household_comparison_table.csv"
    output_table.to_csv(csv_file, index=False)
    print(f"\\nComparison table saved to: {csv_file}")
    
    # Debug: Check a few specific MAZs to verify calculations
    debug_mazs = [10021, 10022]
    print(f"\\nDEBUG: Checking calculations for MAZs {debug_mazs}:")
    for maz in debug_mazs:
        maz_data = comparison[comparison['MAZ_NODE'] == maz]
        if len(maz_data) > 0:
            row = maz_data.iloc[0]
            print(f"\\nMAZ {maz}:")
            print(f"  Control: {row['control_regular_hh']:.0f} regular + {row['control_gq_hh']:.0f} GQ = {row['control_total_hh']:.0f} total")
            print(f"  Synthetic: {row['syn_regular_hh']:.0f} regular + {row['syn_gq_hh']:.0f} GQ = {row['syn_total_hh']:.0f} total")
            print(f"  Control GQ breakdown: {row['control_uni_hh']:.0f} university + {row['control_noninst_hh']:.0f} non-institutional = {row['control_gq_hh']:.0f} total")
            print(f"  Differences: total={row['diff_total_hh']:.0f}, regular={row['diff_regular_hh']:.0f}, GQ={row['diff_gq_hh']:.0f}")
    
    # Show examples of discrepancies
    discrepancies = comparison[comparison['diff_total_hh'] != 0]
    if len(discrepancies) > 0:
        print(f"\\nMAZs with Total HH discrepancies (first 10):")
        print(discrepancies[['MAZ_NODE', 'control_total_hh', 'syn_total_hh', 'diff_total_hh']].head(10))
    else:
        print("\\nNo MAZs with Total HH discrepancies found!")

def main():
    """Main analysis function"""
    print("MAZ Household Comparison Analysis")
    print("=" * 50)
    
    # Load data
    controls, synthetic = load_data()
    
    # Create comparison table
    comparison = create_comparison_table(controls, synthetic)
    
    # Print summary statistics
    print_summary_stats(comparison)
    
    # Save comparison table BEFORE creating plots
    save_comparison_table(comparison)
    
    # Create scatter plots
    create_scatter_plots(comparison)
    
    print("\\n" + "="*50)
    print("ANALYSIS COMPLETE")
    print("="*50)

if __name__ == "__main__":
    main()