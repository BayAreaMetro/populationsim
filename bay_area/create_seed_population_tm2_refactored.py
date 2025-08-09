#!/usr/bin/env python3
"""
Create PUMS seed population for Bay Area PopulationSim TM2

Refactored version with improved modularity, error handling, and maintainability.
Key improvements:
- Separated concerns into focused classes and functions
- Better configuration management
- Improved error handling and logging
- More readable and maintainable code structure
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

warnings.filterwarnings('ignore', category=InsecureRequestWarning)

# Import our utilities
from cpi_conversion import convert_2023_to_2010_dollars
from pums_downloader import PUMSDownloader
from data_validation import PopulationSimValidator, DataQualityReporter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SeedPopulationConfig:
    """Configuration for seed population creation"""
    # Bay Area PUMAs - 2020 definitions (62 PUMAs with actual MAZ coverage)
    bay_area_pumas: List[str] = None
    output_dir: Path = Path("output_2023")
    chunk_size: int = 50000
    random_seed: int = 42
    
    def __post_init__(self):
        if self.bay_area_pumas is None:
            # Try to read PUMAs dynamically from the crosswalk file
            try:
                crosswalk_file = Path("hh_gq/data/geo_cross_walk_tm2.csv")
                if crosswalk_file.exists():
                    import pandas as pd
                    crosswalk_df = pd.read_csv(crosswalk_file)
                    # Get unique PUMAs from the crosswalk and format as 5-digit strings
                    actual_pumas = sorted(crosswalk_df['PUMA'].astype(str).str.zfill(5).unique())
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
    def get_county_mapping() -> Dict[str, int]:
        """Returns PUMA to County mapping for the 62 PUMAs with MAZ coverage"""
        return {
            # Alameda County (COUNTY=4) - 14 PUMAs
            '00101': 4, '00111': 4, '00112': 4, '00113': 4, '00114': 4, '00115': 4, 
            '00116': 4, '00117': 4, '00118': 4, '00119': 4, '00120': 4, '00121': 4, 
            '00122': 4, '00123': 4,
            # Contra Costa County (COUNTY=5) - 9 PUMAs
            '01301': 5, '01305': 5, '01308': 5, '01309': 5, '01310': 5, '01311': 5,
            '01312': 5, '01313': 5, '01314': 5,
            # Marin County (COUNTY=9) - 2 PUMAs
            '04103': 9, '04104': 9,
            # Napa County (COUNTY=7) - 1 PUMA
            '05500': 7,
            # San Francisco County (COUNTY=1) - 8 PUMAs
            '07507': 1, '07508': 1, '07509': 1, '07510': 1, '07511': 1, '07512': 1,
            '07513': 1, '07514': 1,
            # San Mateo County (COUNTY=2) - 6 PUMAs  
            '08101': 2, '08102': 2, '08103': 2, '08104': 2, '08105': 2, '08106': 2,
            # Santa Clara County (COUNTY=3) - 15 PUMAs
            '08505': 3, '08506': 3, '08507': 3, '08508': 3, '08510': 3, '08511': 3,
            '08512': 3, '08515': 3, '08516': 3, '08517': 3, '08518': 3, '08519': 3,
            '08520': 3, '08521': 3, '08522': 3,
            # Solano County (COUNTY=6) - 3 PUMAs
            '09501': 6, '09502': 6, '09503': 6,
            # Sonoma County (COUNTY=8) - 4 PUMAs
            '09702': 8, '09704': 8, '09705': 8, '09706': 8
        }
    
    @classmethod
    def add_county_mapping(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Add county mapping to dataframe based on PUMA"""
        county_map = cls.get_county_mapping()
        df['COUNTY'] = df['PUMA'].astype(str).str.zfill(5).map(county_map).fillna(1)
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
        logger.info("Processing household data...")
        
        # Add county mapping
        df = self.county_mapper.add_county_mapping(df)
        
        # Create group quarters type
        df = self._create_group_quarters_type(df)
        
        # Handle HUPAC (Household Under Poverty Level)
        df = self._handle_hupac(df)
        
        # Clean numeric data
        df = self.data_cleaner.clean_numeric_columns(df, "household")
        
        # Convert to integers
        integer_fields = ['HUPAC', 'NP', 'hhgqtype', 'WGTP', 'TYPEHUGQ', 'PUMA', 'COUNTY']
        df = self.data_cleaner.convert_to_integers(df, integer_fields, "household")
        
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

class PersonProcessor:
    """Processes person data for PopulationSim compatibility"""
    
    def __init__(self, config: SeedPopulationConfig):
        self.config = config
        self.county_mapper = PUMACountyMapper()
        self.data_cleaner = DataCleaner()
    
    def process_persons(self, df: pd.DataFrame, household_df: pd.DataFrame) -> pd.DataFrame:
        """Process person data for PopulationSim"""
        logger.info("Processing person data...")
        
        # Add county mapping
        df = self.county_mapper.add_county_mapping(df)
        
        # Create employment categories
        df = self._create_employment_status(df)
        
        # Create student status
        df = self._create_student_status(df)
        
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
        """Create person type categories by age"""
        df['person_type'] = 1  # Default
        df.loc[df['AGEP'] < 5, 'person_type'] = 1   # Preschool
        df.loc[(df['AGEP'] >= 5) & (df['AGEP'] < 18), 'person_type'] = 2  # School age
        df.loc[(df['AGEP'] >= 18) & (df['AGEP'] < 65), 'person_type'] = 3  # Working age
        df.loc[df['AGEP'] >= 65, 'person_type'] = 4  # Senior
        return df
    
    def _create_occupation_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create occupation categories from OCCP codes"""
        df['occupation'] = 0  # Default to not applicable
        df.loc[(df['OCCP'] >= 10) & (df['OCCP'] <= 950), 'occupation'] = 1    # Management
        df.loc[(df['OCCP'] >= 1005) & (df['OCCP'] <= 3540), 'occupation'] = 2  # Professional
        df.loc[(df['OCCP'] >= 3601) & (df['OCCP'] <= 4650), 'occupation'] = 3  # Services
        df.loc[(df['OCCP'] >= 4700) & (df['OCCP'] <= 5940), 'occupation'] = 4  # Sales/Office
        df.loc[(df['OCCP'] >= 6005) & (df['OCCP'] <= 9750), 'occupation'] = 5  # Manual
        df.loc[(df['OCCP'] >= 9800) & (df['OCCP'] <= 9830), 'occupation'] = 6  # Military
        return df
    
    def _map_group_quarters_type(self, df: pd.DataFrame, household_df: pd.DataFrame) -> pd.DataFrame:
        """Map group quarters type from household data"""
        hh_gq_lookup = household_df.set_index('unique_hh_id')['hhgqtype'].to_dict()
        df['hhgqtype'] = df['unique_hh_id'].map(hh_gq_lookup).fillna(1).astype(int)
        return df

class SeedPopulationCreator:
    """Main class for creating seed population"""
    
    def __init__(self, config: Optional[SeedPopulationConfig] = None):
        self.config = config or SeedPopulationConfig()
        self.household_processor = HouseholdProcessor(self.config)
        self.person_processor = PersonProcessor(self.config)
    
    def create_seed_population(self) -> bool:
        """Main method to create seed population"""
        try:
            logger.info(f"Creating seed population for {len(self.config.bay_area_pumas)} Bay Area PUMAs")
            logger.info("=" * 70)
            
            # Define file paths
            h_raw = self.config.output_dir / "households_2023_raw.csv"
            p_raw = self.config.output_dir / "persons_2023_raw.csv"
            h_processed = self.config.output_dir / "households_2023_tm2.csv"
            p_processed = self.config.output_dir / "persons_2023_tm2.csv"
            
            # Step 1: Load data from M: drive or use existing processed files
            if h_processed.exists() and p_processed.exists():
                logger.info("Using existing processed TM2 files...")
                household_df = pd.read_csv(h_processed)
                person_df = pd.read_csv(p_processed)
                logger.info(f"Loaded {len(household_df):,} households and {len(person_df):,} persons")
                
                # Step 4: Create PopulationSim-compatible copies
                import shutil
                seed_h = self.config.output_dir / "seed_households.csv"
                seed_p = self.config.output_dir / "seed_persons.csv"
                shutil.copy2(h_processed, seed_h)
                shutil.copy2(p_processed, seed_p)
                logger.info("Created PopulationSim-compatible seed file copies")
                
                # Step 5: Generate validation report
                self._generate_validation_report(household_df, person_df)
                
                logger.info("SUCCESS: PopulationSim seed population created successfully!")
                return True
                
            else:
                # Load from M: drive PUMS files
                logger.info("Loading PUMS data from M: drive...")
                m_drive_pums_dir = Path("M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23")
                household_file = m_drive_pums_dir / "hbayarea1923.csv"
                person_file = m_drive_pums_dir / "pbayarea1923.csv"
                
                if household_file.exists() and person_file.exists():
                    household_data = pd.read_csv(household_file)
                    person_data = pd.read_csv(person_file)
                    logger.info(f"Loaded {len(household_data):,} households and {len(person_data):,} persons from M: drive")
                else:
                    logger.error(f"M: drive PUMS files not found: {household_file}, {person_file}")
                    return False
            
            # Step 2: Process raw data (only if we didn't use existing processed files)
            logger.info("Processing raw PUMS data for PopulationSim compatibility...")
            
            # Use the data we just downloaded (already in memory)
            household_df = household_data
            person_df = person_data
            logger.info(f"Loaded {len(household_df):,} households and {len(person_df):,} persons")
            
            # Process households
            household_df = self.household_processor.process_households(household_df)
            
            # Calculate household workers before processing persons
            household_df = self._calculate_household_workers(household_df, person_df)
            
            # Process persons
            person_df = self.person_processor.process_persons(person_df, household_df)
            
            # Step 3: Final processing
            household_df = self._finalize_household_data(household_df)
            person_df = self._finalize_person_data(person_df)
            
            # Step 4: Save processed files
            self._save_processed_files(household_df, person_df, h_processed, p_processed)
            
            # Step 4b: Create PopulationSim-compatible copies (to save space, just copy instead of saving twice)
            import shutil
            seed_h = self.config.output_dir / "seed_households.csv"
            seed_p = self.config.output_dir / "seed_persons.csv"
            shutil.copy2(h_processed, seed_h)
            shutil.copy2(p_processed, seed_p)
            logger.info("Created PopulationSim-compatible seed file copies")
            
            # Step 5: Generate validation report
            self._generate_validation_report(household_df, person_df)
            
            logger.info("SUCCESS: PopulationSim seed population created successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create seed population: {e}")
            return False
    
    def _calculate_household_workers(self, household_df: pd.DataFrame, person_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate household workers from person employment status"""
        logger.info("Calculating household workers from employment status...")
        
        # Create temporary employed field for aggregation
        person_df['temp_employed'] = 0
        person_df.loc[person_df['ESR'].isin([1, 2, 4, 5]), 'temp_employed'] = 1
        
        # Aggregate by household
        workers_df = (person_df[['unique_hh_id', 'temp_employed']]
                     .groupby(['unique_hh_id'])
                     .sum()
                     .rename(columns={"temp_employed": "hh_workers_from_esr"}))
        
        # Merge with household data
        household_df = household_df.merge(workers_df, left_on='unique_hh_id', right_index=True, how='left')
        household_df['hh_workers_from_esr'] = household_df['hh_workers_from_esr'].fillna(0).astype(int)
        
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
        
        return df
    
    def _finalize_person_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Final processing for person data"""
        # Add unique person ID if not present
        if 'unique_person_id' not in df.columns:
            df['unique_person_id'] = range(1, len(df) + 1)
        
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
    
    def _save_processed_files(self, household_df: pd.DataFrame, person_df: pd.DataFrame, 
                            h_path: Path, p_path: Path) -> None:
        """Save processed files with validation"""
        logger.info("Writing PopulationSim-compatible files...")
        
        # Validate data before saving
        self._validate_data(household_df, "household")
        self._validate_data(person_df, "person")
        
        # Save files
        household_df.to_csv(h_path, index=False)
        person_df.to_csv(p_path, index=False)
        
        logger.info(f"Household file written: {h_path} ({len(household_df):,} records)")
        logger.info(f"Person file written: {p_path} ({len(person_df):,} records)")
    
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
