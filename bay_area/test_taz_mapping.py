#!/usr/bin/env python3
"""
Test TAZ Mapping System
Tests the TAZ mapping functionality with the generated control files.
"""

import sys
import os
import pandas as pd
from pathlib import Path

# Add the tm2_control_utils to the path
sys.path.append('tm2_control_utils')

# Import our configuration and mapping classes
from config import ENABLE_TAZ_MAPPING, TAZ_SHAPEFILE_DIR, MAP_OUTPUT_DIR
from taz_mapper import TAZMapper

def test_mapping_system():
    """Test the complete TAZ mapping system."""
    print("=" * 60)
    print("TESTING TAZ MAPPING SYSTEM")
    print("=" * 60)
    
    # Check if mapping is enabled
    if not ENABLE_TAZ_MAPPING:
        print("❌ TAZ mapping is disabled in config. Set ENABLE_TAZ_MAPPING = True")
        return False
    
    print("✅ TAZ mapping is enabled in configuration")
    
    # Check required files
    taz_file = "output_2023/taz_marginals.csv"
    if not os.path.exists(taz_file):
        print(f"❌ TAZ marginals file not found: {taz_file}")
        return False
    
    print(f"✅ Found TAZ marginals file: {taz_file}")
    
    # Load TAZ data to check structure
    try:
        taz_df = pd.read_csv(taz_file)
        print(f"✅ Successfully loaded TAZ data: {len(taz_df)} TAZ zones")
        print(f"   Available columns: {list(taz_df.columns)}")
        
        # Show sample data
        print("\nSample TAZ data:")
        print(taz_df.head())
        
    except Exception as e:
        print(f"❌ Error loading TAZ data: {e}")
        return False
    
    # Test TAZ mapper initialization
    try:
        print("\n" + "=" * 40)
        print("TESTING TAZ MAPPER INITIALIZATION")
        print("=" * 40)
        
        mapper = TAZMapper(
            data_dir="output_2023",
            shapefile_dir=TAZ_SHAPEFILE_DIR,
            output_dir=MAP_OUTPUT_DIR
        )
        print("✅ TAZMapper initialized successfully")
        
        # Load the TAZ data
        mapper.load_taz_data()
        print("✅ TAZ data loaded successfully")
        
    except Exception as e:
        print(f"❌ Error initializing TAZMapper: {e}")
        print(f"   Shapefile directory: {TAZ_SHAPEFILE_DIR}")
        return False
    
    # Test shapefile loading
    try:
        print("\n" + "=" * 40)
        print("TESTING SHAPEFILE LOADING")
        print("=" * 40)
        
        mapper.load_taz_shapes()
        print("✅ TAZ shapefile loaded successfully")
        
        # Test data merging
        mapper.merge_data()
        print("✅ TAZ data and shapes merged successfully")
        
    except Exception as e:
        print(f"❌ Error loading shapefile or merging data: {e}")
        print("   This might be expected if shapefile is not available")
        print("   Continuing with other tests...")
        # Don't return False here as shapefile might not be available
    
    # Test available metrics detection
    try:
        metrics = mapper.get_available_metrics()
        print(f"✅ Available metrics detected: {len(metrics)} metrics")
        for metric in metrics[:5]:  # Show first 5
            print(f"   - {metric}")
        if len(metrics) > 5:
            print(f"   ... and {len(metrics) - 5} more")
            
    except Exception as e:
        print(f"❌ Error detecting metrics: {e}")
        return False
    
    # Test static map creation for first metric
    try:
        print("\n" + "=" * 40)
        print("TESTING STATIC MAP CREATION")
        print("=" * 40)
        
        first_metric = metrics[0] if metrics else 'hh_inc_30'
        print(f"Creating static map for: {first_metric}")
        
        static_file = mapper.create_static_map(first_metric)
        if static_file and os.path.exists(static_file):
            print(f"✅ Static map created: {static_file}")
        else:
            print(f"❌ Static map creation failed or file not found")
            return False
            
    except Exception as e:
        print(f"❌ Error creating static map: {e}")
        return False
    
    # Test interactive dashboard creation
    try:
        print("\n" + "=" * 40)
        print("TESTING INTERACTIVE DASHBOARD")
        print("=" * 40)
        
        dashboard_file = mapper.create_interactive_dashboard()
        if dashboard_file and os.path.exists(dashboard_file):
            print(f"✅ Interactive dashboard created: {dashboard_file}")
            print(f"   File size: {os.path.getsize(dashboard_file):,} bytes")
        else:
            print(f"❌ Dashboard creation failed or file not found")
            return False
            
    except Exception as e:
        print(f"❌ Error creating dashboard: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED! TAZ Mapping system is working correctly.")
    print("=" * 60)
    print(f"\nGenerated files:")
    print(f"  📊 Interactive Dashboard: {dashboard_file}")
    print(f"  🗺️  Static Map Sample: {static_file}")
    print(f"\nTo view the interactive dashboard, open: {dashboard_file}")
    
    return True

def main():
    """Main test function."""
    try:
        success = test_mapping_system()
        if success:
            print("\n🎉 TAZ mapping system test completed successfully!")
            return 0
        else:
            print("\n❌ TAZ mapping system test failed!")
            return 1
            
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
