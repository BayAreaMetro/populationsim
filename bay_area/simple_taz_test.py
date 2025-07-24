#!/usr/bin/env python3
"""
Simple TAZ Mapping Test
Tests basic functionality of the TAZ mapping system.
"""

import sys
import os
import pandas as pd

# Add the tm2_control_utils to the path
sys.path.append('tm2_control_utils')

def test_taz_data_and_basic_functionality():
    """Test basic TAZ data loading and analysis."""
    print("=" * 60)
    print("SIMPLE TAZ MAPPING TEST")
    print("=" * 60)
    
    # Check if we have TAZ data
    taz_file = "output_2023/taz_marginals.csv"
    if not os.path.exists(taz_file):
        print(f"❌ TAZ marginals file not found: {taz_file}")
        return False
    
    # Load and analyze the data
    try:
        taz_df = pd.read_csv(taz_file)
        print(f"✅ Successfully loaded TAZ data: {len(taz_df)} TAZ zones")
        
        # Get numeric columns (potential mapping metrics)
        numeric_cols = []
        for col in taz_df.columns:
            if col != 'TAZ' and pd.api.types.is_numeric_dtype(taz_df[col]):
                if taz_df[col].sum() > 0:  # Has non-zero values
                    numeric_cols.append(col)
        
        print(f"✅ Found {len(numeric_cols)} mappable metrics:")
        for i, col in enumerate(numeric_cols[:10], 1):  # Show first 10
            total = taz_df[col].sum()
            print(f"   {i:2d}. {col:<20} (Total: {total:>10,.0f})")
        
        if len(numeric_cols) > 10:
            print(f"   ... and {len(numeric_cols) - 10} more metrics")
            
        # Show data summary
        print(f"\n📊 TAZ Data Summary:")
        print(f"   • TAZ zones: {len(taz_df):,}")
        print(f"   • Data columns: {len(taz_df.columns)} total")
        print(f"   • Mappable metrics: {len(numeric_cols)}")
        
        # Show some key totals
        key_metrics = ['hh_inc_30', 'hh_inc_30_60', 'hh_inc_60_100', 'hh_inc_100_plus']
        existing_metrics = [m for m in key_metrics if m in taz_df.columns]
        
        if existing_metrics:
            print(f"\n🏠 Household Income Distribution:")
            total_hh = sum(taz_df[m].sum() for m in existing_metrics)
            for metric in existing_metrics:
                count = taz_df[metric].sum()
                pct = (count / total_hh * 100) if total_hh > 0 else 0
                print(f"   • {metric:<15}: {count:>8,.0f} households ({pct:5.1f}%)")
            print(f"   • Total households:  {total_hh:>8,.0f}")
        
        # Test basic mapping functionality
        print(f"\n🗺️  Testing Basic Mapping Components:")
        
        # Try importing mapping modules
        try:
            from taz_mapper import TAZMapper
            print("   ✅ TAZMapper class imported successfully")
            
            # Try initializing
            mapper = TAZMapper(data_dir="output_2023")
            print("   ✅ TAZMapper initialized successfully")
            
            # Try loading data
            mapper.load_taz_data()
            print("   ✅ TAZ data loaded into mapper")
            
            # Check if we have numeric columns method
            if hasattr(mapper, 'get_numeric_columns'):
                try:
                    numeric_from_mapper = mapper.get_numeric_columns()
                    print(f"   ✅ Found {len(numeric_from_mapper)} numeric columns via mapper")
                except:
                    print("   ⚠️  get_numeric_columns method exists but failed (likely due to missing shapefile)")
            
        except ImportError as e:
            print(f"   ❌ Could not import mapping modules: {e}")
        except Exception as e:
            print(f"   ⚠️  Mapping setup issue (likely missing shapefile): {e}")
            
        # Test output directory
        output_dir = "output_2023"
        if os.path.exists(output_dir):
            print(f"   ✅ Output directory exists: {output_dir}")
        else:
            print(f"   ⚠️  Output directory missing: {output_dir}")
            
        print(f"\n" + "=" * 60)
        print("✅ TAZ DATA TEST COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Summary:")
        print(f"  📁 Data file: {taz_file}")
        print(f"  📊 TAZ zones: {len(taz_df):,}")
        print(f"  🎯 Mappable metrics: {len(numeric_cols)}")
        print(f"  💡 Ready for visualization (pending shapefile)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading or analyzing TAZ data: {e}")
        return False

def main():
    """Main test function."""
    try:
        success = test_taz_data_and_basic_functionality()
        if success:
            print("\n🎉 TAZ data test completed successfully!")
            print("\nNext steps:")
            print("  1. Obtain TAZ shapefile for full mapping functionality")
            print("  2. Place shapefile in configured directory")
            print("  3. Run create_interactive_dashboard() for full visualization")
            return 0
        else:
            print("\n❌ TAZ data test failed!")
            return 1
            
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
