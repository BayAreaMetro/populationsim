#!/usr/bin/env python3
"""
Fix the PUMS processing to properly filter and save to M: drive
"""

import pandas as pd
import os

# Combined Bay Area PUMAs (both 2010 and 2020 definitions)
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

def process_pums_file(file_path, year, file_type):
    """Process a PUMS file and filter for Bay Area - with better error handling"""
    print(f"\nProcessing {file_path}...")
    
    try:
        # First, check what columns exist in the file
        df_sample = pd.read_csv(file_path, nrows=5)
        print(f"Available columns: {df_sample.columns.tolist()}")
        
        # Check if required columns exist
        if 'ST' not in df_sample.columns:
            print(f"✗ No 'ST' column found in {file_path}")
            return pd.DataFrame()
        
        if 'PUMA' not in df_sample.columns:
            print(f"✗ No 'PUMA' column found in {file_path}")
            return pd.DataFrame()
        
        # Now read the full file with proper dtypes
        print("Reading full file...")
        df = pd.read_csv(file_path, dtype={'PUMA': str, 'ST': str}, low_memory=False)
        print(f"Original file: {len(df):,} records")
        
        # Check what state values we have
        st_values = df['ST'].unique()
        print(f"State values in file: {sorted(st_values)}")
        
        # Filter for California - try both '6' and '06'
        ca_df = df[(df['ST'] == '6') | (df['ST'] == '06')].copy()
        print(f"California records: {len(ca_df):,}")
        
        if len(ca_df) == 0:
            print("✗ No California records found - check state coding")
            return pd.DataFrame()
        
        # Ensure PUMA is 5-digit string with leading zeros
        ca_df['PUMA'] = ca_df['PUMA'].astype(str).str.zfill(5)
        
        # Check what PUMA values we have
        puma_sample = sorted(ca_df['PUMA'].unique())[:10]  # First 10 PUMAs
        print(f"Sample PUMA values: {puma_sample}")
        
        # Filter for Bay Area PUMAs (using combined list)
        bay_area_df = ca_df[ca_df['PUMA'].isin(BAY_AREA_PUMAS_COMBINED)].copy()
        print(f"Bay Area records (combined PUMAs): {len(bay_area_df):,}")
        
        # Show which PUMAs we actually found
        found_pumas = sorted(bay_area_df['PUMA'].unique())
        print(f"PUMAs found in {year}: {len(found_pumas)} - {found_pumas}")
        
        # Show missing PUMAs
        missing_pumas = set(BAY_AREA_PUMAS_COMBINED) - set(found_pumas)
        if missing_pumas:
            print(f"Missing PUMAs: {len(missing_pumas)} - {sorted(list(missing_pumas))[:10]}...")  # Show first 10
        
        return bay_area_df
        
    except Exception as e:
        print(f"✗ Error processing {file_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def main():
    """Process existing downloaded files and save to M: drive"""
    print("="*60)
    print("FIXING: PUMS processing to save to M: drive location")
    print("="*60)
    
    # Create output directory
    output_dir = "M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23" 
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    years = [2019, 2020, 2021, 2022, 2023]
    all_households = []
    all_persons = []
    
    # Process existing files
    for year in years:
        print(f"\n{'='*40}")
        print(f"Processing {year}")
        print(f"{'='*40}")
        
        # Process household file
        h_file = f"pums_{year}_h.csv"
        if os.path.exists(h_file):
            h_df = process_pums_file(h_file, year, 'h')
            if len(h_df) > 0:
                all_households.append(h_df)
                print(f"✓ Added {len(h_df):,} household records for {year}")
            else:
                print(f"✗ No household records for {year}")
        else:
            print(f"✗ Missing {h_file}")
        
        # Process person file
        p_file = f"pums_{year}_p.csv"
        if os.path.exists(p_file):
            p_df = process_pums_file(p_file, year, 'p')
            if len(p_df) > 0:
                all_persons.append(p_df)
                print(f"✓ Added {len(p_df):,} person records for {year}")
            else:
                print(f"✗ No person records for {year}")
        else:
            print(f"✗ Missing {p_file}")
    
    # Combine all years
    if all_households and all_persons:
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
            print(f"Improvement: {len(new_pumas)} additional PUMAs!")
        else:
            print("No additional PUMAs found beyond current approach")
        
        print(f"\n✓ SUCCESS! Files saved to M: drive")
        print(f"You can now use these files for PopulationSim")
        
    else:
        print(f"\n✗ FAILED! No data was successfully processed")
        print("Check the error messages above for details")
    
    print(f"\nTotal PUMAs in combined list: {len(BAY_AREA_PUMAS_COMBINED)}")

if __name__ == "__main__":
    main()
