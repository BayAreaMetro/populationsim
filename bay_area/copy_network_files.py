"""
copy_network_files.py

Script to copy network input files to local directory for offline work.
"""

import os
import shutil
import glob
from pathlib import Path

def copy_network_files():
    """Copy all network input files to local input_2023 directory."""
    
    # Define source and destination paths
    local_input_dir = Path("C:\\GitHub\\populationsim\\bay_area\\input_2023")
    
    # Network file paths from config.py
    network_files = {
        # GIS files
        "blocks_mazs_tazs.csv": "M:\\Data\\GIS layers\\TM2_maz_taz_v2.2\\blocks_mazs_tazs.csv",
        "mazs_tazs_county_tract_PUMA10.csv": "M:\\Data\\GIS layers\\TM2_maz_taz_v2.2\\mazs_tazs_county_tract_PUMA10.csv", 
        "mazs_tazs_all_geog.csv": "M:\\Data\\GIS layers\\TM2_maz_taz_v2.2\\mazs_tazs_all_geog.csv",
        
        # Census API key
        "api-key.txt": "M:\\Data\\Census\\API\\new_key\\api-key.txt",
        
        # NHGIS crosswalk files
        "nhgis_blk2020_blk2010_06.csv": "M:\\Data\\Census\\NewCachedTablesForPopulationSimControls\\nhgis_blk2020_blk2010_06.csv",
        "nhgis_bg2020_bg2010_06.csv": "M:\\Data\\Census\\NewCachedTablesForPopulationSimControls\\nhgis_bg2020_bg2010_06.csv", 
        "nhgis_tr2020_tr2010_06.csv": "M:\\Data\\Census\\NewCachedTablesForPopulationSimControls\\nhgis_tr2020_tr2010_06.csv",
    }
    
    # Create local directory if it doesn't exist
    local_input_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    gis_dir = local_input_dir / "gis"
    census_cache_dir = local_input_dir / "census_cache"
    api_dir = local_input_dir / "api"
    
    gis_dir.mkdir(exist_ok=True)
    census_cache_dir.mkdir(exist_ok=True)
    api_dir.mkdir(exist_ok=True)
    
    copied_files = []
    failed_files = []
    
    print(f"Copying network files to {local_input_dir}")
    
    for local_name, network_path in network_files.items():
        try:
            if not os.path.exists(network_path):
                print(f"WARNING: Source file not found: {network_path}")
                failed_files.append((local_name, network_path, "Source not found"))
                continue
                
            # Determine destination based on file type
            if "mazs_tazs" in local_name or "blocks_mazs" in local_name:
                dest_path = gis_dir / local_name
            elif "nhgis_" in local_name:
                dest_path = census_cache_dir / local_name
            elif "api-key" in local_name:
                dest_path = api_dir / local_name
            else:
                dest_path = local_input_dir / local_name
                
            # Copy the file
            shutil.copy2(network_path, dest_path)
            print(f"✓ Copied: {local_name}")
            copied_files.append(local_name)
            
        except Exception as e:
            print(f"✗ Failed to copy {local_name}: {e}")
            failed_files.append((local_name, network_path, str(e)))
    
    # Copy all census cache files (CSV files in the cache directory)
    cache_source = "M:\\Data\\Census\\NewCachedTablesForPopulationSimControls"
    if os.path.exists(cache_source):
        print(f"\nCopying census cache files from {cache_source}...")
        try:
            csv_files = glob.glob(os.path.join(cache_source, "*.csv"))
            for csv_file in csv_files:
                filename = os.path.basename(csv_file)
                dest_path = census_cache_dir / filename
                
                # Skip if already copied as part of crosswalk files
                if filename in [f for f in network_files.keys() if filename.endswith('.csv')]:
                    continue
                    
                try:
                    shutil.copy2(csv_file, dest_path)
                    copied_files.append(f"census_cache/{filename}")
                except Exception as e:
                    print(f"✗ Failed to copy cache file {filename}: {e}")
                    failed_files.append((f"census_cache/{filename}", csv_file, str(e)))
            
            print(f"✓ Copied {len(csv_files)} census cache files")
            
        except Exception as e:
            print(f"✗ Failed to access census cache directory: {e}")
    else:
        print(f"WARNING: Census cache directory not found: {cache_source}")
    
    # Summary
    print(f"\n=== COPY SUMMARY ===")
    print(f"Successfully copied: {len(copied_files)} files")
    print(f"Failed to copy: {len(failed_files)} files")
    
    if failed_files:
        print("\nFailed files:")
        for name, path, error in failed_files:
            print(f"  - {name}: {error}")
    
    # Create a status file to indicate successful copy
    status_file = local_input_dir / "copy_status.txt"
    with open(status_file, 'w') as f:
        f.write(f"Files copied on: {Path().cwd()}\n")
        f.write(f"Successfully copied: {len(copied_files)} files\n")
        f.write(f"Failed: {len(failed_files)} files\n")
        f.write("\nCopied files:\n")
        for file in copied_files:
            f.write(f"  - {file}\n")
        if failed_files:
            f.write("\nFailed files:\n")
            for name, path, error in failed_files:
                f.write(f"  - {name}: {error}\n")
    
    print(f"\nStatus saved to: {status_file}")
    return len(copied_files), len(failed_files)

if __name__ == "__main__":
    copied, failed = copy_network_files()
    if failed == 0:
        print("\n🎉 All files copied successfully!")
    else:
        print(f"\n⚠️  {failed} files failed to copy. Check the status file for details.")
