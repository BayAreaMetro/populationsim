#!/usr/bin/env python3
"""
MAZ Control vs Output Summary Analysis
Creates detailed comparison between MAZ controls and PopulationSim outputs
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_and_analyze_maz_data():
    """Load MAZ controls and synthetic population, create detailed comparison"""
    
    # Paths
    base_dir = Path("output_2023/populationsim_working_dir")
    data_dir = base_dir / "data"
    output_dir = base_dir / "output"
    
    logger.info("Loading MAZ controls...")
    maz_controls = pd.read_csv(data_dir / "maz_marginals_hhgq.csv")
    
    logger.info("Loading synthetic households...")
    synthetic_hh = pd.read_csv(output_dir / "synthetic_households.csv")
    
    logger.info(f"MAZ Controls: {len(maz_controls):,} records")
    logger.info(f"Synthetic HH: {len(synthetic_hh):,} records")
    
    # Count households by MAZ in synthetic population
    logger.info("Counting households by MAZ in synthetic population...")
    maz_results = synthetic_hh.groupby('MAZ').size().reset_index(name='hh_count_result')
    
    # Merge controls with results
    logger.info("Merging controls with results...")
    maz_comparison = pd.merge(
        maz_controls[['MAZ', 'num_hh', 'total_pop', 'gq_pop', 'gq_military', 'gq_university', 'gq_other']], 
        maz_results, 
        on='MAZ', 
        how='left'
    ).fillna(0)
    
    # Calculate differences and errors
    maz_comparison['hh_diff'] = maz_comparison['hh_count_result'] - maz_comparison['num_hh']
    maz_comparison['hh_abs_diff'] = np.abs(maz_comparison['hh_diff'])
    maz_comparison['hh_pct_error'] = np.where(
        maz_comparison['num_hh'] > 0,
        maz_comparison['hh_abs_diff'] / maz_comparison['num_hh'] * 100,
        0
    )
    
    # Create error categories
    maz_comparison['error_category'] = pd.cut(
        maz_comparison['hh_pct_error'],
        bins=[0, 1, 5, 10, 25, 50, 100, np.inf],
        labels=['Perfect (0-1%)', 'Excellent (1-5%)', 'Good (5-10%)', 
               'Fair (10-25%)', 'Poor (25-50%)', 'Very Poor (50-100%)', 'Terrible (100%+)'],
        include_lowest=True
    )
    
    # Household size categories
    maz_comparison['hh_size_category'] = pd.cut(
        maz_comparison['num_hh'],
        bins=[0, 1, 10, 50, 100, 500, np.inf],
        labels=['Zero', '1-10', '11-50', '51-100', '101-500', '500+'],
        include_lowest=True
    )
    
    return maz_comparison

def create_detailed_summary(maz_comparison):
    """Create detailed summary statistics"""
    
    logger.info("Creating detailed summary...")
    
    summary_stats = {
        'Total MAZs': len(maz_comparison),
        'MAZs with HH Target > 0': (maz_comparison['num_hh'] > 0).sum(),
        'MAZs with HH Results > 0': (maz_comparison['hh_count_result'] > 0).sum(),
        'MAZs with both Target and Results > 0': ((maz_comparison['num_hh'] > 0) & (maz_comparison['hh_count_result'] > 0)).sum(),
        'MAZs with Target but no Results': ((maz_comparison['num_hh'] > 0) & (maz_comparison['hh_count_result'] == 0)).sum(),
        'MAZs with Results but no Target': ((maz_comparison['num_hh'] == 0) & (maz_comparison['hh_count_result'] > 0)).sum(),
        'Total Target Households': maz_comparison['num_hh'].sum(),
        'Total Result Households': maz_comparison['hh_count_result'].sum(),
        'Total Absolute Error': maz_comparison['hh_abs_diff'].sum(),
        'Mean Absolute Error': maz_comparison['hh_abs_diff'].mean(),
        'Mean Percent Error (MAZs with targets)': maz_comparison[maz_comparison['num_hh'] > 0]['hh_pct_error'].mean(),
        'Max Absolute Error': maz_comparison['hh_abs_diff'].max(),
        'Max Percent Error': maz_comparison['hh_pct_error'].max(),
    }
    
    # Error distribution
    error_dist = maz_comparison['error_category'].value_counts().sort_index()
    
    # Size category performance
    size_performance = maz_comparison.groupby('hh_size_category').agg({
        'num_hh': ['count', 'sum'],
        'hh_count_result': 'sum',
        'hh_pct_error': 'mean',
        'hh_abs_diff': 'mean'
    }).round(2)
    
    return summary_stats, error_dist, size_performance

def create_maz_summary_report(maz_comparison, summary_stats, error_dist, size_performance):
    """Create comprehensive MAZ summary report"""
    
    logger.info("Creating MAZ summary report...")
    
    report_lines = [
        "MAZ CONTROL VS OUTPUT ANALYSIS SUMMARY",
        "=" * 50,
        f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "OVERALL STATISTICS",
        "-" * 30
    ]
    
    for key, value in summary_stats.items():
        if isinstance(value, float):
            report_lines.append(f"{key}: {value:,.2f}")
        else:
            report_lines.append(f"{key}: {value:,}")
    
    report_lines.extend([
        "",
        "ERROR DISTRIBUTION",
        "-" * 30
    ])
    
    for category, count in error_dist.items():
        pct = count / len(maz_comparison) * 100
        report_lines.append(f"{category}: {count:,} MAZs ({pct:.1f}%)")
    
    report_lines.extend([
        "",
        "PERFORMANCE BY HOUSEHOLD SIZE CATEGORY",
        "-" * 50
    ])
    
    report_lines.append(f"{'Category':<15} {'Count':<8} {'Target HH':<12} {'Result HH':<12} {'Avg % Err':<10} {'Avg Abs Err':<12}")
    report_lines.append("-" * 80)
    
    for category in size_performance.index:
        count = size_performance.loc[category, ('num_hh', 'count')]
        target = size_performance.loc[category, ('num_hh', 'sum')]
        result = size_performance.loc[category, ('hh_count_result', 'sum')]
        pct_err = size_performance.loc[category, ('hh_pct_error', 'mean')]
        abs_err = size_performance.loc[category, ('hh_abs_diff', 'mean')]
        
        report_lines.append(f"{str(category):<15} {count:<8.0f} {target:<12.0f} {result:<12.0f} {pct_err:<10.1f} {abs_err:<12.1f}")
    
    # Sample of worst performers
    worst_performers = maz_comparison.nlargest(20, 'hh_abs_diff')[['MAZ', 'num_hh', 'hh_count_result', 'hh_diff', 'hh_pct_error']]
    
    report_lines.extend([
        "",
        "TOP 20 WORST PERFORMING MAZs (by absolute error)",
        "-" * 60,
        f"{'MAZ':<8} {'Target':<8} {'Result':<8} {'Diff':<8} {'% Error':<10}"
    ])
    
    for _, row in worst_performers.iterrows():
        report_lines.append(f"{row['MAZ']:<8.0f} {row['num_hh']:<8.0f} {row['hh_count_result']:<8.0f} {row['hh_diff']:<8.0f} {row['hh_pct_error']:<10.1f}")
    
    # Zero result MAZs with targets
    zero_results = maz_comparison[(maz_comparison['num_hh'] > 0) & (maz_comparison['hh_count_result'] == 0)]
    
    report_lines.extend([
        "",
        f"MAZs WITH TARGETS BUT ZERO RESULTS: {len(zero_results):,}",
        "-" * 50
    ])
    
    if len(zero_results) > 0:
        # Show distribution by target size
        zero_by_size = zero_results['hh_size_category'].value_counts().sort_index()
        for category, count in zero_by_size.items():
            total_target = zero_results[zero_results['hh_size_category'] == category]['num_hh'].sum()
            report_lines.append(f"{category}: {count:,} MAZs, {total_target:,.0f} target households")
    
    return report_lines

def create_visualizations(maz_comparison):
    """Create visualization charts"""
    
    logger.info("Creating visualizations...")
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    
    # 1. Scatter plot: Target vs Result (log scale for better visibility)
    mask = (maz_comparison['num_hh'] > 0) | (maz_comparison['hh_count_result'] > 0)
    data_for_plot = maz_comparison[mask]
    
    ax1.scatter(data_for_plot['num_hh'] + 1, data_for_plot['hh_count_result'] + 1, 
               alpha=0.6, s=15, c='blue')
    max_val = max(data_for_plot['num_hh'].max(), data_for_plot['hh_count_result'].max()) + 1
    ax1.plot([1, max_val], [1, max_val], 'r--', lw=2, label='Perfect Match')
    ax1.set_xlabel('Target Households + 1')
    ax1.set_ylabel('Result Households + 1')
    ax1.set_title('MAZ Household Targets vs Results (Log Scale)')
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Error distribution
    error_dist = maz_comparison['error_category'].value_counts()
    ax2.bar(range(len(error_dist)), error_dist.values, color='lightcoral')
    ax2.set_xlabel('Error Category')
    ax2.set_ylabel('Number of MAZs')
    ax2.set_title('Distribution of MAZ Performance')
    ax2.set_xticks(range(len(error_dist)))
    ax2.set_xticklabels(error_dist.index, rotation=45, ha='right')
    
    # Add counts on bars
    for i, v in enumerate(error_dist.values):
        ax2.text(i, v + 100, str(v), ha='center', va='bottom')
    
    # 3. Performance by household size
    size_perf = maz_comparison.groupby('hh_size_category')['hh_pct_error'].mean()
    ax3.bar(range(len(size_perf)), size_perf.values, color='lightgreen')
    ax3.set_xlabel('Household Size Category')
    ax3.set_ylabel('Mean Percent Error (%)')
    ax3.set_title('Performance by Household Size Category')
    ax3.set_xticks(range(len(size_perf)))
    ax3.set_xticklabels(size_perf.index, rotation=45, ha='right')
    
    # 4. Cumulative error distribution
    pct_errors = maz_comparison[maz_comparison['num_hh'] > 0]['hh_pct_error']
    sorted_errors = np.sort(pct_errors)
    cumulative_pct = np.arange(1, len(sorted_errors) + 1) / len(sorted_errors) * 100
    ax4.plot(sorted_errors, cumulative_pct, linewidth=2, color='purple')
    ax4.set_xlabel('Percent Error (%)')
    ax4.set_ylabel('Cumulative % of MAZs')
    ax4.set_title('Cumulative Distribution of Errors (MAZs with targets)')
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(0, min(500, sorted_errors.max()))
    
    plt.tight_layout()
    plt.savefig('output_2023/populationsim_working_dir/maz_control_vs_output_analysis.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info("Visualizations saved")

def main():
    """Main analysis function"""
    
    logger.info("Starting MAZ Control vs Output Analysis...")
    
    try:
        # Load and analyze data
        maz_comparison = load_and_analyze_maz_data()
        
        # Create summary statistics
        summary_stats, error_dist, size_performance = create_detailed_summary(maz_comparison)
        
        # Save detailed MAZ comparison
        output_file = "output_2023/populationsim_working_dir/maz_control_vs_output_detailed.csv"
        maz_comparison.to_csv(output_file, index=False)
        logger.info(f"Detailed MAZ comparison saved to {output_file}")
        
        # Create and save report
        report_lines = create_maz_summary_report(maz_comparison, summary_stats, error_dist, size_performance)
        report_file = "output_2023/populationsim_working_dir/maz_control_vs_output_report.txt"
        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))
        logger.info(f"Summary report saved to {report_file}")
        
        # Create visualizations
        create_visualizations(maz_comparison)
        
        # Print key findings
        print("\n" + "="*60)
        print("KEY FINDINGS")
        print("="*60)
        print(f"Total MAZs: {summary_stats['Total MAZs']:,}")
        print(f"MAZs with household targets: {summary_stats['MAZs with HH Target > 0']:,}")
        print(f"MAZs with household results: {summary_stats['MAZs with HH Results > 0']:,}")
        print(f"MAZs missing results (have targets but zero results): {summary_stats['MAZs with Target but no Results']:,}")
        print(f"Total household error: {summary_stats['Total Absolute Error']:,.0f}")
        print(f"Mean percent error: {summary_stats['Mean Percent Error (MAZs with targets)']:.1f}%")
        
        logger.info("Analysis completed successfully!")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
