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

class PopulationSimWorkflow:
    def __init__(self, year=2023):
        # Configuration flags - set to True to force step execution
        self.FORCE_SEED = True
        self.FORCE_CONTROLS = False
        self.FORCE_HHGQ = False
        self.FORCE_POPULATIONSIM = False
        self.FORCE_POSTPROCESS = False
        
        # Environment setup
        self.CONDA_PATH = Path("C:/Users/schildress/AppData/Local/anaconda3")
        self.POPSIM_ENV = "popsim"
        self.PYTHON_PATH = self.CONDA_PATH / "envs" / self.POPSIM_ENV / "python.exe"
        
        # Model configuration
        self.MODELTYPE = "TM2"
        self.YEAR = str(year)
        self.TMPATH = "output_2023"
        
        # Output directory
        self.OUTPUT_DIR = Path("output_2023/populationsim_run")
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        
        # Test PUMA configuration
        self.TEST_PUMA = None  # Set to PUMA code for testing, None for full region
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
        """Run a subprocess command with error handling"""
        self.log(f"{description}...")
        self.log(f"Command: {' '.join(map(str, command))}")
        
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            self.log(f"SUCCESS: {description} completed")
            if result.stdout.strip():
                print(result.stdout)
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"ERROR: {description} failed with exit code {e.returncode}", "ERROR")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            return False
        except Exception as e:
            self.log(f"ERROR: {description} failed with exception: {e}", "ERROR")
            return False
    
    def check_file_exists(self, filepath):
        """Check if a file exists"""
        return Path(filepath).exists()
    
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
        step1_complete = self.check_file_exists("hh_gq/data/seed_households.csv")
        status1 = "[COMPLETE]" if step1_complete else "[NEEDED]  "
        print(f"{status1} Step 1: Seed Population - {'files exist' if step1_complete else 'files missing'}")
        
        # Step 2: Control Generation
        control_files = [
            "hh_gq/data/maz_marginals.csv",
            "hh_gq/data/taz_marginals.csv", 
            "hh_gq/data/county_marginals.csv",
            "hh_gq/data/geo_cross_walk_tm2.csv"
        ]
        step2_complete = all(self.check_file_exists(f) for f in control_files)
        status2 = "[COMPLETE]" if step2_complete else "[NEEDED]  "
        print(f"{status2} Step 2: Control Generation - {'all files exist' if step2_complete else 'some files missing'}")
        
        # Step 3: Group Quarters Integration
        step3_complete = self.check_file_exists("hh_gq/data/maz_marginals_hhgq.csv")
        status3 = "[COMPLETE]" if step3_complete else "[NEEDED]  "
        print(f"{status3} Step 3: Group Quarters Integration - {'files exist' if step3_complete else 'files missing'}")
        
        # Step 4: PopulationSim Synthesis
        step4_complete = self.check_file_exists(self.OUTPUT_DIR / "synthetic_households.csv")
        status4 = "[COMPLETE]" if step4_complete else "[NEEDED]  "
        print(f"{status4} Step 4: PopulationSim Synthesis - {'output exists' if step4_complete else 'output missing'}")
        
        # Step 5: Post-processing
        step5_complete = self.check_file_exists(self.OUTPUT_DIR / "summary_melt.csv")
        status5 = "[COMPLETE]" if step5_complete else "[NEEDED]  "
        print(f"{status5} Step 5: Post-processing - {'output exists' if step5_complete else 'output missing'}")
        
        print()
        print(f"Force flags: SEED={self.FORCE_SEED} CONTROLS={self.FORCE_CONTROLS} HHGQ={self.FORCE_HHGQ} POPSIM={self.FORCE_POPULATIONSIM} POST={self.FORCE_POSTPROCESS}")
        
        if not self.TEST_PUMA:
            print("No TEST_PUMA set -- running full region.")
        else:
            print(f"Using TEST_PUMA [{self.TEST_PUMA}]")
        
        print()
        input("Press Enter to continue or Ctrl+C to stop...")
        return step1_complete, step2_complete, step3_complete, step4_complete, step5_complete
    
    def step1_seed_population(self, force_run=False):
        """Step 1: Generate seed population"""
        print("=" * 50)
        print("STEP 1: SEED POPULATION")
        print("=" * 50)
        
        seed_exists = self.check_file_exists("hh_gq/data/seed_households.csv")
        
        if self.FORCE_SEED or force_run or not seed_exists:
            if self.FORCE_SEED:
                self.log("FORCE_SEED=True: Regenerating seed files...")
            else:
                self.log("Seed files missing - creating seed population files...")
            
            self.log("Starting seed generation (this typically takes 10-15 minutes)")
            
            # Use the main TM2 script that handles generation, column fixing, and PopulationSim copying
            command = [str(self.PYTHON_PATH), "create_seed_population_tm2.py"]
            success = self.run_command(command, "Seed population generation with PopulationSim integration")
            
            if not success:
                self.log("ERROR: Seed generation failed!", "ERROR") 
                return False
            
            self.log("SUCCESS: Seed generation and copying completed!")
            return True
        else:
            self.log("Seed files already exist - skipping seed generation")
            return True
    
    def step2_control_generation(self):
        """Step 2: Generate control files for TM2"""
        print("=" * 50)
        print("STEP 2: CONTROL GENERATION")
        print("=" * 50)
        
        if self.MODELTYPE != "TM2":
            self.log("Skipping control generation (not TM2 model)")
            return True
        
        control_files = [
            "hh_gq/data/maz_marginals.csv",
            "hh_gq/data/taz_marginals.csv",
            "hh_gq/data/county_marginals.csv", 
            "hh_gq/data/geo_cross_walk_tm2.csv"
        ]
        
        need_controls = self.FORCE_CONTROLS or not all(self.check_file_exists(f) for f in control_files)
        
        if need_controls:
            if self.FORCE_CONTROLS:
                self.log("FORCE_CONTROLS=True: Regenerating control files...")
            else:
                self.log(f"Control files missing - generating TM2 controls for year {self.YEAR}...")
            
            command = [str(self.PYTHON_PATH), "create_baseyear_controls_23_tm2.py", "--output_dir", "hh_gq/data"]
            success = self.run_command(command, "Control file generation")
            
            if not success:
                return False
            
            # Rename files to PopulationSim expected names
            old_file = Path("hh_gq/data/geo_cross_walk_tm2_updated.csv")
            new_file = Path("hh_gq/data/geo_cross_walk_tm2.csv")
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
            "hh_gq/data/maz_marginals_hhgq.csv",
            "hh_gq/data/taz_marginals_hhgq.csv"
        ]
        
        need_hhgq = self.FORCE_HHGQ or not all(self.check_file_exists(f) for f in hhgq_files)
        
        if need_hhgq:
            if self.FORCE_HHGQ:
                self.log("FORCE_HHGQ=True: Regenerating group quarters files...")
            else:
                self.log("Group quarters files missing - adding combined hh gq columns...")
            
            command = [str(self.PYTHON_PATH), "add_hhgq_combined_controls.py", "--model_type", self.MODELTYPE]
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
        
        synthetic_households = self.OUTPUT_DIR / "synthetic_households.csv"
        need_popsim = self.FORCE_POPULATIONSIM or not synthetic_households.exists()
        
        if need_popsim:
            if self.FORCE_POPULATIONSIM:
                self.log("FORCE_POPULATIONSIM=True: Re-running PopulationSim synthesis...")
            else:
                self.log("PopulationSim output missing - running synthesis...")
            
            command = [
                str(self.PYTHON_PATH), "run_populationsim.py",
                "--config", f"hh_gq/configs_{self.MODELTYPE}",
                "--output", str(self.OUTPUT_DIR),
                "--data", "hh_gq/data"
            ]
            
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
        
        summary_file = self.OUTPUT_DIR / "summary_melt.csv"
        need_postprocess = self.FORCE_POSTPROCESS or not summary_file.exists()
        
        if need_postprocess:
            if self.FORCE_POSTPROCESS:
                self.log("FORCE_POSTPROCESS=True: Re-running post-processing...")
            else:
                self.log("Post-processing files missing - running postprocess and recode...")
            
            command = [
                str(self.PYTHON_PATH), "postprocess_recode.py",
                *self.TEST_PUMA_FLAG,
                "--model_type", self.MODELTYPE,
                "--directory", str(self.OUTPUT_DIR),
                "--year", self.YEAR
            ]
            
            success = self.run_command(command, "Post-processing")
            if not success:
                return False
            
            # Copy validation workbook
            validation_src = Path("validation.twb")
            validation_dst = self.OUTPUT_DIR / "validation.twb"
            if validation_src.exists():
                shutil.copy2(validation_src, validation_dst)
                self.log(f"Copied {validation_src} to output directory")
            
            # Archive input files to output directory
            if self.MODELTYPE == "TM2":
                input_files = [
                    "hh_gq/data/maz_marginals.csv",
                    "hh_gq/data/taz_marginals.csv",
                    "hh_gq/data/county_marginals.csv",
                    "hh_gq/data/geo_cross_walk_tm2.csv"
                ]
                
                for file_path in input_files:
                    src = Path(file_path)
                    if src.exists():
                        dst = self.OUTPUT_DIR / src.name
                        shutil.copy2(src, dst)
                        self.log(f"Archived {src.name} to output directory")
        else:
            self.log("Post-processing files already exist - skipping post-processing")
        
        return True
    
    def run_workflow(self):
        """Run the complete PopulationSim workflow"""
        try:
            # Check workflow status
            step1_done, step2_done, step3_done, step4_done, step5_done = self.workflow_status_check()
            
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
            
            # Success message
            print()
            print("=" * 80)
            print("SUCCESS: PopulationSim TM2 workflow completed!")
            print("=" * 80)
            print()
            print(f"Final outputs are in: {self.OUTPUT_DIR}")
            print("Key files created:")
            
            if (self.OUTPUT_DIR / "synthetic_households.csv").exists():
                print("  - synthetic_households.csv (main output)")
                print("  - synthetic_persons.csv (main output)")
            
            if (self.OUTPUT_DIR / "summary_melt.csv").exists():
                print("  - summary_melt.csv (for validation)")
            
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
    
    args = parser.parse_args()
    
    # Create workflow instance
    workflow = PopulationSimWorkflow(year=args.year)
    
    # Override force flags if specified
    if args.force_seed:
        workflow.FORCE_SEED = True
    if args.force_controls:
        workflow.FORCE_CONTROLS = True
    if args.force_hhgq:
        workflow.FORCE_HHGQ = True
    if args.force_popsim:
        workflow.FORCE_POPULATIONSIM = True
    if args.force_postprocess:
        workflow.FORCE_POSTPROCESS = True
    
    # Run the workflow
    success = workflow.run_workflow()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
