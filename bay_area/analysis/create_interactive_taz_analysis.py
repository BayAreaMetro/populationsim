"""
Interactive TAZ Controls vs Results Analysis
==========================================

Create interactive charts using Plotly for TAZ-level analysis with:
- Proper axis labels (e.g., "Number of Households")
- Interactive hover information
- No box plots
- Zoom and pan capabilities
- Variable selection dropdowns

"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Variable name mapping for better axis labels
VARIABLE_LABELS = {
    'numhh_gq': 'Number of Households',
    'hh_gq_university': 'University Group Quarters',
    'hh_gq_noninstitutional': 'Non-Institutional Group Quarters', 
    'hh_size_1': 'Single-Person Households',
    'hh_size_2': 'Two-Person Households',
    'hh_size_3': 'Three-Person Households',
    'hh_size_4': 'Four-Person Households',
    'hh_size_5': 'Five-Person Households',
    'hh_size_6_plus': 'Six+ Person Households',
    'hh_wrks_0': 'Households with 0 Workers',
    'hh_wrks_1': 'Households with 1 Worker',
    'hh_wrks_2': 'Households with 2 Workers',
    'hh_wrks_3_plus': 'Households with 3+ Workers',
    'pers_age_00_19': 'Persons Age 0-19',
    'pers_age_20_34': 'Persons Age 20-34',
    'pers_age_35_64': 'Persons Age 35-64',
    'pers_age_65_plus': 'Persons Age 65+',
    'hh_kids_yes': 'Households with Children',
    'hh_kids_no': 'Households without Children',
    'inc_lt_20k': 'Households Income <$20k',
    'inc_20k_45k': 'Households Income $20k-45k',
    'inc_45k_60k': 'Households Income $45k-60k',
    'inc_60k_75k': 'Households Income $60k-75k',
    'inc_75k_100k': 'Households Income $75k-100k',
    'inc_100k_150k': 'Households Income $100k-150k',
    'inc_150k_200k': 'Households Income $150k-200k',
    'inc_200k_plus': 'Households Income $200k+'
}

def load_taz_data():
    """Load TAZ data"""
    
    print("[INFO] Loading TAZ data...")
    
    taz_file = Path("output_2023/populationsim_working_dir/output/final_summary_TAZ_NODE.csv")
    if not taz_file.exists():
        print(f"Error: Could not find {taz_file}")
        return None
    
    df = pd.read_csv(taz_file)
    print(f"[INFO] Loaded TAZ data: {len(df):,} TAZ zones")
    
    return df

def create_interactive_variable_chart(df, var_name, output_dir):
    """Create interactive chart for a single variable"""
    
    control_col = f"{var_name}_control"
    result_col = f"{var_name}_result"
    
    if control_col not in df.columns or result_col not in df.columns:
        print(f"   [WARNING] Skipping {var_name} - missing columns")
        return None
    
    controls = df[control_col].values
    results = df[result_col].values
    taz_ids = df['id'].values
    
    # Calculate metrics
    errors = results - controls
    pct_errors = (errors / np.maximum(controls, 1)) * 100
    
    # Calculate statistics
    r_squared = np.corrcoef(controls, results)[0, 1]**2 if len(controls) > 1 else 0
    mae = np.mean(np.abs(errors))
    perfect_matches = np.sum(errors == 0)
    perfect_pct = (perfect_matches / len(errors)) * 100
    
    # Get proper label
    var_label = VARIABLE_LABELS.get(var_name, var_name.replace('_', ' ').title())
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            f'Control vs Result: {var_label}',
            f'Error Distribution: {var_label}', 
            f'Percentage Error Distribution: {var_label}',
            f'Perfect Match Analysis: {var_label}'
        ),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # 1. Scatter plot: Control vs Result
    max_val = max(controls.max(), results.max())
    min_val = min(controls.min(), results.min())
    
    # Add scatter points
    fig.add_trace(
        go.Scatter(
            x=controls,
            y=results,
            mode='markers',
            name='TAZ Values',
            marker=dict(
                size=6,
                color='steelblue',
                opacity=0.6,
                line=dict(width=1, color='white')
            ),
            hovertemplate='<b>TAZ %{customdata}</b><br>' +
                         f'Control {var_label}: %{{x:,.0f}}<br>' +
                         f'Result {var_label}: %{{y:,.0f}}<br>' +
                         'Difference: %{customdata[1]:+,.0f}<br>' +
                         'Percent Error: %{customdata[2]:+.1f}%<br>' +
                         '<extra></extra>',
            customdata=np.column_stack([taz_ids, errors, pct_errors])
        ),
        row=1, col=1
    )
    
    # Perfect fit line (y=x)
    fig.add_trace(
        go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode='lines',
            name='Perfect Fit (y=x)',
            line=dict(color='red', dash='dash', width=2),
            hovertemplate='Perfect Fit Line<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Best fit line
    if len(controls) > 1:
        z = np.polyfit(controls, results, 1)
        p = np.poly1d(z)
        m, b = z  # slope and intercept
        eqn = f'y = {m:.3f}x + {b:.1f}'
        fig.add_trace(
            go.Scatter(
                x=controls,
                y=p(controls),
                mode='lines',
                name=f'Best Fit (R²={r_squared:.3f})',
                line=dict(color='orange', width=2),
                hovertemplate=f'Best Fit Line<br>R²={r_squared:.3f}<br>{eqn}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # 2. Error distribution histogram
    fig.add_trace(
        go.Histogram(
            x=errors,
            nbinsx=min(50, max(10, int(np.sqrt(len(errors))))),
            name='Error Distribution',
            marker_color='lightcoral',
            opacity=0.7,
            hovertemplate='Error Range: %{x}<br>Count: %{y}<extra></extra>'
        ),
        row=1, col=2
    )
    
    # Add vertical line at 0
    fig.add_vline(
        x=0, line_dash="dash", line_color="red", 
        annotation_text="Zero Error",
        row=1, col=2
    )
    
    # 3. Percentage error distribution
    # Filter extreme values for better visualization
    pct_errors_filtered = pct_errors[(pct_errors >= -100) & (pct_errors <= 100)]
    
    fig.add_trace(
        go.Histogram(
            x=pct_errors_filtered,
            nbinsx=min(50, max(10, int(np.sqrt(len(pct_errors_filtered))))),
            name='% Error Distribution',
            marker_color='lightgreen',
            opacity=0.7,
            hovertemplate='% Error Range: %{x}<br>Count: %{y}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Add vertical line at 0
    fig.add_vline(
        x=0, line_dash="dash", line_color="green",
        annotation_text="Zero % Error", 
        row=2, col=1
    )
    
    # 4. Perfect match analysis by control value bins
    if controls.max() > controls.min():
        control_bins = np.percentile(controls, [0, 25, 50, 75, 100])
        control_bins = np.unique(control_bins)
        
        if len(control_bins) > 1:
            bin_labels = []
            perfect_rates = []
            bin_centers = []
            
            for i in range(len(control_bins) - 1):
                mask = (controls >= control_bins[i]) & (controls < control_bins[i+1])
                if i == len(control_bins) - 2:  # Last bin includes upper bound
                    mask = (controls >= control_bins[i]) & (controls <= control_bins[i+1])
                
                if mask.sum() > 0:
                    perfect_rate = (errors[mask] == 0).sum() / mask.sum() * 100
                    perfect_rates.append(perfect_rate)
                    bin_labels.append(f'{control_bins[i]:.0f}-{control_bins[i+1]:.0f}')
                    bin_centers.append((control_bins[i] + control_bins[i+1]) / 2)
            
            if perfect_rates:
                fig.add_trace(
                    go.Bar(
                        x=bin_labels,
                        y=perfect_rates,
                        name='Perfect Match Rate',
                        marker_color='gold',
                        opacity=0.7,
                        hovertemplate='Control Range: %{x}<br>Perfect Match Rate: %{y:.1f}%<extra></extra>'
                    ),
                    row=2, col=2
                )
    
    # Update layout
    fig.update_layout(
        title_text=f"Interactive TAZ Analysis: {var_label}",
        title_x=0.5,
        height=800,
        showlegend=True,
        hovermode='closest'
    )
    
    # Update axis labels
    fig.update_xaxes(title_text=f"Control {var_label}", row=1, col=1)
    fig.update_yaxes(title_text=f"Result {var_label}", row=1, col=1)
    
    fig.update_xaxes(title_text="Error (Result - Control)", row=1, col=2)
    fig.update_yaxes(title_text="Number of TAZ Zones", row=1, col=2)
    
    fig.update_xaxes(title_text="Percentage Error (%)", row=2, col=1)
    fig.update_yaxes(title_text="Number of TAZ Zones", row=2, col=1)
    
    fig.update_xaxes(title_text="Control Value Range", row=2, col=2)
    fig.update_yaxes(title_text="Perfect Match Rate (%)", row=2, col=2)
    
    # Add annotations with statistics
    if len(controls) > 1:
        z = np.polyfit(controls, results, 1)
        m, b = z
        eqn = f'y = {m:.3f}x + {b:.1f}'
        equation_text = f"<br>Best Fit: {eqn}"
    else:
        equation_text = ""
    
    fig.add_annotation(
        text=f"<b>Performance Metrics:</b><br>"
             f"R² = {r_squared:.4f}{equation_text}<br>"
             f"MAE = {mae:.2f}<br>"
             f"Perfect Matches = {perfect_matches:,} ({perfect_pct:.1f}%)<br>"
             f"Total Control = {controls.sum():,.0f}<br>"
             f"Total Result = {results.sum():,.0f}",
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        xanchor="left", yanchor="top",
        showarrow=False,
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="black",
        borderwidth=1
    )
    
    # Save the interactive chart
    safe_name = var_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    output_file = output_dir / f"interactive_taz_{safe_name}.html"
    fig.write_html(output_file)
    
    return {
        'variable': var_name,
        'r_squared': r_squared,
        'mae': mae,
        'perfect_pct': perfect_pct,
        'file': output_file
    }

def create_variable_selector_dashboard(df, output_dir):
    """Create a dashboard with variable selector dropdown"""
    
    print("[INFO] Creating interactive dashboard with variable selector...")
    
    # Get control variables
    control_vars = [col.replace('_control', '') for col in df.columns if col.endswith('_control')]
    control_vars = [var for var in control_vars if f"{var}_result" in df.columns]
    
    # Start with first variable
    initial_var = control_vars[0]
    
    # Create initial traces for first variable
    controls = df[f"{initial_var}_control"].values
    results = df[f"{initial_var}_result"].values
    taz_ids = df['id'].values
    errors = results - controls
    pct_errors = (errors / np.maximum(controls, 1)) * 100
    
    # Create figure with dropdown
    fig = go.Figure()
    
    # Add initial scatter plot
    fig.add_trace(
        go.Scatter(
            x=controls,
            y=results,
            mode='markers',
            name='TAZ Values',
            marker=dict(
                size=6,
                color='steelblue',
                opacity=0.6,
                line=dict(width=1, color='white')
            ),
            hovertemplate='<b>TAZ %{customdata[0]}</b><br>' +
                         'Control: %{x:,.0f}<br>' +
                         'Result: %{y:,.0f}<br>' +
                         'Difference: %{customdata[1]:+,.0f}<br>' +
                         'Percent Error: %{customdata[2]:+.1f}%<br>' +
                         '<extra></extra>',
            customdata=np.column_stack([taz_ids, errors, pct_errors])
        )
    )
    
    # Add perfect fit line
    max_val = max(controls.max(), results.max())
    min_val = min(controls.min(), results.min())
    
    fig.add_trace(
        go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode='lines',
            name='Perfect Fit (y=x)',
            line=dict(color='red', dash='dash', width=2),
            hovertemplate='Perfect Fit Line<extra></extra>'
        )
    )
    
    # Add best fit line
    if len(controls) > 1:
        z = np.polyfit(controls, results, 1)
        p = np.poly1d(z)
        r_squared_initial = np.corrcoef(controls, results)[0, 1]**2
        fig.add_trace(
            go.Scatter(
                x=controls,
                y=p(controls),
                mode='lines',
                name=f'Best Fit (R²={r_squared_initial:.3f})',
                line=dict(color='orange', width=2),
                hovertemplate=f'Best Fit Line (R²={r_squared_initial:.3f})<extra></extra>'
            )
        )
    
    # Create dropdown buttons for variable selection
    dropdown_buttons = []
    
    for var in control_vars:
        var_label = VARIABLE_LABELS.get(var, var.replace('_', ' ').title())
        
        # Get data for this variable
        var_controls = df[f"{var}_control"].values
        var_results = df[f"{var}_result"].values
        var_errors = var_results - var_controls
        var_pct_errors = (var_errors / np.maximum(var_controls, 1)) * 100
        var_max = max(var_controls.max(), var_results.max())
        var_min = min(var_controls.min(), var_results.min())
        
        # Calculate metrics
        r_squared = np.corrcoef(var_controls, var_results)[0, 1]**2 if len(var_controls) > 1 else 0
        mae = np.mean(np.abs(var_errors))
        perfect_matches = np.sum(var_errors == 0)
        perfect_pct = (perfect_matches / len(var_errors)) * 100
        
        # Calculate best fit equation
        if len(var_controls) > 1:
            z = np.polyfit(var_controls, var_results, 1)
            m, b = z
            eqn = f'y = {m:.3f}x + {b:.1f}'
            equation_text = f"<br>Best Fit: {eqn}"
        else:
            equation_text = ""
        
        dropdown_buttons.append(
            dict(
                label=var_label,
                method="update",
                args=[
                    {
                        "x": [var_controls, [var_min, var_max]],
                        "y": [var_results, [var_min, var_max]],
                        "customdata": [np.column_stack([taz_ids, var_errors, var_pct_errors]), None],
                        "hovertemplate": [
                            f'<b>TAZ %{{customdata[0]}}</b><br>' +
                            f'Control {var_label}: %{{x:,.0f}}<br>' +
                            f'Result {var_label}: %{{y:,.0f}}<br>' +
                            'Difference: %{customdata[1]:+,.0f}<br>' +
                            'Percent Error: %{customdata[2]:+.1f}%<br>' +
                            '<extra></extra>',
                            'Perfect Fit Line<extra></extra>'
                        ]
                    },
                    {
                        "title": f"Interactive TAZ Analysis: {var_label}",
                        "xaxis.title": f"Control {var_label}",
                        "yaxis.title": f"Result {var_label}",
                        "annotations": [
                            dict(
                                text=f"<b>Performance Metrics:</b><br>"
                                     f"R² = {r_squared:.4f}{equation_text}<br>"
                                     f"MAE = {mae:.2f}<br>"
                                     f"Perfect Matches = {perfect_matches:,} ({perfect_pct:.1f}%)<br>"
                                     f"Total Control = {var_controls.sum():,.0f}<br>"
                                     f"Total Result = {var_results.sum():,.0f}",
                                xref="paper", yref="paper",
                                x=0.02, y=0.98,
                                xanchor="left", yanchor="top",
                                showarrow=False,
                                bgcolor="rgba(255,255,255,0.8)",
                                bordercolor="black",
                                borderwidth=1
                            )
                        ]
                    }
                ]
            )
        )
    
    # Calculate initial metrics for annotation
    r_squared = np.corrcoef(controls, results)[0, 1]**2 if len(controls) > 1 else 0
    mae = np.mean(np.abs(errors))
    perfect_matches = np.sum(errors == 0)
    perfect_pct = (perfect_matches / len(errors)) * 100
    initial_label = VARIABLE_LABELS.get(initial_var, initial_var.replace('_', ' ').title())
    
    # Calculate initial equation
    if len(controls) > 1:
        z = np.polyfit(controls, results, 1)
        m, b = z
        eqn = f'y = {m:.3f}x + {b:.1f}'
        equation_text = f"<br>Best Fit: {eqn}"
    else:
        equation_text = ""
    
    # Update layout
    fig.update_layout(
        title=f"Interactive TAZ Analysis: {initial_label}",
        xaxis_title=f"Control {initial_label}",
        yaxis_title=f"Result {initial_label}",
        height=700,
        updatemenus=[
            dict(
                active=0,
                buttons=dropdown_buttons,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.1,
                xanchor="left",
                y=1.15,
                yanchor="top"
            ),
        ],
        annotations=[
            dict(
                text="Select Variable:",
                x=0.01, xref="paper",
                y=1.15, yref="paper",
                align="left",
                showarrow=False
            ),
            dict(
                text=f"<b>Performance Metrics:</b><br>"
                     f"R² = {r_squared:.4f}{equation_text}<br>"
                     f"MAE = {mae:.2f}<br>"
                     f"Perfect Matches = {perfect_matches:,} ({perfect_pct:.1f}%)<br>"
                     f"Total Control = {controls.sum():,.0f}<br>"
                     f"Total Result = {results.sum():,.0f}",
                xref="paper", yref="paper",
                x=0.02, y=0.98,
                xanchor="left", yanchor="top",
                showarrow=False,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="black",
                borderwidth=1
            )
        ]
    )
    
    # Save the dashboard
    dashboard_file = output_dir / "interactive_taz_dashboard.html"
    fig.write_html(dashboard_file)
    
    return dashboard_file

def create_interactive_taz_analysis():
    """Main function to create interactive TAZ analysis"""
    
    print("="*80)
    print("INTERACTIVE TAZ CONTROLS VS RESULTS ANALYSIS")
    print("="*80)
    
    # Load data
    df = load_taz_data()
    if df is None:
        return
    
    # Create output directory
    output_dir = Path("output_2023/charts/interactive_taz")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get control variables
    control_vars = [col.replace('_control', '') for col in df.columns if col.endswith('_control')]
    control_vars = [var for var in control_vars if f"{var}_result" in df.columns]
    
    print("[INFO] Creating interactive charts for {:} variables...".format(len(control_vars)))
    
    # Create individual charts
    results = []
    for i, var in enumerate(control_vars):
        print(f"   [INFO] Creating chart {i+1}/{len(control_vars)}: {var}")
        result = create_interactive_variable_chart(df, var, output_dir)
        if result:
            results.append(result)
    
    # Create dashboard with variable selector
    dashboard_file = create_variable_selector_dashboard(df, output_dir)
    
    # Create summary index page
    create_summary_index(results, dashboard_file, output_dir)
    
    print(f"\n[SUCCESS] Interactive analysis complete!")
    print(f"[INFO] Generated {len(results)} interactive charts")
    print(f"[DASHBOARD] Dashboard: {dashboard_file}")
    print(f"📁 All files saved to: {output_dir}")

def create_summary_index(results, dashboard_file, output_dir):
    """Create an HTML index page with links to all charts"""
    
    # Sort results by R-squared
    results_sorted = sorted(results, key=lambda x: x['r_squared'], reverse=True)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Interactive TAZ Analysis - Bay Area PopulationSim</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #2E86AB; }}
            h2 {{ color: #A23B72; }}
            .dashboard-link {{ 
                background-color: #F18F01; 
                color: white; 
                padding: 15px 30px; 
                text-decoration: none; 
                border-radius: 5px; 
                font-size: 18px;
                display: inline-block;
                margin-bottom: 30px;
            }}
            .dashboard-link:hover {{ background-color: #C73E1D; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .good {{ color: #2E8B57; font-weight: bold; }}
            .moderate {{ color: #FF8C00; font-weight: bold; }}
            .attention {{ color: #DC143C; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>Interactive TAZ Analysis - Bay Area PopulationSim Results</h1>
        
        <a href="{dashboard_file.name}" class="dashboard-link">[LINK] Open Interactive Dashboard</a>
        
        <h2>Performance Summary</h2>
        <table>
            <tr>
                <th>Variable</th>
                <th>R-squared</th>
                <th>MAE</th>
                <th>Perfect Match %</th>
                <th>Interactive Chart</th>
            </tr>
    """
    
    for result in results_sorted:
        var_label = VARIABLE_LABELS.get(result['variable'], result['variable'].replace('_', ' ').title())
        
        # Color code performance
        r2_class = "good" if result['r_squared'] > 0.8 else "moderate" if result['r_squared'] > 0.6 else "attention"
        perfect_class = "good" if result['perfect_pct'] > 20 else "moderate" if result['perfect_pct'] > 5 else "attention"
        
        html_content += f"""
            <tr>
                <td>{var_label}</td>
                <td class="{r2_class}">{result['r_squared']:.4f}</td>
                <td>{result['mae']:.2f}</td>
                <td class="{perfect_class}">{result['perfect_pct']:.1f}%</td>
                <td><a href="{result['file'].name}">View Chart</a></td>
            </tr>
        """
    
    html_content += """
        </table>
        
        <h2>About This Analysis</h2>
        <p>This interactive analysis shows the performance of PopulationSim across 4,714 TAZ zones in the Bay Area. 
        Each chart allows you to:</p>
        <ul>
            <li><strong>Zoom and Pan:</strong> Use mouse to explore different parts of the data</li>
            <li><strong>Hover Information:</strong> See detailed TAZ-level information by hovering over points</li>
            <li><strong>Performance Metrics:</strong> R-squared, MAE, and perfect match rates are displayed</li>
        </ul>
        
        <h3>Interpretation Guide:</h3>
        <ul>
            <li><span class="good">Excellent Performance:</span> R² > 0.8, Perfect Match > 20%</li>
            <li><span class="moderate">Good Performance:</span> R² > 0.6, Perfect Match > 5%</li>
            <li><span class="attention">Needs Attention:</span> Lower R² or Perfect Match rates</li>
        </ul>
    </body>
    </html>
    """
    
    # Save index file
    index_file = output_dir / "index.html"
    with open(index_file, 'w') as f:
        f.write(html_content)
    
    print(f"📄 Summary index: {index_file}")

if __name__ == '__main__':
    create_interactive_taz_analysis()