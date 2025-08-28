#!/usr/bin/env python3
"""
PopulationSim TM2 Environment Setup
Ensures consistent environment across machines
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Ensure Python 3.8+ is being used"""
    if sys.version_info < (3, 8):
        print(f"ERROR: Python 3.8+ required, found {sys.version}")
        return False
    print(f"✓ Python version: {sys.version}")
    return True

def check_conda_environment():
    """Check if we're in the correct conda environment"""
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', 'base')
    print(f"✓ Conda environment: {conda_env}")
    return True

def check_populationsim_installation():
    """Check if PopulationSim is properly installed"""
    try:
        import populationsim
        print(f"✓ PopulationSim installed: {populationsim.__file__}")
        return True
    except ImportError:
        print("ERROR: PopulationSim not installed")
        print("Run: pip install -e . (from populationsim root directory)")
        return False

def check_required_packages():
    """Check for required packages"""
    required = [
        'pandas', 'numpy', 'pyarrow', 'tables', 
        'activitysim', 'openmatrix', 'psutil'
    ]
    
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
            print(f"✓ {pkg}")
        except ImportError:
            missing.append(pkg)
            print(f"✗ {pkg} - MISSING")
    
    if missing:
        print(f"\nInstall missing packages: pip install {' '.join(missing)}")
        return False
    return True

def check_external_paths():
    """Check external data paths and create local fallbacks"""
    from unified_tm2_config import UnifiedTM2Config
    
    config = UnifiedTM2Config()
    
    # Check critical paths (update to match config: network_gis is a shapefile, not a directory)
    critical_paths = [
        ('TM2py shapefiles', config.EXTERNAL_PATHS['tm2py_shapefiles']),
        ('TM2py utils', config.EXTERNAL_PATHS['tm2py_utils']),
        ('M: drive Census', config.EXTERNAL_PATHS['network_census_cache']),
        ('M: drive Census API', config.EXTERNAL_PATHS['network_census_api']),
        ('PUMS current', config.EXTERNAL_PATHS['pums_current']),
        ('PUMS cached', config.EXTERNAL_PATHS['pums_cached'])
    ]

    all_good = True
    for name, path in critical_paths:
        if path.exists():
            print(f"✓ {name}: {path}")
        else:
            print(f"✗ {name}: {path} - NOT FOUND")
            all_good = False
            # Only create local fallback directories if path is under local_data or data_cache
            if any(s in str(path) for s in ['local_data', 'data_cache']):
                path.mkdir(parents=True, exist_ok=True)
                print(f"  → Created local fallback: {path}")
    return all_good

def setup_environment_variables():
    """Set up environment variables for consistent paths"""
    base_dir = Path(__file__).parent
    # Set other environment variables (if needed in future)
    env_vars = {
        'POPULATIONSIM_BASE_DIR': str(base_dir),
        'POPULATIONSIM_YEAR': '2023',
        'FORCE_CROSSWALK': 'True',  # Force steps for consistency
        'FORCE_SEED': 'True',
        'FORCE_CONTROLS': 'True'
    }
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"✓ {key}: {value}")

def main():
    """Run all environment checks"""
    print("PopulationSim TM2 Environment Check")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Conda Environment", check_conda_environment), 
        ("PopulationSim Installation", check_populationsim_installation),
        ("Required Packages", check_required_packages),
        ("External Paths", check_external_paths)
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\n{name}:")
        if not check_func():
            all_passed = False
    
    print(f"\n{'='*50}")
    if all_passed:
        setup_environment_variables()
        print("✓ Environment setup complete!")
        print("\nNext steps:")
        print("1. cd bay_area")
        print("2. python tm2_pipeline.py full --force")
    else:
        print("✗ Environment issues found - fix them before running pipeline")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
