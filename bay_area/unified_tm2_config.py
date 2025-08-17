#!/usr/bin/env python3
"""
Unified TM2 PopulationSim Configuration
Single source of truth for ALL paths, commands, and workflow logic
Eliminates ALL hardcoded values across the entire codebase!
"""

from pathlib import Path
import os
import sys

class UnifiedTM2Config:
    """Single configuration class that handles everything"""
    
    def __init__(self, year=2023, model_type="TM2"):
        # Base paths
        self.BASE_DIR = Path(__file__).parent.absolute()
        self.YEAR = year
        self.MODEL_TYPE = model_type
        
        # Python executable (full path to popsim environment)
        # Use the current user's popsim environment
        self.PYTHON_EXE = Path(r"C:\Users\schildress\AppData\Local\anaconda3\envs\popsim\python.exe")
        
        # Validate Python executable exists
        if not self.PYTHON_EXE.exists():
            raise FileNotFoundError(f"PopulationSim Python environment not found at: {self.PYTHON_EXE}")
        
        # Main directories - POPULATIONSIM-COMPATIBLE STRUCTURE
        self.OUTPUT_DIR = self.BASE_DIR / f"output_{self.YEAR}"
        self.SCRIPTS_DIR = self.BASE_DIR / "scripts"
        
        # PopulationSim working directory (this becomes our main output structure)
        self.POPSIM_WORKING_DIR = self.OUTPUT_DIR / "populationsim_working_dir"
        self.POPSIM_DATA_DIR = self.POPSIM_WORKING_DIR / "data"
        self.POPSIM_CONFIG_DIR = self.POPSIM_WORKING_DIR / "configs"
        self.POPSIM_OUTPUT_DIR = self.POPSIM_WORKING_DIR / "output"
        
        # Legacy alias for pipeline compatibility - POINT TO POPSIM DATA DIR
        self.DATA_DIR = self.POPSIM_DATA_DIR
        
        # Example/reference data directories (for template employment/land use data)
        self.EXAMPLE_CONTROLS_DIR = self.BASE_DIR / "example_controls_2015"
        
        # Test PUMA setting (for single PUMA testing)
        # Set to specific PUMA for fast testing, or None for full synthesis
        self.TEST_PUMA = None  # Disabled - run full synthesis to test GQ fixes
        
        # ============================================================
        # BAY AREA PUMA DEFINITIONS - SINGLE SOURCE OF TRUTH
        # Bay Area PUMA codes - dynamically loaded from crosswalk
        # This ensures consistency across all pipeline components
        # NOTE: Will be loaded later after file paths are set up
        self.BAY_AREA_PUMAS = []
        
        # ============================================================
        # BAY AREA COUNTY DEFINITIONS - SINGLE SOURCE OF TRUTH
        # County mapping between sequential IDs (1-9) and FIPS codes
        # This ensures consistency across all pipeline components
        self.BAY_AREA_COUNTIES = {
            1: {'name': 'San Francisco', 'fips_int': 75, 'fips_str': '075'},
            2: {'name': 'San Mateo', 'fips_int': 81, 'fips_str': '081'},
            3: {'name': 'Santa Clara', 'fips_int': 85, 'fips_str': '085'},
            4: {'name': 'Alameda', 'fips_int': 1, 'fips_str': '001'},
            5: {'name': 'Contra Costa', 'fips_int': 13, 'fips_str': '013'},
            6: {'name': 'Solano', 'fips_int': 95, 'fips_str': '095'},
            7: {'name': 'Napa', 'fips_int': 55, 'fips_str': '055'},
            8: {'name': 'Sonoma', 'fips_int': 97, 'fips_str': '097'},
            9: {'name': 'Marin', 'fips_int': 41, 'fips_str': '041'}
        }
        
        # ============================================================
        # MULTI-COUNTY PUMA RESOLUTION SETTINGS
        # Automatic resolution of PUMAs that span multiple counties
        # Future-proof configuration for similar geographic conflicts
        # ============================================================
        self.PUMA_RESOLUTION = {
            'enabled': True,  # Enable automatic multi-county PUMA resolution
            'method': 'majority_rule',  # 'majority_rule' or 'manual_override'
            'min_threshold_pct': 1.0,  # Minimum percentage for reassignment (1% = outliers only)
            'verbose_logging': True,  # Log all reassignments for transparency
            
            # Manual overrides for specific problematic PUMAs (if needed)
            # Format: {puma_id: preferred_county_id}
            'manual_overrides': {
                # PUMA 5500: 99.9% in County 7 (Napa), 0.1% in County 8 (Sonoma) → assign all to Napa
                5500: 7,
                # PUMA 7513: 99.8% in County 1 (SF), 0.2% in County 9 (Marin) → assign all to SF  
                7513: 1
            }
        }
        
        # Now define external paths and other configurations
        self._setup_external_paths()
        self._setup_file_templates()
        
        # Ensure directories exist
        self._create_directories()
        
        # Define ALL file paths in one place
        self._setup_file_paths()
        
        # Now load PUMAs from crosswalk (after file paths are set up)
        self.BAY_AREA_PUMAS = self._load_pumas_from_crosswalk()
        
        # Define ALL commands in one place (AFTER helper methods are available)
        self._setup_commands()
        
        # Force flags for workflow control - FORCE ALL STEPS TO TEST COUNTY CODE FIXES
        self.FORCE_FLAGS = {
            'CROSSWALK': os.getenv('FORCE_CROSSWALK', 'True').lower() == 'true',
            'SEED': os.getenv('FORCE_SEED', 'True').lower() == 'true',
            'CONTROLS': os.getenv('FORCE_CONTROLS', 'True').lower() == 'true',
            'HHGQ': os.getenv('FORCE_HHGQ', 'True').lower() == 'true',
            'POPSIM': os.getenv('FORCE_POPSIM', 'True').lower() == 'true',  # Default to True
            'POSTPROCESS': os.getenv('FORCE_POSTPROCESS', 'True').lower() == 'true',
            'TABLEAU': os.getenv('FORCE_TABLEAU', 'True').lower() == 'true'
        }
        
        # ============================================================
        # PROCESSING PARAMETERS
        # ============================================================
        self.PROCESSING_PARAMS = {
            'chunk_size': 50000,
            'random_seed': 42,
            'census_api_timeout': 300,
            'max_retries': 3
        }
    
    def _load_pumas_from_crosswalk(self):
        """Load Bay Area PUMAs from crosswalk file instead of hardcoding"""
        try:
            import pandas as pd
            
            # Use single, definitive crosswalk location
            crosswalk_path = self.CROSSWALK_FILES['popsim_crosswalk']
            
            if crosswalk_path.exists():
                crosswalk_df = pd.read_csv(crosswalk_path)
                if 'PUMA' in crosswalk_df.columns:
                    pumas = sorted(crosswalk_df['PUMA'].dropna().unique())
                    print(f"[CONFIG] Loaded {len(pumas)} PUMAs from crosswalk: {crosswalk_path}")
                    return pumas
                else:
                    print(f"[CONFIG] WARNING: PUMA column not found in crosswalk: {crosswalk_path}")
                    return []
            else:
                print(f"[CONFIG] WARNING: Crosswalk file not found: {crosswalk_path}")
                print(f"[CONFIG] Generate crosswalk first before running pipeline")
                return []
            
        except Exception as e:
            print(f"[CONFIG] ERROR loading PUMAs from crosswalk: {e}")
            return []
    
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
            # Network locations (M: drive) - with fallbacks
            'network_gis': Path("M:/Data/GIS layers/TM2_maz_taz_v2.2"),
            'network_census_cache': Path("M:/Data/Census/NewCachedTablesForPopulationSimControls"),
            'network_census_api': Path("M:/Data/Census/API/new_key"),
            # PUMS data locations (both current and cached)
            'pums_current': Path("M:/Data/Census/PUMS_2023_5Year_Crosswalked"),
            'pums_cached': Path("M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23"),
            # Local fallback paths
            'local_data': self.BASE_DIR / "local_data",
            'local_gis': self.BASE_DIR / "local_data" / "gis", 
            'local_census': self.BASE_DIR / "local_data" / "census",
            'input_2023_cache': self.BASE_DIR / "input_2023" / "NewCachedTablesForPopulationSimControls",
            # Shapefiles for geographic processing
            'maz_shapefile': Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/mazs_TM2_2_5.shp"),
            'puma_shapefile': Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/tl_2022_06_puma20.shp"),
            'county_shapefile': Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/Counties.shp")
        }
        
        # ============================================================
        # GIS AND REFERENCE FILES
        # ============================================================
        self.GIS_FILES = {
            # Network locations (preferred)
            'maz_taz_def_network': self.EXTERNAL_PATHS['network_gis'] / "blocks_mazs_tazs.csv",
            'maz_taz_all_geog_network': self.EXTERNAL_PATHS['network_gis'] / "mazs_tazs_all_geog.csv",
            # Local fallbacks
            'maz_taz_def_local': self.EXTERNAL_PATHS['local_gis'] / "blocks_mazs_tazs.csv",
            'maz_taz_all_geog_local': self.EXTERNAL_PATHS['local_gis'] / "mazs_tazs_all_geog.csv",
            # Census API key locations
            'census_api_key_network': self.EXTERNAL_PATHS['network_census_api'] / "api-key.txt",
            'census_api_key_local': self.EXTERNAL_PATHS['local_census'] / "api-key.txt"
        }
        
        # ============================================================
        # CACHE DIRECTORIES (with fallback logic)
        # ============================================================
        self.CACHE_DIRS = {
            'network_cache': self.EXTERNAL_PATHS['network_census_cache'],
            'local_cache': self.EXTERNAL_PATHS['local_census'] / "cache",
            'input_2023_cache': self.EXTERNAL_PATHS['input_2023_cache']
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
            'geo_crosswalk_updated': f"geo_cross_walk_{self.MODEL_TYPE.lower()}_updated.csv",
            
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
            'main_crosswalk': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['geo_crosswalk_updated'],
            # PopulationSim needs this specific filename
            'popsim_crosswalk': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['geo_crosswalk_base'],
        }
        
        # ============================================================
        # STEP 1: SEED POPULATION FILES - PopulationSim expects these in data directory
        # ============================================================
        self.SEED_FILES = {
            # Raw downloaded files (can be in data directory)
            'households_raw': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['households_raw'],
            'persons_raw': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['persons_raw'],
            # Processed files (data directory)
            'households_processed': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['households_processed'],
            'persons_processed': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['persons_processed'],
            # Final seed files (PopulationSim data directory)
            'households_main': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['seed_households'], 
            'persons_main': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['seed_persons'],
            # PopulationSim copies (same location now)
            'households_popsim': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['seed_households'],
            'persons_popsim': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['seed_persons']
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
        # STEP 7: ANALYSIS FILES
        # ============================================================
        self.ANALYSIS_FILES = {
            'quick_analysis_script': self.BASE_DIR / "quick_corrected_analysis.py",
            'comprehensive_script': self.BASE_DIR / "analyze_populationsim_results_fast.py",
            'performance_summary': self.OUTPUT_DIR / "PERFORMANCE_SUMMARY.txt",
            'analysis_results': self.OUTPUT_DIR / "README_ANALYSIS_RESULTS.md"
        }
    
    def _setup_commands(self):
        """Define ALL commands in the system"""
        
        self.COMMANDS = {
            # Step 0: Crosswalk creation (MUST be first - seed generation needs it)
            'crosswalk': [
                str(self.PYTHON_EXE),
                str(self.BASE_DIR / "create_tm2_crosswalk.py"),
                "--output", str(self.CROSSWALK_FILES['popsim_crosswalk'])
            ] + self.get_test_puma_args(),
            
            # Step 1: PUMS data download (depends on crosswalk for PUMA filtering)
            'pums': [
                str(self.PYTHON_EXE),
                str(self.BASE_DIR / "download_2023_5year_pums.py")
            ],
            
            # Step 2: Seed generation (depends on crosswalk and PUMS data)
            'seed': [
                str(self.PYTHON_EXE),
                str(self.BASE_DIR / "create_seed_population_tm2_refactored.py"),
                "--year", str(self.YEAR),
                "--model_type", self.MODEL_TYPE
            ] + self.get_test_puma_args(),
            
            # Step 3: Control generation
            'controls': [
                str(self.PYTHON_EXE),
                str(self.BASE_DIR / "create_baseyear_controls_23_tm2.py")
            ] + self.get_test_puma_args(),
            
            # Step 4: Group quarters integration
            'hhgq': [
                str(self.PYTHON_EXE),
                str(self.BASE_DIR / "add_hhgq_combined_controls.py"), 
                "--model_type", self.MODEL_TYPE,
                "--input_dir", str(self.OUTPUT_DIR),
                "--output_dir", str(self.POPSIM_DATA_DIR)
            ] + self.get_test_puma_args(),
            
            # Step 5: PopulationSim synthesis
            'populationsim': [
                str(self.PYTHON_EXE),
                str(self.BASE_DIR / "run_populationsim_synthesis.py"),
                "--working_dir", str(self.POPSIM_WORKING_DIR),
                "--output", str(self.POPSIM_OUTPUT_DIR)
            ] + self.get_test_puma_args(),
            
            # Step 6: Post-processing
            'postprocess': [
                str(self.PYTHON_EXE),
                str(self.BASE_DIR / "postprocess_recode.py"),
                "--model_type", self.MODEL_TYPE,
                "--directory", str(self.POPSIM_OUTPUT_DIR),
                "--year", str(self.YEAR)
            ] + self.get_test_puma_args(),
            
            # Step 7: Tableau preparation
            'tableau': [
                str(self.PYTHON_EXE),
                str(self.TABLEAU_FILES['script']),
                "--output_dir", str(self.TABLEAU_FILES['output_dir']),
                "--year", str(self.YEAR)
            ] + self.get_test_puma_args(),
            
            # Step 8: Performance Analysis
            'analysis': [
                str(self.PYTHON_EXE),
                str(self.ANALYSIS_FILES['quick_analysis_script'])
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
            'households_final': self.SEED_FILES['households_main'],
            'persons_final': self.SEED_FILES['persons_main']
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
            'crosswalk_updated': self.CROSSWALK_FILES['main_crosswalk']
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
        return (self.SEED_FILES['households_main'].exists() and 
                self.SEED_FILES['persons_main'].exists())
    
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
        
        # Then sync seed files
        seed_mappings = [
            (self.SEED_FILES['households_main'], self.SEED_FILES['households_popsim']),
            (self.SEED_FILES['persons_main'], self.SEED_FILES['persons_popsim'])
        ]
        
        for src, dst in seed_mappings:
            if src.exists():
                shutil.copy2(src, dst)
                print(f"Synced: {src.name} -> {dst}")
            elif dst.exists():
                print(f"Using existing: {dst.name} (source {src.name} not found)")
            else:
                print(f"WARNING: Missing source file: {src}")
    
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
            'seed': [self.SEED_FILES['households_main'], self.SEED_FILES['persons_main']],
            'controls': [
                self.CONTROL_FILES['maz_marginals_main'], 
                self.CONTROL_FILES['taz_marginals_main'], 
                self.CONTROL_FILES['county_marginals_main']
            ],
            'populationsim': [
                self.POPSIM_OUTPUT_DIR / "synthetic_households.csv",
                self.POPSIM_OUTPUT_DIR / "synthetic_persons.csv"
            ],
            'analysis': [
                self.ANALYSIS_FILES['performance_summary'],
                self.ANALYSIS_FILES['analysis_results']
            ]
        }
        return step_files.get(step_name, [])
    
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
