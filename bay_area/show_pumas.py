#!/usr/bin/env python3
import pandas as pd

# Load the households data
df = pd.read_csv('hh_gq/data/seed_households.csv')

# Show available PUMAs
pumas = sorted(df['PUMA'].unique())
print("Available PUMAs in Bay Area data:")
print("First 20 PUMAs:", pumas[:20])
print(f"Total number of PUMAs: {len(pumas)}")

# Show PUMA value counts (top 10)
print("\nTop 10 PUMAs by household count:")
print(df['PUMA'].value_counts().head(10))
