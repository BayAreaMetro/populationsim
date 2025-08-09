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
    
    def step2_controls(self):
        """Step 2: Generate control files"""
        print("=" * 60)
        print("STEP 2: CONTROL GENERATION")
        print("=" * 60)
        
        if not self.config.FORCE_FLAGS['CONTROLS'] and self.config.check_controls_exist():
            self.log("Control files already exist - skipping")
            return True
        
        return self.run_command(self.config.COMMANDS['controls'], "Control Generation")
    
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
        step_names = ['Crosswalk', 'Seed', 'Controls', 'HHGQ', 'PopulationSim', 'Post-process', 'Tableau']
        
        for i, (step_key, step_name) in enumerate(zip(status.keys(), step_names)):
            status_icon = "✅ COMPLETE" if status[step_key] else "❌ NEEDED"
            print(f"Step {i}: {step_name:<15} - {status_icon}")
        
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
        
        # Filter steps based on start_step
        steps_needed = [s for s in steps_needed if s >= self.start_step]
        
        if not steps_needed:
            self.log(f"🎉 All steps from {self.start_step} onwards are complete! No work needed.")
            return True
        
        self.log(f"Running steps: {steps_needed} (starting from step {self.start_step})")
        
        # Define step functions
        step_functions = [
            self.step0_crosswalk,
            self.step1_seed, 
            self.step2_controls,
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
    parser.add_argument('--start_step', type=int, default=0, choices=range(7),
                        help='Step to start from (0=crosswalk, 1=seed, 2=controls, 3=hhgq, 4=popsim, 5=postprocess, 6=tableau)')
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
