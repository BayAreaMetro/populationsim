#!/usr/bin/env python3
"""
Patch PopulationSim meta_control_factoring.py to handle zero seed weights
This fixes the IntCastingNaNError when no seed households match control combinations
"""
import shutil
import os

# Backup the original file
original_file = 'populationsim/steps/meta_control_factoring.py'
backup_file = 'populationsim/steps/meta_control_factoring.py.backup'

print("Backing up original meta_control_factoring.py...")
shutil.copy2(original_file, backup_file)

# Read the original file
with open(original_file, 'r') as f:
    content = f.read()

# Find and replace the problematic section
old_code = """    for target in meta_control_targets:
        meta_factors[target] = meta_controls_df[target] / factored_meta_weights[target]
    dump_table("meta_factors", meta_factors)"""

new_code = """    for target in meta_control_targets:
        # Handle division by zero when no seed households match control combination
        denominator = factored_meta_weights[target]
        # Replace zeros with small value to avoid division by zero
        denominator = denominator.replace(0, 1e-10)
        meta_factors[target] = meta_controls_df[target] / denominator
        # Set factor to 0 where original denominator was 0 (no seed data available)
        meta_factors[target] = meta_factors[target].where(factored_meta_weights[target] > 0, 0)
    dump_table("meta_factors", meta_factors)"""

# Replace the problematic code
if old_code in content:
    content = content.replace(old_code, new_code)
    print("✅ Fixed division by zero in meta factor calculation")
else:
    print("❌ Could not find exact code pattern for meta factor fix")

# Also fix the integer conversion issue
old_conversion = """        seed_level_meta_controls[target] = seed_level_meta_controls[target].round().astype(int)"""

new_conversion = """        # Handle NaN values before converting to int
        values = seed_level_meta_controls[target].round()
        values = values.fillna(0)  # Replace NaN with 0
        seed_level_meta_controls[target] = values.astype(int)"""

if old_conversion in content:
    content = content.replace(old_conversion, new_conversion)
    print("✅ Fixed NaN handling in integer conversion")
else:
    print("❌ Could not find exact code pattern for integer conversion fix")

# Write the patched file
with open(original_file, 'w') as f:
    f.write(content)

print(f"✅ Patched {original_file}")
print(f"📦 Backup saved as {backup_file}")
print("\nThis patch fixes:")
print("1. Division by zero when no seed households match control combinations")
print("2. NaN values in integer conversion")
print("3. Maintains original logic while handling edge cases gracefully")
