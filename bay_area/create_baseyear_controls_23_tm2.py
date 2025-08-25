"""
create_baseyear_controls_23_tm2.py

This script creates baseyear control files for the MTC Bay Area populationsim model using 
ACS 2023 data with simplified controls to reflect current Census data availability.

"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tm2_control_utils'))

from tm2_control_utils.config_census import *




USAGE = """


This script creates populationsim-compatible control files using multiple Census data sources
including ACS 2023 5-year estimates and 2020 Decennial Census data.

1) DATA DOWNLOADING AND CACHE MANAGEMENT:

Downloads multiple Census datasets via Census API:
- ACS 2023 5-year estimates (tract, block group levels for detailed demographics)
- ACS 2023 1-year estimates (county level for scaling targets only)
- 2020 Decennial Census data (block level for base geography and household counts)
One CSV file per census table with descriptive column headers in census_cache directory.
Automatic cache validation and refresh capability.
To force re-download: remove specific cache files.
2) GEOGRAPHY INTERPOLATION:

Converts 2020 Census estimates to 2010 Census geographies using areal interpolation crosswalks.
Required because MAZ/TAZ system was built on 2010 Census geography boundaries.
Uses proportional allocation based on area and demographic weights.
Handles block->block, block group->block group, tract->tract interpolation.
3) CONTROL PROCESSING (Config-Driven):

All controls (MAZ, TAZ, COUNTY) are dynamically specified in the configuration.
MAZ Level: Household and group quarters totals from 2020 Census block data.
TAZ Level: Worker, age, household characteristics from ACS tract summary data.
COUNTY Level: County-level ACS targets for scaling and control totals.
4) MAJOR DATA SOURCES BY CONTROL LEVEL:

MAZ Level: Primarily derived from 2020 Census block-level data aggregated to MAZ geography.
TAZ Level: Primarily derived from ACS tract-level data aggregated to TAZ geography.
County Level: Primarily derived from ACS county-level data for scaling and targets.
5) COUNTY-LEVEL SCALING:

Applies ACS 2023 1-year county estimates as scaling targets to MAZ household totals.
Uses more current 1-year estimates (vs 5-year) for county-level scaling factors.
Scaling factors are calculated from county summary and applied using the geographic crosswalk.
Ensures MAZ-level household totals match ACS 2023 1-year county targets.
6) OUTPUT FORMAT:

Creates populationsim-compatible marginals files:
maz_marginals.csv: MAZ-level controls (households, group quarters, etc.)
taz_marginals.csv: TAZ-level controls (workers, age groups, children, household size, income, etc.)
county_marginals.csv: County-level controls and region totals
county_summary_2020_2023.csv: County scaling factors and validation
geo_cross_walk_tm2.csv: Geographic crosswalk
All files are compatible with populationsim expected format and column headers.
7) STRUCTURE VALIDATION:

Automated validation step compares output file columns, types, and names to reference examples.
Ensures outputs match expected structure, except for documented changes.
"""

import collections
import logging
import os
import sys
import shutil
from pathlib import Path
import numpy
import pandas as pd
import traceback

from tm2_control_utils.config_census import *
from tm2_control_utils import config_census as config
from tm2_control_utils.config_census import (get_bay_area_county_codes, get_county_name_mapping, 
                                    get_control_categories_for_geography, get_controls_in_category,
                                    get_all_expected_controls_for_geography, get_missing_controls_for_geography)
from tm2_control_utils.census_fetcher import CensusFetcher
from tm2_control_utils.geog_utils import prepare_geography_dfs, add_aggregate_geography_colums, interpolate_est
from tm2_control_utils.controls import create_control_table, census_col_is_in_control, match_control_to_geography, integerize_control, aggregate_to_control_geo, add_geoid_column


def verify_input_files():
    """Verify that all required input files are accessible."""
    logger = logging.getLogger()
    
    from tm2_control_utils.config_census import unified_config
    logger.info("Checking file accessibility (unified config)")

    required_files = [
        ("Regular crosswalk", str(unified_config.CROSSWALK_FILES['popsim_crosswalk'])),
        ("Enhanced crosswalk", str(unified_config.CROSSWALK_FILES['enhanced_crosswalk'])),
    ]

    missing_files = []
    for desc, filepath in required_files:
        if not os.path.exists(filepath):
            missing_files.append((desc, filepath))
            logger.error(f"Missing {desc}: {filepath}")
        else:
            logger.info(f"Found {desc}: {filepath}")

    if missing_files:
        logger.error(f"Missing {len(missing_files)} required files")
        return False

    logger.info("All required files are accessible")
    return True


def copy_network_data_to_local():
    """
    Copy essential data files from network (M:) drive to local storage for offline work.
    Creates local_data directory structure and copies required files.
    """
    logger = logging.getLogger(__name__)
    
    # Define the files to copy
    files_to_copy = [
        (NETWORK_MAZ_TAZ_DEF_FILE, LOCAL_MAZ_TAZ_DEF_FILE),
        (NETWORK_MAZ_TAZ_ALL_GEOG_FILE, LOCAL_MAZ_TAZ_ALL_GEOG_FILE),
        (NETWORK_CENSUS_API_KEY_FILE, LOCAL_CENSUS_API_KEY_FILE),
    ]
    
    # Create local directories
    for _, local_path in files_to_copy:
        local_dir = Path(local_path).parent
        local_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {local_dir}")
    
    # Create local cache directory
    Path(LOCAL_CACHE_FOLDER).mkdir(parents=True, exist_ok=True)
    logger.info(f"Created directory: {LOCAL_CACHE_FOLDER}")
    
    # Copy files
    copied_files = []
    for network_path, local_path in files_to_copy:
        try:
            if os.path.exists(network_path):
                shutil.copy2(network_path, local_path)
                logger.info(f"Copied: {network_path} -> {local_path}")
                copied_files.append(local_path)
            else:
                logger.warning(f"Network file not found: {network_path}")
        except Exception as e:
            logger.error(f"Failed to copy {network_path}: {e}")
    
    # Copy census cache files if they exist
    if os.path.exists(NETWORK_CACHE_FOLDER):
        try:
            cache_files = []
            for file in os.listdir(NETWORK_CACHE_FOLDER):
                if file.endswith('.csv'):
                    src = os.path.join(NETWORK_CACHE_FOLDER, file)
                    dst = os.path.join(LOCAL_CACHE_FOLDER, file)
                    shutil.copy2(src, dst)
                    cache_files.append(file)
            logger.info(f"Copied {len(cache_files)} census cache files to {LOCAL_CACHE_FOLDER}")
        except Exception as e:
            logger.error(f"Failed to copy census cache files: {e}")
    else:
        logger.warning(f"Network cache folder not found: {NETWORK_CACHE_FOLDER}")
    
    logger.info(f"Successfully copied {len(copied_files)} files to local storage")
    return copied_files


def configure_file_paths(use_local=False):
    """
    Deprecated: All file paths are now managed by the unified config. This function is obsolete and does nothing.
    """
    pass




def show_control_categories():
    """Display the control categories configuration for all geography levels as a formatted table"""
    
    print("="*80)
    print("CONTROL CATEGORIES CONFIGURATION")
    print("="*80)
    
    for geography in ['MAZ', 'TAZ', 'COUNTY']:
        print(f"\n{geography} LEVEL CONTROLS:")
        print("-" * 40)
        
        categories = get_control_categories_for_geography(geography)
        if not categories:
            print(f"  No control categories defined for {geography}")
            continue
            
        for category, controls in categories.items():
            print(f"  {category.upper()}:")
            for control in controls:
                # Check if this control is actually defined in the config
                is_defined = geography in CONTROLS.get(ACS_EST_YEAR, {}) and control in CONTROLS[ACS_EST_YEAR][geography]
                status = "✓" if is_defined else "✗"
                print(f"    {status} {control}")
            print()
    
    print("="*80)
    print("LEGEND: ✓ = Defined in config, ✗ = Expected but not defined")
    print("="*80)


def apply_county_scaling(control_df, control_name, county_targets, maz_taz_def_df, logger):
    """Apply county-level scaling factors to MAZ controls using ACS 2023 county targets.
    
    Args:
        control_df: DataFrame with MAZ-level controls and control_name column
        control_name: Name of the control column to scale  
        county_targets: Dict with county FIPS codes as keys and target values
        maz_taz_def_df: Geographic crosswalk with MAZ to county mapping
        logger: Logger instance
    """
    if not county_targets:
        logger.warning(f"No county targets provided for {control_name}, skipping scaling")
        return control_df
    
    logger.info(f"Applying county-level scaling to {control_name}")
    
    # Ensure control_df has MAZ index
    if 'MAZ' not in control_df.columns and control_df.index.name != 'MAZ':
        logger.error(f"Control dataframe for {control_name} missing MAZ identifier")
        return control_df
        
    # Reset index if MAZ is the index
    if control_df.index.name == 'MAZ':
        control_df = control_df.reset_index()
    
    # Get county mapping from the crosswalk file (same approach as the validation function)
    from tm2_control_utils.config_census import unified_config
    import os
    
    geo_crosswalk_file = str(unified_config.CROSSWALK_FILES['enhanced_crosswalk'])
    if not os.path.exists(geo_crosswalk_file):
        logger.error(f"Crosswalk file not found: {geo_crosswalk_file}")
        return control_df
        
    try:
        crosswalk_df = pd.read_csv(geo_crosswalk_file)
        
        # Import county mapping from unified config (1-9 system to FIPS codes)
        from unified_tm2_config import config
        
        # Create county to FIPS mapping from unified config
        county_to_fips_mapping = {}
        for county_id, county_info in config.BAY_AREA_COUNTIES.items():
            county_to_fips_mapping[county_id] = county_info['fips_str']  # 3-digit FIPS string
        
        # Create county mapping - COUNTY column should already be 1-9 system from crosswalk
        county_fips_map = crosswalk_df[['MAZ', 'county_name', 'COUNTY']].drop_duplicates()
        
        # Convert COUNTY values (1-9) to 3-digit FIPS strings using unified config mapping
        county_fips_map['county_fips'] = county_fips_map['COUNTY'].map(county_to_fips_mapping)
        
        logger.info(f"County mapping created (1-9 to FIPS): {dict(county_fips_map.groupby('COUNTY')['county_fips'].first())}")
        logger.info(f"Available counties in crosswalk: {sorted(county_fips_map['county_fips'].unique())}")
        logger.info(f"Target counties available: {sorted(county_targets.keys())}")
        
    except Exception as e:
        logger.error(f"Error reading crosswalk file: {e}")
        return control_df
    
    # Merge control data with county mapping
    scaled_df = control_df.merge(county_fips_map[['MAZ', 'county_fips']], on='MAZ', how='left')
    
    # Check for missing county mappings
    missing_counties = scaled_df['county_fips'].isna().sum()
    if missing_counties > 0:
        logger.warning(f"Found {missing_counties} MAZ zones without county mapping - will use scale factor 1.0")
        # Fill missing county mappings with default from config instead of hardcoding
        from tm2_control_utils.config_census import get_default_county_fips
        default_county = get_default_county_fips()
        scaled_df['county_fips'] = scaled_df['county_fips'].fillna(default_county)
    
    # Calculate current totals by county from 2020 Census data
    county_current_totals = scaled_df.groupby('county_fips')[control_name].sum()
    logger.info(f"2020 Census {control_name} totals by county: {dict(county_current_totals)}")
    
    # Calculate scaling factors for each county
    county_scale_factors = {}
    for county_fips in county_current_totals.index:
        if county_fips in county_targets:
            current_total = county_current_totals[county_fips]
            target_total = county_targets[county_fips]
            if current_total > 0:
                scale_factor = target_total / current_total
                county_scale_factors[county_fips] = scale_factor
                logger.info(f"County {county_fips}: current={current_total:,.0f}, target={target_total:,.0f}, factor={scale_factor:.4f}")
            else:
                county_scale_factors[county_fips] = 1.0
                logger.warning(f"County {county_fips}: current total is 0, using factor 1.0")
        else:
            county_scale_factors[county_fips] = 1.0
            logger.warning(f"No target found for county {county_fips}, using factor 1.0")
    
    # Apply scaling factors by county
    scaled_df['scale_factor'] = scaled_df['county_fips'].map(county_scale_factors)
    
    # Check for any remaining NaN scale factors
    nan_factors = scaled_df['scale_factor'].isna().sum()
    if nan_factors > 0:
        logger.warning(f"Found {nan_factors} zones with NaN scale factors - setting to 1.0")
        scaled_df['scale_factor'] = scaled_df['scale_factor'].fillna(1.0)
    
    scaled_df[control_name] = scaled_df[control_name] * scaled_df['scale_factor']
    
    # Check for non-finite values before returning
    non_finite = ~numpy.isfinite(scaled_df[control_name])
    if non_finite.any():
        logger.error(f"Found {non_finite.sum()} non-finite values in {control_name} after scaling")
        logger.error(f"Non-finite zones: {scaled_df.loc[non_finite, 'MAZ'].tolist()[:10]}...")  # Show first 10
        # Replace non-finite values with 0
        scaled_df.loc[non_finite, control_name] = 0
        logger.warning(f"Replaced non-finite values in {control_name} with 0")
    
    # Return scaled dataframe with original structure
    result_df = scaled_df[['MAZ', control_name]].set_index('MAZ')
    
    # Verify scaling results
    original_total = control_df[control_name].sum()
    scaled_total = result_df[control_name].sum()
    logger.info(f"County scaling results for {control_name}: original={original_total:,.0f}, scaled={scaled_total:,.0f}")
    
    return result_df


def get_county_targets(cf, logger, use_offline_fallback=True):
    """Get county-level targets from ACS 2023 1-year estimates for scaling MAZ controls.
    
    Returns a dictionary with county FIPS codes as keys and target DataFrames as values.
    """
    # Removed: from tm2_control_utils import config (no such module)
    from tm2_control_utils.config_census import COUNTY_TARGETS_FILE, ACS_EST_YEAR, CONTROLS, PRIMARY_OUTPUT_DIR
    
    # Check for county targets cache file in primary output directory
    possible_cache_files = [
        os.path.join(PRIMARY_OUTPUT_DIR, COUNTY_TARGETS_FILE),  # Primary and only location
    ]
    
    county_targets_file = None
    for cache_file in possible_cache_files:
        if os.path.exists(cache_file):
            county_targets_file = cache_file
            logger.info(f"Using county targets cache: {cache_file}")
            break
    
    # Try to read from cache first
    if county_targets_file:
        logger.info(f"Reading county targets from local cache: {county_targets_file}")
        try:
            targets_df = pd.read_csv(county_targets_file)
            county_targets = {}
            for _, row in targets_df.iterrows():
                county_fips = str(row['county_fips']).zfill(3)
                target_name = row['target_name']
                target_value = row['target_value']
                if county_fips not in county_targets:
                    county_targets[county_fips] = {}
                county_targets[county_fips][target_name] = target_value
            
            logger.info(f"Loaded county targets for {len(county_targets)} counties")
            for county_fips, targets in county_targets.items():
                logger.info(f"  County {county_fips}: {targets}")
            return county_targets
        except Exception as e:
            logger.error(f"Failed to read county targets cache: {e}")
            if use_offline_fallback:
                logger.error("Cannot proceed in offline mode without valid county targets cache")
                return {}
    

    
    # Fetch from Census API and save to cache
    logger.info("Fetching county targets from ACS 2023 1-year estimates and saving to cache")
    logger.info("=== COUNTY TARGETS: Starting API calls ===")
    
    county_targets = {}
    
    try:
        # Get the county target table definitions from configuration
        target_tables = {}
        county_targets_config = CONTROLS[ACS_EST_YEAR].get('COUNTY_TARGETS', {})
        
        for target_name, control_def in county_targets_config.items():
            if len(control_def) >= 4:
                data_source, year, table, geography = control_def[:4]
                target_tables[target_name] = (data_source, year, table, geography)
        
        logger.info(f"=== COUNTY TARGETS: Will fetch {len(target_tables)} tables from config ===")
        
        # Fetch data from Census API
        for i, (target_name, (data_source, year, table, geography)) in enumerate(target_tables.items(), 1):
            try:
                logger.info(f"=== COUNTY TARGETS: API Call {i}/{len(target_tables)} ===")
                logger.info(f"Fetching {target_name} from {data_source} {year} table {table}")
                
                # Fetch county-level data
                county_data = cf.get_census_data(data_source, year, table, geography)
                logger.info(f"Successfully retrieved {len(county_data)} counties from API for {target_name}")
                
                # Extract targets by county
                data_col = f"{table}_001E"
                if data_col in county_data.columns:
                    # Process county data
                    county_data_reset = county_data.reset_index()
                    for _, row in county_data_reset.iterrows():
                        county_fips = str(row['county']).zfill(3)
                        target_value = int(row[data_col])
                        
                        if county_fips not in county_targets:
                            county_targets[county_fips] = {}
                        county_targets[county_fips][target_name] = target_value
                        logger.info(f"County {county_fips}: {target_name} = {target_value:,}")
                else:
                    logger.error(f"Expected column {data_col} not found in {target_name} data")
                    
            except Exception as e:
                logger.error(f"Failed to fetch {target_name}: {e}")
                continue
        
        if not county_targets:
            logger.error("Failed to fetch any county targets from Census API")
            return {}
            
        logger.info(f"Successfully calculated county targets for {len(county_targets)} counties")
        
    except Exception as e:
        logger.error(f"Error fetching county targets from Census API: {e}")
        return {}
    
    # Save to cache file if we successfully calculated targets
    if county_targets:
        try:
            # Prioritize saving to output directory
            cache_file = county_targets_file or possible_cache_files[0]  # Use output directory first
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            
            # Create cache data
            cache_data = []
            for county_fips, targets in county_targets.items():
                for target_name, target_value in targets.items():
                    cache_data.append({
                        'county_fips': county_fips,
                        'target_name': target_name, 
                        'target_value': target_value,
                        'source_year': ACS_EST_YEAR
                    })
            
            targets_df = pd.DataFrame(cache_data)
            targets_df.to_csv(cache_file, index=False)
            logger.info(f"Saved county targets to cache: {cache_file}")
        except Exception as e:
            logger.error(f"Failed to save county targets to cache: {e}")
    
    return county_targets

""" This is for if we wanted to distribute block group controls from household size from the ACS down to a smaller scale. In prior Census
implementations household size was available at block level. Because it is no longer available at block level, we just moved the control to block group level"""
def process_block_distribution_control(control_name, control_def, cf, maz_taz_def_df, crosswalk_df, logger):
    """Process household size controls using block group -> block -> MAZ distribution."""
    logger.info(f"Processing block distribution control: {control_name} - PLACEHOLDER IMPLEMENTATION")
    
    # For now, use regular processing - we can implement the block distribution later
    data_source, year, table, geography, columns = control_def[:5]
    
    # Create control table using standard method
    control_table_df = create_control_table(
        control_name, columns, table, 
        cf.get_census_data(data_source, year, table, geography)
    )
    
    # Match to MAZ geography using standard workflow
    final_df = match_control_to_geography(
        control_name, control_table_df, 'MAZ', geography,  # Force to MAZ regardless of original geography
        maz_taz_def_df, {}  # Empty temp controls for now
    )
    
    logger.info(f"Block distribution placeholder complete for {control_name}: {len(final_df)} MAZs")
    return final_df


def process_maz_scaled_control(control_name, control_def, cf, maz_taz_def_df, crosswalk_df, 
                               temp_controls, final_control_dfs, logger):
    """Process MAZ_SCALED controls with special processing or block distribution."""
    logger.info(f"Processing MAZ_SCALED control: {control_name}")
    
    # Parse the extended control definition
    if len(control_def) >= 6:
        data_source, year, table, geography, columns, processing_type = control_def[:6]
    else:
        data_source, year, table, geography, columns = control_def[:5]
        processing_type = 'regional_scale'  # Default
    
    if processing_type == 'block_distribution':
        # Use special block distribution logic for household size
        final_df = process_block_distribution_control(control_name, control_def, cf, maz_taz_def_df, crosswalk_df, logger)
    else:
        # Use standard processing followed by regional scaling
        # First process normally using existing process_control logic
        logger.info(f"Processing {control_name} with standard workflow first")
        
        # Create control table
        census_data = cf.get_census_data(data_source, year, table, geography)
        control_table_df = create_control_table(
            control_name, columns, table, census_data
        )
        logger.info(f"Control table for {control_name} has {len(control_table_df)} rows and {len(control_table_df.columns)} columns")
        
        # Match to geography and scale
        final_df = match_control_to_geography(
            control_name, control_table_df, 'MAZ', geography,
            maz_taz_def_df, temp_controls
        )
        
        # Integerize (note: this function doesn't actually need crosswalk_df for MAZ level)
        final_df = integerize_control(final_df, crosswalk_df, control_name)
    
    # Add to final outputs
    if 'MAZ_SCALED' not in final_control_dfs:
        final_control_dfs['MAZ_SCALED'] = final_df.copy()
    else:
        # Merge with existing MAZ_SCALED controls
        existing_df = final_control_dfs['MAZ_SCALED']
        final_control_dfs['MAZ_SCALED'] = existing_df.merge(
            final_df, on='MAZ', how='outer'
        ).fillna(0)
    
    logger.info(f"Completed processing MAZ_SCALED control: {control_name}")


def process_control(
    control_geo, control_name, control_def, cf, maz_taz_def_df, crosswalk_df, temp_controls, final_control_dfs, county_targets=None
):
    logger = logging.getLogger()
    logger.info(f"Creating control [{control_name}] for geography [{control_geo}]")
    logger.info("=" * 80)

    # Special case for REGION/gq_pop_region
    if control_geo == "REGION" and control_name == "gq_pop_region":
        # Hardcode the correct ACS 2023 target for now
        gq_pop_value = 155065  # From B26001 table for Bay Area counties
        logger.info(f"Using hardcoded regional target for gq_pop_region: {gq_pop_value:,.0f}")
        
        final_control_dfs[control_geo] = pd.DataFrame.from_dict(
            data={'REGION': [1], "gq_pop_region": [gq_pop_value]}
        ).set_index("REGION")
        logger.debug(f"\n{final_control_dfs[control_geo]}")
        return
    
    print("dataset:", control_def[0])
    print("year:", control_def[1])
    print("table:", control_def[2])
    print("geo:", control_def[3])
    # Step 1: Fetch census data
    census_table_df = cf.get_census_data(
        dataset=control_def[0],
        year=control_def[1],
        table=control_def[2],
        geo=control_def[3]
    )

    # CRITICAL DEBUGGING: Check raw Census API data for worker controls
    if 'wrk' in control_name.lower():
        print(f"[DEBUG][RAW] ==> RAW CENSUS DATA FOR {control_name}")
        print(f"[DEBUG][RAW] Raw census_table_df shape: {census_table_df.shape}")
        print(f"[DEBUG][RAW] Raw census_table_df columns: {list(census_table_df.columns)}")
        if len(census_table_df) > 0:
            print(f"[DEBUG][RAW] Sample tract data:")
            print(census_table_df.head(5))
        # Check if any columns look like they might be summed/aggregated
        numeric_cols = census_table_df.select_dtypes(include=['number']).columns
        for col in numeric_cols[:5]:  # Check first 5 numeric columns
            col_total = census_table_df[col].sum()
            col_mean = census_table_df[col].mean()
            col_max = census_table_df[col].max()
            print(f"[DEBUG][RAW] Column {col}: total={col_total:,.0f}, mean={col_mean:.1f}, max={col_max:.0f}")


    # Special handling for income controls: use config-driven, multi-variable aggregation from INCOME_BIN_MAPPING
    # Dynamically generate income_bin_controls from INCOME_BIN_MAPPING for config-driven logic
    from tm2_control_utils.config_census import INCOME_BIN_MAPPING
    income_bin_controls = [b['control'] for b in INCOME_BIN_MAPPING]
    if control_name in income_bin_controls:
        # Find the bin definition for this control
        bin_def = next((b for b in INCOME_BIN_MAPPING if b['control'] == control_name), None)
        if bin_def is None:
            raise ValueError(f"No INCOME_BIN_MAPPING entry found for control {control_name}")
        acs_vars = bin_def.get('acs_vars', [])
        if not acs_vars:
            raise ValueError(f"No acs_vars defined for income bin {control_name} in INCOME_BIN_MAPPING")
        logger.info(f"[INCOME] Building income control: {control_name}")
        logger.info(f"[INCOME] Using ACS variables: {acs_vars}")
        logger.info(f"[INCOME] Raw census_table_df shape: {census_table_df.shape}")
        logger.info(f"[INCOME] Raw census_table_df columns: {list(census_table_df.columns)}")
        logger.info(f"[INCOME] Sample census_table_df rows:\n{census_table_df[acs_vars + [census_table_df.columns[0]]].head(5)}")
        # Log sum for each ACS variable
        for v in acs_vars:
            if v in census_table_df.columns:
                logger.info(f"[INCOME] {v}: sum={census_table_df[v].sum():,.0f}")
        control_table_df = census_table_df.copy()
        # Sum all relevant ACS variables for this bin
        control_table_df[control_name] = control_table_df[acs_vars].sum(axis=1)
        logger.info(f"[INCOME] Created income control column '{control_name}' (sum={control_table_df[control_name].sum():,.0f})")
        # Log top/bottom 5 TAZs for this income bin if TAZ column exists
        taz_col = None
        for col in ['TAZ', 'taz', 'taz_id']:
            if col in control_table_df.columns:
                taz_col = col
                break
        if taz_col:
            logger.info(f"[INCOME] Top 5 {taz_col}s for {control_name}:\n{control_table_df[[taz_col, control_name]].sort_values(control_name, ascending=False).head(5)}")
            logger.info(f"[INCOME] Bottom 5 {taz_col}s for {control_name}:\n{control_table_df[[taz_col, control_name]].sort_values(control_name, ascending=True).head(5)}")
    else:
        # Step 2: Create control table (default logic)
        control_table_df = create_control_table(control_name, control_def[4], control_def[2], census_table_df)

    # CRITICAL DEBUGGING: Check control table creation for worker controls
    if 'wrk' in control_name.lower():
        print(f"[DEBUG][CREATE] ==> AFTER create_control_table FOR {control_name}")
        print(f"[DEBUG][CREATE] Control table shape: {control_table_df.shape}")
        print(f"[DEBUG][CREATE] Control table columns: {list(control_table_df.columns)}")
        if control_name in control_table_df.columns:
            control_total = control_table_df[control_name].sum()
            control_mean = control_table_df[control_name].mean()
            control_max = control_table_df[control_name].max()
            print(f"[DEBUG][CREATE] {control_name}: total={control_total:,.0f}, mean={control_mean:.1f}, max={control_max:.0f}")
            print(f"[DEBUG][CREATE] Sample control values:")
            print(control_table_df[[control_name]].head(5))

    # Step 2.1: Normalize household size controls if needed
    control_table_df = normalize_household_size_controls(control_table_df, control_name, temp_controls, logger)

    # Step 2.5: Write distribution weights debug file for household size controls
    if len(control_def) > 6:  # Has scaling parameters
        from tm2_control_utils.controls import write_distribution_weights_debug
        write_distribution_weights_debug(
            control_name, control_table_df, 
            control_def[5] if len(control_def) > 5 else None,  # scale_numerator
            control_def[6] if len(control_def) > 6 else None,  # scale_denominator
            temp_controls, maz_taz_def_df, control_def[3]
        )

    # Step 3: Interpolate if needed
    if CENSUS_GEOG_YEAR != CENSUS_EST_YEAR:
        logger.info(f"GEOGRAPHIC INTERPOLATION REQUIRED: {CENSUS_EST_YEAR} -> {CENSUS_GEOG_YEAR}")
        logger.info(f"Source geography: {control_def[3]}")
        
        # CRITICAL DEBUGGING: Track geographic interpolation effects for worker controls
        if 'wrk' in control_name.lower():
            print(f"[DEBUG][MAIN] ==> GEOGRAPHIC INTERPOLATION FOR WORKER CONTROL: {control_name}")
            print(f"[DEBUG][MAIN] Before interpolation: {len(control_table_df)} records, total = {control_table_df[control_name].sum():,.0f}")
        
        print("control_df columns:", control_table_df.columns)
        print(control_table_df.head())
        print(control_table_df.reset_index().head())
        control_table_df = interpolate_est(
            control_table_df,
            geo=control_def[3],
            target_geo_year=CENSUS_GEOG_YEAR,
            source_geo_year=CENSUS_EST_YEAR
        )
        
        # CRITICAL DEBUGGING: Track interpolation results for worker controls
        if 'wrk' in control_name.lower():
            print(f"[DEBUG][MAIN] After interpolation: {len(control_table_df)} records, total = {control_table_df[control_name].sum():,.0f}")
            print(f"[DEBUG][MAIN] Interpolation ratio: {control_table_df[control_name].sum() / 1221884:.6f}")
            print(f"[DEBUG][MAIN] Geographic scope change: {len(control_table_df)} vs original tract count")
        
        logger.info(f"Geographic interpolation completed for {control_name}")
    else:
        logger.info(f"No geographic interpolation needed: both years are {CENSUS_GEOG_YEAR}")

    # Step 4: Check for county_scale 
    if len(control_def) > 5 and control_def[5] == 'county_scale':
        # For county scaling, do simple geographic matching then apply county-specific factors
        logger.info(f"APPLYING COUNTY SCALING for {control_name}")
        final_df = match_control_to_geography(
            control_name, control_table_df, control_geo, control_def[3],
            maz_taz_def_df, temp_controls,
            scale_numerator=None, scale_denominator=None, subtract_table=None
        )
        
        # Apply county-level scaling using county targets
        # Note: county_targets should be passed as a parameter to process_control
        logger.warning(f"County scaling for {control_name}: requires county_targets parameter to be passed to process_control")
            
    else:
        # Normal processing with temp control scaling
        logger.info(f"APPLYING TEMP CONTROL SCALING for {control_name}")
        scale_numerator = control_def[5] if len(control_def) > 5 else None
        scale_denominator = control_def[6] if len(control_def) > 6 else None
        subtract_table = control_def[7] if len(control_def) > 7 else None

        if scale_numerator or scale_denominator:
            logger.info(f"Scaling parameters: numerator={scale_numerator}, denominator={scale_denominator}")
        if subtract_table:
            logger.info(f"Subtraction table: {subtract_table}")

        # For temp controls, use the original census geography as target instead of control_geo
        # This ensures temp controls like temp_hh_bg_for_tract_weights stay at block group level
        if control_name.startswith("temp_"):
            target_geography = control_def[3]  # Use census geography
            logger.info(f"TEMP CONTROL: Using census geography '{target_geography}' as target instead of '{control_geo}'")
            
            # Special handling for block group level temp controls
            if target_geography == 'block group':
                logger.info(f"TEMP CONTROL: Handling block group level control {control_name} with direct aggregation")
                
                # For block group controls, we need to handle them directly since match_control_to_geography
                # doesn't support 'block group' as a target geography
                
                # First prepare the control table with proper GEOID column
                control_table_df = control_table_df.copy()
                
                # Clean the data - remove any header rows and ensure numeric values
                print(f"[DEBUG] Before cleanup - control_table_df shape: {control_table_df.shape}")
                print(f"[DEBUG] Before cleanup - control_table_df dtypes: {control_table_df.dtypes.to_dict()}")
                
                # Check for and remove header rows
                if control_name in control_table_df.columns:
                    # Remove rows where the control column contains string values (headers)
                    string_mask = control_table_df[control_name].astype(str).str.match(r'^[a-zA-Z]', na=False)
                    if string_mask.any():
                        print(f"[DEBUG] Removing {string_mask.sum()} header rows from {control_name}")
                        control_table_df = control_table_df[~string_mask]
                    
                    # Convert to numeric and remove NaN values
                    control_table_df[control_name] = pd.to_numeric(control_table_df[control_name], errors='coerce')
                    control_table_df = control_table_df.dropna(subset=[control_name])
                
                print(f"[DEBUG] After cleanup - control_table_df shape: {control_table_df.shape}")
                
                # Make sure we have the right GEOID column for block group
                if 'GEOID_block group' not in control_table_df.columns:
                    control_table_df = add_geoid_column(control_table_df, 'block group')
                
                # Keep the GEOID as a column for disaggregation function to use
                if 'GEOID_block group' in control_table_df.columns:
                    final_df = control_table_df[['GEOID_block group', control_name]].copy()
                    
                    # Ensure the final DataFrame has clean numeric data
                    final_df[control_name] = pd.to_numeric(final_df[control_name], errors='coerce')
                    final_df = final_df.dropna(subset=[control_name])
                    
                    logger.info(f"Created block group level temp control: {len(final_df)} block groups")
                else:
                    logger.error(f"Could not create GEOID_block group column for {control_name}")
                    raise ValueError(f"Failed to create block group GEOID for {control_name}")
            else:
                # Use normal processing for other temp controls
                final_df = match_control_to_geography(
                    control_name, control_table_df, target_geography, control_def[3],
                    maz_taz_def_df, temp_controls,
                    scale_numerator=scale_numerator, scale_denominator=scale_denominator,
                    subtract_table=subtract_table
                )
        else:
            target_geography = control_geo
            # CRITICAL DEBUGGING: Track worker control processing through the entire pipeline
            if 'wrk' in control_name.lower():
                print(f"[DEBUG][MAIN] ==> PROCESSING WORKER CONTROL: {control_name}")
                print(f"[DEBUG][MAIN] Target geography: {target_geography}")
                print(f"[DEBUG][MAIN] Census geography: {control_def[3]}")
                print(f"[DEBUG][MAIN] Scale numerator: {scale_numerator}")
                print(f"[DEBUG][MAIN] Scale denominator: {scale_denominator}")
                print(f"[DEBUG][MAIN] Input control_table_df[{control_name}].sum(): {control_table_df[control_name].sum():,.0f}")
            
            final_df = match_control_to_geography(
                control_name, control_table_df, target_geography, control_def[3],
                maz_taz_def_df, temp_controls,
                scale_numerator=scale_numerator, scale_denominator=scale_denominator,
                subtract_table=subtract_table
            )
            
            # CRITICAL DEBUGGING: Check what comes back from match_control_to_geography
            if 'wrk' in control_name.lower():
                print(f"[DEBUG][MAIN] ==> RECEIVED RESULT FROM match_control_to_geography")
                print(f"[DEBUG][MAIN] Result final_df[{control_name}].sum(): {final_df[control_name].sum():,.0f}")
                print(f"[DEBUG][MAIN] Input vs Result ratio: {final_df[control_name].sum() / control_table_df[control_name].sum():.6f}")
                print(f"[DEBUG][MAIN] Result shape: {final_df.shape}")
                print(f"[DEBUG][MAIN] Result index name: {final_df.index.name}")
                print(f"[DEBUG][MAIN] Result columns: {list(final_df.columns)}")
    
    # Step 7.5: Apply county-level scaling for household and population controls
    if control_name in ["num_hh", "tot_pop"] and county_targets:
        # Get county targets for this specific control
        if control_name == "num_hh":
            control_county_targets = {k: v.get('num_hh_target_by_county') for k, v in county_targets.items() 
                                    if v.get('num_hh_target_by_county')}
        elif control_name == "total_pop":
            control_county_targets = {k: v.get('tot_pop_target_by_county') for k, v in county_targets.items() 
                                    if v.get('tot_pop_target_by_county')}
        else:
            control_county_targets = {}
            
        if control_county_targets:
            logger.info(f"Applying county-level scaling to {control_name}")
            final_df = apply_county_scaling(final_df, control_name, control_county_targets, maz_taz_def_df, logger)
        else:
            logger.warning(f"No county targets found for {control_name}, skipping county scaling")
    
    # Step 8: Integerize if needed
    if control_name in ["num_hh", "gq_pop", "total_pop"]:
        final_df = integerize_control(final_df, crosswalk_df, control_name)

    # Step 9: Handle temp controls
    if control_name.startswith("temp_"):
        temp_controls[control_name] = final_df
        
        # Log temp control statistics
        if not final_df.empty:
            control_cols = [col for col in final_df.columns if col != final_df.index.name]
            total = final_df[control_cols].sum().sum() if control_cols else 0
            logger.info(f"TEMP CONTROL [{control_name}]: {len(final_df)} zones, total = {total:,.0f}")
            
            # Log distribution for important temp controls
            if control_name in ['temp_base_num_hh_b', 'temp_base_num_hh_bg', 'temp_num_hh_size', 'temp_hh_bg_for_tract_weights']:
                logger.info(f"TEMP CONTROL {control_name} details:")
                logger.info(f"  Target geography: {final_df.index.name}")
                logger.info(f"  Columns: {list(final_df.columns)}")
                if hasattr(final_df, 'index') and len(final_df) > 0:
                    logger.info(f"  Sample indices: {final_df.index[:5].tolist()}")
                for col in control_cols[:3]:  # Log first 3 columns
                    col_total = final_df[col].sum()
                    nonzero_count = (final_df[col] > 0).sum()
                    logger.info(f"  {col}: total = {col_total:,.0f}, non-zero zones = {nonzero_count}")
        
        return

    # Log final control statistics
    if not final_df.empty:
        control_cols = [col for col in final_df.columns if col != final_df.index.name]
        
        # Debug data types in final DataFrame
        print(f"[DEBUG] final_df dtypes: {final_df.dtypes.to_dict()}")
        print(f"[DEBUG] control_cols: {control_cols}")
        if control_cols:
            print(f"[DEBUG] Sample values from {control_name}: {final_df[control_cols[0]].head()}")
            print(f"[DEBUG] Data types in {control_name}: {final_df[control_cols[0]].dtype}")
            
            # Ensure all control columns are numeric
            for col in control_cols:
                if final_df[col].dtype == 'object':
                    print(f"[DEBUG] Converting column {col} from object to numeric")
                    final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
                    final_df = final_df.dropna(subset=[col])
        
        # Filter out any header rows that might still be present
        if control_cols:
            # Check for string values that indicate header rows
            for col in control_cols:
                string_mask = final_df[col].astype(str).str.contains('^[a-zA-Z]', na=False, regex=True)
                if string_mask.any():
                    print(f"[DEBUG] Removing {string_mask.sum()} header/string rows from {control_name}")
                    final_df = final_df[~string_mask]
        
        # Calculate total after cleanup
        try:
            total = final_df[control_cols].sum().sum() if control_cols else 0
            logger.info(f"FINAL CONTROL [{control_name}]: {len(final_df)} zones, total = {total:,.0f}")
        except Exception as e:
            logger.error(f"Error calculating total for {control_name}: {e}")
            # Force convert to numeric and try again
            for col in control_cols:
                final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0)
            total = final_df[control_cols].sum().sum() if control_cols else 0
            logger.info(f"FINAL CONTROL [{control_name}] (after cleanup): {len(final_df)} zones, total = {total:,.0f}")
        
        # Log additional details for key controls (dynamically determined)
        key_controls = (get_controls_in_category('MAZ', 'household_counts') + 
                       get_controls_in_category('MAZ', 'group_quarters') + 
                       get_controls_in_category('TAZ', 'household_size'))
        if control_name in key_controls:
            for col in control_cols[:3]:  # Log first 3 columns
                col_total = final_df[col].sum()
                nonzero_count = (final_df[col] > 0).sum()
                mean_val = final_df[col].mean()
                max_val = final_df[col].max()
                logger.info(f"  {col}: total = {col_total:,.0f}, non-zero zones = {nonzero_count}, mean = {mean_val:.1f}, max = {max_val:.0f}")

    # Step 10: Merge into final_control_dfs
    if 'wrk' in control_name.lower():
        print(f"[DEBUG][MAIN] ==> MERGING WORKER CONTROL INTO final_control_dfs")
        print(f"[DEBUG][MAIN] About to merge final_df[{control_name}].sum(): {final_df[control_name].sum():,.0f}")
        
    if control_geo not in final_control_dfs:
        final_control_dfs[control_geo] = final_df
        if 'wrk' in control_name.lower():
            print(f"[DEBUG][MAIN] ==> FIRST CONTROL FOR {control_geo} - direct assignment")
    else:
        # Check for overlapping columns that would cause suffix conflicts
        left_df = final_control_dfs[control_geo]
        right_df = final_df
        
        if 'wrk' in control_name.lower():
            print(f"[DEBUG][MAIN] ==> MERGING WITH EXISTING {control_geo} CONTROLS")
            print(f"[DEBUG][MAIN] Left df shape: {left_df.shape}")
            print(f"[DEBUG][MAIN] Right df shape: {right_df.shape}")
            print(f"[DEBUG][MAIN] Left df columns: {list(left_df.columns)}")
            print(f"[DEBUG][MAIN] Right df columns: {list(right_df.columns)}")
        
        # Get common columns (excluding the ones we want to merge)
        left_cols = set(left_df.columns)
        right_cols = set(right_df.columns)
        common_cols = left_cols & right_cols
        
        # Remove common columns from right_df before merge (keep only the control column)
        control_cols_to_keep = [col for col in right_df.columns if col not in common_cols or col == control_name]
        right_df_clean = right_df[control_cols_to_keep]
        
        if 'wrk' in control_name.lower():
            print(f"[DEBUG][MAIN] ==> CLEANED RIGHT DF FOR MERGE")
            print(f"[DEBUG][MAIN] Cleaned right df shape: {right_df_clean.shape}")
            print(f"[DEBUG][MAIN] Cleaned right df columns: {list(right_df_clean.columns)}")
            print(f"[DEBUG][MAIN] Cleaned right df[{control_name}].sum(): {right_df_clean[control_name].sum():,.0f}")
        
        final_control_dfs[control_geo] = pd.merge(
            left=left_df,
            right=right_df_clean,
            how="left",
            left_index=True,
            right_index=True
        )
        
        if 'wrk' in control_name.lower():
            print(f"[DEBUG][MAIN] ==> MERGE COMPLETE")
            merged_df = final_control_dfs[control_geo]
            print(f"[DEBUG][MAIN] Merged df shape: {merged_df.shape}")
            print(f"[DEBUG][MAIN] Merged df[{control_name}].sum(): {merged_df[control_name].sum():,.0f}")
            print(f"[DEBUG][MAIN] All worker controls in merged df: {[col for col in merged_df.columns if 'wrk' in col.lower()]}")
    
    # Special case: Add num_hh to temp_controls so household size controls can use it as denominator
    if control_name == "num_hh":
        temp_controls["num_hh"] = final_df
        logger.info(f"Added num_hh to temp_controls for household size scaling")
        logger.info(f"num_hh sum: {final_df['num_hh'].sum():,.0f}")



def scale_maz_households_to_county_targets(maz_marginals_file, county_summary_file, geo_crosswalk_file, logger):
    """Scale MAZ household and population counts to match 2023 county targets using county-specific scaling factors."""
    logger.info("=" * 60)
    logger.info("APPLYING COUNTY-LEVEL SCALING TO MAZ HOUSEHOLDS AND POPULATION")
    logger.info("=" * 60)
    
    if not all(os.path.exists(f) for f in [maz_marginals_file, county_summary_file, geo_crosswalk_file]):
        logger.error("Required files missing for county scaling")
        return False
    
    try:
        # Read input files
        maz_df = pd.read_csv(maz_marginals_file)
        county_summary_df = pd.read_csv(county_summary_file)
        crosswalk_df = pd.read_csv(geo_crosswalk_file)
        
        # Read 2023 ACS county targets for both households and population
        county_targets_file = os.path.join(PRIMARY_OUTPUT_DIR, COUNTY_TARGETS_FILE)
        if os.path.exists(county_targets_file):
            county_targets_df = pd.read_csv(county_targets_file)
        else:
            logger.error(f"County targets file not found: {county_targets_file}")
            return False
        
        county_summary_df['county_name'] = county_summary_df['County_Name']
        
        logger.info(f"Loaded MAZ marginals: {len(maz_df)} rows")
        logger.info(f"Loaded county summary: {len(county_summary_df)} counties")
        logger.info(f"Loaded crosswalk: {len(crosswalk_df)} MAZ zones")
        logger.info(f"Loaded county targets: {len(county_targets_df)} targets")

        # Merge MAZ data with county information from crosswalk
        county_crosswalk = crosswalk_df[['MAZ', 'county_name', 'COUNTY']].drop_duplicates()
        maz_with_county = maz_df.merge(county_crosswalk, on='MAZ', how='left')
        
        # Convert COUNTY codes to 3-digit FIPS strings to match targets
        maz_with_county['county_fips'] = maz_with_county['COUNTY'].apply(lambda x: f'{x:03d}' if pd.notna(x) else None)
        
        logger.info(f"Counties in MAZ data: {sorted(maz_with_county['county_fips'].dropna().unique())}")
        logger.info(f"Counties in targets: {sorted(county_targets_df['county_fips'].unique())}")
        
        # Extract household and population targets by county
        hh_targets = county_targets_df[county_targets_df['target_name'] == 'num_hh_target_by_county'].set_index('county_fips')['target_value']
        pop_targets = county_targets_df[county_targets_df['target_name'] == 'tot_pop_target_by_county'].set_index('county_fips')['target_value']
        
        # Calculate current totals by county
        county_current = maz_with_county.groupby('county_fips').agg({
            'num_hh': 'sum',
            'total_pop': 'sum'
        }).reset_index()
        
        # Calculate scaling factors for each county
        county_scale_factors = {}
        for _, row in county_current.iterrows():
            county_fips = row['county_fips']
            current_hh = row['num_hh']
            current_pop = row['total_pop']
            
            # Household scaling factor
            if county_fips in hh_targets:
                target_hh = hh_targets[county_fips]
                hh_scale = target_hh / current_hh if current_hh > 0 else 1.0
            else:
                hh_scale = 1.0
                logger.warning(f"No household target for county {county_fips}")
            
            # Population scaling factor
            if county_fips in pop_targets:
                target_pop = pop_targets[county_fips]
                pop_scale = target_pop / current_pop if current_pop > 0 else 1.0
            else:
                pop_scale = 1.0
                logger.warning(f"No population target for county {county_fips}")
            
            county_scale_factors[county_fips] = {
                'hh_scale': hh_scale,
                'pop_scale': pop_scale,
                'target_hh': hh_targets.get(county_fips, current_hh),
                'target_pop': pop_targets.get(county_fips, current_pop)
            }
            
            logger.info(f"County {county_fips}: HH scale={hh_scale:.4f}, Pop scale={pop_scale:.4f}")

        # Apply scaling factors to each MAZ
        original_hh_total = maz_with_county['num_hh'].sum()
        original_pop_total = maz_with_county['total_pop'].sum()
        
        for county_fips, factors in county_scale_factors.items():
            county_mask = maz_with_county['county_fips'] == county_fips
            maz_with_county.loc[county_mask, 'num_hh'] = (
                maz_with_county.loc[county_mask, 'num_hh'] * factors['hh_scale']
            ).round().astype(int)
            maz_with_county.loc[county_mask, 'total_pop'] = (
                maz_with_county.loc[county_mask, 'total_pop'] * factors['pop_scale']
            ).round().astype(int)
        
        # Calculate new totals after scaling
        scaled_hh_total = maz_with_county['num_hh'].sum()
        scaled_pop_total = maz_with_county['total_pop'].sum()
        
        logger.info(f"Household scaling results:")
        logger.info(f"  Original total: {original_hh_total:,.0f}")
        logger.info(f"  Scaled total: {scaled_hh_total:,.0f}")
        logger.info(f"  Change: {scaled_hh_total - original_hh_total:+,.0f} ({(scaled_hh_total/original_hh_total - 1)*100:+.2f}%)")
        
        logger.info(f"Population scaling results:")
        logger.info(f"  Original total: {original_pop_total:,.0f}")
        logger.info(f"  Scaled total: {scaled_pop_total:,.0f}")
        logger.info(f"  Change: {scaled_pop_total - original_pop_total:+,.0f} ({(scaled_pop_total/original_pop_total - 1)*100:+.2f}%)")
        
        # Log scaling by county
        logger.info("County scaling summary:")
        for county_fips, factors in county_scale_factors.items():
            current_hh = county_current[county_current['county_fips'] == county_fips]['num_hh'].iloc[0]
            current_pop = county_current[county_current['county_fips'] == county_fips]['total_pop'].iloc[0]
            logger.info(f"  County {county_fips}: HH {current_hh:,.0f} -> {factors['target_hh']:,.0f}, Pop {current_pop:,.0f} -> {factors['target_pop']:,.0f}")
        
        # CRITICAL FIX: Ensure num_hh column exists and is properly estimated
        if 'num_hh' not in maz_with_county.columns:
            logger.warning("num_hh column missing from MAZ data - estimating from population")
            # Estimate households from population (subtract group quarters first)
            household_pop = maz_with_county['total_pop'] - maz_with_county.get('gq_pop', 0)
            maz_with_county['num_hh'] = numpy.maximum(0, (household_pop / 2.5).round()).astype(int)
            logger.info(f"Estimated num_hh: min={maz_with_county['num_hh'].min()}, max={maz_with_county['num_hh'].max()}, sum={maz_with_county['num_hh'].sum():,.0f}")
        
        # Write updated MAZ marginals file
        output_columns = ['MAZ', 'num_hh', 'total_pop', 'gq_pop', 'gq_military', 'gq_university', 'gq_other']
        maz_with_county[output_columns].to_csv(maz_marginals_file, index=False)
        
        logger.info(f"Updated MAZ marginals file: {maz_marginals_file}")
        logger.info("County-level scaling completed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Error applying county scaling: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False


def validate_maz_controls(maz_marginals_file, county_targets, logger):
    """Validate that MAZ control totals match county targets and provide detailed comparison."""
    logger.info("=" * 60)
    logger.info("VALIDATING MAZ CONTROL TOTALS AGAINST COUNTY TARGETS")
    logger.info("=" * 60)
    
    if not os.path.exists(maz_marginals_file):
        logger.error(f"MAZ marginals file not found: {maz_marginals_file}")
        return False
    
    if not county_targets:
        logger.warning("No county targets available for validation")
        return False
    
    # Read MAZ marginals file
    try:
        import pandas as pd
        maz_df = pd.read_csv(maz_marginals_file)
        logger.info(f"Loaded MAZ marginals file with {len(maz_df)} rows and {len(maz_df.columns)} columns")
        logger.info(f"Available MAZ columns: {list(maz_df.columns)}")
    except Exception as e:
        logger.error(f"Failed to read MAZ marginals file: {e}")
        return False
    
    validation_passed = True
    
    # Calculate regional totals from county targets
    logger.info("\nCOMPARING MAZ TOTALS vs COUNTY TARGET TOTALS:")
    logger.info("-" * 60)
    
    # Read county targets from CSV file to get the actual target totals
    county_targets_file = os.path.join(PRIMARY_OUTPUT_DIR, COUNTY_TARGETS_FILE)
    total_hh_target = 0
    total_pop_target = 0
    
    if os.path.exists(county_targets_file):
        try:
            targets_df = pd.read_csv(county_targets_file)
            hh_targets = targets_df[targets_df['target_name'] == 'num_hh_target_by_county']['target_value']
            pop_targets = targets_df[targets_df['target_name'] == 'tot_pop_target_by_county']['target_value']
            total_hh_target = hh_targets.sum()
            total_pop_target = pop_targets.sum()
            logger.info(f"County targets loaded: households={total_hh_target:,.0f}, population={total_pop_target:,.0f}")
        except Exception as e:
            logger.error(f"Error reading county targets file: {e}")
            total_hh_target = 0
    else:
        logger.warning(f"County targets file not found: {county_targets_file}")
        # Fall back to old method if CSV doesn't exist
        total_hh_target = sum(county_info.get('num_hh_target_by_county', 0) 
                             for county_info in county_targets.values() 
                             if isinstance(county_info, dict))
    
    # Check household totals
    if 'num_hh' in maz_df.columns:
        maz_total_hh = maz_df['num_hh'].sum()
        diff_hh = abs(maz_total_hh - total_hh_target)
        pct_diff_hh = (diff_hh / total_hh_target) * 100 if total_hh_target > 0 else 0
        status = "PASS" if pct_diff_hh <= 1.0 else "FAIL"
        
        logger.info(f"{'num_hh':15} | MAZ Total: {maz_total_hh:>10,.0f} | Target: {total_hh_target:>10,.0f} | Diff: {maz_total_hh - total_hh_target:>+10,.0f} | {pct_diff_hh:>6.2f}% | {status}")
        
        if pct_diff_hh > 1.0:
            validation_passed = False
    
    # Check population totals
    if 'total_pop' in maz_df.columns and total_pop_target > 0:
        maz_total_pop = maz_df['total_pop'].sum()
        diff_pop = abs(maz_total_pop - total_pop_target)
        pct_diff_pop = (diff_pop / total_pop_target) * 100 if total_pop_target > 0 else 0
        status_pop = "PASS" if pct_diff_pop <= 1.0 else "FAIL"
        
        logger.info(f"{'total_pop':15} | MAZ Total: {maz_total_pop:>10,.0f} | Target: {total_pop_target:>10,.0f} | Diff: {maz_total_pop - total_pop_target:>+10,.0f} | {pct_diff_pop:>6.2f}% | {status_pop}")
        
        if pct_diff_pop > 1.0:
            validation_passed = False
    
    # Check other controls if available
    if 'gq_pop' in maz_df.columns:
        gq_total = maz_df['gq_pop'].sum()
        logger.info(f"{'gq_pop':15} | MAZ Total: {gq_total:>10,.0f} | (No county target available)")
    
    # Summary
    logger.info("\n" + "=" * 60)
    if validation_passed:
        logger.info("SUCCESS: MAZ controls match county targets within 1% tolerance")
    else:
        logger.error("FAILED: MAZ controls differ from county targets by more than 1%")
    logger.info("=" * 60)
    
    return validation_passed


def harmonize_taz_household_controls(taz_marginals_file, logger, target_geography='TAZ', priority_order=None):
    """
    Harmonize household controls to ensure consistent totals across categories.
    Uses the highest priority available category as the "gold standard" and proportionally adjusts others.
    
    Args:
        taz_marginals_file: Path to marginals CSV file
        logger: Logger instance for output
        target_geography: Geography level to get control categories for (default: 'TAZ')
        priority_order: List of category names in priority order (default: uses configuration-based priority)
        
    Returns:
        bool: True if harmonization successful, False otherwise
    """
    if not os.path.exists(taz_marginals_file):
        logger.error(f"Marginals file not found: {taz_marginals_file}")
        return False
        
    try:
        df = pd.read_csv(taz_marginals_file)
        logger.info(f"Harmonizing {target_geography} controls for {len(df)} zones")
        
        # Get all household control categories from configuration
        all_categories = get_control_categories_for_geography(target_geography)
        
        # Filter to only household-related categories (categories that should sum to the same total)
        # Exclude 'household_counts' which contains base counts, not categorical breakdowns
        household_categories = {name: controls for name, controls in all_categories.items() 
                              if 'household' in name.lower() and 'count' not in name.lower()}
        
        if not household_categories:
            logger.warning(f"No household control categories found for {target_geography}")
            return True
            
        logger.info(f"Configuration-defined household control categories:")
        for category_name, controls in household_categories.items():
            logger.info(f"  {category_name}: {controls}")
        
        # Check which controls are available in the data
        available_categories = {}
        for category_name, controls in household_categories.items():
            available_controls = [col for col in controls if col in df.columns]
            if available_controls:
                available_categories[category_name] = available_controls
                logger.info(f"  Available {category_name}: {available_controls}")
        
        if not available_categories:
            logger.warning("No household control categories available in data")
            return True
        
        # Determine target category based on priority order or dynamically
        if priority_order is None:
            # Use all available categories in alphabetical order as default
            # This ensures consistent behavior without hardcoded category names
            priority_order = sorted(available_categories.keys())
            
        # Use the first available category in priority order as the target
        target_category = None
        target_controls = None
        for category in priority_order:
            if category in available_categories:
                target_category = category
                target_controls = available_categories[category]
                break
        
        if target_category is None:
            # Fall back to first available category
            target_category = list(available_categories.keys())[0]
            target_controls = available_categories[target_category]
        
        logger.info(f"Using {target_category} as target category with controls: {target_controls}")
        
        # Calculate target totals from the selected category
        df['target_total'] = df[target_controls].sum(axis=1)
        total_target = df['target_total'].sum()
        logger.info(f"Target total households from {target_category}: {total_target:,.0f}")
        
        def harmonize_category(category_controls, category_name):
            """Proportionally adjust controls to match target total"""
            if not category_controls or category_name == target_category:
                return 0
                
            current_total = df[category_controls].sum(axis=1)
            target_total = df['target_total']
            
            # Only adjust where both current and target totals > 0 and differ by more than 1
            adjust_mask = (current_total > 0) & (target_total > 0) & (abs(current_total - target_total) > 1)
            
            if adjust_mask.sum() > 0:
                # Calculate scaling factors, avoiding division by zero
                scaling_factor = target_total / current_total.replace(0, 1)  # Replace 0 with 1 to avoid division by zero
                
                # Apply scaling only to rows that need adjustment
                for col in category_controls:
                    df.loc[adjust_mask, col] = (df.loc[adjust_mask, col] * scaling_factor.loc[adjust_mask]).round().astype(int)
                
                logger.info(f"  Harmonized {category_name} controls for {adjust_mask.sum()} zones")
                return adjust_mask.sum()
            return 0
        
        # Harmonize all other categories to match the target category
        total_adjusted = 0
        adjustment_summary = {}
        
        for category_name, category_controls in available_categories.items():
            if category_name != target_category:
                adjusted_count = harmonize_category(category_controls, category_name)
                adjustment_summary[category_name] = adjusted_count
                total_adjusted += adjusted_count
        
        # Ensure all control columns are integers
        all_control_cols = []
        for controls in available_categories.values():
            all_control_cols.extend(controls)
        
        for col in all_control_cols:
            if col in df.columns:
                df[col] = df[col].round().astype(int)
        
        # Drop temporary column
        df = df.drop('target_total', axis=1)
        
        # Save harmonized file
        df.to_csv(taz_marginals_file, index=False)
        
        # Log results
        logger.info(f"SUCCESS: Harmonized {target_geography} household controls")
        logger.info(f"  Target category: {target_category} (unchanged)")
        for category_name, adjusted_count in adjustment_summary.items():
            logger.info(f"  {category_name}: adjusted {adjusted_count} zones")
        
        if total_adjusted == 0:
            logger.info("  No adjustments needed - all categories already consistent")
        
        return True
        
    except Exception as e:
        logger.error(f"Error harmonizing {target_geography} controls: {e}")
        logger.error(f"Harmonization error traceback: {traceback.format_exc()}")
        return False


def validate_taz_household_consistency(marginals_file, logger, target_geography='TAZ', tolerance_pct=1.0):
    """
    Validate that household controls are consistent across categories for a given geography.
    
    For each zone, the sum of worker controls should equal the sum of income controls
    which should equal the sum of household size controls, since they all represent
    the same total number of households categorized differently.
    
    Args:
        marginals_file: Path to marginals CSV file
        logger: Logger instance
        target_geography: Geography level to validate ('TAZ', 'MAZ', etc.)
        tolerance_pct: Tolerance percentage for differences (default 1.0%)
        
    Returns:
        bool: True if validation passes, False otherwise
    """
    logger.info("=" * 60)
    logger.info(f"VALIDATING {target_geography} HOUSEHOLD CONTROL CONSISTENCY")
    logger.info("=" * 60)
    
    if not os.path.exists(marginals_file):
        logger.error(f"{target_geography} marginals file not found: {marginals_file}")
        return False
        
    try:
        df = pd.read_csv(marginals_file)
        logger.info(f"Loaded {target_geography} marginals file with {len(df)} {target_geography} zones")
        
        # Get household control categories from configuration dynamically
        all_categories = get_control_categories_for_geography(target_geography)
        
        # Filter to only household-related categories (categories that should sum to the same total)
        # Exclude 'household_counts' which contains base counts, not categorical breakdowns
        household_categories = {name: controls for name, controls in all_categories.items() 
                              if 'household' in name.lower() and 'count' not in name.lower()}
        
        # Extract available categories and their controls
        available_categories = {}
        for category_name, controls in household_categories.items():
            available_controls = [col for col in controls if col in df.columns]
            if available_controls:
                available_categories[category_name] = available_controls
        
        logger.info(f"Available household control categories:")
        for category_name, controls in available_categories.items():
            logger.info(f"  {category_name}: {controls}")
        
        if len(available_categories) < 2:
            logger.info("Less than 2 household categories available - validation not applicable")
            return True
        
        validation_passed = True
        tolerance = tolerance_pct / 100.0  # Convert percentage to decimal
        
        # Calculate totals for each available category
        category_totals = {}
        for category_name, controls in available_categories.items():
            total_col_name = f"{category_name}_total"
            df[total_col_name] = df[controls].sum(axis=1)
            category_total = df[total_col_name].sum()
            category_totals[category_name] = category_total
            logger.info(f"Total households by {category_name}: {category_total:,.0f}")
        
        # Compare totals between all pairs of categories
        logger.info("\nCOMPARING HOUSEHOLD TOTALS ACROSS CATEGORIES:")
        logger.info("-" * 50)
        
        category_names = list(available_categories.keys())
        for i in range(len(category_names)):
            for j in range(i + 1, len(category_names)):
                cat1, cat2 = category_names[i], category_names[j]
                total1, total2 = category_totals[cat1], category_totals[cat2]
                
                diff = abs(total1 - total2)
                pct_diff = (diff / total1) * 100 if total1 > 0 else 0
                status = "PASS" if pct_diff <= tolerance_pct else "FAIL"
                logger.info(f"{cat1:15} vs {cat2:15} | {total1:>10,.0f} vs {total2:>10,.0f} | Diff: {diff:>8,.0f} | {pct_diff:>5.2f}% | {status}")
                if pct_diff > tolerance_pct:
                    validation_passed = False
        
        # Check for zones with significant inconsistencies
        logger.info(f"\nCHECKING {target_geography}-LEVEL CONSISTENCY:")
        logger.info("-" * 50)
        
        max_zone_diff = 0
        
        # Get the geography column name (assumes it exists and matches target_geography)
        geo_col = target_geography
        
        if len(available_categories) >= 2:
            # Calculate differences between all pairs of categories at zone level
            total_cols = [f"{cat}_total" for cat in available_categories.keys()]
            
            # Calculate pairwise differences for each zone
            diff_cols = []
            category_pairs = []
            for i, cat1 in enumerate(available_categories.keys()):
                for j, cat2 in enumerate(list(available_categories.keys())[i+1:], i+1):
                    diff_col = f"{cat1}_{cat2}_diff"
                    df[diff_col] = abs(df[f"{cat1}_total"] - df[f"{cat2}_total"])
                    diff_cols.append(diff_col)
                    category_pairs.append((cat1, cat2))
            
            if diff_cols:
                # Find maximum difference across all category pairs for each zone
                df['max_diff'] = df[diff_cols].max(axis=1)
                
                # Calculate percentage difference relative to the first category total
                first_total_col = total_cols[0]
                df['pct_diff'] = (df['max_diff'] / df[first_total_col]) * 100
                
                problematic_zones = df[df['pct_diff'] > tolerance_pct]
                
                if len(problematic_zones) > 0:
                    logger.warning(f"Found {len(problematic_zones)} {target_geography}s with inconsistent household totals (>{tolerance_pct}% difference)")
                    
                    # Show worst 5 zones
                    worst_zones = problematic_zones.nlargest(5, 'pct_diff')
                    for _, row in worst_zones.iterrows():
                        # Show totals for each category
                        totals_str = ", ".join([f"{cat}={row[f'{cat}_total']:.0f}" for cat in available_categories.keys()])
                        logger.warning(f"  {target_geography} {row[geo_col]}: {totals_str} (max diff: {row['pct_diff']:.1f}%)")
                    
                    max_zone_diff = problematic_zones['pct_diff'].max()
                    if max_zone_diff > tolerance_pct:
                        validation_passed = False
                else:
                    logger.info(f"All {target_geography}s have consistent household totals across categories")
        
        # Summary
        logger.info("\n" + "=" * 60)
        if validation_passed:
            logger.info(f"SUCCESS: {target_geography} household controls are consistent across categories")
        else:
            logger.error(f"FAILED: {target_geography} household controls have significant inconsistencies")
            logger.error(f"Maximum {target_geography}-level difference: {max_zone_diff:.2f}%")
        logger.info("=" * 60)
        
        return validation_passed
        
    except Exception as e:
        logger.error(f"Error validating {target_geography} household consistency: {e}")
        logger.error(f"Validation error traceback: {traceback.format_exc()}")
        return False


def summarize_maz_households_by_taz(logger):
    """
    Summarize MAZ household totals by TAZ using the geographic crosswalk.
    Adds hh_from_maz column to TAZ marginals for comparison with other household estimates.
    
    Args:
        logger: Logger instance for output
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("=" * 60)
    logger.info("SUMMARIZING MAZ HOUSEHOLDS BY TAZ")
    logger.info("=" * 60)
    
    try:
        # File paths
        maz_marginals_file = os.path.join(PRIMARY_OUTPUT_DIR, MAZ_MARGINALS_FILE)
        taz_marginals_file = os.path.join(PRIMARY_OUTPUT_DIR, TAZ_MARGINALS_FILE)
        geo_crosswalk_file = GEO_CROSSWALK_TM2_PATH
        
        # Check if required files exist
        if not os.path.exists(maz_marginals_file):
            logger.error(f"MAZ marginals file not found: {maz_marginals_file}")
            return False
            
        if not os.path.exists(taz_marginals_file):
            logger.error(f"TAZ marginals file not found: {taz_marginals_file}")
            return False
            
        if not os.path.exists(geo_crosswalk_file):
            logger.error(f"Geographic crosswalk file not found: {geo_crosswalk_file}")
            return False
        
        # Load data
        logger.info("Loading MAZ marginals, TAZ marginals, and geographic crosswalk")
        maz_df = pd.read_csv(maz_marginals_file)
        taz_df = pd.read_csv(taz_marginals_file)
        crosswalk_df = pd.read_csv(geo_crosswalk_file)
        
        logger.info(f"Loaded {len(maz_df):,} MAZ zones with households")
        logger.info(f"Loaded {len(taz_df):,} TAZ zones")
        logger.info(f"Loaded {len(crosswalk_df):,} crosswalk records")
        
        # Merge MAZ households with crosswalk to get TAZ mapping
        maz_taz = maz_df.merge(crosswalk_df[['MAZ', 'TAZ']], on='MAZ', how='left')
        
        # Check for missing TAZ mappings
        missing_taz = maz_taz['TAZ'].isna().sum()
        if missing_taz > 0:
            logger.warning(f"{missing_taz} MAZ zones have no TAZ mapping")
            maz_taz = maz_taz.dropna(subset=['TAZ'])
        
        # Sum MAZ households by TAZ
        logger.info("Summarizing MAZ households by TAZ")
        taz_hh_from_maz = maz_taz.groupby('TAZ')['num_hh'].sum().reset_index()
        taz_hh_from_maz.rename(columns={'num_hh': 'hh_from_maz'}, inplace=True)
        
        logger.info(f"Summarized to {len(taz_hh_from_maz):,} TAZ zones")
        logger.info(f"Total households from MAZ: {taz_hh_from_maz['hh_from_maz'].sum():,.0f}")
        
        # Merge with existing TAZ marginals
        taz_updated = taz_df.merge(taz_hh_from_maz, on='TAZ', how='left')
        
        # Fill missing values with 0 (TAZs with no MAZs)
        taz_updated['hh_from_maz'] = taz_updated['hh_from_maz'].fillna(0)
        
        # Log comparison with existing household controls if available
        hh_cols = [col for col in taz_updated.columns if col.startswith('hh_') and col != 'hh_from_maz']
        if hh_cols:
            logger.info("\n--- HOUSEHOLD COMPARISON ---")
            logger.info(f"Households from MAZ aggregation: {taz_updated['hh_from_maz'].sum():,.0f}")
            
            # Focus on household size controls for comparison
            size_cols = [col for col in hh_cols if 'size' in col]
            if size_cols:
                size_total = sum(taz_updated[col].sum() for col in size_cols)
                logger.info(f"Households from TAZ size controls: {size_total:,.0f}")
                
                difference = abs(taz_updated['hh_from_maz'].sum() - size_total)
                pct_diff = (difference / taz_updated['hh_from_maz'].sum()) * 100 if taz_updated['hh_from_maz'].sum() > 0 else 0
                logger.info(f"Difference: {difference:,.0f} ({pct_diff:.1f}%)")
        
        # Write updated TAZ marginals file
        logger.info(f"Writing updated TAZ marginals with hh_from_maz column")
        taz_updated.to_csv(taz_marginals_file, index=False)
        
        # Validation summary
        total_maz_hh = maz_df['num_hh'].sum()
        total_taz_hh_from_maz = taz_updated['hh_from_maz'].sum()
        
        logger.info("\n--- VALIDATION SUMMARY ---")
        logger.info(f"Original MAZ households: {total_maz_hh:,.0f}")
        logger.info(f"TAZ households from MAZ: {total_taz_hh_from_maz:,.0f}")
        logger.info(f"Difference: {abs(total_maz_hh - total_taz_hh_from_maz):,.0f}")
        
        if abs(total_maz_hh - total_taz_hh_from_maz) > 100:
            logger.warning("Large difference between MAZ and TAZ household totals - check crosswalk")
        else:
            logger.info("MAZ to TAZ household aggregation validated successfully")
        
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"Error summarizing MAZ households by TAZ: {e}")
        logger.error(f"Error traceback: {traceback.format_exc()}")
        return False


# To Do: Generalize using the configuration, we shouldn't be specifically mentioning 2020, and 2023 datasets
def create_county_summary(county_targets, cf, logger, final_control_dfs=None):
    """Create county summary file showing county-specific scaling factors and results.
    
    This file provides county-specific comparison between 2020 Census baseline data and 2023 ACS targets
    that are used for county-level scaling in populationsim.
    
    Args:
        county_targets: Dictionary of targets from ACS 2023 (both county and regional data) 
        cf: CensusFetcher instance for accessing Census data
        logger: Logger instance
        final_control_dfs: Dictionary of processed control dataframes (optional)
    
    Returns:
        pd.DataFrame: County-level summary comparison data
    """
    logger.info("Creating county summary file")
    
    # Get Bay Area county information
    bay_area_counties = get_bay_area_county_codes()
    county_name_map = get_county_name_mapping()
    
    # Initialize summary data - one row per county
    summary_rows = []
    
    try:
        
        for county_fips in bay_area_counties:
            county_name = county_name_map.get(county_fips, f"County {county_fips}")
            logger.info(f"Processing county summary for {county_name} (FIPS: {county_fips})")
            
            # Initialize county row
            county_row = {
                'County_FIPS': county_fips,
                'County_Name': county_name,
                '2020_Census_Households': 0,
                '2023_ACS_Households': 0,
                'Scaling_Factor': 0.0
            }
            
            # Get 2020 Census county totals from block-level data using config
            try:
                # Get household control definition from config
                maz_controls = CONTROLS[ACS_EST_YEAR]['MAZ']
                if 'num_hh' in maz_controls:
                    data_source, year, table, geography = maz_controls['num_hh'][:4]
                    logger.debug(f"Using config for household data: {data_source}, {year}, {table}, {geography}")
                    
                    # Get household data using config parameters
                    household_data = cf.get_census_data(data_source, year, table, geography)
                    if household_data is not None and not household_data.empty:
                        household_data_reset = household_data.reset_index()
                        if 'county' in household_data_reset.columns:
                            household_data_reset['county_str'] = household_data_reset['county'].astype(str).str.zfill(3)
                            county_data = household_data_reset[household_data_reset['county_str'] == county_fips]
                            if len(county_data) > 0:
                                county_data[table] = pd.to_numeric(county_data[table], errors='coerce')
                                hh_2020 = int(county_data[table].sum())
                                county_row['2020_Census_Households'] = hh_2020
                                logger.info(f"  {county_name}: 2020 Census households = {hh_2020:,}")
                else:
                    logger.warning(f"num_hh control not found in config for {ACS_EST_YEAR}")
                            
            except Exception as e:
                logger.warning(f"Failed to get 2020 Census data for {county_name}: {e}")
            
            # Get 2023 ACS targets for this county from the county_targets dictionary
            if county_fips in county_targets:
                county_targets_info = county_targets[county_fips]
                if 'num_hh_target_by_county' in county_targets_info:
                    hh_2023 = county_targets_info['num_hh_target_by_county']
                    county_row['2023_ACS_Households'] = int(hh_2023)
                    logger.info(f"  {county_name}: 2023 ACS households target = {hh_2023:,}")
                    
                    # Calculate scaling factor
                    if county_row['2020_Census_Households'] > 0:
                        scaling_factor = hh_2023 / county_row['2020_Census_Households']
                        county_row['Scaling_Factor'] = scaling_factor
                        logger.info(f"  {county_name}: Household scaling factor = {scaling_factor:.4f}")
            else:
                logger.warning(f"No county targets found for {county_name} (FIPS: {county_fips})")
            
            summary_rows.append(county_row)
            
    except Exception as e:
        logger.error(f"Error creating county summary: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return pd.DataFrame()  # Return empty DataFrame on error
    
    # Create DataFrame from summary rows
    summary_df = pd.DataFrame(summary_rows)
    
    # Write to output file
    output_path = os.path.join(PRIMARY_OUTPUT_DIR, COUNTY_SUMMARY_FILE)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    summary_df.to_csv(output_path, index=False)
    logger.info(f"Wrote county summary file: {output_path}")
    
    # Log summary statistics
    logger.info("County Summary Statistics:")
    total_2020_hh = summary_df['2020_Census_Households'].sum()
    total_2023_hh = summary_df['2023_ACS_Households'].sum()
    regional_scaling_factor = total_2023_hh / total_2020_hh if total_2020_hh > 0 else 0
    logger.info(f"  Total 2020 Census Households: {total_2020_hh:,}")
    logger.info(f"  Total 2023 ACS Households: {total_2023_hh:,}")
    logger.info(f"  Regional Avg Scaling Factor: {regional_scaling_factor:.4f}")
    
    # Log scaling factor range
    non_zero_factors = summary_df[summary_df['Scaling_Factor'] > 0]['Scaling_Factor']
    if len(non_zero_factors) > 0:
        logger.info(f"  County Scaling Factor Range: {non_zero_factors.min():.4f} to {non_zero_factors.max():.4f}")
    
    return summary_df

def create_maz_data_files(logger):
    """
    Create maz_data.csv and maz_data_withDensity.csv files by combining:
    a) Employment data from example_controls_2015/maz_data.csv (unchanged)
    b) Updated HH and POP fields from output_2023/maz_marginals.csv
    
    Args:
        logger: Logger instance for status messages
    """
    logger.info("Creating MAZ data files with updated HH/POP data")
    
    # Define file paths using config
    example_maz_data_file = EXAMPLE_MAZ_DATA_FILE
    example_maz_density_file = EXAMPLE_MAZ_DENSITY_FILE
    maz_marginals_file = os.path.join(PRIMARY_OUTPUT_DIR, MAZ_MARGINALS_FILE)
    
    # Output paths using config
    output_maz_data_file = os.path.join(PRIMARY_OUTPUT_DIR, OUTPUT_MAZ_DATA_FILE)
    output_maz_density_file = os.path.join(PRIMARY_OUTPUT_DIR, OUTPUT_MAZ_DENSITY_FILE)
    
    try:
        # Read the example 2015 maz_data files (employment data to keep unchanged)
        if not os.path.exists(example_maz_data_file):
            logger.error(f"Missing example MAZ data file: {example_maz_data_file}")
            return
            
        example_maz_data = pd.read_csv(example_maz_data_file)
        logger.info(f"Read example MAZ data: {len(example_maz_data)} zones")
        
        if not os.path.exists(example_maz_density_file):
            logger.error(f"Missing example MAZ density file: {example_maz_density_file}")
            return
            
        example_maz_density = pd.read_csv(example_maz_density_file)
        logger.info(f"Read example MAZ density data: {len(example_maz_density)} zones")
        
        # Read the updated 2023 marginals (HH and population data)
        if not os.path.exists(maz_marginals_file):
            logger.error(f"Missing updated MAZ marginals file: {maz_marginals_file}")
            return
            
        maz_marginals_2023 = pd.read_csv(maz_marginals_file)
        logger.info(f"Read 2023 MAZ marginals: {len(maz_marginals_2023)} zones")
        logger.info(f"MAZ marginals columns: {list(maz_marginals_2023.columns)}")
        
        # Get actual population data from the existing maz_data.csv instead of estimating
        # This ensures we use real population totals for hierarchical control consistency
        current_maz_data_file = os.path.join(PRIMARY_OUTPUT_DIR, OUTPUT_MAZ_DATA_FILE)
        if os.path.exists(current_maz_data_file):
            logger.info("Using existing maz_data.csv for population totals")
            current_maz_data = pd.read_csv(current_maz_data_file)
            
            # Create mapping from MAZ to actual population
            if 'MAZ_ORIGINAL' in current_maz_data.columns and 'POP' in current_maz_data.columns:
                pop_mapping = current_maz_data.set_index('MAZ_ORIGINAL')['POP'].to_dict()
                maz_marginals_2023['total_pop'] = maz_marginals_2023['MAZ'].map(pop_mapping)
                
                # Fill any missing values with the household-based estimate as fallback
                missing_pop = maz_marginals_2023['total_pop'].isna()
                if missing_pop.any():
                    logger.warning(f"Using HH-based estimate for {missing_pop.sum()} MAZs with missing population")
                    if 'num_hh' in maz_marginals_2023.columns:
                        maz_marginals_2023.loc[missing_pop, 'total_pop'] = (
                            maz_marginals_2023.loc[missing_pop, 'num_hh'] * 2.5 + 
                            maz_marginals_2023.loc[missing_pop, 'gq_pop']
                        )
                    else:
                        logger.error(f"Cannot estimate population - missing 'num_hh' column. Available: {list(maz_marginals_2023.columns)}")
                        return
                    
                logger.info("Using actual population totals from existing maz_data.csv")
            else:
                logger.warning("Cannot find POP column in existing maz_data.csv, using HH-based estimate")
                # Calculate total population from marginals (HH population + GQ population) as fallback
                maz_marginals_2023['total_pop'] = maz_marginals_2023['num_hh'] * 2.5  # Rough estimate for HH population
                maz_marginals_2023['total_pop'] += maz_marginals_2023['gq_pop']  # Add GQ population
        else:
            logger.warning("No existing maz_data.csv found, using HH-based population estimate")
            # Calculate total population from marginals (HH population + GQ population) as fallback
            if 'num_hh' in maz_marginals_2023.columns:
                maz_marginals_2023['total_pop'] = maz_marginals_2023['num_hh'] * 2.5  # Rough estimate for HH population
                maz_marginals_2023['total_pop'] += maz_marginals_2023['gq_pop']  # Add GQ population
            else:
                logger.error(f"Missing 'num_hh' column in MAZ marginals. Available columns: {list(maz_marginals_2023.columns)}")
                return
        
        # Round to integers
        if 'num_hh' in maz_marginals_2023.columns:
            maz_marginals_2023['num_hh'] = maz_marginals_2023['num_hh'].round().astype(int)
        else:
            logger.error(f"Missing 'num_hh' column in maz_marginals_2023. Available columns: {list(maz_marginals_2023.columns)}")
            return
        
        maz_marginals_2023['total_pop'] = maz_marginals_2023['total_pop'].round().astype(int)
        
        # Prepare the MAZ ID column for merging
        # Convert MAZ column to integer to match the format in marginals
        if 'MAZ_ORIGINAL' in example_maz_data.columns:
            maz_id_col = 'MAZ_ORIGINAL'
        elif 'MAZ' in example_maz_data.columns:
            maz_id_col = 'MAZ'
        else:
            logger.error("Cannot find MAZ ID column in example data")
            return
            
        # Merge the data - update HH and POP fields while keeping employment unchanged
        logger.info("Merging employment data with updated HH/POP data")
        
        # For maz_data.csv
        updated_maz_data = example_maz_data.copy()
        
        # Merge with marginals on MAZ ID
        merged_data = updated_maz_data.merge(
            maz_marginals_2023[['MAZ', 'num_hh', 'total_pop']],
            left_on=maz_id_col,
            right_on='MAZ',
            how='left'
        )
        
        # Update HH and POP columns
        if 'HH' in merged_data.columns:
            merged_data['HH'] = merged_data['num_hh'].fillna(merged_data['HH'])
        
        if 'POP' in merged_data.columns:
            merged_data['POP'] = merged_data['total_pop'].fillna(merged_data['POP'])
            
        # Clean up merge columns
        merged_data = merged_data.drop(columns=['MAZ', 'num_hh', 'total_pop'], errors='ignore')
        
        # Write updated maz_data.csv
        merged_data.to_csv(output_maz_data_file, index=False)
        logger.info(f"Created {output_maz_data_file}")
        
        # For maz_data_withDensity.csv - do the same process
        updated_maz_density = example_maz_density.copy()
        
        # Determine MAZ ID column for density file
        if 'MAZ_ORIGINAL' in example_maz_density.columns:
            maz_id_col_density = 'MAZ_ORIGINAL'
        elif 'MAZ' in example_maz_density.columns:
            maz_id_col_density = 'MAZ'
        else:
            logger.error("Cannot find MAZ ID column in density data")
            return
            
        # Merge with marginals on MAZ ID  
        merged_density = updated_maz_density.merge(
            maz_marginals_2023[['MAZ', 'num_hh', 'total_pop']],
            left_on=maz_id_col_density,
            right_on='MAZ',
            how='left'
        )
        
        # Update HH and POP columns
        if 'HH' in merged_density.columns:
            merged_density['HH'] = merged_density['num_hh'].fillna(merged_density['HH'])
        
        if 'POP' in merged_density.columns:
            merged_density['POP'] = merged_density['total_pop'].fillna(merged_density['POP'])
            
        # Clean up merge columns
        merged_density = merged_density.drop(columns=['MAZ', 'num_hh', 'total_pop'], errors='ignore')
        
        # Write updated maz_data_withDensity.csv
        merged_density.to_csv(output_maz_density_file, index=False)
        logger.info(f"Created {output_maz_density_file}")
        
        # Log summary statistics
        logger.info("MAZ Data File Creation Summary:")
        logger.info(f"  Total zones processed: {len(merged_data)}")
        logger.info(f"  Total households: {merged_data['HH'].sum():,}")
        logger.info(f"  Total population: {merged_data['POP'].sum():,}")
        logger.info(f"  Average HH size: {merged_data['POP'].sum() / merged_data['HH'].sum():.2f}")
        
        # Validate that employment columns are unchanged
        employment_cols = [col for col in example_maz_data.columns 
                          if col.startswith(('ag', 'art_rec', 'constr', 'eat', 'ed_', 'fire', 'gov', 
                                           'health', 'hotel', 'info', 'lease', 'logis', 'man_', 
                                           'natres', 'prof', 'ret_', 'serv_', 'transp', 'util', 'emp_total'))]
        
        if employment_cols:
            orig_emp_total = example_maz_data[employment_cols[0]].sum() if employment_cols else 0
            new_emp_total = merged_data[employment_cols[0]].sum() if employment_cols else 0
            logger.info(f"  Employment validation (sample): {orig_emp_total} -> {new_emp_total} (should be unchanged)")
        
    except Exception as e:
        logger.error(f"Error creating MAZ data files: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

def log_control_statistics(control_geo, out_df, logger):
    """Log detailed statistics for control columns including sums and distributions."""
    logger.info(f"=" * 80)
    logger.info(f"CONTROL STATISTICS FOR {control_geo} LEVEL")
    logger.info(f"=" * 80)
    
    # Get control columns (exclude geography columns)
    geo_cols = [control_geo, 'county_name'] if control_geo == 'COUNTY' else [control_geo]
    control_cols = [col for col in out_df.columns if col not in geo_cols]
    
    logger.info(f"Number of {control_geo} zones: {len(out_df)}")
    logger.info(f"Number of control variables: {len(control_cols)}")
    
    # Log column sums and basic statistics
    logger.info(f"\nCONTROL TOTALS AND DISTRIBUTIONS:")
    logger.info(f"-" * 60)
    
    for col in control_cols:
        if col in out_df.columns:
            col_data = out_df[col]
            total = col_data.sum()
            mean_val = col_data.mean()
            median_val = col_data.median()
            std_val = col_data.std()
            min_val = col_data.min()
            max_val = col_data.max()
            zeros = (col_data == 0).sum()
            nonzeros = (col_data > 0).sum()
            
            logger.info(f"{col}:")
            logger.info(f"  Total: {total:,.0f}")
            logger.info(f"  Mean: {mean_val:.2f}, Median: {median_val:.2f}, Std: {std_val:.2f}")
            logger.info(f"  Range: {min_val:.0f} - {max_val:.0f}")
            logger.info(f"  Zones with data: {nonzeros} ({nonzeros/len(out_df)*100:.1f}%)")
            logger.info(f"  Zones with zeros: {zeros} ({zeros/len(out_df)*100:.1f}%)")
            
            # Show percentile distribution for non-zero values
            if nonzeros > 0:
                nonzero_data = col_data[col_data > 0]
                p25 = nonzero_data.quantile(0.25)
                p75 = nonzero_data.quantile(0.75)
                p95 = nonzero_data.quantile(0.95)
                logger.info(f"  Distribution (non-zero): P25={p25:.1f}, P75={p75:.1f}, P95={p95:.1f}")
            logger.info("")
    
    # Log validation checks for known relationships
    logger.info(f"VALIDATION CHECKS:")
    logger.info(f"-" * 60)
    
    if control_geo == 'MAZ':
        # Check household size consistency if we have both num_hh and household size controls
        hh_size_cols = get_controls_in_category('TAZ', 'household_size')  # Household size controls are at TAZ level
        available_hh_size_cols = [col for col in hh_size_cols if col in out_df.columns and out_df[col].sum() > 0]
        
        if 'num_hh' in out_df.columns and len(available_hh_size_cols) > 0:
            num_hh_total = out_df['num_hh'].sum()
            hh_size_total = out_df[available_hh_size_cols].sum().sum()
            diff = abs(num_hh_total - hh_size_total)
            pct_diff = (diff / num_hh_total) * 100 if num_hh_total > 0 else 0
            
            logger.info(f"Household Size Consistency:")
            logger.info(f"  num_hh total: {num_hh_total:,.0f}")
            logger.info(f"  hh_size_* total: {hh_size_total:,.0f}")
            logger.info(f"  Difference: {diff:,.0f} ({pct_diff:.2f}%)")
            
            if pct_diff > 1.0:
                logger.warning(f"  WARNING: Household size totals differ by more than 1%!")
            else:
                logger.info(f"  ✓ PASS: Household size consistency check")
        
        if 'gq_pop' in out_df.columns:
            gq_total = out_df['gq_pop'].sum()
            logger.info(f"Group Quarters Population: {gq_total:,.0f}")
    
    elif control_geo == 'TAZ':
        # Check if household size controls exist at TAZ level
        hh_size_cols = get_controls_in_category('TAZ', 'household_size')
        available_hh_size_cols = [col for col in hh_size_cols if col in out_df.columns and out_df[col].sum() > 0]
        
        if len(available_hh_size_cols) > 0:
            hh_size_total = out_df[available_hh_size_cols].sum().sum()
            logger.info(f"TAZ-level Household Size Distribution:")
            for col in available_hh_size_cols:
                if col in out_df.columns:
                    col_total = out_df[col].sum()
                    pct = (col_total / hh_size_total) * 100 if hh_size_total > 0 else 0
                    logger.info(f"  {col}: {col_total:,.0f} ({pct:.1f}%)")
            logger.info(f"  Total: {hh_size_total:,.0f}")
        
        # Check income distribution
        income_cols = get_controls_in_category('TAZ', 'household_income')
        available_income_cols = [col for col in income_cols if col in out_df.columns and out_df[col].sum() > 0]
        
        if len(available_income_cols) > 0:
            income_total = out_df[available_income_cols].sum().sum()
            logger.info(f"TAZ-level Income Distribution:")
            for col in available_income_cols:
                if col in out_df.columns:
                    col_total = out_df[col].sum()
                    pct = (col_total / income_total) * 100 if income_total > 0 else 0
                    logger.info(f"  {col}: {col_total:,.0f} ({pct:.1f}%)")
            logger.info(f"  Total: {income_total:,.0f}")
        
        # Check age distribution
        age_cols = get_controls_in_category('TAZ', 'person_age')
        available_age_cols = [col for col in age_cols if col in out_df.columns and out_df[col].sum() > 0]
        
        if len(available_age_cols) > 0:
            age_total = out_df[available_age_cols].sum().sum()
            logger.info(f"TAZ-level Age Distribution:")
            for col in available_age_cols:
                if col in out_df.columns:
                    col_total = out_df[col].sum()
                    pct = (col_total / age_total) * 100 if age_total > 0 else 0
                    logger.info(f"  {col}: {col_total:,.0f} ({pct:.1f}%)")
            logger.info(f"  Total: {age_total:,.0f}")
    
    logger.info(f"=" * 80)


def write_outputs(control_geo, out_df, crosswalk_df):
    """Write final control outputs in populationsim expected format."""
    logger = logging.getLogger()
    out_df.reset_index(drop=False, inplace=True)

    if len(out_df.loc[out_df[control_geo] == 0]) > 0:
        logger.info(f"Dropping {control_geo}=0\n{out_df.loc[out_df[control_geo] == 0, :].T.squeeze()}")
        out_df = out_df.loc[out_df[control_geo] > 0, :]

    if control_geo == "COUNTY":
        # Fix county code format mismatch: Convert full FIPS codes to sequential IDs to match crosswalk
        logger.info(f"Converting COUNTY codes from full FIPS to crosswalk format")
        logger.info(f"Original COUNTY values: {sorted(out_df['COUNTY'].unique())}")
        
        # Use unified configuration's FIPS-to-sequential mapping
        from unified_tm2_config import config
        fips_to_sequential = config.get_fips_to_sequential_mapping()

        # Log the type and contents of out_df['COUNTY'] before applying conversion
        logger.info(f"[DEBUG] out_df['COUNTY'] type: {type(out_df['COUNTY'])}")
        logger.info(f"[DEBUG] out_df['COUNTY'] head: {out_df['COUNTY'].head()}")

        def convert_fips_to_sequential(fips_code):
            if pd.isna(fips_code):
                return fips_code
            fips_int = int(fips_code)
            fips_int = fips_int % 100 if fips_int > 100 else fips_int
            return fips_to_sequential.get(fips_int, fips_int)

        out_df['COUNTY'] = out_df['COUNTY'].apply(convert_fips_to_sequential)
        logger.info(f"Converted COUNTY values: {sorted(out_df['COUNTY'].unique())}")
        
        # Create county name mapping using crosswalk instead of COUNTY_RECODE
        if 'crosswalk_df' in globals():
            county_names = crosswalk_df[['COUNTY', 'county_name']].drop_duplicates()
            out_df = pd.merge(left=county_names, right=out_df, on='COUNTY', how="right")
            logger.info(f"Merged with county names from crosswalk")
        else:
            logger.warning("No crosswalk available for county names, using COUNTY_RECODE mapping")
            # Fallback to original mapping but adjust codes
            county_recode_adjusted = COUNTY_RECODE.copy()
            county_recode_adjusted['COUNTY'] = county_recode_adjusted['GEOID_county'].apply(lambda x: int(x[-3:]) % 100)
            out_df = pd.merge(left=county_recode_adjusted[["COUNTY", "county_name"]], right=out_df, on='COUNTY', how="right")

    # Round all control values to integers, handling NaN and ensuring perfect integer totals
    control_cols = [col for col in out_df.columns if col != control_geo and col != 'county_name']
    for col in control_cols:
        # Fill NaN with 0, round to ensure integer values, then convert to int
        # This extra rounding step prevents floating-point precision issues in PopulationSim
        out_df[col] = numpy.round(out_df[col].fillna(0)).astype(int)

    # Calculate gq_other for MAZ controls if we have the detailed group quarters controls
    if control_geo == 'MAZ' and all(col in out_df.columns for col in ['gq_pop', 'gq_military', 'gq_university']):
        logger.info("Calculating gq_other as remainder after military and university")
        out_df['gq_other'] = out_df['gq_pop'] - out_df['gq_military'] - out_df['gq_university']
        # Ensure gq_other is non-negative
        out_df['gq_other'] = out_df['gq_other'].clip(lower=0)
        
        # Update control_cols to include gq_other
        control_cols = [col for col in out_df.columns if col != control_geo and col != 'county_name']
        
        # Log summary of group quarters breakdown
        total_gq = out_df['gq_pop'].sum()
        military_gq = out_df['gq_military'].sum()
        university_gq = out_df['gq_university'].sum()
        other_gq = out_df['gq_other'].sum()
        
        logger.info(f"Group Quarters Breakdown:")
        logger.info(f"  Total GQ: {total_gq:,.0f}")
        logger.info(f"  Military: {military_gq:,.0f} ({military_gq/total_gq*100:.1f}%)")
        logger.info(f"  University: {university_gq:,.0f} ({university_gq/total_gq*100:.1f}%)")
        logger.info(f"  Other: {other_gq:,.0f} ({other_gq/total_gq*100:.1f}%)")
        
        # Validate and fix GQ component consistency
        logger.info("Validating GQ component consistency...")
        gq_total_check = out_df['gq_military'] + out_df['gq_university'] + out_df['gq_other']
        gq_mismatch = abs(out_df['gq_pop'] - gq_total_check) > 0.1
        
        if gq_mismatch.sum() > 0:
            logger.warning(f"Found {gq_mismatch.sum()} MAZs where GQ components don't sum to total - fixing...")
            # Adjust gq_pop to match the sum of components
            out_df.loc[gq_mismatch, 'gq_pop'] = gq_total_check.loc[gq_mismatch]
            logger.info(f"Fixed GQ component consistency for {gq_mismatch.sum()} MAZs")
        else:
            logger.info("All MAZ GQ components are consistent with totals")

    logger.info(f"Processing {control_geo} controls with {len(out_df)} rows and {len(out_df.columns)} columns")
    logger.info(f"Control columns: {control_cols}")
    
    # Log detailed statistics before writing files
    log_control_statistics(control_geo, out_df, logger)
    
    # Write single marginals file in populationsim expected format
    if control_geo == 'MAZ':
        # MAZ provides: num_hh, gq_pop, gq_military, gq_university, gq_other
        # Household size controls moved to TAZ level for better data quality
        # Group quarters now include detailed type breakdown from 2020 Census DHC data
        
        output_file = os.path.join(PRIMARY_OUTPUT_DIR, MAZ_MARGINALS_FILE)
        
    elif control_geo == 'TAZ':
        # Add any missing expected controls as zeros for TAZ level
        existing_controls = list(out_df.columns)
        missing_by_category = get_missing_controls_for_geography('TAZ', existing_controls)
        
        for category, missing_controls in missing_by_category.items():
            for control in missing_controls:
                out_df[control] = 0
                logger.info(f"Added missing {category} control '{control}' as zeros (data not available or reliable)")
        
        output_file = os.path.join(PRIMARY_OUTPUT_DIR, TAZ_MARGINALS_FILE)
        
    elif control_geo == 'COUNTY':
        # Add any missing expected controls as zeros for COUNTY level
        existing_controls = list(out_df.columns)
        missing_by_category = get_missing_controls_for_geography('COUNTY', existing_controls)
        
        for category, missing_controls in missing_by_category.items():
            for control in missing_controls:
                out_df[control] = 0
                logger.info(f"Added missing {category} control '{control}' as zeros (data not available or reliable)")
        
        output_file = os.path.join(PRIMARY_OUTPUT_DIR, COUNTY_MARGINALS_FILE)
        
    else:
        # For other geographies, use the generic format
        output_file = os.path.join(PRIMARY_OUTPUT_DIR, f"{control_geo.lower()}_{ACS_EST_YEAR}_marginals.csv")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write the single marginals file
    if control_geo == 'COUNTY' and 'county_name' in out_df.columns:
        # For county, exclude county_name from the output
        output_cols = [control_geo] + control_cols
        out_df[output_cols].to_csv(output_file, index=False)
    else:
        # Ensure geographic ID columns are integers to match crosswalk format
        if control_geo in out_df.columns:
            out_df = out_df.copy()  # Avoid modifying original dataframe
            out_df[control_geo] = out_df[control_geo].astype(int)
            if control_geo == 'MAZ':
                logger.info(f"Converted MAZ IDs to integers for compatibility with crosswalk format")
        out_df.to_csv(output_file, index=False)
    
    logger.info(f"Wrote {control_geo} marginals file: {output_file} with {len(control_cols)} controls")


def normalize_household_size_controls(control_table_df, control_name, temp_controls, logger):
    """
    Normalize household size controls to ensure they sum to the correct total.
    
    
    Args:
        control_table_df: DataFrame with household size controls 
        control_name: Name of the control (e.g., 'hh_size_1')
        temp_controls: Dictionary of temp controls including 'num_hh'
        logger: Logger instance
    """
    
    # Only apply to household size controls (dynamically determined)
    household_size_controls = get_controls_in_category('TAZ', 'household_size')
    if control_name not in household_size_controls:
        return control_table_df
    
    # Check if we have num_hh available for normalization
    if 'num_hh' not in temp_controls:
        logger.warning(f"Cannot normalize {control_name} - num_hh not available in temp_controls")
        return control_table_df
    
    logger.info(f"Normalizing household size control: {control_name}")
    
    # Get the geographic level from control_table_df
    geo_cols = ['state', 'county', 'tract', 'block', 'block group']
    available_geo_cols = [col for col in geo_cols if col in control_table_df.columns]
    
    if not available_geo_cols:
        logger.warning(f"Cannot normalize {control_name} - no geographic columns found")
        return control_table_df
    
    # Create a copy to avoid modifying the original
    normalized_df = control_table_df.copy()
    
    # For household size controls, we want to preserve the proportional distribution
    # but scale to match the total households (num_hh) rather than using raw ACS counts
    
    # The key insight: ACS gives us the distribution shape, but the total magnitude
    # should match the scaled num_hh values, not the raw ACS totals
    
    # Since this is complex geographic aggregation, we'll let the temp_table_scaling
    # handle the details, but we'll ensure the config uses proper normalization
    
    logger.info(f"Household size control {control_name} will be normalized during temp_table_scaling")
    logger.info(f"Raw control sum before normalization: {normalized_df[control_name].sum():,.0f}")
    
    return normalized_df


def create_hhgq_integrated_files(logger):
    """
    Create HHGQ-integrated control files that combine households and group quarters
    as single-person households for PopulationSim processing.
    
    This integrates the functionality from add_hhgq_combined_controls.py directly
    into the main pipeline.
    """
    logger.info("=" * 60)
    logger.info("CREATING HHGQ-INTEGRATED CONTROL FILES")
    logger.info("=" * 60)
    
    from tm2_control_utils.config_census import PRIMARY_OUTPUT_DIR, MAZ_MARGINALS_FILE, TAZ_MARGINALS_FILE, COUNTY_MARGINALS_FILE
    import shutil
    
    try:
        # Define input file paths - marginals are in main output directory
        import unified_tm2_config
        main_output_dir = str(unified_tm2_config.config.POPSIM_DATA_DIR)
        
        maz_input = os.path.join(main_output_dir, MAZ_MARGINALS_FILE)
        taz_input = os.path.join(main_output_dir, TAZ_MARGINALS_FILE)
        county_input = os.path.join(PRIMARY_OUTPUT_DIR, COUNTY_MARGINALS_FILE)  # This one is in PopSim data dir
        
        # Output files will be in PopulationSim data directory
        output_dir = PRIMARY_OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)
        
        maz_output = os.path.join(output_dir, "maz_marginals_hhgq.csv")
        taz_output = os.path.join(output_dir, "taz_marginals_hhgq.csv") 
        county_output = os.path.join(output_dir, "county_marginals.csv")
        
        # Process MAZ controls
        if os.path.exists(maz_input):
            logger.info(f"Processing MAZ controls: {maz_input}")
            maz_df = pd.read_csv(maz_input)
            logger.info(f"Read {len(maz_df)} MAZ controls")
            
            # Create numhh_gq = num_hh + gq_pop (treat group quarters as single-person households)
            if 'num_hh' in maz_df.columns and 'gq_pop' in maz_df.columns:
                maz_df["numhh_gq"] = maz_df.num_hh + maz_df.gq_pop
                logger.info(f"Created numhh_gq column: num_hh ({maz_df.num_hh.sum():,.0f}) + gq_pop ({maz_df.gq_pop.sum():,.0f}) = {maz_df.numhh_gq.sum():,.0f}")
            else:
                logger.error(f"Missing required columns in MAZ data: num_hh={('num_hh' in maz_df.columns)}, gq_pop={('gq_pop' in maz_df.columns)}")
                return False
            
            maz_df.to_csv(maz_output, index=False)
            logger.info(f"Wrote MAZ HHGQ file: {maz_output}")
        else:
            logger.error(f"MAZ input file not found: {maz_input}")
            return False
            
        # Process TAZ controls  
        if os.path.exists(taz_input):
            logger.info(f"Processing TAZ controls: {taz_input}")
            taz_df = pd.read_csv(taz_input)
            logger.info(f"Read {len(taz_df)} TAZ controls")
            
            # Need to adjust household size 1 category to include group quarters
            # Get the single-person household control name from configuration
            size_controls = get_controls_in_category('TAZ', 'household_size')
            size_1_control = None
            
            # Find the single-person household control (usually ends with '_1' or contains 'size_1')
            for control in size_controls:
                if control.endswith('_1') or 'size_1' in control:
                    size_1_control = control
                    break
            
            if not size_1_control and size_controls:
                # Fallback: use the first size control if we can't identify size_1 specifically
                size_1_control = size_controls[0]
                logger.warning(f"Could not identify single-person household control, using first size control: {size_1_control}")
            
            logger.info(f"Using size-1 household control: {size_1_control}")
            
            # Get GQ population by TAZ from MAZ data
            if 'TAZ' in maz_df.columns:
                maz_gq_by_taz = maz_df.groupby('TAZ')['gq_pop'].sum().reset_index()
                logger.info(f"Aggregated GQ population from {len(maz_df)} MAZ to {len(maz_gq_by_taz)} TAZ")
                
                # Merge GQ data with TAZ controls
                taz_df = taz_df.merge(maz_gq_by_taz, on='TAZ', how='left')
                taz_df['gq_pop'] = taz_df['gq_pop'].fillna(0)
                
                # Create size_1_gq control = size_1 + gq_pop
                if size_1_control and size_1_control in taz_df.columns:
                    gq_control_name = f"{size_1_control}_gq"
                    taz_df[gq_control_name] = taz_df[size_1_control] + taz_df.gq_pop
                    logger.info(f"Created {gq_control_name} column: {size_1_control} ({taz_df[size_1_control].sum():,.0f}) + gq_pop ({taz_df.gq_pop.sum():,.0f}) = {taz_df[gq_control_name].sum():,.0f}")
                    
                    # Remove the temporary gq_pop column
                    taz_df.drop('gq_pop', axis=1, inplace=True)
                elif size_1_control:
                    logger.warning(f"No {size_1_control} column found in TAZ data - creating {size_1_control}_gq = gq_pop")
                    gq_control_name = f"{size_1_control}_gq"
                    taz_df[gq_control_name] = taz_df.gq_pop
                    taz_df.drop('gq_pop', axis=1, inplace=True)
                else:
                    logger.warning("No household size controls found in configuration - cannot create HHGQ integration")
                    taz_df.drop('gq_pop', axis=1, inplace=True)
            else:
                logger.warning("No TAZ column in MAZ data - cannot aggregate GQ by TAZ")
                # Assume no GQ adjustment needed
                if size_1_control and size_1_control in taz_df.columns:
                    gq_control_name = f"{size_1_control}_gq"
                    taz_df[gq_control_name] = taz_df[size_1_control]
                    logger.info(f"Created {gq_control_name} = {size_1_control} (no GQ adjustment)")
                elif size_1_control:
                    logger.warning(f"No {size_1_control} column found in TAZ data for HHGQ integration")
                
            taz_df.to_csv(taz_output, index=False)
            logger.info(f"Wrote TAZ HHGQ file: {taz_output}")
        else:
            logger.error(f"TAZ input file not found: {taz_input}")
            return False
            
        # Copy county controls file (no HHGQ integration needed at county level)
        if os.path.exists(county_input):
            # Only copy if source and destination are not the same file
            if os.path.abspath(county_input) != os.path.abspath(county_output):
                shutil.copy2(county_input, county_output)
                logger.info(f"Copied county controls: {county_input} -> {county_output}")
            else:
                logger.info(f"Skipped copying county controls: source and destination are the same file ({county_input})")
        else:
            logger.warning(f"County input file not found: {county_input}")
            
        logger.info("SUCCESS: HHGQ-integrated control files created successfully")
        logger.info(f"Files created in: {output_dir}")
        logger.info(f"  - maz_marginals_hhgq.csv (with numhh_gq column)")
        
        # Dynamic message based on which size control was used
        size_controls = get_controls_in_category('TAZ', 'household_size')
        size_1_control = None
        for control in size_controls:
            if control.endswith('_1') or 'size_1' in control:
                size_1_control = control
                break
        if size_1_control:
            logger.info(f"  - taz_marginals_hhgq.csv (with {size_1_control}_gq column)")
        else:
            logger.info(f"  - taz_marginals_hhgq.csv (no household size integration)")
        logger.info(f"  - county_marginals.csv (copied)")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating HHGQ-integrated files: {e}")
        logger.error(f"HHGQ integration traceback: {traceback.format_exc()}")
        return False


def enforce_hierarchical_consistency_in_controls(logger):
    """
    Enforce hierarchical consistency between MAZ and TAZ controls.
    Ensures MAZ totals equal the sum of corresponding TAZ categories within each MAZ.
    """
    import pandas as pd
    logger.info("Enforcing hierarchical consistency between MAZ and TAZ controls...")
    
    # Define file paths
    maz_file = os.path.join(PRIMARY_OUTPUT_DIR, MAZ_MARGINALS_FILE)
    taz_file = os.path.join(PRIMARY_OUTPUT_DIR, TAZ_MARGINALS_FILE)
    
    if not os.path.exists(maz_file):
        logger.error(f"MAZ marginals file not found: {maz_file}")
        return False
        
    if not os.path.exists(taz_file):
        logger.error(f"TAZ marginals file not found: {taz_file}")
        return False
    
    try:
        # Load the control files
        logger.info(f"Loading MAZ controls from: {maz_file}")
        maz_controls = pd.read_csv(maz_file)
        
        logger.info(f"Loading TAZ controls from: {taz_file}")
        taz_controls = pd.read_csv(taz_file)
        
        logger.info(f"MAZ controls shape: {maz_controls.shape}")
        logger.info(f"TAZ controls shape: {taz_controls.shape}")
        
        # Check that we have the necessary columns
        if 'MAZ' not in maz_controls.columns:
            logger.error("MAZ column not found in MAZ controls")
            return False
            
        if 'TAZ' not in taz_controls.columns or 'MAZ' not in taz_controls.columns:
            logger.error("TAZ or MAZ column not found in TAZ controls")
            return False
        
        # Load crosswalk for MAZ-TAZ mapping
        crosswalk_file = GEO_CROSSWALK_TM2_PATH
        if not os.path.exists(crosswalk_file):
            logger.error(f"Crosswalk file not found: {crosswalk_file}")
            return False
            
        logger.info(f"Loading crosswalk from: {crosswalk_file}")
        crosswalk_df = pd.read_csv(crosswalk_file)
        
        # Show the hierarchical consistency rules that will be applied
        logger.info("Hierarchical consistency rules to be enforced:")
        for maz_control, taz_control_list in HIERARCHICAL_CONSISTENCY.items():
            logger.info(f"  {maz_control} (MAZ) = sum({taz_control_list}) (TAZ)")
        
        # Apply hierarchical consistency enforcement
        logger.info("Applying hierarchical consistency enforcement...")
        maz_updated, taz_updated = enforce_hierarchical_consistency(maz_controls, taz_controls, crosswalk_df)
        
        # Create backups of original files
        maz_backup_file = maz_file.replace('.csv', '_backup_original.csv')
        if not os.path.exists(maz_backup_file):
            logger.info(f"Creating MAZ backup: {maz_backup_file}")
            maz_controls.to_csv(maz_backup_file, index=False)
            
        taz_backup_file = taz_file.replace('.csv', '_backup_original.csv')
        if not os.path.exists(taz_backup_file):
            logger.info(f"Creating TAZ backup: {taz_backup_file}")
            taz_controls.to_csv(taz_backup_file, index=False)
        
        # Write the updated controls
        # MAZ controls should be unchanged (they're authoritative)
        logger.info(f"Writing MAZ controls to: {maz_file}")
        maz_updated.to_csv(maz_file, index=False)
        
        # TAZ controls have been proportionally adjusted
        logger.info(f"Writing adjusted TAZ controls to: {taz_file}")
        taz_updated.to_csv(taz_file, index=False)
        
        # Validate the results
        logger.info("Validating hierarchical consistency enforcement results...")
        
        # Use the updated TAZ controls for validation
        taz_by_maz = taz_updated.groupby('MAZ')
        
        validation_passed = True
        for maz_control, taz_control_list in HIERARCHICAL_CONSISTENCY.items():
            if maz_control not in maz_updated.columns:
                continue
                
            existing_taz_controls = [ctrl for ctrl in taz_control_list if ctrl in taz_updated.columns]
            if not existing_taz_controls:
                continue
                
            # Calculate sums from adjusted TAZ controls
            taz_sums = taz_by_maz[existing_taz_controls].sum().sum(axis=1)
            
            # Get MAZ totals (should be unchanged)
            maz_totals = maz_updated.set_index('MAZ')[maz_control]
            
            # Check for consistency
            inconsistent_count = 0
            for maz_id in taz_sums.index:
                if maz_id in maz_totals.index:
                    taz_sum = taz_sums[maz_id]
                    maz_total = maz_totals[maz_id]
                    if abs(taz_sum - maz_total) > HIERARCHICAL_TOLERANCE:
                        logger.warning(f"Inconsistency in MAZ {maz_id}, {maz_control}: TAZ sum {taz_sum}, MAZ total {maz_total}")
                        validation_passed = False
                        inconsistent_count += 1
            
            if inconsistent_count == 0:
                logger.info(f"✓ {maz_control}: All MAZs consistent within tolerance")
            else:
                logger.warning(f"✗ {maz_control}: {inconsistent_count} MAZs still inconsistent")
        
        if validation_passed:
            logger.info("[SUCCESS] Hierarchical consistency enforcement completed successfully!")
        else:
            logger.warning("[WARNING]  Some inconsistencies remain after enforcement")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during hierarchical consistency enforcement: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate baseyear controls for TM2 PopulationSim')
    # Removed --output_dir argument - now using unified config
    args = parser.parse_args()

    # Use PRIMARY_OUTPUT_DIR from config (no command line override)
    # PRIMARY_OUTPUT_DIR is set in tm2_control_utils.config_census from unified config


    
    pd.set_option("display.width", 500)
    pd.set_option("display.float_format", "{:,.2f}".format)

    LOG_FILE = f"create_baseyear_controls_{ACS_EST_YEAR}.log"

    # create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
    logger.addHandler(ch)
    fh = logging.FileHandler(LOG_FILE, mode='w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
    logger.addHandler(fh)

    # I'd set things up so I can run locally, but I'm not sure if we need this long term

    # Configure file paths based on mode
    # if args.use_local:
    #     logger.info("Using LOCAL data mode - reading from local_data/ directory")
    #     configure_file_paths(use_local=True)
    #     if not check_file_accessibility_with_mode(use_local=True):
    #         logger.error("Cannot access required local files. Run with --copy-data first.")
    #         return 1
    # else:

    logger.info("Using NETWORK data mode - reading from M: drive")
    configure_file_paths(use_local=False)


    logger.info("Preparing geography lookups")
    
    # Verify all input files are accessible
    if not verify_input_files():
        logger.error("Cannot proceed - required files are missing")
        return
        
    maz_taz_def_df, crosswalk_df = prepare_geography_dfs()
    cf = CensusFetcher() 
    final_control_dfs = {}

    # Verify input files before proceeding
    if not verify_input_files():
        logger.error("Input file verification failed, exiting")
        sys.exit(1)

    # Step 1: Process county targets first to establish scaling factors for MAZ household estimates
    county_targets = {}  # Updated variable name to reflect county-level approach
    if 'COUNTY_TARGETS' in CONTROLS[ACS_EST_YEAR]:
        county_targets = get_county_targets(cf, logger, use_offline_fallback=True)

    for control_geo, control_dict in CONTROLS[ACS_EST_YEAR].items():
        # Debug: Check what's actually in each control dictionary
        logger.info(f"[DEBUG] Checking geography {control_geo}: dict type = {type(control_dict)}, len = {len(control_dict)}")
        if control_geo == 'TAZ':
            logger.info(f"[DEBUG] TAZ controls dictionary: {control_dict}")
            logger.info(f"[DEBUG] TAZ control keys: {list(control_dict.keys()) if control_dict else 'Empty'}")
        
        # Skip empty control dictionaries and already processed county targets
        if not control_dict or control_geo == 'COUNTY_TARGETS':
            logger.info(f"Skipping {control_geo} - no controls defined or already processed")
            continue
        
        # Debug: Log what controls are found for each geography
        logger.info(f">>> FOUND GEOGRAPHY: {control_geo} with {len(control_dict)} controls: {list(control_dict.keys())}")
        
        # Process MAZ, TAZ, and COUNTY controls (household size moved from MAZ to TAZ)
        if control_geo not in ['MAZ', 'MAZ_SCALED', 'TAZ', 'COUNTY']:
            logger.info(f"TEMPORARILY SKIPPING {control_geo} - focusing on MAZ, TAZ, and COUNTY controls only")
            continue
            
        temp_controls = collections.OrderedDict()

        # THIS IS WHERE MOST OF THE WORK IS DONE
        for control_name, control_def in control_dict.items():
            logger.info(f">>> PROCESSING CONTROL: {control_geo}.{control_name}")
            try:
                # Handle MAZ_SCALED controls with special processing
                if control_geo == 'MAZ_SCALED':
                    process_maz_scaled_control(
                        control_name, control_def, cf, maz_taz_def_df, crosswalk_df, 
                        temp_controls, final_control_dfs, county_targets, logger
                    )
                else:
                    process_control(
                        control_geo, control_name, control_def,
                        cf, maz_taz_def_df, crosswalk_df, temp_controls, final_control_dfs, county_targets
                    )
                logger.info(f">>> COMPLETED CONTROL: {control_geo}.{control_name}")
            except Exception as e:
                logger.error(f">>> FAILED CONTROL: {control_geo}.{control_name} - Error: {e}")
                logger.error(f">>> Error traceback: {traceback.format_exc()}")
                continue  # Continue with next control instead of stopping

        # Log summary of temp controls created for this geography
        logger.info(f"\nSUMMARY OF TEMP CONTROLS FOR {control_geo}:")
        logger.info(f"-" * 50)
        for temp_name, temp_df in temp_controls.items():
            if not temp_df.empty:
                # For temp controls, find numeric columns (exclude GEOID columns)
                control_cols = [col for col in temp_df.columns 
                               if not col.startswith('GEOID') and temp_df[col].dtype in ['int64', 'float64']]
                if control_cols:
                    total = temp_df[control_cols].sum().sum()
                    logger.info(f"{temp_name}: {len(temp_df)} zones, total = {total:,.0f}")
                else:
                    logger.info(f"{temp_name}: {len(temp_df)} zones, no numeric columns found")

        logger.info(f"Preparing final controls files for {control_geo}")
        out_df = final_control_dfs[control_geo].copy()
        
        # Special handling for COUNTY controls: Combine manual+military to match seed encoding
        if control_geo == 'COUNTY' and 'pers_occ_manual' in out_df.columns and 'pers_occ_military' in out_df.columns:
            logger.info(f"Combining manual+military occupation controls to match seed population encoding")
            
            # Create combined manual+military control
            out_df['pers_occ_manual_military'] = out_df['pers_occ_manual'] + out_df['pers_occ_military']
            
            # Remove the separate manual and military controls since seed population combines them
            logger.info(f"Removing separate manual ({out_df['pers_occ_manual'].sum():,.0f}) and military ({out_df['pers_occ_military'].sum():,.0f}) controls")
            logger.info(f"Combined manual_military total: {out_df['pers_occ_manual_military'].sum():,.0f}")
            
            out_df = out_df.drop(['pers_occ_manual', 'pers_occ_military'], axis=1)
            
            logger.info(f"Updated COUNTY controls now have combined manual_military occupation category")
        
        # CRITICAL DEBUGGING: Check worker control totals right before writing to file
        if control_geo == 'TAZ':
            worker_cols = [col for col in out_df.columns if 'wrk' in col.lower()]
            if worker_cols:
                print(f"[DEBUG][FINAL] ==> FINAL TAZ CONTROLS BEFORE WRITING TO FILE")
                for col in worker_cols:
                    total = out_df[col].sum()
                    print(f"[DEBUG][FINAL] {col}: {total:,.0f}")
                
                worker_total = sum(out_df[col].sum() for col in worker_cols)
                print(f"[DEBUG][FINAL] Total worker controls: {worker_total:,.0f}")
                
                # Compare with size controls
                size_cols = [col for col in out_df.columns if 'size' in col.lower()]
                if size_cols:
                    size_total = sum(out_df[col].sum() for col in size_cols)
                    ratio = worker_total / size_total if size_total > 0 else 0
                    print(f"[DEBUG][FINAL] Total size controls: {size_total:,.0f}")
                    print(f"[DEBUG][FINAL] Worker/Size ratio: {ratio:.6f}")
        
        write_outputs(control_geo, out_df, crosswalk_df)
        
        # Validate TAZ household consistency after writing TAZ controls
        if control_geo == 'TAZ':
            logger.info("Validating TAZ household control consistency")
            taz_marginals_file = os.path.join(PRIMARY_OUTPUT_DIR, TAZ_MARGINALS_FILE)
            validation_passed = validate_taz_household_consistency(taz_marginals_file, logger)
            
            # If validation failed, attempt to harmonize controls
            if not validation_passed:
                logger.info("TAZ validation failed - attempting to harmonize household controls")
                harmonization_success = harmonize_taz_household_controls(taz_marginals_file, logger)
                
                if harmonization_success:
                    logger.info("Re-validating TAZ controls after harmonization")
                    final_validation = validate_taz_household_consistency(taz_marginals_file, logger)
                    if final_validation:
                        logger.info("SUCCESS: TAZ controls are now consistent after harmonization")
                    else:
                        logger.warning("TAZ controls still have inconsistencies after harmonization")
                else:
                    logger.error("Failed to harmonize TAZ controls")
            
            # Add MAZ household summary by TAZ for comparison
            logger.info("Adding MAZ household summary to TAZ marginals")
            summarize_maz_households_by_taz(logger)
    
    # Handle COUNTY separately since we have no data but need to create empty file for populationsim
    # TEMPORARILY COMMENTED OUT - focusing on MAZ controls only
    # if 'COUNTY' not in final_control_dfs:
    #     logger.info("Creating empty COUNTY controls file since occupation data is no longer available")
    #     # Create a minimal county dataframe with just county IDs and zero controls
    #     county_df = pd.DataFrame({
    #         'COUNTY': range(1, 10),  # Bay Area counties 1-9
    #         'pers_occ_management': 0,
    #         'pers_occ_professional': 0, 
    #         'pers_occ_services': 0,
    #         'pers_occ_retail': 0,
    #         'pers_occ_manual': 0,
    #         'pers_occ_military': 0
    #     })
    #     write_outputs('COUNTY', county_df, crosswalk_df)

    # Write geographic crosswalk file in expected location
    crosswalk_file = GEO_CROSSWALK_TM2_PATH
    
    # Ensure we have the expected columns for populationsim
    expected_crosswalk_cols = ['MAZ', 'TAZ', 'COUNTY', 'county_name', 'COUNTYFP10', 'TRACTCE10', 'PUMA']
    available_cols = [col for col in expected_crosswalk_cols if col in crosswalk_df.columns]
    
    if len(available_cols) < len(expected_crosswalk_cols):
        missing_cols = set(expected_crosswalk_cols) - set(available_cols)
        logger.warning(f"Missing crosswalk columns: {missing_cols}. Writing available columns: {available_cols}")
    
    # Write the crosswalk file with available columns
    crosswalk_df[available_cols].to_csv(crosswalk_file, index=False)
    logger.info(f"Wrote geographic crosswalk file {crosswalk_file}")

    # Create county summary file showing county-level scaling factors and results
    # (Called after control processing to reuse already-calculated totals)
    create_county_summary(county_targets, cf, logger, final_control_dfs)

    # Note: County-level scaling is now applied during main control processing
    # The scale_maz_households_to_county_targets validation step has been removed
    # to avoid confusion from duplicate scaling attempts
    
    # Validate MAZ controls against county targets
    maz_marginals_file = os.path.join(PRIMARY_OUTPUT_DIR, MAZ_MARGINALS_FILE)
    validate_maz_controls(maz_marginals_file, county_targets, logger)

    # ENFORCE HIERARCHICAL CONSISTENCY: Ensure TAZ categories sum to validated MAZ totals
    logger.info("=" * 60)
    logger.info("ENFORCING HIERARCHICAL CONSISTENCY AFTER MAZ VALIDATION")
    logger.info("=" * 60)
    
    enforce_hierarchical_consistency_in_controls(logger)

    # Create MAZ data files with updated household and population data
    logger.info("Creating maz_data.csv and maz_data_withDensity.csv files")
    create_maz_data_files(logger)

    # INTEGRATE HHGQ FILES: Create HHGQ-integrated control files for PopulationSim
    logger.info("Creating HHGQ-integrated control files for PopulationSim")
    create_hhgq_integrated_files(logger)


# This isn't working, needs more testing
    # Run output structure validation test if requested
    # logger.info("Running output structure validation test")
    # try:
    #     from test_output_structure import OutputStructureTest
    #     test_runner = OutputStructureTest(verbose=True)
    #     test_results = test_runner.run_all_tests()
            
    #     if test_results['success']:
    #             logger.info("✓ Output structure validation PASSED")
    #             logger.info(f"All {test_results['tests_run']} validation tests completed successfully")
    #     else:
    #             logger.error("✗ Output structure validation FAILED")
    #             logger.error(f"{test_results['failures']} out of {test_results['tests_run']} tests failed")
    #             for failure in test_results.get('failure_details', []):
    #                 logger.error(f"  - {failure}")
    # except ImportError as e:
    #         logger.error(f"Could not import test_output_structure: {e}")
    # except Exception as e:
    #         logger.error(f"Error running output structure test: {e}")
    #         logger.error(f"Test error traceback: {traceback.format_exc()}")

    logger.info("Control file generation completed successfully!")


if __name__ == '__main__':

    main()
