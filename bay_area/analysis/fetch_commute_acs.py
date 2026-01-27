#!/usr/bin/env python3
"""
Fetch ACS 1-year commute data (B08006) for Bay Area counties for 2019 and 2023.
B08006: Sex of Workers by Means of Transportation to Work
B08006_001: Total workers
B08006_017: Worked from home
"""

import pandas as pd
from pathlib import Path
from census import Census
import sys

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.config_census import CENSUS_API_KEY_FILE, BAY_AREA_COUNTY_FIPS, CA_STATE_FIPS

# Output directory
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output_2023" / "acs_commute"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def fetch_commute_data(year: int, census_api: Census) -> pd.DataFrame:
    """
    Fetch B08006 commute data for Bay Area counties for a given year.
    
    Args:
        year: Census year (2019 or 2023)
        census_api: Census API object
    
    Returns:
        DataFrame with county-level commute data
    """
    print(f"\nFetching {year} ACS 1-year data for B08006 (commute)...")
    
    # Variables to fetch
    variables = [
        'B08006_001E',  # Total workers
        'B08006_017E',  # Worked from home
        'NAME',
    ]
    
    all_data = []
    
    for county_name, county_fips in BAY_AREA_COUNTY_FIPS.items():
        print(f"  Fetching {county_name} County ({county_fips})...")
        
        try:
            # Fetch data using census library
            data = census_api.acs1.get(
                variables,
                geo={
                    'for': 'county:' + county_fips,
                    'in': 'state:' + CA_STATE_FIPS
                },
                year=year
            )
            
            if data:
                df = pd.DataFrame(data)
                df['county_name'] = county_name
                all_data.append(df)
                print(f"    ✓ Retrieved data for {county_name}")
            else:
                print(f"    ✗ No data returned for {county_name}")
                
        except Exception as e:
            print(f"    ✗ Error fetching {county_name}: {e}")
            continue
    
    if not all_data:
        print(f"  No data retrieved for {year}")
        return None
    
    # Combine all counties
    combined = pd.concat(all_data, ignore_index=True)
    
    # Rename columns
    combined.rename(columns={
        'B08006_001E': 'total_workers',
        'B08006_017E': 'work_from_home',
        'NAME': 'county_full_name',
    }, inplace=True)
    
    # Calculate work from home percentage
    combined['work_from_home_pct'] = (
        combined['work_from_home'] / combined['total_workers'] * 100
    )
    
    # Add year column
    combined['year'] = year
    
    # Select and reorder columns
    combined = combined[[
        'year',
        'county_name',
        'county_full_name',
        'state',
        'county',
        'total_workers',
        'work_from_home',
        'work_from_home_pct'
    ]]
    
    # Sort by county name
    combined.sort_values('county_name', inplace=True)
    
    print(f"  Total records: {len(combined)}")
    print(f"  Total workers: {combined['total_workers'].sum():,}")
    print(f"  Total WFH: {combined['work_from_home'].sum():,}")
    print(f"  Average WFH %: {combined['work_from_home_pct'].mean():.2f}%")
    
    return combined


def main():
    """Main execution function."""
    print("="*60)
    print("ACS 1-Year Commute Data Fetcher")
    print("Table B08006: Means of Transportation to Work")
    print("="*60)
    
    # Load API key
    print(f"\nLoading Census API key from: {CENSUS_API_KEY_FILE}")
    try:
        with open(CENSUS_API_KEY_FILE) as f:
            api_key = f.read().strip()
        census_api = Census(api_key)
        print("  ✓ API key loaded")
    except FileNotFoundError:
        print(f"  ✗ API key file not found: {CENSUS_API_KEY_FILE}")
        return
    except Exception as e:
        print(f"  ✗ Error loading API key: {e}")
        return
    
    # Fetch data for both years
    results = {}
    for year in [2019, 2023]:
        df = fetch_commute_data(year, census_api)
        if df is not None:
            results[year] = df
    
    if not results:
        print("\n✗ No data retrieved")
        return
    
    # Save individual year files
    print("\n" + "="*60)
    print("SAVING RESULTS")
    print("="*60)
    
    for year, df in results.items():
        output_file = OUTPUT_DIR / f"commute_data_{year}.csv"
        df.to_csv(output_file, index=False)
        print(f"\nSaved {year} data: {output_file}")
        print(f"  {len(df)} counties")
        print("\n  Sample data:")
        print(df[['county_name', 'total_workers', 'work_from_home', 'work_from_home_pct']].head(3).to_string(index=False))
    
    # Create combined file
    if len(results) > 1:
        combined_all = pd.concat(results.values(), ignore_index=True)
        combined_file = OUTPUT_DIR / "commute_data_combined.csv"
        combined_all.to_csv(combined_file, index=False)
        print(f"\nSaved combined data: {combined_file}")
        print(f"  {len(combined_all)} total records")
        
        # Show comparison
        print("\n" + "="*60)
        print("WORK FROM HOME COMPARISON")
        print("="*60)
        pivot = combined_all.pivot_table(
            index='county_name',
            columns='year',
            values=['work_from_home_pct'],
            aggfunc='first'
        )
        pivot.columns = [f'WFH_pct_{col[1]}' for col in pivot.columns]
        pivot['Change'] = pivot['WFH_pct_2023'] - pivot['WFH_pct_2019']
        print(pivot.round(2).to_string())
    
    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
