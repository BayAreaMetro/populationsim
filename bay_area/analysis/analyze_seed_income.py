import pandas as pd
from pathlib import Path

# File path to seed households
seed_file = Path(r"C:\GitHub\populationsim\bay_area\output_2023\populationsim_working_dir\data\seed_households.csv")

# Columns to analyze
income_cols = ['hh_income_2010', 'hh_income_2023', 'HINCP']

# Read the data
print(f"Reading: {seed_file}")
df = pd.read_csv(seed_file, usecols=[col for col in income_cols if col in pd.read_csv(seed_file, nrows=0).columns])

# Prepare summary statistics
summary_stats = {}
for col in income_cols:
    if col in df.columns:
        vals = pd.to_numeric(df[col], errors='coerce').dropna()
        summary_stats[col] = {
            'count': len(vals),
            'mean': vals.mean(),
            'median': vals.median(),
            'min': vals.min(),
            'max': vals.max(),
            'p10': vals.quantile(0.10),
            'p25': vals.quantile(0.25),
            'p50': vals.quantile(0.50),
            'p75': vals.quantile(0.75),
            'p90': vals.quantile(0.90)
        }
    else:
        summary_stats[col] = None

# Output as a markdown table
output_file = Path("analysis/SEED_INCOME_COMPARISON.md")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# Seed Household Income Comparative Table\n\n")
    f.write(f"File: {seed_file}\n\n")
    # Table header
    f.write("| Statistic | hh_income_2010 | hh_income_2023 | HINCP |\n")
    f.write("|-----------|----------------|----------------|------|\n")
    stats = ['count', 'mean', 'median', 'min', 'max', 'p10', 'p25', 'p50', 'p75', 'p90']
    for stat in stats:
        row = [stat]
        for col in income_cols:
            if summary_stats[col] is not None:
                val = summary_stats[col][stat]
                if stat == 'count':
                    row.append(f"{int(val):,}")
                else:
                    row.append(f"${val:,.2f}")
            else:
                row.append("N/A")
        f.write(f"| {' | '.join(row)} |\n")

print(f"\n✓ Seed income comparative table written to {output_file}")
