#!/usr/bin/env python3
"""
Unified TM2 PopulationSim Workflow
Clean, simple workflow orchestrator with unified configuration
NO MORE FILE COPYING MADNESS!
"""

import subprocess
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Import our unified configuration
from unified_tm2_config import config

class UnifiedWorkflow:
    """Clean workflow orchestrator"""
    
    def __init__(self, start_step=0, force_all=False):
        self.config = config
        self.start_time = datetime.now()
        self.start_step = start_step
        self.force_all = force_all
    
    def log(self, message):
        """Simple logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def run_command(self, command, step_name):
        """Run a command with proper error handling"""
        self.log(f"Running: {' '.join(str(c) for c in command)}")
        
        try:
            result = subprocess.run(
                command,
                cwd=str(self.config.BASE_DIR),
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout:
                print(result.stdout)
            
            self.log(f"✅ {step_name} completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"❌ {step_name} failed with exit code {e.returncode}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            return False
    
    def step0_crosswalk(self):
        """Step 0: Create geographic crosswalk"""
        print("=" * 60)
        print("STEP 0: GEOGRAPHIC CROSSWALK CREATION")
        print("=" * 60)
        
        if not self.config.FORCE_FLAGS['CROSSWALK'] and self.config.check_crosswalk_exists():
            self.log("Crosswalk already exists - skipping")
            return True
        
        return self.run_command(self.config.COMMANDS['crosswalk'], "Crosswalk Creation")
    
    def step1_seed(self):
        """Step 1: Generate seed population"""
        print("=" * 60)
        print("STEP 1: SEED POPULATION GENERATION")
        print("=" * 60)
        
        if not self.config.FORCE_FLAGS['SEED'] and self.config.check_seed_exists():
            self.log("Seed files already exist - skipping")
            return True
        
        return self.run_command(self.config.COMMANDS['seed'], "Seed Generation")
    
    def step1_5_validation(self):
        """Step 1.5: Validation check between seed and controls (OBSOLETE - moved to step 2.5)"""
        print("=" * 60)
        print("STEP 1.5: SEED & CONTROLS VALIDATION (OBSOLETE)")
        print("=" * 60)
        self.log("This step is obsolete - validation moved to after controls generation")
        return True
    
    def step2_controls(self):
        """Step 2: Generate control files"""
        print("=" * 60)
        print("STEP 2: CONTROL GENERATION")
        print("=" * 60)
        
        if not self.config.FORCE_FLAGS['CONTROLS'] and self.config.check_controls_exist():
            self.log("Control files already exist - skipping")
            return True
        
        return self.run_command(self.config.COMMANDS['controls'], "Control Generation")
    
    def step2_5_validation_post_controls(self):
        """Step 2.5: Post-controls validation check"""
        print("=" * 60)
        print("STEP 2.5: POST-CONTROLS VALIDATION")
        print("=" * 60)
        
        # Run the validation script using unified config's Python executable
        validation_command = [
            str(self.config.PYTHON_EXE),
            str(self.config.BASE_DIR / "check_controls_2_seed.py")
        ]
        
        self.log("Running final validation to ensure seed and controls are fully compatible...")
        return self.run_command(validation_command, "Final Seed & Controls Validation")
    
    def step3_hhgq(self):
        """Step 3: Group quarters integration"""
        print("=" * 60)
        print("STEP 3: GROUP QUARTERS INTEGRATION")
        print("=" * 60)
        
        if not self.config.FORCE_FLAGS['HHGQ'] and self.config.check_hhgq_exists():
            self.log("Group quarters files already exist - skipping")
            return True
        
        # Sync control files before running
        self.log("Syncing files for group quarters integration...")
        self.config.sync_files_for_step(3)
        
        return self.run_command(self.config.COMMANDS['hhgq'], "Group Quarters Integration")
    
    def step4_populationsim(self):
        """Step 4: PopulationSim synthesis"""
        print("=" * 60)
        print("STEP 4: POPULATIONSIM SYNTHESIS")
        print("=" * 60)
        
        if not self.config.FORCE_FLAGS['POPSIM'] and self.config.check_popsim_output_exists():
            self.log("PopulationSim output already exists - skipping")
            return True
        
        # Sync all files before running PopulationSim
        self.log("Syncing files for PopulationSim...")
        self.config.sync_files_for_step(4)
        
        return self.run_command(self.config.COMMANDS['populationsim'], "PopulationSim Synthesis")
    
    def step5_postprocess(self):
        """Step 5: Post-processing"""
        print("=" * 60)
        print("STEP 5: POST-PROCESSING")
        print("=" * 60)
        
        if not self.config.FORCE_FLAGS['POSTPROCESS'] and self.config.check_postprocess_exists():
            self.log("Post-processing output already exists - skipping")
            return True
        
        return self.run_command(self.config.COMMANDS['postprocess'], "Post-processing")
    
    def step6_tableau(self):
        """Step 6: Tableau preparation"""
        print("=" * 60)
        print("STEP 6: TABLEAU PREPARATION")
        print("=" * 60)
        
        if not self.config.FORCE_FLAGS['TABLEAU'] and self.config.check_tableau_exists():
            self.log("Tableau files already exist - skipping")
            return True
        
        return self.run_command(self.config.COMMANDS['tableau'], "Tableau Preparation")
    
    def print_status(self):
        """Print workflow status"""
        print("=" * 80)
        print("    Bay Area PopulationSim TM2 Workflow (UNIFIED)")
        print("=" * 80)
        print()
        
        status, steps_needed = self.config.get_workflow_status()
        
        print("===== WORKFLOW STATUS =====")
        step_names = ['Crosswalk', 'Seed', 'Seed-Validation', 'Controls', 'Controls-Validation', 'HHGQ', 'PopulationSim', 'Post-process', 'Tableau']
        base_status = ['crosswalk', 'seed', 'controls', 'hhgq', 'popsim', 'postprocess', 'tableau']
        
        step_counter = 0
        for i, base_step in enumerate(base_status):
            # Show base step
            status_icon = "✅ COMPLETE" if status[base_step] else "❌ NEEDED"
            print(f"Step {step_counter}: {step_names[step_counter]:<18} - {status_icon}")
            step_counter += 1
            
            # Add validation steps after seed and controls
            if base_step in ['seed', 'controls']:
                print(f"Step {step_counter}: {step_names[step_counter]:<18} - 🔍 VALIDATION")
                step_counter += 1
        
        print()
        print(f"Force flags: {self.config.FORCE_FLAGS}")
        print(f"Test PUMA: {self.config.TEST_PUMA or 'None (full region)'}")
        print(f"Model: {self.config.MODEL_TYPE}, Year: {self.config.YEAR}")
        print(f"PopulationSim Output: {self.config.POPSIM_OUTPUT_DIR}")
        print()
        
        return steps_needed
    
    def run_workflow(self):
        """Run the complete workflow"""
        # Override force flags if specified
        if self.force_all:
            print(f"🔥 Force mode enabled - will regenerate files from step {self.start_step} onwards")
            for key in self.config.FORCE_FLAGS:
                self.config.FORCE_FLAGS[key] = True
        
        steps_needed = self.print_status()
        
        # Create list of all steps to run based on what's needed and start_step
        all_steps_to_run = []
        
        # Map original steps to new step numbers
        step_mapping = {0: 0, 1: 1, 2: 3, 3: 5, 4: 6, 5: 7, 6: 8}  # original -> new step numbers
        
        for original_step in steps_needed:
            new_step = step_mapping[original_step]
            if new_step >= self.start_step:
                all_steps_to_run.append(new_step)
                
                # Add validation steps only after controls (3) - need both seed AND controls for validation
                if new_step == 3:  # After controls  
                    all_steps_to_run.append(4)  # Post-controls validation
        
        steps_needed = sorted(set(all_steps_to_run))
        
        if not steps_needed:
            self.log(f"🎉 All steps from {self.start_step} onwards are complete! No work needed.")
            return True
        
        self.log(f"Running steps: {steps_needed} (starting from step {self.start_step})")
        
        # Define step functions
        step_functions = [
            self.step0_crosswalk,
            self.step1_seed,
            self.step1_5_validation,
            self.step2_controls,
            self.step2_5_validation_post_controls,
            self.step3_hhgq,
            self.step4_populationsim,
            self.step5_postprocess,
            self.step6_tableau
        ]
        
        # Run needed steps
        for step_num in steps_needed:
            if not step_functions[step_num]():
                self.log(f"❌ Workflow failed at step {step_num}")
                return False
        
        elapsed = datetime.now() - self.start_time
        self.log(f"🎉 Workflow completed successfully in {elapsed}")
        return True

def main():
    """Main entry point with command line argument support"""
    parser = argparse.ArgumentParser(description='Unified TM2 PopulationSim Workflow')
    parser.add_argument('--start_step', type=int, default=0, choices=range(9),
                        help='Step to start from (0=crosswalk, 1=seed, 2=validation, 3=controls, 4=validation, 5=hhgq, 6=popsim, 7=postprocess, 8=tableau)')
    parser.add_argument('--force_all_steps', action='store_true',
                        help='Force regeneration of all files')
    parser.add_argument('--force_remaining_steps', action='store_true',
                        help='Force regeneration from start_step onwards')
    
    args = parser.parse_args()
    
    # Determine force setting
    force_all = args.force_all_steps or args.force_remaining_steps
    
    workflow = UnifiedWorkflow(start_step=args.start_step, force_all=force_all)
    success = workflow.run_workflow()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
