#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

TO DO: Move to tm2py_utils instead.

Single script to create area-based MAZ-TAZ-PUMA-COUNTY crosswalk for PopulationSim TM2

This is the ONE AND ONLY crosswalk script for the TM2 pipeline.
- Uses area-based TAZ-PUMA assignment (most accurate)
- Uses spatial join for MAZ-to-County assignment via centroid
- Outputs directly to consolidated output_2023 directory
- Uses 1-9 county system from unified config
- No copying, no duplication, no confusion

DATA SOURCES:
- MAZ/TAZ Shapefiles: TM2py-utils repository
- PUMA Shapefiles: US Census TIGER/Line files
- County Shapefiles: California Counties from California Open Data Portal
  Source: https://gis.data.ca.gov/datasets/CDEGIS::california-counties-3/explore
  Downloaded and placed in: C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/
"""


import argparse
import geopandas as gpd
import numpy as np
import pandas as pd
import sys
from pathlib import Path
from unified_tm2_config import config

def create_tm2_crosswalk(maz_shapefile, puma_shapefile, output_file, verbose=True):
    """
    Create definitive TM2 crosswalk with area-based PUMA assignment
    """
    
    if verbose:
        print("=" * 60)
        print("TM2 DEFINITIVE CROSSWALK CREATION")
        print("=" * 60)
        print("Area-based TAZ-PUMA assignment for maximum accuracy")
    
    # Load MAZ shapefile (contains TAZ relationships)
    if verbose:
        print(f"\nStep 1: Loading MAZ shapefile...")
        print(f"  File: {maz_shapefile}")
    
    if not maz_shapefile.exists():
        print(f"ERROR: MAZ shapefile not found: {maz_shapefile}")
        return False
        
    try:
        maz_gdf = gpd.read_file(maz_shapefile, engine='pyogrio')
        if verbose:
            print(f"  Loaded {len(maz_gdf):,} MAZ zones")
            print(f"  CRS: {maz_gdf.crs}")
        
        # Identify MAZ and TAZ columns
        maz_col = None
        taz_col = None
        county_col = None
        
        for col in maz_gdf.columns:
            if col.upper() in ['MAZ', 'MAZ_ID', 'MAZ_ID_']:
                maz_col = col
            elif col.upper() in ['TAZ', 'TAZ_ID', 'TAZ1454']:
                taz_col = col
            elif col.upper() in ['COUNTY', 'CO_FIPS', 'COUNTY_FIPS']:
                county_col = col
                
        if not maz_col or not taz_col:
            print(f"ERROR: Could not identify MAZ and TAZ columns in {list(maz_gdf.columns)}")
            return False
            
        if verbose:
            print(f"  MAZ column: {maz_col}")
            print(f"  TAZ column: {taz_col}")
            print(f"  County column: {county_col}")
        
    except Exception as e:
        print(f"ERROR loading MAZ shapefile: {e}")
        return False
    
    # Load PUMA shapefile
    if verbose:
        print(f"\nStep 2: Loading PUMA shapefile...")
        print(f"  File: {puma_shapefile}")
    
    if not puma_shapefile.exists():
        print(f"ERROR: PUMA shapefile not found: {puma_shapefile}")
        return False
        
    try:
        puma_gdf = gpd.read_file(puma_shapefile, engine='pyogrio')
        if verbose:
            print(f"  Loaded {len(puma_gdf):,} PUMA zones")
            print(f"  CRS: {puma_gdf.crs}")
        
        # Identify PUMA column
        puma_col = None
        for col in puma_gdf.columns:
            if col.upper() in ['PUMA', 'PUMACE20', 'PUMA20']:
                puma_col = col
                break
                
        if not puma_col:
            print(f"ERROR: Could not identify PUMA column in {list(puma_gdf.columns)}")
            return False
            
        if verbose:
            print(f"  PUMA column: {puma_col}")
        
        # Filter to Bay Area counties if possible
        bay_area_counties = ['001', '013', '041', '055', '075', '081', '085', '095', '097']
        puma_county_col = None
        for col in puma_gdf.columns:
            if col.upper() in ['COUNTY', 'COUNTYFP20', 'COUNTYFP']:
                puma_county_col = col
                break
                
        if puma_county_col:
            original_count = len(puma_gdf)
            puma_gdf = puma_gdf[puma_gdf[puma_county_col].isin(bay_area_counties)]
            if verbose:
                print(f"  Filtered to Bay Area: {len(puma_gdf):,} PUMAs (was {original_count:,})")
        
        # Reproject to match MAZ CRS if needed
        if puma_gdf.crs != maz_gdf.crs:
            if verbose:
                print(f"  Reprojecting PUMA from {puma_gdf.crs} to {maz_gdf.crs}")
            puma_gdf = puma_gdf.to_crs(maz_gdf.crs)
            
    except Exception as e:
        print(f"ERROR loading PUMA shapefile: {e}")
        return False
    
    # Load County shapefile for spatial county assignment
    if verbose:
        print(f"\nStep 2.5: Loading County shapefile...")
        print(f"  File: {config.SHAPEFILES['county_shapefile']}")
    
    county_shapefile = config.SHAPEFILES['county_shapefile']
    if not county_shapefile.exists():
        print(f"ERROR: County shapefile not found: {county_shapefile}")
        return False
        
    try:
        county_gdf = gpd.read_file(county_shapefile, engine='pyogrio')
        if verbose:
            print(f"  Loaded {len(county_gdf):,} counties")
            print(f"  CRS: {county_gdf.crs}")
        
        # Identify county name and FIPS columns
        county_name_col = None
        county_fips_col = None
        
        for col in county_gdf.columns:
            if col.upper() in ['NAME', 'COUNTY_NAME', 'COUNTYNAME']:
                county_name_col = col
            elif col.upper() in ['FIPS', 'COUNTYFP', 'FIPSCODE', 'CNTY_FIPS', 'COUNTY_FIP']:
                county_fips_col = col
                
        if not county_name_col or not county_fips_col:
            print(f"ERROR: Could not identify county name and FIPS columns in {list(county_gdf.columns)}")
            return False
            
        if verbose:
            print(f"  County name column: {county_name_col}")
            print(f"  County FIPS column: {county_fips_col}")
        
        # Filter to Bay Area counties using FIPS codes
        bay_area_county_fips = ['001', '013', '041', '055', '075', '081', '085', '095', '097']
        
        # Handle both string and integer FIPS codes
        county_gdf['FIPS_STR'] = county_gdf[county_fips_col].astype(str).str.zfill(3)
        county_gdf_filtered = county_gdf[county_gdf['FIPS_STR'].isin(bay_area_county_fips)]
        
        if verbose:
            print(f"  Filtered to Bay Area: {len(county_gdf_filtered):,} counties (was {len(county_gdf):,})")
            print(f"  Bay Area counties: {sorted(county_gdf_filtered[county_name_col].tolist())}")
        
        # Reproject to match MAZ CRS if needed
        if county_gdf_filtered.crs != maz_gdf.crs:
            if verbose:
                print(f"  Reprojecting County from {county_gdf_filtered.crs} to {maz_gdf.crs}")
            county_gdf_filtered = county_gdf_filtered.to_crs(maz_gdf.crs)
            
    except Exception as e:
        print(f"ERROR loading County shapefile: {e}")
        return False
    
    # Create TAZ summary for area-based assignment
    if verbose:
        print(f"\nStep 3: Area-based TAZ-PUMA assignment...")
    
    taz_groups = maz_gdf.groupby(taz_col)
    taz_assignments = {}
    no_intersection_count = 0
    single_intersection_count = 0
    multi_intersection_count = 0
    
    for taz_id, taz_group in taz_groups:
        # Create TAZ polygon by unioning all MAZs in the TAZ
        taz_geom = taz_group.geometry.unary_union
        
        # Find intersecting PUMAs
        intersecting_pumas = []
        for idx, puma_row in puma_gdf.iterrows():
            puma_geom = puma_row.geometry
            if taz_geom.intersects(puma_geom):
                intersecting_pumas.append((idx, puma_row[puma_col], puma_geom))
        
        if len(intersecting_pumas) == 0:
            # No intersection - assign to nearest PUMA
            distances = [(idx, taz_geom.distance(puma_row.geometry), puma_row[puma_col]) 
                        for idx, puma_row in puma_gdf.iterrows()]
            nearest_idx, _, nearest_puma = min(distances, key=lambda x: x[1])
            taz_assignments[taz_id] = nearest_puma
            no_intersection_count += 1
            
        elif len(intersecting_pumas) == 1:
            # Single intersection - easy assignment
            _, puma_id, _ = intersecting_pumas[0]
            taz_assignments[taz_id] = puma_id
            single_intersection_count += 1
            
        else:
            # Multiple intersections - use area-based assignment
            max_area = 0
            best_puma = None
            
            for _, puma_id, puma_geom in intersecting_pumas:
                try:
                    intersection = taz_geom.intersection(puma_geom)
                    area = intersection.area
                    if area > max_area:
                        max_area = area
                        best_puma = puma_id
                except Exception:
                    continue
                    
            taz_assignments[taz_id] = best_puma if best_puma else intersecting_pumas[0][1]
            multi_intersection_count += 1
    
    if verbose:
        print(f"  TAZ assignment summary:")
        print(f"    No intersection (nearest): {no_intersection_count:,}")
        print(f"    Single intersection: {single_intersection_count:,}")
        print(f"    Multiple intersection (area-based): {multi_intersection_count:,}")
        print(f"    Total TAZs: {len(taz_assignments):,}")
    
    # Create final crosswalk
    if verbose:
        print(f"\nStep 4: Creating final crosswalk...")
    
    # Add PUMA assignments to MAZ data
    maz_gdf['PUMA'] = maz_gdf[taz_col].map(taz_assignments)
    
    # Create base crosswalk DataFrame
    crosswalk_df = maz_gdf[[maz_col, taz_col, 'PUMA']].copy()
    crosswalk_df.columns = ['MAZ', 'TAZ', 'PUMA']
    
    # Add spatial county assignment using MAZ centroids
    if verbose:
        print(f"\nStep 4.5: Spatial county assignment using MAZ centroids...")
    
    try:
        # Ensure both datasets are in the same CRS (use projected CRS for accuracy)
        target_crs = 'EPSG:3857'  # Web Mercator for better spatial operations
        
        if verbose:
            print(f"  Converting to {target_crs} for spatial operations...")
        
        # Reproject MAZ data to target CRS
        maz_projected = maz_gdf.to_crs(target_crs)
        maz_centroids = maz_projected.copy()
        maz_centroids['geometry'] = maz_centroids.geometry.centroid
        
        # Reproject county data to target CRS
        county_projected = county_gdf_filtered.to_crs(target_crs)
        
        if verbose:
            print(f"  Performing spatial join with 'intersects' predicate...")
        
        # First try: spatial join with 'intersects' (more permissive than 'within')
        maz_with_counties = gpd.sjoin(
            maz_centroids[[maz_col, 'geometry']], 
            county_projected[[county_name_col, county_fips_col, 'FIPS_STR', 'geometry']], 
            how='left', 
            predicate='intersects'
        )
        
        # Check coverage and try fallback if needed
        initial_coverage = maz_with_counties['FIPS_STR'].notna().sum()
        if verbose:
            print(f"  Initial spatial join coverage: {initial_coverage:,}/{len(maz_with_counties):,} ({initial_coverage/len(maz_with_counties)*100:.1f}%)")
        
        # If coverage is not 100%, try nearest neighbor assignment for missing ones
        if initial_coverage < len(maz_with_counties):
            if verbose:
                print(f"  Using nearest neighbor for {len(maz_with_counties) - initial_coverage:,} unassigned MAZ zones...")
            
            missing_mask = maz_with_counties['FIPS_STR'].isna()
            missing_indices = maz_with_counties[missing_mask].index
            
            # For each missing centroid, find nearest county using sjoin_nearest
            missing_centroids = maz_centroids.loc[missing_indices, [maz_col, 'geometry']].copy()
            
            # Use sjoin_nearest to find closest counties
            nearest_assignments = gpd.sjoin_nearest(
                missing_centroids, 
                county_projected[[county_name_col, county_fips_col, 'FIPS_STR', 'geometry']],
                how='left'
            )
            
            # Update the main assignments with nearest neighbor results
            for _, nearest_row in nearest_assignments.iterrows():
                maz_id = nearest_row[maz_col]
                # Find the corresponding row in maz_with_counties
                update_mask = maz_with_counties[maz_col] == maz_id
                maz_with_counties.loc[update_mask, 'FIPS_STR'] = nearest_row['FIPS_STR']
                maz_with_counties.loc[update_mask, county_name_col] = nearest_row[county_name_col]
                maz_with_counties.loc[update_mask, county_fips_col] = nearest_row[county_fips_col]
        
        if verbose:
            print(f"  Spatial join completed for {len(maz_with_counties):,} MAZ zones")
            final_coverage = maz_with_counties['FIPS_STR'].notna().sum()
            print(f"  Final coverage: {final_coverage:,}/{len(maz_with_counties):,} ({final_coverage/len(maz_with_counties)*100:.1f}%)")
            
        # Create mapping from MAZ to county FIPS
        maz_to_fips = dict(zip(maz_with_counties[maz_col], maz_with_counties['FIPS_STR']))
        
        # Convert FIPS codes to sequential county IDs (1-9) using unified config
        fips_to_sequential = config.get_fips_to_sequential_mapping()
        
        # Add county information to crosswalk
        crosswalk_df['COUNTY_FIPS_STR'] = crosswalk_df['MAZ'].map(maz_to_fips)
        crosswalk_df['COUNTY_FIPS_INT'] = crosswalk_df['COUNTY_FIPS_STR'].astype('Int64', errors='ignore')
        crosswalk_df['COUNTY'] = crosswalk_df['COUNTY_FIPS_INT'].map(fips_to_sequential)
        
        # Count successful assignments
        successful_assignments = crosswalk_df['COUNTY'].notna().sum()
        if verbose:
            print(f"  Successfully assigned counties to {successful_assignments:,} of {len(crosswalk_df):,} MAZ zones")
            assignment_rate = (successful_assignments / len(crosswalk_df)) * 100
            print(f"  Success rate: {assignment_rate:.1f}%")
            
            # Show county distribution
            county_counts = crosswalk_df['COUNTY'].value_counts().sort_index()
            print(f"  County distribution:")
            for county_id, count in county_counts.items():
                if pd.notna(county_id):
                    county_info = config.BAY_AREA_COUNTIES.get(int(county_id), {})
                    county_name = county_info.get('name', 'Unknown')
                    print(f"    {int(county_id)}: {county_name} - {count:,} MAZ zones")
            
            missing_count = crosswalk_df['COUNTY'].isna().sum()
            if missing_count > 0:
                print(f"  WARNING: {missing_count:,} MAZ zones could not be assigned to counties")
                print(f"  These may be in water areas or outside Bay Area county boundaries")
            else:
                print(f"  SUCCESS: 100% of MAZ zones assigned to counties!")
        
        # Clean up temporary columns
        crosswalk_df = crosswalk_df.drop(['COUNTY_FIPS_STR', 'COUNTY_FIPS_INT'], axis=1, errors='ignore')
        
    except Exception as e:
        print(f"ERROR in spatial county assignment: {e}")
        print(f"Setting all counties to None - manual investigation needed")
        crosswalk_df['COUNTY'] = None
    
    # ============================================================
    # STEP 6: RESOLVE MULTI-COUNTY PUMAS
    # ============================================================
    # Use configurable logic to resolve PUMAs that span multiple counties
    # This ensures PopulationSim's geography hierarchy assumptions are met
    crosswalk_df = config.resolve_multi_county_pumas(crosswalk_df, verbose=verbose)
    
    # Add county names and FIPS codes using unified config
    if verbose:
        print(f"\nStep 7: Adding county names and FIPS codes from unified config...")
    
    # Create county name mapping from unified config (1-9 system)
    county_name_map = {}
    countyfp10_map = {}
    
    for seq_id, county_info in config.BAY_AREA_COUNTIES.items():
        county_name_map[seq_id] = county_info['name']
        countyfp10_map[seq_id] = county_info['fips_int']
    
    if verbose:
        print(f"  County mapping from unified config:")
        for seq_id in sorted(config.BAY_AREA_COUNTIES.keys()):
            county_info = config.BAY_AREA_COUNTIES[seq_id]
            print(f"    {seq_id}: {county_info['name']} (FIPS {county_info['fips_int']})")
    
    # Apply county names and FIPS codes
    crosswalk_df['county_name'] = crosswalk_df['COUNTY'].map(county_name_map).fillna('Unknown')
    crosswalk_df['COUNTYFP10'] = crosswalk_df['COUNTY'].map(countyfp10_map)
    
    # Final summary
    if verbose:
        print(f"\nStep 8: Saving crosswalk...")
        unique_tazs = crosswalk_df['TAZ'].nunique()
        unique_pumas = crosswalk_df['PUMA'].nunique()
        assigned_counties = crosswalk_df['COUNTY'].nunique()
        
        print(f"  Final crosswalk: {len(crosswalk_df):,} MAZ zones")
        print(f"  Unique TAZs: {unique_tazs:,}")
        print(f"  Unique PUMAs: {unique_pumas}")
        print(f"  Counties: {assigned_counties}")
    
    # Save the crosswalk
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        crosswalk_df.to_csv(output_file, index=False)
        
        if verbose:
            file_size = output_file.stat().st_size
            print(f"  Output: {output_file}")
            print(f"  SAVED: {len(crosswalk_df):,} records")
            print(f"  File size: {file_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"ERROR saving crosswalk: {e}")
        return False

def main():
    """Main execution function"""
    
    # Use paths from unified config
    maz_shapefile = config.SHAPEFILES['maz_shapefile']
    puma_shapefile = config.SHAPEFILES['puma_shapefile']
    output_file = config.CROSSWALK_FILES['popsim_crosswalk']  # Output directly to final name
    
    # Always print header information
    print(f"MAZ shapefile: {maz_shapefile}")
    print(f"PUMA shapefile: {puma_shapefile}")
    print(f"County shapefile: {config.SHAPEFILES['county_shapefile']}")
    print(f"Output file: {output_file}")
    
    # Create the crosswalk
    success = create_tm2_crosswalk(maz_shapefile, puma_shapefile, output_file, verbose=True)
    
    if success:
        print("=" * 60)
        print("TM2 CROSSWALK CREATION COMPLETE")
        print("=" * 60)
        print(f"SUCCESS: Area-based crosswalk: {output_file}")
        print("Each TAZ assigned to PUMA with largest area overlap")
        print("Counties assigned via spatial join using MAZ centroids")
        print("Ready for next pipeline step")
        return 0
    else:
        print("FAILED: Crosswalk creation failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
