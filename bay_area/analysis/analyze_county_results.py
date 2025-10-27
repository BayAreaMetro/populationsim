"""
County-Level PopulationSim Results Visualization
===============================================

Comprehensive analysis and visualization of PopulationSim results at the county level.
Creates charts showing:
1. Controls vs Results by county
2. Geographic distribution of performance
3. Variable performance across counties
4. County comparison dashboard

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("Set2")

# County name mapping
COUNTY_NAMES = {
    1: "San Francisco",
    2: "San Mateo", 
    3: "Santa Clara",
    4: "Alameda",
    5: "Contra Costa",
    6: "Solano",
    7: "Napa",
    8: "Sonoma",
    9: "Marin"
}

def load_county_data():
    """Load and combine all county summary files"""
    
    print("Loading county data files...")
    
    all_counties = []
    
    for county_id in range(1, 10):
        county_file = Path(f"output_2023/populationsim_working_dir/output/final_summary_COUNTY_{county_id}.csv")
        
        if county_file.exists():
            df = pd.read_csv(county_file)
            df['county_id'] = county_id
            df['county_name'] = COUNTY_NAMES[county_id]
            
            # Use the final integer weight as the result
            df['result'] = df['TAZ_NODE_integer_weight']
            # Restore the original behavior: use the raw control_value column as the control.
            # The `control_value` field contains the original control marginals (from marginals source).
            df['control'] = df['control_value']
            
            # No special handling for hh_size_1 at the county aggregation level.
            # Keep control and result values as provided in the county summary files.
            
            all_counties.append(df)
            print(f"   Loaded {COUNTY_NAMES[county_id]}: {len(df)} variables")
        else:
            print(f"   Missing file for county {county_id}")
    
    if not all_counties:
        print("No county files found!")
        return None
    
    combined_df = pd.concat(all_counties, ignore_index=True)
    print(f"Combined data: {len(combined_df)} records across {len(all_counties)} counties")
    
    return combined_df

def create_county_performance_overview(df, output_dir):
    """Create overall county performance comparison"""
    
    print("📊 Creating county performance overview...")
    
    # Calculate performance metrics by county
    county_metrics = []
    
    for county_id, county_name in COUNTY_NAMES.items():
        county_data = df[df['county_id'] == county_id]
        
        if len(county_data) == 0:
            continue
        
        # Calculate metrics - use only numhh_gq for total households
        numhh_gq_data = county_data[county_data['control_name'] == 'numhh_gq']
        
        if len(numhh_gq_data) > 0:
            total_control = numhh_gq_data['control'].iloc[0]
            total_result = numhh_gq_data['result'].iloc[0]
        else:
            # Fallback to sum if numhh_gq not found (shouldn't happen)
            total_control = county_data['control'].sum()
            total_result = county_data['result'].sum()
        
        errors = county_data['result'] - county_data['control']
        abs_errors = np.abs(errors)
        
        mae = np.mean(abs_errors)
        rmse = np.sqrt(np.mean(errors**2))
        
        perfect_matches = np.sum(errors == 0)
        perfect_pct = (perfect_matches / len(errors)) * 100
        
        total_diff_pct = ((total_result - total_control) / total_control) * 100 if total_control > 0 else 0
        
        county_metrics.append({
            'county_id': county_id,
            'county_name': county_name,
            'total_control': total_control,
            'total_result': total_result,
            'total_diff': total_result - total_control,
            'total_diff_pct': total_diff_pct,
            'mae': mae,
            'rmse': rmse,
            'perfect_matches': perfect_matches,
            'perfect_pct': perfect_pct,
            'variable_count': len(county_data)
        })
    
    metrics_df = pd.DataFrame(county_metrics)
    
    # Create overview dashboard
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle('County-Level PopulationSim Performance Overview', fontsize=16, fontweight='bold')
    
    # 1. Total households by county
    ax1 = axes[0, 0]
    bars = ax1.bar(metrics_df['county_name'], metrics_df['total_control'] / 1000, 
                   alpha=0.7, color='steelblue', label='Control')
    ax1.bar(metrics_df['county_name'], metrics_df['total_result'] / 1000, 
            alpha=0.7, color='orange', label='Result', width=0.6)
    ax1.set_ylabel('Total Households (thousands)')
    ax1.set_title('Total Households: Control vs Result')
    ax1.legend()
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, metrics_df['total_control'] / 1000)):
        ax1.text(bar.get_x() + bar.get_width()/2, val + 5, f'{val:.0f}k', 
                ha='center', va='bottom', fontsize=9)
    
    # 2. Regional accuracy (total difference %)
    ax2 = axes[0, 1]
    colors = ['green' if abs(x) < 1 else 'orange' if abs(x) < 2 else 'red' 
              for x in metrics_df['total_diff_pct']]
    bars = ax2.bar(metrics_df['county_name'], metrics_df['total_diff_pct'], 
                   alpha=0.7, color=colors)
    ax2.axhline(0, color='black', linestyle='-', linewidth=1, alpha=0.8)
    ax2.set_ylabel('Total Difference (%)')
    ax2.set_title('Regional Total Accuracy by County')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3)
    
    # Add value labels
    for bar, val in zip(bars, metrics_df['total_diff_pct']):
        ax2.text(bar.get_x() + bar.get_width()/2, val + (0.1 if val >= 0 else -0.1), 
                f'{val:.2f}%', ha='center', va='bottom' if val >= 0 else 'top', fontsize=9)
    
    # 3. Perfect match rates
    ax3 = axes[0, 2]
    bars = ax3.bar(metrics_df['county_name'], metrics_df['perfect_pct'], 
                   alpha=0.7, color='gold')
    ax3.set_ylabel('Perfect Match Rate (%)')
    ax3.set_title('Perfect Match Rate by County')
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(True, alpha=0.3)
    
    # Add value labels
    for bar, val in zip(bars, metrics_df['perfect_pct']):
        ax3.text(bar.get_x() + bar.get_width()/2, val + 1, f'{val:.1f}%', 
                ha='center', va='bottom', fontsize=9)
    
    # 4. MAE comparison
    ax4 = axes[1, 0]
    bars = ax4.bar(metrics_df['county_name'], metrics_df['mae'], 
                   alpha=0.7, color='lightcoral')
    ax4.set_ylabel('Mean Absolute Error')
    ax4.set_title('Mean Absolute Error by County')
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(True, alpha=0.3)
    
    # Add value labels
    for bar, val in zip(bars, metrics_df['mae']):
        ax4.text(bar.get_x() + bar.get_width()/2, val + max(metrics_df['mae'])*0.02, 
                f'{val:.1f}', ha='center', va='bottom', fontsize=9)
    
    # 5. County size comparison (pie chart)
    ax5 = axes[1, 1]
    wedges, texts, autotexts = ax5.pie(metrics_df['total_control'], 
                                       labels=metrics_df['county_name'],
                                       autopct='%1.1f%%', startangle=90)
    ax5.set_title('Share of Regional Households by County')
    
    # 6. Summary statistics table
    ax6 = axes[1, 2]
    ax6.axis('off')
    
    # Calculate regional totals
    regional_control = metrics_df['total_control'].sum()
    regional_result = metrics_df['total_result'].sum()
    regional_diff = regional_result - regional_control
    regional_diff_pct = (regional_diff / regional_control) * 100
    
    summary_text = f"""
Regional Performance Summary

Total Households:
• Control: {regional_control:,.0f}
• Result: {regional_result:,.0f}
• Difference: {regional_diff:,.0f} ({regional_diff_pct:.2f}%)

County Performance:
• Mean MAE: {metrics_df['mae'].mean():.1f}
• Mean Perfect Match: {metrics_df['perfect_pct'].mean():.1f}%
• Best Performer: {metrics_df.loc[metrics_df['perfect_pct'].idxmax(), 'county_name']}
• Most Accurate Total: {metrics_df.loc[metrics_df['total_diff_pct'].abs().idxmin(), 'county_name']}

Accuracy Standards:
• Counties within ±1%: {(metrics_df['total_diff_pct'].abs() <= 1).sum()}/9
• Counties within ±2%: {(metrics_df['total_diff_pct'].abs() <= 2).sum()}/9
• Perfect match rate >15%: {(metrics_df['perfect_pct'] > 15).sum()}/9
"""
    
    ax6.text(0.1, 0.9, summary_text, transform=ax6.transAxes, fontsize=11,
             verticalalignment='top', fontfamily='monospace')
    
    plt.tight_layout()
    
    # Save the chart
    output_file = output_dir / "county_performance_overview.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    return metrics_df

def create_variable_performance_by_county(df, output_dir):
    """Create heatmap of variable performance across counties"""
    
    print("📊 Creating variable performance heatmap...")
    
    # Calculate perfect match rates for each variable by county
    pivot_data = []
    
    variables = df['control_name'].unique()
    
    for var in variables:
        var_data = df[df['control_name'] == var]
        
        for county_id, county_name in COUNTY_NAMES.items():
            county_var_data = var_data[var_data['county_id'] == county_id]
            
            if len(county_var_data) > 0:
                error = county_var_data['result'].iloc[0] - county_var_data['control'].iloc[0]
                perfect_match = 1 if error == 0 else 0
                
                control_val = county_var_data['control'].iloc[0]
                result_val = county_var_data['result'].iloc[0]
                
                pct_error = ((result_val - control_val) / control_val * 100) if control_val > 0 else 0
                
                pivot_data.append({
                    'variable': var,
                    'county_name': county_name,
                    'perfect_match': perfect_match,
                    'pct_error': pct_error,
                    'abs_pct_error': abs(pct_error)
                })
    
    pivot_df = pd.DataFrame(pivot_data)
    
    # Create heatmaps
    fig, axes = plt.subplots(1, 2, figsize=(20, 12))
    fig.suptitle('Variable Performance Across Counties', fontsize=16, fontweight='bold')
    
    # 1. Perfect match heatmap
    ax1 = axes[0]
    perfect_pivot = pivot_df.pivot(index='variable', columns='county_name', values='perfect_match')
    
    sns.heatmap(perfect_pivot, annot=True, cmap='RdYlGn', cbar_kws={'label': 'Perfect Match (1=Yes, 0=No)'}, 
                ax=ax1, fmt='d')
    ax1.set_title('Perfect Matches by Variable and County')
    ax1.set_xlabel('County')
    ax1.set_ylabel('Variable')
    
    # 2. Percentage error heatmap
    ax2 = axes[1]
    error_pivot = pivot_df.pivot(index='variable', columns='county_name', values='pct_error')
    
    # Create custom colormap centered at 0
    max_error = max(abs(error_pivot.min().min()), abs(error_pivot.max().max()))
    sns.heatmap(error_pivot, annot=True, cmap='RdBu_r', center=0, 
                vmin=-max_error, vmax=max_error,
                cbar_kws={'label': 'Percentage Error (%)'}, 
                ax=ax2, fmt='.1f')
    ax2.set_title('Percentage Error by Variable and County')
    ax2.set_xlabel('County')
    ax2.set_ylabel('Variable')
    
    plt.tight_layout()
    
    # Save the chart
    output_file = output_dir / "county_variable_heatmap.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def create_detailed_variable_analysis(df, output_dir):
    """Create detailed analysis for key variable categories"""
    
    print("📊 Creating detailed variable analysis...")
    
    # Group variables by category
    variable_categories = {
        'Household Size': [col for col in df['control_name'].unique() if 'hh_size' in col],
        'Workers': [col for col in df['control_name'].unique() if 'hh_wrks' in col],
        'Age Groups': [col for col in df['control_name'].unique() if 'pers_age' in col],
        'Income': [col for col in df['control_name'].unique() if 'inc_' in col],
        'Group Quarters': [col for col in df['control_name'].unique() if 'gq' in col]
    }
    
    # Remove empty categories
    variable_categories = {k: v for k, v in variable_categories.items() if v}
    
    for category, variables in variable_categories.items():
        if not variables:
            continue
            
        print(f"   📈 Analyzing {category} variables...")
        
        # Create figure for this category
        n_vars = len(variables)
        n_cols = min(3, n_vars)
        n_rows = (n_vars + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(6*n_cols, 5*n_rows))
        if n_rows == 1 and n_cols == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = axes
        else:
            axes = axes.flatten()
        
        fig.suptitle(f'{category} Variables: Control vs Result by County', 
                     fontsize=14, fontweight='bold')
        
        for i, var in enumerate(variables):
            if i >= len(axes):
                break
                
            ax = axes[i]
            
            # Get data for this variable
            var_data = df[df['control_name'] == var].copy()
            
            if len(var_data) == 0:
                ax.text(0.5, 0.5, f'No data for\n{var}', ha='center', va='center', transform=ax.transAxes)
                ax.set_title(var.replace('_', ' ').title())
                continue
            
            # Create bar chart
            x = range(len(var_data))
            width = 0.35
            
            bars1 = ax.bar([i - width/2 for i in x], var_data['control'], width, 
                          label='Control', alpha=0.7, color='steelblue')
            bars2 = ax.bar([i + width/2 for i in x], var_data['result'], width,
                          label='Result', alpha=0.7, color='orange')
            
            ax.set_xlabel('County')
            # Set appropriate y-axis label based on variable category
            if category in ['Household Size', 'Workers', 'Income']:
                ax.set_ylabel('Total Households')
            elif category == 'Age Groups':
                ax.set_ylabel('Total Persons')
            elif category == 'Group Quarters':
                ax.set_ylabel('People in Group Quarters')
            else:
                ax.set_ylabel('Count')
            
            # Standard title for the variable
            ax.set_title(var.replace('_', ' ').title())
            ax.set_xticks(x)
            ax.set_xticklabels(var_data['county_name'], rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Add difference annotations
            for j, (ctrl, res) in enumerate(zip(var_data['control'], var_data['result'])):
                diff = res - ctrl
                diff_pct = (diff / ctrl * 100) if ctrl > 0 else 0
                
                color = 'green' if abs(diff_pct) < 1 else 'orange' if abs(diff_pct) < 5 else 'red'
                
                ax.text(j, max(ctrl, res) + max(var_data['control'].max(), var_data['result'].max()) * 0.05,
                       f'{diff_pct:+.1f}%', ha='center', va='bottom', 
                       fontsize=8, color=color, fontweight='bold')
        
        # Hide unused subplots
        for i in range(len(variables), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        
        # Save the chart
        safe_category = category.replace(' ', '_').lower()
        output_file = output_dir / f"county_{safe_category}_analysis.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

def analyze_county_results():
    """Main analysis function"""
    
    print("="*80)
    print("COUNTY-LEVEL POPULATIONSIM RESULTS ANALYSIS")
    print("="*80)
    
    # Load data
    df = load_county_data()
    if df is None:
        return
    
    # Create output directory
    output_dir = Path("output_2023/charts/county_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📊 Analyzing {len(df['control_name'].unique())} variables across {len(df['county_id'].unique())} counties")
    
    # Create visualizations
    metrics_df = create_county_performance_overview(df, output_dir)
    create_variable_performance_by_county(df, output_dir)
    create_detailed_variable_analysis(df, output_dir)
    
    # Save summary data
    summary_file = output_dir / "county_performance_summary.csv"
    metrics_df.to_csv(summary_file, index=False)
    
    # Save detailed data
    detailed_file = output_dir / "county_detailed_results.csv"
    df.to_csv(detailed_file, index=False)
    
    print(f"\n✅ County analysis complete!")
    print(f"📊 Charts saved to: {output_dir}")
    print(f"📈 Generated performance overview, heatmaps, and detailed variable analysis")
    
    # Print summary
    regional_control = metrics_df['total_control'].sum()
    regional_result = metrics_df['total_result'].sum()
    regional_diff_pct = ((regional_result - regional_control) / regional_control) * 100
    
    print(f"\n📈 REGIONAL SUMMARY:")
    print(f"   • Total households - Control: {regional_control:,.0f}, Result: {regional_result:,.0f}")
    print(f"   • Regional accuracy: {regional_diff_pct:+.2f}%")
    print(f"   • Best performing county: {metrics_df.loc[metrics_df['perfect_pct'].idxmax(), 'county_name']}")
    print(f"   • Counties within ±1% total: {(metrics_df['total_diff_pct'].abs() <= 1).sum()}/9")

if __name__ == '__main__':
    analyze_county_results()