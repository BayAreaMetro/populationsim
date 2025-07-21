import sys
sys.path.append('tm2_control_utils')
from config import CONTROLS, ACS_EST_YEAR
import pandas as pd

def show_region_targets():
    print('='*80)
    print('REGION TARGETS CONFIGURATION')
    print('='*80)
    
    region_targets = CONTROLS[ACS_EST_YEAR]['REGION_TARGETS']
    
    target_data = []
    for target_name, target_config in region_targets.items():
        data_source, year, table, geography, variables = target_config
        
        var_str = ''
        if variables:
            var_str = ', '.join([var[0] if isinstance(var, tuple) else str(var) for var in variables])
        else:
            var_str = f'{table}_001E (total)'
            
        target_data.append({
            'Target Name': target_name,
            'Data Source': data_source.upper(),
            'Year': year,
            'Table': table,
            'Geography': geography,
            'Variables': var_str
        })
    
    df = pd.DataFrame(target_data)
    print(df.to_string(index=False))
    print()
    
    print('SUMMARY:')
    print(f'- Total targets: {len(target_data)}')
    print(f'- Data sources: {set([t["Data Source"] for t in target_data])}')
    print(f'- Year: {target_data[0]["Year"]}')
    print(f'- Geography level: {target_data[0]["Geography"]}')
    print()
    
    print('RAW CONFIGURATION:')
    print('-' * 50)
    for target_name, target_config in region_targets.items():
        print(f'{target_name}: {target_config}')

if __name__ == "__main__":
    show_region_targets()
