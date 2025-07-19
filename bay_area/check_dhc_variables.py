#!/usr/bin/env python3
"""Check DHC variables available."""

import requests
import json

print("Fetching DHC variables...")
dhc_vars_url = "https://api.census.gov/data/2020/dec/dhc/variables.json"

try:
    response = requests.get(dhc_vars_url)
    if response.status_code == 200:
        variables = response.json()
        
        print(f"Found {len(variables['variables'])} variables")
        
        # Look for group quarters related variables
        gq_vars = []
        for var_name, var_info in variables['variables'].items():
            if 'group quarters' in var_info.get('label', '').lower():
                gq_vars.append((var_name, var_info.get('label', 'No label')))
        
        print(f"\nFound {len(gq_vars)} group quarters variables:")
        for var_name, label in gq_vars[:10]:  # Show first 10
            print(f"  {var_name}: {label}")
            
        # Look for variables containing "PCT" and numbers
        pct_vars = []
        for var_name, var_info in variables['variables'].items():
            if var_name.startswith('PCT') and any(char.isdigit() for char in var_name):
                pct_vars.append((var_name, var_info.get('label', 'No label')))
        
        print(f"\nFound {len(pct_vars)} PCT variables (first 10):")
        for var_name, label in pct_vars[:10]:
            print(f"  {var_name}: {label}")
            
    else:
        print(f"Error fetching variables: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Request failed: {e}")
