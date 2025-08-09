#!/usr/bin/env python3
"""
Add diagnostic code to the INSTALLED PopulationSim meta_control_factoring.py
"""
import shutil
import os

# Path to the installed PopulationSim package
installed_file = r'C:\Users\MTCPB\AppData\Local\anaconda3\envs\popsim\lib\site-packages\populationsim\steps\meta_control_factoring.py'
backup_file = installed_file + '.original'

print(f"Modifying installed PopulationSim file: {installed_file}")

# Backup the original if not already backed up
if not os.path.exists(backup_file):
    shutil.copy2(installed_file, backup_file)
    print("✅ Created backup of original file")
else:
    print("📦 Backup already exists")

# Read the installed file
with open(installed_file, 'r') as f:
    content = f.read()

# Check if already modified
if 'DIAGNOSTIC:' in content:
    print("⚠️  File already contains diagnostic code")
    exit(0)

# Add numpy import
import_section = """import logging
import os

import pandas as pd"""

new_import_section = """import logging
import os
import numpy as np

import pandas as pd"""

content = content.replace(import_section, new_import_section)

# Add diagnostic code before the problematic division
old_division = """    for target in meta_control_targets:
        meta_factors[target] = meta_controls_df[target] / factored_meta_weights[target]
    dump_table("meta_factors", meta_factors)"""

new_division = """    for target in meta_control_targets:
        logger.info(f"DIAGNOSTIC: Processing meta control target: {target}")
        
        # Diagnostic: Check for zero denominators before division
        denominator = factored_meta_weights[target]
        zero_mask = (denominator == 0) | (denominator.isna())
        zero_count = zero_mask.sum()
        
        if zero_count > 0:
            logger.error(f"DIAGNOSTIC: Target '{target}' has {zero_count} zones with zero/NaN seed weights")
            zero_zones = denominator[zero_mask].index.tolist()
            logger.error(f"DIAGNOSTIC: Zero weight zones for '{target}': {zero_zones[:10]}")  # First 10 only
            
            # Show corresponding control targets for these zones
            for zone in zero_zones[:3]:  # Show first 3 to avoid log spam
                control_value = meta_controls_df.loc[zone, target] if zone in meta_controls_df.index else "NOT_FOUND"
                logger.error(f"DIAGNOSTIC: Zone {zone} - Control target: {control_value}, Seed weight: {denominator.loc[zone] if zone in denominator.index else 'NOT_FOUND'}")
        
        # Perform the division
        try:
            meta_factors[target] = meta_controls_df[target] / factored_meta_weights[target]
        except Exception as e:
            logger.error(f"DIAGNOSTIC: Division failed for '{target}': {e}")
            raise
        
        # Check for NaN/infinite results
        nan_count = meta_factors[target].isna().sum()
        inf_count = np.isinf(meta_factors[target]).sum()
        
        if nan_count > 0 or inf_count > 0:
            logger.error(f"DIAGNOSTIC: Target '{target}' produced {nan_count} NaN and {inf_count} infinite factors")
            
    dump_table("meta_factors", meta_factors)"""

if old_division in content:
    content = content.replace(old_division, new_division)
    print("✅ Added diagnostic code to division section")
else:
    print("❌ Could not find division section to modify")

# Add diagnostic code before the integer conversion
old_conversion = """        seed_level_meta_controls[target] = seed_level_meta_controls[target].round().astype(int)"""

new_conversion = """        # Diagnostic: Check values before integer conversion
        values_to_convert = seed_level_meta_controls[target].round()
        nan_count = values_to_convert.isna().sum()
        inf_count = np.isinf(values_to_convert).sum()
        
        logger.info(f"DIAGNOSTIC: '{target}' conversion - NaN: {nan_count}, Inf: {inf_count}, Range: {values_to_convert.min():.2f} to {values_to_convert.max():.2f}")
        
        if nan_count > 0:
            logger.error(f"DIAGNOSTIC: '{target}' has {nan_count} NaN values before integer conversion")
            nan_indices = values_to_convert[values_to_convert.isna()].index.tolist()[:5]
            logger.error(f"DIAGNOSTIC: First 5 NaN indices for '{target}': {nan_indices}")
            # Show the values that led to NaN
            for idx in nan_indices[:3]:
                orig_factor = meta_factors[target].loc[idx] if idx in meta_factors[target].index else "NOT_FOUND"
                orig_weight = factored_seed_weights.loc[idx, target] if idx in factored_seed_weights.index else "NOT_FOUND"
                logger.error(f"DIAGNOSTIC: Index {idx} - Factor: {orig_factor}, Original weight: {orig_weight}")
            
        try:
            seed_level_meta_controls[target] = values_to_convert.astype(int)
            logger.info(f"DIAGNOSTIC: Successfully converted '{target}' to integer")
        except Exception as e:
            logger.error(f"DIAGNOSTIC: FAILED to convert '{target}' to integer: {e}")
            logger.error(f"DIAGNOSTIC: This is the exact error causing the pipeline failure!")
            raise"""

if old_conversion in content:
    content = content.replace(old_conversion, new_conversion)
    print("✅ Added diagnostic code to conversion section")
else:
    print("❌ Could not find conversion section to modify")

# Write the modified file
with open(installed_file, 'w') as f:
    f.write(content)

print("✅ Modified installed PopulationSim file with diagnostic code")
print("🔍 Diagnostic features added:")
print("  - Logs zero seed weights by zone and target")
print("  - Shows NaN/infinite values before integer conversion")
print("  - Detailed error reporting with actual values")
print("  - Identifies exact zones causing the failure")
