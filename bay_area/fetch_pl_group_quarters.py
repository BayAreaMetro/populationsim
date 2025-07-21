"""
fetch_pl_group_quarters.py

Function to fetch all Bay Area block-level group quarters data from the PL 94-171 dataset.
This replaces the problematic DHC dataset approach with the correct PL dataset.
"""

import os
import pandas as pd
import logging
import requests
import time

# Constants
CA_STATE_FIPS = '06'
BAY_AREA_COUNTY_FIPS = {
    'Alameda': '001',
    'Contra Costa': '013', 
    'Marin': '041',
    'Napa': '055',
    'San Francisco': '075',
    'San Mateo': '081',
    'Santa Clara': '085',
    'Solano': '095',
    'Sonoma': '097'
}

CENSUS_API_KEY_FILE = r"M:\Data\Census\API\new_key\api-key.txt"

def load_api_key():
    """Load Census API key from file."""
    with open(CENSUS_API_KEY_FILE, 'r') as f:
        return f.read().strip()

def fetch_bay_area_pl_group_quarters(save_cache=True, cache_dir=None):
    """
    Fetch block-level group quarters data for all Bay Area counties from PL 94-171 dataset.
    
    Args:
        save_cache (bool): Whether to save cached CSV files
        cache_dir (str): Directory to save cache files (optional)
    
    Returns:
        pd.DataFrame: Combined block-level group quarters data for all Bay Area counties
    """
    logger = logging.getLogger(__name__)
    api_key = load_api_key()
    
    # PL dataset endpoint (confirmed working)
    base_url = "https://api.census.gov/data/2020/dec/pl"
    
    # P5 table variables for group quarters
    pl_variables = [
        "P5_001N",  # Total Group Quarters Population
        "P5_002N",  # Institutionalized Group Quarters  
        "P5_003N",  # Noninstitutionalized Group Quarters
        "P5_008N",  # College/University student housing
        "P5_009N",  # Military quarters
    ]
    
    all_blocks_data = []
    
    logger.info(f"Fetching block-level group quarters data for {len(BAY_AREA_COUNTY_FIPS)} Bay Area counties...")
    
    for county_name, county_fips in BAY_AREA_COUNTY_FIPS.items():
        logger.info(f"Fetching blocks for {county_name} County ({county_fips})...")
        
        try:
            # Build API URL - this format confirmed working in our tests
            var_list = ",".join(pl_variables)
            api_url = f"{base_url}?get=NAME,{var_list}&for=block:*&in=state:{CA_STATE_FIPS}&in=county:{county_fips}&key={api_key}"
            
            logger.info(f"API call: {api_url[:100]}...")
            
            response = requests.get(api_url, timeout=120)
            
            if response.status_code == 200:
                json_data = response.json()
                
                if json_data and len(json_data) > 1:
                    # Convert to DataFrame
                    county_df = pd.DataFrame(json_data[1:], columns=json_data[0])
                    
                    # Add county name for easier identification
                    county_df['county_name'] = county_name
                    
                    # Convert numeric columns
                    for var in pl_variables:
                        county_df[var] = pd.to_numeric(county_df[var], errors='coerce')
                    
                    logger.info(f"  {county_name}: {len(county_df):,} blocks retrieved")
                    
                    # Calculate county totals for verification
                    county_total_gq = county_df['P5_001N'].sum()
                    county_blocks_with_gq = (county_df['P5_001N'] > 0).sum()
                    logger.info(f"  {county_name}: {county_total_gq:,.0f} total GQ, {county_blocks_with_gq:,} blocks with GQ")
                    
                    all_blocks_data.append(county_df)
                    
                    # Save county-specific cache if requested
                    if save_cache and cache_dir:
                        os.makedirs(cache_dir, exist_ok=True)
                        county_file = os.path.join(cache_dir, f"pl_2020_P5_blocks_{county_name.lower().replace(' ', '_')}.csv")
                        county_df.to_csv(county_file, index=False)
                        logger.info(f"  Saved to: {county_file}")
                
                else:
                    logger.warning(f"  {county_name}: No block data returned")
                    
            else:
                logger.error(f"  {county_name}: API request failed with status {response.status_code}")
                logger.error(f"  Error: {response.text[:200]}")
                
        except Exception as e:
            logger.error(f"  {county_name}: Error fetching data - {e}")
        
        # Small delay to be respectful to Census API
        time.sleep(0.5)
    
    if not all_blocks_data:
        logger.error("No block data retrieved for any county!")
        return None
    
    # Combine all county data
    logger.info("Combining data from all counties...")
    combined_df = pd.concat(all_blocks_data, ignore_index=True)
    
    # Calculate regional totals
    total_blocks = len(combined_df)
    total_gq = combined_df['P5_001N'].sum()
    total_university = combined_df['P5_008N'].sum()
    total_military = combined_df['P5_009N'].sum()
    blocks_with_gq = (combined_df['P5_001N'] > 0).sum()
    
    logger.info("=== BAY AREA BLOCK-LEVEL SUMMARY ===")
    logger.info(f"Total blocks: {total_blocks:,}")
    logger.info(f"Total GQ population: {total_gq:,.0f}")
    logger.info(f"University housing: {total_university:,.0f}")
    logger.info(f"Military quarters: {total_military:,.0f}")
    logger.info(f"Blocks with any GQ: {blocks_with_gq:,} ({blocks_with_gq/total_blocks*100:.1f}%)")
    
    # Show top blocks with GQ for verification
    if blocks_with_gq > 0:
        top_gq_blocks = combined_df[combined_df['P5_001N'] > 0].nlargest(5, 'P5_001N')
        logger.info("Top 5 blocks by GQ population:")
        for _, row in top_gq_blocks.iterrows():
            logger.info(f"  {row['county_name']}: {row['P5_001N']:.0f} GQ (Univ: {row['P5_008N']:.0f}, Mil: {row['P5_009N']:.0f})")
    
    # Save combined regional file
    if save_cache:
        if cache_dir:
            output_dir = cache_dir
        else:
            output_dir = r"c:\GitHub\populationsim\bay_area\input_2023\census_cache"
        
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "pl_2020_P5_blocks_bay_area.csv")
        combined_df.to_csv(output_file, index=False)
        logger.info(f"Saved combined Bay Area data to: {output_file}")
        
        # Also save to M: drive cache
        m_cache_dir = r"M:\Data\Census\NewCachedTablesForPopulationSimControls"
        if os.path.exists(os.path.dirname(m_cache_dir)):
            m_output_file = os.path.join(m_cache_dir, "pl_2020_P5_blocks_bay_area.csv")
            combined_df.to_csv(m_output_file, index=False)
            logger.info(f"Saved to M: drive cache: {m_output_file}")
    
    return combined_df

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("Fetching Bay Area block-level group quarters data from PL 94-171...")
    
    # Fetch the data
    bay_area_blocks = fetch_bay_area_pl_group_quarters(
        save_cache=True,
        cache_dir=r"c:\GitHub\populationsim\bay_area\input_2023\census_cache"
    )
    
    if bay_area_blocks is not None:
        print(f"\nSuccess! Retrieved {len(bay_area_blocks):,} blocks with group quarters data.")
        print(f"Total Bay Area GQ population: {bay_area_blocks['P5_001N'].sum():,.0f}")
    else:
        print("Failed to retrieve block data.")
