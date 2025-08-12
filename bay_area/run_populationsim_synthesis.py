#!/usr/bin/env python3
"""
PopulationSim runner script for TM2 Bay Area
Enhanced with detailed progress logging to track synthesis progress
Based on the original PopulationSim execution pattern
"""

import os
import sys
import time
import logging
import threading
import argparse
from datetime import datetime
from pathlib import Path

from activitysim.core import config

from activitysim.core import tracing
from activitysim.core import pipeline
from activitysim.core import inject

from activitysim.core.tracing import print_elapsed_time
from activitysim.core.config import handle_standard_args

from populationsim import steps
from activitysim.core.config import setting
from populationsim import lp
from populationsim import multi_integerizer

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run PopulationSim synthesis")
    parser.add_argument("--working_dir", type=str, required=True,
                       help="Working directory for PopulationSim")
    parser.add_argument("--output", type=str, required=True,
                       help="Output directory for results")
    parser.add_argument("--test_PUMA", type=str, default=None,
                       help="Test with specific PUMA only")
    return parser.parse_args()

# Parse command line arguments
args = parse_arguments()

# Change to the working directory
working_dir = Path(args.working_dir)
if not working_dir.exists():
    raise FileNotFoundError(f"Working directory does not exist: {working_dir}")

print(f"Changing to working directory: {working_dir}")
os.chdir(working_dir)

# Enhanced logging setup
def setup_enhanced_logging():
    """Setup detailed logging for PopulationSim progress tracking"""
    
    # Create a custom logger for progress tracking
    progress_logger = logging.getLogger('popsim_progress')
    progress_logger.setLevel(logging.INFO)
    
    # Create console handler with detailed format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Create detailed formatter (no Unicode characters)
    formatter = logging.Formatter(
        '[%(asctime)s] [POPSIM] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Only add handler if not already present
    if not progress_logger.handlers:
        progress_logger.addHandler(console_handler)
    
    return progress_logger

def log_step_progress(step_name, step_num, total_steps, start_time):
    """Log progress for each PopulationSim step"""
    elapsed = time.time() - start_time
    progress_logger = logging.getLogger('popsim_progress')
    
    progress_logger.info(f"STEP {step_num}/{total_steps}: {step_name}")
    progress_logger.info(f"  Elapsed time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    progress_logger.info(f"  Memory usage: {get_memory_usage()}")

def get_memory_usage():
    """Get current memory usage"""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        return f"{memory_mb:.1f} MB"
    except ImportError:
        return "Unknown (psutil not available)"

# Global heartbeat control
heartbeat_active = False
heartbeat_thread = None
current_step_name = "initialization"

def start_heartbeat_logging():
    """Start heartbeat logging thread"""
    global heartbeat_active, heartbeat_thread
    
    if heartbeat_thread and heartbeat_thread.is_alive():
        return  # Already running
    
    heartbeat_active = True
    
    def heartbeat_worker():
        """Background worker that logs every 5 minutes"""
        progress_logger = logging.getLogger('popsim_progress')
        last_log_time = time.time()
        
        while heartbeat_active:
            time.sleep(30)  # Check every 30 seconds
            
            if not heartbeat_active:
                break
                
            current_time = time.time()
            if current_time - last_log_time >= 300:  # 5 minutes = 300 seconds
                progress_logger.info(f"[HEARTBEAT] PopulationSim still running... {datetime.now().strftime('%H:%M:%S')}")
                progress_logger.info(f"[HEARTBEAT] Current step: {current_step_name}")
                progress_logger.info(f"[HEARTBEAT] Memory usage: {get_memory_usage()}")
                progress_logger.info(f"[HEARTBEAT] Total elapsed: {(current_time - synthesis_start_time)/60:.1f} minutes")
                
                # Also check the PopulationSim log for actual progress
                log_file = os.path.join("output", "populationsim.log")
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            if lines:
                                last_line = lines[-1].strip()
                                progress_logger.info(f"[HEARTBEAT] PopulationSim last activity: {last_line}")
                                
                                # Extract step info from log line
                                if "integerize_final_seed_weights" in last_line:
                                    progress_logger.info(f"[HEARTBEAT] Status: Integerizing final seed weights (this can take 30+ minutes)")
                                elif "final_seed_balancing" in last_line and "seed id" in last_line:
                                    seed_id = last_line.split("seed id ")[-1].strip()
                                    progress_logger.info(f"[HEARTBEAT] Status: Balancing seed {seed_id}")
                                elif "seed_balancer status" in last_line:
                                    progress_logger.info(f"[HEARTBEAT] Status: Seed balancing in progress")
                    except Exception as e:
                        progress_logger.warning(f"[HEARTBEAT] Could not read PopulationSim log: {e}")
                
                last_log_time = current_time
    
    heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
    heartbeat_thread.start()
    progress_logger.info("[HEARTBEAT] Started 5-minute progress logging with PopulationSim log monitoring")

def stop_heartbeat_logging():
    """Stop heartbeat logging thread"""
    global heartbeat_active
    heartbeat_active = False
    progress_logger = logging.getLogger('popsim_progress')
    progress_logger.info("[HEARTBEAT] Stopped progress logging")

def set_current_step(step_name):
    """Update the current step name for heartbeat logging"""
    global current_step_name
    current_step_name = step_name

# Setup enhanced logging
progress_logger = setup_enhanced_logging()

progress_logger.info("=" * 80)
progress_logger.info("STARTING POPULATIONSIM SYNTHESIS")
progress_logger.info("=" * 80)
progress_logger.info(f"Working directory: {working_dir}")
progress_logger.info(f"Output directory: {args.output}")
progress_logger.info(f"Current working directory: {os.getcwd()}")

# Start heartbeat logging for long-running processes
start_heartbeat_logging()

handle_standard_args()

tracing.config_logger()

# Track overall synthesis start time
synthesis_start_time = time.time()
t0 = print_elapsed_time()

logger = logging.getLogger('populationsim')

progress_logger.info("PopulationSim Configuration:")
progress_logger.info(f"  Working directory: {os.getcwd()}")
progress_logger.info(f"  Python executable: {sys.executable}")

logger.info("GROUP_BY_INCIDENCE_SIGNATURE: %s"
            % setting('GROUP_BY_INCIDENCE_SIGNATURE'))
logger.info("INTEGERIZE_WITH_BACKSTOPPED_CONTROLS: %s"
            % setting('INTEGERIZE_WITH_BACKSTOPPED_CONTROLS'))
logger.info("SUB_BALANCE_WITH_FLOAT_SEED_WEIGHTS: %s"
            % setting('SUB_BALANCE_WITH_FLOAT_SEED_WEIGHTS'))
logger.info("meta_control_data: %s"
            % setting('meta_control_data'))
logger.info("control_file_name: %s"
            % setting('control_file_name'))

progress_logger.info("PopulationSim Settings:")
progress_logger.info(f"  GROUP_BY_INCIDENCE_SIGNATURE: {setting('GROUP_BY_INCIDENCE_SIGNATURE')}")
progress_logger.info(f"  INTEGERIZE_WITH_BACKSTOPPED_CONTROLS: {setting('INTEGERIZE_WITH_BACKSTOPPED_CONTROLS')}")
progress_logger.info(f"  SUB_BALANCE_WITH_FLOAT_SEED_WEIGHTS: {setting('SUB_BALANCE_WITH_FLOAT_SEED_WEIGHTS')}")

logger.info("USE_CVXPY: %s" % lp.use_cvxpy())
logger.info("USE_SIMUL_INTEGERIZER: %s" % multi_integerizer.use_simul_integerizer())

progress_logger.info(f"  USE_CVXPY: {lp.use_cvxpy()}")
progress_logger.info(f"  USE_SIMUL_INTEGERIZER: {multi_integerizer.use_simul_integerizer()}")


# get the run list (name was possibly specified on the command line with the -m option)
run_list_name = inject.get_injectable('run_list_name', 'run_list')

# run list from settings file is dict with list of 'steps' and optional 'resume_after'
run_list = setting(run_list_name)
assert 'steps' in run_list, "Did not find steps in run_list"

# list of steps and possible resume_after in run_list
steps = run_list.get('steps')
resume_after = run_list.get('resume_after', None)

# they may have overridden resume_after on command line
resume_after = inject.get_injectable('resume_after', resume_after)

progress_logger.info("PopulationSim Execution Plan:")
progress_logger.info(f"  Total steps: {len(steps)}")
progress_logger.info(f"  Steps to run: {steps}")
if resume_after:
    progress_logger.info(f"  Resuming after: {resume_after}")

progress_logger.info("=" * 80)
progress_logger.info("BEGINNING POPULATIONSIM PIPELINE EXECUTION")
progress_logger.info("=" * 80)

# Track pipeline execution with detailed logging
class PopulationSimProgressMonitor:
    """Monitor PopulationSim pipeline progress"""
    
    def __init__(self, steps_list):
        self.steps_list = steps_list
        self.current_step = 0
        self.total_steps = len(steps_list)
        self.step_start_time = None
        
    def log_step_start(self, step_name):
        """Log when a step starts"""
        self.current_step += 1
        self.step_start_time = time.time()
        elapsed_total = time.time() - synthesis_start_time
        
        # Update current step for heartbeat
        set_current_step(step_name)
        
        progress_logger.info(f"STEP {self.current_step}/{self.total_steps}: {step_name}")
        progress_logger.info(f"  Total elapsed: {elapsed_total:.1f}s ({elapsed_total/60:.1f}min)")
        progress_logger.info(f"  Memory: {get_memory_usage()}")
        progress_logger.info(f"  Time: {datetime.now().strftime('%H:%M:%S')}")
        
        # Special note for integerization step
        if 'integerize' in step_name.lower():
            progress_logger.info(f"  NOTE: {step_name} can take 10-30 minutes for large datasets")
            progress_logger.info(f"  NOTE: Heartbeat logs will appear every 5 minutes during long steps")
        
    def log_step_complete(self, step_name):
        """Log when a step completes"""
        if self.step_start_time:
            step_duration = time.time() - self.step_start_time
            progress_logger.info(f"  COMPLETED: {step_name} in {step_duration:.1f}s")
        
# Create progress monitor
monitor = PopulationSimProgressMonitor(steps)

# Log each step as it executes
for i, step_name in enumerate(steps, 1):
    monitor.log_step_start(step_name)
    
# Run the pipeline
try:
    progress_logger.info("Executing PopulationSim pipeline...")
    pipeline.run(models=steps, resume_after=resume_after)
    progress_logger.info("PopulationSim pipeline completed successfully!")
    
except Exception as e:
    stop_heartbeat_logging()  # Stop heartbeat on error
    progress_logger.error(f"PopulationSim pipeline failed: {str(e)}")
    progress_logger.error(f"Error type: {type(e).__name__}")
    raise


# tables will no longer be available after pipeline is closed
pipeline.close_pipeline()

# Calculate total synthesis time
total_synthesis_time = time.time() - synthesis_start_time

# Stop heartbeat logging
stop_heartbeat_logging()

progress_logger.info("=" * 80)
progress_logger.info("POPULATIONSIM SYNTHESIS COMPLETE!")
progress_logger.info("=" * 80)
progress_logger.info(f"Total synthesis time: {total_synthesis_time:.1f}s ({total_synthesis_time/60:.1f}min)")
progress_logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
progress_logger.info(f"Final memory usage: {get_memory_usage()}")

# write checkpoints (this can be called whether or not pipeline is open)
# file_path = os.path.join(inject.get_injectable("output_dir"), "checkpoints.csv")
# pipeline.get_checkpoints().to_csv(file_path)
t0 = print_elapsed_time("all models", t0)
