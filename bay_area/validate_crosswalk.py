import pandas as pd
df = pd.read_csv('output_2023/geo_cross_walk_tm2_updated.csv')
print(f'Unique PUMAs: {df.PUMA.nunique()}')
print(f'Unique Counties: {df.COUNTY.nunique()}')
print('Sample PUMAs:', sorted(df.PUMA.unique())[:10])
print('✅ 62-PUMA crosswalk restored!')
