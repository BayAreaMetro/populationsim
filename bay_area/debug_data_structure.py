import pandas as pd
import numpy as np

# Load the incidence table that was generated
print('Loading incidence table...')
pipeline_path = 'output_2023/populationsim_working_dir/output/pipeline.h5'
try:
    incidence = pd.read_hdf(pipeline_path, '/incidence_table/setup_data_structures')
    print(f'Incidence table shape: {incidence.shape}')
    print(f'Incidence table columns: {list(incidence.columns)}')
    print(f'Incidence table index type: {type(incidence.index)}')
    print(f'Incidence table index range: {incidence.index.min()} to {incidence.index.max()}')
    print()
    
    # Check for any remaining data issues
    print('Checking for data issues:')
    print(f'Total NaN values: {incidence.isna().sum().sum()}')
    
    print('\nNaN values by column:')
    nan_counts = incidence.isna().sum()
    for col, count in nan_counts.items():
        if count > 0:
            print(f'  {col}: {count}')
    
    # Check the sample_weight column specifically
    print(f'\nSample weight column:')
    print(f'  Total values: {len(incidence)}')
    print(f'  NaN count: {incidence["sample_weight"].isna().sum()}')
    if not incidence['sample_weight'].isna().all():
        print(f'  Min value: {incidence["sample_weight"].min()}')
        print(f'  Max value: {incidence["sample_weight"].max()}')

    # Check if the NaN values are clustered at the end (suggesting index mismatch)
    print(f'\nFirst few sample_weight values:')
    print(incidence['sample_weight'].head(10))
    print(f'\nLast few sample_weight values:')
    print(incidence['sample_weight'].tail(10))

    # Check which household IDs have NaN values
    nan_indices = incidence[incidence['sample_weight'].isna()].index
    print(f'\nHousehold IDs with NaN sample_weight (first 10):')
    print(list(nan_indices[:10]))
    print(f'Household IDs with NaN sample_weight (last 10):')
    print(list(nan_indices[-10:]))
    
except Exception as e:
    print(f'Error loading data: {e}')
    import traceback
    traceback.print_exc()
