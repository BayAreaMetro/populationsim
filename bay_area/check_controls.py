"""Quick diagnostic to check control files structure."""
import pandas as pd
import os

data_dir = 'output_2023/populationsim_working_dir/data'
files = {
    'MAZ': 'maz_marginals_hhgq.csv',
    'TAZ': 'taz_marginals_hhgq.csv', 
    'COUNTY': 'county_marginals.csv'
}

print("="*70)
print("CONTROL FILES DIAGNOSTIC")
print("="*70)

for geo_name, filename in files.items():
    path = os.path.join(data_dir, filename)
    if os.path.exists(path):
        df = pd.read_csv(path)
        geo_cols = [c for c in df.columns if 'NODE' in c.upper() or c.upper() == 'COUNTY']
        geo_col = geo_cols[0] if geo_cols else df.columns[0]
        
        print(f"\n{filename}")
        print(f"  Rows: {len(df)}")
        print(f"  Geography column: {geo_col}")
        print(f"  Unique geographies: {df[geo_col].nunique()}")
        print(f"  Has duplicates: {len(df) != df[geo_col].nunique()}")
        print(f"  Control columns: {len(df.columns)-1}")
        print(f"  Column names: {list(df.columns)}")
        
        # Check for any null values
        nulls = df.isnull().sum().sum()
        if nulls > 0:
            print(f"  ⚠️ WARNING: {nulls} null values found")
            
    else:
        print(f"\n{filename}: NOT FOUND")

print("\n" + "="*70)
