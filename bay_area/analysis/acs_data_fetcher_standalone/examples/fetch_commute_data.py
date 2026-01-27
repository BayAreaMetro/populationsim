#!/usr/bin/env python3
"""
Example: Fetch work-from-home commute data (B08006) for Bay Area counties.

Table B08006: Sex of Workers by Means of Transportation to Work
- B08006_001E: Total workers
- B08006_017E: Worked from home

Calculates work-from-home percentage for 2019 and 2023.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from acs_fetcher import ACSDataFetcher
from config import (
    CENSUS_API_KEY_FILE,
    BAY_AREA_COUNTIES,
    CA_STATE_FIPS,
    OUTPUT_DIR
)


def main():
    """Fetch and analyze work-from-home commute data."""
    print("="*60)
    print("ACS Commute Data Fetcher")
    print("Table B08006: Means of Transportation to Work")
    print("="*60)
    
    # Initialize fetcher
    fetcher = ACSDataFetcher(CENSUS_API_KEY_FILE)
    
    # Define variables to fetch
    variables = [
        'B08006_001E',  # Total workers
        'B08006_017E',  # Worked from home
    ]
    
    # Fetch data for 2019 and 2023
    years = [2019, 2023]
    
    all_data = []
    for year in years:
        df = fetcher.fetch_variables(
            variables=variables,
            year=year,
            counties=BAY_AREA_COUNTIES,
            state_fips=CA_STATE_FIPS,
            dataset='acs1'
        )
        
        if df is not None:
            all_data.append(df)
    
    if not all_data:
        print("\n✗ No data retrieved")
        return
    
    # Combine all years
    import pandas as pd
    combined = pd.concat(all_data, ignore_index=True)
    
    # Rename columns for clarity
    combined.rename(columns={
        'B08006_001E': 'total_workers',
        'B08006_017E': 'work_from_home',
        'NAME': 'county_full_name',
    }, inplace=True)
    
    # Calculate work-from-home percentage
    combined = fetcher.calculate_percentage(
        combined,
        numerator_col='work_from_home',
        denominator_col='total_workers',
        output_col='work_from_home_pct'
    )
    
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
    
    # Sort by year and county
    combined.sort_values(['year', 'county_name'], inplace=True)
    
    # Save results
    print("\n" + "="*60)
    print("SAVING RESULTS")
    print("="*60)
    
    # Save combined file
    output_file = OUTPUT_DIR / "commute_data_combined.csv"
    fetcher.save_results(combined, output_file)
    
    # Save individual year files
    for year in years:
        year_data = combined[combined['year'] == year]
        year_file = OUTPUT_DIR / f"commute_data_{year}.csv"
        fetcher.save_results(year_data, year_file, print_summary=False)
    
    # Print comparison
    print("\n" + "="*60)
    print("WORK FROM HOME COMPARISON")
    print("="*60)
    
    pivot = combined.pivot_table(
        index='county_name',
        columns='year',
        values=['work_from_home_pct'],
        aggfunc='first'
    )
    pivot.columns = [f'WFH_pct_{int(col[1])}' for col in pivot.columns]
    
    if len(years) > 1:
        pivot['Change'] = pivot[f'WFH_pct_{years[-1]}'] - pivot[f'WFH_pct_{years[0]}']
    
    print(pivot.round(2).to_string())
    
    # Regional summary
    print("\n" + "="*60)
    print("REGIONAL SUMMARY")
    print("="*60)
    
    for year in years:
        year_data = combined[combined['year'] == year]
        total_workers = year_data['total_workers'].sum()
        total_wfh = year_data['work_from_home'].sum()
        avg_pct = (total_wfh / total_workers * 100)
        
        print(f"\n{year}:")
        print(f"  Total workers: {total_workers:,.0f}")
        print(f"  Work from home: {total_wfh:,.0f}")
        print(f"  WFH percentage: {avg_pct:.2f}%")
    
    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
