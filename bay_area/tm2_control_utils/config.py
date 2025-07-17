import pandas as pd
import collections

# File paths - Network locations (M: drive)
NETWORK_MAZ_TAZ_DEF_FILE   = "M:\\Data\\GIS layers\\TM2_maz_taz_v2.2\\blocks_mazs_tazs.csv"
NETWORK_MAZ_TAZ_PUMA_FILE  = "M:\\Data\\GIS layers\\TM2_maz_taz_v2.2\\mazs_tazs_county_tract_PUMA10.csv"
NETWORK_MAZ_TAZ_ALL_GEOG_FILE =  "M:\\Data\\GIS layers\\TM2_maz_taz_v2.2\\mazs_tazs_all_geog.csv"
NETWORK_CENSUS_API_KEY_FILE = "M:\\Data\\Census\\API\\new_key\\api-key.txt"
NETWORK_CACHE_FOLDER  = "M:\\Data\\Census\\NewCachedTablesForPopulationSimControls"

# Local file paths for offline work
LOCAL_DATA_DIR = "local_data"
LOCAL_MAZ_TAZ_DEF_FILE   = f"{LOCAL_DATA_DIR}\\gis\\blocks_mazs_tazs.csv"
LOCAL_MAZ_TAZ_PUMA_FILE  = f"{LOCAL_DATA_DIR}\\gis\\mazs_tazs_county_tract_PUMA10.csv"
LOCAL_MAZ_TAZ_ALL_GEOG_FILE = f"{LOCAL_DATA_DIR}\\gis\\mazs_tazs_all_geog.csv"
LOCAL_CENSUS_API_KEY_FILE = f"{LOCAL_DATA_DIR}\\census\\api-key.txt"
LOCAL_CACHE_FOLDER  = f"{LOCAL_DATA_DIR}\\census\\cache"

# Alternative local cache folder (for manually copied cache files)
INPUT_2023_CACHE_FOLDER = "input_2023\\NewCachedTablesForPopulationSimControls"

# Active file paths (will be set based on offline mode)
MAZ_TAZ_DEF_FILE = NETWORK_MAZ_TAZ_DEF_FILE
MAZ_TAZ_PUMA_FILE = NETWORK_MAZ_TAZ_PUMA_FILE
MAZ_TAZ_ALL_GEOG_FILE = NETWORK_MAZ_TAZ_ALL_GEOG_FILE
CENSUS_API_KEY_FILE = NETWORK_CENSUS_API_KEY_FILE
LOCAL_CACHE_FOLDER = NETWORK_CACHE_FOLDER

# Output directories and file formats 
HOUSEHOLDS_DIR = "households"
GROUP_QUARTERS_DIR = "group_quarters"
DATA_SUBDIR = "data"
GEO_CROSSWALK_FILE = "geo_cross_walk.csv"
MAZ_HH_POP_FILE = "maz_data_hh_pop.csv"
OUTPUT_DIR_FMT = "output_{}"
CONTROL_FILE_FMT = "{}_{}_controls.csv"


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
    {"GEOID_county":"06001", "COUNTY":4, "county_name":"Alameda"      , "REGION":1},
    {"GEOID_county":"06013", "COUNTY":5, "county_name":"Contra Costa" , "REGION":1},
    {"GEOID_county":"06041", "COUNTY":9, "county_name":"Marin"        , "REGION":1},
    {"GEOID_county":"06055", "COUNTY":7, "county_name":"Napa"         , "REGION":1},
    {"GEOID_county":"06075", "COUNTY":1, "county_name":"San Francisco", "REGION":1},
    {"GEOID_county":"06081", "COUNTY":2, "county_name":"San Mateo"    , "REGION":1},
    {"GEOID_county":"06085", "COUNTY":3, "county_name":"Santa Clara"  , "REGION":1},
    {"GEOID_county":"06095", "COUNTY":6, "county_name":"Solano"       , "REGION":1},
    {"GEOID_county":"06097", "COUNTY":8, "county_name":"Sonoma"       , "REGION":1}
])

# Years
CENSUS_EST_YEAR = 2020
CENSUS_GEOG_YEAR = 2010
ACS_EST_YEAR = 2023



CONTROLS = {
    CENSUS_EST_YEAR: collections.OrderedDict(),
    ACS_EST_YEAR:    collections.OrderedDict()
}

# ----------------------------------------
# MAZ controls for Census estimate year
CONTROLS[CENSUS_EST_YEAR]['MAZ'] = collections.OrderedDict([
    ('tot_pop',        ('dec', CENSUS_EST_YEAR, 'P1_001N', 'block', [])),
    ('pop_hh',         ('dec', CENSUS_EST_YEAR, 'P1_002N', 'block', [])),
    ('pop_gq',         ('dec', CENSUS_EST_YEAR, 'P1_003N', 'block', [])),
    ('tot_hu',         ('dec', CENSUS_EST_YEAR, 'H1_001N', 'block', [])),
    ('occ_hu',         ('dec', CENSUS_EST_YEAR, 'H1_002N', 'block', [])),
    ('vac_hu',         ('dec', CENSUS_EST_YEAR, 'H1_003N', 'block', [])),
])

# ----------------------------------------
# MAZ controls for ACS estimate year
CONTROLS[ACS_EST_YEAR]['MAZ'] = collections.OrderedDict([
    # block‐level households (occupied units) from PL redistricting file - scaled to 2023
    ('temp_base_num_hh_b',    ('pl',  CENSUS_EST_YEAR, 'H1_002N',       'block',
                               [], 'regional_scale')),
    # block‐group–level households from PL redistricting file - scaled to 2023
    ('temp_base_num_hh_bg',   ('pl',  CENSUS_EST_YEAR, 'H1_002N',       'block group',
                               [], 'regional_scale')),
    # Total population from 2020 Census - scaled to 2023 ACS estimates
    ('tot_pop',               ('pl',  CENSUS_EST_YEAR, 'P1_001N',       'block',
                               [], 'regional_scale')),
    # Group quarters population from 2020 Census - scaled to 2023 ACS estimates  
    ('gq_pop',                ('pl',  CENSUS_EST_YEAR, 'P1_003N',       'block',
                               [], 'regional_scale')),
    # distribute ACS5 household counts down to blocks
    ('temp_num_hh_bg_to_b',   ('acs5', ACS_EST_YEAR,    'B11016',       'block group',
                               [collections.OrderedDict([('pers_min',1),('pers_max',NPER_MAX)])],
                               'temp_base_num_hh_b','temp_base_num_hh_bg')),
    # ACS5 household income distribution at block‐group
    ('temp_num_hhinc',        ('acs5', ACS_EST_YEAR,    'B19001',       'block group',
                               [collections.OrderedDict([('hhinc_min',0),   ('hhinc_max',HINC_MAX)])])),
    ('hh_inc_30',             ('acs5', ACS_EST_YEAR,    'B19001',       'block group',
                               [collections.OrderedDict([('hhinc_min',0),   ('hhinc_max',34999)])],
                               'temp_num_hh_bg_to_b','temp_num_hhinc')),
    ('hh_inc_30_60',          ('acs5', ACS_EST_YEAR,    'B19001',       'block group',
                               [collections.OrderedDict([('hhinc_min',35000),('hhinc_max',74999)])],
                               'temp_num_hh_bg_to_b','temp_num_hhinc')),
    ('hh_inc_60_100',         ('acs5', ACS_EST_YEAR,    'B19001',       'block group',
                               [collections.OrderedDict([('hhinc_min',75000),('hhinc_max',124999)])],
                               'temp_num_hh_bg_to_b','temp_num_hhinc')),
    ('hh_inc_100_plus',       ('acs5', ACS_EST_YEAR,    'B19001',       'block group',
                               [collections.OrderedDict([('hhinc_min',125000),('hhinc_max',HINC_MAX)])],
                               'temp_num_hh_bg_to_b','temp_num_hhinc')),
    # ACS5 workers per household at tract level
    ('temp_num_hh_wrks',      ('acs5', ACS_EST_YEAR,    'B08202',       'tract',
                               [collections.OrderedDict([('workers_min',0),('workers_max',NWOR_MAX),
                                                         ('persons_min',0), ('persons_max',NPER_MAX)])])),
    ('hh_wrks_0',             ('acs5', ACS_EST_YEAR,    'B08202',       'tract',
                               [collections.OrderedDict([('workers_min',0),('workers_max',0),
                                                         ('persons_min',0), ('persons_max',NPER_MAX)])],
                               'temp_num_hh_bg_to_b','temp_num_hh_wrks')),
    ('hh_wrks_1',             ('acs5', ACS_EST_YEAR,    'B08202',       'tract',
                               [collections.OrderedDict([('workers_min',1),('workers_max',1),
                                                         ('persons_min',0), ('persons_max',NPER_MAX)])],
                               'temp_num_hh_bg_to_b','temp_num_hh_wrks')),
    ('hh_wrks_2',             ('acs5', ACS_EST_YEAR,    'B08202',       'tract',
                               [collections.OrderedDict([('workers_min',2),('workers_max',2),
                                                         ('persons_min',0), ('persons_max',NPER_MAX)])],
                               'temp_num_hh_bg_to_b','temp_num_hh_wrks')),
    ('hh_wrks_3_plus',        ('acs5', ACS_EST_YEAR,    'B08202',       'tract',
                               [collections.OrderedDict([('workers_min',3),('workers_max',NWOR_MAX),
                                                         ('persons_min',0), ('persons_max',NPER_MAX)])],
                               'temp_num_hh_bg_to_b','temp_num_hh_wrks')),
    # block‐level persons‐in‐households from PL redistricting file
    ('temp_base_num_pers_hh_b', ('pl', CENSUS_EST_YEAR, 'P1_002N', 'block', [])),
    # block‐group–level persons‐in‐households from PL redistricting file
    ('temp_base_num_pers_hh_bg', ('pl', CENSUS_EST_YEAR, 'P1_002N', 'block group', [])),
    # distribute ACS5 persons‐in‐households down to blocks
    ('temp_num_pers_hh_bg_to_b',('acs5', ACS_EST_YEAR,    'B11002',       'block group',
                                 [collections.OrderedDict([])],
                                 'temp_base_num_pers_hh_b','temp_base_num_pers_hh_bg')),
    # ACS5 total persons by age at block‐group
    ('temp_num_pers',         ('acs5', ACS_EST_YEAR,    'B01001',       'block group',
                               [collections.OrderedDict([('sex','All'),
                                                         ('age_min',0),('age_max',AGE_MAX)])])),
    ('pers_age_00_19',        ('acs5', ACS_EST_YEAR,    'B01001',       'block group',
                               [collections.OrderedDict([('age_min',0),('age_max',19)])],
                               'temp_num_pers_hh_bg_to_b','temp_num_pers')),
    ('pers_age_20_34',        ('acs5', ACS_EST_YEAR,    'B01001',       'block group',
                               [collections.OrderedDict([('age_min',20),('age_max',34)])],
                               'temp_num_pers_hh_bg_to_b','temp_num_pers')),
    ('pers_age_35_64',        ('acs5', ACS_EST_YEAR,    'B01001',       'block group',
                               [collections.OrderedDict([('age_min',35),('age_max',64)])],
                               'temp_num_pers_hh_bg_to_b','temp_num_pers')),
    ('pers_age_65_plus',      ('acs5', ACS_EST_YEAR,    'B01001',       'block group',
                               [collections.OrderedDict([('age_min',65),('age_max',AGE_MAX)])],
                               'temp_num_pers_hh_bg_to_b','temp_num_pers')),
    # ACS5 households with children at block‐group
    ('temp_num_hh_kids',      ('acs5', ACS_EST_YEAR,    'B11005',       'block group',
                               [collections.OrderedDict([('num_kids_min',0),('num_kids_max',NKID_MAX)])])),
    ('hh_kids_no',            ('acs5', ACS_EST_YEAR,    'B11005',       'block group',
                               [collections.OrderedDict([('num_kids_min',0),('num_kids_max',0)])],
                               'temp_num_hh_bg_to_b','temp_num_hh_kids')),
    ('hh_kids_yes',           ('acs5', ACS_EST_YEAR,    'B11005',       'block group',
                               [collections.OrderedDict([('num_kids_min',1),('num_kids_max',NKID_MAX)])],
                               'temp_num_hh_bg_to_b','temp_num_hh_kids')),
    # ACS5 household size distribution at block‐group - TEMP CONTROL MUST COME FIRST
    ('temp_num_hh_size',      ('acs5', ACS_EST_YEAR,    'B11016',       'block group',
                               [collections.OrderedDict([('pers_min',1),('pers_max',NPER_MAX)])])),
    ('hh_size_1',             ('acs5', ACS_EST_YEAR,    'B11016',       'block group',
                               [collections.OrderedDict([('pers_min',1),('pers_max',1)])],
                               'temp_num_hh_bg_to_b','temp_num_hh_size')),
    ('hh_size_2',             ('acs5', ACS_EST_YEAR,    'B11016',       'block group',
                               [collections.OrderedDict([('pers_min',2),('pers_max',2)])],
                               'temp_num_hh_bg_to_b','temp_num_hh_size')),
    ('hh_size_3',             ('acs5', ACS_EST_YEAR,    'B11016',       'block group',
                               [collections.OrderedDict([('pers_min',3),('pers_max',3)])],
                               'temp_num_hh_bg_to_b','temp_num_hh_size')),
    ('hh_size_4_plus',        ('acs5', ACS_EST_YEAR,    'B11016',       'block group',
                               [collections.OrderedDict([('pers_min',4),('pers_max',NPER_MAX)])],
                               'temp_num_hh_bg_to_b','temp_num_hh_size')),
])


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
    # Military
    ('temp_gq_type_mil',      ('pl', CENSUS_EST_YEAR, 'P5', 'tract', [
        collections.OrderedDict([('inst','Noninst'), ('subcategory','Military')])
    ])),
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
# REGION controls
CONTROLS[CENSUS_EST_YEAR]['REGION'] = collections.OrderedDict([
    ('gq_num_hh_region', 'special')
])
CONTROLS[ACS_EST_YEAR]['REGION'] = collections.OrderedDict([
    ('gq_num_hh_region', 'special')
])

# ----------------------------------------
# REGION TARGETS for scaling MAZ controls to 2023 ACS estimates
CONTROLS[ACS_EST_YEAR]['REGION_TARGETS'] = collections.OrderedDict([
    # Total households from ACS 2023 county estimates (B25001)
    ('num_hh_target',     ('acs5', ACS_EST_YEAR, 'B25001', 'county', [])),
    # Total population from ACS 2023 county estimates (B01003) 
    ('tot_pop_target',    ('acs5', ACS_EST_YEAR, 'B01003', 'county', [])),
    # Group quarters population from ACS 2023 county estimates (B26001)
    ('pop_gq_target',     ('acs5', ACS_EST_YEAR, 'B26001', 'county', [])),
])



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
    "P5": [  # PL 94-171: Group quarters population by major group quarters type
        ["variable", "inst", "subcategory"],
        ["P5_001N", "All", "All"],
        ["P5_002N", "Inst", "All"],
        ["P5_003N", "Inst", "Correctional facilities for adults"],
        ["P5_004N", "Inst", "Juvenile facilities"],
        ["P5_005N", "Inst", "Nursing facilities/Skilled-nursing facilities"],
        ["P5_006N", "Inst", "Other institutional facilities"],
        ["P5_007N", "Noninst", "All"],
        ["P5_008N", "Noninst", "College/University student housing"],
        ["P5_009N", "Noninst", "Military"],
        ["P5_010N", "Noninst", "Other noninstitutional facilities"]
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
        ["B26001_001E"]
    ],
    "B11002": [  # ACS5-2023: Household type (including living alone)
        ["variable"],
        ["B11002_001E"]
    ],
    "B01001": [  # ACS5-2023: Sex by age
        ["variable", "sex", "age_min", "age_max"],
        ["B01001_001E", "All", 0, AGE_MAX],
        ["B01001_002E", "Male", 0, AGE_MAX],
        ["B01001_026E", "Female", 0, AGE_MAX]
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
        ["B08202_005E",3,NWOR_MAX,0,NPER_MAX],
        ["B08202_006E",0,NWOR_MAX,1,1],
        ["B08202_007E",0,0,1,1],
        ["B08202_008E",1,1,1,1],
        ["B08202_009E",0,NWOR_MAX,2,2],
        ["B08202_010E",0,0,2,2],
        ["B08202_011E",1,1,2,2],
        ["B08202_012E",2,2,2,2],
        ["B08202_013E",0,NWOR_MAX,3,3],
        ["B08202_014E",0,0,3,3],
        ["B08202_015E",1,1,3,3],
        ["B08202_016E",2,2,3,3],
        ["B08202_017E",3,3,3,3],
        ["B08202_018E",0,NWOR_MAX,4,NPER_MAX],
        ["B08202_019E",0,0,4,NPER_MAX],
        ["B08202_020E",1,1,4,NPER_MAX],
        ["B08202_021E",2,2,4,NPER_MAX],
        ["B08202_022E",3,NWOR_MAX,4,NPER_MAX]
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