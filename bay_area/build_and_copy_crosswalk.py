#!/usr/bin/env python3
"""
Crosswalk Builder and Copier for TM2 Pipeline
Creates the crosswalk and copies it to the consolidated output directory
"""

import sys
import shutil
from pathlib import Path
import subprocess

def main():
    """Build crosswalk and copy to consolidated output directory"""
    
    # Import after ensuring we're in the right directory
    sys.path.insert(0, str(Path(__file__).parent))
    from unified_tm2_config import UnifiedTM2Config
    
    config = UnifiedTM2Config()
    
    print("=" * 60)
    print("CROSSWALK CREATION AND CONSOLIDATION")
    print("=" * 60)
    
    # Step 1: Run the area-based crosswalk creation
    print("Step 1: Creating area-based crosswalk...")
    crosswalk_script = config.BASE_DIR / "create_area_based_crosswalk.py"
    
    # Set output directly to the consolidated directory
    target_file = config.CROSSWALK_FILES['main_crosswalk']
    
    try:
        result = subprocess.run([
            str(config.PYTHON_EXE),
            str(crosswalk_script),
            "--maz-shapefile", str(config.SHAPEFILES['maz_shapefile']),
            "--puma-shapefile", str(config.SHAPEFILES['puma_shapefile']),
            "--output", str(target_file)
        ] + sys.argv[1:], check=True, capture_output=False)
        
        print("✓ Area-based crosswalk creation completed successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Area-based crosswalk creation failed: {e}")
        return 1
    
    # Step 2: Verify the file was created
    print("\nStep 2: Verifying crosswalk file...")
    
    try:
        if target_file.exists():
            print(f"✓ Verification: Crosswalk file exists ({target_file.stat().st_size:,} bytes)")
            print(f"✓ Location: {target_file}")
        else:
            print("✗ Verification: Crosswalk file missing!")
            return 1
            
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return 1
    
    print("\n" + "=" * 60)
    print("AREA-BASED CROSSWALK CREATION COMPLETE")
    print("=" * 60)
    print(f"✓ Area-based crosswalk: {target_file}")
    print("✓ Each TAZ assigned to PUMA with largest area overlap")
    print("✓ Ready for next pipeline step")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
