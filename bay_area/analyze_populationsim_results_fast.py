#!/usr/bin/env python3
"""
Fast PopulationSim Results Analysis Script
==========================================

Optimized analysis of PopulationSim TM2 results vs targets with chunked processing:
1. TAZ-level results vs targets analysis
2. MAZ-level household distribution analysis (sampled)
3. County-level population rollups
4. Key performance metrics

Usage:
    python analyze_populationsim_results_fast.py

Output:
    - fast_results_summary.txt
    - key_metrics.csv
    - Simple charts (PNG format)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FastPopulationSimAnalyzer:
    """Fast analyzer for PopulationSim results with chunked processing"""
    
    def __init__(self, working_dir="output_2023/populationsim_working_dir"):
        self.working_dir = Path(working_dir)
        self.output_dir = self.working_dir / "output"
        self.data_dir = self.working_dir / "data"
        self.results = {}
        
    def load_control_data(self):
        """Load control targets (small files)"""
        logger.info("Loading control data...")
        
        self.taz_controls = pd.read_csv(self.data_dir / "taz_marginals_hhgq.csv")
        self.maz_controls = pd.read_csv(self.data_dir / "maz_marginals_hhgq.csv")
        self.county_controls = pd.read_csv(self.data_dir / "county_marginals.csv")
        self.geo_crosswalk = pd.read_csv(self.data_dir / "geo_cross_walk_tm2.csv")
        
        logger.info(f"Loaded controls: {len(self.taz_controls)} TAZs, {len(self.maz_controls)} MAZs")
        
    def load_results_data(self):
        """Load results (small summary files only)"""
        logger.info("Loading results data...")
        
        # Results are in the populationsim_working_dir/output subdirectory
        results_output_dir = self.working_dir / "output"
        self.taz_results = pd.read_csv(results_output_dir / "final_summary_TAZ.csv")
        
        # Load county results
        county_files = list(results_output_dir.glob("final_summary_COUNTY_*.csv"))
        county_dfs = []
        for file in county_files:
            df = pd.read_csv(file)
            county_num = file.stem.split('_')[-1]
            df['COUNTY'] = int(county_num)
            county_dfs.append(df)
        self.county_results = pd.concat(county_dfs, ignore_index=True) if county_dfs else pd.DataFrame()
        
        logger.info(f"Loaded results: {len(self.taz_results)} TAZs, {len(self.county_results)} counties")

    def get_synthetic_household_sample(self, sample_size=50000):
        """Load a sample of synthetic households for faster analysis"""
        logger.info(f"Loading sample of {sample_size:,} synthetic households...")
        
        # Get file size to estimate total rows - look in working_dir/output subdirectory
        hh_file = self.working_dir / "output" / "synthetic_households.csv"
        
        # Read just the header first
        header_df = pd.read_csv(hh_file, nrows=0)
        
        # Read a sample
        total_chunks = []
        chunk_size = 10000
        rows_read = 0
        
        for chunk in pd.read_csv(hh_file, chunksize=chunk_size):
            if rows_read >= sample_size:
                break
            total_chunks.append(chunk)
            rows_read += len(chunk)
            
        sample_df = pd.concat(total_chunks, ignore_index=True)[:sample_size]
        logger.info(f"Loaded sample: {len(sample_df):,} households")
        
        return sample_df

    def analyze_taz_performance(self):
        """Analyze TAZ-level results vs targets with comprehensive metrics"""
        logger.info("Analyzing TAZ-level performance...")
        
        # Merge results with controls (controls has 'TAZ', results has 'id')
        taz_comparison = pd.merge(
            self.taz_controls, 
            self.taz_results, 
            left_on='TAZ',
            right_on='id',
            how='inner',
            suffixes=('_target', '_result')
        )
        
        # Define control variables to analyze
        taz_controls = [
            'hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus',
            'hh_inc_30', 'hh_inc_30_60', 'hh_inc_60_100', 'hh_inc_100_plus',
            'hh_wrks_0', 'hh_wrks_1', 'hh_wrks_2', 'hh_wrks_3_plus',
            'pers_age_00_19', 'pers_age_20_34', 'pers_age_35_64', 'pers_age_65_plus',
            'hh_kids_yes', 'hh_kids_no'
        ]
        
        # Calculate comprehensive performance metrics
        performance_stats = {}
        detailed_stats = []
        
        for control in taz_controls:
            target_col = f"{control}_target"
            result_col = f"{control}_result"
            
            if target_col in taz_comparison.columns and result_col in taz_comparison.columns:
                targets = taz_comparison[target_col]
                results = taz_comparison[result_col]
                
                # Calculate comprehensive metrics
                abs_diff = np.abs(results - targets)
                pct_diff = np.where(targets > 0, abs_diff / targets * 100, 0)
                
                # R-squared calculation
                ss_res = np.sum((results - targets) ** 2)
                ss_tot = np.sum((targets - np.mean(targets)) ** 2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                
                # Correlation coefficient
                correlation = np.corrcoef(targets, results)[0, 1] if len(targets) > 1 else 0
                
                # Root Mean Square Error (RMSE)
                rmse = np.sqrt(np.mean((results - targets) ** 2))
                
                # Mean Absolute Error (MAE)
                mae = np.mean(abs_diff)
                
                # Mean Absolute Percentage Error (MAPE)
                mape = np.mean(pct_diff)
                
                # Total absolute error
                total_target = targets.sum()
                total_result = results.sum()
                total_abs_error = abs(total_result - total_target)
                total_pct_error = (total_abs_error / total_target * 100) if total_target > 0 else 0
                
                stats = {
                    'control': control,
                    'total_target': total_target,
                    'total_result': total_result,
                    'total_abs_error': total_abs_error,
                    'total_pct_error': total_pct_error,
                    'r_squared': r_squared,
                    'correlation': correlation,
                    'rmse': rmse,
                    'mae': mae,
                    'mape': mape,
                    'max_abs_error': abs_diff.max(),
                    'max_pct_error': pct_diff.max(),
                    'zones_with_error': (abs_diff > 0.5).sum(),
                    'zones_with_high_error': (pct_diff > 10).sum(),
                    'mean_target': targets.mean(),
                    'mean_result': results.mean(),
                    'std_target': targets.std(),
                    'std_result': results.std()
                }
                
                performance_stats[control] = stats
                detailed_stats.append(stats)
        
        # Create summary DataFrame and save
        self.taz_performance_df = pd.DataFrame(detailed_stats)
        self.taz_performance_df.to_csv(self.output_dir / "taz_performance_metrics.csv", index=False)
        
        self.results['taz_performance'] = performance_stats
        
        # Create enhanced performance chart
        self.create_taz_performance_chart_enhanced()
        
        return performance_stats

    def create_taz_performance_chart(self, stats):
        """Create a simple performance chart"""
        controls = list(stats.keys())[:8]  # Limit to 8 for readability
        mean_errors = [stats[c]['mean_abs_pct_error'] for c in controls]
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(range(len(controls)), mean_errors, color='skyblue', alpha=0.7)
        plt.xlabel('Control Variables')
        plt.ylabel('Mean Absolute % Error')
        plt.title('TAZ-Level Control Performance (Mean Absolute % Error)')
        plt.xticks(range(len(controls)), controls, rotation=45, ha='right')
        plt.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar, error in zip(bars, mean_errors):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    f'{error:.1f}%', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(self.working_dir / 'taz_performance_chart.png', dpi=150, bbox_inches='tight')
        plt.close()
        logger.info("TAZ performance chart saved")

    def analyze_maz_household_distribution(self):
        """Analyze MAZ-level household distribution using sample"""
        logger.info("Analyzing MAZ household distribution (sampled)...")
        
        # Get household sample
        hh_sample = self.get_synthetic_household_sample(sample_size=50000)
        
        # Count households by MAZ
        synthetic_by_maz = hh_sample.groupby('MAZ').agg({
            'unique_hh_id': 'count',
            'hhgqtype': lambda x: (x == 0).sum()  # Regular households
        }).rename(columns={'unique_hh_id': 'total_hh', 'hhgqtype': 'regular_hh'})
        
        synthetic_by_maz['gq_hh'] = synthetic_by_maz['total_hh'] - synthetic_by_maz['regular_hh']
        synthetic_by_maz.reset_index(inplace=True)
        
        # Merge with controls
        maz_comparison = pd.merge(
            self.maz_controls,
            synthetic_by_maz,
            on='MAZ',
            how='left',
            suffixes=('_target', '_result')
        )
        
        # Fill NaN with 0 (MAZs not in sample)
        maz_comparison.fillna(0, inplace=True)
        
        # Calculate performance for key MAZ controls
        maz_stats = {}
        
        # Total households
        if 'num_hh' in maz_comparison.columns:
            diff = maz_comparison['total_hh'] - maz_comparison['num_hh']
            pct_diff = (diff / (maz_comparison['num_hh'] + 1)) * 100
            
            maz_stats['total_households'] = {
                'mean_abs_pct_error': abs(pct_diff).mean(),
                'max_abs_error': abs(diff).max(),
                'total_target': maz_comparison['num_hh'].sum(),
                'total_result': maz_comparison['total_hh'].sum(),
                'coverage_pct': (maz_comparison['total_hh'] > 0).mean() * 100
            }
        
        self.results['maz_performance'] = maz_stats
        
        # Create distribution comparison chart
        self.create_maz_distribution_chart(maz_comparison)
        
        return maz_stats

    def create_maz_distribution_chart(self, maz_comparison):
        """Create MAZ household distribution chart"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Histogram of household counts
        ax1.hist(maz_comparison['num_hh'], bins=50, alpha=0.7, label='Target', color='blue')
        ax1.hist(maz_comparison['total_hh'], bins=50, alpha=0.7, label='Result', color='red')
        ax1.set_xlabel('Households per MAZ')
        ax1.set_ylabel('Frequency')
        ax1.set_title('MAZ Household Distribution')
        ax1.legend()
        ax1.grid(alpha=0.3)
        
        # Scatter plot
        ax2.scatter(maz_comparison['num_hh'], maz_comparison['total_hh'], 
                   alpha=0.5, s=1)
        max_val = max(maz_comparison['num_hh'].max(), maz_comparison['total_hh'].max())
        ax2.plot([0, max_val], [0, max_val], 'r--', alpha=0.5)
        ax2.set_xlabel('Target Households')
        ax2.set_ylabel('Result Households')
        ax2.set_title('MAZ Results vs Targets')
        ax2.grid(alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.working_dir / 'maz_distribution_chart.png', dpi=150, bbox_inches='tight')
        plt.close()
        logger.info("MAZ distribution chart saved")

    def analyze_county_rollups(self):
        """Analyze county-level population rollups"""
        logger.info("Analyzing county-level rollups...")
        
        if self.county_results.empty:
            logger.warning("No county results found")
            return {}
        
        # Merge with controls
        county_comparison = pd.merge(
            self.county_controls,
            self.county_results,
            on='COUNTY',
            how='inner',
            suffixes=('_target', '_result')
        )
        
        # Add county names
        county_names = {
            1: 'San Francisco', 2: 'San Mateo', 3: 'Santa Clara', 
            4: 'Alameda', 5: 'Contra Costa', 6: 'Solano', 
            7: 'Napa', 8: 'Sonoma', 9: 'Marin'
        }
        county_comparison['county_name'] = county_comparison['COUNTY'].map(county_names)
        
        self.results['county_rollup'] = county_comparison
        
        return county_comparison

    def generate_summary_report(self):
        """Generate a text summary report"""
        logger.info("Generating summary report...")
        
        report_lines = [
            "PopulationSim TM2 Results Analysis Summary",
            "=" * 50,
            f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "TAZ-LEVEL PERFORMANCE SUMMARY",
            "-" * 30
        ]
        
        if 'taz_performance' in self.results:
            stats = self.results['taz_performance']
            
            # Sort by performance (mean absolute % error)
            sorted_controls = sorted(stats.items(), key=lambda x: x[1]['mean_abs_pct_error'])
            
            report_lines.extend([
                f"{'Control':<20} {'Avg % Err':<10} {'Max Err':<10} {'Total % Err':<12}",
                "-" * 60
            ])
            
            for control, data in sorted_controls[:10]:  # Top 10
                report_lines.append(
                    f"{control:<20} {data['mean_abs_pct_error']:>8.1f}% "
                    f"{data['max_abs_error']:>8.0f} {data['total_pct_error']:>10.1f}%"
                )
        
        if 'maz_performance' in self.results:
            maz_stats = self.results['maz_performance']
            report_lines.extend([
                "",
                "MAZ-LEVEL PERFORMANCE SUMMARY",
                "-" * 30
            ])
            
            if 'total_households' in maz_stats:
                hh_stats = maz_stats['total_households']
                report_lines.extend([
                    f"Total Households Target: {hh_stats['total_target']:,}",
                    f"Total Households Result: {hh_stats['total_result']:,}",
                    f"Mean Absolute % Error: {hh_stats['mean_abs_pct_error']:.1f}%",
                    f"MAZ Coverage: {hh_stats['coverage_pct']:.1f}%"
                ])
        
        if 'county_rollup' in self.results:
            county_df = self.results['county_rollup']
            report_lines.extend([
                "",
                "COUNTY-LEVEL ROLLUPS",
                "-" * 20,
                f"{'County':<15} {'Population':<12}",
                "-" * 30
            ])
            
            for _, row in county_df.iterrows():
                pop_col = next((col for col in county_df.columns if 'pop' in col.lower()), None)
                if pop_col:
                    report_lines.append(f"{row['county_name']:<15} {row[pop_col]:>10,.0f}")
        
        # Write report
        report_file = self.working_dir / 'fast_results_summary.txt'
        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"Summary report saved to {report_file}")

    def save_key_metrics(self):
        """Save key metrics to CSV"""
        logger.info("Saving key metrics...")
        
        metrics_data = []
        
        if 'taz_performance' in self.results:
            for control, stats in self.results['taz_performance'].items():
                metrics_data.append({
                    'geography': 'TAZ',
                    'control': control,
                    'mean_abs_pct_error': stats['mean_abs_pct_error'],
                    'max_abs_error': stats['max_abs_error'],
                    'total_pct_error': stats['total_pct_error']
                })
        
        if metrics_data:
            metrics_df = pd.DataFrame(metrics_data)
            metrics_file = self.working_dir / 'key_metrics.csv'
            metrics_df.to_csv(metrics_file, index=False)
            logger.info(f"Key metrics saved to {metrics_file}")

    def create_taz_performance_chart_enhanced(self):
        """Create enhanced performance chart with R-squared and detailed metrics"""
        if not hasattr(self, 'taz_performance_df') or self.taz_performance_df.empty:
            return
            
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Sort by R-squared for better visualization
        df_sorted = self.taz_performance_df.sort_values('r_squared', ascending=True)
        
        # 1. R-squared by control
        bars1 = ax1.barh(df_sorted['control'], df_sorted['r_squared'], color='skyblue')
        ax1.set_xlabel('R-squared')
        ax1.set_title('Model Fit (R-squared) by Control Variable')
        ax1.set_xlim(0, 1)
        for i, v in enumerate(df_sorted['r_squared']):
            ax1.text(v + 0.01, i, f'{v:.3f}', va='center', fontsize=9)
        
        # 2. Total Percent Error
        bars2 = ax2.barh(df_sorted['control'], df_sorted['total_pct_error'], color='lightcoral')
        ax2.set_xlabel('Total Percent Error (%)')
        ax2.set_title('Total Percent Error by Control Variable')
        for i, v in enumerate(df_sorted['total_pct_error']):
            ax2.text(v + 0.1, i, f'{v:.1f}%', va='center', fontsize=9)
        
        # 3. MAPE (Mean Absolute Percentage Error)
        bars3 = ax3.barh(df_sorted['control'], df_sorted['mape'], color='lightgreen')
        ax3.set_xlabel('Mean Absolute Percentage Error (%)')
        ax3.set_title('MAPE by Control Variable')
        for i, v in enumerate(df_sorted['mape']):
            ax3.text(v + 0.1, i, f'{v:.1f}%', va='center', fontsize=9)
        
        # 4. Correlation
        bars4 = ax4.barh(df_sorted['control'], df_sorted['correlation'], color='gold')
        ax4.set_xlabel('Correlation Coefficient')
        ax4.set_title('Correlation (Target vs Result)')
        ax4.set_xlim(0, 1)
        for i, v in enumerate(df_sorted['correlation']):
            ax4.text(v + 0.01, i, f'{v:.3f}', va='center', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(self.working_dir / "taz_performance_enhanced.png", dpi=300, bbox_inches='tight')
        plt.close()

    def analyze_maz_performance_detailed(self):
        """Detailed MAZ analysis with comprehensive metrics"""
        logger.info("Analyzing MAZ-level performance (detailed)...")
        
        # Load synthetic households sample for MAZ analysis
        sample_households = self.get_synthetic_household_sample(100000)  # Larger sample for MAZ analysis
        
        if sample_households.empty or 'MAZ' not in sample_households.columns:
            logger.warning("No MAZ data found in synthetic households")
            return {}
        
        # Group by MAZ and count households
        maz_results = sample_households.groupby('MAZ').size().reset_index(name='hh_count_sample')
        
        # Scale up to full population
        total_sample = len(sample_households)
        total_target = self.maz_controls['num_hh'].sum()
        scale_factor = total_target / total_sample if total_sample > 0 else 1
        maz_results['hh_count_scaled'] = maz_results['hh_count_sample'] * scale_factor
        
        # Merge with controls
        maz_comparison = pd.merge(
            self.maz_controls, 
            maz_results, 
            on='MAZ', 
            how='left'
        ).fillna(0)
        
        # Calculate comprehensive MAZ metrics
        targets = maz_comparison['num_hh']
        results = maz_comparison['hh_count_scaled']
        
        # Overall metrics
        abs_diff = np.abs(results - targets)
        pct_diff = np.where(targets > 0, abs_diff / targets * 100, 0)
        
        # R-squared
        ss_res = np.sum((results - targets) ** 2)
        ss_tot = np.sum((targets - np.mean(targets)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Correlation
        correlation = np.corrcoef(targets, results)[0, 1] if len(targets) > 1 else 0
        
        # Create detailed MAZ performance summary
        maz_performance = {
            'total_mazs': len(self.maz_controls),
            'mazs_with_households': (targets > 0).sum(),
            'mazs_with_results': (results > 0).sum(),
            'total_target_hh': targets.sum(),
            'total_result_hh': results.sum(),
            'total_abs_error': abs_diff.sum(),
            'total_pct_error': abs(results.sum() - targets.sum()) / targets.sum() * 100 if targets.sum() > 0 else 0,
            'r_squared': r_squared,
            'correlation': correlation,
            'rmse': np.sqrt(np.mean((results - targets) ** 2)),
            'mae': np.mean(abs_diff),
            'mape': np.mean(pct_diff),
            'max_abs_error': abs_diff.max(),
            'max_pct_error': pct_diff.max(),
            'mazs_with_error_gt_10pct': (pct_diff > 10).sum(),
            'mazs_with_error_gt_50pct': (pct_diff > 50).sum(),
            'mazs_perfect_match': (abs_diff < 0.1).sum()
        }
        
        # Create error distribution summary
        error_bins = [0, 1, 5, 10, 25, 50, 100, np.inf]
        error_labels = ['0-1%', '1-5%', '5-10%', '10-25%', '25-50%', '50-100%', '100%+']
        maz_comparison['error_bin'] = pd.cut(pct_diff, bins=error_bins, labels=error_labels, include_lowest=True)
        error_distribution = maz_comparison['error_bin'].value_counts().to_dict()
        maz_performance['error_distribution'] = error_distribution
        
        # Save detailed MAZ results
        maz_comparison['abs_error'] = abs_diff
        maz_comparison['pct_error'] = pct_diff
        maz_comparison.to_csv(self.working_dir / "maz_performance_detailed.csv", index=False)
        
        # Create MAZ performance summary
        maz_summary_stats = {
            'metric': ['Total MAZs', 'MAZs with HH Target > 0', 'MAZs with Results > 0',
                      'Total Target HH', 'Total Result HH', 'R-squared', 'Correlation',
                      'RMSE', 'MAE', 'MAPE (%)', 'Total Percent Error (%)',
                      'MAZs with Error > 10%', 'MAZs with Error > 50%', 'Perfect Matches'],
            'value': [maz_performance['total_mazs'], maz_performance['mazs_with_households'],
                     maz_performance['mazs_with_results'], maz_performance['total_target_hh'],
                     maz_performance['total_result_hh'], maz_performance['r_squared'],
                     maz_performance['correlation'], maz_performance['rmse'],
                     maz_performance['mae'], maz_performance['mape'], maz_performance['total_pct_error'],
                     maz_performance['mazs_with_error_gt_10pct'], maz_performance['mazs_with_error_gt_50pct'],
                     maz_performance['mazs_perfect_match']]
        }
        
        maz_summary_df = pd.DataFrame(maz_summary_stats)
        maz_summary_df.to_csv(self.working_dir / "maz_performance_summary.csv", index=False)
        
        self.results['maz_performance_detailed'] = maz_performance
        
        # Create enhanced MAZ visualization
        self.create_maz_performance_chart_enhanced(maz_comparison)
        
        logger.info("Detailed MAZ analysis completed")
        return maz_performance

    def create_maz_performance_chart_enhanced(self, maz_comparison):
        """Create enhanced MAZ performance visualization"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Scatter plot of targets vs results
        ax1.scatter(maz_comparison['num_hh'], maz_comparison['hh_count_scaled'], 
                   alpha=0.6, s=20, c='blue')
        max_val = max(maz_comparison['num_hh'].max(), maz_comparison['hh_count_scaled'].max())
        ax1.plot([0, max_val], [0, max_val], 'r--', lw=2, label='Perfect Match')
        ax1.set_xlabel('Target Households')
        ax1.set_ylabel('Result Households')
        ax1.set_title('MAZ Household Targets vs Results')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Error distribution histogram
        pct_errors = maz_comparison['pct_error']
        ax2.hist(pct_errors[pct_errors <= 100], bins=50, alpha=0.7, color='lightcoral')
        ax2.set_xlabel('Percent Error (%)')
        ax2.set_ylabel('Number of MAZs')
        ax2.set_title('Distribution of MAZ Percent Errors (≤100%)')
        ax2.grid(True, alpha=0.3)
        
        # 3. Error by household size
        maz_comparison['hh_size_category'] = pd.cut(maz_comparison['num_hh'], 
                                                   bins=[0, 10, 50, 100, 500, float('inf')],
                                                   labels=['0-10', '11-50', '51-100', '101-500', '500+'])
        error_by_size = maz_comparison.groupby('hh_size_category')['pct_error'].mean()
        ax3.bar(range(len(error_by_size)), error_by_size.values, color='lightgreen')
        ax3.set_xlabel('Household Size Category')
        ax3.set_ylabel('Mean Percent Error (%)')
        ax3.set_title('Mean Percent Error by Household Size')
        ax3.set_xticks(range(len(error_by_size)))
        ax3.set_xticklabels(error_by_size.index, rotation=45)
        
        # 4. Cumulative error distribution
        sorted_errors = np.sort(pct_errors)
        cumulative_pct = np.arange(1, len(sorted_errors) + 1) / len(sorted_errors) * 100
        ax4.plot(sorted_errors, cumulative_pct, linewidth=2, color='gold')
        ax4.set_xlabel('Percent Error (%)')
        ax4.set_ylabel('Cumulative Percentage of MAZs')
        ax4.set_title('Cumulative Distribution of Errors')
        ax4.grid(True, alpha=0.3)
        ax4.set_xlim(0, min(200, sorted_errors.max()))
        
        plt.tight_layout()
        plt.savefig(self.working_dir / "maz_performance_enhanced.png", dpi=300, bbox_inches='tight')
        plt.close()

    def run_analysis(self):
        """Run the complete fast analysis"""
        logger.info("Starting fast PopulationSim analysis...")
        
        try:
            # Load data
            self.load_control_data()
            self.load_results_data()
            
            # Run analyses
            self.analyze_taz_performance()
            self.analyze_maz_performance_detailed()  # Use detailed MAZ analysis instead
            self.analyze_county_rollups()
            
            # Generate outputs
            self.generate_summary_report()
            self.save_key_metrics()
            
            logger.info("Analysis completed successfully!")
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise

if __name__ == "__main__":
    analyzer = FastPopulationSimAnalyzer()
    analyzer.run_analysis()
