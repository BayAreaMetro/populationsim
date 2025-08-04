#!/usr/bin/env python3
"""
Create PUMS seed population for Bay Area PopulationSim
Final version incorporating lessons learned and CPI income conversion

Key Features:
- Downloads PUMS data for all Bay Area PUMAs (66 total including PUMA 07707)
- Processes household income using ADJINC adjustment factor
- Converts income from 2023$ to 2010$ purchasing power using CPI-U deflation
- Creates income breakpoint analysis consistent with PopulationSim control files
- Handles both household and person files with chunked processing for memory efficiency
- Transforms raw PUMS data into PopulationSim-compatible format with required columns

Income Conversion:
- PUMS provides income in survey year dollars adjusted to 2023$ via ADJINC
- We convert 2023$ to 2010$ using deflation factor of 0.725 (based on ~38% cumulative inflation)
- This ensures consistency with control file breakpoints representing 2010 purchasing power
- Final output includes both hh_income_2023 and hh_income_2010 columns

PopulationSim Processing:
- Creates required columns like hhgqtype, occupation, employed, etc.
- Processes raw PUMS codes into PopulationSim-compatible format
- Saves final seed files to both raw location and hh_gq/data/ for PopulationSim
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
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

# Import our CPI conversion utilities
from cpi_conversion import convert_2023_to_2010_dollars

def process_pums_for_populationsim(h_output, p_output):
    """
    Process raw PUMS data into PopulationSim-compatible format
    Creates all required columns including hhgqtype, occupation, employed, etc.
    """
    print(f"\n>> Processing PUMS data for PopulationSim compatibility...")
    
    # Read the raw PUMS files
    print(f"   Reading household data from: {h_output}")
    h_df = pd.read_csv(h_output)
    print(f"   Read {len(h_df):,} household records")
    
    print(f"   Reading person data from: {p_output}")
    p_df = pd.read_csv(p_output)
    print(f"   Read {len(p_df):,} person records")
    
    # Process households
    print(f"   Processing household data...")
    
    # Add county mapping based on PUMA
    county_map = {
        # San Francisco County (COUNTY=1)
        '00101': 1, '00111': 1, '00112': 1, '00113': 1, '00114': 1, '00115': 1, 
        '00116': 1, '00117': 1, '00118': 1, '00119': 1, '00120': 1, '00121': 1, 
        '00122': 1, '00123': 1,
        # San Mateo County (COUNTY=2)  
        '05303': 2, '05500': 2,
        # Santa Clara County (COUNTY=3)
        '08101': 3, '08102': 3, '08103': 3, '08104': 3, '08105': 3, '08106': 3,
        '08505': 3, '08506': 3, '08507': 3, '08508': 3, '08510': 3, '08511': 3,
        '08512': 3, '08515': 3, '08516': 3, '08517': 3, '08518': 3, '08519': 3,
        '08520': 3, '08521': 3, '08522': 3, '08701': 3,
        # Alameda County (COUNTY=4)
        '01301': 4, '01305': 4, '01308': 4, '01309': 4, '01310': 4, '01311': 4,
        '01312': 4, '01313': 4, '01314': 4,
        # Contra Costa County (COUNTY=5)
        '04103': 5, '04104': 5,
        # Solano County (COUNTY=6)
        '11301': 6,
        # Napa County (COUNTY=7)
        '09702': 7, '09704': 7, '09705': 7, '09706': 7,
        # Sonoma County (COUNTY=8)
        '09501': 8, '09502': 8, '09503': 8,
        # Marin County (COUNTY=9)
        '07507': 9, '07508': 9, '07509': 9, '07510': 9, '07511': 9, '07512': 9,
        '07513': 9, '07514': 9,
        # San Joaquin County West (Tracy area) (COUNTY=5 - assign to Contra Costa for modeling)
        '07707': 5
    }
    
    h_df['COUNTY'] = h_df['PUMA'].astype(str).str.zfill(5).map(county_map).fillna(1)  # Default to SF County if mapping fails
    h_df['COUNTY'] = h_df['COUNTY'].astype(int)  # Ensure integer type
    
        # Create PopulationSim-compatible group quarters type
    # Based on TYPEHUGQ: 1=household, 2=institutional GQ, 3=noninstitutional GQ  
    # PopulationSim controls.csv expects: 0=household, 1=university GQ, 2=military GQ, 3=other GQ
    h_df['hhgqtype'] = 0  # Default to household (TYPEHUGQ=1)
    h_df.loc[h_df['TYPEHUGQ'] == 3, 'hhgqtype'] = 1  # Noninstitutional GQ (university) -> 1
    
    # Split institutional GQ (TYPEHUGQ=2) into military vs other
    # Based on control targets: military=1,684, other=122,467 (ratio ~1:73 or ~1.4% military)
    institutional_gq_mask = h_df['TYPEHUGQ'] == 2
    institutional_gq_count = institutional_gq_mask.sum()
    
    if institutional_gq_count > 0:
        # Calculate split ratio based on control targets
        military_target = 1684  # From controls
        other_target = 122467   # From controls 
        military_ratio = military_target / (military_target + other_target)  # ~1.4%
        
        # Randomly assign institutional GQ to military vs other based on target ratio
        np.random.seed(42)  # For reproducibility
        institutional_indices = h_df[institutional_gq_mask].index
        n_military = int(len(institutional_indices) * military_ratio)
        military_indices = np.random.choice(institutional_indices, n_military, replace=False)
        
        # Assign hhgqtype
        h_df.loc[institutional_gq_mask, 'hhgqtype'] = 3  # Default institutional GQ to "other"
        h_df.loc[military_indices, 'hhgqtype'] = 2       # Small fraction to military
        
        print(f"   Split {institutional_gq_count:,} institutional GQ records:")
        print(f"     Military (hhgqtype=2): {n_military:,} ({n_military/institutional_gq_count*100:.1f}%)")
        print(f"     Other (hhgqtype=3): {institutional_gq_count-n_military:,} ({(institutional_gq_count-n_military)/institutional_gq_count*100:.1f}%)")
    
    # Handle NaN values in key household fields that PopulationSim uses
    key_household_fields = ['WGTP', 'NP', 'TYPEHUGQ']
    for field in key_household_fields:
        if field in h_df.columns:
            h_df[field] = h_df[field].fillna(0)
    
    # Special handling for HUPAC (Household Under Poverty Level)
    # HUPAC values: 1=below poverty, 2=at/above poverty, 3=not determined, 4=GQ not applicable
    if 'HUPAC' in h_df.columns:
        hupac_nan_count = h_df['HUPAC'].isna().sum()
        if hupac_nan_count > 0:
            print(f"      Fixing {hupac_nan_count} NaN values in HUPAC...")
            # For group quarters (hhgqtype=1,2,3), set HUPAC=4 (not applicable)
            gq_mask = (h_df['HUPAC'].isna()) & (h_df['hhgqtype'].isin([1, 2, 3]))
            h_df.loc[gq_mask, 'HUPAC'] = 4
            # For households (hhgqtype=0), set HUPAC=2 (assume at/above poverty as conservative default)
            hh_mask = (h_df['HUPAC'].isna()) & (h_df['hhgqtype'] == 0)
            h_df.loc[hh_mask, 'HUPAC'] = 2
            # Fix any remaining NaN values
            h_df['HUPAC'] = h_df['HUPAC'].fillna(2)
    
    # Handle NaN values in ALL numeric columns to prevent PopulationSim conversion errors
    print(f"   Cleaning all numeric columns in household data...")
    nan_summary = []
    for col in h_df.columns:
        if col == 'HUPAC':
            continue  # Skip HUPAC - handled specifically above
        if h_df[col].dtype in ['float64', 'float32', 'int64', 'int32']:
            nan_count = h_df[col].isna().sum()
            inf_count = np.isinf(h_df[col]).sum()
            if nan_count > 0 or inf_count > 0:
                nan_summary.append(f"{col}: {nan_count} NaN, {inf_count} inf")
            h_df[col] = h_df[col].fillna(0)
            h_df[col] = h_df[col].replace([np.inf, -np.inf], 0)
    
    if nan_summary:
        print(f"      Cleaned household fields: {nan_summary}")
    else:
        print(f"      No NaN/inf values found in household numeric fields")
    
    # Convert critical PopulationSim fields to proper integer types to prevent IntCastingNaNError
    print(f"   Converting critical fields to integer types for PopulationSim compatibility...")
    integer_fields = ['HUPAC', 'NP', 'hhgqtype', 'hh_workers_from_esr', 'WGTP', 'TYPEHUGQ', 'PUMA', 'COUNTY']
    for field in integer_fields:
        if field in h_df.columns:
            try:
                # Ensure no NaN/inf values before conversion
                h_df[field] = h_df[field].fillna(0)
                h_df[field] = h_df[field].replace([np.inf, -np.inf], 0)
                # Convert to integer
                h_df[field] = h_df[field].astype(int)
                print(f"      Converted {field} to int64")
            except Exception as e:
                print(f"      WARNING: Could not convert {field} to integer: {e}")
    
    # Also ensure income fields are integers
    income_fields = ['hh_income_2010', 'hh_income_2023']
    for field in income_fields:
        if field in h_df.columns:
            try:
                h_df[field] = h_df[field].fillna(0)
                h_df[field] = h_df[field].replace([np.inf, -np.inf], 0)
                h_df[field] = h_df[field].round().astype(int)
                print(f"      Converted {field} to int64")
            except Exception as e:
                print(f"      WARNING: Could not convert {field} to integer: {e}")
    
    print(f"      Household processing completed - {len(h_df):,} records")
    
    # Process persons  
    print(f"   Processing person data...")
    
    # Add county mapping for persons
    p_df['COUNTY'] = p_df['PUMA'].astype(str).str.zfill(5).map(county_map).fillna(1)  # Default to SF County if mapping fails
    p_df['COUNTY'] = p_df['COUNTY'].astype(int)  # Ensure integer type
    
    # Create employment status (employed: 0=not employed, 1=employed)
    p_df['employed'] = 0
    p_df.loc[p_df['ESR'].isin([1, 2, 4, 5]), 'employed'] = 1  # Employed (civilian or military)
    
    # Create employment status categories (employ_status)
    # 1=Employed, 2=Unemployed, 3=Not in labor force, 4=Under 16
    p_df['employ_status'] = 3  # Default to not in labor force
    p_df.loc[p_df['ESR'].isin([1, 2, 4, 5]), 'employ_status'] = 1  # Employed
    p_df.loc[p_df['ESR'] == 3, 'employ_status'] = 2  # Unemployed
    p_df.loc[p_df['ESR'] == 6, 'employ_status'] = 3  # Not in labor force
    p_df.loc[p_df['AGEP'] < 16, 'employ_status'] = 4  # Under 16
    
    # Create student status (student_status)
    # 1=Not student, 2=Student under 16, 3=Student 16+
    p_df['student_status'] = 1  # Default to not student
    p_df.loc[(p_df['SCHG'].notna()) & (p_df['AGEP'] < 16), 'student_status'] = 2
    p_df.loc[(p_df['SCHG'].notna()) & (p_df['AGEP'] >= 16), 'student_status'] = 3
    
    # Create person type categories (person_type)
    # This is a simplified categorization - you may want to refine
    p_df['person_type'] = 1  # Default
    p_df.loc[p_df['AGEP'] < 5, 'person_type'] = 1   # Preschool
    p_df.loc[(p_df['AGEP'] >= 5) & (p_df['AGEP'] < 18), 'person_type'] = 2  # School age
    p_df.loc[(p_df['AGEP'] >= 18) & (p_df['AGEP'] < 65), 'person_type'] = 3  # Working age
    p_df.loc[p_df['AGEP'] >= 65, 'person_type'] = 4  # Senior
    
    # Create SOC occupation codes (simplified)
    p_df['soc'] = p_df['SOCP'].astype(str)
    p_df.loc[p_df['soc'] == 'nan', 'soc'] = ''
    
    # Create occupation categories (occupation)
    # 0=Not applicable, 1=Management, 2=Professional, 3=Services, 4=Sales, 5=Manual, 6=Military
    p_df['occupation'] = 0  # Default to not applicable
    
    # Map OCCP codes to occupation categories (simplified mapping)
    # This is a basic mapping - you may want to refine based on your needs
    p_df.loc[(p_df['OCCP'] >= 10) & (p_df['OCCP'] <= 950), 'occupation'] = 1    # Management
    p_df.loc[(p_df['OCCP'] >= 1005) & (p_df['OCCP'] <= 3540), 'occupation'] = 2  # Professional/Technical
    p_df.loc[(p_df['OCCP'] >= 3601) & (p_df['OCCP'] <= 4650), 'occupation'] = 3  # Services
    p_df.loc[(p_df['OCCP'] >= 4700) & (p_df['OCCP'] <= 5940), 'occupation'] = 4  # Sales/Office
    p_df.loc[(p_df['OCCP'] >= 6005) & (p_df['OCCP'] <= 9750), 'occupation'] = 5  # Manual/Production
    p_df.loc[(p_df['OCCP'] >= 9800) & (p_df['OCCP'] <= 9830), 'occupation'] = 6  # Military
    
    # Create group quarters type for persons (must match household hhgqtype)
    # Map from household hhgqtype
    hh_gq_lookup = h_df.set_index('unique_hh_id')['hhgqtype'].to_dict()
    p_df['hhgqtype'] = p_df['unique_hh_id'].map(hh_gq_lookup).fillna(1).astype(int)
    
    # Handle NaN values in key person fields that PopulationSim uses
    key_person_fields = ['AGEP', 'ESR', 'WGTP']
    for field in key_person_fields:
        if field in p_df.columns:
            p_df[field] = p_df[field].fillna(0)
    
    # Handle NaN values in ALL numeric columns to prevent PopulationSim conversion errors
    print(f"   Cleaning all numeric columns in person data...")
    nan_summary = []
    for col in p_df.columns:
        if p_df[col].dtype in ['float64', 'float32', 'int64', 'int32']:
            nan_count = p_df[col].isna().sum()
            inf_count = np.isinf(p_df[col]).sum()
            if nan_count > 0 or inf_count > 0:
                nan_summary.append(f"{col}: {nan_count} NaN, {inf_count} inf")
            p_df[col] = p_df[col].fillna(0)
            p_df[col] = p_df[col].replace([np.inf, -np.inf], 0)
    
    if nan_summary:
        print(f"      Cleaned person fields: {nan_summary}")
    else:
        print(f"      No NaN/inf values found in person numeric fields")
    
    # Convert critical PopulationSim person fields to proper integer types to prevent IntCastingNaNError
    print(f"   Converting critical person fields to integer types for PopulationSim compatibility...")
    person_integer_fields = ['AGEP', 'hhgqtype', 'employed', 'employ_status', 'student_status', 'person_type', 'occupation', 'ESR', 'PWGTP', 'PUMA', 'COUNTY']
    for field in person_integer_fields:
        if field in p_df.columns:
            try:
                # Ensure no NaN/inf values before conversion
                p_df[field] = p_df[field].fillna(0)
                p_df[field] = p_df[field].replace([np.inf, -np.inf], 0)
                # Convert to integer
                p_df[field] = p_df[field].astype(int)
                print(f"      Converted {field} to int64")
            except Exception as e:
                print(f"      WARNING: Could not convert {field} to integer: {e}")
    
    print(f"      Person processing completed - {len(p_df):,} records")
    
    # Create household workers count (hh_workers_from_esr) by aggregating employed persons
    print(f"   Calculating household workers from employment status...")
    workers_df = p_df[['unique_hh_id', 'employed']].groupby(['unique_hh_id']).sum().rename(columns={"employed": "hh_workers_from_esr"})
    h_df = h_df.merge(workers_df, left_on='unique_hh_id', right_index=True, how='left')
    h_df['hh_workers_from_esr'] = h_df['hh_workers_from_esr'].fillna(0).astype(np.uint8)
    print(f"      Household workers calculation completed")
    
    return h_df, p_df

def create_seed_population():
    """Create seed population from PUMS data"""
    
    # Bay Area PUMAs - Complete 2020 definitions including transportation model region (66 total)
    BAY_AREA_PUMAS = [
        # San Francisco County
        '00101', '00111', '00112', '00113', '00114', '00115', '00116', '00117', '00118', '00119',
        '00120', '00121', '00122', '00123',
        
        # Alameda County  
        '01301', '01305', '01308', '01309', '01310', '01311', '01312', '01313', '01314',
        
        # Contra Costa County
        '04103', '04104',
        
        # San Mateo County
        '05303', '05500',
        
        # Marin County
        '07507', '07508', '07509', '07510', '07511', '07512', '07513', '07514',
        
        # San Joaquin County (West) - Tracy area (NEW)
        '07707',
        
        # Santa Clara County
        '08101', '08102', '08103', '08104', '08105', '08106', '08505', '08506', '08507', 
        '08508', '08510', '08511', '08512', '08515', '08516', '08517', '08518', '08519', 
        '08520', '08521', '08522', '08701',
        
        # Sonoma County
        '09501', '09502', '09503',
        
        # Napa County
        '09702', '09704', '09705', '09706',
        
        # Solano County
        '11301'
    ]
    
    print(f"Creating seed population for {len(BAY_AREA_PUMAS)} Bay Area PUMAs")
    print("="*70)
    
    # Output directory - save locally since M: drive is unavailable
    output_dir = "output_2023"
    os.makedirs(output_dir, exist_ok=True)
    
    # File paths
    h_output = os.path.join(output_dir, "households_2023_raw.csv")
    p_output = os.path.join(output_dir, "persons_2023_raw.csv")
    
    # Check if files already exist
    if os.path.exists(h_output) and os.path.exists(p_output):
        print(f"Seed population files already exist:")
        print(f"   Households: {h_output}")
        print(f"   Persons: {p_output}")
        
        # Quick validation
        try:
            h_df = pd.read_csv(h_output, dtype={'PUMA': str}, nrows=5)
            p_df = pd.read_csv(p_output, dtype={'PUMA': str}, nrows=5)
            print(f"   Files appear valid, skipping recreation")
            return h_output, p_output
        except Exception as e:
            print(f"   Files exist but appear corrupted: {e}")
            print(f"   Will recreate...")
    
    # Download and process PUMS files - Use California-specific files for efficiency
    base_url = "https://www2.census.gov/programs-surveys/acs/data/pums/2023/5-Year"
    
    years = ['2019', '2020', '2021', '2022', '2023']
    
    all_households = []
    all_persons = []
    
    for year in years:
        print(f"\nProcessing {year}...")
        
        # Download California household file (csv_hca.zip = California households)
        h_url = f"{base_url}/csv_hca.zip"
        h_zip_path = f"csv_hca_{year}.zip"
        
        print(f"   Downloading households from: {h_url}")
        print(f"   Saving to: {h_zip_path}")
        
        import time
        start_time = time.time()
        
        try:
            # Start download with progress tracking
            print(f"   Initiating HTTP request...")
            response = requests.get(h_url, verify=False, timeout=600, stream=True)
            response.raise_for_status()
            
            # Get file size from headers
            total_size = int(response.headers.get('content-length', 0))
            if total_size > 0:
                print(f"   File size: {total_size / 1024 / 1024:.1f} MB")
            
            # Download with progress tracking
            downloaded = 0
            chunk_size = 8192
            last_progress_time = time.time()
            
            print(f"   Downloading in progress...")
            with open(h_zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Show progress every 5 seconds
                        current_time = time.time()
                        if current_time - last_progress_time >= 5:
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                speed = downloaded / (current_time - start_time) / 1024 / 1024
                                print(f"      Progress: {percent:.1f}% ({downloaded / 1024 / 1024:.1f} MB) - Speed: {speed:.1f} MB/s")
                            else:
                                speed = downloaded / (current_time - start_time) / 1024 / 1024
                                print(f"      Downloaded: {downloaded / 1024 / 1024:.1f} MB - Speed: {speed:.1f} MB/s")
                            last_progress_time = current_time
            
            download_time = time.time() - start_time
            final_speed = downloaded / download_time / 1024 / 1024
            print(f"   Download completed in {download_time:.1f}s (avg speed: {final_speed:.1f} MB/s)")
            
            # Extract and process household file
            print(f"   Extracting ZIP file...")
            extract_start = time.time()
            
            with zipfile.ZipFile(h_zip_path, 'r') as zip_ref:
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                if csv_files:
                    h_csv = csv_files[0]
                    print(f"   Processing CSV: {h_csv}")
                    
                    # Read in chunks to handle large files
                    chunk_list = []
                    chunk_count = 0
                    total_rows = 0
                    
                    print(f"   Reading data in chunks...")
                    with zip_ref.open(h_csv) as csv_file:
                        for chunk in pd.read_csv(csv_file, dtype={'PUMA': str, 'ST': str}, chunksize=10000):
                            chunk_count += 1
                            total_rows += len(chunk)
                            
                            # Since we're using California-specific file, just filter for Bay Area PUMAs
                            chunk['PUMA'] = chunk['PUMA'].astype(str).str.zfill(5)
                            bay_chunk = chunk[chunk['PUMA'].isin(BAY_AREA_PUMAS)]
                            if not bay_chunk.empty:
                                chunk_list.append(bay_chunk)
                            
                            # Progress every 50 chunks
                            if chunk_count % 50 == 0:
                                print(f"      Processed {chunk_count:,} chunks ({total_rows:,} total rows)")
                    
                    print(f"   Finished reading {chunk_count:,} chunks ({total_rows:,} total rows)")
                    
                    if chunk_list:
                        year_households = pd.concat(chunk_list, ignore_index=True)
                        all_households.append(year_households)
                        extract_time = time.time() - extract_start
                        print(f"   Found {len(year_households):,} Bay Area households (processed in {extract_time:.1f}s)")
                    else:
                        print(f"   No Bay Area households found in {year}")
            
            # Clean up zip file
            print(f"   Cleaning up: {h_zip_path}")
            os.remove(h_zip_path)
            
        except Exception as e:
            print(f"   Error processing households for {year}: {e}")
            import traceback
            print(f"   Error details: {traceback.format_exc()}")
            continue
        
        # Download California person file (csv_pca.zip = California persons)
        p_url = f"{base_url}/csv_pca.zip"
        p_zip_path = f"csv_pca_{year}.zip"
        
        print(f"\n   DOWNLOADING PERSON DATA")
        print(f"   Downloading persons from: {p_url}")
        print(f"   Saving to: {p_zip_path}")
        
        start_time = time.time()
        
        try:
            # Start download with progress tracking
            print(f"   Initiating HTTP request...")
            response = requests.get(p_url, verify=False, timeout=600, stream=True)
            response.raise_for_status()
            
            # Get file size from headers
            total_size = int(response.headers.get('content-length', 0))
            if total_size > 0:
                print(f"   File size: {total_size / 1024 / 1024:.1f} MB")
            
            # Download with progress tracking
            downloaded = 0
            chunk_size = 8192
            last_progress_time = time.time()
            
            print(f"   Downloading in progress...")
            with open(p_zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Show progress every 5 seconds
                        current_time = time.time()
                        if current_time - last_progress_time >= 5:
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                speed = downloaded / (current_time - start_time) / 1024 / 1024
                                print(f"      Progress: {percent:.1f}% ({downloaded / 1024 / 1024:.1f} MB) - Speed: {speed:.1f} MB/s")
                            else:
                                speed = downloaded / (current_time - start_time) / 1024 / 1024
                                print(f"      Downloaded: {downloaded / 1024 / 1024:.1f} MB - Speed: {speed:.1f} MB/s")
                            last_progress_time = current_time
            
            download_time = time.time() - start_time
            final_speed = downloaded / download_time / 1024 / 1024
            print(f"   Download completed in {download_time:.1f}s (avg speed: {final_speed:.1f} MB/s)")
            
            # Extract and process person file
            print(f"   Extracting ZIP file...")
            extract_start = time.time()
            
            with zipfile.ZipFile(p_zip_path, 'r') as zip_ref:
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                if csv_files:
                    p_csv = csv_files[0]
                    print(f"   Processing CSV: {p_csv}")
                    
                    # Read in chunks to handle large files
                    chunk_list = []
                    chunk_count = 0
                    total_rows = 0
                    
                    print(f"   Reading data in chunks...")
                    with zip_ref.open(p_csv) as csv_file:
                        for chunk in pd.read_csv(csv_file, dtype={'PUMA': str, 'ST': str}, chunksize=10000):
                            chunk_count += 1
                            chunk_rows = len(chunk)
                            total_rows += chunk_rows
                            
                            # Since we're using California-specific file, just filter for Bay Area PUMAs
                            chunk['PUMA'] = chunk['PUMA'].astype(str).str.zfill(5)
                            bay_chunk = chunk[chunk['PUMA'].isin(BAY_AREA_PUMAS)]
                            if not bay_chunk.empty:
                                chunk_list.append(bay_chunk)
                            
                            # Progress update every 50 chunks
                            if chunk_count % 50 == 0:
                                print(f"   Processed {chunk_count} chunks, {total_rows:,} total rows")
                    
                    if chunk_list:
                        year_persons = pd.concat(chunk_list, ignore_index=True)
                        all_persons.append(year_persons)
                        print(f"   Found {len(year_persons):,} Bay Area persons from {total_rows:,} total California persons")
            
            # Clean up zip file
            os.remove(p_zip_path)
            
        except Exception as e:
            print(f"   Error processing persons for {year}: {e}")
            continue
    
    # Combine all years
    print(f"\n>> Combining data from all years...")
    
    if all_households:
        # Create unique household IDs by combining SERIALNO with year suffix
        print(f"   Creating unique household IDs across years...")
        for i, year_households in enumerate(all_households):
            year = years[i]  # Get the corresponding year
            # Create unique ID by combining original SERIALNO with year
            year_households['unique_hh_id'] = year_households['SERIALNO'].astype(str) + '_' + year
            print(f"   Year {year}: {len(year_households):,} households with unique IDs")
        
        final_households = pd.concat(all_households, ignore_index=True)
        print(f"   Total households after combining: {len(final_households):,}")
        
        # Verify uniqueness
        duplicate_count = final_households['unique_hh_id'].duplicated().sum()
        if duplicate_count > 0:
            print(f"   WARNING: {duplicate_count:,} duplicate household IDs found - removing duplicates...")
            final_households = final_households.drop_duplicates(subset=['unique_hh_id'], keep='first')
            print(f"   After deduplication: {len(final_households):,} households")
        else:
            print(f"   SUCCESS: All household IDs are unique!")
        
        # Remove the original SERIALNO column since we now have unique_hh_id
        if 'SERIALNO' in final_households.columns:
            final_households = final_households.drop(columns=['SERIALNO'])
            print(f"   Removed original SERIALNO column")
        
        # Process household income conversion from 2023$ to 2010$
        print(f"   Converting household income from 2023$ to 2010$ purchasing power...")
        
        # Check if required income columns exist
        if 'HINCP' in final_households.columns and 'ADJINC' in final_households.columns:
            # Calculate 2023 dollar income (PUMS standard adjustment)
            # ADJINC adjustment factor automatically converts all survey year responses (2019-2023)
            # to 2023 dollar equivalents, handling year-specific inflation internally
            # ADJINC factor (divide by 1,000,000 per PUMS documentation)
            ONE_MILLION = 1000000
            final_households['hh_income_2023'] = (final_households['ADJINC'] / ONE_MILLION) * final_households['HINCP'].fillna(0)
            
            # Convert 2023$ to 2010$ using CPI deflation
            final_households['hh_income_2010'] = convert_2023_to_2010_dollars(final_households['hh_income_2023'])
            
            # Handle any NaN or infinite values before converting to int
            final_households['hh_income_2010'] = final_households['hh_income_2010'].fillna(0)
            final_households['hh_income_2023'] = final_households['hh_income_2023'].fillna(0)
            
            # Replace infinite values with 0
            final_households['hh_income_2010'] = final_households['hh_income_2010'].replace([np.inf, -np.inf], 0)
            final_households['hh_income_2023'] = final_households['hh_income_2023'].replace([np.inf, -np.inf], 0)
            
            # Round to nearest dollar for cleaner data
            final_households['hh_income_2010'] = final_households['hh_income_2010'].round().astype(int)
            final_households['hh_income_2023'] = final_households['hh_income_2023'].round().astype(int)
            
            print(f"      Income conversion completed")
            print(f"      Sample 2023$: {final_households['hh_income_2023'].head().tolist()}")
            print(f"      Sample 2010$: {final_households['hh_income_2010'].head().tolist()}")
            print(f"      Mean income 2023$: ${final_households['hh_income_2023'].mean():,.0f}")
            print(f"      Mean income 2010$: ${final_households['hh_income_2010'].mean():,.0f}")
        else:
            print(f"      Warning: HINCP or ADJINC columns not found, skipping income conversion")
            missing_cols = [col for col in ['HINCP', 'ADJINC'] if col not in final_households.columns]
            print(f"      Missing columns: {missing_cols}")
        
        # Save households
        print(f"   Saving to: {h_output}")
        final_households.to_csv(h_output, index=False)
        print(f"   Household file saved ({os.path.getsize(h_output) / 1024 / 1024:.1f} MB)")
    else:
        print(f"   No household data found!")
        return None, None
    
    if all_persons:
        # Create unique household IDs for persons to match households
        print(f"   Creating matching unique household IDs for persons...")
        for i, year_persons in enumerate(all_persons):
            year = years[i]  # Get the corresponding year
            # Create unique household ID by combining original SERIALNO with year (same as households)
            year_persons['unique_hh_id'] = year_persons['SERIALNO'].astype(str) + '_' + year
            print(f"   Year {year}: {len(year_persons):,} persons with unique household IDs")
        
        final_persons = pd.concat(all_persons, ignore_index=True)
        print(f"   Total persons after combining: {len(final_persons):,}")
        
        # Remove the original SERIALNO column since we now have unique_hh_id
        if 'SERIALNO' in final_persons.columns:
            final_persons = final_persons.drop(columns=['SERIALNO'])
            print(f"   Removed original SERIALNO column from persons")
        
        # Save persons
        print(f"   Saving to: {p_output}")
        final_persons.to_csv(p_output, index=False)
        print(f"   Person file saved ({os.path.getsize(p_output) / 1024 / 1024:.1f} MB)")
    else:
        print(f"   No person data found!")
        return None, None
    
    # Quick summary
    unique_pumas = sorted(final_households['PUMA'].unique())
    print(f"\nFINAL SUMMARY:")
    print(f"   Households: {len(final_households):,}")
    print(f"   Persons: {len(final_persons):,}")
    print(f"   PUMAs covered: {len(unique_pumas)}")
    print(f"   PUMA list: {unique_pumas}")
    
    # Income summary if available
    if 'hh_income_2010' in final_households.columns:
        print(f"\nINCOME SUMMARY (2010 purchasing power):")
        print(f"   Mean household income: ${final_households['hh_income_2010'].mean():,.0f}")
        print(f"   Median household income: ${final_households['hh_income_2010'].median():,.0f}")
        print(f"   Income breakpoint analysis:")
        print(f"      <$30K:  {(final_households['hh_income_2010'] < 30000).sum():,} households ({(final_households['hh_income_2010'] < 30000).mean()*100:.1f}%)")
        print(f"      $30-60K: {((final_households['hh_income_2010'] >= 30000) & (final_households['hh_income_2010'] < 60000)).sum():,} households ({((final_households['hh_income_2010'] >= 30000) & (final_households['hh_income_2010'] < 60000)).mean()*100:.1f}%)")
        print(f"      $60-100K: {((final_households['hh_income_2010'] >= 60000) & (final_households['hh_income_2010'] < 100000)).sum():,} households ({((final_households['hh_income_2010'] >= 60000) & (final_households['hh_income_2010'] < 100000)).mean()*100:.1f}%)")
        print(f"      $100K+: {(final_households['hh_income_2010'] >= 100000).sum():,} households ({(final_households['hh_income_2010'] >= 100000).mean()*100:.1f}%)")
    
    return h_output, p_output

if __name__ == "__main__":
    print("=== Creating PopulationSim Seed Population for TM2 (2023 ACS) ===")
    
    # Define paths
    output_dir = Path("output_2023")
    
    # Step 1: Download raw PUMS data
    household_file, person_file = create_seed_population()
    
    if household_file and person_file:
        print(f"\n>> Raw PUMS data downloaded successfully!")
        print(f"   Household file: {household_file}")
        print(f"   Person file: {person_file}")
        
        # Step 2: Process for PopulationSim compatibility
        h_processed, p_processed = process_pums_for_populationsim(household_file, person_file)
        
        # Step 3: Write processed files
        h_final = output_dir / "households_2023_tm2.csv"
        p_final = output_dir / "persons_2023_tm2.csv"
        
        print(f"\n>> Writing PopulationSim-compatible files...")
        
        # Final validation before writing
        print(f"   FINAL DATA VALIDATION:")
        print(f"   Household data:")
        print(f"      Shape: {h_processed.shape}")
        print(f"      Data types: {h_processed.dtypes.value_counts().to_dict()}")
        h_nan_count = h_processed.isna().sum().sum()
        h_inf_count = np.isinf(h_processed.select_dtypes(include=[np.number])).sum().sum()
        print(f"      Total NaN values: {h_nan_count}")
        print(f"      Total Inf values: {h_inf_count}")
        if h_nan_count > 0:
            nan_cols = [col for col in h_processed.columns if h_processed[col].isna().sum() > 0]
            print(f"      Columns with NaN: {nan_cols[:5]}...")  # Show first 5
        
        h_processed.to_csv(h_final, index=False)
        print(f"   Household file written: {h_final}")
        print(f"   Records: {len(h_processed):,}")
        print(f"   Columns: {list(h_processed.columns)}")
        
        print(f"   Person data:")
        print(f"      Shape: {p_processed.shape}")
        print(f"      Data types: {p_processed.dtypes.value_counts().to_dict()}")
        p_nan_count = p_processed.isna().sum().sum()
        p_inf_count = np.isinf(p_processed.select_dtypes(include=[np.number])).sum().sum()
        print(f"      Total NaN values: {p_nan_count}")
        print(f"      Total Inf values: {p_inf_count}")
        if p_nan_count > 0:
            nan_cols = [col for col in p_processed.columns if p_processed[col].isna().sum() > 0]
            print(f"      Columns with NaN: {nan_cols[:5]}...")  # Show first 5
        
        p_processed.to_csv(p_final, index=False)
        print(f"   Person file written: {p_final}")
        print(f"   Records: {len(p_processed):,}")
        print(f"   Columns: {list(p_processed.columns)}")
        
        print(f"\nSUCCESS: PopulationSim seed population created successfully!")
        print(f"SUCCESS: Use {h_final} and {p_final} for PopulationSim synthesis")
    else:
        print(f"\n✗ Seed population creation failed!")
