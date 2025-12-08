#!/usr/bin/env python3
"""
Compare old and new synthetic population outputs (households and persons).
Outputs side-by-side frequency counts for all columns (except HHINCADJ, which gets summary stats),
notes missing columns, and writes results to output_2023.
"""
import pandas as pd
from pathlib import Path

# Repo-root aware paths
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ROOT = REPO_ROOT / "output_2023"

# File locations (old example outputs and new outputs)
old_dir = REPO_ROOT / "example_2015_outputs" / "hh_persons_model"
new_dir = OUTPUT_ROOT / "populationsim_working_dir" / "output"

files = [
    ("households.csv", "households_{year}_tm2.csv", "households_comparison_summary.txt"),
    ("persons.csv", "persons_{year}_tm2.csv", "persons_comparison_summary.txt")
]

# You may need to update the year if your output file is named differently
YEAR = 2023

# Field labels and descriptions from TM2 documentation
FIELD_LABELS = {
    # Household fields
    'HHINCADJ': 'Household income (2010 dollars)',
    'HINC': 'Household income (2010 dollars)',
    'NP': 'Number of persons in household',
    'VEH': 'Number of vehicles (0-6, -9=GQ)',
    'HHT': 'Household type (1=Married couple, 2-3=Other family, 4-7=Nonfamily, -9=GQ)',
    'BLD': 'Units in structure (1=Mobile, 2=Detached house, 3=Attached, 4-9=Apartments, 10=Boat/RV, -9=GQ)',
    'TYPE': 'Unit type (1=Housing unit, 2=Institutional GQ, 3=Noninstitutional GQ)',
    'UNITTYPE': 'Unit type (1=Housing unit, 2=Institutional GQ, 3=Noninstitutional GQ)',
    'TYPEHUGQ': 'Housing unit/GQ type',
    'TEN': 'Tenure (1=Owned with mortgage, 2=Owned free and clear, 3=Rented, 4=Occupied without rent)',
    'NWRKRS_ESR': 'Number of workers (0-20)',
    'hhgqtype': 'Group quarters type indicator (0=Housing unit, >0=GQ categories)',
    'MTCCountyID': 'County ID (1=SF, 2=San Mateo, 3=Santa Clara, 4=Alameda, 5=Contra Costa, 6=Solano, 7=Napa, 8=Sonoma, 9=Marin)',
    
    # Person fields
    'AGEP': 'Age in years (0-99)',
    'SEX': 'Sex (1=Male, 2=Female)',
    'ESR': 'Employment status recode (1=Employed, 2=Employed not at work, 3=Unemployed, 4=Armed forces, 5=Not in labor force, 6=<16 years old)',
    'EMPLOYED': 'Employment indicator (0=Not employed, 1=Employed)',
    'SCHL': 'Educational attainment (1=No school, 9=HS graduate, 13=Bachelor, 16=Doctorate, -9=N/A)',
    'SCHG': 'Grade level attending (1-7=Preschool through graduate school, -9=N/A)',
    'OCCP': 'Occupation category (1-6=Major occupation groups, -999=N/A)',
    'WKHP': 'Usual hours worked per week (1-99, -9=N/A)',
    'WKW': 'Weeks worked in past 12 months (1-6=Categorized weeks, -9=N/A)',
    'person_type': 'Person type for travel modeling (1-8)',
    'PUMA': 'Public Use Microdata Area code',
}

# Value labels for coded fields
VALUE_LABELS = {
    'TYPE': {
        '1': 'Housing unit',
        '2': 'Institutional GQ',
        '3': 'Noninstitutional GQ',
    },
    'UNITTYPE': {
        '1': 'Housing unit',
        '2': 'Institutional GQ',
        '3': 'Noninstitutional GQ',
    },
    'HHT': {
        '1': 'Married couple family',
        '2': 'Other family, male householder',
        '3': 'Other family, female householder',
        '4': 'Nonfamily, male alone',
        '5': 'Nonfamily, male not alone',
        '6': 'Nonfamily, female alone',
        '7': 'Nonfamily, female not alone',
        '-9': 'N/A (GQ)',
    },
    'BLD': {
        '1': 'Mobile home/trailer',
        '2': 'One-family detached',
        '3': 'One-family attached',
        '4': '2 Apartments',
        '5': '3-4 Apartments',
        '6': '5-9 Apartments',
        '7': '10-19 Apartments',
        '8': '20-49 Apartments',
        '9': '50+ Apartments',
        '10': 'Boat/RV/van',
        '-9': 'N/A (GQ)',
    },
    'TEN': {
        '1': 'Owned with mortgage',
        '2': 'Owned free and clear',
        '3': 'Rented',
        '4': 'Occupied without rent',
    },
    'SEX': {
        '1': 'Male',
        '2': 'Female',
    },
    'ESR': {
        '1': 'Employed',
        '2': 'Employed, not at work',
        '3': 'Unemployed',
        '4': 'Armed forces',
        '5': 'Not in labor force',
        '6': '<16 years old',
    },
    'EMPLOYED': {
        '0': 'Not employed',
        '1': 'Employed',
    },
    'hhgqtype': {
        '0': 'Housing unit',
        '1': 'GQ type 1',
        '2': 'GQ type 2',
        '3': 'GQ type 3',
        '4': 'GQ type 4',
        '5': 'GQ type 5',
    },
    'MTCCountyID': {
        '1': 'San Francisco',
        '2': 'San Mateo',
        '3': 'Santa Clara',
        '4': 'Alameda',
        '5': 'Contra Costa',
        '6': 'Solano',
        '7': 'Napa',
        '8': 'Sonoma',
        '9': 'Marin',
    },
}

def compare_files(old_file, new_file, out_file, key_col="HHINCADJ"):
    if not old_file.exists():
        print(f"[WARN] Old file not found: {old_file}")
        return
    if not new_file.exists():
        print(f"[WARN] New file not found: {new_file}")
        return

    old_df = pd.read_csv(old_file)
    new_df = pd.read_csv(new_file)

    out_file.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(f"Comparing: {old_file} vs {new_file}\n\n")
        # Column matching
        old_cols = set(old_df.columns)
        new_cols = set(new_df.columns)
        all_cols = sorted(old_cols | new_cols)
        f.write("Column presence:\n")
        for col in all_cols:
            in_old = col in old_cols
            in_new = col in new_cols
            status = (
                "Both" if in_old and in_new else
                "Only in old" if in_old else
                "Only in new"
            )
            label = FIELD_LABELS.get(col, "")
            label_str = f" - {label}" if label else ""
            f.write(f"  {col}: {status}{label_str}\n")
        f.write("\n")
        # Only compare columns present in both
        common_cols = sorted(old_cols & new_cols)
        for col in common_cols:
            # Skip columns that are likely ID columns or are MAZ/TAZ columns
            col_lower = col.lower()
            if (
                'id' in col_lower or
                col_lower in ('maz', 'taz', 'maz_node', 'taz_node') or
                'maz_' in col_lower or 'taz_' in col_lower
            ):
                continue
            label = FIELD_LABELS.get(col, "")
            label_str = f" - {label}" if label else ""
            f.write(f"=== {col}{label_str} ===\n")
            if col.upper() == key_col.upper():
                # Numeric summary
                old_vals = pd.to_numeric(old_df[col], errors='coerce')
                new_vals = pd.to_numeric(new_df[col], errors='coerce')
                stats = [
                    ("mean", old_vals.mean(), new_vals.mean()),
                    ("median", old_vals.median(), new_vals.median()),
                    ("min", old_vals.min(), new_vals.min()),
                    ("max", old_vals.max(), new_vals.max()),
                ]
                f.write("  Stat      Old         New         Diff        %Diff\n")
                for stat, o, n in stats:
                    diff = n - o
                    pct = (diff / o * 100) if o != 0 else float('nan')
                    f.write(f"  {stat:<8} {o:10.2f} {n:10.2f} {diff:10.2f} {pct:10.2f}\n")
                f.write("\n")
            else:
                old_counts = old_df[col].value_counts(dropna=False).sort_index()
                new_counts = new_df[col].value_counts(dropna=False).sort_index()
                # Convert all value keys to strings for safe sorting and lookup
                old_counts_str = old_counts.copy()
                old_counts_str.index = old_counts_str.index.map(str)
                new_counts_str = new_counts.copy()
                new_counts_str.index = new_counts_str.index.map(str)
                all_vals = set(old_counts_str.index) | set(new_counts_str.index)
                
                # Calculate totals for within-group percentages
                old_total = old_counts_str.sum()
                new_total = new_counts_str.sum()
                
                # Sort by old counts (descending)
                all_vals = sorted(all_vals, key=lambda v: old_counts_str.get(v, 0), reverse=True)
                
                f.write("  Value           Old      %Old     New      %New     Diff     %Diff  Label\n")
                for val in all_vals:
                    o = old_counts_str.get(val, 0)
                    n = new_counts_str.get(val, 0)
                    diff = n - o
                    pct_change = (diff / o * 100) if o != 0 else float('nan')
                    
                    # Within-group percentages
                    pct_old = (o / old_total * 100) if old_total > 0 else 0
                    pct_new = (n / new_total * 100) if new_total > 0 else 0
                    
                    # Get value label if available
                    val_label = ""
                    if col in VALUE_LABELS and val in VALUE_LABELS[col]:
                        val_label = VALUE_LABELS[col][val]
                    
                    f.write(f"  {str(val):<15} {o:8} {pct_old:7.2f}% {n:8} {pct_new:7.2f}% {diff:8} {pct_change:8.2f}  {val_label}\n")
                f.write("\n")
        f.write("\n---\n\n")
        f.write("Note: Only columns present in both files are compared. Columns missing in one file are listed above.\n")

if __name__ == "__main__":
    for old_name, new_name_tmpl, out_name in files:
        old_file = old_dir / old_name
        new_file = new_dir / new_name_tmpl.format(year=YEAR)
        out_file = new_dir / out_name
        compare_files(old_file, new_file, out_file)
    print("Comparison summaries written to output_2023.")



