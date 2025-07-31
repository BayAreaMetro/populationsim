#!/usr/bin/env python3
"""Check if required packages are installed"""

import sys

packages_to_check = [
    'pandas',
    'numpy', 
    'requests',
    'populationsim',
    'activitysim',
    'urllib3',
    'zipfile',
    'pathlib',
    'collections'
]

print("Checking required packages:")
print("=" * 40)

missing_packages = []

for package in packages_to_check:
    try:
        __import__(package)
        print(f"{package:15}: INSTALLED")
    except ImportError as e:
        print(f"{package:15}: MISSING")
        missing_packages.append(package)

if missing_packages:
    print(f"\nMISSING PACKAGES: {missing_packages}")
    print("These packages need to be installed in the popsim environment")
else:
    print("\nAll required packages are installed!")
