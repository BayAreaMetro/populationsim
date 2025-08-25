#!/usr/bin/env python3
"""
Compare old and new synthetic population outputs (households and persons).
Outputs side-by-side frequency counts for all columns (except HHINCADJ, which gets summary stats),
notes missing columns, and writes results to output_2023.
"""
import pandas as pd
from pathlib import Path

# File locations
old_dir = Path(r"C:/GitHub/populationsim/bay_area/example_2015_outputs/hh_persons_model")
new_dir = Path(r"C:/GitHub/populationsim/bay_area/output_2023/populationsim_working_dir/output")

files = [
    ("households.csv", "households_{year}_tm2.csv", "households_comparison_summary.txt"),
    ("persons.csv", "persons_{year}_tm2.csv", "persons_comparison_summary.txt")
]

# You may need to update the year if your output file is named differently
YEAR = 2023

def compare_files(old_file, new_file, out_file, key_col="HHINCADJ"):
    old_df = pd.read_csv(old_file)
    new_df = pd.read_csv(new_file)
    
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
            f.write(f"  {col}: {status}\n")
        f.write("\n")
        # Only compare columns present in both
        common_cols = sorted(old_cols & new_cols)
        for col in common_cols:
            # Skip columns that are likely ID columns or are MAZ/TAZ columns
            col_lower = col.lower()
            if 'id' in col_lower or col_lower == 'maz' or col_lower == 'taz':
                continue
            f.write(f"=== {col} ===\n")
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
                all_vals = sorted(set(old_counts_str.index) | set(new_counts_str.index))
                f.write("  Value           Old      New      Diff     %Diff\n")
                for val in all_vals:
                    o = old_counts_str.get(val, 0)
                    n = new_counts_str.get(val, 0)
                    diff = n - o
                    pct = (diff / o * 100) if o != 0 else float('nan')
                    f.write(f"  {str(val):<15} {o:8} {n:8} {diff:8} {pct:8.2f}\n")
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
