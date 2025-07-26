#!/usr/bin/env python3
"""
Analyze PUMS files and show counts by PUMA with year definitions
"""

import pandas as pd
import os

def analyze_puma_coverage():
    """Analyze PUMA coverage in the existing files"""
    
    # PUMA definitions by year
    pumas_2010_only = [
        # These existed in 2010 but not in 2020
        '04100', '04105', '04106', '04107', '04108', '04109', '04110', 
        '04111', '04112', '04113', '04114'
    ]
    
    pumas_2020_only = [
        # These exist in 2020 but not in 2010  
        '04101', '04102', '04103', '04104'
    ]
    
    pumas_both_years = [
        # San Francisco County (same in both years)
        '00101', '00102', '00103', '00104', '00105', '00106', '00107',
        
        # Alameda County (same in both years)
        '01301', '01302', '01303', '01304', '01305', '01306', '01307', 
        '01308', '01309', '01310', '01311', '01312', '01313',
        
        # San Mateo County (same in both years)
        '05500',
        
        # Marin County (same in both years)
        '07501', '07502', '07503', '07504', '07505', '07506', '07507',
        
        # Santa Clara County (same in both years)
        '08101', '08102', '08103', '08104', '08105', '08106',
        '08501', '08502', '08503', '08504', '08505', '08506', '08507', 
        '08508', '08509', '08510', '08511', '08512',
        
        # Sonoma County (2020 definitions but likely same)
        '09501', '09502', '09503',
        
        # Napa County (2020 definitions)
        '09702'
    ]
    
    # County mapping
    county_names = {
        '001': 'San Francisco',
        '013': 'Contra Costa', 
        '041': 'Marin',
        '075': 'San Francisco',  # Alternative code
        '081': 'San Mateo',
        '085': 'Santa Clara',
        '097': 'Sonoma',
        '055': 'Napa'
    }
    
    def get_county_from_puma(puma):
        """Map PUMA to county"""
        if puma.startswith('001'):
            return 'San Francisco'
        elif puma.startswith('013') or puma.startswith('041'):
            return 'Contra Costa' 
        elif puma.startswith('055'):
            return 'Napa'
        elif puma.startswith('075'):
            return 'San Francisco'
        elif puma.startswith('081'):
            return 'San Mateo'
        elif puma.startswith('085'):
            return 'Santa Clara'
        elif puma.startswith('097'):
            return 'Sonoma'
        elif puma.startswith('01'):
            return 'Alameda'
        elif puma.startswith('04'):
            return 'Contra Costa'
        elif puma.startswith('05'):
            return 'San Mateo'
        elif puma.startswith('07'):
            return 'Marin'
        elif puma.startswith('08'):
            return 'Santa Clara'
        elif puma.startswith('09'):
            if puma.endswith('02'):
                return 'Napa'
            else:
                return 'Sonoma'
        else:
            return 'Unknown'
    
    def get_puma_year_type(puma):
        """Determine if PUMA is from 2010, 2020, or both"""
        if puma in pumas_2010_only:
            return '2010 only'
        elif puma in pumas_2020_only:
            return '2020 only'
        elif puma in pumas_both_years:
            return 'Both years'
        else:
            return 'Unknown'
    
    print("="*80)
    print("PUMA COVERAGE ANALYSIS - Bay Area PUMS 2019-2023")
    print("="*80)
    
    # Check if files exist
    h_file = "M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23/hbayarea1923.csv"
    p_file = "M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23/pbayarea1923.csv"
    
    if not os.path.exists(h_file):
        print(f"❌ Household file not found: {h_file}")
        return
    
    if not os.path.exists(p_file):
        print(f"❌ Person file not found: {p_file}")
        return
    
    print(f"📊 Analyzing files:")
    print(f"   Households: {h_file}")
    print(f"   Persons: {p_file}")
    
    # Load household data
    print(f"\n🔄 Loading household data...")
    h_df = pd.read_csv(h_file, dtype={'PUMA': str}, low_memory=False)
    h_df['PUMA'] = h_df['PUMA'].astype(str).str.zfill(5)
    
    # Load person data  
    print(f"🔄 Loading person data...")
    p_df = pd.read_csv(p_file, dtype={'PUMA': str}, low_memory=False)
    p_df['PUMA'] = p_df['PUMA'].astype(str).str.zfill(5)
    
    # Get PUMA counts
    h_counts = h_df['PUMA'].value_counts().sort_index()
    p_counts = p_df['PUMA'].value_counts().sort_index()
    
    print(f"\n📈 SUMMARY:")
    print(f"   Total households: {len(h_df):,}")
    print(f"   Total persons: {len(p_df):,}")
    print(f"   Unique PUMAs: {len(h_counts)}")
    
    # Create analysis table
    analysis_data = []
    
    for puma in sorted(h_counts.index):
        county = get_county_from_puma(puma)
        year_type = get_puma_year_type(puma)
        hh_count = h_counts.get(puma, 0)
        p_count = p_counts.get(puma, 0)
        
        analysis_data.append({
            'PUMA': puma,
            'County': county,
            'Year_Type': year_type,
            'Households': hh_count,
            'Persons': p_count
        })
    
    # Convert to DataFrame for easy display
    analysis_df = pd.DataFrame(analysis_data)
    
    print(f"\n📋 DETAILED PUMA ANALYSIS:")
    print("="*80)
    print(f"{'PUMA':<6} {'County':<15} {'Year Type':<12} {'Households':<12} {'Persons':<12}")
    print("-"*80)
    
    for _, row in analysis_df.iterrows():
        print(f"{row['PUMA']:<6} {row['County']:<15} {row['Year_Type']:<12} {row['Households']:<12,} {row['Persons']:<12,}")
    
    # Summary by year type
    print(f"\n📊 SUMMARY BY PUMA YEAR TYPE:")
    print("="*50)
    
    year_summary = analysis_df.groupby('Year_Type').agg({
        'PUMA': 'count',
        'Households': 'sum', 
        'Persons': 'sum'
    }).rename(columns={'PUMA': 'PUMA_Count'})
    
    for year_type, data in year_summary.iterrows():
        print(f"{year_type}:")
        print(f"  PUMAs: {data['PUMA_Count']}")
        print(f"  Households: {data['Households']:,}")
        print(f"  Persons: {data['Persons']:,}")
        print()
    
    # Summary by county
    print(f"📊 SUMMARY BY COUNTY:")
    print("="*50)
    
    county_summary = analysis_df.groupby('County').agg({
        'PUMA': 'count',
        'Households': 'sum',
        'Persons': 'sum'
    }).rename(columns={'PUMA': 'PUMA_Count'}).sort_values('Households', ascending=False)
    
    for county, data in county_summary.iterrows():
        print(f"{county}:")
        print(f"  PUMAs: {data['PUMA_Count']}")
        print(f"  Households: {data['Households']:,}")
        print(f"  Persons: {data['Persons']:,}")
        print()
    
    # Show the benefit of combined approach
    print(f"🎉 COMBINED APPROACH BENEFITS:")
    print("="*50)
    
    current_pumas = [
        '00101', '01301', '01305', '01308', '01309', '05500', '07507',
        '08101', '08102', '08103', '08104', '08105', '08106', '08505',
        '08506', '08507', '08508', '08510', '08511', '08512', '09501',
        '09502', '09503', '09702'
    ]
    
    found_pumas = list(analysis_df['PUMA'])
    new_pumas = set(found_pumas) - set(current_pumas)
    
    current_hh = analysis_df[analysis_df['PUMA'].isin(current_pumas)]['Households'].sum()
    total_hh = analysis_df['Households'].sum()
    gained_hh = total_hh - current_hh
    
    current_p = analysis_df[analysis_df['PUMA'].isin(current_pumas)]['Persons'].sum()
    total_p = analysis_df['Persons'].sum()
    gained_p = total_p - current_p
    
    print(f"Original approach (24 PUMAs):")
    print(f"  Households: {current_hh:,}")
    print(f"  Persons: {current_p:,}")
    print()
    print(f"Combined approach ({len(found_pumas)} PUMAs):")
    print(f"  Households: {total_hh:,}")
    print(f"  Persons: {total_p:,}")
    print()
    print(f"IMPROVEMENT:")
    print(f"  Additional PUMAs: {len(new_pumas)}")
    print(f"  Additional households: {gained_hh:,} (+{gained_hh/current_hh*100:.1f}%)")
    print(f"  Additional persons: {gained_p:,} (+{gained_p/current_p*100:.1f}%)")
    
    return analysis_df

if __name__ == "__main__":
    analyze_puma_coverage()
