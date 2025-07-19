"""
Analyze PCT9 table structure to find aggregated military and university variables
"""
import requests
import json

# Get PCT9 table details
url = "https://api.census.gov/data/2020/dec/dhc/variables.json"
response = requests.get(url)
variables = response.json()['variables']

# Find all PCT9 variables (without race suffixes)
pct9_vars = {var: info for var, info in variables.items() 
             if var.startswith('PCT9_') and not any(letter in var for letter in 'ABCDEFGHI')}

print("PCT9 base table variables:")
for var in sorted(pct9_vars.keys()):
    print(f"  {var}: {pct9_vars[var]['label']}")

# Look for military aggregates
print("\nLooking for military aggregates in PCT tables:")
military_agg = {var: info for var, info in variables.items() 
                if 'military' in info['label'].lower() and not any(letter in var[-3:] for letter in 'ABCDEFGHI')}

for var in sorted(military_agg.keys())[:10]:  # Show first 10
    print(f"  {var}: {military_agg[var]['label']}")

# Look for university aggregates  
print("\nLooking for university aggregates in PCT tables:")
univ_agg = {var: info for var, info in variables.items() 
            if any(word in info['label'].lower() for word in ['college', 'university', 'student']) 
            and not any(letter in var[-3:] for letter in 'ABCDEFGHI')}

for var in sorted(univ_agg.keys())[:10]:  # Show first 10
    print(f"  {var}: {univ_agg[var]['label']}")
