#!/usr/bin/env python3
import os

# Files we expect to have from our cleanup work
essential_files = [
    "build_crosswalk_focused.py",
    "add_hhgq_combined_controls.py", 
    "run_populationsim_tm2.py",
    "config_tm2.py",
    "create_seed_population_tm2.py",
    "create_baseyear_controls_23_tm2.py"
]

# Files we created during our session
session_files = [
    "cleanup_audit.py",
    "add_county_to_crosswalk.py",
    "fix_county_mapping.py", 
    "fix_puma_format.py",
    "validate_counties.py",
    "validate_crosswalk.py"
]

# Old files we should have removed
obsolete_files = [
    "build_crosswalk_from_shapefiles.py",
    "build_maz_taz_puma_crosswalk.py", 
    "build_crosswalk_shapely.py",
    "build_crosswalk_robust.py",
    "recreate_puma_crosswalk.py",
    "analyze_geo_crosswalk.py",
    "simple_debug.py",
    "patch_and_debug_merge.py",
    "show_pumas.py"
]

print("=== CURRENT STATE ASSESSMENT ===")
print(f"Current directory: {os.getcwd()}")

print("\n✅ ESSENTIAL FILES:")
for f in essential_files:
    status = "✅" if os.path.exists(f) else "❌"
    print(f"  {status} {f}")

print("\n🔧 SESSION FILES (created today):")
for f in session_files:
    status = "✅" if os.path.exists(f) else "❌" 
    print(f"  {status} {f}")

print("\n🗑️ OBSOLETE FILES (should be gone):")
for f in obsolete_files:
    status = "❌ STILL HERE" if os.path.exists(f) else "✅ REMOVED"
    print(f"  {status} {f}")

# Count all Python files
py_files = [f for f in os.listdir('.') if f.endswith('.py')]
print(f"\nTotal Python files: {len(py_files)}")
