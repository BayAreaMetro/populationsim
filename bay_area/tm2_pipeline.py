#!/usr/bin/env python3
"""
TM2 Pipeline - Single workflow script for the entire Bay Area population synthesis
NO MORE MULTIPLE WORKFLOWS! This is the one and only pipeline script.
Uses UnifiedTM2Config for single source of truth.
"""

import subprocess
import sys
import time
from pathlib import Path
from unified_tm2_config import UnifiedTM2Config

class TM2Pipeline:
    """Complete TM2 population synthesis pipeline with single source of truth"""
    
    def __init__(self, offline_mode=False, verbose=True):
        self.config = UnifiedTM2Config()
        self.config.ensure_directories()
        self.verbose = verbose
        self.offline_mode = offline_mode
        self.fast_mode = False
        self.timeout = 7200  # Default 2 hour timeout
        
    def log(self, message, level="INFO"):
        """Unified logging"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def check_step_completion(self, step_name):
        """Check if step has been completed successfully"""
        step_files = self.config.get_step_files(step_name)
        if not step_files:
            return False
        
        existing = [f for f in step_files if f.exists()]
        if len(existing) == len(step_files):
            self.log(f"Step {step_name} already completed:")
            for f in existing:
                self.log(f"  ✓ {f.name}", "FOUND")
            return True
        elif existing:
            self.log(f"Step {step_name} partially completed ({len(existing)}/{len(step_files)} files):")
            for f in step_files:
                status = "✓" if f.exists() else "✗"
                self.log(f"  {status} {f.name}", "STATUS")
        return False
        
    def run_command(self, command, step_name):
        """Execute a command and handle output with progress monitoring"""
        self.log(f"Running {step_name}: {' '.join(command)}")
        
        start_time = time.time()
        last_log_time = start_time
        
        try:
            if self.verbose:
                # Stream output in real-time with progress monitoring
                process = subprocess.Popen(
                    command,
                    cwd=self.config.BASE_DIR,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                line_count = 0
                for line in process.stdout:
                    print(f"  {line.rstrip()}")
                    line_count += 1
                    
                    # Progress monitoring for long-running steps
                    current_time = time.time()
                    if current_time - last_log_time > 60:  # Every minute
                        elapsed = current_time - start_time
                        self.log(f"[PROGRESS] {step_name} still running... {elapsed:.0f}s elapsed, {line_count} log lines processed")
                        last_log_time = current_time
                
                process.wait()
                returncode = process.returncode
            else:
                result = subprocess.run(
                    command,
                    cwd=self.config.BASE_DIR,
                    capture_output=True,
                    text=True,
                    timeout=7200  # 2 hour timeout
                )
                returncode = result.returncode
                
        except subprocess.TimeoutExpired:
            self.log(f"Step {step_name} timed out after 2 hours", "ERROR")
            return False
        except Exception as e:
            self.log(f"Step {step_name} failed with exception: {e}", "ERROR")
            return False
            
        duration = time.time() - start_time
        
        if returncode == 0:
            self.log(f"Step {step_name} completed successfully in {duration:.1f}s", "SUCCESS")
            return True
        else:
            self.log(f"Step {step_name} failed with code {returncode} after {duration:.1f}s", "ERROR")
            return False
    
    def check_pums_files_exist(self):
        """Check if PUMS files exist (check both current and cached locations)"""
        # Check current location first
        households_current = self.config.PUMS_FILES['households_current']
        persons_current = self.config.PUMS_FILES['persons_current']
        
        if households_current.exists() and persons_current.exists():
            self.log(f"Found PUMS files in current location: {households_current.parent}")
            return True
            
        # Check cached location
        households_cached = self.config.PUMS_FILES['households_cached']
        persons_cached = self.config.PUMS_FILES['persons_cached']
        
        if households_cached.exists() and persons_cached.exists():
            self.log(f"Found PUMS files in cached location: {households_cached.parent}")
            return True
            
        return False

    def run_step(self, step_name, force=False):
        """Run a specific pipeline step"""
        
        self.log(f"{'='*60}")
        self.log(f"STEP {step_name.upper()}")
        self.log(f"{'='*60}")
        
        # Check if already completed
        if not force and self.check_step_completion(step_name):
            self.log(f"Skipping {step_name} (already completed, use --force to rerun)")
            return True
        
        # Get command for this step
        command = self.config.get_command(step_name)
        
        # Check for special steps that are handled internally (not via external commands)
        special_steps = ['geographic_rebuild']
        if not command and step_name not in special_steps:
            self.log(f"Unknown step: {step_name}", "ERROR")
            return False
        
        # Special handling for PUMS download
        if step_name == 'pums':
            # Skip if files already exist and not forced
            if not force and self.check_pums_files_exist():
                self.log("Skipping PUMS download (files already exist, use --force to redownload)")
                return True
            # Skip if in offline mode
            if self.offline_mode:
                self.log("Skipping PUMS download (offline mode enabled)", "WARN")
                if not self.check_pums_files_exist():
                    self.log("ERROR: PUMS files not found and offline mode enabled", "ERROR")
                    return False
                return True
            self.log("Downloading PUMS data...")
        
        # Special handling for geographic rebuild
        elif step_name == 'geographic_rebuild':
            return self.run_geographic_rebuild()
        
        # Special handling for PopulationSim with log monitoring
        elif step_name == 'populationsim':
            # Prepare PopulationSim data directory first
            if not self.prepare_populationsim_data():
                self.log("Failed to prepare PopulationSim data", "ERROR")
                return False
                
            # Fix crosswalk before running PopulationSim
            if not self.fix_crosswalk_multi_puma():
                self.log("Failed to fix crosswalk - this may cause NaN control aggregation issues", "ERROR")
                return False
                
            return self.run_populationsim_with_monitoring(command)
        else:
            return self.run_command(command, step_name)
    
    def fix_county_codes(self):
        """Fix county codes to use sequential 1-9 numbering expected by PopulationSim"""
        import pandas as pd
        import os
        
        self.log("Converting county codes to sequential 1-9 numbering (matching working 2015 version)...")
        
        try:
            data_dir = self.config.DATA_DIR
            
            # Get the FIPS-to-sequential mapping from config
            fips_to_sequential = self.config.get_fips_to_sequential_mapping()
            
            self.log(f"FIPS to sequential mapping: {fips_to_sequential}")
            
            # Load and update crosswalk
            crosswalk_path = self.config.CROSSWALK_FILES['main_crosswalk']
            if not crosswalk_path.exists():
                self.log(f"Crosswalk file not found: {crosswalk_path}", "ERROR")
                return False
                
            crosswalk_df = pd.read_csv(crosswalk_path)
            self.log(f"Original crosswalk counties: {sorted(crosswalk_df['COUNTY'].unique())}")
            
            # Convert crosswalk county codes
            crosswalk_df['COUNTY'] = crosswalk_df['COUNTY'].map(fips_to_sequential)
            unmapped_crosswalk = crosswalk_df[crosswalk_df['COUNTY'].isna()]
            if len(unmapped_crosswalk) > 0:
                self.log(f"WARNING: {len(unmapped_crosswalk)} crosswalk records have unmapped counties", "WARN")
                return False
                
            crosswalk_df.to_csv(crosswalk_path, index=False)
            self.log(f"Updated crosswalk counties: {sorted(crosswalk_df['COUNTY'].unique())}")
            
            # Create PUMA to sequential county mapping
            puma_county_map = crosswalk_df[['PUMA', 'COUNTY']].drop_duplicates().set_index('PUMA')['COUNTY'].to_dict()
            self.log(f"PUMA to sequential county mapping: {puma_county_map}")
            
            # Update county marginals controls
            county_controls_path = os.path.join(data_dir, "county_marginals.csv")
            if os.path.exists(county_controls_path):
                county_controls_df = pd.read_csv(county_controls_path)
                self.log(f"Original control counties: {sorted(county_controls_df['COUNTY'].unique())}")
                
                county_controls_df['COUNTY'] = county_controls_df['COUNTY'].map(fips_to_sequential)
                unmapped_controls = county_controls_df[county_controls_df['COUNTY'].isna()]
                if len(unmapped_controls) > 0:
                    self.log(f"WARNING: {len(unmapped_controls)} control records have unmapped counties", "WARN")
                    return False
                    
                county_controls_df.to_csv(county_controls_path, index=False)
                self.log(f"Updated control counties: {sorted(county_controls_df['COUNTY'].unique())}")
            
            # Fix households file
            households_path = os.path.join(data_dir, "seed_households.csv")
            if not os.path.exists(households_path):
                self.log(f"Households file not found: {households_path}", "ERROR")
                return False
                
            self.log("Updating households data...")
            households_df = pd.read_csv(households_path)
            
            # Map PUMA to sequential county
            households_df['COUNTY'] = households_df['PUMA'].map(puma_county_map)
            
            # Check for any unmapped PUMAs
            unmapped = households_df[households_df['COUNTY'].isna()]
            if len(unmapped) > 0:
                self.log(f"ERROR: {len(unmapped)} households have unmapped PUMAs", "ERROR")
                return False
            
            households_df.to_csv(households_path, index=False)
            self.log(f"Updated {len(households_df)} household records with sequential county codes")
            
            # Fix persons file
            persons_path = os.path.join(data_dir, "seed_persons.csv")
            if not os.path.exists(persons_path):
                self.log(f"Persons file not found: {persons_path}", "ERROR")
                return False
                
            self.log("Updating persons data...")
            persons_df = pd.read_csv(persons_path)
            
            # Map PUMA to sequential county
            persons_df['COUNTY'] = persons_df['PUMA'].map(puma_county_map)
            
            # Check for any unmapped PUMAs
            unmapped = persons_df[persons_df['COUNTY'].isna()]
            if len(unmapped) > 0:
                self.log(f"ERROR: {len(unmapped)} persons have unmapped PUMAs", "ERROR")
                return False
            
            persons_df.to_csv(persons_path, index=False)
            self.log(f"Updated {len(persons_df)} person records with sequential county codes")
            
            self.log("✓ Successfully converted all data to sequential 1-9 county numbering", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Error fixing county codes: {e}", "ERROR")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}", "ERROR")
            return False
    
    def run_geographic_rebuild(self):
        """Rebuild complete geographic crosswalk from 2010 Census blocks"""
        try:
            from tm2_control_utils.config_census import rebuild_maz_taz_all_geog_file
            
            self.log("Rebuilding complete geographic crosswalk from 2010 Census blocks...")
            
            # Use unified config paths
            blocks_file = self.config.TM2PY_UTILS_BLOCKS_FILE
            output_dir = self.config.PRIMARY_OUTPUT_DIR
            
            self.log(f"Source blocks file: {blocks_file}")
            self.log(f"Output directory: {output_dir}")
            
            # Call the rebuild function - pass None for output_path to use default
            success = rebuild_maz_taz_all_geog_file(blocks_file, None)
            
            if success:
                self.log("✓ Successfully rebuilt complete geographic crosswalk", "SUCCESS")
                return True
            else:
                self.log("Failed to rebuild geographic crosswalk", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error rebuilding geographic crosswalk: {e}", "ERROR")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}", "ERROR")
            return False
    
    def fix_crosswalk_multi_puma(self):
        """Fix crosswalk to resolve TAZs assigned to multiple PUMAs (root cause of NaN control aggregation)"""
        import pandas as pd
        import os
        
        self.log("Fixing crosswalk: resolving TAZs with multiple PUMA assignments...")
        
        try:
            data_dir = self.config.DATA_DIR
            crosswalk_file = os.path.join(data_dir, "geo_cross_walk_tm2.csv")
            
            if not os.path.exists(crosswalk_file):
                self.log(f"Crosswalk file not found: {crosswalk_file}", "ERROR")
                return False
            
            # Load existing crosswalk
            crosswalk = pd.read_csv(crosswalk_file)
            self.log(f"Original crosswalk: {len(crosswalk):,} records")
            
            # Identify TAZs with multiple PUMA assignments
            taz_puma_counts = crosswalk.groupby('TAZ')['PUMA'].nunique()
            multi_puma_tazs = taz_puma_counts[taz_puma_counts > 1].index.tolist()
            
            if len(multi_puma_tazs) == 0:
                self.log("No multi-PUMA TAZs found - crosswalk is already clean!")
                return True
            
            self.log(f"Found {len(multi_puma_tazs)} TAZs with multiple PUMA assignments")
            
            # Show examples
            for taz in multi_puma_tazs[:3]:
                taz_data = crosswalk[crosswalk['TAZ'] == taz]
                puma_counts = taz_data['PUMA'].value_counts()
                self.log(f"  TAZ {taz}: {dict(puma_counts)}")
            
            # Fix assignments using majority rule (PUMA with most MAZs for each TAZ)
            fixed_crosswalk = crosswalk.copy()
            
            for taz in multi_puma_tazs:
                taz_data = crosswalk[crosswalk['TAZ'] == taz]
                
                # Find PUMA with most MAZs for this TAZ
                puma_counts = taz_data['PUMA'].value_counts()
                majority_puma = puma_counts.index[0]
                
                # Update all MAZs in this TAZ to use the majority PUMA
                mask = fixed_crosswalk['TAZ'] == taz
                fixed_crosswalk.loc[mask, 'PUMA'] = majority_puma
            
            # Verify the fix
            taz_puma_counts_fixed = fixed_crosswalk.groupby('TAZ')['PUMA'].nunique()
            remaining_multi_puma = taz_puma_counts_fixed[taz_puma_counts_fixed > 1]
            
            if len(remaining_multi_puma) > 0:
                self.log(f"ERROR: {len(remaining_multi_puma)} TAZs still have multiple PUMAs!", "ERROR")
                return False
            
            # Save the fixed crosswalk (backup original first)
            backup_file = crosswalk_file + ".backup"
            if not os.path.exists(backup_file):
                crosswalk.to_csv(backup_file, index=False)
                self.log(f"Backed up original crosswalk to: {backup_file}")
            
            fixed_crosswalk.to_csv(crosswalk_file, index=False)
            self.log(f"✓ Fixed crosswalk saved: {len(fixed_crosswalk):,} records")
            self.log(f"✓ All {fixed_crosswalk['TAZ'].nunique():,} TAZs now have unique PUMA assignments")
            self.log("✓ This should resolve the NaN control aggregation issue", "SUCCESS")
            
            return True
            
        except Exception as e:
            self.log(f"Error fixing crosswalk: {e}", "ERROR")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}", "ERROR")
            return False
    
    def prepare_populationsim_data(self):
        """Prepare PopulationSim data directory with proper file structure and symbolic links"""
        import os
        from pathlib import Path
        
        self.log("Preparing PopulationSim data directory...")
        
    def prepare_populationsim_data(self):
        """Prepare PopulationSim data directory with proper file structure and symbolic links"""
        import os
        from pathlib import Path
        
        self.log("Preparing PopulationSim data directory...")
        
        try:
            # Target directory (where PopulationSim expects files)
            target_dir = Path(self.config.POPSIM_DATA_DIR)
            
            # Files that PopulationSim needs
            required_files = [
                'seed_households.csv',
                'seed_persons.csv', 
                'geo_cross_walk_tm2.csv',
                'maz_marginals.csv',
                'taz_marginals.csv',
                'county_marginals.csv'
            ]
            
            # Check if files are already in target location (unified config approach)
            all_files_present = True
            for filename in required_files:
                target_file = target_dir / filename
                if target_file.exists():
                    self.log(f"✓ Found: {filename}")
                else:
                    all_files_present = False
                    # Try to find in source directory (legacy approach)
                    source_dir = Path(self.config.OUTPUT_DIR)
                    source_file = source_dir / filename
                    
                    if source_file.exists():
                        # Create symbolic link (Windows) 
                        try:
                            target_file.symlink_to(source_file)
                            self.log(f"✓ Linked: {filename}")
                        except OSError:
                            # Fallback to copy if symlink fails
                            import shutil
                            shutil.copy2(source_file, target_file)
                            self.log(f"✓ Copied: {filename} (symlink failed)")
                    else:
                        self.log(f"ERROR: Required file not found: {filename} (checked both {target_file} and {source_file})", "ERROR")
                        return False
            
            if all_files_present:
                self.log("✓ All required files already in PopulationSim data directory", "SUCCESS")
            
            self.log("✓ PopulationSim data directory prepared successfully", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Error preparing PopulationSim data: {e}", "ERROR")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}", "ERROR")
            return False

    def run_populationsim_with_monitoring(self, command):
        """Run PopulationSim with enhanced progress monitoring"""
        import threading
        import time
        from pathlib import Path
        
        self.log("Starting PopulationSim with enhanced monitoring...")
        
        # Fix county codes in seed data before running PopulationSim
        # Note: Both seed and control data are already using consistent FIPS codes
        # so skipping the county fix for now to test if the original system works
        # if not self.fix_county_codes():
        #     self.log("Failed to fix county codes", "ERROR")
        #     return False
        
        # DISABLED: Fast mode settings were causing data corruption (NaN values)
        # Using regular settings.yaml for all runs to ensure data integrity
        if hasattr(self, 'fast_mode') and self.fast_mode:
            self.log("[WARNING] Fast mode disabled - fast settings were causing NaN control values")
            self.log("[INFO] Using regular settings.yaml to ensure data integrity")
            # Don't modify the command - use regular settings
        
        # Log file path
        log_file = self.config.OUTPUT_DIR / "populationsim.log"
        
        # Start the process
        process = subprocess.Popen(
            command,
            cwd=self.config.BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Monitor function
        def monitor_progress():
            last_size = 0
            silent_time = 0
            last_activity = time.time()
            warning_sent = False
            
            while process.poll() is None:
                time.sleep(30)  # Check every 30 seconds
                
                # Check log file activity
                if log_file.exists():
                    current_size = log_file.stat().st_size
                    if current_size > last_size:
                        last_activity = time.time()
                        last_size = current_size
                        silent_time = 0
                        warning_sent = False
                    else:
                        silent_time = time.time() - last_activity
                        
                    if silent_time > 120 and not warning_sent:  # Silent for more than 2 minutes
                        self.log(f"[MONITOR] PopulationSim silent for {silent_time:.0f}s - checking progress...")
                        try:
                            # Show last few lines of log
                            with open(log_file, 'r') as f:
                                lines = f.readlines()
                                if len(lines) >= 3:
                                    self.log(f"[MONITOR] Recent log entries:")
                                    for line in lines[-3:]:
                                        self.log(f"[LOG]     {line.strip()}")
                        except Exception:
                            pass
                            
                    if silent_time > 600:  # Silent for more than 10 minutes
                        if not warning_sent:
                            self.log(f"[WARNING] PopulationSim has been silent for {silent_time:.0f}s - may be in integerization step", "WARN")
                            self.log(f"[INFO] Integerization can take 10-30 minutes for large datasets", "INFO")
                            warning_sent = True
                            
                    if silent_time > self.timeout:  # Timeout reached
                        self.log(f"[TIMEOUT] PopulationSim has been silent for {silent_time:.0f}s - terminating", "ERROR")
                        process.terminate()
                        return
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_progress, daemon=True)
        monitor_thread.start()
        
        # Stream output
        start_time = time.time()
        for line in process.stdout:
            print(f"  {line.rstrip()}")
        
        returncode = process.wait()
        duration = time.time() - start_time
        
        if returncode == 0:
            self.log(f"PopulationSim completed successfully in {duration:.1f}s", "SUCCESS")
            return True
        else:
            self.log(f"PopulationSim failed with code {returncode} after {duration:.1f}s", "ERROR")
            return False
    
    def run_full_pipeline(self, start_step=None, end_step=None, force=False):
        """Run the complete pipeline or a subset"""
        
        # Default pipeline includes geographic rebuild before controls
        steps = ['crosswalk', 'geographic_rebuild', 'seed', 'controls', 'populationsim', 'postprocess', 'analysis']
        
        # If start_step is explicitly 'pums', include it
        if start_step == 'pums':
            steps = ['crosswalk', 'pums', 'geographic_rebuild', 'seed', 'controls', 'populationsim', 'postprocess', 'analysis']
        
        # Determine step range
        if start_step:
            try:
                start_idx = steps.index(start_step)
                steps = steps[start_idx:]
            except ValueError:
                self.log(f"Invalid start step: {start_step}", "ERROR")
                return False
                
        if end_step:
            try:
                end_idx = steps.index(end_step) + 1
                steps = steps[:end_idx]
            except ValueError:
                self.log(f"Invalid end step: {end_step}", "ERROR")
                return False
        
        self.log(f"Running pipeline steps: {' → '.join(steps)}")
        
        # Run each step
        overall_start = time.time()
        for step in steps:
            if not self.run_step(step, force):
                self.log(f"Pipeline failed at step: {step}", "ERROR")
                return False
                
        overall_duration = time.time() - overall_start
        self.log(f"{'='*60}")
        self.log(f"PIPELINE COMPLETED SUCCESSFULLY in {overall_duration:.1f}s", "SUCCESS")
        self.log(f"{'='*60}")
        return True
    
    def status(self):
        """Show status of all pipeline steps"""
        self.log("Pipeline Status Check")
        self.log("-" * 40)
        
        steps = ['crosswalk', 'pums', 'geographic_rebuild', 'seed', 'controls', 'populationsim', 'postprocess', 'analysis']
        for step in steps:
            if self.check_step_completion(step):
                self.log(f"{step.ljust(15)}: ✓ COMPLETE", "STATUS")
            else:
                self.log(f"{step.ljust(15)}: ✗ INCOMPLETE", "STATUS")
    
    def clean(self, step_name=None):
        """Clean outputs for a specific step or all steps"""
        if step_name:
            steps = [step_name]
        else:
            steps = ['crosswalk', 'pums', 'seed', 'controls', 'populationsim']
            
        for step in steps:
            step_files = self.config.get_step_files(step)
            if step_files:
                for f in step_files:
                    if f.exists():
                        f.unlink()
                        self.log(f"Removed: {f.name}")
                self.log(f"Cleaned step: {step}")

def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TM2 Population Synthesis Pipeline")
    parser.add_argument('command', nargs='?', default='status',
                       choices=['status', 'pums', 'crosswalk', 'geographic_rebuild', 'seed', 'controls', 'populationsim', 'postprocess', 'analysis', 'full', 'clean'],
                       help='Command to run')
    parser.add_argument('--force', action='store_true',
                       help='Force rerun even if outputs exist')
    parser.add_argument('--start', help='Start step for full pipeline')
    parser.add_argument('--end', help='End step for full pipeline')
    parser.add_argument('--offline', action='store_true',
                       help='Run in offline mode (no external data downloads)')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce output verbosity')
    parser.add_argument('--fast', action='store_true',
                       help='Use fast mode settings (relaxed tolerances)')
    parser.add_argument('--timeout', type=int, default=7200,
                       help='Timeout in seconds for PopulationSim (default: 7200 = 2 hours)')
    
    args = parser.parse_args()
    
    # Create pipeline
    pipeline = TM2Pipeline(offline_mode=args.offline, verbose=not args.quiet)
    
    # Set fast mode if requested
    if args.fast:
        pipeline.fast_mode = True
        pipeline.timeout = args.timeout
        pipeline.log("Fast mode enabled - using relaxed tolerances for speed")
    
    # Execute command
    if args.command == 'status':
        pipeline.status()
    elif args.command == 'full':
        success = pipeline.run_full_pipeline(args.start, args.end, args.force)
        sys.exit(0 if success else 1)
    elif args.command == 'clean':
        step = getattr(args, 'step', None)
        pipeline.clean(step)
    else:
        success = pipeline.run_step(args.command, args.force)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
