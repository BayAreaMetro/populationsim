"""
Debug script to isolate the doubling issue in TAZ worker controls.
Run a minimal test to trace exactly where the doubling occurs.
"""

import pandas as pd
import logging
import sys
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tm2_control_utils.controls import disaggregate_tract_to_block_group

def debug_disaggregation_doubling():
    """Test the disaggregation function directly to identify doubling issue."""
    
    print("="*80)
    print("DEBUGGING TRACT TO BLOCK GROUP DISAGGREGATION")
    print("="*80)
    
    # Load actual data files
    print("Loading test data...")
    
    # Load geography crosswalk
    maz_taz_def_path = 'output_2023/geo_cross_walk_tm2.csv'
    maz_taz_def_df = pd.read_csv(maz_taz_def_path)
    print(f"Loaded crosswalk: {len(maz_taz_def_df)} records")
    print(f"Original crosswalk columns: {list(maz_taz_def_df.columns)}")
    
    # Add test block group to TAZ mapping for our test data
    test_bg_taz_mapping = pd.DataFrame({
        'GEOID_block group': ['060140110011', '060140110012', '060140120011', '060140120012', '060140130011'],
        'TAZ': [1001, 1001, 1002, 1002, 1003]  # Group some BGs into same TAZ
    })
    
    # Add to crosswalk for testing
    maz_taz_def_df = pd.concat([maz_taz_def_df, test_bg_taz_mapping], ignore_index=True)
    print(f"Enhanced crosswalk with test data: {len(maz_taz_def_df)} records")
    print(f"Test BG-TAZ mapping:")
    print(test_bg_taz_mapping)
    
    # Create test tract-level data (simplified B08202 worker data)
    test_tract_data = pd.DataFrame({
        'GEOID_tract': ['06014011001', '06014012001', '06014013001'],  # Sample Bay Area tracts (11 digits)
        'hh_wrks_0': [100, 200, 150]  # Test values
    })
    print(f"Test tract data:")
    print(test_tract_data)
    print(f"Test tract total: {test_tract_data['hh_wrks_0'].sum()}")
    
    # Create test household weights for block groups (from temp_hh_bg_for_tract_weights equivalent)
    # Block group GEOIDs are 12 digits: tract (11) + block group (1)
    test_hh_weights = pd.DataFrame({
        'GEOID_block group': ['060140110011', '060140110012', '060140120011', '060140120012', '060140130011'],
        'hh_count': [40, 60, 80, 120, 150]  # Household counts per block group
    })
    print(f"\nTest household weights:")
    print(test_hh_weights)
    print(f"Total households: {test_hh_weights['hh_count'].sum()}")
    
    # Show expected manual calculation
    print(f"\nMANUAL CALCULATION CHECK:")
    for tract in test_tract_data['GEOID_tract']:
        tract_value = test_tract_data[test_tract_data['GEOID_tract'] == tract]['hh_wrks_0'].iloc[0]
        
        # Get block groups in this tract (first 11 digits match)
        bgs_in_tract = test_hh_weights[test_hh_weights['GEOID_block group'].str[:11] == tract]
        tract_total_hh = bgs_in_tract['hh_count'].sum()
        
        print(f"  Tract {tract}: Value={tract_value}, HH={tract_total_hh}")
        
        for _, bg_row in bgs_in_tract.iterrows():
            bg_geoid = bg_row['GEOID_block group']
            bg_hh = bg_row['hh_count']
            weight = bg_hh / tract_total_hh if tract_total_hh > 0 else 0
            expected_value = tract_value * weight
            print(f"    BG {bg_geoid}: HH={bg_hh}, Weight={weight:.3f}, Expected={expected_value:.1f}")
    
    expected_total = test_tract_data['hh_wrks_0'].sum()
    print(f"  Expected total after disaggregation: {expected_total}")
    
    print(f"\nTESTING DISAGGREGATION FUNCTION:")
    print("-" * 50)
    
    try:
        result = disaggregate_tract_to_block_group(
            control_table_df=test_tract_data,
            control_name='hh_wrks_0',
            hh_weights_df=test_hh_weights,
            maz_taz_def_df=maz_taz_def_df
        )
        
        print(f"\nFUNCTION RESULT:")
        print(f"Result shape: {result.shape}")
        print(f"Result total: {result['hh_wrks_0'].sum():,.1f}")
        print(f"Expected total: {expected_total}")
        print(f"RATIO (result/expected): {result['hh_wrks_0'].sum() / expected_total:.4f}")
        
        if abs(result['hh_wrks_0'].sum() / expected_total - 1.0) > 0.01:
            print(f"*** ISSUE DETECTED: Ratio is not 1.0! ***")
        else:
            print("✓ Result matches expected total")
            
        print(f"\nResult details:")
        print(result)
        
    except Exception as e:
        print(f"ERROR in disaggregation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_disaggregation_doubling()
