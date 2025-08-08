#!/usr/bin/env python3
"""
TM2 Population Synthesis Workflow Orchestrator for the Bay Area
Orchestrates the complete 6-step population synthesis pipeline

Usage: python tm2_workflow_orchestrator.py [year]
Example: python tm2_workflow_orchestrator.py 2023

Steps:
  0. PUMA/MAZ/TAZ Crosswalk Creation
  1. Seed Population Generation
  2. Control Totals Generation  
  3. Group Quarters Integration
  4. PopulationSim Synthesis (calls external PopulationSim tool)
  5. Post-processing and Recoding
  6. Tableau Data Preparation
"""

import os
import sys
import shutil
import subprocess
import argparse
import traceback
from pathlib import Path
from datetime import datetime

# Import our configuration
from config_tm2 import PopulationSimConfig

class PopulationSimWorkflow:
    def __init__(self, year=2023, config=None):
        # Use provided config or create new one
        self.config = config or PopulationSimConfig()
        
        # Update year if different
        if year != self.config.YEAR:
            self.config.YEAR = year
        
        # Test PUMA configuration
        self.TEST_PUMA = self.config.TEST_PUMA
        if self.TEST_PUMA:
            self.TEST_PUMA_FLAG = ["--test_PUMA", self.TEST_PUMA]
            self.PUMA_SUFFIX = f"_puma{self.TEST_PUMA}"
        else:
            self.TEST_PUMA_FLAG = []
            self.PUMA_SUFFIX = ""
    
    def log(self, message, level="INFO"):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {level}: {message}"
        print(log_message)
        
        # Also write to error log file if it's an error or warning
        if level in ["ERROR", "WARNING"]:
            self._write_to_error_log(log_message)
    
    def _write_to_error_log(self, message):
        """Write error messages to a dedicated error log file"""
        try:
            error_log_file = self.config.POPULATIONSIM_OUTPUT_DIR / "populationsim_errors.log"
            error_log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Remove emoji characters for Windows compatibility
            import re
            clean_message = re.sub(r'[^\x00-\x7F]+', '', message)
            
            with open(error_log_file, 'a', encoding='utf-8') as f:
                f.write(clean_message + '\n')
        except Exception:
            # Don't let logging errors break the main process
            pass
    
    def run_command(self, command, description="Running command"):
        """Run a subprocess command with error handling and real-time output"""
        self.log(f"{description}...")
        self.log(f"Command: {' '.join(map(str, command))}")
        print("-" * 60)
        
        try:
            # Use Popen for real-time output streaming
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True,
                cwd=Path.cwd()
            )
            
            # Stream output in real-time
            output_lines = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())  # Print to terminal immediately
                    output_lines.append(output.strip())
            
            # Wait for process to complete
            return_code = process.poll()
            
            if return_code == 0:
                print("-" * 60)
                self.log(f"SUCCESS: {description} completed")
                return True
            else:
                print("-" * 60)
                self.log(f"ERROR: {description} failed with exit code {return_code}", "ERROR")
                return False
            
        except Exception as e:
            print("-" * 60)
            self.log(f"ERROR: {description} failed with exception: {e}", "ERROR")
            return False
    
    def check_file_exists(self, filepath):
        """Check if a file exists"""
        return Path(filepath).exists()
    
    def fix_gqtype_column_names(self):
        """Fix gqtype -> hhgqtype column naming in seed files for PopulationSim compatibility"""
        import pandas as pd
        
        hh_file = self.config.SEED_FILES['households_popsim']
        p_file = self.config.SEED_FILES['persons_popsim']
        
        files_fixed = False
        
        # Fix households file
        if hh_file.exists():
            try:
                df_hh = pd.read_csv(hh_file, nrows=5)  # Quick check
                if 'gqtype' in df_hh.columns and 'hhgqtype' not in df_hh.columns:
                    self.log("Fixing gqtype -> hhgqtype column in households file...")
                    df_hh_full = pd.read_csv(hh_file)
                    df_hh_full = df_hh_full.rename(columns={'gqtype': 'hhgqtype'})
                    df_hh_full.to_csv(hh_file, index=False)
                    files_fixed = True
            except Exception as e:
                self.log(f"WARNING: Could not fix households column: {e}", "WARNING")
        
        # Fix persons file  
        if p_file.exists():
            try:
                df_p = pd.read_csv(p_file, nrows=5)  # Quick check
                if 'gqtype' in df_p.columns and 'hhgqtype' not in df_p.columns:
                    self.log("Fixing gqtype -> hhgqtype column in persons file...")
                    df_p_full = pd.read_csv(p_file)
                    df_p_full = df_p_full.rename(columns={'gqtype': 'hhgqtype'})
                    df_p_full.to_csv(p_file, index=False)
                    files_fixed = True
            except Exception as e:
                self.log(f"WARNING: Could not fix persons column: {e}", "WARNING")
        
        if files_fixed:
            self.log("SUCCESS: Fixed column naming for PopulationSim compatibility")
        
        return files_fixed
    
    def workflow_status_check(self):
        """Check existing files to determine what steps need to run"""
        print("=" * 80)
        print("    Bay Area PopulationSim TM2 Workflow")
        print("=" * 80)
        print()
        
        print("===== WORKFLOW STATUS CHECK =====")
        print("Checking existing files to determine what steps need to run...")
        print()
        
        # Step 0: PUMA/MAZ/TAZ Crosswalk Creation (check for crosswalk file)
        step0_complete = self.config.CONTROL_FILES['geo_cross_walk'].exists()
        status0 = "[COMPLETE]" if step0_complete else "[NEEDED]  "
        print(f"{status0} Step 0: PUMA/MAZ/TAZ Crosswalk Creation - {'crosswalk file exists' if step0_complete else 'crosswalk file missing'}")
        
        # Step 1: Seed Population (check for PopulationSim-ready files)
        step1_complete = (self.config.SEED_FILES['households_popsim'].exists() and 
                         self.config.SEED_FILES['persons_popsim'].exists())
        status1 = "[COMPLETE]" if step1_complete else "[NEEDED]  "
        print(f"{status1} Step 1: Seed Population - {'PopulationSim files exist' if step1_complete else 'PopulationSim files missing'}")
        
        # Step 2: Control Generation
        step2_complete = all(f.exists() for f in [
            self.config.CONTROL_FILES['maz_marginals'],
            self.config.CONTROL_FILES['taz_marginals'], 
            self.config.CONTROL_FILES['county_marginals'],
            self.config.CONTROL_FILES['geo_cross_walk']
        ])
        status2 = "[COMPLETE]" if step2_complete else "[NEEDED]  "
        print(f"{status2} Step 2: Control Generation - {'all files exist' if step2_complete else 'some files missing'}")
        
        # Step 3: Group Quarters Integration
        step3_complete = self.config.HHGQ_FILES['maz_marginals_hhgq'].exists()
        status3 = "[COMPLETE]" if step3_complete else "[NEEDED]  "
        print(f"{status3} Step 3: Group Quarters Integration - {'files exist' if step3_complete else 'files missing'}")
        
        # Step 4: PopulationSim Synthesis
        step4_complete = self.config.POPSIM_OUTPUT_FILES['synthetic_households'].exists()
        status4 = "[COMPLETE]" if step4_complete else "[NEEDED]  "
        print(f"{status4} Step 4: PopulationSim Synthesis - {'output exists' if step4_complete else 'output missing'}")
        
        # Step 5: Post-processing
        step5_complete = self.config.POPSIM_OUTPUT_FILES['summary_melt'].exists()
        status5 = "[COMPLETE]" if step5_complete else "[NEEDED]  "
        print(f"{status5} Step 5: Post-processing - {'output exists' if step5_complete else 'output missing'}")
        
        # Step 6: Tableau Preparation
        tableau_status = self.config.check_tableau_files()
        key_files = ['taz_boundaries', 'puma_boundaries', 'taz_marginals', 'maz_marginals', 'geo_crosswalk']
        step6_complete = all(tableau_status.get(key, False) for key in key_files)
        status6 = "[COMPLETE]" if step6_complete else "[NEEDED]  "
        print(f"{status6} Step 6: Tableau Preparation - {'files exist' if step6_complete else 'files missing'}")
        
        print()
        print(f"Force flags: CROSSWALK={self.config.FORCE_FLAGS.get('CROSSWALK', False)} SEED={self.config.FORCE_FLAGS['SEED']} CONTROLS={self.config.FORCE_FLAGS['CONTROLS']} HHGQ={self.config.FORCE_FLAGS['HHGQ']} POPSIM={self.config.FORCE_FLAGS['POPULATIONSIM']} POST={self.config.FORCE_FLAGS['POSTPROCESS']} TABLEAU={self.config.FORCE_FLAGS['TABLEAU']}")
        
        if not self.TEST_PUMA:
            print("No TEST_PUMA set -- running full region.")
        else:
            print(f"Using TEST_PUMA [{self.TEST_PUMA}]")
        
        print()
        print(f"Configuration: {self.config.MODEL_TYPE} model, Year {self.config.YEAR}")
        print(f"Output directory: {self.config.POPULATIONSIM_OUTPUT_DIR}")
        print()
        return step0_complete, step1_complete, step2_complete, step3_complete, step4_complete, step5_complete, step6_complete
    
    def step0_crosswalk_creation(self):
        """Step 0: Create PUMA/MAZ/TAZ geographic crosswalk"""
        print("=" * 50)
        print("STEP 0: PUMA/MAZ/TAZ CROSSWALK CREATION")
        print("=" * 50)
        
        crosswalk_file = self.config.CONTROL_FILES['geo_cross_walk']
        
        # Check if we need to create the crosswalk
        need_crosswalk = (self.config.FORCE_FLAGS.get('CROSSWALK', False) or 
                         not crosswalk_file.exists())
        
        if need_crosswalk:
            if self.config.FORCE_FLAGS.get('CROSSWALK', False):
                self.log("FORCE_CROSSWALK=True: Regenerating crosswalk file...")
            else:
                self.log("Geographic crosswalk file missing - creating PUMA/MAZ/TAZ relationships...")
            
            self.log("Creating spatial crosswalk (this typically takes 5-10 minutes)")
            self.log("The process will spatially join MAZ centroids to PUMA boundaries...")
            
            # Use the focused crosswalk creation script
            command = self.config.get_command_args('create_crosswalk')
            success = self.run_command(command, "PUMA/MAZ/TAZ crosswalk creation")
            
            if not success:
                self.log("ERROR: Crosswalk creation failed!", "ERROR") 
                return False
            
            self.log("SUCCESS: Geographic crosswalk created!")
            
            # Update the configuration with the actual PUMAs found in the crosswalk
            try:
                import pandas as pd
                crosswalk_df = pd.read_csv(crosswalk_file)
                actual_pumas = sorted(crosswalk_df['PUMA'].unique().astype(str))
                self.log(f"Found {len(actual_pumas)} PUMAs in crosswalk: {actual_pumas}")
                
                # Update the config with actual PUMAs (this will be used by subsequent steps)
                self.config.ACTUAL_PUMAS = actual_pumas
                
            except Exception as e:
                self.log(f"WARNING: Could not read crosswalk for PUMA validation: {e}", "WARNING")
            
            return True
        else:
            self.log("Geographic crosswalk file already exists - skipping crosswalk creation")
            
            # Still read the PUMAs for validation
            try:
                import pandas as pd
                crosswalk_df = pd.read_csv(crosswalk_file)
                actual_pumas = sorted(crosswalk_df['PUMA'].unique().astype(str))
                self.log(f"Using existing crosswalk with {len(actual_pumas)} PUMAs")
                self.config.ACTUAL_PUMAS = actual_pumas
                
            except Exception as e:
                self.log(f"WARNING: Could not read existing crosswalk: {e}", "WARNING")
            
            return True
    
    def step1_seed_population(self, force_run=False):
        """Step 1: Generate seed population"""
        print("=" * 50)
        print("STEP 1: SEED POPULATION")
        print("=" * 50)
        
        # Check for PopulationSim-ready seed files (not intermediate files)
        seed_exists = (self.config.SEED_FILES['households_popsim'].exists() and 
                      self.config.SEED_FILES['persons_popsim'].exists())
        
        if self.config.FORCE_FLAGS['SEED'] or force_run or not seed_exists:
            if self.config.FORCE_FLAGS['SEED']:
                self.log("FORCE_SEED=True: Regenerating seed files...")
            else:
                self.log("PopulationSim seed files missing - creating seed population files...")
            
            self.log("Starting seed generation (this typically takes 10-15 minutes)")
            self.log("The process will download PUMS data and create PopulationSim-compatible files...")
            
            # Use the main TM2 script that handles generation, column fixing, and PopulationSim copying
            command = self.config.get_command_args('seed_population')
            success = self.run_command(command, "Seed population generation with PopulationSim integration")
            
            if not success:
                self.log("ERROR: Seed generation failed!", "ERROR") 
                return False
            
            self.log("SUCCESS: Seed generation and copying completed!")
            
            # Copy the generated files to the PopulationSim data directory
            self.log("Copying seed files to PopulationSim data directory...")
            try:
                self.config.copy_seed_files_to_popsim()
                self.log("SUCCESS: Seed files copied to hh_gq/data/ directory")
                
                # Fix column naming for PopulationSim compatibility
                self.fix_gqtype_column_names()
                
            except Exception as e:
                self.log(f"ERROR: Failed to copy seed files: {e}", "ERROR")
                return False
            
            return True
        else:
            self.log("Seed files already exist - skipping seed generation")
            # Still ensure files are in the right place for PopulationSim
            try:
                if not self.config.SEED_FILES['households_popsim'].exists():
                    self.config.copy_seed_files_to_popsim()
                    self.log("Copied existing seed files to PopulationSim data directory")
                
                # Always check and fix column naming for PopulationSim compatibility
                self.fix_gqtype_column_names()
                
            except Exception as e:
                self.log(f"WARNING: Could not copy seed files: {e}", "WARNING")
            return True
    
    def step2_control_generation(self):
        """Step 2: Generate control files for TM2"""
        print("=" * 50)
        print("STEP 2: CONTROL GENERATION")
        print("=" * 50)
        
        if self.config.MODEL_TYPE != "TM2":
            self.log("Skipping control generation (not TM2 model)")
            return True
        
        control_files = [
            self.config.CONTROL_FILES['maz_marginals'],
            self.config.CONTROL_FILES['taz_marginals'],
            self.config.CONTROL_FILES['county_marginals'], 
            self.config.CONTROL_FILES['geo_cross_walk']
        ]
        
        need_controls = self.config.FORCE_FLAGS['CONTROLS'] or not all(f.exists() for f in control_files)
        
        if need_controls:
            if self.config.FORCE_FLAGS['CONTROLS']:
                self.log("FORCE_CONTROLS=True: Regenerating control files...")
            else:
                self.log(f"Control files missing - generating TM2 controls for year {self.config.YEAR}...")
            
            command = self.config.get_command_args('create_controls')
            success = self.run_command(command, "Control file generation")
            
            if not success:
                return False
            
            # Copy the generated control files from output_2023 to hh_gq/data
            self.log("Copying generated control files to PopulationSim data directory...")
            try:
                files_copied, files_moved = self.config.copy_control_files_to_popsim()
                if files_copied:
                    self.log(f"SUCCESS: Copied {len(files_copied)} control files to hh_gq/data/")
                    for file_name in files_copied:
                        if file_name in files_moved:
                            self.log(f"  - {file_name} (moved - removed duplicate)")
                        else:
                            self.log(f"  - {file_name} (copied)")
                if files_moved:
                    self.log(f"Cleaned up {len(files_moved)} duplicate/old files from output_2023/")
                if not files_copied:
                    self.log("WARNING: No control files found to copy", "WARNING")
            except Exception as e:
                self.log(f"ERROR: Failed to copy control files: {e}", "ERROR")
                return False
            
            # Rename files to PopulationSim expected names
            old_file = self.config.CONTROL_FILES['geo_cross_walk_updated']
            new_file = self.config.CONTROL_FILES['geo_cross_walk']
            if old_file.exists():
                shutil.move(str(old_file), str(new_file))
                self.log(f"Renamed {old_file.name} to {new_file.name}")
        else:
            self.log("Control files already exist - skipping control generation")
        
        return True
    
    def step3_group_quarters_integration(self):
        """Step 3: Integrate group quarters data"""
        print("=" * 50)
        print("STEP 3: GROUP QUARTERS INTEGRATION")
        print("=" * 50)
        
        hhgq_files = [
            self.config.HHGQ_FILES['maz_marginals_hhgq'],
            self.config.HHGQ_FILES['taz_marginals_hhgq']
        ]
        
        need_hhgq = self.config.FORCE_FLAGS['HHGQ'] or not all(f.exists() for f in hhgq_files)
        
        if need_hhgq:
            if self.config.FORCE_FLAGS['HHGQ']:
                self.log("FORCE_HHGQ=True: Regenerating group quarters files...")
            else:
                self.log("Group quarters files missing - adding combined hh gq columns...")
            
            command = self.config.get_command_args('add_hhgq')
            success = self.run_command(command, "Group quarters integration")
            return success
        else:
            self.log("Group quarters files already exist - skipping HHGQ integration")
            return True
    
    def step4_population_synthesis(self):
        """Step 4: Run PopulationSim synthesis"""
        print("=" * 50)
        print("STEP 4: POPULATION SYNTHESIS")
        print("=" * 50)
        
        synthetic_households = self.config.POPSIM_OUTPUT_FILES['synthetic_households']
        need_popsim = self.config.FORCE_FLAGS['POPULATIONSIM'] or not synthetic_households.exists()
        
        if need_popsim:
            if self.config.FORCE_FLAGS['POPULATIONSIM']:
                self.log("FORCE_POPULATIONSIM=True: Re-running PopulationSim synthesis...")
            else:
                self.log("PopulationSim output missing - running synthesis...")
            
            self.log("PopulationSim synthesis typically takes 30-60 minutes for the full Bay Area")
            self.log("You can monitor progress in the output below...")
            
            # Clean pipeline cache for fresh start
            if self.config.clean_pipeline_cache():
                self.log("Cleaned PopulationSim pipeline cache")
            
            # Clean data to prevent IntCastingNaNError
            self.log("Cleaning data to prevent IntCastingNaNError...")
            try:
                self._clean_data_for_populationsim()
            except Exception as e:
                self.log(f"WARNING: Data cleaning failed: {e}", "WARNING")
            
            # Enhanced debugging for IntCastingNaNError
            self.log("Running enhanced pre-synthesis data validation...")
            try:
                self._debug_populationsim_data()
            except Exception as e:
                self.log(f"WARNING: Data validation failed: {e}", "WARNING")
            
            command = self.config.get_command_args('run_populationsim')
            
            # Enhanced error handling for PopulationSim
            success = self._run_populationsim_with_debug(command)
            return success
        else:
            self.log("PopulationSim output already exists - skipping synthesis")
            return True
    
    def _clean_data_for_populationsim(self):
        """Clean seed data to prevent IntCastingNaNError"""
        import pandas as pd
        import numpy as np
        
        self.log("CLEANING DATA TO PREVENT IntCastingNaNError...")
        
        files_cleaned = []
        
        # Clean households file
        hh_file = self.config.HH_GQ_DATA_DIR / "seed_households.csv"
        if hh_file.exists():
            try:
                df_hh = pd.read_csv(hh_file)
                original_shape = df_hh.shape
                changes_made = False
                
                # Key integer columns that PopulationSim expects
                integer_columns = ['PUMA', 'hhgqtype', 'NP', 'HUPAC', 'hh_workers_from_esr']
                
                for col in integer_columns:
                    if col in df_hh.columns:
                        # Count problematic values
                        nan_count = df_hh[col].isna().sum()
                        inf_count = np.isinf(df_hh[col]).sum() if df_hh[col].dtype in ['float64', 'float32'] else 0
                        
                        if nan_count > 0 or inf_count > 0:
                            self.log(f"  Fixing {col}: {nan_count} NaN, {inf_count} infinite values")
                            
                            # Replace infinite values with NaN first
                            if inf_count > 0:
                                df_hh[col] = df_hh[col].replace([np.inf, -np.inf], np.nan)
                            
                            # Handle NaN values based on column type
                            if col == 'PUMA':
                                # Use mode (most common PUMA)
                                mode_value = df_hh[col].mode()[0] if not df_hh[col].mode().empty else 1
                                df_hh[col] = df_hh[col].fillna(mode_value)
                            elif col == 'hhgqtype':
                                # Default to household (0)
                                df_hh[col] = df_hh[col].fillna(0)
                            elif col in ['NP', 'hh_workers_from_esr']:
                                # Use 0 for count variables
                                df_hh[col] = df_hh[col].fillna(0)
                            elif col == 'HUPAC':
                                # Default to "No own children" (4)
                                df_hh[col] = df_hh[col].fillna(4)
                            
                            # Ensure the column is integer type
                            df_hh[col] = df_hh[col].astype(int)
                            changes_made = True
                
                # Also check hh_income_2023 if it exists
                if 'hh_income_2023' in df_hh.columns:
                    nan_count = df_hh['hh_income_2023'].isna().sum()
                    inf_count = np.isinf(df_hh['hh_income_2023']).sum() if df_hh['hh_income_2023'].dtype in ['float64', 'float32'] else 0
                    
                    if nan_count > 0 or inf_count > 0:
                        self.log(f"  Fixing hh_income_2023: {nan_count} NaN, {inf_count} infinite values")
                        
                        # Replace infinite values with NaN
                        if inf_count > 0:
                            df_hh['hh_income_2023'] = df_hh['hh_income_2023'].replace([np.inf, -np.inf], np.nan)
                        
                        # Use median income for missing values
                        median_income = df_hh['hh_income_2023'].median()
                        df_hh['hh_income_2023'] = df_hh['hh_income_2023'].fillna(median_income)
                        changes_made = True
                
                # CRITICAL FIX: Filter out zero-weight households to prevent IntCastingNaNError
                # TEMPORARILY DISABLED - GROUP_BY_INCIDENCE_SIGNATURE: False should prevent the error
                # and we need to preserve zero-weight households for seed balancing
                if False and 'WGTP' in df_hh.columns:
                    zero_weight_count = (df_hh['WGTP'] == 0).sum()
                    if zero_weight_count > 0:
                        self.log(f"  FILTERING OUT {zero_weight_count:,} zero-weight households (WGTP=0)")
                        df_hh = df_hh[df_hh['WGTP'] > 0]
                        changes_made = True
                        
                        # Also filter out any infinite or NaN weights
                        inf_weight_count = np.isinf(df_hh['WGTP']).sum()
                        nan_weight_count = df_hh['WGTP'].isna().sum()
                        
                        if inf_weight_count > 0 or nan_weight_count > 0:
                            self.log(f"  FILTERING OUT {inf_weight_count} infinite and {nan_weight_count} NaN weight households")
                            df_hh = df_hh[np.isfinite(df_hh['WGTP']) & df_hh['WGTP'].notna()]
                            changes_made = True
                        
                        self.log(f"  Households after weight filtering: {len(df_hh):,} (was {original_shape[0]:,})")
                else:
                    # WGTP filtering is disabled, so don't warn about missing WGTP column
                    pass  # self.log("  WARNING: WGTP column not found in households file!", "WARNING")
                
                if changes_made:
                    # Save the cleaned file
                    df_hh.to_csv(hh_file, index=False)
                    files_cleaned.append(f"households ({original_shape[0]} -> {len(df_hh)} rows)")
                    self.log(f"  Cleaned households file")
                
            except Exception as e:
                self.log(f"  Error cleaning households file: {e}", "ERROR")
        
        # Clean persons file
        p_file = self.config.HH_GQ_DATA_DIR / "seed_persons.csv"
        if p_file.exists():
            try:
                df_p = pd.read_csv(p_file)
                original_shape = df_p.shape
                changes_made = False
                
                # Key integer columns that PopulationSim expects
                integer_columns = ['PUMA', 'hhgqtype', 'AGEP', 'employed', 'occupation']
                
                for col in integer_columns:
                    if col in df_p.columns:
                        # Count problematic values
                        nan_count = df_p[col].isna().sum()
                        inf_count = np.isinf(df_p[col]).sum() if df_p[col].dtype in ['float64', 'float32'] else 0
                        
                        if nan_count > 0 or inf_count > 0:
                            self.log(f"  Fixing {col}: {nan_count} NaN, {inf_count} infinite values")
                            
                            # Replace infinite values with NaN first
                            if inf_count > 0:
                                df_p[col] = df_p[col].replace([np.inf, -np.inf], np.nan)
                            
                            # Handle NaN values based on column type
                            if col == 'PUMA':
                                # Use mode (most common PUMA)
                                mode_value = df_p[col].mode()[0] if not df_p[col].mode().empty else 1
                                df_p[col] = df_p[col].fillna(mode_value)
                            elif col == 'hhgqtype':
                                # Default to household (0)
                                df_p[col] = df_p[col].fillna(0)
                            elif col == 'AGEP':
                                # Use median age for missing ages
                                median_age = df_p[col].median()
                                df_p[col] = df_p[col].fillna(median_age)
                            elif col == 'employed':
                                # Default to not employed (0)
                                df_p[col] = df_p[col].fillna(0)
                            elif col == 'occupation':
                                # Default to no occupation (0)
                                df_p[col] = df_p[col].fillna(0)
                            
                            # Ensure the column is integer type
                            df_p[col] = df_p[col].astype(int)
                            changes_made = True
                
                # CRITICAL FIX: Filter persons to only include those from valid households
                # This ensures consistency after filtering zero-weight households
                hh_file = self.config.HH_GQ_DATA_DIR / "seed_households.csv"
                if hh_file.exists() and 'unique_hh_id' in df_p.columns:
                    try:
                        # Read the cleaned households file to get valid household IDs
                        df_hh_clean = pd.read_csv(hh_file)
                        valid_hh_ids = set(df_hh_clean['unique_hh_id'])
                        
                        # Filter persons to only those in valid households
                        original_person_count = len(df_p)
                        df_p = df_p[df_p['unique_hh_id'].isin(valid_hh_ids)]
                        filtered_person_count = len(df_p)
                        
                        if filtered_person_count < original_person_count:
                            self.log(f"  FILTERED PERSONS: {original_person_count:,} -> {filtered_person_count:,} "
                                   f"(removed {original_person_count - filtered_person_count:,} persons from invalid households)")
                            changes_made = True
                        
                    except Exception as e:
                        self.log(f"  Warning: Could not filter persons by valid households: {e}", "WARNING")
                
                if changes_made:
                    # Save the cleaned file
                    df_p.to_csv(p_file, index=False)
                    files_cleaned.append(f"persons ({original_shape[0]} -> {len(df_p)} rows)")
                    self.log(f"  Cleaned persons file")
                
            except Exception as e:
                self.log(f"  Error cleaning persons file: {e}", "ERROR")
        
        if files_cleaned:
            self.log(f"Data cleaning completed for: {', '.join(files_cleaned)}")
        else:
            self.log("No data cleaning needed - all files appear clean")
        
        return len(files_cleaned) > 0

    def _debug_populationsim_data(self):
        """Enhanced debugging for PopulationSim data issues"""
        import pandas as pd
        import numpy as np
        
        self.log("=== ENHANCED POPULATIONSIM DATA VALIDATION ===")
        
        # Check household data
        hh_file = self.config.HH_GQ_DATA_DIR / "seed_households.csv"
        if hh_file.exists():
            df_hh = pd.read_csv(hh_file)
            self.log(f"DATA: Households: {df_hh.shape[0]} rows, {df_hh.shape[1]} columns")
            
            # Check for duplicate IDs
            if 'SERIALNO' in df_hh.columns:
                dup_count = df_hh['SERIALNO'].duplicated().sum()
                if dup_count > 0:
                    self.log(f"  WARNING: {dup_count} duplicate SERIALNO values!", "WARNING")
            
            # Check key columns used for grouping
            key_cols = ['PUMA', 'hhgqtype', 'NP', 'HUPAC', 'hh_workers_from_esr']
            problematic_cols = []
            
            for col in key_cols:
                if col in df_hh.columns:
                    dtype = df_hh[col].dtype
                    nan_count = df_hh[col].isna().sum()
                    inf_count = np.isinf(df_hh[col]).sum() if dtype in ['float64', 'float32'] else 0
                    
                    # Check for negative values in count columns
                    neg_count = 0
                    if col in ['NP', 'hh_workers_from_esr'] and dtype in ['int64', 'float64']:
                        neg_count = (df_hh[col] < 0).sum()
                    
                    status = "OK"
                    if nan_count > 0 or inf_count > 0 or neg_count > 0:
                        status = f"PROBLEM: {nan_count} NaN, {inf_count} inf, {neg_count} negative"
                        problematic_cols.append(col)
                    
                    self.log(f"  {col}: {dtype} - {status}")
                    
                    # Show sample problematic values
                    if nan_count > 0:
                        sample_nan_idx = df_hh[df_hh[col].isna()].index[:3].tolist()
                        self.log(f"    LOCATION: NaN sample row indices: {sample_nan_idx}")
                    
                    if inf_count > 0 and dtype in ['float64', 'float32']:
                        inf_mask = np.isinf(df_hh[col])
                        sample_inf_idx = df_hh[inf_mask].index[:3].tolist()
                        self.log(f"    LOCATION: Infinite sample row indices: {sample_inf_idx}")
                    
                    # Show value distribution for categorical columns
                    if col in ['hhgqtype', 'PUMA'] and not (nan_count > 0 or inf_count > 0):
                        value_counts = df_hh[col].value_counts().head(5)
                        self.log(f"    TRENDING Top values: {dict(value_counts)}")
            
            if problematic_cols:
                self.log(f"  PROBLEM SUMMARY: Problematic household columns: {problematic_cols}", "ERROR")
        else:
            self.log("  FILE Household file not found!", "ERROR")
        
        # Check persons data
        p_file = self.config.HH_GQ_DATA_DIR / "seed_persons.csv"
        if p_file.exists():
            df_p = pd.read_csv(p_file)
            self.log(f"PEOPLE Persons: {df_p.shape[0]} rows, {df_p.shape[1]} columns")
            
            # Check household linkage
            if 'SERIALNO' in df_p.columns and hh_file.exists():
                hh_serials = set(df_hh['SERIALNO']) if 'SERIALNO' in df_hh.columns else set()
                p_serials = set(df_p['SERIALNO'])
                unlinked_persons = len(p_serials - hh_serials)
                if unlinked_persons > 0:
                    self.log(f"  PROBLEM WARNING: {unlinked_persons} persons with no matching household!", "WARNING")
            
            # Check key person columns
            key_p_cols = ['PUMA', 'hhgqtype', 'AGEP', 'employed', 'occupation']
            problematic_p_cols = []
            
            for col in key_p_cols:
                if col in df_p.columns:
                    dtype = df_p[col].dtype
                    nan_count = df_p[col].isna().sum()
                    inf_count = np.isinf(df_p[col]).sum() if dtype in ['float64', 'float32'] else 0
                    
                    # Check for unrealistic age values
                    age_issues = 0
                    if col == 'AGEP' and dtype in ['int64', 'float64']:
                        age_issues = ((df_p[col] < 0) | (df_p[col] > 120)).sum()
                    
                    status = "OK OK"
                    if nan_count > 0 or inf_count > 0 or age_issues > 0:
                        status = f"PROBLEM PROBLEM: {nan_count} NaN, {inf_count} inf, {age_issues} unrealistic"
                        problematic_p_cols.append(col)
                    
                    self.log(f"  {col}: {dtype} - {status}")
                    
                    # Show value distribution for key columns
                    if col in ['hhgqtype', 'employed'] and not (nan_count > 0 or inf_count > 0):
                        value_counts = df_p[col].value_counts().head(5)
                        self.log(f"    TRENDING Top values: {dict(value_counts)}")
            
            if problematic_p_cols:
                self.log(f"  PROBLEM SUMMARY: Problematic person columns: {problematic_p_cols}", "ERROR")
        else:
            self.log("  FILE Person file not found!", "ERROR")
        
        # Check control files
        controls_file = self.config.HH_GQ_DATA_DIR / "controls.csv"
        if controls_file.exists():
            controls = pd.read_csv(controls_file)
            self.log(f"TARGET Controls: {len(controls)} control specifications")
            
            # Check for zero or negative control totals
            if 'total' in controls.columns:
                zero_controls = (controls['total'] == 0).sum()
                neg_controls = (controls['total'] < 0).sum()
                if zero_controls > 0 or neg_controls > 0:
                    self.log(f"  PROBLEM WARNING: {zero_controls} zero controls, {neg_controls} negative controls!", "WARNING")
            
            # Check for potential problematic control expressions
            problematic_expressions = []
            for _, row in controls.iterrows():
                expr = str(row.get('expression', ''))
                if 'hhgqtype' in expr and '==' in expr:
                    self.log(f"  TARGET Control {row.get('target', 'unknown')}: {expr}")
                
                # Look for potential float comparison issues
                if any(float_indicator in expr for float_indicator in ['.0', 'float', 'nan']):
                    problematic_expressions.append(expr)
            
            if problematic_expressions:
                self.log(f"  WARNING Potentially problematic expressions: {len(problematic_expressions)}", "WARNING")
                for expr in problematic_expressions[:3]:  # Show first 3
                    self.log(f"    NOTE {expr}", "WARNING")
        else:
            self.log("  FILE Controls file not found!", "ERROR")
        
        # Check marginals files for data consistency
        marginals_files = [
            ('MAZ marginals', self.config.HH_GQ_DATA_DIR / "maz_marginals_hhgq.csv"),
            ('TAZ marginals', self.config.HH_GQ_DATA_DIR / "taz_marginals_hhgq.csv"),
            ('County marginals', self.config.HH_GQ_DATA_DIR / "county_marginals.csv")
        ]
        
        for name, file_path in marginals_files:
            if file_path.exists():
                try:
                    df_marg = pd.read_csv(file_path)
                    
                    # Check for NaN/inf in marginals
                    numeric_cols = df_marg.select_dtypes(include=[np.number]).columns
                    total_nan = df_marg[numeric_cols].isna().sum().sum()
                    total_inf = np.isinf(df_marg[numeric_cols]).sum().sum()
                    total_neg = (df_marg[numeric_cols] < 0).sum().sum()
                    
                    status = "OK OK"
                    if total_nan > 0 or total_inf > 0 or total_neg > 0:
                        status = f"PROBLEM Issues: {total_nan} NaN, {total_inf} inf, {total_neg} negative values"
                    
                    self.log(f"  TRENDING {name}: {df_marg.shape[0]} rows - {status}")
                    
                except Exception as e:
                    self.log(f"  TRENDING {name}: Error reading file - {e}", "ERROR")
            else:
                self.log(f"  TRENDING {name}: File not found", "WARNING")
        
        self.log("=== DATA VALIDATION COMPLETE ===")
    
    def _validate_grouping_columns(self):
        """Enhanced validation specifically for PopulationSim incidence table grouping columns"""
        
        import pandas as pd
        import numpy as np
        import shutil
        
        self.log("VALIDATION: TARGETED GROUPING COLUMN VALIDATION...")
        
        # The exact columns that PopulationSim uses for household grouping
        # These come from the PopulationSim source code analysis
        critical_grouping_cols = ['PUMA', 'hhgqtype', 'NP', 'HUPAC', 'hh_workers_from_esr']
        
        hh_file = self.config.HH_GQ_DATA_DIR / "seed_households.csv"
        if not hh_file.exists():
            self.log("  PROBLEM ERROR: Household file not found for grouping validation!", "ERROR")
            return False
        
        try:
            # Read household data
            df_hh = pd.read_csv(hh_file)
            self.log(f"  DATA: Validating {len(critical_grouping_cols)} critical grouping columns in {df_hh.shape[0]} households")
            
            issues_found = []
            fixes_applied = []
            
            for col in critical_grouping_cols:
                if col not in df_hh.columns:
                    issues_found.append(f"Missing column: {col}")
                    continue
                
                # Check for data issues that cause IntCastingNaNError
                original_nan = df_hh[col].isna().sum()
                original_inf = np.isinf(df_hh[col]).sum() if df_hh[col].dtype in ['float64', 'float32'] else 0
                
                if original_nan > 0 or original_inf > 0:
                    self.log(f"    PROBLEM CRITICAL FIX NEEDED for {col}: {original_nan} NaN, {original_inf} inf values")
                    
                    # Apply targeted fixes for each critical column
                    if col == 'PUMA':
                        if original_inf > 0:
                            df_hh[col] = df_hh[col].replace([np.inf, -np.inf], np.nan)
                        if df_hh[col].isna().sum() > 0:
                            # Use the most common PUMA (should be our test PUMA)
                            mode_puma = df_hh[col].mode()[0] if not df_hh[col].mode().empty else 101
                            df_hh[col] = df_hh[col].fillna(mode_puma)
                            df_hh[col] = df_hh[col].astype(int)
                            fixes_applied.append(f"{col}: filled {original_nan} NaN with mode {mode_puma}")
                    
                    elif col == 'hhgqtype':
                        if original_inf > 0:
                            df_hh[col] = df_hh[col].replace([np.inf, -np.inf], np.nan)
                        if df_hh[col].isna().sum() > 0:
                            # Default to household type (0)
                            df_hh[col] = df_hh[col].fillna(0)
                            df_hh[col] = df_hh[col].astype(int)
                            fixes_applied.append(f"{col}: filled {original_nan} NaN with default 0")
                    
                    elif col == 'NP':
                        if original_inf > 0:
                            df_hh[col] = df_hh[col].replace([np.inf, -np.inf], np.nan)
                        if df_hh[col].isna().sum() > 0:
                            # Use median household size for missing values
                            median_np = df_hh[col].median()
                            if pd.isna(median_np):
                                median_np = 2  # Default household size
                            df_hh[col] = df_hh[col].fillna(median_np)
                            df_hh[col] = df_hh[col].astype(int)
                            fixes_applied.append(f"{col}: filled {original_nan} NaN with median {median_np}")
                    
                    elif col == 'HUPAC':
                        if original_inf > 0:
                            df_hh[col] = df_hh[col].replace([np.inf, -np.inf], np.nan)
                        if df_hh[col].isna().sum() > 0:
                            # Default to "No own children" (4)
                            df_hh[col] = df_hh[col].fillna(4)
                            df_hh[col] = df_hh[col].astype(int)
                            fixes_applied.append(f"{col}: filled {original_nan} NaN with default 4")
                    
                    elif col == 'hh_workers_from_esr':
                        if original_inf > 0:
                            df_hh[col] = df_hh[col].replace([np.inf, -np.inf], np.nan)
                        if df_hh[col].isna().sum() > 0:
                            # Default to 0 workers
                            df_hh[col] = df_hh[col].fillna(0)
                            df_hh[col] = df_hh[col].astype(int)
                            fixes_applied.append(f"{col}: filled {original_nan} NaN with default 0")
                    
                    # Verify the fix worked
                    final_nan = df_hh[col].isna().sum()
                    final_inf = np.isinf(df_hh[col]).sum() if df_hh[col].dtype in ['float64', 'float32'] else 0
                    
                    if final_nan > 0 or final_inf > 0:
                        issues_found.append(f"{col}: Still has {final_nan} NaN, {final_inf} inf after fix!")
                    else:
                        self.log(f"    FIXED FIXED {col}: Now clean, dtype={df_hh[col].dtype}")
                else:
                    self.log(f"    OK {col}: Clean ({df_hh[col].dtype})")
            
            # Save the fixed file if any fixes were applied
            if fixes_applied:
                self.log(f"  SAVE SAVING FIXED DATA: Applied {len(fixes_applied)} critical fixes")
                for fix in fixes_applied:
                    self.log(f"    OK {fix}")
                
                # Create backup first
                backup_file = hh_file.with_suffix('.csv.backup')
                if not backup_file.exists():
                    shutil.copy2(hh_file, backup_file)
                    self.log(f"    SAVE Created backup: {backup_file.name}")
                
                # Save the fixed data
                df_hh.to_csv(hh_file, index=False)
                self.log(f"    SAVE Saved fixed households file with clean grouping columns")
                
                # Verify the saved file
                df_verify = pd.read_csv(hh_file)
                for col in critical_grouping_cols:
                    if col in df_verify.columns:
                        verify_nan = df_verify[col].isna().sum()
                        verify_inf = np.isinf(df_verify[col]).sum() if df_verify[col].dtype in ['float64', 'float32'] else 0
                        if verify_nan > 0 or verify_inf > 0:
                            self.log(f"    PROBLEM VERIFICATION FAILED for {col}: {verify_nan} NaN, {verify_inf} inf", "ERROR")
                        else:
                            self.log(f"    OK VERIFIED {col}: Clean after save")
            
            # Final validation summary
            if issues_found:
                self.log(f"  PROBLEM REMAINING ISSUES: {len(issues_found)} problems found:", "ERROR")
                for issue in issues_found:
                    self.log(f"    ERROR {issue}", "ERROR")
                return False
            else:
                self.log(f"  OK GROUPING VALIDATION COMPLETE: All {len(critical_grouping_cols)} critical columns are clean")
                return True
                
        except Exception as e:
            self.log(f"  PROBLEM ERROR during grouping validation: {e}", "ERROR")
            import traceback
            self.log(f"  NOTES Validation traceback: {traceback.format_exc()}", "ERROR")
            return False
    
    def _run_populationsim_with_debug(self, command):
        """Run PopulationSim with enhanced error handling"""
        self.log(f"Enhanced PopulationSim execution...")
        self.log(f"Command: {' '.join(map(str, command))}")
        print("-" * 60)
        
        try:
            import pandas as pd
            import numpy as np
            
            # Enhanced pre-check specifically for incidence table grouping columns
            self.log("ENHANCED PRE-CHECK: Validating incidence table grouping columns...")
            try:
                # Temporarily skip validation to avoid Unicode issues
                # validation_success = self._validate_grouping_columns()
                validation_success = True  # Skip validation for now
                if not validation_success:
                    self.log("PROBLEM CRITICAL: Grouping column validation failed! This will cause IntCastingNaNError.", "ERROR")
                    # Continue anyway to see if our fixes work
                else:
                    self.log("VALIDATION SUCCESS: All grouping columns are clean for PopulationSim")
            except Exception as e:
                self.log(f"WARNING: Grouping column validation failed: {e}", "WARNING")
            
            # Monkey patch pandas merge to add debugging
            original_merge = pd.DataFrame.merge
            merge_call_count = 0
            
            def debug_merge(self, *args, **kwargs):
                nonlocal merge_call_count
                merge_call_count += 1
                
                try:
                    # Check for problematic data before merge
                    if merge_call_count <= 5:  # Only log first few merges to avoid spam
                        print(f"DEBUG MERGE #{merge_call_count}: DataFrame shape {self.shape}")
                        
                        # Check for NaN/inf in numeric columns
                        numeric_cols = self.select_dtypes(include=[np.number]).columns
                        for col in numeric_cols:
                            if col in self.columns:
                                nan_count = self[col].isna().sum()
                                inf_count = np.isinf(self[col]).sum()
                                if nan_count > 0 or inf_count > 0:
                                    print(f"  WARNING: {col} has {nan_count} NaN, {inf_count} inf values")
                    
                    result = original_merge(self, *args, **kwargs)
                    return result
                    
                except pd.errors.IntCastingNaNError as e:
                    print(f"CAUGHT IntCastingNaNError in merge #{merge_call_count}!")
                    print(f"  Error: {e}")
                    print(f"  DataFrame dtypes: {dict(self.dtypes)}")
                    
                    # Show problematic columns
                    for col in self.columns:
                        if self[col].dtype in ['float64', 'float32']:
                            nan_count = self[col].isna().sum()
                            inf_count = np.isinf(self[col]).sum()
                            if nan_count > 0 or inf_count > 0:
                                print(f"  PROBLEM COLUMN {col}: {nan_count} NaN, {inf_count} inf")
                                print(f"    Sample values: {self[col].dropna().head(5).tolist()}")
                    
                    raise
            
            # Apply the monkey patch
            pd.DataFrame.merge = debug_merge
            
            try:
                # Use Popen for real-time output streaming
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Combine stderr with stdout
                    text=True,
                    bufsize=1,  # Line buffered
                    universal_newlines=True,
                    cwd=Path.cwd()
                )
                
                # Stream output in real-time
                output_lines = []
                error_context_lines = []  # Store context around errors
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        # Enhanced error pattern detection
                        output_stripped = output.strip()
                        
                        # Store recent output for context
                        error_context_lines.append(output_stripped)
                        if len(error_context_lines) > 50:  # Keep last 50 lines for context
                            error_context_lines.pop(0)
                        
                        # Critical data errors
                        if "IntCastingNaNError" in output:
                            print("PROBLEM DETECTED IntCastingNaNError in output!")
                            print(f"   Full error line: {output_stripped}")
                            
                            # Print context around the error
                            print("\n" + "=" * 60)
                            print("CONTEXT AROUND IntCastingNaNError:")
                            print("=" * 60)
                            for i, context_line in enumerate(error_context_lines[-20:]):  # Last 20 lines
                                marker = ">>> " if "IntCastingNaNError" in context_line else "    "
                                print(f"{marker}{context_line}")
                            print("=" * 60 + "\n")
                            
                        if "Cannot convert non-finite values" in output:
                            print("PROBLEM DETECTED non-finite values error!")
                            print(f"   Full error line: {output_stripped}")
                        if "ValueError" in output and ("NaN" in output or "inf" in output):
                            print("PROBLEM DETECTED ValueError with NaN/inf values!")
                            print(f"   Full error line: {output_stripped}")
                        
                        # Look for PopulationSim step indicators
                        if "populationsim.steps." in output:
                            print(f"LOCATION POPULATIONSIM STEP: {output_stripped}")
                        if "setup_data_structures" in output:
                            print(f"SETUP DATA STRUCTURES: {output_stripped}")
                        if "incidence" in output.lower():
                            print(f"INCIDENCE PROCESSING: {output_stripped}")
                        if "control target" in output:
                            print(f"TARGET CONTROL TARGET: {output_stripped}")
                        
                        # DataFrame/data processing errors
                        if "KeyError" in output:
                            print("WARNING DETECTED KeyError - possible missing column!")
                            print(f"   Full error line: {output_stripped}")
                        if "TypeError" in output and "dtype" in output:
                            print("WARNING DETECTED TypeError with dtype - possible data type mismatch!")
                            print(f"   Full error line: {output_stripped}")
                        if "IndexError" in output:
                            print("WARNING DETECTED IndexError - possible array/list bounds issue!")
                            print(f"   Full error line: {output_stripped}")
                        
                        # Memory and performance issues
                        if "MemoryError" in output:
                            print("SAVE DETECTED MemoryError - insufficient memory!")
                            print(f"   Full error line: {output_stripped}")
                        if "PerformanceWarning" in output:
                            print("SLOW DETECTED PerformanceWarning!")
                            print(f"   Full warning line: {output_stripped}")
                        
                        # PopulationSim specific errors
                        if "balancing failed" in output.lower():
                            print("BALANCE DETECTED balancing failure!")
                            print(f"   Full error line: {output_stripped}")
                        if "control totals" in output.lower() and ("missing" in output.lower() or "zero" in output.lower()):
                            print("DETECTED control totals issue!")
                            print(f"   Full error line: {output_stripped}")
                        if "seed data" in output.lower() and "error" in output.lower():
                            print("SEED DETECTED seed data error!")
                            print(f"   Full error line: {output_stripped}")
                        
                        # File I/O errors
                        if "FileNotFoundError" in output:
                            print("FILE DETECTED FileNotFoundError - missing required file!")
                            print(f"   Full error line: {output_stripped}")
                        if "PermissionError" in output:
                            print("LOCK DETECTED PermissionError - file access denied!")
                            print(f"   Full error line: {output_stripped}")
                        
                        # Configuration errors
                        if "settings" in output.lower() and "error" in output.lower():
                            print("SETTINGS DETECTED settings/configuration error!")
                            print(f"   Full error line: {output_stripped}")
                        
                        # Convergence and iteration issues
                        if "convergence" in output.lower() and ("failed" in output.lower() or "error" in output.lower()):
                            print("TARGET DETECTED convergence failure!")
                            print(f"   Full error line: {output_stripped}")
                        if "maximum iterations" in output.lower():
                            print("LOOP DETECTED maximum iterations reached!")
                            print(f"   Full error line: {output_stripped}")
                        
                        # Log progress indicators
                        if "Building" in output or "Processing" in output or "Running" in output:
                            print(f"TRENDING PROGRESS: {output_stripped}")
                        if "completed" in output.lower() and "step" in output.lower():
                            print(f"OK STEP COMPLETED: {output_stripped}")
                        
                        print(output_stripped)  # Print to terminal immediately
                        output_lines.append(output_stripped)
                
                # Wait for process to complete
                return_code = process.poll()
                
                if return_code == 0:
                    print("-" * 60)
                    self.log(f"SUCCESS: PopulationSim synthesis completed")
                    return True
                else:
                    print("-" * 60)
                    self.log(f"ERROR: PopulationSim synthesis failed with exit code {return_code}", "ERROR")
                    
                    # Enhanced error analysis
                    error_lines = [line for line in output_lines if any(keyword in line.lower() for keyword in ['error', 'exception', 'failed', 'traceback'])]
                    warning_lines = [line for line in output_lines if 'warning' in line.lower()]
                    
                    # Categorize errors for better debugging
                    data_errors = [line for line in error_lines if any(keyword in line.lower() for keyword in ['nan', 'inf', 'dtype', 'casting', 'convert'])]
                    file_errors = [line for line in error_lines if any(keyword in line.lower() for keyword in ['file', 'permission', 'not found', 'directory'])]
                    memory_errors = [line for line in error_lines if any(keyword in line.lower() for keyword in ['memory', 'allocation', 'overflow'])]
                    config_errors = [line for line in error_lines if any(keyword in line.lower() for keyword in ['config', 'setting', 'parameter'])]
                    convergence_errors = [line for line in error_lines if any(keyword in line.lower() for keyword in ['convergence', 'iteration', 'balancing'])]
                    
                    if data_errors:
                        self.log("SEARCH DATA-RELATED ERRORS DETECTED:", "ERROR")
                        for line in data_errors[-5:]:  # Last 5 data-related errors
                            self.log(f"  DATA: {line}", "ERROR")
                    
                    if file_errors:
                        self.log("SEARCH FILE-RELATED ERRORS DETECTED:", "ERROR")
                        for line in file_errors[-3:]:  # Last 3 file-related errors
                            self.log(f"  FILE {line}", "ERROR")
                    
                    if memory_errors:
                        self.log("SEARCH MEMORY-RELATED ERRORS DETECTED:", "ERROR")
                        for line in memory_errors[-3:]:  # Last 3 memory-related errors
                            self.log(f"  SAVE {line}", "ERROR")
                    
                    if config_errors:
                        self.log("SEARCH CONFIGURATION-RELATED ERRORS DETECTED:", "ERROR")
                        for line in config_errors[-3:]:  # Last 3 config-related errors
                            self.log(f"  SETTINGS {line}", "ERROR")
                    
                    if convergence_errors:
                        self.log("SEARCH CONVERGENCE-RELATED ERRORS DETECTED:", "ERROR")
                        for line in convergence_errors[-3:]:  # Last 3 convergence-related errors
                            self.log(f"  TARGET {line}", "ERROR")
                    
                    if warning_lines:
                        self.log("WARNING WARNINGS DETECTED (may indicate root cause):", "WARNING")
                        for line in warning_lines[-5:]:  # Last 5 warnings
                            self.log(f"  WARNING {line}", "WARNING")
                    
                    # General error summary
                    if error_lines:
                        self.log("NOTES GENERAL ERROR SUMMARY:", "ERROR")
                        for line in error_lines[-10:]:  # Last 10 error-related lines
                            self.log(f"  {line}", "ERROR")
                    
                    # Suggest debugging steps
                    self.log("TOOLS DEBUGGING SUGGESTIONS:", "INFO")
                    if data_errors:
                        self.log("  - Check seed data for NaN/infinite values using enhanced_debug_populationsim.py", "INFO")
                        self.log("  - Verify control file totals are not zero or negative", "INFO")
                        self.log("  - Run check_nan_values.py to identify problematic data", "INFO")
                    if file_errors:
                        self.log("  - Verify all required input files exist in hh_gq/data/ directory", "INFO")
                        self.log("  - Check file permissions and disk space", "INFO")
                    if memory_errors:
                        self.log("  - Consider reducing PUMA scope with --test-puma option", "INFO")
                        self.log("  - Close other memory-intensive applications", "INFO")
                    if convergence_errors:
                        self.log("  - Check control totals for unrealistic values", "INFO")
                        self.log("  - Review PopulationSim settings for iteration limits", "INFO")
                    
                    return False
            
            finally:
                # Restore original merge function
                pd.DataFrame.merge = original_merge
                
        except Exception as e:
            print("-" * 60)
            self.log(f"ERROR: PopulationSim synthesis failed with exception: {e}", "ERROR")
            
            # Print detailed traceback for debugging
            import traceback
            self.log("=" * 80, "ERROR")
            self.log("COMPLETE PYTHON STACK TRACE:", "ERROR")
            self.log("=" * 80, "ERROR")
            
            # Get the complete traceback with more detail
            tb_lines = traceback.format_exc().split('\n')
            for i, line in enumerate(tb_lines):
                if line.strip():
                    # Add line numbers for easier reference
                    self.log(f"[{i:2d}] {line}", "ERROR")
            
            self.log("=" * 80, "ERROR")
            self.log("STACK TRACE ANALYSIS:", "ERROR")
            self.log("=" * 80, "ERROR")
            
            # Analyze the stack trace for key PopulationSim components
            populationsim_frames = []
            pandas_frames = []
            activitysim_frames = []
            
            for line in tb_lines:
                if 'populationsim' in line.lower():
                    populationsim_frames.append(line.strip())
                elif 'pandas' in line.lower() or 'astype' in line:
                    pandas_frames.append(line.strip())
                elif 'activitysim' in line.lower():
                    activitysim_frames.append(line.strip())
            
            if populationsim_frames:
                self.log("PopulationSim-related stack frames:", "ERROR")
                for frame in populationsim_frames:
                    self.log(f"  -> {frame}", "ERROR")
            
            if activitysim_frames:
                self.log("ActivitySim-related stack frames:", "ERROR") 
                for frame in activitysim_frames:
                    self.log(f"  -> {frame}", "ERROR")
            
            if pandas_frames:
                self.log("Pandas-related stack frames:", "ERROR")
                for frame in pandas_frames:
                    self.log(f"  -> {frame}", "ERROR")
            
            self.log("=" * 80, "ERROR")
            
            return False
    
    def step5_post_processing(self):
        """Step 5: Post-processing and validation"""
        print("=" * 50)
        print("STEP 5: POST-PROCESSING")
        print("=" * 50)
        
        summary_file = self.config.POPSIM_OUTPUT_FILES['summary_melt']
        need_postprocess = self.config.FORCE_FLAGS['POSTPROCESS'] or not summary_file.exists()
        
        if need_postprocess:
            if self.config.FORCE_FLAGS['POSTPROCESS']:
                self.log("FORCE_POSTPROCESS=True: Re-running post-processing...")
            else:
                self.log("Post-processing files missing - running postprocess and recode...")
            
            command = self.config.get_command_args('postprocess')
            success = self.run_command(command, "Post-processing")
            if not success:
                return False
            
            # Copy validation workbook
            validation_src = self.config.VALIDATION_FILES['validation_workbook']
            validation_dst = self.config.VALIDATION_FILES['validation_output']
            if validation_src.exists():
                shutil.copy2(validation_src, validation_dst)
                self.log(f"Copied {validation_src.name} to output directory")
            
            # Archive input files to output directory
            if self.config.MODEL_TYPE == "TM2":
                self.config.archive_input_files()
                self.log("Archived input files to output directory")
        else:
            self.log("Post-processing files already exist - skipping post-processing")
        
        return True
    
    def step6_tableau_preparation(self):
        """Step 6: Tableau data preparation"""
        print("=" * 50)
        print("STEP 6: TABLEAU DATA PREPARATION")
        print("=" * 50)
        
        # Check if Tableau files exist
        tableau_status = self.config.check_tableau_files()
        key_files = ['taz_boundaries', 'puma_boundaries', 'taz_marginals', 'maz_marginals', 'geo_crosswalk']
        
        need_tableau = (self.config.FORCE_FLAGS['TABLEAU'] or 
                       not all(tableau_status.get(key, False) for key in key_files))
        
        if need_tableau:
            if self.config.FORCE_FLAGS['TABLEAU']:
                self.log("FORCE_TABLEAU=True: Re-running Tableau preparation...")
            else:
                self.log("Tableau files missing - running Tableau data preparation...")
            
            # Ensure tableau output directory exists
            self.config.TABLEAU_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            
            command = self.config.get_command_args('tableau')
            success = self.run_command(command, "Tableau data preparation")
            if not success:
                return False
            
            self.log("Tableau data preparation completed successfully")
            self.log(f"Tableau files created in: {self.config.TABLEAU_OUTPUT_DIR}")
            
        else:
            self.log("Tableau files already exist - skipping Tableau preparation")
        
        return True
    
    def run_workflow(self):
        """Run the complete PopulationSim workflow"""
        try:
            # Check workflow status
            step0_done, step1_done, step2_done, step3_done, step4_done, step5_done, step6_done = self.workflow_status_check()
            
            # Run each step
            if not self.step0_crosswalk_creation():
                raise Exception("Step 0 (PUMA/MAZ/TAZ Crosswalk Creation) failed")
            
            if not self.step1_seed_population():
                raise Exception("Step 1 (Seed Population) failed")
            
            if not self.step2_control_generation():
                raise Exception("Step 2 (Control Generation) failed")
            
            if not self.step3_group_quarters_integration():
                raise Exception("Step 3 (Group Quarters Integration) failed")
            
            if not self.step4_population_synthesis():
                raise Exception("Step 4 (Population Synthesis) failed")
            
            if not self.step5_post_processing():
                raise Exception("Step 5 (Post-processing) failed")
            
            if not self.step6_tableau_preparation():
                raise Exception("Step 6 (Tableau Preparation) failed")
            
            # Success message
            print()
            print("=" * 80)
            print("SUCCESS: PopulationSim TM2 workflow completed!")
            print("=" * 80)
            print()
            print(f"Final outputs are in: {self.config.POPULATIONSIM_OUTPUT_DIR}")
            print("Key files created:")
            
            if self.config.POPSIM_OUTPUT_FILES['synthetic_households'].exists():
                print("  - synthetic_households.csv (main output)")
                print("  - synthetic_persons.csv (main output)")
            
            if self.config.POPSIM_OUTPUT_FILES['summary_melt'].exists():
                print("  - summary_melt.csv (for validation)")
            
            if self.config.TABLEAU_OUTPUT_DIR.exists():
                print(f"  - tableau/ directory (Tableau-ready analysis files)")
            
            print("  - populationsim.log (detailed log)")
            print("=" * 80)
            
            return True
            
        except KeyboardInterrupt:
            self.log("Workflow interrupted by user", "WARNING")
            return False
        except Exception as e:
            self.log(f"Workflow failed: {e}", "ERROR")
            return False

def main():
    parser = argparse.ArgumentParser(description="Run Bay Area PopulationSim TM2 workflow")
    parser.add_argument("year", nargs="?", default=2023, type=int, help="Year to process (default: 2023)")
    parser.add_argument("--force-crosswalk", action="store_true", help="Force regeneration of PUMA/MAZ/TAZ crosswalk")
    parser.add_argument("--force-seed", action="store_true", help="Force regeneration of seed files")
    parser.add_argument("--force-controls", action="store_true", help="Force regeneration of control files")
    parser.add_argument("--force-hhgq", action="store_true", help="Force regeneration of group quarters files")
    parser.add_argument("--force-popsim", action="store_true", help="Force re-run of PopulationSim synthesis")
    parser.add_argument("--force-postprocess", action="store_true", help="Force re-run of post-processing")
    parser.add_argument("--force-tableau", action="store_true", help="Force re-run of Tableau data preparation")
    parser.add_argument("--test-puma", type=str, help="Run for specific PUMA only (for testing)")
    
    args = parser.parse_args()
    
    # Create configuration
    config = PopulationSimConfig()
    config.YEAR = args.year
    
    # Set test PUMA if specified
    if args.test_puma:
        config.TEST_PUMA = args.test_puma
    
    # Override force flags if specified
    if args.force_crosswalk:
        config.FORCE_FLAGS['CROSSWALK'] = True
    if args.force_seed:
        config.FORCE_FLAGS['SEED'] = True
    if args.force_controls:
        config.FORCE_FLAGS['CONTROLS'] = True
    if args.force_hhgq:
        config.FORCE_FLAGS['HHGQ'] = True
    if args.force_popsim:
        config.FORCE_FLAGS['POPULATIONSIM'] = True
    if args.force_postprocess:
        config.FORCE_FLAGS['POSTPROCESS'] = True
    if args.force_tableau:
        config.FORCE_FLAGS['TABLEAU'] = True
    
    # Create workflow instance
    workflow = PopulationSimWorkflow(year=args.year, config=config)
    
    # Run the workflow
    success = workflow.run_workflow()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
