#!/usr/bin/env python3
"""
Create seed population from PUMS 2019-2023 data using COMBINED 2010+2020 PUMA definitions
Testing if using both 2010 and 2020 PUMA codes gives us better coverage
"""

import pandas as pd
import requests
import zipfile
import os
import ssl
import urllib3
from io import StringIO

# Disable SSL warnings and verification for Census downloads
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

# Combined Bay Area PUMAs (both 2010 and 2020 definitions)
# This includes all PUMAs that existed in either period
BAY_AREA_PUMAS_COMBINED = [
    # San Francisco County (075)
    '00101', '00102', '00103', '00104', '00105', '00106', '00107',
    
    # Alameda County (001) 
    '01301', '01302', '01303', '01304', '01305', '01306', '01307', 
    '01308', '01309', '01310', '01311', '01312', '01313',
    
    # Contra Costa County (013)
    '04100', '04101', '04102', '04103', '04104', '04105', '04106', 
    '04107', '04108', '04109', '04110', '04111', '04112', '04113', '04114',
    
    # San Mateo County (081)
    '05500', 
    
    # Marin County (041)
    '07501', '07502', '07503', '07504', '07505', '07506', '07507',
    
    # Santa Clara County (085)
    '08101', '08102', '08103', '08104', '08105', '08106', 
    '08501', '08502', '08503', '08504', '08505', '08506', '08507', 
    '08508', '08509', '08510', '08511', '08512',
    
    # Sonoma County (097) - 2020 definitions
    '09501', '09502', '09503', 
    
    # Napa County (055) - 2020 definitions  
    '09702'
]

print(f"Testing PUMS download with COMBINED PUMA list: {len(BAY_AREA_PUMAS_COMBINED)} PUMAs")
print("This includes both 2010 and 2020 PUMA definitions to maximize coverage")

def download_and_extract_pums(year, file_type='h'):
    """Download and extract PUMS data for a given year"""
    print(f"\nDownloading {year} PUMS {file_type.upper()} file...")
    
    # Construct URL based on year
    if year <= 2021:
        url = f"https://www2.census.gov/programs-surveys/acs/data/pums/{year}/5-Year/csv_{file_type}ca.zip"
    else:
        url = f"https://www2.census.gov/programs-surveys/acs/data/pums/{year}/5-Year/csv_{file_type}ca.zip"
    
    print(f"URL: {url}")
    
    try:
        # Download the file
        response = requests.get(url, verify=False, timeout=60)
        response.raise_for_status()
        
        # Save to temporary file
        zip_path = f"temp_pums_{year}_{file_type}.zip"
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        # Extract CSV file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            if csv_files:
                csv_file = csv_files[0]
                print(f"Extracting {csv_file}...")
                zip_ref.extract(csv_file, '.')
                
                # Rename to standard name
                extracted_path = csv_file
                standard_path = f"pums_{year}_{file_type}.csv"
                if os.path.exists(extracted_path):
                    os.rename(extracted_path, standard_path)
                    print(f"✓ Saved as {standard_path}")
                    
                    # Clean up zip file
                    os.remove(zip_path)
                    return standard_path
        
        print(f"✗ No CSV file found in {zip_path}")
        return None
        
    except Exception as e:
        print(f"✗ Error downloading {year}: {str(e)}")
        return None

def process_pums_file(file_path, year, file_type):
    """Process a California-specific PUMS file and filter for Bay Area"""
    print(f"\nProcessing {file_path}...")
    
    try:
        # Read the CSV file - California files already contain only CA data
        # So we don't need to filter by state, just read with PUMA as string
        df = pd.read_csv(file_path, dtype={'PUMA': str}, low_memory=False)
        print(f"California file: {len(df):,} records")
        
        # Check if PUMA column exists
        if 'PUMA' not in df.columns:
            print(f"✗ No 'PUMA' column found in {file_path}")
            print(f"Available columns: {df.columns.tolist()}")
            return pd.DataFrame()
        
        # Ensure PUMA is 5-digit string with leading zeros
        df['PUMA'] = df['PUMA'].astype(str).str.zfill(5)
        
        # Show sample of PUMA values for debugging
        puma_sample = sorted(df['PUMA'].unique())[:10]
        print(f"Sample PUMA values: {puma_sample}")
        
        # Filter for Bay Area PUMAs (using combined list)
        bay_area_df = df[df['PUMA'].isin(BAY_AREA_PUMAS_COMBINED)].copy()
        print(f"Bay Area records (combined PUMAs): {len(bay_area_df):,}")
        
        # Show which PUMAs we actually found
        found_pumas = sorted(bay_area_df['PUMA'].unique())
        print(f"PUMAs found in {year}: {len(found_pumas)} - {found_pumas}")
        
        # Show missing PUMAs (limit to first 10 for readability)
        missing_pumas = set(BAY_AREA_PUMAS_COMBINED) - set(found_pumas)
        if missing_pumas:
            missing_list = sorted(list(missing_pumas))
            if len(missing_list) > 10:
                print(f"Missing PUMAs: {len(missing_list)} total - first 10: {missing_list[:10]}")
            else:
                print(f"Missing PUMAs: {len(missing_list)} - {missing_list}")
        
        return bay_area_df
        
    except Exception as e:
        print(f"✗ Error processing {file_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def main():
    """Main function to create seed population files"""
    print("="*60)
    print("DOWNLOADING: California PUMS 2019-2023 with COMBINED 2010+2020 PUMA definitions")
    print("="*60)
    
    # Create output directory
    output_dir = "M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23"
    os.makedirs(output_dir, exist_ok=True)
    
    # Years to process
    years = [2019, 2020, 2021, 2022, 2023]
    
    all_households = []
    all_persons = []
    
    # Download and process all years
    for year in years:
        print(f"\n{'='*40}")
        print(f"Processing {year}")
        print(f"{'='*40}")
        
        # Download household file
        h_file = download_and_extract_pums(year, 'h')
        if h_file:
            h_df = process_pums_file(h_file, year, 'h')
            if len(h_df) > 0:
                all_households.append(h_df)
                print(f"✓ Added {len(h_df):,} household records for {year}")
            # Clean up temporary file
            if os.path.exists(h_file):
                try:
                    os.remove(h_file)
                except:
                    print(f"Note: Could not delete temporary file {h_file}")
        
        # Download person file
        p_file = download_and_extract_pums(year, 'p')
        if p_file:
            p_df = process_pums_file(p_file, year, 'p')
            if len(p_df) > 0:
                all_persons.append(p_df)
                print(f"✓ Added {len(p_df):,} person records for {year}")
            # Clean up temporary file
            if os.path.exists(p_file):
                try:
                    os.remove(p_file)
                except:
                    print(f"Note: Could not delete temporary file {p_file}")
    
    # Combine all years
    if all_households:
        print(f"\n{'='*50}")
        print("COMBINING ALL YEARS")
        print(f"{'='*50}")
        
        combined_households = pd.concat(all_households, ignore_index=True)
        combined_persons = pd.concat(all_persons, ignore_index=True)
        
        # Save combined files
        h_output = os.path.join(output_dir, "hbayarea1923.csv")
        p_output = os.path.join(output_dir, "pbayarea1923.csv")
        
        print(f"Saving household file: {len(combined_households):,} records")
        combined_households.to_csv(h_output, index=False)
        
        print(f"Saving person file: {len(combined_persons):,} records")
        combined_persons.to_csv(p_output, index=False)
        
        # Final summary
        print(f"\n{'='*60}")
        print("FINAL RESULTS WITH COMBINED PUMA APPROACH")
        print(f"{'='*60}")
        print(f"Household file: {h_output}")
        print(f"  Records: {len(combined_households):,}")
        print(f"  File size: {os.path.getsize(h_output):,} bytes")
        
        print(f"Person file: {p_output}")
        print(f"  Records: {len(combined_persons):,}")
        print(f"  File size: {os.path.getsize(p_output):,} bytes")
        
        # Show all PUMAs found
        found_pumas = sorted(combined_households['PUMA'].unique())
        print(f"\nPUMAs found across all years: {len(found_pumas)}")
        print(f"PUMAs: {found_pumas}")
        
        # Compare to previous approach
        current_pumas = [
            '00101', '01301', '01305', '01308', '01309', '05500', '07507',
            '08101', '08102', '08103', '08104', '08105', '08106', '08505',
            '08506', '08507', '08508', '08510', '08511', '08512', '09501',
            '09502', '09503', '09702'
        ]
        new_pumas = set(found_pumas) - set(current_pumas)
        if new_pumas:
            print(f"NEW PUMAs gained with combined approach: {sorted(new_pumas)}")
        else:
            print("No additional PUMAs found beyond current approach")
    
    print(f"\n✓ Processing complete using combined PUMA approach!")
    print(f"Total PUMAs in combined list: {len(BAY_AREA_PUMAS_COMBINED)}")
    print(f"Files saved to: {output_dir}")

if __name__ == "__main__":
    main()
