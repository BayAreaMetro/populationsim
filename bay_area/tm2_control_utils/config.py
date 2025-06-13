import pandas
import collections

# File paths
MAZ_TAZ_DEF_FILE   = "M:\\Data\\GIS layers\\TM2_maz_taz_v2.2\\blocks_mazs_tazs.csv"
MAZ_TAZ_PUMA_FILE  = "M:\\Data\\GIS layers\\TM2_maz_taz_v2.2\\mazs_tazs_county_tract_PUMA10.csv"
CENSUS_API_KEY_FILE = "M:\\Data\\Census\\API\\new_key\\api-key.txt"
IPUMS_API_KEY_FILE  = "M:\\Data\\Census\\API\\ipums_key\\ipums-api-key.txt"
LOCAL_CACHE_FOLDER  = "M:\\Data\\Census\\NewCachedTablesForPopulationSimControls"

# Output directories and file formats 
HOUSEHOLDS_DIR = "households"
GROUP_QUARTERS_DIR = "group_quarters"
DATA_SUBDIR = "data"
GEO_CROSSWALK_FILE = "geo_cross_walk.csv"
MAZ_HH_POP_FILE = "maz_data_hh_pop.csv"
OUTPUT_DIR_FMT = "output_{}"
CONTROL_FILE_FMT = "{}_{}_controls.csv"


# Constants
AGE_MAX  = 130
NKID_MAX = 10
NPER_MAX = 10
NWOR_MAX = 10
HINC_MAX = 2000000

# County recode DataFrame
COUNTY_RECODE = pandas.DataFrame([
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
    ('num_hh',         ('dec/dp', CENSUS_EST_YEAR, 'DP1_HOUSEHOLD_SIZE',       'block',
                        [collections.OrderedDict([('pers_min',1),('pers_max',NPER_MAX)])])),
    ('hh_size_1',      ('dec/dp', CENSUS_EST_YEAR, 'DP1_HOUSEHOLD_SIZE',       'block',
                        [collections.OrderedDict([('pers_min',1),('pers_max',1)])])),
    ('hh_size_2',      ('dec/dp', CENSUS_EST_YEAR, 'DP1_HOUSEHOLD_SIZE',       'block',
                        [collections.OrderedDict([('pers_min',2),('pers_max',2)])])),
    ('hh_size_3',      ('dec/dp', CENSUS_EST_YEAR, 'DP1_HOUSEHOLD_SIZE',       'block',
                        [collections.OrderedDict([('pers_min',3),('pers_max',3)])])),
    ('hh_size_4_plus', ('dec/dp', CENSUS_EST_YEAR, 'DP1_HOUSEHOLD_SIZE',       'block',
                        [collections.OrderedDict([('pers_min',4),('pers_max',NPER_MAX)])])),
    ('gq_num_hh',      ('dec/dhc', CENSUS_EST_YEAR, 'P5_GROUP_QUARTERS',        'block',
                        [collections.OrderedDict([('inst','Noninstitutional'),('subcategory','All')])])),
    ('gq_type_univ',   ('dec/dhc', CENSUS_EST_YEAR, 'P5_GROUP_QUARTERS',        'block',
                        [collections.OrderedDict([('inst','Noninstitutional'),
                                                  ('subcategory','College/University')])])),
    ('gq_type_mil',    ('dec/dhc', CENSUS_EST_YEAR, 'P5_GROUP_QUARTERS',        'block',
                        [collections.OrderedDict([('inst','Noninstitutional'),
                                                  ('subcategory','Military')])])),
    ('gq_type_othnon', ('dec/dhc', CENSUS_EST_YEAR, 'P5_GROUP_QUARTERS',        'block',
                        [collections.OrderedDict([('inst','Noninstitutional'),
                                                  ('subcategory','Other Noninstitutional')])])),
    ('tot_pop',        ('dec/dp', CENSUS_EST_YEAR, 'DP1_SEX_BY_AGE',           'block',
                        [collections.OrderedDict([('sex','All'),('age_min',0),('age_max',AGE_MAX)])])),
])

# ----------------------------------------
# MAZ controls for ACS estimate year
CONTROLS[ACS_EST_YEAR]['MAZ'] = collections.OrderedDict([
    ('temp_base_num_hh_b',    ('dec/dp', CENSUS_EST_YEAR, 'DP1_HOUSEHOLD_SIZE',       'block',
                               [collections.OrderedDict([('pers_min',1),('pers_max',NPER_MAX)])])),
    ('temp_base_num_hh_bg',   ('dec/dp', CENSUS_EST_YEAR, 'DP1_HOUSEHOLD_SIZE',       'block group',
                               [collections.OrderedDict([('pers_min',1),('pers_max',NPER_MAX)])])),
    ('temp_num_hh_bg_to_b',   ('acs5',    ACS_EST_YEAR,    'B11016',                   'block group',
                               [collections.OrderedDict([('pers_min',1),('pers_max',NPER_MAX)])],
                               'temp_base_num_hh_b','temp_base_num_hh_bg')),
    ('temp_num_hhinc',        ('acs5',    ACS_EST_YEAR,    'B19001',                   'block group',
                               [collections.OrderedDict([('hhinc_min',0),('hhinc_max',HINC_MAX)])])),
    ('hh_inc_30',             ('acs5',    ACS_EST_YEAR,    'B19001',                   'block group',
                               [collections.OrderedDict([('hhinc_min',0),('hhinc_max',34999)])],
                               'temp_num_hh_bg_to_b','temp_num_hhinc')),
    ('hh_inc_30_60',          ('acs5',    ACS_EST_YEAR,    'B19001',                   'block group',
                               [collections.OrderedDict([('hhinc_min',35000),('hhinc_max',74999)])],
                               'temp_num_hh_bg_to_b','temp_num_hhinc')),
    ('hh_inc_60_100',         ('acs5',    ACS_EST_YEAR,    'B19001',                   'block group',
                               [collections.OrderedDict([('hhinc_min',75000),('hhinc_max',124999)])],
                               'temp_num_hh_bg_to_b','temp_num_hhinc')),
    ('hh_inc_100_plus',       ('acs5',    ACS_EST_YEAR,    'B19001',                   'block group',
                               [collections.OrderedDict([('hhinc_min',125000),('hhinc_max',HINC_MAX)])],
                               'temp_num_hh_bg_to_b','temp_num_hhinc')),
    ('temp_num_hh_wrks',      ('acs5',    ACS_EST_YEAR,    'B08202',                   'tract',
                               [collections.OrderedDict([('workers_min',0),('workers_max',NWOR_MAX),
                                                         ('persons_min',0),('persons_max',NPER_MAX)])])),
    ('hh_wrks_0',             ('acs5',    ACS_EST_YEAR,    'B08202',                   'tract',
                               [collections.OrderedDict([('workers_min',0),('workers_max',0),
                                                         ('persons_min',0),('persons_max',NPER_MAX)])],
                               'temp_num_hh_bg_to_b','temp_num_hh_wrks')),
    ('hh_wrks_1',             ('acs5',    ACS_EST_YEAR,    'B08202',                   'tract',
                               [collections.OrderedDict([('workers_min',1),('workers_max',1),
                                                         ('persons_min',0),('persons_max',NPER_MAX)])],
                               'temp_num_hh_bg_to_b','temp_num_hh_wrks')),
    ('hh_wrks_2',             ('acs5',    ACS_EST_YEAR,    'B08202',                   'tract',
                               [collections.OrderedDict([('workers_min',2),('workers_max',2),
                                                         ('persons_min',0),('persons_max',NPER_MAX)])],
                               'temp_num_hh_bg_to_b','temp_num_hh_wrks')),
    ('hh_wrks_3_plus',        ('acs5',    ACS_EST_YEAR,    'B08202',                   'tract',
                               [collections.OrderedDict([('workers_min',3),('workers_max',NWOR_MAX),
                                                         ('persons_min',0),('persons_max',NPER_MAX)])],
                               'temp_num_hh_bg_to_b','temp_num_hh_wrks')),
    ('temp_base_num_pers_hh_b',('dec/dp', CENSUS_EST_YEAR, 'DP1_POPULATION_IN_HOUSEHOLDS','block',
                                [collections.OrderedDict([('age_min',0),('age_max',AGE_MAX)])])),
    ('temp_base_num_pers_hh_bg',('dec/dp', CENSUS_EST_YEAR, 'DP1_POPULATION_IN_HOUSEHOLDS','block group',
                                 [collections.OrderedDict([('age_min',0),('age_max',AGE_MAX)])])),
    ('temp_num_pers_hh_bg_to_b',('acs5',    ACS_EST_YEAR,    'B11002',                   'block group',
                                 [collections.OrderedDict([])],
                                 'temp_base_num_pers_hh_b','temp_base_num_pers_hh_bg')),
    ('temp_num_pers',         ('acs5',    ACS_EST_YEAR,    'B01001',                   'block group',
                               [collections.OrderedDict([('sex','All'),('age_min',0),('age_max',AGE_MAX)])])),
    ('pers_age_00_19',        ('acs5',    ACS_EST_YEAR,    'B01001',                   'block group',
                               [collections.OrderedDict([('age_min',0),('age_max',19)])],
                               'temp_num_pers_hh_bg_to_b','temp_num_pers')),
    ('pers_age_20_34',        ('acs5',    ACS_EST_YEAR,    'B01001',                   'block group',
                               [collections.OrderedDict([('age_min',20),('age_max',34)])],
                               'temp_num_pers_hh_bg_to_b','temp_num_pers')),
    ('pers_age_35_64',        ('acs5',    ACS_EST_YEAR,    'B01001',                   'block group',
                               [collections.OrderedDict([('age_min',35),('age_max',64)])],
                               'temp_num_pers_hh_bg_to_b','temp_num_pers')),
    ('pers_age_65_plus',      ('acs5',    ACS_EST_YEAR,    'B01001',                   'block group',
                               [collections.OrderedDict([('age_min',65),('age_max',AGE_MAX)])],
                               'temp_num_pers_hh_bg_to_b','temp_num_pers')),
    ('temp_num_hh_kids',      ('acs5',    ACS_EST_YEAR,    'B11005',                   'block group',
                               [collections.OrderedDict([('num_kids_min',0),('num_kids_max',NKID_MAX)])])),
    ('hh_kids_no',            ('acs5',    ACS_EST_YEAR,    'B11005',                   'block group',
                               [collections.OrderedDict([('num_kids_min',0),('num_kids_max',0)])],
                               'temp_num_hh_bg_to_b','temp_num_hh_kids')),
    ('hh_kids_yes',           ('acs5',    ACS_EST_YEAR,    'B11005',                   'block group',
                               [collections.OrderedDict([('num_kids_min',1),('num_kids_max',NKID_MAX)])],
                               'temp_num_hh_bg_to_b','temp_num_hh_kids')),
])

# ----------------------------------------
# COUNTY controls for Census estimate year
CONTROLS[CENSUS_EST_YEAR]['COUNTY'] = collections.OrderedDict([
    ('pers_occ_management',   ('acs5', ACS_EST_YEAR, 'C24010', 'tract', [
        collections.OrderedDict([('occ_cat1','Management, business, science, and arts'),
                                ('occ_cat2','Management, business, and financial'),
                                ('occ_cat3','Management')])
    ])),
    # … (other COUNTY entries for CENSUS_EST_YEAR) …
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
    "DP1_HOUSEHOLD_SIZE": [
        ["variable","pers_min","pers_max"],
        ["DP1_001E",1,NPER_MAX],
        ["DP1_002E",1,1],
        ["DP1_003E",2,2],
        ["DP1_004E",3,3],
        ["DP1_005E",4,4],
        ["DP1_006E",5,5],
        ["DP1_007E",6,6],
        ["DP1_008E",7,NPER_MAX]
    ],
    "DP1_POP_HH": [
        ["variable","age_min","age_max"],
        ["DP1_009E",0,AGE_MAX],
        ["DP1_010E",0,17],
        ["DP1_011E",18,AGE_MAX]
    ],
    "DP1_SEX_BY_AGE": [
        ["variable","sex","age_min","age_max"],
        ["DP1_012E","All",0,AGE_MAX],
        ["DP1_013E","Male",0,AGE_MAX],
        ["DP1_014E","Male",0,4],
        ["DP1_015E","Male",5,9],
        ["DP1_016E","Male",10,14],
        ["DP1_017E","Male",15,17],
        ["DP1_018E","Male",18,19],
        ["DP1_019E","Male",20,24],
        ["DP1_020E","Male",25,34],
        ["DP1_021E","Male",35,44],
        ["DP1_022E","Male",45,54],
        ["DP1_023E","Male",55,64],
        ["DP1_024E","Male",65,74],
        ["DP1_025E","Male",75,AGE_MAX],
        ["DP1_026E","Female",0,AGE_MAX],
        ["DP1_027E","Female",0,4],
        ["DP1_028E","Female",5,9],
        ["DP1_029E","Female",10,14],
        ["DP1_030E","Female",15,17],
        ["DP1_031E","Female",18,19],
        ["DP1_032E","Female",20,24],
        ["DP1_033E","Female",25,34],
        ["DP1_034E","Female",35,44],
        ["DP1_035E","Female",45,54],
        ["DP1_036E","Female",55,64],
        ["DP1_037E","Female",65,74],
        ["DP1_038E","Female",75,AGE_MAX]
    ],
    "B01001": [
        ["variable","sex","age_min","age_max"],
        ["B01001_001E","All",0,AGE_MAX],
        ["B01001_002E","Male",0,AGE_MAX],
        ["B01001_003E","Male",0,4],
        ["B01001_004E","Male",5,9],
        ["B01001_005E","Male",10,14],
        ["B01001_006E","Male",15,17],
        ["B01001_007E","Male",18,19],
        ["B01001_008E","Male",20,20],
        ["B01001_009E","Male",21,21],
        ["B01001_010E","Male",22,24],
        ["B01001_011E","Male",25,29],
        ["B01001_012E","Male",30,34],
        ["B01001_013E","Male",35,39],
        ["B01001_014E","Male",40,44],
        ["B01001_015E","Male",45,49],
        ["B01001_016E","Male",50,54],
        ["B01001_017E","Male",55,59],
        ["B01001_018E","Male",60,61],
        ["B01001_019E","Male",62,64],
        ["B01001_020E","Male",65,66],
        ["B01001_021E","Male",67,69],
        ["B01001_022E","Male",70,74],
        ["B01001_023E","Male",75,79],
        ["B01001_024E","Male",80,84],
        ["B01001_025E","Male",85,AGE_MAX],
        ["B01001_026E","Female",0,AGE_MAX],
        ["B01001_027E","Female",0,4],
        ["B01001_028E","Female",5,9],
        ["B01001_029E","Female",10,14],
        ["B01001_030E","Female",15,17],
        ["B01001_031E","Female",18,19],
        ["B01001_032E","Female",20,20],
        ["B01001_033E","Female",21,21],
        ["B01001_034E","Female",22,24],
        ["B01001_035E","Female",25,29],
        ["B01001_036E","Female",30,34],
        ["B01001_037E","Female",35,39],
        ["B01001_038E","Female",40,44],
        ["B01001_039E","Female",45,49],
        ["B01001_040E","Female",50,54],
        ["B01001_041E","Female",55,59],
        ["B01001_042E","Female",60,61],
        ["B01001_043E","Female",62,64],
        ["B01001_044E","Female",65,66],
        ["B01001_045E","Female",67,69],
        ["B01001_046E","Female",70,74],
        ["B01001_047E","Female",75,79],
        ["B01001_048E","Female",80,84],
        ["B01001_049E","Female",85,AGE_MAX]
    ],
    "B11002": [
        ["variable"],
        ["B11002_001E"]
    ],
    "B11005": [
        ["variable","family","famtype","num_kids_min","num_kids_max"],
        ["B11005_002E","All","All",1, NKID_MAX],
        ["B11005_011E","All","All",0,0]
    ],
    "P5_GROUP_QUARTERS": [
        ["variable","inst","subcategory"],
        ["P5_001E","All","All"],
        ["P5_002E","Inst","All"],
        ["P5_003E","Inst","Correctional"],
        ["P5_004E","Inst","Juvenile"],
        ["P5_005E","Inst","Nursing"],
        ["P5_006E","Inst","Other"],
        ["P5_007E","Noninst","All"],
        ["P5_008E","Noninst","College/University"],
        ["P5_009E","Noninst","Military"],
        ["P5_010E","Noninst","Other"]
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
    "PCT16": [  # 2020 Decennial DP1: Household type by children under 18
        ["variable","family","famtype","num_kids_min","num_kids_max"],
        ["DP1_0127E","All","All",0,NPER_MAX],
        ["DP1_0128E","All","HusWif",0,NPER_MAX],
        ["DP1_0129E","All","HusWif",0,0],
        ["DP1_0130E","All","HusWif",1,1],
        ["DP1_0131E","All","HusWif",2,2],
        ["DP1_0132E","All","HusWif",3,3],
        ["DP1_0133E","All","HusWif",4,NPER_MAX],
        ["DP1_0134E","All","MaleH",0,NPER_MAX],
        ["DP1_0135E","All","MaleH",0,0],
        ["DP1_0136E","All","MaleH",1,1],
        ["DP1_0137E","All","MaleH",2,2],
        ["DP1_0138E","All","MaleH",3,3],
        ["DP1_0139E","All","MaleH",4,NPER_MAX],
        ["DP1_0140E","All","FemaleH",0,NPER_MAX],
        ["DP1_0141E","All","FemaleH",0,0],
        ["DP1_0142E","All","FemaleH",1,1],
        ["DP1_0143E","All","FemaleH",2,2],
        ["DP1_0144E","All","FemaleH",3,3],
        ["DP1_0145E","All","FemaleH",4,NPER_MAX],
        ["DP1_0146E","All","All",0,NPER_MAX],
        ["DP1_0147E","All","All",0,0],
        ["DP1_0148E","All","All",1,1],
        ["DP1_0149E","All","All",2,2],
        ["DP1_0150E","All","All",3,3],
        ["DP1_0151E","All","All",4,NPER_MAX]
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