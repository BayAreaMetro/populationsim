import pandas as pd
import os
from tm2_control_utils.config_census import PRIMARY_OUTPUT_DIR, GEO_CROSSWALK_TM2_FILE

def scale_existing_maz_data():
    """
    Direct approach: Take existing MAZ data and apply county scaling factors
    This bypasses the slow census data fetching process
    """
    
    print("=== DIRECT MAZ SCALING APPROACH ===")
    
    # Load county targets
    targets_df = pd.read_csv('output_2023/county_targets_acs2023.csv')
    hh_targets = targets_df[targets_df['target_name'] == 'num_hh_target_by_county'].set_index('county_fips')['target_value']
    pop_targets = targets_df[targets_df['target_name'] == 'tot_pop_target_by_county'].set_index('county_fips')['target_value']
    
    print(f"Loaded targets for {len(hh_targets)} counties")
    
    # Load existing MAZ data (this should have 2020 household/pop data)
    existing_files = [
        'output_2023/maz_marginals.csv',  # Current file (might be incomplete)
        'maz_data_hh_pop.csv',           # Alternative source
        'example_maz_data.csv'           # Another alternative
    ]
    
    maz_df = None
    for file_path in existing_files:
        if os.path.exists(file_path):
            try:
                temp_df = pd.read_csv(file_path)
                if 'MAZ' in temp_df.columns:
                    print(f"Found MAZ data in: {file_path}")
                    print(f"Columns: {temp_df.columns.tolist()}")
                    print(f"Rows: {len(temp_df)}")
                    
                    # Check if it has household/population data
                    hh_cols = [col for col in temp_df.columns if 'hh' in col.lower() or 'household' in col.lower()]
                    pop_cols = [col for col in temp_df.columns if 'pop' in col.lower() and 'total' in col.lower()]
                    
                    print(f"Household columns: {hh_cols}")
                    print(f"Population columns: {pop_cols}")
                    
                    if hh_cols and pop_cols:
                        maz_df = temp_df
                        hh_col = hh_cols[0]
                        pop_col = pop_cols[0] 
                        print(f"Using {file_path} with {hh_col} and {pop_col}")
                        break
                        
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue
    
    if maz_df is None:
        print("ERROR: Could not find suitable MAZ data file with household/population columns")
        return False
        
    # Load crosswalk and apply county mapping
    crosswalk_df = pd.read_csv(os.path.join(PRIMARY_OUTPUT_DIR, GEO_CROSSWALK_TM2_FILE))
    
    # County mapping
    county_to_fips_mapping = {
        1: '075',  # San Francisco
        2: '081',  # San Mateo  
        3: '085',  # Santa Clara
        4: '001',  # Alameda
        5: '013',  # Contra Costa
        6: '095',  # Solano
        7: '055',  # Napa
        8: '097',  # Sonoma
        9: '041'   # Marin
    }
    
    # Create county mapping
    county_map = crosswalk_df[['MAZ', 'COUNTY']].drop_duplicates()
    county_map['county_fips'] = county_map['COUNTY'].map(county_to_fips_mapping)
    
    # Merge MAZ data with county mapping
    maz_with_county = maz_df.merge(county_map[['MAZ', 'county_fips']], on='MAZ', how='left')
    
    # Calculate current totals by county
    county_current_hh = maz_with_county.groupby('county_fips')[hh_col].sum()
    county_current_pop = maz_with_county.groupby('county_fips')[pop_col].sum()
    
    print("\nCounty scaling factors:")
    for county_fips in county_current_hh.index:
        if county_fips in hh_targets.index:
            current_hh = county_current_hh[county_fips]
            target_hh = hh_targets[county_fips]
            hh_scale = target_hh / current_hh if current_hh > 0 else 1.0
            
            current_pop = county_current_pop[county_fips]
            target_pop = pop_targets[county_fips]
            pop_scale = target_pop / current_pop if current_pop > 0 else 1.0
            
            print(f"County {county_fips}: HH scale={hh_scale:.4f}, Pop scale={pop_scale:.4f}")
            
            # Apply scaling
            county_mask = maz_with_county['county_fips'] == county_fips
            maz_with_county.loc[county_mask, hh_col] = (maz_with_county.loc[county_mask, hh_col] * hh_scale).round().astype(int)
            maz_with_county.loc[county_mask, pop_col] = (maz_with_county.loc[county_mask, pop_col] * pop_scale).round().astype(int)
    
    # Check results
    final_hh = maz_with_county[hh_col].sum()
    final_pop = maz_with_county[pop_col].sum()
    target_hh_total = hh_targets.sum()
    target_pop_total = pop_targets.sum()
    
    print(f"\nScaling results:")
    print(f"Final households: {final_hh:,} (target: {target_hh_total:,})")
    print(f"Final population: {final_pop:,} (target: {target_pop_total:,})")
    print(f"HH difference: {final_hh - target_hh_total:,}")
    print(f"Pop difference: {final_pop - target_pop_total:,}")
    
    # Save the scaled MAZ data
    output_df = maz_with_county[['MAZ', hh_col, pop_col]].rename(columns={hh_col: 'num_hh', pop_col: 'total_pop'})
    output_df.to_csv('output_2023/maz_marginals_scaled.csv', index=False)
    
    print(f"Saved scaled data to: output_2023/maz_marginals_scaled.csv")
    return True

if __name__ == "__main__":
    scale_existing_maz_data()
