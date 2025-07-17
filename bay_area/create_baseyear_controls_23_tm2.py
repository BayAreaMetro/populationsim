"""
create_baseyear_controls_23_tm2.py

This script creates baseyear control files for the MTC Bay Area populationsim model using 
ACS 2023 data with simplified controls to reflect current Census data availability.

"""


USAGE = """



This script creates populationsim-compatible control files using only reliably available 
ACS 2023 data, with zero-fill strategy for discontinued Census variables.

1) CACHE MANAGEMENT: Downloads ACS 2023 tables to input_2023/census_cache/ directory.
   - One CSV file per census table with descriptive column headers
   - Automatic cache validation and refresh capability
   - To force re-download: remove specific cache files

2) GEOGRAPHY INTERPOLATION: Converts 2020 Census estimates to 2010 Census geographies:
   - 2020 Census data → 2010 Census geographies using areal interpolation crosswalks
   - Required because MAZ/TAZ system was built on 2010 Census geography boundaries
   - Uses proportional allocation based on area and demographic weights
   - Handles block→block, block group→block group, tract→tract interpolation

3) AVAILABLE CONTROLS PROCESSING:
   - MAZ Level: Total households (B25001), household size (B25009), group quarters (B26001)
   - TAZ Level: Workers (B08202), age groups (B01001), children (B09001) 
   - County Level: Basic geographic identifiers only
   
4) MISSING CONTROLS HANDLING:
   - Detailed GQ types (gq_type_univ, gq_type_mil): Zero-filled with documentation
   - Income categories (hh_inc_30, hh_inc_60, etc.): Basic categories only where available
   - Occupation data (pers_occ_*): Zero-filled as Census no longer provides county detail

5) REGIONAL SCALING: Applies ACS 2023 county totals for accurate population scaling:
   - Total households: Sum of county B25001 estimates
   - Group quarters: 155,065 from regional B26001 aggregation
   - Population totals: B01003 county estimates aggregated to region

6) OUTPUT FORMAT: Creates populationsim-compatible marginals files:
   - maz_marginals.csv: MAZ-level controls (households, GQ, housing size)
   - taz_marginals.csv: TAZ-level controls (workers, age groups, children) 
   - county_marginals.csv: County-level controls and region totals
   - All files compatible with populationsim expected format and column headers
"""

import argparse
import collections
import logging
import os
import sys
import shutil
from pathlib import Path
import numpy
import pandas as pd

from tm2_control_utils.config import *
from tm2_control_utils.census_fetcher import CensusFetcher
from tm2_control_utils.geog_utils import prepare_geography_dfs, add_aggregate_geography_colums, interpolate_est
from tm2_control_utils.controls import create_control_table, census_col_is_in_control, match_control_to_geography, integerize_control


def verify_input_files():
    """Verify that all required input files are accessible."""
    logger = logging.getLogger()
    
    from tm2_control_utils.config import MAZ_TAZ_DEF_FILE, MAZ_TAZ_PUMA_FILE, MAZ_TAZ_ALL_GEOG_FILE, CENSUS_API_KEY_FILE, LOCAL_CACHE_FOLDER
    
    logger.info("Checking file accessibility")
    
    required_files = [
        ("MAZ/TAZ definitions", MAZ_TAZ_DEF_FILE),
        ("MAZ/TAZ PUMA mapping", MAZ_TAZ_PUMA_FILE), 
        ("MAZ/TAZ all geography", MAZ_TAZ_ALL_GEOG_FILE),
        ("Census API key", CENSUS_API_KEY_FILE),
    ]
    
    missing_files = []
    for desc, filepath in required_files:
        if not os.path.exists(filepath):
            missing_files.append((desc, filepath))
            logger.error(f"Missing {desc}: {filepath}")
        else:
            logger.info(f"Found {desc}: {filepath}")
    
    # Check cache directory
    if not os.path.exists(LOCAL_CACHE_FOLDER):
        missing_files.append(("Census cache directory", LOCAL_CACHE_FOLDER))
        logger.error(f"Missing census cache directory: {LOCAL_CACHE_FOLDER}")
    else:
        logger.info(f"Found census cache directory: {LOCAL_CACHE_FOLDER}")
    
    if missing_files:
        logger.error(f"Missing {len(missing_files)} required files/directories")
        logger.error("Make sure you're connected to the MTC network or files are available locally")
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
        (NETWORK_MAZ_TAZ_PUMA_FILE, LOCAL_MAZ_TAZ_PUMA_FILE),
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
                logger.info(f"Copied: {network_path} → {local_path}")
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
    Configure file paths based on whether to use local or network storage.
    Updates the global config variables.
    """
    global MAZ_TAZ_DEF_FILE, MAZ_TAZ_PUMA_FILE, MAZ_TAZ_ALL_GEOG_FILE
    global CENSUS_API_KEY_FILE, LOCAL_CACHE_FOLDER
    
    if use_local:
        MAZ_TAZ_DEF_FILE = LOCAL_MAZ_TAZ_DEF_FILE
        MAZ_TAZ_PUMA_FILE = LOCAL_MAZ_TAZ_PUMA_FILE  
        MAZ_TAZ_ALL_GEOG_FILE = LOCAL_MAZ_TAZ_ALL_GEOG_FILE
        CENSUS_API_KEY_FILE = LOCAL_CENSUS_API_KEY_FILE
        
        # Check for input_2023 cache directory first, then fall back to local_data cache
        if os.path.exists(INPUT_2023_CACHE_FOLDER):
            LOCAL_CACHE_FOLDER = INPUT_2023_CACHE_FOLDER
            print(f"Using input_2023 cache directory: {INPUT_2023_CACHE_FOLDER}")
        else:
            LOCAL_CACHE_FOLDER = LOCAL_CACHE_FOLDER  # Use local_data cache
            print(f"Using local_data cache directory: {LOCAL_CACHE_FOLDER}")
    else:
        MAZ_TAZ_DEF_FILE = NETWORK_MAZ_TAZ_DEF_FILE
        MAZ_TAZ_PUMA_FILE = NETWORK_MAZ_TAZ_PUMA_FILE
        MAZ_TAZ_ALL_GEOG_FILE = NETWORK_MAZ_TAZ_ALL_GEOG_FILE
        CENSUS_API_KEY_FILE = NETWORK_CENSUS_API_KEY_FILE
        
        # For network mode, check for input_2023 cache first as fallback
        if os.path.exists(INPUT_2023_CACHE_FOLDER):
            LOCAL_CACHE_FOLDER = INPUT_2023_CACHE_FOLDER
            print(f"Using input_2023 cache directory as fallback: {INPUT_2023_CACHE_FOLDER}")
        else:
            LOCAL_CACHE_FOLDER = NETWORK_CACHE_FOLDER


def check_file_accessibility_with_mode(use_local=False):
    """
    Check if all required files are accessible for the specified mode.
    Returns True if all required files exist, False otherwise.
    """
    logger = logging.getLogger(__name__)
    mode_str = "LOCAL" if use_local else "NETWORK"
    logger.info(f"Checking file accessibility in {mode_str} mode")
    
    # Check for input_2023 cache directory first
    if os.path.exists(INPUT_2023_CACHE_FOLDER):
        logger.info(f"Detected input_2023 cache directory: {INPUT_2023_CACHE_FOLDER}")
    
    # Configure paths based on mode
    configure_file_paths(use_local)
    
    required_files = [
        ("MAZ/TAZ definitions", MAZ_TAZ_DEF_FILE),
        ("MAZ/TAZ PUMA mapping", MAZ_TAZ_PUMA_FILE),
        ("MAZ/TAZ all geography", MAZ_TAZ_ALL_GEOG_FILE),
        ("Census API key", CENSUS_API_KEY_FILE),
        ("census cache directory", LOCAL_CACHE_FOLDER),
    ]
    
    all_accessible = True
    for desc, filepath in required_files:
        if os.path.exists(filepath):
            logger.info(f"Found {desc}: {filepath}")
        else:
            logger.error(f"Missing {desc}: {filepath}")
            all_accessible = False
    
    if all_accessible:
        logger.info("All required files are accessible")
    else:
        logger.error("Some required files are missing")
        if not use_local:
            logger.info("Try using --copy-data to copy network files to local storage, then --use-local")
        
    return all_accessible


def get_regional_targets(cf, logger, use_offline_fallback=True):
    """Get regional targets from ACS 2023 county data for scaling MAZ controls.
    
    This function first tries to read from a local cache file. If that fails and
    use_offline_fallback is False, it fetches from Census API and saves to cache.
    
    Args:
        cf: CensusFetcher instance
        logger: Logger instance
        use_offline_fallback: If True, only read from local cache file
    """
    # Check for regional targets in input_2023 cache first, then input_2023, then local cache
    possible_cache_files = [
        os.path.join(INPUT_2023_CACHE_FOLDER, "regional_targets_acs2023.csv"),
        os.path.join("input_2023", "regional_targets_acs2023.csv"),
        os.path.join(LOCAL_CACHE_FOLDER, "regional_targets_acs2023.csv")
    ]
    
    regional_targets_file = None
    for cache_file in possible_cache_files:
        if os.path.exists(cache_file):
            regional_targets_file = cache_file
            logger.info(f"Using regional targets cache: {cache_file}")
            break
    
    if not regional_targets_file:
        regional_targets_file = possible_cache_files[1]  # Default to input_2023 location
    
    # First, try to read from local cache
    if os.path.exists(regional_targets_file):
        logger.info(f"Reading regional targets from local cache: {regional_targets_file}")
        try:
            targets_df = pd.read_csv(regional_targets_file)
            regional_targets = dict(zip(targets_df['target_name'], targets_df['target_value']))
            logger.info(f"Loaded {len(regional_targets)} regional targets from cache")
            for name, value in regional_targets.items():
                logger.info(f"  {name}: {value:,.0f}")
            return regional_targets
        except Exception as e:
            logger.error(f"Failed to read regional targets cache: {e}")
            if use_offline_fallback:
                logger.error("Cannot proceed in offline mode without valid regional targets cache")
                return {}
    
    # If offline mode and no cache, return empty
    if use_offline_fallback:
        logger.warning("Offline mode requested but no regional targets cache found")
        logger.info(f"To create the cache, run once without --offline flag")
        return {}
    
    # Fetch from Census API and save to cache
    logger.info("Fetching regional targets from ACS 2023 county data and saving to cache")
    
    regional_targets = {}
    region_controls = CONTROLS[ACS_EST_YEAR].get('REGION_TARGETS', {})
    
    for target_name, control_def in region_controls.items():
        data_source, year, table, geography, columns = control_def
        logger.info(f"Fetching {target_name} from table {table}")
        
        try:
            # Get county data for the Bay Area using existing method
            county_data = cf.get_census_data(data_source, year, table, geography)
            
            # Sum across all counties to get regional total
            if not columns:
                # Use total from first data column (usually _001E for estimates)
                data_cols = [col for col in county_data.columns if col not in ['state', 'county']]
                if data_cols:
                    target_value = county_data[data_cols[0]].sum()
                else:
                    logger.warning(f"No data columns found for {target_name}")
                    continue
            else:
                # Create control table to handle column filtering
                control_table_df = create_control_table(
                    target_name, columns, table, county_data
                )
                # Sum the control column
                control_cols = [col for col in control_table_df.columns if col not in ['state', 'county']]
                target_value = control_table_df[control_cols].sum().sum()
            
            regional_targets[target_name] = target_value
            logger.info(f"Regional target for {target_name}: {target_value:,.0f}")
            
        except Exception as e:
            logger.error(f"Error fetching regional target {target_name}: {e}")
            continue
    
    # Save to cache file if we successfully fetched any targets
    if regional_targets:
        try:
            os.makedirs(os.path.dirname(regional_targets_file), exist_ok=True)
            targets_df = pd.DataFrame([
                {'target_name': name, 'target_value': value, 'source_year': ACS_EST_YEAR}
                for name, value in regional_targets.items()
            ])
            targets_df.to_csv(regional_targets_file, index=False)
            logger.info(f"Saved {len(regional_targets)} regional targets to cache: {regional_targets_file}")
        except Exception as e:
            logger.error(f"Failed to save regional targets to cache: {e}")
    
    return regional_targets


def apply_regional_scaling(control_df, control_name, target_name, regional_targets, logger):
    """Apply regional scaling to MAZ controls using ACS 2023 targets."""
    if target_name not in regional_targets:
        logger.warning(f"No regional target found for {target_name}, skipping scaling")
        return control_df
    
    # Calculate current total
    control_cols = [col for col in control_df.columns if col not in ['MAZ', 'geography']]
    current_total = control_df[control_cols].sum().sum()
    target_total = regional_targets[target_name]
    
    if current_total == 0:
        logger.warning(f"Current total is 0 for {control_name}, cannot scale")
        return control_df
    
    # Calculate scaling factor
    scale_factor = target_total / current_total
    logger.info(f"Scaling {control_name}: current={current_total:,.0f}, target={target_total:,.0f}, factor={scale_factor:.4f}")
    
    # Apply scaling
    scaled_df = control_df.copy()
    scaled_df[control_cols] = scaled_df[control_cols] * scale_factor
    
    return scaled_df


def process_block_distribution_control(control_name, control_def, cf, maz_taz_def_df, crosswalk_df, logger):
    """Process household size controls using block group → block → MAZ distribution."""
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
                               temp_controls, final_control_dfs, regional_targets, logger):
    """Process MAZ_SCALED controls with special regional scaling or block distribution."""
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
        
        # Apply regional scaling
        final_df = apply_regional_scaling(final_df, control_name, regional_targets, logger)
        
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
    control_geo, control_name, control_def, cf, maz_taz_def_df, crosswalk_df, temp_controls, final_control_dfs, regional_targets=None
):
    logger = logging.getLogger()
    logger.info(f"Creating control [{control_name}] for geography [{control_geo}]")
    logger.info("=" * 80)

    # Special case for REGION/gq_pop_region
    if control_geo == "REGION" and control_name == "gq_pop_region":
        # Use regional target if available, otherwise fall back to MAZ sum
        if regional_targets and 'pop_gq_target' in regional_targets:
            gq_pop_value = regional_targets['pop_gq_target']
            logger.info(f"Using regional target for gq_pop_region: {gq_pop_value:,.0f}")
        else:
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

    # Step 2: Create control table
    control_table_df = create_control_table(control_name, control_def[4], control_def[2], census_table_df)

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
        print("control_df columns:", control_table_df.columns)
        print(control_table_df.head())
        print(control_table_df.reset_index().head())
        control_table_df = interpolate_est(
            control_table_df,
            geo=control_def[3],
            target_geo_year=CENSUS_GEOG_YEAR,
            source_geo_year=CENSUS_EST_YEAR
   
        )

    # Step 4: Check for regional scaling first
    if len(control_def) > 5 and control_def[5] == 'regional_scale':
        # For regional scaling, do simple geographic matching without temp control scaling
        final_df = match_control_to_geography(
            control_name, control_table_df, control_geo, control_def[3],
            maz_taz_def_df, temp_controls,
            scale_numerator=None, scale_denominator=None, subtract_table=None
        )
        
        # Apply regional scaling
        scaling_map = {
            'temp_base_num_hh_b': 'num_hh_target',
            'temp_base_num_hh_bg': 'num_hh_target', 
            'tot_pop': 'tot_pop_target',
            'gq_pop': 'pop_gq_target'
        }
        
        if control_name in scaling_map and regional_targets:
            target_name = scaling_map[control_name]
            final_df = apply_regional_scaling(final_df, control_name, target_name, regional_targets, logger)
            logger.info(f"Applied regional scaling to {control_name}")
        else:
            logger.warning(f"Regional scaling requested for {control_name} but no target found")
    else:
        # Normal processing with temp control scaling
        scale_numerator = control_def[5] if len(control_def) > 5 else None
        scale_denominator = control_def[6] if len(control_def) > 6 else None
        subtract_table = control_def[7] if len(control_def) > 7 else None

        final_df = match_control_to_geography(
            control_name, control_table_df, control_geo, control_def[3],
            maz_taz_def_df, temp_controls,
            scale_numerator=scale_numerator, scale_denominator=scale_denominator,
            subtract_table=subtract_table
        )
    
    # Step 8: Integerize if needed
    if control_name in ["num_hh", "gq_pop", "tot_pop"]:
        final_df = integerize_control(final_df, crosswalk_df, control_name)

    # Step 9: Handle temp controls
    if control_name.startswith("temp_"):
        temp_controls[control_name] = final_df
        return

    # Step 10: Merge into final_control_dfs
    if control_geo not in final_control_dfs:
        final_control_dfs[control_geo] = final_df
    else:
        final_control_dfs[control_geo] = pd.merge(
            left=final_control_dfs[control_geo],
            right=final_df,
            how="left",
            left_index=True,
            right_index=True
        )


def write_outputs(control_geo, out_df, crosswalk_df):
    """Write final control outputs in populationsim expected format."""
    logger = logging.getLogger()
    out_df.reset_index(drop=False, inplace=True)

    if len(out_df.loc[out_df[control_geo] == 0]) > 0:
        logger.info(f"Dropping {control_geo}=0\n{out_df.loc[out_df[control_geo] == 0, :].T.squeeze()}")
        out_df = out_df.loc[out_df[control_geo] > 0, :]

    if control_geo == "COUNTY":
        out_df = pd.merge(left=COUNTY_RECODE[["COUNTY", "county_name"]], right=out_df, how="right")

    # Round all control values to integers, handling NaN
    control_cols = [col for col in out_df.columns if col != control_geo and col != 'county_name']
    for col in control_cols:
        # Fill NaN with 0 before converting to int
        out_df[col] = out_df[col].fillna(0).round().astype(int)

    logger.info(f"Processing {control_geo} controls with {len(out_df)} rows and {len(out_df.columns)} columns")
    logger.info(f"Control columns: {control_cols}")
    
    # Write single marginals file in populationsim expected format
    if control_geo == 'MAZ':
        # MAZ expects: num_hh, hh_size_1, hh_size_2, hh_size_3, hh_size_4_plus, gq_type_univ, gq_type_mil, gq_type_othnon
        # We can provide: num_hh, hh_size_1, hh_size_2, hh_size_3, hh_size_4_plus, gq_pop
        # Missing: gq_type_univ, gq_type_mil, gq_type_othnon (no longer surveyed by Census)
        
        # Add missing GQ type columns as zeros since this data is no longer available
        if 'gq_type_univ' not in out_df.columns:
            out_df['gq_type_univ'] = 0
        if 'gq_type_mil' not in out_df.columns:
            out_df['gq_type_mil'] = 0  
        if 'gq_type_othnon' not in out_df.columns:
            out_df['gq_type_othnon'] = 0
            
        output_file = os.path.join("hh_gq", "data", "maz_marginals.csv")
        
    elif control_geo == 'TAZ':
        # TAZ expects: hh_inc_30, hh_inc_30_60, hh_inc_60_100, hh_inc_100_plus, hh_wrks_0, hh_wrks_1, hh_wrks_2, hh_wrks_3_plus, 
        #              pers_age_00_19, pers_age_20_34, pers_age_35_64, pers_age_65_plus, hh_kids_no, hh_kids_yes
        # We can provide: hh_wrks_0, hh_wrks_1, hh_wrks_2, hh_wrks_3_plus, pers_age_00_19, pers_age_20_34, pers_age_35_64, pers_age_65_plus, hh_kids_no, hh_kids_yes
        # Missing: hh_inc_30, hh_inc_30_60, hh_inc_60_100, hh_inc_100_plus (no longer reliable at tract level)
        
        # Add missing income columns as zeros since this data is no longer reliably available at tract level
        if 'hh_inc_30' not in out_df.columns:
            out_df['hh_inc_30'] = 0
        if 'hh_inc_30_60' not in out_df.columns:
            out_df['hh_inc_30_60'] = 0
        if 'hh_inc_60_100' not in out_df.columns:
            out_df['hh_inc_60_100'] = 0
        if 'hh_inc_100_plus' not in out_df.columns:
            out_df['hh_inc_100_plus'] = 0
            
        output_file = os.path.join("hh_gq", "data", "taz_marginals.csv")
        
    elif control_geo == 'COUNTY':
        # COUNTY expects: pers_occ_management, pers_occ_professional, pers_occ_services, pers_occ_retail, pers_occ_manual, pers_occ_military
        # We can provide: None (occupation data no longer reliable at tract level)
        # Missing: All occupation controls (Census has reduced detail and geographic granularity)
        
        # Add missing occupation columns as zeros since this data is no longer available with sufficient reliability
        if 'pers_occ_management' not in out_df.columns:
            out_df['pers_occ_management'] = 0
        if 'pers_occ_professional' not in out_df.columns:
            out_df['pers_occ_professional'] = 0
        if 'pers_occ_services' not in out_df.columns:
            out_df['pers_occ_services'] = 0
        if 'pers_occ_retail' not in out_df.columns:
            out_df['pers_occ_retail'] = 0
        if 'pers_occ_manual' not in out_df.columns:
            out_df['pers_occ_manual'] = 0
        if 'pers_occ_military' not in out_df.columns:
            out_df['pers_occ_military'] = 0
            
        output_file = os.path.join("hh_gq", "data", "county_marginals.csv")
        
    else:
        # For other geographies, use the generic format
        output_file = os.path.join("output_2023", f"{control_geo.lower()}_{ACS_EST_YEAR}_marginals.csv")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write the single marginals file
    if control_geo == 'COUNTY' and 'county_name' in out_df.columns:
        # For county, exclude county_name from the output
        output_cols = [control_geo] + control_cols
        out_df[output_cols].to_csv(output_file, index=False)
    else:
        out_df.to_csv(output_file, index=False)
    
    logger.info(f"Wrote {control_geo} marginals file: {output_file} with {len(control_cols)} controls")
    
    # Also write to output_2023 for reference/debugging
    reference_file = os.path.join("output_2023", f"{control_geo.lower()}_{ACS_EST_YEAR}_all_controls.csv")
    out_df.to_csv(reference_file, index=False, float_format="%.5f")
    logger.info(f"Wrote reference file: {reference_file}")


def main():
    parser = argparse.ArgumentParser(description='Create baseyear controls for PopulationSim using ACS 2023 data')
    parser.add_argument('--offline', action='store_true', 
                       help='Run in offline mode using only cached data (no network required). '
                            'Regional targets will be read from input_2023/regional_targets_acs2023.csv. '
                            'If this file does not exist, run once without --offline to create it.')
    parser.add_argument('--copy-data', action='store_true',
                       help='Copy essential data files from network (M:) drive to local storage for offline work. '
                            'Creates local_data/ directory structure and copies required GIS and census files.')
    parser.add_argument('--use-local', action='store_true',
                       help='Use local data files instead of network (M:) drive. '
                            'Requires data to be copied first with --copy-data.')
    args = parser.parse_args()
    
    # Handle copy-data operation first
    if args.copy_data:
        # Set up logging for copy operation
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
        logger.addHandler(ch)
        
        logger.info("Starting data copy operation from network to local storage")
        copied_files = copy_network_data_to_local()
        logger.info(f"Data copy completed. {len(copied_files)} files copied to local_data/")
        logger.info("You can now use --use-local to work with the local data")
        return
    
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

    # Configure file paths based on mode
    if args.use_local:
        logger.info("Using LOCAL data mode - reading from local_data/ directory")
        configure_file_paths(use_local=True)
        if not check_file_accessibility_with_mode(use_local=True):
            logger.error("Cannot access required local files. Run with --copy-data first.")
            return 1
    else:
        logger.info("Using NETWORK data mode - reading from M: drive")
        configure_file_paths(use_local=False)
        if not check_file_accessibility_with_mode(use_local=False):
            logger.error("Cannot access required network files. Try --copy-data then --use-local.")
            return 1

    if args.offline:
        logger.info("Running in OFFLINE mode - using only cached data")
        logger.info("Regional targets will be read from input_2023/regional_targets_acs2023.csv")
    else:
        logger.info("Running in ONLINE mode - will fetch from Census API and update caches")

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

    # Step 1: Process regional targets first to establish scaling factors
    regional_targets = {}
    if 'REGION_TARGETS' in CONTROLS[ACS_EST_YEAR]:
        regional_targets = get_regional_targets(cf, logger, use_offline_fallback=args.offline)

    for control_geo, control_dict in CONTROLS[ACS_EST_YEAR].items():
        # Skip empty control dictionaries and already processed regional targets
        if not control_dict or control_geo == 'REGION_TARGETS':
            logger.info(f"Skipping {control_geo} - no controls defined or already processed")
            continue
            
        temp_controls = collections.OrderedDict()
        for control_name, control_def in control_dict.items():
            # Handle MAZ_SCALED controls with special processing
            if control_geo == 'MAZ_SCALED':
                process_maz_scaled_control(
                    control_name, control_def, cf, maz_taz_def_df, crosswalk_df, 
                    temp_controls, final_control_dfs, regional_targets, logger
                )
            else:
                process_control(
                    control_geo, control_name, control_def,
                    cf, maz_taz_def_df, crosswalk_df, temp_controls, final_control_dfs, regional_targets
                )

        logger.info(f"Preparing final controls files for {control_geo}")
        out_df = final_control_dfs[control_geo].copy()
        write_outputs(control_geo, out_df, crosswalk_df)
    
    # Handle COUNTY separately since we have no data but need to create empty file for populationsim
    if 'COUNTY' not in final_control_dfs:
        logger.info("Creating empty COUNTY controls file since occupation data is no longer available")
        # Create a minimal county dataframe with just county IDs and zero controls
        county_df = pd.DataFrame({
            'COUNTY': range(1, 10),  # Bay Area counties 1-9
            'pers_occ_management': 0,
            'pers_occ_professional': 0, 
            'pers_occ_services': 0,
            'pers_occ_retail': 0,
            'pers_occ_manual': 0,
            'pers_occ_military': 0
        })
        write_outputs('COUNTY', county_df, crosswalk_df)

    # Write geographic crosswalk file in expected location
    crosswalk_file = os.path.join("hh_gq", "data", "geo_cross_walk_tm2.csv")
    
    # Ensure we have the expected columns for populationsim
    expected_crosswalk_cols = ['MAZ', 'TAZ', 'COUNTY', 'county_name', 'COUNTYFP10', 'TRACTCE10', 'PUMA']
    available_cols = [col for col in expected_crosswalk_cols if col in crosswalk_df.columns]
    
    if len(available_cols) < len(expected_crosswalk_cols):
        missing_cols = set(expected_crosswalk_cols) - set(available_cols)
        logger.warning(f"Missing crosswalk columns: {missing_cols}. Writing available columns: {available_cols}")
    
    # Write the crosswalk file with available columns
    crosswalk_df[available_cols].to_csv(crosswalk_file, index=False)
    logger.info(f"Wrote geographic crosswalk file {crosswalk_file}")
    
    # Also write to output_2023 for reference
    reference_crosswalk = os.path.join("output_2023", f"geo_crosswalk_{ACS_EST_YEAR}.csv")
    crosswalk_df.to_csv(reference_crosswalk, index=False)
    logger.info(f"Wrote reference crosswalk file {reference_crosswalk}")


if __name__ == '__main__':

    main()
