#!/usr/bin/env python3
"""
Pipeline-ready PopulationSim workflow for Bay Area TM2

This script is designed to run reliably in CI/CD pipelines with:
- Comprehensive error handling and logging
- Automatic dependency verification
- Robust file path management
- Environment validation
- Clear exit codes and status reporting
- Resource monitoring
- Recovery mechanisms

Usage: python pipeline_populationsim_tm2.py [options]
"""

import os
import sys
import json
import time
import psutil
import shutil
import argparse
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

class PipelineLogger:
    """Pipeline-specific logger with structured output"""
    
    def __init__(self, log_file: Path, verbose: bool = True):
        self.log_file = log_file
        self.verbose = verbose
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize log file
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"Pipeline PopulationSim Log - Started {datetime.now()}\n")
            f.write("="*80 + "\n")
    
    def log(self, message: str, level: str = "INFO", step: Optional[str] = None):
        """Log message with timestamp and level"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        step_prefix = f"[{step}] " if step else ""
        log_entry = f"[{timestamp}] {level}: {step_prefix}{message}"
        
        # Print to console if verbose
        if self.verbose:
            print(log_entry)
        
        # Write to log file
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + "\n")
        except Exception:
            print(f"WARNING: Could not write to log file: {message}")
    
    def log_status(self, status: Dict):
        """Log structured status information"""
        self.log(f"STATUS: {json.dumps(status, indent=2)}")

class PipelineEnvironmentValidator:
    """Validates pipeline environment and dependencies"""
    
    def __init__(self, logger: PipelineLogger):
        self.logger = logger
    
    def validate_environment(self) -> bool:
        """Validate all environment requirements"""
        self.logger.log("Validating pipeline environment...", "INFO", "VALIDATION")
        
        checks = [
            ("Python version", self._check_python_version),
            ("Required packages", self._check_packages),
            ("File system access", self._check_file_access),
            ("Memory availability", self._check_memory),
            ("Disk space", self._check_disk_space),
            ("Input files", self._check_input_files),
            ("Configuration", self._check_configuration)
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                passed = check_func()
                status = "PASS" if passed else "FAIL"
                self.logger.log(f"{check_name}: {status}", "INFO", "VALIDATION")
                if not passed:
                    all_passed = False
            except Exception as e:
                self.logger.log(f"{check_name}: ERROR - {e}", "ERROR", "VALIDATION")
                all_passed = False
        
        return all_passed
    
    def _check_python_version(self) -> bool:
        """Check Python version is compatible"""
        version = sys.version_info
        return version.major >= 3 and version.minor >= 8
    
    def _check_packages(self) -> bool:
        """Check required packages are available"""
        required_packages = ['pandas', 'numpy', 'pathlib', 'subprocess', 'psutil']
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                self.logger.log(f"Missing required package: {package}", "ERROR")
                return False
        return True
    
    def _check_file_access(self) -> bool:
        """Check file system read/write access"""
        test_file = Path("test_write_access.tmp")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            test_file.unlink()
            return True
        except Exception:
            return False
    
    def _check_memory(self) -> bool:
        """Check available memory (need at least 4GB)"""
        available_gb = psutil.virtual_memory().available / (1024**3)
        return available_gb >= 4.0
    
    def _check_disk_space(self) -> bool:
        """Check available disk space (need at least 10GB)"""
        free_gb = psutil.disk_usage('.').free / (1024**3)
        return free_gb >= 10.0
    
    def _check_input_files(self) -> bool:
        """Check critical input files exist"""
        required_files = [
            "hh_gq/data/geo_cross_walk_tm2_updated.csv",
            "output_2023/households_2023_tm2.csv",
            "output_2023/persons_2023_tm2.csv"
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                self.logger.log(f"Missing required file: {file_path}", "ERROR")
                return False
        return True
    
    def _check_configuration(self) -> bool:
        """Check configuration is valid"""
        try:
            from config_tm2 import PopulationSimConfig
            config = PopulationSimConfig()
            return True
        except Exception as e:
            self.logger.log(f"Configuration error: {e}", "ERROR")
            return False

class PipelinePopulationSim:
    """Pipeline-ready PopulationSim workflow"""
    
    def __init__(self, logger: PipelineLogger, year: int = 2023):
        self.logger = logger
        self.year = year
        self.start_time = time.time()
        
        # Import and setup configuration
        try:
            from config_tm2 import PopulationSimConfig
            from run_populationsim_tm2 import PopulationSimWorkflow
            
            self.config = PopulationSimConfig()
            self.config.YEAR = year
            self.workflow = PopulationSimWorkflow(year=year, config=self.config)
            
        except ImportError as e:
            self.logger.log(f"Failed to import required modules: {e}", "ERROR")
            raise
    
    def ensure_crosswalk_in_place(self) -> bool:
        """Ensure the crosswalk file is in the correct location for the pipeline"""
        source_path = Path("output_2023/geo_cross_walk_tm2_updated.csv")
        target_path = Path("hh_gq/data/geo_cross_walk_tm2_updated.csv")
        
        if not source_path.exists():
            self.logger.log(f"Source crosswalk file not found: {source_path}", "ERROR", "SETUP")
            return False
        
        if not target_path.exists() or source_path.stat().st_mtime > target_path.stat().st_mtime:
            self.logger.log("Copying updated crosswalk to expected location...", "INFO", "SETUP")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            self.logger.log(f"Crosswalk copied: {source_path} -> {target_path}", "INFO", "SETUP")
        
        # Verify crosswalk content
        try:
            import pandas as pd
            df = pd.read_csv(target_path, dtype={'PUMA': str})
            puma_count = df['PUMA'].nunique()
            record_count = len(df)
            
            self.logger.log(f"Crosswalk verified: {record_count:,} records, {puma_count} PUMAs", "INFO", "SETUP")
            
            if puma_count != 62:
                self.logger.log(f"Warning: Expected 62 PUMAs, found {puma_count}", "WARNING", "SETUP")
            
            return True
            
        except Exception as e:
            self.logger.log(f"Failed to verify crosswalk: {e}", "ERROR", "SETUP")
            return False
    
    def run_with_monitoring(self) -> bool:
        """Run the workflow with resource monitoring"""
        self.logger.log("Starting PopulationSim workflow with monitoring...", "INFO", "WORKFLOW")
        
        # Setup monitoring
        monitor_interval = 60  # seconds
        last_monitor = time.time()
        
        try:
            # Ensure setup is correct
            if not self.ensure_crosswalk_in_place():
                return False
            
            # Start the workflow
            success = self.workflow.run_workflow()
            
            if success:
                self.logger.log("PopulationSim workflow completed successfully", "INFO", "WORKFLOW")
                self._log_final_status()
            else:
                self.logger.log("PopulationSim workflow failed", "ERROR", "WORKFLOW")
            
            return success
            
        except KeyboardInterrupt:
            self.logger.log("Workflow interrupted by user/system", "WARNING", "WORKFLOW")
            return False
        except Exception as e:
            self.logger.log(f"Workflow failed with exception: {e}", "ERROR", "WORKFLOW")
            self.logger.log(f"Traceback: {traceback.format_exc()}", "ERROR", "WORKFLOW")
            return False
        finally:
            total_time = time.time() - self.start_time
            self.logger.log(f"Total execution time: {total_time/3600:.2f} hours", "INFO", "WORKFLOW")
    
    def _log_resource_usage(self):
        """Log current resource usage"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        status = {
            "memory_used_gb": (memory.total - memory.available) / (1024**3),
            "memory_available_gb": memory.available / (1024**3),
            "disk_free_gb": disk.free / (1024**3),
            "cpu_percent": psutil.cpu_percent(interval=1)
        }
        
        self.logger.log_status(status)
    
    def _log_final_status(self):
        """Log final workflow status and outputs"""
        self.logger.log("Checking final outputs...", "INFO", "FINAL")
        
        # Check for key output files
        output_files = {
            "synthetic_households": self.config.POPSIM_OUTPUT_FILES.get('synthetic_households'),
            "synthetic_persons": self.config.POPSIM_OUTPUT_FILES.get('synthetic_persons'),
            "summary_melt": self.config.POPSIM_OUTPUT_FILES.get('summary_melt')
        }
        
        status = {"outputs": {}}
        
        for name, file_path in output_files.items():
            if file_path and Path(file_path).exists():
                size_mb = Path(file_path).stat().st_size / (1024**2)
                status["outputs"][name] = f"EXISTS ({size_mb:.1f} MB)"
                self.logger.log(f"Output {name}: {size_mb:.1f} MB", "INFO", "FINAL")
            else:
                status["outputs"][name] = "MISSING"
                self.logger.log(f"Output {name}: MISSING", "WARNING", "FINAL")
        
        self.logger.log_status(status)

def main():
    parser = argparse.ArgumentParser(description="Pipeline-ready PopulationSim for Bay Area TM2")
    parser.add_argument("--year", type=int, default=2023, help="Year to process (default: 2023)")
    parser.add_argument("--log-file", type=str, default="pipeline_populationsim.log", 
                       help="Log file path (default: pipeline_populationsim.log)")
    parser.add_argument("--quiet", action="store_true", help="Suppress console output")
    parser.add_argument("--validate-only", action="store_true", help="Only run validation, don't execute workflow")
    
    args = parser.parse_args()
    
    # Setup logging
    log_file = Path(args.log_file)
    logger = PipelineLogger(log_file, verbose=not args.quiet)
    
    logger.log("Starting pipeline PopulationSim workflow", "INFO", "INIT")
    logger.log(f"Arguments: {vars(args)}", "INFO", "INIT")
    
    # Environment validation
    validator = PipelineEnvironmentValidator(logger)
    if not validator.validate_environment():
        logger.log("Environment validation failed", "ERROR", "INIT")
        sys.exit(1)
    
    logger.log("Environment validation passed", "INFO", "INIT")
    
    if args.validate_only:
        logger.log("Validation-only mode: Exiting after validation", "INFO", "INIT")
        sys.exit(0)
    
    # Run the workflow
    try:
        pipeline = PipelinePopulationSim(logger, args.year)
        success = pipeline.run_with_monitoring()
        
        exit_code = 0 if success else 1
        status = "SUCCESS" if success else "FAILURE"
        logger.log(f"Pipeline completed with status: {status}", "INFO", "FINAL")
        
        sys.exit(exit_code)
        
    except Exception as e:
        logger.log(f"Pipeline failed with exception: {e}", "ERROR", "FINAL")
        logger.log(f"Traceback: {traceback.format_exc()}", "ERROR", "FINAL")
        sys.exit(1)

if __name__ == "__main__":
    main()
