#!/usr/bin/env python3
"""Look for specific group quarters variables."""

import requests
import json

print("Looking for specific group quarters variables...")
dhc_vars_url = "https://api.census.gov/data/2020/dec/dhc/variables.json"

try:
    response = requests.get(dhc_vars_url)
    if response.status_code == 200:
        variables = response.json()
        
        # Look for total group quarters variables
        total_gq_vars = []
        military_vars = []
        university_vars = []
        
        for var_name, var_info in variables['variables'].items():
            label = var_info.get('label', '').lower()
            
            # Total group quarters
            if ('group quarters' in label and 
                ('total' in label or 'all' in label) and 
                'institutionalized' not in label and 
                'noninstitutionalized' not in label):
                total_gq_vars.append((var_name, var_info.get('label', '')))
            
            # Military
            if 'military' in label or 'armed forces' in label:
                military_vars.append((var_name, var_info.get('label', '')))
                
            # University/college
            if ('college' in label or 'university' in label or 
                'student' in label or 'dormitor' in label):
                university_vars.append((var_name, var_info.get('label', '')))
        
        print(f"\nTotal Group Quarters variables ({len(total_gq_vars)}):")
        for var_name, label in total_gq_vars[:5]:
            print(f"  {var_name}: {label}")
            
        print(f"\nMilitary-related variables ({len(military_vars)}):")
        for var_name, label in military_vars[:5]:
            print(f"  {var_name}: {label}")
            
        print(f"\nUniversity-related variables ({len(university_vars)}):")
        for var_name, label in university_vars[:5]:
            print(f"  {var_name}: {label}")
            
        # Also look for the simplest total GQ variable
        print("\nLooking for PCT9 variables (likely group quarters):")
        pct9_vars = []
        for var_name, var_info in variables['variables'].items():
            if var_name.startswith('PCT9') and '_014N' in var_name:  # Based on what we saw above
                pct9_vars.append((var_name, var_info.get('label', '')))
        
        for var_name, label in pct9_vars[:10]:
            print(f"  {var_name}: {label}")
            
    else:
        print(f"Error: {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")
