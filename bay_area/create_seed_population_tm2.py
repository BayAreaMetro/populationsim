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

Income Conversion:
- PUMS provides income in survey year dollars adjusted to 2023$ via ADJINC
- We convert 2023$ to 2010$ using deflation factor of 0.725 (based on ~38% cumulative inflation)
- This ensures consistency with control file breakpoints representing 2010 purchasing power
- Final output includes both hh_income_2023 and hh_income_2010 columns
"""

import pandas as pd
import numpy as np
import os
import zipfile
import requests
from urllib3.exceptions import InsecureRequestWarning
import warnings
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

# Import our CPI conversion utilities
from cpi_conversion import convert_2023_to_2010_dollars

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
    
    print(f"🎯 Creating seed population for {len(BAY_AREA_PUMAS)} Bay Area PUMAs")
    print("="*70)
    
    # Output directory
    output_dir = "M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23"
    os.makedirs(output_dir, exist_ok=True)
    
    # File paths
    h_output = os.path.join(output_dir, "hbayarea1923.csv")
    p_output = os.path.join(output_dir, "pbayarea1923.csv")
    
    # Check if files already exist
    if os.path.exists(h_output) and os.path.exists(p_output):
        print(f"✅ Seed population files already exist:")
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
        print(f"\n📅 Processing {year}...")
        
        # Download California household file (csv_hca.zip = California households)
        h_url = f"{base_url}/csv_hca.zip"
        h_zip_path = f"csv_hca_{year}.zip"
        
        print(f"   📥 Downloading households from: {h_url}")
        print(f"   💾 Saving to: {h_zip_path}")
        
        import time
        start_time = time.time()
        
        try:
            # Start download with progress tracking
            print(f"   🌐 Initiating HTTP request...")
            response = requests.get(h_url, verify=False, timeout=600, stream=True)
            response.raise_for_status()
            
            # Get file size from headers
            total_size = int(response.headers.get('content-length', 0))
            if total_size > 0:
                print(f"   📊 File size: {total_size / 1024 / 1024:.1f} MB")
            
            # Download with progress tracking
            downloaded = 0
            chunk_size = 8192
            last_progress_time = time.time()
            
            print(f"   ⬇️  Downloading in progress...")
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
            print(f"   ✅ Download completed in {download_time:.1f}s (avg speed: {final_speed:.1f} MB/s)")
            
            # Extract and process household file
            print(f"   📂 Extracting ZIP file...")
            extract_start = time.time()
            
            with zipfile.ZipFile(h_zip_path, 'r') as zip_ref:
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                if csv_files:
                    h_csv = csv_files[0]
                    print(f"   📄 Processing CSV: {h_csv}")
                    
                    # Read in chunks to handle large files
                    chunk_list = []
                    chunk_count = 0
                    total_rows = 0
                    
                    print(f"   🔄 Reading data in chunks...")
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
                    
                    print(f"   📊 Finished reading {chunk_count:,} chunks ({total_rows:,} total rows)")
                    
                    if chunk_list:
                        year_households = pd.concat(chunk_list, ignore_index=True)
                        all_households.append(year_households)
                        extract_time = time.time() - extract_start
                        print(f"   ✅ Found {len(year_households):,} Bay Area households (processed in {extract_time:.1f}s)")
                    else:
                        print(f"   ⚠️  No Bay Area households found in {year}")
            
            # Clean up zip file
            print(f"   🗑️  Cleaning up: {h_zip_path}")
            os.remove(h_zip_path)
            
        except Exception as e:
            print(f"   ❌ Error processing households for {year}: {e}")
            import traceback
            print(f"   🔍 Error details: {traceback.format_exc()}")
            continue
        
        # Download California person file (csv_pca.zip = California persons)
        p_url = f"{base_url}/csv_pca.zip"
        p_zip_path = f"csv_pca_{year}.zip"
        
        print(f"\n   👥 DOWNLOADING PERSON DATA")
        print(f"   📥 Downloading persons from: {p_url}")
        print(f"   💾 Saving to: {p_zip_path}")
        
        start_time = time.time()
        
        try:
            # Start download with progress tracking
            print(f"   🌐 Initiating HTTP request...")
            response = requests.get(p_url, verify=False, timeout=600, stream=True)
            response.raise_for_status()
            
            # Get file size from headers
            total_size = int(response.headers.get('content-length', 0))
            if total_size > 0:
                print(f"   📊 File size: {total_size / 1024 / 1024:.1f} MB")
            
            # Download with progress tracking
            downloaded = 0
            chunk_size = 8192
            last_progress_time = time.time()
            
            print(f"   ⬇️  Downloading in progress...")
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
            print(f"   ✅ Download completed in {download_time:.1f}s (avg speed: {final_speed:.1f} MB/s)")
            
            # Extract and process person file
            print(f"   📂 Extracting ZIP file...")
            extract_start = time.time()
            
            with zipfile.ZipFile(p_zip_path, 'r') as zip_ref:
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                if csv_files:
                    p_csv = csv_files[0]
                    print(f"   📄 Processing CSV: {p_csv}")
                    
                    # Read in chunks to handle large files
                    chunk_list = []
                    chunk_count = 0
                    total_rows = 0
                    
                    print(f"   🔄 Reading data in chunks...")
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
                                print(f"   📊 Processed {chunk_count} chunks, {total_rows:,} total rows")
                    
                    if chunk_list:
                        year_persons = pd.concat(chunk_list, ignore_index=True)
                        all_persons.append(year_persons)
                        print(f"   ✅ Found {len(year_persons):,} Bay Area persons from {total_rows:,} total California persons")
            
            # Clean up zip file
            os.remove(p_zip_path)
            
        except Exception as e:
            print(f"   ❌ Error processing persons for {year}: {e}")
            continue
    
    # Combine all years
    print(f"\n🔄 Combining data from all years...")
    
    if all_households:
        final_households = pd.concat(all_households, ignore_index=True)
        print(f"   Total households: {len(final_households):,}")
        
        # Process household income conversion from 2023$ to 2010$
        print(f"   🔄 Converting household income from 2023$ to 2010$ purchasing power...")
        
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
            
            # Round to nearest dollar for cleaner data
            final_households['hh_income_2010'] = final_households['hh_income_2010'].round().astype(int)
            final_households['hh_income_2023'] = final_households['hh_income_2023'].round().astype(int)
            
            print(f"      ✅ Income conversion completed")
            print(f"      Sample 2023$: {final_households['hh_income_2023'].head().tolist()}")
            print(f"      Sample 2010$: {final_households['hh_income_2010'].head().tolist()}")
            print(f"      Mean income 2023$: ${final_households['hh_income_2023'].mean():,.0f}")
            print(f"      Mean income 2010$: ${final_households['hh_income_2010'].mean():,.0f}")
        else:
            print(f"      ⚠️  Warning: HINCP or ADJINC columns not found, skipping income conversion")
            missing_cols = [col for col in ['HINCP', 'ADJINC'] if col not in final_households.columns]
            print(f"      Missing columns: {missing_cols}")
        
        # Save households
        print(f"   Saving to: {h_output}")
        final_households.to_csv(h_output, index=False)
        print(f"   ✅ Household file saved ({os.path.getsize(h_output) / 1024 / 1024:.1f} MB)")
    else:
        print(f"   ❌ No household data found!")
        return None, None
    
    if all_persons:
        final_persons = pd.concat(all_persons, ignore_index=True)
        print(f"   Total persons: {len(final_persons):,}")
        
        # Save persons
        print(f"   Saving to: {p_output}")
        final_persons.to_csv(p_output, index=False)
        print(f"   ✅ Person file saved ({os.path.getsize(p_output) / 1024 / 1024:.1f} MB)")
    else:
        print(f"   ❌ No person data found!")
        return None, None
    
    # Quick summary
    unique_pumas = sorted(final_households['PUMA'].unique())
    print(f"\n📊 FINAL SUMMARY:")
    print(f"   Households: {len(final_households):,}")
    print(f"   Persons: {len(final_persons):,}")
    print(f"   PUMAs covered: {len(unique_pumas)}")
    print(f"   PUMA list: {unique_pumas}")
    
    # Income summary if available
    if 'hh_income_2010' in final_households.columns:
        print(f"\n💰 INCOME SUMMARY (2010 purchasing power):")
        print(f"   Mean household income: ${final_households['hh_income_2010'].mean():,.0f}")
        print(f"   Median household income: ${final_households['hh_income_2010'].median():,.0f}")
        print(f"   Income breakpoint analysis:")
        print(f"      <$30K:  {(final_households['hh_income_2010'] < 30000).sum():,} households ({(final_households['hh_income_2010'] < 30000).mean()*100:.1f}%)")
        print(f"      $30-60K: {((final_households['hh_income_2010'] >= 30000) & (final_households['hh_income_2010'] < 60000)).sum():,} households ({((final_households['hh_income_2010'] >= 30000) & (final_households['hh_income_2010'] < 60000)).mean()*100:.1f}%)")
        print(f"      $60-100K: {((final_households['hh_income_2010'] >= 60000) & (final_households['hh_income_2010'] < 100000)).sum():,} households ({((final_households['hh_income_2010'] >= 60000) & (final_households['hh_income_2010'] < 100000)).mean()*100:.1f}%)")
        print(f"      $100K+: {(final_households['hh_income_2010'] >= 100000).sum():,} households ({(final_households['hh_income_2010'] >= 100000).mean()*100:.1f}%)")
    
    return h_output, p_output

if __name__ == "__main__":
    household_file, person_file = create_seed_population()
    
    if household_file and person_file:
        print(f"\n🎉 Seed population creation completed successfully!")
        print(f"   Household file: {household_file}")
        print(f"   Person file: {person_file}")
    else:
        print(f"\n❌ Seed population creation failed!")
