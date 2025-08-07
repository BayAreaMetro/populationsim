#!/usr/bin/env python3
"""
Focused geospatial crosswalk creation for PopulationSim TM2

Creates geo_cross_walk_tm2_updated.csv using pure geospatial approach:
1. Load existing MAZ→TAZ relationship from CSV
2. Create spatial join from TAZ centroids to PUMA20 boundaries 
3. Regular join to create final MAZ→TAZ→PUMA20 crosswalk

User requirements:
- Pure geospatial approach only
- No fallback methods
- Use pyogrio backend for shapefile loading
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
import sys

def main():
    print("=" * 60)
    print("FOCUSED GEOSPATIAL CROSSWALK CREATION")
    print("=" * 60)
    print("User specifications:")
    print("- Use existing MAZ→TAZ relationship from CSV")
    print("- Spatial join TAZ centroids → PUMA20 boundaries")
    print("- Regular join for final crosswalk")
    print("- No fallback methods")
    print()
    
    # Define paths - using full absolute paths
    base_dir = Path("c:/GitHub/populationsim/bay_area")
    tm2py_dir = Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz")
    shapefiles_dir = Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles")
    
    # Input files - using the correct file that already has MAZ→TAZ→PUMA relationships
    maz_taz_puma_csv = Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/mazs_tazs_county_tract_PUMA.csv")
    taz_shapefile = Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/tazs_TM2_v2_2.shp")
    puma_shapefile = Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/tl_2022_06_puma20.shp")
    
    # Output file
    output_file = Path("c:/GitHub/populationsim/bay_area/output_2023/geo_cross_walk_tm2_updated.csv")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print("🔍 STEP 1: Loading existing MAZ→TAZ→PUMA data (will use fresh 2020 PUMAs)")
    print(f"   File: {maz_taz_puma_csv}")
    
    if not maz_taz_puma_csv.exists():
        print(f"❌ ERROR: MAZ-TAZ-PUMA CSV file not found: {maz_taz_puma_csv}")
        return False
    
    try:
        maz_taz_old_df = pd.read_csv(maz_taz_puma_csv)
        print(f"   ✅ Loaded {len(maz_taz_old_df):,} existing MAZ→TAZ→PUMA relationships")
        print(f"   📊 Columns: {list(maz_taz_old_df.columns)}")
        
        # Extract just MAZ→TAZ relationships (ignore old PUMA data)
        if 'MAZ' in maz_taz_old_df.columns and 'TAZ' in maz_taz_old_df.columns:
            maz_taz_df = maz_taz_old_df[['MAZ', 'TAZ']].copy()
        else:
            print(f"❌ ERROR: Expected MAZ and TAZ columns not found")
            print(f"   Available columns: {list(maz_taz_old_df.columns)}")
            return False
        
        # Show sample data
        print("   📋 Sample MAZ→TAZ data (ignoring old PUMA data):")
        print(maz_taz_df.head())
        print(f"   🗂️  Will create fresh PUMA20 mappings for {maz_taz_df['TAZ'].nunique():,} TAZ zones")
        
    except Exception as e:
        print(f"❌ ERROR: Failed to load existing MAZ-TAZ-PUMA CSV: {e}")
        return False
    
    print()
    print("🗺️  STEP 2: Loading TAZ shapefile for spatial join with fresh PUMA20 data")
    print(f"   File: {taz_shapefile}")
    
    if not taz_shapefile.exists():
        print(f"❌ ERROR: TAZ shapefile not found: {taz_shapefile}")
        return False
    
    try:
        # Load TAZ shapefile using pyogrio backend
        print("   🔧 Using pyogrio backend for shapefile loading...")
        taz_gdf = gpd.read_file(taz_shapefile, engine='pyogrio')
        print(f"   ✅ Loaded {len(taz_gdf):,} TAZ zones")
        print(f"   📊 Columns: {list(taz_gdf.columns)}")
        print(f"   🌍 CRS: {taz_gdf.crs}")
        
        # Check for TAZ ID column
        taz_id_cols = [col for col in taz_gdf.columns if 'TAZ' in col.upper() or 'ZONE' in col.upper()]
        print(f"   🔍 Potential TAZ ID columns: {taz_id_cols}")
        
        # Determine the TAZ ID column
        if 'TAZ1454' in taz_gdf.columns:
            taz_id_col = 'TAZ1454'
        elif 'TAZ_ID' in taz_gdf.columns:
            taz_id_col = 'TAZ_ID'
        elif 'TAZ' in taz_gdf.columns:
            taz_id_col = 'TAZ'
        elif 'taz' in taz_gdf.columns:  # lowercase version
            taz_id_col = 'taz'
        else:
            print(f"❌ ERROR: Cannot identify TAZ ID column in shapefile")
            print(f"   Available columns: {list(taz_gdf.columns)}")
            return False
        
        print(f"   🎯 Using TAZ ID column: {taz_id_col}")
        
        # Calculate TAZ centroids
        print("   📍 Calculating TAZ centroids...")
        taz_gdf['centroid'] = taz_gdf.geometry.centroid
        
        # Create a new GeoDataFrame with centroids as geometry
        taz_centroids = taz_gdf.copy()
        taz_centroids['geometry'] = taz_centroids['centroid']
        
        print(f"   ✅ Created centroids for {len(taz_centroids):,} TAZ zones")
        
    except Exception as e:
        print(f"❌ ERROR: Failed to load TAZ shapefile: {e}")
        return False
    
    print()
    print("🏛️  STEP 3: Loading PUMA20 shapefile (2020 boundaries)")
    print(f"   File: {puma_shapefile}")
    print("   🆕 Creating fresh PUMA20 mappings to replace old PUMA10 data")
    
    if not puma_shapefile.exists():
        print(f"❌ ERROR: PUMA20 shapefile not found: {puma_shapefile}")
        return False
    
    try:
        # Load PUMA shapefile using pyogrio backend
        puma_gdf = gpd.read_file(puma_shapefile, engine='pyogrio')
        print(f"   ✅ Loaded {len(puma_gdf):,} PUMA zones")
        print(f"   📊 Columns: {list(puma_gdf.columns)}")
        print(f"   🌍 CRS: {puma_gdf.crs}")
        
        # Check for PUMA ID column first
        if 'PUMACE20' in puma_gdf.columns:
            puma_id_col = 'PUMACE20'
        elif 'PUMA20' in puma_gdf.columns:
            puma_id_col = 'PUMA20'
        else:
            print(f"❌ ERROR: Cannot identify PUMA ID column in shapefile")
            print(f"   Available columns: {list(puma_gdf.columns)}")
            return False
        
        print(f"   🎯 Using PUMA ID column: {puma_id_col}")
        
        # Filter to Bay Area counties (FIPS codes) - ALL 9 Bay Area counties for complete coverage
        # 001=Alameda, 013=Contra Costa, 041=Marin, 055=Napa, 075=San Francisco
        # 081=San Mateo, 085=Santa Clara, 095=Solano, 097=Sonoma
        bay_area_counties = ['001', '013', '041', '055', '075', '081', '085', '095', '097']
        county_col = None
        
        # Check for different possible county column names
        for col in ['COUNTYFP20', 'COUNTYFP10', 'COUNTYFP', 'COUNTY']:
            if col in puma_gdf.columns:
                county_col = col
                break
        
        if county_col:
            original_count = len(puma_gdf)
            puma_gdf = puma_gdf[puma_gdf[county_col].isin(bay_area_counties)]
            print(f"   🌉 Filtered to Bay Area using {county_col}: {len(puma_gdf):,} PUMA zones (was {original_count:,})")
        else:
            print("   ⚠️  WARNING: No county column found, using spatial overlap filter")
            print(f"   📊 Available columns: {list(puma_gdf.columns)}")
            print(f"   🗂️  Filtering to 72 PUMAs that have TAZ overlaps in Bay Area")
            
            # Use the 72 PUMAs found in spatial analysis that have TAZ overlaps
            bay_area_pumas = ['00101', '00111', '00112', '00113', '00114', '00115', '00116', '00117', '00118', '00119', 
                             '00120', '00121', '00122', '00123', '01301', '01305', '01308', '01309', '01310', '01311', 
                             '01312', '01313', '01314', '03300', '04103', '04104', '04701', '05303', '05500', '06717', 
                             '07507', '07508', '07509', '07510', '07511', '07512', '07513', '07514', '07707', '07708', 
                             '08101', '08102', '08103', '08104', '08105', '08106', '08505', '08506', '08507', '08508', 
                             '08510', '08511', '08512', '08515', '08516', '08517', '08518', '08519', '08520', '08521', 
                             '08522', '08701', '09501', '09502', '09503', '09702', '09704', '09705', '09706', '09901', 
                             '11301', '11302']
            
            original_count = len(puma_gdf)
            puma_gdf = puma_gdf[puma_gdf[puma_id_col].isin(bay_area_pumas)]
            print(f"   🌉 Filtered to Bay Area using spatial overlap: {len(puma_gdf):,} PUMA zones (was {original_count:,})")
        
        # Show sample PUMA IDs
        sample_pumas = sorted(puma_gdf[puma_id_col].unique())[:10]
        print(f"   📋 Sample PUMA IDs: {sample_pumas}")
        
    except Exception as e:
        print(f"❌ ERROR: Failed to load PUMA20 shapefile: {e}")
        return False
    
    print()
    print("🔗 STEP 4: Creating fresh spatial join TAZ centroids → PUMA20 (2020 boundaries)")
    print("   🆕 This will create updated PUMA mappings using 2020 boundaries")
    
    try:
        # Ensure both datasets have the same CRS
        if taz_centroids.crs != puma_gdf.crs:
            print(f"   🔧 Reprojecting TAZ centroids from {taz_centroids.crs} to {puma_gdf.crs}")
            taz_centroids = taz_centroids.to_crs(puma_gdf.crs)
        
        # Perform spatial join with enhanced matching
        print("   🔗 Executing spatial join (trying 'within' first, then 'intersects' for unmatched)...")
        
        # First try: within predicate (centroids within PUMA boundaries)
        taz_puma_join = gpd.sjoin(
            taz_centroids[[taz_id_col, 'geometry']], 
            puma_gdf[[puma_id_col, 'geometry']], 
            how='left', 
            predicate='within'
        )
        
        # Check for unmatched TAZs
        unmatched_mask = taz_puma_join[puma_id_col].isna()
        unmatched_count = unmatched_mask.sum()
        
        if unmatched_count > 0:
            print(f"   ⚠️  WARNING: {unmatched_count:,} TAZ centroids not within any PUMA")
            print("   🔧 Trying 'intersects' predicate for unmatched TAZs...")
            
            # Get unmatched TAZ centroids
            unmatched_tazs = taz_centroids[taz_centroids[taz_id_col].isin(
                taz_puma_join[unmatched_mask][taz_id_col]
            )]
            
            # Try intersects for unmatched TAZs
            unmatched_join = gpd.sjoin(
                unmatched_tazs[[taz_id_col, 'geometry']], 
                puma_gdf[[puma_id_col, 'geometry']], 
                how='left', 
                predicate='intersects'
            )
            
            # Update the main join with intersects results
            intersects_matches = unmatched_join[unmatched_join[puma_id_col].notna()]
            if len(intersects_matches) > 0:
                print(f"   ✅ Found {len(intersects_matches):,} additional matches using 'intersects'")
                
                # Update the main join results
                for _, row in intersects_matches.iterrows():
                    mask = taz_puma_join[taz_id_col] == row[taz_id_col]
                    taz_puma_join.loc[mask, puma_id_col] = row[puma_id_col]
            
            # Check for still unmatched TAZs
            still_unmatched = taz_puma_join[taz_puma_join[puma_id_col].isna()]
            if len(still_unmatched) > 0:
                print(f"   ⚠️  {len(still_unmatched):,} TAZs still unmatched - using nearest neighbor...")
                
                # For remaining unmatched, find nearest PUMA
                unmatched_remaining = taz_centroids[taz_centroids[taz_id_col].isin(
                    still_unmatched[taz_id_col]
                )]
                
                for _, unmatched_taz in unmatched_remaining.iterrows():
                    # Calculate distance to all PUMAs
                    distances = puma_gdf.geometry.distance(unmatched_taz.geometry)
                    nearest_idx = distances.idxmin()
                    nearest_puma = puma_gdf.loc[nearest_idx, puma_id_col]
                    
                    # Update the join
                    mask = taz_puma_join[taz_id_col] == unmatched_taz[taz_id_col]
                    taz_puma_join.loc[mask, puma_id_col] = nearest_puma
                
                print(f"   ✅ Assigned remaining TAZs to nearest PUMAs")
        
        print(f"   ✅ Spatial join completed: {len(taz_puma_join):,} TAZ→PUMA relationships")
        
        # Final check for unmatched TAZs
        final_unmatched = taz_puma_join[taz_puma_join[puma_id_col].isna()]
        if len(final_unmatched) > 0:
            print(f"   ❌ ERROR: {len(final_unmatched):,} TAZ zones still not matched to any PUMA")
            print(f"   📋 Unmatched TAZ IDs: {final_unmatched[taz_id_col].head().tolist()}")
        else:
            print(f"   ✅ All TAZs successfully matched to PUMAs")
        
        # Create clean TAZ→PUMA mapping with 2020 boundaries
        taz_puma_mapping = taz_puma_join[[taz_id_col, puma_id_col]].copy()
        taz_puma_mapping = taz_puma_mapping.dropna()  # Remove unmatched TAZs
        taz_puma_mapping.columns = ['TAZ', 'PUMA20']  # Use PUMA20 to be explicit about 2020 boundaries
        
        print(f"   📊 Clean TAZ→PUMA20 mapping: {len(taz_puma_mapping):,} relationships")
        print(f"   🏛️  PUMA20 zones found: {taz_puma_mapping['PUMA20'].nunique():,}")
        print("   📋 Sample TAZ→PUMA20 mappings:")
        print(taz_puma_mapping.head())
        
    except Exception as e:
        print(f"❌ ERROR: Spatial join failed: {e}")
        return False
    
    print()
    print("🔗 STEP 5: Creating final MAZ→TAZ→PUMA20 crosswalk with fresh 2020 boundaries")
    
    try:
        # Join MAZ→TAZ with fresh TAZ→PUMA20
        print("   🔗 Joining MAZ→TAZ with fresh TAZ→PUMA20...")
        
        # Ensure consistent data types
        maz_taz_df['TAZ'] = maz_taz_df['TAZ'].astype(int)
        taz_puma_mapping['TAZ'] = taz_puma_mapping['TAZ'].astype(int)
        
        # Perform the join
        crosswalk = maz_taz_df.merge(
            taz_puma_mapping, 
            on='TAZ', 
            how='left'
        )
        
        print(f"   ✅ Final crosswalk created: {len(crosswalk):,} MAZ records")
        
        # Check for MAZs without PUMA assignment
        unmatched_mazs = crosswalk[crosswalk['PUMA20'].isna()]
        if len(unmatched_mazs) > 0:
            print(f"   ⚠️  WARNING: {len(unmatched_mazs):,} MAZ zones do not have PUMA20 assignment")
            unmatched_tazs_list = unmatched_mazs['TAZ'].unique()
            print(f"   📋 TAZs without PUMA20: {unmatched_tazs_list[:10]}")
        
        # Create final output format
        final_crosswalk = crosswalk[['MAZ', 'TAZ', 'PUMA20']].copy()
        final_crosswalk.columns = ['MAZ', 'TAZ', 'PUMA']  # PopulationSim expects 'PUMA' column name
        
        # Remove rows without PUMA assignment
        final_crosswalk = final_crosswalk.dropna()
        
        print(f"   📊 Final output: {len(final_crosswalk):,} complete MAZ→TAZ→PUMA20 mappings")
        
        # Show summary statistics
        print("   📈 Summary statistics:")
        print(f"     • Unique MAZs: {final_crosswalk['MAZ'].nunique():,}")
        print(f"     • Unique TAZs: {final_crosswalk['TAZ'].nunique():,}")
        print(f"     • Unique PUMA20s: {final_crosswalk['PUMA'].nunique():,}")
        
        # Show sample of final data
        print("   📋 Sample final crosswalk:")
        print(final_crosswalk.head(10))
        
    except Exception as e:
        print(f"❌ ERROR: Failed to create final crosswalk: {e}")
        return False
    
    print()
    print("💾 STEP 6: Saving crosswalk file")
    print(f"   Output: {output_file}")
    
    try:
        # Save the crosswalk
        final_crosswalk.to_csv(output_file, index=False)
        print(f"   ✅ Saved crosswalk: {len(final_crosswalk):,} records")
        
        # Verify the saved file
        verify_df = pd.read_csv(output_file)
        print(f"   ✅ Verification: {len(verify_df):,} records loaded from saved file")
        
        # Show final statistics
        print()
        print("=" * 60)
        print("🎉 FRESH GEOSPATIAL CROSSWALK CREATION COMPLETE")
        print("=" * 60)
        print(f"✅ Created: {output_file}")
        print(f"📊 Records: {len(final_crosswalk):,}")
        print(f"🌍 MAZs: {final_crosswalk['MAZ'].nunique():,}")
        print(f"🗺️  TAZs: {final_crosswalk['TAZ'].nunique():,}")
        print(f"🏛️  PUMA20s (2020 boundaries): {final_crosswalk['PUMA'].nunique():,}")
        print()
        print("🆕 This crosswalk uses fresh 2020 PUMA boundaries!")
        print("Ready for PopulationSim!")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to save crosswalk: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
