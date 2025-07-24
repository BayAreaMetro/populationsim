"""
Quick TAZ Mapping Utility

Simple script to quickly generate TAZ control maps.
Run this after generating TAZ marginals to create visualizations.

Usage:
    python quick_taz_maps.py [column_name]
    
If no column is specified, creates maps for all numeric columns.
"""

import sys
import os

# Add current directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from taz_mapper import TAZMapper
    from config import ENABLE_TAZ_MAPPING
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure config.py and taz_mapper.py are in the same directory")
    sys.exit(1)


def quick_map(column_name=None):
    """
    Quickly create TAZ maps.
    
    Parameters:
    -----------
    column_name : str, optional
        Specific column to map. If None, maps all numeric columns.
    """
    if not ENABLE_TAZ_MAPPING:
        print("TAZ mapping is disabled in configuration")
        print("Set ENABLE_TAZ_MAPPING = True in config.py to enable")
        return
        
    try:
        mapper = TAZMapper()
        
        if column_name:
            # Map specific column
            numeric_cols = mapper.get_numeric_columns()
            if column_name not in numeric_cols:
                print(f"Column '{column_name}' not found or not numeric")
                print(f"Available columns: {', '.join(numeric_cols)}")
                return
                
            print(f"Creating map for: {column_name}")
            
            # Create interactive map
            folium_map = mapper.create_folium_map(
                column_name, 
                title=f'TAZ {column_name.replace("_", " ").title()}'
            )
            
            # Save map
            output_path = os.path.join(mapper.output_dir, f'taz_map_{column_name}.html')
            folium_map.save(output_path)
            print(f"Interactive map saved: {output_path}")
            
        else:
            # Create all maps
            mapper.create_all_maps()
            
    except Exception as e:
        print(f"Error creating maps: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Parse command line arguments
    column_name = sys.argv[1] if len(sys.argv) > 1 else None
    quick_map(column_name)
