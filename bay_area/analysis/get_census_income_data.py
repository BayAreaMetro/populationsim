#!/usr/bin/env python3
"""
Download household income distribution for Bay Area counties using Census API
Get actual ACS 2023 5-year data in 2023$ for the 9 Bay Area counties
"""

import requests
import pandas as pd
import numpy as np
import json

def get_bay_area_income_from_census():
    """Get household income distribution for Bay Area counties from Census API"""
    
    print("=" * 80)
    print("BAY AREA HOUSEHOLD INCOME DISTRIBUTION - CENSUS API ACS 2023 5-YEAR")
    print("Direct from Census Bureau - 2023$ Income Data")
    print("=" * 80)
    print()
    
    # Bay Area counties with FIPS codes
    bay_area_counties = {
        "001": "Alameda",
        "013": "Contra Costa", 
        "041": "Marin",
        "055": "Napa",
        "075": "San Francisco",
        "081": "San Mateo",
        "085": "Santa Clara",
        "095": "Solano",
        "097": "Sonoma"
    }
    
    # California state FIPS code
    state_fips = "06"
    
    print(f"Downloading data for {len(bay_area_counties)} Bay Area counties:")
    for fips, name in bay_area_counties.items():
        print(f"  • {name} County (FIPS: {state_fips}{fips})")
    print()
    
    # ACS 2023 5-year household income variables
    # Table B19001: Household Income in the Past 12 Months (In 2023 Inflation-Adjusted Dollars)
    income_variables = {
        # Less than $10,000
        "B19001_002E": "Under $10K",
        # $10,000 to $14,999
        "B19001_003E": "$10K-$15K",
        # $15,000 to $19,999
        "B19001_004E": "$15K-$20K", 
        # $20,000 to $24,999
        "B19001_005E": "$20K-$25K",
        # $25,000 to $29,999
        "B19001_006E": "$25K-$30K",
        # $30,000 to $34,999
        "B19001_007E": "$30K-$35K",
        # $35,000 to $39,999
        "B19001_008E": "$35K-$40K",
        # $40,000 to $44,999
        "B19001_009E": "$40K-$45K",
        # $45,000 to $49,999
        "B19001_010E": "$45K-$50K",
        # $50,000 to $59,999
        "B19001_011E": "$50K-$60K",
        # $60,000 to $74,999
        "B19001_012E": "$60K-$75K",
        # $75,000 to $99,999
        "B19001_013E": "$75K-$100K",
        # $100,000 to $124,999
        "B19001_014E": "$100K-$125K",
        # $125,000 to $149,999
        "B19001_015E": "$125K-$150K",
        # $150,000 to $199,999
        "B19001_016E": "$150K-$200K",
        # $200,000 or more
        "B19001_017E": "$200K+",
        # Total households
        "B19001_001E": "Total"
    }
    
    # Build API request
    variables = ",".join(income_variables.keys())
    county_list = ",".join(bay_area_counties.keys())
    
    # Census API endpoint for ACS 2023 5-year
    base_url = "https://api.census.gov/data/2023/acs/acs5"
    params = {
        "get": variables,
        "for": f"county:{county_list}",
        "in": f"state:{state_fips}"
    }
    
    print("🌐 Downloading data from Census API...")
    print(f"   API: {base_url}")
    print(f"   Variables: {len(income_variables)} income brackets")
    print()
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Successfully downloaded data")
        print(f"   Response size: {len(data)} rows")
        print()
        
    except requests.RequestException as e:
        print(f"❌ Error downloading data: {e}")
        return
    
    # Process the data
    print("📊 Processing Census data...")
    
    # First row is headers
    headers = data[0]
    rows = data[1:]
    
    # Create DataFrame
    df = pd.DataFrame(rows, columns=headers)
    
    # Add county names
    df['county_name'] = df['county'].map(lambda x: bay_area_counties.get(x, f"County_{x}"))
    
    print(f"   Processed {len(df)} counties")
    print()
    
    # Convert income columns to numeric
    income_cols = list(income_variables.keys())
    for col in income_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Create our target income brackets by aggregating Census brackets
    # Target: $0-41K, $41K-83K, $83K-138K, $138K+
    
    print("🎯 Mapping Census brackets to target brackets...")
    print("   Target brackets: $0-41K, $41K-83K, $83K-138K, $138K+ (2023$)")
    print()
    
    # Map census variables to our brackets
    bracket_mapping = {
        # $0-41K bracket (roughly)
        "0_41K": [
            "B19001_002E",  # Under $10K
            "B19001_003E",  # $10K-$15K
            "B19001_004E",  # $15K-$20K
            "B19001_005E",  # $20K-$25K
            "B19001_006E",  # $25K-$30K
            "B19001_007E",  # $30K-$35K
            "B19001_008E",  # $35K-$40K
            "B19001_009E",  # $40K-$45K (partial - need ~25% of this)
        ],
        # $41K-83K bracket (roughly)
        "41_83K": [
            "B19001_010E",  # $45K-$50K (partial - need ~75% of $40K-$45K + all of this)
            "B19001_011E",  # $50K-$60K
            "B19001_012E",  # $60K-$75K
            "B19001_013E",  # $75K-$100K (partial - need ~83% of this)
        ],
        # $83K-138K bracket (roughly)
        "83_138K": [
            "B19001_014E",  # $100K-$125K (partial - need ~17% of $75K-$100K + all of this)
            "B19001_015E",  # $125K-$150K (partial - need ~87% of this)
        ],
        # $138K+ bracket
        "138K_plus": [
            "B19001_016E",  # $150K-$200K (partial - need ~13% of $125K-$150K + all of this)
            "B19001_017E",  # $200K+
        ]
    }
    
    print("Census bracket to target bracket mapping:")
    print("📋 $0-41K includes:")
    print("   • Under $10K through $40K-$45K")
    print("   • Approximate adjustment: Use 25% of $40K-$45K bracket")
    print()
    print("📋 $41K-83K includes:")
    print("   • $45K-$50K through most of $75K-$100K")
    print("   • Approximate adjustment: 75% of $40K-$45K + 83% of $75K-$100K")
    print()
    print("📋 $83K-138K includes:")
    print("   • Remainder of $75K-$100K through most of $125K-$150K")
    print("   • Approximate adjustment: 17% of $75K-$100K + 87% of $125K-$150K")
    print()
    print("📋 $138K+ includes:")
    print("   • Remainder of $125K-$150K + all higher brackets")
    print("   • Approximate adjustment: 13% of $125K-$150K + $150K+")
    print()
    
    # Calculate adjusted brackets for each county
    results = []
    
    for _, row in df.iterrows():
        county_name = row['county_name']
        
        # Get values with fallback to 0 for missing data
        def get_val(var):
            return row.get(var, 0) if pd.notna(row.get(var, 0)) else 0
        
        # Calculate adjusted brackets
        bracket_0_41K = (
            get_val("B19001_002E") +   # Under $10K
            get_val("B19001_003E") +   # $10K-$15K  
            get_val("B19001_004E") +   # $15K-$20K
            get_val("B19001_005E") +   # $20K-$25K
            get_val("B19001_006E") +   # $25K-$30K
            get_val("B19001_007E") +   # $30K-$35K
            get_val("B19001_008E") +   # $35K-$40K
            get_val("B19001_009E") * 0.2  # ~20% of $40K-$45K
        )
        
        bracket_41_83K = (
            get_val("B19001_009E") * 0.8 +   # ~80% of $40K-$45K
            get_val("B19001_010E") +          # $45K-$50K
            get_val("B19001_011E") +          # $50K-$60K
            get_val("B19001_012E") +          # $60K-$75K
            get_val("B19001_013E") * 0.32     # ~32% of $75K-$100K (up to $83K)
        )
        
        bracket_83_138K = (
            get_val("B19001_013E") * 0.68 +   # ~68% of $75K-$100K (from $83K)
            get_val("B19001_014E") +          # $100K-$125K
            get_val("B19001_015E") * 0.52     # ~52% of $125K-$150K (up to $138K)
        )
        
        bracket_138K_plus = (
            get_val("B19001_015E") * 0.48 +   # ~48% of $125K-$150K (from $138K)
            get_val("B19001_016E") +          # $150K-$200K
            get_val("B19001_017E")            # $200K+
        )
        
        total_households = get_val("B19001_001E")
        
        results.append({
            "County": county_name,
            "Total_Households": int(total_households),
            "$0-41K": int(round(bracket_0_41K)),
            "$41K-83K": int(round(bracket_41_83K)),
            "$83K-138K": int(round(bracket_83_138K)),
            "$138K+": int(round(bracket_138K_plus)),
            "$0-41K_Pct": bracket_0_41K / total_households * 100 if total_households > 0 else 0,
            "$41K-83K_Pct": bracket_41_83K / total_households * 100 if total_households > 0 else 0,
            "$83K-138K_Pct": bracket_83_138K / total_households * 100 if total_households > 0 else 0,
            "$138K+_Pct": bracket_138K_plus / total_households * 100 if total_households > 0 else 0
        })
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    # Display results
    print("📊 BAY AREA HOUSEHOLD INCOME DISTRIBUTION BY COUNTY")
    print("Source: ACS 2023 5-Year Estimates (2023 Inflation-Adjusted Dollars)")
    print("=" * 95)
    print()
    
    print(f"{'County':<15} | {'Total HH':<10} | {'$0-41K':<8} | {'$41-83K':<9} | {'$83-138K':<10} | {'$138K+':<8}")
    print("-" * 75)
    
    for _, row in results_df.iterrows():
        county = row['County'][:14]
        total = row['Total_Households']
        pct1 = row['$0-41K_Pct']
        pct2 = row['$41K-83K_Pct']  
        pct3 = row['$83K-138K_Pct']
        pct4 = row['$138K+_Pct']
        
        print(f"{county:<15} | {total:>9,} | {pct1:>6.1f}% | {pct2:>7.1f}% | {pct3:>8.1f}% | {pct4:>6.1f}%")
    
    # Calculate Bay Area totals
    bay_area_totals = {
        "Total_Households": results_df['Total_Households'].sum(),
        "$0-41K": results_df['$0-41K'].sum(),
        "$41K-83K": results_df['$41K-83K'].sum(), 
        "$83K-138K": results_df['$83K-138K'].sum(),
        "$138K+": results_df['$138K+'].sum()
    }
    
    # Calculate percentages for totals
    total_hh = bay_area_totals['Total_Households']
    bay_area_totals['$0-41K_Pct'] = bay_area_totals['$0-41K'] / total_hh * 100
    bay_area_totals['$41K-83K_Pct'] = bay_area_totals['$41K-83K'] / total_hh * 100
    bay_area_totals['$83K-138K_Pct'] = bay_area_totals['$83K-138K'] / total_hh * 100
    bay_area_totals['$138K+_Pct'] = bay_area_totals['$138K+'] / total_hh * 100
    
    print("-" * 75)
    print(f"{'BAY AREA TOTAL':<15} | {total_hh:>9,} | {bay_area_totals['$0-41K_Pct']:>6.1f}% | {bay_area_totals['$41K-83K_Pct']:>7.1f}% | {bay_area_totals['$83K-138K_Pct']:>8.1f}% | {bay_area_totals['$138K+_Pct']:>6.1f}%")
    
    print()
    print("📈 KEY FINDINGS - ACTUAL ACS 2023 DATA")
    print("=" * 45)
    print()
    
    # Find highest and lowest income counties
    highest_income_county = results_df.loc[results_df['$138K+_Pct'].idxmax()]
    lowest_income_county = results_df.loc[results_df['$0-41K_Pct'].idxmax()]
    
    print(f"Highest income county: {highest_income_county['County']} ({highest_income_county['$138K+_Pct']:.1f}% high-income)")
    print(f"Most low-income households: {lowest_income_county['County']} ({lowest_income_county['$0-41K_Pct']:.1f}% low-income)")
    print()
    
    print("Bay Area summary (ACS 2023, 2023$):")
    print(f"  • Total households: {total_hh:,}")
    print(f"  • Low income ($0-41K): {bay_area_totals['$0-41K_Pct']:.1f}% ({bay_area_totals['$0-41K']:,} households)")
    print(f"  • High income ($138K+): {bay_area_totals['$138K+_Pct']:.1f}% ({bay_area_totals['$138K+']:,} households)")
    
    # Comparison with our PopulationSim output
    print()
    print("🔍 COMPARISON WITH POPULATIONSIM OUTPUT")
    print("=" * 45)
    print("This shows the ACTUAL ACS income distribution that PopulationSim")
    print("should be trying to match with its census controls.")
    print()
    print(f"ACS 2023 actual: {bay_area_totals['$0-41K_Pct']:.1f}% low-income households")
    print("PopulationSim target: Should match this closely")
    
    # Save results
    output_file = "bay_area_income_acs_2023.csv"
    results_df.to_csv(output_file, index=False)
    print()
    print(f"💾 Results saved to: {output_file}")
    
    return results_df, bay_area_totals

if __name__ == "__main__":
    get_bay_area_income_from_census()
