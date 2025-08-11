#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced TAZ-PUMA crosswalk creation with area-based assignment

This script creates a geographically correct crosswalk by:
1. Loading TAZ polygons and PUMA polygons
2. For each TAZ that intersects multiple PUMAs, calculating intersection areas
3. Assigning each TAZ to the PUMA where it has the largest area overlap
4. Creating a clean TAZ-PUMA mapping without duplicates
5. Inheriting MAZ assignments from their parent TAZ assignments
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
import sys
import argparse

def create_area_based_crosswalk(maz_shapefile, puma_shapefile, output_file):
    """
    Create crosswalk with area-based TAZ-PUMA assignment
    """
    
    print("=== AREA-BASED TAZ-PUMA CROSSWALK CREATION ===")
    
    # Load MAZ shapefile (contains TAZ relationships)
    print(f"\nStep 1: Loading MAZ shapefile...")
    print(f"  File: {maz_shapefile}")
    
    if not maz_shapefile.exists():
        print(f"ERROR: MAZ shapefile not found: {maz_shapefile}")
        return False
        
    try:
        maz_gdf = gpd.read_file(maz_shapefile, engine='pyogrio')
        print(f"  Loaded {len(maz_gdf):,} MAZ zones")
        print(f"  Columns: {list(maz_gdf.columns)}")
        print(f"  CRS: {maz_gdf.crs}")
        
        # Identify MAZ and TAZ columns
        maz_col = None
        taz_col = None
        
        for col in maz_gdf.columns:
            if 'MAZ' in col.upper() and 'TAZ' not in col.upper():
                maz_col = col
            elif 'TAZ' in col.upper():
                taz_col = col
                
        if not maz_col or not taz_col:
            print(f"ERROR: Cannot find MAZ and TAZ columns in shapefile")
            print(f"  Available columns: {list(maz_gdf.columns)}")
            return False
            
        print(f"  Using MAZ column: {maz_col}")
        print(f"  Using TAZ column: {taz_col}")
        
        # Get unique TAZs and their geometries
        print(f"  Creating TAZ polygons from MAZ data...")
        taz_geometries = maz_gdf.groupby(taz_col)['geometry'].apply(
            lambda x: x.unary_union
        ).reset_index()
        taz_gdf = gpd.GeoDataFrame(taz_geometries, crs=maz_gdf.crs)
        print(f"  Created {len(taz_gdf):,} TAZ polygons")
        
    except Exception as e:
        print(f"ERROR: Failed to load MAZ shapefile: {e}")
        return False
    
    # Load PUMA shapefile
    print(f"\nStep 2: Loading PUMA shapefile...")
    print(f"  File: {puma_shapefile}")
    
    if not puma_shapefile.exists():
        print(f"ERROR: PUMA shapefile not found: {puma_shapefile}")
        return False
        
    try:
        puma_gdf = gpd.read_file(puma_shapefile, engine='pyogrio')
        print(f"  Loaded {len(puma_gdf):,} PUMA zones")
        print(f"  CRS: {puma_gdf.crs}")
        
        # Find PUMA ID column
        puma_col = None
        for col in ['PUMACE20', 'PUMA20', 'PUMACE10', 'PUMA10']:
            if col in puma_gdf.columns:
                puma_col = col
                break
                
        if not puma_col:
            print(f"ERROR: Cannot find PUMA ID column")
            print(f"  Available columns: {list(puma_gdf.columns)}")
            return False
            
        print(f"  Using PUMA column: {puma_col}")
        
        # Filter to Bay Area counties if possible
        bay_area_counties = ['001', '013', '041', '055', '075', '081', '085', '097']
        county_col = None
        for col in ['COUNTYFP20', 'COUNTYFP10', 'COUNTYFP', 'COUNTY']:
            if col in puma_gdf.columns:
                county_col = col
                break
                
        if county_col:
            original_count = len(puma_gdf)
            puma_gdf = puma_gdf[puma_gdf[county_col].isin(bay_area_counties)]
            print(f"  Filtered to Bay Area: {len(puma_gdf):,} PUMAs (was {original_count:,})")
        else:
            print(f"  WARNING: No county filter applied")
            
    except Exception as e:
        print(f"ERROR: Failed to load PUMA shapefile: {e}")
        return False
    
    # Ensure same CRS
    if taz_gdf.crs != puma_gdf.crs:
        print(f"  Reprojecting PUMA to match TAZ CRS...")
        puma_gdf = puma_gdf.to_crs(taz_gdf.crs)
    
    # Perform area-based assignment
    print(f"\nStep 3: Area-based TAZ-PUMA assignment...")
    
    taz_puma_assignments = []
    
    for idx, taz_row in taz_gdf.iterrows():
        taz_id = taz_row[taz_col]
        taz_geom = taz_row['geometry']
        
        if idx % 500 == 0:
            print(f"  Processing TAZ {idx+1:,} of {len(taz_gdf):,}...")
        
        # Find intersecting PUMAs
        intersecting_pumas = puma_gdf[puma_gdf.intersects(taz_geom)]
        
        if len(intersecting_pumas) == 0:
            # No intersection - find nearest PUMA
            distances = puma_gdf.distance(taz_geom)
            nearest_idx = distances.idxmin()
            assigned_puma = puma_gdf.loc[nearest_idx, puma_col]
            assignment_method = 'nearest'
            
        elif len(intersecting_pumas) == 1:
            # Single intersection - easy assignment
            assigned_puma = intersecting_pumas.iloc[0][puma_col]
            assignment_method = 'single'
            
        else:
            # Multiple intersections - use area-based assignment
            max_area = 0
            assigned_puma = None
            
            for _, puma_row in intersecting_pumas.iterrows():
                puma_geom = puma_row['geometry']
                
                try:
                    intersection = taz_geom.intersection(puma_geom)
                    if intersection.is_empty:
                        area = 0
                    else:
                        area = intersection.area
                        
                    if area > max_area:
                        max_area = area
                        assigned_puma = puma_row[puma_col]
                        
                except Exception as e:
                    print(f"    Warning: Error calculating intersection for TAZ {taz_id}: {e}")
                    continue
            
            assignment_method = 'area_based'
            
        taz_puma_assignments.append({
            'TAZ': taz_id,
            'PUMA': assigned_puma,
            'method': assignment_method
        })
    
    # Create TAZ-PUMA mapping dataframe
    taz_puma_df = pd.DataFrame(taz_puma_assignments)
    
    print(f"  TAZ-PUMA assignments completed:")
    method_counts = taz_puma_df['method'].value_counts()
    for method, count in method_counts.items():
        print(f"    {method}: {count:,} TAZs")
    
    # Check for any unassigned TAZs
    unassigned = taz_puma_df[taz_puma_df['PUMA'].isna()]
    if len(unassigned) > 0:
        print(f"  WARNING: {len(unassigned)} TAZs could not be assigned to any PUMA")
        return False
    
    # Now create MAZ-level crosswalk by inheriting TAZ assignments
    print(f"\nStep 4: Creating MAZ-level crosswalk...")
    
    # Merge MAZ data with TAZ-PUMA assignments
    maz_crosswalk = maz_gdf[[maz_col, taz_col]].merge(
        taz_puma_df[['TAZ', 'PUMA']], 
        left_on=taz_col, 
        right_on='TAZ', 
        how='left'
    )
    
    # Clean up column names
    maz_crosswalk = maz_crosswalk[[maz_col, taz_col, 'PUMA']].copy()
    maz_crosswalk.columns = ['MAZ', 'TAZ', 'PUMA']
    
    # Add county information (simplified mapping for Bay Area)
    print(f"  Adding county information...")
    
    # PUMA to County mapping for Bay Area
    puma_county_map = {
        # Add your PUMA-County mappings here
        # For now, derive from PUMA ranges (this is simplified)
    }
    
    # Simplified county assignment based on PUMA ID patterns
    def assign_county(puma_id):
        puma_str = str(puma_id).zfill(5)
        if puma_str.startswith('001'):
            return ('75', 'San Francisco')
        elif puma_str.startswith('013'):
            return ('01', 'Alameda') 
        elif puma_str.startswith('041'):
            return ('13', 'Contra Costa')
        elif puma_str.startswith('075'):
            return ('85', 'Santa Clara')
        else:
            # Try to derive from actual PUMA values in your data
            if int(puma_id) >= 7507 and int(puma_id) <= 7514:
                return ('85', 'Santa Clara')
            elif int(puma_id) >= 1301 and int(puma_id) <= 1314:
                return ('01', 'Alameda')
            else:
                return ('99', 'Unknown')
    
    county_info = maz_crosswalk['PUMA'].apply(assign_county)
    maz_crosswalk['COUNTY'] = [x[0] for x in county_info]
    maz_crosswalk['county_name'] = [x[1] for x in county_info]
    
    print(f"  Final crosswalk: {len(maz_crosswalk):,} MAZ records")
    print(f"    Unique TAZs: {maz_crosswalk['TAZ'].nunique():,}")
    print(f"    Unique PUMAs: {maz_crosswalk['PUMA'].nunique():,}")
    
    # Verify no TAZ has multiple PUMA assignments
    taz_puma_check = maz_crosswalk.groupby('TAZ')['PUMA'].nunique()
    multi_puma_tazs = taz_puma_check[taz_puma_check > 1]
    
    if len(multi_puma_tazs) > 0:
        print(f"  ERROR: {len(multi_puma_tazs)} TAZs still have multiple PUMA assignments!")
        return False
    else:
        print(f"  SUCCESS: All TAZs have unique PUMA assignments")
    
    # Save the crosswalk
    print(f"\nStep 5: Saving crosswalk...")
    print(f"  Output: {output_file}")
    
    try:
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save with proper data types
        maz_crosswalk.to_csv(output_file, index=False)
        print(f"  Saved successfully: {len(maz_crosswalk):,} records")
        
        # Show sample
        print(f"  Sample data:")
        print(maz_crosswalk.head(10).to_string(index=False))
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to save crosswalk: {e}")
        return False

def main():
    """Main function"""
    
    parser = argparse.ArgumentParser(description='Create area-based TAZ-PUMA crosswalk')
    parser.add_argument('--maz-shapefile', type=str, 
                       help='Path to MAZ shapefile')
    parser.add_argument('--puma-shapefile', type=str,
                       help='Path to PUMA shapefile') 
    parser.add_argument('--output', type=str,
                       help='Output crosswalk file path')
    
    args = parser.parse_args()
    
    # Default paths if not provided
    if not args.maz_shapefile:
        maz_shapefile = Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/mazs_TM2_2_4.shp")
    else:
        maz_shapefile = Path(args.maz_shapefile)
        
    if not args.puma_shapefile:
        puma_shapefile = Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/tl_2022_06_puma20.shp")
    else:
        puma_shapefile = Path(args.puma_shapefile)
        
    if not args.output:
        output_file = Path("hh_gq/tm2_working_dir/data/geo_cross_walk_tm2_area_based.csv")
    else:
        output_file = Path(args.output)
    
    print(f"MAZ shapefile: {maz_shapefile}")
    print(f"PUMA shapefile: {puma_shapefile}")
    print(f"Output file: {output_file}")
    
    success = create_area_based_crosswalk(maz_shapefile, puma_shapefile, output_file)
    
    if success:
        print(f"\n✅ SUCCESS: Area-based crosswalk created!")
        print(f"   File: {output_file}")
        print(f"   Each TAZ assigned to PUMA with largest area overlap")
    else:
        print(f"\n❌ FAILED: Could not create crosswalk")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
