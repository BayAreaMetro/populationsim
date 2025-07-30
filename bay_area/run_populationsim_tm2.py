#!/usr/bin/env python3
"""
Python script to run the population simulation for the Bay Area TM2
Replaces run_populationsim_tm2.bat with better error handling and cross-platform support

Usage: python run_populationsim_tm2.py [year]
Example: python run_populationsim_tm2.py 2023
"""

import os
import sys
import shutil
import subprocess
import argparse
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
        print(f"[{timestamp}] {level}: {message}")
    
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
        
        # Step 1: Seed Population
        step1_complete = self.config.SEED_FILES['households_processed'].exists()
        status1 = "[COMPLETE]" if step1_complete else "[NEEDED]  "
        print(f"{status1} Step 1: Seed Population - {'files exist' if step1_complete else 'files missing'}")
        
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
        print(f"Force flags: SEED={self.config.FORCE_FLAGS['SEED']} CONTROLS={self.config.FORCE_FLAGS['CONTROLS']} HHGQ={self.config.FORCE_FLAGS['HHGQ']} POPSIM={self.config.FORCE_FLAGS['POPULATIONSIM']} POST={self.config.FORCE_FLAGS['POSTPROCESS']} TABLEAU={self.config.FORCE_FLAGS['TABLEAU']}")
        
        if not self.TEST_PUMA:
            print("No TEST_PUMA set -- running full region.")
        else:
            print(f"Using TEST_PUMA [{self.TEST_PUMA}]")
        
        print()
        print(f"Configuration: {self.config.MODEL_TYPE} model, Year {self.config.YEAR}")
        print(f"Output directory: {self.config.POPULATIONSIM_OUTPUT_DIR}")
        print()
        input("Press Enter to continue or Ctrl+C to stop...")
        return step1_complete, step2_complete, step3_complete, step4_complete, step5_complete, step6_complete
    
    def step1_seed_population(self, force_run=False):
        """Step 1: Generate seed population"""
        print("=" * 50)
        print("STEP 1: SEED POPULATION")
        print("=" * 50)
        
        seed_exists = self.config.SEED_FILES['households_processed'].exists()
        
        if self.config.FORCE_FLAGS['SEED'] or force_run or not seed_exists:
            if self.config.FORCE_FLAGS['SEED']:
                self.log("FORCE_SEED=True: Regenerating seed files...")
            else:
                self.log("Seed files missing - creating seed population files...")
            
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
            
            command = self.config.get_command_args('run_populationsim')
            success = self.run_command(command, "PopulationSim synthesis")
            return success
        else:
            self.log("PopulationSim output already exists - skipping synthesis")
            return True
    
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
            step1_done, step2_done, step3_done, step4_done, step5_done, step6_done = self.workflow_status_check()
            
            # Run each step
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
