#!/usr/bin/env python3
"""
TM2 PopulationSim Utilities

Helper functions and utilities for working with TM2 configuration.
File checks, workflow commands, data loading, etc.
"""

import shutil
import pandas as pd
from pathlib import Path


class TM2Utils:
    """Utility methods for TM2 workflow"""
    
    def __init__(self, config):
        """Initialize with a TM2Config instance"""
        self.config = config
    
    # ============================================================
    # DATA LOADING
    # ============================================================
    
    def load_pumas_from_crosswalk(self):
        """Load Bay Area PUMAs from crosswalk file"""
        try:
            crosswalk_path = self.config.CROSSWALK_FILES['main']
            if crosswalk_path.exists():
                df = pd.read_csv(crosswalk_path)
                if 'PUMA' in df.columns:
                    pumas = sorted(df['PUMA'].dropna().unique())
                    print(f"[UTILS] Loaded {len(pumas)} PUMAs from crosswalk")
                    return pumas
                else:
                    print(f"[UTILS] WARNING: PUMA column not found in crosswalk")
                    return []
            else:
                print(f"[UTILS] WARNING: Crosswalk not found at {crosswalk_path}")
                return []
        except Exception as e:
            print(f"[UTILS] ERROR loading PUMAs: {e}")
            return []
    
    def generate_puma_to_county_mapping(self):
        """
        Generate PUMA to county mapping dynamically from crosswalk.
        Uses majority rule: assign each PUMA to county with most zones.
        """
        try:
            crosswalk_path = self.config.CROSSWALK_FILES['main']
            if not crosswalk_path.exists():
                print(f"[UTILS] WARNING: Crosswalk not found")
                return {}
            
            df = pd.read_csv(crosswalk_path)
            if 'PUMA' not in df.columns or 'COUNTY' not in df.columns:
                print(f"[UTILS] WARNING: PUMA or COUNTY column missing")
                return {}
            
            # Count zones per PUMA-county combination
            puma_county_counts = df.groupby(['PUMA', 'COUNTY']).size().reset_index(name='count')
            
            # For each PUMA, find county with most zones
            puma_to_county = {}
            for puma in puma_county_counts['PUMA'].unique():
                puma_data = puma_county_counts[puma_county_counts['PUMA'] == puma]
                majority_county = puma_data.loc[puma_data['count'].idxmax(), 'COUNTY']
                puma_to_county[int(puma)] = int(majority_county)
            
            print(f"[UTILS] Generated PUMA-to-county mapping for {len(puma_to_county)} PUMAs")
            return puma_to_county
            
        except Exception as e:
            print(f"[UTILS] ERROR generating PUMA mapping: {e}")
            return {}
    
    def resolve_multi_county_pumas(self, crosswalk_df, verbose=False):
        """
        Resolve PUMAs spanning multiple counties using majority rule.
        
        Args:
            crosswalk_df: DataFrame with PUMA, COUNTY columns
            verbose: Whether to print detailed logging
            
        Returns:
            DataFrame with resolved county assignments
        """
        if not self.config.PUMA_RESOLUTION['enabled']:
            return crosswalk_df
        
        verbose = verbose or self.config.PUMA_RESOLUTION.get('verbose_logging', False)
        resolved_df = crosswalk_df.copy()
        
        # Find multi-county PUMAs
        puma_county_counts = resolved_df.groupby('PUMA')['COUNTY'].nunique()
        multi_county_pumas = puma_county_counts[puma_county_counts > 1].index.tolist()
        
        if not multi_county_pumas:
            if verbose:
                print("No multi-county PUMAs found")
            return resolved_df
        
        total_reassigned = 0
        
        for puma in multi_county_pumas:
            puma_data = resolved_df[resolved_df['PUMA'] == puma]
            county_counts = puma_data['COUNTY'].value_counts()
            
            # Determine target county
            if puma in self.config.PUMA_RESOLUTION['manual_overrides']:
                target_county = self.config.PUMA_RESOLUTION['manual_overrides'][puma]
                method = "manual override"
            else:
                target_county = county_counts.index[0]  # Majority
                method = "majority rule"
            
            # Reassign zones
            reassign_mask = (resolved_df['PUMA'] == puma) & (resolved_df['COUNTY'] != target_county)
            zones_reassigned = reassign_mask.sum()
            
            if zones_reassigned > 0:
                resolved_df.loc[reassign_mask, 'COUNTY'] = target_county
                total_reassigned += zones_reassigned
                
                if verbose:
                    county_name = self.config.BAY_AREA_COUNTIES.get(target_county, {}).get('name', 'Unknown')
                    print(f"PUMA {puma}: {zones_reassigned} zones -> County {target_county} ({county_name}) [{method}]")
        
        if verbose or total_reassigned > 0:
            print(f"Resolved {len(multi_county_pumas)} multi-county PUMAs, reassigned {total_reassigned} zones")
        
        return resolved_df
    
    # ============================================================
    # FILE EXISTENCE CHECKS
    # ============================================================
    
    def check_crosswalk_exists(self):
        """Check if crosswalk file exists"""
        return self.config.CROSSWALK_FILES['main'].exists()
    
    def check_seed_exists(self):
        """Check if seed files exist"""
        return (self.config.SEED_FILES['households'].exists() and 
                self.config.SEED_FILES['persons'].exists())
    
    def check_controls_exist(self):
        """Check if control files exist"""
        return (self.config.CONTROL_FILES['maz_marginals'].exists() and
                self.config.CONTROL_FILES['taz_marginals'].exists() and 
                self.config.CONTROL_FILES['county_marginals'].exists())
    
    def check_popsim_output_exists(self):
        """Check if PopulationSim output exists"""
        return (self.config.POPSIM_OUTPUT_FILES['synthetic_households'].exists() and
                self.config.POPSIM_OUTPUT_FILES['synthetic_persons'].exists())
    
    # ============================================================
    # FILE SYNCHRONIZATION
    # ============================================================
    
    def sync_control_files(self):
        """Copy control files to PopulationSim data directory"""
        mappings = [
            (self.config.CONTROL_FILES['maz_marginals'], 
             self.config.POPSIM_DATA_DIR / self.config.FILE_TEMPLATES['maz_marginals']),
            (self.config.CONTROL_FILES['taz_marginals'], 
             self.config.POPSIM_DATA_DIR / self.config.FILE_TEMPLATES['taz_marginals']),
            (self.config.CONTROL_FILES['county_marginals'], 
             self.config.POPSIM_DATA_DIR / self.config.FILE_TEMPLATES['county_marginals'])
        ]
        
        for src, dst in mappings:
            if src.exists():
                shutil.copy2(src, dst)
                print(f"Synced: {src.name} -> {dst}")
            else:
                print(f"WARNING: Missing file {src}")
    
    # ============================================================
    # DIRECTORY MANAGEMENT
    # ============================================================
    
    def create_directories(self):
        """Create all necessary directories"""
        dirs_to_create = [
            self.config.OUTPUT_DIR,
            self.config.POPSIM_WORKING_DIR,
            self.config.POPSIM_DATA_DIR,
            self.config.POPSIM_CONFIG_DIR,
            self.config.POPSIM_OUTPUT_DIR,
            self.config.OUTPUT_DIR / "tableau",
            self.config.EXTERNAL_PATHS['census_cache']
        ]
        
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # ============================================================
    # WORKFLOW COMMANDS
    # ============================================================
    
    def get_workflow_commands(self):
        """Generate workflow commands based on configuration"""
        return {
            'pums': [
                "python",
                str(self.config.BASE_DIR / "download_2023_5year_pums.py")
            ],
            'seed': [
                "python",
                str(self.config.BASE_DIR / "create_seed_population.py"),
                "--year", str(self.config.YEAR),
                "--model_type", self.config.MODEL_TYPE
            ] + self.config.get_test_puma_args(),
            'controls': [
                "python",
                str(self.config.BASE_DIR / "create_baseyear_controls.py")
            ] + self.config.get_test_puma_args(),
            'populationsim': [
                "python",
                str(self.config.BASE_DIR / "run_populationsim.py"),
                "--working_dir", str(self.config.POPSIM_WORKING_DIR),
                "--output", str(self.config.POPSIM_OUTPUT_DIR)
            ] + self.config.get_test_puma_args(),
            'postprocess': [
                "python",
                str(self.config.BASE_DIR / "postprocess_recode.py"),
                "--model_type", self.config.MODEL_TYPE,
                "--directory", str(self.config.POPSIM_OUTPUT_DIR),
                "--year", str(self.config.YEAR)
            ] + self.config.get_test_puma_args(),
            'summary_analysis': [
                "python",
                str(self.config.BASE_DIR / "run_all_summaries.py"),
                "--year", str(self.config.YEAR),
                "--model_type", self.config.MODEL_TYPE
            ] + self.config.get_test_puma_args(),
        }
    
    def get_workflow_status(self):
        """Get complete workflow status"""
        status = {
            'crosswalk': self.check_crosswalk_exists(),
            'seed': self.check_seed_exists(), 
            'controls': self.check_controls_exist(),
            'popsim': self.check_popsim_output_exists(),
        }
        
        # Determine what steps need to run
        steps_needed = []
        if self.config.FORCE_FLAGS['CROSSWALK'] or not status['crosswalk']:
            steps_needed.append('crosswalk')
        if self.config.FORCE_FLAGS['SEED'] or not status['seed']:
            steps_needed.append('seed')
        if self.config.FORCE_FLAGS['CONTROLS'] or not status['controls']:
            steps_needed.append('controls')
        if self.config.FORCE_FLAGS['POPSIM'] or not status['popsim']:
            steps_needed.append('popsim')
        if self.config.FORCE_FLAGS['POSTPROCESS']:
            steps_needed.append('postprocess')
        
        return status, steps_needed
    
    # ============================================================
    # COUNTY LOOKUP HELPERS
    # ============================================================
    
    def get_county_by_fips(self, fips_code):
        """Get county info by FIPS code"""
        fips_int = int(str(fips_code).lstrip('0')) if fips_code else None
        for county_id, info in self.config.BAY_AREA_COUNTIES.items():
            if info['fips_int'] == fips_int:
                return county_id, info
        return None, None
    
    def get_county_by_name(self, name):
        """Get county info by name"""
        for county_id, info in self.config.BAY_AREA_COUNTIES.items():
            if info['name'].lower() == name.lower():
                return county_id, info
        return None, None
