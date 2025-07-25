"""
Debug the PUMA values in the shapefiles to understand the formatting issue
"""
import geopandas as gpd
import pandas as pd

def debug_puma_values():
    """Check PUMA values in the shapefile"""
    
    print("=" * 60)
    print("DEBUGGING PUMA VALUES IN SHAPEFILES")
    print("=" * 60)
    
    # Load the 2020 PUMA shapefile
    puma_shapefile = r'C:\GitHub\tm2py-utils\tm2py_utils\inputs\maz_taz\shapefiles\tl_2022_06_puma20.shp'
    
    print(f"Loading PUMA shapefile: {puma_shapefile}")
    puma_gdf = gpd.read_file(puma_shapefile)
    
    # Filter for California
    ca_pumas = puma_gdf[puma_gdf['STATEFP20'] == '06']
    print(f"California PUMAs: {len(ca_pumas)}")
    
    # Check PUMA ID column
    puma_id_col = 'PUMACE20'
    print(f"Using PUMA ID column: {puma_id_col}")
    
    # Sample PUMA values
    print(f"\nSample PUMA values (first 10):")
    sample_pumas = ca_pumas[puma_id_col].head(10).tolist()
    for puma in sample_pumas:
        print(f"  Original: '{puma}' -> Formatted: '{str(puma).zfill(5)}'")
    
    # All unique PUMA values
    all_pumas = sorted(ca_pumas[puma_id_col].unique())
    print(f"\nAll California PUMAs ({len(all_pumas)}):")
    for puma in all_pumas:
        formatted = str(puma).zfill(5)
        print(f"  {puma} -> {formatted}")
    
    # Compare with our expected seed PUMAs
    SEED_PUMAS = [
        '00101', '00111', '00112', '00113', '00114', '00115', '00116', '00117', '00118', '00119',
        '00120', '00121', '00122', '00123', '01301', '01305', '01308', '01309', '01310', '01311',
        '01312', '01313', '01314', '04103', '04104', '05303', '05500', '07507', '07508', '07509',
        '07510', '07511', '07512', '07513', '07514', '08101', '08102', '08103', '08104', '08105',
        '08106', '08505', '08506', '08507', '08508', '08510', '08511', '08512', '08515', '08516',
        '08517', '08518', '08519', '08520', '08521', '08522', '08701', '09501', '09502', '09503',
        '09702', '09704', '09705', '09706', '11301'
    ]
    
    formatted_pumas = [str(puma).zfill(5) for puma in all_pumas]
    
    print(f"\nComparison with seed PUMAs:")
    print(f"  Shapefile PUMAs: {len(formatted_pumas)}")
    print(f"  Seed PUMAs: {len(SEED_PUMAS)}")
    
    missing_in_shapefile = set(SEED_PUMAS) - set(formatted_pumas)
    extra_in_shapefile = set(formatted_pumas) - set(SEED_PUMAS)
    
    if missing_in_shapefile:
        print(f"\n❌ PUMAs in seed but NOT in shapefile ({len(missing_in_shapefile)}):")
        for puma in sorted(missing_in_shapefile):
            print(f"   {puma}")
    
    if extra_in_shapefile:
        print(f"\n⚠️  PUMAs in shapefile but NOT in seed ({len(extra_in_shapefile)}):")
        for puma in sorted(extra_in_shapefile):
            print(f"   {puma}")
    
    if not missing_in_shapefile and not extra_in_shapefile:
        print(f"\n✅ Perfect match!")

if __name__ == "__main__":
    debug_puma_values()
