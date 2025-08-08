import pandas as pd

# Check county mapping
df = pd.read_csv('output_2023/geo_cross_walk_tm2_updated.csv')
county_map = df[['COUNTY', 'county_name']].drop_duplicates().sort_values('COUNTY')
print('County mapping:')
for _, row in county_map.iterrows():
    print(f'  {row["COUNTY"]}: {row["county_name"]}')

print(f'\nTotal MAZs: {len(df)}')
print(f'Unique PUMAs: {df["PUMA"].nunique()}')
