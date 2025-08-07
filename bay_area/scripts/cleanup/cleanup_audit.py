#!/usr/bin/env python3
"""
CLEANUP AUDIT: Identify core pipeline scripts vs. unused/obsolete files
"""

import os
from pathlib import Path
import re

def analyze_bay_area_scripts():
    """Analyze all Python scripts in bay_area directory and categorize them."""
    
    bay_area_dir = Path(".")
    
    # Define core pipeline components
    core_pipeline = {
        "ESSENTIAL": {
            "build_crosswalk_focused.py": "Creates 62-PUMA geospatial crosswalk (CURRENT)",
            "add_hhgq_combined_controls.py": "Processes control files for group quarters",
            "run_populationsim_tm2.py": "Main PopulationSim execution script",
        },
        
        "SUPPORTING": {
            "config_tm2.py": "Configuration for TM2 model",
            "create_seed_population_tm2.py": "Creates seed population",
            "create_baseyear_controls_23_tm2.py": "Creates control files",
        },
        
        "OBSOLETE_CROSSWALK": {
            "build_crosswalk_from_shapefiles.py": "OLD: Superseded by focused version",
            "build_maz_taz_puma_crosswalk.py": "OLD: Superseded by focused version", 
            "build_crosswalk_shapely.py": "OLD: Superseded by focused version",
            "build_crosswalk_robust.py": "OLD: Superseded by focused version",
            "recreate_puma_crosswalk.py": "OLD: Superseded by focused version",
        },
        
        "OBSOLETE_DEBUG": {
            "analyze_geo_crosswalk.py": "OLD: Debug script no longer needed",
            "simple_debug.py": "OLD: Debug script no longer needed",
            "patch_and_debug_merge.py": "OLD: Debug script no longer needed",
            "show_pumas.py": "OLD: Debug script no longer needed",
        },
        
        "OBSOLETE_RUNNERS": {
            "run_populationsim.py": "OLD: TM1 version",
            "run_populationsim_tm2_backup.py": "OLD: Backup version",
        },
        
        "DATA_PROCESSING": {
            "process_pums_efficient.py": "PUMS data processing",
            "process_ca_pums.py": "California PUMS processing",
            "prepare_tableau_data.py": "Tableau visualization prep",
            "prepare_tableau_csv.py": "Tableau CSV prep", 
            "postprocess_recode.py": "Post-processing recoding",
        },
        
        "UTILITIES": {
            "download_puma_shapefiles.py": "Downloads PUMA shapefiles",
            "check_files.py": "File validation",
            "check_packages.py": "Package validation",
            "check_seed_data.py": "Seed data validation",
        },
        
        "BATCH_FILES": {
            "*.bat": "Windows batch files for automation",
        }
    }
    
    print("=" * 80)
    print("BAY AREA SCRIPT ANALYSIS")
    print("=" * 80)
    
    # Scan actual files
    python_files = list(bay_area_dir.glob("*.py"))
    all_files = list(bay_area_dir.glob("*"))
    
    print(f"📁 Found {len(python_files)} Python files")
    print(f"📁 Found {len(all_files)} total files")
    
    # Track which files we've categorized
    categorized_files = set()
    
    for category, files in core_pipeline.items():
        print(f"\n📂 {category}:")
        for filename, description in files.items():
            file_path = bay_area_dir / filename
            if file_path.exists():
                print(f"   ✅ {filename} - {description}")
                categorized_files.add(filename)
            else:
                print(f"   ❌ {filename} - {description} (NOT FOUND)")
    
    # Find uncategorized files
    uncategorized = []
    for py_file in python_files:
        if py_file.name not in categorized_files:
            uncategorized.append(py_file.name)
    
    if uncategorized:
        print(f"\n❓ UNCATEGORIZED FILES ({len(uncategorized)}):")
        for filename in sorted(uncategorized):
            print(f"   ❓ {filename}")
    
    return core_pipeline, categorized_files, uncategorized

def create_cleanup_plan(core_pipeline, categorized_files, uncategorized):
    """Create a specific cleanup plan."""
    
    print(f"\n" + "=" * 80)
    print("CLEANUP RECOMMENDATIONS")
    print("=" * 80)
    
    # Files to keep
    keep_files = []
    keep_files.extend(core_pipeline["ESSENTIAL"].keys())
    keep_files.extend(core_pipeline["SUPPORTING"].keys())
    keep_files.extend(core_pipeline["DATA_PROCESSING"].keys())
    keep_files.extend(core_pipeline["UTILITIES"].keys())
    
    print("✅ KEEP (Core Pipeline):")
    for filename in sorted(keep_files):
        if Path(filename).exists():
            print(f"   📌 {filename}")
    
    # Files to remove
    remove_files = []
    remove_files.extend(core_pipeline["OBSOLETE_CROSSWALK"].keys())
    remove_files.extend(core_pipeline["OBSOLETE_DEBUG"].keys()) 
    remove_files.extend(core_pipeline["OBSOLETE_RUNNERS"].keys())
    
    print(f"\n🗑️  REMOVE (Obsolete):")
    for filename in sorted(remove_files):
        if Path(filename).exists():
            print(f"   🗑️  {filename}")
    
    print(f"\n❓ REVIEW (Uncategorized):")
    for filename in sorted(uncategorized):
        print(f"   ❓ {filename}")
    
    return keep_files, remove_files

def main():
    print("🧹 STARTING COMPREHENSIVE CODE CLEANUP AUDIT")
    
    # Change to bay_area directory
    os.chdir(".")
    
    # Analyze scripts
    core_pipeline, categorized_files, uncategorized = analyze_bay_area_scripts()
    
    # Create cleanup plan
    keep_files, remove_files = create_cleanup_plan(core_pipeline, categorized_files, uncategorized)
    
    print(f"\n" + "=" * 80)
    print("CLEANUP SUMMARY")
    print("=" * 80)
    print(f"📌 Keep: {len([f for f in keep_files if Path(f).exists()])} files")
    print(f"🗑️  Remove: {len([f for f in remove_files if Path(f).exists()])} files") 
    print(f"❓ Review: {len(uncategorized)} files")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"1. Review uncategorized files")
    print(f"2. Remove obsolete files") 
    print(f"3. Organize remaining files")
    print(f"4. Test core pipeline")

if __name__ == "__main__":
    main()
