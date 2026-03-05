#!/usr/bin/env python3
"""
Marginal Controls Visualization Generator

This script creates comprehensive visual outputs of marginal controls by MAZ, TAZ, and County.
Generates maps, charts, and interactive dashboards showing demographic control distributions.

Author: PopulationSim Bay Area Team
Date: October 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import geopandas as gpd
import warnings
import os
import sys
from pathlib import Path

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Set style for matplotlib
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class MarginalControlsVisualizer:
    """Comprehensive visualization generator for marginal controls data."""
    
    def __init__(self, data_dir="output_2023/populationsim_working_dir/data", 
                 output_dir="docs/visualizations/marginal_controls"):
        """
        Initialize the visualizer with data and output directories.
        
        Args:
            data_dir (str): Directory containing marginal control CSV files
            output_dir (str): Directory to save generated visualizations
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize data containers
        self.maz_data = None
        self.taz_data = None 
        self.county_data = None
        self.geo_crosswalk = None
        
        # Define human-readable label mappings
        self.income_labels = {
            'inc_lt_20k': 'Less than $20K',
            'inc_20k_45k': '$20K - $45K',
            'inc_45k_60k': '$45K - $60K',
            'inc_60k_75k': '$60K - $75K',
            'inc_75k_100k': '$75K - $100K',
            'inc_100k_150k': '$100K - $150K',
            'inc_150k_200k': '$150K - $200K',
            'inc_200k_plus': '$200K+'
        }
        
        self.age_labels = {
            'pers_age_00_19': 'Ages 0-19',
            'pers_age_20_34': 'Ages 20-34',
            'pers_age_35_64': 'Ages 35-64',
            'pers_age_65_plus': 'Ages 65+'
        }
        
        self.worker_labels = {
            'hh_wrks_0': '0 Workers',
            'hh_wrks_1': '1 Worker',
            'hh_wrks_2': '2 Workers',
            'hh_wrks_3_plus': '3+ Workers'
        }
        
        self.size_labels = {
            'hh_size_1': '1 Person',
            'hh_size_2': '2 Persons',
            'hh_size_3': '3 Persons',
            'hh_size_4': '4 Persons',
            'hh_size_5': '5 Persons',
            'hh_size_6_plus': '6+ Persons'
        }
        
        self.occupation_labels = {
            'pers_occ_management': 'Management',
            'pers_occ_professional': 'Professional',
            'pers_occ_services': 'Services',
            'pers_occ_retail': 'Retail',
            'pers_occ_manual_military': 'Manual/Military'
        }
        
        self.county_names = {
            1: 'Alameda', 2: 'Contra Costa', 3: 'Santa Clara', 4: 'San Francisco',
            5: 'San Mateo', 6: 'Solano', 7: 'Napa', 8: 'Sonoma', 9: 'Marin'
        }
        
        # Load data
        self._load_marginal_data()
        self._load_geographic_data()
        
    def _load_marginal_data(self):
        """Load marginal control data files."""
        print("Loading marginal controls data...")
        
        try:
            # Load MAZ marginals
            maz_file = self.data_dir / "maz_marginals_hhgq.csv"
            if maz_file.exists():
                self.maz_data = pd.read_csv(maz_file)
                print(f"✓ Loaded MAZ data: {len(self.maz_data)} zones")
            else:
                print(f"⚠ MAZ marginals file not found: {maz_file}")
                
            # Load TAZ marginals  
            taz_file = self.data_dir / "taz_marginals_hhgq.csv"
            if taz_file.exists():
                self.taz_data = pd.read_csv(taz_file)
                print(f"✓ Loaded TAZ data: {len(self.taz_data)} zones")
            else:
                print(f"⚠ TAZ marginals file not found: {taz_file}")
                
            # Load County marginals
            county_file = self.data_dir / "county_marginals.csv"
            if county_file.exists():
                self.county_data = pd.read_csv(county_file)
                print(f"✓ Loaded County data: {len(self.county_data)} counties")
            else:
                print(f"⚠ County marginals file not found: {county_file}")
                
        except Exception as e:
            print(f"Error loading marginal data: {e}")
            
    def _load_geographic_data(self):
        """Load geographic crosswalk and boundary data if available."""
        print("Loading geographic crosswalk data...")
        
        try:
            # Try to load crosswalk
            crosswalk_paths = [
                self.data_dir / "../data/geo_cross_walk_tm2_maz.csv",
                "geo_cross_walk_tm2_maz.csv",
                "mazs_tazs_all_geog.csv"
            ]
            
            for path in crosswalk_paths:
                if Path(path).exists():
                    self.geo_crosswalk = pd.read_csv(path)
                    print(f"✓ Loaded geographic crosswalk: {path}")
                    break
            else:
                print("⚠ No geographic crosswalk found - spatial analysis will be limited")
                
        except Exception as e:
            print(f"Error loading geographic data: {e}")
    
    def create_maz_visualizations(self):
        """Create visualizations for MAZ-level marginal controls."""
        if self.maz_data is None:
            print("⚠ No MAZ data available for visualization")
            return
            
        print("Creating MAZ visualizations...")
        
        # 1. MAZ Household Distribution Map/Chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Histogram of household counts
        ax1.hist(self.maz_data['numhh_gq'], bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.set_xlabel('Households per MAZ')
        ax1.set_ylabel('Number of MAZs')
        ax1.set_title('Distribution of Households by MAZ')
        ax1.grid(True, alpha=0.3)
        
        # Summary statistics
        stats_text = f"""Statistics:
Total MAZs: {len(self.maz_data):,}
Total HH: {self.maz_data['numhh_gq'].sum():,.0f}
Mean HH/MAZ: {self.maz_data['numhh_gq'].mean():.1f}
Median HH/MAZ: {self.maz_data['numhh_gq'].median():.1f}
Max HH/MAZ: {self.maz_data['numhh_gq'].max():.0f}"""
        
        ax2.text(0.1, 0.9, stats_text, transform=ax2.transAxes, fontsize=12,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightgray'))
        ax2.axis('off')
        ax2.set_title('MAZ Household Summary Statistics')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / "maz_household_distribution.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Group Quarters Analysis
        if 'gq_type_univ' in self.maz_data.columns and 'gq_type_noninst' in self.maz_data.columns:
            gq_summary = pd.DataFrame({
                'University GQ': [self.maz_data['gq_type_univ'].sum()],
                'Non-institutional GQ': [self.maz_data['gq_type_noninst'].sum()],
                'Regular Households': [self.maz_data['numhh_gq'].sum()]
            })
            
            fig, ax = plt.subplots(figsize=(10, 6))
            gq_summary.T.plot(kind='bar', ax=ax, color=['coral', 'lightgreen', 'skyblue'])
            ax.set_title('MAZ-Level Housing Unit Types')
            ax.set_ylabel('Total Units')
            ax.set_xlabel('Unit Type')
            ax.legend().remove()
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(self.output_dir / "maz_group_quarters_summary.png", dpi=300, bbox_inches='tight')
            plt.close()
    
    def create_taz_visualizations(self):
        """Create visualizations for TAZ-level marginal controls."""
        if self.taz_data is None:
            print("⚠ No TAZ data available for visualization")
            return
            
        print("Creating TAZ visualizations...")
        
        # 1. Income Distribution Analysis
        income_cols = [col for col in self.taz_data.columns if 'inc_' in col]
        if income_cols:
            income_data = self.taz_data[income_cols].sum()
            # Apply human-readable labels
            income_data.index = [self.income_labels.get(col, col) for col in income_data.index]
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
            
            # Income distribution pie chart
            colors = plt.cm.Set3(np.linspace(0, 1, len(income_cols)))
            wedges, texts, autotexts = ax1.pie(income_data.values, labels=income_data.index, 
                                              autopct='%1.1f%%', colors=colors, startangle=90)
            ax1.set_title('Regional Household Income Distribution\n(All TAZs Combined)')
            
            # Income distribution by TAZ (top 10 TAZs)
            taz_income_totals = self.taz_data[income_cols].sum(axis=1)
            top_taz_indices = taz_income_totals.nlargest(10).index
            top_taz_data = self.taz_data.loc[top_taz_indices, ['TAZ_NODE'] + income_cols]
            
            # Create readable column names for plotting
            readable_income_cols = [self.income_labels.get(col, col) for col in income_cols]
            plot_data = top_taz_data.set_index('TAZ_NODE')[income_cols]
            plot_data.columns = readable_income_cols
            
            # Stacked bar chart for top TAZs
            plot_data.plot(kind='bar', stacked=True, ax=ax2, colormap='Set3')
            ax2.set_title('Income Distribution - Top 10 TAZs by Total Households')
            ax2.set_xlabel('TAZ ID')
            ax2.set_ylabel('Number of Households')
            ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            plt.tight_layout()
            plt.savefig(self.output_dir / "taz_income_distribution.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        # 2. Household Size Distribution
        size_cols = [col for col in self.taz_data.columns if 'hh_size_' in col and col != 'hh_size_1_gq']
        if size_cols:
            size_data = self.taz_data[size_cols].sum()
            # Apply human-readable labels
            readable_labels = [self.size_labels.get(col, col) for col in size_data.index]
            
            fig, ax = plt.subplots(figsize=(12, 8))
            bars = ax.bar(readable_labels, size_data.values, color='lightcoral', alpha=0.8)
            ax.set_xlabel('Household Size')
            ax.set_ylabel('Number of Households')
            ax.set_title('Regional Household Size Distribution')
            ax.tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for bar, value in zip(bars, size_data.values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'{int(value):,}', ha='center', va='bottom')
            
            plt.tight_layout()
            plt.savefig(self.output_dir / "taz_household_size_distribution.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        # 3. Worker Distribution
        worker_cols = [col for col in self.taz_data.columns if 'hh_wrks_' in col]
        if worker_cols:
            worker_data = self.taz_data[worker_cols].sum()
            # Apply human-readable labels
            readable_labels = [self.worker_labels.get(col, col) for col in worker_data.index]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            wedges, texts, autotexts = ax.pie(worker_data.values, labels=readable_labels, 
                                             autopct='%1.1f%%', startangle=90, colors=plt.cm.Pastel1.colors)
            ax.set_title('Regional Distribution of Households by Number of Workers')
            
            plt.savefig(self.output_dir / "taz_worker_distribution.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        # 4. Age Distribution
        age_cols = [col for col in self.taz_data.columns if 'pers_age_' in col]
        if age_cols:
            age_data = self.taz_data[age_cols].sum()
            # Apply human-readable labels
            readable_labels = [self.age_labels.get(col, col) for col in age_data.index]
            
            fig, ax = plt.subplots(figsize=(12, 6))
            bars = ax.bar(readable_labels, age_data.values, color='lightsteelblue', alpha=0.8)
            ax.set_xlabel('Age Group')
            ax.set_ylabel('Number of Persons')
            ax.set_title('Regional Age Distribution')
            ax.tick_params(axis='x', rotation=45)
            
            # Add value labels
            for bar, value in zip(bars, age_data.values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'{int(value):,}', ha='center', va='bottom')
            
            plt.tight_layout()
            plt.savefig(self.output_dir / "taz_age_distribution.png", dpi=300, bbox_inches='tight')
            plt.close()
    
    def create_county_visualizations(self):
        """Create visualizations for County-level marginal controls."""
        if self.county_data is None:
            print("⚠ No County data available for visualization")
            return
            
        print("Creating County visualizations...")
        
        # Add county names to data
        self.county_data['County_Name'] = self.county_data['COUNTY'].map(self.county_names)
        
        # 1. Occupation Distribution by County
        occ_cols = [col for col in self.county_data.columns if 'pers_occ_' in col]
        if occ_cols:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
            
            # Prepare data with readable labels
            county_occ_data = self.county_data.set_index('County_Name')[occ_cols]
            # Create readable column names
            readable_occ_cols = [self.occupation_labels.get(col, col) for col in occ_cols]
            county_occ_data.columns = readable_occ_cols
            
            # Stacked bar chart
            county_occ_data.plot(kind='bar', stacked=True, ax=ax1, colormap='Set2')
            ax1.set_title('Employment by Occupation and County (Total Numbers)')
            ax1.set_xlabel('County')
            ax1.set_ylabel('Number of Employed Persons')
            ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax1.tick_params(axis='x', rotation=45)
            
            # Grouped bar chart (normalized to 100%)
            county_occ_pct = county_occ_data.div(county_occ_data.sum(axis=1), axis=0) * 100
            county_occ_pct.plot(kind='bar', ax=ax2, colormap='Set2')
            ax2.set_title('Employment by Occupation and County (Percentage Distribution)')
            ax2.set_xlabel('County')
            ax2.set_ylabel('Percentage of Employed Persons')
            ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax2.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            plt.savefig(self.output_dir / "county_occupation_distribution.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        # 2. County Totals Comparison
        if occ_cols:
            county_totals = self.county_data.set_index('County_Name')[occ_cols].sum(axis=1)
            
            fig, ax = plt.subplots(figsize=(12, 8))
            bars = ax.bar(county_totals.index, county_totals.values, color='lightgreen', alpha=0.8)
            ax.set_title('Total Employed Persons by County')
            ax.set_xlabel('County')
            ax.set_ylabel('Number of Employed Persons')
            ax.tick_params(axis='x', rotation=45)
            
            # Add value labels
            for bar, value in zip(bars, county_totals.values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'{int(value):,}', ha='center', va='bottom', rotation=90)
            
            plt.tight_layout()
            plt.savefig(self.output_dir / "county_employment_totals.png", dpi=300, bbox_inches='tight')
            plt.close()
    
    def create_comprehensive_powerpoint_image(self):
        """Create three separate landscape-oriented images for PowerPoint presentation."""
        print("Creating comprehensive PowerPoint images...")
        
        # 1. MAZ Controls Image (Landscape)
        self._create_maz_controls_image()
        
        # 2. TAZ Controls Image (Landscape)
        self._create_taz_controls_image()
        
        # 3. County Controls Image (Landscape)
        self._create_county_controls_image()
        
        print("✓ All three PowerPoint images saved")
    
    def _create_maz_controls_image(self):
        """Create MAZ controls landscape image."""
        fig = plt.figure(figsize=(16, 10))  # Landscape orientation
        
        # Create layout with more space
        gs = fig.add_gridspec(1, 2, width_ratios=[1, 1], 
                             hspace=0.4, wspace=0.4)
        
        # MAZ Categories (left side)
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.axis('off')
        maz_categories = [
            "Housing Unit Categories:",
            "",
            "• Total Households (numhh_gq)",
            "• University Group Quarters (gq_type_univ)", 
            "• Non-institutional Group Quarters (gq_type_noninst)",
            "",
            "Geographic Coverage:",
            "• 39,586 MAZ zones across Bay Area",
            "• Finest level of geographic detail",
            "• Building block for TAZ aggregation"
        ]
        maz_text = "\n".join(maz_categories)
        ax1.text(0.05, 0.85, maz_text, transform=ax1.transAxes, fontsize=18,
                verticalalignment='top', bbox=dict(boxstyle='round,pad=1.0', facecolor='lightblue', alpha=0.8))
        
        # MAZ Data Sources (right side)
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.axis('off')
        maz_sources = [
            "Data Sources & Methodology:",
            "",
            "Primary Sources:",
            "• 2020 Census (block level counts)",
            "• 2020/2010 NHGIS interpolation",
            "• Geographic allocation methods",
            "",
            "Processing Steps:",
            "• Block-to-MAZ aggregation",
            "• Group quarters identification",
            "• Institutional vs. non-institutional classification",
            "• Quality validation against regional totals",
            "",
            "Update Frequency:",
            "• Census: Every 10 years",
            "• Interpolation: As needed"
        ]
        maz_source_text = "\n".join(maz_sources)
        ax2.text(0.05, 0.85, maz_source_text, transform=ax2.transAxes, fontsize=16,
                verticalalignment='top', bbox=dict(boxstyle='round,pad=1.0', facecolor='lightgray', alpha=0.9))
        
        # Title
        fig.suptitle('MAZ (Micro Analysis Zone) Controls - Data Categories & Sources', 
                    fontsize=24, fontweight='bold', y=0.95)
        
        # Subtitle
        subtitle = 'Finest Geographic Level: 39,586 zones • Housing Units & Group Quarters • 2020/2010 Interpolation'
        fig.text(0.5, 0.88, subtitle, fontsize=16, ha='center', style='italic')
        
        plt.savefig(self.output_dir / "maz_controls_powerpoint.png", 
                   dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close()
        print(f"✓ MAZ controls image saved: {self.output_dir}/maz_controls_powerpoint.png")
    
    def _create_taz_controls_image(self):
        """Create TAZ controls landscape image."""
        fig = plt.figure(figsize=(16, 12))  # Landscape orientation, taller for more content
        
        # Create layout - 3 columns, 2 rows with more spacing
        gs = fig.add_gridspec(2, 3, height_ratios=[1, 1], width_ratios=[1, 1, 1], 
                             hspace=0.4, wspace=0.3)
        
        # Income Categories (top left)
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.axis('off')
        income_categories = ["Households by Income:"] + [f"• {label}" for label in self.income_labels.values()]
        income_text = "\n".join(income_categories)
        ax1.text(0.05, 0.9, income_text, transform=ax1.transAxes, fontsize=14,
                verticalalignment='top', bbox=dict(boxstyle='round,pad=0.6', facecolor='lightgreen', alpha=0.8))
        ax1.set_title('Income Distribution', fontsize=16, fontweight='bold')
        
        # Age Categories (top center)
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.axis('off')
        age_categories = ["Persons by Age Group:"] + [f"• {label}" for label in self.age_labels.values()]
        age_text = "\n".join(age_categories)
        ax2.text(0.05, 0.9, age_text, transform=ax2.transAxes, fontsize=14,
                verticalalignment='top', bbox=dict(boxstyle='round,pad=0.6', facecolor='lightyellow', alpha=0.8))
        ax2.set_title('Age Distribution', fontsize=16, fontweight='bold')
        
        # Household Size Categories (top right)
        ax3 = fig.add_subplot(gs[0, 2])
        ax3.axis('off')
        size_categories = ["Households by Size:"] + [f"• {label}" for label in self.size_labels.values()]
        size_text = "\n".join(size_categories)
        ax3.text(0.05, 0.9, size_text, transform=ax3.transAxes, fontsize=14,
                verticalalignment='top', bbox=dict(boxstyle='round,pad=0.6', facecolor='lightcoral', alpha=0.8))
        ax3.set_title('Household Size', fontsize=16, fontweight='bold')
        
        # Worker Categories (bottom left)
        ax4 = fig.add_subplot(gs[1, 0])
        ax4.axis('off')
        worker_categories = ["Households by Workers:"] + [f"• {label}" for label in self.worker_labels.values()]
        worker_text = "\n".join(worker_categories)
        ax4.text(0.05, 0.9, worker_text, transform=ax4.transAxes, fontsize=14,
                verticalalignment='top', bbox=dict(boxstyle='round,pad=0.6', facecolor='lightsteelblue', alpha=0.8))
        ax4.set_title('Worker Distribution', fontsize=16, fontweight='bold')
        
        # Additional Categories (bottom center)
        ax5 = fig.add_subplot(gs[1, 1])
        ax5.axis('off')
        additional_categories = [
            "Additional Categories:",
            "• Households with Children (Yes/No)",
            "• Single-Person Group Quarters",
            "",
            "Geographic Coverage:",
            "• 4,734 TAZ zones",
            "• Aggregated from MAZ level",
            "• Transportation modeling units"
        ]
        additional_text = "\n".join(additional_categories)
        ax5.text(0.05, 0.9, additional_text, transform=ax5.transAxes, fontsize=14,
                verticalalignment='top', bbox=dict(boxstyle='round,pad=0.6', facecolor='wheat', alpha=0.8))
        ax5.set_title('Additional Controls', fontsize=16, fontweight='bold')
        
        # Data Sources (bottom right)
        ax6 = fig.add_subplot(gs[1, 2])
        ax6.axis('off')
        taz_sources = [
            "Data Sources:",
            "• 2020/2010 NHGIS interpolation",
            "• Census block group mapping",
            "• Geographic allocation methods",
            "",
            "Processing:",
            "• Spatial disaggregation",
            "• Control harmonization", 
            "• Quality validation",
            "• Cross-level consistency"
        ]
        taz_source_text = "\n".join(taz_sources)
        ax6.text(0.05, 0.9, taz_source_text, transform=ax6.transAxes, fontsize=14,
                verticalalignment='top', bbox=dict(boxstyle='round,pad=0.6', facecolor='lightgray', alpha=0.9))
        ax6.set_title('Data Sources', fontsize=16, fontweight='bold')
        
        # Title
        fig.suptitle('TAZ (Traffic Analysis Zone) Controls - Demographic Categories & Sources', 
                    fontsize=22, fontweight='bold', y=0.95)
        
        # Subtitle
        subtitle = 'Transportation Level: 4,734 zones • Household & Person Demographics • 2020/2010 Interpolation'
        fig.text(0.5, 0.88, subtitle, fontsize=16, ha='center', style='italic')
        
        plt.savefig(self.output_dir / "taz_controls_powerpoint.png", 
                   dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close()
        print(f"✓ TAZ controls image saved: {self.output_dir}/taz_controls_powerpoint.png")
    
    def _create_county_controls_image(self):
        """Create County controls landscape image."""
        fig = plt.figure(figsize=(16, 10))  # Landscape orientation
        
        # Create layout with more spacing
        gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], width_ratios=[1, 1], 
                             hspace=0.4, wspace=0.4)
        
        # Counties List (top left)
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.axis('off')
        county_list = ["Bay Area Counties:"] + [f"• {name}" for name in self.county_names.values()]
        county_text = "\n".join(county_list)
        ax1.text(0.05, 0.85, county_text, transform=ax1.transAxes, fontsize=16,
                verticalalignment='top', bbox=dict(boxstyle='round,pad=0.6', facecolor='lightpink', alpha=0.8))
        ax1.set_title('Geographic Coverage', fontsize=18, fontweight='bold')
        
        # Occupation Categories (top right)
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.axis('off')
        occupation_categories = ["Persons by Occupation:"] + [f"• {label}" for label in self.occupation_labels.values()]
        occupation_text = "\n".join(occupation_categories)
        ax2.text(0.05, 0.85, occupation_text, transform=ax2.transAxes, fontsize=16,
                verticalalignment='top', bbox=dict(boxstyle='round,pad=0.6', facecolor='lavender', alpha=0.8))
        ax2.set_title('Employment Categories', fontsize=18, fontweight='bold')
        
        # Data Sources (bottom left)
        ax3 = fig.add_subplot(gs[1, 0])
        ax3.axis('off')
        county_sources = [
            "Data Sources:",
            "• 2020/2010 NHGIS interpolation",
            "• SOCP occupation codes",
            "• County-level aggregation",
            "• Census geographic boundaries",
            "• FIPS county definitions",
            "",
            "Geographic Framework:",
            "• 9-county Bay Area region",
            "• Standard metropolitan area",
            "• Regional planning boundaries"
        ]
        county_source_text = "\n".join(county_sources)
        ax3.text(0.05, 0.85, county_source_text, transform=ax3.transAxes, fontsize=16,
                verticalalignment='top', bbox=dict(boxstyle='round,pad=0.6', facecolor='lightgray', alpha=0.9))
        ax3.set_title('Data Sources & Geography', fontsize=18, fontweight='bold')
        
        # Processing Details (bottom right)
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.axis('off')
        processing_details = [
            "Processing Methodology:",
            "",
            "Employment Classification:",
            "• SOCP to 5-category mapping",
            "• Professional vs. service workers",
            "• Management hierarchy",
            "• Manual labor & military",
            "",
            "Quality Assurance:",
            "• Regional employment totals",
            "• Industry sector validation", 
            "• Cross-county consistency",
            "• Labor force participation rates"
        ]
        processing_text = "\n".join(processing_details)
        ax4.text(0.05, 0.85, processing_text, transform=ax4.transAxes, fontsize=16,
                verticalalignment='top', bbox=dict(boxstyle='round,pad=0.6', facecolor='lightcyan', alpha=0.8))
        ax4.set_title('Processing & Validation', fontsize=18, fontweight='bold')
        
        # Title
        fig.suptitle('County Level Controls - Employment Categories & Regional Framework', 
                    fontsize=24, fontweight='bold', y=0.95)
        
        # Subtitle
        subtitle = 'Regional Level: 9 counties • Employment by Occupation • 2020/2010 Interpolation + SOCP codes'
        fig.text(0.5, 0.88, subtitle, fontsize=16, ha='center', style='italic')
        
        plt.savefig(self.output_dir / "county_controls_powerpoint.png", 
                   dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close()
        print(f"✓ County controls image saved: {self.output_dir}/county_controls_powerpoint.png")
    
    def _generate_summary_stats(self):
        """Generate summary statistics text."""
        stats = []
        
        if self.maz_data is not None:
            total_maz = len(self.maz_data)
            total_hh_maz = self.maz_data['numhh_gq'].sum()
            stats.append(f"MAZ Zones: {total_maz:,}")
            stats.append(f"Total HH (MAZ): {total_hh_maz:,.0f}")
        
        if self.taz_data is not None:
            total_taz = len(self.taz_data)
            stats.append(f"TAZ Zones: {total_taz:,}")
            
            # Calculate total persons from age groups
            age_cols = [col for col in self.taz_data.columns if 'pers_age_' in col]
            if age_cols:
                total_persons = self.taz_data[age_cols].sum().sum()
                stats.append(f"Total Persons: {total_persons:,.0f}")
        
        if self.county_data is not None:
            total_counties = len(self.county_data)
            occ_cols = [col for col in self.county_data.columns if 'pers_occ_' in col]
            if occ_cols:
                total_employed = self.county_data[occ_cols].sum().sum()
                stats.append(f"Counties: {total_counties}")
                stats.append(f"Total Employed: {total_employed:,.0f}")
        
        return "<br>".join(stats)
    
    def create_summary_report(self):
        """Create a comprehensive summary report."""
        print("Creating summary report...")
        
        report_content = f"""
# Marginal Controls Visualization Summary Report

**Generated**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## Data Overview

"""
        
        if self.maz_data is not None:
            report_content += f"""
### MAZ (Micro Analysis Zone) Controls
- **Total MAZ Zones**: {len(self.maz_data):,}
- **Total Households**: {self.maz_data['numhh_gq'].sum():,.0f}
- **Average Households per MAZ**: {self.maz_data['numhh_gq'].mean():.1f}
- **Max Households in Single MAZ**: {self.maz_data['numhh_gq'].max():.0f}
- **Zones with Group Quarters**: {(self.maz_data['gq_type_univ'] + self.maz_data['gq_type_noninst'] > 0).sum()}

"""
        
        if self.taz_data is not None:
            report_content += f"""
### TAZ (Traffic Analysis Zone) Controls  
- **Total TAZ Zones**: {len(self.taz_data):,}

#### Income Distribution
"""
            income_cols = [col for col in self.taz_data.columns if 'inc_' in col]
            if income_cols:
                for col in income_cols:
                    total = self.taz_data[col].sum()
                    pct = (total / self.taz_data[income_cols].sum().sum()) * 100
                    readable_label = self.income_labels.get(col, col)
                    report_content += f"- **{readable_label}**: {total:,.0f} households ({pct:.1f}%)\n"
            
            report_content += f"""
#### Age Distribution
"""
            age_cols = [col for col in self.taz_data.columns if 'pers_age_' in col]
            if age_cols:
                for col in age_cols:
                    total = self.taz_data[col].sum()
                    pct = (total / self.taz_data[age_cols].sum().sum()) * 100
                    readable_label = self.age_labels.get(col, col)
                    report_content += f"- **{readable_label}**: {total:,.0f} persons ({pct:.1f}%)\n"
        
        if self.county_data is not None:
            county_names = {
                1: 'Alameda', 2: 'Contra Costa', 3: 'Santa Clara', 4: 'San Francisco',
                5: 'San Mateo', 6: 'Solano', 7: 'Napa', 8: 'Sonoma', 9: 'Marin'
            }
            
            report_content += f"""
### County Controls
- **Total Counties**: {len(self.county_data)}

#### Employment by County
"""
            occ_cols = [col for col in self.county_data.columns if 'pers_occ_' in col]
            if occ_cols:
                for _, row in self.county_data.iterrows():
                    county_name = county_names.get(row['COUNTY'], f"County {row['COUNTY']}")
                    total_employed = row[occ_cols].sum()
                    report_content += f"- **{county_name}**: {total_employed:,.0f} employed persons\n"
        
        report_content += f"""
## Generated Visualizations

### Static Charts (PNG)
1. **maz_household_distribution.png** - Distribution of households across MAZ zones
2. **maz_group_quarters_summary.png** - Summary of group quarters by type
3. **taz_income_distribution.png** - Household income distribution analysis
4. **taz_household_size_distribution.png** - Regional household size patterns
5. **taz_worker_distribution.png** - Distribution by number of workers per household
6. **taz_age_distribution.png** - Regional age distribution patterns
7. **county_occupation_distribution.png** - Employment by occupation and county
8. **county_employment_totals.png** - Total employment by county

### Comprehensive PowerPoint Image
- **comprehensive_marginal_controls_powerpoint.png** - Single comprehensive image with all key visualizations optimized for PowerPoint presentations (20" x 24" at 300 DPI)

## Usage Notes

- All visualizations are saved in: `{self.output_dir}/`
- Static charts are high-resolution PNG (300 DPI) suitable for reports
- Interactive dashboard requires web browser for viewing
- Data represents current marginal controls used for PopulationSim synthesis
"""
        
        # Save report
        with open(self.output_dir / "visualization_summary_report.md", 'w') as f:
            f.write(report_content)
        
        print(f"✓ Summary report saved: {self.output_dir}/visualization_summary_report.md")
    
    def run_complete_analysis(self):
        """Run the complete visualization analysis."""
        print("="*60)
        print("MARGINAL CONTROLS VISUALIZATION GENERATOR")
        print("="*60)
        
        # Create all visualizations
        self.create_maz_visualizations()
        self.create_taz_visualizations() 
        self.create_county_visualizations()
        self.create_comprehensive_powerpoint_image()
        self.create_summary_report()
        
        print("\n" + "="*60)
        print("VISUALIZATION GENERATION COMPLETE")
        print("="*60)
        print(f"Output directory: {self.output_dir}")
        print("Generated files:")
        
        # List all generated files
        for file_path in self.output_dir.glob("*"):
            if file_path.is_file():
                print(f"  ✓ {file_path.name}")
        
        print(f"\nTotal files generated: {len(list(self.output_dir.glob('*')))}")


def main():
    """Main execution function."""
    print("PopulationSim Marginal Controls Visualization Generator")
    print("Author: PopulationSim Bay Area Team")
    print()
    
    # Check required packages
    required_packages = ['pandas', 'matplotlib', 'seaborn', 'plotly']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"⚠ Missing required packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return
    
    # Initialize and run visualizer
    try:
        visualizer = MarginalControlsVisualizer()
        visualizer.run_complete_analysis()
        
    except Exception as e:
        print(f"❌ Error during visualization generation: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n🎉 Visualization generation completed successfully!")
    print("📊 Check the output directory for all generated charts and dashboards.")


if __name__ == "__main__":
    main()


