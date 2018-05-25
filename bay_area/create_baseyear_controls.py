USAGE="""
Create baseyear controls for MTC Bay Area populationsim.

This script does the following:

1) Downloads the relevant Census tables to a local cache specified by CensusFetcher.LOCAL_CACHE_FOLDER,
   one table per file in CSV format.  These files are the raw tables at a census geography appropriate
   for the control geographies in this script, although the column headers have additional variables
   that are more descriptive of what the columns mean.

   To re-download the data using the Census API, remove the cache file.

2) It then combines the columns in the Census tables to match the control definitions in the
   CONTROLS structure in the script.

3) Finally, it transforms the control tables from the Census geographies to the desired control
   geography using the MAZ_TAZ_DEF_FILE, which defines MAZs and TAZs as unions of Census blocks.

   For controls derived from census data which is available at smaller geographies, this is a
   simple aggregation.

   However, for controls derived from census data which is not available at smaller geographies,
   it is assumed that the smaller geography's total (e.g. households) are apportioned similarly
   to it's census geography, and the controls are tallied that way.

4) It joins the MAZs and TAZs to the 2000 PUMAs (used in the 2007-2011 PUMS, which is
   used by create_seed_population.py) and saves these crosswalks as well.

   Outputs: households    /data/[model_year]_[maz,taz,county]_controls.csv
            households    /data/geo_cross_walk.csv
            group_quarters/data/[model_year]_maz_controls.csv
            group_quarters/data/geo_cross_walk.csv

            create_baseyear_controls_[model_year].log
"""

import argparse, collections, logging, os, sys
import census, us
import numpy, pandas, simpledbf

MAZ_TAZ_DEF_FILE   = "M:\\Data\\GIS layers\\TM2_maz_taz_v2.2\\blocks_mazs_tazs.csv"
MAZ_TAZ_PUMA_FILE  = "M:\\Data\\GIS layers\\TM2_maz_taz_v2.2\\mazs_TM2_v2_2_intersect_puma2000.dbf"  # NOTE these are PUMA 2000
AGE_MAX  = 130 # max person age
NKID_MAX = 10 # max number of kids
NPER_MAX = 10 # max number of persons
NWOR_MAX = 10 # max number of workers
HINC_MAX = 2000000

# COUNTY coding - census to our county code
COUNTY_RECODE = pandas.DataFrame([{"GEOID_county":"06001", "COUNTY":4, "county_name":"Alameda"      , "REGION":1},
                                  {"GEOID_county":"06013", "COUNTY":5, "county_name":"Contra Costa" , "REGION":1},
                                  {"GEOID_county":"06041", "COUNTY":9, "county_name":"Marin"        , "REGION":1},
                                  {"GEOID_county":"06055", "COUNTY":7, "county_name":"Napa"         , "REGION":1},
                                  {"GEOID_county":"06075", "COUNTY":1, "county_name":"San Francisco", "REGION":1},
                                  {"GEOID_county":"06081", "COUNTY":2, "county_name":"San Mateo"    , "REGION":1},
                                  {"GEOID_county":"06085", "COUNTY":3, "county_name":"Santa Clara"  , "REGION":1},
                                  {"GEOID_county":"06095", "COUNTY":6, "county_name":"Solano"       , "REGION":1},
                                  {"GEOID_county":"06097", "COUNTY":8, "county_name":"Sonoma"       , "REGION":1}])

class CensusFetcher:
    """
    Class to fetch the census data needed for these controls and cache them.

    Uses the census python package (https://pypi.org/project/census/)
    """
    # Location of the Census API key
    API_KEY_FILE = "M:\\Data\\Census\\API\\api-key.txt"

    # Store cache of census tables here
    LOCAL_CACHE_FOLDER = "M:\\Data\\Census\\CachedTablesForPopulationSimControls"

    CA_STATE_FIPS   = "06"

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

    # https://api.census.gov/data/2011/acs/acs5/variables.html
    # https://api.census.gov/data/2012/acs5/variables.html
    # https://api.census.gov/data/2010/sf1/variables.html

    CENSUS_DEFINITIONS = {
        "H13":[  # sf1, H13. Household Size [8]
            # Universe: Occupied housing units
            ["variable","pers_min", "pers_max"],
            ["H0130001",         1,   NPER_MAX], # Occupied housing units
            ["H0130002",         1,          1], #  1-person household
            ["H0130003",         2,          2], #  2-person household
            ["H0130004",         3,          3], #  3-person household
            ["H0130005",         4,          4], #  4-person household
            ["H0130006",         5,          5], #  5-person household
            ["H0130007",         6,          6], #  6-person household
            ["H0130008",         7,   NPER_MAX], #  7-or-more-person household
        ],
        "P16":[  # sf1, P16. POPULATION IN HOUSEHOLDS BY AGE
            # Universe: Population in households
            ["variable", "age_min", "age_max"],
            ["P0160001",         0,   AGE_MAX], # Population in households
            ["P0160002",         0,        17], # Under 18 years
            ["P0160003",        18,   AGE_MAX], # 18 years and over
        ],
        "P12":[  # sf1, P12. Sex By Age [49]
            # Universe: Total population
            ["variable", "sex", "age_min", "age_max"],
            ["P0120001", "All",         0,   AGE_MAX],        # Total population
            ["P0120002", "Male",        0,   AGE_MAX],        # Male:
            ["P0120003", "Male",        0,         4],        # Male: Under 5 years
            ["P0120004", "Male",        5,         9],        # Male: 5 to 9 years
            ["P0120005", "Male",       10,        14],        # Male: 10 to 14 years
            ["P0120006", "Male",       15,        17],        # Male: 15 to 17 years
            ["P0120007", "Male",       18,        19],        # Male: 18 and 19 years
            ["P0120008", "Male",       20,        20],        # Male: 20 years
            ["P0120009", "Male",       21,        21],        # Male: 21 years
            ["P0120010", "Male",       22,        24],        # Male: 22 to 24 years
            ["P0120011", "Male",       25,        29],        # Male: 25 to 29 years
            ["P0120012", "Male",       30,        34],        # Male: 30 to 34 years
            ["P0120013", "Male",       35,        39],        # Male: 35 to 39 years
            ["P0120014", "Male",       40,        44],        # Male: 40 to 44 years
            ["P0120015", "Male",       45,        49],        # Male: 45 to 49 years
            ["P0120016", "Male",       50,        54],        # Male: 50 to 54 years
            ["P0120017", "Male",       55,        59],        # Male: 55 to 59 years
            ["P0120018", "Male",       60,        61],        # Male: 60 and 61 years
            ["P0120019", "Male",       62,        64],        # Male: 62 to 64 years
            ["P0120020", "Male",       65,        66],        # Male: 65 and 66 years
            ["P0120021", "Male",       67,        69],        # Male: 67 to 69 years
            ["P0120022", "Male",       70,        74],        # Male: 70 to 74 years",
            ["P0120023", "Male",       75,        79],        # Male: 75 to 79 years",
            ["P0120024", "Male",       80,        84],        # Male: 80 to 84 years",
            ["P0120025", "Male",       85,   AGE_MAX],        # Male: 85 years and over",
            ["P0120026", "Female",      0,   AGE_MAX],        # Female:
            ["P0120027", "Female",      0,         4],        # Female: Under 5 years
            ["P0120028", "Female",      5,         9],        # Female: 5 to 9 years
            ["P0120029", "Female",     10,        14],        # Female: 10 to 14 years
            ["P0120030", "Female",     15,        17],        # Female: 15 to 17 years
            ["P0120031", "Female",     18,        19],        # Female: 18 and 19 years
            ["P0120032", "Female",     20,        20],        # Female: 20 years
            ["P0120033", "Female",     21,        21],        # Female: 21 years
            ["P0120034", "Female",     22,        24],        # Female: 22 to 24 years
            ["P0120035", "Female",     25,        29],        # Female: 25 to 29 years
            ["P0120036", "Female",     30,        34],        # Female: 30 to 34 years
            ["P0120037", "Female",     35,        39],        # Female: 35 to 39 years
            ["P0120038", "Female",     40,        44],        # Female: 40 to 44 years
            ["P0120039", "Female",     45,        49],        # Female: 45 to 49 years
            ["P0120040", "Female",     50,        54],        # Female: 50 to 54 years
            ["P0120041", "Female",     55,        59],        # Female: 55 to 59 years
            ["P0120042", "Female",     60,        61],        # Female: 60 and 61 years
            ["P0120043", "Female",     62,        64],        # Female: 62 to 64 years
            ["P0120044", "Female",     65,        66],        # Female: 65 and 66 years
            ["P0120045", "Female",     67,        69],        # Female: 67 to 69 years
            ["P0120046", "Female",     70,        74],        # Female: 70 to 74 years",
            ["P0120047", "Female",     75,        79],        # Female: 75 to 79 years",
            ["P0120048", "Female",     80,        84],        # Female: 80 to 84 years",
            ["P0120049", "Female",     85,   AGE_MAX],        # Female: 85 years and over",
        ],
        "P43":[  # sf1, P43. GROUP QUARTERS POPULATION BY SEX BY AGE BY GROUP QUARTERS TYPE [63]  
            # Universe: Population in group quarters
            ["variable", "sex",  "age_min", "age_max",     "inst","subcategory"  ],
            ["P0430001", "All",          0,       130,      "All", "All"         ],
            ["P0430002", "Male",         0,       130,      "All", "All"         ],
            ["P0430003", "Male",         0,        17,      "All", "All"         ],
            ["P0430004", "Male",         0,        17,     "Inst", "All"         ], # Institutionalized population (101-106, 201-203, 301, 401-405):
            ["P0430005", "Male",         0,        17,     "Inst", "Correctional"], # Institutionalized population (101-106, 201-203, 301, 401-405): - Correctional facilities for adults (101-106)
            ["P0430006", "Male",         0,        17,     "Inst", "Juvenile"    ], # Institutionalized population (101-106, 201-203, 301, 401-405): - Juvenile facilities (201-203)
            ["P0430007", "Male",         0,        17,     "Inst", "Nursing"     ], # Institutionalized population (101-106, 201-203, 301, 401-405): - Nursing facilities/Skilled-nursing facilities (301)
            ["P0430008", "Male",         0,        17,     "Inst", "Other"       ], # Institutionalized population (101-106, 201-203, 301, 401-405): - Other institutional facilities (401-405)
            ["P0430009", "Male",         0,        17,  "Noninst", "All"         ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904):
            ["P0430010", "Male",         0,        17,  "Noninst", "College"     ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904): - College/University student housing (501)
            ["P0430011", "Male",         0,        17,  "Noninst", "Military"    ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904): - Military quarters (601-602)
            ["P0430012", "Male",         0,        17,  "Noninst", "Other"       ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904): - Other noninstitutional facilities (701-702, 704, 706, 801-802, 900-901, 903-904)
            ["P0430013", "Male",        18,        64,      "All", "All"         ],
            ["P0430014", "Male",        18,        64,     "Inst", "All"         ], # Institutionalized population (101-106, 201-203, 301, 401-405):
            ["P0430015", "Male",        18,        64,     "Inst", "Correctional"], # Institutionalized population (101-106, 201-203, 301, 401-405): - Correctional facilities for adults (101-106)
            ["P0430016", "Male",        18,        64,     "Inst", "Juvenile"    ], # Institutionalized population (101-106, 201-203, 301, 401-405): - Juvenile facilities (201-203)
            ["P0430017", "Male",        18,        64,     "Inst", "Nursing"     ], # Institutionalized population (101-106, 201-203, 301, 401-405): - Nursing facilities/Skilled-nursing facilities (301)
            ["P0430018", "Male",        18,        64,     "Inst", "Other"       ], # Institutionalized population (101-106, 201-203, 301, 401-405): - Other institutional facilities (401-405)
            ["P0430019", "Male",        18,        64,  "Noninst", "All"         ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904):
            ["P0430020", "Male",        18,        64,  "Noninst", "College"     ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904): - College/University student housing (5
            ["P0430021", "Male",        18,        64,  "Noninst", "Military"    ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904): - Military quarters (601-602)
            ["P0430022", "Male",        18,        64,  "Noninst", "Other"       ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904): - Other noninstitutional facilities (701-702, 704, 706, 801-802, 900-901, 903-904)
            ["P0430023", "Male",        65,       130,      "All", "All"         ],
            ["P0430024", "Male",        65,       130,     "Inst", "All"         ], # Institutionalized population (101-106, 201-203, 301, 401-405):
            ["P0430025", "Male",        65,       130,     "Inst", "Correctional"], # Institutionalized population (101-106, 201-203, 301, 401-405): - Correctional facilities for adults (101-106)
            ["P0430026", "Male",        65,       130,     "Inst", "Juvenile"    ], # Institutionalized population (101-106, 201-203, 301, 401-405): - Juvenile facilities (201-203)
            ["P0430027", "Male",        65,       130,     "Inst", "Nursing"     ], # Institutionalized population (101-106, 201-203, 301, 401-405): - Nursing facilities/Skilled-nursing facilities (301)
            ["P0430028", "Male",        65,       130,     "Inst", "Other"       ], # Institutionalized population (101-106, 201-203, 301, 401-405): - Other institutional facilities (401-405)
            ["P0430029", "Male",        65,       130,  "Noninst", "All"         ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904):
            ["P0430030", "Male",        65,       130,  "Noninst", "College"     ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904): - College/University student housing (5
            ["P0430031", "Male",        65,       130,  "Noninst", "Military"    ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904): - Military quarters (601-602)
            ["P0430032", "Male",        65,       130,  "Noninst", "Other"       ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904): - Other noninstitutional facilities (701-702, 704, 706, 801-802, 900-901, 903-904)
            ["P0430033", "Male",         0,       130,      "All", "All"         ],
            ["P0430034", "Female",       0,        17,      "All", "All"         ],
            ["P0430035", "Female",       0,        17,     "Inst", "All"         ], # Institutionalized population (101-106, 201-203, 301, 401-405):
            ["P0430036", "Female",       0,        17,     "Inst", "Correctional"], # Institutionalized population (101-106, 201-203, 301, 401-405): - Correctional facilities for adults (101-106)
            ["P0430037", "Female",       0,        17,     "Inst", "Juvenile"    ], # Institutionalized population (101-106, 201-203, 301, 401-405): - Juvenile facilities (201-203)
            ["P0430038", "Female",       0,        17,     "Inst", "Nursing"     ], # Institutionalized population (101-106, 201-203, 301, 401-405): - Nursing facilities/Skilled-nursing facilities (301)
            ["P0430039", "Female",       0,        17,     "Inst", "Other"       ], # Institutionalized population (101-106, 201-203, 301, 401-405): - Other institutional facilities (401-405)
            ["P0430040", "Female",       0,        17,  "Noninst", "All"         ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904):
            ["P0430041", "Female",       0,        17,  "Noninst", "College"     ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904): - College/University student housing (501)
            ["P0430042", "Female",       0,        17,  "Noninst", "Military"    ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904): - Military quarters (601-602)
            ["P0430043", "Female",       0,        17,  "Noninst", "Other"       ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904): - Other noninstitutional facilities (701-702, 704, 706, 801-802, 900-901, 903-904)
            ["P0430044", "Female",      18,        64,      "All", "All"         ],
            ["P0430045", "Female",      18,        64,     "Inst", "All"         ], # Institutionalized population (101-106, 201-203, 301, 401-405):
            ["P0430046", "Female",      18,        64,     "Inst", "Correctional"], # Institutionalized population (101-106, 201-203, 301, 401-405): - Correctional facilities for adults (101-106)
            ["P0430047", "Female",      18,        64,     "Inst", "Juvenile"    ], # Institutionalized population (101-106, 201-203, 301, 401-405): - Juvenile facilities (201-203)
            ["P0430048", "Female",      18,        64,     "Inst", "Nursing"     ], # Institutionalized population (101-106, 201-203, 301, 401-405): - Nursing facilities/Skilled-nursing facilities (301)
            ["P0430049", "Female",      18,        64,     "Inst", "Other"       ], # Institutionalized population (101-106, 201-203, 301, 401-405): - Other institutional facilities (401-405)
            ["P0430050", "Female",      18,        64,  "Noninst", "All"         ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904):
            ["P0430051", "Female",      18,        64,  "Noninst", "College"     ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904): - College/University student housing (5
            ["P0430052", "Female",      18,        64,  "Noninst", "Military"    ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904): - Military quarters (601-602)
            ["P0430053", "Female",      18,        64,  "Noninst", "Other"       ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904): - Other noninstitutional facilities (701-702, 704, 706, 801-802, 900-901, 903-904)
            ["P0430054", "Female",      65,       130,      "All", "All"         ],
            ["P0430055", "Female",      65,       130,     "Inst", "All"         ], # Institutionalized population (101-106, 201-203, 301, 401-405):
            ["P0430056", "Female",      65,       130,     "Inst", "Correctional"], # Institutionalized population (101-106, 201-203, 301, 401-405): - Correctional facilities for adults (101-106)
            ["P0430057", "Female",      65,       130,     "Inst", "Juvenile"    ], # Institutionalized population (101-106, 201-203, 301, 401-405): - Juvenile facilities (201-203)
            ["P0430058", "Female",      65,       130,     "Inst", "Nursing"     ], # Institutionalized population (101-106, 201-203, 301, 401-405): - Nursing facilities/Skilled-nursing facilities (301)
            ["P0430059", "Female",      65,       130,     "Inst", "Other"       ], # Institutionalized population (101-106, 201-203, 301, 401-405): - Other institutional facilities (401-405)
            ["P0430060", "Female",      65,       130,  "Noninst", "All"         ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904):
            ["P0430061", "Female",      65,       130,  "Noninst", "College"     ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904): - College/University student housing (5
            ["P0430062", "Female",      65,       130,  "Noninst", "Military"    ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904): - Military quarters (601-602)
            ["P0430063", "Female",      65,       130,  "Noninst", "Other"       ], # Noninstitutionalized population (501, 601-602, 701-702, 704, 706, 801-802, 900-901, 903-904): - Other noninstitutional facilities (701-702, 704, 706, 801-802, 900-901, 903-904)
        ],
        "PCT16":[ # sf1, PCT16. HOUSEHOLD TYPE BY NUMBER OF PEOPLE UNDER 18 YEARS (EXCLUDING HOUSEHOLDERS, SPOUSES, AND UNMARRIED PARTNERS) [26]
            # Universe: Households
            ["variable",   "family",   "famtype", "num_kids_min", "num_kids_max"],
            ["PCT0160001", "All",      "All",                  0,       NKID_MAX], # Total
            ["PCT0160002", "Family",   "All",                  0,       NKID_MAX], # Family households:
            ["PCT0160003", "Family",   "HusWif",               0,       NKID_MAX], # Family households: - Husband-wife family:
            ["PCT0160004", "Family",   "HusWif",               0,              0], # Family households: - Husband-wife family: - With no children under 18 years
            ["PCT0160005", "Family",   "HusWif",               1,              1], # Family households: - Husband-wife family: - With one child under 18 years
            ["PCT0160006", "Family",   "HusWif",               2,              2], # Family households: - Husband-wife family: - With two children under 18 years
            ["PCT0160007", "Family",   "HusWif",               3,              3], # Family households: - Husband-wife family: - With three children under 18 years
            ["PCT0160008", "Family",   "HusWif",               4,       NKID_MAX], # Family households: - Husband-wife family: - With four or more children under 18 years
            ["PCT0160009", "Family",   "MaleH",                0,       NKID_MAX], # Family households: - Male householder, no wife present:
            ["PCT0160010", "Family",   "MaleH",                0,              0], # Family households: - Male householder, no wife present: - With no children under 18 years
            ["PCT0160011", "Family",   "MaleH",                1,              1], # Family households: - Male householder, no wife present: - With one child under 18 years
            ["PCT0160012", "Family",   "MaleH",                2,              2], # Family households: - Male householder, no wife present: - With two children under 18 years
            ["PCT0160013", "Family",   "MaleH",                3,              3], # Family households: - Male householder, no wife present: - With three children under 18 years
            ["PCT0160014", "Family",   "MaleH",                4,       NKID_MAX], # Family households: - Male householder, no wife present: - With four or more children under 18 years
            ["PCT0160015", "Family",   "FemaleH",              0,       NKID_MAX], # Family households: - Female householder, no husband present:
            ["PCT0160016", "Family",   "FemaleH",              0,              0], # Family households: - Female householder, no husband present: - With no children under 18 years
            ["PCT0160017", "Family",   "FemaleH",              1,              1], # Family households: - Female householder, no husband present: - With one child under 18 years
            ["PCT0160018", "Family",   "FemaleH",              2,              2], # Family households: - Female householder, no husband present: - With two children under 18 years
            ["PCT0160019", "Family",   "FemaleH",              3,              3], # Family households: - Female householder, no husband present: - With three children under 18 years
            ["PCT0160020", "Family",   "FemaleH",              4,       NKID_MAX], # Family households: - Female householder, no husband present: - With four or more children under 18 years
            ["PCT0160021", "Nonfamily","All",                  0,       NKID_MAX], # Nonfamily households:
            ["PCT0160022", "Nonfamily","All",                  0,              0], # Nonfamily households: - With no children under 18 years
            ["PCT0160023", "Nonfamily","All",                  1,              1], # Nonfamily households: - With one child under 18 years
            ["PCT0160024", "Nonfamily","All",                  2,              2], # Nonfamily households: - With two children under 18 years
            ["PCT0160025", "Nonfamily","All",                  3,              3], # Nonfamily households: - With three children under 18 years
            ["PCT0160026", "Nonfamily","All",                  4,       NKID_MAX], # Nonfamily households: - With four or more children under 18 years
        ],
        "B08202":[ # acs5, B08202. HOUSEHOLD SIZE BY NUMBER OF WORKERS IN HOUSEHOLD
            # Universe: Households
            ["variable",   "workers_min","workers_max","persons_min","persons_max"],
            ["B08202_001E",            0,     NWOR_MAX,            0,     NPER_MAX], # Estimate; Total:
            ["B08202_002E",            0,            0,            0,     NPER_MAX], # Estimate; Total: - No workers
            ["B08202_003E",            1,            1,            0,     NPER_MAX], # Estimate; Total: - 1 worker
            ["B08202_004E",            2,            2,            0,     NPER_MAX], # Estimate; Total: - 2 workers
            ["B08202_005E",            3,     NWOR_MAX,            0,     NPER_MAX], # Estimate; Total: - 3 or more workers
            ["B08202_006E",            0,     NWOR_MAX,            1,            1], # Estimate; Total: - 1-person household:
            ["B08202_007E",            0,            0,            1,            1], # Estimate; Total: - 1-person household: - No workers
            ["B08202_008E",            1,            1,            1,            1], # Estimate; Total: - 1-person household: - 1 worker
            ["B08202_009E",            0,     NWOR_MAX,            2,            2], # Estimate; Total: - 2-person household:
            ["B08202_010E",            0,            0,            2,            2], # Estimate; Total: - 2-person household: - No workers
            ["B08202_011E",            1,            1,            2,            2], # Estimate; Total: - 2-person household: - 1 worker
            ["B08202_012E",            2,            2,            2,            2], # Estimate; Total: - 2-person household: - 2 workers
            ["B08202_013E",            0,     NWOR_MAX,            3,            3], # Estimate; Total: - 3-person household:
            ["B08202_014E",            0,            0,            3,            3], # Estimate; Total: - 3-person household: - No workers
            ["B08202_015E",            1,            1,            3,            3], # Estimate; Total: - 3-person household: - 1 worker
            ["B08202_016E",            2,            2,            3,            3], # Estimate; Total: - 3-person household: - 2 workers
            ["B08202_017E",            3,            3,            3,            3], # Estimate; Total: - 3-person household: - 3 workers
            ["B08202_018E",            0,     NWOR_MAX,            4,     NPER_MAX], # Estimate; Total: - 4-or-more-person household:
            ["B08202_019E",            0,            0,            4,     NPER_MAX], # Estimate; Total: - 4-or-more-person household: - No workers
            ["B08202_020E",            1,            1,            4,     NPER_MAX], # Estimate; Total: - 4-or-more-person household: - 1 worker
            ["B08202_021E",            2,            2,            4,     NPER_MAX], # Estimate; Total: - 4-or-more-person household: - 2 workers
            ["B08202_022E",            3,     NWOR_MAX,            4,     NPER_MAX], # Estimate; Total: - 4-or-more-person household: - 3 or more workers
        ],
        "B19001":[ # acs5, B19001. HOUSEHOLD INCOME IN THE PAST 12 MONTHS (IN 2010 INFLATION-ADJUSTED DOLLARS): 
            # USE acs 2006-2010 https://api.census.gov/data/2010/acs5/variables.html for 2010 dollars
            ["variable",   "hhinc_min", "hhinc_max"],
            ["B19001_001E",          0,    HINC_MAX], # Households
            ["B19001_002E",          0,       10000], # Households Less than $10,000
            ["B19001_003E",      10000,       14999], # Households $10,000 to $14,999
            ["B19001_004E",      15000,       19999], # Households $15,000 to $19,999
            ["B19001_005E",      20000,       24999], # Households $20,000 to $24,999
            ["B19001_006E",      25000,       29999], # Households $25,000 to $29,999
            ["B19001_007E",      30000,       34999], # Households $30,000 to $34,999
            ["B19001_008E",      35000,       39999], # Households $35,000 to $39,999
            ["B19001_009E",      40000,       44999], # Households $40,000 to $44,999
            ["B19001_010E",      45000,       49999], # Households $45,000 to $49,999
            ["B19001_011E",      50000,       59999], # Households $50,000 to $59,999
            ["B19001_012E",      60000,       74999], # Households $60,000 to $74,999
            ["B19001_013E",      75000,       99999], # Households $75,000 to $99,999
            ["B19001_014E",     100000,      124999], # Households $100,000 to $124,999
            ["B19001_015E",     125000,      149999], # Households $125,000 to $149,999
            ["B19001_016E",     150000,      199999], # Households $150,000 to $199,999
            ["B19001_017E",     200000,    HINC_MAX], # Households $200,000 or more
        ],
        "C24010":[ # acs5, C24010. SEX BY OCCUPATION FOR THE CIVILIAN EMPLOYED POPULATION 16 YEARS AND OVER
            ["variable",    "sex",    "occ_cat1",                                         "occ_cat2",                                             "occ_cat3"                                                          ],
            ["C24010_001E", "All",    "All",                                              "All",                                                  "All"                                                               ],
            ["C24010_002E", "Male",   "All",                                              "All",                                                  "All"                                                               ],
            ["C24010_003E", "Male",   "Management, business, science, and arts",          "All",                                                  "All"                                                               ],
            ["C24010_004E", "Male",   "Management, business, science, and arts",          "Management, business, and financial",                  "All"                                                               ],
            ["C24010_005E", "Male",   "Management, business, science, and arts",          "Management, business, and financial",                  "Management"                                                        ],
            ["C24010_006E", "Male",   "Management, business, science, and arts",          "Management, business, and financial",                  "Business and financial operations"                                 ],
            ["C24010_007E", "Male",   "Management, business, science, and arts",          "Computer, engineering, and science",                   "All"                                                               ],
            ["C24010_008E", "Male",   "Management, business, science, and arts",          "Computer, engineering, and science",                   "Computer and mathematical"                                         ],
            ["C24010_009E", "Male",   "Management, business, science, and arts",          "Computer, engineering, and science",                   "Architecture and engineering"                                      ],
            ["C24010_010E", "Male",   "Management, business, science, and arts",          "Computer, engineering, and science",                   "Life, physical, and social science"                                ],
            ["C24010_011E", "Male",   "Management, business, science, and arts",          "Education, legal, community service, arts, and media", "All"                                                               ],
            ["C24010_012E", "Male",   "Management, business, science, and arts",          "Education, legal, community service, arts, and media", "Community and social service"                                      ],
            ["C24010_013E", "Male",   "Management, business, science, and arts",          "Education, legal, community service, arts, and media", "Legal"                                                             ],
            ["C24010_014E", "Male",   "Management, business, science, and arts",          "Education, legal, community service, arts, and media", "Education, training, and library"                                  ],
            ["C24010_015E", "Male",   "Management, business, science, and arts",          "Education, legal, community service, arts, and media", "Arts, design, entertainment, sports, and media"                    ],
            ["C24010_016E", "Male",   "Management, business, science, and arts",          "Healthcare practitioners and technical",               "All"                                                               ],
            ["C24010_017E", "Male",   "Management, business, science, and arts",          "Healthcare practitioners and technical",               "Health diagnosing and treating practitioners and other technical"  ],
            ["C24010_018E", "Male",   "Management, business, science, and arts",          "Healthcare practitioners and technical",               "Health technologists and technicians"                              ],
            ["C24010_019E", "Male",   "Service",                                          "All",                                                  "All"                                                               ],
            ["C24010_020E", "Male",   "Service",                                          "Healthcare support",                                   "All"                                                               ],
            ["C24010_021E", "Male",   "Service",                                          "Protective service",                                   "All"                                                               ],
            ["C24010_022E", "Male",   "Service",                                          "Protective service",                                   "Fire fighting and prevention, and other protective service workers"], # including supervisors
            ["C24010_023E", "Male",   "Service",                                          "Protective service",                                   "Law enforcement workers"                                           ], # including supervisors
            ["C24010_024E", "Male",   "Service",                                          "Food preparation and serving related",                 "All"                                                               ],
            ["C24010_025E", "Male",   "Service",                                          "Building and grounds cleaning and maintenance",        "All"                                                               ],
            ["C24010_026E", "Male",   "Service",                                          "Personal care and service",                            "All"                                                               ],
            ["C24010_027E", "Male",   "Sales and office",                                 "All",                                                  "All"                                                               ],
            ["C24010_028E", "Male",   "Sales and office",                                 "Sales and related",                                    "All"                                                               ],
            ["C24010_029E", "Male",   "Sales and office",                                 "Office and administrative support",                    "All"                                                               ],
            ["C24010_030E", "Male",   "Natural resources, construction, and maintenance", "All",                                                  "All"                                                               ],
            ["C24010_031E", "Male",   "Natural resources, construction, and maintenance", "Farming, fishing, and forestry",                       "All"                                                               ],
            ["C24010_032E", "Male",   "Natural resources, construction, and maintenance", "Construction and extraction",                          "All"                                                               ],
            ["C24010_033E", "Male",   "Natural resources, construction, and maintenance", "Installation, maintenance, and repair",                "All"                                                               ],
            ["C24010_034E", "Male",   "Production, transportation, and material moving",  "All",                                                  "All"                                                               ],
            ["C24010_035E", "Male",   "Production, transportation, and material moving",  "Production",                                           "All"                                                               ],
            ["C24010_036E", "Male",   "Production, transportation, and material moving",  "Transportation",                                       "All"                                                               ],
            ["C24010_037E", "Male",   "Production, transportation, and material moving",  "Material moving",                                      "All"                                                               ],
            ["C24010_038E", "Female", "All",                                              "All",                                                  "All"                                                               ],
            ["C24010_039E", "Female", "Management, business, science, and arts",          "All",                                                  "All"                                                               ],
            ["C24010_040E", "Female", "Management, business, science, and arts",          "Management, business, and financial",                  "All"                                                               ],
            ["C24010_041E", "Female", "Management, business, science, and arts",          "Management, business, and financial",                  "Management"                                                        ],
            ["C24010_042E", "Female", "Management, business, science, and arts",          "Management, business, and financial",                  "Business and financial operations"                                 ],
            ["C24010_043E", "Female", "Management, business, science, and arts",          "Computer, engineering, and science",                   "All"                                                               ],
            ["C24010_044E", "Female", "Management, business, science, and arts",          "Computer, engineering, and science",                   "Computer and mathematical"                                         ],
            ["C24010_045E", "Female", "Management, business, science, and arts",          "Computer, engineering, and science",                   "Architecture and engineering"                                      ],
            ["C24010_046E", "Female", "Management, business, science, and arts",          "Computer, engineering, and science",                   "Life, physical, and social science"                                ],
            ["C24010_047E", "Female", "Management, business, science, and arts",          "Education, legal, community service, arts, and media", "All"                                                               ],
            ["C24010_048E", "Female", "Management, business, science, and arts",          "Education, legal, community service, arts, and media", "Community and social service"                                      ],
            ["C24010_049E", "Female", "Management, business, science, and arts",          "Education, legal, community service, arts, and media", "Legal"                                                             ],
            ["C24010_050E", "Female", "Management, business, science, and arts",          "Education, legal, community service, arts, and media", "Education, training, and library"                                  ],
            ["C24010_051E", "Female", "Management, business, science, and arts",          "Education, legal, community service, arts, and media", " Arts, design, entertainment, sports, and media"                   ],
            ["C24010_052E", "Female", "Management, business, science, and arts",          "Healthcare practitioners and technical",               "All"                                                               ],
            ["C24010_053E", "Female", "Management, business, science, and arts",          "Healthcare practitioners and technical",               "Health diagnosing and treating practitioners and other technical"  ],
            ["C24010_054E", "Female", "Management, business, science, and arts",          "Healthcare practitioners and technical",               "Health technologists and technicians"                              ],
            ["C24010_055E", "Female", "Service",                                          "All",                                                  "All"                                                               ],
            ["C24010_056E", "Female", "Service",                                          "Healthcare support",                                   "All"                                                               ],
            ["C24010_057E", "Female", "Service",                                          "Protective service",                                   "All"                                                               ],
            ["C24010_058E", "Female", "Service",                                          "Protective service",                                   "Fire fighting and prevention, and other protective service"        ], # including supervisors
            ["C24010_059E", "Female", "Service",                                          "Protective service",                                   "Law enforcement workers"                                           ], # including supervisors
            ["C24010_060E", "Female", "Service",                                          "Food preparation and serving related",                 "All"                                                               ],
            ["C24010_061E", "Female", "Service",                                          "Building and grounds cleaning and maintenance",        "All"                                                               ],
            ["C24010_062E", "Female", "Service",                                          "Personal care and service",                            "All"                                                               ],
            ["C24010_063E", "Female", "Sales and office",                                 "All",                                                  "All"                                                               ],
            ["C24010_064E", "Female", "Sales and office",                                 "Sales and related",                                    "All"                                                               ],
            ["C24010_065E", "Female", "Sales and office",                                 "Office and administrative support",                    "All"                                                               ],
            ["C24010_066E", "Female", "Natural resources, construction, and maintenance", "All",                                                  "All"                                                               ],
            ["C24010_067E", "Female", "Natural resources, construction, and maintenance", "Farming, fishing, and forestry",                       "All"                                                               ],
            ["C24010_068E", "Female", "Natural resources, construction, and maintenance", "Construction and extraction",                          "All"                                                               ],
            ["C24010_069E", "Female", "Natural resources, construction, and maintenance", "Installation, maintenance, and repair",                "All"                                                               ],
            ["C24010_070E", "Female", "Production, transportation, and material moving",  "All",                                                  "All"                                                               ],
            ["C24010_071E", "Female", "Production, transportation, and material moving",  "Production",                                           "All"                                                               ],
            ["C24010_072E", "Female", "Production, transportation, and material moving",  "Transportation",                                       "All"                                                               ],
            ["C24010_073E", "Female", "Production, transportation, and material moving",  "Material moving",                                      "All"                                                               ],
        ]
    }

    def __init__(self):
        """
        Read the census api key and instantiate the census object.
        """
        # read the census api key
        with open(CensusFetcher.API_KEY_FILE) as f: self.CENSUS_API_KEY = f.read()

        self.census = census.Census(self.CENSUS_API_KEY)
        logging.debug("census object instantiated")

    def get_census_data(self, dataset, year, table, geo):
        """
        Dataset is one of "sf1" or "ac5"
        Year is a number for the table
        Geo is one of "block", "block group", "tract", or "county"
        """
        if dataset not in ["sf1","acs5"]:
            raise ValueError("get_census_data only supports datasets 'sf1' and 'acs5'")
        if geo not in ["block", "block group", "tract", "county"]:
            raise ValueError("get_census_data received unsupported geo {0}".format(geo))
        if table not in CensusFetcher.CENSUS_DEFINITIONS.keys():
            raise ValueError("get_census_data received unsupported table {0}".format(table))

        table_cache_file = os.path.join(CensusFetcher.LOCAL_CACHE_FOLDER, "{0}_{1}_{2}_{3}.csv".format(dataset,year,table,geo))
        logging.info("Checking for table cache at {0}".format(table_cache_file))

        # lookup table definition
        table_def = CensusFetcher.CENSUS_DEFINITIONS[table]
        # logging.debug(table_def)
        table_cols    = table_def[0]  # e.g. ['variable', 'pers_min', 'pers_max']

        if geo=="block":
            geo_index = ["state","county","tract","block"]
        elif geo=="block group":
            geo_index = ["state","county","tract","block group"]
        elif geo=="tract":
            geo_index = ["state","county","tract"]
        elif geo=="county":
            geo_index = ["state","county"]

        # lookup cache and return, if it exists
        if os.path.exists(table_cache_file):
            logging.info("Reading {0}".format(table_cache_file))
            dtypes_dict = {k:object for k in geo_index}

            # This version doesn't make the index columns into strings
            # full_df_v1 = pandas.read_csv(table_cache_file,
            #                              header=range(len(table_cols)),
            #                              index_col=range(len(geo_index)), dtype=dtypes_dict)

            # we want the index columns as strings
            # https://github.com/pandas-dev/pandas/issues/9435
            full_df      = pandas.read_csv(table_cache_file, dtype=dtypes_dict, skiprows=len(table_cols)).set_index(geo_index)
            full_df_cols = pandas.read_csv(table_cache_file,
                                           header=range(len(table_cols)),
                                           index_col=range(len(geo_index)),nrows=0).columns
            full_df.columns = full_df_cols
            return full_df


        multi_col_def = []            # we'll build this
        full_df       = None          # and this
        for census_col in table_def[1:]:
            # census_col looks like ['H0130001', 1, 10]

            # fetch for one county at a time
            df = pandas.DataFrame()
            for county_code in CensusFetcher.BAY_AREA_COUNTY_FIPS.values():
                geo_dict = {'for':'{0}:*'.format(geo),
                            'in':'state:{0} county:{1}'.format(CensusFetcher.CA_STATE_FIPS, county_code)}

                if dataset == "sf1":
                    county_df = pandas.DataFrame.from_records(self.census.sf1.get(census_col[0], geo_dict, year=year)).set_index(geo_index)
                elif dataset == "acs5":
                    county_df = pandas.DataFrame.from_records(self.census.acs5.get(census_col[0], geo_dict, year=year)).set_index(geo_index)

                df = df.append(county_df)

            # join with existing full_df
            if len(multi_col_def) == 0:
                full_df = df
            else:
                full_df = full_df.merge(df, left_index=True, right_index=True)

            # note column defs
            multi_col_def.append(census_col)

        # now we have the table with multiple columns -- name the columns with decoded names
        full_df.columns = pandas.MultiIndex.from_tuples(multi_col_def, names=table_cols)
        # logging.debug(full_df.head())

        # write it out
        full_df.to_csv(table_cache_file, header=True, index=True)
        logging.info("Wrote {0}".format(table_cache_file))

        return full_df

def census_col_is_in_control(param_dict, control_dict):
    """
    param_dict is from  CENSUS_DEFINITIONS,   e.g. OrderedDict([('pers_min',4), ('pers_max', 4)])
    control_dict is from control definitions, e.g. OrderedDict([('pers_min',4), ('pers_max',10)])

    Checks if this census column should be included in the control.
    Returns True or False.
    """
    # assume true unless kicked out
    for control_name, control_val in control_dict.iteritems():
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
    returns a version of the census table with just the relevant column.
    """
    logging.info("Creating control table for {}".format(control_name))
    logging.debug("\n{}".format(census_table_df.head()))

    # construct a new dataframe to return with same index as census_table_df
    control_df = pandas.DataFrame(index=census_table_df.index, columns=[control_name], data=0)
    # logging.debug control_df.head()

    # logging.debug(census_table_df.columns.names)
    # [u'variable', u'pers_min', u'pers_max']

    # logging.debug(census_table_df.columns.get_level_values(0))
    # Index([u'H0130001', u'H0130002', u'H0130003', u'H0130004', u'H0130005', u'H0130006', u'H0130007', u'H0130008'], dtype='object', name=u'variable')

    # logging.debug(census_table_df.columns.get_level_values(1))
    # Index([u'1', u'1', u'2', u'3', u'4', u'5', u'6', u'7'], dtype='object', name=u'pers_min')

    # logging.debug(census_table_df.columns.get_level_values(2))
    # Index([u'10', u'1', u'2', u'3', u'4', u'5', u'6', u'10'], dtype='object', name=u'pers_max')

    # the control_dict_list is a list of dictionaries -- iterate through them
    prev_sum = 0
    for control_dict in control_dict_list:
        logging.info("  Control definition:")
        for cname,cval in control_dict.iteritems(): logging.info("      {:15} {}".format(cname, cval))

        # find the relevant column, if there is one
        for colnum in range(len(census_table_df.columns.levels[0])):
            param_dict = collections.OrderedDict()
            # level 0 is the Census variable name, e.g. H0130001
            variable_name = census_table_df.columns.get_level_values(0)[colnum]

            for paramnum in range(1, len(census_table_df.columns.names)):
                param = census_table_df.columns.names[paramnum]
                try: # assume this is an int but fall back if it's nominal
                    param_dict[param] = int(census_table_df.columns.get_level_values(paramnum)[colnum])
                except:
                    param_dict[param] = census_table_df.columns.get_level_values(paramnum)[colnum]
            # logging.debug(param_dict)

            # Is this single column sufficient?
            if param_dict == control_dict:
                logging.info("    Found a single matching column: [{}]".format(variable_name))
                for pname,pval in param_dict.iteritems(): logging.info("      {:15} {}".format(pname, pval))

                control_df["temp"] = census_table_df[variable_name]
                control_df[control_name] = census_table_df[variable_name]
                control_df.drop(columns="temp", inplace=True)
                break  # stop iterating through columns

            # Otherwise, if it's in the range, add it in
            if census_col_is_in_control(param_dict, control_dict):
                logging.info("    Adding column [{}]".format(variable_name))
                for pname,pval in param_dict.iteritems(): logging.info("      {:15} {}".format(pname, pval))

                control_df["temp"] = census_table_df[variable_name]
                control_df[control_name] = control_df[control_name] + control_df["temp"]
                control_df.drop(columns="temp", inplace=True)

        # assume each control dict needs to find *something*
        new_sum = control_df[control_name].sum()
        logging.info("  => Total added: {:,}".format(new_sum - prev_sum))
        assert( new_sum > prev_sum)
        prev_sum = new_sum

    return control_df

def match_control_to_geography(control_name, control_table_df, control_geography, census_geography,
                               maz_taz_def_df, temp_controls, full_region, scale_by_temp=False):
    """
    Given a control table in the given census geography, this method will transform the table to the appropriate
    control geography and return it.

    Pass full_region=False if this is a test subset so the control totals don't need to add up to the census table total.
    Pass scale_by_temp=True if scaling isn't required (e.g. the census_geography is smaller than the control_geography)
                            but you want to force scaling anyway because the universe isn't correct.
    """
    if control_geography not in ["MAZ","TAZ","COUNTY","REGION"]:
        raise ValueError("match_control_to_geography passed unsupported control geography {}".format(control_geography))
    if census_geography not in ["block","block group","tract","county"]:
        raise ValueError("match_control_to_geography passed unsupported census geography {}".format(census_geography))

    # to verify we kept the totals
    variable_total = control_table_df[control_name].sum()

    GEO_HIERARCHY = { 'MAZ'   :['block','MAZ','block group','tract','county'],
                      'TAZ'   :['block',      'TAZ',        'tract','county'],
                      'COUNTY':['block',      'block group','tract','county','COUNTY'],
                      'REGION':['block',      'block group','tract','county','REGION']}

    control_geo_index = GEO_HIERARCHY[control_geography].index(control_geography)
    try:
        census_geo_index = GEO_HIERARCHY[control_geography].index(census_geography)
    except:
        census_geo_index = -1

    # consolidate geography columns
    control_table_df.reset_index(drop=False, inplace=True)
    if census_geography=="block":
        control_table_df["GEOID_block"] = control_table_df["state"] + control_table_df["county"] + control_table_df["tract"] + control_table_df["block"]
    elif census_geography=="block group":
        control_table_df["GEOID_block group"] = control_table_df["state"] + control_table_df["county"] + control_table_df["tract"] + control_table_df["block group"]
    elif census_geography=="tract":
        control_table_df["GEOID_tract"] = control_table_df["state"] + control_table_df["county"] + control_table_df["tract"]
    elif ceneus_geography=="county":
        control_table_df["GEOID_county"] = control_table_df["state"] + control_table_df["county"]
    # drop the others
    control_table_df = control_table_df[["GEOID_{}".format(census_geography), control_name]]

    # if this is a temp, don't go further -- we'll use it later
    if control_name.startswith("temp_"):
        logging.info("Total for {} {:,}".format(control_name, control_table_df[control_name].sum()))
        return control_table_df

    # if the census geography is smaller than the target geography, this is a simple aggregation
    if census_geo_index >= 0 and census_geo_index < control_geo_index:
        logging.info("Simple aggregation from {} to {}".format(census_geography, control_geography))

        if scale_by_temp:
            # by convention, numerator then denominator
            scale_name_numer = temp_controls.keys()[-2]
            scale_name_denom = temp_controls.keys()[-1]
            assert(len(temp_controls[scale_name_numer]) == len(control_table_df))
            assert(len(temp_controls[scale_name_denom]) == len(control_table_df))
            logging.info("  Scaling by {}/{}".format(scale_name_numer,scale_name_denom))

            control_table_df = pandas.merge(left=control_table_df, right=temp_controls[scale_name_numer], how="left")
            control_table_df = pandas.merge(left=control_table_df, right=temp_controls[scale_name_denom], how="left")
            control_table_df[control_name] = control_table_df[control_name] * control_table_df[scale_name_numer]/control_table_df[scale_name_denom]
            control_table_df.fillna(0, inplace=True)

            variable_total = variable_total * temp_controls[scale_name_numer][scale_name_numer].sum()/temp_controls[scale_name_denom][scale_name_denom].sum()

        # we really only need these columns - control geography and the census geography
        geo_mapping_df   = maz_taz_def_df[[control_geography, "GEOID_{}".format(census_geography)]].drop_duplicates()
        control_table_df = pandas.merge(left=control_table_df, right=geo_mapping_df, how="left")

        # aggregate now
        final_df         = control_table_df[[control_geography, control_name]].groupby(control_geography).aggregate(numpy.sum)

        # verify the totals didn't change
        if full_region and not scale_by_temp: assert(final_df[control_name].sum() == variable_total)

        logging.info("  => Total for {} {:,}".format(control_name, final_df[control_name].sum()))
        return final_df

    # this is more complicated -- by convention, the first one will be at the block (smaller geo) level
    # and the last one will be at the same level as this one so we'll use to proportion
    # e.g. hh_inc_15_prop = hh_inc_15 / temp_num_hh_bg   (at block group)
    #      then multiply this by the households at the block level to get hh_inc_15 for blocks (these will be floats)
    #      and aggregate to control geo (e.g. TAZ)

    # verify the last one matches our geography
    same_geo_total_name = temp_controls.keys()[-1]
    same_geo_total_df   = temp_controls[same_geo_total_name]
    assert(len(same_geo_total_df) == len(control_table_df))

    proportion_df = pandas.merge(left=control_table_df, right=same_geo_total_df, how="left")
    proportion_var = "{} proportion".format(control_name)
    proportion_df[proportion_var] = proportion_df[control_name] / proportion_df[same_geo_total_name]
    logging.debug("Create proportion {} at {} geography using {}/{}\n{}".format(proportion_var, control_geography,
                  control_name, same_geo_total_name, proportion_df.head()))
    logging.debug("Sums:\n{}".format(proportion_df[[control_name, same_geo_total_name]].sum()))
    logging.debug("Mean:\n{}".format(proportion_df[[proportion_var]].mean()))

    # join this to the maz_taz_definition - it'll be the lowest level
    block_prop_df = pandas.merge(left=maz_taz_def_df, right=proportion_df, how="left")
    # and again to the first temp table
    block_total_name = temp_controls.keys()[0]
    block_total_df   = temp_controls[block_total_name]
    block_prop_df    = pandas.merge(left=block_prop_df, right=block_total_df, how="left")

    # now multiply to get total at block level
    block_prop_df[control_name] = block_prop_df[proportion_var]*block_prop_df[block_total_name]
    logging.debug("Proportion at block level:\n{}".format(block_prop_df.head()))

    # NOW aggregate
    final_df = block_prop_df[[control_geography, control_name]].groupby(control_geography).aggregate(numpy.sum)
    # this won't be exact but hopefully close
    logging.info("Proportionally-derived Total added: {:,}".format(final_df[control_name].sum()))
    return final_df

if __name__ == '__main__':
    pandas.set_option("display.width", 500)
    pandas.set_option("display.float_format", "{:,.2f}".format)

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=USAGE)
    parser.add_argument("model_year", type=int)
    parser.add_argument("--test_PUMA", type=str, help="Pass PUMA to output controls only for geographies relevant to a single PUMA, for testing")
    args = parser.parse_args()

    # for now, we only do 2010
    if args.model_year not in [2010]:
        raise ValueError("Model year {} not supported yet".format(args.model_year))

    LOG_FILE = "create_baseyear_controls_{0}.log".format(args.model_year)

    # create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
    logger.addHandler(ch)
    # file handler
    fh = logging.FileHandler(LOG_FILE, mode='w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
    logger.addHandler(fh)

    CONTROLS = collections.OrderedDict()
    CONTROLS['MAZ'] = collections.OrderedDict([
        ('num_hh'        ,('sf1',2010,'H13','block',[collections.OrderedDict([ ('pers_min',1), ('pers_max',NPER_MAX) ])] )),
        ('hh_size_1'     ,('sf1',2010,'H13','block',[collections.OrderedDict([ ('pers_min',1), ('pers_max',1       ) ])] )),
        ('hh_size_2'     ,('sf1',2010,'H13','block',[collections.OrderedDict([ ('pers_min',2), ('pers_max',2       ) ])] )),
        ('hh_size_3'     ,('sf1',2010,'H13','block',[collections.OrderedDict([ ('pers_min',3), ('pers_max',3       ) ])] )),
        ('hh_size_4_plus',('sf1',2010,'H13','block',[collections.OrderedDict([ ('pers_min',4), ('pers_max',NPER_MAX) ])] )),
        # group quarters -- include non institutional only
        ('gq_num_hh'     ,('sf1',2010,'P43','block',[collections.OrderedDict([ ('inst','Noninst'), ('subcategory','All'     ) ])] )),
        ('gq_type_univ'  ,('sf1',2010,'P43','block',[collections.OrderedDict([ ('inst','Noninst'), ('subcategory','College' ) ])] )),
        ('gq_type_mil'   ,('sf1',2010,'P43','block',[collections.OrderedDict([ ('inst','Noninst'), ('subcategory','Military') ])] )),
        ('gq_type_othnon',('sf1',2010,'P43','block',[collections.OrderedDict([ ('inst','Noninst'), ('subcategory','Other'   ) ])] )),
    ])
    CONTROLS['TAZ'] = collections.OrderedDict([
        ('temp_num_hh_b'   ,('sf1', 2010,'H13',   'block',      [collections.OrderedDict([ ('pers_min',1), ('pers_max',NPER_MAX) ])] )),

        ('temp_num_hhinc'  ,('acs5',2010,'B19001','block group',[collections.OrderedDict([ ('hhinc_min',     0), ('hhinc_max',HINC_MAX) ])] )),
        ('hh_inc_30'       ,('acs5',2010,'B19001','block group',[collections.OrderedDict([ ('hhinc_min',     0), ('hhinc_max',   29999) ])] )),
        ('hh_inc_30_60'    ,('acs5',2010,'B19001','block group',[collections.OrderedDict([ ('hhinc_min', 30000), ('hhinc_max',   59999) ])] )),
        ('hh_inc_60_100'   ,('acs5',2010,'B19001','block group',[collections.OrderedDict([ ('hhinc_min', 60000), ('hhinc_max',   99999) ])] )),
        ('hh_inc_100_plus' ,('acs5',2010,'B19001','block group',[collections.OrderedDict([ ('hhinc_min',100000), ('hhinc_max',HINC_MAX) ])] )),

        ('temp_num_hh_wrks',('acs5',2012,'B08202','tract',      [collections.OrderedDict([ ('workers_min',0), ('workers_max',NWOR_MAX), ('persons_min',0), ('persons_max', NPER_MAX) ])] )),
        ('hh_wrks_0'       ,('acs5',2012,'B08202','tract',      [collections.OrderedDict([ ('workers_min',0), ('workers_max',       0), ('persons_min',0), ('persons_max', NPER_MAX) ])] )),
        ('hh_wrks_1'       ,('acs5',2012,'B08202','tract',      [collections.OrderedDict([ ('workers_min',1), ('workers_max',       1), ('persons_min',0), ('persons_max', NPER_MAX) ])] )),
        ('hh_wrks_2'       ,('acs5',2012,'B08202','tract',      [collections.OrderedDict([ ('workers_min',2), ('workers_max',       2), ('persons_min',0), ('persons_max', NPER_MAX) ])] )),
        ('hh_wrks_3_plus'  ,('acs5',2012,'B08202','tract',      [collections.OrderedDict([ ('workers_min',3), ('workers_max',NWOR_MAX), ('persons_min',0), ('persons_max', NPER_MAX) ])] )),

        # temp tables needed because P12 is All persons but we want only persons in households so we'll force scaling via the scale_by_temp to match_control_to_geography()
        ('temp_num_pers_hh',('sf1', 2010,'P16',   'block',      [collections.OrderedDict([ ('age_min', 0), ('age_max',AGE_MAX) ])] )),                    # numerator
        ('temp_num_pers   ',('sf1', 2010,'P12',   'block',      [collections.OrderedDict([ ('age_min', 0), ('age_max',AGE_MAX), ('sex', 'All') ])] )),    # denominator
        ('pers_age_00_19'  ,('sf1', 2010,'P12',   'block',      [collections.OrderedDict([ ('age_min', 0), ('age_max',     19) ])] )),
        ('pers_age_20_34'  ,('sf1', 2010,'P12',   'block',      [collections.OrderedDict([ ('age_min',20), ('age_max',     34) ])] )),
        ('pers_age_35_64'  ,('sf1', 2010,'P12',   'block',      [collections.OrderedDict([ ('age_min',35), ('age_max',     64) ])] )),
        ('pers_age_65_plus',('sf1', 2010,'P12',   'block',      [collections.OrderedDict([ ('age_min',65), ('age_max',AGE_MAX) ])] )),

        ('temp_num_hh_kids',('sf1', 2010,'PCT16', 'tract',      [collections.OrderedDict([ ('num_kids_min', 0), ('num_kids_max', NKID_MAX), ('family','All'), ('famtype','All') ])] )),
        ('hh_kids_no'      ,('sf1', 2010,'PCT16', 'tract',      [collections.OrderedDict([ ('num_kids_min', 0), ('num_kids_max',        0)])] )),
        ('hh_kids_yes'     ,('sf1', 2010,'PCT16', 'tract',      [collections.OrderedDict([ ('num_kids_min', 1), ('num_kids_max', NKID_MAX)])] )),
    ])
    CONTROLS['COUNTY'] = collections.OrderedDict([
        # this one is more complicated since the categories are nominal
        ('pers_occ_management'  ,('acs5',2012,'C24010', 'tract', [
            collections.OrderedDict([ ('occ_cat1','Management, business, science, and arts'          ), ('occ_cat2','Management, business, and financial'                 ), ('occ_cat3','Management'                        ) ]),
        ] )),
        ('pers_occ_professional',('acs5',2012,'C24010', 'tract', [
            collections.OrderedDict([ ('occ_cat1','Management, business, science, and arts'          ), ('occ_cat2','Management, business, and financial'                 ), ('occ_cat3','Business and financial operations'                               ) ]),
            collections.OrderedDict([ ('occ_cat1','Management, business, science, and arts'          ), ('occ_cat2','Computer, engineering, and science'                  ), ('occ_cat3','Computer and mathematical'                                       ) ]),
            collections.OrderedDict([ ('occ_cat1','Management, business, science, and arts'          ), ('occ_cat2','Computer, engineering, and science'                  ), ('occ_cat3','Architecture and engineering'                                    ) ]),
            collections.OrderedDict([ ('occ_cat1','Management, business, science, and arts'          ), ('occ_cat2','Computer, engineering, and science'                  ), ('occ_cat3','Life, physical, and social science'                              ) ]),
            collections.OrderedDict([ ('occ_cat1','Management, business, science, and arts'          ), ('occ_cat2','Education, legal, community service, arts, and media'), ('occ_cat3','Legal'                                                           ) ]),
            collections.OrderedDict([ ('occ_cat1','Management, business, science, and arts'          ), ('occ_cat2','Education, legal, community service, arts, and media'), ('occ_cat3','Education, training, and library'                                ) ]),
            collections.OrderedDict([ ('occ_cat1','Management, business, science, and arts'          ), ('occ_cat2','Healthcare practitioners and technical'              ), ('occ_cat3','Health diagnosing and treating practitioners and other technical') ]),
            collections.OrderedDict([ ('occ_cat1','Management, business, science, and arts'          ), ('occ_cat2','Healthcare practitioners and technical'              ), ('occ_cat3','Health technologists and technicians'                            ) ]),
        ] )),
        ('pers_occ_services'    ,('acs5',2012,'C24010', 'tract', [
            collections.OrderedDict([ ('occ_cat1','Management, business, science, and arts'          ), ('occ_cat2','Education, legal, community service, arts, and media'), ('occ_cat3','Community and social service'                                      ) ]),
            collections.OrderedDict([ ('occ_cat1','Management, business, science, and arts'          ), ('occ_cat2','Education, legal, community service, arts, and media'), ('occ_cat3','Arts, design, entertainment, sports, and media'                    ) ]),
            collections.OrderedDict([ ('occ_cat1','Service'                                          ), ('occ_cat2','Healthcare support'                                  ), ('occ_cat3','All'                                                               ) ]),
            collections.OrderedDict([ ('occ_cat1','Service'                                          ), ('occ_cat2','Protective service'                                  ), ('occ_cat3','Fire fighting and prevention, and other protective service workers') ]),
            collections.OrderedDict([ ('occ_cat1','Service'                                          ), ('occ_cat2','Protective service'                                  ), ('occ_cat3','Law enforcement workers'                                           ) ]),
            collections.OrderedDict([ ('occ_cat1','Service'                                          ), ('occ_cat2','Personal care and service'                           ), ('occ_cat3','All'                                                               ) ]),
            collections.OrderedDict([ ('occ_cat1','Sales and office'                                 ), ('occ_cat2','Office and administrative support'                   ), ('occ_cat3','All'                                                               ) ]),
        ] )),
        ('pers_occ_retail'      ,('acs5',2012,'C24010', 'tract', [
            collections.OrderedDict([ ('occ_cat1','Service'                                          ), ('occ_cat2','Food preparation and serving related'                ), ('occ_cat3','All') ]),
            collections.OrderedDict([ ('occ_cat1','Sales and office'                                 ), ('occ_cat2','Sales and related'                                   ), ('occ_cat3','All') ]),
        ] )),
        ('pers_occ_manual'      ,('acs5',2012,'C24010', 'tract', [
            collections.OrderedDict([ ('occ_cat1','Service'                                         ), ('occ_cat2','Building and grounds cleaning and maintenance'        ), ('occ_cat3','All') ]),
            collections.OrderedDict([ ('occ_cat1','Natural resources, construction, and maintenance'), ('occ_cat2','Farming, fishing, and forestry'                       ), ('occ_cat3','All') ]),
            collections.OrderedDict([ ('occ_cat1','Natural resources, construction, and maintenance'), ('occ_cat2','Construction and extraction'                          ), ('occ_cat3','All') ]),
            collections.OrderedDict([ ('occ_cat1','Natural resources, construction, and maintenance'), ('occ_cat2','Installation, maintenance, and repair'                ), ('occ_cat3','All') ]),
            collections.OrderedDict([ ('occ_cat1','Production, transportation, and material moving' ), ('occ_cat2','Production'                                           ), ('occ_cat3','All') ]),
            collections.OrderedDict([ ('occ_cat1','Production, transportation, and material moving' ), ('occ_cat2','Transportation'                                       ), ('occ_cat3','All') ]),
            collections.OrderedDict([ ('occ_cat1','Production, transportation, and material moving' ), ('occ_cat2','Material moving'                                      ), ('occ_cat3','All') ]),
        ] )),
        # TODO - these folks are in group quarters so they shouldn't be included
        # Perhaps use acs5 2012 Table B23025. EMPLOYMENT STATUS FOR THE POPULATION 16 YEARS AND OVER - Armed Forces
        # minus the group quarters military
        ('pers_occ_military'    ,('sf1',2010,'P43','block',[collections.OrderedDict([ ('inst','Noninst'), ('subcategory','Military') ])] )),
    ])
    CONTROLS['REGION'] = collections.OrderedDict([
        ('gq_num_hh_region'     ,('sf1',2010,'P43','block',[collections.OrderedDict([ ('inst','Noninst'), ('subcategory','All'     ) ])] )),
    ])

    maz_taz_def_df = pandas.read_csv(MAZ_TAZ_DEF_FILE)
    # we use MAZ, TAZ not maz,taz; use GEOID_BLOCK
    maz_taz_def_df.rename(columns={"maz":"MAZ", "taz":"TAZ"}, inplace=True)
    maz_taz_def_df["GEOID_block"] = "0" + maz_taz_def_df["GEOID10"].astype(str)
    # add county, tract, block group GEOID
    maz_taz_def_df["GEOID_county"     ] = maz_taz_def_df["GEOID_block"].str[:5 ]
    maz_taz_def_df["GEOID_tract"      ] = maz_taz_def_df["GEOID_block"].str[:11]
    maz_taz_def_df["GEOID_block group"] = maz_taz_def_df["GEOID_block"].str[:12]
    maz_taz_def_df.drop("GEOID10", axis="columns", inplace=True)
    # add COUNTY and REGION
    maz_taz_def_df = pandas.merge(left=maz_taz_def_df, right=COUNTY_RECODE, how="left")

    # and PUMA
    taz_puma_dbf   = simpledbf.Dbf5(MAZ_TAZ_PUMA_FILE)
    taz_puma_df    = taz_puma_dbf.to_dataframe()
    # since this is an intersect, there may be multiple PUMAs per taz
    # remedy this by picking the one with the biggest calc_area -- the sort will put that one last
    taz_puma_df    = taz_puma_df[["taz","PUMA","calc_area"]].sort_values(by=["taz","calc_area"])
    taz_puma_df    = taz_puma_df.drop_duplicates(subset=["taz"], keep="last")
    taz_puma_df.rename(columns={"taz":"TAZ"}, inplace=True)
    maz_taz_def_df = pandas.merge(left=maz_taz_def_df, right=taz_puma_df[["TAZ", "PUMA"]], how="left")

    if args.test_PUMA:
        logging.info("test_PUMA {} passed -- ZEROING OUT MAZ, TAZ, COUNTY for other PUMAs".format(args.test_PUMA))
        maz_taz_def_df.loc[ maz_taz_def_df.PUMA != args.test_PUMA, "MAZ"   ] = 0
        maz_taz_def_df.loc[ maz_taz_def_df.PUMA != args.test_PUMA, "TAZ"   ] = 0
        maz_taz_def_df.loc[ maz_taz_def_df.PUMA != args.test_PUMA, "COUNTY"] = 0

    cf = CensusFetcher()

    final_control_dfs = {} # control geography => dataframe
    for control_geo, control_dict in CONTROLS.iteritems():
        temp_controls = collections.OrderedDict()
        for control_name, control_def in control_dict.iteritems():
            census_table_df = cf.get_census_data(dataset=control_def[0],
                                                 year   =control_def[1],
                                                 table  =control_def[2],
                                                 geo    =control_def[3])

            control_table_df = create_control_table(control_name, control_def[4], control_def[2], census_table_df)

            final_df = match_control_to_geography(control_name, control_table_df, control_geo, control_def[3],
                                                  maz_taz_def_df, temp_controls, full_region=(args.test_PUMA==None),
                                                  scale_by_temp=True if control_name.startswith("pers_age") else False)

            # the temp control tables are special -- they're intermediate for matching
            if control_name.startswith("temp_"):
                temp_controls[control_name] = final_df
                continue

            # save it
            if control_geo not in final_control_dfs:
                final_control_dfs[control_geo] = final_df
            else:
                final_control_dfs[control_geo] = pandas.merge(left       =final_control_dfs[control_geo],
                                                              right      =final_df,
                                                              how        ="left",
                                                              left_index =True,
                                                              right_index=True)

        # Write the controls file for this geography
        logging.info("Preparing final controls files")
        out_df = final_control_dfs[control_geo]  # easier to reference
        out_df.reset_index(drop=False, inplace=True)

        # for county, add readable county name
        if control_geo=="COUNTY":
            out_df = pandas.merge(left=COUNTY_RECODE[["COUNTY","county_name"]], right=out_df, how="right")

        # First, log and drop control=0 if necessary
        if len(out_df.loc[ out_df[control_geo]==0]) > 0:
            logging.info("Dropping {}=0\n{}".format(control_geo, out_df.loc[ out_df[control_geo]==0,:].T.squeeze()))
            out_df = out_df.loc[out_df[control_geo]>0, :]

        # Controls start with gq_ are group quarters
        hh_control_names = []
        gq_control_names = []
        for control_name in list(out_df.columns):
            if control_name == control_geo: continue
            if control_name.startswith("gq_"):
                gq_control_names.append(control_name)
            else:
                hh_control_names.append(control_name)

        if len(hh_control_names) > 0:
            hh_control_df   = out_df[[control_geo] + hh_control_names]
            hh_control_file = os.path.join("households", "data", "{}_{}_controls.csv".format(args.model_year, control_geo))
            hh_control_df.to_csv(hh_control_file, index=False, float_format="%.2f")
            logging.info("Wrote control file {}".format(hh_control_file))

        if len(gq_control_names) > 0:
            gq_control_df   = out_df[[control_geo] + gq_control_names]
            gq_control_file = os.path.join("group_quarters", "data", "{}_{}_controls.csv".format(args.model_year, control_geo))
            gq_control_df.to_csv(gq_control_file, index=False, float_format="%.2f")
            logging.info("Wrote control file {}".format(gq_control_file))


    # finally, save the cross walk file
    crosswalk_df = maz_taz_def_df.loc[ maz_taz_def_df["MAZ"] > 0] # drop MAZ=0

    crosswalk_df = crosswalk_df[["MAZ","TAZ","PUMA","COUNTY","county_name","REGION"]].drop_duplicates()
    crosswalk_df.sort_values(by="MAZ", inplace=True)
    for hh_gq in ["households","group_quarters"]:
        crosswalk_file = os.path.join(hh_gq, "data", "geo_cross_walk.csv")
        crosswalk_df.to_csv(crosswalk_file, index=False)
        logging.info("Wrote geographic cross walk file {}".format(crosswalk_file))
