import pandas as pd

# Read the TAZ marginals
df = pd.read_csv('output_2023/taz_marginals.csv')

# Check age control columns
age_cols = [c for c in df.columns if 'pers_age' in c]
print(f"Age control columns: {age_cols}")
print(f"Total TAZs: {len(df)}")
print(f"Total TAZ range: {df['TAZ'].min()} to {df['TAZ'].max()}")

print("\nAge control statistics:")
for col in age_cols:
    non_zero = (df[col] > 0).sum()
    total_val = df[col].sum()
    max_val = df[col].max()
    print(f"  {col}:")
    print(f"    Non-zero TAZs: {non_zero}")
    print(f"    Total sum: {total_val:,.0f}")
    print(f"    Max value: {max_val:.0f}")

print(f"\nTotal persons across all age groups: {df[age_cols].sum().sum():,.0f}")

# Sample of TAZs with age data
print(f"\nSample TAZs with age data:")
sample_tazs = df[df[age_cols].sum(axis=1) > 0].head(5)
print(sample_tazs[['TAZ'] + age_cols].to_string(index=False))
