#!/usr/bin/env python3
# TODO: Some of the paths listed below are legacy fallbacks and are not required.
# We need to clean up this config to only include the required files and paths.
"""
Unified TM2 PopulationSim Configuration
Single source of truth for ALL paths, commands, and workflow logic
Eliminates ALL hardcoded values across the entire codebase!
"""

from pathlib import Path
import os
import sys

class UnifiedTM2Config:
    @property
    def SUMMARY_REPORT_FILE(self):
        """Standard summary report file path in output_2023 directory."""
        return self.OUTPUT_DIR / "validation_summary.txt"

    def get_summary_file_path(self, name="validation_summary.txt"):
        """Get a summary file path in the output_2023 directory (optionally override filename)."""
        return self.OUTPUT_DIR / name
    """Single configuration class that handles everything"""
    
    def __init__(self, year=2023, model_type="TM2"):
        # Base paths and main directories
        self.BASE_DIR = Path(__file__).parent.absolute()
        self.YEAR = year
        self.MODEL_TYPE = model_type
        self.PYTHON_EXE = Path(r"C:\Users\schildress\AppData\Local\anaconda3\envs\popsim\python.exe")

        if not self.PYTHON_EXE.exists():
            raise FileNotFoundError(f"PopulationSim Python environment not found at: {self.PYTHON_EXE}")
        self.OUTPUT_DIR = self.BASE_DIR / f"output_{self.YEAR}"
        self.SCRIPTS_DIR = self.BASE_DIR / "scripts"
        self.POPSIM_WORKING_DIR = self.OUTPUT_DIR / "populationsim_working_dir"
        self.POPSIM_DATA_DIR = self.POPSIM_WORKING_DIR / "data"
        self.POPSIM_CONFIG_DIR = self.POPSIM_WORKING_DIR / "configs"
        self.POPSIM_OUTPUT_DIR = self.POPSIM_WORKING_DIR / "output"
        self.ACS_2010BINS_FILE = self.POPSIM_OUTPUT_DIR / "bay_area_income_acs_2023_2010bins.csv"

        # Ensure all templates and paths are set up before defining COMMANDS
        self._setup_file_templates()
        self._setup_external_paths()
        self._setup_file_paths()

        # Set TEST_PUMA before any use in get_test_puma_args
        self.TEST_PUMA = None

        self.COMMANDS = {
            # Step 0: Crosswalk creation (MUST be first - seed generation needs it)
            'crosswalk': [
                [
                    "python",
                    str(self.BASE_DIR / "create_tm2_crosswalk.py"),
                    "--output", str(self.CROSSWALK_FILES['popsim_crosswalk'])
                ] + self.get_test_puma_args(),
                [
                    "python",
                    str(self.BASE_DIR / "build_complete_crosswalk.py")
                ]
            ],
            # Step 0.5: Geographic rebuild (rebuild complete crosswalk from Census blocks)
            'geographic_rebuild': [],  # Handled specially in pipeline - no external command needed
            # Step 1: PUMS data download (depends on crosswalk for PUMA filtering)
            'pums': [
                "python",
                str(self.BASE_DIR / "download_2023_5year_pums.py")
            ],
            # Step 2: Seed generation (depends on crosswalk and PUMS data)
            'seed': [
                "python",
                str(self.BASE_DIR / "create_seed_population_tm2_refactored.py"),
                "--year", str(self.YEAR),
                "--model_type", self.MODEL_TYPE
            ] + self.get_test_puma_args(),
            # Step 3: Control generation
            'controls': [
                "python",
                str(self.BASE_DIR / "create_baseyear_controls_23_tm2.py")
            ] + self.get_test_puma_args(),
            # Step 4: Group quarters integration
            'hhgq': [
                "python",
                str(self.BASE_DIR / "add_hhgq_combined_controls.py"), 
                "--model_type", self.MODEL_TYPE,
                "--input_dir", str(self.OUTPUT_DIR),
                "--output_dir", str(self.POPSIM_DATA_DIR)
            ] + self.get_test_puma_args(),
            # Step 5: PopulationSim synthesis
            'populationsim': [
                "python",
                str(self.BASE_DIR / "run_populationsim_synthesis.py"),
                "--working_dir", str(self.POPSIM_WORKING_DIR),
                "--output", str(self.POPSIM_OUTPUT_DIR)
            ] + self.get_test_puma_args(),
            # Step 6: Post-processing
            'postprocess': [
                "python",
                str(self.BASE_DIR / "postprocess_recode.py"),
                "--model_type", self.MODEL_TYPE,
                "--directory", str(self.POPSIM_OUTPUT_DIR),
                "--year", str(self.YEAR)
            ] + self.get_test_puma_args(),
            # Step 7: Tableau preparation
            'tableau': [
                "python",
                str(self.TABLEAU_FILES['script']),
                "--output_dir", str(self.TABLEAU_FILES['output_dir']),
                "--year", str(self.YEAR)
            ] + self.get_test_puma_args(),
            # Step 8: (analysis step removed; tm2_pipeline runs analysis scripts directly)
        }

        # ============================================================
        # PROCESSING PARAMETERS
        self.FORCE_FLAGS = {
            'CROSSWALK': os.getenv('FORCE_CROSSWALK', 'True').lower() == 'true',
            'SEED': os.getenv('FORCE_SEED', 'True').lower() == 'true',
            'CONTROLS': os.getenv('FORCE_CONTROLS', 'True').lower() == 'true',
            'HHGQ': os.getenv('FORCE_HHGQ', 'True').lower() == 'true',
            'POPSIM': os.getenv('FORCE_POPSIM', 'True').lower() == 'true',  # Default to True
            'POSTPROCESS': os.getenv('FORCE_POSTPROCESS', 'True').lower() == 'true',
            'TABLEAU': os.getenv('FORCE_TABLEAU', 'True').lower() == 'true'
        }

    def _setup_external_paths(self):
        """Setup external system paths"""
        self.EXTERNAL_PATHS = {
            # TM2PY utilities (for shapefiles and outputs)
            'tm2py_shapefiles': Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles"),
            'tm2py_utils': Path("C:/GitHub/tm2py-utils/tm2py_utils"),
            # Original populationsim_update path (used in some scripts)
            'populationsim_update': Path("c:/GitHub/populationsim_update/bay_area"),
            # Census data cache
            'census_cache': self.BASE_DIR / "data_cache" / "census",
            'network_gis': Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/mazs_TM2_2_5.shp"),
            'network_census_cache': Path("M:/Data/Census/NewCachedTablesForPopulationSimControls"),
            'network_census_api': Path("M:/Data/Census/API/new_key"),
            'pums_current': Path("M:/Data/Census/PUMS_2023_5Year_Crosswalked"),
            'pums_cached': Path("M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23"),
            # LEGACY: Local fallback paths - not required for config-driven runs
            #'local_data': self.BASE_DIR / "local_data",
            #'local_gis': self.BASE_DIR / "local_data" / "gis", 
            #'local_census': self.BASE_DIR / "local_data" / "census",
            #'input_2023_cache': self.BASE_DIR / "input_2023" / "NewCachedTablesForPopulationSimControls",
            # Shapefiles for geographic processing
            'maz_shapefile': Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/mazs_TM2_2_5.shp"),
            'puma_shapefile': Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/tl_2022_06_puma20.shp"),
            'county_shapefile': Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/Counties.shp"),
            # Geographic crosswalk source
            'blocks_file': Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/blocks_mazs_tazs_2.5.csv")
        }

        # ============================================================
        # SHAPEFILE PATHS
        # ============================================================
        self.SHAPEFILES = {
            'maz_shapefile': self.EXTERNAL_PATHS['tm2py_shapefiles'] / "mazs_TM2_2_5.shp",
            'taz_shapefile': self.EXTERNAL_PATHS['tm2py_shapefiles'] / "tazs_TM2_2_5.shp",
            'puma_shapefile': self.EXTERNAL_PATHS['tm2py_shapefiles'] / "tl_2022_06_puma20.shp",
            'county_shapefile': self.EXTERNAL_PATHS['tm2py_shapefiles'] / "Counties.shp"
        }
    
    def _setup_file_templates(self):
        """Setup file naming templates"""
        self.FILE_TEMPLATES = {
            # Seed files
            'households_raw': f"households_{self.YEAR}_raw.csv",
            'persons_raw': f"persons_{self.YEAR}_raw.csv", 
            'households_processed': f"households_{self.YEAR}_{self.MODEL_TYPE.lower()}.csv",
            'persons_processed': f"persons_{self.YEAR}_{self.MODEL_TYPE.lower()}.csv",
            'seed_households': "seed_households.csv",
            'seed_persons': "seed_persons.csv",
            
            # PUMS data files (downloaded from Census)
            'pums_households': "bay_area_households_2019_2023_crosswalked.csv",
            'pums_persons': "bay_area_persons_2019_2023_crosswalked.csv",
            
            # Control files
            'maz_marginals': "maz_marginals.csv",
            'taz_marginals': "taz_marginals.csv",
            'county_marginals': "county_marginals.csv",
            'maz_data': "maz_data.csv",
            'maz_data_density': "maz_data_withDensity.csv",
            
            # Example/reference files (contain employment/land use data to preserve)
            'example_maz_data': "maz_data.csv",
            'example_maz_density': "maz_data_withDensity.csv",
            
            # Crosswalk files
            'geo_crosswalk_base': f"geo_cross_walk_{self.MODEL_TYPE.lower()}.csv",
            
            # Group quarters files
            'maz_marginals_hhgq': "maz_marginals_hhgq.csv",
            'taz_marginals_hhgq': "taz_marginals_hhgq.csv",
            'taz_summaries_hhgq': "taz_summaries_hhgq.csv",  # For TM1
            
            # PopulationSim config files
            'settings_yaml': "settings.yaml",
            'logging_yaml': "logging.yaml",
            'controls_csv': "controls.csv",
            
            # PopulationSim output files
            'synthetic_households': "synthetic_households.csv",
            'synthetic_persons': "synthetic_persons.csv",
            'summary_melt': "summary_melt.csv",
            
            # Validation files
            'validation_workbook': "validation.twb"
        }
    
    def _create_directories(self):
        """Create all necessary directories"""
        dirs_to_create = [
            self.OUTPUT_DIR,
            self.POPSIM_WORKING_DIR,
            self.POPSIM_DATA_DIR,
            self.POPSIM_CONFIG_DIR,
            self.POPSIM_OUTPUT_DIR,
            self.OUTPUT_DIR / "tableau",
            self.EXTERNAL_PATHS['census_cache']
        ]
        
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _setup_file_paths(self):
        """Define ALL file paths in the system - no more confusion!"""
        
        # ============================================================
        # STEP 0: CROSSWALK FILES
        # ============================================================
        self.CROSSWALK_FILES = {
            # Primary crosswalk (PopulationSim expects this in data directory)
            'main_crosswalk': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['geo_crosswalk_base'],
            # PopulationSim default crosswalk (regular)
            'popsim_crosswalk': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['geo_crosswalk_base'],
            # Enhanced crosswalk (for controls step)
            'enhanced_crosswalk': self.POPSIM_DATA_DIR / 'geo_cross_walk_tm2_enhanced.csv',
        }
        
        # ============================================================
        # STEP 1: SEED POPULATION FILES - PopulationSim expects these in data directory
        # ============================================================
        self.SEED_FILES = {
            # Raw downloaded files (temporary processing in data directory)
            'households_raw': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['households_raw'],
            'persons_raw': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['persons_raw'],
            # Final seed files (PopulationSim data directory) - used directly by PopulationSim
            'households': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['seed_households'], 
            'persons': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['seed_persons']
        }
        
        # ============================================================
        # STEP 1B: PUMS DATA FILES (Raw Census downloads)
        # ============================================================
        self.PUMS_FILES = {
            # Primary locations (current pipeline use from M: drive)
            'households_current': self.EXTERNAL_PATHS['pums_current'] / self.FILE_TEMPLATES['pums_households'],
            'persons_current': self.EXTERNAL_PATHS['pums_current'] / self.FILE_TEMPLATES['pums_persons'],
            # Cached backup locations (for long-term storage)
            'households_cached': self.EXTERNAL_PATHS['pums_cached'] / self.FILE_TEMPLATES['pums_households'],
            'persons_cached': self.EXTERNAL_PATHS['pums_cached'] / self.FILE_TEMPLATES['pums_persons']
        }
        
        # ============================================================
        # STEP 2: CONTROL FILES - PopulationSim expects these in data directory  
        # ============================================================
        self.CONTROL_FILES = {
            # Generated control files (PopulationSim data directory)
            'maz_marginals_main': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['maz_marginals'],
            'taz_marginals_main': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['taz_marginals'], 
            'county_marginals_main': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['county_marginals'],
            'maz_data_main': self.OUTPUT_DIR / self.FILE_TEMPLATES['maz_data'],  # Keep convenience copies in main output
            'maz_data_density_main': self.OUTPUT_DIR / self.FILE_TEMPLATES['maz_data_density'],
            
            # PopulationSim files (same location now)
            'maz_marginals_popsim': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['maz_marginals'],
            'taz_marginals_popsim': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['taz_marginals'],
            'county_marginals_popsim': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['county_marginals'],
            'maz_data_popsim': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['maz_data_density']  # PopulationSim uses the density version
        }
        
        # ============================================================
        # STEP 3: GROUP QUARTERS FILES
        # ============================================================
        self.HHGQ_FILES = {
            # Group quarters integrated files (what PopulationSim needs)
            'maz_marginals_hhgq': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['maz_marginals_hhgq'],
            'taz_marginals_hhgq': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['taz_marginals_hhgq'],
            'taz_summaries_hhgq': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['taz_summaries_hhgq']  # For TM1
        }
        
        # ============================================================
        # STEP 4: POPULATIONSIM CONFIGURATION
        # ============================================================
        self.POPSIM_CONFIG_FILES = {
            'settings': self.POPSIM_CONFIG_DIR / self.FILE_TEMPLATES['settings_yaml'],
            'logging': self.POPSIM_CONFIG_DIR / self.FILE_TEMPLATES['logging_yaml'], 
            'controls': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['controls_csv']
        }
        
        # ============================================================
        # STEP 4: POPULATIONSIM OUTPUT FILES
        # ============================================================
        self.POPSIM_OUTPUT_FILES = {
            'synthetic_households': self.POPSIM_OUTPUT_DIR / self.FILE_TEMPLATES['synthetic_households'],
            'synthetic_persons': self.POPSIM_OUTPUT_DIR / self.FILE_TEMPLATES['synthetic_persons'],
            'summary_melt': self.POPSIM_OUTPUT_DIR / self.FILE_TEMPLATES['summary_melt']
        }
        
        # ============================================================
        # STEP 5: POST-PROCESSING FILES
        # ============================================================
        self.POSTPROCESS_FILES = {
            'validation_workbook_src': self.BASE_DIR / self.FILE_TEMPLATES['validation_workbook'],
            'validation_workbook_dst': self.OUTPUT_DIR / self.FILE_TEMPLATES['validation_workbook']
        }
        
        # ============================================================
        # STEP 6: TABLEAU FILES
        # ============================================================
        self.TABLEAU_FILES = {
            'output_dir': self.OUTPUT_DIR / "tableau",
            'script': self.BASE_DIR / "prepare_tableau_data.py"
        }
        
        # ============================================================
        # STEP 7: COMPREHENSIVE ANALYSIS FILES
        # ============================================================
        self.ANALYSIS_FILES = {
            # Main analysis outputs
            'full_analysis': self.OUTPUT_DIR / "FULL_DATASET_ANALYSIS.md",


            # Analysis scripts (organized by category)
            'scripts_dir': self.BASE_DIR / "analysis",
            'main_scripts': {
                'performance_summary': self.BASE_DIR / "analysis" / "analyze_corrected_populationsim_performance.py",
                'full_dataset': self.BASE_DIR / "analysis" / "analyze_full_dataset.py",
                'compare_controls_vs_results_by_taz': self.BASE_DIR / "analysis" / "compare_controls_vs_results_by_taz.py"
            },

            'validation_scripts': {
                # 'data_validation': self.BASE_DIR / "analysis" / "data_validation.py"
            },

            'check_scripts': {
                # 'taz_controls_rollup': self.BASE_DIR / "analysis" / "check_taz_controls_rollup.py",
                # (Removed as requested)
            },

            'visualization_scripts': {
                #'taz_puma_mapping': self.BASE_DIR / "analysis" / "visualize_taz_puma_mapping.py",
              
            }
        }
    
    def _setup_commands(self):
        """Define ALL commands in the system"""
        
        self.COMMANDS = {
            # Step 0: Crosswalk creation (MUST be first - seed generation needs it)
            'crosswalk': [
                [
                    "python",
                    str(self.BASE_DIR / "create_tm2_crosswalk.py"),
                    "--output", str(self.CROSSWALK_FILES['popsim_crosswalk'])
                ] + self.get_test_puma_args(),
                [
                    "python",
                    str(self.BASE_DIR / "build_complete_crosswalk.py")
                ]
            ],
            
            # Step 0.5: Geographic rebuild (rebuild complete crosswalk from Census blocks)
            'geographic_rebuild': [],  # Handled specially in pipeline - no external command needed
            
            # Step 1: PUMS data download (depends on crosswalk for PUMA filtering)
            'pums': [
                "python",
                str(self.BASE_DIR / "download_2023_5year_pums.py")
            ],
            
            # Step 2: Seed generation (depends on crosswalk and PUMS data)
            'seed': [
                "python",
                str(self.BASE_DIR / "create_seed_population_tm2_refactored.py"),
                "--year", str(self.YEAR),
                "--model_type", self.MODEL_TYPE
            ] + self.get_test_puma_args(),
            
            # Step 3: Control generation
            'controls': [
                "python",
                str(self.BASE_DIR / "create_baseyear_controls_23_tm2.py")
            ] + self.get_test_puma_args(),
            
            # Step 4: Group quarters integration
            'hhgq': [
                "python",
                str(self.BASE_DIR / "add_hhgq_combined_controls.py"), 
                "--model_type", self.MODEL_TYPE,
                "--input_dir", str(self.OUTPUT_DIR),
                "--output_dir", str(self.POPSIM_DATA_DIR)
            ] + self.get_test_puma_args(),
            
            # Step 5: PopulationSim synthesis
            'populationsim': [
                "python",
                str(self.BASE_DIR / "run_populationsim_synthesis.py"),
                "--working_dir", str(self.POPSIM_WORKING_DIR),
                "--output", str(self.POPSIM_OUTPUT_DIR)
            ] + self.get_test_puma_args(),
            
            # Step 6: Post-processing
            'postprocess': [
                "python",
                str(self.BASE_DIR / "postprocess_recode.py"),
                "--model_type", self.MODEL_TYPE,
                "--directory", str(self.POPSIM_OUTPUT_DIR),
                "--year", str(self.YEAR)
            ] + self.get_test_puma_args(),
            
            # Step 7: Tableau preparation
            'tableau': [
                "python",
                str(self.TABLEAU_FILES['script']),
                "--output_dir", str(self.TABLEAU_FILES['output_dir']),
                "--year", str(self.YEAR)
            ] + self.get_test_puma_args(),
            
            # Step 8: Comprehensive Analysis and Validation
            'analysis': [
                "python",
                str(self.BASE_DIR / "run_comprehensive_analysis.py"),
                "--output_dir", str(self.OUTPUT_DIR),
                "--year", str(self.YEAR)
            ],

            # Step 9: Old vs New Synthetic Population Comparison
            'compare_synthetic_populations': [
                "python",
                str(self.BASE_DIR / "compare_synthetic_populations.py")
            ]

        }
    
    # ============================================================
    # HELPER METHODS FOR SCRIPT INTEGRATION
    # ============================================================
    
    def get_crosswalk_paths(self):
        """Get paths for crosswalk generation scripts"""
        return {
            'maz_shapefile': self.SHAPEFILES['maz_shapefile'],
            'puma_shapefile': self.SHAPEFILES['puma_shapefile'], 
            'output_primary': self.CROSSWALK_FILES['popsim_crosswalk'],
            'output_reference': self.CROSSWALK_FILES['main_crosswalk']
        }
    
    def get_seed_paths(self):
        """Get paths for seed generation scripts"""
        return {
            'crosswalk_file': self.CROSSWALK_FILES['popsim_crosswalk'],
            'output_dir': self.OUTPUT_DIR,
            'households_raw': self.SEED_FILES['households_raw'],
            'persons_raw': self.SEED_FILES['persons_raw'],
            'households_processed': self.SEED_FILES['households_processed'],
            'persons_processed': self.SEED_FILES['persons_processed'],
            'households_final': self.SEED_FILES['households'],
            'persons_final': self.SEED_FILES['persons']
        }
    
    def get_control_paths(self):
        """Get paths for control generation scripts"""
        return {
            'output_dir': self.OUTPUT_DIR,
            'maz_marginals': self.CONTROL_FILES['maz_marginals_main'],
            'taz_marginals': self.CONTROL_FILES['taz_marginals_main'],
            'county_marginals': self.CONTROL_FILES['county_marginals_main'],
            'maz_data': self.CONTROL_FILES['maz_data_main'],
            'maz_data_density': self.CONTROL_FILES['maz_data_density_main'],
            'crosswalk': self.CROSSWALK_FILES['main_crosswalk']
        }
    
    def get_hhgq_paths(self):
        """Get paths for group quarters integration"""
        return {
            'input_dir': self.OUTPUT_DIR,
            'output_dir': self.POPSIM_DATA_DIR,
            'maz_marginals_in': self.CONTROL_FILES['maz_marginals_main'],
            'taz_marginals_in': self.CONTROL_FILES['taz_marginals_main'],
            'county_marginals_in': self.CONTROL_FILES['county_marginals_main'],
            'maz_marginals_out': self.HHGQ_FILES['maz_marginals_hhgq'],
            'taz_marginals_out': self.HHGQ_FILES['taz_marginals_hhgq']
        }
    
    def get_external_paths(self):
        """Get external system paths for scripts that need them"""
        return self.EXTERNAL_PATHS
    
    @property
    def TM2PY_UTILS_BLOCKS_FILE(self):
        """Get path to TM2PY utils blocks file for geographic rebuild"""
        return self.EXTERNAL_PATHS['blocks_file']
    
    def get_file_template(self, template_name):
        """Get a specific file template"""
        return self.FILE_TEMPLATES.get(template_name, template_name)
    
    def get_processing_params(self):
        """Get processing parameters"""
        return self.PROCESSING_PARAMS
    
    def get_script_paths(self):
        """Get paths to all workflow scripts"""
        return {
            'crosswalk': self.BASE_DIR / "create_tm2_crosswalk.py",
            'seed': self.BASE_DIR / "create_seed_population_tm2_refactored.py",
            'controls': self.BASE_DIR / "create_baseyear_controls_23_tm2.py",
            'hhgq': self.BASE_DIR / "add_hhgq_combined_controls.py",
            'populationsim': self.BASE_DIR / "run_populationsim_synthesis.py",
            'postprocess': self.BASE_DIR / "postprocess_recode.py",
            'tableau': self.BASE_DIR / "prepare_tableau_data.py",
            'cpi_conversion': self.BASE_DIR / "cpi_conversion.py"
        }
    
    def get_gis_files_with_fallback(self):
        """Get GIS file paths with network/local fallback logic"""
        paths = {}
        
        # MAZ/TAZ definition file
        if self.GIS_FILES['maz_taz_def_network'].exists():
            paths['maz_taz_def'] = self.GIS_FILES['maz_taz_def_network']
        else:
            paths['maz_taz_def'] = self.GIS_FILES['maz_taz_def_local']
        
        # MAZ/TAZ all geography file  
        if self.GIS_FILES['maz_taz_all_geog_network'].exists():
            paths['maz_taz_all_geog'] = self.GIS_FILES['maz_taz_all_geog_network']
        else:
            paths['maz_taz_all_geog'] = self.GIS_FILES['maz_taz_all_geog_local']
        
        return paths
    
    def get_census_api_key_path(self):
        """Get Census API key path with network/local fallback"""
        if self.GIS_FILES['census_api_key_network'].exists():
            return self.GIS_FILES['census_api_key_network']
        else:
            return self.GIS_FILES['census_api_key_local']
    
    def get_cache_dir_with_fallback(self):
        """Get cache directory with fallback logic"""
        # Try network cache first
        if self.CACHE_DIRS['network_cache'].exists():
            return self.CACHE_DIRS['network_cache']
        # Try input_2023 cache
        elif self.CACHE_DIRS['input_2023_cache'].exists():
            return self.CACHE_DIRS['input_2023_cache']
        # Fall back to local cache
        else:
            # Create local cache if it doesn't exist
            self.CACHE_DIRS['local_cache'].mkdir(parents=True, exist_ok=True)
            return self.CACHE_DIRS['local_cache']
    
    def get_puma_configuration(self):
        """Get PUMA configuration for scripts"""
        return {
            'bay_area_pumas': self.BAY_AREA_PUMAS,
            'test_puma': self.TEST_PUMA,
            'total_pumas': len(self.BAY_AREA_PUMAS)
        }
    
    def get_test_puma_args(self):
        """Get TEST_PUMA command line arguments if set"""
        if self.TEST_PUMA:
            return ["--test_PUMA", self.TEST_PUMA]
        else:
            return []
    
    def get_puma_suffix(self):
        """Get PUMA suffix for file naming"""
        if self.TEST_PUMA:
            return f"_puma{self.TEST_PUMA}"
        else:
            return ""

    # ============================================================
    # FILE EXISTENCE CHECKS
    # ============================================================

    def check_crosswalk_exists(self):
        """Check if crosswalk files exist"""
        return self.CROSSWALK_FILES['main_crosswalk'].exists()
    
    def check_seed_exists(self):
        """Check if seed files exist"""
        return (self.SEED_FILES['households'].exists() and 
                self.SEED_FILES['persons'].exists())
    
    def check_controls_exist(self):
        """Check if control files exist"""
        return (self.CONTROL_FILES['maz_marginals_main'].exists() and
                self.CONTROL_FILES['taz_marginals_main'].exists() and 
                self.CONTROL_FILES['county_marginals_main'].exists())
    
    def check_hhgq_exists(self):
        """Check if group quarters files exist"""
        return (self.HHGQ_FILES['maz_marginals_hhgq'].exists() and
                self.HHGQ_FILES['taz_marginals_hhgq'].exists())
    
    def check_popsim_output_exists(self):
        """Check if PopulationSim output exists"""
        return (self.POPSIM_OUTPUT_FILES['synthetic_households'].exists() and
                self.POPSIM_OUTPUT_FILES['synthetic_persons'].exists())
    
    def check_postprocess_exists(self):
        """Check if post-processing output exists"""
        return self.POPSIM_OUTPUT_FILES['summary_melt'].exists()
    
    def check_tableau_exists(self):
        """Check if Tableau files exist"""
        tableau_dir = self.TABLEAU_FILES['output_dir']
        if not tableau_dir.exists():
            return False
        # Check for key tableau files
        key_files = ['taz_marginals.csv', 'maz_marginals.csv', 'geo_crosswalk.csv']
        return all((tableau_dir / f).exists() for f in key_files)
    
    # ============================================================
    # FILE SYNCHRONIZATION (SMART COPYING)
    # ============================================================
    
    def sync_files_for_step(self, step_number):
        """Intelligently sync files needed for a specific step"""
        import shutil
        
        if step_number == 3:  # Group quarters step needs control files
            self._sync_control_files()
        elif step_number == 4:  # PopulationSim needs everything
            self._sync_all_popsim_files()
    
    def _sync_control_files(self):
        """Copy control files from output_2023 to PopulationSim data directory"""
        import shutil
        
        mappings = [
            (self.CONTROL_FILES['maz_marginals_main'], self.CONTROL_FILES['maz_marginals_popsim']),
            (self.CONTROL_FILES['taz_marginals_main'], self.CONTROL_FILES['taz_marginals_popsim']),
            (self.CONTROL_FILES['county_marginals_main'], self.CONTROL_FILES['county_marginals_popsim']),
            (self.CONTROL_FILES['maz_data_density_main'], self.CONTROL_FILES['maz_data_popsim']),
            (self.CROSSWALK_FILES['main_crosswalk'], self.CROSSWALK_FILES['popsim_crosswalk'])
        ]
        
        for src, dst in mappings:
            if src.exists():
                shutil.copy2(src, dst)
                print(f"Synced: {src.name} -> {dst}")
            elif dst.exists():
                print(f"Using existing: {dst.name} (source {src.name} not found)")
            else:
                print(f"WARNING: Missing source file: {src}")
                
        # Special handling for files that are already in working dir
        if not self.CONTROL_FILES['maz_data_density_main'].exists():
            if self.CONTROL_FILES['maz_data_popsim'].exists():
                print(f"Using existing: {self.CONTROL_FILES['maz_data_popsim'].name}")
            else:
                print(f"WARNING: Missing maz_data_withDensity.csv in both locations")
    
    def _sync_all_popsim_files(self):
        """Sync all files needed for PopulationSim"""
        import shutil
        
        # First sync control files
        self._sync_control_files()
        
        # Seed files are already in the correct PopulationSim data directory
        # No additional syncing needed since SEED_FILES point directly to POPSIM_DATA_DIR
    
    # ============================================================
    # WORKFLOW STATUS
    # ============================================================
    
    def get_workflow_status(self):
        """Get complete workflow status"""
        status = {
            'crosswalk': self.check_crosswalk_exists(),
            'seed': self.check_seed_exists(), 
            'controls': self.check_controls_exist(),
            'hhgq': self.check_hhgq_exists(),
            'popsim': self.check_popsim_output_exists(),
            'postprocess': self.check_postprocess_exists(),
            'tableau': self.check_tableau_exists()
        }
        
        # Determine what steps need to run
        steps_needed = []
        if self.FORCE_FLAGS['CROSSWALK'] or not status['crosswalk']:
            steps_needed.append(0)
        if self.FORCE_FLAGS['SEED'] or not status['seed']:
            steps_needed.append(1)
        if self.FORCE_FLAGS['CONTROLS'] or not status['controls']:
            steps_needed.append(2)
        if self.FORCE_FLAGS['HHGQ'] or not status['hhgq']:
            steps_needed.append(3)
        if self.FORCE_FLAGS['POPSIM'] or not status['popsim']:
            steps_needed.append(4)
        if self.FORCE_FLAGS['POSTPROCESS'] or not status['postprocess']:
            steps_needed.append(5)
        if self.FORCE_FLAGS['TABLEAU'] or not status['tableau']:
            steps_needed.append(6)
        
        return status, steps_needed
    
    def get_command(self, step_name):
        """Get command for a specific step"""
        return self.COMMANDS.get(step_name, [])
    
    def ensure_directories(self):
        """Create all necessary directories"""
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        self.POPSIM_WORKING_DIR.mkdir(parents=True, exist_ok=True)
        self.POPSIM_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.POPSIM_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.POPSIM_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create M: drive directories if they don't exist and are accessible
        for path_key in ['pums_current', 'pums_cached']:
            path = self.EXTERNAL_PATHS[path_key]
            try:
                path.mkdir(parents=True, exist_ok=True)
            except (FileNotFoundError, OSError) as e:
                # M: drive not accessible, skip creating these directories
                print(f"[CONFIG] WARNING: Cannot create {path_key} directory (M: drive not accessible): {path}")
                continue
    
    def get_step_files(self, step_name):
        """Get the files that should exist after a step completes"""
        step_files = {
            'pums': [
                self.PUMS_FILES['households_current'],
                self.PUMS_FILES['persons_current']
            ],
            'crosswalk': [self.CROSSWALK_FILES['main_crosswalk']],
            'geographic_rebuild': [self.POPSIM_DATA_DIR / "mazs_tazs_all_geog.csv"],
            'seed': [self.SEED_FILES['households'], self.SEED_FILES['persons']],
            'controls': [
                self.CONTROL_FILES['maz_marginals_main'],
                self.CONTROL_FILES['taz_marginals_main'],
                self.CONTROL_FILES['county_marginals_main']
            ],
            'populationsim': [
                self.POPSIM_OUTPUT_DIR / "synthetic_households.csv",
                self.POPSIM_OUTPUT_DIR / "synthetic_persons.csv"
            ],
            'postprocess': [
                self.POPSIM_OUTPUT_DIR / "summary_melt.csv",
                self.POPSIM_OUTPUT_DIR / f"households_{self.YEAR}_tm2.csv",
                self.POPSIM_OUTPUT_DIR / f"persons_{self.YEAR}_tm2.csv"
            ],
            'analysis': [
                # Main analysis outputs (if they exist)
                self.ANALYSIS_FILES.get('full_analysis'),
                # All main_scripts
                *self.ANALYSIS_FILES.get('main_scripts', {}).values(),
                # All validation_scripts
                *self.ANALYSIS_FILES.get('validation_scripts', {}).values(),
                # All check_scripts
                *self.ANALYSIS_FILES.get('check_scripts', {}).values(),
                # All visualization_scripts
                *self.ANALYSIS_FILES.get('visualization_scripts', {}).values(),
                # Standard summary and chart outputs
                self.OUTPUT_DIR / "validation_summary.txt",
                self.OUTPUT_DIR / "control_checks_summary.txt",
                self.OUTPUT_DIR / "populationsim_analysis_charts.html"
            ]
        }
        # Remove any None values (e.g., if check_scripts is empty)
        files = step_files.get(step_name, [])
        return [f for f in files if f is not None]
    
    # ============================================================
    # COUNTY LOOKUP HELPER METHODS
    # ============================================================
    def get_county_by_fips(self, fips_code):
        """Get county info by FIPS code (int or str)"""
        fips_int = int(str(fips_code).lstrip('0')) if fips_code else None
        for county_id, info in self.BAY_AREA_COUNTIES.items():
            if info['fips_int'] == fips_int:
                return county_id, info
        return None, None
    
    def get_county_by_name(self, name):
        """Get county info by name"""
        for county_id, info in self.BAY_AREA_COUNTIES.items():
            if info['name'].lower() == name.lower():
                return county_id, info
        return None, None
    
    def get_county_sequential_ids(self):
        """Get list of sequential county IDs (1-9)"""
        return list(self.BAY_AREA_COUNTIES.keys())
    
    def get_county_fips_list(self):
        """Get list of FIPS codes as integers"""
        return [info['fips_int'] for info in self.BAY_AREA_COUNTIES.values()]
    
    def get_fips_to_sequential_mapping(self):
        """Get FIPS code to sequential county ID mapping"""
        return {info['fips_int']: county_id for county_id, info in self.BAY_AREA_COUNTIES.items()}
    
    def resolve_multi_county_pumas(self, crosswalk_df, verbose=True):
        """
        Resolve PUMAs that span multiple counties using configurable rules
        
        Args:
            crosswalk_df: DataFrame with MAZ, TAZ, PUMA, COUNTY columns
            verbose: Whether to print detailed logging
            
        Returns:
            DataFrame with resolved county assignments
        """
        if not self.PUMA_RESOLUTION['enabled']:
            if verbose:
                print("Multi-county PUMA resolution is disabled in config")
            return crosswalk_df
        
        if verbose:
            print(f"\nStep 6: Resolving multi-county PUMAs...")
            print(f"  Method: {self.PUMA_RESOLUTION['method']}")
            print(f"  Threshold: {self.PUMA_RESOLUTION['min_threshold_pct']}%")
        
        # Create a copy to modify
        resolved_df = crosswalk_df.copy()
        
        # Find PUMAs that span multiple counties
        puma_county_counts = resolved_df.groupby('PUMA')['COUNTY'].nunique()
        multi_county_pumas = puma_county_counts[puma_county_counts > 1].index.tolist()
        
        if not multi_county_pumas:
            if verbose:
                print("  No multi-county PUMAs found - no resolution needed")
            return resolved_df
        
        if verbose:
            print(f"  Found {len(multi_county_pumas)} PUMAs spanning multiple counties:")
        
        total_reassigned = 0
        
        for puma in multi_county_pumas:
            puma_data = resolved_df[resolved_df['PUMA'] == puma]
            county_counts = puma_data['COUNTY'].value_counts()
            
            if verbose:
                print(f"\n    PUMA {puma}: {len(puma_data)} zones")
                for county, count in county_counts.items():
                    pct = (count / len(puma_data)) * 100
                    county_name = self.BAY_AREA_COUNTIES.get(county, {}).get('name', 'Unknown')
                    print(f"      County {county} ({county_name}): {count} zones ({pct:.1f}%)")
            
            # Determine target county
            target_county = None
            
            if puma in self.PUMA_RESOLUTION['manual_overrides']:
                # Use manual override
                target_county = self.PUMA_RESOLUTION['manual_overrides'][puma]
                method_used = "manual override"
            elif self.PUMA_RESOLUTION['method'] == 'majority_rule':
                # Use majority rule
                target_county = county_counts.index[0]  # Most frequent county
                method_used = "majority rule"
            
            if target_county:
                # Identify zones to reassign (those NOT in target county)
                reassign_mask = (resolved_df['PUMA'] == puma) & (resolved_df['COUNTY'] != target_county)
                zones_to_reassign = reassign_mask.sum()
                
                if zones_to_reassign > 0:
                    # Apply reassignment
                    resolved_df.loc[reassign_mask, 'COUNTY'] = target_county
                    total_reassigned += zones_to_reassign
                    
                    target_name = self.BAY_AREA_COUNTIES.get(target_county, {}).get('name', 'Unknown')
                    if verbose:
                        print(f"      -> Reassigned {zones_to_reassign} zones to County {target_county} ({target_name}) using {method_used}")
        
        if verbose:
            print(f"\n  Resolution complete:")
            print(f"    Total zones reassigned: {total_reassigned}")
            
            # Verify no multi-county PUMAs remain
            final_puma_county_counts = resolved_df.groupby('PUMA')['COUNTY'].nunique()
            remaining_multi = final_puma_county_counts[final_puma_county_counts > 1]
            
            if len(remaining_multi) == 0:
                print(f"    SUCCESS: All PUMAs now belong to single counties")
            else:
                print(f"    WARNING: {len(remaining_multi)} PUMAs still span multiple counties")
                for puma in remaining_multi.index:
                    counties = resolved_df[resolved_df['PUMA'] == puma]['COUNTY'].unique()
                    print(f"      PUMA {puma}: Counties {list(counties)}")
        
        return resolved_df
    
    def get_puma_to_county_mapping(self):
        """
        Get PUMA to county (1-9) mapping for Bay Area
        Based on geographic knowledge of which PUMAs are in which counties
        """
        puma_to_county = {
            # San Francisco County (1) - PUMAs 7501-7511
            7501: 1, 7502: 1, 7503: 1, 7504: 1, 7505: 1, 7506: 1, 7507: 1, 7508: 1, 7509: 1, 7510: 1, 7511: 1,
            
            # San Mateo County (2) - PUMAs 8101-8103 
            8101: 2, 8102: 2, 8103: 2,
            
            # Santa Clara County (3) - PUMAs 8501-8509
            8501: 3, 8502: 3, 8503: 3, 8504: 3, 8505: 3, 8506: 3, 8507: 3, 8508: 3, 8509: 3,
            
            # Alameda County (4) - PUMAs 0101-0108
            101: 4, 102: 4, 103: 4, 104: 4, 105: 4, 106: 4, 107: 4, 108: 4,
            
            # Contra Costa County (5) - PUMAs 1301-1305
            1301: 5, 1302: 5, 1303: 5, 1304: 5, 1305: 5,
            
            # Solano County (6) - PUMAs 9501-9502
            9501: 6, 9502: 6,
            
            # Napa County (7) - PUMA 5501
            5501: 7,
            
            # Sonoma County (8) - PUMAs 9701-9703
            9701: 8, 9702: 8, 9703: 8,
            
            # Marin County (9) - PUMAs 4101-4102
            4101: 9, 4102: 9
        }
        return puma_to_county

# Create global configuration instance
config = UnifiedTM2Config()
