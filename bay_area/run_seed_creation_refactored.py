#!/usr/bin/env python3
"""
Simple runner for refactored PopulationSim TM2 seed population creation

This demonstrates the improved modularity and ease of use.
"""

import sys
from pathlib import Path
import logging

# Import our refactored modules
from create_seed_population_tm2_refactored import SeedPopulationCreator, SeedPopulationConfig
from tm2_config_refactored import PopulationSimTM2Config

def main():
    """Run the refactored seed population creation"""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('seed_population_creation.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Validate configuration
        if not PopulationSimTM2Config.validate_config():
            logger.error("Configuration validation failed!")
            return 1
        
        # Create configuration object using our config file
        config = SeedPopulationConfig(
            bay_area_pumas=PopulationSimTM2Config.BAY_AREA_PUMAS,
            output_dir=PopulationSimTM2Config.OUTPUT_DIR,
            chunk_size=PopulationSimTM2Config.CHUNK_SIZE,
            random_seed=PopulationSimTM2Config.RANDOM_SEED
        )
        
        # Create the seed population
        logger.info("Starting PopulationSim TM2 seed population creation...")
        logger.info("=" * 70)
        
        creator = SeedPopulationCreator(config)
        success = creator.create_seed_population()
        
        if success:
            logger.info("✅ Seed population creation completed successfully!")
            
            # Show output files
            output_files = PopulationSimTM2Config.get_output_files()
            logger.info("\nOutput files created:")
            for desc, path in output_files.items():
                if path.exists():
                    size_mb = path.stat().st_size / (1024*1024)
                    logger.info(f"  {desc}: {path} ({size_mb:.1f} MB)")
            
            return 0
        else:
            logger.error("❌ Seed population creation failed!")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
