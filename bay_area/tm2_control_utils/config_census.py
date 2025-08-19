# ============================================================================
# INCOME BIN MAPPING: 2010$ BINS, 2023$ BINS, AND ACS BIN MAPPING
# This dictionary is the canonical mapping for all scripts and summarization.
#
# Each entry is a dict with:
#   - '2010_bin': (min_2010, max_2010)
#   - '2023_bin': (min_2023, max_2023)
#   - 'acs_bin_label': str (human readable)
#   - 'acs_var': str (B19001_xxxE)
#   - 'acs_bin_range': (min_2023, max_2023)
#   - 'acs_bin_mid': float
#   - 'mapping_note': str (how mapping is determined)
# ============================================================================
INCOME_BIN_MAPPING = [
    {
        'control': 'hhinc_0_14',
        '2010_bin': (0, 13999),
        '2023_bin': (0, 19999),
        'acs_vars': [
            'B19001_002E', 'B19001_003E', 'B19001_004E'  # <$10k, $10-15k, $15-20k
        ],
    },
    {
        'control': 'hhinc_14_30',
        '2010_bin': (14000, 29999),
        '2023_bin': (20000, 44999),
        'acs_vars': [
            'B19001_005E', 'B19001_006E', 'B19001_007E', 'B19001_008E', 'B19001_009E'  # $20-25k, $25-30k, $30-35k, $35-40k, $40-45k
        ],
    },
    {
        'control': 'hhinc_45_60',
        '2010_bin': (45000, 59999),
        '2023_bin': (45000, 59999),
        'acs_vars': [
            'B19001_010E', 'B19001_011E'  # $45-50k, $50-60k
        ],
    },
    {
        'control': 'hhinc_60_75',
        '2010_bin': (60000, 74999),
        '2023_bin': (60000, 74999),
        'acs_vars': [
            'B19001_012E'  # $60-75k
        ],
    },
    {
        'control': 'hhinc_75_100',
        '2010_bin': (75000, 99999),
        '2023_bin': (75000, 99999),
        'acs_vars': [
            'B19001_013E', 'B19001_014E'  # $75-100k, $100-125k
        ],
    },
    {
        'control': 'hhinc_125_150',
        '2010_bin': (125000, 149999),
        '2023_bin': (125000, 149999),
        'acs_vars': [
            'B19001_015E'  # $125-150k
        ],
    },
    {
        'control': 'hhinc_150_200',
        '2010_bin': (150000, 199999),
        '2023_bin': (150000, 199999),
        'acs_vars': [
            'B19001_016E'  # $150-200k
        ],
    },
    {
        'control': 'hhinc_200_plus',
        '2010_bin': (200000, 2000000),
        '2023_bin': (200000, 2000000),
        'acs_vars': [
            'B19001_017E'  # $200k+
        ],
    },
]
#!/usr/bin/env python3
"""
TM2 Control Utils Config - Control generation configuration
This defines which Census/ACS data to use for PopulationSim controls.
"""

import pandas as pd
import collections

# This file is specialized for control generation and doesn't need the main pipeline config
# It defines the business logic of what controls to create, not just file paths

# Define required crosswalks as (source_year, target_year, geography)
# if you don't need geography crosswalks, you can set the two years to the same value

# The crosswalk files were download from https://www.nhgis.org/geographic-crosswalks#download-2020-2010
# This required a login so had to be manual.
NHGIS_CROSSWALK_PATHS = {
    ("block", 2020, 2010): r"M:\Data\Census\NewCachedTablesForPopulationSimControls\nhgis_blk2020_blk2010_06.csv",
    ("block group", 2020, 2010): r"M:\Data\Census\NewCachedTablesForPopulationSimControls\nhgis_bg2020_bg2010_06.csv",
    ("tract", 2020, 2010): r"M:\Data\Census\NewCachedTablesForPopulationSimControls\nhgis_tr2020_tr2010_06.csv",
}

# Constants
AGE_MAX  = 130
NKID_MAX = 10
NPER_MAX = 10
NWOR_MAX = 10
HINC_MAX = 2000000

# County recode DataFrame
COUNTY_RECODE = pd.DataFrame([
    {"GEOID_county":"06001", "COUNTY":1, "county_name":"Alameda"      , "REGION":1},
    {"GEOID_county":"06013", "COUNTY":13, "county_name":"Contra Costa" , "REGION":1},
    {"GEOID_county":"06041", "COUNTY":41, "county_name":"Marin"        , "REGION":1},
    {"GEOID_county":"06055", "COUNTY":55, "county_name":"Napa"         , "REGION":1},
    {"GEOID_county":"06075", "COUNTY":75, "county_name":"San Francisco", "REGION":1},
    {"GEOID_county":"06081", "COUNTY":81, "county_name":"San Mateo"    , "REGION":1},
    {"GEOID_county":"06085", "COUNTY":85, "county_name":"Santa Clara"  , "REGION":1},
    {"GEOID_county":"06095", "COUNTY":95, "county_name":"Solano"       , "REGION":1},
    {"GEOID_county":"06097", "COUNTY":97, "county_name":"Sonoma"       , "REGION":1}
])

# Years
CENSUS_EST_YEAR = 2020
CENSUS_GEOG_YEAR = 2010
ACS_EST_YEAR = 2023

# Census API Configuration  
CENSUS_API_KEY_FILE = r"M:\Data\Census\API\new_key\api-key.txt"
LOCAL_CACHE_FOLDER = r"M:\Data\Census\NewCachedTablesForPopulationSimControls"
NETWORK_CACHE_FOLDER = r"M:\Data\Census\NewCachedTablesForPopulationSimControls"
INPUT_2023_CACHE_FOLDER = "input_2023/NewCachedTablesForPopulationSimControls"

# Network (M: drive) file locations
NETWORK_MAZ_TAZ_DEF_FILE = r"C:\GitHub\tm2py-utils\tm2py_utils\inputs\maz_taz\shapefiles\mazs_TM2_2_5.shp"
NETWORK_MAZ_TAZ_ALL_GEOG_FILE = "output_2023/populationsim_working_dir/data/mazs_tazs_all_geog.csv"
NETWORK_CENSUS_API_KEY_FILE = r"M:\Data\Census\API\new_key\api-key.txt"



# Geographic data files - Using verified 2010 Census blocks
BLOCKS_MAZ_TAZ_FILE = r"C:\GitHub\tm2py-utils\tm2py_utils\inputs\maz_taz\blocks_mazs_tazs_2.5.csv"  # Verified 2010 Census blocks with MAZ/TAZ mapping

# Output file names
GEO_CROSSWALK_TM2_FILE = "geo_cross_walk_tm2.csv"
MAZ_TAZ_ALL_GEOG_OUTPUT_FILE = "output_2023/populationsim_working_dir/data/mazs_tazs_all_geog.csv"  # Rebuilt complete geography file
COUNTY_TARGETS_FILE = "county_targets_2023.csv"
MAZ_MARGINALS_FILE = "maz_marginals.csv"
TAZ_MARGINALS_FILE = "taz_marginals.csv"
COUNTY_MARGINALS_FILE = "county_marginals.csv"
COUNTY_SUMMARY_FILE = "county_summary_2020_2023.csv"
OUTPUT_MAZ_DATA_FILE = "maz_data.csv"
OUTPUT_MAZ_DENSITY_FILE = "maz_data_withDensity.csv"

# Example/reference data files (contain employment/land use data to preserve)
EXAMPLE_MAZ_DATA_FILE = "example_controls_2015/maz_data_2015.csv"
EXAMPLE_MAZ_DENSITY_FILE = "example_controls_2015/maz_data_withDensity_2015.csv"

# Default output directory (can be overridden in main script)
# Use unified configuration for PopulationSim-compatible output directory
from unified_tm2_config import UnifiedTM2Config
unified_config = UnifiedTM2Config()
PRIMARY_OUTPUT_DIR = str(unified_config.POPSIM_DATA_DIR)

# Geographic crosswalk file location (single source of truth)
GEO_CROSSWALK_TM2_PATH = str(unified_config.CROSSWALK_FILES['main_crosswalk'])

# Define variables that may not be set but are used by legacy scripts
MAZ_TAZ_DEF_FILE = NETWORK_MAZ_TAZ_DEF_FILE  # Default to network location
MAZ_TAZ_ALL_GEOG_FILE = "output_2023/populationsim_working_dir/data/mazs_tazs_all_geog.csv"  # Use canonical, up-to-date geography file


def rebuild_maz_taz_all_geog_file(blocks_file_path=None, output_path=None):
    """
    Rebuild the complete MAZ/TAZ geography file with block-level GEOIDs from the verified 
    2010 Census blocks file. This creates the missing geographic hierarchy needed for 
    Census control aggregation.
    
    Args:
        blocks_file_path: Path to the blocks file (defaults to BLOCKS_MAZ_TAZ_FILE)
        output_path: Where to save the rebuilt file (defaults to PRIMARY_OUTPUT_DIR/MAZ_TAZ_ALL_GEOG_OUTPUT_FILE)
        
    Returns:
        DataFrame with complete geographic hierarchy: MAZ, TAZ, GEOID_block, GEOID_block_group, etc.
    """
    global MAZ_TAZ_ALL_GEOG_FILE
    import os
    import pandas as pd
    from tm2_control_utils.geog_utils import add_aggregate_geography_colums
    
    # Use default blocks file if not specified
    if blocks_file_path is None:
        blocks_file_path = BLOCKS_MAZ_TAZ_FILE
    
    # Set default output path
    if output_path is None:
        output_path = os.path.join(PRIMARY_OUTPUT_DIR, MAZ_TAZ_ALL_GEOG_OUTPUT_FILE)
    
    print("=== REBUILDING MAZ/TAZ ALL GEOGRAPHY FILE ===")
    print(f"Input file: {blocks_file_path}")
    print(f"Output file: {output_path}")
    
    if not os.path.exists(blocks_file_path):
        raise FileNotFoundError(f"Blocks file not found: {blocks_file_path}")
    
    # Step 1: Load and validate the blocks file
    print("\n1. LOADING BLOCKS FILE...")
    blocks_df = pd.read_csv(blocks_file_path)
    print(f"   - Loaded {len(blocks_df)} block records")
    print(f"   - Columns: {list(blocks_df.columns)}")
    
    # Standardize column names to match expected format
    blocks_df.rename(columns={
        'GEOID10': 'GEOID10',  # Keep as-is if already correct
        'maz': 'MAZ',
        'taz': 'TAZ'
    }, inplace=True)
    
    # Step 2: Create standardized GEOID_block (15 digits, 2010 format)
    print("\n2. CREATING STANDARDIZED GEOID_BLOCK...")
    
    # Ensure GEOID10 is treated as string and properly zero-padded to 15 digits
    blocks_df['GEOID10_str'] = blocks_df['GEOID10'].astype(str).str.zfill(15)
    
    # Create GEOID_block in the format expected by the control system
    blocks_df['GEOID_block'] = blocks_df['GEOID10_str']
    
    print(f"   - Sample GEOID_block values:")
    for i in range(min(3, len(blocks_df))):
        sample_geoid = blocks_df['GEOID_block'].iloc[i]
        print(f"     {sample_geoid} (length: {len(sample_geoid)})")
        
    # Validate GEOID structure
    geoid_lengths = blocks_df['GEOID_block'].str.len()
    if not (geoid_lengths == 15).all():
        bad_geoids = blocks_df[geoid_lengths != 15]['GEOID_block'].head(5).tolist()
        raise ValueError(f"Invalid GEOID lengths found. Expected 15 digits. Examples: {bad_geoids}")
    
    # Step 3: Create aggregate geography columns using the existing utility function
    print("\n3. CREATING AGGREGATE GEOGRAPHY COLUMNS...")
    add_aggregate_geography_colums(blocks_df)
    
    print(f"   - GEOID_county: {blocks_df['GEOID_county'].nunique()} unique (should be 9 Bay Area counties)")
    print(f"   - GEOID_tract: {blocks_df['GEOID_tract'].nunique()} unique")
    print(f"   - GEOID_block group: {blocks_df['GEOID_block group'].nunique()} unique")
    
    # Step 4: Add county information using COUNTY_RECODE
    print("\n4. ADDING COUNTY INFORMATION...")
    blocks_df = pd.merge(
        left=blocks_df,
        right=COUNTY_RECODE[['GEOID_county', 'COUNTY', 'county_name']],
        on='GEOID_county',
        how='left'
    )
    
    # Validate county mapping
    missing_counties = blocks_df['COUNTY'].isna().sum()
    if missing_counties > 0:
        print(f"   - WARNING: {missing_counties} blocks missing county mapping")
        unmapped_counties = blocks_df[blocks_df['COUNTY'].isna()]['GEOID_county'].unique()
        print(f"   - Unmapped county GEOIDs: {unmapped_counties}")
    else:
        print(f"   - Successfully mapped all blocks to counties")
        county_counts = blocks_df.groupby(['COUNTY', 'county_name']).size().reset_index(name='block_count')
        for _, row in county_counts.iterrows():
            print(f"     County {row['COUNTY']} ({row['county_name']}): {row['block_count']} blocks")
    
    # Step 5: Add PUMA information from existing crosswalk if available
    print("\n5. ADDING PUMA INFORMATION...")
    
    # Try to load the existing crosswalk to get PUMA mappings
    if os.path.exists(GEO_CROSSWALK_TM2_PATH):
        crosswalk_df = pd.read_csv(GEO_CROSSWALK_TM2_PATH)
        if 'PUMA' in crosswalk_df.columns:
            puma_mapping = crosswalk_df[['MAZ', 'PUMA']].drop_duplicates()
            
            blocks_df = pd.merge(
                left=blocks_df,
                right=puma_mapping,
                on='MAZ',
                how='left'
            )
            
            missing_pumas = blocks_df['PUMA'].isna().sum()
            if missing_pumas > 0:
                print(f"   - WARNING: {missing_pumas} blocks missing PUMA mapping")
            else:
                print(f"   - Successfully mapped all blocks to PUMAs")
        else:
            print(f"   - No PUMA column in existing crosswalk")
            blocks_df['PUMA'] = None
    else:
        print(f"   - No existing crosswalk found, PUMA mapping skipped")
        blocks_df['PUMA'] = None
    
    # Step 6: Prepare final output with proper column order
    print("\n6. PREPARING FINAL OUTPUT...")
    
    # Select and order columns to match expected format
    output_columns = [
        'MAZ', 'TAZ', 'COUNTY', 'county_name', 'PUMA',
        'GEOID_block', 'GEOID_block group', 'GEOID_tract', 'GEOID_county'
    ]
    
    # Only include columns that exist
    final_columns = [col for col in output_columns if col in blocks_df.columns]
    result_df = blocks_df[final_columns].copy()
    
    # Step 7: Save the rebuilt file in the control data output directory
    print(f"\n7. SAVING REBUILT FILE...")
    
    # Create directory if needed
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the file
    result_df.to_csv(output_path, index=False)
    print(f"   - Saved to: {output_path}")
    print(f"   - Final columns: {list(result_df.columns)}")
    print(f"   - Total records: {len(result_df)}")
    
    # Step 8: Set this as the active geography file
    MAZ_TAZ_ALL_GEOG_FILE = output_path
    print(f"   - Set as active MAZ_TAZ_ALL_GEOG_FILE: {MAZ_TAZ_ALL_GEOG_FILE}")
    
    # Step 9: Validation summary
    print(f"\n8. VALIDATION SUMMARY:")
    print(f"   - MAZs: {result_df['MAZ'].nunique()}")
    print(f"   - TAZs: {result_df['TAZ'].nunique()}")  
    print(f"   - Block groups: {result_df['GEOID_block group'].nunique()}")
    print(f"   - Counties: {result_df['COUNTY'].nunique()}")
    
    if 'PUMA' in result_df.columns:
        print(f"   - PUMAs: {result_df['PUMA'].nunique()}")
    
    # Check for any potential joinability issues
    print(f"\n9. JOINABILITY CHECKS:")
    duplicate_blocks = result_df['GEOID_block'].duplicated().sum()
    if duplicate_blocks > 0:
        print(f"   - WARNING: {duplicate_blocks} duplicate block GEOIDs found!")
    else:
        print(f"   - ✅ All block GEOIDs are unique")
        
    duplicate_bg = result_df[['GEOID_block group', 'TAZ']].duplicated().sum()
    if duplicate_bg > 0:
        print(f"   - INFO: {duplicate_bg} block groups span multiple TAZs (expected)")
    
    print(f"\n=== REBUILD COMPLETE ===")
    print(f"The rebuilt file is now active and should work with the Census control aggregation system.")
    
    return True


CONTROLS = {
    CENSUS_EST_YEAR: collections.OrderedDict(),
    ACS_EST_YEAR:    collections.OrderedDict()
}

# ----------------------------------------
# MAZ controls for ACS estimate year - PopulationSim expects: num_hh + group quarters 
# 
# NOTE: Income breakpoints aligned with ACS B19001 table boundaries for accurate aggregation.
# Using actual Census bracket boundaries eliminates household splitting across income categories:
# - $0-39,999 (ACS brackets B19001_002E through B19001_008E)
# - $40,000-74,999 (ACS brackets B19001_009E through B19001_012E) 
# - $75,000-124,999 (ACS brackets B19001_013E through B19001_014E)
# - $125,000+ (ACS brackets B19001_015E through B19001_017E)
# This ensures perfect alignment between control generation and ACS source data. 
CONTROLS[ACS_EST_YEAR]['MAZ'] = collections.OrderedDict([
    # Number of households (PopulationSim: num_hh) - Start with 2020 Census H1_002N, apply county-level scaling factors
    ('num_hh',                ('pl',  CENSUS_EST_YEAR, 'H1_002N',      'block',
                               [], 'county_scale')),
    # Total population from 2020 Census PL 94-171 - essential for hierarchical control consistency, scaled to 2023 ACS
    ('total_pop',             ('pl',   CENSUS_EST_YEAR, 'P1_001N',      'block',
                               [], 'county_scale')),
    # Group quarters from 2020 Census PL 94-171 - keep at 2020 levels (no detailed ACS1 targets available)
    ('gq_pop',                ('pl',   CENSUS_EST_YEAR, 'P5_001N',      'block',
                               [])),
    # Detailed group quarters by type from 2020 Census PL 94-171 - keep at 2020 levels
    ('gq_military',           ('pl',   CENSUS_EST_YEAR, 'P5_009N',      'block',
                               [])),
    ('gq_university',         ('pl',   CENSUS_EST_YEAR, 'P5_008N',      'block',
                               [])),
])

# ----------------------------------------
# TAZ controls for ACS estimate year - PopulationSim expects: workers, age, children, income
CONTROLS[ACS_EST_YEAR]['TAZ'] = collections.OrderedDict()
# Income bins: programmatically generated from INCOME_BIN_MAPPING
# Use the ACS bin min/max (2023_bin) for each control
for bin_def in INCOME_BIN_MAPPING:
    CONTROLS[ACS_EST_YEAR]['TAZ'][bin_def['control']] = (
        'acs5', ACS_EST_YEAR, 'B19001', 'block group',
        [collections.OrderedDict([
            ('hhinc_min', bin_def['2023_bin'][0]),
            ('hhinc_max', bin_def['2023_bin'][1])
        ])]
    )
# Add the rest of the TAZ controls (unchanged)
CONTROLS[ACS_EST_YEAR]['TAZ'].update(collections.OrderedDict([
    ('temp_hh_bg_for_tract_weights', ('acs5', ACS_EST_YEAR, 'B11016', 'block group',
                               [collections.OrderedDict([('pers_min',1),('pers_max',NPER_MAX)])])),
    ('hh_wrks_0',             ('acs5', ACS_EST_YEAR,    'B08202',       'tract',
                               [collections.OrderedDict([('workers_min',0),('workers_max',0),
                                                         ('persons_min',0), ('persons_max',NPER_MAX)])],
                               'temp_hh_bg_for_tract_weights','tract_to_bg_disaggregation')),
    ('hh_wrks_1',             ('acs5', ACS_EST_YEAR,    'B08202',       'tract',
                               [collections.OrderedDict([('workers_min',1),('workers_max',1),
                                                         ('persons_min',0), ('persons_max',NPER_MAX)])],
                               'temp_hh_bg_for_tract_weights','tract_to_bg_disaggregation')),
    ('hh_wrks_2',             ('acs5', ACS_EST_YEAR,    'B08202',       'tract',
                               [collections.OrderedDict([('workers_min',2),('workers_max',2),
                                                         ('persons_min',0), ('persons_max',NPER_MAX)])],
                               'temp_hh_bg_for_tract_weights','tract_to_bg_disaggregation')),
    ('hh_wrks_3_plus',        ('acs5', ACS_EST_YEAR,    'B08202',       'tract',
                               [collections.OrderedDict([('workers_min',3),('workers_max',NWOR_MAX),
                                                         ('persons_min',0), ('persons_max',NPER_MAX)])],
                               'temp_hh_bg_for_tract_weights','tract_to_bg_disaggregation')),
    # ACS5 total persons by age at tract level - DISAGGREGATION NEEDED (tract -> block group -> TAZ)
    ('pers_age_00_19',        ('acs5', ACS_EST_YEAR,    'B01001',       'tract',
                               [collections.OrderedDict([('age_min',0),('age_max',19)])], 
                               'temp_hh_bg_for_tract_weights','tract_to_bg_disaggregation')),
    ('pers_age_20_34',        ('acs5', ACS_EST_YEAR,    'B01001',       'tract',
                               [collections.OrderedDict([('age_min',20),('age_max',34)])], 
                               'temp_hh_bg_for_tract_weights','tract_to_bg_disaggregation')),
    ('pers_age_35_64',        ('acs5', ACS_EST_YEAR,    'B01001',       'tract',
                               [collections.OrderedDict([('age_min',35),('age_max',64)])], 
                               'temp_hh_bg_for_tract_weights','tract_to_bg_disaggregation')),
    ('pers_age_65_plus',      ('acs5', ACS_EST_YEAR,    'B01001',       'tract',
                               [collections.OrderedDict([('age_min',65),('age_max',AGE_MAX)])], 
                               'temp_hh_bg_for_tract_weights','tract_to_bg_disaggregation')),
    # ACS5 households with children at block-group - DIRECT AGGREGATION (no scaling needed)
    ('hh_kids_no',            ('acs5', ACS_EST_YEAR,    'B11005',       'block group',
                               [collections.OrderedDict([('num_kids_min',0),('num_kids_max',0)])])),
    ('hh_kids_yes',           ('acs5', ACS_EST_YEAR,    'B11005',       'block group',
                               [collections.OrderedDict([('num_kids_min',1),('num_kids_max',NKID_MAX)])])),
    # ACS5 household size distribution at block-group - moved from MAZ to TAZ level
    ('hh_size_1',             ('acs5', ACS_EST_YEAR,    'B11016',       'block group',
                               [collections.OrderedDict([('pers_min',1),('pers_max',1)])])),
    ('hh_size_2',             ('acs5', ACS_EST_YEAR,    'B11016',       'block group',
                               [collections.OrderedDict([('pers_min',2),('pers_max',2)])])),
    ('hh_size_3',             ('acs5', ACS_EST_YEAR,    'B11016',       'block group',
                               [collections.OrderedDict([('pers_min',3),('pers_max',3)])])),
    ('hh_size_4_plus',        ('acs5', ACS_EST_YEAR,    'B11016',       'block group',
                               [collections.OrderedDict([('pers_min',4),('pers_max',NPER_MAX)])])),
]))


# ----------------------------------------
# COUNTY controls for Census estimate year
CONTROLS[CENSUS_EST_YEAR]['COUNTY'] = collections.OrderedDict([
    ('pers_occ_management',   ('acs5', ACS_EST_YEAR, 'C24010', 'tract', [
        collections.OrderedDict([('occ_cat1','Management, business, science, and arts'),
                                 ('occ_cat2','Management, business, and financial'),
                                 ('occ_cat3','Management')])
    ])),
    ('pers_occ_professional', ('acs5', ACS_EST_YEAR, 'C24010', 'tract', [
        collections.OrderedDict([('occ_cat1','Management, business, science, and arts'),
                                 ('occ_cat2','Management, business, and financial'),
                                 ('occ_cat3','Business and financial operations')]),
        collections.OrderedDict([('occ_cat1','Management, business, science, and arts'),
                                 ('occ_cat2','Computer, engineering, and science'),
                                 ('occ_cat3','Computer and mathematical')]),
        collections.OrderedDict([('occ_cat1','Management, business, science, and arts'),
                                 ('occ_cat2','Computer, engineering, and science'),
                                 ('occ_cat3','Architecture and engineering')]),
        collections.OrderedDict([('occ_cat1','Management, business, science, and arts'),
                                 ('occ_cat2','Computer, engineering, and science'),
                                 ('occ_cat3','Life, physical, and social science')]),
        collections.OrderedDict([('occ_cat1','Management, business, science, and arts'),
                                 ('occ_cat2','Education, legal, community service, arts, and media'),
                                 ('occ_cat3','Legal')]),
        collections.OrderedDict([('occ_cat1','Management, business, science, and arts'),
                                 ('occ_cat2','Education, legal, community service, arts, and media'),
                                 ('occ_cat3','Education, training, and library')]),
        collections.OrderedDict([('occ_cat1','Management, business, science, and arts'),
                                 ('occ_cat2','Healthcare practitioners and technical'),
                                 ('occ_cat3','Health diagnosing and treating practitioners and other technical')]),
        collections.OrderedDict([('occ_cat1','Management, business, science, and arts'),
                                 ('occ_cat2','Healthcare practitioners and technical'),
                                 ('occ_cat3','Health technologists and technicians')]),
    ])),
    ('pers_occ_services',     ('acs5', ACS_EST_YEAR, 'C24010', 'tract', [
        collections.OrderedDict([('occ_cat1','Management, business, science, and arts'),
                                 ('occ_cat2','Education, legal, community service, arts, and media'),
                                 ('occ_cat3','Community and social service')]),
        collections.OrderedDict([('occ_cat1','Management, business, science, and arts'),
                                 ('occ_cat2','Education, legal, community service, arts, and media'),
                                 ('occ_cat3','Arts, design, entertainment, sports, and media')]),
        collections.OrderedDict([('occ_cat1','Service'),
                                 ('occ_cat2','Healthcare support'),
                                 ('occ_cat3','All')]),
        collections.OrderedDict([('occ_cat1','Service'),
                                 ('occ_cat2','Protective service'),
                                 ('occ_cat3','Fire fighting and prevention, and other protective service workers')]),
        collections.OrderedDict([('occ_cat1','Service'),
                                 ('occ_cat2','Protective service'),
                                 ('occ_cat3','Law enforcement workers')]),
        collections.OrderedDict([('occ_cat1','Service'),
                                 ('occ_cat2','Personal care and service'),
                                 ('occ_cat3','All')]),
        collections.OrderedDict([('occ_cat1','Sales and office'),
                                 ('occ_cat2','Office and administrative support'),
                                 ('occ_cat3','All')]),
    ])),
    ('pers_occ_retail',       ('acs5', ACS_EST_YEAR, 'C24010', 'tract', [
        collections.OrderedDict([('occ_cat1','Service'),
                                 ('occ_cat2','Food preparation and serving related'),
                                 ('occ_cat3','All')]),
        collections.OrderedDict([('occ_cat1','Sales and office'),
                                 ('occ_cat2','Sales and related'),
                                 ('occ_cat3','All')]),
    ])),
    ('pers_occ_manual',       ('acs5', ACS_EST_YEAR, 'C24010', 'tract', [
        collections.OrderedDict([('occ_cat1','Service'),
                                 ('occ_cat2','Building and grounds cleaning and maintenance'),
                                 ('occ_cat3','All')]),
        collections.OrderedDict([('occ_cat1','Natural resources, construction, and maintenance'),
                                 ('occ_cat2','Farming, fishing, and forestry'),
                                 ('occ_cat3','All')]),
        collections.OrderedDict([('occ_cat1','Natural resources, construction, and maintenance'),
                                 ('occ_cat2','Construction and extraction'),
                                 ('occ_cat3','All')]),
        collections.OrderedDict([('occ_cat1','Natural resources, construction, and maintenance'),
                                 ('occ_cat2','Installation, maintenance, and repair'),
                                 ('occ_cat3','All')]),
        collections.OrderedDict([('occ_cat1','Production, transportation, and material moving'),
                                 ('occ_cat2','Production'),
                                 ('occ_cat3','All')]),
        collections.OrderedDict([('occ_cat1','Production, transportation, and material moving'),
                                 ('occ_cat2','Transportation'),
                                 ('occ_cat3','All')]),
        collections.OrderedDict([('occ_cat1','Production, transportation, and material moving'),
                                 ('occ_cat2','Material moving'),
                                 ('occ_cat3','All')]),
    ])),
    # Military occupation (civilian data only)
    ('pers_occ_military',     ('acs5', ACS_EST_YEAR, 'B23025', 'tract', [
        collections.OrderedDict([('inlaborforce','Yes'),('type','Armed Forces')])
    ])),
])

# copy COUNTY controls into ACS_EST_YEAR and update any 'acs5' tuples
CONTROLS[ACS_EST_YEAR]['COUNTY'] = collections.OrderedDict()
for name, tpl in CONTROLS[CENSUS_EST_YEAR]['COUNTY'].items():
    lst = list(tpl)
    if lst[0] == 'acs5':
        lst[1] = ACS_EST_YEAR
    CONTROLS[ACS_EST_YEAR]['COUNTY'][name] = tuple(lst)

# ----------------------------------------
# REGION controls and targets - Combined for regional scaling operations
CONTROLS[CENSUS_EST_YEAR]['REGION'] = collections.OrderedDict([
    ('gq_num_hh_region', 'special')
])

CONTROLS[ACS_EST_YEAR]['REGION'] = collections.OrderedDict([
    ('gq_num_hh_region', 'special')
])

# County-level scaling targets from ACS 2023 1-year estimates (using acs1)
# These will be used as county-specific scaling factors applied to 2020 Census occupied housing units
CONTROLS[ACS_EST_YEAR]['COUNTY_TARGETS'] = collections.OrderedDict([
    # Household targets from ACS 2023 1-year county estimates (by county)
    ('num_hh_target_by_county',  ('acs1', ACS_EST_YEAR, 'B25001', 'county', [])),        # Total households by county
    ('tot_pop_target_by_county', ('acs1', ACS_EST_YEAR, 'B01003', 'county', [])),        # Total population by county
    # Note: Group quarters subcategory variables (B26001_006E, B26001_007E) are not available in ACS1
    # Using 2020 Census PL data for group quarters (no county-level scaling)
])


# ----------------------------------------
# HIERARCHICAL CONSISTENCY CONFIGURATION
# Define which TAZ-level controls must sum to which MAZ-level totals
# This ensures the control hierarchy is mathematically consistent
# Format: 'maz_control_name': ['taz_control_1', 'taz_control_2', ...]
HIERARCHICAL_CONSISTENCY = collections.OrderedDict([
    # Household totals: TAZ household size categories must sum to MAZ household total
    ('num_hh', [
        'hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus'
    ]),
    
    # Population totals: TAZ population categories must sum to MAZ population total
    ('total_pop', [
        'pers_age_00_19', 'pers_age_20_34', 'pers_age_35_64', 'pers_age_65_plus'
    ])
])

# Additional consistency checks - Multiple TAZ breakdowns that all sum to the same MAZ total
# Note: We can't use duplicate keys in OrderedDict, so we process these as alternative checks
ALTERNATIVE_HIERARCHICAL_CONSISTENCY = collections.OrderedDict([
    # Income consistency: TAZ income categories must sum to total households at MAZ
    ('num_hh_income', [
        'hh_inc_30', 'hh_inc_30_60', 'hh_inc_60_100', 'hh_inc_100_plus'
    ]),
    
    # Worker consistency: TAZ worker categories must sum to total households at MAZ
    ('num_hh_workers', [
        'hh_wrks_0', 'hh_wrks_1', 'hh_wrks_2', 'hh_wrks_3_plus'
    ]),
    
    # Children consistency: TAZ household children categories must sum to total households at MAZ
    ('num_hh_children', [
        'hh_kids_no', 'hh_kids_yes'
    ])
])

# Additional consistency checks (same MAZ total but different TAZ breakdowns)
# These will be checked separately since OrderedDict can't have duplicate keys
ADDITIONAL_CONSISTENCY_CHECKS = collections.OrderedDict([
    # Income consistency: TAZ income categories must sum to total households at MAZ
    ('hh_income_categories', {
        'maz_total': 'num_hh', 
        'taz_categories': ['hh_inc_30', 'hh_inc_30_60', 'hh_inc_60_100', 'hh_inc_100_plus']
    }),
    
    # Worker consistency: TAZ worker categories must sum to total households at MAZ
    ('hh_worker_categories', {
        'maz_total': 'num_hh',
        'taz_categories': ['hh_wrks_0', 'hh_wrks_1', 'hh_wrks_2', 'hh_wrks_3_plus']
    }),
    
    # Children consistency: TAZ household children categories must sum to total households at MAZ
    ('hh_children_categories', {
        'maz_total': 'num_hh',
        'taz_categories': ['hh_kids_no', 'hh_kids_yes']
    })
])

# Validation tolerance for hierarchical consistency checks
HIERARCHICAL_TOLERANCE = 1.0  # Allow up to 1 unit difference due to rounding


def enforce_hierarchical_consistency(maz_controls, taz_controls, crosswalk_df=None):
    """
    Enforce hierarchical consistency by adjusting TAZ categories to sum to MAZ totals.
    
    This function ensures that TAZ-level categories sum to equal the corresponding
    MAZ-level totals within each TAZ. MAZ totals are considered authoritative (from Census
    block data) and TAZ categories are proportionally adjusted to match.
    
    IMPORTANT: TAZ data has one record per TAZ, MAZ data has one record per MAZ.
    Multiple MAZs can belong to the same TAZ.
    
    Parameters:
    -----------
    maz_controls : pandas.DataFrame
        MAZ-level control data with columns like MAZ, numhh_gq, total_pop
    taz_controls : pandas.DataFrame  
        TAZ-level control data with columns like TAZ, hh_size_1, hh_size_2, etc.
    crosswalk_df : pandas.DataFrame, optional
        Crosswalk with MAZ-TAZ mapping if TAZ controls don't have MAZ column
        
    Returns:
    --------
    tuple : (maz_controls, updated_taz_controls) where MAZ controls are unchanged
           and TAZ controls are proportionally adjusted
    """
    import pandas as pd
    
    print("=== ENFORCING HIERARCHICAL CONSISTENCY (CORRECTED) ===")
    print("MAZ totals are authoritative and will NOT be changed.")
    print("TAZ categories will be proportionally adjusted to sum to MAZ totals.")
    
    # MAZ controls stay exactly the same - they are authoritative
    maz_updated = maz_controls.copy()
    taz_updated = taz_controls.copy()
    
    if crosswalk_df is None:
        print("ERROR: Crosswalk is required for hierarchical consistency")
        return maz_updated, taz_updated
    
    # Calculate target totals for each TAZ by summing MAZs within each TAZ
    print("Calculating target totals for each TAZ...")
    
    # Merge MAZ controls with crosswalk to get TAZ assignments
    maz_with_taz = maz_controls.merge(crosswalk_df[['MAZ', 'TAZ']], on='MAZ', how='left')
    
    # Group by TAZ and sum MAZ totals
    taz_targets = maz_with_taz.groupby('TAZ').agg({
        'num_hh': 'sum',
        'total_pop': 'sum'
    }).reset_index()
    
    print(f"Calculated targets for {len(taz_targets)} TAZs")
    
    total_adjustments = 0
    
    # Process primary consistency rules
    for maz_control, taz_control_list in HIERARCHICAL_CONSISTENCY.items():
        
        # Skip if MAZ control doesn't exist in the data
        if maz_control not in taz_targets.columns:
            print(f"Skipping {maz_control} - not found in target calculations")
            continue
            
        # Check which TAZ controls exist
        existing_taz_controls = [ctrl for ctrl in taz_control_list if ctrl in taz_updated.columns]
        missing_taz_controls = [ctrl for ctrl in taz_control_list if ctrl not in taz_updated.columns]
        
        if missing_taz_controls:
            print(f"Warning: Missing TAZ controls for {maz_control}: {missing_taz_controls}")
        
        if not existing_taz_controls:
            print(f"Skipping {maz_control} - no corresponding TAZ controls found")
            continue
            
        print(f"Adjusting TAZ {existing_taz_controls} to sum to MAZ {maz_control}")
        
        # Merge TAZ data with targets
        taz_with_targets = taz_updated.merge(taz_targets[['TAZ', maz_control]], on='TAZ', how='left')
        
        # Calculate current sums for each TAZ
        taz_with_targets['current_sum'] = taz_with_targets[existing_taz_controls].sum(axis=1)
        
        # Calculate scaling factors
        taz_with_targets['scale_factor'] = 1.0  # Default no scaling
        nonzero_mask = taz_with_targets['current_sum'] > 0
        taz_with_targets.loc[nonzero_mask, 'scale_factor'] = (
            taz_with_targets.loc[nonzero_mask, maz_control] / 
            taz_with_targets.loc[nonzero_mask, 'current_sum']
        )
        
        # Apply scaling to TAZ categories
        adjustments_made = 0
        for col in existing_taz_controls:
            # Apply proportional scaling
            taz_updated[col] *= taz_with_targets['scale_factor']
        
        # Handle special case: zero current sum but non-zero target
        zero_current_nonzero_target = (taz_with_targets['current_sum'] == 0) & (taz_with_targets[maz_control] > 0)
        if zero_current_nonzero_target.any():
            for idx in taz_with_targets[zero_current_nonzero_target].index:
                target_value = taz_with_targets.loc[idx, maz_control]
                per_category = target_value / len(existing_taz_controls)
                for col in existing_taz_controls:
                    taz_updated.loc[idx, col] = per_category
        
        # Count adjustments
        adjustment_mask = (
            (abs(taz_with_targets['current_sum'] - taz_with_targets[maz_control]) > HIERARCHICAL_TOLERANCE) |
            zero_current_nonzero_target
        )
        adjustments_made = adjustment_mask.sum()
        
        print(f"  Adjusted {adjustments_made} TAZs for {maz_control}")
        total_adjustments += adjustments_made
    
    # Process alternative consistency rules (multiple TAZ breakdowns for same MAZ total)
    print("\n--- Processing Alternative Consistency Rules ---")
    for alt_control_name, taz_control_list in ALTERNATIVE_HIERARCHICAL_CONSISTENCY.items():
        # These all map to 'num_hh' at MAZ level
        maz_control = 'num_hh'
        
        # Check which TAZ controls exist
        existing_taz_controls = [ctrl for ctrl in taz_control_list if ctrl in taz_updated.columns]
        missing_taz_controls = [ctrl for ctrl in taz_control_list if ctrl not in taz_updated.columns]
        
        if missing_taz_controls:
            print(f"Warning: Missing TAZ controls for {alt_control_name}: {missing_taz_controls}")
        
        if not existing_taz_controls:
            print(f"Skipping {alt_control_name} - no corresponding TAZ controls found")
            continue
            
        print(f"Adjusting TAZ {existing_taz_controls} to sum to MAZ {maz_control} ({alt_control_name})")
        
        # Merge TAZ data with targets (use num_hh targets)
        taz_with_targets = taz_updated.merge(taz_targets[['TAZ', maz_control]], on='TAZ', how='left')
        
        # Calculate current sums for each TAZ
        taz_with_targets['current_sum'] = taz_with_targets[existing_taz_controls].sum(axis=1)
        
        # Calculate scaling factors
        taz_with_targets['scale_factor'] = 1.0  # Default no scaling
        nonzero_mask = taz_with_targets['current_sum'] > 0
        taz_with_targets.loc[nonzero_mask, 'scale_factor'] = (
            taz_with_targets.loc[nonzero_mask, maz_control] / 
            taz_with_targets.loc[nonzero_mask, 'current_sum']
        )
        
        # Apply scaling to TAZ categories
        for col in existing_taz_controls:
            # Apply proportional scaling
            taz_updated[col] *= taz_with_targets['scale_factor']
        
        # Handle special case: zero current sum but non-zero target
        zero_current_nonzero_target = (taz_with_targets['current_sum'] == 0) & (taz_with_targets[maz_control] > 0)
        if zero_current_nonzero_target.any():
            for idx in taz_with_targets[zero_current_nonzero_target].index:
                target_value = taz_with_targets.loc[idx, maz_control]
                per_category = target_value / len(existing_taz_controls)
                for col in existing_taz_controls:
                    taz_updated.loc[idx, col] = per_category
        
        # Count adjustments
        adjustment_mask = (
            (abs(taz_with_targets['current_sum'] - taz_with_targets[maz_control]) > HIERARCHICAL_TOLERANCE) |
            zero_current_nonzero_target
        )
        adjustments_made = adjustment_mask.sum()
        
        print(f"  Adjusted {adjustments_made} TAZs for {alt_control_name}")
        total_adjustments += adjustments_made
    
    # Print summary
    if total_adjustments > 0:
        print(f"\nHierarchical Consistency Summary: {total_adjustments} total TAZ adjustments applied")
        print("TAZ categories have been proportionally scaled to match MAZ totals.")
    else:
        print("No enforcement needed - all controls already consistent!")
    
    print("=== HIERARCHICAL CONSISTENCY ENFORCED (CORRECTED) ===")
    print("MAZ totals remained unchanged (authoritative).")
    print("TAZ categories were proportionally adjusted so each TAZ sums to its constituent MAZs.")
    
    return maz_updated, taz_updated


BAY_AREA_COUNTY_FIPS  = collections.OrderedDict([
    ("Alameda"      ,"001"),
    ("Contra Costa" ,"013"),
    ("Marin"        ,"041"),
    ("Napa"         ,"055"),
    ("San Francisco","075"),
    ("San Mateo"    ,"081"),
    ("Santa Clara"  ,"085"),
    ("Solano"       ,"095"),
    ("Sonoma"       ,"097"),
])

CA_STATE_FIPS = "06"

# Bay Area county configuration consolidation
def get_bay_area_county_codes():
    """Return list of Bay Area county FIPS codes (3-digit, zero-padded)."""
    return list(BAY_AREA_COUNTY_FIPS.values())

def get_bay_area_county_geoids():
    """Return list of Bay Area county GEOIDs (5-digit: state + county)."""
    return [CA_STATE_FIPS + county_fips for county_fips in BAY_AREA_COUNTY_FIPS.values()]

def get_county_info():
    """Return comprehensive county information dictionary."""
    return {
        'state_fips': CA_STATE_FIPS,
        'county_fips_codes': list(BAY_AREA_COUNTY_FIPS.values()),
        'county_names': list(BAY_AREA_COUNTY_FIPS.keys()),
        'county_geoids': get_bay_area_county_geoids(),
        'county_name_to_fips': BAY_AREA_COUNTY_FIPS,
        'county_recode_df': COUNTY_RECODE
    }

def get_county_name_mapping():
    """Return mapping of county FIPS codes to county names."""
    return dict(zip(BAY_AREA_COUNTY_FIPS.values(), BAY_AREA_COUNTY_FIPS.keys()))

def get_crosswalk_to_fips_mapping():
    """Return mapping from crosswalk county codes to 3-digit FIPS codes.
    
    The crosswalk uses last 2 digits of FIPS codes (1, 13, 41, etc.)
    This maps them to full 3-digit FIPS format (001, 013, 041, etc.)
    """
    return {
        1: '001',   # Alameda
        13: '013',  # Contra Costa  
        41: '041',  # Marin
        55: '055',  # Napa
        75: '075',  # San Francisco
        81: '081',  # San Mateo
        85: '085',  # Santa Clara
        95: '095',  # Solano
        97: '097'   # Sonoma
    }

def get_default_county_fips():
    """Return default county FIPS code for missing mappings (San Francisco)."""
    return '075'

CENSUS_DEFINITIONS = {
    # 2020 PL 94-171 Redistricting Data (block-level)
    "P1_001N": [  # Total population
        ["variable"],
        ["P1_001N"]
    ],
    "P1_002N": [  # Population in households
        ["variable"],
        ["P1_002N"]
    ],
    "P1_003N": [  # Population in group quarters
        ["variable"],
        ["P1_003N"]
    ],
    "H1_001N": [  # Total housing units
        ["variable"],
        ["H1_001N"]
    ],
    "H1_002N": [  # Occupied housing units (households)
        ["variable"],
        ["H1_002N"]
    ],
    "H1_003N": [  # Vacant housing units
        ["variable"],
        ["H1_003N"]
    ],
    "B23025": [  # ACS5-2023: Employment status
        ["variable","inlaborforce","type","employed"],
        ["B23025_001E","All","All","All"],
        ["B23025_002E","Yes","All","All"],
        ["B23025_003E","Yes","Civilian","All"],
        ["B23025_004E","Yes","Civilian","Employed"],
        ["B23025_005E","Yes","Civilian","Unemployed"],
        ["B23025_006E","Yes","Armed Forces","Employed"],
        ["B23025_007E","No","All","All"]
    ],
    "B26001": [  # ACS5-2023: Group quarters population
        ["variable"],
        ["B26001_001E", "B26001_006E", "B26001_007E"]
    ],
    "B26010": [  # ACS5-2023: Group quarters population by type
        ["variable", "gq_type"],
        ["B26010_001E", "All"],
        ["B26010_008E", "Military"],
        ["B26010_005E", "University"]
    ],
    "B11002": [  # ACS5-2023: Household type (including living alone)
        ["variable"],
        ["B11002_001E"]
    ],
    "B01001": [  # ACS5-2023: Sex by age - Complete age breakdown
        ["variable", "sex", "age_min", "age_max"],
        ["B01001_001E", "All", 0, AGE_MAX],
        ["B01001_002E", "Male", 0, AGE_MAX],
        ["B01001_026E", "Female", 0, AGE_MAX],
        # Male age categories
        ["B01001_003E", "Male", 0, 4],
        ["B01001_004E", "Male", 5, 9],
        ["B01001_005E", "Male", 10, 14],
        ["B01001_006E", "Male", 15, 17],
        ["B01001_007E", "Male", 18, 19],
        ["B01001_008E", "Male", 20, 20],
        ["B01001_009E", "Male", 21, 21],
        ["B01001_010E", "Male", 22, 24],
        ["B01001_011E", "Male", 25, 29],
        ["B01001_012E", "Male", 30, 34],
        ["B01001_013E", "Male", 35, 39],
        ["B01001_014E", "Male", 40, 44],
        ["B01001_015E", "Male", 45, 49],
        ["B01001_016E", "Male", 50, 54],
        ["B01001_017E", "Male", 55, 59],
        ["B01001_018E", "Male", 60, 61],
        ["B01001_019E", "Male", 62, 64],
        ["B01001_020E", "Male", 65, 66],
        ["B01001_021E", "Male", 67, 69],
        ["B01001_022E", "Male", 70, 74],
        ["B01001_023E", "Male", 75, 79],
        ["B01001_024E", "Male", 80, 84],
        ["B01001_025E", "Male", 85, AGE_MAX],
        # Female age categories
        ["B01001_027E", "Female", 0, 4],
        ["B01001_028E", "Female", 5, 9],
        ["B01001_029E", "Female", 10, 14],
        ["B01001_030E", "Female", 15, 17],
        ["B01001_031E", "Female", 18, 19],
        ["B01001_032E", "Female", 20, 20],
        ["B01001_033E", "Female", 21, 21],
        ["B01001_034E", "Female", 22, 24],
        ["B01001_035E", "Female", 25, 29],
        ["B01001_036E", "Female", 30, 34],
        ["B01001_037E", "Female", 35, 39],
        ["B01001_038E", "Female", 40, 44],
        ["B01001_039E", "Female", 45, 49],
        ["B01001_040E", "Female", 50, 54],
        ["B01001_041E", "Female", 55, 59],
        ["B01001_042E", "Female", 60, 61],
        ["B01001_043E", "Female", 62, 64],
        ["B01001_044E", "Female", 65, 66],
        ["B01001_045E", "Female", 67, 69],
        ["B01001_046E", "Female", 70, 74],
        ["B01001_047E", "Female", 75, 79],
        ["B01001_048E", "Female", 80, 84],
        ["B01001_049E", "Female", 85, AGE_MAX]
    ],
    "B11005": [  # ACS5-2023: Household by presence of own children under 18 years
        ["variable", "num_kids_min", "num_kids_max"],
        ["B11005_001E", 0, NKID_MAX],
        ["B11005_002E", 1, NKID_MAX],
        ["B11005_011E", 0, 0]
    ],
    "B08202": [
        ["variable","workers_min","workers_max","persons_min","persons_max"],
        ["B08202_001E",0,NWOR_MAX,0,NPER_MAX],
        ["B08202_002E",0,0,0,NPER_MAX],
        ["B08202_003E",1,1,0,NPER_MAX],
        ["B08202_004E",2,2,0,NPER_MAX],
        ["B08202_005E",3,NWOR_MAX,0,NPER_MAX]
    ],
    "B11016": [
        ["variable","family","pers_min","pers_max"],
        ["B11016_001E","All",0,NPER_MAX],
        ["B11016_002E","Family",0,NPER_MAX],
        ["B11016_003E","Family",2,2],
        ["B11016_004E","Family",3,3],
        ["B11016_005E","Family",4,4],
        ["B11016_006E","Family",5,5],
        ["B11016_007E","Family",6,6],
        ["B11016_008E","Family",7,NPER_MAX],
        ["B11016_009E","Nonfamily",0,NPER_MAX],
        ["B11016_010E","Nonfamily",1,1],
        ["B11016_011E","Nonfamily",2,2],
        ["B11016_012E","Nonfamily",3,3],
        ["B11016_013E","Nonfamily",4,4],
        ["B11016_014E","Nonfamily",5,5],
        ["B11016_015E","Nonfamily",6,6],
        ["B11016_016E","Nonfamily",7,NPER_MAX]
    ],
    "B19001": [
        ["variable","hhinc_min","hhinc_max"],
        ["B19001_001E",0,HINC_MAX],
        ["B19001_002E",0,9999],
        ["B19001_003E",10000,14999],
        ["B19001_004E",15000,19999],
        ["B19001_005E",20000,24999],
        ["B19001_006E",25000,29999],
        ["B19001_007E",30000,34999],
        ["B19001_008E",35000,39999],
        ["B19001_009E",40000,44999],
        ["B19001_010E",45000,49999],
        ["B19001_011E",50000,59999],
        ["B19001_012E",60000,74999],
        ["B19001_013E",75000,99999],
        ["B19001_014E",100000,124999],
        ["B19001_015E",125000,149999],
        ["B19001_016E",150000,199999],
        ["B19001_017E",200000,HINC_MAX]
    ],
    "C24010": [
        ["variable","sex","occ_cat1","occ_cat2","occ_cat3"],
        ["C24010_001E","All","All","All","All"],
        ["C24010_002E","Male","All","All","All"],
        ["C24010_003E","Male","Management, business, science, and arts","All","All"],
        ["C24010_004E","Male","Management, business, science, and arts","Management, business, and financial","All"],
        ["C24010_005E","Male","Management, business, science, and arts","Management, business, and financial","Management"],
        ["C24010_006E","Male","Management, business, science, and arts","Management, business, and financial","Business and financial operations"],
        ["C24010_007E","Male","Management, business, science, and arts","Computer, engineering, and science","All"],
        ["C24010_008E","Male","Management, business, science, and arts","Computer, engineering, and science","Computer and mathematical"],
        ["C24010_009E","Male","Management, business, science, and arts","Computer, engineering, and science","Architecture and engineering"],
        ["C24010_010E","Male","Management, business, science, and arts","Computer, engineering, and science","Life, physical, and social science"],
        ["C24010_011E","Male","Management, business, science, and arts","Education, legal, community service, arts, and media","All"],
        ["C24010_012E","Male","Management, business, science, and arts","Education, legal, community service, arts, and media","Community and social service"],
        ["C24010_013E","Male","Management, business, science, and arts","Education, legal, community service, arts, and media","Legal"],
        ["C24010_014E","Male","Management, business, science, and arts","Education, legal, community service, arts, and media","Education, training, and library"],
        ["C24010_015E","Male","Management, business, science, and arts","Education, legal, community service, arts, and media","Arts, design, entertainment, sports, and media"],
        ["C24010_016E","Male","Management, business, science, and arts","Healthcare practitioners and technical","All"],
        ["C24010_017E","Male","Management, business, science, and arts","Healthcare practitioners and technical","Health diagnosing and treating practitioners and other technical"],
        ["C24010_018E","Male","Management, business, science, and arts","Healthcare practitioners and technical","Health technologists and technicians"],
        ["C24010_019E","Male","Service","All","All"],
        ["C24010_020E","Male","Service","Healthcare support","All"],
        ["C24010_021E","Male","Service","Protective service","All"],
        ["C24010_022E","Male","Service","Protective service","Fire fighting and prevention, and other protective service workers"],
        ["C24010_023E","Male","Service","Protective service","Law enforcement workers"],
        ["C24010_024E","Male","Service","Food preparation and serving related","All"],
        ["C24010_025E","Male","Service","Building and grounds cleaning and maintenance","All"],
        ["C24010_026E","Male","Service","Personal care and service","All"],
        ["C24010_027E","Male","Sales and office","All","All"],
        ["C24010_028E","Male","Sales and office","Sales and related","All"],
        ["C24010_029E","Male","Sales and office","Office and administrative support","All"],
        ["C24010_030E","Male","Natural resources, construction, and maintenance","All","All"],
        ["C24010_031E","Male","Natural resources, construction, and maintenance","Farming, fishing, and forestry","All"],
        ["C24010_032E","Male","Natural resources, construction, and maintenance","Construction and extraction","All"],
        ["C24010_033E","Male","Natural resources, construction, and maintenance","Installation, maintenance, and repair","All"],
        ["C24010_034E","Male","Production, transportation, and material moving","All","All"],
        ["C24010_035E","Male","Production, transportation, and material moving","Production","All"],
        ["C24010_036E","Male","Production, transportation, and material moving","Transportation","All"],
        ["C24010_037E","Male","Production, transportation, and material moving","Material moving","All"],
        ["C24010_038E","Female","All","All","All"],
        ["C24010_039E","Female","Management, business, science, and arts","All","All"],
        ["C24010_040E","Female","Management, business, science, and arts","Management, business, and financial","All"],
        ["C24010_041E","Female","Management, business, science, and arts","Management, business, and financial","Management"],
        ["C24010_042E","Female","Management, business, science, and arts","Management, business, and financial","Business and financial operations"],
        ["C24010_043E","Female","Management, business, science, and arts","Computer, engineering, and science","All"],
        ["C24010_044E","Female","Management, business, science, and arts","Computer, engineering, and science","Computer and mathematical"],
        ["C24010_045E","Female","Management, business, science, and arts","Computer, engineering, and science","Architecture and engineering"],
        ["C24010_046E","Female","Management, business, science, and arts","Computer, engineering, and science","Life, physical, and social science"],
        ["C24010_047E","Female","Management, business, science, and arts","Education, legal, community service, arts, and media","All"],
        ["C24010_048E","Female","Management, business, science, and arts","Education, legal, community service, arts, and media","Community and social service"],
        ["C24010_049E","Female","Management, business, science, and arts","Education, legal, community service, arts, and media","Legal"],
        ["C24010_050E","Female","Management, business, science, and arts","Education, legal, community service, arts, and media","Education, training, and library"],
        ["C24010_051E","Female","Management, business, science, and arts","Education, legal, community service, arts, and media","Arts, design, entertainment, sports, and media"],
        ["C24010_052E","Female","Management, business, science, and arts","Healthcare practitioners and technical","All"],
        ["C24010_053E","Female","Management, business, science, and arts","Healthcare practitioners and technical","Health diagnosing and treating practitioners and other technical"],
        ["C24010_054E","Female","Management, business, science, and arts","Healthcare practitioners and technical","Health technologists and technicians"],
        ["C24010_055E","Female","Service","All","All"],
        ["C24010_056E","Female","Service","Healthcare support","All"],
        ["C24010_057E","Female","Service","Protective service","All"],
        ["C24010_058E","Female","Service","Protective service","Fire fighting and prevention, and other protective service workers"],
        ["C24010_059E","Female","Service","Protective service","Law enforcement workers"],
        ["C24010_060E","Female","Service","Food preparation and serving related","All"],
        ["C24010_061E","Female","Service","Building and grounds cleaning and maintenance","All"],
        ["C24010_062E","Female","Service","Personal care and service","All"],
        ["C24010_063E","Female","Sales and office","All","All"],
        ["C24010_064E","Female","Sales and office","Sales and related","All"],
        ["C24010_065E","Female","Sales and office","Office and administrative support","All"],
        ["C24010_066E","Female","Natural resources, construction, and maintenance","All","All"],
        ["C24010_067E","Female","Natural resources, construction, and maintenance","Farming, fishing, and forestry","All"],
        ["C24010_068E","Female","Natural resources, construction, and maintenance","Construction and extraction","All"],
        ["C24010_069E","Female","Natural resources, construction, and maintenance","Installation, maintenance, and repair","All"],
        ["C24010_070E","Female","Production, transportation, and material moving","All","All"],
        ["C24010_071E","Female","Production, transportation, and material moving","Production","All"],
        ["C24010_072E","Female","Production, transportation, and material moving","Transportation","All"],
        ["C24010_073E","Female","Production, transportation, and material moving","Material moving","All"]
    ],
    # 2020 PL 94-171 Redistricting tables for group quarters (replaces DHC)
    "P5_001N": [  # Total group quarters population
        ["variable"],
        ["P5_001N"]
    ],
    "P5_008N": [  # Group quarters university/college student housing 
        ["variable"],
        ["P5_008N"]
    ],
    "P5_009N": [  # Group quarters military quarters
        ["variable"],
        ["P5_009N"]
    ],
    # ACS1-2023: Regional scaling targets (1-year estimates)
    "B25001": [  # Total housing units (households)
        ["variable"],
        ["B25001_001E"]
    ],
    "B01003": [  # Total population
        ["variable"],
        ["B01003_001E"]
    ],
    # ACS1 B26001 - only total group quarters available (no subcategories)
    "B26001_ACS1": [  # Total group quarters population (ACS1 version)
        ["variable"],
        ["B26001_001E"]
    ]
}

# Canonical column names for all geographies in all relevant tables
GEOGRAPHY_ID_COLUMNS = {
    'block': {
        'census': 'GEOID_block',
        'crosswalk': 'blk2020ge',
        'mapping': 'GEOID_block',  # Use GEOID_block to match maz_taz_def_df
        'components': ['state', 'county', 'tract', 'block'],
    },
    'block group': {
        'census': 'GEOID_block group',
        'crosswalk': 'bg2020ge',
        'mapping': 'GEOID_block group',  # Use GEOID_block group to match maz_taz_def_df
        'components': ['state', 'county', 'tract', 'block group'],
    },
    'tract': {
        'census': 'GEOID_tract',
        'crosswalk': 'tr2020ge',
        'mapping': 'GEOID_tract',  # Use GEOID_tract to match maz_taz_def_df
        'components': ['state', 'county', 'tract'],
    },
    'county': {
        'census': 'GEOID_county',
        'crosswalk': 'cty2020ge',
        'mapping': 'GEOID_county',  # Use GEOID_county to match maz_taz_def_df
        'components': ['state', 'county'],
    },
    'maz': {
        'mapping': 'MAZ',
    },
    'taz': {
        'mapping': 'TAZ',
    },
    'puma': {
        'mapping': 'PUMA',
    },
    # Add more as needed
}


# ============================================================================
# CONTROL CATEGORIES - Define groups of related controls for validation and analysis
# ============================================================================

# Control categories for different geography levels
# These are dynamically extracted from the CONTROLS configuration but can be overridden here
CONTROL_CATEGORIES = {
    'MAZ': {
        'household_counts': ['num_hh'],
        'group_quarters': ['gq_pop', 'gq_military', 'gq_university', 'gq_other'],
    },
    'TAZ': {
        'household_income': ['hhinc_0_14', 'hhinc_14_30', 'hhinc_30_60', 'hhinc_60_100', 'hhinc_100_175', 'hhinc_175_plus'],
        'household_workers': ['hh_wrks_0', 'hh_wrks_1', 'hh_wrks_2', 'hh_wrks_3_plus'],
        'person_age': ['pers_age_00_19', 'pers_age_20_34', 'pers_age_35_64', 'pers_age_65_plus'],
        'household_children': ['hh_kids_no', 'hh_kids_yes'],
        'household_size': ['hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus'],
    },
    'COUNTY': {
        'person_occupation': ['pers_occ_management', 'pers_occ_professional', 'pers_occ_services', 
                             'pers_occ_retail', 'pers_occ_manual_military'],
    }
}


def get_control_categories_for_geography(geography):
    """
    Get control categories for a specific geography level.
    Returns a dictionary of category_name -> list of control names.
    
    This function dynamically extracts control categories from the CONTROLS configuration,
    or falls back to the static CONTROL_CATEGORIES if controls are missing.
    """
    categories = {}
    
    # Always use INCOME_BIN_MAPPING for TAZ household_income
    if geography == 'TAZ':
        # Build household_income from INCOME_BIN_MAPPING
        categories['household_income'] = [b['control'] for b in INCOME_BIN_MAPPING]

    # Try to get from current CONTROLS configuration
    if geography in CONTROLS.get(ACS_EST_YEAR, {}):
        control_names = list(CONTROLS[ACS_EST_YEAR][geography].keys())
        # Group controls by patterns (prefix-based categorization)
        for control_name in control_names:
            if control_name.startswith('temp_'):
                continue  # Skip temp controls
            if control_name.startswith('hh_size_'):
                categories.setdefault('household_size', []).append(control_name)
            elif control_name.startswith('hh_inc_') and geography != 'TAZ':
                # For TAZ, already handled above
                categories.setdefault('household_income', []).append(control_name)
            elif control_name.startswith('hh_wrks_'):
                categories.setdefault('household_workers', []).append(control_name)
            elif control_name.startswith('hh_kids_'):
                categories.setdefault('household_children', []).append(control_name)
            elif control_name.startswith('pers_age_'):
                categories.setdefault('person_age', []).append(control_name)
            elif control_name.startswith('pers_occ_'):
                categories.setdefault('person_occupation', []).append(control_name)
            elif control_name.startswith('gq_'):
                categories.setdefault('group_quarters', []).append(control_name)
            elif control_name == 'num_hh':
                categories.setdefault('household_counts', []).append(control_name)
            else:
                categories.setdefault('other', []).append(control_name)

    # Fall back to static configuration if nothing found or supplement missing categories
    if geography in CONTROL_CATEGORIES:
        for category, controls in CONTROL_CATEGORIES[geography].items():
            if category == 'household_income' and geography == 'TAZ':
                continue  # Already handled above
            if category not in categories:
                categories[category] = controls
            else:
                # Merge, avoiding duplicates
                for control in controls:
                    if control not in categories[category]:
                        categories[category].append(control)
    
    return categories


def get_controls_in_category(geography, category):
    """
    Get all controls in a specific category for a geography.
    Returns a list of control names, or empty list if category doesn't exist.
    """
    categories = get_control_categories_for_geography(geography)
    return categories.get(category, [])


def get_all_expected_controls_for_geography(geography):
    """
    Get all expected controls for a geography level.
    Returns a list of all control names that should exist for this geography.
    """
    if geography in CONTROLS.get(ACS_EST_YEAR, {}):
        return list(CONTROLS[ACS_EST_YEAR][geography].keys())
    
    # Fall back to categories if no controls defined
    categories = get_control_categories_for_geography(geography)
    all_controls = []
    for control_list in categories.values():
        all_controls.extend(control_list)
    return all_controls


def get_missing_controls_for_geography(geography, existing_controls):
    """
    Get controls that are expected but missing from the existing_controls list.
    Returns a dictionary of {category: [missing_control_names]}.
    """
    expected_controls = get_all_expected_controls_for_geography(geography)
    missing_controls = [ctrl for ctrl in expected_controls if ctrl not in existing_controls]
    
    # Group missing controls by category
    categories = get_control_categories_for_geography(geography)
    missing_by_category = {}
    
    for category, controls in categories.items():
        missing_in_category = [ctrl for ctrl in controls if ctrl in missing_controls]
        if missing_in_category:
            missing_by_category[category] = missing_in_category
    
    return missing_by_category