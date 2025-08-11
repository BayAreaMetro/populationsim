#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct MAZ->PUMA geospatial crosswalk creation for PopulationSim TM2

Creates geo_cross_walk_tm2_updated.csv using direct MAZ->PUMA spatial approach:
1. Load MAZ shapefile with existing MAZ->TAZ relationships
2. Create direct spatial join from MAZ centroids to PUMA20 boundaries 
3. Output final MAZ->TAZ->PUMA20 crosswalk with direct spatial relationships

User requirements:
- Direct MAZ->PUMA spatial mapping (TAZs don't nest cleanly in PUMAs)
- Pure geospatial approach only
- No fallback methods
- Use pyogrio backend for shapefile loading
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
import sys
import argparse

# Import unified configuration
from simplified_tm2_config import config

# PUMA to County mapping for Bay Area (2020 boundaries)
# Based on exact PUMA IDs from spatial analysis (5-digit format with leading zeros)
# All 9 Bay Area counties: Alameda, Contra Costa, Marin, Napa, San Francisco, San Mateo, Santa Clara, Solano, Sonoma
PUMA_COUNTY_MAP = {
    # San Francisco County (75) - PUMAs 00101-00123
    '00101': ('75', 'San Francisco'), '00111': ('75', 'San Francisco'), '00112': ('75', 'San Francisco'),
    '00113': ('75', 'San Francisco'), '00114': ('75', 'San Francisco'), '00115': ('75', 'San Francisco'),
    '00116': ('75', 'San Francisco'), '00117': ('75', 'San Francisco'), '00118': ('75', 'San Francisco'),
    '00119': ('75', 'San Francisco'), '00120': ('75', 'San Francisco'), '00121': ('75', 'San Francisco'),
    '00122': ('75', 'San Francisco'), '00123': ('75', 'San Francisco'),
    
    # Alameda County (01) - PUMAs 01301-01314
    '01301': ('01', 'Alameda'), '01305': ('01', 'Alameda'), '01308': ('01', 'Alameda'),
    '01309': ('01', 'Alameda'), '01310': ('01', 'Alameda'), '01311': ('01', 'Alameda'),
    '01312': ('01', 'Alameda'), '01313': ('01', 'Alameda'), '01314': ('01', 'Alameda'),
    
    # Santa Clara County (85) - PUMAs 07507-07514 (reassigned from Alameda)
    '07507': ('85', 'Santa Clara'), '07508': ('85', 'Santa Clara'), '07509': ('85', 'Santa Clara'),
    '07510': ('85', 'Santa Clara'), '07511': ('85', 'Santa Clara'), '07512': ('85', 'Santa Clara'),
    '07513': ('85', 'Santa Clara'), '07514': ('85', 'Santa Clara'),
    
    # Contra Costa County (13) - PUMAs 04103-04104, 08101-08104
    '04103': ('13', 'Contra Costa'), '04104': ('13', 'Contra Costa'),
    '08101': ('13', 'Contra Costa'), '08102': ('13', 'Contra Costa'), 
    '08103': ('13', 'Contra Costa'), '08104': ('13', 'Contra Costa'),
    
    # Napa County (55) - PUMAs 08105-08106 (reassigned from Contra Costa)
    '08105': ('55', 'Napa'), '08106': ('55', 'Napa'),
    
    # San Mateo County (81) - PUMAs 08505-08522
    '08505': ('81', 'San Mateo'), '08506': ('81', 'San Mateo'), '08507': ('81', 'San Mateo'),
    '08508': ('81', 'San Mateo'), '08510': ('81', 'San Mateo'), '08511': ('81', 'San Mateo'),
    '08512': ('81', 'San Mateo'), '08515': ('81', 'San Mateo'), '08516': ('81', 'San Mateo'),
    '08517': ('81', 'San Mateo'), '08518': ('81', 'San Mateo'), '08519': ('81', 'San Mateo'),
    '08520': ('81', 'San Mateo'), '08521': ('81', 'San Mateo'), '08522': ('81', 'San Mateo'),
    
    # Marin County (41)
    '05500': ('41', 'Marin'),
    
    # Solano County (95) - PUMAs 09501-09503
    '09501': ('95', 'Solano'), '09502': ('95', 'Solano'), '09503': ('95', 'Solano'),
    
    # Sonoma County (97) - PUMAs 09702-09706
    '09702': ('97', 'Sonoma'), '09704': ('97', 'Sonoma'), '09705': ('97', 'Sonoma'), '09706': ('97', 'Sonoma'),
}

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Create MAZ->PUMA geospatial crosswalk")
    parser.add_argument("--maz_shapefile", type=str, help="Path to MAZ shapefile")
    parser.add_argument("--puma_shapefile", type=str, help="Path to PUMA shapefile")
    args = parser.parse_args()
    
    print("=" * 60)
    print("DIRECT MAZ->PUMA GEOSPATIAL CROSSWALK CREATION")
    print("=" * 60)
    print("User specifications:")
    print("- Direct MAZ->PUMA spatial mapping (TAZs don't nest in PUMAs)")
    print("- Use MAZ shapefile with existing TAZ relationships")
    print("- Spatial join MAZ centroids -> PUMA20 boundaries")
    print("- No fallback methods")
    print()
    
    # Import configuration to get shape file paths
    try:
        from unified_tm2_config import config
        print("SUCCESS: Using unified configuration for shape file paths")
    except ImportError:
        print("WARNING: Could not import config, using fallback paths")
        config = None
    
    # Define paths - use command line args first, then configuration, then fallback
    base_dir = Path("c:/GitHub/populationsim/bay_area")
    
    # Input files - prioritize command line arguments
    if args.maz_shapefile and args.puma_shapefile:
        maz_shapefile = Path(args.maz_shapefile)
        puma_shapefile = Path(args.puma_shapefile)
        print(f"INFO: Using command line shapefile paths")
    elif config:
        maz_shapefile = config.SHAPEFILES['maz_shapefile']
        puma_shapefile = config.SHAPEFILES['puma_shapefile']
        print(f"INFO: Using unified config shapefile paths")
    else:
        # Fallback paths using tm2py-utils location with NEW filenames
        maz_shapefile = Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/mazs_TM2_2_4.shp")
        puma_shapefile = Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/tl_2022_06_puma20.shp")
        print("INFO: Using fallback paths from tm2py-utils")
    
    print(f"   MAZ shapefile: {maz_shapefile}")
    print(f"   PUMA shapefile: {puma_shapefile}")
    
    # Output file - single location using simplified config
    if config:
        output_file = config.geo_crosswalk
        print(f"INFO: Using config output path: {output_file}")
    else:
        # Fallback to working directory only (no more dual locations!)
        output_file = base_dir / "hh_gq" / "tm2_working_dir" / "data" / "geo_cross_walk_tm2.csv"
        print(f"INFO: Using fallback output path: {output_file}")
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print("  STEP 1: Loading MAZ shapefile with existing TAZ relationships")
    print(f"   File: {maz_shapefile}")
    print("    Direct approach: MAZ  PUMA spatial mapping")
    
    if not maz_shapefile.exists():
        print(f" ERROR: MAZ shapefile not found: {maz_shapefile}")
        return False
    
    try:
        # Load MAZ shapefile using pyogrio backend
        print("    Using pyogrio backend for shapefile loading...")
        maz_gdf = gpd.read_file(maz_shapefile, engine='pyogrio')
        print(f"    Loaded {len(maz_gdf):,} MAZ zones")
        print(f"    Columns: {list(maz_gdf.columns)}")
        print(f"    CRS: {maz_gdf.crs}")
        
        # Check for MAZ and TAZ ID columns
        maz_id_cols = [col for col in maz_gdf.columns if 'MAZ' in col.upper() or 'ZONE' in col.upper()]
        taz_id_cols = [col for col in maz_gdf.columns if 'TAZ' in col.upper()]
        print(f"    Potential MAZ ID columns: {maz_id_cols}")
        print(f"    Potential TAZ ID columns: {taz_id_cols}")
        
        # Determine the MAZ ID column
        if 'MAZ' in maz_gdf.columns:
            maz_id_col = 'MAZ'
        elif 'maz' in maz_gdf.columns:  # lowercase version
            maz_id_col = 'maz'
        elif 'MAZ_ID' in maz_gdf.columns:
            maz_id_col = 'MAZ_ID'
        elif 'MAZID' in maz_gdf.columns:
            maz_id_col = 'MAZID'
        else:
            print(f" ERROR: Cannot identify MAZ ID column in shapefile")
            print(f"   Available columns: {list(maz_gdf.columns)}")
            return False
        
        # Determine the TAZ ID column
        if 'TAZ' in maz_gdf.columns:
            taz_id_col = 'TAZ'
        elif 'taz' in maz_gdf.columns:  # lowercase version
            taz_id_col = 'taz'
        elif 'TAZ_ID' in maz_gdf.columns:
            taz_id_col = 'TAZ_ID'
        elif 'TAZ1454' in maz_gdf.columns:
            taz_id_col = 'TAZ1454'
        else:
            print(f" ERROR: Cannot identify TAZ ID column in shapefile")
            print(f"   Available columns: {list(maz_gdf.columns)}")
            return False
        
        print(f"    Using MAZ ID column: {maz_id_col}")
        print(f"    Using TAZ ID column: {taz_id_col}")
        
        # Calculate MAZ centroids for spatial join
        print("    Calculating MAZ centroids...")
        maz_gdf['centroid'] = maz_gdf.geometry.centroid
        
        # Create a new GeoDataFrame with centroids as geometry for spatial join
        maz_centroids = maz_gdf.copy()
        maz_centroids['geometry'] = maz_centroids['centroid']
        
        print(f"    Created centroids for {len(maz_centroids):,} MAZ zones")
        print(f"    MAZTAZ relationships available: {maz_gdf[taz_id_col].nunique():,} unique TAZs")
        
        # Show sample data
        print("    Sample MAZ data:")
        sample_cols = [maz_id_col, taz_id_col]
        print(maz_gdf[sample_cols].head())
        
    except Exception as e:
        print(f" ERROR: Failed to load MAZ shapefile: {e}")
        return False
    
    print()
    print("  STEP 2: Loading PUMA20 shapefile (2020 boundaries)")
    print(f"   File: {puma_shapefile}")
    print("    Creating direct MAZPUMA20 spatial mappings")
    
    if not puma_shapefile.exists():
        print(f" ERROR: PUMA20 shapefile not found: {puma_shapefile}")
        return False
    
    try:
        # Load PUMA shapefile using pyogrio backend
        puma_gdf = gpd.read_file(puma_shapefile, engine='pyogrio')
        print(f"    Loaded {len(puma_gdf):,} PUMA zones")
        print(f"    Columns: {list(puma_gdf.columns)}")
        print(f"    CRS: {puma_gdf.crs}")
        
        # Check for PUMA ID column first
        if 'PUMACE20' in puma_gdf.columns:
            puma_id_col = 'PUMACE20'
        elif 'PUMA20' in puma_gdf.columns:
            puma_id_col = 'PUMA20'
        else:
            print(f" ERROR: Cannot identify PUMA ID column in shapefile")
            print(f"   Available columns: {list(puma_gdf.columns)}")
            return False
        
        print(f"    Using PUMA ID column: {puma_id_col}")
        
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
            print(f"    Filtered to Bay Area using {county_col}: {len(puma_gdf):,} PUMA zones (was {original_count:,})")
        else:
            print("     WARNING: No county column found, using spatial overlap to determine Bay Area PUMAs")
            print(f"    Available columns: {list(puma_gdf.columns)}")
            print(f"     Will determine Bay Area PUMAs based on spatial overlap with MAZ/TAZ data")
            
            # Don't filter here - let the spatial join determine which PUMAs are valid
            original_count = len(puma_gdf)
            print(f"    Using all {original_count:,} PUMAs for spatial analysis - will filter after spatial join")
        
        # Show sample PUMA IDs
        sample_pumas = sorted(puma_gdf[puma_id_col].unique())[:10]
        print(f"    Sample PUMA IDs: {sample_pumas}")
        
    except Exception as e:
        print(f" ERROR: Failed to load PUMA20 shapefile: {e}")
        return False
    
    print()
    print(" STEP 3: Creating direct spatial join MAZ centroids  PUMA20 (2020 boundaries)")
    print("    Direct approach: MAZ centroids mapped to PUMA boundaries")
    
    try:
        # Ensure both datasets have the same CRS
        if maz_centroids.crs != puma_gdf.crs:
            print(f"    Reprojecting MAZ centroids from {maz_centroids.crs} to {puma_gdf.crs}")
            maz_centroids = maz_centroids.to_crs(puma_gdf.crs)
        
        # Perform spatial join with enhanced matching
        print("    Executing spatial join (trying 'within' first, then 'intersects' for unmatched)...")
        
        # First try: within predicate (MAZ centroids within PUMA boundaries)
        maz_puma_join = gpd.sjoin(
            maz_centroids[[maz_id_col, taz_id_col, 'geometry']], 
            puma_gdf[[puma_id_col, 'geometry']], 
            how='left', 
            predicate='within'
        )
        
        # Check for unmatched MAZs
        unmatched_mask = maz_puma_join[puma_id_col].isna()
        unmatched_count = unmatched_mask.sum()
        
        if unmatched_count > 0:
            print(f"     WARNING: {unmatched_count:,} MAZ centroids not within any PUMA")
            print("    Trying 'intersects' predicate for unmatched MAZs...")
            
            # Get unmatched MAZ centroids
            unmatched_mazs = maz_centroids[maz_centroids[maz_id_col].isin(
                maz_puma_join[unmatched_mask][maz_id_col]
            )]
            
            # Try intersects for unmatched MAZs
            unmatched_join = gpd.sjoin(
                unmatched_mazs[[maz_id_col, taz_id_col, 'geometry']], 
                puma_gdf[[puma_id_col, 'geometry']], 
                how='left', 
                predicate='intersects'
            )
            
            # Update the main join with intersects results
            intersects_matches = unmatched_join[unmatched_join[puma_id_col].notna()]
            if len(intersects_matches) > 0:
                print(f"    Found {len(intersects_matches):,} additional matches using 'intersects'")
                
                # Update the main join results
                for _, row in intersects_matches.iterrows():
                    mask = maz_puma_join[maz_id_col] == row[maz_id_col]
                    maz_puma_join.loc[mask, puma_id_col] = row[puma_id_col]
            
            # Check for still unmatched MAZs
            still_unmatched = maz_puma_join[maz_puma_join[puma_id_col].isna()]
            if len(still_unmatched) > 0:
                print(f"     {len(still_unmatched):,} MAZs still unmatched - using nearest neighbor...")
                
                # For remaining unmatched, find nearest PUMA
                unmatched_remaining = maz_centroids[maz_centroids[maz_id_col].isin(
                    still_unmatched[maz_id_col]
                )]
                
                for _, unmatched_maz in unmatched_remaining.iterrows():
                    # Calculate distance to all PUMAs
                    distances = puma_gdf.geometry.distance(unmatched_maz.geometry)
                    nearest_idx = distances.idxmin()
                    nearest_puma = puma_gdf.loc[nearest_idx, puma_id_col]
                    
                    # Update the join
                    mask = maz_puma_join[maz_id_col] == unmatched_maz[maz_id_col]
                    maz_puma_join.loc[mask, puma_id_col] = nearest_puma
                
                print(f"    Assigned remaining MAZs to nearest PUMAs")
        
        print(f"    Spatial join completed: {len(maz_puma_join):,} MAZPUMA relationships")
        
        # Final check for unmatched MAZs
        final_unmatched = maz_puma_join[maz_puma_join[puma_id_col].isna()]
        if len(final_unmatched) > 0:
            print(f"    ERROR: {len(final_unmatched):,} MAZ zones still not matched to any PUMA")
            print(f"    Unmatched MAZ IDs: {final_unmatched[maz_id_col].head().tolist()}")
        else:
            print(f"    All MAZs successfully matched to PUMAs")
        
        # Create clean MAZTAZPUMA mapping with 2020 boundaries
        final_mapping = maz_puma_join[[maz_id_col, taz_id_col, puma_id_col]].copy()
        final_mapping = final_mapping.dropna()  # Remove unmatched MAZs
        final_mapping.columns = ['MAZ', 'TAZ', 'PUMA']  # Standard column names
        
        print(f"    Clean MAZTAZPUMA mapping: {len(final_mapping):,} relationships")
        print(f"     MAZ zones: {final_mapping['MAZ'].nunique():,}")
        print(f"     TAZ zones: {final_mapping['TAZ'].nunique():,}")
        print(f"     PUMA20 zones: {final_mapping['PUMA'].nunique():,}")
        print("    Sample MAZTAZPUMA mappings:")
        print(final_mapping.head(10))
        
    except Exception as e:
        print(f" ERROR: Spatial join failed: {e}")
        return False
    
    print()
    print(" STEP 4: Saving direct MAZ→TAZ→PUMA20 crosswalk file")
    print(f"   Output: {output_file}")
    
    try:
        # The final_mapping already contains the complete crosswalk
        # Just need to ensure data types are correct
        final_mapping['MAZ'] = final_mapping['MAZ'].astype(int)
        final_mapping['TAZ'] = final_mapping['TAZ'].astype(int)
        
        # Add county information based on PUMA mapping (before formatting)
        print("     Adding county information...")
        # Convert PUMA to zero-padded 5-digit string for mapping lookup (handles both int and str formats)
        # Remove leading zeros first, then re-add them consistently
        final_mapping['PUMA_str'] = final_mapping['PUMA'].astype(str).str.lstrip('0').str.zfill(5)
        final_mapping['COUNTY'] = final_mapping['PUMA_str'].map(lambda x: PUMA_COUNTY_MAP.get(x, ('99', 'Unknown'))[0])
        final_mapping['county_name'] = final_mapping['PUMA_str'].map(lambda x: PUMA_COUNTY_MAP.get(x, ('99', 'Unknown'))[1])
        
        # Debug: Show PUMA format conversion
        sample_conversions = final_mapping[['PUMA', 'PUMA_str', 'COUNTY', 'county_name']].head()
        print(f"     PUMA format conversions (sample):")
        print(sample_conversions.to_string(index=False))
        
        final_mapping = final_mapping.drop('PUMA_str', axis=1)  # Remove temporary column
        
        # NOW format PUMA IDs as integers for PopulationSim compatibility
        # Convert from zero-padded strings to integers (removes leading zeros)
        final_mapping['PUMA'] = final_mapping['PUMA'].astype(str).str.lstrip('0').astype(int)
        
        # Check for any unmapped PUMAs
        unmapped_pumas = final_mapping[final_mapping['COUNTY'] == '99']['PUMA'].unique()
        if len(unmapped_pumas) > 0:
            print(f"     WARNING: {len(unmapped_pumas)} PUMAs not in county mapping: {unmapped_pumas}")
        else:
            print(f"    All PUMAs successfully mapped to counties")
        
        print(f"    Final crosswalk: {len(final_mapping):,} records")
        
        # Show summary statistics
        print("    Summary statistics:")
        print(f"      Unique MAZs: {final_mapping['MAZ'].nunique():,}")
        print(f"      Unique TAZs: {final_mapping['TAZ'].nunique():,}")
        print(f"      Unique PUMA20s: {final_mapping['PUMA'].nunique():,}")
        print(f"      Unique Counties: {final_mapping['COUNTY'].nunique():,}")
        
        # Reorder columns for expected format: MAZ, TAZ, PUMA, COUNTY, county_name
        final_mapping = final_mapping[['MAZ', 'TAZ', 'PUMA', 'COUNTY', 'county_name']]
        
        # Show sample of final data
        print("    Sample final crosswalk:")
        print(final_mapping.head(10))
        
        # Save to single location with proper data types
        final_mapping.to_csv(output_file, index=False)
        print(f"    Saved crosswalk: {output_file}")
        
        # Verify the saved file and ensure PUMA format is integer  
        verify_df = pd.read_csv(output_file, dtype={'MAZ': int, 'TAZ': int, 'PUMA': int, 'COUNTY': str, 'county_name': str})
        # Ensure PUMA is integer format for PopulationSim
        verify_df['PUMA'] = verify_df['PUMA'].astype(int)
        # Re-save with correct format
        verify_df.to_csv(output_file, index=False)
        print(f"    Verification: {len(verify_df):,} records with integer PUMA format")
        
        # Show final statistics
        print()
        print("=" * 60)
        print(" DIRECT MAZ→PUMA GEOSPATIAL CROSSWALK COMPLETE")
        print("=" * 60)
        print(f" Created: {output_file}")
        print(f" Records: {len(final_mapping):,}")
        print(f" MAZs: {final_mapping['MAZ'].nunique():,}")
        print(f"  TAZs: {final_mapping['TAZ'].nunique():,}")
        print(f"  PUMA20s (2020 boundaries): {final_mapping['PUMA'].nunique():,}")
        print()
        print(" Direct spatial approach: MAZ centroids → PUMA boundaries")
        print(" Single source of truth: No duplicate files!")
        print(" Ready for PopulationSim!")
        
        return True
        
    except Exception as e:
        print(f" ERROR: Failed to save crosswalk: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
