#!/usr/bin/env python

"""
Create baseyear controls for MTC Bay Area populationsim with regional scaling.

This script implements the new workflow with:
1. Regional targets from ACS 2023 county-level data
2. Regional scaling of basic controls (2020 Census → 2010 MAZ → scaled to ACS 2023)
3. Block group distribution for household size controls (no problematic scaling)

Based on create_baseyear_controls_23_tm2.py but with improved workflow.
"""

import argparse, collections, logging, os, sys, pathlib
import numpy as np, pandas as pd

# Import existing functions from the main script
sys.path.insert(0, '.')
from create_baseyear_controls import (
    CensusFetcher, 
    create_control_table,
    match_control_to_geography,
    integerize_control,
    stochastic_round
)

# Configuration constants
ACS_EST_YEAR = 2023
CENSUS_EST_YEAR = 2020
NPER_MAX = 10

# Bay Area county FIPS codes
BAY_AREA_COUNTY_FIPS = collections.OrderedDict([
    ("Alameda", "001"),
    ("Contra Costa", "013"),
    ("Marin", "041"),
    ("Napa", "055"),
    ("San Francisco", "075"),
    ("San Mateo", "081"),
    ("Santa Clara", "085"),
    ("Solano", "095"),
    ("Sonoma", "097"),
])

# Output formats
OUTPUT_DIR_FMT = "output_{}"
CONTROL_FILE_FMT = "{}_{}_controls.csv"
HOUSEHOLDS_DIR = "households"
DATA_SUBDIR = "data"
GEO_CROSSWALK_FILE = "geo_cross_walk.csv"

# Define the new control structures
CONTROLS = {
    ACS_EST_YEAR: {
        'MAZ_SCALED': collections.OrderedDict([
            # Basic controls from 2020 Census aggregated to MAZ, then regionally scaled to ACS 2023 targets
            ('tot_pop', ('pl', CENSUS_EST_YEAR, 'P1_001N', 'block', [], 'regional_scale')),
            ('pop_hh', ('pl', CENSUS_EST_YEAR, 'P1_002N', 'block', [], 'regional_scale')),
            ('pop_gq', ('pl', CENSUS_EST_YEAR, 'P1_003N', 'block', [], 'regional_scale')),
            ('tot_hu', ('pl', CENSUS_EST_YEAR, 'H1_001N', 'block', [], 'regional_scale')),
            ('occ_hu', ('pl', CENSUS_EST_YEAR, 'H1_002N', 'block', [], 'regional_scale')),
            ('vac_hu', ('pl', CENSUS_EST_YEAR, 'H1_003N', 'block', [], 'regional_scale')),
            
            # Household size controls: block group→block→MAZ distribution (NO regional scaling)
            ('hh_size_1', ('acs5', ACS_EST_YEAR, 'B11016', 'block group',
                           [collections.OrderedDict([('pers_min', 1), ('pers_max', 1)])],
                           'block_distribution')),
            ('hh_size_2', ('acs5', ACS_EST_YEAR, 'B11016', 'block group',
                           [collections.OrderedDict([('pers_min', 2), ('pers_max', 2)])],
                           'block_distribution')),
            ('hh_size_3', ('acs5', ACS_EST_YEAR, 'B11016', 'block group',
                           [collections.OrderedDict([('pers_min', 3), ('pers_max', 3)])],
                           'block_distribution')),
            ('hh_size_4_plus', ('acs5', ACS_EST_YEAR, 'B11016', 'block group',
                               [collections.OrderedDict([('pers_min', 4), ('pers_max', NPER_MAX)])],
                               'block_distribution')),
        ]),
        
        'REGION_TARGETS': collections.OrderedDict([
            ('tot_pop_target', ('acs5', ACS_EST_YEAR, 'B01003', 'county', [])),
            ('pop_gq_target', ('acs5', ACS_EST_YEAR, 'B26001', 'county', [])),
            ('tot_hu_target', ('acs5', ACS_EST_YEAR, 'B25001', 'county', [])),
            ('occ_hu_target', ('acs5', ACS_EST_YEAR, 'B25002', 'county',
                               [collections.OrderedDict([('occupancy', 'Occupied')])])),
            ('vac_hu_target', ('acs5', ACS_EST_YEAR, 'B25002', 'county',
                               [collections.OrderedDict([('occupancy', 'Vacant')])])),
        ])
    }
}

def get_regional_targets(cf, target_controls, bay_area_counties):
    """
    Get ACS 2023 regional targets by aggregating county-level data across Bay Area counties.
    
    Returns:
        dict: {control_name: bay_area_total}
    """
    logging.info("Getting regional targets from ACS 2023 county data")
    
    regional_targets = {}
    
    for control_name, control_def in target_controls.items():
        logging.info(f"Processing regional target: {control_name}")
        
        # Get county-level data
        census_table_df = cf.get_census_data(
            dataset=control_def[0],  # 'acs5'
            year=control_def[1],     # ACS_EST_YEAR (2023)
            table=control_def[2],    # table name (e.g., 'B01003')
            geo=control_def[3]       # 'county'
        )
        
        # Create control table
        control_table_df = create_control_table(control_name, control_def[4], control_def[2], census_table_df)
        
        # Filter to Bay Area counties
        bay_area_df = control_table_df[control_table_df['GEOID_county'].isin([f"06{fips}" for fips in bay_area_counties.values()])]
        
        # Sum across Bay Area
        regional_total = bay_area_df[control_name].sum()
        regional_targets[control_name] = regional_total
        
        logging.info(f"  {control_name}: {regional_total:,.0f}")
    
    # Calculate pop_hh_target = tot_pop_target - pop_gq_target
    if 'tot_pop_target' in regional_targets and 'pop_gq_target' in regional_targets:
        regional_targets['pop_hh_target'] = regional_targets['tot_pop_target'] - regional_targets['pop_gq_target']
        logging.info(f"  pop_hh_target (calculated): {regional_targets['pop_hh_target']:,.0f}")
    
    return regional_targets

def apply_regional_scaling(control_df, control_name, regional_targets, regional_scale_factors):
    """
    Apply regional scaling to a control DataFrame.
    
    Parameters:
        control_df: DataFrame with MAZ-level controls
        control_name: Name of the control to scale
        regional_targets: Dict of regional target values
        regional_scale_factors: Dict to store calculated scale factors
    
    Returns:
        DataFrame: Scaled control DataFrame
    """
    # Map control names to target names
    target_mapping = {
        'tot_pop': 'tot_pop_target',
        'pop_hh': 'pop_hh_target', 
        'pop_gq': 'pop_gq_target',
        'tot_hu': 'tot_hu_target',
        'occ_hu': 'occ_hu_target',
        'vac_hu': 'vac_hu_target'
    }
    
    target_name = target_mapping.get(control_name)
    if not target_name:
        logging.warning(f"No regional target found for {control_name}, skipping scaling")
        return control_df
    
    if target_name not in regional_targets:
        logging.warning(f"Regional target {target_name} not found, skipping scaling")
        return control_df
    
    # Calculate current total
    current_total = control_df[control_name].sum()
    target_total = regional_targets[target_name]
    
    if current_total == 0:
        logging.warning(f"Current total is 0 for {control_name}, cannot scale")
        return control_df
    
    # Calculate scale factor
    scale_factor = target_total / current_total
    regional_scale_factors[control_name] = scale_factor
    
    logging.info(f"  {control_name}: current={current_total:,.0f}, target={target_total:,.0f}, scale_factor={scale_factor:.4f}")
    
    # Apply scaling
    scaled_df = control_df.copy()
    scaled_df[control_name] = scaled_df[control_name] * scale_factor
    
    return scaled_df

def process_block_distribution_control(control_name, control_def, cf, maz_taz_def_df):
    """
    Process household size controls using block group→block→MAZ distribution.
    This replaces the problematic scaling approach.
    """
    logging.info(f"Processing block distribution control: {control_name}")
    
    # Get ACS block group data
    census_table_df = cf.get_census_data(
        dataset=control_def[0],  # 'acs5'
        year=control_def[1],     # ACS_EST_YEAR (2023)
        table=control_def[2],    # 'B11016'
        geo=control_def[3]       # 'block group'
    )
    
    # Create control table
    control_table_df = create_control_table(control_name, control_def[4], control_def[2], census_table_df)
    
    # Use existing function but without problematic scaling
    final_df = match_control_to_geography(
        control_name=control_name,
        control_table_df=control_table_df,
        control_geography='MAZ',
        census_geography='block group',
        maz_taz_def_df=maz_taz_def_df,
        temp_controls={},  # No temp controls needed
        full_region=True,
        scale_numerator=None,   # No scaling
        scale_denominator=None,
        subtract_table=None
    )
    
    return final_df

def validate_control_relationships(final_control_dfs, regional_scale_factors):
    """
    Validate that control relationships are maintained after scaling.
    """
    logging.info("Validating control relationships after scaling")
    
    maz_controls = final_control_dfs.get('MAZ')
    if maz_controls is None:
        logging.warning("No MAZ controls found for validation")
        return
    
    # Check tot_pop = pop_hh + pop_gq
    if all(col in maz_controls.columns for col in ['tot_pop', 'pop_hh', 'pop_gq']):
        calculated_tot_pop = maz_controls['pop_hh'] + maz_controls['pop_gq']
        diff = abs(maz_controls['tot_pop'] - calculated_tot_pop).sum()
        logging.info(f"tot_pop vs (pop_hh + pop_gq) difference: {diff:.2f}")
        
        if diff > 1.0:  # Allow small rounding differences
            logging.warning(f"Large difference in population relationship: {diff:.2f}")
    
    # Check tot_hu = occ_hu + vac_hu
    if all(col in maz_controls.columns for col in ['tot_hu', 'occ_hu', 'vac_hu']):
        calculated_tot_hu = maz_controls['occ_hu'] + maz_controls['vac_hu']
        diff = abs(maz_controls['tot_hu'] - calculated_tot_hu).sum()
        logging.info(f"tot_hu vs (occ_hu + vac_hu) difference: {diff:.2f}")
        
        if diff > 1.0:  # Allow small rounding differences
            logging.warning(f"Large difference in housing unit relationship: {diff:.2f}")
    
    # Report scale factors
    logging.info("Regional scale factors applied:")
    for control_name, scale_factor in regional_scale_factors.items():
        logging.info(f"  {control_name}: {scale_factor:.4f}")

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model_year", type=int, default=ACS_EST_YEAR, help=f"Model year (default: {ACS_EST_YEAR})")
    parser.add_argument("--test_PUMA", type=str, help="Test with single PUMA (for debugging)")
    args = parser.parse_args()

    # Set up logging
    LOG_FILE = f"create_baseyear_controls_scaled_{args.model_year}.log"
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, mode='w'),
            logging.StreamHandler()
        ]
    )
    
    logging.info(f"=== Creating scaled controls for model year {args.model_year} ===")
    logging.info(f"Using new workflow with regional scaling and improved household size distribution")
    
    # Read MAZ/TAZ definition
    all_geog_file = "M:\\Data\\GIS layers\\TM2_maz_taz_v2.2\\mazs_tazs_all_geog.csv"
    maz_taz_def_df = pd.read_csv(all_geog_file)
    logging.info(f"Read {len(maz_taz_def_df)} rows from {all_geog_file}")
    
    # Filter for test PUMA if specified
    if args.test_PUMA:
        logging.info(f"Testing with PUMA {args.test_PUMA} only")
        maz_taz_def_df = maz_taz_def_df[maz_taz_def_df.PUMA == int(args.test_PUMA)]
    
    # Initialize data fetcher
    cf = CensusFetcher()
    
    # Step 1: Get regional targets
    logging.info("STEP 1: Getting regional targets from ACS 2023")
    regional_targets = get_regional_targets(cf, CONTROLS[args.model_year]['REGION_TARGETS'], BAY_AREA_COUNTY_FIPS)
    
    # Step 2: Process MAZ_SCALED controls
    logging.info("STEP 2: Processing MAZ_SCALED controls")
    
    final_control_dfs = {}
    regional_scale_factors = {}
    temp_controls = collections.OrderedDict()
    
    for control_name, control_def in CONTROLS[args.model_year]['MAZ_SCALED'].items():
        logging.info(f"Processing control: {control_name}")
        logging.info("=" * 80)
        
        # Determine processing type
        processing_type = control_def[-1] if len(control_def) > 5 else None
        
        if processing_type == 'regional_scale':
            # Basic controls: 2020 Census → 2010 MAZ → regional scaling
            logging.info(f"Processing {control_name} with regional scaling")
            
            # Get census data
            census_table_df = cf.get_census_data(
                dataset=control_def[0],  # 'pl'
                year=control_def[1],     # CENSUS_EST_YEAR (2020)
                table=control_def[2],    # e.g., 'P1_001N'
                geo=control_def[3]       # 'block'
            )
            
            # Create control table
            control_table_df = create_control_table(control_name, control_def[4], control_def[2], census_table_df)
            
            # Aggregate to MAZ using existing function
            final_df = match_control_to_geography(
                control_name=control_name,
                control_table_df=control_table_df,
                control_geography='MAZ',
                census_geography='block',
                maz_taz_def_df=maz_taz_def_df,
                temp_controls=temp_controls,
                full_region=(args.test_PUMA is None),
                scale_numerator=None,
                scale_denominator=None,
                subtract_table=None
            )
            
            # Apply regional scaling
            final_df = apply_regional_scaling(final_df, control_name, regional_targets, regional_scale_factors)
            
        elif processing_type == 'block_distribution':
            # Household size controls: block group → block → MAZ distribution
            logging.info(f"Processing {control_name} with block distribution")
            final_df = process_block_distribution_control(control_name, control_def, cf, maz_taz_def_df)
            
        else:
            logging.error(f"Unknown processing type: {processing_type}")
            continue
        
        # Integerize certain controls
        if control_name in ["num_hh", "gq_pop", "tot_pop"]:
            crosswalk_df = maz_taz_def_df[["MAZ", "TAZ", "PUMA", "COUNTY", "REGION"]].drop_duplicates()
            final_df = integerize_control(final_df, crosswalk_df, control_name)
        
        # Store result
        if 'MAZ' not in final_control_dfs:
            final_control_dfs['MAZ'] = final_df
        else:
            final_control_dfs['MAZ'] = pd.merge(
                left=final_control_dfs['MAZ'],
                right=final_df,
                left_index=True,
                right_index=True,
                how='outer'
            )
    
    # Step 3: Validate relationships
    logging.info("STEP 3: Validating control relationships")
    validate_control_relationships(final_control_dfs, regional_scale_factors)
    
    # Step 4: Write outputs
    logging.info("STEP 4: Writing output files")
    
    # Create output directory
    output_dir = pathlib.Path(OUTPUT_DIR_FMT.format(args.model_year))
    output_dir.mkdir(exist_ok=True)
    
    households_data_dir = pathlib.Path(HOUSEHOLDS_DIR) / DATA_SUBDIR
    households_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Write MAZ controls
    if 'MAZ' in final_control_dfs:
        maz_controls = final_control_dfs['MAZ']
        
        # Write household controls (all except gq_pop)
        hh_controls = [col for col in maz_controls.columns if col != 'gq_pop']
        if hh_controls:
            hh_control_file = households_data_dir / CONTROL_FILE_FMT.format(args.model_year, 'MAZ')
            maz_controls[hh_controls].to_csv(hh_control_file, float_format="%.5f")
            logging.info(f"Wrote {len(maz_controls)} MAZ household controls to {hh_control_file}")
        
        # Write summary
        summary_file = output_dir / f"control_summary_scaled_{args.model_year}.csv"
        summary_data = []
        for control_name in maz_controls.columns:
            total = maz_controls[control_name].sum()
            scale_factor = regional_scale_factors.get(control_name, 1.0)
            summary_data.append({
                'control_name': control_name,
                'total': total,
                'scale_factor': scale_factor,
                'processing_type': 'regional_scale' if control_name in regional_scale_factors else 'block_distribution'
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(summary_file, index=False, float_format="%.5f")
        logging.info(f"Wrote control summary to {summary_file}")
    
    # Write crosswalk
    crosswalk_file = households_data_dir / GEO_CROSSWALK_FILE
    crosswalk_df = maz_taz_def_df[maz_taz_def_df["MAZ"] > 0][["MAZ", "TAZ", "PUMA", "COUNTY", "REGION"]].drop_duplicates()
    crosswalk_df.sort_values(by="MAZ").to_csv(crosswalk_file, index=False)
    logging.info(f"Wrote {len(crosswalk_df)} crosswalk records to {crosswalk_file}")
    
    logging.info("=== Workflow completed successfully ===")

if __name__ == "__main__":
    main()
