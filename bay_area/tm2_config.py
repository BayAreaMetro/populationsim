#!/usr/bin/env python3
"""
TM2 PopulationSim Configuration

Pure configuration - paths, settings, and project-specific variables only.
No utility methods - those are in tm2_utils.py
"""

import os
import json
from pathlib import Path

# Import centralized county configuration
try:
    from utils.config_census import (
        get_sequential_county_mapping,
        BAY_AREA_COUNTY_FIPS,
        get_county_names_list
    )
    COUNTY_MAPPING_AVAILABLE = True
except ImportError as e:
    COUNTY_MAPPING_AVAILABLE = False
    print(f"[CONFIG] WARNING: Could not import centralized county mapping: {e}")


class TM2Config:
    """Pure configuration - paths and settings only"""
    
    def __init__(self, year=2023, model_type="TM2", test_puma=None):
        # Core settings
        self.YEAR = year
        self.MODEL_TYPE = model_type
        self.TEST_PUMA = test_puma
        
        # Base directories
        self.BASE_DIR = Path(__file__).parent.absolute()
        self.OUTPUT_DIR = self.BASE_DIR / f"output_{self.YEAR}"
        self.SCRIPTS_DIR = self.BASE_DIR / "scripts"
        
        # PopulationSim working directories
        self.POPSIM_WORKING_DIR = self.OUTPUT_DIR / "populationsim_working_dir"
        self.POPSIM_DATA_DIR = self.POPSIM_WORKING_DIR / "data"
        self.POPSIM_CONFIG_DIR = self.POPSIM_WORKING_DIR / "configs"
        self.POPSIM_OUTPUT_DIR = self.POPSIM_WORKING_DIR / "output"
        
        # External network paths
        self.EXTERNAL_PATHS = {
            'census_cache': self.BASE_DIR / "data_cache" / "census",
            'network_census_cache': Path("M:/Data/Census/NewCachedTablesForPopulationSimControls"),
            'network_census_api': Path("M:/Data/Census/API/new_key"),
            'pums_current': Path("M:/Data/Census/PUMS_2023_5Year_Crosswalked"),
            'pums_cached': Path("M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23")
        }
        
        # File templates (naming patterns)
        self.FILE_TEMPLATES = {
            'households_raw': f"households_{self.YEAR}_raw.csv",
            'persons_raw': f"persons_{self.YEAR}_raw.csv",
            'households_processed': f"households_{self.YEAR}_{self.MODEL_TYPE.lower()}.csv",
            'persons_processed': f"persons_{self.YEAR}_{self.MODEL_TYPE.lower()}.csv",
            'seed_households': "seed_households.csv",
            'seed_persons': "seed_persons.csv",
            'pums_households': "bay_area_households_2019_2023_crosswalked.csv",
            'pums_persons': "bay_area_persons_2019_2023_crosswalked.csv",
            'maz_marginals': "maz_marginals_hhgq.csv",
            'taz_marginals': "taz_marginals_hhgq.csv",
            'county_marginals': "county_marginals.csv",
            'maz_data': "maz_data.csv",
            'geo_crosswalk_base': f"geo_cross_walk_{self.MODEL_TYPE.lower()}_maz.csv",
            'settings_yaml': "settings.yaml",
            'logging_yaml': "logging.yaml",
            'controls_csv': "controls.csv",
            'synthetic_households': "synthetic_households.csv",
            'synthetic_persons': "synthetic_persons.csv",
            'summary_melt': "summary_melt.csv",
        }
        
        # Specific file paths
        self.CROSSWALK_FILES = {
            'main': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['geo_crosswalk_base'],
            'enhanced': self.POPSIM_DATA_DIR / 'geo_cross_walk_tm2_block10.csv',
        }
        
        self.SEED_FILES = {
            'households_raw': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['households_raw'],
            'persons_raw': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['persons_raw'],
            'households': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['seed_households'],
            'persons': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['seed_persons']
        }
        
        self.PUMS_FILES = {
            'households_current': self.EXTERNAL_PATHS['pums_current'] / self.FILE_TEMPLATES['pums_households'],
            'persons_current': self.EXTERNAL_PATHS['pums_current'] / self.FILE_TEMPLATES['pums_persons'],
            'households_cached': self.EXTERNAL_PATHS['pums_cached'] / self.FILE_TEMPLATES['pums_households'],
            'persons_cached': self.EXTERNAL_PATHS['pums_cached'] / self.FILE_TEMPLATES['pums_persons']
        }
        
        self.CONTROL_FILES = {
            'maz_marginals': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['maz_marginals'],
            'taz_marginals': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['taz_marginals'],
            'county_marginals': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['county_marginals'],
            'maz_data': self.OUTPUT_DIR / self.FILE_TEMPLATES['maz_data']
        }
        
        self.POPSIM_CONFIG_FILES = {
            'settings': self.POPSIM_CONFIG_DIR / self.FILE_TEMPLATES['settings_yaml'],
            'logging': self.POPSIM_CONFIG_DIR / self.FILE_TEMPLATES['logging_yaml'],
            'controls': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['controls_csv']
        }
        
        self.POPSIM_OUTPUT_FILES = {
            'synthetic_households': self.POPSIM_OUTPUT_DIR / self.FILE_TEMPLATES['synthetic_households'],
            'synthetic_persons': self.POPSIM_OUTPUT_DIR / self.FILE_TEMPLATES['synthetic_persons'],
            'summary_melt': self.POPSIM_OUTPUT_DIR / self.FILE_TEMPLATES['summary_melt']
        }
        
        # Processing parameters
        self.PROCESSING_PARAMS = {
            'chunk_size': 50000,
            'random_seed': 42,
            'census_api_timeout': 300,
            'max_retries': 3
        }
        
        # PUMA resolution settings
        self.PUMA_RESOLUTION = {
            'enabled': True,
            'method': 'majority_rule',
            'verbose_logging': False,
            'manual_overrides': {5500: 7, 7513: 1}
        }
        
        # Force flags for workflow control
        self.FORCE_FLAGS = {
            'CROSSWALK': os.getenv('FORCE_CROSSWALK', 'True').lower() == 'true',
            'SEED': os.getenv('FORCE_SEED', 'True').lower() == 'true',
            'CONTROLS': os.getenv('FORCE_CONTROLS', 'True').lower() == 'true',
            'POPSIM': os.getenv('FORCE_POPSIM', 'True').lower() == 'true',
            'POSTPROCESS': os.getenv('FORCE_POSTPROCESS', 'True').lower() == 'true',
        }
        
        # Analysis scripts configuration
        self.ANALYSIS_FILES = {
            'main_scripts': {
                'maz_household_comparison': self.BASE_DIR / 'analysis' / 'MAZ_hh_comparison.py',
                'full_dataset': self.BASE_DIR / 'analysis' / 'analyze_full_dataset.py',
                'compare_controls_vs_results_by_taz': self.BASE_DIR / 'analysis' / 'compare_controls_vs_results_by_taz.py',
                'synthetic_population_analysis': self.BASE_DIR / 'analysis' / 'analyze_syn_pop_model.py',
            },
            'validation_scripts': {
                'maz_household_summary': self.BASE_DIR / 'analysis' / 'maz_household_summary.py',
                'compare_synthetic_populations': self.BASE_DIR / 'analysis' / 'compare_synthetic_populations.py',
                'data_validation': self.BASE_DIR / 'analysis' / 'data_validation.py',
            },
            'visualization_scripts': {
                'taz_controls_analysis': self.BASE_DIR / 'analysis' / 'analyze_taz_controls_vs_results.py',
                'county_analysis': self.BASE_DIR / 'analysis' / 'analyze_county_results.py',
                'interactive_taz_analysis': self.BASE_DIR / 'analysis' / 'create_interactive_taz_analysis.py',
            }
        }
        
        # Load data (counties, PUMAs, value labels)
        self.BAY_AREA_COUNTIES = get_sequential_county_mapping() if COUNTY_MAPPING_AVAILABLE else {}
        self._load_value_labels()
    
    def _load_value_labels(self):
        """Load value labels from external JSON file"""
        labels_file = self.BASE_DIR / "utils" / "census_value_labels.json"
        try:
            with open(labels_file, 'r') as f:
                labels_data = json.load(f)
            self.VALUE_LABELS = {}
            for var_name, mappings in labels_data.items():
                self.VALUE_LABELS[var_name] = {int(k): v for k, v in mappings.items()}
        except Exception as e:
            print(f"[CONFIG] WARNING: Could not load value labels: {e}")
            self.VALUE_LABELS = {}
    
    def get_test_puma_args(self):
        """Get command line arguments for TEST_PUMA if set"""
        return ["--test_PUMA", self.TEST_PUMA] if self.TEST_PUMA else []
    
    def get_puma_suffix(self):
        """Get PUMA suffix for file naming"""
        return f"_puma{self.TEST_PUMA}" if self.TEST_PUMA else ""
    
    def get_step_files(self, step_name):
        """Get expected output files for a pipeline step"""
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
    
    def get_command(self, step_name):
        """Get command for a pipeline step - delegates to TM2Utils"""
        # Import here to avoid circular dependency
        from utils.tm2_utils import TM2Utils
        utils = TM2Utils(self)
        return utils.get_workflow_commands().get(step_name, [])
    
    def get_fips_to_sequential_mapping(self):
        """Get mapping from FIPS codes to sequential county IDs (1-9)"""
        return {info['fips_int']: county_id for county_id, info in self.BAY_AREA_COUNTIES.items()}


# Create global configuration instance
config = TM2Config()
