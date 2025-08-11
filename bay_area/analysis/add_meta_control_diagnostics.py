#!/usr/bin/env python3
"""
Add diagnostic code to meta_control_factoring.py to identify failing combinations
"""
import shutil

# Backup the original file first
original_file = 'populationsim/steps/meta_control_factoring.py'
backup_file = 'populationsim/steps/meta_control_factoring.py.original'

print("Creating diagnostic version of meta_control_factoring.py...")
shutil.copy2(original_file, backup_file)

# Read the original file
with open(original_file, 'r') as f:
    content = f.read()

# Add diagnostic imports at the top
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
        logger.info(f"Processing meta control target: {target}")
        
        # Diagnostic: Check for zero denominators before division
        denominator = factored_meta_weights[target]
        zero_mask = (denominator == 0) | (denominator.isna())
        zero_count = zero_mask.sum()
        
        if zero_count > 0:
            logger.warning(f"DIAGNOSTIC: Target '{target}' has {zero_count} zones with zero/NaN seed weights")
            zero_zones = denominator[zero_mask].index.tolist()
            logger.warning(f"DIAGNOSTIC: Zero weight zones for '{target}': {zero_zones}")
            
            # Show corresponding control targets for these zones
            for zone in zero_zones[:5]:  # Show first 5 to avoid log spam
                control_value = meta_controls_df.loc[zone, target] if zone in meta_controls_df.index else "NOT_FOUND"
                logger.warning(f"DIAGNOSTIC: Zone {zone} - Control target: {control_value}, Seed weight: {denominator.loc[zone] if zone in denominator.index else 'NOT_FOUND'}")
        
        # Perform the division
        meta_factors[target] = meta_controls_df[target] / factored_meta_weights[target]
        
        # Check for NaN/infinite results
        nan_count = meta_factors[target].isna().sum()
        inf_count = np.isinf(meta_factors[target]).sum()
        
        if nan_count > 0 or inf_count > 0:
            logger.error(f"DIAGNOSTIC: Target '{target}' produced {nan_count} NaN and {inf_count} infinite factors")
            
    dump_table("meta_factors", meta_factors)"""

content = content.replace(old_division, new_division)

# Add diagnostic code before the integer conversion
old_conversion = """        seed_level_meta_controls[target] = seed_level_meta_controls[target].round().astype(int)"""

new_conversion = """        # Diagnostic: Check values before integer conversion
        values_to_convert = seed_level_meta_controls[target].round()
        nan_count = values_to_convert.isna().sum()
        inf_count = np.isinf(values_to_convert).sum()
        
        if nan_count > 0:
            logger.error(f"DIAGNOSTIC: '{target}' has {nan_count} NaN values before integer conversion")
            nan_indices = values_to_convert[values_to_convert.isna()].index.tolist()[:10]
            logger.error(f"DIAGNOSTIC: First 10 NaN indices for '{target}': {nan_indices}")
            
        if inf_count > 0:
            logger.error(f"DIAGNOSTIC: '{target}' has {inf_count} infinite values before integer conversion")
            
        try:
            seed_level_meta_controls[target] = values_to_convert.astype(int)
            logger.info(f"DIAGNOSTIC: Successfully converted '{target}' to integer")
        except Exception as e:
            logger.error(f"DIAGNOSTIC: Failed to convert '{target}' to integer: {e}")
            logger.error(f"DIAGNOSTIC: Value range for '{target}': min={values_to_convert.min()}, max={values_to_convert.max()}")
            logger.error(f"DIAGNOSTIC: Value types: {values_to_convert.dtype}, unique types: {values_to_convert.apply(type).unique()}")
            raise"""

content = content.replace(old_conversion, new_conversion)

# Write the diagnostic version
with open(original_file, 'w') as f:
    f.write(content)

print("[SUCCESS] Added diagnostic code to meta_control_factoring.py")
print("[PACKAGE] Original backed up as meta_control_factoring.py.original")
print("\nDiagnostic features added:")
print("1. Logs which control targets have zero seed weights")
print("2. Shows specific zones causing division by zero")
print("3. Reports NaN/infinite values after calculations")
print("4. Detailed error reporting during integer conversion")
print("5. Shows value ranges and types when conversion fails")
print("\nThis will help identify exactly which control combinations are impossible!")
