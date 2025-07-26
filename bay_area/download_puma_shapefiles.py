#!/usr/bin/env python3
"""
Download 2020 PUMA shapefiles from Census Bureau
"""

import os
import requests
import zipfile
from pathlib import Path
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download_puma_shapefiles():
    """Download 2020 PUMA shapefiles for California"""
    
    print("="*80)
    print("DOWNLOADING 2020 PUMA SHAPEFILES FROM CENSUS BUREAU")
    print("="*80)
    
    # Target directory
    target_dir = "C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles"
    
    # Create directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    print(f"📁 Target directory: {target_dir}")
    
    # Census Bureau URL for 2020 PUMA shapefiles (California)
    # Using the TIGER/Line shapefiles for 2020 PUMA boundaries (puma20)
    puma_url = "https://www2.census.gov/geo/tiger/TIGER2022/PUMA/tl_2022_06_puma20.zip"
    
    print(f"🌐 Downloading from: {puma_url}")
    
    # Download the zip file
    zip_filename = "tl_2022_06_puma20.zip"
    zip_path = os.path.join(target_dir, zip_filename)
    
    try:
        print(f"⬇️  Downloading PUMA shapefile...")
        response = requests.get(puma_url, verify=False, timeout=300)
        response.raise_for_status()
        
        with open(zip_path, 'wb') as f:
            f.write(response.content)
            
        print(f"✅ Downloaded: {zip_path} ({len(response.content) / 1024 / 1024:.1f} MB)")
        
        # Extract the zip file
        print(f"📂 Extracting shapefile...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
            
        # List extracted files
        extracted_files = []
        for file in Path(target_dir).glob("tl_2022_06_puma20.*"):
            extracted_files.append(file.name)
            
        print(f"✅ Extracted files:")
        for file in sorted(extracted_files):
            print(f"   {file}")
            
        # Clean up zip file
        os.remove(zip_path)
        print(f"🗑️  Removed zip file: {zip_filename}")
        
        # Check for the main shapefile
        shapefile_path = os.path.join(target_dir, "tl_2022_06_puma20.shp")
        if os.path.exists(shapefile_path):
            print(f"\\n🎉 SUCCESS!")
            print(f"   PUMA shapefile ready: {shapefile_path}")
            return shapefile_path
        else:
            print(f"\\n❌ Shapefile not found after extraction")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Download failed: {e}")
        return None
    except zipfile.BadZipFile as e:
        print(f"❌ Zip extraction failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def download_alternative_puma_shapefiles():
    """Try alternative sources for 2020 PUMA shapefiles"""
    
    print("\\n🔄 Trying alternative download sources...")
    
    target_dir = "C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles"
    
    # Alternative URLs to try
    alternative_urls = [
        # 2020 PUMAs (most recent)
        "https://www2.census.gov/geo/tiger/TIGER2021/PUMA/tl_2021_06_puma10.zip",
        "https://www2.census.gov/geo/tiger/TIGER2022/PUMA/tl_2022_06_puma20.zip",
        # 2010 PUMAs (backup)
        "https://www2.census.gov/geo/tiger/TIGER2020/PUMA/tl_2020_06_puma10.zip"
    ]
    
    for i, url in enumerate(alternative_urls, 1):
        print(f"\\n🌐 Trying source {i}: {url}")
        
        try:
            filename = url.split('/')[-1]
            zip_path = os.path.join(target_dir, filename)
            
            response = requests.get(url, verify=False, timeout=300)
            response.raise_for_status()
            
            with open(zip_path, 'wb') as f:
                f.write(response.content)
                
            print(f"✅ Downloaded: {filename} ({len(response.content) / 1024 / 1024:.1f} MB)")
            
            # Extract
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
                
            # Check for shapefile
            base_name = filename.replace('.zip', '')
            shapefile_path = os.path.join(target_dir, f"{base_name}.shp")
            
            if os.path.exists(shapefile_path):
                os.remove(zip_path)  # Clean up
                print(f"✅ Success! Shapefile: {shapefile_path}")
                return shapefile_path
            else:
                os.remove(zip_path)  # Clean up
                print(f"❌ Shapefile not found after extraction")
                
        except Exception as e:
            print(f"❌ Failed: {e}")
            if os.path.exists(zip_path):
                os.remove(zip_path)
            continue
    
    print(f"\\n❌ All download attempts failed")
    return None

if __name__ == "__main__":
    # Try main download first
    shapefile = download_puma_shapefiles()
    
    # If main download fails, try alternatives
    if not shapefile:
        shapefile = download_alternative_puma_shapefiles()
    
    if shapefile:
        print(f"\\n🎯 READY TO PROCEED!")
        print(f"   Use this shapefile for crosswalk updates: {shapefile}")
    else:
        print(f"\\n📋 MANUAL DOWNLOAD REQUIRED:")
        print(f"   Please manually download 2020 PUMA shapefiles from:")
        print(f"   https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html")
        print(f"   Select: 2020 > Public Use Microdata Areas (PUMAs) > California")
        print(f"   Save to: C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/")
