#!/usr/bin/env python3
"""
PopulationSim Results Analysis Script
====================================

Comprehensive analysis of PopulationSim TM2 results vs targets:
1. TAZ-level results vs targets analysis
2. MAZ-level household distribution analysis
3. County-level population rollups
4. Visualization of control vs results distributions

Usage:
    python analyze_populationsim_results.py

Output:
    - detailed_results_analysis.txt
    - populationsim_analysis_charts.html (interactive plots)
    - Various CSV summary files
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('populationsim_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PopulationSimAnalyzer:
    """Analyzes PopulationSim results against control targets"""
    
    def __init__(self, working_dir="output_2023/populationsim_working_dir"):
        self.working_dir = Path(working_dir)
        self.output_dir = self.working_dir / "output"
        self.data_dir = self.working_dir / "data"
        self.results = {}
        self.figures = []
        
    def load_data(self):
        """Load all necessary data files"""
        logger.info("Loading PopulationSim results and control data...")
        
        try:
            # Load synthetic population
            self.synthetic_households = pd.read_csv(self.output_dir / "synthetic_households.csv")
            self.synthetic_persons = pd.read_csv(self.output_dir / "synthetic_persons.csv")
            logger.info(f"Loaded {len(self.synthetic_households):,} synthetic households")
            logger.info(f"Loaded {len(self.synthetic_persons):,} synthetic persons")
            
            # Load control targets
            self.taz_controls = pd.read_csv(self.data_dir / "taz_marginals_hhgq.csv")
            self.maz_controls = pd.read_csv(self.data_dir / "maz_marginals_hhgq.csv")
            self.county_controls = pd.read_csv(self.data_dir / "county_marginals.csv")
            logger.info(f"Loaded control targets: {len(self.taz_controls)} TAZ, {len(self.maz_controls)} MAZ, {len(self.county_controls)} County")
            
            # Load TAZ summary results
            self.taz_results = pd.read_csv(self.output_dir / "final_summary_TAZ.csv")
            logger.info(f"Loaded TAZ results: {len(self.taz_results)} zones")
            
            # Load geographic crosswalk
            self.geo_crosswalk = pd.read_csv(self.data_dir / "geo_cross_walk_tm2.csv")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
            
    def analyze_taz_results(self):
        """Analyze TAZ-level results vs targets"""
        logger.info("Analyzing TAZ-level results vs targets...")
        
        # Merge TAZ results with controls
        taz_comparison = pd.merge(
            self.taz_results, 
            self.taz_controls, 
            on='TAZ', 
            how='inner',
            suffixes=('_result', '_target')
        )
        
        # Define control columns to analyze
        control_columns = [
            'hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus',
            'hh_inc_30', 'hh_inc_30_60', 'hh_inc_60_100', 'hh_inc_100_plus',
            'hh_wrks_0', 'hh_wrks_1', 'hh_wrks_2', 'hh_wrks_3_plus',
            'pers_age_00_19', 'pers_age_20_34', 'pers_age_35_64', 'pers_age_65_plus',
            'hh_kids_yes', 'hh_kids_no'
        ]
        
        taz_analysis = {}
        
        for control in control_columns:
            result_col = f"{control}_result"
            target_col = f"{control}_target"
            
            if result_col in taz_comparison.columns and target_col in taz_comparison.columns:
                # Calculate differences
                taz_comparison[f"{control}_diff"] = taz_comparison[result_col] - taz_comparison[target_col]
                taz_comparison[f"{control}_pct_diff"] = np.where(
                    taz_comparison[target_col] > 0,
                    (taz_comparison[f"{control}_diff"] / taz_comparison[target_col]) * 100,
                    np.nan
                )
                
                # Summary statistics
                valid_data = taz_comparison[taz_comparison[target_col] > 0]
                
                analysis = {
                    'mean_pct_diff': valid_data[f"{control}_pct_diff"].mean(),
                    'median_pct_diff': valid_data[f"{control}_pct_diff"].median(),
                    'std_pct_diff': valid_data[f"{control}_pct_diff"].std(),
                    'max_abs_diff': valid_data[f"{control}_diff"].abs().max(),
                    'max_diff_taz': valid_data.loc[valid_data[f"{control}_diff"].abs().idxmax(), 'TAZ'] if len(valid_data) > 0 else None,
                    'max_diff_values': {
                        'target': valid_data.loc[valid_data[f"{control}_diff"].abs().idxmax(), target_col] if len(valid_data) > 0 else None,
                        'result': valid_data.loc[valid_data[f"{control}_diff"].abs().idxmax(), result_col] if len(valid_data) > 0 else None,
                        'difference': valid_data.loc[valid_data[f"{control}_diff"].abs().idxmax(), f"{control}_diff"] if len(valid_data) > 0 else None
                    },
                    'total_target': taz_comparison[target_col].sum(),
                    'total_result': taz_comparison[result_col].sum(),
                    'total_diff': taz_comparison[result_col].sum() - taz_comparison[target_col].sum()
                }
                
                taz_analysis[control] = analysis
        
        self.results['taz_analysis'] = taz_analysis
        self.results['taz_comparison'] = taz_comparison
        
        logger.info(f"Completed TAZ analysis for {len(control_columns)} controls")
        
    def analyze_maz_households(self):
        """Analyze MAZ-level household distribution"""
        logger.info("Analyzing MAZ-level household distribution...")
        
        # Aggregate synthetic households by MAZ
        synthetic_by_maz = self.synthetic_households.groupby('MAZ').agg({
            'unique_hh_id': 'count',
            'hhgqtype': lambda x: (x == 0).sum()  # Count non-GQ households
        }).rename(columns={'unique_hh_id': 'total_hh', 'hhgqtype': 'regular_hh'})
        
        # Add GQ households
        synthetic_by_maz['gq_hh'] = synthetic_by_maz['total_hh'] - synthetic_by_maz['regular_hh']
        
        # Merge with MAZ controls
        maz_comparison = pd.merge(
            synthetic_by_maz,
            self.maz_controls,
            on='MAZ',
            how='outer',
            suffixes=('_result', '_target')
        ).fillna(0)
        
        # Calculate differences for household counts
        maz_comparison['num_hh_diff'] = maz_comparison['total_hh'] - maz_comparison['num_hh']
        maz_comparison['num_hh_pct_diff'] = np.where(
            maz_comparison['num_hh'] > 0,
            (maz_comparison['num_hh_diff'] / maz_comparison['num_hh']) * 100,
            np.nan
        )
        
        # Summary statistics
        valid_maz = maz_comparison[maz_comparison['num_hh'] > 0]
        
        maz_analysis = {
            'total_maz_with_hh': len(valid_maz),
            'mean_hh_pct_diff': valid_maz['num_hh_pct_diff'].mean(),
            'median_hh_pct_diff': valid_maz['num_hh_pct_diff'].median(),
            'std_hh_pct_diff': valid_maz['num_hh_pct_diff'].std(),
            'max_abs_hh_diff': valid_maz['num_hh_diff'].abs().max(),
            'max_diff_maz': valid_maz.loc[valid_maz['num_hh_diff'].abs().idxmax(), 'MAZ'] if len(valid_maz) > 0 else None,
            'total_hh_target': maz_comparison['num_hh'].sum(),
            'total_hh_result': maz_comparison['total_hh'].sum(),
            'total_hh_diff': maz_comparison['total_hh'].sum() - maz_comparison['num_hh'].sum()
        }
        
        self.results['maz_analysis'] = maz_analysis
        self.results['maz_comparison'] = maz_comparison
        
        logger.info(f"Completed MAZ analysis for {len(maz_comparison)} MAZ zones")
        
    def analyze_county_rollups(self):
        """Analyze county-level population rollups"""
        logger.info("Analyzing county-level population rollups...")
        
        # Add county info to synthetic data using crosswalk
        households_with_county = pd.merge(
            self.synthetic_households,
            self.geo_crosswalk[['MAZ', 'COUNTY']],
            on='MAZ',
            how='left'
        )
        
        persons_with_county = pd.merge(
            self.synthetic_persons,
            self.geo_crosswalk[['MAZ', 'COUNTY']],
            on='MAZ',
            how='left'
        )
        
        # County rollups from results
        county_results = pd.merge(
            households_with_county.groupby('COUNTY').agg({
                'unique_hh_id': 'count'
            }).rename(columns={'unique_hh_id': 'households_result'}),
            persons_with_county.groupby('COUNTY').agg({
                'SERIALNO': 'count'
            }).rename(columns={'SERIALNO': 'persons_result'}),
            left_index=True, right_index=True
        )
        
        # County rollups from MAZ controls
        maz_with_county = pd.merge(self.maz_controls, self.geo_crosswalk[['MAZ', 'COUNTY']], on='MAZ')
        county_targets = maz_with_county.groupby('COUNTY').agg({
            'num_hh': 'sum',
            'total_pop': 'sum'
        }).rename(columns={'num_hh': 'households_target', 'total_pop': 'persons_target'})
        
        # Combine results and targets
        county_comparison = pd.merge(
            county_results,
            county_targets,
            left_index=True, right_index=True,
            how='outer'
        ).fillna(0)
        
        county_comparison['hh_diff'] = county_comparison['households_result'] - county_comparison['households_target']
        county_comparison['persons_diff'] = county_comparison['persons_result'] - county_comparison['persons_target']
        county_comparison['hh_pct_diff'] = np.where(
            county_comparison['households_target'] > 0,
            (county_comparison['hh_diff'] / county_comparison['households_target']) * 100,
            np.nan
        )
        county_comparison['persons_pct_diff'] = np.where(
            county_comparison['persons_target'] > 0,
            (county_comparison['persons_diff'] / county_comparison['persons_target']) * 100,
            np.nan
        )
        
        self.results['county_comparison'] = county_comparison
        
        logger.info(f"Completed county analysis for {len(county_comparison)} counties")
        
    def create_visualizations(self):
        """Create comprehensive visualizations"""
        logger.info("Creating visualizations...")
        
        # Initialize plotly figures list
        figures = []
        
        # 1. TAZ Control Analysis Charts
        if 'taz_analysis' in self.results:
            fig = self._create_taz_control_charts()
            figures.append(('TAZ Control Analysis', fig))
            
        # 2. MAZ Household Distribution Charts  
        if 'maz_comparison' in self.results:
            fig = self._create_maz_household_charts()
            figures.append(('MAZ Household Distribution', fig))
            
        # 3. County Rollup Charts
        if 'county_comparison' in self.results:
            fig = self._create_county_charts()
            figures.append(('County Rollup Analysis', fig))
            
        # 4. Overall Performance Dashboard
        fig = self._create_performance_dashboard()
        figures.append(('Performance Dashboard', fig))
        
        # Save all figures to HTML
        self._save_html_report(figures)
        
    def _create_taz_control_charts(self):
        """Create TAZ control analysis charts"""
        taz_analysis = self.results['taz_analysis']
        
        # Create subplots for different controls
        control_groups = {
            'Household Size': ['hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus'],
            'Household Income': ['hh_inc_30', 'hh_inc_30_60', 'hh_inc_60_100', 'hh_inc_100_plus'],
            'Household Workers': ['hh_wrks_0', 'hh_wrks_1', 'hh_wrks_2', 'hh_wrks_3_plus'],
            'Person Age': ['pers_age_00_19', 'pers_age_20_34', 'pers_age_35_64', 'pers_age_65_plus']
        }
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=list(control_groups.keys()),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        colors = px.colors.qualitative.Set1
        
        for i, (group_name, controls) in enumerate(control_groups.items()):
            row = i // 2 + 1
            col = i % 2 + 1
            
            for j, control in enumerate(controls):
                if control in taz_analysis:
                    analysis = taz_analysis[control]
                    
                    # Add bar for mean percentage difference
                    fig.add_trace(
                        go.Bar(
                            name=control.replace('_', ' ').title(),
                            x=[control.replace('_', ' ')],
                            y=[analysis['mean_pct_diff']],
                            marker_color=colors[j % len(colors)],
                            showlegend=(i == 0)  # Only show legend for first subplot
                        ),
                        row=row, col=col
                    )
        
        fig.update_layout(
            title_text="TAZ Control Analysis - Mean Percentage Differences",
            height=800,
            showlegend=True
        )
        
        return fig
        
    def _create_maz_household_charts(self):
        """Create MAZ household distribution charts"""
        maz_comparison = self.results['maz_comparison']
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Household Count: Target vs Result',
                'Percentage Difference Distribution', 
                'Absolute Difference Distribution',
                'Target vs Result Scatter'
            ]
        )
        
        # 1. Histogram of target vs result
        fig.add_trace(
            go.Histogram(
                x=maz_comparison['num_hh'],
                name='Target',
                opacity=0.7,
                nbinsx=50
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Histogram(
                x=maz_comparison['total_hh'],
                name='Result',
                opacity=0.7,
                nbinsx=50
            ),
            row=1, col=1
        )
        
        # 2. Percentage difference distribution
        valid_pct_diff = maz_comparison['num_hh_pct_diff'].dropna()
        fig.add_trace(
            go.Histogram(
                x=valid_pct_diff,
                name='% Difference',
                nbinsx=50
            ),
            row=1, col=2
        )
        
        # 3. Absolute difference distribution
        fig.add_trace(
            go.Histogram(
                x=maz_comparison['num_hh_diff'],
                name='Absolute Difference',
                nbinsx=50
            ),
            row=2, col=1
        )
        
        # 4. Scatter plot target vs result
        fig.add_trace(
            go.Scatter(
                x=maz_comparison['num_hh'],
                y=maz_comparison['total_hh'],
                mode='markers',
                name='MAZ Points',
                opacity=0.6
            ),
            row=2, col=2
        )
        
        # Add diagonal line for perfect match
        max_hh = max(maz_comparison['num_hh'].max(), maz_comparison['total_hh'].max())
        fig.add_trace(
            go.Scatter(
                x=[0, max_hh],
                y=[0, max_hh],
                mode='lines',
                name='Perfect Match',
                line=dict(dash='dash', color='red')
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title_text="MAZ Household Distribution Analysis",
            height=800
        )
        
        return fig
        
    def _create_county_charts(self):
        """Create county rollup charts"""
        county_comparison = self.results['county_comparison']
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'County Households: Target vs Result',
                'County Population: Target vs Result',
                'Household Percentage Differences by County',
                'Population Percentage Differences by County'
            ]
        )
        
        counties = county_comparison.index.tolist()
        
        # 1. Household comparison
        fig.add_trace(
            go.Bar(
                x=counties,
                y=county_comparison['households_target'],
                name='HH Target',
                opacity=0.7
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=counties,
                y=county_comparison['households_result'],
                name='HH Result',
                opacity=0.7
            ),
            row=1, col=1
        )
        
        # 2. Population comparison  
        fig.add_trace(
            go.Bar(
                x=counties,
                y=county_comparison['persons_target'],
                name='Pop Target',
                opacity=0.7
            ),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Bar(
                x=counties,
                y=county_comparison['persons_result'],
                name='Pop Result',
                opacity=0.7
            ),
            row=1, col=2
        )
        
        # 3. Household percentage differences
        fig.add_trace(
            go.Bar(
                x=counties,
                y=county_comparison['hh_pct_diff'],
                name='HH % Diff',
                marker_color='lightcoral'
            ),
            row=2, col=1
        )
        
        # 4. Population percentage differences
        fig.add_trace(
            go.Bar(
                x=counties,
                y=county_comparison['persons_pct_diff'],
                name='Pop % Diff',
                marker_color='lightblue'
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title_text="County-Level Rollup Analysis",
            height=800
        )
        
        return fig
        
    def _create_performance_dashboard(self):
        """Create overall performance dashboard"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'TAZ Controls - Mean Absolute % Error',
                'County Performance Summary',
                'MAZ Household Fit Quality',
                'Overall Statistics'
            ]
        )
        
        # 1. TAZ controls performance
        if 'taz_analysis' in self.results:
            taz_analysis = self.results['taz_analysis']
            controls = list(taz_analysis.keys())
            mean_abs_errors = [abs(taz_analysis[c]['mean_pct_diff']) for c in controls]
            
            fig.add_trace(
                go.Bar(
                    x=[c.replace('_', ' ') for c in controls],
                    y=mean_abs_errors,
                    name='Mean Abs % Error',
                    marker_color='lightgreen'
                ),
                row=1, col=1
            )
            
        # 2. County summary
        if 'county_comparison' in self.results:
            county_comparison = self.results['county_comparison']
            
            fig.add_trace(
                go.Scatter(
                    x=county_comparison['hh_pct_diff'],
                    y=county_comparison['persons_pct_diff'],
                    mode='markers+text',
                    text=county_comparison.index,
                    textposition='top center',
                    name='Counties',
                    marker=dict(size=10)
                ),
                row=1, col=2
            )
            
        # 3. MAZ household fit
        if 'maz_comparison' in self.results:
            maz_comparison = self.results['maz_comparison']
            
            # Create quality bins
            valid_maz = maz_comparison[maz_comparison['num_hh'] > 0]
            pct_diffs = valid_maz['num_hh_pct_diff'].abs()
            
            quality_bins = pd.cut(pct_diffs, bins=[0, 5, 10, 20, 50, float('inf')], 
                                labels=['Excellent (<5%)', 'Good (5-10%)', 'Fair (10-20%)', 
                                       'Poor (20-50%)', 'Very Poor (>50%)'])
            
            quality_counts = quality_bins.value_counts()
            
            fig.add_trace(
                go.Pie(
                    labels=quality_counts.index,
                    values=quality_counts.values,
                    name='MAZ Quality'
                ),
                row=2, col=1
            )
            
        # 4. Overall statistics table
        stats_text = self._generate_summary_stats()
        fig.add_trace(
            go.Scatter(
                x=[0.1], y=[0.9],
                mode='text',
                text=[stats_text],
                textfont=dict(size=12),
                showlegend=False
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title_text="PopulationSim Performance Dashboard",
            height=1000
        )
        
        return fig
        
    def _generate_summary_stats(self):
        """Generate summary statistics text"""
        stats = []
        
        if 'taz_analysis' in self.results:
            taz_analysis = self.results['taz_analysis']
            n_controls = len(taz_analysis)
            avg_error = np.mean([abs(v['mean_pct_diff']) for v in taz_analysis.values()])
            stats.append(f"TAZ Controls: {n_controls}")
            stats.append(f"Avg Error: {avg_error:.1f}%")
            
        if 'maz_analysis' in self.results:
            maz_analysis = self.results['maz_analysis']
            stats.append(f"MAZ Zones: {maz_analysis['total_maz_with_hh']:,}")
            stats.append(f"MAZ HH Error: {maz_analysis['mean_hh_pct_diff']:.1f}%")
            
        if 'county_comparison' in self.results:
            county_comparison = self.results['county_comparison']
            total_hh_error = abs(county_comparison['hh_pct_diff']).mean()
            total_pop_error = abs(county_comparison['persons_pct_diff']).mean()
            stats.append(f"County HH Error: {total_hh_error:.1f}%")
            stats.append(f"County Pop Error: {total_pop_error:.1f}%")
            
        return "<br>".join(stats)
        
    def _save_html_report(self, figures):
        """Save interactive HTML report"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PopulationSim Results Analysis</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; }}
                .chart-container {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>PopulationSim TM2 Results Analysis</h1>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        for title, fig in figures:
            html_content += f"""
            <div class="chart-container">
                <h2>{title}</h2>
                <div id="{title.lower().replace(' ', '_')}">{fig.to_html(include_plotlyjs=False, div_id=title.lower().replace(' ', '_'))}</div>
            </div>
            """
            
        html_content += """
        </body>
        </html>
        """
        
        output_file = Path("populationsim_analysis_charts.html")
        output_file.write_text(html_content)
        logger.info(f"Saved interactive charts to {output_file.absolute()}")
        
    def generate_text_report(self):
        """Generate detailed text report"""
        logger.info("Generating detailed text report...")
        
        report_lines = [
            "="*80,
            "POPULATIONSIM TM2 RESULTS ANALYSIS REPORT",
            "="*80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]
        
        # TAZ Analysis
        if 'taz_analysis' in self.results:
            report_lines.extend(self._format_taz_analysis())
            
        # MAZ Analysis  
        if 'maz_analysis' in self.results:
            report_lines.extend(self._format_maz_analysis())
            
        # County Analysis
        if 'county_comparison' in self.results:
            report_lines.extend(self._format_county_analysis())
            
        report_content = "\n".join(report_lines)
        
        output_file = Path("detailed_results_analysis.txt")
        output_file.write_text(report_content)
        logger.info(f"Saved detailed report to {output_file.absolute()}")
        
    def _format_taz_analysis(self):
        """Format TAZ analysis for text report"""
        taz_analysis = self.results['taz_analysis']
        
        lines = [
            "TAZ-LEVEL ANALYSIS",
            "="*50,
            "",
            f"Total TAZ controls analyzed: {len(taz_analysis)}",
            "",
            "Control Performance Summary:",
            "-"*30,
        ]
        
        for control, analysis in taz_analysis.items():
            lines.extend([
                f"",
                f"Control: {control.replace('_', ' ').title()}",
                f"  Mean % Difference: {analysis['mean_pct_diff']:.2f}%",
                f"  Std Dev % Diff: {analysis['std_pct_diff']:.2f}%",
                f"  Max Absolute Diff: {analysis['max_abs_diff']:.0f}",
                f"  Max Diff TAZ: {analysis['max_diff_taz']}",
                f"    Target: {analysis['max_diff_values']['target']:.0f}",
                f"    Result: {analysis['max_diff_values']['result']:.0f}",
                f"    Difference: {analysis['max_diff_values']['difference']:.0f}",
                f"  Total Target: {analysis['total_target']:.0f}",
                f"  Total Result: {analysis['total_result']:.0f}",
                f"  Total Difference: {analysis['total_diff']:.0f}",
            ])
            
        return lines
        
    def _format_maz_analysis(self):
        """Format MAZ analysis for text report"""
        maz_analysis = self.results['maz_analysis']
        
        lines = [
            "",
            "",
            "MAZ-LEVEL HOUSEHOLD ANALYSIS", 
            "="*50,
            "",
            f"Total MAZ zones with households: {maz_analysis['total_maz_with_hh']:,}",
            f"Mean household % difference: {maz_analysis['mean_hh_pct_diff']:.2f}%",
            f"Median household % difference: {maz_analysis['median_hh_pct_diff']:.2f}%", 
            f"Std Dev household % difference: {maz_analysis['std_hh_pct_diff']:.2f}%",
            f"Maximum absolute difference: {maz_analysis['max_abs_hh_diff']:.0f} households",
            f"MAZ with max difference: {maz_analysis['max_diff_maz']}",
            "",
            "Totals:",
            f"  Target households: {maz_analysis['total_hh_target']:,.0f}",
            f"  Result households: {maz_analysis['total_hh_result']:,.0f}",
            f"  Difference: {maz_analysis['total_hh_diff']:,.0f}",
        ]
        
        return lines
        
    def _format_county_analysis(self):
        """Format county analysis for text report"""
        county_comparison = self.results['county_comparison']
        
        lines = [
            "",
            "",
            "COUNTY-LEVEL ROLLUP ANALYSIS",
            "="*50,
            "",
            "County-by-County Results:",
            "-"*30,
        ]
        
        for county in county_comparison.index:
            row = county_comparison.loc[county]
            lines.extend([
                f"",
                f"County {county}:",
                f"  Households - Target: {row['households_target']:,.0f}, Result: {row['households_result']:,.0f}, Diff: {row['hh_diff']:,.0f} ({row['hh_pct_diff']:.1f}%)",
                f"  Population - Target: {row['persons_target']:,.0f}, Result: {row['persons_result']:,.0f}, Diff: {row['persons_diff']:,.0f} ({row['persons_pct_diff']:.1f}%)",
            ])
            
        # Regional totals
        total_hh_target = county_comparison['households_target'].sum()
        total_hh_result = county_comparison['households_result'].sum()
        total_pop_target = county_comparison['persons_target'].sum()
        total_pop_result = county_comparison['persons_result'].sum()
        
        lines.extend([
            "",
            "REGIONAL TOTALS:",
            "-"*20,
            f"Total Households - Target: {total_hh_target:,.0f}, Result: {total_hh_result:,.0f}, Diff: {total_hh_result-total_hh_target:,.0f}",
            f"Total Population - Target: {total_pop_target:,.0f}, Result: {total_pop_result:,.0f}, Diff: {total_pop_result-total_pop_target:,.0f}",
        ])
        
        return lines
        
    def save_csv_outputs(self):
        """Save detailed CSV outputs"""
        logger.info("Saving CSV output files...")
        
        if 'taz_comparison' in self.results:
            self.results['taz_comparison'].to_csv('taz_results_vs_targets.csv', index=False)
            logger.info("Saved taz_results_vs_targets.csv")
            
        if 'maz_comparison' in self.results:
            self.results['maz_comparison'].to_csv('maz_household_comparison.csv')
            logger.info("Saved maz_household_comparison.csv")
            
        if 'county_comparison' in self.results:
            self.results['county_comparison'].to_csv('county_rollup_comparison.csv')
            logger.info("Saved county_rollup_comparison.csv")
            
    def run_complete_analysis(self):
        """Run the complete analysis workflow"""
        logger.info("Starting complete PopulationSim results analysis...")
        
        try:
            self.load_data()
            self.analyze_taz_results()
            self.analyze_maz_households()
            self.analyze_county_rollups()
            self.create_visualizations()
            self.generate_text_report()
            self.save_csv_outputs()
            
            logger.info("="*60)
            logger.info("ANALYSIS COMPLETE!")
            logger.info("="*60)
            logger.info("Generated files:")
            logger.info("  - detailed_results_analysis.txt (comprehensive text report)")
            logger.info("  - populationsim_analysis_charts.html (interactive visualizations)")
            logger.info("  - taz_results_vs_targets.csv (detailed TAZ comparisons)")
            logger.info("  - maz_household_comparison.csv (MAZ household analysis)")
            logger.info("  - county_rollup_comparison.csv (county-level rollups)")
            logger.info("  - populationsim_analysis.log (execution log)")
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise

def main():
    """Main execution function"""
    print("PopulationSim Results Analysis")
    print("="*40)
    
    analyzer = PopulationSimAnalyzer()
    analyzer.run_complete_analysis()

if __name__ == "__main__":
    main()
