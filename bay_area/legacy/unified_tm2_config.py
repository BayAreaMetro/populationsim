#!/usr/bin/env python3
"""
DEPRECATED: Use tm2_config.py and tm2_utils.py instead

This file is maintained for backward compatibility only.
New code should use:
  - tm2_config.py for configuration (paths, settings)
  - tm2_utils.py for utilities (helpers, file checks)
"""

# Import the new modules
from tm2_config import TM2Config
from utils.tm2_utils import TM2Utils

# Backward compatibility wrapper
class UnifiedTM2Config(TM2Config):
    """Backward compatibility wrapper - delegates to TM2Config and TM2Utils"""
    
    def __init__(self, year=2023, model_type="TM2"):
        super().__init__(year, model_type)
        self._utils = TM2Utils(self)
        
        # Load PUMAs for backward compatibility
        self.BAY_AREA_PUMAS = self._utils.load_pumas_from_crosswalk()
        
        # Ensure directories exist
        self._utils.create_directories()
        
        # Deprecated attributes maintained for compatibility
        self.SCRIPTS_DIR = self.BASE_DIR / "scripts"
        self.ACS_2010BINS_FILE = self.POPSIM_OUTPUT_DIR / f"bay_area_income_acs_{self.YEAR}_2010bins.csv"
        self.EXAMPLE_CONTROLS_DIR = self.BASE_DIR / "example_controls_2015"
        
        # Setup commands
        self.COMMANDS = self._utils.get_workflow_commands()
    
    # Delegate utility methods to TM2Utils
    def check_crosswalk_exists(self):
        return self._utils.check_crosswalk_exists()
    
    def check_seed_exists(self):
        return self._utils.check_seed_exists()
    
    def check_controls_exist(self):
        return self._utils.check_controls_exist()
    
    def check_popsim_output_exists(self):
        return self._utils.check_popsim_output_exists()
    
    def get_puma_to_county_mapping(self):
        return self._utils.generate_puma_to_county_mapping()
    
    def resolve_multi_county_pumas(self, crosswalk_df, verbose=False):
        return self._utils.resolve_multi_county_pumas(crosswalk_df, verbose)
    
    def get_workflow_status(self):
        return self._utils.get_workflow_status()
    
    def get_county_by_fips(self, fips_code):
        return self._utils.get_county_by_fips(fips_code)
    
    def get_county_by_name(self, name):
        return self._utils.get_county_by_name(name)
    
    def ensure_directories(self):
        return self._utils.create_directories()
    
    # Legacy property for backward compatibility
    @property
    def MAZ_TAZ_ALL_GEOG_FILE(self):
        return self.POPSIM_DATA_DIR / "geo_cross_walk_tm2_block10.csv"
    
    @property
    def SUMMARY_REPORT_FILE(self):
        return self.OUTPUT_DIR / "validation_summary.txt"
    
    def get_summary_file_path(self, name="validation_summary.txt"):
        return self.OUTPUT_DIR / name
    
    # Deprecated methods kept for compatibility
    def get_seed_paths(self):
        return {
            'crosswalk_file': self.CROSSWALK_FILES['main'],
            'output_dir': self.OUTPUT_DIR,
            'households_raw': self.SEED_FILES['households_raw'],
            'persons_raw': self.SEED_FILES['persons_raw'],
            'households_final': self.SEED_FILES['households'],
            'persons_final': self.SEED_FILES['persons']
        }
    
    def get_control_paths(self):
        return {
            'output_dir': self.OUTPUT_DIR,
            'maz_marginals': self.CONTROL_FILES['maz_marginals'],
            'taz_marginals': self.CONTROL_FILES['taz_marginals'],
            'county_marginals': self.CONTROL_FILES['county_marginals'],
            'maz_data': self.CONTROL_FILES['maz_data'],
            'crosswalk': self.CROSSWALK_FILES['main']
        }
    
    def get_external_paths(self):
        return self.EXTERNAL_PATHS
    
    def get_file_template(self, template_name):
        return self.FILE_TEMPLATES.get(template_name, template_name)
    
    def get_processing_params(self):
        return self.PROCESSING_PARAMS
    
    def get_puma_configuration(self):
        return {
            'bay_area_pumas': self.BAY_AREA_PUMAS,
            'test_puma': self.TEST_PUMA,
            'total_pumas': len(self.BAY_AREA_PUMAS)
        }
    
    def get_command(self, step_name):
        return self.COMMANDS.get(step_name, [])
    
    def sync_files_for_step(self, step_number):
        if step_number in [3, 4]:
            self._utils.sync_control_files()
    
    def check_hhgq_exists(self):
        # Simplified for backward compatibility
        return self.check_controls_exist()
    
    def check_postprocess_exists(self):
        return self.POPSIM_OUTPUT_FILES['summary_melt'].exists()
    
    def check_tableau_exists(self):
        tableau_dir = self.OUTPUT_DIR / "tableau"
        if not tableau_dir.exists():
            return False
        key_files = ['taz_marginals_hhgq.csv', 'maz_marginals_hhgq.csv', 'geo_cross_walk_tm2_maz.csv']
        return all((tableau_dir / f).exists() for f in key_files)
    
    def get_step_files(self, step_name):
        step_files = {
            'pums': [self.PUMS_FILES['households_current'], self.PUMS_FILES['persons_current']],
            'crosswalk': [self.CROSSWALK_FILES['main']],
            'seed': [self.SEED_FILES['households'], self.SEED_FILES['persons']],
            'controls': [
                self.CONTROL_FILES['maz_marginals'], 
                self.CONTROL_FILES['taz_marginals'], 
                self.CONTROL_FILES['county_marginals']
            ],
            'populationsim': [
                self.POPSIM_OUTPUT_DIR / "synthetic_households.csv",
                self.POPSIM_OUTPUT_DIR / "synthetic_persons.csv"
            ],
        }
        return step_files.get(step_name, [])
    
    def get_county_sequential_ids(self):
        return list(self.BAY_AREA_COUNTIES.keys())
    
    def get_county_fips_list(self):
        return [info['fips_int'] for info in self.BAY_AREA_COUNTIES.values()]
    
    def get_fips_to_sequential_mapping(self):
        return {info['fips_int']: county_id for county_id, info in self.BAY_AREA_COUNTIES.items()}


# Backward compatibility: maintain old import pattern


# Backward compatibility: maintain old import pattern
config = UnifiedTM2Config()

config = UnifiedTM2Config()



