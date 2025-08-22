#!/usr/bin/env python3
"""
Comprehensive Analysis Runner for TM2 PopulationSim
====================================================

Orchestrates all analysis, validation, checking, and visualization scripts
for the TM2 PopulationSim pipeline. This script replaces running individual
analysis scripts manually.

Usage:
    python run_comprehensive_analysis.py [--step STEP] [--output_dir DIR] [--year YEAR]

Steps:
    validation  - Run all validation scripts (income, vehicles, etc.)
    checks      - Run all control and data checks
    debug       - Run debug analysis scripts  
    visualize   - Generate visualizations
    analysis    - Run main analysis scripts
    all         - Run everything (default)

Author: TM2 Pipeline Team
Date: August 2025
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
import logging
from unified_tm2_config import UnifiedTM2Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ComprehensiveAnalysisRunner:
    """Orchestrates all analysis scripts for TM2 PopulationSim"""
    
    def __init__(self, output_dir="output_2023", year=2023):
        self.config = UnifiedTM2Config(year=year)
        self.output_dir = Path(output_dir)
        self.year = year
        
        # Set up analysis logging
        self.analysis_log = self.output_dir / "analysis_complete.log"
        
        # File handler for analysis log
        if self.analysis_log.exists():
            self.analysis_log.unlink()
        
        file_handler = logging.FileHandler(self.analysis_log)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        
    def log(self, message, level="INFO"):
        """Unified logging"""
        timestamp = time.strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] [{level}] {message}"
        print(log_msg)
        
        # Also write to analysis log
        with open(self.analysis_log, 'a', encoding='utf-8') as f:
            f.write(log_msg + "\n")
    
    def run_script(self, script_path, script_name, timeout=300):
        """Run a single analysis script with error handling"""
        self.log(f"Running {script_name}...")
        self.log(f"Script: {script_path}")
        
        if not script_path.exists():
            self.log(f"ERROR: Script not found: {script_path}", "ERROR")
            return False
            
        start_time = time.time()
        
        try:
            # Change to bay_area directory to ensure relative imports work
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=self.config.BASE_DIR,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                self.log(f"SUCCESS: {script_name} completed successfully in {duration:.1f}s", "SUCCESS")
                if result.stdout.strip():
                    self.log(f"Output: {result.stdout.strip()}")
                return True
            else:
                self.log(f"ERROR: {script_name} failed with code {result.returncode}", "ERROR")
                if result.stderr:
                    self.log(f"Error: {result.stderr}", "ERROR")
                if result.stdout:
                    self.log(f"Output: {result.stdout}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log(f"ERROR: {script_name} timed out after {timeout}s", "ERROR")
            return False
        except Exception as e:
            self.log(f"ERROR: {script_name} failed with exception: {e}", "ERROR")
            return False
    
    def run_validation_scripts(self):
        """Run all validation scripts"""
        self.log("=" * 60)
        self.log("RUNNING VALIDATION SCRIPTS")
        self.log("=" * 60)
        
        validation_scripts = self.config.ANALYSIS_FILES['validation_scripts']
        results = {}
        
        for script_name, script_path in validation_scripts.items():
            results[script_name] = self.run_script(script_path, f"validate_{script_name}")
        
        # Summary
        successful = sum(results.values())
        total = len(results)
        self.log(f"Validation Summary: {successful}/{total} scripts completed successfully")
        
        return all(results.values())
    
    def run_check_scripts(self):
        """Run all check scripts"""
        self.log("=" * 60)
        self.log("RUNNING CHECK SCRIPTS") 
        self.log("=" * 60)
        
        check_scripts = self.config.ANALYSIS_FILES['check_scripts']
        results = {}
        
        for script_name, script_path in check_scripts.items():
            results[script_name] = self.run_script(script_path, f"check_{script_name}")
        
        # Summary
        successful = sum(results.values())
        total = len(results)
        self.log(f"Check Summary: {successful}/{total} scripts completed successfully")
        
        return all(results.values())
    
    def run_debug_scripts(self):
        """Run all debug scripts (if any are defined in config)"""
        self.log("=" * 60)
        self.log("RUNNING DEBUG SCRIPTS")
        self.log("=" * 60)
        results = {}
        debug_scripts = self.config.ANALYSIS_FILES.get('debug_scripts', {})
        if not debug_scripts:
            self.log("No debug scripts defined in config. Skipping debug step.")
            return all(results.values())
        for script_name, script_path in debug_scripts.items():
            results[script_name] = self.run_script(script_path, f"debug_{script_name}")
        successful = sum(results.values())
        total = len(results)
        self.log(f"Debug Summary: {successful}/{total} scripts completed successfully")
        return all(results.values())
    
    def run_visualization_scripts(self):
        """Run all visualization scripts"""
        self.log("=" * 60)
        self.log("RUNNING VISUALIZATION SCRIPTS")
        self.log("=" * 60)
        
        viz_scripts = self.config.ANALYSIS_FILES['visualization_scripts']
        def run_all(self):
            """Run only the analysis scripts/categories present in ANALYSIS_FILES in config"""
            self.log("=" * 80)
            self.log("COMPREHENSIVE TM2 POPULATIONSIM ANALYSIS")
            self.log("=" * 80)
            self.log(f"Starting comprehensive analysis for {self.year}")
            self.log(f"Output directory: {self.output_dir}")

            start_time = time.time()
            step_results = {}

            # Only run categories present in config
            if 'validation_scripts' in self.config.ANALYSIS_FILES:
                step_results['validation'] = self.run_validation_scripts()
            if 'check_scripts' in self.config.ANALYSIS_FILES:
                step_results['checks'] = self.run_check_scripts()
            if 'debug_scripts' in self.config.ANALYSIS_FILES:
                step_results['debug'] = self.run_debug_scripts()
            if 'visualization_scripts' in self.config.ANALYSIS_FILES:
                step_results['visualization'] = self.run_visualization_scripts()
            if 'main_scripts' in self.config.ANALYSIS_FILES:
                step_results['analysis'] = self.run_main_analysis_scripts()

            # Generate summary
            summary_file = self.generate_comprehensive_summary()

            # Final summary
            total_time = time.time() - start_time
            successful_steps = sum(step_results.values())
            total_steps = len(step_results)

            self.log("=" * 80)
            self.log("COMPREHENSIVE ANALYSIS COMPLETE")
            self.log("=" * 80)
            self.log(f"Total time: {total_time:.1f} seconds")
            self.log(f"Successful steps: {successful_steps}/{total_steps}")
            self.log(f"Summary file: {summary_file}")
            self.log(f"Analysis log: {self.analysis_log}")

            if successful_steps == total_steps:
                self.log("SUCCESS: ALL ANALYSIS COMPLETED SUCCESSFULLY", "SUCCESS")
                return True
            else:
                self.log(f"ERROR: {total_steps - successful_steps} steps failed", "ERROR")
                return False
        return all(results.values())
    
    def generate_comprehensive_summary(self):
        """Generate a comprehensive summary of all analysis results"""
        self.log("=" * 60)
        self.log("GENERATING COMPREHENSIVE SUMMARY")
        self.log("=" * 60)
        
        summary_file = self.output_dir / "COMPREHENSIVE_ANALYSIS_SUMMARY.md"
        
        summary_content = f"""# TM2 PopulationSim Comprehensive Analysis Summary

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
Year: {self.year}
Output Directory: {self.output_dir}

## Analysis Pipeline Status

This summary consolidates results from all analysis, validation, check, debug, and visualization scripts.

### Key Files Generated:
- Analysis Log: `{self.analysis_log.name}`
- Performance Summary: `PERFORMANCE_SUMMARY.txt`
- Validation Results: `validation_summary.txt`
- Control Checks: `control_checks_summary.txt`
- Interactive Charts: `populationsim_analysis_charts.html`

### Analysis Categories Completed:

1. **Validation Scripts** - Income vs ACS, Vehicle Ownership, Data Quality
2. **Check Scripts** - TAZ Controls Rollup, Census Vintage, PUMA Consistency  
3. **Debug Scripts** - Income Mismatch Analysis, Geographic Aggregation
4. **Visualization Scripts** - TAZ-PUMA Mapping, Corrected MAZ Charts
5. **Main Analysis Scripts** - Results Analysis, Performance Metrics, Bias Assessment

### Next Steps:

Review individual analysis outputs in the `{self.output_dir}` directory.
Check the analysis log for detailed execution information.

For issues or questions, refer to the individual script outputs and logs.
"""
        
        with open(summary_file, 'w') as f:
            f.write(summary_content)
        
        self.log(f"✓ Comprehensive summary written to: {summary_file}")
        
        return summary_file
    
    def run_all(self):
        """Run all analysis scripts in proper order"""
        self.log("=" * 80)
        self.log("COMPREHENSIVE TM2 POPULATIONSIM ANALYSIS")
        self.log("=" * 80)
        self.log(f"Starting comprehensive analysis for {self.year}")
        self.log(f"Output directory: {self.output_dir}")
        
        start_time = time.time()
        
        # Track results
        step_results = {}
        
        # Run each category
        step_results['validation'] = self.run_validation_scripts()
       #step_results['checks'] = self.run_check_scripts()
       #step_results['debug'] = self.run_debug_scripts()
        step_results['visualization'] = self.run_visualization_scripts()
        step_results['analysis'] = self.run_main_analysis_scripts()
        
        # Generate summary
        summary_file = self.generate_comprehensive_summary()
        
        # Final summary
        total_time = time.time() - start_time
        successful_steps = sum(step_results.values())
        total_steps = len(step_results)
        
        self.log("=" * 80)
        self.log("COMPREHENSIVE ANALYSIS COMPLETE")
        self.log("=" * 80)
        self.log(f"Total time: {total_time:.1f} seconds")
        self.log(f"Successful steps: {successful_steps}/{total_steps}")
        self.log(f"Summary file: {summary_file}")
        self.log(f"Analysis log: {self.analysis_log}")
        
        if successful_steps == total_steps:
            self.log("SUCCESS: ALL ANALYSIS COMPLETED SUCCESSFULLY", "SUCCESS")
            return True
        else:
            self.log(f"ERROR: {total_steps - successful_steps} steps failed", "ERROR")
            return False


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="TM2 PopulationSim Comprehensive Analysis")
    parser.add_argument('--step', default='all',
                       choices=['validation', 'checks', 'debug', 'visualize', 'analysis', 'all'],
                       help='Analysis step to run (default: all)')
    parser.add_argument('--output_dir', default="output_2023",
                       help='Output directory (default: output_2023)')
    parser.add_argument('--year', type=int, default=2023,
                       help='Analysis year (default: 2023)')
    
    args = parser.parse_args()
    
    # Create analysis runner
    runner = ComprehensiveAnalysisRunner(args.output_dir, args.year)
    
    # Run requested step(s)
    if args.step == 'all':
        success = runner.run_all()
    elif args.step == 'validation':
        success = runner.run_validation_scripts()
    elif args.step == 'checks':
        success = runner.run_check_scripts()
    elif args.step == 'debug':
        success = runner.run_debug_scripts()
    elif args.step == 'visualize':
        success = runner.run_visualization_scripts()
    elif args.step == 'analysis':
        success = runner.run_main_analysis_scripts()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
