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
        # Allow environment variable override, otherwise use current user
        python_exe_env = os.getenv('POPSIM_PYTHON_EXE')
        if python_exe_env:
            self.PYTHON_EXE = Path(python_exe_env)
        else:
            # Auto-detect current user and use popsim environment (not popsim_py312)
            current_user = os.getenv('USERNAME', 'schildress')
            self.PYTHON_EXE = Path(rf"C:\Users\{current_user}\AppData\Local\anaconda3\envs\popsim\python.exe")
        
        # Validate Python executable exists
        if not self.PYTHON_EXE.exists():
            raise FileNotFoundError(f"PopulationSim Python environment not found at: {self.PYTHON_EXE}")
        
        # Main directories - DEFINE THESE FIRST
        self.OUTPUT_DIR = self.BASE_DIR / f"output_{self.YEAR}"
        self.HH_GQ_DIR = self.BASE_DIR / "hh_gq"
        self.SCRIPTS_DIR = self.BASE_DIR / "scripts"
        
        # PopulationSim working directory (where PopulationSim actually runs)
        self.POPSIM_WORKING_DIR = self.HH_GQ_DIR / "tm2_working_dir"
        self.POPSIM_DATA_DIR = self.POPSIM_WORKING_DIR / "data"
        self.POPSIM_CONFIG_DIR = self.POPSIM_WORKING_DIR / "configs"
        self.POPSIM_OUTPUT_DIR = self.POPSIM_WORKING_DIR / "output"
        
        # Test PUMA setting (needed for command setup)
        self.TEST_PUMA = os.getenv('TEST_PUMA', None)
        
        # ============================================================
        # BAY AREA PUMA DEFINITIONS - SINGLE SOURCE OF TRUTH
        # Bay Area PUMA codes (62 actual PUMAs from crosswalk - integer format for PopulationSim)
        # Updated to match actual crosswalk PUMAs rather than theoretical full list
        self.BAY_AREA_PUMAS = [
            101, 111, 112, 113, 114, 115, 116, 117, 118, 119, 
            120, 121, 122, 123, 1301, 1305, 1308, 1309, 1310, 1311, 
            1312, 1313, 1314, 4103, 4104, 5500, 7507, 7508, 7509, 7510, 
            7511, 7512, 7513, 7514, 8101, 8102, 8103, 8104, 8105, 8106, 
            8505, 8506, 8507, 8508, 8510, 8511, 8512, 8515, 8516, 8517, 
            8518, 8519, 8520, 8521, 8522, 9501, 9502, 9503, 9702, 9704, 
            9705, 9706
        ]
        
        # Now define external paths and other configurations
        self._setup_external_paths()
        self._setup_file_templates()
        
        # Ensure directories exist
        self._create_directories()
        
        # Define ALL file paths in one place
        self._setup_file_paths()
        
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
    
    def _setup_external_paths(self):
        """Setup external system paths"""
        self.EXTERNAL_PATHS = {
            # TM2PY utilities (for shapefiles)
            'tm2py_shapefiles': Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles"),
            # Original populationsim_update path (used in some scripts)
            'populationsim_update': Path("c:/GitHub/populationsim_update/bay_area"),
            # Census data cache
            'census_cache': self.BASE_DIR / "data_cache" / "census",
            # Network locations (M: drive) - with fallbacks
            'network_gis': Path("M:/Data/GIS layers/TM2_maz_taz_v2.2"),
            'network_census_cache': Path("M:/Data/Census/NewCachedTablesForPopulationSimControls"),
            'network_census_api': Path("M:/Data/Census/API/new_key"),
            # Local fallback paths
            'local_data': self.BASE_DIR / "local_data",
            'local_gis': self.BASE_DIR / "local_data" / "gis", 
            'local_census': self.BASE_DIR / "local_data" / "census",
            'input_2023_cache': self.BASE_DIR / "input_2023" / "NewCachedTablesForPopulationSimControls"
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
            'maz_shapefile': self.EXTERNAL_PATHS['tm2py_shapefiles'] / "mazs_TM2_2_4.shp",
            'taz_shapefile': self.EXTERNAL_PATHS['tm2py_shapefiles'] / "tazs_TM2_2_4.shp",
            'puma_shapefile': self.EXTERNAL_PATHS['tm2py_shapefiles'] / "tl_2022_06_puma20.shp"
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
            
            # Control files
            'maz_marginals': "maz_marginals.csv",
            'taz_marginals': "taz_marginals.csv",
            'county_marginals': "county_marginals.csv",
            'maz_data': "maz_data.csv",
            'maz_data_density': "maz_data_withDensity.csv",
            
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
            # Primary crosswalk (gets created and updated)
            'main_crosswalk': self.OUTPUT_DIR / self.FILE_TEMPLATES['geo_crosswalk_updated'],
            # PopulationSim needs its own copy
            'popsim_crosswalk': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['geo_crosswalk_base']
        }
        
        # ============================================================
        # STEP 1: SEED POPULATION FILES  
        # ============================================================
        self.SEED_FILES = {
            # Raw downloaded files
            'households_raw': self.OUTPUT_DIR / self.FILE_TEMPLATES['households_raw'],
            'persons_raw': self.OUTPUT_DIR / self.FILE_TEMPLATES['persons_raw'],
            # Processed files 
            'households_processed': self.OUTPUT_DIR / self.FILE_TEMPLATES['households_processed'],
            'persons_processed': self.OUTPUT_DIR / self.FILE_TEMPLATES['persons_processed'],
            # Final seed files (main versions)
            'households_main': self.OUTPUT_DIR / self.FILE_TEMPLATES['seed_households'], 
            'persons_main': self.OUTPUT_DIR / self.FILE_TEMPLATES['seed_persons'],
            # PopulationSim copies
            'households_popsim': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['seed_households'],
            'persons_popsim': self.POPSIM_DATA_DIR / self.FILE_TEMPLATES['seed_persons']
        }
        
        # ============================================================
        # STEP 2: CONTROL FILES
        # ============================================================
        self.CONTROL_FILES = {
            # Generated control files (main versions in output_2023)
            'maz_marginals_main': self.OUTPUT_DIR / self.FILE_TEMPLATES['maz_marginals'],
            'taz_marginals_main': self.OUTPUT_DIR / self.FILE_TEMPLATES['taz_marginals'], 
            'county_marginals_main': self.OUTPUT_DIR / self.FILE_TEMPLATES['county_marginals'],
            'maz_data_main': self.OUTPUT_DIR / self.FILE_TEMPLATES['maz_data'],
            'maz_data_density_main': self.OUTPUT_DIR / self.FILE_TEMPLATES['maz_data_density'],
            
            # PopulationSim copies (what PopulationSim actually reads)
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
    
    def _setup_commands(self):
        """Define ALL commands in the system"""
        
        self.COMMANDS = {
            # Step 0: Crosswalk creation
            'crosswalk': [
                str(self.PYTHON_EXE),
                str(self.BASE_DIR / "build_crosswalk_focused.py")
            ] + self.get_test_puma_args(),
            
            # Step 1: Seed generation  
            'seed': [
                str(self.PYTHON_EXE),
                str(self.BASE_DIR / "create_seed_population_tm2_refactored.py"),
                "--year", str(self.YEAR),
                "--model_type", self.MODEL_TYPE
            ] + self.get_test_puma_args(),
            
            # Step 2: Control generation
            'controls': [
                str(self.PYTHON_EXE),
                str(self.BASE_DIR / "create_baseyear_controls_23_tm2.py"),
                "--output_dir", str(self.OUTPUT_DIR)
            ] + self.get_test_puma_args(),
            
            # Step 3: Group quarters integration
            'hhgq': [
                str(self.PYTHON_EXE),
                str(self.BASE_DIR / "add_hhgq_combined_controls.py"), 
                "--model_type", self.MODEL_TYPE,
                "--input_dir", str(self.OUTPUT_DIR),
                "--output_dir", str(self.POPSIM_DATA_DIR)
            ] + self.get_test_puma_args(),
            
            # Step 4: PopulationSim synthesis
            'populationsim': [
                str(self.PYTHON_EXE),
                str(self.BASE_DIR / "run_populationsim_synthesis.py"),
                "--working_dir", str(self.POPSIM_WORKING_DIR),
                "--output", str(self.POPSIM_OUTPUT_DIR)
            ] + self.get_test_puma_args(),
            
            # Step 5: Post-processing
            'postprocess': [
                str(self.PYTHON_EXE),
                str(self.BASE_DIR / "postprocess_recode.py"),
                "--model_type", self.MODEL_TYPE,
                "--directory", str(self.POPSIM_OUTPUT_DIR),
                "--year", str(self.YEAR)
            ] + self.get_test_puma_args(),
            
            # Step 6: Tableau preparation
            'tableau': [
                str(self.PYTHON_EXE),
                str(self.TABLEAU_FILES['script']),
                "--output_dir", str(self.TABLEAU_FILES['output_dir']),
                "--year", str(self.YEAR)
            ] + self.get_test_puma_args()
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
            'crosswalk': self.BASE_DIR / "build_crosswalk_focused.py",
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

# Create global configuration instance
config = UnifiedTM2Config()
