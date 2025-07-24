#!/usr/bin/env python3
"""
Test TAZ Dashboard Creation
Tests creating an interactive dashboard with the TAZ data.
"""

import sys
import os

# Add the tm2_control_utils to the path
sys.path.append('tm2_control_utils')

def test_dashboard_creation():
    """Test creating an interactive dashboard."""
    print("=" * 60)
    print("TESTING TAZ DASHBOARD CREATION")
    print("=" * 60)
    
    try:
        from taz_mapper import TAZMapper
        
        # Initialize mapper
        mapper = TAZMapper(data_dir="output_2023", output_dir="output_2023")
        print("✅ TAZMapper initialized")
        
        # Load TAZ data
        mapper.load_taz_data()
        print("✅ TAZ data loaded")
        
        # Try to create dashboard (should work even without shapefile)
        print("\n🎨 Creating interactive dashboard...")
        try:
            dashboard_file = mapper.create_interactive_dashboard()
            
            if dashboard_file and os.path.exists(dashboard_file):
                file_size = os.path.getsize(dashboard_file)
                print(f"✅ Dashboard created successfully!")
                print(f"   📄 File: {dashboard_file}")
                print(f"   📏 Size: {file_size:,} bytes")
                
                # Try to open in browser (optional)
                try:
                    import webbrowser
                    full_path = os.path.abspath(dashboard_file)
                    webbrowser.open(f'file:///{full_path}')
                    print(f"🌐 Opened dashboard in default browser")
                except Exception as e:
                    print(f"⚠️  Could not auto-open browser: {e}")
                    print(f"   💡 You can manually open: {os.path.abspath(dashboard_file)}")
                
                return True
            else:
                print("❌ Dashboard file was not created or not found")
                return False
                
        except Exception as e:
            print(f"❌ Error creating dashboard: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error during dashboard test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    success = test_dashboard_creation()
    
    if success:
        print("\n🎉 Dashboard test completed successfully!")
        print("\nThe dashboard provides:")
        print("  📊 Interactive data tables for all TAZ metrics")
        print("  🔍 Filtering and sorting capabilities")
        print("  📈 Summary statistics")
        print("  📋 Data export options")
        print("\nNote: Geographic maps require TAZ shapefiles")
        return 0
    else:
        print("\n❌ Dashboard test failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
