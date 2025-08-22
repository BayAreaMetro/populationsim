"""
update_controls_with_new_income_bins.py

This script updates controls.csv to use the new ACS-aligned, non-overlapping income bins
defined in INCOME_BIN_MAPPING from tm2_control_utils.config_census.

- It removes old income bin rows (those starting with 'hhinc_')
- It inserts new rows for each bin in INCOME_BIN_MAPPING
- All other controls are preserved

Usage:
    python update_controls_with_new_income_bins.py
"""

import pandas as pd
from pathlib import Path
from tm2_control_utils.config_census import INCOME_BIN_MAPPING

controls_path = Path("output_2023/populationsim_working_dir/configs/controls.csv")
df = pd.read_csv(controls_path)

# Remove old income bin controls (those with control_field starting with 'hhinc_')
mask = ~df['control_field'].str.startswith('hhinc_')
df = df[mask].copy()

# Add new income bin controls from INCOME_BIN_MAPPING
new_rows = []
for bin_def in INCOME_BIN_MAPPING:
    new_rows.append({
        'target': bin_def['control'],
        'geography': 'TAZ',
        'seed_table': 'households',
        'importance': 1000000,
        'control_field': bin_def['control'],
        'expression': bin_def['expression']
    })

# Append new bins and sort for readability
new_df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
new_df.to_csv(controls_path, index=False)

print(f"Updated {controls_path} with new income bins from INCOME_BIN_MAPPING.")
