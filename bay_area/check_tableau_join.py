import geopandas as gpd
import pandas as pd

# Load files
shp = gpd.read_file('output_2023/tableau/maz_boundaries_tableau.shp')
csv = pd.read_csv('output_2023/tableau/maz_data_tableau.csv')

# Get unique IDs
shp_ids = set(shp['MAZ_ID'])
csv_ids = set(csv['MAZ_ID'])

print('Shapefile:', len(shp), 'records,', len(shp_ids), 'unique MAZ_IDs')
print('CSV:', len(csv), 'records,', len(csv_ids), 'unique MAZ_IDs')
print('Match:', len(shp_ids.intersection(csv_ids)), 'IDs in both')

only_shp = shp_ids - csv_ids
only_csv = csv_ids - shp_ids

if only_shp:
    print(f'\nOnly in shapefile: {len(only_shp)} IDs')
    print('Sample:', sorted(list(only_shp))[:20])

if only_csv:
    print(f'\nOnly in CSV: {len(only_csv)} IDs')
    print('Sample:', sorted(list(only_csv))[:20])

# Check for nulls
print('\nNull check:')
print('Shapefile MAZ_ID nulls:', shp['MAZ_ID'].isna().sum())
print('CSV MAZ_ID nulls:', csv['MAZ_ID'].isna().sum())
