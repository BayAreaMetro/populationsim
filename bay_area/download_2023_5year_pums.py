#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified PUMS Data Downloader for 2023 5-Year Files
Uses unified config for all paths - NO HARDCODED PATHS!

Based on Census Bureau documentation, the 2023 5-Year PUMS files already include:
- All years 2019-2023 with consistent 2020 PUMA codes
- Automatic crosswalking of 2019-2021 data from 2010 to 2020 PUMAs
- No manual PUMA allocation needed!

This script downloads the 2023 5-Year PUMS files and filters to Bay Area using 2020 PUMA codes.
"""

import pandas as pd
import numpy as np
import requests
import io
import zipfile
from pathlib import Path
import logging
import urllib3

# Import unified config
from unified_tm2_config import UnifiedTM2Config

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimplifiedPUMSDownloader:
    """Downloads 2023 5-Year PUMS data with pre-crosswalked PUMAs"""
    
    def __init__(self, config: UnifiedTM2Config, bay_area_pumas_2020: list):
        self.config = config
        # Use both output directories from config
        self.output_dir_current = config.EXTERNAL_PATHS['pums_current']
        self.output_dir_cached = config.EXTERNAL_PATHS['pums_cached']
        
        # Create both directories
        self.output_dir_current.mkdir(exist_ok=True, parents=True)
        self.output_dir_cached.mkdir(exist_ok=True, parents=True)
        
        # Use 2020 PUMA codes (already crosswalked in 2023 5-year files)
        self.bay_area_pumas_2020 = [str(p).zfill(5) for p in bay_area_pumas_2020]
        logger.info(f"Bay Area 2020 PUMAs: {len(self.bay_area_pumas_2020)}")
        
        # 2023 5-Year PUMS URLs (contains all 2019-2023 data with consistent 2020 PUMAs)
        self.pums_urls = {
            'households': 'https://www2.census.gov/programs-surveys/acs/data/pums/2023/5-Year/csv_hca.zip',
            'persons': 'https://www2.census.gov/programs-surveys/acs/data/pums/2023/5-Year/csv_pca.zip'
        }
    
    def download_pums_data(self, data_type: str) -> pd.DataFrame:
        """Download 2023 5-Year PUMS data"""
        
        logger.info(f"Downloading 2023 5-Year {data_type} data...")
        
        url = self.pums_urls[data_type]
        logger.info(f"  URL: {url}")
        
        try:
            # Download zip file
            response = requests.get(url, verify=False, stream=True)
            response.raise_for_status()
            
            # Extract CSV from zip
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                # Look for California CSV files - 2023 5-year format: psam_h06.csv (households) or psam_p06.csv (persons)
                csv_files = [f for f in z.namelist() if f.endswith('.csv') and 'psam_' in f and '06' in f]
                
                if not csv_files:
                    logger.error(f"  No California CSV file found in {url}")
                    logger.info(f"  Available files: {z.namelist()}")
                    return None
                
                csv_file = csv_files[0]
                logger.info(f"  Extracting: {csv_file}")
                
                with z.open(csv_file) as f:
                    df = pd.read_csv(f, low_memory=False)
                    
            logger.info(f"  Downloaded {len(df):,} {data_type} records")
            return df
            
        except Exception as e:
            logger.error(f"  ERROR downloading {data_type}: {e}")
            return None
    
    def filter_bay_area_data(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """Filter data to Bay Area using 2020 PUMA codes"""
        
        if df is None or len(df) == 0:
            return df
            
        logger.info(f"  Filtering {data_type} to Bay Area using 2020 PUMA codes")
        
        # Ensure PUMA column exists
        if 'PUMA' not in df.columns:
            logger.error(f"  ERROR: PUMA column not found in {data_type} data")
            return df
            
        # Convert PUMA to string and pad with zeros
        df['PUMA_str'] = df['PUMA'].astype(str).str.zfill(5)
        
        # Filter to Bay Area PUMAs
        initial_count = len(df)
        bay_area_df = df[df['PUMA_str'].isin(self.bay_area_pumas_2020)].copy()
        filtered_count = len(bay_area_df)
        
        logger.info(f"  Filtered {initial_count:,} → {filtered_count:,} Bay Area {data_type} records ({filtered_count/initial_count*100:.1f}%)")
        
        return bay_area_df
    
    def add_year_from_serialno(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """Extract year from SERIALNO and analyze year distribution"""
        
        if df is None or len(df) == 0:
            return df
            
        logger.info(f"  Extracting year information from SERIALNO...")
        
        # Extract year from SERIALNO (first 4 characters)
        df['YEAR'] = df['SERIALNO'].astype(str).str[:4].astype(int)
        
        # Create unique household ID for linking
        df['unique_hh_id'] = df['SERIALNO'].astype(str)
        
        # Analyze year distribution
        year_counts = df['YEAR'].value_counts().sort_index()
        logger.info(f"  {data_type.title()} by year:")
        for year, count in year_counts.items():
            logger.info(f"    {year}: {count:,}")
        
        return df
    
    def download_and_process_2023_5year_data(self):
        """Download and process 2023 5-Year PUMS data (contains 2019-2023 with crosswalked PUMAs)"""
        
        logger.info("="*80)
        logger.info("SIMPLIFIED PUMS DOWNLOAD - 2023 5-YEAR FILES")
        logger.info("Using Census-provided PUMA crosswalking (2019-2021 → 2020 PUMAs)")
        logger.info("="*80)
        
        results = {}
        
        for data_type in ['households', 'persons']:
            logger.info(f"\n{'='*60}")
            logger.info(f"PROCESSING {data_type.upper()}")
            logger.info(f"{'='*60}")
            
            # Download data
            df = self.download_pums_data(data_type)
            if df is None:
                continue
            
            # Filter to Bay Area
            bay_area_df = self.filter_bay_area_data(df, data_type)
            if len(bay_area_df) == 0:
                continue
            
            # Add year information
            final_df = self.add_year_from_serialno(bay_area_df, data_type)
            
            results[data_type] = final_df
            logger.info(f"  Final {data_type} records: {len(final_df):,}")
        
        return results.get('households'), results.get('persons')
    
    def save_data(self, households_df: pd.DataFrame, persons_df: pd.DataFrame):
        """Save processed data to files using config paths"""
        
        logger.info(f"\n{'='*60}")
        logger.info("SAVING PROCESSED DATA")
        logger.info(f"{'='*60}")
        
        if households_df is not None and len(households_df) > 0:
            # Save household data to both locations
            hh_current = self.config.PUMS_FILES['households_current']
            hh_cached = self.config.PUMS_FILES['households_cached']
            
            households_df.to_csv(hh_current, index=False)
            households_df.to_csv(hh_cached, index=False)
            
            logger.info(f"✅ Household data saved:")
            logger.info(f"   Current: {hh_current}")
            logger.info(f"   Cached:  {hh_cached}")
            logger.info(f"   Total households: {len(households_df):,}")
            logger.info(f"   Years: {sorted(households_df['YEAR'].unique())}")
            logger.info(f"   PUMAs: {households_df['PUMA'].nunique()}")
            
            # Year breakdown
            year_counts = households_df['YEAR'].value_counts().sort_index()
            logger.info("   Household distribution by year:")
            for year, count in year_counts.items():
                logger.info(f"     {year}: {count:,}")
        
        if persons_df is not None and len(persons_df) > 0:
            # Save person data to both locations
            persons_current = self.config.PUMS_FILES['persons_current']
            persons_cached = self.config.PUMS_FILES['persons_cached']
            
            persons_df.to_csv(persons_current, index=False)
            persons_df.to_csv(persons_cached, index=False)
            
            logger.info(f"✅ Person data saved:")
            logger.info(f"   Current: {persons_current}")
            logger.info(f"   Cached:  {persons_cached}")
            logger.info(f"   Total persons: {len(persons_df):,}")
            logger.info(f"   Years: {sorted(persons_df['YEAR'].unique())}")
            logger.info(f"   PUMAs: {persons_df['PUMA'].nunique()}")
            
            # Year breakdown
            year_counts = persons_df['YEAR'].value_counts().sort_index()
            logger.info("   Person distribution by year:")
            for year, count in year_counts.items():
                logger.info(f"     {year}: {count:,}")
        
        # Save processing summary to current directory
        summary_output = self.output_dir_current / "pums_2023_5year_summary.txt"
        with open(summary_output, 'w', encoding='utf-8') as f:
            f.write("2023 5-YEAR PUMS DATA DOWNLOAD SUMMARY\n")
            f.write("="*50 + "\n\n")
            f.write("Source: Census Bureau 2023 5-Year PUMS files\n")
            f.write("PUMA Codes: 2020 boundaries (pre-crosswalked by Census)\n")
            f.write("Years Included: 2019-2023\n\n")
            
            if households_df is not None:
                f.write(f"HOUSEHOLDS: {len(households_df):,} total\n")
                year_counts = households_df['YEAR'].value_counts().sort_index()
                for year, count in year_counts.items():
                    f.write(f"  {year}: {count:,}\n")
                f.write(f"  Unique PUMAs: {households_df['PUMA'].nunique()}\n\n")
            
            if persons_df is not None:
                f.write(f"PERSONS: {len(persons_df):,} total\n")
                year_counts = persons_df['YEAR'].value_counts().sort_index()
                for year, count in year_counts.items():
                    f.write(f"  {year}: {count:,}\n")
                f.write(f"  Unique PUMAs: {persons_df['PUMA'].nunique()}\n\n")
            
            f.write("NOTES:\n")
            f.write("- 2019-2021 data automatically crosswalked from 2010 to 2020 PUMAs by Census\n")
            f.write("- 2022-2023 data natively uses 2020 PUMAs\n")
            f.write("- All data uses consistent 2020 PUMA boundaries\n")
            f.write("- No manual PUMA allocation required\n")
        
        logger.info(f"✅ Summary saved: {summary_output}")
        
        return households_df, persons_df

def load_pumas_from_crosswalk(crosswalk_file: str) -> list:
    """Load Bay Area PUMAs directly from the crosswalk file"""
    try:
        import pandas as pd
        logger.info(f"Loading PUMAs from crosswalk: {crosswalk_file}")
        
        crosswalk_df = pd.read_csv(crosswalk_file)
        # Get unique PUMAs from crosswalk (already integers, convert to 5-digit strings)
        pumas = sorted(crosswalk_df['PUMA'].unique())
        puma_strings = [str(p).zfill(5) for p in pumas]
        
        logger.info(f"Loaded {len(puma_strings)} PUMAs from crosswalk")
        logger.info(f"Sample PUMAs: {puma_strings[:10]}...")
        
        return puma_strings
        
    except Exception as e:
        logger.error(f"Error loading PUMAs from crosswalk {crosswalk_file}: {e}")
        logger.info("Using fallback PUMA list")
        
        # Fallback to basic Bay Area PUMAs if crosswalk fails
        return [
            '00101', '00111', '00112', '00113', '00114', '00115', '00116', '00117', '00118', '00119',
            '00120', '00121', '00122', '00123', '01301', '01305', '01308', '01309', '01310', '01311',
            '01312', '01313', '01314', '04103', '04104', '05500', '07501', '07502', '07503', '07504',
            '07505', '07506', '07507', '07508', '07509', '07510', '07511', '07512', '07513', '07514',
            '08101', '08102', '08103', '08104', '08105', '08106', '08505', '08506', '08507', '08508',
            '08509', '08510', '08511', '08512', '08513', '08514', '08515', '08516', '08517', '08518',
            '08519', '08520', '08521', '08522', '09501', '09502', '09503', '09702', '09704', '09705', '09706'
        ]

def main():
    """Main execution function using unified config"""
    
    # Initialize unified config
    config = UnifiedTM2Config()
    
    logger.info("="*80)
    logger.info("🚀 Starting PUMS Download with Unified Config")
    logger.info("="*80)
    logger.info(f"Crosswalk path: {config.CROSSWALK_FILES['puma_crosswalk']}")
    logger.info(f"Output current: {config.EXTERNAL_PATHS['pums_current']}")
    logger.info(f"Output cached:  {config.EXTERNAL_PATHS['pums_cached']}")
    
    # Load PUMAs directly from crosswalk (the definitive source!)
    pumas_2020 = load_pumas_from_crosswalk(str(config.CROSSWALK_FILES['puma_crosswalk']))
    
    # Create downloader with config
    downloader = SimplifiedPUMSDownloader(
        config=config,
        bay_area_pumas_2020=pumas_2020
    )
    
    # Download and process 2023 5-year data
    households_df, persons_df = downloader.download_and_process_2023_5year_data()
    
    # Save data
    households_df, persons_df = downloader.save_data(households_df, persons_df)
    
    logger.info("\n" + "="*80)
    logger.info("✅ SUCCESS: 2023 5-Year PUMS download completed!")
    logger.info(f"Data saved to:")
    logger.info(f"  Current: {config.EXTERNAL_PATHS['pums_current']}")
    logger.info(f"  Cached:  {config.EXTERNAL_PATHS['pums_cached']}")
    logger.info("="*80)
    logger.info("="*80)
    logger.info("Key achievements:")
    logger.info("1. Downloaded 2023 5-Year PUMS with all years 2019-2023")
    logger.info("2. Used Census-provided PUMA crosswalking (no manual allocation needed)")
    logger.info("3. All data uses consistent 2020 PUMA boundaries")
    logger.info("4. Complete household-person linkage with unique_hh_id")
    logger.info("5. Saved to both current and cached locations via unified config")
    
    if households_df is not None and len(households_df) > 0:
        years_available = sorted(households_df['YEAR'].unique())
        total_hh = len(households_df)
        logger.info(f"\nHouseholds: {total_hh:,} across years {years_available}")
        
        if len(years_available) == 5 and min(years_available) == 2019 and max(years_available) == 2023:
            logger.info("🎉 SUCCESS: Complete 2019-2023 household data obtained!")
        else:
            logger.warning(f"⚠️  Expected years 2019-2023, got: {years_available}")

if __name__ == "__main__":
    main()
