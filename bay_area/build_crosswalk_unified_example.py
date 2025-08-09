#!/usr/bin/env python3
"""
Example of how to update build_crosswalk_focused.py to use unified configuration
This shows the pattern for eliminating ALL hardcoded paths
"""

from pathlib import Path
import sys
import geopandas as gpd
import pandas as pd

# Import unified configuration
from unified_tm2_config import config

def main():
    """Updated crosswalk generation using unified configuration"""
    
    print("🗺️  Geographic Crosswalk Creation (TM2)")
    print("=" * 60)
    
    # Get all paths from unified configuration
    paths = config.get_crosswalk_paths()
    
    print(f"📂 Configuration:")
    print(f"   MAZ Shapefile: {paths['maz_shapefile']}")
    print(f"   PUMA Shapefile: {paths['puma_shapefile']}")
    print(f"   Output Primary: {paths['output_primary']}")
    print(f"   Output Reference: {paths['output_reference']}")
    print()
    
    # Ensure both output directories exist
    paths['output_primary'].parent.mkdir(parents=True, exist_ok=True)
    paths['output_reference'].parent.mkdir(parents=True, exist_ok=True)
    
    # Check input files exist
    if not paths['maz_shapefile'].exists():
        print(f"❌ ERROR: MAZ shapefile not found: {paths['maz_shapefile']}")
        return False
    
    if not paths['puma_shapefile'].exists():
        print(f"❌ ERROR: PUMA shapefile not found: {paths['puma_shapefile']}")
        return False
    
    print("✅ All input files found")
    print()
    print("🔄 Loading shapefiles...")
    
    # Load shapefiles
    maz_gdf = gpd.read_file(paths['maz_shapefile'])
    puma_gdf = gpd.read_file(paths['puma_shapefile'])
    
    print(f"   MAZ records: {len(maz_gdf):,}")
    print(f"   PUMA records: {len(puma_gdf):,}")
    
    # Rest of crosswalk logic would go here...
    # (spatial join, processing, etc.)
    
    print("✅ Crosswalk generation completed")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
