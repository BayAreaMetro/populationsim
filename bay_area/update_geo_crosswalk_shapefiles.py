#!/usr/bin/env python3
"""
Update geography crosswalk using 2020 PUMA shapefiles
This script spatially intersects MAZ/TAZ boundaries with 2020 PUMA boundaries
"""

import pandas as pd
import geopandas as gpd
import os
from pathlib import Path

def update_geo_crosswalk_with_shapefiles():
    """Update the geography crosswalk using spatial intersection with 2020 PUMA shapefiles"""
    
    print("="*80)
    print("UPDATING GEOGRAPHY CROSSWALK USING 2020 PUMA SHAPEFILES")
    print("="*80)
    
    # File paths
    input_file = "output_2023/geo_cross_walk_tm2.csv"
    backup_file = "output_2023/geo_cross_walk_tm2_backup.csv"
    output_file = "output_2023/geo_cross_walk_tm2_updated.csv"
    
    # Shapefile paths
    shapefile_dirs = [
        "C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles",
        "local_data/gis",
        "input_2023/gis", 
        "../shapefiles",
        "C:/shapefiles",
        "M:/Data/GIS"
    ]
    
    print("🔍 Looking for required shapefiles...")
    
    # Look for MAZ/TAZ shapefiles
    maz_shapefile = None
    taz_shapefile = None
    puma_2020_shapefile = None
    
    for dir_path in shapefile_dirs:
        if os.path.exists(dir_path):
            print(f"   Checking: {dir_path}")
            for file in Path(dir_path).rglob("*.shp"):
                filename = file.name.lower()
                if ("maz" in filename or "microzone" in filename) and not maz_shapefile:
                    maz_shapefile = str(file)
                    print(f"   Found MAZ shapefile: {maz_shapefile}")
                elif ("taz" in filename or "taz2" in filename or "traffic" in filename) and not taz_shapefile:
                    taz_shapefile = str(file) 
                    print(f"   Found TAZ shapefile: {taz_shapefile}")
                elif ("puma" in filename and ("2020" in filename or "20" in filename)) and not puma_2020_shapefile:
                    puma_2020_shapefile = str(file)
                    print(f"   Found 2020 PUMA shapefile: {puma_2020_shapefile}")
                elif "puma" in filename and not puma_2020_shapefile:  # Fallback for any PUMA file
                    puma_2020_shapefile = str(file)
                    print(f"   Found PUMA shapefile: {puma_2020_shapefile}")
    
    # Check what we found
    missing_files = []
    if not maz_shapefile:
        missing_files.append("MAZ shapefile")
    if not taz_shapefile:
        missing_files.append("TAZ shapefile") 
    if not puma_2020_shapefile:
        missing_files.append("2020 PUMA shapefile")
    
    if missing_files:
        print(f"\\n❌ Missing required shapefiles:")
        for file in missing_files:
            print(f"   - {file}")
        print(f"\\nPlease ensure the following shapefiles are available:")
        print(f"   - MAZ boundaries (MAZ polygons)")
        print(f"   - TAZ boundaries (TAZ polygons)")  
        print(f"   - 2020 PUMA boundaries from Census Bureau")
        print(f"\\nYou can download 2020 PUMA shapefiles from:")
        print(f"   https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html")
        return None
    
    # Load current crosswalk
    if not os.path.exists(input_file):
        print(f"❌ Input crosswalk file not found: {input_file}")
        return None
    
    print(f"\\n📊 Loading current crosswalk: {input_file}")
    geo_df = pd.read_csv(input_file)
    
    # Create backup
    print(f"📁 Creating backup: {backup_file}")
    geo_df.to_csv(backup_file, index=False)
    
    print(f"\\n🗺️  Loading shapefiles...")
    
    try:
        # Load MAZ boundaries
        print(f"   Loading MAZ shapefile: {maz_shapefile}")
        maz_gdf = gpd.read_file(maz_shapefile)
        print(f"   MAZ records: {len(maz_gdf):,}")
        
        # Load 2020 PUMA boundaries  
        print(f"   Loading 2020 PUMA shapefile: {puma_2020_shapefile}")
        puma_gdf = gpd.read_file(puma_2020_shapefile)
        
        # Filter for California PUMAs
        if 'STATEFP' in puma_gdf.columns:
            puma_gdf = puma_gdf[puma_gdf['STATEFP'] == '06']  # California
        elif 'STATEFP20' in puma_gdf.columns:
            puma_gdf = puma_gdf[puma_gdf['STATEFP20'] == '06']  # California
            
        print(f"   California PUMA records: {len(puma_gdf):,}")
        
        # Get PUMA ID column name
        puma_id_col = None
        for col in ['PUMACE20', 'PUMACE', 'PUMA20', 'PUMA']:
            if col in puma_gdf.columns:
                puma_id_col = col
                break
                
        if not puma_id_col:
            print(f"❌ Could not find PUMA ID column in shapefile")
            print(f"   Available columns: {list(puma_gdf.columns)}")
            return None
            
        print(f"   Using PUMA ID column: {puma_id_col}")
        
        # Ensure same CRS
        if maz_gdf.crs != puma_gdf.crs:
            print(f"   Reprojecting PUMA data to match MAZ CRS")
            puma_gdf = puma_gdf.to_crs(maz_gdf.crs)
        
        # Get MAZ ID column name
        maz_id_col = None
        for col in ['maz', 'MAZ', 'MAZ_ID', 'MAZID']:
            if col in maz_gdf.columns:
                maz_id_col = col
                break
                
        if not maz_id_col:
            print(f"❌ Could not find MAZ ID column in shapefile")
            print(f"   Available columns: {list(maz_gdf.columns)}")
            return None
            
        print(f"   Using MAZ ID column: {maz_id_col}")
        
        # Perform spatial intersection
        print(f"\\n🔄 Performing spatial intersection...")
        print(f"   This may take several minutes for large datasets...")
        
        # Use spatial join to assign PUMAs to MAZs
        maz_puma = gpd.sjoin(maz_gdf, puma_gdf, how='left', predicate='intersects')
        
        # Create new crosswalk mapping
        new_mapping = maz_puma[[maz_id_col, puma_id_col]].copy()
        new_mapping.columns = ['MAZ', 'PUMA_NEW']
        new_mapping['PUMA_NEW'] = new_mapping['PUMA_NEW'].astype(str).str.zfill(5)
        
        # Remove any duplicates (MAZ might intersect multiple PUMAs)
        new_mapping = new_mapping.drop_duplicates(subset=['MAZ'])
        
        print(f"   Mapped {len(new_mapping):,} MAZs to 2020 PUMAs")
        
        # Merge with original crosswalk
        print(f"\\n🔗 Updating crosswalk...")
        geo_updated = geo_df.merge(new_mapping, on='MAZ', how='left')
        
        # Update PUMA codes where we have matches
        geo_updated['PUMA_OLD'] = geo_updated['PUMA']
        geo_updated['PUMA'] = geo_updated['PUMA_NEW'].fillna(geo_updated['PUMA'].astype(str).str.zfill(5))
        
        # Update county names based on new PUMAs
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
        
        geo_updated['county_name'] = geo_updated['PUMA'].map(county_mapping).fillna(geo_updated['county_name'])
        
        # Clean up columns
        final_df = geo_updated[['MAZ', 'TAZ', 'COUNTY', 'county_name', 'PUMA']].copy()
        
        # Ensure PUMA column is saved as strings
        final_df['PUMA'] = final_df['PUMA'].astype(str)
        
        # Show changes
        changes = geo_updated[geo_updated['PUMA'] != geo_updated['PUMA_OLD']]
        print(f"   Updated {len(changes):,} records with new PUMA assignments")
        
        if len(changes) > 0:
            change_summary = changes.groupby(['PUMA_OLD', 'PUMA']).size().reset_index(name='Records')
            print(f"\\n📝 PUMA Changes:")
            for _, row in change_summary.iterrows():
                print(f"   {row['PUMA_OLD']} → {row['PUMA']}: {row['Records']:,} records")
        
        # Save updated crosswalk
        print(f"\\n💾 Saving updated crosswalk: {output_file}")
        print(f"🔍 Debug - PUMA column dtype before save: {final_df['PUMA'].dtype}")
        print(f"🔍 Debug - Sample PUMA values before save: {final_df['PUMA'].head(5).tolist()}")
        final_df.to_csv(output_file, index=False)
        
        # Final summary
        final_pumas = sorted(final_df['PUMA'].unique())
        print(f"\\n📊 FINAL SUMMARY:")
        print("="*50)
        print(f"Updated crosswalk saved to: {output_file}")
        print(f"Backup saved to: {backup_file}")
        print(f"Total records: {len(final_df):,}")
        print(f"Unique PUMAs: {len(final_pumas)}")
        print(f"PUMA list: {final_pumas}")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error processing shapefiles: {e}")
        return None

if __name__ == "__main__":
    update_geo_crosswalk_with_shapefiles()
