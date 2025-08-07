#!/usr/bin/env python3
"""
COMPREHENSIVE WORKSPACE CLEANUP

This script:
1. Organizes all diagnostic and cleanup scripts into folders
2. Removes temporary/obsolete files
3. Creates a clean, standardized structure
4. Consolidates redundant scripts
"""

import shutil
from pathlib import Path
from datetime import datetime

def main():
    print("=" * 70)
    print("COMPREHENSIVE WORKSPACE CLEANUP")
    print("=" * 70)
    
    base_dir = Path(".")
    
    # Create organized folder structure
    folders = {
        "scripts": "Main production scripts",
        "scripts/diagnostic": "Diagnostic and analysis scripts", 
        "scripts/cleanup": "One-time cleanup scripts",
        "scripts/archive": "Archived/obsolete scripts",
        "hh_gq/data/backup": "Data backups"
    }
    
    print("📁 CREATING ORGANIZED FOLDER STRUCTURE...")
    for folder, description in folders.items():
        folder_path = base_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {folder}/ - {description}")
    
    # Define file categories for organization
    files_to_organize = {
        # Production scripts (keep in main directory)
        "KEEP_MAIN": [
            "build_crosswalk_focused.py",          # Main crosswalk creation
            "run_populationsim_tm2.py",            # Main PopSim runner
            "add_hhgq_combined_controls.py",       # Control file processor
        ],
        
        # Move to scripts/diagnostic/
        "DIAGNOSTIC": [
            "find_missing_pumas_final.py",
            "find_missing_pumas_simple.py", 
            "find_missing_pumas.py",
            "diagnose_puma_mismatch.py",
            "investigate_edge_cases.py",
            "compare_pumas.py",
            "hh_gq/data/compare_pumas.py",
        ],
        
        # Move to scripts/cleanup/
        "CLEANUP": [
            "cleanup_step1_crosswalk.py",
            "cleanup_step2_seed.py",
            "CLEANUP_PLAN.py",
        ],
        
        # Archive (old/obsolete scripts)
        "ARCHIVE": [
            "build_maz_to_puma_crosswalk.py",     # Superseded by focused version
            "enhanced_debug_populationsim.py",    # Old debug script
            "debug_populationsim.py",             # Old debug script
            "debug_populationsim_data.py",        # Old debug script
        ]
    }
    
    print(f"\n🗂️  ORGANIZING FILES...")
    
    # Keep main production scripts
    print(f"   📌 KEEPING IN MAIN DIRECTORY:")
    for script in files_to_organize["KEEP_MAIN"]:
        if (base_dir / script).exists():
            print(f"      ✅ {script}")
        else:
            print(f"      ⚠️  {script} (not found)")
    
    # Move diagnostic scripts
    print(f"   🔍 MOVING TO scripts/diagnostic/:")
    for script in files_to_organize["DIAGNOSTIC"]:
        src = base_dir / script
        if src.exists():
            dst = base_dir / "scripts" / "diagnostic" / src.name
            shutil.move(str(src), str(dst))
            print(f"      ✅ {script} → {dst.relative_to(base_dir)}")
        else:
            print(f"      ⚠️  {script} (not found)")
    
    # Move cleanup scripts  
    print(f"   🧹 MOVING TO scripts/cleanup/:")
    for script in files_to_organize["CLEANUP"]:
        src = base_dir / script
        if src.exists():
            dst = base_dir / "scripts" / "cleanup" / src.name
            shutil.move(str(src), str(dst))
            print(f"      ✅ {script} → {dst.relative_to(base_dir)}")
        else:
            print(f"      ⚠️  {script} (not found)")
    
    # Archive old scripts
    print(f"   📦 MOVING TO scripts/archive/:")
    for script in files_to_organize["ARCHIVE"]:
        src = base_dir / script
        if src.exists():
            dst = base_dir / "scripts" / "archive" / src.name
            shutil.move(str(src), str(dst))
            print(f"      ✅ {script} → {dst.relative_to(base_dir)}")
        else:
            print(f"      ⚠️  {script} (not found)")
    
    # Create README files for organization
    print(f"\n📝 CREATING DOCUMENTATION...")
    
    # Main README
    main_readme = base_dir / "README_SCRIPTS.md"
    main_readme.write_text("""# PopulationSim TM2 Scripts

## Main Production Scripts
- `build_crosswalk_focused.py` - Creates geospatial MAZ→TAZ→PUMA crosswalk (62 PUMAs)
- `run_populationsim_tm2.py` - Main PopulationSim execution script  
- `add_hhgq_combined_controls.py` - Processes control files for group quarters

## Script Organization
- `scripts/diagnostic/` - Analysis and diagnostic scripts
- `scripts/cleanup/` - One-time cleanup and migration scripts
- `scripts/archive/` - Obsolete scripts (kept for reference)

## Data Files
- `hh_gq/data/geo_cross_walk_tm2.csv` - Primary crosswalk (62 PUMAs)
- `hh_gq/data/seed_households.csv` - Filtered seed households (62 PUMAs)
- `hh_gq/data/seed_persons.csv` - Filtered seed persons (62 PUMAs)
""")
    print(f"   ✅ Created: {main_readme}")
    
    # Diagnostic README
    diag_readme = base_dir / "scripts" / "diagnostic" / "README.md"
    diag_readme.write_text("""# Diagnostic Scripts

These scripts were used to analyze and resolve the PUMA geography mismatch issue.

## Key Findings
- Original seed population had 66 PUMAs
- 4 PUMAs (5303, 7707, 8701, 11301) are outside Bay Area modeling region
- Final crosswalk correctly includes 62 PUMAs within the region

## Scripts
- `find_missing_pumas_final.py` - Identifies missing PUMAs between seed and crosswalk
- `compare_pumas.py` - Simple comparison of PUMA lists
- `investigate_edge_cases.py` - Spatial analysis of missing PUMAs
""")
    print(f"   ✅ Created: {diag_readme}")
    
    # Remove any temporary files
    print(f"\n🗑️  REMOVING TEMPORARY FILES...")
    temp_patterns = [
        "*.pyc",
        "__pycache__",
        "*.tmp",
        "debug_*.txt",
    ]
    
    for pattern in temp_patterns:
        for temp_file in base_dir.rglob(pattern):
            if temp_file.is_file():
                temp_file.unlink()
                print(f"   🗑️  {temp_file.relative_to(base_dir)}")
            elif temp_file.is_dir():
                shutil.rmtree(temp_file)
                print(f"   🗑️  {temp_file.relative_to(base_dir)}/")
    
    print(f"\n📊 FINAL DIRECTORY STRUCTURE:")
    print(f"   📁 bay_area/")
    print(f"   ├── 🔧 build_crosswalk_focused.py")
    print(f"   ├── 🚀 run_populationsim_tm2.py") 
    print(f"   ├── ⚙️  add_hhgq_combined_controls.py")
    print(f"   ├── 📁 scripts/")
    print(f"   │   ├── 📁 diagnostic/")
    print(f"   │   ├── 📁 cleanup/")
    print(f"   │   └── 📁 archive/")
    print(f"   └── 📁 hh_gq/data/")
    print(f"       ├── 🗺️  geo_cross_walk_tm2.csv (62 PUMAs)")
    print(f"       ├── 🏠 seed_households.csv")
    print(f"       ├── 👥 seed_persons.csv")
    print(f"       └── 📁 backup/")
    
    print(f"\n" + "=" * 70)
    print("✅ COMPREHENSIVE CLEANUP COMPLETE")
    print("=" * 70)
    print("✨ Workspace is now clean and organized!")
    print("🚀 Ready for PopulationSim pipeline testing!")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("❌ CLEANUP FAILED")
        exit(1)
