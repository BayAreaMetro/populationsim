#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEFINITIVE TM2 Crosswalk Creator
Single script to create area-based MAZ-TAZ-PUMA crosswalk for PopulationSim TM2

This is the ONE AND ONLY crosswalk script for the TM2 pipeline.
- Uses area-based TAZ-PUMA assignment (most accurate)
- Outputs directly to consolidated output_2023 directory
- Uses 1-9 county system from unified config
- No copying, no duplication, no confusion
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
import sys
import argparse

# Import unified config for county mappings
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
    
    # Add county information using 1-9 system from unified config
    if verbose:
        print(f"\nStep 4a: Adding county information using 1-9 system...")
    
    # Use existing tm2py-utils crosswalk as reference for PUMA-to-county mapping
    reference_crosswalk_file = Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/puma_outputs/geo_cross_walk_tm2.csv")
    
    if reference_crosswalk_file.exists():
        try:
            ref_df = pd.read_csv(reference_crosswalk_file)
            if 'PUMA' in ref_df.columns and 'COUNTY' in ref_df.columns:
                # Create PUMA-to-county mapping from reference (this uses old FIPS-based system)
                puma_county_ref = ref_df[['PUMA', 'COUNTY']].drop_duplicates()
                
                # Convert both PUMA formats to integers for comparison
                def normalize_puma(puma_val):
                    """Convert PUMA to integer for consistent comparison"""
                    try:
                        if pd.isna(puma_val):
                            return None
                        puma_str = str(puma_val).strip()
                        # Remove leading zeros and convert to int
                        return int(puma_str.lstrip('0')) if puma_str.strip('0') else 0
                    except:
                        return None
                
                # Normalize reference PUMAs - but map to FIPS first, then to 1-9 system
                ref_df['PUMA_norm'] = ref_df['PUMA'].apply(normalize_puma)
                puma_county_ref = ref_df[['PUMA_norm', 'COUNTY']].dropna().drop_duplicates()
                
                # Convert FIPS-based counties to 1-9 system using unified config
                puma_to_county_seq = {}
                for _, row in puma_county_ref.iterrows():
                    puma_id = row['PUMA_norm']
                    fips_county = row['COUNTY']
                    
                    # Look up the sequential county ID (1-9) from FIPS code
                    county_seq_id, county_info = config.get_county_by_fips(fips_county)
                    if county_seq_id:
                        puma_to_county_seq[puma_id] = county_seq_id
                
                # Normalize our crosswalk PUMAs and map to 1-9 system
                crosswalk_df['PUMA_norm'] = crosswalk_df['PUMA'].apply(normalize_puma)
                crosswalk_df['COUNTY'] = crosswalk_df['PUMA_norm'].map(puma_to_county_seq)
                
                if verbose:
                    print(f"  Loaded PUMA-to-county mapping and converted to 1-9 system:")
                    print(f"  Found {len(puma_to_county_seq)} PUMA-to-county mappings")
                    counties = sorted([c for c in set(puma_to_county_seq.values()) if pd.notna(c)])
                    print(f"  Counties (1-9 system): {counties}")
                    
                    # Show the mapping for clarity
                    print(f"  County mapping used:")
                    for seq_id in sorted(config.BAY_AREA_COUNTIES.keys()):
                        county_info = config.BAY_AREA_COUNTIES[seq_id]
                        print(f"    {seq_id}: {county_info['name']} (FIPS {county_info['fips_int']})")
                
                # Check for missing mappings
                missing_counties = crosswalk_df['COUNTY'].isna().sum()
                if missing_counties > 0:
                    print(f"  WARNING: {missing_counties:,} MAZ zones have no county assignment")
                    missing_pumas = crosswalk_df[crosswalk_df['COUNTY'].isna()]['PUMA'].unique()
                    print(f"  PUMAs without county mapping: {sorted(missing_pumas)}")
                
                # Clean up temporary column
                crosswalk_df = crosswalk_df.drop('PUMA_norm', axis=1)
                
            else:
                print(f"  ERROR: Reference crosswalk missing PUMA or COUNTY columns")
                crosswalk_df['COUNTY'] = None
                
        except Exception as e:
            print(f"  ERROR: Could not read reference crosswalk: {e}")
            crosswalk_df['COUNTY'] = None
    else:
        print(f"  WARNING: Reference crosswalk not found: {reference_crosswalk_file}")
        print(f"  Setting all counties to None")
        crosswalk_df['COUNTY'] = None
    
    # Add county names and FIPS codes using unified config
    if verbose:
        print(f"\nStep 4b: Adding county names and FIPS codes from unified config...")
    
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
    
    # Reorder columns to match expected format
    final_columns = ['MAZ', 'TAZ', 'COUNTY', 'county_name', 'COUNTYFP10', 'PUMA']
    crosswalk_df = crosswalk_df[final_columns]
    
    # Ensure integer types for IDs
    for col in ['MAZ', 'TAZ', 'COUNTY']:
        if col in crosswalk_df.columns:
            crosswalk_df[col] = pd.to_numeric(crosswalk_df[col], errors='coerce').astype('Int64')
    
    # Sort by MAZ
    crosswalk_df = crosswalk_df.sort_values('MAZ').reset_index(drop=True)
    
    if verbose:
        print(f"  Final crosswalk: {len(crosswalk_df):,} MAZ zones")
        print(f"  Unique TAZs: {crosswalk_df['TAZ'].nunique():,}")
        print(f"  Unique PUMAs: {crosswalk_df['PUMA'].nunique():,}")
        print(f"  Counties: {sorted(crosswalk_df['COUNTY'].dropna().unique())}")
    
    # Save output
    if verbose:
        print(f"\nStep 5: Saving crosswalk...")
        print(f"  Output: {output_file}")
    
    try:
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save CSV
        crosswalk_df.to_csv(output_file, index=False)
        
        if verbose:
            print(f"  SAVED: {len(crosswalk_df):,} records")
            print(f"  File size: {output_file.stat().st_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"ERROR saving crosswalk: {e}")
        return False

def main():
    """Main function"""
    
    parser = argparse.ArgumentParser(description='Create definitive TM2 crosswalk')
    parser.add_argument('--maz-shapefile', type=str, 
                       help='Path to MAZ shapefile')
    parser.add_argument('--puma-shapefile', type=str,
                       help='Path to PUMA shapefile') 
    parser.add_argument('--output', type=str,
                       help='Output crosswalk file path')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress verbose output')
    
    args = parser.parse_args()
    
    # Default paths using unified config
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from unified_tm2_config import UnifiedTM2Config
        config = UnifiedTM2Config()
        
        maz_shapefile = Path(args.maz_shapefile) if args.maz_shapefile else config.SHAPEFILES['maz_shapefile']
        puma_shapefile = Path(args.puma_shapefile) if args.puma_shapefile else config.SHAPEFILES['puma_shapefile']
        output_file = Path(args.output) if args.output else config.CROSSWALK_FILES['main_crosswalk']
        
    except Exception as e:
        print(f"ERROR: Could not load configuration: {e}")
        print("Using fallback paths...")
        
        maz_shapefile = Path(args.maz_shapefile) if args.maz_shapefile else Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/mazs_TM2_2_4.shp")
        puma_shapefile = Path(args.puma_shapefile) if args.puma_shapefile else Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/tl_2022_06_puma20.shp")
        output_file = Path(args.output) if args.output else Path("output_2023/geo_cross_walk_tm2_updated.csv")
    
    verbose = not args.quiet
    
    if verbose:
        print(f"MAZ shapefile: {maz_shapefile}")
        print(f"PUMA shapefile: {puma_shapefile}")
        print(f"Output file: {output_file}")
    
    success = create_tm2_crosswalk(maz_shapefile, puma_shapefile, output_file, verbose)
    
    if success:
        if verbose:
            print(f"\n" + "=" * 60)
            print("TM2 CROSSWALK CREATION COMPLETE")
            print("=" * 60)
            print(f"SUCCESS: Area-based crosswalk: {output_file}")
            print("Each TAZ assigned to PUMA with largest area overlap")
            print("Ready for next pipeline step")
        return 0
    else:
        print(f"\nFAILED: Could not create crosswalk")
        return 1

if __name__ == "__main__":
    sys.exit(main())
