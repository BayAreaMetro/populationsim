#!/usr/bin/env python3
"""
Create PUMS seed population for Bay Area PopulationSim
Final version incorporating lessons learned
"""

import pandas as pd
import numpy as np
import os
import zipfile
import requests
from urllib3.exceptions import InsecureRequestWarning
import warnings
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

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
    
    # Download and process PUMS files
    base_url = "https://www2.census.gov/programs-surveys/acs/data/pums/2023/5-Year"
    
    years = ['2019', '2020', '2021', '2022', '2023']
    
    all_households = []
    all_persons = []
    
    for year in years:
        print(f"\n📅 Processing {year}...")
        
        # Download household file
        h_url = f"{base_url}/csv_hca.zip"
        h_zip_path = f"csv_hca_{year}.zip"
        
        print(f"   Downloading households: {h_url}")
        try:
            response = requests.get(h_url, verify=False, timeout=300)
            response.raise_for_status()
            
            with open(h_zip_path, 'wb') as f:
                f.write(response.content)
            
            # Extract and process household file
            with zipfile.ZipFile(h_zip_path, 'r') as zip_ref:
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                if csv_files:
                    h_csv = csv_files[0]
                    print(f"   Extracting: {h_csv}")
                    
                    # Read in chunks to handle large files
                    chunk_list = []
                    with zip_ref.open(h_csv) as csv_file:
                        for chunk in pd.read_csv(csv_file, dtype={'PUMA': str, 'ST': str}, chunksize=10000):
                            # Filter for California and Bay Area PUMAs
                            ca_chunk = chunk[chunk['ST'] == '06']
                            if not ca_chunk.empty:
                                ca_chunk['PUMA'] = ca_chunk['PUMA'].astype(str).str.zfill(5)
                                bay_chunk = ca_chunk[ca_chunk['PUMA'].isin(BAY_AREA_PUMAS)]
                                if not bay_chunk.empty:
                                    chunk_list.append(bay_chunk)
                    
                    if chunk_list:
                        year_households = pd.concat(chunk_list, ignore_index=True)
                        all_households.append(year_households)
                        print(f"   Found {len(year_households):,} Bay Area households")
            
            # Clean up zip file
            os.remove(h_zip_path)
            
        except Exception as e:
            print(f"   ❌ Error processing households for {year}: {e}")
            continue
        
        # Download person file
        p_url = f"{base_url}/csv_pca.zip"
        p_zip_path = f"csv_pca_{year}.zip"
        
        print(f"   Downloading persons: {p_url}")
        try:
            response = requests.get(p_url, verify=False, timeout=300)
            response.raise_for_status()
            
            with open(p_zip_path, 'wb') as f:
                f.write(response.content)
            
            # Extract and process person file
            with zipfile.ZipFile(p_zip_path, 'r') as zip_ref:
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                if csv_files:
                    p_csv = csv_files[0]
                    print(f"   Extracting: {p_csv}")
                    
                    # Read in chunks to handle large files
                    chunk_list = []
                    with zip_ref.open(p_csv) as csv_file:
                        for chunk in pd.read_csv(csv_file, dtype={'PUMA': str, 'ST': str}, chunksize=10000):
                            # Filter for California and Bay Area PUMAs
                            ca_chunk = chunk[chunk['ST'] == '06']
                            if not ca_chunk.empty:
                                ca_chunk['PUMA'] = ca_chunk['PUMA'].astype(str).str.zfill(5)
                                bay_chunk = ca_chunk[ca_chunk['PUMA'].isin(BAY_AREA_PUMAS)]
                                if not bay_chunk.empty:
                                    chunk_list.append(bay_chunk)
                    
                    if chunk_list:
                        year_persons = pd.concat(chunk_list, ignore_index=True)
                        all_persons.append(year_persons)
                        print(f"   Found {len(year_persons):,} Bay Area persons")
            
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
    
    return h_output, p_output

if __name__ == "__main__":
    household_file, person_file = create_seed_population()
    
    if household_file and person_file:
        print(f"\n🎉 Seed population creation completed successfully!")
        print(f"   Household file: {household_file}")
        print(f"   Person file: {person_file}")
    else:
        print(f"\n❌ Seed population creation failed!")
