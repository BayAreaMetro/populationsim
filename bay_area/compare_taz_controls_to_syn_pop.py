"""
compare_taz_controls_to_syn_pop.py
Compare TAZ-level controls to synthetic population outputs using controls.csv mapping.
- Inputs: final_summary_TAZ.csv, households_2023_tm2.csv, configs/controls.csv
- Uses cpi_conversion.py to convert HHINCADJ (2010$) to 2023$ for income controls
- Outputs: One CSV per control, with TAZ, control_total, synthetic_total, difference, notes
"""
import pandas as pd
import numpy as np
import re
import os
from pathlib import Path
import importlib.util

# --- CONFIG ---
OUTPUT_DIR = Path("output_2023")
HOUSEHOLDS_FILE = OUTPUT_DIR / "populationsim_working_dir" / "output" / "households_2023_tm2.csv"
TAZ_CONTROLS_FILE = OUTPUT_DIR / "final_summary_TAZ.csv"
CONTROLS_CSV = OUTPUT_DIR / "populationsim_working_dir" / "configs" / "controls.csv"
CPI_CONVERSION_SCRIPT = Path("cpi_conversion.py")

# --- LOAD CPI CONVERSION FUNCTION ---
def get_cpi_factor():
    # Dynamically import cpi_conversion.py and get the factor for 2010->2023
    spec = importlib.util.spec_from_file_location("cpi_conversion", CPI_CONVERSION_SCRIPT)
    cpi_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cpi_mod)
    # Assume function get_cpi_factor(from_year, to_year)
    return cpi_mod.get_cpi_factor(2010, 2023)

CPI_FACTOR = get_cpi_factor()

# --- LOAD DATA ---
hh = pd.read_csv(HOUSEHOLDS_FILE)
taz_controls = pd.read_csv(TAZ_CONTROLS_FILE)
controls = pd.read_csv(CONTROLS_CSV)

# --- PREPARE ---
# Convert HHINCADJ to 2023$ for income controls
if 'HHINCADJ' in hh.columns:
    hh['HHINCADJ_2023'] = hh['HHINCADJ'] * CPI_FACTOR

# Helper: Evaluate a control expression on the households DataFrame
def eval_expr(expr, df):
    # Replace 'households.' with '' for eval
    expr = expr.replace('households.', '')
    # Replace np.inf with a large number
    expr = expr.replace('np.inf', '1e9')
    # Only allow safe names
    allowed_names = set(df.columns)
    # Replace logical operators for pandas
    expr = expr.replace('&', 'and').replace('|', 'or')
    # Use query for simple expressions
    try:
        mask = df.eval(expr)
    except Exception:
        # fallback: try query
        try:
            mask = df.query(expr).index
            out = pd.Series(False, index=df.index)
            out.loc[mask] = True
            return out
        except Exception as e:
            print(f"Failed to evaluate expression: {expr}\n{e}")
            return pd.Series(False, index=df.index)
    return mask

# --- MAIN COMPARISON LOOP ---
for idx, row in controls.iterrows():
    control = row['target']
    geography = row['geography']
    expr = row['expression']
    notes = []
    # Only TAZ-level controls
    if geography != 'TAZ':
        continue
    # Try to find matching column in taz_controls
    taz_cols = taz_controls.columns
    match_col = None
    if control in taz_cols:
        match_col = control
    else:
        # Try regex/partial match
        for col in taz_cols:
            if re.search(control, col, re.IGNORECASE):
                match_col = col
                notes.append(f"Matched {control} to {col} by regex.")
                break
    if not match_col:
        notes.append(f"No match for {control} in TAZ controls.")
        continue
    # --- Summarize synthetic households ---
    if 'hh_income_2023' in expr:
        # Income controls: use HHINCADJ_2023
        expr = expr.replace('households.hh_income_2023', 'HHINCADJ_2023')
    mask = eval_expr(expr, hh)
    # Group by TAZ and sum
    if 'TAZ' not in hh.columns:
        print("TAZ column not found in households file!")
        continue
    syn_counts = hh[mask].groupby('TAZ').size().rename('synthetic_total')
    # --- Prepare output ---
    out = taz_controls[['TAZ', match_col]].copy()
    out = out.rename(columns={match_col: 'control_total'})
    out = out.merge(syn_counts, left_on='TAZ', right_index=True, how='left')
    out['synthetic_total'] = out['synthetic_total'].fillna(0).astype(int)
    out['difference'] = out['synthetic_total'] - out['control_total']
    out['notes'] = '; '.join(notes)
    # Note for income controls
    if 'income' in control or 'inc_' in control:
        out['notes'] = out['notes'] + '; Income in 2023$ (converted from 2010$)'
    # Write to CSV
    out_file = OUTPUT_DIR / f'compare_{control}.csv'
    out.to_csv(out_file, index=False)
    print(f"Wrote comparison for {control} to {out_file}")
