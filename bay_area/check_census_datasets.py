#!/usr/bin/env python3
"""Check available Census API datasets."""

from census import Census
import os

# Read API key
with open('M:/Data/Census/API/new_key/api-key.txt') as f:
    key = f.read().strip()

c = Census(key)

print("Available datasets in Census API library:")
datasets = [attr for attr in dir(c) if not attr.startswith('_') and not callable(getattr(c, attr, None))]
for dataset in datasets:
    print(f"  {dataset}")

print("\nAvailable methods in Census API library:")
methods = [attr for attr in dir(c) if not attr.startswith('_') and callable(getattr(c, attr, None))]
for method in methods:
    print(f"  {method}")
