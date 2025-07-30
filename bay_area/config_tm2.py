#!/usr/bin/env python3
"""
Configuration file for Bay Area PopulationSim TM2 workflow
Centralizes all paths, settings, and parameters
"""

from pathlib import Path
import os

class PopulationSimConfig:
    """Configuration class for PopulationSim TM2 workflow"""
    
    def __init__(self, base_dir=None):
        # Base directory - defaults to current working directory
        self.BASE_DIR = Path(base_dir) if base_dir else Path.cwd()
        
        # Environment setup
        self.CONDA_PATH = Path("C:/Users/schildress/AppData/Local/anaconda3")
        self.POPSIM_ENV = "popsim"
        self.PYTHON_PATH = self.CONDA_PATH / "envs" / self.POPSIM_ENV / "python.exe"
        
        # Model configuration
        self.MODEL_TYPE = "TM2"
        self.YEAR = 2023
        
        # Directory structure
        self.OUTPUT_DIR = self.BASE_DIR / "output_2023"
        self.POPULATIONSIM_OUTPUT_DIR = self.OUTPUT_DIR / "populationsim_run"
        self.HH_GQ_DIR = self.BASE_DIR / "hh_gq"
        self.HH_GQ_DATA_DIR = self.HH_GQ_DIR / "data"
        self.HH_GQ_CONFIGS_DIR = self.HH_GQ_DIR / f"configs_{self.MODEL_TYPE}"
        
        # Ensure directories exist
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        self.POPULATIONSIM_OUTPUT_DIR.mkdir(exist_ok=True)
        self.HH_GQ_DATA_DIR.mkdir(exist_ok=True)
        
        # Seed population files
        self.SEED_FILES = {
            'households_raw': self.OUTPUT_DIR / "households_2023_raw.csv",
            'persons_raw': self.OUTPUT_DIR / "persons_2023_raw.csv",
            'households_processed': self.OUTPUT_DIR / "households_2023_tm2.csv",
            'persons_processed': self.OUTPUT_DIR / "persons_2023_tm2.csv",
            'households_popsim': self.HH_GQ_DATA_DIR / "seed_households.csv",
            'persons_popsim': self.HH_GQ_DATA_DIR / "seed_persons.csv"
        }
        
        # Control files
        self.CONTROL_FILES = {
            'maz_marginals': self.HH_GQ_DATA_DIR / "maz_marginals.csv",
            'taz_marginals': self.HH_GQ_DATA_DIR / "taz_marginals.csv",
            'county_marginals': self.HH_GQ_DATA_DIR / "county_marginals.csv",
            'geo_cross_walk': self.HH_GQ_DATA_DIR / "geo_cross_walk_tm2.csv",
            'geo_cross_walk_updated': self.HH_GQ_DATA_DIR / "geo_cross_walk_tm2_updated.csv"
        }
        
        # Group quarters integration files
        self.HHGQ_FILES = {
            'maz_marginals_hhgq': self.HH_GQ_DATA_DIR / "maz_marginals_hhgq.csv",
            'taz_marginals_hhgq': self.HH_GQ_DATA_DIR / "taz_marginals_hhgq.csv"
        }
        
        # PopulationSim output files
        self.POPSIM_OUTPUT_FILES = {
            'synthetic_households': self.POPULATIONSIM_OUTPUT_DIR / "synthetic_households.csv",
            'synthetic_persons': self.POPULATIONSIM_OUTPUT_DIR / "synthetic_persons.csv",
            'summary_melt': self.POPULATIONSIM_OUTPUT_DIR / "summary_melt.csv",
            'populationsim_log': self.POPULATIONSIM_OUTPUT_DIR / "populationsim.log",
            'pipeline_cache': self.POPULATIONSIM_OUTPUT_DIR / "pipeline.h5"
        }
        
        # Scripts and executables
        self.SCRIPTS = {
            'create_seed_population': self.BASE_DIR / "create_seed_population_tm2.py",
            'create_controls': self.BASE_DIR / "create_baseyear_controls_23_tm2.py",
            'add_hhgq': self.BASE_DIR / "add_hhgq_combined_controls.py",
            'run_populationsim': self.BASE_DIR / "run_populationsim.py",
            'postprocess': self.BASE_DIR / "postprocess_recode.py"
        }
        
        # Validation and archive files
        self.VALIDATION_FILES = {
            'validation_workbook': self.BASE_DIR / "validation.twb",
            'validation_output': self.POPULATIONSIM_OUTPUT_DIR / "validation.twb"
        }
        
        # Archive files to copy to output directory
        self.ARCHIVE_FILES = [
            self.CONTROL_FILES['maz_marginals'],
            self.CONTROL_FILES['taz_marginals'],
            self.CONTROL_FILES['county_marginals'],
            self.CONTROL_FILES['geo_cross_walk']
        ]
        
        # Tableau data preparation
        self.TABLEAU_OUTPUT_DIR = self.POPULATIONSIM_OUTPUT_DIR / "tableau"
        self.TABLEAU_FILES = {
            'script': self.BASE_DIR / "prepare_tableau_data.py",
            'taz_boundaries': self.TABLEAU_OUTPUT_DIR / "taz_boundaries_tableau.shp",
            'puma_boundaries': self.TABLEAU_OUTPUT_DIR / "puma_boundaries_tableau.shp",
            'taz_marginals': self.TABLEAU_OUTPUT_DIR / "taz_marginals_tableau.csv",
            'maz_marginals': self.TABLEAU_OUTPUT_DIR / "maz_marginals_tableau.csv",
            'geo_crosswalk': self.TABLEAU_OUTPUT_DIR / "geo_crosswalk_tableau.csv",
            'readme': self.TABLEAU_OUTPUT_DIR / "README_TABLEAU.md"
        }
        
        # Force flags (can be overridden)
        self.FORCE_FLAGS = {
            'SEED': False,
            'CONTROLS': False,
            'HHGQ': False,
            'POPULATIONSIM': False,
            'POSTPROCESS': False,
            'TABLEAU': False
        }
        
        # Test configuration
        self.TEST_PUMA = None  # Set to PUMA code for testing, None for full region
    
    def get_command_args(self, command_type, **kwargs):
        """Get command arguments for different script types"""
        commands = {
            'seed_population': [str(self.PYTHON_PATH), str(self.SCRIPTS['create_seed_population'])],
            'create_controls': [
                str(self.PYTHON_PATH), 
                str(self.SCRIPTS['create_controls']), 
                "--output_dir", 
                str(self.HH_GQ_DATA_DIR)
            ],
            'add_hhgq': [
                str(self.PYTHON_PATH), 
                str(self.SCRIPTS['add_hhgq']), 
                "--model_type", 
                self.MODEL_TYPE
            ],
            'run_populationsim': [
                str(self.PYTHON_PATH),
                str(self.SCRIPTS['run_populationsim']),
                "--config", str(self.HH_GQ_CONFIGS_DIR),
                "--output", str(self.POPULATIONSIM_OUTPUT_DIR),
                "--data", str(self.HH_GQ_DATA_DIR)
            ],
            'postprocess': [
                str(self.PYTHON_PATH),
                str(self.SCRIPTS['postprocess']),
                "--model_type", self.MODEL_TYPE,
                "--directory", str(self.POPULATIONSIM_OUTPUT_DIR),
                "--year", str(self.YEAR)
            ],
            'tableau': [
                str(self.PYTHON_PATH),
                str(self.TABLEAU_FILES['script']),
                "--output_dir", str(self.POPULATIONSIM_OUTPUT_DIR),
                "--year", str(self.YEAR)
            ]
        }
        
        # Add test PUMA flag if set
        if self.TEST_PUMA and command_type == 'postprocess':
            commands['postprocess'].extend(["--test_PUMA", self.TEST_PUMA])
        
        return commands.get(command_type, [])
    
    def check_file_exists(self, file_key, file_category='SEED_FILES'):
        """Check if a file exists by key"""
        file_dict = getattr(self, file_category, {})
        file_path = file_dict.get(file_key)
        if file_path:
            return Path(file_path).exists()
        return False
    
    def get_file_path(self, file_key, file_category='SEED_FILES'):
        """Get file path by key"""
        file_dict = getattr(self, file_category, {})
        return file_dict.get(file_key)
    
    def clean_pipeline_cache(self):
        """Clean PopulationSim pipeline cache"""
        cache_file = self.POPSIM_OUTPUT_FILES['pipeline_cache']
        if cache_file.exists():
            cache_file.unlink()
            return True
        return False
    
    def copy_seed_files_to_popsim(self):
        """Copy processed seed files to PopulationSim data directory"""
        import shutil
        
        # Copy household file
        src_hh = self.SEED_FILES['households_processed']
        dst_hh = self.SEED_FILES['households_popsim']
        if src_hh.exists():
            shutil.copy2(src_hh, dst_hh)
        
        # Copy persons file
        src_p = self.SEED_FILES['persons_processed']
        dst_p = self.SEED_FILES['persons_popsim']
        if src_p.exists():
            shutil.copy2(src_p, dst_p)
    
    def archive_input_files(self):
        """Copy input files to output directory for archival"""
        import shutil
        
        for src_file in self.ARCHIVE_FILES:
            if src_file.exists():
                dst_file = self.POPULATIONSIM_OUTPUT_DIR / src_file.name
                shutil.copy2(src_file, dst_file)
    
    def check_tableau_files(self):
        """Check which Tableau files exist"""
        status = {}
        for key, file_path in self.TABLEAU_FILES.items():
            if key == 'script':
                status[key] = file_path.exists()
            else:
                status[key] = file_path.exists()
        return status
    
    def __str__(self):
        """String representation of configuration"""
        return f"""PopulationSimConfig:
  Model Type: {self.MODEL_TYPE}
  Year: {self.YEAR}
  Base Directory: {self.BASE_DIR}
  Output Directory: {self.OUTPUT_DIR}
  PopulationSim Output: {self.POPULATIONSIM_OUTPUT_DIR}
  Tableau Output: {self.TABLEAU_OUTPUT_DIR}
  Test PUMA: {self.TEST_PUMA or 'None (full region)'}
  Force Flags: {self.FORCE_FLAGS}
"""

# Default configuration instance
config = PopulationSimConfig()
