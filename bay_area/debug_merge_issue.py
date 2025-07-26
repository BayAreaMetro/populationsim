import pandas as pd
import geopandas as gpd
import os

print('=== TAZ CONTROL DATA ===')
if os.path.exists('output_2023/taz_marginals.csv'):
    taz_data = pd.read_csv('output_2023/taz_marginals.csv')
    print(f'TAZ data shape: {taz_data.shape}')
    print(f'TAZ data columns: {list(taz_data.columns)}')
    print('TAZ data head:')
    print(taz_data.head())
    print(f'TAZ field values (first 10): {taz_data["TAZ"].head(10).tolist()}')
    print(f'TAZ field dtype: {taz_data["TAZ"].dtype}')
else:
    print('TAZ marginals file not found!')

print('\n=== SHAPEFILE DATA ===')
try:
    shapefile_path = r'C:\GitHub\tm2py-utils\tm2py_utils\inputs\maz_taz\shapefiles\tazs_TM2_v2_2.shp'
    if os.path.exists(shapefile_path):
        gdf = gpd.read_file(shapefile_path)
        print(f'Shapefile shape: {gdf.shape}')
        print(f'Shapefile columns: {list(gdf.columns)}')
        print(f'taz field values (first 10): {gdf["taz"].head(10).tolist()}')
        print(f'taz field dtype: {gdf["taz"].dtype}')
        
        # Check for merge compatibility
        print('\n=== MERGE COMPATIBILITY ===')
        taz_unique = set(taz_data["TAZ"].unique())
        shp_unique = set(gdf["taz"].unique())
        print(f'Unique TAZ values in control data: {len(taz_unique)}')
        print(f'Unique taz values in shapefile: {len(shp_unique)}')
        print(f'Intersection: {len(taz_unique & shp_unique)}')
        print(f'Control data only: {len(taz_unique - shp_unique)}')
        print(f'Shapefile only: {len(shp_unique - taz_unique)}')
        
        # Sample of non-matching values
        if len(taz_unique - shp_unique) > 0:
            print(f'Sample control-only values: {list(taz_unique - shp_unique)[:10]}')
        if len(shp_unique - taz_unique) > 0:
            print(f'Sample shapefile-only values: {list(shp_unique - taz_unique)[:10]}')
            
    else:
        print('Shapefile not found!')
except Exception as e:
    print(f'Error reading shapefile: {e}')
