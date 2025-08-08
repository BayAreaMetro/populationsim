#!/usr/bin/env python3
"""
Debug version of seed population creation with better monitoring

This version includes detailed progress monitoring and timeouts to identify
where the hanging might be occurring.
"""

import sys
import time
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('seed_creation_debug.log')
    ]
)
logger = logging.getLogger(__name__)

def check_existing_files():
    """Check if seed population files already exist"""
    output_dir = Path("output_2023")
    files_to_check = [
        "households_2023_raw.csv",
        "persons_2023_raw.csv", 
        "households_2023_tm2.csv",
        "persons_2023_tm2.csv"
    ]
    
    logger.info("Checking for existing files...")
    existing_files = []
    
    for file in files_to_check:
        file_path = output_dir / file
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            logger.info(f"  ✅ {file} exists ({size_mb:.1f} MB)")
            existing_files.append(file)
        else:
            logger.info(f"  ❌ {file} missing")
    
    return existing_files, files_to_check

def test_imports():
    """Test if all required imports work"""
    logger.info("Testing imports...")
    
    try:
        logger.info("  Testing pandas...")
        import pandas as pd
        logger.info("  ✅ pandas imported")
        
        logger.info("  Testing create_seed_population_tm2_refactored...")
        from create_seed_population_tm2_refactored import SeedPopulationConfig, SeedPopulationCreator
        logger.info("  ✅ SeedPopulationConfig and SeedPopulationCreator imported")
        
        logger.info("  Testing config creation...")
        config = SeedPopulationConfig()
        logger.info(f"  ✅ Config created with {len(config.bay_area_pumas)} PUMAs")
        
        logger.info("  Testing creator instantiation...")
        creator = SeedPopulationCreator(config)
        logger.info("  ✅ SeedPopulationCreator instantiated")
        
        return True, config, creator
        
    except Exception as e:
        logger.error(f"  ❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None

def test_pums_downloader():
    """Test the PUMS downloader separately"""
    logger.info("Testing PUMS downloader...")
    
    try:
        from pums_downloader import PUMSDownloader
        logger.info("  ✅ PUMSDownloader imported")
        
        # Test with just one PUMA to see if it hangs
        downloader = PUMSDownloader(year=2023, state="06")
        logger.info("  ✅ PUMSDownloader instantiated")
        
        # Test with minimal data
        test_pumas = ["00101"]  # Just Alameda PUMA 1
        logger.info(f"  Testing download with {test_pumas}")
        
        # Set a timeout to prevent hanging
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Download timed out after 60 seconds")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(60)  # 60 second timeout
        
        try:
            start_time = time.time()
            household_data, person_data = downloader.download_pums_data(
                test_pumas, 
                Path("output_2023")
            )
            elapsed = time.time() - start_time
            signal.alarm(0)  # Cancel timeout
            
            logger.info(f"  ✅ Test download completed in {elapsed:.1f} seconds")
            logger.info(f"  Downloaded {len(household_data)} households, {len(person_data)} persons")
            return True
            
        except TimeoutError:
            logger.error("  ❌ Download timed out - this is likely where the hang occurs")
            return False
        except Exception as e:
            signal.alarm(0)  # Cancel timeout
            logger.error(f"  ❌ Download error: {e}")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ PUMS downloader error: {e}")
        return False

def main():
    logger.info("=" * 60)
    logger.info("DEBUG SEED POPULATION CREATION")
    logger.info("=" * 60)
    
    # Step 1: Check existing files
    existing_files, all_files = check_existing_files()
    
    if len(existing_files) == len(all_files):
        logger.info("All files already exist - no need to recreate")
        return True
    
    # Step 2: Test imports
    imports_ok, config, creator = test_imports()
    if not imports_ok:
        return False
    
    # Step 3: Test PUMS downloader if raw files don't exist
    raw_files = ["households_2023_raw.csv", "persons_2023_raw.csv"]
    if not all(f in existing_files for f in raw_files):
        logger.info("Raw files missing - testing PUMS downloader...")
        downloader_ok = test_pums_downloader()
        if not downloader_ok:
            logger.error("PUMS downloader test failed - this is likely the hanging point")
            return False
    else:
        logger.info("Raw files exist - skipping downloader test")
    
    # Step 4: If we get here, try the full process
    logger.info("All tests passed - attempting full seed population creation...")
    
    try:
        success = creator.create_seed_population()
        if success:
            logger.info("✅ Seed population creation successful!")
            return True
        else:
            logger.error("❌ Seed population creation failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Seed population creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
