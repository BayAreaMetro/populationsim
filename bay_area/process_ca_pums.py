#!/usr/bin/env python3
"""
Process the downloaded California PUMS files and save to M: drive
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
    """Process a California-specific PUMS file and filter for Bay Area"""
    print(f"\nProcessing {file_path}...")
    
    try:
        # Read the CSV file - California files already contain only CA data
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
        
        return bay_area_df
        
    except Exception as e:
        print(f"✗ Error processing {file_path}: {str(e)}")
        return pd.DataFrame()

def main():
    """Process downloaded files and save to M: drive"""
    print("="*60)
    print("PROCESSING: Downloaded California PUMS files")
    print("="*60)
    
    # Create output directory
    output_dir = "M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23"
    os.makedirs(output_dir, exist_ok=True)
    
    years = [2019, 2020, 2021, 2022, 2023]
    all_households = []
    all_persons = []
    
    # Process downloaded files
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
                print(f"✓ Added {len(h_df):,} household records")
        else:
            print(f"✗ Missing {h_file}")
        
        # Process person file
        p_file = f"pums_{year}_p.csv"
        if os.path.exists(p_file):
            p_df = process_pums_file(p_file, year, 'p')
            if len(p_df) > 0:
                all_persons.append(p_df)
                print(f"✓ Added {len(p_df):,} person records")
        else:
            print(f"✗ Missing {p_file}")
    
    # Combine and save
    if all_households and all_persons:
        print(f"\n{'='*50}")
        print("COMBINING AND SAVING")
        print(f"{'='*50}")
        
        combined_households = pd.concat(all_households, ignore_index=True)
        combined_persons = pd.concat(all_persons, ignore_index=True)
        
        # Save to M: drive
        h_output = os.path.join(output_dir, "hbayarea1923.csv")
        p_output = os.path.join(output_dir, "pbayarea1923.csv")
        
        print(f"Saving to {h_output}")
        combined_households.to_csv(h_output, index=False)
        
        print(f"Saving to {p_output}")
        combined_persons.to_csv(p_output, index=False)
        
        # Summary
        print(f"\n✓ SUCCESS!")
        print(f"Household file: {len(combined_households):,} records, {os.path.getsize(h_output):,} bytes")
        print(f"Person file: {len(combined_persons):,} records, {os.path.getsize(p_output):,} bytes")
        
        # Show PUMAs found
        found_pumas = sorted(combined_households['PUMA'].unique())
        print(f"PUMAs found: {len(found_pumas)} - {found_pumas}")
        
        # Compare to current approach
        current_pumas = [
            '00101', '01301', '01305', '01308', '01309', '05500', '07507',
            '08101', '08102', '08103', '08104', '08105', '08106', '08505',
            '08506', '08507', '08508', '08510', '08511', '08512', '09501',
            '09502', '09503', '09702'
        ]
        new_pumas = set(found_pumas) - set(current_pumas)
        if new_pumas:
            print(f"NEW PUMAs gained: {sorted(new_pumas)}")
        else:
            print("Same PUMAs as current approach")
    else:
        print("✗ No data processed successfully")

if __name__ == "__main__":
    main()
