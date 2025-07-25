#!/usr/bin/env python3
"""
Update geography crosswalk to use correct 2020 PUMA definitions
"""

import pandas as pd
import os

def update_geo_crosswalk():
    """Update the geography crosswalk file with correct 2020 PUMA codes"""
    
    print("="*80)
    print("UPDATING GEOGRAPHY CROSSWALK - 2020 PUMA CORRECTIONS")
    print("="*80)
    
    # Load the current crosswalk
    input_file = "output_2023/geo_cross_walk_tm2.csv"
    output_file = "output_2023/geo_cross_walk_tm2_updated.csv"
    backup_file = "output_2023/geo_cross_walk_tm2_backup.csv"
    
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return
    
    print(f"📊 Loading current crosswalk: {input_file}")
    geo_df = pd.read_csv(input_file, dtype={'PUMA': str})
    geo_df['PUMA'] = geo_df['PUMA'].astype(str).str.zfill(5)
    
    print(f"   Records: {len(geo_df):,}")
    print(f"   Unique PUMAs: {len(geo_df['PUMA'].unique())}")
    
    # Create backup
    print(f"📁 Creating backup: {backup_file}")
    geo_df.to_csv(backup_file, index=False)
    
    # PUMA mapping from current (geography) to correct (2020 Census)
    puma_mapping = {
        # San Francisco County - these appear to be incorrectly mapped to Marin codes
        # Geography uses 07501-07507, but SF should be 00101-00107
        '07501': '00101',
        '07502': '00102', 
        '07503': '00103',
        '07504': '00104',
        '07505': '00105',
        '07506': '00106',
        '07507': '00107',
        
        # Alameda County - geography uses 00101-00110, should be 01301-01313
        '00101': '01301',
        '00102': '01302',
        '00103': '01303', 
        '00104': '01304',
        '00105': '01305',
        '00106': '01306',
        '00107': '01307',
        '00108': '01308',
        '00109': '01309',
        '00110': '01310',
        # Need to split some PUMAs to get to 13 total for Alameda
        
        # Contra Costa County - geography uses 01301-01309, should be 04101-04104
        '01301': '04101',
        '01302': '04102', 
        '01303': '04103',
        '01304': '04104',
        # The geography has 9 PUMAs but 2020 census only has 4 - need to consolidate
        '01305': '04104',  # Merge with 04104
        '01306': '04103',  # Merge with 04103
        '01307': '04102',  # Merge with 04102
        '01308': '04101',  # Merge with 04101
        '01309': '04104',  # Merge with 04104
        
        # Marin County - geography uses 04101-04102, should be 07501-07507
        '04101': '07501',
        '04102': '07502',
        # Need to expand to 7 PUMAs - will need to split existing areas
        
        # San Mateo County - geography uses 08101-08106, but Census shows only 05500
        '08101': '05500',
        '08102': '05500',  # Merge all into single PUMA
        '08103': '05500',
        '08104': '05500', 
        '08105': '05500',
        '08106': '05500',
        
        # Santa Clara County - remove extra PUMAs 08513, 08514
        '08513': '08512',  # Merge with existing
        '08514': '08511',  # Merge with existing
        
        # Sonoma County - geography uses 09701-09703, Census shows 09501-09503
        '09701': '09501',
        '09702': '09502', 
        '09703': '09503',
        
        # Napa County - geography uses 05500, should be 09702
        '05500': '09702',
    }
    
    print(f"\\n🔄 Applying PUMA corrections...")
    print(f"   Mapping {len(puma_mapping)} PUMA codes")
    
    # Apply the mapping
    original_pumas = geo_df['PUMA'].value_counts()
    
    # Update PUMA codes
    geo_df['PUMA_OLD'] = geo_df['PUMA']  # Keep original for reference
    geo_df['PUMA'] = geo_df['PUMA'].map(puma_mapping).fillna(geo_df['PUMA'])
    
    # Show changes
    updated_pumas = geo_df['PUMA'].value_counts()
    
    print(f"\\n📊 PUMA CHANGES:")
    print("="*50)
    print(f"Original unique PUMAs: {len(original_pumas)}")
    print(f"Updated unique PUMAs: {len(updated_pumas)}")
    
    # Show specific changes
    changes = geo_df[geo_df['PUMA'] != geo_df['PUMA_OLD']]
    if len(changes) > 0:
        print(f"\\n📝 Records updated: {len(changes):,}")
        change_summary = changes.groupby(['PUMA_OLD', 'PUMA']).size().reset_index(name='Records')
        for _, row in change_summary.iterrows():
            print(f"   {row['PUMA_OLD']} → {row['PUMA']}: {row['Records']:,} records")
    
    # Check for missing 2020 PUMAs that we need to create
    target_2020_pumas = [
        '00101', '00102', '00103', '00104', '00105', '00106', '00107',  # SF
        '01301', '01302', '01303', '01304', '01305', '01306', '01307',   # Alameda
        '01308', '01309', '01310', '01311', '01312', '01313',
        '04101', '04102', '04103', '04104',  # Contra Costa
        '05500',  # San Mateo  
        '07501', '07502', '07503', '07504', '07505', '07506', '07507',  # Marin
        '08101', '08102', '08103', '08104', '08105', '08106',  # Santa Clara
        '08501', '08502', '08503', '08504', '08505', '08506', '08507',
        '08508', '08509', '08510', '08511', '08512',
        '09501', '09502', '09503',  # Sonoma
        '09702'  # Napa
    ]
    
    current_pumas = set(geo_df['PUMA'].unique())
    target_pumas = set(target_2020_pumas)
    
    still_missing = target_pumas - current_pumas
    
    if still_missing:
        print(f"\\n⚠️  Still missing PUMAs after mapping: {sorted(still_missing)}")
        print("   These will need manual geographic splitting or other data sources")
    
    # Update county names to match PUMA assignments
    county_mapping = {
        '00101': 'San Francisco', '00102': 'San Francisco', '00103': 'San Francisco',
        '00104': 'San Francisco', '00105': 'San Francisco', '00106': 'San Francisco', '00107': 'San Francisco',
        '01301': 'Alameda', '01302': 'Alameda', '01303': 'Alameda', '01304': 'Alameda',
        '01305': 'Alameda', '01306': 'Alameda', '01307': 'Alameda', '01308': 'Alameda',
        '01309': 'Alameda', '01310': 'Alameda', '01311': 'Alameda', '01312': 'Alameda', '01313': 'Alameda',
        '04101': 'Contra Costa', '04102': 'Contra Costa', '04103': 'Contra Costa', '04104': 'Contra Costa',
        '05500': 'San Mateo',
        '07501': 'Marin', '07502': 'Marin', '07503': 'Marin', '07504': 'Marin',
        '07505': 'Marin', '07506': 'Marin', '07507': 'Marin',
        '08101': 'Santa Clara', '08102': 'Santa Clara', '08103': 'Santa Clara', '08104': 'Santa Clara',
        '08105': 'Santa Clara', '08106': 'Santa Clara', '08501': 'Santa Clara', '08502': 'Santa Clara',
        '08503': 'Santa Clara', '08504': 'Santa Clara', '08505': 'Santa Clara', '08506': 'Santa Clara',
        '08507': 'Santa Clara', '08508': 'Santa Clara', '08509': 'Santa Clara', '08510': 'Santa Clara',
        '08511': 'Santa Clara', '08512': 'Santa Clara',
        '09501': 'Sonoma', '09502': 'Sonoma', '09503': 'Sonoma',  
        '09702': 'Napa'
    }
    
    geo_df['county_name'] = geo_df['PUMA'].map(county_mapping).fillna(geo_df['county_name'])
    
    # Drop the old PUMA column
    geo_df = geo_df.drop('PUMA_OLD', axis=1)
    
    # Save updated file
    print(f"\\n💾 Saving updated crosswalk: {output_file}")
    geo_df.to_csv(output_file, index=False)
    
    # Final summary
    final_pumas = sorted(geo_df['PUMA'].unique())
    print(f"\\n📊 FINAL SUMMARY:")
    print("="*50)
    print(f"Updated crosswalk saved to: {output_file}")
    print(f"Backup saved to: {backup_file}")
    print(f"Total records: {len(geo_df):,}")
    print(f"Unique PUMAs: {len(final_pumas)}")
    print(f"PUMA list: {final_pumas}")
    
    return output_file

if __name__ == "__main__":
    update_geo_crosswalk()
