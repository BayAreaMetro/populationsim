import numpy
import pandas as pd
import collections
import logging
from tm2_control_utils.geog_utils import add_aggregate_geography_colums
from tm2_control_utils.config import GEOGRAPHY_ID_COLUMNS, CENSUS_DEFINITIONS


# Utility to get GEOID column for a geography

def get_geoid_col(df, geography):
    """
    Return the GEOID column name for the given geography in the DataFrame, or None if not found.
    """
    geo = geography.lower().replace('_', ' ')
    candidates = [
        f'GEOID_{geo}',
        geo + '2020ge',
        geo.replace(' ', '') + '2020ge',
        geo.replace(' ', '_') + '2020ge',
        geo.replace(' ', '').upper() + '2020GE',
        'GEOID',
    ]
    for c in candidates:
        if c in df.columns:
            return c
    # Fallback: first column containing 'GEOID'
    for c in df.columns:
        if 'GEOID' in c:
            return c
    return None


def census_col_is_in_control(param_dict, control_dict):
    """
    param_dict is from  CENSUS_DEFINITIONS,   e.g. OrderedDict([('pers_min',4), ('pers_max', 4)])
    control_dict is from control definitions, e.g. OrderedDict([('pers_min',4), ('pers_max',10)])

    Checks if this census column should be included in the control.
    Returns True or False.
    """
    # assume true unless kicked out
    for control_name, control_val in control_dict.items():
        if control_name not in param_dict:
            pass # later

        # if the value is a string, require exact match
        if isinstance(control_val, str):
            if control_dict[control_name] != param_dict[control_name]:
                return False
            continue

        # otherwise, check the min/max ranges
        if control_name.endswith('_min') and param_dict[control_name] < control_dict[control_name]:
            # census includes values less than control allows
            return False

        if control_name.endswith('_max') and param_dict[control_name] > control_dict[control_name]:
            # census includes values greater than control allows
            return False

    return True

def create_control_table(control_name, control_dict_list, census_table_name, census_table_df):
    """
    Given a control list of ordered dictionary (e.g. [{"pers_min":1, "pers_max":NPER_MAX}]) for a specific control,
    returns a version of the census table with just the relevant column, plus geography columns.
    """
    # Identify geography columns (those present in census_table_df and likely to be geo columns)
    possible_geo_cols = [
        'state', 'county', 'tract', 'block', 'block group',
        'GEOID', 'GEOID_block', 'GEOID_block group', 'GEOID_tract', 'GEOID_county'
    ]
    geo_cols = [col for col in possible_geo_cols if col in census_table_df.columns]

    # Debug: print dtype and unique values of data columns before summing
    data_cols = [col for col in census_table_df.columns if col not in geo_cols]
    for col in data_cols:
        try:
            print(f"[DEBUG] dtype of {col}: {census_table_df[col].dtypes if hasattr(census_table_df[col], 'dtypes') else 'N/A'}")
            print(f"[DEBUG] unique values of {col} (sample): {census_table_df[col].unique()[:10] if hasattr(census_table_df[col], 'unique') else 'N/A'}")
        except Exception as e:
            print(f"[DEBUG] Error inspecting column {col}: {e}")

    # If all control_dicts are empty, sum once outside the loop
    if all(len(control_dict) == 0 for control_dict in control_dict_list):
        summed = census_table_df[data_cols].apply(
            lambda x: pd.to_numeric(x.astype(str).str.replace(',', '').str.replace(' ', ''), errors="coerce").fillna(0)
        ).sum(axis=1)
        control_df = pd.DataFrame({control_name: summed.astype(float)})
    else:
        control_df = pd.DataFrame(index=census_table_df.index, columns=[control_name], data=0.0)
        for control_dict in control_dict_list:
            # If control_dict is empty, always sum all non-geo columns (even if there are multiple columns)
            if len(control_dict) == 0:
                data_cols = [col for col in census_table_df.columns if col not in geo_cols]
                # Clean and sum all data columns at once
                summed = census_table_df[data_cols].apply(
                    lambda x: pd.to_numeric(x.astype(str).str.replace(',', '').str.replace(' ', ''), errors="coerce").fillna(0)
                ).sum(axis=1)
                control_df[control_name] = summed.astype(float)
            else:
                # Handle both MultiIndex and regular Index
                if isinstance(census_table_df.columns, pd.MultiIndex):
                    for colnum in range(len(census_table_df.columns.levels[0])):
                        param_dict = collections.OrderedDict()
                        variable_name = census_table_df.columns.get_level_values(0)[colnum]
                        for paramnum in range(1, len(census_table_df.columns.names)):
                            param = census_table_df.columns.names[paramnum]
                            try:
                                param_dict[param] = int(census_table_df.columns.get_level_values(paramnum)[colnum])
                            except:
                                param_dict[param] = census_table_df.columns.get_level_values(paramnum)[colnum]
                        if param_dict == control_dict:
                            control_df["temp"] = census_table_df[variable_name]
                            control_df[control_name] = census_table_df[variable_name]
                            control_df.drop(columns="temp", inplace=True)
                            break
                        if census_col_is_in_control(param_dict, control_dict):
                            control_df["temp"] = census_table_df[variable_name]
                            # Ensure temp and control_name columns are numeric before summing
                            control_df["temp"] = pd.to_numeric(control_df["temp"], errors="coerce").fillna(0)
                            control_df[control_name] = pd.to_numeric(control_df[control_name], errors="coerce").fillna(0)
                            control_df[control_name] = control_df[control_name] + control_df["temp"]
                            control_df.drop(columns="temp", inplace=True)
                else:
                    # Regular Index: Use CENSUS_DEFINITIONS to find matching columns
                    if census_table_name in CENSUS_DEFINITIONS:
                        table_def = CENSUS_DEFINITIONS[census_table_name]
                        header_row = table_def[0]  # e.g. ['variable','family','pers_min','pers_max']
                        
                        # Find columns that match the control criteria
                        for row in table_def[1:]:  # Skip header row
                            if len(row) != len(header_row):
                                continue
                                
                            # Create parameter dict for this census column
                            param_dict = collections.OrderedDict()
                            variable_name = row[0]  # e.g. 'B11016_010E'
                            for i, param_name in enumerate(header_row[1:], 1):  # Skip 'variable'
                                try:
                                    param_dict[param_name] = int(row[i]) if str(row[i]).isdigit() else row[i]
                                except (ValueError, IndexError):
                                    param_dict[param_name] = row[i] if i < len(row) else 0
                            
                            # Check if this column matches the control criteria
                            if census_col_is_in_control(param_dict, control_dict):
                                if variable_name in census_table_df.columns:
                                    col_data = census_table_df[variable_name].astype(str).str.replace(',', '').str.replace(' ', '')
                                    col_data = pd.to_numeric(col_data, errors="coerce").fillna(0)
                                    control_df["temp"] = col_data
                                    control_df[control_name] = pd.to_numeric(control_df[control_name], errors="coerce").fillna(0)
                                    control_df[control_name] = control_df[control_name] + control_df["temp"]
                                    control_df.drop(columns="temp", inplace=True)
                    else:
                        # Fallback: sum all non-geo columns if no table definition found
                        data_cols = [col for col in census_table_df.columns if col not in geo_cols]
                        for variable_name in data_cols:
                            col_data = census_table_df[variable_name].astype(str).str.replace(',', '').str.replace(' ', '')
                            col_data = pd.to_numeric(col_data, errors="coerce").fillna(0)
                            control_df["temp"] = col_data
                            control_df[control_name] = pd.to_numeric(control_df[control_name], errors="coerce").fillna(0)
                            control_df[control_name] = control_df[control_name] + control_df["temp"]
                            control_df.drop(columns="temp", inplace=True)
            new_sum = control_df[control_name].sum()

    # Always include geography columns in the returned DataFrame
    if geo_cols:
        geo_df = census_table_df[geo_cols].copy()
        # If index is not aligned, reset and merge
        if not geo_df.index.equals(control_df.index):
            geo_df = geo_df.reset_index(drop=True)
            control_df = control_df.reset_index(drop=True)
        control_df = pd.concat([geo_df, control_df], axis=1)
    # Ensure GEOID for the most detailed geography present
    for geo in ["block", "block group", "tract", "county"]:
        try:
            control_df = ensure_geoid_column(control_df, geo)
        except Exception:
            continue
    # Skip writing intermediate control table to CSV
    return control_df



def prepare_geography_columns(df, census_geography):
    # If you already have a GEOID column, just use it
    possible_geoid_cols = ['blk2020ge', 'blk2010ge', 'GEOID_block', 'GEOID']
    for col in possible_geoid_cols:
        if col in df.columns:
            df = df.rename(columns={col: 'GEOID_block'})
            return df
    # Otherwise, try to build from state/county/tract/block
    geo_col_map = {
        "block":       ['state', 'county', 'tract', 'block'],
        "block group": ['state', 'county', 'tract', 'block group'],
        "tract":       ['state', 'county', 'tract'],
        "county":      ['state', 'county']
    }
    expected_cols = geo_col_map.get(census_geography)
    if expected_cols and all(col in df.columns for col in expected_cols):
        df['GEOID_block'] = df['state'] + df['county'] + df['tract'] + df['block']
    return df

def add_geoid_column(df, census_geography):
    """
    Robustly create or use a GEOID column for the specified geography.
    If a suitable GEOID column already exists, use it. Otherwise, try to build from components.
    """
    df = df.copy()
    geo = census_geography.lower().replace("_", " ")
    crosswalk_col_map = {
        "block": "blk2020ge",
        "block group": "bg2020ge",
        "tract": "tr2020ge",
        "county": "cty2020ge"
    }
    geoid_col = crosswalk_col_map.get(geo)
    alt_cols = [
        geoid_col,
        f"GEOID_{geo}",
        "GEOID",
        geo.replace(" ", "") + "2020ge",
        geo.replace(" ", "_") + "2020ge",
        geo.replace(" ", "").upper() + "2020GE"
    ]
    for alt in alt_cols:
        if alt and alt in df.columns:
            df["GEOID_" + geo] = df[alt]
            return df
    # Otherwise, try to build from components
    geo_specs = {
        "block":       [("state", 2), ("county", 3), ("tract", 6), ("block", 4)],
        "block group": [("state", 2), ("county", 3), ("tract", 6), ("block group", 1)],
        "tract":       [("state", 2), ("county", 3), ("tract", 6)],
        "county":      [("state", 2), ("county", 3)],
    }
    if geo not in geo_specs:
        raise ValueError(f"Unsupported geography: {geo}")
    for col, _ in geo_specs[geo]:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame for geography '{geo}' and no suitable GEOID column present.")
    parts = [df[col].astype(str).str.zfill(width) for col, width in geo_specs[geo]]
    df["GEOID_" + geo] = parts[0].str.cat(parts[1:], sep='') if len(parts) > 1 else parts[0]
    return df

def ensure_geoid_column(df, geography):
    """
    Ensure the DataFrame has a GEOID column for the specified geography (block, block group, tract, county).
    If not present, construct it from component columns with correct zero-padding, using config-driven names.
    Returns the DataFrame with a new or existing GEOID_{geography} column.
    Adds diagnostics to show the first few constructed GEOIDs and columns used.
    For non-census geographies (maz, taz, region), returns df unchanged.
    For temp controls already aggregated to MAZ level, skips GEOID construction.
    """
    import logging
    from tm2_control_utils.config import GEOGRAPHY_ID_COLUMNS
    geo = geography.lower().replace('_', ' ')
    supported = ["block", "block group", "tract", "county"]
    colname = GEOGRAPHY_ID_COLUMNS.get(geo, {}).get('census', f'GEOID_{geo}')
    if geo not in supported:
        return df
    # If already present, just return
    if colname in df.columns:
        return df
    # Try to find an alternate GEOID column
    alt_cols = [
        colname,
        'GEOID',
        GEOGRAPHY_ID_COLUMNS[geo].get('crosswalk'),
        GEOGRAPHY_ID_COLUMNS[geo].get('mapping'),
    ]
    for alt in alt_cols:
        if alt and alt in df.columns:
            df[colname] = df[alt]
            logging.error(f"[GEOID] Used alternate GEOID column '{alt}' for '{geo}'")
            print(f"[GEOID] Used alternate GEOID column '{alt}' for '{geo}'")
            return df
    # Otherwise, try to build from components using config
    components = GEOGRAPHY_ID_COLUMNS[geo].get('components', [])
    missing_cols = [col for col in components if col not in df.columns]
    if missing_cols:
        logging.error(f"[GEOID] Missing columns {missing_cols} for GEOID construction at '{geo}' level.")
        print(f"[GEOID] Missing columns {missing_cols} for GEOID construction at '{geo}' level.")
        
        # For temporary controls that have been aggregated to MAZ level, we might not have component columns
        # Check if this is a temp control that has already been aggregated to MAZ level
        if df.index.name == 'MAZ' or 'MAZ' in df.columns:
            logging.error(f"[GEOID] DataFrame appears to be MAZ-level temp control, skipping GEOID construction for '{geo}'")
            print(f"[GEOID] DataFrame appears to be MAZ-level temp control, skipping GEOID construction for '{geo}'")
            return df
            
        raise ValueError(f"Column(s) {missing_cols} not found in DataFrame for geography '{geo}' and no suitable GEOID column present.")
    # Use correct zero-padding for each component
    pad_widths = {'state': 2, 'county': 3, 'tract': 6, 'block': 4, 'block group': 1}
    parts = [df[col].astype(str).str.zfill(pad_widths.get(col, 1)) for col in components]
    df[colname] = parts[0].str.cat(parts[1:], sep='') if len(parts) > 1 else parts[0]
    logging.error(f"[GEOID] Constructed {colname} from columns {components}. Sample: {df[colname].head(5).tolist()}")
    print(f"[GEOID] Constructed {colname} from columns {components}. Sample: {df[colname].head(5).tolist()}")
    return df

def temp_table_scaling(control_table_df, control_name, scale_numerator, scale_denominator, temp_controls, maz_taz_def_df=None, geography=None):
    import pandas as pd
    import numpy
    import logging
    
    # Add diagnostics
    print(f"[DEBUG] temp_table_scaling: control_name={control_name}, scale_numerator={scale_numerator}, scale_denominator={scale_denominator}")
    print(f"[DEBUG] control_table_df columns: {list(control_table_df.columns)}")
    print(f"[DEBUG] control_table_df head:\n{control_table_df.head()}")
    
    if scale_numerator and scale_numerator in temp_controls:
        print(f"[DEBUG] scale_numerator table columns: {list(temp_controls[scale_numerator].columns)}")
        print(f"[DEBUG] scale_numerator table head:\n{temp_controls[scale_numerator].head()}")
    
    if scale_denominator and scale_denominator in temp_controls:
        print(f"[DEBUG] scale_denominator table columns: {list(temp_controls[scale_denominator].columns)}")
        print(f"[DEBUG] scale_denominator table head:\n{temp_controls[scale_denominator].head()}")
    
    if geography is None:
        for g in ["block", "block group", "tract", "county"]:
            if get_geoid_col(control_table_df, g):
                geography = g
                break
                
    print(f"[DEBUG] Using geography: {geography}")
    
    # Check if temp controls are MAZ-level (already aggregated)
    scale_denom_df = temp_controls.get(scale_denominator)
    scale_num_df = temp_controls.get(scale_numerator) if scale_numerator else None
    
    is_maz_level = (scale_denom_df is not None and 
                   (scale_denom_df.index.name == 'MAZ' or 'MAZ' in scale_denom_df.columns))
    
    if is_maz_level:
        print(f"[DEBUG] Detected MAZ-level temp controls, performing MAZ-level scaling")
        
        # First, aggregate control_table_df to MAZ level if needed
        if 'MAZ' not in control_table_df.columns:
            print(f"[DEBUG] Need to aggregate control_table_df to MAZ level first")
            # Need to use aggregate_to_control_geo to get the control to MAZ level
            
            if maz_taz_def_df is None:
                raise ValueError("maz_taz_def_df is required for MAZ-level scaling")
            
            print(f"[DEBUG] maz_taz_def_df columns: {list(maz_taz_def_df.columns)}")
            
            # Aggregate to MAZ level
            control_maz_df = aggregate_to_control_geo(
                control_table_df, control_name, 'MAZ', geography, 
                maz_taz_def_df, {}, None, None, None, 0
            )
            
            if control_maz_df.index.name != 'MAZ':
                if 'MAZ' in control_maz_df.columns:
                    control_maz_df = control_maz_df.set_index('MAZ')[[control_name]]
                else:
                    raise ValueError(f"Failed to aggregate control_table_df to MAZ level")
            else:
                control_maz_df = control_maz_df[[control_name]]
        else:
            # Already has MAZ column
            if control_table_df.index.name != 'MAZ':
                control_maz_df = control_table_df.groupby('MAZ')[control_name].sum().to_frame()
            else:
                control_maz_df = control_table_df[[control_name]]
        
        print(f"[DEBUG] control_maz_df columns: {list(control_maz_df.columns)}")
        print(f"[DEBUG] control_maz_df head:\n{control_maz_df.head()}")
        
        # Get denominator values (ensure it's indexed by MAZ)
        if scale_denom_df.index.name != 'MAZ':
            if 'MAZ' in scale_denom_df.columns:
                denom_maz = scale_denom_df.set_index('MAZ')[[scale_denominator]]
            else:
                raise ValueError(f"Cannot determine MAZ index for scale_denominator {scale_denominator}")
        else:
            denom_maz = scale_denom_df[[scale_denominator]]
        
        # Merge and calculate fraction
        merged = pd.merge(control_maz_df, denom_maz, left_index=True, right_index=True, how='left')
        merged[scale_denominator] = merged[scale_denominator].fillna(0)
        merged['temp_fraction'] = merged[control_name] / merged[scale_denominator].replace({0: numpy.nan})
        merged['temp_fraction'] = merged['temp_fraction'].replace({numpy.inf: 0, numpy.nan: 0})
        
        if scale_numerator and scale_num_df is not None:
            # Get numerator values (ensure it's indexed by MAZ)
            if scale_num_df.index.name != 'MAZ':
                if 'MAZ' in scale_num_df.columns:
                    num_maz = scale_num_df.set_index('MAZ')[[scale_numerator]]
                else:
                    raise ValueError(f"Cannot determine MAZ index for scale_numerator {scale_numerator}")
            else:
                num_maz = scale_num_df[[scale_numerator]]
            
            merged = pd.merge(merged, num_maz, left_index=True, right_index=True, how='left')
            merged[scale_numerator] = merged[scale_numerator].fillna(0)
            merged[control_name] = merged['temp_fraction'] * merged[scale_numerator]
        
        result = merged[[control_name]]
        print(f"[DEBUG] temp_table_scaling result columns: {list(result.columns)}")
        print(f"[DEBUG] temp_table_scaling result head:\n{result.head()}")
        
        # Skip writing intermediate scaled CSV
        return result
    
    # Original logic for non-MAZ level scaling
    geo = geography.lower().replace('_', ' ')
    supported = ["block", "block group", "tract", "county"]
    if geo in supported:
        control_table_df = prepare_geoid_for_merge(control_table_df, geo)
        denom_df = prepare_geoid_for_merge(temp_controls[scale_denominator], geo)
        
        # Check GEOID columns match
        control_geoid_col = get_geoid_col(control_table_df, geo)
        denom_geoid_col = get_geoid_col(denom_df, geo)
        print(f"[DEBUG] control_geoid_col: {control_geoid_col}, denom_geoid_col: {denom_geoid_col}")
        
        if control_geoid_col != denom_geoid_col:
            # Rename to match
            if denom_geoid_col and control_geoid_col:
                denom_df = denom_df.rename(columns={denom_geoid_col: control_geoid_col})
        
        merged = pd.merge(control_table_df, denom_df[[control_geoid_col, scale_denominator]], on=control_geoid_col, how='left', suffixes=('', '_denom'))
        merged[scale_denominator] = merged[scale_denominator].fillna(0)
        merged['temp_fraction'] = merged[control_name] / merged[scale_denominator].replace({0: numpy.nan})
        merged['temp_fraction'] = merged['temp_fraction'].replace({numpy.inf: 0, numpy.nan: 0})
        
        if scale_numerator:
            num_df = prepare_geoid_for_merge(temp_controls[scale_numerator], geo)
            num_geoid_col = get_geoid_col(num_df, geo)
            if num_geoid_col != control_geoid_col:
                num_df = num_df.rename(columns={num_geoid_col: control_geoid_col})
            merged = pd.merge(num_df[[control_geoid_col, scale_numerator]], merged, on=control_geoid_col, how='left', suffixes=('_num', ''))
            merged[control_name] = merged['temp_fraction'] * merged[scale_numerator]
            merged = merged[[control_geoid_col, control_name]]
        else:
            merged = merged[[control_geoid_col, control_name]]
            
        print(f"[DEBUG] temp_table_scaling result columns: {list(merged.columns)}")
        print(f"[DEBUG] temp_table_scaling result head:\n{merged.head()}")
        
        # Skip writing intermediate scaled CSV
        return merged
    else:
        # For synthetic geographies, just return the input DataFrame (no scaling)
        return control_table_df

def aggregate_to_control_geo(control_table_df, control_name, control_geography, census_geography, maz_taz_def_df, temp_controls, scale_numerator, scale_denominator, subtract_table, variable_total):
    from tm2_control_utils.config import GEOGRAPHY_ID_COLUMNS
    import logging
    
    # Diagnostics
    print(f"[DEBUG] aggregate_to_control_geo: control_geography={control_geography}, census_geography={census_geography}")
    print(f"[DEBUG] control_table_df columns: {list(control_table_df.columns)}")
    print(f"[DEBUG] maz_taz_def_df columns: {list(maz_taz_def_df.columns)}")
    print(f"[DEBUG] control_table_df head:\n{control_table_df.head()}")
    print(f"[DEBUG] maz_taz_def_df head:\n{maz_taz_def_df.head()}")
    
    # Determine if we need to aggregate from census to synthetic geography
    census_geo_lower = census_geography.lower().replace('_', ' ')
    control_geo_lower = control_geography.lower().replace('_', ' ')
    
    # Get column names from config
    census_geoid_col = GEOGRAPHY_ID_COLUMNS.get(census_geo_lower, {}).get('census', f'GEOID_{census_geo_lower}')
    census_mapping_col = GEOGRAPHY_ID_COLUMNS.get(census_geo_lower, {}).get('mapping', f'{census_geo_lower}2020ge')
    synth_mapping_col = GEOGRAPHY_ID_COLUMNS.get(control_geo_lower, {}).get('mapping', control_geography)
    
    print(f"[DEBUG] Using census_geoid_col: {census_geoid_col}")
    print(f"[DEBUG] Using census_mapping_col: {census_mapping_col}")  
    print(f"[DEBUG] Using synth_mapping_col: {synth_mapping_col}")
    
    # Ensure census GEOID is present
    if census_geoid_col not in control_table_df.columns:
        control_table_df = prepare_geoid_for_merge(control_table_df, census_geo_lower)
    
    # Handle scaling and subtraction on census geography first
    if scale_numerator and scale_denominator:
        num_df = prepare_geoid_for_merge(temp_controls[scale_numerator], census_geo_lower)
        denom_df = prepare_geoid_for_merge(temp_controls[scale_denominator], census_geo_lower)
        merged = pd.merge(control_table_df, num_df[[census_geoid_col, scale_numerator]], on=census_geoid_col, how='left')
        merged = pd.merge(merged, denom_df[[census_geoid_col, scale_denominator]], on=census_geoid_col, how='left')
        merged[control_name] = merged[control_name] * merged[scale_numerator] / merged[scale_denominator].replace({0: numpy.nan})
        merged[control_name] = merged[control_name].replace({numpy.inf: 0, numpy.nan: 0})
        merged.fillna(0, inplace=True)
        variable_total = variable_total * num_df[scale_numerator].sum() / denom_df[scale_denominator].sum()
        control_table_df = merged
        
    if subtract_table:
        sub_df = prepare_geoid_for_merge(temp_controls[subtract_table], census_geo_lower)
        merged = pd.merge(control_table_df, sub_df[[census_geoid_col, subtract_table]], on=census_geoid_col, how='left')
        merged[control_name] = merged[control_name] - merged[subtract_table]
        variable_total = variable_total - sub_df[subtract_table].sum()
        control_table_df = merged
    
    # Now map from census geography to synthetic geography if needed
    if control_geography in ["MAZ", "TAZ", "COUNTY", "REGION"]:
        print(f"[DEBUG] Mapping from {census_geography} to {control_geography}")
        
        # Check if mapping columns exist in maz_taz_def_df
        if census_mapping_col not in maz_taz_def_df.columns:
            raise KeyError(f"Census mapping column '{census_mapping_col}' not found in maz_taz_def_df. Available: {list(maz_taz_def_df.columns)}")
        if synth_mapping_col not in maz_taz_def_df.columns:
            raise KeyError(f"Synthetic mapping column '{synth_mapping_col}' not found in maz_taz_def_df. Available: {list(maz_taz_def_df.columns)}")
        
        # Get unique mapping and ensure consistent data types
        geo_mapping_df = maz_taz_def_df[[synth_mapping_col, census_mapping_col]].drop_duplicates()
        
        # Convert both join keys to string to ensure compatibility
        control_table_df[census_geoid_col] = control_table_df[census_geoid_col].astype(str).str.strip()
        geo_mapping_df[census_mapping_col] = geo_mapping_df[census_mapping_col].astype(str).str.strip()
        
        # Ensure leading zeros are consistent based on geography type
        if census_geography.lower() == 'block':
            control_table_df[census_geoid_col] = control_table_df[census_geoid_col].str.zfill(15)
            geo_mapping_df[census_mapping_col] = geo_mapping_df[census_mapping_col].str.zfill(15)
        elif census_geography.lower() == 'block group':
            control_table_df[census_geoid_col] = control_table_df[census_geoid_col].str.zfill(12)
            geo_mapping_df[census_mapping_col] = geo_mapping_df[census_mapping_col].str.zfill(12)
        elif census_geography.lower() == 'tract':
            control_table_df[census_geoid_col] = control_table_df[census_geoid_col].str.zfill(11)
            geo_mapping_df[census_mapping_col] = geo_mapping_df[census_mapping_col].str.zfill(11)
        elif census_geography.lower() == 'county':
            control_table_df[census_geoid_col] = control_table_df[census_geoid_col].str.zfill(5)
            geo_mapping_df[census_mapping_col] = geo_mapping_df[census_mapping_col].str.zfill(5)
        
        print(f"[DEBUG] geo_mapping_df shape: {geo_mapping_df.shape}")
        print(f"[DEBUG] geo_mapping_df head:\n{geo_mapping_df.head()}")
        print(f"[DEBUG] control_table_df dtypes: {control_table_df[census_geoid_col].dtype}")
        print(f"[DEBUG] geo_mapping_df dtypes: {geo_mapping_df[census_mapping_col].dtype}")
        print(f"[DEBUG] control_table_df join key sample: {control_table_df[census_geoid_col].head().tolist()}")
        print(f"[DEBUG] geo_mapping_df join key sample: {geo_mapping_df[census_mapping_col].head().tolist()}")
        
        # Merge control table with mapping on census GEOID
        merged_df = pd.merge(
            control_table_df, 
            geo_mapping_df, 
            left_on=census_geoid_col, 
            right_on=census_mapping_col, 
            how='left'
        )
        
        print(f"[DEBUG] After merge, columns: {list(merged_df.columns)}")
        print(f"[DEBUG] merged_df shape: {merged_df.shape}")
        
        # Check if synthetic geography column is present
        if synth_mapping_col not in merged_df.columns:
            raise KeyError(f"'{synth_mapping_col}' not in merged DataFrame after merge. Available: {list(merged_df.columns)}")
        
        # Aggregate to synthetic geography
        final_df = merged_df.groupby(synth_mapping_col)[control_name].sum().reset_index()
        final_df.set_index(synth_mapping_col, inplace=True)
        final_df.index.name = control_geography
        
    else:
        # For census geographies, group by the census GEOID
        final_df = control_table_df.groupby(census_geoid_col)[control_name].sum().reset_index()
        final_df.set_index(census_geoid_col, inplace=True)
        final_df.index.name = control_geography
    
    print(f"[DEBUG] final_df shape: {final_df.shape}")
    print(f"[DEBUG] final_df head:\n{final_df.head()}")
    
    # Check totals
    if not scale_numerator:
        diff = abs(final_df[control_name].sum() - variable_total)
        if diff >= 0.5:
            logging.warning(f"Total difference of {diff} between input and output for {control_name}")
    
    return final_df

def proportional_scaling(control_table_df, control_name, control_geography, census_geography, maz_taz_def_df, temp_controls, scale_numerator, scale_denominator):
    geo = control_geography.lower().replace('_', ' ')
    control_table_df = ensure_geoid_column(control_table_df, geo)
    denom_df = ensure_geoid_column(temp_controls[scale_denominator], geo)
    geoid_col = get_geoid_col(control_table_df, geo)
    control_table_df = control_table_df.rename(columns={geoid_col: 'GEOID'})
    denom_df = denom_df.rename(columns={get_geoid_col(denom_df, geo): 'GEOID'})
    control_table_df['GEOID'] = control_table_df['GEOID'].astype(str).str.strip()
    denom_df['GEOID'] = denom_df['GEOID'].astype(str).str.strip()
    proportion_df = pd.merge(control_table_df, denom_df[['GEOID', scale_denominator]], on='GEOID', how='left')
    proportion_var = f"{control_name} proportion"
    proportion_df[proportion_var] = proportion_df[control_name] / proportion_df[scale_denominator].replace({0: numpy.nan})
    proportion_df[proportion_var] = proportion_df[proportion_var].replace({numpy.inf: 0, numpy.nan: 0})
    block_prop_df = pd.merge(maz_taz_def_df, proportion_df, how='left', left_on=control_geography, right_on='GEOID')
    num_df = ensure_geoid_column(temp_controls[scale_numerator], geo)
    num_df = num_df.rename(columns={get_geoid_col(num_df, geo): 'GEOID'})
    num_df['GEOID'] = num_df['GEOID'].astype(str).str.strip()
    block_prop_df = pd.merge(block_prop_df, num_df[['GEOID', scale_numerator]], on='GEOID', how='left')
    block_prop_df[control_name] = block_prop_df[proportion_var] * block_prop_df[scale_numerator]
    final_df = block_prop_df[[control_geography, control_name]].groupby(control_geography).aggregate(numpy.sum)
    return final_df

def match_control_to_geography(
    control_name, control_table_df, control_geography, census_geography,
    maz_taz_def_df, temp_controls,
    scale_numerator=None, scale_denominator=None, subtract_table=None
):
    print(f"[DEBUG] match_control_to_geography called with control_name={control_name}, control_geography={control_geography}, census_geography={census_geography}")
    print(f"[DEBUG] control_table_df columns: {list(control_table_df.columns)}")
    print(f"[DEBUG] maz_taz_def_df columns: {list(maz_taz_def_df.columns)}")
    print(temp_controls.keys())
    print(temp_controls.values())
    print(control_table_df.head())



    # Only allow supported geographies
    if control_geography not in ["MAZ","TAZ","COUNTY","REGION"]:
        raise ValueError(f"match_control_to_geography passed unsupported control geography {control_geography}")
    if census_geography not in ["block","block group","tract","county subdivision","county"]:
        raise ValueError(f"match_control_to_geography passed unsupported census geography {census_geography}")
    variable_total = control_table_df[control_name].sum()
    GEO_HIERARCHY = { 'MAZ'   :['block','MAZ','block group','tract','county subdivision','county'],
                      'TAZ'   :['block',      'TAZ',        'tract','county subdivision','county'],
                      'COUNTY':['block',      'block group','tract','county subdivision','county','COUNTY'],
                      'REGION':['block',      'block group','tract','county subdivision','county','REGION']}
    control_geo_index = GEO_HIERARCHY[control_geography].index(control_geography)
    try:
        census_geo_index = GEO_HIERARCHY[control_geography].index(census_geography)
    except:
        census_geo_index = -1
    # Use flexible scaling/aggregation
    if scale_numerator or scale_denominator:
        return temp_table_scaling(control_table_df, control_name, scale_numerator, scale_denominator, temp_controls, maz_taz_def_df, geography=census_geography)
    else:
        return aggregate_to_control_geo(control_table_df, control_name, control_geography, census_geography, maz_taz_def_df, temp_controls, scale_numerator, scale_denominator, subtract_table, variable_total)
def stochastic_round(my_series):
    """
    Performs stochastic rounding of a series and returns it.
    https://en.wikipedia.org/wiki/Rounding#Stochastic_rounding
    """
    numpy.random.seed(32)
    return numpy.floor(my_series + numpy.random.rand(len(my_series)))


def integerize_control(out_df, crosswalk_df, control_name):
    """
    Integerize this control
    """
    # keep index as a normal column
    out_df.reset_index(drop=False, inplace=True)
    # keep track of columns to go back to
    out_df_cols = list(out_df.columns.values)

    # stochastic rounding
    out_df["control_stoch_round"] = stochastic_round(out_df[control_name])

    # see how they look at the TAZ and county level
    out_df = pd.merge(left=out_df, right=crosswalk_df, how="left")

    # this is being exacting... maybe not necessary

    # make them match taz totals (especially those that are already even)
    # really doing this in one iteration but check it
    for iteration in [1,2]:

        out_df_by_taz = out_df[["TAZ",control_name,"control_stoch_round"]].groupby("TAZ").aggregate(numpy.sum).reset_index(drop=False)
        out_df_by_taz["control_taz"]       = out_df_by_taz[control_name]  # copy and name explicitly
        out_df_by_taz["control_round_taz"] = numpy.around(out_df_by_taz[control_name])

        out_df_by_taz["control_stoch_round_diff"]     = out_df_by_taz["control_round_taz"] - out_df_by_taz["control_stoch_round"]
        out_df_by_taz["control_stoch_round_diff_abs"] = numpy.absolute(out_df_by_taz["control_stoch_round_diff"])

        # if the total is off by less than one, don't touch
        # otherwise, choose a MAZ to tweak based on control already in the MAZ
        out_df_by_taz["control_adjust"] = numpy.trunc(out_df_by_taz["control_stoch_round_diff"])

        tazdict_to_adjust = out_df_by_taz.loc[ out_df_by_taz["control_adjust"] != 0, ["TAZ","control_taz","control_adjust"]].set_index("TAZ").to_dict(orient="index")

        # nothing to do
        if len(tazdict_to_adjust)==0: break

        # add or remove a household if needed from a MAZ
        out_df = pd.merge(left=out_df, right=out_df_by_taz[["TAZ","control_adjust","control_taz"]], how="left")
        out_df_by_taz_grouped = out_df[["MAZ","TAZ",control_name,"control_stoch_round","control_adjust","control_taz"]].groupby("TAZ")
        for taz in tazdict_to_adjust.keys():
            adjustment = tazdict_to_adjust[taz]["control_adjust"]  # e.g. -2
            sample_n   = int(abs(adjustment)) # e.g. 2
            change_by  = adjustment/sample_n  # so this will be +1 or -1

            # choose a maz to tweak weighted by number of households in the MAZ, so we don't tweak 0-hh MAZs
            try:
                sample = out_df_by_taz_grouped.get_group(taz).sample(n=sample_n, weights="control_stoch_round")

                # actually make the change in the out_df.  iterate rather than join since there are so few
                for maz in sample["MAZ"].tolist():
                    out_df.loc[ out_df["MAZ"] == maz, "control_stoch_round"] += change_by

            except ValueError as e:
                # this could fail if the weights are all zero
                pass

    out_df_by_county = out_df[["COUNTY",control_name,"control_stoch_round"]].groupby("COUNTY").aggregate(numpy.sum).reset_index(drop=False)

    # use the new version
    out_df[control_name] = out_df["control_stoch_round"].astype(int)
    # go back to original cols
    out_df = out_df[out_df_cols]
    # and index
    out_df.set_index("MAZ", inplace=True)


    return out_df

# Helper to prepare a DataFrame for GEOID-based merge

def prepare_geoid_for_merge(df, geography):
    """
    For census geographies, ensure the correct GEOID column exists, rename to canonical config-driven name, and cast/strip.
    For non-census geographies or temp controls, returns df unchanged.
    """
    from tm2_control_utils.config import GEOGRAPHY_ID_COLUMNS
    geo = geography.lower().replace('_', ' ')
    supported = ["block", "block group", "tract", "county"]
    colname = GEOGRAPHY_ID_COLUMNS.get(geo, {}).get('census', f'GEOID_{geo}')
    
    # For temp controls that are already aggregated to MAZ level, skip GEOID preparation
    if df.index.name == 'MAZ' or 'MAZ' in df.columns:
        print(f"[DEBUG] prepare_geoid_for_merge: DataFrame appears to be MAZ-level temp control, skipping GEOID preparation for '{geo}'")
        return df
        
    if geo in supported:
        df = ensure_geoid_column(df, geo)
        if colname in df.columns:
            df[colname] = df[colname].astype(str).str.strip()
    return df

def get_geography_id_col(geography, table_type='mapping'):
    """
    Get the canonical column name for a geography and table type (census, crosswalk, mapping).
    """
    geo = geography.lower().replace('_', ' ')
    if geo in GEOGRAPHY_ID_COLUMNS and table_type in GEOGRAPHY_ID_COLUMNS[geo]:
        return GEOGRAPHY_ID_COLUMNS[geo][table_type]
    raise ValueError(f"No canonical column for geography '{geography}' and table_type '{table_type}'")

def write_distribution_weights_debug(control_name, control_table_df, scale_numerator, scale_denominator, 
                                      temp_controls, maz_taz_def_df, geography):
    """Write debugging file showing distribution weights for household size controls."""
    import pandas as pd
    import numpy as np
    import os
    
    logger = logging.getLogger()
    
    # Only create debug files for household size controls
    if not control_name.startswith('hh_size_'):
        return
    
    try:
        logger.info(f"Writing distribution weights debug file for {control_name}")
        
        # Get the temp control tables
        scale_num_df = temp_controls.get(scale_numerator) if scale_numerator else None
        scale_denom_df = temp_controls.get(scale_denominator)
        
        if scale_num_df is None or scale_denom_df is None:
            logger.warning(f"Missing temp controls for {control_name}: num={scale_numerator}, denom={scale_denominator}")
            return
        
        # Create debug DataFrame showing the distribution logic
        debug_rows = []
        
        # First, get the block group to block relationships from maz_taz_def_df
        if geography == 'block group':
            # Group blocks by block group
            block_group_mapping = maz_taz_def_df.groupby('GEOID_block group')['GEOID_block'].apply(list).to_dict()
            
            for bg_geoid, block_list in block_group_mapping.items():
                # Get block group total households from denominator
                bg_total = scale_denom_df[scale_denom_df.index.str.contains(bg_geoid[-12:], na=False)]
                if len(bg_total) > 0:
                    bg_households = bg_total[scale_denominator].iloc[0]
                else:
                    bg_households = 0
                    
                # Get individual block households from numerator 
                block_households = {}
                total_block_households = 0
                
                for block_geoid in block_list:
                    block_data = scale_num_df[scale_num_df.index.str.contains(str(block_geoid), na=False)]
                    if len(block_data) > 0:
                        households = block_data[scale_numerator].iloc[0]
                        block_households[block_geoid] = households
                        total_block_households += households
                    else:
                        block_households[block_geoid] = 0
                
                # Calculate distribution weights and show how ACS data would be distributed
                for block_geoid, block_hh in block_households.items():
                    if total_block_households > 0:
                        weight = block_hh / total_block_households
                    else:
                        weight = 0
                        
                    # Get ACS household size value for this block group
                    bg_hh_size = 0
                    control_data = control_table_df[control_table_df.index.str.contains(bg_geoid[-12:], na=False)]
                    if len(control_data) > 0:
                        bg_hh_size = control_data[control_name].iloc[0]
                    
                    distributed_value = weight * bg_hh_size
                    
                    debug_rows.append({
                        'control_name': control_name,
                        'block_group_geoid': bg_geoid,
                        'block_geoid': block_geoid,
                        'bg_total_households': bg_households,
                        'block_households': block_hh,
                        'total_blocks_households': total_block_households,
                        'distribution_weight': weight,
                        'bg_acs_value': bg_hh_size,
                        'distributed_value': distributed_value
                    })
        
        if debug_rows:
            debug_df = pd.DataFrame(debug_rows)
            
            # Write to debug file
            output_dir = "output_2023"
            os.makedirs(output_dir, exist_ok=True)
            debug_file = os.path.join(output_dir, f"distribution_weights_{control_name}.csv")
            debug_df.to_csv(debug_file, index=False, float_format="%.6f")
            
            logger.info(f"Wrote distribution weights debug file: {debug_file}")
            
            # Also log some summary statistics
            logger.info(f"Distribution weights summary for {control_name}:")
            logger.info(f"  - Total block groups: {debug_df['block_group_geoid'].nunique()}")
            logger.info(f"  - Total blocks: {len(debug_df)}")
            logger.info(f"  - Avg distribution weight: {debug_df['distribution_weight'].mean():.4f}")
            logger.info(f"  - Blocks with weight=0: {len(debug_df[debug_df['distribution_weight']==0])}")
            
    except Exception as e:
        logger.warning(f"Failed to write distribution weights debug for {control_name}: {e}")