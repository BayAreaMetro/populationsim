#!/usr/bin/env python3
"""
Create PUMS seed population for Bay Area PopulationSim TM2

Refactored version with improved modularity, error handling, and maintainability.
Key improvements:
- Separated concerns into focused classes and functions
- Better configuration management
- Improved error handling and logging
- More readable and maintainable code structure
- Direct output to final PopulationSim data directory (no intermediate copies)

Key ID Columns:
- SERIALNO: Original Census household serial number (preserved on both tables)
- unique_hh_id: Household identifier for PopulationSim
  Format: YEAR_STATE_PUMA_SERIALNO (e.g., "2023_6_06001_0000001")
  Used for household-person linkage in PopulationSim
"""

import pandas as pd
import numpy as np
import os
import zipfile
import requests
from urllib3.exceptions import InsecureRequestWarning
import warnings
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import logging
import time
from datetime import datetime

warnings.filterwarnings('ignore', category=InsecureRequestWarning)

# Import our utilities
from cpi_conversion import convert_2023_to_2010_dollars
from analysis.pums_downloader import PUMSDownloader
from analysis.data_validation import PopulationSimValidator, DataQualityReporter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SeedPopulationConfig:
    """Configuration for seed population creation"""
    # Bay Area PUMAs - 2020 definitions (62 PUMAs with actual MAZ coverage)
    bay_area_pumas: List[int] = None
    output_dir: Path = Path("output_2023")
    chunk_size: int = 50000
    random_seed: int = 42
    
    def __post_init__(self):
        if self.bay_area_pumas is None:
            # Try to read PUMAs dynamically from the crosswalk file
            try:
                from unified_tm2_config import config as unified_config
                crosswalk_file = unified_config.CROSSWALK_FILES['main_crosswalk']
                if crosswalk_file.exists():
                    import pandas as pd
                    crosswalk_df = pd.read_csv(crosswalk_file)
                    # Get unique PUMAs from the crosswalk as integers (PopulationSim format)
                    actual_pumas = sorted(crosswalk_df['PUMA'].astype(int).unique())
                    self.bay_area_pumas = actual_pumas
                    logger.info(f"Loaded {len(actual_pumas)} PUMAs from crosswalk file: {crosswalk_file}")
                    logger.info(f"PUMA range: {actual_pumas[0]} to {actual_pumas[-1]}")
                else:
                    logger.warning(f"Crosswalk file not found: {crosswalk_file}, using hardcoded PUMA list")
                    self._use_hardcoded_pumas()
            except Exception as e:
                logger.warning(f"Could not read crosswalk file: {e}, using hardcoded PUMA list")
                self._use_hardcoded_pumas()
        
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def _use_hardcoded_pumas(self):
        """Get Bay Area PUMAs from unified configuration"""
        from unified_tm2_config import config
        puma_config = config.get_puma_configuration()
        self.bay_area_pumas = puma_config['bay_area_pumas']
        logger.info(f"Using {puma_config['total_pumas']} Bay Area PUMAs from unified configuration")

class PUMACountyMapper:
    """Handles PUMA to County mapping for Bay Area"""
    
    @staticmethod
    def get_county_mapping_from_crosswalk(crosswalk_file: str = None) -> Dict[int, int]:
        """Returns PUMA to County mapping from the crosswalk file
        
        Args:
            crosswalk_file: Path to crosswalk file. If None, uses default locations.
            
        Returns:
            Dictionary mapping PUMA (int) to COUNTY (int)
        """
        import pandas as pd
        from pathlib import Path
        
        # Try multiple crosswalk locations
        if crosswalk_file:
            crosswalk_paths = [Path(crosswalk_file)]
        else:
            # Use unified config to get crosswalk paths
            try:
                from unified_tm2_config import config as unified_config
                crosswalk_paths = [
                    unified_config.CROSSWALK_FILES['popsim_crosswalk']  # Use the definitive crosswalk location
                ]
            except:
                # Fallback to hardcoded paths if config fails
                crosswalk_paths = [
                    Path("output_2023/populationsim_working_dir/data/geo_cross_walk_tm2.csv"),  # Fresh crosswalk only
                    Path("output_2023/geo_cross_walk_tm2.csv"),
                    Path("geo_cross_walk_tm2.csv")
                ]
        
        for crosswalk_path in crosswalk_paths:
            if crosswalk_path.exists():
                try:
                    crosswalk_df = pd.read_csv(crosswalk_path)
                    
                    # Ensure we have the required columns
                    if 'PUMA' not in crosswalk_df.columns or 'COUNTY' not in crosswalk_df.columns:
                        continue
                    
                    # Create PUMA to COUNTY mapping from crosswalk
                    puma_county_df = crosswalk_df[['PUMA', 'COUNTY']].dropna().drop_duplicates()
                    puma_to_county = dict(zip(puma_county_df['PUMA'], puma_county_df['COUNTY']))
                    
                    print(f"[SUCCESS] Loaded PUMA-to-county mapping from crosswalk: {crosswalk_path}")
                    print(f"[INFO] Found {len(puma_to_county)} PUMA-to-county mappings")
                    
                    # Validate we have reasonable county codes (1-97 range for Bay Area)
                    counties = set(puma_to_county.values())
                    valid_counties = {c for c in counties if isinstance(c, (int, float)) and 1 <= c <= 97}
                    if len(valid_counties) >= 7:  # Expect at least 7 Bay Area counties
                        print(f"[INFO] Valid counties found: {sorted(valid_counties)}")
                        return puma_to_county
                    else:
                        print(f"[WARNING] Invalid counties in crosswalk: {counties}")
                        
                except Exception as e:
                    print(f"[ERROR] Could not read crosswalk {crosswalk_path}: {e}")
                    continue
        
        # Fallback: if no crosswalk found, return empty dict and warn
        print(f"[ERROR] No valid crosswalk file found. Tried:")
        for path in crosswalk_paths:
            print(f"  - {path}")
        print(f"[ERROR] Cannot create PUMA-to-county mapping without crosswalk")
        return {}
    
    @staticmethod  
    def get_county_mapping() -> Dict[int, int]:
        """Legacy method - redirects to crosswalk-based mapping"""
        return PUMACountyMapper.get_county_mapping_from_crosswalk()
    
    @classmethod
    def add_county_mapping(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Add county mapping to dataframe based on PUMA"""
        county_map = cls.get_county_mapping()
        # Use San Francisco (75) as default fallback to match config
        # Map integer PUMAs directly (no string conversion needed)
        df['COUNTY'] = df['PUMA'].map(county_map).fillna(75)
        df['COUNTY'] = df['COUNTY'].astype(int)
        return df

class DataCleaner:
    """Handles data cleaning and validation"""
    
    @staticmethod
    def clean_numeric_columns(df: pd.DataFrame, description: str = "data") -> pd.DataFrame:
        """Clean all numeric columns of NaN and infinite values"""
        logger.info(f"Cleaning numeric columns in {description}...")
        
        nan_summary = []
        for col in df.columns:
            if df[col].dtype in ['float64', 'float32', 'int64', 'int32']:
                nan_count = df[col].isna().sum()
                inf_count = np.isinf(df[col]).sum()
                if nan_count > 0 or inf_count > 0:
                    nan_summary.append(f"{col}: {nan_count} NaN, {inf_count} inf")
                df[col] = df[col].fillna(0)
                df[col] = df[col].replace([np.inf, -np.inf], 0)
        
        if nan_summary:
            logger.info(f"Cleaned {description} fields: {nan_summary}")
        else:
            logger.info(f"No NaN/inf values found in {description} numeric fields")
        
        return df
    
    @staticmethod
    def convert_to_integers(df: pd.DataFrame, fields: List[str], description: str = "data") -> pd.DataFrame:
        """Convert specified fields to integers safely"""
        logger.info(f"Converting {description} fields to integer types for PopulationSim compatibility...")
        
        for field in fields:
            if field in df.columns:
                try:
                    df[field] = df[field].fillna(0)
                    df[field] = df[field].replace([np.inf, -np.inf], 0)
                    df[field] = df[field].astype(int)
                    logger.debug(f"Converted {field} to int64")
                except Exception as e:
                    logger.warning(f"Could not convert {field} to integer: {e}")
        
        return df

class HouseholdProcessor:
    """Processes household data for PopulationSim compatibility"""
    
    def __init__(self, config: SeedPopulationConfig):
        self.config = config
        self.county_mapper = PUMACountyMapper()
        self.data_cleaner = DataCleaner()
    
    def process_households(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process household data for PopulationSim"""
        logger.info(f"[HOUSEHOLD] Processing {len(df):,} households...")
        
        # Show initial data info
        logger.info(f"   Initial columns: {len(df.columns)}")
        logger.info(f"   Initial memory: {df.memory_usage(deep=True).sum() / 1024**2:.1f}MB")
        
        # Add county mapping
        logger.info("[MAP]  Step 1/6: Adding county mapping...")
        df = self.county_mapper.add_county_mapping(df)
        county_counts = df['COUNTY'].value_counts().sort_index()
        logger.info(f"   County distribution: {dict(county_counts)}")
        
        # Create group quarters type
        logger.info("[BUILDING] Step 2/6: Creating group quarters type...")
        initial_gq = len(df[df.get('TYPEHUGQ', 0) != 1]) if 'TYPEHUGQ' in df.columns else 0
        df = self._create_group_quarters_type(df)
        final_gq = len(df[df['hhgqtype'] != 0])  # Count non-household (GQ) units
        logger.info(f"   Group quarters households: {initial_gq} → {final_gq}")
        
        # Add detailed hhgqtype distribution for households
        hh_gq_counts = df['hhgqtype'].value_counts().sort_index()
        gq_labels = {0: 'Household', 1: 'University GQ', 2: 'Military GQ', 3: 'Other GQ'}
        for gq_type, count in hh_gq_counts.items():
            label = gq_labels.get(gq_type, f'Type {gq_type}')
            logger.info(f"     {label}: {count:,} households")
        
        # Check TYPEHUGQ distribution for debugging
        if 'TYPEHUGQ' in df.columns:
            typehugq_counts = df['TYPEHUGQ'].value_counts().sort_index()
            typehugq_labels = {1: 'Household', 2: 'Institutional GQ', 3: 'Noninstitutional GQ'}
            logger.info("   TYPEHUGQ source distribution:")
            for typ, count in typehugq_counts.items():
                label = typehugq_labels.get(typ, f'Type {typ}')
                logger.info(f"     {label}: {count:,} households")
        
        # Fix WGTP weights for group quarters households
        logger.info("[WEIGHT] Step 2.5/6: Fixing WGTP weights for group quarters...")
        gq_mask = df['hhgqtype'] != 0
        zero_weight_gq = len(df[gq_mask & (df['WGTP'] == 0)])
        if zero_weight_gq > 0:
            logger.info(f"   Found {zero_weight_gq:,} GQ households with zero WGTP - setting to 1")
            df.loc[gq_mask & (df['WGTP'] == 0), 'WGTP'] = 1
            logger.info(f"   Fixed WGTP weights for {zero_weight_gq:,} GQ households")
        else:
            logger.info("   No GQ households with zero WGTP found")
        
        # Verify weight fix
        final_zero_weights = len(df[df['WGTP'] == 0])
        if final_zero_weights > 0:
            logger.warning(f"   WARNING: {final_zero_weights:,} households still have zero WGTP")
        else:
            logger.info("   ✓ All households now have non-zero WGTP")
        
        # Handle HUPAC (Household Under Poverty Level)
        logger.info("[MONEY] Step 3/6: Processing poverty status...")
        df = self._handle_hupac(df)
        poverty_count = len(df[df.get('HUPAC', 0) == 1]) if 'HUPAC' in df.columns else 0
        logger.info(f"   Households in poverty: {poverty_count:,} ({poverty_count/len(df)*100:.1f}%)")
        
        # Create income fields
        logger.info("[INCOME] Step 4/6: Converting income to 2010 dollars...")
        df = self._create_income_fields(df)
        
        # Clean numeric data
        logger.info("[CLEAN] Step 5/6: Cleaning numeric data...")
        df = self.data_cleaner.clean_numeric_columns(df, "household")
        
        # Convert to integers
        logger.info("[NUMBER] Step 6/6: Converting to integer types...")
        integer_fields = ['HUPAC', 'NP', 'hhgqtype', 'WGTP', 'TYPEHUGQ', 'PUMA', 'COUNTY']
        df = self.data_cleaner.convert_to_integers(df, integer_fields, "household")
        
        logger.info("[SUCCESS] Step 7/7: Household processing complete!")
        logger.info(f"   Final columns: {len(df.columns)}")
        logger.info(f"   Final memory: {df.memory_usage(deep=True).sum() / 1024**2:.1f}MB")
        
        return df
    
    def _create_group_quarters_type(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create PopulationSim-compatible group quarters type"""
        # Based on TYPEHUGQ: 1=household, 2=institutional GQ, 3=noninstitutional GQ  
        # PopulationSim expects: 0=household, 1=university GQ, 2=military GQ, 3=other GQ
        df['hhgqtype'] = 0  # Default to household
        df.loc[df['TYPEHUGQ'] == 3, 'hhgqtype'] = 1  # Noninstitutional GQ -> university
        
        # Split institutional GQ into military vs other
        institutional_gq_mask = df['TYPEHUGQ'] == 2
        institutional_gq_count = institutional_gq_mask.sum()
        
        if institutional_gq_count > 0:
            df = self._split_institutional_gq(df, institutional_gq_mask, institutional_gq_count)
        
        return df
    
    def _split_institutional_gq(self, df: pd.DataFrame, mask: pd.Series, count: int) -> pd.DataFrame:
        """Split institutional GQ into military vs other based on control targets"""
        # Control targets: military=1,684, other=122,467 (ratio ~1.4% military)
        military_target, other_target = 1684, 122467
        military_ratio = military_target / (military_target + other_target)
        
        # Randomly assign institutional GQ
        np.random.seed(self.config.random_seed)
        institutional_indices = df[mask].index
        n_military = int(len(institutional_indices) * military_ratio)
        military_indices = np.random.choice(institutional_indices, n_military, replace=False)
        
        # Assign hhgqtype
        df.loc[mask, 'hhgqtype'] = 3  # Default to "other"
        df.loc[military_indices, 'hhgqtype'] = 2  # Military
        
        logger.info(f"Split {count:,} institutional GQ records:")
        logger.info(f"  Military (hhgqtype=2): {n_military:,} ({n_military/count*100:.1f}%)")
        logger.info(f"  Other (hhgqtype=3): {count-n_military:,} ({(count-n_military)/count*100:.1f}%)")
        
        return df
    
    def _handle_hupac(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle HUPAC (Household Under Poverty Level) field"""
        if 'HUPAC' not in df.columns:
            return df
        
        hupac_nan_count = df['HUPAC'].isna().sum()
        if hupac_nan_count > 0:
            logger.info(f"Fixing {hupac_nan_count} NaN values in HUPAC...")
            # For group quarters, set HUPAC=4 (not applicable)
            gq_mask = (df['HUPAC'].isna()) & (df['hhgqtype'].isin([1, 2, 3]))
            df.loc[gq_mask, 'HUPAC'] = 4
            # For households, set HUPAC=2 (assume at/above poverty)
            hh_mask = (df['HUPAC'].isna()) & (df['hhgqtype'] == 0)
            df.loc[hh_mask, 'HUPAC'] = 2
            # Fix any remaining NaN values
            df['HUPAC'] = df['HUPAC'].fillna(2)
        
        return df

    def _create_income_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create income fields in both 2023 and 2010 dollars from HINCP using proper ADJINC adjustment"""
        if 'HINCP' not in df.columns:
            logger.warning("HINCP column not found - cannot create income fields")
            return df
        
        if 'ADJINC' not in df.columns:
            logger.error("ADJINC column not found - cannot properly adjust PUMS income!")
            logger.error("HINCP values are in survey year dollars and must be adjusted with ADJINC")
            return df
        
        # Step 1: Apply ADJINC to get income in 2023 dollars
        logger.info("   Applying ADJINC factor to convert survey year income to 2023 dollars...")
        
        valid_mask = (df['HINCP'] > 0) & (df['ADJINC'] > 0)
        df['hh_income_2023'] = 0.0
        df.loc[valid_mask, 'hh_income_2023'] = (df.loc[valid_mask, 'ADJINC'] / 1_000_000) * df.loc[valid_mask, 'HINCP']
        
        # Step 2: Convert 2023 dollars to 2010 dollars for PopulationSim controls  
        # Note: 2023 ACS data requires 2023→2010 conversion, not 2021→2010
        # CPI 2023 ≈ 310.0, CPI 2010 = 218.056  
        cpi_2023_to_2010 = 218.056 / 310.0
        df['hh_income_2010'] = df['hh_income_2023'] * cpi_2023_to_2010
        
        # Log conversion summary
        valid_income_count = valid_mask.sum()
        if valid_income_count > 0:
            # Show ADJINC factor distribution
            adjinc_factors = (df.loc[valid_mask, 'ADJINC'] / 1_000_000).describe()
            logger.info(f"   ADJINC factors: min={adjinc_factors['min']:.6f}, max={adjinc_factors['max']:.6f}, mean={adjinc_factors['mean']:.6f}")
            
            median_2023 = df.loc[valid_mask, 'hh_income_2023'].median()
            median_2010 = df.loc[valid_mask, 'hh_income_2010'].median()
            
            logger.info(f"   Created income fields for {valid_income_count:,} households")
            logger.info(f"   Median income: 2023=${median_2023:,.0f} → 2010=${median_2010:,.0f}")
            logger.info(f"   CPI conversion: 2023→2010 factor = {cpi_2023_to_2010:.4f}")
            
            # Validate against expected Bay Area medians (rough check)
            if median_2010 < 70000:
                logger.warning(f"   ⚠️  2010$ median (${median_2010:,.0f}) seems low for Bay Area")
            elif median_2010 > 100000:
                logger.warning(f"   ⚠️  2010$ median (${median_2010:,.0f}) seems high for Bay Area")
            else:
                logger.info(f"   ✓ 2010$ median (${median_2010:,.0f}) appears reasonable for Bay Area")
        else:
            logger.warning("   No valid income data found")
        
        return df

class PersonProcessor:
    """Processes person data for PopulationSim compatibility"""
    
    def __init__(self, config: SeedPopulationConfig):
        self.config = config
        self.county_mapper = PUMACountyMapper()
        self.data_cleaner = DataCleaner()
    
    def process_persons(self, df: pd.DataFrame, household_df: pd.DataFrame) -> pd.DataFrame:
        """Process person data for PopulationSim"""
        logger.info(f"[PERSON] Processing {len(df):,} persons...")
        
        # Show initial data info
        logger.info(f"   Initial columns: {len(df.columns)}")
        logger.info(f"   Initial memory: {df.memory_usage(deep=True).sum() / 1024**2:.1f}MB")
        
        # Add county mapping
        logger.info("[MAP]  Step 1/8: Adding county mapping...")
        df = self.county_mapper.add_county_mapping(df)
        county_counts = df['COUNTY'].value_counts().sort_index()
        logger.info(f"   County distribution: {dict(county_counts)}")
        
        # Create employment categories
        logger.info("[WORK] Step 2/8: Creating employment status...")
        df = self._create_employment_status(df)
        employed_count = len(df[df.get('employed', 0) == 1]) if 'employed' in df.columns else 0
        logger.info(f"   Employed persons: {employed_count:,} ({employed_count/len(df)*100:.1f}%)")
        
        # Create student status
        logger.info("[STUDENT] Step 3/8: Creating student status...")
        df = self._create_student_status(df)
        
        # Create person type categories
        logger.info("[AGE] Step 4/8: Creating person types by age...")
        df = self._create_person_type(df)
        if 'person_type' in df.columns:
            person_type_counts = df['person_type'].value_counts().sort_index()
            type_names = {1: 'Preschool', 2: 'School-age', 3: 'Working-age', 4: 'Senior'}
            for ptype, count in person_type_counts.items():
                type_name = type_names.get(ptype, f'Type {ptype}')
                logger.info(f"     {type_name}: {count:,} ({count/len(df)*100:.1f}%)")
        
        # Create occupation categories  
        logger.info("[CONFIG] Step 5/8: Creating occupation categories...")
        df = self._create_occupation_categories(df)
        
        # Map group quarters type from household data
        logger.info("[BUILDING] Step 6/8: Mapping group quarters type...")
        df = self._map_group_quarters_type(df, household_df)
        gq_counts = df['hhgqtype'].value_counts().sort_index()
        gq_labels = {0: 'Household', 1: 'University GQ', 2: 'Military GQ', 3: 'Other GQ'}
        logger.info("   Person GQ type distribution:")
        for gq_type, count in gq_counts.items():
            label = gq_labels.get(gq_type, f'Type {gq_type}')
            pct = count / len(df) * 100
            logger.info(f"     {label}: {count:,} persons ({pct:.1f}%)")
        
        # Check for GQ people specifically
        total_gq_persons = len(df[df['hhgqtype'] >= 2])
        logger.info(f"   Total GQ persons (hhgqtype >= 2): {total_gq_persons:,}")
        if total_gq_persons == 0:
            logger.warning("   WARNING: No GQ persons found! This may indicate a data mapping issue.")
        
        # Clean numeric data
        logger.info("[CLEAN] Step 7/8: Cleaning numeric data...")
        df = self.data_cleaner.clean_numeric_columns(df, "person")
        
        # Convert to integers
        logger.info("[NUMBER] Step 8/8: Converting to integer types...")
        integer_fields = ['employed', 'employ_status', 'student_status', 'person_type', 
                         'occupation', 'hhgqtype', 'PUMA', 'COUNTY', 'PWGTP']
        df = self.data_cleaner.convert_to_integers(df, integer_fields, "person")
        
        logger.info("[SUCCESS] Person processing complete!")
        logger.info(f"   Final columns: {len(df.columns)}")
        logger.info(f"   Final memory: {df.memory_usage(deep=True).sum() / 1024**2:.1f}MB")
        
        return df
        
        # Create person type
        df = self._create_person_type(df)
        
        # Create occupation categories
        df = self._create_occupation_categories(df)
        
        # Map group quarters type from households
        df = self._map_group_quarters_type(df, household_df)
        
        # Clean numeric data
        df = self.data_cleaner.clean_numeric_columns(df, "person")
        
        # Convert to integers
        integer_fields = ['AGEP', 'hhgqtype', 'employed', 'employ_status', 'student_status', 
                         'person_type', 'occupation', 'ESR', 'PWGTP', 'PUMA', 'COUNTY']
        df = self.data_cleaner.convert_to_integers(df, integer_fields, "person")
        
        return df
    
    def _create_employment_status(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create employment status fields"""
        # Binary employed field
        df['employed'] = 0
        df.loc[df['ESR'].isin([1, 2, 4, 5]), 'employed'] = 1
        
        # Detailed employment status
        df['employ_status'] = 3  # Default to not in labor force
        df.loc[df['ESR'].isin([1, 2, 4, 5]), 'employ_status'] = 1  # Employed
        df.loc[df['ESR'] == 3, 'employ_status'] = 2  # Unemployed
        df.loc[df['ESR'] == 6, 'employ_status'] = 3  # Not in labor force
        df.loc[df['AGEP'] < 16, 'employ_status'] = 4  # Under 16
        
        return df
    
    def _create_student_status(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create student status categories"""
        df['student_status'] = 1  # Default to not student
        df.loc[(df['SCHG'].notna()) & (df['AGEP'] < 16), 'student_status'] = 2
        df.loc[(df['SCHG'].notna()) & (df['AGEP'] >= 16), 'student_status'] = 3
        return df
    
    def _create_person_type(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create person type categories based on employment status"""
        # Map employment status to person type as per TM1 convention
        # 1 = full-time worker, 2 = part-time worker, 3 = college student, 4 = non-working adult
        df['person_type'] = 4  # Default to non-working adult
        
        # Map from employ_status if it exists
        if 'employ_status' in df.columns:
            df.loc[df['employ_status'] == 1, 'person_type'] = 1  # Full-time worker
            df.loc[df['employ_status'] == 2, 'person_type'] = 2  # Part-time worker  
            df.loc[df['employ_status'] == 4, 'person_type'] = 3  # Student (under 16, map to college student category)
            # employ_status == 3 (not in labor force) stays as person_type = 4
        else:
            # Fallback to age-based if employ_status doesn't exist
            df.loc[df['AGEP'] < 18, 'person_type'] = 3   # Students
            df.loc[(df['AGEP'] >= 18) & (df['AGEP'] < 65), 'person_type'] = 1  # Working age -> full-time
            df.loc[df['AGEP'] >= 65, 'person_type'] = 4  # Seniors -> non-working
            
        return df
    
    def _create_occupation_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create occupation categories from OCCP codes"""
        df['occupation'] = 0  # Default to not applicable
        df.loc[(df['OCCP'] >= 10) & (df['OCCP'] <= 950), 'occupation'] = 1    # Management
        df.loc[(df['OCCP'] >= 1005) & (df['OCCP'] <= 3540), 'occupation'] = 2  # Professional
        df.loc[(df['OCCP'] >= 3601) & (df['OCCP'] <= 4650), 'occupation'] = 3  # Services
        df.loc[(df['OCCP'] >= 4700) & (df['OCCP'] <= 5940), 'occupation'] = 4  # Sales/Office
        df.loc[(df['OCCP'] >= 6005) & (df['OCCP'] <= 9750), 'occupation'] = 5  # Manual
        df.loc[(df['OCCP'] >= 9800) & (df['OCCP'] <= 9830), 'occupation'] = 5  # Military -> Manual
        return df
    
    def _map_group_quarters_type(self, df: pd.DataFrame, household_df: pd.DataFrame) -> pd.DataFrame:
        """Map group quarters type from household data"""
        hh_gq_lookup = household_df.set_index('unique_hh_id')['hhgqtype'].to_dict()
        df['hhgqtype'] = df['unique_hh_id'].map(hh_gq_lookup).fillna(0).astype(int)
        return df

class SeedPopulationCreator:
    """Main class for creating seed population"""
    
    def __init__(self, config: Optional[SeedPopulationConfig] = None):
        self.config = config or SeedPopulationConfig()
        self.household_processor = HouseholdProcessor(self.config)
        self.person_processor = PersonProcessor(self.config)
    
    def create_seed_population(self) -> bool:
        """Main method to create seed population"""
        start_time = datetime.now()
        logger.info("=" * 80)
        logger.info("[START] STARTING SEED POPULATION CREATION")
        logger.info("=" * 80)
        logger.info(f"[TIME] Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            logger.info(f"[STATS] Configuration:")
            logger.info(f"   Target PUMAs: {len(self.config.bay_area_pumas)} from crosswalk")
            logger.info(f"   Output directory: {self.config.output_dir}")
            logger.info(f"   Chunk size: {self.config.chunk_size:,}")
            logger.info("=" * 80)
            
            # Use unified configuration for all file paths
            from unified_tm2_config import config as unified_config
            
            # Define file paths from unified config
            h_raw = unified_config.SEED_FILES['households_raw']
            p_raw = unified_config.SEED_FILES['persons_raw']
            # Final seed files - write directly to PopulationSim data directory
            h_final = unified_config.SEED_FILES['households'] 
            p_final = unified_config.SEED_FILES['persons']
            
            # Step 1: Check for existing final seed files
            step_time = datetime.now()
            logger.info("STEP 1: CHECKING EXISTING SEED FILES")
            logger.info("=" * 70)
            
            if h_final.exists() and p_final.exists():
                logger.info("[SUCCESS] Found existing seed files - using them...")
                
                load_start = datetime.now()
                logger.info("📖 Loading existing seed files...")
                household_df = pd.read_csv(h_final)
                person_df = pd.read_csv(p_final)
                load_time = datetime.now() - load_start
                logger.info(f"[SUCCESS] Loaded {len(household_df):,} households and {len(person_df):,} persons in {load_time}")
                
                # Files are already in final location - no copying needed
                
                # Step 5: Generate validation report
                logger.info("-" * 50)
                logger.info("[SEARCH] VALIDATION REPORT")
                logger.info("-" * 50)
                self._generate_validation_report(household_df, person_df)
                
                total_time = datetime.now() - start_time
                logger.info("=" * 80)
                logger.info("[COMPLETE] SUCCESS: PopulationSim seed population created successfully!")
                logger.info(f"⏱️  Total time: {total_time}")
                logger.info("=" * 80)
                return True
                
            else:
                # Load from M: drive PUMS files (2023 5-Year with complete 2019-2023 data)
                logger.info("[DATA] Loading PUMS data from M: drive (2023 5-Year PUMS)...")
                m_drive_pums_dir = Path("M:/Data/Census/PUMS_2023_5Year_Crosswalked")
                household_file = m_drive_pums_dir / "bay_area_households_2019_2023_crosswalked.csv"
                person_file = m_drive_pums_dir / "bay_area_persons_2019_2023_crosswalked.csv"
                
                if household_file.exists() and person_file.exists():
                    load_start = datetime.now()
                    logger.info(f"📖 Loading: {household_file}")
                    
                    # Load household file with progress tracking
                    hh_load_start = datetime.now()
                    household_data = pd.read_csv(household_file)
                    hh_load_time = datetime.now() - hh_load_start
                    logger.info(f"[SUCCESS] Household file loaded: {len(household_data):,} records in {hh_load_time}")
                    
                    logger.info(f"📖 Loading: {person_file}")
                    logger.info("⏳ Person file is large (~2M records) - this may take 2-4 minutes...")
                    
                    # Load person file with progress indication
                    person_load_start = datetime.now()
                    
                    # Try to load in chunks to show progress
                    try:
                        # First, get the file size for progress estimation
                        import os
                        file_size_mb = os.path.getsize(person_file) / 1024**2
                        logger.info(f"[STATS] Person file size: {file_size_mb:.1f}MB")
                        
                        # Load the file
                        person_data = pd.read_csv(person_file)
                        person_load_time = datetime.now() - person_load_start
                        logger.info(f"[SUCCESS] Person file loaded: {len(person_data):,} records in {person_load_time}")
                        
                    except Exception as e:
                        logger.error(f"[ERROR] Failed to load person file: {e}")
                        return False
                    
                    total_load_time = datetime.now() - load_start
                    logger.info(f"[SUCCESS] All data loaded in {total_load_time}")
                    
                else:
                    logger.error(f"[ERROR] M: drive PUMS files not found:")
                    logger.error(f"   {household_file}")
                    logger.error(f"   {person_file}")
                    return False
            
            # Step 2: Process raw data (only if we didn't use existing processed files)
            logger.info("=" * 70)
            logger.info("STEP 2: PROCESSING RAW PUMS DATA")
            logger.info("=" * 70)
            
            # Use the data we just downloaded (already in memory)
            household_df = household_data
            person_df = person_data
            logger.info(f"[SUCCESS] Loaded {len(household_df):,} households and {len(person_df):,} persons from M: drive")
            
            # Show data size info
            household_mb = household_df.memory_usage(deep=True).sum() / 1024**2
            person_mb = person_df.memory_usage(deep=True).sum() / 1024**2
            logger.info(f"[STATS] Memory usage: Households {household_mb:.1f}MB, Persons {person_mb:.1f}MB")
            
            # CRITICAL: Filter to only include PUMAs from crosswalk
            logger.info("-" * 50)
            logger.info("[SEARCH] PUMA FILTERING (CRITICAL STEP)")
            logger.info("-" * 50)
            
            initial_hh_count = len(household_df)
            initial_person_count = len(person_df)
            
            # Show initial PUMA distribution
            initial_pumas = sorted(household_df['PUMA'].astype(str).str.lstrip('0').astype(int).unique())
            logger.info(f"[SUMMARY] Initial PUMAs in data: {len(initial_pumas)} total")
            logger.info(f"   Range: {initial_pumas[0]} to {initial_pumas[-1]}")
            logger.info(f"   First 10: {initial_pumas[:10]}")
            
            # Convert string PUMAs to integers to match crosswalk format
            logger.info("🔄 Converting PUMA formats from string to integer...")
            logger.info("   Processing household PUMAs...")
            household_df['PUMA'] = household_df['PUMA'].astype(str).str.lstrip('0').astype(int)
            logger.info("   Processing person PUMAs...")
            person_df['PUMA'] = person_df['PUMA'].astype(str).str.lstrip('0').astype(int)
            logger.info("[SUCCESS] PUMA format conversion complete")
            
            # Show target PUMAs from crosswalk
            valid_pumas = set(self.config.bay_area_pumas)
            target_pumas = sorted(self.config.bay_area_pumas)
            logger.info(f"[TARGET] Target PUMAs from crosswalk: {len(target_pumas)} total")
            logger.info(f"   Range: {target_pumas[0]} to {target_pumas[-1]}")
            logger.info(f"   First 10: {target_pumas[:10]}")
            
            # Check overlap
            initial_puma_set = set(initial_pumas)
            overlap = initial_puma_set.intersection(valid_pumas)
            logger.info(f"🔗 PUMA overlap: {len(overlap)} PUMAs will be kept")
            
            missing_from_data = valid_pumas - initial_puma_set
            if missing_from_data:
                logger.warning(f"[WARNING]  Target PUMAs missing from data: {sorted(missing_from_data)}")
            
            extra_in_data = initial_puma_set - valid_pumas
            if extra_in_data:
                logger.info(f"➖ Extra PUMAs in data (will be filtered out): {len(extra_in_data)} PUMAs")
                logger.info(f"   Examples: {sorted(extra_in_data)[:10]}")
            
            # Filter both datasets to crosswalk PUMAs with progress tracking
            logger.info("🔽 Filtering datasets to crosswalk PUMAs...")
            
            # Filter households first (smaller dataset)
            logger.info("   [HOUSEHOLD] Filtering households...")
            filter_start = datetime.now()
            household_df = household_df[household_df['PUMA'].isin(valid_pumas)].copy()
            hh_filter_time = datetime.now() - filter_start
            logger.info(f"   [SUCCESS] Household filtering complete in {hh_filter_time}")
            
            # Filter persons (larger dataset - this is the slow step)
            logger.info("   [PERSON] Filtering persons...")
            logger.info(f"   ⏳ Processing {len(person_df):,} person records - this may take 30-60 seconds...")
            person_filter_start = datetime.now()
            person_df = person_df[person_df['PUMA'].isin(valid_pumas)].copy()
            person_filter_time = datetime.now() - person_filter_start
            logger.info(f"   [SUCCESS] Person filtering complete in {person_filter_time}")
            
            logger.info("[SUCCESS] PUMA FILTERING COMPLETE:")
            logger.info(f"   Households: {initial_hh_count:,} → {len(household_df):,} (removed {initial_hh_count - len(household_df):,})")
            logger.info(f"   Persons: {initial_person_count:,} → {len(person_df):,} (removed {initial_person_count - len(person_df):,})")
            logger.info(f"   Retention rate: {len(household_df)/initial_hh_count*100:.1f}% households, {len(person_df)/initial_person_count*100:.1f}% persons")
            
            # Verify final PUMA list
            final_pumas = sorted(household_df['PUMA'].unique())
            logger.info(f"[SUCCESS] Final PUMAs in filtered data: {len(final_pumas)} total")
            logger.info(f"   Final PUMAs: {final_pumas}")
            
            # CRITICAL: Create unique IDs for linking households and persons
            logger.info("-" * 50)
            logger.info("🔗 CREATING UNIQUE IDs")
            logger.info("-" * 50)
            
            # Create integer household IDs (PopulationSim requirement)
            logger.info("[HOUSEHOLD] Creating integer household IDs for PopulationSim compatibility...")
            
            # Method 1: Create sequential integer IDs starting from 1 as unique_hh_id
            # This ensures PopulationSim gets the integer IDs it expects in the main column
            household_df['unique_hh_id'] = range(1, len(household_df) + 1)
            
            # Keep the unique string ID as hh_id_string for debugging/reference
            household_df['hh_id_string'] = (
                household_df['YEAR'].astype(str) + '_' +
                household_df['STATE'].astype(str) + '_' +
                household_df['PUMA'].astype(str).str.zfill(5) + '_' +
                household_df['SERIALNO'].astype(str).str.zfill(7)
            )
            
            logger.info(f"[SUCCESS] Created {len(household_df):,} integer household IDs (1 to {len(household_df)})")
            logger.info(f"   Example unique_hh_id: {household_df['unique_hh_id'].iloc[0]} (int)")
            logger.info(f"   Example hh_id_string: {household_df['hh_id_string'].iloc[0]} (reference)")
            
            # Create household lookup for persons using SERIALNO -> unique_hh_id mapping
            logger.info("[PERSON] Creating household-person linkage using SERIALNO -> unique_hh_id lookup...")
            linking_start = datetime.now()
            
            # Create lookup dictionary from household file: SERIALNO -> unique_hh_id (integer)
            hh_lookup = household_df.set_index('SERIALNO')['unique_hh_id'].to_dict()
            
            # Map persons to household IDs using SERIALNO lookup
            person_df['unique_hh_id'] = person_df['SERIALNO'].map(hh_lookup)
            
            linking_time = datetime.now() - linking_start
            logger.info(f"[SUCCESS] Linked persons to households using SERIALNO -> unique_hh_id lookup in {linking_time}")
            
            # Check for orphaned persons (persons without matching households)
            orphaned_persons = person_df['unique_hh_id'].isna().sum()
            if orphaned_persons > 0:
                logger.warning(f"[WARNING] Found {orphaned_persons} persons without household links - removing them")
                person_df = person_df[person_df['unique_hh_id'].notna()].copy()
            
            logger.info(f"[SUCCESS] Final counts: {len(person_df):,} persons linked to {len(household_df):,} households")
            
            # Verify the linking worked correctly
            unique_hh_in_persons = person_df['unique_hh_id'].nunique()
            unique_hh_in_households = household_df['unique_hh_id'].nunique()
            
            logger.info(f"[VALIDATION] Households with unique_hh_id: {unique_hh_in_households:,}")
            logger.info(f"[VALIDATION] Unique households referenced by persons: {unique_hh_in_persons:,}")
            
            if unique_hh_in_persons == unique_hh_in_households:
                logger.info("[SUCCESS] ✓ Perfect household-person linkage!")
            else:
                households_without_persons = unique_hh_in_households - unique_hh_in_persons
                logger.warning(f"[WARNING] Linkage mismatch: {households_without_persons} households have no persons")
                
                # Filter out households without persons for PopulationSim compatibility
                logger.info("[FILTER] Removing households without persons for PopulationSim compatibility...")
                households_with_persons = person_df['unique_hh_id'].unique()
                original_household_count = len(household_df)
                household_df = household_df[household_df['unique_hh_id'].isin(households_with_persons)].copy()
                removed_households = original_household_count - len(household_df)
                
                logger.info(f"[SUCCESS] Filtered households: {original_household_count:,} → {len(household_df):,} (removed {removed_households:,})")
                logger.info("✓ All remaining households have corresponding persons")

            # Verify the linking worked
            unique_hh_in_persons = person_df['unique_hh_id'].nunique()
            logger.info(f"[SEARCH] Verification: {unique_hh_in_persons} unique households referenced in person data")            # Process households with chunked logging
            logger.info("-" * 50)
            logger.info("[HOUSEHOLD] PROCESSING HOUSEHOLDS")
            logger.info("-" * 50)
            
            hh_process_start = datetime.now()
            household_df = self.household_processor.process_households(household_df)
            hh_process_time = datetime.now() - hh_process_start
            logger.info(f"[SUCCESS] Household processing completed in {hh_process_time}")
            
            # Calculate household workers before processing persons
            logger.info("-" * 50)
            logger.info("👷 CALCULATING HOUSEHOLD WORKERS")
            logger.info("-" * 50)
            
            workers_start = datetime.now()
            household_df = self._calculate_household_workers(household_df, person_df)
            workers_time = datetime.now() - workers_start
            logger.info(f"[SUCCESS] Household workers calculation completed in {workers_time}")
            
            # Process persons with chunked logging
            logger.info("-" * 50)
            logger.info("[PERSON] PROCESSING PERSONS")
            logger.info("-" * 50)
            
            person_process_start = datetime.now()
            person_df = self.person_processor.process_persons(person_df, household_df)
            person_process_time = datetime.now() - person_process_start
            logger.info(f"[SUCCESS] Person processing completed in {person_process_time}")
            
            # Step 3: Final processing
            logger.info("-" * 50)
            logger.info("✨ FINAL DATA PROCESSING")
            logger.info("-" * 50)
            
            logger.info("[HOUSEHOLD] Finalizing household data...")
            household_df = self._finalize_household_data(household_df)
            
            logger.info("[PERSON] Finalizing person data...")
            person_df = self._finalize_person_data(person_df)
            
            # Step 4: Save final seed files directly to PopulationSim data directory
            logger.info("-" * 50)
            logger.info("💾 SAVING FINAL SEED FILES")
            logger.info("-" * 50)
            self._save_seed_files(household_df, person_df, h_final, p_final)
            
            # Files are saved directly to final location - no copying needed
            
            # Use unified configuration for PopulationSim data directory
            from unified_tm2_config import UnifiedTM2Config
            unified_config = UnifiedTM2Config()
            
            seed_h = unified_config.SEED_FILES['households']
            seed_p = unified_config.SEED_FILES['persons']
            
            
            # Step 5: Generate validation report
            logger.info("-" * 50)
            logger.info("[SEARCH] VALIDATION REPORT")
            logger.info("-" * 50)
            self._generate_validation_report(household_df, person_df)
            
            total_time = datetime.now() - start_time
            logger.info("=" * 80)
            logger.info("[COMPLETE] SUCCESS: PopulationSim seed population created successfully!")
            logger.info(f"⏱️  Total processing time: {total_time}")
            logger.info(f"[TIME] Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 80)
            return True
            
        except Exception as e:
            total_time = datetime.now() - start_time
            logger.error("=" * 80)
            logger.error(f"[ERROR] FAILED to create seed population after {total_time}")
            logger.error(f"💥 Error: {e}")
            logger.error("=" * 80)
            return False
    
    def _calculate_household_workers(self, household_df: pd.DataFrame, person_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate household workers from person employment status"""
        logger.info(f"👷 Calculating household workers from {len(person_df):,} persons...")
        
        # Create temporary employed field for aggregation
        logger.info("   Step 1/3: Identifying employed persons...")
        person_df['temp_employed'] = 0
        person_df.loc[person_df['ESR'].isin([1, 2, 4, 5]), 'temp_employed'] = 1
        
        employed_count = person_df['temp_employed'].sum()
        logger.info(f"   Found {employed_count:,} employed persons ({employed_count/len(person_df)*100:.1f}%)")
        
        # Show employment by ESR code
        esr_counts = person_df['ESR'].value_counts().sort_index()
        esr_names = {1: 'Civilian employed', 2: 'Civilian unemployed', 3: 'Armed forces', 
                    4: 'Armed forces unemployed', 5: 'Not in labor force', 6: 'Under 16'}
        logger.info("   Employment status distribution:")
        for esr, count in esr_counts.items():
            name = esr_names.get(esr, f'ESR {esr}')
            employed = 'employed' if esr in [1, 2, 4, 5] else 'not employed'
            logger.info(f"     ESR {esr} ({name}): {count:,} - {employed}")
        
        # Aggregate by household
        logger.info("   Step 2/3: Aggregating workers by household...")
        workers_df = (person_df[['unique_hh_id', 'temp_employed']]
                     .groupby(['unique_hh_id'])
                     .sum()
                     .rename(columns={"temp_employed": "hh_workers_from_esr"}))
        
        logger.info(f"   Calculated workers for {len(workers_df):,} households")
        
        # Show worker distribution
        worker_dist = workers_df['hh_workers_from_esr'].value_counts().sort_index()
        logger.info("   Household worker distribution:")
        for workers, count in worker_dist.head(10).items():
            logger.info(f"     {workers} workers: {count:,} households ({count/len(workers_df)*100:.1f}%)")
        
        # Merge with household data
        logger.info("   Step 3/3: Merging with household data...")
        household_df = household_df.merge(workers_df, left_on='unique_hh_id', right_index=True, how='left')
        household_df['hh_workers_from_esr'] = household_df['hh_workers_from_esr'].fillna(0).astype(int)
        
        # Verify merge
        merged_count = len(household_df[household_df['hh_workers_from_esr'].notna()])
        logger.info(f"[SUCCESS] Successfully merged workers for {merged_count:,} households")
        
        return household_df
    
    def _finalize_household_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Final processing for household data"""
        # Convert income fields to integers
        income_fields = ['hh_income_2010', 'hh_income_2023']
        for field in income_fields:
            if field in df.columns:
                df[field] = df[field].fillna(0).round().astype(int)
        
        # Ensure hh_workers_from_esr is integer
        if 'hh_workers_from_esr' in df.columns:
            df['hh_workers_from_esr'] = df['hh_workers_from_esr'].astype(int)
        
        # CRITICAL: Ensure PUMA is in integer format for PopulationSim compatibility
        if 'PUMA' in df.columns:
            df['PUMA'] = df['PUMA'].astype(int)
        
        return df
    
    def _finalize_person_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Final processing for person data"""
        # Add unique person ID if not present
        if 'unique_person_id' not in df.columns:
            df['unique_person_id'] = range(1, len(df) + 1)
        
        # CRITICAL: Ensure PUMA is in integer format for PopulationSim compatibility
        if 'PUMA' in df.columns:
            df['PUMA'] = df['PUMA'].astype(int)
        
        # Handle NaN values in occupation/industry fields
        # NAICSP (Industry codes) - fill NaN with 0 for unemployed/children
        if 'NAICSP' in df.columns:
            df['NAICSP'] = df['NAICSP'].fillna(0)
        
        # SOCP (Occupation codes) - fill NaN with 0 for unemployed/children  
        if 'SOCP' in df.columns:
            df['SOCP'] = df['SOCP'].fillna(0)
        
        # Create SOC codes (convert to string, handle NaN and 'X' characters)
        df['soc'] = df['SOCP'].fillna('0')
        # Remove 'X' characters that appear in some SOCP codes
        df['soc'] = df['soc'].astype(str).str.replace('X', '', regex=False)
        # Convert to int, then back to string for consistency
        df['soc'] = pd.to_numeric(df['soc'], errors='coerce').fillna(0).astype(int).astype(str)
        df.loc[df['soc'] == '0', 'soc'] = ''
        
        return df
    
    def _save_seed_files(self, household_df: pd.DataFrame, person_df: pd.DataFrame, 
                            h_path: Path, p_path: Path) -> None:
        """Save final seed files with validation"""
        logger.info("💾 Writing final seed files to PopulationSim data directory...")
        
        # Ensure directory exists
        h_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Validate data before saving
        logger.info("   Step 1/4: Validating household data...")
        self._validate_data(household_df, "household")
        
        logger.info("   Step 2/4: Validating person data...")
        self._validate_data(person_df, "person")
        
        # Save files with progress
        logger.info(f"   Step 3/4: Writing household file to {h_path}...")
        household_df.to_csv(h_path, index=False)
        file_size_mb = h_path.stat().st_size / 1024**2
        logger.info(f"   [SUCCESS] Household file written: {len(household_df):,} records, {file_size_mb:.1f}MB")
        
        logger.info(f"   Step 4/4: Writing person file to {p_path}...")
        person_df.to_csv(p_path, index=False)
        file_size_mb = p_path.stat().st_size / 1024**2
        logger.info(f"   [SUCCESS] Person file written: {len(person_df):,} records, {file_size_mb:.1f}MB")
        
        logger.info("💾 Final seed files saved successfully!")
    
    def _validate_data(self, df: pd.DataFrame, data_type: str) -> None:
        """Validate data quality before saving"""
        nan_count = df.isna().sum().sum()
        inf_count = np.isinf(df.select_dtypes(include=[np.number])).sum().sum()
        
        logger.info(f"{data_type.title()} data validation:")
        logger.info(f"  Shape: {df.shape}")
        logger.info(f"  Total NaN values: {nan_count}")
        logger.info(f"  Total Inf values: {inf_count}")
        
        if nan_count > 0:
            nan_cols = [col for col in df.columns if df[col].isna().sum() > 0]
            logger.warning(f"  Columns with NaN: {nan_cols[:5]}...")
        
        if inf_count > 0:
            logger.warning(f"  Found {inf_count} infinite values!")
    
    def _generate_validation_report(self, household_df: pd.DataFrame, person_df: pd.DataFrame) -> None:
        """Generate comprehensive validation report"""
        logger.info("Generating data validation report...")
        
        reporter = DataQualityReporter()
        report = reporter.generate_summary_report(
            household_df, person_df, self.config.bay_area_pumas
        )
        
        # Save report
        report_path = self.config.output_dir / "data_validation_report.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        
        # Also log key findings
        logger.info("Validation report saved to: %s", report_path)
        logger.info("Key validation findings:")
        lines = report.split('\n')
        for line in lines:
            if 'VALIDATION STATUS:' in line or 'ERRORS (' in line or 'WARNINGS (' in line:
                logger.info(f"  {line.strip()}")

def main():
    """Main execution function"""
    config = SeedPopulationConfig()
    creator = SeedPopulationCreator(config)
    success = creator.create_seed_population()
    
    if not success:
        logger.error("Seed population creation failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
