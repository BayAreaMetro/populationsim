#!/usr/bin/env python3
"""
Run All PopulationSim Analysis Summaries
========================================

This script runs all analysis and summary scripts independently, ensuring they use
the latest synthesis results. Each script is run with --force to regenerate outputs.

Usage:
    python run_all_summaries.py [--year YEAR] [--model_type MODEL_TYPE]

Features:
- Forces regeneration of all analysis outputs  
- Uses latest synthesis data
- Handles script failures gracefully
- Provides comprehensive logging
- Can run individual script categories

Categories:
- Core Analysis: Performance, dataset analysis, comparisons
- Visualization: Charts, plots, interactive dashboards  
- Validation: Data quality checks, marginal comparisons
- Tableau: Data preparation for external visualization

"""

import sys
import os
import argparse
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path for config imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def log(message, level="INFO"):
    """Simple logging function"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def run_script(script_path, script_name, args=None):
    """Run a single analysis script with error handling"""
    if not script_path.exists():
        log(f"Script not found: {script_name} ({script_path})", "WARN")
        return False
    
    if script_path.stat().st_size == 0:
        log(f"Script is empty: {script_name} ({script_path})", "WARN") 
        return False
    
    log(f"Running: {script_name}")
    start_time = time.time()
    
    # Build command
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=script_path.parent.parent  # Run from bay_area directory
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            log(f"✅ {script_name} completed successfully in {elapsed:.1f}s")
            return True
        else:
            log(f"❌ {script_name} failed with code {result.returncode}", "ERROR")
            if result.stderr:
                log(f"Error output: {result.stderr[:500]}", "ERROR")
            return False
            
    except Exception as e:
        elapsed = time.time() - start_time
        log(f"❌ {script_name} crashed: {e}", "ERROR")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Run all PopulationSim analysis summaries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--year", type=int, default=2023, help="Model year")
    parser.add_argument("--model_type", default="TM2", help="Model type (TM1/TM2)")
    parser.add_argument("--category", choices=['core', 'visualization', 'validation', 'all'], 
                       default='all', help="Script category to run")
    parser.add_argument("--skip-errors", action="store_true", help="Continue even if scripts fail")
    
    args = parser.parse_args()
    
    # Base directory setup
    base_dir = Path(__file__).parent
    analysis_dir = base_dir / "analysis"
    output_dir = base_dir / f"output_{args.year}"
    
    log("="*80)
    log("POPULATIONSIM ANALYSIS SUMMARIES")
    log("="*80)
    log(f"Year: {args.year}")
    log(f"Model Type: {args.model_type}")
    log(f"Output Directory: {output_dir}")
    log(f"Category: {args.category}")
    log("")
    
    # Check that synthesis outputs exist
    required_files = [
        output_dir / "populationsim_working_dir" / "output" / "synthetic_households.csv",
        output_dir / "populationsim_working_dir" / "output" / "synthetic_persons.csv",
        output_dir / "populationsim_working_dir" / "output" / f"households_{args.year}_tm2.csv",
        output_dir / "populationsim_working_dir" / "output" / f"persons_{args.year}_tm2.csv"
    ]
    
    missing_files = [f for f in required_files if not f.exists()]
    if missing_files:
        log("❌ Required synthesis output files missing:", "ERROR")
        for f in missing_files:
            log(f"   - {f}", "ERROR")
        log("Run population synthesis first!")
        return False
    
    # Define script categories
    scripts = {
        'core': [
            ('maz_household_comparison', analysis_dir / "MAZ_hh_comparison.py", []),
            ('full_dataset', analysis_dir / "analyze_full_dataset.py", []),
            ('compare_controls_vs_results_by_taz', analysis_dir / "compare_controls_vs_results_by_taz.py", []),
            ('synthetic_population_analysis', analysis_dir / "analyze_syn_pop_model.py", ["--year", str(args.year), "--model_type", args.model_type])
        ],
        'visualization': [
            ('taz_controls_analysis', analysis_dir / "analyze_taz_controls_vs_results.py", []),
            ('county_analysis', analysis_dir / "analyze_county_results.py", []),
            ('interactive_taz_analysis', analysis_dir / "create_interactive_taz_analysis.py", [])
        ],
        'validation': [
            ('maz_household_summary', analysis_dir / "maz_household_summary.py", []),
            ('compare_synthetic_populations', analysis_dir / "compare_synthetic_populations.py", []),
            ('data_validation', analysis_dir / "data_validation.py", [])
        ],
        # 'tableau' category intentionally removed per user request
    }
    
    # Determine which categories to run
    if args.category == 'all':
        categories_to_run = scripts.keys()
    else:
        categories_to_run = [args.category]
    
    # Track results
    total_scripts = 0
    successful_scripts = 0
    failed_scripts = []
    
    # Run scripts by category
    for category in categories_to_run:
        if category not in scripts:
            log(f"Unknown category: {category}", "WARN")
            continue
            
        log(f"\n{'='*60}")
        log(f"CATEGORY: {category.upper()}")
        log(f"{'='*60}")
        
        category_scripts = scripts[category]
        for script_name, script_path, script_args in category_scripts:
            total_scripts += 1
            success = run_script(script_path, script_name, script_args)
            
            if success:
                successful_scripts += 1
            else:
                failed_scripts.append(script_name)
                if not args.skip_errors:
                    log(f"❌ Stopping due to failure in {script_name}", "ERROR")
                    break
    
    # Final summary
    log(f"\n{'='*80}")
    log("SUMMARY")
    log(f"{'='*80}")
    log(f"Total scripts run: {total_scripts}")
    log(f"Successful: {successful_scripts}")
    log(f"Failed: {len(failed_scripts)}")
    
    if failed_scripts:
        log("Failed scripts:")
        for script in failed_scripts:
            log(f"  - {script}")
    
    if successful_scripts == total_scripts:
        log("🎉 All analysis summaries completed successfully!")
        return True
    else:
        log(f"⚠️  {len(failed_scripts)} scripts failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


