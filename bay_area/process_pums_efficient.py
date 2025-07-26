#!/usr/bin/env python3
"""
Efficient processing of existing PUMS files using chunked reading
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

def process_pums_file_chunked(file_path, year, file_type, chunk_size=50000):
    """Process a PUMS file in chunks to avoid memory issues"""
    print(f"\nProcessing {file_path} in chunks of {chunk_size:,} records...")
    
    try:
        # Get total file size for progress
        file_size = os.path.getsize(file_path)
        print(f"File size: {file_size:,} bytes")
        
        # First, peek at the file to check columns
        sample_df = pd.read_csv(file_path, nrows=5)
        if 'PUMA' not in sample_df.columns:
            print(f"✗ No 'PUMA' column found in {file_path}")
            print(f"Available columns: {sample_df.columns.tolist()}")
            return pd.DataFrame()
        
        print(f"✓ PUMA column found. Processing in chunks...")
        
        # Process file in chunks
        bay_area_chunks = []
        total_records = 0
        chunk_count = 0
        
        # Use chunked reading
        for chunk in pd.read_csv(file_path, chunksize=chunk_size, dtype={'PUMA': str}, low_memory=False):
            chunk_count += 1
            total_records += len(chunk)
            
            # Show progress
            if chunk_count % 5 == 0:  # Every 5th chunk
                print(f"  Processed {total_records:,} records ({chunk_count} chunks)...")
            
            # Ensure PUMA is 5-digit string with leading zeros
            chunk['PUMA'] = chunk['PUMA'].astype(str).str.zfill(5)
            
            # Filter for Bay Area PUMAs
            bay_area_chunk = chunk[chunk['PUMA'].isin(BAY_AREA_PUMAS_COMBINED)].copy()
            
            if len(bay_area_chunk) > 0:
                bay_area_chunks.append(bay_area_chunk)
        
        print(f"✓ Processed {total_records:,} total records in {chunk_count} chunks")
        
        # Combine all Bay Area chunks
        if bay_area_chunks:
            bay_area_df = pd.concat(bay_area_chunks, ignore_index=True)
            print(f"Bay Area records (combined PUMAs): {len(bay_area_df):,}")
            
            # Show which PUMAs we found
            found_pumas = sorted(bay_area_df['PUMA'].unique())
            print(f"PUMAs found in {year}: {len(found_pumas)} - {found_pumas}")
            
            return bay_area_df
        else:
            print(f"✗ No Bay Area records found in {file_path}")
            return pd.DataFrame()
        
    except Exception as e:
        print(f"✗ Error processing {file_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def main():
    """Process existing downloaded files efficiently"""
    print("="*60)
    print("EFFICIENT PROCESSING: Existing California PUMS files")
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
        print(f"\n{'='*50}")
        print(f"PROCESSING YEAR {year}")
        print(f"{'='*50}")
        
        # Process household file
        h_file = f"pums_{year}_h.csv"
        if os.path.exists(h_file):
            print(f"Found {h_file}")
            h_df = process_pums_file_chunked(h_file, year, 'h')
            if len(h_df) > 0:
                all_households.append(h_df)
                print(f"✓ Added {len(h_df):,} household records for {year}")
            else:
                print(f"✗ No household records found for {year}")
        else:
            print(f"✗ Missing {h_file}")
        
        # Process person file
        p_file = f"pums_{year}_p.csv"
        if os.path.exists(p_file):
            print(f"Found {p_file}")
            p_df = process_pums_file_chunked(p_file, year, 'p')
            if len(p_df) > 0:
                all_persons.append(p_df)
                print(f"✓ Added {len(p_df):,} person records for {year}")
            else:
                print(f"✗ No person records found for {year}")
        else:
            print(f"✗ Missing {p_file}")
    
    # Combine and save
    if all_households and all_persons:
        print(f"\n{'='*60}")
        print("COMBINING AND SAVING TO M: DRIVE")
        print(f"{'='*60}")
        
        print("Combining household data...")
        combined_households = pd.concat(all_households, ignore_index=True)
        
        print("Combining person data...")
        combined_persons = pd.concat(all_persons, ignore_index=True)
        
        # Save to M: drive
        h_output = os.path.join(output_dir, "hbayarea1923.csv")
        p_output = os.path.join(output_dir, "pbayarea1923.csv")
        
        print(f"Saving household file to {h_output}")
        print(f"  {len(combined_households):,} records")
        combined_households.to_csv(h_output, index=False)
        
        print(f"Saving person file to {p_output}")
        print(f"  {len(combined_persons):,} records")
        combined_persons.to_csv(p_output, index=False)
        
        # Final summary
        print(f"\n{'='*60}")
        print("SUCCESS! FILES SAVED TO M: DRIVE")
        print(f"{'='*60}")
        print(f"Household file: {h_output}")
        print(f"  Records: {len(combined_households):,}")
        print(f"  File size: {os.path.getsize(h_output):,} bytes")
        
        print(f"Person file: {p_output}")
        print(f"  Records: {len(combined_persons):,}")
        print(f"  File size: {os.path.getsize(p_output):,} bytes")
        
        # Show PUMAs found
        found_pumas = sorted(combined_households['PUMA'].unique())
        print(f"\nPUMAs found across all years: {len(found_pumas)}")
        print(f"PUMAs: {found_pumas}")
        
        # Compare to current approach
        current_pumas = [
            '00101', '01301', '01305', '01308', '01309', '05500', '07507',
            '08101', '08102', '08103', '08104', '08105', '08106', '08505',
            '08506', '08507', '08508', '08510', '08511', '08512', '09501',
            '09502', '09503', '09702'
        ]
        new_pumas = set(found_pumas) - set(current_pumas)
        if new_pumas:
            print(f"\n🎉 NEW PUMAs gained with combined approach: {sorted(new_pumas)}")
            print(f"Improvement: {len(new_pumas)} additional PUMAs!")
        else:
            print(f"\n📊 Same {len(found_pumas)} PUMAs as current approach")
        
        print(f"\n✅ COMPLETE! Bay Area PUMS data ready for PopulationSim")
        
    else:
        print(f"\n❌ FAILED! No data was successfully processed")
        if not all_households:
            print("- No household data found")
        if not all_persons:
            print("- No person data found")

if __name__ == "__main__":
    main()
