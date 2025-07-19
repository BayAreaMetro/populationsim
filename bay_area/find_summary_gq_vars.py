"""
Find summary/total variables for military and university group quarters
"""
import requests
import json

# Get all DHC variables
url = "https://api.census.gov/data/2020/dec/dhc/variables.json"
response = requests.get(url)
variables = response.json()['variables']

print("Looking for total military quarters variables:")
military_totals = {}
for var, info in variables.items():
    label = info['label'].lower()
    if ('military' in label and 
        ('total' in label or var.endswith('_001N')) and
        not any(letter in var[-3:] for letter in 'ABCDEFGHI')):
        military_totals[var] = info['label']

for var in sorted(military_totals.keys()):
    print(f"  {var}: {military_totals[var]}")

print("\nLooking for total college/university quarters variables:")
univ_totals = {}
for var, info in variables.items():
    label = info['label'].lower()
    if (any(word in label for word in ['college', 'university', 'student']) and 
        ('total' in label or var.endswith('_001N')) and
        not any(letter in var[-3:] for letter in 'ABCDEFGHI')):
        univ_totals[var] = info['label']

for var in sorted(univ_totals.keys()):
    print(f"  {var}: {univ_totals[var]}")

print("\nLooking for PCT43 (Group Quarters Population by Major Type):")
pct43_vars = {var: info for var, info in variables.items() 
              if var.startswith('PCT43_') and not any(letter in var[-3:] for letter in 'ABCDEFGHI')}

for var in sorted(pct43_vars.keys()):
    print(f"  {var}: {pct43_vars[var]['label']}")

print("\nLooking for any 'Total' group quarters by type:")
gq_totals = {}
for var, info in variables.items():
    label = info['label']
    if ('group quarters' in label.lower() and 
        'total' in label.lower() and
        not any(letter in var[-3:] for letter in 'ABCDEFGHI')):
        gq_totals[var] = label

for var in sorted(gq_totals.keys())[:20]:  # Show first 20
    print(f"  {var}: {gq_totals[var]}")
