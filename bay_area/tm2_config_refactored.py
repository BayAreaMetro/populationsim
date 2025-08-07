#!/usr/bin/env python3
"""
Configuration file for Bay Area PopulationSim TM2
"""

from pathlib import Path
from typing import List

class PopulationSimTM2Config:
    """Configuration for PopulationSim TM2 workflow"""
    
    # Data year
    DATA_YEAR = 2023
    
    # Output directories
    OUTPUT_DIR = Path("output_2023")
    
    # Script names (matching actual pipeline)
    SCRIPT_NAMES = {
        'create_seed_population': 'create_seed_population_tm2.py',
        'create_controls': 'create_baseyear_controls_23_tm2.py', 
        'add_hhgq': 'add_hhgq_combined_controls.py',
        'run_populationsim': 'run_populationsim.py',  # Correct script name
        'postprocess': 'postprocess_recode.py'
    }
    
    @classmethod
    def get_script_path(cls, script_name: str, base_dir: Path = None) -> Path:
        """Get full path to a script"""
        if base_dir is None:
            base_dir = Path.cwd()
        return base_dir / cls.SCRIPT_NAMES[script_name]
    
    # Bay Area PUMAs - 2020 definitions (62 PUMAs in modeling region)
    BAY_AREA_PUMAS = [
        # San Francisco County
        '00101', '00111', '00112', '00113', '00114', '00115', '00116', '00117', '00118', '00119',
        '00120', '00121', '00122', '00123',
        # Alameda County  
        '01301', '01305', '01308', '01309', '01310', '01311', '01312', '01313', '01314',
        # Contra Costa County
        '04103', '04104',
        # San Mateo County
        '05303', '05500',
        # Marin County
        '07507', '07508', '07509', '07510', '07511', '07512', '07513', '07514',
        # Santa Clara County
        '08101', '08102', '08103', '08104', '08105', '08106', '08505', '08506', '08507', 
        '08508', '08510', '08511', '08512', '08515', '08516', '08517', '08518', '08519', 
        '08520', '08521', '08522', '08701',
        # Sonoma County
        '09501', '09502', '09503',
        # Napa County
        '09702', '09704', '09705', '09706',
        # Solano County
        '11301'
    ]
    
    # PUMA to County mapping for TM2
    PUMA_COUNTY_MAPPING = {
        # San Francisco County (COUNTY=1)
        '00101': 1, '00111': 1, '00112': 1, '00113': 1, '00114': 1, '00115': 1, 
        '00116': 1, '00117': 1, '00118': 1, '00119': 1, '00120': 1, '00121': 1, 
        '00122': 1, '00123': 1,
        # San Mateo County (COUNTY=2)  
        '05303': 2, '05500': 2,
        # Santa Clara County (COUNTY=3)
        '08101': 3, '08102': 3, '08103': 3, '08104': 3, '08105': 3, '08106': 3,
        '08505': 3, '08506': 3, '08507': 3, '08508': 3, '08510': 3, '08511': 3,
        '08512': 3, '08515': 3, '08516': 3, '08517': 3, '08518': 3, '08519': 3,
        '08520': 3, '08521': 3, '08522': 3, '08701': 3,
        # Alameda County (COUNTY=4)
        '01301': 4, '01305': 4, '01308': 4, '01309': 4, '01310': 4, '01311': 4,
        '01312': 4, '01313': 4, '01314': 4,
        # Contra Costa County (COUNTY=5)
        '04103': 5, '04104': 5,
        # Solano County (COUNTY=6)
        '11301': 6,
        # Napa County (COUNTY=7)
        '09702': 7, '09704': 7, '09705': 7, '09706': 7,
        # Sonoma County (COUNTY=8)
        '09501': 8, '09502': 8, '09503': 8,
        # Marin County (COUNTY=9)
        '07507': 9, '07508': 9, '07509': 9, '07510': 9, '07511': 9, '07512': 9,
        '07513': 9, '07514': 9
    }
    
    # PopulationSim field mappings
    EMPLOYMENT_STATUS_MAPPING = {
        # ESR codes to employ_status
        1: 1,  # Civilian employed
        2: 1,  # Armed Forces
        3: 2,  # Unemployed
        4: 1,  # Armed Forces (not at work)
        5: 1,  # Civilian employed (not at work)
        6: 3   # Not in labor force
    }
    
    OCCUPATION_MAPPING = {
        # OCCP code ranges to occupation categories
        (10, 950): 1,      # Management
        (1005, 3540): 2,   # Professional
        (3601, 4650): 3,   # Services
        (4700, 5940): 4,   # Sales/Office
        (6005, 9750): 5,   # Manual
        (9800, 9830): 6    # Military
    }
    
    # Income conversion
    CPI_CONVERSION_FACTOR = 0.725  # 2023 to 2010 dollars
    
    # Group quarters targets (for random assignment)
    GQ_TARGETS = {
        'military': 1684,
        'other': 122467
    }
    
    # Processing parameters
    CHUNK_SIZE = 50000
    RANDOM_SEED = 42
    
    @classmethod
    def get_output_files(cls) -> dict:
        """Get standard output file paths"""
        base_dir = cls.OUTPUT_DIR
        return {
            'households_raw': base_dir / f"households_{cls.DATA_YEAR}_raw.csv",
            'persons_raw': base_dir / f"persons_{cls.DATA_YEAR}_raw.csv",
            'households_processed': base_dir / f"households_{cls.DATA_YEAR}_tm2.csv",
            'persons_processed': base_dir / f"persons_{cls.DATA_YEAR}_tm2.csv",
            'validation_report': base_dir / "data_validation_report.txt"
        }
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        # Check PUMA count
        if len(cls.BAY_AREA_PUMAS) != 62:
            print(f"WARNING: Expected 62 PUMAs, found {len(cls.BAY_AREA_PUMAS)}")
        
        # Check county mapping coverage
        mapped_pumas = set(cls.PUMA_COUNTY_MAPPING.keys())
        all_pumas = set(cls.BAY_AREA_PUMAS)
        unmapped = all_pumas - mapped_pumas
        
        if unmapped:
            print(f"ERROR: Unmapped PUMAs: {unmapped}")
            return False
        
        # Create output directory
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        
        return True

# Validate config on import
if __name__ == "__main__":
    if PopulationSimTM2Config.validate_config():
        print("Configuration validated successfully")
        print(f"Bay Area PUMAs: {len(PopulationSimTM2Config.BAY_AREA_PUMAS)}")
        print(f"Output directory: {PopulationSimTM2Config.OUTPUT_DIR}")
    else:
        print("Configuration validation failed!")
