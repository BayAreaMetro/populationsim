#!/usr/bin/env python3
"""Quick script to check if all required files exist"""

from config_tm2 import PopulationSimConfig
import os

config = PopulationSimConfig()

print("Checking script files:")
print("=" * 50)
for name, path in config.SCRIPTS.items():
    status = "EXISTS" if os.path.exists(path) else "MISSING"
    print(f"{name:20}: {status:7} - {path}")

print("\nChecking validation files:")
print("=" * 50)
for name, path in config.VALIDATION_FILES.items():
    status = "EXISTS" if os.path.exists(path) else "MISSING"
    print(f"{name:20}: {status:7} - {path}")

print("\nChecking tableau script:")
print("=" * 50)
path = config.TABLEAU_FILES['script']
status = "EXISTS" if os.path.exists(path) else "MISSING"
print(f"tableau_script:      {status:7} - {path}")

print("\nChecking Python environment:")
print("=" * 50)
python_path = config.PYTHON_PATH
status = "EXISTS" if os.path.exists(python_path) else "MISSING"
print(f"python_executable:   {status:7} - {python_path}")
