
import pandas as pd
import re
from pathlib import Path

# List of variables to check
variables = ['ESR', 'OCCP', 'SCHG', 'SCHL', 'WKW']

# Files to compare (old and new)
script_pairs = [
    ('create_seed_population_tm2_refactored.py', 'create_seed_population_old.py'),
    ('postprocess_recode.py', 'postprocess_recode_old.py'),
]

def extract_variable_context(filepath, variable, context=5):
    """Extract lines where variable is assigned or recoded, with context."""
    lines = Path(filepath).read_text(encoding='utf-8').splitlines()
    pattern = re.compile(rf'(\b{variable}\b\s*=|\.{variable}\s*=|{variable}\s*[\[\.])')
    matches = [i for i, line in enumerate(lines) if pattern.search(line)]
    snippets = []
    for idx in matches:
        start = max(0, idx - context)
        end = min(len(lines), idx + context + 1)
        snippet = '\n'.join(lines[start:end])
        snippets.append((idx+1, snippet))
    return snippets

for var in variables:
    print(f"\n{'='*40}\nVariable: {var}\n{'='*40}")
    for new_file, old_file in script_pairs:
        for label, file in [('NEW', new_file), ('OLD', old_file)]:
            if not Path(file).exists():
                print(f"[{label}] {file} not found.")
                continue
            print(f"\n[{label}] {file}:")
            contexts = extract_variable_context(file, var)
            if not contexts:
                print("  No direct assignment or recode found.")
            for lineno, snippet in contexts:
                print(f"  [Line {lineno}]\n{snippet}\n")

def compare_unique_values(var, old_csv, new_csv):
    old_df = pd.read_csv(old_csv)
    new_df = pd.read_csv(new_csv)
    old_vals = set(old_df[var].dropna().unique()) if var in old_df else set()
    new_vals = set(new_df[var].dropna().unique()) if var in new_df else set()
    print(f"\nUnique values for {var}:")
    print(f"  Old: {sorted(old_vals)}")
    print(f"  New: {sorted(new_vals)}")

# Example usage:
# compare_unique_values('ESR', 'example_2015_outputs/hh_persons_model/persons.csv', 'output_2023/populationsim_working_dir/output/persons_2023_tm2.csv')
