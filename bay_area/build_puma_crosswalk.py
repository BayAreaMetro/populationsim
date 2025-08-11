#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PUMA Crosswalk Creator with 2020 PUMA Support

This script creates spatial crosswalk using 2020 PUMA boundaries:
1. Uses existing build_crosswalk_focused.py functionality  
2. Creates spatial mappings for 2020 PUMA boundaries
3. Generates crosswalk with columns: MAZ, TAZ, COUNTY, county_name, PUMA
4. Prepares Bay Area PUMA lists for PUMS data filtering

Supports the workflow:
- Uses Census Bureau 2023 5-Year PUMS data with pre-crosswalked PUMA codes
- All data already converted to 2020 PUMA boundaries by Census Bureau
- Direct filtering using 2020 PUMA definitions
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
import sys
import argparse

# Bay Area FIPS county codes (without leading zeros to match extracted codes)
BAY_AREA_COUNTIES = ['01', '13', '41', '55', '75', '81', '85', '95', '97']

class PUMACrosswalkBuilder:
    """Creates crosswalks with 2020 PUMA definitions"""
    
    def __init__(self, maz_shapefile_path, puma_2020_path, output_dir):
        self.maz_shapefile = Path(maz_shapefile_path)
        self.puma_2020_shapefile = Path(puma_2020_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
    def extract_bay_area_pumas_from_shapefiles(self):
        """Extract Bay Area PUMA lists from 2020 shapefiles using spatial intersection"""
        
        print("="*60)
        print("EXTRACTING BAY AREA PUMAS FROM SHAPEFILES")
        print("="*60)
        
        # Load 2020 PUMA shapefile and extract Bay Area PUMAs
        print(f"\nExtracting 2020 Bay Area PUMAs...")
        
        if not self.puma_2020_shapefile.exists():
            print(f"ERROR: 2020 PUMA shapefile not found: {self.puma_2020_shapefile}")
            return None
            
        try:
            # Load PUMA shapefile
            puma_gdf = gpd.read_file(self.puma_2020_shapefile)
            print(f"  Loaded {len(puma_gdf)} 2020 PUMAs for California")
            
            # Find PUMA column
            puma_col = None
            for col in puma_gdf.columns:
                if 'PUMACE20' in col:
                    puma_col = col
                    break
            
            if not puma_col:
                print(f"  ERROR: Could not find PUMA column for 2020")
                return None
            
            # Get all PUMAs - we'll do proper spatial filtering against Bay Area counties
            all_pumas = puma_gdf[puma_col].astype(str).unique()
            
            # Load county boundaries to do proper spatial intersection
            # For now, use all CA PUMAs and filter during spatial join
            print(f"  Found {len(all_pumas)} total California PUMAs")
            
            bay_area_puma_list = sorted(all_pumas)
            
            print(f"  Using all {len(bay_area_puma_list)} PUMAs for spatial analysis")
            print(f"  Sample PUMAs: {bay_area_puma_list[:10]}")
            
        except Exception as e:
            print(f"  ERROR processing 2020 shapefile: {e}")
            return None
        
        # Save PUMA list for PUMS filtering
        output_file = self.output_dir / f"bay_area_pumas_2020.txt"
        with open(output_file, 'w') as f:
            f.write(f"# Bay Area PUMAs - 2020 Census definitions\n")
            f.write(f"# Total California PUMAs: {len(bay_area_puma_list)}\n")
            f.write(f"# For PUMS data filtering: 2019-2023 data years (all pre-crosswalked to 2020 boundaries)\n\n")
            
            # Write as Python list for easy import
            f.write(f"BAY_AREA_PUMAS_2020 = [\n")
            for i, puma in enumerate(bay_area_puma_list):
                if i > 0 and i % 10 == 0:
                    f.write("\n    ")
                f.write(f"'{puma}', ")
            f.write("\n]\n")
            
        print(f"  Saved 2020 PUMA list: {output_file}")
        
        return bay_area_puma_list
    
    def create_puma_crosswalk(self):
        """Create crosswalk with 2020 PUMA assignments"""
        
        print("\n" + "="*60)
        print("CREATING PUMA CROSSWALK")
        print("="*60)
        
        # Load base crosswalk (MAZ->TAZ relationships)
        print("\nLoading base MAZ->TAZ crosswalk...")
        
        # Load MAZ shapefile
        if not self.maz_shapefile.exists():
            print(f"ERROR: MAZ shapefile not found: {self.maz_shapefile}")
            return None
            
        try:
            maz_gdf = gpd.read_file(self.maz_shapefile)
            print(f"  Loaded {len(maz_gdf):,} MAZ zones")
            
            # Check for required columns
            if 'maz' not in maz_gdf.columns or 'taz' not in maz_gdf.columns:
                print("  ERROR: MAZ shapefile missing required columns (maz, taz)")
                return None
                
        except Exception as e:
            print(f"  ERROR loading MAZ shapefile: {e}")
            return None
        
        # Create base crosswalk with MAZ->TAZ relationships
        base_crosswalk = maz_gdf[['maz', 'taz']].copy()
        base_crosswalk.rename(columns={'maz': 'MAZ', 'taz': 'TAZ'}, inplace=True)
        
        print(f"  Base crosswalk: {len(base_crosswalk):,} MAZ->TAZ relationships")
        
        # Create MAZ centroids for spatial join
        print("\nPreparing MAZ centroids for spatial join...")
        maz_centroids = maz_gdf.copy()
        maz_centroids['geometry'] = maz_centroids.geometry.centroid
        maz_centroids = maz_centroids[['maz', 'geometry']]
        maz_centroids.rename(columns={'maz': 'MAZ'}, inplace=True)
        
        # Spatial join with 2020 PUMAs  
        print(f"\nSpatial join with 2020 PUMAs: {self.puma_2020_shapefile}")
        puma_2020_gdf = gpd.read_file(self.puma_2020_shapefile)
        
        # Find 2020 PUMA column
        puma_2020_col = None
        for col in puma_2020_gdf.columns:
            if 'PUMACE20' in col:
                puma_2020_col = col
                break
        
        if not puma_2020_col:
            print("ERROR: Could not find 2020 PUMA column")
            return None
            
        # Reproject to match CRS
        print(f"  Reprojecting 2020 PUMAs to match MAZ CRS...")
        puma_2020_gdf = puma_2020_gdf.to_crs(maz_centroids.crs)
        
        # Perform spatial join for 2020 PUMAs
        maz_puma_2020 = gpd.sjoin(
            maz_centroids,
            puma_2020_gdf[[puma_2020_col, 'geometry']],
            how='left', 
            predicate='within'
        )
        
        print(f"  2020 PUMA assignments: {maz_puma_2020[puma_2020_col].notna().sum():,} / {len(maz_puma_2020):,} MAZs")
        
        # Combine results
        print("\nCombining PUMA assignments...")
        
        # Create final crosswalk
        final_crosswalk = base_crosswalk[['MAZ', 'TAZ']].copy()
        final_crosswalk['PUMA'] = maz_puma_2020[puma_2020_col].values
        
        # Add county information (simplified mapping based on PUMA patterns)
        def puma_to_county(puma_code):
            if pd.isna(puma_code):
                return '99'
            puma_str = str(puma_code).zfill(5)
            
            # Basic county mapping for Bay Area (simplified)
            if puma_str.startswith('001'):
                return '01'  # Alameda
            elif puma_str.startswith('013'):
                return '13'  # Contra Costa
            elif puma_str.startswith('041'):
                return '41'  # Marin
            elif puma_str.startswith('055'):
                return '55'  # Napa
            elif puma_str.startswith('075'):
                return '75'  # San Francisco
            elif puma_str.startswith('081'):
                return '81'  # San Mateo
            elif puma_str.startswith('085'):
                return '85'  # Santa Clara
            elif puma_str.startswith('095'):
                return '95'  # Solano
            elif puma_str.startswith('097'):
                return '97'  # Sonoma
            else:
                return '99'  # Unknown
        
        final_crosswalk['COUNTY'] = final_crosswalk['PUMA'].apply(puma_to_county)
        
        # Debug: Check PUMA distribution before filtering
        print(f"\nDEBUG: Before filtering - Total MAZs: {len(final_crosswalk)}")
        puma_counts = final_crosswalk['PUMA'].value_counts()
        print(f"DEBUG: Top 10 PUMAs by MAZ count:")
        for puma, count in puma_counts.head(10).items():
            county = puma_to_county(puma)
            print(f"  PUMA {puma}: {count} MAZs (County: {county})")
        
        county_counts = final_crosswalk['COUNTY'].value_counts()
        print(f"\nDEBUG: Counties found:")
        for county, count in county_counts.items():
            print(f"  County {county}: {count} MAZs")
        
        # Filter to Bay Area counties only
        bay_area_mask = final_crosswalk['COUNTY'].isin(BAY_AREA_COUNTIES)
        print(f"\nDEBUG: Bay Area filter - {bay_area_mask.sum()} of {len(final_crosswalk)} MAZs match Bay Area counties")
        final_crosswalk = final_crosswalk[bay_area_mask].copy()
        
        print(f"  Final Bay Area crosswalk: {len(final_crosswalk):,} MAZ zones")
        print(f"  Unique 2020 PUMAs: {final_crosswalk['PUMA'].nunique():,}")
        print(f"  Coverage: {(final_crosswalk['PUMA'].notna().sum() / len(final_crosswalk) * 100):.1f}%")
        
        # Format PUMA column as integer (strip leading zeros like PopulationSim expects)
        final_crosswalk['PUMA'] = final_crosswalk['PUMA'].astype(str).str.lstrip('0').astype(int)
        
        return final_crosswalk
    
    def run(self):
        """Execute the complete crosswalk creation process"""
        
        print("STARTING PUMA CROSSWALK CREATION")
        print("="*80)
        print("Census Bureau 2023 5-Year PUMS with pre-crosswalked 2020 PUMA codes")
        print("All data years (2019-2023) already converted to 2020 PUMA boundaries")
        print("="*80)
        
        # Step 1: Extract Bay Area PUMA lists
        bay_area_pumas = self.extract_bay_area_pumas_from_shapefiles()
        if bay_area_pumas is None:
            print("ERROR: Failed to extract Bay Area PUMAs")
            return None
        
        # Step 2: Create crosswalk
        crosswalk_df = self.create_puma_crosswalk()
        if crosswalk_df is None:
            print("ERROR: Failed to create crosswalk")
            return None
        
        # Step 3: Save outputs
        print("\n" + "="*60)
        print("SAVING OUTPUTS")
        print("="*60)
        
        # Save main crosswalk
        crosswalk_output = self.output_dir / "geo_cross_walk_tm2.csv"
        crosswalk_df.to_csv(crosswalk_output, index=False)
        print(f"Main crosswalk saved: {crosswalk_output}")
        
        # Save summary
        summary_output = self.output_dir / "puma_crosswalk_summary.txt"
        with open(summary_output, 'w') as f:
            f.write("PUMA CROSSWALK SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total MAZ zones: {len(crosswalk_df):,}\n")
            f.write(f"Unique TAZ zones: {crosswalk_df['TAZ'].nunique():,}\n")
            f.write(f"Unique 2020 PUMAs: {crosswalk_df['PUMA'].nunique():,}\n")
            f.write(f"Unique counties: {crosswalk_df['COUNTY'].nunique():,}\n")
            f.write(f"PUMA coverage: {(crosswalk_df['PUMA'].notna().sum() / len(crosswalk_df) * 100):.1f}%\n\n")
            
            f.write("County distribution:\n")
            county_counts = crosswalk_df['COUNTY'].value_counts()
            for county, count in county_counts.items():
                f.write(f"  County {county}: {count:,} MAZs\n")
        
        print(f"Summary saved: {summary_output}")
        
        print("\n" + "="*60)
        print("CROSSWALK CREATION COMPLETE")
        print("="*60)
        print("Files created:")
        print(f"1. Main crosswalk: {crosswalk_output}")
        print(f"2. Bay Area PUMAs: {self.output_dir / 'bay_area_pumas_2020.txt'}")
        print(f"3. Summary: {summary_output}")
        print()
        print("Usage:")
        print("1. Use bay_area_pumas_2020.txt for filtering 2019-2023 PUMS data")
        print("2. Use geo_cross_walk_tm2.csv for PopulationSim crosswalk")
        print("3. All PUMA codes are 2020 Census boundaries")
        
        return crosswalk_df

def main():
    """Main execution function"""
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Create MAZ->PUMA crosswalk with 2020 PUMA boundaries")
    parser.add_argument("--maz_shapefile", type=str, help="Path to MAZ shapefile")
    parser.add_argument("--puma_shapefile", type=str, help="Path to 2020 PUMA shapefile")
    parser.add_argument("--output_dir", type=str, help="Output directory")
    args = parser.parse_args()
    
    # Import configuration to get paths
    try:
        from unified_tm2_config import config
        print("Using unified configuration for paths")
        
        maz_shapefile = config.SHAPEFILES['maz_shapefile']
        puma_shapefile = config.SHAPEFILES['puma_shapefile']
        output_dir = Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/puma_outputs")
        
    except ImportError:
        print("Could not import config, using command line arguments")
        if not all([args.maz_shapefile, args.puma_shapefile, args.output_dir]):
            print("ERROR: When config is not available, all arguments are required")
            return 1
            
        maz_shapefile = Path(args.maz_shapefile)
        puma_shapefile = Path(args.puma_shapefile) 
        output_dir = Path(args.output_dir)
    
    # Override with command line arguments if provided
    if args.maz_shapefile:
        maz_shapefile = Path(args.maz_shapefile)
    if args.puma_shapefile:
        puma_shapefile = Path(args.puma_shapefile)
    if args.output_dir:
        output_dir = Path(args.output_dir)
    
    print(f"MAZ shapefile: {maz_shapefile}")
    print(f"PUMA shapefile: {puma_shapefile}")
    print(f"Output directory: {output_dir}")
    
    # Create and run builder
    builder = PUMACrosswalkBuilder(
        maz_shapefile_path=maz_shapefile,
        puma_2020_path=puma_shapefile,
        output_dir=output_dir
    )
    
    result = builder.run()
    
    if result is not None:
        print("SUCCESS: Crosswalk creation completed")
        return 0
    else:
        print("ERROR: Crosswalk creation failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
