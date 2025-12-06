#!/usr/bin/env python3
"""
PopulationSim Aggregate Summary Generator
=======================================

Generate comprehensive summary CSV files that match the tm2py-utils validation 
dashboard format for comparison between 2015, 2023, and ACS control data.

This script leverages existing PopulationSim analysis patterns and utilities to create:
1. Regional and county-level summaries
2. Household size, income, and demographic distributions  
3. Group quarters vs household distinctions
4. Dashboard-compatible CSV format with consistent structure

Design Pattern:
- Reuse existing county handling from analyze_county_results.py
- Leverage unified_tm2_config.py for paths and mappings
- Follow data_validation.py patterns for robust data handling
- Match tm2py-utils CSV structure (dataset, share, count columns)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
from typing import Dict, List, Tuple, Optional
warnings.filterwarnings('ignore')

from unified_tm2_config import UnifiedTM2Config
from cpi_conversion import convert_2023_to_2010_dollars

class PopulationSimSummaryGenerator:
    """Generate dashboard summaries leveraging existing analysis patterns"""
    
    def __init__(self):
        self.config = UnifiedTM2Config()
        self.output_dir = Path("output_2023/aggregate_summaries")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # County mapping from existing code
        self.COUNTY_NAMES = {
            1: "San Francisco", 2: "San Mateo", 3: "Santa Clara", 4: "Alameda",
            5: "Contra Costa", 6: "Solano", 7: "Napa", 8: "Sonoma", 9: "Marin"
        }
        
        # Load MAZ to county crosswalk (TM2 for 2023 data)
        self.maz_crosswalk = None
        crosswalk_file = self.config.POPSIM_DATA_DIR / "geo_cross_walk_tm2_maz.csv"
        if crosswalk_file.exists():
            try:
                self.maz_crosswalk = pd.read_csv(crosswalk_file)
                print(f"Loaded TM2 MAZ crosswalk: {len(self.maz_crosswalk)} records")
            except Exception as e:
                print(f"Could not load TM2 MAZ crosswalk: {e}")
        
        # Load 2010 PUMA crosswalk (for 2015 data)
        self.maz_crosswalk_2010 = None
        crosswalk_2010_file = Path(r"C:\GitHub\tm2py-utils\tm2py_utils\inputs\maz_taz\mazs_tazs_county_tract_PUMA10.csv")
        if crosswalk_2010_file.exists():
            try:
                self.maz_crosswalk_2010 = pd.read_csv(crosswalk_2010_file)
                print(f"Loaded 2010 PUMA crosswalk: {len(self.maz_crosswalk_2010)} records")
            except Exception as e:
                print(f"Could not load 2010 PUMA crosswalk: {e}")
        
        self.summaries = {}
        
    def load_population_data(self, use_samples: bool = False):
        """Load 2015 and 2023 population data using existing file patterns"""
        print("="*60)
        print("LOADING POPULATION DATA")
        print("="*60)
        
        data = {}
        
        # 2023 data - use postprocessed files with HHINCADJ (2010$)
        files_2023 = {
            'households': self.config.OUTPUT_DIR / "populationsim_working_dir" / "output" / "households_2023_tm2.csv",
            'persons': self.config.OUTPUT_DIR / "populationsim_working_dir" / "output" / "persons_2023_tm2.csv"
        }
        
        # 2015 data - use postprocessed files with HINC (2010$)
        files_2015 = {
            'households': Path("example_2015_outputs/hh_persons_model/households.csv"),
            'persons': Path("example_2015_outputs/hh_persons_model/persons.csv")
        }
        
        for year, files in [("2023", files_2023), ("2015", files_2015)]:
            print(f"\\nLoading {year} data...")
            
            for file_type, file_path in files.items():
                if file_path.exists():
                    try:
                        # Load samples or full data based on flag
                        sample_size = 5000 if use_samples else None
                        df = pd.read_csv(file_path, nrows=sample_size)
                        
                        data_key = f"{file_type}_{year}"
                        data[data_key] = df
                        
                        rows_msg = f" (sample)" if use_samples else ""
                        print(f"  {file_type}: {len(df):,} rows{rows_msg}, {len(df.columns)} columns")
                        
                        # Show key columns for debugging
                        key_cols = [col for col in df.columns if col.upper() in 
                                  ['COUNTY', 'MTCCOUNTYID', 'NP', 'HHSIZE', 'AGEP', 'HINC', 'HHINCADJ', 'TYPE', 'UNITTYPE']]
                        if key_cols:
                            print(f"    Key columns: {key_cols}")
                        
                    except Exception as e:
                        print(f"  ERROR loading {file_path}: {e}")
                else:
                    print(f"  MISSING: {file_path}")
        
        return data
        
    def filter_households_only(self, hh_df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        """Filter to households only, excluding group quarters using existing patterns"""
        
        # Look for group quarters identifier - different column names in different years
        # Postprocessed: TYPE (TM2) or UNITTYPE (TM1)
        gq_indicators = ['TYPE', 'UNITTYPE', 'TYPEHUGQ', 'hhgqtype']
        gq_col = None
        
        for col in gq_indicators:
            if col in hh_df.columns:
                gq_col = col
                break
        
        if gq_col is None:
            print(f"    No GQ column found for {dataset_name}, using all records")
            return hh_df.copy()
        
        # Filter based on column type (pattern from existing analysis)
        if gq_col in ['TYPE', 'UNITTYPE']:
            # TYPE: 1 = housing unit, 2-3 = group quarters
            household_mask = hh_df[gq_col] == 1
        elif gq_col in ['TYPEHUGQ', 'hhgqtype']:
            # TYPEHUGQ: 0-1 = households, 2+ = group quarters
            # In synthetic files, TYPEHUGQ 1 = housing unit, 2-5 = group quarters
            household_mask = hh_df[gq_col] == 1
        else:
            household_mask = hh_df[gq_col] == 0  # Default assumption
        
        filtered_df = hh_df[household_mask].copy()
        print(f"    Filtered {dataset_name}: {len(filtered_df):,} households (from {len(hh_df):,} total)")
        
        return filtered_df
        
    def get_county_column(self, df: pd.DataFrame) -> Optional[str]:
        """Identify county column using existing patterns"""
        # Synthetic files typically have PUMA or COUNTY, not MTCCountyID
        county_candidates = ['COUNTY', 'county', 'MTCCountyID', 'PUMA']
        
        for col in county_candidates:
            if col in df.columns:
                return col
        
        return None
        
    def create_household_size_summary(self, hh_data: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        """Create household size summary matching tm2py-utils format"""
        print(f"  Creating household size summary for {dataset_name}")
        
        # Find household size column
        size_col = None
        for col in ['NP', 'HHSIZE', 'household_size']:
            if col in hh_data.columns:
                size_col = col
                break
        
        if size_col is None:
            print(f"    No household size column found")
            return None
        
        # Use all records (including GQ) since controls don't distinguish
        working_data = hh_data.copy()
        print(f"    Processing {len(working_data):,} records")
        
        # Standardize size categories to match across years (1-7+)
        working_data['household_size'] = working_data[size_col].fillna(0).astype(int)
        working_data['household_size'] = working_data['household_size'].clip(lower=1, upper=7)
        
        # Create summary
        summary = working_data.groupby('household_size').size().reset_index(name='households')
        
        # Ensure all size categories 1-7 exist
        all_sizes = pd.DataFrame({'household_size': range(1, 8)})
        summary = all_sizes.merge(summary, on='household_size', how='left')
        summary['households'] = summary['households'].fillna(0).astype(int)
        
        # Calculate share
        summary['share'] = summary['households'] / summary['households'].sum()
        summary['dataset'] = dataset_name
        
        # Convert size to string, with 7+ label
        summary['household_size'] = summary['household_size'].astype(str)
        summary.loc[summary['household_size'] == '7', 'household_size'] = '7+'
        
        return summary
        
    def create_county_summary(self, hh_data: pd.DataFrame, dataset_name: str, include_gq: bool = True) -> pd.DataFrame:
        """Create county summary using MAZ crosswalk for proper county identification"""
        gq_label = " (all)" if include_gq else " (households only)"
        print(f"  Creating county summary for {dataset_name}{gq_label}")
        
        # Filter based on include_gq
        if include_gq:
            working_data = hh_data.copy()
        else:
            working_data = self.filter_households_only(hh_data, dataset_name)
        
        # Determine which crosswalk to use based on available columns
        crosswalk = None
        merge_col = None
        
        if 'MAZ_NODE' in working_data.columns and self.maz_crosswalk is not None:
            print(f"    Using TM2 MAZ crosswalk for county identification")
            crosswalk = self.maz_crosswalk
            merge_col = 'MAZ_NODE'
        elif 'MAZ' in working_data.columns and self.maz_crosswalk_2010 is not None:
            print(f"    Using 2010 PUMA MAZ crosswalk for county identification")
            crosswalk = self.maz_crosswalk_2010
            merge_col = 'MAZ'
        
        if crosswalk is not None and merge_col is not None:
            # Merge with crosswalk to get county
            crosswalk_cols = [merge_col, 'COUNTY'] if 'COUNTY' in crosswalk.columns else [merge_col, 'county']
            county_col_name = crosswalk_cols[1]
            
            working_data = working_data.merge(
                crosswalk[crosswalk_cols],
                on=merge_col,
                how='left'
            )
            
            # Create summary by county
            summary = working_data.groupby(county_col_name).size().reset_index(name='households')
            summary['county_name'] = summary[county_col_name].map(self.COUNTY_NAMES)
            
        else:
            # Fallback to direct county column
            county_col = self.get_county_column(working_data)
            if county_col is None:
                print(f"    No county information available")
                return None
            
            print(f"    Using direct county column: {county_col}")
            summary = working_data.groupby(county_col).size().reset_index(name='households')
            
            if county_col in ['COUNTY', 'MTCCountyID', 'county']:
                summary['county_name'] = summary[county_col].map(self.COUNTY_NAMES)
            else:
                summary['county_name'] = summary[county_col].astype(str)
        
        # Remove records with missing county
        summary = summary[summary['county_name'].notna()]
        
        summary['share'] = summary['households'] / summary['households'].sum()
        summary['dataset'] = dataset_name + ("_with_gq" if include_gq else "_households_only")
        summary['includes_gq'] = 'Yes' if include_gq else 'No'
        
        return summary
        
    def create_income_summary(self, hh_data: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        """Create income distribution summary - all in 2010 dollars"""
        print(f"  Creating income summary for {dataset_name}")
        
        # Postprocessed files use HHINCADJ (2023) or HINC (2015) - both in 2010$
        income_col = None
        
        if 'HHINCADJ' in hh_data.columns:
            income_col = 'HHINCADJ'
            print(f"    Using HHINCADJ (2010 dollars from postprocessed 2023 data)")
        elif 'HINC' in hh_data.columns:
            income_col = 'HINC'
            print(f"    Using HINC (2010 dollars from postprocessed 2015 data)")
        else:
            print(f"    No income column found (expected HHINCADJ or HINC)")
            return None
        
        # Filter to households only
        households_only = self.filter_households_only(hh_data, dataset_name)
        working_data = households_only.copy()
        
        # Keep all households with income data (including zero income)
        # Remap negative or null incomes to 0
        working_data = working_data[working_data[income_col].notna()].copy()
        working_data['income_2010'] = working_data[income_col].clip(lower=0)
        
        # Define income bins matching converted TAZ controls (2023$ -> 2010$)
        # Using conversion factor 218.056 / 310.0 = 0.7034
        conversion_factor = 218.056 / 310.0
        bins = [
            0,
            20000 * conversion_factor,   # $14,068
            45000 * conversion_factor,   # $31,653
            60000 * conversion_factor,   # $42,204
            75000 * conversion_factor,   # $52,755
            100000 * conversion_factor,  # $70,340
            150000 * conversion_factor,  # $105,510
            200000 * conversion_factor,  # $140,680
            np.inf
        ]
        labels = [
            'Under $14K',
            '$14K-$32K',
            '$32K-$42K',
            '$42K-$53K',
            '$53K-$70K',
            '$70K-$106K',
            '$106K-$141K',
            '$141K+'
        ]
        
        working_data['income_category'] = pd.cut(working_data['income_2010'], 
                                               bins=bins, labels=labels, right=False)
        
        # Create summary
        summary = working_data.groupby('income_category', observed=False).size().reset_index(name='households')
        summary['share'] = summary['households'] / summary['households'].sum()
        summary['dataset'] = dataset_name
        summary['base_year'] = '2010 dollars'
        
        print(f"    Created {len(summary)} income categories, {summary['households'].sum():,.0f} total households")
        
        return summary
        
    def load_acs_control_data(self):
        """Load ACS control data for comparison using existing patterns"""
        print("\\nLoading ACS control data...")
        
        controls = {}
        
        # County-level controls
        county_controls_file = self.config.POPSIM_DATA_DIR / "county_marginals.csv"
        if county_controls_file.exists():
            try:
                df = pd.read_csv(county_controls_file)
                controls['county'] = df
                print(f"  County controls: {len(df)} counties, {len(df.columns)} variables")
            except Exception as e:
                print(f"  Error loading county controls: {e}")
        
        # TAZ-level controls - load FULL file for aggregation
        # Try both possible filenames
        for taz_filename in ["taz_marginals_hhgq.csv", "taz_marginals.csv"]:
            taz_controls_file = self.config.POPSIM_DATA_DIR / taz_filename
            if taz_controls_file.exists():
                try:
                    print(f"  Loading full TAZ controls from {taz_filename}...")
                    df = pd.read_csv(taz_controls_file)
                    controls['taz'] = df
                    print(f"  TAZ controls: {len(df):,} TAZs, {len(df.columns)} variables")
                    
                    # Show household size columns if they exist
                    size_cols = [col for col in df.columns if 'hh_size_' in col.lower()]
                    if size_cols:
                        print(f"    Found household size columns: {size_cols}")
                    break
                except Exception as e:
                    print(f"  Error loading TAZ controls: {e}")
                
        return controls
        
    def create_acs_household_size_summary(self, controls_data: Dict) -> Optional[pd.DataFrame]:
        """Create ACS household size summary from TAZ control data aggregated to regional level"""
        
        # Look for household size controls in TAZ data
        if 'taz' not in controls_data:
            print("    No TAZ control data available for ACS comparison")
            return None
            
        taz_controls = controls_data['taz']
        
        # Find household size columns (looking for hh_size_1, hh_size_2, etc.)
        size_cols = [col for col in taz_controls.columns if 'hh_size_' in col.lower()]
        
        if not size_cols:
            print("    No household size controls found in ACS data")
            return None
        
        print(f"    Found ACS household size columns: {size_cols}")
        
        # Aggregate across all TAZs for sizes 1-7+
        size_data = {}
        for size_num in range(1, 7):  # 1-6
            col_name = f'hh_size_{size_num}'
            if col_name in taz_controls.columns:
                total = taz_controls[col_name].sum()
                size_data[str(size_num)] = total
                print(f"      {col_name}: {total:,} households")
        
        # Handle 6_plus or 7_plus category
        if 'hh_size_6_plus' in taz_controls.columns:
            total = taz_controls['hh_size_6_plus'].sum()
            size_data['6'] = total
            print(f"      hh_size_6_plus (mapped to 6): {total:,} households")
        elif 'hh_size_7_plus' in taz_controls.columns:
            total = taz_controls['hh_size_7_plus'].sum()
            size_data['7'] = total
            print(f"      hh_size_7_plus: {total:,} households")
        elif 'hh_size_7' in taz_controls.columns:
            total = taz_controls['hh_size_7'].sum()
            size_data['7'] = total
            print(f"      hh_size_7: {total:,} households")
        
        if not size_data:
            print("    No household size data could be aggregated")
            return None
        
        # Create standardized size summary (1-7+)
        # Note: ACS controls use 6+ as highest category, map to our 7+ for consistency
        size_summary = []
        for size_str in ['1', '2', '3', '4', '5', '6']:
            households = size_data.get(size_str, 0)
            if size_str == '6' and '6' in size_data:
                # This is the 6+ category, label it as 7+
                size_summary.append({'household_size': '7+', 'households': int(households)})
            else:
                size_summary.append({'household_size': size_str, 'households': int(households)})
        
        # Add size 7+ if we have it separately (not 6+)
        if '7' in size_data and '6' not in size_data:
            size_summary.append({'household_size': '7+', 'households': int(size_data['7'])})
        
        # Convert to DataFrame and add share
        df = pd.DataFrame(size_summary)
        total_hh = df['households'].sum()
        df['share'] = df['households'] / total_hh
        df['dataset'] = 'ACS_Controls'
        
        print(f"    Created ACS summary: {total_hh:,} total households")
        
        return df
    
    def create_acs_income_summary(self, controls: dict) -> Optional[pd.DataFrame]:
        """Create ACS income summary from TAZ controls - all in 2010 dollars"""
        print(f"  Creating ACS income summary from TAZ controls")
        
        if 'taz' not in controls:
            print(f"    No TAZ controls available")
            return None
        
        taz_controls = controls['taz']
        
        # Look for income columns in controls
        income_cols = [c for c in taz_controls.columns if 'inc_' in c.lower()]
        
        if not income_cols:
            print(f"    No income columns found in controls")
            return None
        
        print(f"    Found income columns: {income_cols}")
        
        # Aggregate across all TAZs
        income_data = taz_controls[income_cols].sum()
        
        # Convert TAZ control bins from 2023$ to 2010$ equivalent bins
        # Per README_INCOME.md: TAZ controls use 2023$ bins
        # Conversion factor: 2023$ to 2010$ = 218.056 / 310.0 ≈ 0.7034
        # 
        # Convert 2023$ bin boundaries to 2010$:
        # - <$20K (2023$) * 0.7034 = <$14.1K (2010$)
        # - $20K-$45K (2023$) * 0.7034 = $14.1K-$31.7K (2010$)
        # - $45K-$60K (2023$) * 0.7034 = $31.7K-$42.2K (2010$)
        # - $60K-$75K (2023$) * 0.7034 = $42.2K-$52.8K (2010$)
        # - $75K-$100K (2023$) * 0.7034 = $52.8K-$70.3K (2010$)
        # - $100K-$150K (2023$) * 0.7034 = $70.3K-$105.5K (2010$)
        # - $150K-$200K (2023$) * 0.7034 = $105.5K-$140.7K (2010$)
        # - $200K+ (2023$) * 0.7034 = $140.7K+ (2010$)
        
        conversion_factor = 218.056 / 310.0
        
        # Map 2023$ TAZ control columns directly to 2010$ bins (same structure as PopSim outputs)
        # TAZ controls in 2023$: <$20K, $20K-$45K, $45K-$60K, $60K-$75K, $75K-$100K, $100K-$150K, $150K-$200K, $200K+
        # Converted to 2010$: <$14K, $14K-$32K, $32K-$42K, $42K-$53K, $53K-$70K, $70K-$106K, $106K-$141K, $141K+
        
        taz_to_output = {
            'inc_lt_20k': 'Under $14K',
            'inc_20k_45k': '$14K-$32K',
            'inc_45k_60k': '$32K-$42K',
            'inc_60k_75k': '$42K-$53K',
            'inc_75k_100k': '$53K-$70K',
            'inc_100k_150k': '$70K-$106K',
            'inc_150k_200k': '$106K-$141K',
            'inc_200k_plus': '$141K+',
        }
        
        # Create output bins with exact boundaries
        output_bins = [
            'Under $14K',
            '$14K-$32K',
            '$32K-$42K',
            '$42K-$53K',
            '$53K-$70K',
            '$70K-$106K',
            '$106K-$141K',
            '$141K+'
        ]
        
        # Map TAZ control data directly to output bins
        summary_dict = {cat: 0.0 for cat in output_bins}
        
        for taz_col, households in income_data.items():
            if taz_col in taz_to_output:
                output_cat = taz_to_output[taz_col]
                summary_dict[output_cat] += households
        
        # Convert to DataFrame
        summary = pd.DataFrame([
            {'income_category': cat, 'households': hh}
            for cat, hh in summary_dict.items()
        ])
        
        summary['share'] = summary['households'] / summary['households'].sum()
        summary['dataset'] = 'ACS_Controls'
        summary['base_year'] = '2010 dollars'
        
        print(f"    Created income summary: {summary['households'].sum():,.0f} total households")
        print(f"    Converted 2023$ TAZ bins to 2010$ equivalent bins (factor: {conversion_factor:.4f})")
        
        return summary
        
    def create_acs_county_summary(self) -> Optional[pd.DataFrame]:
        """Create ACS county summary from MAZ marginals with GQ distinction"""
        print(f"  Creating ACS county summary from MAZ marginals")
        
        maz_marginals_file = self.config.POPSIM_DATA_DIR / "maz_marginals_hhgq.csv"
        if not maz_marginals_file.exists():
            print(f"    MAZ marginals file not found")
            return None
        
        if self.maz_crosswalk is None:
            print(f"    No MAZ crosswalk available")
            return None
        
        # Load MAZ marginals
        maz_marginals = pd.read_csv(maz_marginals_file)
        print(f"    Loaded {len(maz_marginals):,} MAZ records")
        
        # Merge with crosswalk to get county
        crosswalk_cols = ['MAZ_NODE', 'COUNTY'] if 'COUNTY' in self.maz_crosswalk.columns else ['MAZ_NODE', 'county']
        county_col_name = crosswalk_cols[1]
        
        maz_with_county = maz_marginals.merge(
            self.maz_crosswalk[crosswalk_cols],
            on='MAZ_NODE',
            how='left'
        )
        
        # Create summaries for both with and without GQ
        summaries = []
        
        # Households only (numhh column)
        if 'numhh' in maz_with_county.columns:
            county_hh = maz_with_county.groupby(county_col_name)['numhh'].sum().reset_index()
            county_hh.columns = ['county_id', 'households']
            county_hh['county_name'] = county_hh['county_id'].map(self.COUNTY_NAMES)
            county_hh['share'] = county_hh['households'] / county_hh['households'].sum()
            county_hh['dataset'] = 'ACS_Controls_households_only'
            county_hh['includes_gq'] = 'No'
            summaries.append(county_hh)
            print(f"    Created households-only summary: {county_hh['households'].sum():,.0f} total")
        
        # With GQ (numhh_gq column)
        if 'numhh_gq' in maz_with_county.columns:
            county_all = maz_with_county.groupby(county_col_name)['numhh_gq'].sum().reset_index()
            county_all.columns = ['county_id', 'households']
            county_all['county_name'] = county_all['county_id'].map(self.COUNTY_NAMES)
            county_all['share'] = county_all['households'] / county_all['households'].sum()
            county_all['dataset'] = 'ACS_Controls_with_gq'
            county_all['includes_gq'] = 'Yes'
            summaries.append(county_all)
            print(f"    Created with-GQ summary: {county_all['households'].sum():,.0f} total")
        
        if not summaries:
            return None
        
        combined = pd.concat(summaries, ignore_index=True)
        return combined
        
    def generate_all_summaries(self, use_samples: bool = False):
        """Generate comprehensive summaries for dashboard"""
        print("\\n" + "="*60)
        print("GENERATING DASHBOARD SUMMARIES")
        print("="*60)
        
        # Load data
        data = self.load_population_data(use_samples=use_samples)
        
        # Load ACS controls
        controls = self.load_acs_control_data()
        
        if not data:
            print("ERROR: No data loaded")
            return
        
        # Generate summaries for each dataset
        for data_key, df in data.items():
            if 'households' not in data_key:
                continue
                
            year = data_key.split('_')[1]
            dataset_name = f"PopSim_{year}"
            
            print(f"\nProcessing {dataset_name}...")
            
            # Household size summary (no GQ distinction - controls don't separate)
            size_summary = self.create_household_size_summary(df, dataset_name)
            if size_summary is not None:
                self.summaries[f'household_size_{year}'] = size_summary
            
            # County summary - households only
            county_summary_hh = self.create_county_summary(df, dataset_name, include_gq=False)
            if county_summary_hh is not None:
                self.summaries[f'households_by_county_{year}_hh'] = county_summary_hh
            
            # County summary - with GQ
            county_summary_gq = self.create_county_summary(df, dataset_name, include_gq=True)
            if county_summary_gq is not None:
                self.summaries[f'households_by_county_{year}_with_gq'] = county_summary_gq
            
            # Income distribution (all in 2010 dollars)
            income_summary = self.create_income_summary(df, dataset_name)
            if income_summary is not None:
                self.summaries[f'households_by_income_{year}'] = income_summary
        
        # Add ACS control summaries
        if controls:
            print("\nProcessing ACS Controls...")
            acs_size_summary = self.create_acs_household_size_summary(controls)
            if acs_size_summary is not None:
                self.summaries['household_size_acs'] = acs_size_summary
            
            # ACS county controls from MAZ marginals
            acs_county_summary = self.create_acs_county_summary()
            if acs_county_summary is not None:
                self.summaries['households_by_county_acs'] = acs_county_summary
            
            # ACS income controls from TAZ marginals
            acs_income_summary = self.create_acs_income_summary(controls)
            if acs_income_summary is not None:
                self.summaries['households_by_income_acs'] = acs_income_summary
        
        print(f"\\nGenerated {len(self.summaries)} summary datasets")
        
    def save_summaries(self):
        """Save individual and combined summaries"""
        print("\\n" + "="*60)
        print("SAVING SUMMARIES")
        print("="*60)
        
        # Save individual summaries
        for name, df in self.summaries.items():
            output_path = self.output_dir / f"{name}.csv"
            df.to_csv(output_path, index=False)
            print(f"Saved {name}: {len(df)} rows -> {output_path.name}")
        
        # Create combined files for dashboard (tm2py-utils pattern)
        summary_types = ['household_size', 'households_by_county', 'households_by_income']
        
        for summary_type in summary_types:
            matching_summaries = [df for name, df in self.summaries.items() 
                                if summary_type in name]
            
            if matching_summaries:
                combined = pd.concat(matching_summaries, ignore_index=True)
                
                # Use tm2py-utils naming convention
                if summary_type == 'household_size':
                    output_name = "household_size_regional.csv"
                elif summary_type == 'households_by_county':
                    output_name = "households_by_county.csv"
                elif summary_type == 'households_by_income':
                    output_name = "households_by_income.csv"
                
                output_path = self.output_dir / output_name
                combined.to_csv(output_path, index=False)
                print(f"\\nSaved combined {summary_type}: {len(combined)} rows -> {output_name}")
                
                # Show sample for verification
                print("  Sample data:")
                for _, row in combined.head(3).iterrows():
                    print(f"    {dict(row)}")
        
    def create_dashboard_config(self):
        """Create dashboard YAML configuration matching tm2py-utils pattern"""
        print("\\n" + "="*60) 
        print("CREATING DASHBOARD CONFIG")
        print("="*60)
        
        # Basic dashboard config matching tm2py-utils structure
        config_content = """header:
  tab: PopulationSim Comparison
  title: PopulationSim Multi-Year Summary
  description: Comparison of 2015 vs 2023 synthetic populations
  
layout:
  household_demographics:
  - type: bar
    title: Households by Size - Share
    props:
      dataset: household_size_regional.csv
      x: household_size
      y: share
      groupBy: dataset
    description: 'Share: households by household size across model years'
  - type: bar
    title: Households by Size - Total
    props:
      dataset: household_size_regional.csv
      x: household_size
      y: households
      groupBy: dataset  
    description: 'Total: households by household size across model years'
    
  geographic_distribution:
  - type: bar
    title: Households by County - Share
    props:
      dataset: households_by_county.csv
      x: county_name
      y: share
      groupBy: dataset
    description: 'Share: household distribution across Bay Area counties'
  - type: bar
    title: Households by County - Total
    props:
      dataset: households_by_county.csv
      x: county_name
      y: households
      groupBy: dataset
    description: 'Total: household counts by county across model years'
    
  economic_characteristics:
  - type: bar
    title: Households by Income - Share
    props:
      dataset: households_by_income.csv
      x: income_category
      y: share
      groupBy: dataset
    description: 'Share: household income distribution across model years'
"""
        
        config_path = self.output_dir / "dashboard-populationsim.yaml"
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        print(f"Created dashboard config: {config_path.name}")
        
def main():
    """Main execution function"""
    print("PopulationSim Aggregate Summary Generator")
    print("Using existing analysis patterns and configurations")
    
    # Create generator
    generator = PopulationSimSummaryGenerator()
    
    # Generate summaries (use samples=False for full datasets in production)
    use_full_data = True  # Set to True to process complete datasets
    generator.generate_all_summaries(use_samples=False)
    
    # Save all outputs
    generator.save_summaries()
    
    # Create dashboard configuration
    generator.create_dashboard_config()
    
    print("\\n" + "="*60)
    print("SUMMARY GENERATION COMPLETE")
    print("="*60)
    print(f"Output directory: {generator.output_dir}")
    print("\\nFiles created:")
    print("- Individual CSV summaries by year and type")
    print("- Combined CSV files for dashboard (household_size_regional.csv, etc.)")
    print("- Dashboard YAML configuration (dashboard-populationsim.yaml)")
    print("\\nNext steps:")
    print("1. Review generated CSV files for accuracy")
    print("2. Copy CSV files to tm2py-utils dashboard data directory")
    print("3. Integrate dashboard config with tm2py-utils validation system")
    print("4. Extend to include person-level summaries (age, employment, etc.)")
    print("5. Add additional summary types (household type, auto ownership, etc.)")

if __name__ == "__main__":
    main()