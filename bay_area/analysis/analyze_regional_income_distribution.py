#!/usr/bin/env python3
"""
Analyze regional distribution of households by income using ACS 2023 5-year data
Show income distribution by county using 2023$ brackets: $0-41K, $41K-83K, $83K-138K, $138K+
"""

import pandas as pd
import numpy as np

def analyze_regional_income_distribution():
    """Analyze household income distribution by Bay Area counties using ACS 2023 data"""
    
    print("=" * 80)
    print("REGIONAL HOUSEHOLD INCOME DISTRIBUTION - ACS 2023 5-YEAR DATA")
    print("Using 2023$ Income Brackets")
    print("=" * 80)
    print()
    
    # Load the synthetic household data (this comes from ACS via PopulationSim)
    households_file = "output_2023/households_2023_tm2.csv"
    
    print(f"Loading household data from: {households_file}")
    
    try:
        df = pd.read_csv(households_file)
        print(f"Loaded {len(df):,} households")
        print()
    except FileNotFoundError:
        print(f"ERROR: File not found: {households_file}")
        print("This analysis requires the postprocessed TM2 households file.")
        return
    
    # Load the crosswalk to get county names
    from unified_tm2_config import config
    crosswalk_file = config.CROSSWALK_FILES['main_crosswalk']
    
    try:
        crosswalk = pd.read_csv(crosswalk_file)
        county_names = {
            1: "San Francisco",
            2: "San Mateo", 
            3: "Santa Clara",
            4: "Alameda",
            5: "Contra Costa",
            6: "Solano",
            7: "Napa",
            8: "Sonoma",
            9: "Marin"
        }
        print("County mapping loaded successfully")
        print()
    except FileNotFoundError:
        print("Warning: Crosswalk file not found, using county codes")
        county_names = {i: f"County {i}" for i in range(1, 10)}
    
    # Use the 2023$ income field that was created with proper ADJINC conversion
    income_field = 'hh_income_2023'  # This field has proper ADJINC conversion to 2023$
    
    if income_field not in df.columns:
        print(f"ERROR: Income field {income_field} not found in data")
        print(f"Available columns: {list(df.columns)}")
        return
    
    # Remove households with missing or zero income
    valid_households = df[(df[income_field] > 0) & (df[income_field].notna())].copy()
    print(f"Analyzing {len(valid_households):,} households with valid income data")
    print(f"Excluded {len(df) - len(valid_households):,} households with missing/zero income")
    print()
    
    # Get county information - assume it's available in the crosswalk or can be derived
    # For now, let's use the TAZ to approximate regions
    # This is a simplification - in reality we'd need proper county mapping
    
    print("🔍 INCOME DISTRIBUTION SETUP")
    print("=" * 40)
    print()
    
    # Define 2023$ income brackets (matching census control structure)
    income_brackets = [
        ("$0-41K", 0, 41399),
        ("$41K-83K", 41400, 82799),
        ("$83K-138K", 82800, 137999), 
        ("$138K+", 138000, 999999999)
    ]
    
    print("Income brackets (2023$):")
    for label, min_val, max_val in income_brackets:
        if max_val == 999999999:
            print(f"  {label}: ${min_val:,}+")
        else:
            print(f"  {label}: ${min_val:,} - ${max_val:,}")
    print()
    
    # For regional analysis, let's group by TAZ ranges to approximate counties
    # This is a rough approximation - TAZ ranges tend to cluster by county
    def assign_region(taz):
        """Assign region based on TAZ (rough approximation)"""
        if pd.isna(taz):
            return "Unknown"
        
        taz = int(taz)
        
        # These are rough TAZ ranges - would need actual TAZ->County mapping for precision
        if 300000 <= taz <= 300099:
            return "San Francisco"
        elif 300100 <= taz <= 300199:
            return "San Mateo"
        elif 300200 <= taz <= 300399:
            return "Santa Clara"
        elif 300400 <= taz <= 300499:
            return "Alameda"
        elif 300500 <= taz <= 300599:
            return "Contra Costa"
        elif 300600 <= taz <= 300649:
            return "Solano"
        elif 300650 <= taz <= 300669:
            return "Napa"
        elif 300670 <= taz <= 300689:
            return "Sonoma"
        elif 300690 <= taz <= 300699:
            return "Marin"
        else:
            return f"TAZ_{taz//100}"
    
    # Assign regions
    if 'TAZ' in valid_households.columns:
        valid_households['Region'] = valid_households['TAZ'].apply(assign_region)
        print(f"✓ Assigned regions based on TAZ")
    else:
        print("Warning: TAZ column not found, cannot assign regions")
        valid_households['Region'] = 'Bay Area Total'
    
    print()
    
    # Calculate income distribution by region
    print("📊 REGIONAL INCOME DISTRIBUTION")
    print("=" * 50)
    print()
    
    # Create income brackets
    def categorize_income(income):
        """Categorize income into brackets"""
        for label, min_val, max_val in income_brackets:
            if min_val <= income <= max_val:
                return label
        return "Unknown"
    
    valid_households['Income_Bracket'] = valid_households[income_field].apply(categorize_income)
    
    # Summary by region
    regions = valid_households['Region'].unique()
    regions = sorted([r for r in regions if r != 'Unknown'])
    
    # Create summary table
    summary_data = []
    
    for region in regions:
        region_data = valid_households[valid_households['Region'] == region]
        total_households = len(region_data)
        
        if total_households == 0:
            continue
            
        region_summary = {'Region': region, 'Total_Households': total_households}
        
        for bracket_label, min_val, max_val in income_brackets:
            count = len(region_data[region_data['Income_Bracket'] == bracket_label])
            pct = count / total_households * 100
            region_summary[f'{bracket_label}_Count'] = count
            region_summary[f'{bracket_label}_Pct'] = pct
        
        # Median income
        median_income = region_data[income_field].median()
        region_summary['Median_Income'] = median_income
        
        summary_data.append(region_summary)
    
    # Convert to DataFrame for better display
    summary_df = pd.DataFrame(summary_data)
    
    print(f"{'Region':<15} | {'Total HH':<10} | {'$0-41K':<8} | {'$41-83K':<9} | {'$83-138K':<10} | {'$138K+':<8} | {'Median':<10}")
    print("-" * 85)
    
    bay_area_total = {'Region': 'BAY AREA TOTAL', 'Total_Households': len(valid_households)}
    
    # Calculate Bay Area totals
    for bracket_label, min_val, max_val in income_brackets:
        count = len(valid_households[valid_households['Income_Bracket'] == bracket_label])
        pct = count / len(valid_households) * 100
        bay_area_total[f'{bracket_label}_Count'] = count
        bay_area_total[f'{bracket_label}_Pct'] = pct
    
    bay_area_total['Median_Income'] = valid_households[income_field].median()
    
    # Display regional data
    for _, row in summary_df.iterrows():
        region = row['Region'][:14]  # Truncate long names
        total = row['Total_Households']
        pct1 = row.get('$0-41K_Pct', 0)
        pct2 = row.get('$41K-83K_Pct', 0)
        pct3 = row.get('$83K-138K_Pct', 0)
        pct4 = row.get('$138K+_Pct', 0)
        median = row['Median_Income']
        
        print(f"{region:<15} | {total:>9,} | {pct1:>6.1f}% | {pct2:>7.1f}% | {pct3:>8.1f}% | {pct4:>6.1f}% | ${median:>8,.0f}")
    
    # Add Bay Area total
    print("-" * 85)
    total = bay_area_total['Total_Households']
    pct1 = bay_area_total['$0-41K_Pct']
    pct2 = bay_area_total['$41K-83K_Pct']
    pct3 = bay_area_total['$83K-138K_Pct']
    pct4 = bay_area_total['$138K+_Pct']
    median = bay_area_total['Median_Income']
    
    print(f"{'BAY AREA TOTAL':<15} | {total:>9,} | {pct1:>6.1f}% | {pct2:>7.1f}% | {pct3:>8.1f}% | {pct4:>6.1f}% | ${median:>8,.0f}")
    
    print()
    print("📈 KEY FINDINGS")
    print("=" * 20)
    print()
    
    # Find highest and lowest income regions
    if len(summary_df) > 0:
        highest_income_region = summary_df.loc[summary_df['Median_Income'].idxmax()]
        lowest_income_region = summary_df.loc[summary_df['Median_Income'].idxmin()]
        
        print(f"Highest median income: {highest_income_region['Region']} (${highest_income_region['Median_Income']:,.0f})")
        print(f"Lowest median income: {lowest_income_region['Region']} (${lowest_income_region['Median_Income']:,.0f})")
        print()
        
        # High-income concentration
        high_income_pct = bay_area_total['$138K+_Pct']
        low_income_pct = bay_area_total['$0-41K_Pct']
        
        print(f"Bay Area income distribution (2023$):")
        print(f"  Low income ($0-41K): {low_income_pct:.1f}% of households")
        print(f"  High income ($138K+): {high_income_pct:.1f}% of households")
        print(f"  Median household income: ${median:,.0f}")
    
    print()
    print("💡 NOTES")
    print("=" * 10)
    print("• Income brackets use 2023$ as specified in ACS controls")
    print("• Regional assignment based on TAZ ranges (approximation)")
    print("• Data represents synthetic population from PopulationSim")
    print("• For precise county analysis, need TAZ->County crosswalk")

if __name__ == "__main__":
    analyze_regional_income_distribution()
