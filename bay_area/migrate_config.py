#!/usr/bin/env python3
"""
Configuration Migration Script
Transitions from old config_tm2.py and tm2_control_utils/config.py to unified_tm2_config.py
"""

from pathlib import Path
import shutil
import sys

def backup_old_configs():
    """Backup old configuration files before deletion"""
    base_dir = Path(__file__).parent
    backup_dir = base_dir / "config_backup"
    backup_dir.mkdir(exist_ok=True)
    
    old_configs = [
        base_dir / "config_tm2.py",
        base_dir / "tm2_control_utils" / "config.py"
    ]
    
    backed_up = []
    for config_file in old_configs:
        if config_file.exists():
            backup_path = backup_dir / config_file.name
            shutil.copy2(config_file, backup_path)
            backed_up.append(config_file.name)
            print(f"✅ Backed up {config_file.name} to {backup_path}")
    
    return backed_up

def check_old_config_usage():
    """Check which files still import old configs"""
    base_dir = Path(__file__).parent
    
    files_to_check = list(base_dir.glob("*.py"))
    old_imports = []
    
    for py_file in files_to_check:
        if py_file.name.startswith("unified_") or py_file.name.startswith("config"):
            continue
            
        try:
            content = py_file.read_text(encoding='utf-8')
            if "from config_tm2 import" in content or "from tm2_control_utils import config" in content:
                old_imports.append(py_file.name)
        except Exception as e:
            print(f"⚠️  Could not read {py_file.name}: {e}")
    
    return old_imports

def show_migration_guide():
    """Show migration guide for updating scripts"""
    guide = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                          CONFIGURATION MIGRATION GUIDE                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

OLD PATTERN (config_tm2.py):
    from config_tm2 import PopulationSimConfig
    config = PopulationSimConfig()
    output_dir = config.OUTPUT_DIR

NEW PATTERN (unified_tm2_config.py):
    from unified_tm2_config import config
    paths = config.get_control_paths()
    output_dir = paths['output_dir']

╔══════════════════════════════════════════════════════════════════════════════╗
║                              HELPER METHODS                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

For different script types, use these methods:

📂 CROSSWALK SCRIPTS:
    paths = config.get_crosswalk_paths()
    # Returns: maz_shapefile, puma_shapefile, output_primary, output_reference

🌱 SEED SCRIPTS:
    paths = config.get_seed_paths()
    # Returns: crosswalk_file, output_dir, households_raw, persons_raw, etc.

📊 CONTROL SCRIPTS:
    paths = config.get_control_paths()
    # Returns: output_dir, maz_marginals, taz_marginals, county_marginals

🏠 GROUP QUARTERS SCRIPTS:
    paths = config.get_hhgq_paths()
    # Returns: input_dir, output_dir, maz_marginals_in/out, etc.

🗺️  GIS FILES (with fallback):
    gis_paths = config.get_gis_files_with_fallback()
    # Returns: maz_taz_def, maz_taz_all_geog (network or local)

💾 CACHE DIRECTORIES:
    cache_dir = config.get_cache_dir_with_fallback()
    # Returns: network cache, input_2023 cache, or local cache

🔑 CENSUS API KEY:
    api_key_path = config.get_census_api_key_path()
    # Returns: network or local API key file

⚙️  PROCESSING PARAMETERS:
    params = config.get_processing_params()
    # Returns: chunk_size, random_seed, census_api_timeout, max_retries

╔══════════════════════════════════════════════════════════════════════════════╗
║                             MIGRATION STEPS                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

1. Update import statement
2. Replace hardcoded paths with config methods
3. Use helper methods for specific script types
4. Test the script
5. Remove old config file (after all scripts updated)
"""
    return guide

def main():
    """Main migration process"""
    print("🔄 Configuration Migration Tool")
    print("=" * 50)
    
    # Check current state
    old_imports = check_old_config_usage()
    
    if not old_imports:
        print("✅ No files found using old configuration imports!")
        print("✅ Migration appears to be complete.")
        
        # Ask about cleaning up old configs
        response = input("\n🗑️  Remove old config files? (y/N): ").lower()
        if response == 'y':
            backed_up = backup_old_configs()
            if backed_up:
                print(f"\n✅ Old configs backed up. Safe to remove:")
                for config_name in backed_up:
                    print(f"   - {config_name}")
            return
    
    print(f"⚠️  Found {len(old_imports)} files still using old configs:")
    for file_name in old_imports:
        print(f"   - {file_name}")
    
    print("\n" + show_migration_guide())
    
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║ NEXT STEPS:                                                                  ║")
    print("║ 1. Update the files listed above to use unified_tm2_config                  ║")
    print("║ 2. Run this script again to verify migration                                ║")
    print("║ 3. Remove old config files once migration is complete                       ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")

if __name__ == "__main__":
    main()
