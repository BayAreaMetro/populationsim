#!/usr/bin/env python3
"""
Download PUMA Shapefiles for 2010 and 2020 Census

Downloads both 2010 and 2020 PUMA shapefiles for California to properly
handle the PUMA boundary changes between census periods.
"""

import requests
import zipfile
import logging
from pathlib import Path
import urllib3
import shutil

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PUMAShapefileDownloader:
    """Downloads PUMA shapefiles for both 2010 and 2020 Census"""
    
    def __init__(self, output_dir: str = "M:/Data/GIS/PUMA_Shapefiles"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
    def download_both_puma_shapefiles(self):
        """Download both 2010 and 2020 PUMA shapefiles"""
        
        logger.info("="*60)
        logger.info("DOWNLOADING PUMA SHAPEFILES FOR 2010 AND 2020")
        logger.info("="*60)
        
        # PUMA shapefile URLs
        puma_urls = {
            2010: {
                'url': 'https://www2.census.gov/geo/tiger/TIGER2010/PUMA5/2010/tl_2010_06_puma10.zip',
                'description': '2010 Census PUMA boundaries (used for 2019-2020 ACS data)'
            },
            2020: {
                'url': 'https://www2.census.gov/geo/tiger/TIGER2022/PUMA/tl_2022_06_puma20.zip', 
                'description': '2020 Census PUMA boundaries (used for 2021-2023 ACS data)'
            }
        }
        
        success_count = 0
        
        for year, info in puma_urls.items():
            logger.info(f"\n{'='*50}")
            logger.info(f"DOWNLOADING {year} PUMA SHAPEFILE")
            logger.info(f"{'='*50}")
            logger.info(f"Description: {info['description']}")
            logger.info(f"URL: {info['url']}")
            
            try:
                output_folder = self.output_dir / f"PUMA_{year}"
                success = self._download_shapefile(info['url'], output_folder, year)
                if success:
                    success_count += 1
                    logger.info(f"✅ Successfully downloaded {year} PUMA shapefile")
                else:
                    logger.error(f"❌ Failed to download {year} PUMA shapefile")
                    
            except Exception as e:
                logger.error(f"❌ Error downloading {year} PUMA shapefile: {e}")
                continue
        
        if success_count == 2:
            logger.info(f"\n{'='*60}")
            logger.info("✅ SUCCESS: Both PUMA shapefiles downloaded!")
            logger.info(f"{'='*60}")
            logger.info("Downloaded files:")
            logger.info(f"  2010 PUMAs: {self.output_dir / 'PUMA_2010'}")
            logger.info(f"  2020 PUMAs: {self.output_dir / 'PUMA_2020'}")
            logger.info("\nNext steps:")
            logger.info("1. Update crosswalk creator to use both PUMA shapefiles")
            logger.info("2. Create crosswalk with PUMA2010 and PUMA2020 columns")
            logger.info("3. Update PUMS downloader to use appropriate PUMA lists by year")
            return True
        else:
            logger.error(f"❌ Only {success_count}/2 shapefiles downloaded successfully")
            return False
    
    def _download_shapefile(self, url: str, output_folder: Path, year: int) -> bool:
        """Download and extract a single PUMA shapefile"""
        
        # Create output folder
        output_folder.mkdir(exist_ok=True, parents=True)
        
        # Download zip file
        zip_filename = f"puma_{year}_ca.zip"
        zip_path = output_folder / zip_filename
        
        logger.info(f"Downloading to: {zip_path}")
        
        try:
            response = requests.get(url, stream=True, verify=False)
            response.raise_for_status()
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded zip file: {zip_path}")
            
            # Extract zip file
            logger.info("Extracting shapefile...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(output_folder)
            
            # Find the shapefile
            shp_files = list(output_folder.glob("*.shp"))
            if not shp_files:
                logger.error("No .shp file found in extracted files")
                return False
            
            shp_file = shp_files[0]
            logger.info(f"Extracted shapefile: {shp_file}")
            
            # List all extracted files
            all_files = list(output_folder.glob("*"))
            shapefile_files = [f for f in all_files if f.suffix.lower() in ['.shp', '.shx', '.dbf', '.prj', '.cpg']]
            
            logger.info(f"Shapefile components found: {len(shapefile_files)}")
            for f in sorted(shapefile_files):
                logger.info(f"  {f.name}")
            
            # Clean up zip file
            zip_path.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return False
    
    def analyze_puma_shapefiles(self):
        """Analyze the downloaded PUMA shapefiles to extract PUMA lists"""
        
        logger.info(f"\n{'='*60}")
        logger.info("ANALYZING DOWNLOADED PUMA SHAPEFILES")
        logger.info(f"{'='*60}")
        
        try:
            import geopandas as gpd
        except ImportError:
            logger.error("GeoPandas not available - cannot analyze shapefiles")
            logger.info("Install with: conda install geopandas")
            return
        
        puma_data = {}
        
        for year in [2010, 2020]:
            shapefile_dir = self.output_dir / f"PUMA_{year}"
            shp_files = list(shapefile_dir.glob("*.shp"))
            
            if not shp_files:
                logger.warning(f"No shapefile found for {year}")
                continue
            
            shp_file = shp_files[0]
            logger.info(f"\nAnalyzing {year} PUMA shapefile: {shp_file}")
            
            try:
                # Load shapefile
                gdf = gpd.read_file(shp_file)
                logger.info(f"Loaded {len(gdf)} PUMA features")
                
                # Check columns
                logger.info(f"Columns: {list(gdf.columns)}")
                
                # Find PUMA ID column
                puma_col = None
                for col in gdf.columns:
                    if 'PUMA' in col.upper():
                        puma_col = col
                        break
                
                if puma_col:
                    puma_values = sorted(gdf[puma_col].astype(str).unique())
                    logger.info(f"PUMA column: {puma_col}")
                    logger.info(f"Number of PUMAs: {len(puma_values)}")
                    logger.info(f"PUMA values: {puma_values}")
                    
                    # Filter to Bay Area counties (state code 06, counties 01,13,41,55,75,81,85,95,97)
                    # This is a rough filter - we'd need county info to be more precise
                    bay_area_pumas = [p for p in puma_values if p.startswith('0')]  # CA PUMAs start with 0
                    logger.info(f"Potential Bay Area PUMAs: {len(bay_area_pumas)}")
                    logger.info(f"Sample Bay Area PUMAs: {bay_area_pumas[:20]}")
                    
                    puma_data[year] = {
                        'column': puma_col,
                        'all_pumas': puma_values,
                        'bay_area_pumas': bay_area_pumas
                    }
                
                else:
                    logger.warning(f"No PUMA column found in {year} shapefile")
                    
            except Exception as e:
                logger.error(f"Error analyzing {year} shapefile: {e}")
                continue
        
        # Save PUMA lists to files
        if puma_data:
            logger.info(f"\n{'='*50}")
            logger.info("SAVING PUMA LISTS")
            logger.info(f"{'='*50}")
            
            for year, data in puma_data.items():
                output_file = self.output_dir / f"bay_area_pumas_{year}.txt"
                with open(output_file, 'w') as f:
                    f.write(f"# Bay Area PUMAs - {year} Census definitions\n")
                    f.write(f"# Column name in shapefile: {data['column']}\n")
                    f.write(f"# Total PUMAs in CA: {len(data['all_pumas'])}\n")
                    f.write(f"# Potential Bay Area PUMAs: {len(data['bay_area_pumas'])}\n\n")
                    
                    # Write as Python list
                    f.write(f"BAY_AREA_PUMAS_{year} = [\n")
                    for i, puma in enumerate(data['bay_area_pumas']):
                        if i > 0 and i % 10 == 0:
                            f.write("\n    ")
                        f.write(f"'{puma}', ")
                    f.write("\n]\n")
                
                logger.info(f"Saved {year} PUMA list to: {output_file}")

def main():
    """Main execution"""
    logger.info("Starting PUMA shapefile download...")
    
    downloader = PUMAShapefileDownloader()
    
    # Download shapefiles
    success = downloader.download_both_puma_shapefiles()
    
    if success:
        # Analyze the shapefiles to extract PUMA lists
        downloader.analyze_puma_shapefiles()
        
        logger.info("\n✅ SUCCESS: PUMA shapefiles downloaded and analyzed!")
        logger.info("Review the generated PUMA lists and update your crosswalk creator.")
    else:
        logger.error("❌ FAILED: Could not download PUMA shapefiles")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
