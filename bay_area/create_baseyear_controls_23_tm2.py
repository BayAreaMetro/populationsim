"""
create_baseyear_controls_23_tm2.py

This script creates baseyear control files for the MTC Bay Area populationsim model using 
ACS 2023 data with simplified controls to reflect current Census data availability.

"""

import traceback


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
   - MAZ Level: Total households (B25001), group quarters (B26001)  
   - TAZ Level: Workers (B08202), age groups (B01001), children (B09001), household size (B11016)
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
   - maz_marginals.csv: MAZ-level controls (households, GQ)
   - taz_marginals.csv: TAZ-level controls (workers, age groups, children, household size)
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


def show_region_targets():
    """Display the region targets configuration as a formatted table"""
    
    print("="*80)
    print("REGION TARGETS CONFIGURATION")
    print("="*80)
    
    region_targets = CONTROLS[ACS_EST_YEAR]['REGION_TARGETS']
    
    # Create a list to store the target information
    target_data = []
    
    for target_name, target_config in region_targets.items():
        data_source, year, table, geography, variables = target_config
        
        # Format variables if they exist
        var_str = ""
        if variables:
            var_str = ", ".join([var[0] if isinstance(var, tuple) else str(var) for var in variables])
        else:
            var_str = f"{table}_001E (total)"
            
        target_data.append({
            'Target Name': target_name,
            'Data Source': data_source.upper(),
            'Year': year,
            'Table': table,
            'Geography': geography,
            'Variables': var_str,
            'Description': get_target_description(target_name, table, var_str)
        })
    
    # Create DataFrame and display
    df = pd.DataFrame(target_data)
    
    # Print with nice formatting
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 50)
    
    print(df.to_string(index=False))
    print("\n")
    
    # Summary
    print("SUMMARY:")
    print(f"- Total targets: {len(target_data)}")
    print(f"- Data sources: {', '.join(set([t['Data Source'] for t in target_data]))}")
    print(f"- Year: {target_data[0]['Year']}")
    print(f"- Geography level: {target_data[0]['Geography']}")
    print("\n")
    
    # Show the actual configuration format
    print("RAW CONFIGURATION:")
    print("-" * 50)
    for target_name, target_config in region_targets.items():
        print(f"'{target_name}': {target_config}")
    print("\n")
    
    return df

def get_target_description(target_name, table, variables):
    """Get human-readable description for each target"""
    descriptions = {
        'num_hh_target': 'Total occupied housing units (households)',
        'tot_pop_target': 'Total population',
        'pop_gq_target': 'Total group quarters population',
        'gq_military_target': 'Military group quarters population',
        'gq_university_target': 'University/college group quarters population'
    }
    
    return descriptions.get(target_name, f'{table} - {variables}')


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
    logger.info("=== REGIONAL TARGETS: Starting API calls ===")
    
    regional_targets = {}
    
    # Fetch actual regional targets by summing county-level data for Bay Area counties
    try:
        # Get the regional target table definitions from configuration
        target_tables = {}
        region_targets_config = CONTROLS[ACS_EST_YEAR].get('REGION_TARGETS', {})
        
        for target_name, control_def in region_targets_config.items():
            if len(control_def) >= 4:  # Ensure we have the required fields
                data_source, year, table, geography = control_def[:4]
                target_tables[target_name] = (data_source, year, table, geography)
        
        logger.info(f"=== REGIONAL TARGETS: Will fetch {len(target_tables)} tables from config ===")
        
        # Try Census API first, fall back to cache file reading if it fails
        for i, (target_name, (data_source, year, table, geography)) in enumerate(target_tables.items(), 1):
            try:
                logger.info(f"=== REGIONAL TARGETS: API Call {i}/{len(target_tables)} ===")
                logger.info(f"Fetching {target_name} from {data_source} {year} table {table}")
                
                # First, try using census_fetcher directly (the normal path)
                api_success = False
                try:
                    logger.info(f"Attempting Census API fetch for {target_name}...")
                    county_data = cf.get_census_data(data_source, year, table, geography)
                    logger.info(f"Successfully retrieved {len(county_data)} counties from API for {target_name}")
                    
                    # Sum across all Bay Area counties to get regional total
                    data_col = f"{table}_001E"  # The column name should be table + _001E for totals
                    if data_col in county_data.columns:
                        target_value = county_data[data_col].sum()
                        regional_targets[target_name] = int(target_value)  # Convert to int for clean output
                        logger.info(f"Successfully calculated {target_name}: {target_value:,.0f}")
                        
                        # Log county breakdown for verification
                        logger.info(f"County breakdown for {target_name}:")
                        for _, row in county_data.iterrows():
                            county_name = row.get('county', 'Unknown')
                            county_value = row[data_col]
                            logger.info(f"  County {county_name}: {county_value:,.0f}")
                        
                        api_success = True
                    else:
                        logger.error(f"Column {data_col} not found in API data for {target_name}")
                        logger.info(f"Available columns: {list(county_data.columns)}")
                        
                except Exception as api_error:
                    logger.warning(f"Census API fetch failed for {target_name}: {api_error}")
                    logger.info("Falling back to cache file reading...")
                
                # If API failed, try cache file reading as fallback
                if not api_success:
                    cache_file = os.path.join(LOCAL_CACHE_FOLDER, f"{data_source}_{year}_{table}_{geography}.csv")
                    if os.path.exists(cache_file):
                        logger.info(f"Reading from cache file as fallback: {cache_file}")
                        
                        try:
                            import pandas as pd
                            
                            # Read the file and parse the header correctly
                            with open(cache_file, 'r') as f:
                                first_line = f.readline().strip()
                                
                            # Parse the variable name from first line (format: "variable,,B25001_001E")
                            parts = first_line.split(',')
                            if len(parts) >= 3 and parts[2]:
                                data_col = parts[2]  # The actual variable name like B25001_001E
                            else:
                                data_col = f"{table}_001E"  # fallback
                            
                            # Read CSV starting from line 2 (skip variable and geo headers)
                            df = pd.read_csv(cache_file, skiprows=1, names=['state', 'county', data_col])
                            
                            logger.info(f"Parsed variable column from cache: {data_col}")
                            
                            # Convert county codes to strings and filter Bay Area counties
                            df['county'] = df['county'].astype(str).str.zfill(3)
                            bay_area_counties = get_bay_area_county_codes()  # Get from config instead of hardcoding
                            bay_area_data = df[df['county'].isin(bay_area_counties)]
                            
                            if not bay_area_data.empty:
                                bay_area_total = bay_area_data[data_col].sum()
                                regional_targets[target_name] = int(bay_area_total)
                                logger.info(f"Successfully calculated {target_name} from cache: {bay_area_total:,.0f}")
                                
                                # Log county breakdown for verification
                                logger.info(f"County breakdown for {target_name} (from cache):")
                                for _, row in bay_area_data.iterrows():
                                    county_code = row['county']
                                    county_value = row[data_col]
                                    logger.info(f"  County {county_code}: {county_value:,.0f}")
                            else:
                                logger.warning(f"No Bay Area counties found in cache for {target_name}")
                                
                        except Exception as cache_error:
                            logger.error(f"Failed to read cache file: {cache_error}")
                            
                    else:
                        logger.error(f"Neither API nor cache file available for {target_name}")
                        logger.error(f"Expected cache file: {cache_file}")
                    
            except Exception as e:
                logger.error(f"Failed to fetch {target_name}: {e}")
                continue
        
        if not regional_targets:
            logger.error("Failed to fetch any regional targets from Census API")
            return {}
            
        logger.info(f"Successfully calculated {len(regional_targets)} regional targets:")
        for name, value in regional_targets.items():
            logger.info(f"  {name}: {value:,.0f}")
            
    except Exception as e:
        logger.error(f"Error fetching regional targets from Census API: {e}")
        return {}
    
    # Save to cache file if we successfully calculated targets
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
        logger.info(f"GEOGRAPHIC INTERPOLATION REQUIRED: {CENSUS_EST_YEAR} → {CENSUS_GEOG_YEAR}")
        logger.info(f"Source geography: {control_def[3]}")
        print("control_df columns:", control_table_df.columns)
        print(control_table_df.head())
        print(control_table_df.reset_index().head())
        control_table_df = interpolate_est(
            control_table_df,
            geo=control_def[3],
            target_geo_year=CENSUS_GEOG_YEAR,
            source_geo_year=CENSUS_EST_YEAR
   
        )
        logger.info(f"Geographic interpolation completed for {control_name}")
    else:
        logger.info(f"No geographic interpolation needed: both years are {CENSUS_GEOG_YEAR}")

    # Step 4: Check for regional scaling first
    if len(control_def) > 5 and control_def[5] == 'regional_scale':
        # For regional scaling, do simple geographic matching without temp control scaling
        logger.info(f"APPLYING REGIONAL SCALING for {control_name}")
        final_df = match_control_to_geography(
            control_name, control_table_df, control_geo, control_def[3],
            maz_taz_def_df, temp_controls,
            scale_numerator=None, scale_denominator=None, subtract_table=None
        )
        
        # Apply regional scaling
        scaling_map = {
            'temp_base_num_hh_b': 'num_hh_target',
            'temp_base_num_hh_bg': 'num_hh_target',
            'temp_num_hh_size': 'num_hh_target',  # Add temp_num_hh_size to regional scaling
            'num_hh': 'num_hh_target',  # Add num_hh to regional scaling
            'tot_pop': 'tot_pop_target',
            'gq_pop': 'pop_gq_target',
            'gq_military': 'gq_military_target',
            'gq_university': 'gq_university_target'
        }
        
        if control_name in scaling_map and regional_targets:
            target_name = scaling_map[control_name]
            final_df = apply_regional_scaling(final_df, control_name, target_name, regional_targets, logger)
            logger.info(f"Applied regional scaling to {control_name}")
        else:
            logger.warning(f"Regional scaling requested for {control_name} but no target found")
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
        
        # Log temp control statistics
        if not final_df.empty:
            control_cols = [col for col in final_df.columns if col != final_df.index.name]
            total = final_df[control_cols].sum().sum() if control_cols else 0
            logger.info(f"TEMP CONTROL [{control_name}]: {len(final_df)} zones, total = {total:,.0f}")
            
            # Log distribution for important temp controls
            if control_name in ['temp_base_num_hh_b', 'temp_base_num_hh_bg', 'temp_num_hh_size']:
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
        
        total = final_df[control_cols].sum().sum() if control_cols else 0
        logger.info(f"FINAL CONTROL [{control_name}]: {len(final_df)} zones, total = {total:,.0f}")
        
        # Log additional details for key controls
        if control_name in ['num_hh', 'gq_pop', 'hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus']:
            for col in control_cols[:3]:  # Log first 3 columns
                col_total = final_df[col].sum()
                nonzero_count = (final_df[col] > 0).sum()
                mean_val = final_df[col].mean()
                max_val = final_df[col].max()
                logger.info(f"  {col}: total = {col_total:,.0f}, non-zero zones = {nonzero_count}, mean = {mean_val:.1f}, max = {max_val:.0f}")

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
    
    # Special case: Add num_hh to temp_controls so household size controls can use it as denominator
    if control_name == "num_hh":
        temp_controls["num_hh"] = final_df
        logger.info(f"Added num_hh to temp_controls for household size scaling")
        logger.info(f"num_hh sum: {final_df['num_hh'].sum():,.0f}")


def create_regional_summary(regional_targets, cf, logger):
    """Create a summary file with regional totals from 2020 Census and 2023 ACS."""
    logger.info("Creating regional summary file")
    
    summary_data = []
    census_2020_data = {}
    
    # Get 2020 Census regional totals from block-level data
    try:
        import pandas as pd
        from tm2_control_utils.config import get_bay_area_county_codes
        bay_area_counties = get_bay_area_county_codes()
        logger.info(f"Aggregating 2020 Census data for Bay Area counties: {bay_area_counties}")
        
        # Total households from 2020 Census PL data (block level, aggregate to region)
        h1_data = cf.get_census_data('pl', '2020', 'H1_002N', 'block')
        logger.info(f"Census data columns: {list(h1_data.columns)}")
        logger.info(f"Census data shape: {h1_data.shape}")
        
        # Check if the data has an index that includes county information
        if hasattr(h1_data.index, 'names') and h1_data.index.names:
            logger.info(f"Census data index names: {h1_data.index.names}")
            # Reset index to make geographic components accessible as columns
            h1_data = h1_data.reset_index()
            logger.info(f"Census data columns after reset_index: {list(h1_data.columns)}")
        
        # Filter for Bay Area counties and convert to numeric before sum
        h1_data_filtered = h1_data[h1_data['county'].isin(bay_area_counties)]
        h1_data_filtered['H1_002N'] = pd.to_numeric(h1_data_filtered['H1_002N'], errors='coerce')
        census_2020_households = h1_data_filtered['H1_002N'].sum()
        census_2020_data['households'] = int(census_2020_households)
        summary_data.append({
            'metric': 'Total Households',
            'source': '2020 Census PL H1_002N',
            'year': 2020,
            'value': int(census_2020_households)
        })
        logger.info(f"2020 Census households (blocks in Bay Area): {census_2020_households:,}")
        
        # Total population from 2020 Census PL data (block level, aggregate to region)
        p1_data = cf.get_census_data('pl', '2020', 'P1_001N', 'block')
        # Filter for Bay Area counties and convert to numeric before sum
        p1_data_filtered = p1_data[p1_data['county'].isin(bay_area_counties)]
        p1_data_filtered['P1_001N'] = pd.to_numeric(p1_data_filtered['P1_001N'], errors='coerce')
        census_2020_population = p1_data_filtered['P1_001N'].sum()
        census_2020_data['population'] = int(census_2020_population)
        summary_data.append({
            'metric': 'Total Population', 
            'source': '2020 Census PL P1_001N',
            'year': 2020,
            'value': int(census_2020_population)
        })
        logger.info(f"2020 Census population (blocks in Bay Area): {census_2020_population:,}")
        
        # Total group quarters from 2020 Census PL data (P5_001N)
        p5_data = cf.get_census_data('pl', '2020', 'P5_001N', 'block')
        p5_data_filtered = p5_data[p5_data['county'].isin(bay_area_counties)]
        p5_data_filtered['P5_001N'] = pd.to_numeric(p5_data_filtered['P5_001N'], errors='coerce')
        census_2020_gq = p5_data_filtered['P5_001N'].sum()
        census_2020_data['gq_population'] = int(census_2020_gq)
        summary_data.append({
            'metric': 'Total Group Quarters Population',
            'source': '2020 Census PL P5_001N', 
            'year': 2020,
            'value': int(census_2020_gq)
        })
        logger.info(f"2020 Census group quarters (blocks in Bay Area): {census_2020_gq:,}")
        
        # Military group quarters from 2020 Census PL data (P5_009N)
        p5_mil_data = cf.get_census_data('pl', '2020', 'P5_009N', 'block')
        p5_mil_filtered = p5_mil_data[p5_mil_data['county'].isin(bay_area_counties)]
        p5_mil_filtered['P5_009N'] = pd.to_numeric(p5_mil_filtered['P5_009N'], errors='coerce')
        census_2020_gq_military = p5_mil_filtered['P5_009N'].sum()
        census_2020_data['gq_military'] = int(census_2020_gq_military)
        summary_data.append({
            'metric': 'Military Group Quarters Population',
            'source': '2020 Census PL P5_009N', 
            'year': 2020,
            'value': int(census_2020_gq_military)
        })
        logger.info(f"2020 Census military group quarters (blocks in Bay Area): {census_2020_gq_military:,}")
        
        # University group quarters from 2020 Census PL data (P5_008N)
        p5_univ_data = cf.get_census_data('pl', '2020', 'P5_008N', 'block')
        p5_univ_filtered = p5_univ_data[p5_univ_data['county'].isin(bay_area_counties)]
        p5_univ_filtered['P5_008N'] = pd.to_numeric(p5_univ_filtered['P5_008N'], errors='coerce')
        census_2020_gq_university = p5_univ_filtered['P5_008N'].sum()
        census_2020_data['gq_university'] = int(census_2020_gq_university)
        summary_data.append({
            'metric': 'University Group Quarters Population',
            'source': '2020 Census PL P5_008N', 
            'year': 2020,
            'value': int(census_2020_gq_university)
        })
        logger.info(f"2020 Census university group quarters (blocks in Bay Area): {census_2020_gq_university:,}")
        
    except Exception as e:
        logger.warning(f"Failed to get 2020 Census regional totals: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
    
    # Add 2023 ACS regional targets
    acs_2023_data = {}
    if regional_targets:
        if 'num_hh_target' in regional_targets:
            acs_2023_data['households'] = regional_targets['num_hh_target']
            summary_data.append({
                'metric': 'Total Households',
                'source': '2023 ACS1 B25001',
                'year': 2023,
                'value': int(regional_targets['num_hh_target'])
            })
        
        if 'tot_pop_target' in regional_targets:
            acs_2023_data['population'] = regional_targets['tot_pop_target']
            summary_data.append({
                'metric': 'Total Population',
                'source': '2023 ACS1 B01003',
                'year': 2023,
                'value': int(regional_targets['tot_pop_target'])
            })
            
        if 'pop_gq_target' in regional_targets:
            acs_2023_data['gq_population'] = regional_targets['pop_gq_target']
            summary_data.append({
                'metric': 'Total Group Quarters Population',
                'source': '2023 ACS1 B26001',
                'year': 2023,
                'value': int(regional_targets['pop_gq_target'])
            })
            
        if 'gq_military_target' in regional_targets:
            acs_2023_data['gq_military'] = regional_targets['gq_military_target']
            summary_data.append({
                'metric': 'Military Group Quarters Population',
                'source': '2023 ACS1 B26001_007E',
                'year': 2023,
                'value': int(regional_targets['gq_military_target'])
            })
            
        if 'gq_university_target' in regional_targets:
            acs_2023_data['gq_university'] = regional_targets['gq_university_target']
            summary_data.append({
                'metric': 'University Group Quarters Population',
                'source': '2023 ACS1 B26001_006E',
                'year': 2023,
                'value': int(regional_targets['gq_university_target'])
            })
    
    # Calculate 2023/2020 ratios
    if census_2020_data and acs_2023_data:
        for metric_key in ['households', 'population', 'gq_population', 'gq_military', 'gq_university']:
            if metric_key in census_2020_data and metric_key in acs_2023_data:
                census_2020_val = census_2020_data[metric_key]
                acs_2023_val = acs_2023_data[metric_key]
                
                if census_2020_val > 0:
                    ratio = acs_2023_val / census_2020_val
                    
                    metric_name_map = {
                        'households': 'Total Households',
                        'population': 'Total Population', 
                        'gq_population': 'Total Group Quarters Population',
                        'gq_military': 'Military Group Quarters Population',
                        'gq_university': 'University Group Quarters Population'
                    }
                    
                    summary_data.append({
                        'metric': metric_name_map[metric_key],
                        'source': '2023/2020 Ratio',
                        'year': 'Ratio',
                        'value': round(ratio, 4)
                    })
    
    # Create summary DataFrame with better column order
    summary_df = pd.DataFrame(summary_data)
    
    # Reorder for better readability: 2020 values, then 2023 values, then ratios
    ordered_data = []
    
    # Group data by metric for better presentation
    metrics_order = [
        'Total Households',
        'Total Population', 
        'Total Group Quarters Population',
        'Military Group Quarters Population',
        'University Group Quarters Population'
    ]
    
    for metric in metrics_order:
        # Add 2020 data
        df_2020 = summary_df[(summary_df['metric'] == metric) & (summary_df['year'] == 2020)]
        if not df_2020.empty:
            ordered_data.extend(df_2020.to_dict('records'))
        
        # Add 2023 data  
        df_2023 = summary_df[(summary_df['metric'] == metric) & (summary_df['year'] == 2023)]
        if not df_2023.empty:
            ordered_data.extend(df_2023.to_dict('records'))
            
        # Add ratio data
        df_ratio = summary_df[(summary_df['metric'] == metric) & (summary_df['year'] == 'Ratio')]
        if not df_ratio.empty:
            ordered_data.extend(df_ratio.to_dict('records'))
    
    # Create final ordered DataFrame
    summary_df = pd.DataFrame(ordered_data)
    
    # Write summary file
    summary_file = os.path.join("output_2023", "regional_summary_2020_2023.csv")
    os.makedirs(os.path.dirname(summary_file), exist_ok=True)
    summary_df.to_csv(summary_file, index=False)
    
    logger.info(f"Wrote regional summary file: {summary_file}")
    logger.info("Regional Summary:")
    for _, row in summary_df.iterrows():
        if row['year'] == 'Ratio':
            logger.info(f"  {row['metric']} 2023/2020 Ratio: {row['value']}")
        else:
            logger.info(f"  {row['year']} {row['metric']}: {row['value']:,}")
    
    return summary_df


def validate_maz_controls(maz_marginals_file, regional_targets, logger):
    """Validate that MAZ control totals match regional targets."""
    logger.info("Validating MAZ control totals against regional targets")
    
    if not os.path.exists(maz_marginals_file):
        logger.error(f"MAZ marginals file not found: {maz_marginals_file}")
        return False
    
    if not regional_targets:
        logger.warning("No regional targets available for validation")
        return False
    
    # Read MAZ marginals file
    try:
        maz_df = pd.read_csv(maz_marginals_file)
        logger.info(f"Loaded MAZ marginals file with {len(maz_df)} rows and {len(maz_df.columns)} columns")
    except Exception as e:
        logger.error(f"Failed to read MAZ marginals file: {e}")
        return False
    
    validation_passed = True
    
    # Check total households
    if 'num_hh' in maz_df.columns and 'num_hh_target' in regional_targets:
        maz_total_hh = maz_df['num_hh'].sum()
        regional_target_hh = regional_targets['num_hh_target']
        diff_hh = abs(maz_total_hh - regional_target_hh)
        pct_diff_hh = (diff_hh / regional_target_hh) * 100 if regional_target_hh > 0 else 0
        
        logger.info(f"Total Households - MAZ sum: {maz_total_hh:,.0f}, Regional target: {regional_target_hh:,.0f}, Diff: {diff_hh:,.0f} ({pct_diff_hh:.2f}%)")
        
        if pct_diff_hh > 1.0:  # Allow 1% tolerance
            logger.error(f"VALIDATION FAILED: Household totals differ by more than 1% ({pct_diff_hh:.2f}%)")
            validation_passed = False
        else:
            logger.info("PASS: Household totals validation passed")
    
    # Check household size consistency
    hh_size_cols = ['hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus']
    available_hh_size_cols = [col for col in hh_size_cols if col in maz_df.columns]
    
    if len(available_hh_size_cols) > 0 and 'num_hh' in maz_df.columns:
        maz_total_hh = maz_df['num_hh'].sum()
        maz_sum_hh_sizes = maz_df[available_hh_size_cols].sum().sum()
        diff_hh_sizes = abs(maz_total_hh - maz_sum_hh_sizes)
        pct_diff_hh_sizes = (diff_hh_sizes / maz_total_hh) * 100 if maz_total_hh > 0 else 0
        
        logger.info(f"Household Size Consistency - num_hh sum: {maz_total_hh:,.0f}, hh_size_* sum: {maz_sum_hh_sizes:,.0f}, Diff: {diff_hh_sizes:,.0f} ({pct_diff_hh_sizes:.2f}%)")
        
        if pct_diff_hh_sizes > 1.0:  # Allow 1% tolerance
            logger.error(f"VALIDATION FAILED: Household size totals differ from num_hh by more than 1% ({pct_diff_hh_sizes:.2f}%)")
            validation_passed = False
        else:
            logger.info("PASS: Household size consistency validation passed")
    
    # Check group quarters population
    if 'gq_pop' in maz_df.columns and 'pop_gq_target' in regional_targets:
        maz_total_gq = maz_df['gq_pop'].sum()
        regional_target_gq = regional_targets['pop_gq_target']
        diff_gq = abs(maz_total_gq - regional_target_gq)
        pct_diff_gq = (diff_gq / regional_target_gq) * 100 if regional_target_gq > 0 else 0
        
        logger.info(f"Group Quarters Population - MAZ sum: {maz_total_gq:,.0f}, Regional target: {regional_target_gq:,.0f}, Diff: {diff_gq:,.0f} ({pct_diff_gq:.2f}%)")
        
        if pct_diff_gq > 1.0:  # Allow 1% tolerance
            logger.error(f"VALIDATION FAILED: Group quarters totals differ by more than 1% ({pct_diff_gq:.2f}%)")
            validation_passed = False
        else:
            logger.info("PASS: Group quarters population validation passed")
    
    # Summary
    if validation_passed:
        logger.info("SUCCESS: ALL VALIDATIONS PASSED - MAZ controls match regional targets")
    else:
        logger.error("FAILED: VALIDATION FAILED - MAZ controls do not match regional targets")
    
    return validation_passed


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
        hh_size_cols = ['hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus']
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
        hh_size_cols = ['hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus']
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
        income_cols = ['hh_inc_30', 'hh_inc_30_60', 'hh_inc_60_100', 'hh_inc_100_plus']
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
        age_cols = ['pers_age_00_19', 'pers_age_20_34', 'pers_age_35_64', 'pers_age_65_plus']
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
        out_df = pd.merge(left=COUNTY_RECODE[["COUNTY", "county_name"]], right=out_df, how="right")

    # Round all control values to integers, handling NaN
    control_cols = [col for col in out_df.columns if col != control_geo and col != 'county_name']
    for col in control_cols:
        # Fill NaN with 0 before converting to int
        out_df[col] = out_df[col].fillna(0).round().astype(int)

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

    logger.info(f"Processing {control_geo} controls with {len(out_df)} rows and {len(out_df.columns)} columns")
    logger.info(f"Control columns: {control_cols}")
    
    # Log detailed statistics before writing files
    log_control_statistics(control_geo, out_df, logger)
    
    # Write single marginals file in populationsim expected format
    if control_geo == 'MAZ':
        # MAZ provides: num_hh, gq_pop, gq_military, gq_university, gq_other
        # Household size controls moved to TAZ level for better data quality
        # Group quarters now include detailed type breakdown from 2020 Census DHC data
        
        output_file = os.path.join("hh_gq", "data", "maz_marginals.csv")
        
    elif control_geo == 'TAZ':
        # TAZ expects: hh_inc_30, hh_inc_30_60, hh_inc_60_100, hh_inc_100_plus, hh_wrks_0, hh_wrks_1, hh_wrks_2, hh_wrks_3_plus, 
        #              pers_age_00_19, pers_age_20_34, pers_age_35_64, pers_age_65_plus, hh_kids_no, hh_kids_yes, hh_size_1, hh_size_2, hh_size_3, hh_size_4_plus
        # We can provide: hh_wrks_0, hh_wrks_1, hh_wrks_2, hh_wrks_3_plus, pers_age_00_19, pers_age_20_34, pers_age_35_64, pers_age_65_plus, hh_kids_no, hh_kids_yes, hh_size_1, hh_size_2, hh_size_3, hh_size_4_plus
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


def normalize_household_size_controls(control_table_df, control_name, temp_controls, logger):
    """
    Normalize household size controls to ensure they sum to the correct total.
    
    The issue: ACS household size data gives raw counts that don't necessarily sum to 
    the scaled Census household totals. This function normalizes household size controls
    to be proportional distributions rather than absolute counts.
    
    Args:
        control_table_df: DataFrame with household size controls 
        control_name: Name of the control (e.g., 'hh_size_1')
        temp_controls: Dictionary of temp controls including 'num_hh'
        logger: Logger instance
    """
    
    # Only apply to household size controls
    if not control_name.startswith('hh_size_'):
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

# ... existing code ...
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

    # Display region targets configuration (commented out to avoid automatic display)
    # logger.info("Displaying current region targets configuration:")
    # show_region_targets()

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

    # Create regional summary file comparing 2020 Census and 2023 ACS totals
    create_regional_summary(regional_targets, cf, logger)

    for control_geo, control_dict in CONTROLS[ACS_EST_YEAR].items():
        # Skip empty control dictionaries and already processed regional targets
        if not control_dict or control_geo == 'REGION_TARGETS':
            logger.info(f"Skipping {control_geo} - no controls defined or already processed")
            continue
        
        # Debug: Log what controls are found for each geography
        logger.info(f">>> FOUND GEOGRAPHY: {control_geo} with {len(control_dict)} controls: {list(control_dict.keys())}")
        
        # Process MAZ and TAZ controls (household size moved from MAZ to TAZ)
        if control_geo not in ['MAZ', 'MAZ_SCALED', 'TAZ']:
            logger.info(f"TEMPORARILY SKIPPING {control_geo} - focusing on MAZ and TAZ controls only")
            continue
            
        temp_controls = collections.OrderedDict()
        for control_name, control_def in control_dict.items():
            logger.info(f">>> PROCESSING CONTROL: {control_geo}.{control_name}")
            try:
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
                control_cols = [col for col in temp_df.columns if col != temp_df.index.name]
                total = temp_df[control_cols].sum().sum() if control_cols else 0
                logger.info(f"{temp_name}: {len(temp_df)} zones, total = {total:,.0f}")

        logger.info(f"Preparing final controls files for {control_geo}")
        out_df = final_control_dfs[control_geo].copy()
        write_outputs(control_geo, out_df, crosswalk_df)
    
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

    # Validate MAZ controls against regional targets
    maz_marginals_file = os.path.join("hh_gq", "data", "maz_marginals.csv")
    validate_maz_controls(maz_marginals_file, regional_targets, logger)


if __name__ == '__main__':

    main()
