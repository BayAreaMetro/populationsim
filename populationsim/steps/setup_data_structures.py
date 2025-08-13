

# PopulationSim
# See full license in LICENSE.txt.

from builtins import zip
import logging
import os

import pandas as pd
import numpy as np

from activitysim.core import inject
from activitysim.core import pipeline
from activitysim.core import config

from ..assign import assign_variable
from .helper import control_table_name
from .helper import get_control_table
from .helper import get_control_data_table

from activitysim.core.config import setting

logger = logging.getLogger(__name__)


def read_control_spec(data_filename):

    # read the csv file
    data_file_path = config.config_file_path(data_filename)
    if not os.path.exists(data_file_path):
        raise RuntimeError(
            "initial_seed_balancing - control file not found: %s" % (data_file_path,))

    logger.info("Reading control file %s" % data_file_path)
    control_spec = pd.read_csv(data_file_path, comment='#')

    geographies = setting('geographies')

    if 'geography' not in control_spec.columns:
        raise RuntimeError("missing geography column in controls file")

    for g in control_spec.geography.unique():
        if g not in geographies:
            raise RuntimeError("unknown geography column '%s' in control file" % g)

    return control_spec


def build_incidence_table(control_spec, households_df, persons_df, crosswalk_df):

    hh_col = setting('household_id_col')

    # CRITICAL FIX: Use household IDs as index instead of DataFrame positional index
    logger.info(f"BUILD_INCIDENCE_TABLE: Creating incidence table indexed by household IDs ({hh_col})")
    logger.info(f"  households_df shape: {households_df.shape}")
    logger.info(f"  households_df index range: {households_df.index.min()} to {households_df.index.max()}")
    logger.info(f"  {hh_col} sample values: {households_df[hh_col].head().tolist()}")
    logger.info(f"  {hh_col} unique count: {households_df[hh_col].nunique()}")
    
    # Create incidence table with household IDs as the index
    incidence_table = pd.DataFrame(index=households_df[hh_col])
    logger.info(f"  incidence_table initial shape: {incidence_table.shape}")
    logger.info(f"  incidence_table index sample: {incidence_table.index[:5].tolist()}")

    seed_tables = {
        'households': households_df,
        'persons': persons_df,
    }

    for control_row in control_spec.itertuples():

        logger.info("control target %s" % control_row.target)
        logger.debug("control_row.seed_table %s" % control_row.seed_table)
        logger.debug("control_row.expression %s" % control_row.expression)

        incidence, trace_results = assign_variable(
            target=control_row.target,
            expression=control_row.expression,
            df=seed_tables[control_row.seed_table],
            locals_dict={'np': np},
            df_alias=control_row.seed_table,
            trace_rows=None
        )

        # convert boolean True/False values to 1/0
        incidence = incidence * 1

        # Handle household vs person level controls differently
        if control_row.seed_table == 'households':
            logger.info(f"  Processing household-level control: {control_row.target}")
            logger.info(f"    households_df shape: {households_df.shape}")
            logger.info(f"    incidence shape: {incidence.shape}")
            logger.info(f"    households_df index range: {households_df.index.min()} to {households_df.index.max()}")
            logger.info(f"    incidence index range: {incidence.index.min()} to {incidence.index.max()}")
            
            # CRITICAL FIX: For household controls, map incidence by household ID
            # Create a mapping from household ID to incidence value
            incidence_for_assignment = pd.Series(incidence.values, index=households_df[hh_col])
            logger.info(f"    Created household ID to incidence mapping with {len(incidence_for_assignment)} entries")
            logger.info(f"    incidence_for_assignment index sample: {incidence_for_assignment.index[:5].tolist()}")
            logger.info(f"    incidence_table index sample: {incidence_table.index[:5].tolist()}")
            
        elif control_row.seed_table == 'persons':
            logger.info(f"  Processing person-level control: {control_row.target}")
            logger.info(f"    persons_df shape: {persons_df.shape}")
            logger.info(f"    hh_col value: {hh_col}")
            logger.info(f"    persons_df has {hh_col} column: {hh_col in persons_df.columns}")
            
            if hh_col in persons_df.columns:
                logger.info(f"    {hh_col} column sample values: {persons_df[hh_col].head().tolist()}")
                logger.info(f"    {hh_col} column unique count: {persons_df[hh_col].nunique()}")
                logger.info(f"    {hh_col} column null count: {persons_df[hh_col].isna().sum()}")
            else:
                logger.error(f"    ERROR: {hh_col} column not found in persons_df!")
                logger.error(f"    Available columns: {list(persons_df.columns)}")
                
            logger.info(f"    incidence shape before aggregation: {incidence.shape}")
            logger.info(f"    incidence sample values: {incidence.head().tolist()}")
            logger.info(f"    incidence non-zero count: {(incidence > 0).sum()}")
            
            df = pd.DataFrame({
                hh_col: persons_df[hh_col],
                'incidence': incidence
            })
            logger.info(f"    Aggregation dataframe shape: {df.shape}")
            logger.info(f"    Aggregation dataframe null counts: {df.isna().sum().to_dict()}")
            
            aggregated = df.groupby([hh_col], as_index=True).sum()
            logger.info(f"    aggregated shape after aggregation: {aggregated.shape}")
            logger.info(f"    aggregated sum after aggregation: {aggregated['incidence'].sum()}")
            logger.info(f"    aggregated null count after aggregation: {aggregated['incidence'].isna().sum()}")
            
            # Extract the series for assignment
            incidence_for_assignment = aggregated['incidence']
            
            logger.info(f"    Final incidence_for_assignment series shape: {incidence_for_assignment.shape}")
            logger.info(f"    Final incidence_for_assignment index type: {type(incidence_for_assignment.index[0]) if len(incidence_for_assignment) > 0 else 'EMPTY'}")
            logger.info(f"    Final incidence_for_assignment index sample: {incidence_for_assignment.index[:5].tolist()}")
            logger.info(f"    Incidence table index type: {type(incidence_table.index[0]) if len(incidence_table) > 0 else 'EMPTY'}")
            logger.info(f"    Incidence table index sample: {incidence_table.index[:5].tolist()}")
            
            # Check for index alignment issues
            missing_from_incidence_table = set(incidence_for_assignment.index) - set(incidence_table.index)
            missing_from_incidence = set(incidence_table.index) - set(incidence_for_assignment.index)
            
            if len(missing_from_incidence_table) > 0:
                logger.warning(f"    WARNING: {len(missing_from_incidence_table)} household IDs in person aggregation not found in incidence table")
                logger.warning(f"    Sample missing IDs: {list(missing_from_incidence_table)[:5]}")
                
            if len(missing_from_incidence) > 0:
                logger.warning(f"    WARNING: {len(missing_from_incidence)} household IDs in incidence table not found in person aggregation")
                logger.warning(f"    Sample missing IDs: {list(missing_from_incidence)[:5]}")

        # Single assignment point for both household and person controls
        logger.info(f"    ASSIGNING to incidence_table[{control_row.target}]...")
        incidence_table[control_row.target] = incidence_for_assignment
        
        # Verify the assignment worked
        assigned_nan_count = incidence_table[control_row.target].isna().sum()
        logger.info(f"    POST-ASSIGNMENT: {control_row.target} has {assigned_nan_count} NaN values out of {len(incidence_table)}")
        if assigned_nan_count > 0:
            logger.error(f"    ERROR: Assignment created NaN values!")
            logger.error(f"    First few NaN indices: {incidence_table[incidence_table[control_row.target].isna()].index[:5].tolist()}")

    return incidence_table


def add_geography_columns(incidence_table, households_df, crosswalk_df):
    """
    Add seed and meta geography columns to incidence_table

    Parameters
    ----------
    incidence_table
    households_df
    crosswalk_df

    Returns
    -------

    """

    geographies = setting('geographies')
    meta_geography = geographies[0]
    seed_geography = setting('seed_geography')
    hh_col = setting('household_id_col')

    logger.info(f"ADD_GEOGRAPHY_COLUMNS: Adding {seed_geography} and {meta_geography} columns")
    logger.info(f"  incidence_table shape: {incidence_table.shape}")
    logger.info(f"  households_df shape: {households_df.shape}")
    logger.info(f"  incidence_table indexed by: {hh_col}")

    # CRITICAL FIX: Create mapping from household ID to seed geography
    # Since incidence_table is indexed by household IDs, we need to map from household ID to geography
    hh_to_seed_geo = households_df.set_index(hh_col)[seed_geography]
    logger.info(f"  Created household ID to {seed_geography} mapping with {len(hh_to_seed_geo)} entries")
    
    # add seed_geography col to incidence table using household ID mapping
    incidence_table[seed_geography] = incidence_table.index.map(hh_to_seed_geo)
    logger.info(f"  Added {seed_geography} column to incidence table")
    
    # Check for any missing mappings
    missing_seed_geo = incidence_table[seed_geography].isna().sum()
    if missing_seed_geo > 0:
        logger.error(f"  ERROR: {missing_seed_geo} households missing {seed_geography} assignments!")
    else:
        logger.info(f"  SUCCESS: All households have {seed_geography} assignments")

    # add meta column to incidence table (unless it's already there)
    if seed_geography != meta_geography:
        tmp = crosswalk_df[list({seed_geography, meta_geography})]
        seed_to_meta = tmp.groupby(seed_geography, as_index=True).min()[meta_geography]
        incidence_table[meta_geography] = incidence_table[seed_geography].map(seed_to_meta)
        logger.info(f"  Added {meta_geography} column to incidence table")
        
        # Check for any missing meta geography mappings
        missing_meta_geo = incidence_table[meta_geography].isna().sum()
        if missing_meta_geo > 0:
            logger.error(f"  ERROR: {missing_meta_geo} households missing {meta_geography} assignments!")
        else:
            logger.info(f"  SUCCESS: All households have {meta_geography} assignments")

    # Final diagnostic
    logger.info(f"COMPLETED build_incidence_table - final shape: {incidence_table.shape}")
    
    # Check for any NaN values in the final incidence table
    nan_columns = []
    for col in incidence_table.columns:
        nan_count = incidence_table[col].isna().sum()
        if nan_count > 0:
            nan_columns.append(f"{col}: {nan_count}")
    
    if nan_columns:
        logger.error(f"FINAL INCIDENCE TABLE HAS NaN VALUES:")
        for nan_info in nan_columns:
            logger.error(f"  {nan_info}")
    else:
        logger.info(f"FINAL INCIDENCE TABLE: No NaN values found")

    return incidence_table


def build_control_table(geo, control_spec, crosswalk_df):

    # control_geographies is list with target geography and the geographies beneath it
    control_geographies = setting('geographies')
    assert geo in control_geographies
    control_geographies = control_geographies[control_geographies.index(geo):]

    # only want controls for control_geographies
    control_spec = control_spec[control_spec['geography'].isin(control_geographies)]
    controls_list = []

    # for each geography at or beneath target geography
    for g in control_geographies:

        # control spec rows for this geography
        spec = control_spec[control_spec['geography'] == g]

        # are there any controls specified for this geography? (e.g. seed has none)
        if len(spec.index) == 0:
            continue

        # control_data for this geography
        control_data_df = get_control_data_table(g)

        control_data_columns = [geo] + spec.control_field.tolist()

        if g == geo:
            # for top level, we expect geo_col, and need to group and sum
            assert geo in control_data_df.columns
            controls = control_data_df[control_data_columns]
            controls.set_index(geo, inplace=True)
        else:
            # aggregate sub geography control totals to the target geo level

            # add geo_col to control_data table
            if geo not in control_data_df.columns:
                # FIXED: Proper handling of higher-level controls (e.g., COUNTY to PUMA)
                # Instead of mapping to min() PUMA, distribute controls across all PUMAs in county
                if g == 'COUNTY' and geo == 'PUMA':
                    # Special handling for COUNTY controls distributed to PUMA level
                    logger.info(f"Distributing {g} controls to {geo} level")
                    
                    # Get unique COUNTY->PUMA mappings from crosswalk
                    county_puma_map = crosswalk_df[[g, geo]].drop_duplicates()
                    
                    # Count PUMAs per county for equal distribution
                    pumas_per_county = county_puma_map.groupby(g)[geo].count()
                    
                    # Create expanded control data with one row per PUMA
                    expanded_controls = []
                    for county_id in control_data_df[g]:
                        # Get all PUMAs for this county
                        county_pumas = county_puma_map[county_puma_map[g] == county_id][geo].tolist()
                        county_data = control_data_df[control_data_df[g] == county_id].iloc[0]
                        
                        # Distribute control values equally across all PUMAs in county
                        num_pumas = len(county_pumas)
                        for puma_id in county_pumas:
                            puma_row = county_data.copy()
                            puma_row[geo] = puma_id
                            
                            # Divide county control values by number of PUMAs (equal distribution)
                            for col in control_data_columns:
                                if col != geo and col != g:  # Don't modify geography columns
                                    puma_row[col] = puma_row[col] / num_pumas
                            
                            expanded_controls.append(puma_row)
                    
                    # Create new dataframe with distributed controls
                    control_data_df = pd.DataFrame(expanded_controls)
                    logger.info(f"Distributed {g} controls: {len(expanded_controls)} PUMA records created")
                    
                else:
                    # Standard mapping for other geography combinations (original logic)
                    sub_to_geog = crosswalk_df[[g, geo]].groupby(g, as_index=True).min()[geo]
                    control_data_df[geo] = control_data_df[g].map(sub_to_geog)

            # aggregate (sum) controls to geo level
            controls = control_data_df[control_data_columns].groupby(geo, as_index=True).sum()

        controls_list.append(controls)

    # concat geography columns
    controls = pd.concat(controls_list, axis=1)

    # rename columns from seed_col to target
    columns = {c: t for c, t in zip(control_spec.control_field, control_spec.target)}
    controls.rename(columns=columns, inplace=True)

    # reorder columns to match order of control_spec rows
    controls = controls[control_spec.target]

    # drop controls for zero-household geographies
    total_hh_control_col = setting('total_hh_control')
    empty = (controls[total_hh_control_col] == 0)
    if empty.any():
        controls = controls[~empty]
        logger.info("dropping %s %s control rows with empty total_hh_control" % (empty.sum(), geo))

    return controls


def build_crosswalk_table():
    """
    build crosswalk table filtered to include only zones in lowest geography
    """

    geographies = setting('geographies')

    crosswalk_data_table = inject.get_table('geo_cross_walk').to_frame()

    # dont need any other geographies
    crosswalk = crosswalk_data_table[geographies]

    # filter geo_cross_walk_df to only include geo_ids with lowest_geography controls
    # (just in case geo_cross_walk_df table contains rows for unused low zones)
    low_geography = geographies[-1]
    low_control_data_df = get_control_data_table(low_geography)
    rows_in_low_controls = crosswalk[low_geography].isin(low_control_data_df[low_geography])
    crosswalk = crosswalk[rows_in_low_controls]

    return crosswalk


def build_grouped_incidence_table(incidence_table, control_spec, seed_geography):

    hh_incidence_table = incidence_table
    household_id_col = setting('household_id_col')

    hh_groupby_cols = list(control_spec.target) + [seed_geography]
    hh_grouper = hh_incidence_table.groupby(hh_groupby_cols)
    group_incidence_table = hh_grouper.max()
    group_incidence_table['sample_weight'] = hh_grouper.sum()['sample_weight']
    group_incidence_table['group_size'] = hh_grouper.count()['sample_weight']
    group_incidence_table = group_incidence_table.reset_index()

    logger.info("grouped incidence table has %s entries, ungrouped has %s"
                % (len(group_incidence_table.index), len(hh_incidence_table.index)))

    # add group_id of each hh to hh_incidence_table
    group_incidence_table['group_id'] = group_incidence_table.index
    # DEBUG: Enhanced merge debugging for IntCastingNaNError
    print("DEBUG: About to merge household incidence table with group incidence table")
    print(f"DEBUG: hh_groupby_cols = {hh_groupby_cols}")
    print(f"DEBUG: hh_incidence_table shape: {hh_incidence_table.shape}")
    print(f"DEBUG: group_incidence_table shape: {group_incidence_table.shape}")
    
    # Check for NaN values in groupby columns before merge
    for col in hh_groupby_cols:
        hh_nan_count = hh_incidence_table[col].isna().sum()
        group_nan_count = group_incidence_table[col].isna().sum()
        print(f"DEBUG: {col} - hh NaN: {hh_nan_count}, group NaN: {group_nan_count}")
        if hh_nan_count > 0:
            print(f"DEBUG: Sample hh NaN rows for {col}:")
            nan_sample = hh_incidence_table[hh_incidence_table[col].isna()].head(3)
            for idx, row in nan_sample.iterrows():
                print(f"  Row {idx}: {dict(row[hh_groupby_cols])}")
    
    # Perform the merge with debugging
    merge_result = hh_incidence_table[hh_groupby_cols].merge(
        group_incidence_table[hh_groupby_cols + ['group_id']],
        on=hh_groupby_cols,
        how='left')
    
    print(f"DEBUG: Merge result shape: {merge_result.shape}")
    group_id_nan_count = merge_result['group_id'].isna().sum()
    print(f"DEBUG: group_id NaN count after merge: {group_id_nan_count}")
    
    if group_id_nan_count > 0:
        print("DEBUG: Sample rows with NaN group_id after merge:")
        nan_rows = merge_result[merge_result['group_id'].isna()].head(5)
        for idx, row in nan_rows.iterrows():
            print(f"  Row {idx}: {dict(row)}")
        
        print("DEBUG: Checking what combinations exist in group_incidence_table:")
        group_combinations = group_incidence_table[hh_groupby_cols].drop_duplicates()
        print(f"  Found {len(group_combinations)} unique combinations in group table")
        
        # Show some unmatched combinations
        hh_combinations = hh_incidence_table[hh_groupby_cols].drop_duplicates()
        unmatched = hh_combinations.merge(group_combinations, on=hh_groupby_cols, how='left', indicator=True)
        unmatched_only = unmatched[unmatched['_merge'] == 'left_only']
        print(f"  Found {len(unmatched_only)} unmatched combinations in household table")
        if len(unmatched_only) > 0:
            print("  Sample unmatched combinations:")
            for idx, row in unmatched_only.head(5).iterrows():
                print(f"    {dict(row[hh_groupby_cols])}")
    
    # Convert to int, but handle NaN values first
    if group_id_nan_count > 0:
        print("ERROR: Cannot convert group_id to int due to NaN values")
        print("Attempting to fill NaN values with -1 as fallback")
        merge_result['group_id'] = merge_result['group_id'].fillna(-1)
    
    hh_incidence_table['group_id'] = merge_result.group_id.astype(int).values

    # it doesn't really matter what the incidence_table index is until we create population
    # when we need to expand each group to constituent households
    # but incidence_table should have the same name whether grouped or ungrouped
    # so that the rest of the steps can handle them interchangeably
    group_incidence_table.index.name = hh_incidence_table.index.name

    # create table mapping household_groups to households and their sample_weights
    # explicitly provide hh_id as a column to make it easier for use when expanding population
    household_groups = hh_incidence_table[['group_id', 'sample_weight']].copy()
    household_groups[household_id_col] = household_groups.index.astype(int)

    return group_incidence_table, household_groups


def filter_households(households_df, persons_df, crosswalk_df):
    """
    Filter households and persons tables, removing zero weight households
    and any households not in seed zones.

    Returns filtered households_df and persons_df
    """
    
    # Store original counts for logging
    original_hh_count = len(households_df)
    original_person_count = len(persons_df)
    logger.info(f"FILTER_HOUSEHOLDS: Starting with {original_hh_count} households, {original_person_count} persons")

    # drop any zero weight households (there are some in calm data)
    hh_weight_col = setting('household_weight_col')
    zero_weight_count = (households_df[hh_weight_col] <= 0).sum()
    logger.info(f"FILTER_HOUSEHOLDS: Found {zero_weight_count} zero-weight households to remove")
    households_df = households_df[households_df[hh_weight_col] > 0]
    logger.info(f"FILTER_HOUSEHOLDS: After zero-weight removal: {len(households_df)} households")

    # remove any households not in seed zones
    seed_geography = setting('seed_geography')
    seed_ids = crosswalk_df[seed_geography].unique()
    logger.info(f"FILTER_HOUSEHOLDS: Seed geography '{seed_geography}' has {len(seed_ids)} zones")

    rows_in_seed_zones = households_df[seed_geography].isin(seed_ids)
    if rows_in_seed_zones.any():
        households_df = households_df[rows_in_seed_zones]
        logger.info("dropped %s households not in seed zones" % (~rows_in_seed_zones).sum())
        logger.info("kept %s households in seed zones" % len(households_df))

    # CRITICAL FIX: Filter persons to match the filtered households
    household_id_col = setting('household_id_col')
    retained_household_ids = set(households_df[household_id_col])
    logger.info(f"FILTER_HOUSEHOLDS: Filtering persons to match {len(retained_household_ids)} retained households")
    
    # Filter persons to only include those belonging to retained households
    persons_df = persons_df[persons_df[household_id_col].isin(retained_household_ids)]
    logger.info(f"FILTER_HOUSEHOLDS: After person filtering: {len(persons_df)} persons")
    
    # CRITICAL FIX: Reset DataFrame indexes to ensure proper alignment
    households_df = households_df.reset_index(drop=True)
    persons_df = persons_df.reset_index(drop=True)
    logger.info("FILTER_HOUSEHOLDS: Reset DataFrame indexes for proper alignment")
    
    # Final summary and verification
    logger.info("FILTER_SUMMARY:")
    logger.info(f"  Original households: {original_hh_count} -> Filtered households: {len(households_df)}")
    logger.info(f"  Original persons: {original_person_count} -> Filtered persons: {len(persons_df)}")
    logger.info(f"  Retained {len(retained_household_ids)} household IDs")
    logger.info(f"  Households index range: {households_df.index.min()} to {households_df.index.max()}")
    logger.info(f"  Persons index range: {persons_df.index.min()} to {persons_df.index.max()}")
    
    # Verify household ID alignment
    hh_ids_households = set(households_df[household_id_col])
    hh_ids_persons = set(persons_df[household_id_col])
    missing_from_persons = hh_ids_households - hh_ids_persons
    missing_from_households = hh_ids_persons - hh_ids_households
    
    logger.info(f"  Final household ID alignment check:")
    logger.info(f"    Household IDs in households: {len(hh_ids_households)}")
    logger.info(f"    Household IDs in persons: {len(hh_ids_persons)}")
    logger.info(f"    Missing from persons: {len(missing_from_persons)}")
    logger.info(f"    Missing from households: {len(missing_from_households)}")
    
    if missing_from_persons or missing_from_households:
        logger.error("FILTER_HOUSEHOLDS: ERROR - Household ID mismatch detected!")
        if missing_from_persons:
            logger.error(f"    Sample missing from persons: {list(missing_from_persons)[:5]}")
        if missing_from_households:
            logger.error(f"    Sample missing from households: {list(missing_from_households)[:5]}")
    else:
        logger.info("  SUCCESS: Perfect household ID alignment achieved")

    return households_df, persons_df


@inject.step()
def setup_data_structures(settings, households, persons):
    """
    Setup geographic correspondence (crosswalk), control sets, and incidence tables.

    A control tables for target geographies should already have been read in by running
    input_pre_processor. The zone control tables contains one row for each zone, with columns
    specifying control field totals for that control

    This step reads in the global control file, which specifies which control control fields
    in the control table should be used for balancing, along with their importance and the
    recipe (seed table and expression) for determining household incidence for that control.

    If GROUP_BY_INCIDENCE_SIGNATURE setting is enabled, then incidence table rows are
    household group ids and and additional household_groups table is created mapping hh group ids
    to actual hh_ids.

    Parameters
    ----------
    settings: dict
        contents of settings.yaml as dict
    households: pipeline table
    persons: pipeline table

    creates pipeline tables:
        crosswalk
        controls
        geography-specific controls
        incidence_table
        household_groups (if GROUP_BY_INCIDENCE_SIGNATURE setting is enabled)

    modifies tables:
        households
        persons

    """

    seed_geography = setting('seed_geography')
    geographies = settings['geographies']

    households_df = households.to_frame()
    persons_df = persons.to_frame()

    crosswalk_df = build_crosswalk_table()
    inject.add_table('crosswalk', crosswalk_df)

    slice_geography = settings.get('slice_geography', None)
    if slice_geography:
        assert slice_geography in geographies
        assert slice_geography in crosswalk_df.columns

        # only want rows for slice_geography and higher
        slice_geographies = geographies[:geographies.index(slice_geography) + 1]
        slice_table = crosswalk_df[slice_geographies].groupby(slice_geography).max()
        # it is convenient to have slice_geography column in table as well as index
        slice_table[slice_geography] = slice_table.index
        inject.add_table(f"slice_crosswalk", slice_table)

    control_spec = read_control_spec(setting('control_file_name', 'controls.csv'))
    inject.add_table('control_spec', control_spec)

    for g in geographies:
        controls = build_control_table(g, control_spec, crosswalk_df)
        inject.add_table(control_table_name(g), controls)

    households_df, persons_df = filter_households(households_df, persons_df, crosswalk_df)
    pipeline.replace_table('households', households_df)
    pipeline.replace_table('persons', persons_df)

    incidence_table = \
        build_incidence_table(control_spec, households_df, persons_df, crosswalk_df)

    incidence_table = add_geography_columns(incidence_table, households_df, crosswalk_df)

    # CRITICAL FIX: add sample_weight col to incidence table using household ID mapping
    hh_weight_col = setting('household_weight_col')
    hh_col = setting('household_id_col')
    logger.info(f"ADDING SAMPLE_WEIGHT: Mapping {hh_weight_col} by household ID ({hh_col})")
    
    # Create mapping from household ID to sample weight
    hh_id_to_weight = pd.Series(households_df[hh_weight_col].values, index=households_df[hh_col])
    logger.info(f"  Created household ID to sample weight mapping with {len(hh_id_to_weight)} entries")
    logger.info(f"  Sample weight stats: min={hh_id_to_weight.min()}, max={hh_id_to_weight.max()}, mean={hh_id_to_weight.mean():.1f}")
    
    # Assign using household ID alignment
    incidence_table['sample_weight'] = hh_id_to_weight
    
    # Verify the assignment worked
    sample_weight_nan_count = incidence_table['sample_weight'].isna().sum()
    logger.info(f"  POST-ASSIGNMENT: sample_weight has {sample_weight_nan_count} NaN values out of {len(incidence_table)}")
    if sample_weight_nan_count > 0:
        logger.error(f"  ERROR: Sample weight assignment created {sample_weight_nan_count} NaN values!")
    else:
        logger.info("  SUCCESS: Sample weight assignment completed with no NaN values")

    if setting('GROUP_BY_INCIDENCE_SIGNATURE') and not setting('NO_INTEGERIZATION_EVER', False):
        group_incidence_table, household_groups \
            = build_grouped_incidence_table(incidence_table, control_spec, seed_geography)

        inject.add_table('household_groups', household_groups)
        inject.add_table('incidence_table', group_incidence_table)
    else:
        inject.add_table('incidence_table', incidence_table)


@inject.step()
def repop_setup_data_structures(households, persons):
    """
    Setup geographic correspondence (crosswalk), control sets, and incidence tables for repop run.

    A new lowest-level geography control tables should already have been read in by rerunning
    input_pre_processor with a table_list override. The control table contains one row for
    each zone, with columns specifying control field totals for that control

    This step reads in the repop control file, which specifies which control control fields
    in the control table should be used for balancing, along with their importance and the
    recipe (seed table and expression) for determining household incidence for that control.

    Parameters
    ----------
    households: pipeline table
    persons: pipeline table

    Returns
    -------

    """

    seed_geography = setting('seed_geography')
    geographies = setting('geographies')
    low_geography = geographies[-1]

    # replace crosswalk table
    crosswalk_df = build_crosswalk_table()
    pipeline.replace_table('crosswalk', crosswalk_df)

    # replace control_spec
    control_file_name = setting('repop_control_file_name', 'repop_controls.csv')
    control_spec = read_control_spec(control_file_name)

    # repop control spec should only specify controls for lowest level geography
    assert control_spec.geography.unique() == [low_geography]

    pipeline.replace_table('control_spec', control_spec)

    # build incidence_table with repop controls and households in repop zones
    # filter households (dropping any not in crosswalk) in order to build incidence_table
    # We DO NOT REPLACE households and persons as we need full tables to synthesize population
    # (There is no problem, however, with overwriting the incidence_table and household_groups
    # because the expand_households step has ALREADY created the expanded_household_ids table
    # for the original simulated population. )

    households_df = households.to_frame()
    persons_df = persons.to_frame()
    households_df, persons_df = filter_households(households_df, persons_df, crosswalk_df)
    incidence_table = build_incidence_table(control_spec, households_df, persons_df, crosswalk_df)
    incidence_table = add_geography_columns(incidence_table, households_df, crosswalk_df)
    
    # CRITICAL FIX: add sample_weight col to incidence table using household ID mapping
    hh_weight_col = setting('household_weight_col')
    hh_col = setting('household_id_col')
    logger.info(f"ADDING SAMPLE_WEIGHT (repop): Mapping {hh_weight_col} by household ID ({hh_col})")
    
    # Create mapping from household ID to sample weight
    hh_id_to_weight = pd.Series(households_df[hh_weight_col].values, index=households_df[hh_col])
    logger.info(f"  Created household ID to sample weight mapping with {len(hh_id_to_weight)} entries")
    
    # Assign using household ID alignment
    incidence_table['sample_weight'] = hh_id_to_weight
    
    # Verify the assignment worked
    sample_weight_nan_count = incidence_table['sample_weight'].isna().sum()
    logger.info(f"  POST-ASSIGNMENT (repop): sample_weight has {sample_weight_nan_count} NaN values out of {len(incidence_table)}")
    if sample_weight_nan_count > 0:
        logger.error(f"  ERROR: Sample weight assignment created {sample_weight_nan_count} NaN values!")
    else:
        logger.info("  SUCCESS: Sample weight assignment completed with no NaN values")

    # rebuild control tables with only the low level controls (aggregated at higher levels)
    for g in geographies:
        controls = build_control_table(g, control_spec, crosswalk_df)
        pipeline.replace_table(control_table_name(g), controls)

    if setting('GROUP_BY_INCIDENCE_SIGNATURE') and not setting('NO_INTEGERIZATION_EVER', False):
        group_incidence_table, household_groups \
            = build_grouped_incidence_table(incidence_table, control_spec, seed_geography)

        pipeline.replace_table('household_groups', household_groups)
        pipeline.replace_table('incidence_table', group_incidence_table)
    else:
        pipeline.replace_table('incidence_table', incidence_table)
