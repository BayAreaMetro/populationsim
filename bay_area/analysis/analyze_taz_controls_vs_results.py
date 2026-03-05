"""
TAZ Controls vs Results Distribution Analysis
============================================

Analyze the distribution of controls vs results for each variable at the TAZ level.
Creates comprehensive charts showing:
1. Scatter plots (control vs result)
2. Error distribution histograms  
3. Percentage error distributions
4. Summary statistics for each variable

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')
import re

# Repo root and output root (make paths robust regardless of current working dir)
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ROOT = REPO_ROOT / "output_2023"

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def analyze_taz_controls_vs_results():
    """Main analysis function"""
    
    print("="*80)
    print("TAZ CONTROLS VS RESULTS DISTRIBUTION ANALYSIS")
    print("="*80)
    
    # Load TAZ data
    taz_file = OUTPUT_ROOT / "populationsim_working_dir" / "output" / "final_summary_TAZ_NODE.csv"
    if not taz_file.exists():
        print(f"Error: Could not find {taz_file}")
        return
    
    df = pd.read_csv(taz_file)
    print("[INFO] Loaded TAZ data: {:,} TAZ zones".format(len(df)))
    
    # Create output directory (repo-root based)
    output_dir = OUTPUT_ROOT / "charts" / "taz_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Identify control variables (exclude geography and id columns)
    control_vars = [col for col in df.columns if col.endswith('_control')]
    control_vars = [var.replace('_control', '') for var in control_vars]
    
    print("[INFO] Found {:} control variables to analyze".format(len(control_vars)))
    print("Variables:", control_vars[:10], "..." if len(control_vars) > 10 else "")

    # --- HHGQ diagnostics (per-TAZ) -------------------------------------------------
    # Create a small diagnostics CSV to help identify where household-size buckets and
    # numhh_gq disagree (possible double-counting of GQ). This emits:
    # id, hh_size_sum_control, numhh_gq_control, hh_gq_total_control, diff, pct_diff, flag
    hh_size_cols = [c for c in df.columns if c.startswith('hh_size_') and c.endswith('_control')]
    hh_gq_cols = [c for c in df.columns if c.startswith('hh_gq_') and c.endswith('_control')]

    if 'id' in df.columns and len(hh_size_cols) > 0 and 'numhh_gq_control' in df.columns:
        diag = pd.DataFrame()
        diag['id'] = df['id']
        diag['hh_size_sum_control'] = df[hh_size_cols].sum(axis=1)
        diag['numhh_gq_control'] = df['numhh_gq_control']
        diag['hh_gq_total_control'] = df[hh_gq_cols].sum(axis=1) if len(hh_gq_cols) > 0 else 0
        diag['diff'] = diag['hh_size_sum_control'] - diag['numhh_gq_control']
        # pct diff relative to numhh_gq (guard against zero)
        diag['pct_diff'] = diag['diff'] / diag['numhh_gq_control'].replace({0: pd.NA}) * 100
        diag['flag'] = diag['diff'].abs() >= 1  # flag TA Zs with non-zero diff

        diag_output = output_dir / 'taz_hhgq_diagnostics.csv'
        diag.to_csv(diag_output, index=False)
        print(f"[DIAG] Wrote HH/GQ diagnostics to {diag_output} (rows: {len(diag)})")

        # Print quick aggregate summary
        tot_size = diag['hh_size_sum_control'].sum()
        tot_numhh = diag['numhh_gq_control'].sum()
        tot_gq = diag['hh_gq_total_control'].sum()
        n_flags = diag['flag'].sum()
        print(f"[DIAG] hh_size_sum total: {tot_size:,.0f}, numhh_gq total: {tot_numhh:,.0f}, hh_gq_total: {tot_gq:,.0f}")
        print(f"[DIAG] Zones with non-zero diff: {n_flags} (top 10 diffs shown below)")
        print(diag.sort_values('diff', ascending=False).head(10).to_string(index=False))
    else:
        print("[DIAG] Skipping HH/GQ diagnostics: required columns missing")
    # -------------------------------------------------------------------------------
    
    # Analyze each variable
    results_summary = []
    
    for i, var in enumerate(control_vars):
        print(f"\n[INFO] Analyzing variable {i+1}/{len(control_vars)}: {var}")
        
        control_col = f"{var}_control"
        result_col = f"{var}_result"
        
        # Skip if columns don't exist
        if control_col not in df.columns or result_col not in df.columns:
            print(f"   [WARNING] Skipping {var} - missing columns")
            continue
        
        # Get data
        controls = df[control_col].values
        results = df[result_col].values
        
        # No special handling for hh_size_1 here: keep hh_size_1 values as-is (do not add GQ)
        
        # Calculate metrics
        total_control = controls.sum()
        total_result = results.sum()
        
        if total_control == 0:
            print(f"   [WARNING] Skipping {var} - zero total control")
            continue
        
        # Calculate errors
        errors = results - controls
        abs_errors = np.abs(errors)
        pct_errors = (errors / np.maximum(controls, 1)) * 100  # Avoid division by zero
        
        # Statistics
        mae = np.mean(abs_errors)
        rmse = np.sqrt(np.mean(errors**2))
        mape = np.mean(np.abs(pct_errors))
        r_squared = np.corrcoef(controls, results)[0, 1]**2 if len(controls) > 1 else 0
        
        # Count perfect matches
        perfect_matches = np.sum(errors == 0)
        perfect_pct = (perfect_matches / len(errors)) * 100
        
        print(f"   [INFO] Total Control: {total_control:,.0f}, Total Result: {total_result:,.0f}")
        print(f"   [INFO] R-squared: {r_squared:.4f}, MAE: {mae:.2f}, RMSE: {rmse:.2f}")
        print(f"   [RESULT] Perfect matches: {perfect_matches:,} ({perfect_pct:.1f}%)")
        
        # Store results
        results_summary.append({
            'variable': var,
            'total_control': total_control,
            'total_result': total_result,
            'total_diff': total_result - total_control,
            'total_diff_pct': ((total_result - total_control) / total_control) * 100,
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'r_squared': r_squared,
            'perfect_matches': perfect_matches,
            'perfect_pct': perfect_pct,
            'taz_count': len(controls)
        })
        
        # Create individual variable chart
        create_variable_chart(var, controls, results, errors, pct_errors, 
                            output_dir, r_squared, mae, perfect_pct)
    
    # Create summary analysis
    create_summary_analysis(results_summary, output_dir)
    
    print(f"\n[SUCCESS] Analysis complete! Charts saved to: {output_dir}")
    print(f"[INFO] Generated {len(results_summary)} variable analyses")

def create_variable_chart(var_name, controls, results, errors, pct_errors, 
                         output_dir, r_squared, mae, perfect_pct):
    """Create comprehensive chart for a single variable"""
    
    # Set up the figure
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle(f'TAZ Analysis: {var_name.replace("_", " ").title()}', 
                 fontsize=16, fontweight='bold')
    # 1. Scatter plot: Control vs Result
    ax1 = axes[0, 0]
    max_val = max(controls.max(), results.max())
    min_val = min(controls.min(), results.min())
    
    # Plot points
    ax1.scatter(controls, results, alpha=0.6, s=20, color='steelblue', edgecolors='white', linewidth=0.5)
    
    # Perfect fit line (y=x)
    ax1.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, alpha=0.8, label='Perfect Fit (y=x)')
    
    # Best fit line with equation
    if len(controls) > 1:
        z = np.polyfit(controls, results, 1)
        p = np.poly1d(z)
        m, b = z  # slope and intercept
        ax1.plot(controls, p(controls), 'orange', linewidth=2, alpha=0.8, 
                label=f'Best Fit (R²={r_squared:.3f})')
        
        # Add equation text
        eqn = f'y = {m:.3f}x + {b:.1f}'
        ax1.text(0.5, 0.5, eqn, transform=ax1.transAxes, 
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8, pad=0.5, edgecolor='black'),
                fontsize=11, ha='center', va='center', fontweight='bold')
    
    ax1.set_xlabel('Control Values')
    ax1.set_ylabel('Result Values')
    ax1.set_title(f'Control vs Result\nR² = {r_squared:.4f}')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Error distribution histogram
    ax2 = axes[0, 1]
    
    # Calculate reasonable bins for errors
    error_range = errors.max() - errors.min()
    if error_range > 0:
        n_bins = min(50, max(10, int(np.sqrt(len(errors)))))
        ax2.hist(errors, bins=n_bins, alpha=0.7, color='lightcoral', edgecolor='black', linewidth=0.5)
        ax2.axvline(0, color='red', linestyle='--', linewidth=2, alpha=0.8)
        ax2.set_xlabel('Error (Result - Control)')
        ax2.set_ylabel('Number of TAZs')
        ax2.set_title(f'Error Distribution\nMAE = {mae:.2f}')
        ax2.grid(True, alpha=0.3)
    else:
        ax2.text(0.5, 0.5, 'All Perfect Matches', ha='center', va='center', transform=ax2.transAxes, fontsize=14)
        ax2.set_title('Error Distribution\n(All Perfect)')
    
    # 3. Percentage error distribution
    ax3 = axes[0, 2]
    
    # Filter out extreme percentage errors for better visualization
    pct_errors_filtered = pct_errors[(pct_errors >= -100) & (pct_errors <= 100)]
    
    if len(pct_errors_filtered) > 0:
        n_bins = min(50, max(10, int(np.sqrt(len(pct_errors_filtered)))))
        ax3.hist(pct_errors_filtered, bins=n_bins, alpha=0.7, color='lightgreen', edgecolor='black', linewidth=0.5)
        ax3.axvline(0, color='green', linestyle='--', linewidth=2, alpha=0.8)
        ax3.set_xlabel('Percentage Error (%)')
        ax3.set_ylabel('Number of TAZs')
        ax3.set_title(f'% Error Distribution\nMAPE = {np.mean(np.abs(pct_errors_filtered)):.1f}%')
        ax3.grid(True, alpha=0.3)
    else:
        ax3.text(0.5, 0.5, 'No Valid % Errors', ha='center', va='center', transform=ax3.transAxes, fontsize=14)
        ax3.set_title('% Error Distribution\n(No Data)')
    
    # 4. Box plot comparison
    ax4 = axes[1, 0]
    box_data = [controls, results]
    bp = ax4.boxplot(box_data, labels=['Control', 'Result'], patch_artist=True)
    bp['boxes'][0].set_facecolor('lightblue')
    bp['boxes'][1].set_facecolor('lightcoral')
    ax4.set_title('Distribution Comparison')
    ax4.set_ylabel('Values')
    ax4.grid(True, alpha=0.3)
    
    # 5. Perfect match analysis
    ax5 = axes[1, 1]
    
    # Create bins for control values
    if controls.max() > controls.min():
        control_bins = np.percentile(controls, [0, 25, 50, 75, 100])
        control_bins = np.unique(control_bins)  # Remove duplicates
        
        if len(control_bins) > 1:
            bin_labels = []
            perfect_rates = []
            
            for i in range(len(control_bins) - 1):
                mask = (controls >= control_bins[i]) & (controls < control_bins[i+1])
                if i == len(control_bins) - 2:  # Last bin includes upper bound
                    mask = (controls >= control_bins[i]) & (controls <= control_bins[i+1])
                
                if mask.sum() > 0:
                    perfect_rate = (errors[mask] == 0).sum() / mask.sum() * 100
                    perfect_rates.append(perfect_rate)
                    bin_labels.append(f'{control_bins[i]:.0f}-{control_bins[i+1]:.0f}')
            
            if perfect_rates:
                bars = ax5.bar(range(len(perfect_rates)), perfect_rates, alpha=0.7, color='gold')
                ax5.set_xlabel('Control Value Bins')
                ax5.set_ylabel('Perfect Match Rate (%)')
                ax5.set_title(f'Perfect Matches by Control Size\nOverall: {perfect_pct:.1f}%')
                ax5.set_xticks(range(len(bin_labels)))
                ax5.set_xticklabels(bin_labels, rotation=45)
                ax5.grid(True, alpha=0.3)
                
                # Add value labels on bars
                for bar, rate in zip(bars, perfect_rates):
                    ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                            f'{rate:.1f}%', ha='center', va='bottom', fontsize=10)
            else:
                ax5.text(0.5, 0.5, 'No Binning Possible', ha='center', va='center', transform=ax5.transAxes)
        else:
            ax5.text(0.5, 0.5, 'All Same Control Value', ha='center', va='center', transform=ax5.transAxes)
    else:
        ax5.text(0.5, 0.5, f'Perfect Match Rate\n{perfect_pct:.1f}%', 
                ha='center', va='center', transform=ax5.transAxes, fontsize=14)
        ax5.set_title('Perfect Match Analysis')
    
    # 6. Summary statistics
    ax6 = axes[1, 2]
    ax6.axis('off')
    
    # Create summary text
    summary_text = f"""
Summary Statistics

Total Control: {controls.sum():,.0f}
Total Result: {results.sum():,.0f}
Total Difference: {(results.sum() - controls.sum()):,.0f}

Accuracy Metrics:
• R-squared: {r_squared:.4f}
• MAE: {mae:.2f}
• RMSE: {np.sqrt(np.mean((results - controls)**2)):.2f}
• MAPE: {np.mean(np.abs(pct_errors)):.1f}%

TAZ Distribution:
• Total TAZs: {len(controls):,}
• Perfect matches: {(errors == 0).sum():,} ({perfect_pct:.1f}%)
• Within ±1: {(np.abs(errors) <= 1).sum():,} ({(np.abs(errors) <= 1).sum()/len(errors)*100:.1f}%)
• Within ±5: {(np.abs(errors) <= 5).sum():,} ({(np.abs(errors) <= 5).sum()/len(errors)*100:.1f}%)
"""
    
    ax6.text(0.1, 0.9, summary_text, transform=ax6.transAxes, fontsize=11,
             verticalalignment='top', fontfamily='monospace')
    
    plt.tight_layout()
    
    # Save the chart
    # Create a filesystem-safe name: remove/control non-printable or unsafe characters
    safe_name = var_name
    # replace spaces and slashes
    safe_name = safe_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    # remove any characters that are not alphanumeric, underscore, dot or hyphen
    safe_name = re.sub(r'[^A-Za-z0-9_.-]', '_', safe_name)
    # limit length to avoid Windows path issues
    if len(safe_name) > 120:
        safe_name = safe_name[:120]
    output_file = output_dir / f"taz_{safe_name}_analysis.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def create_summary_analysis(results_summary, output_dir):
    """Create overall summary analysis across all variables"""
    
    if not results_summary:
        print("No results to summarize")
        return
    
    df_summary = pd.DataFrame(results_summary)
    
    # Create summary figure
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle('TAZ Controls vs Results: Overall Summary Analysis', fontsize=16, fontweight='bold')
    
    # 1. R-squared distribution
    ax1 = axes[0, 0]
    ax1.hist(df_summary['r_squared'], bins=20, alpha=0.7, color='steelblue', edgecolor='black')
    ax1.axvline(df_summary['r_squared'].mean(), color='red', linestyle='--', linewidth=2, 
                label=f'Mean = {df_summary["r_squared"].mean():.3f}')
    ax1.set_xlabel('R-squared')
    ax1.set_ylabel('Number of Variables')
    ax1.set_title('R-squared Distribution')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Perfect match rate distribution
    ax2 = axes[0, 1]
    ax2.hist(df_summary['perfect_pct'], bins=20, alpha=0.7, color='gold', edgecolor='black')
    ax2.axvline(df_summary['perfect_pct'].mean(), color='red', linestyle='--', linewidth=2,
                label=f'Mean = {df_summary["perfect_pct"].mean():.1f}%')
    ax2.set_xlabel('Perfect Match Rate (%)')
    ax2.set_ylabel('Number of Variables')
    ax2.set_title('Perfect Match Rate Distribution')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Total difference percentage
    ax3 = axes[0, 2]
    ax3.hist(df_summary['total_diff_pct'], bins=20, alpha=0.7, color='lightcoral', edgecolor='black')
    ax3.axvline(0, color='black', linestyle='-', linewidth=2, alpha=0.8)
    ax3.axvline(df_summary['total_diff_pct'].mean(), color='red', linestyle='--', linewidth=2,
                label=f'Mean = {df_summary["total_diff_pct"].mean():.2f}%')
    ax3.set_xlabel('Total Difference (%)')
    ax3.set_ylabel('Number of Variables')
    ax3.set_title('Regional Total Difference Distribution')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Top performers by R-squared
    ax4 = axes[1, 0]
    top_vars = df_summary.nlargest(10, 'r_squared')
    bars = ax4.barh(range(len(top_vars)), top_vars['r_squared'], color='steelblue', alpha=0.7)
    ax4.set_yticks(range(len(top_vars)))
    ax4.set_yticklabels(top_vars['variable'], fontsize=10)
    ax4.set_xlabel('R-squared')
    ax4.set_title('Top 10 Variables by R-squared')
    ax4.grid(True, alpha=0.3)
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, top_vars['r_squared'])):
        ax4.text(val + 0.001, bar.get_y() + bar.get_height()/2, f'{val:.3f}', 
                va='center', fontsize=9)
    
    # 5. Perfect match champions
    ax5 = axes[1, 1]
    top_perfect = df_summary.nlargest(10, 'perfect_pct')
    bars = ax5.barh(range(len(top_perfect)), top_perfect['perfect_pct'], color='gold', alpha=0.7)
    ax5.set_yticks(range(len(top_perfect)))
    ax5.set_yticklabels(top_perfect['variable'], fontsize=10)
    ax5.set_xlabel('Perfect Match Rate (%)')
    ax5.set_title('Top 10 Variables by Perfect Match Rate')
    ax5.grid(True, alpha=0.3)
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, top_perfect['perfect_pct'])):
        ax5.text(val + 0.5, bar.get_y() + bar.get_height()/2, f'{val:.1f}%', 
                va='center', fontsize=9)
    
    # 6. Summary statistics table
    ax6 = axes[1, 2]
    ax6.axis('off')
    
    summary_stats = f"""
Overall Performance Summary

Variables Analyzed: {len(df_summary)}
TAZ Zones: {df_summary['taz_count'].iloc[0]:,}

R-squared Statistics:
• Mean: {df_summary['r_squared'].mean():.4f}
• Median: {df_summary['r_squared'].median():.4f}
• Min: {df_summary['r_squared'].min():.4f}
• Max: {df_summary['r_squared'].max():.4f}
• > 0.95: {(df_summary['r_squared'] > 0.95).sum()} variables

Perfect Match Statistics:
• Mean: {df_summary['perfect_pct'].mean():.1f}%
• Median: {df_summary['perfect_pct'].median():.1f}%
• > 90%: {(df_summary['perfect_pct'] > 90).sum()} variables
• > 80%: {(df_summary['perfect_pct'] > 80).sum()} variables

Regional Accuracy:
• Mean total diff: {df_summary['total_diff_pct'].mean():.2f}%
• Within ±1%: {((df_summary['total_diff_pct'].abs()) <= 1).sum()} variables
• Within ±5%: {((df_summary['total_diff_pct'].abs()) <= 5).sum()} variables
"""
    
    ax6.text(0.1, 0.9, summary_stats, transform=ax6.transAxes, fontsize=11,
             verticalalignment='top', fontfamily='monospace')
    
    plt.tight_layout()
    
    # Save summary chart
    summary_file = output_dir / "taz_overall_summary.png"
    plt.savefig(summary_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save detailed results CSV
    csv_file = output_dir / "taz_analysis_summary.csv"
    df_summary.to_csv(csv_file, index=False)
    print(f"[INFO] Summary data saved to: {csv_file}")
    
    print(f"\n[SUMMARY] OVERALL PERFORMANCE SUMMARY:")
    print(f"   • Variables analyzed: {len(df_summary)}")
    print(f"   • Mean R-squared: {df_summary['r_squared'].mean():.4f}")
    print(f"   • Mean perfect match rate: {df_summary['perfect_pct'].mean():.1f}%")
    print(f"   • Variables with R² > 0.95: {(df_summary['r_squared'] > 0.95).sum()}")
    print(f"   • Variables with >90% perfect matches: {(df_summary['perfect_pct'] > 90).sum()}")

def analyze_total_population_by_taz():
    """Analyze total population by TAZ compared to controls"""
    
    print("\n" + "="*80)
    print("TOTAL POPULATION BY TAZ ANALYSIS")
    print("="*80)
    
    # Load TAZ data
    taz_file = OUTPUT_ROOT / "populationsim_working_dir" / "output" / "final_summary_TAZ_NODE.csv"
    if not taz_file.exists():
        print(f"Error: Could not find {taz_file}")
        return
    
    df = pd.read_csv(taz_file)
    
    # Calculate total population from age groups
    age_vars = ['pers_age_00_19', 'pers_age_20_34', 'pers_age_35_64', 'pers_age_65_plus']
    
    # Sum control and result populations
    df['total_pop_control'] = sum(df[f"{var}_control"] for var in age_vars)
    df['total_pop_result'] = sum(df[f"{var}_result"] for var in age_vars)
    df['total_pop_diff'] = df['total_pop_result'] - df['total_pop_control']
    df['total_pop_pct_error'] = (df['total_pop_diff'] / np.maximum(df['total_pop_control'], 1)) * 100
    
    # Overall statistics
    total_control = df['total_pop_control'].sum()
    total_result = df['total_pop_result'].sum()
    total_diff = total_result - total_control
    total_diff_pct = (total_diff / total_control) * 100
    
    print("[INFO] Total Population Analysis:")
    print(f"   • Control Population: {total_control:,.0f}")
    print(f"   • Result Population: {total_result:,.0f}")
    print(f"   • Difference: {total_diff:,.0f} ({total_diff_pct:+.3f}%)")
    print(f"   • TAZ zones analyzed: {len(df):,}")
    
    # Error statistics
    mae = np.mean(np.abs(df['total_pop_diff']))
    rmse = np.sqrt(np.mean(df['total_pop_diff']**2))
    r_squared = np.corrcoef(df['total_pop_control'], df['total_pop_result'])[0, 1]**2
    perfect_matches = (df['total_pop_diff'] == 0).sum()
    perfect_pct = (perfect_matches / len(df)) * 100
    
    print(f"   • MAE: {mae:.2f}, RMSE: {rmse:.2f}, R²: {r_squared:.6f}")
    print(f"   • Perfect matches: {perfect_matches:,} ({perfect_pct:.1f}%)")
    
    # Create visualization (repo-root based)
    output_dir = OUTPUT_ROOT / "charts" / "taz_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Total Population by TAZ: Controls vs Results', fontsize=16, fontweight='bold')

    # 1. Scatter plot (Control vs Result) with best-fit line and equation annotation
    ax1 = axes[0, 0]
    x = df['total_pop_control'].values
    y = df['total_pop_result'].values
    scatter = ax1.scatter(x, y, alpha=0.6, s=20, c='steelblue', edgecolors='none')

    # Perfect line
    max_val = max(x.max(), y.max())
    ax1.plot([0, max_val], [0, max_val], 'r--', alpha=0.8, linewidth=2, label='Perfect Match')

    # Best fit line (linear regression) and equation annotation
    if len(x) > 1:
        m, b = np.polyfit(x, y, 1)
        p = np.poly1d((m, b))
        ax1.plot([0, max_val], p([0, max_val]), color='orange', linewidth=2, alpha=0.9,
                 label=f'Best Fit: y = {m:.4f}x + {b:.1f}')

        # Annotate equation and R^2 on the plot
        eq_text = f'y = {m:.4f}x + {b:.1f}\nR² = {r_squared:.4f}'
        # Place annotation in top-left corner of the axes
        ax1.text(0.02, 0.98, eq_text, transform=ax1.transAxes, fontsize=10,
                 verticalalignment='top', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

    ax1.set_xlabel('Control Population')
    ax1.set_ylabel('Result Population')
    ax1.set_title('Population Control vs Result')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. Error distribution (zoomed to -2000..2000 on x; counts 0..1500 on y)
    ax2 = axes[0, 1]
    errors = df['total_pop_diff']
    # Filter errors to the requested display range so the histogram focuses on the central mass
    err_min, err_max = -2000, 2000
    errors_display = errors[(errors >= err_min) & (errors <= err_max)]
    n_bins = min(80, max(10, int(np.sqrt(len(errors_display)))))
    if len(errors_display) > 0:
        ax2.hist(errors_display, bins=n_bins, alpha=0.7, color='lightcoral', edgecolor='black')
    else:
        # Fallback: plot empty histogram with same bins
        ax2.hist([], bins=n_bins, alpha=0.7, color='lightcoral', edgecolor='black')
    ax2.axvline(0, color='red', linestyle='--', linewidth=2, alpha=0.8)
    ax2.set_xlabel('Population Error (Result - Control)')
    ax2.set_ylabel('Number of TAZs')
    ax2.set_title(f'Population Error Distribution\nMAE = {mae:.1f}')
    # Zoom x-axis to the requested range and limit y-axis counts
    ax2.set_xlim(err_min, err_max)
    ax2.set_ylim(0, 1500)
    ax2.grid(True, alpha=0.3)

    # 3. (Removed) Population Error by TAZ ID - per user request the geographic-by-ID chart is removed
    # Keep the axis invisible (no placeholder text) so the figure layout stays consistent
    ax3 = axes[1, 0]
    ax3.axis('off')

    # 4. Summary statistics
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    summary_text = f"""Population Summary Statistics:

Regional Totals:
• Control Population: {total_control:,.0f}
• Result Population: {total_result:,.0f}  
• Total Difference: {total_diff:+,.0f}
• Percent Error: {total_diff_pct:+.3f}%

TAZ-Level Performance:
• Mean Absolute Error: {mae:.1f} people
• Root Mean Square Error: {rmse:.1f} people
• R-squared: {r_squared:.6f}
• Perfect Matches: {perfect_matches:,} ({perfect_pct:.1f}%)

Error Distribution:
• Min Error: {errors.min():,.0f}
• Max Error: {errors.max():,.0f}
• Std Dev: {errors.std():.1f}
• Median Error: {errors.median():.1f}
"""
    
    # Increase summary stats font size for readability per request
    ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes, fontsize=13,
             verticalalignment='top', fontfamily='monospace')
    
    plt.tight_layout()
    
    # Save chart
    pop_file = output_dir / "taz_total_population_analysis.png"
    plt.savefig(pop_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[INFO] Population analysis chart saved to: {pop_file}")
    
    # Save detailed population data
    pop_csv = output_dir / "taz_population_summary.csv" 
    df[['id', 'total_pop_control', 'total_pop_result', 'total_pop_diff', 'total_pop_pct_error']].to_csv(pop_csv, index=False)
    print(f"[INFO] Population data saved to: {pop_csv}")

def create_tableau_export():
    """Create Tableau-formatted export with controls, results, and differences for mapping"""
    
    print("="*80)
    print("CREATING TABLEAU MAP DATA EXPORT")
    print("="*80)
    
    # Load TAZ data
    taz_file = OUTPUT_ROOT / "populationsim_working_dir" / "output" / "final_summary_TAZ_NODE.csv"
    if not taz_file.exists():
        print(f"Error: Could not find {taz_file}")
        return

    df = pd.read_csv(taz_file)
    print(f"[INFO] Loaded TAZ data: {len(df):,} TAZ zones")

    # Create output directory
    output_dir = OUTPUT_ROOT / "tableau"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Start with geography columns
    tableau_data = df[['id']].copy()
    tableau_data = tableau_data.rename(columns={'id': 'TAZ_NODE'})
    
    # Calculate summary variables first (as requested) with human-readable names
    print("[INFO] Calculating summary variables...")
    
    # 1. Total Households (sum of all hh_size categories) - NOTE: this excludes GQ
    # Label changed to make explicit that these are Non-GQ households
    hh_size_vars = ['hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4', 'hh_size_5', 'hh_size_6_plus']
    tableau_data['Total Households Non-GQ - Control'] = sum(df[f"{var}_control"] for var in hh_size_vars)
    tableau_data['Total Households Non-GQ - Result'] = sum(df[f"{var}_result"] for var in hh_size_vars)
    tableau_data['Total Households Non-GQ - Difference'] = tableau_data['Total Households Non-GQ - Result'] - tableau_data['Total Households Non-GQ - Control']
    
    # 2. Total Group Quarters (sum of GQ categories)
    gq_vars = ['hh_gq_university', 'hh_gq_noninstitutional']
    tableau_data['Total Group Quarters - Control'] = sum(df[f"{var}_control"] for var in gq_vars)
    tableau_data['Total Group Quarters - Result'] = sum(df[f"{var}_result"] for var in gq_vars)
    tableau_data['Total Group Quarters - Difference'] = tableau_data['Total Group Quarters - Result'] - tableau_data['Total Group Quarters - Control']
    
    # 3. Total Population (sum of age categories)
    age_vars = ['pers_age_00_19', 'pers_age_20_34', 'pers_age_35_64', 'pers_age_65_plus']
    tableau_data['Total Population - Control'] = sum(df[f"{var}_control"] for var in age_vars)
    tableau_data['Total Population - Result'] = sum(df[f"{var}_result"] for var in age_vars)
    tableau_data['Total Population - Difference'] = tableau_data['Total Population - Result'] - tableau_data['Total Population - Control']
    
    # Create human-readable variable name mapping
    variable_labels = {
        'numhh_gq': 'Total Households + Group Quarters',
        'hh_gq_university': 'Group Quarters - University',
        'hh_gq_noninstitutional': 'Group Quarters - Non-institutional',
        'hh_size_1': 'Household Size - 1 Person (including GQ)',
        'hh_size_2': 'Household Size - 2 Persons',
        'hh_size_3': 'Household Size - 3 Persons', 
        'hh_size_4': 'Household Size - 4 Persons',
        'hh_size_5': 'Household Size - 5 Persons',
        'hh_size_6_plus': 'Household Size - 6+ Persons',
        'hh_wrks_0': 'Households - 0 Workers',
        'hh_wrks_1': 'Households - 1 Worker',
        'hh_wrks_2': 'Households - 2 Workers',
        'hh_wrks_3_plus': 'Households - 3+ Workers',
        'pers_age_00_19': 'Population - Age 0-19',
        'pers_age_20_34': 'Population - Age 20-34',
        'pers_age_35_64': 'Population - Age 35-64',
        'pers_age_65_plus': 'Population - Age 65+',
        'hh_kids_yes': 'Households - With Children',
        'hh_kids_no': 'Households - Without Children',
        'inc_lt_20k': 'Income - Under $20k',
        'inc_20k_45k': 'Income - $20k to $45k',
        'inc_45k_60k': 'Income - $45k to $60k',
        'inc_60k_75k': 'Income - $60k to $75k',
        'inc_75k_100k': 'Income - $75k to $100k',
        'inc_100k_150k': 'Income - $100k to $150k',
        'inc_150k_200k': 'Income - $150k to $200k',
        'inc_200k_plus': 'Income - $200k+'
    }
    
    # Add all individual control variables with human-readable names
    control_vars = [col for col in df.columns if col.endswith('_control')]
    control_vars = [var.replace('_control', '') for var in control_vars]
    
    print(f"[INFO] Adding {len(control_vars)} individual variables with human-readable names...")
    
    for var in control_vars:
        if f"{var}_control" in df.columns and f"{var}_result" in df.columns:
            # Use human-readable label if available, otherwise clean up the variable name
            label = variable_labels.get(var, var.replace('_', ' ').title())
            
            # No special handling for hh_size_1 in the Tableau export: keep raw hh_size_1
            if var == 'hh_size_1':
                tableau_data[f"{label} - Control"] = df[f"{var}_control"]
                tableau_data[f"{label} - Result"] = df[f"{var}_result"]
                tableau_data[f"{label} - Difference"] = df[f"{var}_result"] - df[f"{var}_control"]
            else:
                tableau_data[f"{label} - Control"] = df[f"{var}_control"]
                tableau_data[f"{label} - Result"] = df[f"{var}_result"]
                tableau_data[f"{label} - Difference"] = df[f"{var}_result"] - df[f"{var}_control"]
    
    # Calculate percentage errors for key summary variables
    tableau_data['Total Households Non-GQ - Percent Error'] = (
        tableau_data['Total Households Non-GQ - Difference'] / np.maximum(tableau_data['Total Households Non-GQ - Control'], 1) * 100
    )
    tableau_data['Total Group Quarters - Percent Error'] = (
        tableau_data['Total Group Quarters - Difference'] / np.maximum(tableau_data['Total Group Quarters - Control'], 1) * 100
    )
    tableau_data['Total Population - Percent Error'] = (
        tableau_data['Total Population - Difference'] / np.maximum(tableau_data['Total Population - Control'], 1) * 100
    )
    
    # Save the Tableau export
    tableau_file = output_dir / "taz_controls_results_tableau.csv"
    tableau_data.to_csv(tableau_file, index=False)
    
    print(f"[INFO] Tableau data exported to: {tableau_file}")
    print(f"[INFO] Export contains {len(tableau_data)} TAZ zones and {len(tableau_data.columns)} variables")
    
    # Print summary of key totals
    print("\n[SUMMARY] Regional Totals:")
    print(f"   • Total Households Non-GQ - Control: {tableau_data['Total Households Non-GQ - Control'].sum():,}")
    print(f"   • Total Households Non-GQ - Result: {tableau_data['Total Households Non-GQ - Result'].sum():,}")
    print(f"   • Total Households Non-GQ - Difference: {tableau_data['Total Households Non-GQ - Difference'].sum():+,}")
    
    print(f"   • Total Group Quarters - Control: {tableau_data['Total Group Quarters - Control'].sum():,}")
    print(f"   • Total Group Quarters - Result: {tableau_data['Total Group Quarters - Result'].sum():,}")
    print(f"   • Total Group Quarters - Difference: {tableau_data['Total Group Quarters - Difference'].sum():+,}")
    
    print(f"   • Total Population - Control: {tableau_data['Total Population - Control'].sum():,}")
    print(f"   • Total Population - Result: {tableau_data['Total Population - Result'].sum():,}")
    print(f"   • Total Population - Difference: {tableau_data['Total Population - Difference'].sum():+,}")
    
    # Print column information for Tableau users
    print(f"\n[INFO] Variable naming convention:")
    print(f"   • * - Control: Control/target values")
    print(f"   • * - Result: PopulationSim output values")
    print(f"   • * - Difference: Difference (result - control)")
    print(f"   • * - Percent Error: Percentage error for summary variables")
    
    return tableau_file

if __name__ == '__main__':
    analyze_taz_controls_vs_results()
    analyze_total_population_by_taz()
    create_tableau_export()


