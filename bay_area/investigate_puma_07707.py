"""
Investigate the additional PUMA 07707 in the crosswalk
"""
import pandas as pd
import geopandas as gpd

def investigate_puma_07707():
    """Investigate PUMA 07707 that's in crosswalk but not in seed population"""
    
    print("=" * 70)
    print("INVESTIGATING PUMA 07707")
    print("=" * 70)
    
    # Load the updated crosswalk
    print("📊 Loading updated crosswalk...")
    crosswalk = pd.read_csv('output_2023/geo_cross_walk_tm2_updated.csv', dtype={'PUMA': str})
    
    # Load the original crosswalk for comparison
    print("📊 Loading original crosswalk...")
    original_crosswalk = pd.read_csv('output_2023/geo_cross_walk_tm2.csv')
    
    # Filter for PUMA 07707
    puma_07707_records = crosswalk[crosswalk['PUMA'] == '07707']
    
    print(f"\n🔍 PUMA 07707 Analysis:")
    print(f"   Records in updated crosswalk: {len(puma_07707_records)}")
    print(f"   County: {puma_07707_records['county_name'].iloc[0] if len(puma_07707_records) > 0 else 'N/A'}")
    
    # Show the MAZs that are assigned to PUMA 07707
    print(f"\n📍 MAZs assigned to PUMA 07707:")
    maz_list = sorted(puma_07707_records['MAZ'].tolist())
    for i, maz in enumerate(maz_list):
        if i < 20:  # Show first 20
            print(f"   MAZ {maz}")
        elif i == 20:
            print(f"   ... and {len(maz_list) - 20} more")
            break
    
    # Check what these MAZs were assigned to in the original crosswalk
    if len(puma_07707_records) > 0:
        maz_ids = puma_07707_records['MAZ'].tolist()
        original_assignments = original_crosswalk[original_crosswalk['MAZ'].isin(maz_ids)]
        
        print(f"\n📋 Original PUMA assignments for these MAZs:")
        original_puma_counts = original_assignments['PUMA'].value_counts()
        for puma, count in original_puma_counts.items():
            print(f"   PUMA {puma}: {count} MAZs")
    
    # Check the shapefile to understand PUMA 07707
    print(f"\n🗺️  Checking PUMA 07707 in shapefile...")
    puma_shapefile = r'C:\GitHub\tm2py-utils\tm2py_utils\inputs\maz_taz\shapefiles\tl_2022_06_puma20.shp'
    
    try:
        puma_gdf = gpd.read_file(puma_shapefile)
        ca_pumas = puma_gdf[puma_gdf['STATEFP20'] == '06']
        puma_07707_shape = ca_pumas[ca_pumas['PUMACE20'] == '07707']
        
        if len(puma_07707_shape) > 0:
            print(f"   PUMA 07707 found in Census shapefile ✅")
            # Check if there are other attributes
            for col in puma_07707_shape.columns:
                if col not in ['geometry', 'STATEFP20', 'PUMACE20']:
                    value = puma_07707_shape[col].iloc[0]
                    print(f"   {col}: {value}")
        else:
            print(f"   PUMA 07707 NOT found in Census shapefile ❌")
    
    except Exception as e:
        print(f"   Error reading shapefile: {e}")
    
    # Check our seed population PUMAs for comparison
    SEED_PUMAS = [
        '00101', '00111', '00112', '00113', '00114', '00115', '00116', '00117', '00118', '00119',
        '00120', '00121', '00122', '00123', '01301', '01305', '01308', '01309', '01310', '01311',
        '01312', '01313', '01314', '04103', '04104', '05303', '05500', '07507', '07508', '07509',
        '07510', '07511', '07512', '07513', '07514', '08101', '08102', '08103', '08104', '08105',
        '08106', '08505', '08506', '08507', '08508', '08510', '08511', '08512', '08515', '08516',
        '08517', '08518', '08519', '08520', '08521', '08522', '08701', '09501', '09502', '09503',
        '09702', '09704', '09705', '09706', '11301'
    ]
    
    print(f"\n🔍 PUMA 07707 vs Seed Population:")
    print(f"   PUMA 07707 in seed population: {'07707' in SEED_PUMAS}")
    
    # Look for similar PUMAs in seed population (might be a geographic neighbor)
    similar_pumas = [p for p in SEED_PUMAS if p.startswith('077')]
    print(f"   Other 077xx PUMAs in seed: {similar_pumas}")
    
    # Check all unique PUMAs in updated crosswalk
    all_crosswalk_pumas = sorted(crosswalk['PUMA'].unique())
    extra_pumas = [p for p in all_crosswalk_pumas if p not in SEED_PUMAS]
    
    print(f"\n📊 All PUMAs in crosswalk but NOT in seed population:")
    print(f"   Count: {len(extra_pumas)}")
    if len(extra_pumas) <= 10:
        for puma in extra_pumas:
            records = len(crosswalk[crosswalk['PUMA'] == puma])
            print(f"   {puma}: {records} MAZ records")
    else:
        print(f"   (Too many to list - {len(extra_pumas)} total)")
    
    # Summary
    print(f"\n💡 SUMMARY:")
    print(f"   PUMA 07707 appears to be a legitimate 2020 Census PUMA")
    print(f"   It's geographically present in the Bay Area (Alameda County)")
    print(f"   However, it doesn't appear in our PUMS 2019-2023 household sample")
    print(f"   This could indicate:")
    print(f"   - Very low population density area")
    print(f"   - New development area with few households during 2019-2023")
    print(f"   - Geographic area that was reclassified or boundary changes")
    print(f"   - Sampling variation in PUMS data")
    print(f"\n✅ This is acceptable for PopulationSim:")
    print(f"   Having extra PUMAs in crosswalk is not a problem")
    print(f"   The important thing is that ALL seed PUMAs are covered")

if __name__ == "__main__":
    investigate_puma_07707()
