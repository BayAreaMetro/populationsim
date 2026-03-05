#!/usr/bin/env python3
"""
Synthetic Population Analysis Script

Reads final TM2 synthetic households and persons files and generates comprehensive
cross-tabulation summaries with proper value labels.

Outputs:
- Cross-tabulation summaries for key variable combinations
- Income distribution analysis
- Age by person type analysis
- Other demographic breakdowns

Usage: python analyze_syn_pop_model.py --year 2023
"""

import argparse
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add the parent directory to path to import unified config
sys.path.append(str(Path(__file__).parent.parent))
from tm2_config import TM2Config


class SyntheticPopulationAnalyzer:
    def __init__(self, year=2023, model_type="TM2"):
        self.config = TM2Config(year=year, model_type=model_type)
        self.year = year
        self.model_type = model_type
        
        # Get value labels from config
        self.value_labels = self.config.VALUE_LABELS
    
    def _create_income_bins(self, income_series):
        """Create income bins in 2010 dollars"""
        bins = [0, 50000, 100000, 150000, 200000, 250000, float('inf')]
        labels = ['$0-50K', '$50K-100K', '$100K-150K', '$150K-200K', '$200K-250K', '$250K+']
        return pd.cut(income_series, bins=bins, labels=labels, include_lowest=True)
    
    def _create_age_bins(self, age_series):
        """Create standard age groups"""
        bins = [0, 18, 35, 65, 100]
        labels = ['0-17', '18-34', '35-64', '65+']
        return pd.cut(age_series, bins=bins, labels=labels, include_lowest=True, right=False)
    
    def load_data(self):
        """Load the final synthetic population files"""
        # Get file paths from config
        households_file = self.config.POPSIM_OUTPUT_DIR / f"households_{self.year}_tm2.csv"
        persons_file = self.config.POPSIM_OUTPUT_DIR / f"persons_{self.year}_tm2.csv"
        
        print(f"Loading households from: {households_file}")
        print(f"Loading persons from: {persons_file}")
        
        self.households_df = pd.read_csv(households_file)
        self.persons_df = pd.read_csv(persons_file)
        
        print(f"Loaded {len(self.households_df):,} households")
        print(f"Loaded {len(self.persons_df):,} persons")
        
        return self.households_df, self.persons_df
    
    def apply_labels(self, df, column, value_col='value'):
        """Apply value labels to a dataframe column"""
        if column in self.value_labels:
            df[f'{column}_label'] = df[column].map(self.value_labels[column]).fillna(f'Unknown ({df[column]})')
        return df
    
    def create_crosstab(self, df, row_var, col_var, add_labels=True):
        """Create a cross-tabulation with optional labels"""
        crosstab = pd.crosstab(df[row_var], df[col_var], margins=True)
        
        if add_labels:
            # Add labels for row variable
            if row_var in self.value_labels:
                row_labels = pd.Series(crosstab.index).map(self.value_labels[row_var])
                crosstab.index = [f"{idx} ({label})" if pd.notna(label) else str(idx) 
                                for idx, label in zip(crosstab.index, row_labels)]
            
            # Add labels for column variable  
            if col_var in self.value_labels:
                col_labels = pd.Series(crosstab.columns).map(self.value_labels[col_var])
                crosstab.columns = [f"{col} ({label})" if pd.notna(label) else str(col)
                                  for col, label in zip(crosstab.columns, col_labels)]
        
        return crosstab
    
    def add_binned_variables(self):
        """Add binned versions of continuous variables"""
        # Add income bins to households
        self.households_df['HHINCADJ_binned'] = self._create_income_bins(self.households_df['HHINCADJ'])
        
        # Add age bins to persons
        self.persons_df['AGEP_binned'] = self._create_age_bins(self.persons_df['AGEP'])
        
        # Add household size bins
        self.households_df['NP_binned'] = pd.cut(
            self.households_df['NP'], 
            bins=[0, 1, 2, 3, 4, float('inf')], 
            labels=['1 person', '2 persons', '3 persons', '4 persons', '5+ persons'],
            include_lowest=True
        )
        
        # Add hours worked bins
        self.persons_df['WKHP_binned'] = pd.cut(
            self.persons_df['WKHP'].replace(-9, np.nan),
            bins=[0, 20, 35, 40, float('inf')],
            labels=['Part-time (<20hrs)', 'Part-time (20-34hrs)', 'Full-time (35-39hrs)', 'Full-time (40+hrs)'],
            include_lowest=True
        )
        
        # Update value labels for binned variables
        self.value_labels.update({
            'HHINCADJ_binned': {str(label): str(label) for label in self.households_df['HHINCADJ_binned'].cat.categories},
            'AGEP_binned': {str(label): str(label) for label in self.persons_df['AGEP_binned'].cat.categories},
            'NP_binned': {str(label): str(label) for label in self.households_df['NP_binned'].cat.categories},
            'WKHP_binned': {str(label): str(label) for label in self.persons_df['WKHP_binned'].cat.categories if pd.notna(label)}
        })
    
    def generate_all_crosstabs(self):
        """Generate all pairwise cross-tabulations"""
        results = {}
        
        # Define meaningful variables for cross-tabulation (excluding TAZ/MAZ per user request)
        household_vars = ['MTCCountyID', 'HHINCADJ_binned', 'NWRKRS_ESR', 'VEH', 'TEN', 'NP_binned', 'HHT', 'BLD', 'TYPE']
        person_vars = ['AGEP_binned', 'SEX', 'SCHL', 'OCCP', 'WKHP_binned', 'WKW', 'EMPLOYED', 'ESR', 'SCHG', 'hhgqtype', 'person_type']
        
        # Household cross-tabs
        print("Generating household cross-tabulations...")
        for i, var1 in enumerate(household_vars):
            for var2 in household_vars[i+1:]:
                if var1 in self.households_df.columns and var2 in self.households_df.columns:
                    crosstab = self.create_crosstab(self.households_df, var1, var2)
                    results[f"HH_{var1}_by_{var2}"] = crosstab
                    print(f"  Generated: {var1} × {var2}")
        
        # Person cross-tabs
        print("Generating person cross-tabulations...")
        for i, var1 in enumerate(person_vars):
            for var2 in person_vars[i+1:]:
                if var1 in self.persons_df.columns and var2 in self.persons_df.columns:
                    crosstab = self.create_crosstab(self.persons_df, var1, var2)
                    results[f"PERS_{var1}_by_{var2}"] = crosstab
                    print(f"  Generated: {var1} × {var2}")
        
        return results
    
    def generate_html_report(self, crosstabs, output_file):
        """Generate comprehensive HTML report"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Synthetic Population Analysis Report - {self.year}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .section {{
                    background-color: white;
                    margin: 20px 0;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .crosstab {{
                    margin: 20px 0;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 10px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: right;
                }}
                th {{
                    background-color: #f2f2f2;
                    font-weight: bold;
                }}
                .table-title {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin: 20px 0 10px 0;
                }}
                .summary-stats {{
                    background-color: #ecf0f1;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
                .toc {{
                    background-color: #ecf0f1;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .toc a {{
                    display: block;
                    margin: 5px 0;
                    text-decoration: none;
                    color: #2980b9;
                }}
                .toc a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Synthetic Population Analysis Report</h1>
                <p>Model Year: {self.year} | Model Type: {self.model_type}</p>
                <p>Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>Summary Statistics</h2>
                <div class="summary-stats">
                    <p><strong>Total Households:</strong> {len(self.households_df):,}</p>
                    <p><strong>Total Persons:</strong> {len(self.persons_df):,}</p>
                    <p><strong>Average Household Size:</strong> {self.persons_df.groupby('HHID').size().mean():.2f}</p>
                </div>
            </div>
        """
        
        # Table of Contents
        html_content += '<div class="section"><h2>Table of Contents</h2><div class="toc">'
        for table_name in sorted(crosstabs.keys()):
            clean_name = table_name.replace('_', ' ').title()
            html_content += f'<a href="#{table_name}">{clean_name}</a>'
        html_content += '</div></div>'
        
        # Add each cross-tabulation
        for table_name, crosstab in crosstabs.items():
            html_content += f'<div class="section">'
            html_content += f'<div class="table-title" id="{table_name}">{table_name.replace("_", " ").title()}</div>'
            html_content += crosstab.to_html(classes='crosstab')
            html_content += '</div>'
        
        html_content += """
        </body>
        </html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML report written to: {output_file}")
    
    def run_analysis(self):
        """Run the complete analysis"""
        print("Starting synthetic population analysis...")
        
        # Load data
        self.load_data()
        
        # Add binned variables
        print("Creating binned variables...")
        self.add_binned_variables()
        
        # Generate all cross-tabulations
        print("Generating cross-tabulations...")
        crosstabs = self.generate_all_crosstabs()
        
        # Generate HTML report
        output_file = self.config.OUTPUT_DIR / f"synthetic_population_analysis_{self.year}.html"
        print(f"Generating HTML report...")
        self.generate_html_report(crosstabs, output_file)
        
        print(f"Analysis complete! Generated {len(crosstabs)} cross-tabulations.")
        return output_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze synthetic population model outputs')
    parser.add_argument('--year', type=int, default=2023, help='Model year')
    parser.add_argument('--model_type', type=str, default='TM2', help='Model type')
    parser.add_argument('--output_dir', type=str, help='Output directory for analysis files')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = SyntheticPopulationAnalyzer(year=args.year, model_type=args.model_type)
    
    # Run complete analysis
    try:
        output_file = analyzer.run_analysis()
        print(f"\nAnalysis completed successfully!")
        print(f"Report available at: {output_file}")
    except Exception as e:
        print(f"ERROR during analysis: {e}")
        raise


