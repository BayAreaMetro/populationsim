import numpy
import pandas as pd
import collections
import logging
from tm2_control_utils.geog_utils import add_aggregate_geography_colums
from tm2_control_utils.config import GEOGRAPHY_ID_COLUMNS, CENSUS_DEFINITIONS


# Utility to get GEOID column for a geography

def get_geoid_col(df, geo):
    """
    Get the appropriate GEOID column name for a given geography.
    """
    geo = geo.lower().replace('_', ' ')
    if f'GEOID_{geo}' in df.columns:
        return f'GEOID_{geo}'
    
    # Check alternative column names based on geography
    geo_mapping = {
        'block': ['blk2020ge', 'GEOID_block', 'geoid_block'],
        'block group': ['bg2020ge', 'GEOID_block group', 'geoid_block_group'],
        'tract': ['tr2020ge', 'GEOID_tract', 'geoid_tract'],
        'county': ['cty2020ge', 'GEOID_county', 'geoid_county']
    }
    
    if geo in geo_mapping:
        for col in geo_mapping[geo]:
            if col in df.columns:
                return col
    
    print(f"[WARNING] No suitable GEOID column found for geography '{geo}' in columns: {list(df.columns)}")
    return None


def prepare_geoid_for_merge(df, geography):
    """
    Prepare a DataFrame for merging by ensuring it has the correct GEOID column for the geography.
    """
    target_col = f'GEOID_{geography}'
    
    if target_col in df.columns:
        return df
    
    # Try to find an existing GEOID column to use or rename
    geoid_col = get_geoid_col(df, geography)
    if geoid_col and geoid_col != target_col:
        df = df.copy()
        df[target_col] = df[geoid_col]
    
    return df


def disaggregate_tract_to_block_group(control_table_df, control_name, hh_weights_df, maz_taz_def_df):
    """
    Disaggregate tract-level data to block group level using household distribution as weights.
    
    Process:
    1. Sum household counts by tract to get tract totals
    2. Calculate weights: hh_blockgroup / hh_tract
    3. Apply weights: tract_value * weight -> blockgroup_value
    
    Args:
        control_table_df: DataFrame with tract-level control data
        control_name: Name of the control column
        hh_weights_df: DataFrame with block group household counts for weighting
        maz_taz_def_df: Geography crosswalk DataFrame
    
    Returns:
        DataFrame with block group level data
    """
    import pandas as pd
    
    import logging
    logger = logging.getLogger()
    logger.info(f"[TRACT2BG] Starting tract-to-block group disaggregation for '{control_name}'")
    print(f"[DEBUG][TRACT2BG] ==> DISAGGREGATION START: {control_name}")
    print(f"[DEBUG][TRACT2BG] Input control_table_df shape: {control_table_df.shape}")
    print(f"[DEBUG][TRACT2BG] Input hh_weights_df shape: {hh_weights_df.shape}")
    print(f"[DEBUG][TRACT2BG] Input control total: {control_table_df[control_name].sum():,.0f}")
    
    control_table_df = prepare_geoid_for_merge(control_table_df, 'tract')
    hh_weights_df = prepare_geoid_for_merge(hh_weights_df, 'block group')

    print(f"[DEBUG][TRACT2BG] Columns in control_table_df: {list(control_table_df.columns)}")
    print(f"[DEBUG][TRACT2BG] Columns in hh_weights_df: {list(hh_weights_df.columns)}")


    # Try to find or construct a block group GEOID column
    geoid_col = None
    print(f"[DEBUG][TRACT2BG] Available columns in hh_weights_df: {list(hh_weights_df.columns)}")
    for col in ['GEOID_block group', 'bg2020ge', 'GEOID_bg']:
        print(f"[DEBUG][TRACT2BG] Checking for column: '{col}' - exists: {col in hh_weights_df.columns}")
        if col in hh_weights_df.columns:
            geoid_col = col
            break

    # If no block group GEOID found, construct it from components
    if geoid_col is None:
        print(f"[DEBUG][TRACT2BG] No existing block group GEOID found, constructing from components")
        if all(col in hh_weights_df.columns for col in ['state', 'county', 'tract', 'block group']):
            hh_weights_df['GEOID_block_group'] = (
                hh_weights_df['state'].astype(str).str.zfill(2) +
                hh_weights_df['county'].astype(str).str.zfill(3) +
                hh_weights_df['tract'].astype(str).str.zfill(6) +
                hh_weights_df['block group'].astype(str).str.zfill(1)
            )
            geoid_col = 'GEOID_block_group'
            print(f"[DEBUG][TRACT2BG] Constructed block group GEOID, sample: {hh_weights_df[geoid_col].head().tolist()}")
        else:
            raise ValueError("Cannot construct block group GEOID - missing required columns")

    print(f"[DEBUG][TRACT2BG] Using block group GEOID column: {geoid_col}")
    
    hh_weights_df['GEOID_tract'] = hh_weights_df[geoid_col].str[:11]
    print(f"[DEBUG][TRACT2BG] Created GEOID_tract in hh_weights_df, sample: {hh_weights_df[['GEOID_tract', geoid_col]].head().to_dict()}")

    # CRITICAL DEBUG: Check the household weights DataFrame structure
    # Find the actual household weights column
    tract_hh_col = None
    for col in hh_weights_df.columns:
        if 'temp_hh_bg_for_tract_weights' in col:
            tract_hh_col = col
            break
    
    if tract_hh_col is None:
        raise ValueError("Cannot find household weights column in hh_weights_df")
        
    print(f"[DEBUG][TRACT2BG] Using household count column: {tract_hh_col}")
    print(f"[DEBUG][TRACT2BG] Household weights sum: {hh_weights_df[tract_hh_col].sum():,.0f}")
    print(f"[DEBUG][TRACT2BG] Household weights head:\n{hh_weights_df.head()}")
    
    # Sum households by tract
    tract_totals = hh_weights_df.groupby('GEOID_tract')[tract_hh_col].sum().reset_index()
    tract_totals.columns = ['GEOID_tract', 'tract_hh_total']
    print(f"[DEBUG][TRACT2BG] Tract totals shape: {tract_totals.shape}")
    print(f"[DEBUG][TRACT2BG] Tract totals sum: {tract_totals['tract_hh_total'].sum():,.0f}")
    print(f"[DEBUG][TRACT2BG] Tract totals head: {tract_totals.head()}")

    # CRITICAL FIX: Only include block groups that are within tracts present after interpolation
    # Get the set of tracts that survived the geographic interpolation
    input_tract_geoids = set(control_table_df['GEOID_tract'].unique())
    print(f"[DEBUG][TRACT2BG] Input tract GEOIDs: {len(input_tract_geoids)} unique tracts")
    
    # Debug: Check what tracts we have in hh_weights_df
    weights_tract_geoids = set(hh_weights_df['GEOID_tract'].unique())
    print(f"[DEBUG][TRACT2BG] Block group file has: {len(weights_tract_geoids)} unique tracts")
    print(f"[DEBUG][TRACT2BG] Tract overlap: {len(input_tract_geoids & weights_tract_geoids)} tracts in both")
    print(f"[DEBUG][TRACT2BG] Extra tracts in BG file: {len(weights_tract_geoids - input_tract_geoids)}")
    
    # Filter hh_weights_df to only include block groups within these tracts
    original_bg_count = len(hh_weights_df)
    hh_weights_df = hh_weights_df[hh_weights_df['GEOID_tract'].isin(input_tract_geoids)]
    filtered_bg_count = len(hh_weights_df)
    print(f"[DEBUG][TRACT2BG] Filtered block groups: {original_bg_count} -> {filtered_bg_count} (kept {filtered_bg_count/original_bg_count:.1%})")
    
    # Calculate weights: hh_blockgroup / hh_tract
    hh_with_tract_totals = pd.merge(hh_weights_df, tract_totals, on='GEOID_tract', how='left')
    hh_with_tract_totals['weight'] = hh_with_tract_totals[tract_hh_col] / hh_with_tract_totals['tract_hh_total']
    hh_with_tract_totals['weight'] = hh_with_tract_totals['weight'].fillna(0)
    print(f"[DEBUG][TRACT2BG] Weights calculated - shape: {hh_with_tract_totals.shape}")
    print(f"[DEBUG][TRACT2BG] Weight sum by tract check: {hh_with_tract_totals.groupby('GEOID_tract')['weight'].sum().head()}")
    print(f"[DEBUG][TRACT2BG] Weight statistics: min={hh_with_tract_totals['weight'].min():.4f}, max={hh_with_tract_totals['weight'].max():.4f}")

    # CRITICAL FIX: Calculate the true original sum BEFORE merging (before expansion)
    true_original_sum = control_table_df[control_name].sum()
    print(f"[DEBUG][TRACT2BG] True original sum (before merge): {true_original_sum:,.0f}")

    # Merge tract data with weights
    print(f"[DEBUG][TRACT2BG] Merging tract control data with block group weights...")
    merged = pd.merge(control_table_df, hh_with_tract_totals[['GEOID_tract', geoid_col, 'weight']], 
                      on='GEOID_tract', how='left')
    print(f"[DEBUG][TRACT2BG] After merge shape: {merged.shape}")
    print(f"[DEBUG][TRACT2BG] Original tract records: {len(control_table_df)}")
    print(f"[DEBUG][TRACT2BG] After merge records: {len(merged)}")
    
    # CRITICAL: Check if we're getting multiple records per tract
    orig_tract_count = len(control_table_df)
    final_tract_count = len(merged)
    expansion_ratio = final_tract_count / orig_tract_count
    print(f"[DEBUG][TRACT2BG] ** EXPANSION RATIO: {expansion_ratio:.2f} **")
    if expansion_ratio > 1.1:  # More than 10% increase
        print(f"[DEBUG][TRACT2BG] *** WARNING: Significant expansion detected! Original={orig_tract_count}, Final={final_tract_count}")
        
        # Check which tracts have multiple records
        tract_counts = merged['GEOID_tract'].value_counts()
        multi_tracts = tract_counts[tract_counts > 1]
        print(f"[DEBUG][TRACT2BG] Tracts with multiple records: {len(multi_tracts)}")
        if len(multi_tracts) > 0:
            sample_tract = multi_tracts.index[0]
            sample_data = merged[merged['GEOID_tract'] == sample_tract]
            print(f"[DEBUG][TRACT2BG] Sample multi-record tract {sample_tract}:")
            print(f"[DEBUG][TRACT2BG] {sample_data[['GEOID_tract', geoid_col, control_name, 'weight']].to_dict()}")

    # Apply disaggregation: tract_value * weight -> blockgroup_value
    # CRITICAL FIX: Calculate the true original sum BEFORE the merge to avoid inflated totals
    true_original_sum = control_table_df[control_name].sum()
    inflated_sum_before_weighting = merged[control_name].sum()
    print(f"[DEBUG][TRACT2BG] True original sum (before merge): {true_original_sum:,.0f}")
    print(f"[DEBUG][TRACT2BG] Inflated sum (after merge, before weighting): {inflated_sum_before_weighting:,.0f}")
    merged[control_name] = merged[control_name] * merged['weight']
    merged[control_name] = merged[control_name].fillna(0)
    final_sum = merged[control_name].sum()
    ratio = final_sum / true_original_sum if true_original_sum > 0 else 0
    
    print(f"[DEBUG][TRACT2BG] *** DISAGGREGATION RESULT ***")
    print(f"[DEBUG][TRACT2BG] True original sum: {true_original_sum:,.0f}")
    print(f"[DEBUG][TRACT2BG] Final sum after disaggregation: {final_sum:,.0f}")
    print(f"[DEBUG][TRACT2BG] ** RATIO (final/original): {ratio:.4f} **")
    
    if abs(ratio - 1.0) > 0.01:  # More than 1% change
        print(f"[DEBUG][TRACT2BG] *** WARNING: Significant sum change! Expected ~1.0, got {ratio:.4f}")

    # Step 2: Aggregate from block group level to TAZ level
    print(f"[DEBUG][TRACT2BG] ==> Starting block group to TAZ aggregation")
    
    # Get block group to TAZ mapping from maz_taz_def_df
    if 'GEOID_block group' not in maz_taz_def_df.columns or 'TAZ' not in maz_taz_def_df.columns:
        logger.error("Missing block group to TAZ mapping columns in maz_taz_def_df")
        print(f"[DEBUG][TRACT2BG] maz_taz_def_df columns: {list(maz_taz_def_df.columns)}")
        raise ValueError("Cannot aggregate to TAZ level - missing geographic mapping")
    
    print(f"[DEBUG][TRACT2BG] Available columns in maz_taz_def_df: {list(maz_taz_def_df.columns)}")
    
    # Check if we have weighting columns for proper apportionment
    potential_weight_cols = [col for col in maz_taz_def_df.columns if any(w in col.lower() for w in ['weight', 'area', 'pop', 'hh', 'proportion', 'fraction'])]
    print(f"[DEBUG][TRACT2BG] Potential weight columns: {potential_weight_cols}")
    
    # Get the mapping and ensure consistent data types - USE MAZ-BASED APPORTIONMENT
    # Since block groups can span multiple TAZs, we need to apportion based on MAZ counts
    bg_taz_mapping = maz_taz_def_df[['GEOID_block group', 'TAZ', 'MAZ']].copy()
    bg_taz_mapping['GEOID_block group'] = bg_taz_mapping['GEOID_block group'].astype(str)
    
    print(f"[DEBUG][TRACT2BG] Total MAZ-TAZ-BG records: {len(bg_taz_mapping)}")
    
    # Count MAZs per block group per TAZ for apportionment weights
    maz_counts = bg_taz_mapping.groupby(['GEOID_block group', 'TAZ']).size().reset_index(name='maz_count')
    total_maz_per_bg = maz_counts.groupby('GEOID_block group')['maz_count'].transform('sum')
    maz_counts['weight'] = maz_counts['maz_count'] / total_maz_per_bg
    
    print(f"[DEBUG][TRACT2BG] Block group-TAZ relationships after MAZ counting: {len(maz_counts)}")
    
    # Check that weights sum to 1.0 for each block group
    weight_sums = maz_counts.groupby('GEOID_block group')['weight'].sum()
    weight_check = weight_sums.describe()
    print(f"[DEBUG][TRACT2BG] Weight sum check - min:{weight_check['min']:.4f}, max:{weight_check['max']:.4f}, mean:{weight_check['mean']:.4f}")
    
    if weight_check['min'] < 0.99 or weight_check['max'] > 1.01:
        print(f"[DEBUG][TRACT2BG] *** WARNING: Weight normalization issue detected ***")
    
    bg_to_taz = maz_counts[['GEOID_block group', 'TAZ', 'weight']].copy()
    
    # CRITICAL CHECK: Look for block groups with multiple TAZ mappings
    bg_counts = bg_to_taz['GEOID_block group'].value_counts()
    multi_taz_bgs = bg_counts[bg_counts > 1]
    if len(multi_taz_bgs) > 0:
        print(f"[DEBUG][TRACT2BG] Block groups spanning multiple TAZs: {len(multi_taz_bgs)}")
        sample_bg = multi_taz_bgs.index[0]
        sample_mappings = bg_to_taz[bg_to_taz['GEOID_block group'] == sample_bg]
        print(f"[DEBUG][TRACT2BG] Sample multi-TAZ BG {sample_bg}: TAZs={sample_mappings['TAZ'].tolist()}, weights={sample_mappings['weight'].tolist()}")
    else:
        print(f"[DEBUG][TRACT2BG] All block groups map to single TAZs")
    
    # Prepare the disaggregated block group data for aggregation
    bg_result = merged[[geoid_col, control_name]].copy()
    bg_result[geoid_col] = bg_result[geoid_col].astype(str)
    
    # CRITICAL FIX: Normalize GEOID formats by removing leading zeros
    # The crosswalk data has GEOIDs without leading zeros while Census data has them
    bg_result[geoid_col] = bg_result[geoid_col].str.lstrip('0')
    bg_to_taz['GEOID_block group'] = bg_to_taz['GEOID_block group'].str.lstrip('0')
    
    print(f"[DEBUG][TRACT2BG] BG result shape before TAZ merge: {bg_result.shape}")
    print(f"[DEBUG][TRACT2BG] BG result sum before TAZ merge: {bg_result[control_name].sum():,.0f}")
    
    # Merge block group data with weighted TAZ mapping
    bg_with_taz = pd.merge(
        bg_result, 
        bg_to_taz, 
        left_on=geoid_col, 
        right_on='GEOID_block group', 
        how='left'
    )
    
    print(f"[DEBUG][TRACT2BG] After BG-to-TAZ merge shape: {bg_with_taz.shape}")
    print(f"[DEBUG][TRACT2BG] After BG-to-TAZ merge sum (before apportionment): {bg_with_taz[control_name].sum():,.0f}")
    
    # Apply weights to apportion block group values across TAZs
    bg_with_taz[control_name] = bg_with_taz[control_name] * bg_with_taz['weight'].fillna(1.0)
    
    print(f"[DEBUG][TRACT2BG] After apportionment sum: {bg_with_taz[control_name].sum():,.0f}")
    
    # Check for unmatched block groups
    unmatched_bgs = bg_with_taz['TAZ'].isna().sum()
    if unmatched_bgs > 0:
        logger.warning(f"Found {unmatched_bgs} block groups without TAZ mapping")
        print(f"[DEBUG][TRACT2BG] Warning: {unmatched_bgs} block groups without TAZ mapping")
    
    # Aggregate from block group to TAZ level
    taz_result = bg_with_taz.groupby('TAZ')[control_name].sum().reset_index()
    taz_result = taz_result.set_index('TAZ')
    
    print(f"[DEBUG][TRACT2BG] ==> FINAL TAZ RESULT")
    print(f"[DEBUG][TRACT2BG] TAZ result shape: {taz_result.shape}")
    print(f"[DEBUG][TRACT2BG] TAZ result sum: {taz_result[control_name].sum():,.0f}")
    print(f"[DEBUG][TRACT2BG] ** OVERALL RATIO (TAZ/tract): {taz_result[control_name].sum() / control_table_df[control_name].sum():.4f} **")

    # CRITICAL VALIDATION: Check if total matches expected input
    expected_total = control_table_df[control_name].sum()
    actual_total = taz_result[control_name].sum()
    ratio = actual_total / expected_total if expected_total > 0 else 0
    
    if abs(ratio - 1.0) > 0.05:  # More than 5% difference
        print(f"[DEBUG][TRACT2BG] *** WARNING: SIGNIFICANT TOTAL CHANGE ***")
        print(f"[DEBUG][TRACT2BG] Expected: {expected_total:,.0f}")
        print(f"[DEBUG][TRACT2BG] Actual: {actual_total:,.0f}")
        print(f"[DEBUG][TRACT2BG] Ratio: {ratio:.4f}")
        print(f"[DEBUG][TRACT2BG] This suggests geographic scope differences or data issues")

    logger.info(f"[TRACT2BG] Completed tract-to-block group-to-TAZ disaggregation for '{control_name}'")
    return taz_result


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

    import logging
    logger = logging.getLogger()
    logger.info(f"[CREATE_CONTROL_TABLE] Building '{control_name}' from census_table '{census_table_name}'")
    logger.info(f"[CREATE_CONTROL_TABLE] Input DataFrame shape: {census_table_df.shape}, columns: {list(census_table_df.columns)}")

    # Identify geography columns (those present in census_table_df and likely to be geo columns)
    possible_geo_cols = [
        'state', 'county', 'tract', 'block', 'block group',
        'GEOID', 'GEOID_block', 'GEOID_block group', 'GEOID_tract', 'GEOID_county'
    ]
    geo_cols = [col for col in possible_geo_cols if col in census_table_df.columns]

    # Identify data columns (non-geography columns)
    data_cols = [col for col in census_table_df.columns if col not in geo_cols]

    # If all control_dicts are empty, sum once outside the loop
    if all(len(control_dict) == 0 for control_dict in control_dict_list):
        logger.info(f"[CREATE_CONTROL_TABLE] All control_dicts empty for '{control_name}', summing all data columns: {data_cols}")
        summed = census_table_df[data_cols].apply(
            lambda x: pd.to_numeric(x.astype(str).str.replace(',', '').str.replace(' ', ''), errors="coerce").fillna(0)
        ).sum(axis=1)
        control_df = pd.DataFrame({control_name: summed.astype(float)})
    else:
        control_df = pd.DataFrame(index=census_table_df.index, columns=[control_name], data=0.0)
        for control_dict in control_dict_list:
            # If control_dict is empty, always sum all non-geo columns (even if there are multiple columns)
            if len(control_dict) == 0:
                logger.info(f"[CREATE_CONTROL_TABLE] control_dict empty for '{control_name}', summing all data columns: {data_cols}")
                summed = census_table_df[data_cols].apply(
                    lambda x: pd.to_numeric(x.astype(str).str.replace(',', '').str.replace(' ', ''), errors="coerce").fillna(0)
                ).sum(axis=1)
                control_df[control_name] = summed.astype(float)
            else:
                # Handle both MultiIndex and regular Index
                if isinstance(census_table_df.columns, pd.MultiIndex):
                    logger.info(f"[CREATE_CONTROL_TABLE] MultiIndex detected for '{control_name}'")
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
                            logger.info(f"[CREATE_CONTROL_TABLE] param_dict matches control_dict for '{control_name}', using variable: {variable_name}")
                            control_df["temp"] = census_table_df[variable_name]
                            control_df[control_name] = census_table_df[variable_name]
                            control_df.drop(columns="temp", inplace=True)
                            break
                        if census_col_is_in_control(param_dict, control_dict):
                            logger.info(f"[CREATE_CONTROL_TABLE] param_dict in control for '{control_name}', adding variable: {variable_name}")
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
                                    logger.info(f"[CREATE_CONTROL_TABLE] Adding variable '{variable_name}' to '{control_name}'")
                                    col_data = census_table_df[variable_name].astype(str).str.replace(',', '').str.replace(' ', '')
                                    col_data = pd.to_numeric(col_data, errors="coerce").fillna(0)
                                    control_df["temp"] = col_data
                                    control_df[control_name] = pd.to_numeric(control_df[control_name], errors="coerce").fillna(0)
                                    control_df[control_name] = control_df[control_name] + control_df["temp"]
                                    control_df.drop(columns="temp", inplace=True)
                    else:
                        # Fallback: sum all non-geo columns if no table definition found
                        logger.info(f"[CREATE_CONTROL_TABLE] No CENSUS_DEFINITIONS for '{census_table_name}', summing all data columns for '{control_name}'")
                        data_cols = [col for col in census_table_df.columns if col not in geo_cols]
                        for variable_name in data_cols:
                            col_data = census_table_df[variable_name].astype(str).str.replace(',', '').str.replace(' ', '')
                            col_data = pd.to_numeric(col_data, errors="coerce").fillna(0)
                            control_df["temp"] = col_data
                            control_df[control_name] = pd.to_numeric(control_df[control_name], errors="coerce").fillna(0)
                            control_df[control_name] = control_df[control_name] + control_df["temp"]
                            control_df.drop(columns="temp", inplace=True)
            new_sum = control_df[control_name].sum()
            logger.info(f"[CREATE_CONTROL_TABLE] After processing control_dict, '{control_name}' sum: {new_sum}")

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
    if 'GEOID_block group' in control_df.columns and 'GEOID_block' in control_df.columns:
        logger.info(f"[CREATE_CONTROL_TABLE] Aggregating '{control_name}' from block to block group level.")
        control_df = control_df.groupby('GEOID_block group')[control_name].sum().reset_index()
        control_df.set_index('GEOID_block group', inplace=True)

    logger.info(f"[CREATE_CONTROL_TABLE] Final DataFrame for '{control_name}' shape: {control_df.shape}, index: {control_df.index.name}")
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
    
    # Enhanced logging for temp table scaling
    logger = logging.getLogger()
    logger.info(f"TEMP TABLE SCALING START: {control_name}")
    logger.info(f"Scaling: {scale_numerator}/{scale_denominator}")
    logger.info(f"Input data: {len(control_table_df)} records, geography: {geography}")
    
    # Calculate input total
    if control_name in control_table_df.columns:
        input_total = control_table_df[control_name].sum()
        logger.info(f"Input total: {input_total:,.0f}")
    
    # Essential debug info
    print(f"[DEBUG] temp_table_scaling: {control_name}, scale: {scale_numerator}/{scale_denominator}")
    
    # Special case: check for disaggregation flag
    if scale_denominator == 'tract_to_bg_disaggregation':
        logger.info(f"Applying tract-to-block-group disaggregation using {scale_numerator} as weights")
        print(f"[DEBUG][PIPELINE] ==> TRACT-TO-BG DISAGGREGATION DETECTED")
        print(f"[DEBUG][PIPELINE] Control: {control_name}")
        print(f"[DEBUG][PIPELINE] Input total: {control_table_df[control_name].sum():,.0f}")
        logger.debug(f"Control Table df '{control_table_df}' ")
        logger.debug(f"Control name '{control_name}' ")
        logger.debug(f"Temporary controls '{temp_controls}' ")
        # Use the scale_numerator as the household weights table
        hh_weights_df = temp_controls.get(scale_numerator)
        if hh_weights_df is None:
            logger.error(f"Household weights table '{scale_numerator}' not found for disaggregation")
            raise ValueError(f"Cannot find household weights table '{scale_numerator}' for disaggregation")
        
        logger.info(f"Using weights from {scale_numerator}: {len(hh_weights_df)} records")
        print(f"[DEBUG][PIPELINE] About to call disaggregate_tract_to_block_group...")
        result = disaggregate_tract_to_block_group(control_table_df, control_name, hh_weights_df, maz_taz_def_df)
        print(f"[DEBUG][PIPELINE] ==> DISAGGREGATION COMPLETE")
        print(f"[DEBUG][PIPELINE] Result total: {result[control_name].sum():,.0f}")
        print(f"[DEBUG][PIPELINE] Input vs Result ratio: {result[control_name].sum() / control_table_df[control_name].sum():.6f}")
        
        # CRITICAL: Check if result is empty and handle fallback
        if result.empty:
            logger.warning("Tract-to-block-group disaggregation failed, falling back to direct tract-to-TAZ aggregation")
            print(f"[DEBUG][PIPELINE] *** WARNING: Disaggregation returned empty result! ***")
        
        # If disaggregation failed (empty result), aggregate tract data directly to TAZ level
        if result.empty:
            logger.warning("Tract-to-block-group disaggregation failed, falling back to direct tract-to-TAZ aggregation")
            print(f"[DEBUG][PIPELINE] *** WARNING: Disaggregation returned empty result! ***")
            print(f"[DEBUG][PIPELINE] Executing fallback to direct tract-to-TAZ aggregation")
            
            if maz_taz_def_df is None:
                logger.error("maz_taz_def_df required for TAZ aggregation fallback")
                raise ValueError("maz_taz_def_df is required for TAZ aggregation when disaggregation fails")
            
            # Filter out any header rows that might have string values
            filtered_df = control_table_df.copy()
            
            # Clean all columns that might have mixed types
            for col in filtered_df.columns:
                if col not in ['tr2020ge', 'GEOID_tract']:  # Keep geographic identifiers as-is
                    try:
                        # Convert to string first to handle any mixed types, then to numeric
                        filtered_df[col] = filtered_df[col].astype(str)
                        filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')
                    except Exception as e:
                        print(f"[DEBUG] Error converting column {col} to numeric: {e}")
            
            # Drop any rows where the control column is NaN (was non-numeric)
            before_filter = len(filtered_df)
            filtered_df = filtered_df.dropna(subset=[control_name])
            after_filter = len(filtered_df)
            print(f"[DEBUG] Filtered out {before_filter - after_filter} non-numeric rows, remaining: {after_filter} rows")
            
            # Now aggregate from tract to TAZ using the crosswalk
            print(f"[DEBUG] Aggregating tract data to TAZ level")
            
            # Get tract-to-TAZ mapping from maz_taz_def_df
            tract_to_taz = maz_taz_def_df[['GEOID_tract', 'TAZ']].drop_duplicates()
            print(f"[DEBUG] tract_to_taz mapping shape: {tract_to_taz.shape}")
            
            # Ensure data types match for merge
            print(f"[DEBUG] filtered_df['tr2020ge'] dtype: {filtered_df['tr2020ge'].dtype}")
            print(f"[DEBUG] tract_to_taz['GEOID_tract'] dtype: {tract_to_taz['GEOID_tract'].dtype}")
            
            # Convert both to string to ensure consistent merge
            filtered_df['tr2020ge'] = filtered_df['tr2020ge'].astype(str)
            tract_to_taz['GEOID_tract'] = tract_to_taz['GEOID_tract'].astype(str)
            
            print(f"[DEBUG] After type conversion - filtered_df['tr2020ge'] dtype: {filtered_df['tr2020ge'].dtype}")
            print(f"[DEBUG] After type conversion - tract_to_taz['GEOID_tract'] dtype: {tract_to_taz['GEOID_tract'].dtype}")
            
            # Merge with tract data
            merged_df = pd.merge(
                filtered_df,
                tract_to_taz,
                left_on='tr2020ge',
                right_on='GEOID_tract',
                how='inner'
            )
            print(f"[DEBUG] After tract-to-TAZ merge: {merged_df.shape}")
            
            # Aggregate by TAZ
            taz_aggregated = merged_df.groupby('TAZ')[control_name].sum().reset_index()
            print(f"[DEBUG] After TAZ aggregation: {taz_aggregated.shape}")
            
            # Set TAZ as index to match expected format
            taz_aggregated = taz_aggregated.set_index('TAZ')
            print(f"[DEBUG] Final TAZ result shape: {taz_aggregated.shape}")
            
            return taz_aggregated
        
        print(f"[DEBUG][PIPELINE] ==> RETURNING DISAGGREGATION RESULT")
        print(f"[DEBUG][PIPELINE] Final result shape: {result.shape}")
        print(f"[DEBUG][PIPELINE] Final result total: {result[control_name].sum():,.0f}")
        return result
    
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
        logger.info("Detected MAZ-level temp controls, performing MAZ-level scaling")
        print(f"[DEBUG] Detected MAZ-level temp controls, performing MAZ-level scaling")
        
        # First, aggregate control_table_df to MAZ level if needed
        if 'MAZ' not in control_table_df.columns:
            logger.info("Aggregating control data to MAZ level first")
            print(f"[DEBUG] Need to aggregate control_table_df to MAZ level first")
            # Need to use aggregate_to_control_geo to get the control to MAZ level
            
            if maz_taz_def_df is None:
                logger.error("maz_taz_def_df required for MAZ-level scaling")
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
                    logger.error("Failed to aggregate control_table_df to MAZ level")
                    raise ValueError(f"Failed to aggregate control_table_df to MAZ level")
            else:
                control_maz_df = control_maz_df[[control_name]]
        else:
            # Already has MAZ column
            logger.info("Control data already has MAZ column")
            if control_table_df.index.name != 'MAZ':
                control_maz_df = control_table_df.groupby('MAZ')[control_name].sum().to_frame()
            else:
                control_maz_df = control_table_df[[control_name]]
        
        logger.info(f"Control data aggregated to {len(control_maz_df)} MAZ zones")
        print(f"[DEBUG] control_maz_df columns: {list(control_maz_df.columns)}")
        print(f"[DEBUG] control_maz_df head:\n{control_maz_df.head()}")
        
        # Get denominator values (ensure it's indexed by MAZ)
        logger.info(f"Preparing denominator data: {scale_denominator}")
        if scale_denom_df.index.name != 'MAZ':
            if 'MAZ' in scale_denom_df.columns:
                denom_maz = scale_denom_df.set_index('MAZ')[[scale_denominator]]
            else:
                logger.error(f"Cannot determine MAZ index for scale_denominator {scale_denominator}")
                raise ValueError(f"Cannot determine MAZ index for scale_denominator {scale_denominator}")
        else:
            denom_maz = scale_denom_df[[scale_denominator]]
        
        # Merge and calculate fraction
        logger.info("Calculating scaling fractions by MAZ")
        merged = pd.merge(control_maz_df, denom_maz, left_index=True, right_index=True, how='left')
        merged[scale_denominator] = merged[scale_denominator].fillna(0)
        
        # Log scaling statistics
        orig_total = merged[control_name].sum()
        denom_total = merged[scale_denominator].sum()
        
        merged['temp_fraction'] = merged[control_name] / merged[scale_denominator].replace({0: numpy.nan})
        merged['temp_fraction'] = merged['temp_fraction'].replace({numpy.inf: 0, numpy.nan: 0})
        
        # Log fraction statistics
        fraction_stats = merged['temp_fraction'].describe()
        logger.info(f"Scaling fractions - mean: {fraction_stats['mean']:.4f}, std: {fraction_stats['std']:.4f}")
        logger.info(f"Fraction range: {fraction_stats['min']:.4f} to {fraction_stats['max']:.4f}")
        non_zero_fractions = (merged['temp_fraction'] > 0).sum()
        logger.info(f"MAZs with non-zero fractions: {non_zero_fractions}/{len(merged)}")
        
        if scale_numerator and scale_num_df is not None:
            print(f"[DEBUG] merged columns before numerator merge: {list(merged.columns)}")
            # Get numerator values (ensure it's indexed by MAZ)
            if scale_num_df.index.name != 'MAZ':
                if 'MAZ' in scale_num_df.columns:
                    num_maz = scale_num_df.set_index('MAZ')[[scale_numerator]]
                else:
                    raise ValueError(f"Cannot determine MAZ index for scale_numerator {scale_numerator}")
            else:
                num_maz = scale_num_df[[scale_numerator]]
            
            print(f"[DEBUG] num_maz columns: {list(num_maz.columns)}")
            print(f"[DEBUG] About to merge with suffixes for potential duplicates")
            
            # Check if column already exists to avoid conflicts
            if scale_numerator in merged.columns:
                print(f"[DEBUG] Column {scale_numerator} already exists in merged, using suffixes")
                merged = pd.merge(merged, num_maz, left_index=True, right_index=True, how='left', suffixes=('', '_num'))
                scale_col = f"{scale_numerator}_num"
            else:
                merged = pd.merge(merged, num_maz, left_index=True, right_index=True, how='left')
                scale_col = scale_numerator
            
            print(f"[DEBUG] merged columns after numerator merge: {list(merged.columns)}")
            merged[scale_col] = merged[scale_col].fillna(0)
            
            # Special case: when numerator equals denominator for household size controls
            if scale_numerator == scale_denominator and control_name.startswith('hh_size_'):
                print(f"[DEBUG] Scale numerator equals denominator ({scale_numerator}) for household size control, computing proper normalization")
                
                print(f"[DEBUG] temp_fraction sample values: {merged['temp_fraction'].head().values}")
                print(f"[DEBUG] scale_col sample values: {merged[scale_col].head().values}")
                print(f"[DEBUG] control_maz_df sample values: {control_maz_df[control_name].head().values}")
                
                # For household size controls, we need proper normalization:
                # final_hh_size_X = (raw_hh_size_X / sum_all_raw_hh_sizes) * num_hh
                #
                # We have:
                # - control_maz_df[control_name] = raw household size counts for this category
                # - merged[scale_col] = num_hh values
                #
                # We need to calculate: sum_all_raw_hh_sizes for each MAZ
                # This requires summing all household size categories (dynamically determined)
                
                # Get all household size controls from config
                from tm2_control_utils.config import get_controls_in_category
                hh_size_controls = get_controls_in_category('TAZ', 'household_size')
                available_hh_size_controls = [ctrl for ctrl in hh_size_controls if ctrl in temp_controls]
                
                if len(available_hh_size_controls) < len(hh_size_controls):
                    print(f"[DEBUG] Not all household size controls available yet ({len(available_hh_size_controls)}/{len(hh_size_controls)}), using temp_fraction scaling")
                    merged[control_name] = merged['temp_fraction'] * merged[scale_col]
                else:
                    print(f"[DEBUG] All household size controls available, computing proper normalization")
                    
                    # Calculate the sum of all raw household sizes for each MAZ
                    total_raw_hh_sizes = None
                    for ctrl_name in available_hh_size_controls:
                        # Get the control data aggregated to MAZ level
                        ctrl_data = temp_controls[ctrl_name]
                        if ctrl_data.index.name != 'MAZ':
                            if 'MAZ' in ctrl_data.columns:
                                ctrl_maz = ctrl_data.set_index('MAZ')[ctrl_name]
                            else:
                                print(f"[DEBUG] Cannot get MAZ-indexed data for {ctrl_name}")
                                continue
                        else:
                            ctrl_maz = ctrl_data[ctrl_name]
                        
                        if total_raw_hh_sizes is None:
                            total_raw_hh_sizes = ctrl_maz.copy()
                        else:
                            total_raw_hh_sizes += ctrl_maz
                    
                    if total_raw_hh_sizes is not None:
                        # Apply the proper normalization formula
                        raw_control = control_maz_df[control_name]
                        num_hh_values = merged[scale_col]
                        
                        # Ensure indices match for the calculation
                        total_raw_aligned = total_raw_hh_sizes.reindex(control_maz_df.index, fill_value=0)
                        
                        # Calculate: (raw_hh_size_X / sum_all_raw_hh_sizes) * num_hh
                        merged[control_name] = (raw_control / total_raw_aligned.replace(0, numpy.nan)) * num_hh_values
                        merged[control_name] = merged[control_name].fillna(0)
                        
                        print(f"[DEBUG] Applied proper household size normalization")
                        print(f"[DEBUG] Result sample values: {merged[control_name].head().values}")
                    else:
                        print(f"[DEBUG] Failed to calculate total raw household sizes, falling back to temp_fraction")
                        merged[control_name] = merged['temp_fraction'] * merged[scale_col]
                        
            elif scale_numerator == scale_denominator:
                print(f"[DEBUG] Scale numerator equals denominator ({scale_numerator}), using temp_fraction scaling")
                merged[control_name] = merged['temp_fraction'] * merged[scale_col]
                print(f"[DEBUG] Result sample values: {merged[control_name].head().values}")
            else:
                print(f"[DEBUG] Different numerator/denominator, applying temp_fraction scaling")
                merged[control_name] = merged['temp_fraction'] * merged[scale_col]
        
        result = merged[[control_name]]
        
        # Calculate final totals and log results
        final_total = result[control_name].sum()
        logger.info(f"MAZ-level scaling complete: {len(result)} MAZ zones, total = {final_total:,.0f}")
        
        if 'input_total' in locals():
            scaling_ratio = final_total / input_total if input_total > 0 else 0
            logger.info(f"Total scaling ratio: {scaling_ratio:.6f} ({final_total:,.0f}/{input_total:,.0f})")
        
        print(f"[DEBUG] temp_table_scaling result columns: {list(result.columns)}")
        print(f"[DEBUG] temp_table_scaling result head:\n{result.head()}")
        
        logger.info("TEMP TABLE SCALING COMPLETE (MAZ-level)")
        # Skip writing intermediate scaled CSV
        return result
    
    # Original logic for non-MAZ level scaling
    logger.info(f"Applying geographic-level scaling for {geo} geography")
    geo = geography.lower().replace('_', ' ')
    supported = ["block", "block group", "tract", "county"]
    if geo in supported:
        control_table_df = prepare_geoid_for_merge(control_table_df, geo)
        
        # Special handling for TAZ-level temp controls used as scaling basis
        denom_df = temp_controls[scale_denominator]
        if denom_df.index.name == 'TAZ':
            logger.info(f"Mapping {scale_denominator} from TAZ level back to {geo} geography for scaling")
            print(f"[DEBUG] {scale_denominator} is at TAZ level - need to map back to {geo} geography for scaling")
            
            # Map TAZ-level temp control back to block group level for scaling
            # This uses the same mapping logic but in reverse
            geo_mapping_df = maz_taz_def_df[['TAZ', f'GEOID_{geo}']].drop_duplicates()
            denom_with_geo = pd.merge(denom_df.reset_index(), geo_mapping_df, on='TAZ', how='left')
            denom_df = denom_with_geo.groupby(f'GEOID_{geo}')[scale_denominator].sum().to_frame()
            denom_df.index.name = f'GEOID_{geo}'
            denom_df = denom_df.reset_index()
            logger.info(f"Mapped {scale_denominator} from TAZ to {geo} level: {len(denom_df)} records")
            print(f"[DEBUG] Mapped {scale_denominator} from TAZ to {geo} level, shape: {denom_df.shape}")
        else:
            denom_df = prepare_geoid_for_merge(denom_df, geo)
        
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
            num_df = temp_controls[scale_numerator]
            if num_df.index.name == 'TAZ':
                print(f"[DEBUG] {scale_numerator} is at TAZ level - need to map back to {geo} geography for scaling")
                
                # Map TAZ-level temp control back to block group level for scaling
                geo_mapping_df = maz_taz_def_df[['TAZ', f'GEOID_{geo}']].drop_duplicates()
                num_with_geo = pd.merge(num_df.reset_index(), geo_mapping_df, on='TAZ', how='left')
                num_df = num_with_geo.groupby(f'GEOID_{geo}')[scale_numerator].sum().to_frame()
                num_df.index.name = f'GEOID_{geo}'
                num_df = num_df.reset_index()
                print(f"[DEBUG] Mapped {scale_numerator} from TAZ to {geo} level, shape: {num_df.shape}")
            else:
                num_df = prepare_geoid_for_merge(num_df, geo)
            
            logger.info(f"Preparing numerator data: {scale_numerator}")
            num_geoid_col = get_geoid_col(num_df, geo)
            if num_geoid_col != control_geoid_col:
                num_df = num_df.rename(columns={num_geoid_col: control_geoid_col})
            
            # Log scaling application
            orig_total = merged[control_name].sum()
            merged = pd.merge(num_df[[control_geoid_col, scale_numerator]], merged, on=control_geoid_col, how='left', suffixes=('_num', ''))
            merged[control_name] = merged['temp_fraction'] * merged[scale_numerator]
            scaled_total = merged[control_name].sum()
            
            logger.info(f"Geographic scaling applied: {orig_total:,.0f} -> {scaled_total:,.0f}")
            merged = merged[[control_geoid_col, control_name]]
        else:
            merged = merged[[control_geoid_col, control_name]]
            
        final_total = merged[control_name].sum()
        logger.info(f"Geographic-level scaling complete: {len(merged)} records, total = {final_total:,.0f}")
        logger.info("TEMP TABLE SCALING COMPLETE (Geographic-level)")
        
        print(f"[DEBUG] temp_table_scaling result columns: {list(merged.columns)}")
        print(f"[DEBUG] temp_table_scaling result head:\n{merged.head()}")
        
        # Skip writing intermediate scaled CSV
        return merged
    else:
        # For synthetic geographies, just return the input DataFrame (no scaling)
        logger.info(f"No scaling required for synthetic geography: {geography}")
        return control_table_df

def aggregate_to_control_geo(control_table_df, control_name, control_geography, census_geography, maz_taz_def_df, temp_controls, scale_numerator, scale_denominator, subtract_table, variable_total):
    from tm2_control_utils.config import GEOGRAPHY_ID_COLUMNS
    import logging
    
    # Diagnostics
    logger = logging.getLogger()
    logger.info(f"GEOGRAPHIC AGGREGATION START: {control_name} from {census_geography} to {control_geography}")
    logger.info(f"Input: {len(control_table_df)} records, total = {variable_total:,.0f}")
    
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
    
    logger.info(f"Column mapping: census_geoid='{census_geoid_col}', census_mapping='{census_mapping_col}', synth_mapping='{synth_mapping_col}'")
    
    print(f"[DEBUG] Using census_geoid_col: {census_geoid_col}")
    print(f"[DEBUG] Using census_mapping_col: {census_mapping_col}")  
    print(f"[DEBUG] Using synth_mapping_col: {synth_mapping_col}")
    
    # Ensure census GEOID is present
    if census_geoid_col not in control_table_df.columns:
        logger.info(f"Preparing GEOID column for {census_geo_lower} geography")
        control_table_df = prepare_geoid_for_merge(control_table_df, census_geo_lower)
    
    # Handle scaling and subtraction on census geography first
    if scale_numerator and scale_denominator:
        logger.info(f"Applying scaling: {scale_numerator}/{scale_denominator}")
        num_df = prepare_geoid_for_merge(temp_controls[scale_numerator], census_geo_lower)
        denom_df = prepare_geoid_for_merge(temp_controls[scale_denominator], census_geo_lower)
        
        # Log scaling statistics
        orig_total = control_table_df[control_name].sum()
        num_total = num_df[scale_numerator].sum() 
        denom_total = denom_df[scale_denominator].sum()
        scaling_factor = num_total / denom_total if denom_total > 0 else 0
        logger.info(f"Scaling factor: {scaling_factor:.6f} ({num_total:,.0f}/{denom_total:,.0f})")
        
        merged = pd.merge(control_table_df, num_df[[census_geoid_col, scale_numerator]], on=census_geoid_col, how='left')
        merged = pd.merge(merged, denom_df[[census_geoid_col, scale_denominator]], on=census_geoid_col, how='left')
        merged[control_name] = merged[control_name] * merged[scale_numerator] / merged[scale_denominator].replace({0: numpy.nan})
        merged[control_name] = merged[control_name].replace({numpy.inf: 0, numpy.nan: 0})
        merged.fillna(0, inplace=True)
        
        scaled_total = merged[control_name].sum()
        logger.info(f"Scaling complete: {orig_total:,.0f} -> {scaled_total:,.0f} (factor: {scaled_total/orig_total:.6f})")
        
        variable_total = variable_total * num_df[scale_numerator].sum() / denom_df[scale_denominator].sum()
        control_table_df = merged
        
    if subtract_table:
        logger.info(f"Applying subtraction: -{subtract_table}")
        orig_total = control_table_df[control_name].sum()
        sub_df = prepare_geoid_for_merge(temp_controls[subtract_table], census_geo_lower)
        sub_total = sub_df[subtract_table].sum()
        logger.info(f"Subtracting {sub_total:,.0f} from {orig_total:,.0f}")
        
        merged = pd.merge(control_table_df, sub_df[[census_geoid_col, subtract_table]], on=census_geoid_col, how='left')
        merged[control_name] = merged[control_name] - merged[subtract_table]
        
        final_total = merged[control_name].sum()
        logger.info(f"Subtraction complete: {orig_total:,.0f} -> {final_total:,.0f} (difference: {final_total-orig_total:,.0f})")
        
        variable_total = variable_total - sub_df[subtract_table].sum()
        control_table_df = merged
    
    # Now map from census geography to synthetic geography if needed
    if control_geography in ["MAZ", "TAZ", "COUNTY", "REGION"]:
        logger.info(f"Mapping from {census_geography} to {control_geography} using crosswalk")
        print(f"[DEBUG] Mapping from {census_geography} to {control_geography}")
        
        # Check if mapping columns exist in maz_taz_def_df
        if census_mapping_col not in maz_taz_def_df.columns:
            logger.error(f"Census mapping column '{census_mapping_col}' not found in crosswalk")
            raise KeyError(f"Census mapping column '{census_mapping_col}' not found in maz_taz_def_df. Available: {list(maz_taz_def_df.columns)}")
        if synth_mapping_col not in maz_taz_def_df.columns:
            logger.error(f"Synthetic mapping column '{synth_mapping_col}' not found in crosswalk")
            raise KeyError(f"Synthetic mapping column '{synth_mapping_col}' not found in maz_taz_def_df. Available: {list(maz_taz_def_df.columns)}")
        
        # Get unique mapping and ensure consistent data types
        geo_mapping_df = maz_taz_def_df[[synth_mapping_col, census_mapping_col]].drop_duplicates()
        logger.info(f"Geographic mapping: {len(geo_mapping_df)} unique {census_geography}->{control_geography} relationships")
        
        # Convert both join keys to string to ensure compatibility
        control_table_df[census_geoid_col] = control_table_df[census_geoid_col].astype(str).str.strip()
        geo_mapping_df[census_mapping_col] = geo_mapping_df[census_mapping_col].astype(str).str.strip()
        
        # Ensure leading zeros are consistent based on geography type
        if census_geography.lower() == 'block':
            control_table_df[census_geoid_col] = control_table_df[census_geoid_col].str.zfill(15)
            geo_mapping_df[census_mapping_col] = geo_mapping_df[census_mapping_col].str.zfill(15)
            logger.info("Applied 15-digit zero-padding for block geography")
        elif census_geography.lower() == 'block group':
            control_table_df[census_geoid_col] = control_table_df[census_geoid_col].str.zfill(12)
            geo_mapping_df[census_mapping_col] = geo_mapping_df[census_mapping_col].str.zfill(12)
            logger.info("Applied 12-digit zero-padding for block group geography")
        elif census_geography.lower() == 'tract':
            control_table_df[census_geoid_col] = control_table_df[census_geoid_col].str.zfill(11)
            geo_mapping_df[census_mapping_col] = geo_mapping_df[census_mapping_col].str.zfill(11)
            logger.info("Applied 11-digit zero-padding for tract geography")
        elif census_geography.lower() == 'county':
            control_table_df[census_geoid_col] = control_table_df[census_geoid_col].str.zfill(5)
            geo_mapping_df[census_mapping_col] = geo_mapping_df[census_mapping_col].str.zfill(5)
            logger.info("Applied 5-digit zero-padding for county geography")
        
        # Log merge preparation statistics
        control_records = len(control_table_df)
        unique_control_geoids = control_table_df[census_geoid_col].nunique()
        unique_mapping_geoids = geo_mapping_df[census_mapping_col].nunique()
        logger.info(f"Merge preparation: {control_records} control records, {unique_control_geoids} unique control GEOIDs")
        logger.info(f"Crosswalk contains {unique_mapping_geoids} unique {census_geography} GEOIDs")
        
        print(f"[DEBUG] geo_mapping_df shape: {geo_mapping_df.shape}")
        print(f"[DEBUG] geo_mapping_df head:\n{geo_mapping_df.head()}")
        print(f"[DEBUG] control_table_df dtypes: {control_table_df[census_geoid_col].dtype}")
        print(f"[DEBUG] geo_mapping_df dtypes: {geo_mapping_df[census_mapping_col].dtype}")
        print(f"[DEBUG] control_table_df join key sample: {control_table_df[census_geoid_col].head().tolist()}")
        print(f"[DEBUG] geo_mapping_df join key sample: {geo_mapping_df[census_mapping_col].head().tolist()}")
        
        # Merge control table with mapping on census GEOID
        logger.info(f"Merging control data with crosswalk on {census_geoid_col}")
        merged_df = pd.merge(
            control_table_df, 
            geo_mapping_df, 
            left_on=census_geoid_col, 
            right_on=census_mapping_col, 
            how='left'
        )
        
        # Log merge results
        merge_match_rate = len(merged_df) / len(control_table_df) if len(control_table_df) > 0 else 0
        non_null_synth = merged_df[synth_mapping_col].notna().sum()
        logger.info(f"Merge completed: {len(merged_df)} records ({merge_match_rate:.1%} match rate)")
        logger.info(f"Records with valid {control_geography} mapping: {non_null_synth}")
        
        print(f"[DEBUG] After merge, columns: {list(merged_df.columns)}")
        print(f"[DEBUG] merged_df shape: {merged_df.shape}")
        
        # Check if synthetic geography column is present
        if synth_mapping_col not in merged_df.columns:
            logger.error(f"Synthetic geography column '{synth_mapping_col}' missing after merge")
            raise KeyError(f"'{synth_mapping_col}' not in merged DataFrame after merge. Available: {list(merged_df.columns)}")
        
        # Aggregate to synthetic geography
        logger.info(f"Aggregating to {control_geography} level")
        pre_agg_total = merged_df[control_name].sum()
        unique_target_geog = merged_df[synth_mapping_col].nunique()
        
        final_df = merged_df.groupby(synth_mapping_col)[control_name].sum().reset_index()
        final_df.set_index(synth_mapping_col, inplace=True)
        final_df.index.name = control_geography
        
        post_agg_total = final_df[control_name].sum()
        logger.info(f"Aggregation complete: {len(final_df)} {control_geography} zones, total = {post_agg_total:,.0f}")
        logger.info(f"Total conservation: {post_agg_total/pre_agg_total:.6f}" if pre_agg_total > 0 else "Total conservation: N/A (zero input)")
        
        if abs(post_agg_total - pre_agg_total) > 0.01:
            logger.warning(f"Total changed during aggregation: {pre_agg_total:,.0f} -> {post_agg_total:,.0f}")

    else:
        # For census geographies, group by the census GEOID
        logger.info(f"Grouping by census geography: {census_geoid_col}")
        final_df = control_table_df.groupby(census_geoid_col)[control_name].sum().reset_index()
        final_df.set_index(census_geoid_col, inplace=True)
        final_df.index.name = control_geography
    
    logger.info(f"GEOGRAPHIC AGGREGATION COMPLETE: {len(final_df)} output zones")
    
    print(f"[DEBUG] final_df shape: {final_df.shape}")
    print(f"[DEBUG] final_df head:\n{final_df.head()}")
    
    # Check totals
    if not scale_numerator:
        final_total = final_df[control_name].sum()
        diff = abs(final_total - variable_total)
        if diff >= 0.5:
            logger.warning(f"Total difference of {diff:,.1f} between input ({variable_total:,.0f}) and output ({final_total:,.0f}) for {control_name}")
        else:
            logger.info(f"Total conservation check passed: difference = {diff:.3f}")
    
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
    logger = logging.getLogger()
    logger.info(f"GEOGRAPHIC MATCHING START: {control_name}")
    logger.info(f"Source: {census_geography} -> Target: {control_geography}")
    logger.info(f"Input: {len(control_table_df)} records")
    
    if scale_numerator or scale_denominator:
        logger.info(f"Scaling parameters: {scale_numerator}/{scale_denominator}")
    if subtract_table:
        logger.info(f"Subtraction: -{subtract_table}")
    
    print(f"[DEBUG] match_control_to_geography called with control_name={control_name}, control_geography={control_geography}, census_geography={census_geography}")
    print(f"[DEBUG] control_table_df columns: {list(control_table_df.columns)}")
    print(f"[DEBUG] maz_taz_def_df columns: {list(maz_taz_def_df.columns)}")
    print(temp_controls.keys())
    print(temp_controls.values())
    print(control_table_df.head())



    # Only allow supported geographies
    if control_geography not in ["MAZ","TAZ","COUNTY","REGION"]:
        logger.error(f"Unsupported control geography: {control_geography}")
        raise ValueError(f"match_control_to_geography passed unsupported control geography {control_geography}")
    if census_geography not in ["block","block group","tract","county subdivision","county"]:
        logger.error(f"Unsupported census geography: {census_geography}")
        raise ValueError(f"match_control_to_geography passed unsupported census geography {census_geography}")
        
    variable_total = control_table_df[control_name].sum()
    logger.info(f"Input total for validation: {variable_total:,.0f}")
    
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
        logger.info("Using temp table scaling approach")
        result = temp_table_scaling(control_table_df, control_name, scale_numerator, scale_denominator, temp_controls, maz_taz_def_df, geography=census_geography)
    else:
        logger.info("Using direct aggregation approach")
        result = aggregate_to_control_geo(control_table_df, control_name, control_geography, census_geography, maz_taz_def_df, temp_controls, scale_numerator, scale_denominator, subtract_table, variable_total)
    
    # Log final results
    final_total = result[control_name].sum()
    logger.info(f"GEOGRAPHIC MATCHING COMPLETE: {len(result)} {control_geography} zones, total = {final_total:,.0f}")
    
    if not scale_numerator:  # Only check conservation when not scaling
        conservation_ratio = final_total / variable_total if variable_total > 0 else 1.0
        logger.info(f"Total conservation: {conservation_ratio:.6f}")
        if abs(conservation_ratio - 1.0) > 0.01:
            logger.warning(f"Significant total change during geographic matching: {conservation_ratio:.6f}")
    
    return result

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
# Helper to get the canonical column name for a geography

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