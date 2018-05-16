USAGE="""
Create baseyear controls for MTC Bay Area populationsim.

"""

import os, sys
import census, us
import pandas

AGE_MAX = 130 # max person age
NKID_MAX = 10 # max number of kids
NPER_MAX = 10 # max number of persons
NWOR_MAX = 10 # max number of workers
HINC_MAX = 2000000

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

    BAY_AREA_COUNTY_FIPS  = {
        "Alameda"      :"01",
        "Contra Costa" :"13",
        "Marin"        :"41",
        "Napa"         :"55",
        "San Francisco":"75",
        "San Mateo"    :"81",
        "Santa Clara"  :"85",
        "Solano"       :"95",
        "Sonoma"       :"97"
    }

    # https://api.census.gov/data/2011/acs/acs5/variables.html
    # https://api.census.gov/data/2012/acs5/variables.html
    # https://api.census.gov/data/2010/sf1/variables.html

    CENSUS_DEFINITIONS = {
        "H13":[  # sf1, H13. Household Size [8]
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
        "P12":[  # sf1, P12. Sex By Age [49]
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
            ["variable",   "min_workers","max_workers","min_persons","max_persons"],
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
            ["variable",   "min_hhinc", "max_hhinc"],
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
        "C2401":[ # acs5, C2401. SEX BY OCCUPATION FOR THE CIVILIAN EMPLOYED POPULATION 16 YEARS AND OVER
            ["variable",    "sex",    "occ_cat1",                                          "occ_cat2",                                             "occ_cat3"                                                        ],
            ["C24010_001E", "All",    "All",                                              "All",                                                  "All"                                                             ],
            ["C24010_002E", "Male",   "All",                                              "All",                                                  "All"                                                             ],
            ["C24010_003E", "Male",   "Management, business, science, and arts",          "All",                                                  "All"                                                             ],
            ["C24010_004E", "Male",   "Management, business, science, and arts",          "Management, business, and financial",                  "All"                                                             ],
            ["C24010_005E", "Male",   "Management, business, science, and arts",          "Management, business, and financial",                  "Management"                                                      ],
            ["C24010_006E", "Male",   "Management, business, science, and arts",          "Management, business, and financial",                  "Business and financial operations"                               ],
            ["C24010_007E", "Male",   "Management, business, science, and arts",          "Computer, engineering, and science",                   "All"                                                             ],
            ["C24010_008E", "Male",   "Management, business, science, and arts",          "Computer, engineering, and science",                   "Computer and mathematical"                                       ],
            ["C24010_009E", "Male",   "Management, business, science, and arts",          "Computer, engineering, and science",                   "Architecture and engineering"                                    ],
            ["C24010_010E", "Male",   "Management, business, science, and arts",          "Computer, engineering, and science",                   "Life, physical, and social science"                              ],
            ["C24010_011E", "Male",   "Management, business, science, and arts",          "Education, legal, community service, arts, and media", "All"                                                             ],
            ["C24010_012E", "Male",   "Management, business, science, and arts",          "Education, legal, community service, arts, and media", "Community and social service"                                    ],
            ["C24010_013E", "Male",   "Management, business, science, and arts",          "Education, legal, community service, arts, and media", "Legal"                                                           ],
            ["C24010_014E", "Male",   "Management, business, science, and arts",          "Education, legal, community service, arts, and media", "Education, training, and library"                                ],
            ["C24010_015E", "Male",   "Management, business, science, and arts",          "Education, legal, community service, arts, and media", " Arts, design, entertainment, sports, and media"                 ],
            ["C24010_016E", "Male",   "Management, business, science, and arts",          "Healthcare practitioners and technical",               "All"                                                             ],
            ["C24010_017E", "Male",   "Management, business, science, and arts",          "Healthcare practitioners and technical",               "Health diagnosing and treating practitioners and other technical"],
            ["C24010_018E", "Male",   "Management, business, science, and arts",          "Healthcare practitioners and technical",               "Health technologists and technicians"                            ],
            ["C24010_019E", "Male",   "Service",                                          "All",                                                  "All"                                                             ],
            ["C24010_020E", "Male",   "Service",                                          "Healthcare support",                                   "All"                                                             ],
            ["C24010_021E", "Male",   "Service",                                          "Protective service",                                   "All"                                                             ],
            ["C24010_022E", "Male",   "Service",                                          "Protective service",                                   "Fire fighting and prevention, and other protective service"      ], # including supervisors
            ["C24010_023E", "Male",   "Service",                                          "Protective service",                                   "Law enforcement workers"                                         ], # including supervisors
            ["C24010_024E", "Male",   "Service",                                          "Food preparation and serving related",                 "All"                                                             ],
            ["C24010_025E", "Male",   "Service",                                          "Building and grounds cleaning and maintenance",        "All"                                                             ],
            ["C24010_026E", "Male",   "Service",                                          "Personal care and service",                            "All"                                                             ],
            ["C24010_027E", "Male",   "Sales and office",                                 "All",                                                  "All"                                                             ],
            ["C24010_028E", "Male",   "Sales and office",                                 "Sales and related",                                    "All"                                                             ],
            ["C24010_029E", "Male",   "Sales and office",                                 "Office and administrative support",                    "All"                                                             ],
            ["C24010_030E", "Male",   "Natural resources, construction, and maintenance", "All",                                                  "All"                                                             ],
            ["C24010_031E", "Male",   "Natural resources, construction, and maintenance", "Farming, fishing, and forestry",                       "All"                                                             ],
            ["C24010_032E", "Male",   "Natural resources, construction, and maintenance", "Construction and extraction",                          "All"                                                             ],
            ["C24010_033E", "Male",   "Natural resources, construction, and maintenance", "Installation, maintenance, and repair",                "All"                                                             ],
            ["C24010_034E", "Male",   "Production, transportation, and material moving",  "All",                                                  "All"                                                             ],
            ["C24010_035E", "Male",   "Production, transportation, and material moving",  "Production",                                           "All"                                                             ],
            ["C24010_036E", "Male",   "Production, transportation, and material moving",  "Transportation",                                       "All"                                                             ],
            ["C24010_037E", "Male",   "Production, transportation, and material moving",  "Material moving",                                      "All"                                                             ],
            ["C24010_038E", "Female", "All",                                              "All",                                                  "All"                                                             ],
            ["C24010_039E", "Female", "Management, business, science, and arts",          "All",                                                  "All"                                                             ],
            ["C24010_040E", "Female", "Management, business, science, and arts",          "Management, business, and financial",                  "All"                                                             ],
            ["C24010_041E", "Female", "Management, business, science, and arts",          "Management, business, and financial",                  "Management"                                                      ],
            ["C24010_042E", "Female", "Management, business, science, and arts",          "Management, business, and financial",                  "Business and financial operations"                               ],
            ["C24010_043E", "Female", "Management, business, science, and arts",          "Computer, engineering, and science",                   "All"                                                             ],
            ["C24010_044E", "Female", "Management, business, science, and arts",          "Computer, engineering, and science",                   "Computer and mathematical"                                       ],
            ["C24010_045E", "Female", "Management, business, science, and arts",          "Computer, engineering, and science",                   "Architecture and engineering"                                    ],
            ["C24010_046E", "Female", "Management, business, science, and arts",          "Computer, engineering, and science",                   "Life, physical, and social science"                              ],
            ["C24010_047E", "Female", "Management, business, science, and arts",          "Education, legal, community service, arts, and media", "All"                                                             ],
            ["C24010_048E", "Female", "Management, business, science, and arts",          "Education, legal, community service, arts, and media", "Community and social service"                                    ],
            ["C24010_049E", "Female", "Management, business, science, and arts",          "Education, legal, community service, arts, and media", "Legal"                                                           ],
            ["C24010_050E", "Female", "Management, business, science, and arts",          "Education, legal, community service, arts, and media", "Education, training, and library"                                ],
            ["C24010_051E", "Female", "Management, business, science, and arts",          "Education, legal, community service, arts, and media", " Arts, design, entertainment, sports, and media"                 ],
            ["C24010_052E", "Female", "Management, business, science, and arts",          "Healthcare practitioners and technical",               "All"                                                             ],
            ["C24010_053E", "Female", "Management, business, science, and arts",          "Healthcare practitioners and technical",               "Health diagnosing and treating practitioners and other technical"],
            ["C24010_054E", "Female", "Management, business, science, and arts",          "Healthcare practitioners and technical",               "Health technologists and technicians"                            ],
            ["C24010_055E", "Female", "Service",                                          "All",                                                  "All"                                                             ],
            ["C24010_056E", "Female", "Service",                                          "Healthcare support",                                   "All"                                                             ],
            ["C24010_057E", "Female", "Service",                                          "Protective service",                                   "All"                                                             ],
            ["C24010_058E", "Female", "Service",                                          "Protective service",                                   "Fire fighting and prevention, and other protective service"      ], # including supervisors
            ["C24010_059E", "Female", "Service",                                          "Protective service",                                   "Law enforcement workers"                                         ], # including supervisors
            ["C24010_060E", "Female", "Service",                                          "Food preparation and serving related",                 "All"                                                             ],
            ["C24010_061E", "Female", "Service",                                          "Building and grounds cleaning and maintenance",        "All"                                                             ],
            ["C24010_062E", "Female", "Service",                                          "Personal care and service",                            "All"                                                             ],
            ["C24010_063E", "Female", "Sales and office",                                 "All",                                                  "All"                                                             ],
            ["C24010_064E", "Female", "Sales and office",                                 "Sales and related",                                    "All"                                                             ],
            ["C24010_065E", "Female", "Sales and office",                                 "Office and administrative support",                    "All"                                                             ],
            ["C24010_066E", "Female", "Natural resources, construction, and maintenance", "All",                                                  "All"                                                             ],
            ["C24010_067E", "Female", "Natural resources, construction, and maintenance", "Farming, fishing, and forestry",                       "All"                                                             ],
            ["C24010_068E", "Female", "Natural resources, construction, and maintenance", "Construction and extraction",                          "All"                                                             ],
            ["C24010_069E", "Female", "Natural resources, construction, and maintenance", "Installation, maintenance, and repair",                "All"                                                             ],
            ["C24010_070E", "Female", "Production, transportation, and material moving",  "All",                                                  "All"                                                             ],
            ["C24010_071E", "Female", "Production, transportation, and material moving",  "Production",                                           "All"                                                             ],
            ["C24010_072E", "Female", "Production, transportation, and material moving",  "Transportation",                                       "All"                                                             ],
            ["C24010_073E", "Female", "Production, transportation, and material moving",  "Material moving",                                      "All"                                                             ],
        ]
    }

    def __init__(self):
        """
        Read the census api key and instantiate the census object.
        """
        # read the census api key
        with open(CensusFetcher.API_KEY_FILE) as f: self.CENSUS_API_KEY = f.read()

        self.census = census.Census(self.CENSUS_API_KEY)
        print("census object instantiated")

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
        print("Checking for table cache at {0}".format(table_cache_file))

        # lookup table definition
        table_def = CensusFetcher.CENSUS_DEFINITIONS[table]
        print(table_def)
        table_cols    = table_def[0]  # e.g. ['variable', 'pers_min', 'pers_max']

        if geo=="block":
            geo_index = ["block","tract","county","state"]
        elif geo=="block group":
            geo_index = ["block group","tract","county","state"]
        elif geo=="tract":
            geo_index = ["tract","county","state"]
        elif geo=="county":
            geo_index = ["county","state"]

        # lookup cache and return, if it exists
        if os.path.exists(table_cache_file):
            print("Reading {0}".format(table_cache_file))

            full_df = pandas.read_csv(table_cache_file,
                                      header=range(len(table_cols)),
                                      index_col=range(len(geo_index)))
            print(full_df.head())
            return full_df


        multi_col_def = []            # we'll build this
        full_df       = None          # and this
        for census_col in table_def[1:]:
            # census_col looks like ['H0130001', 1, 10]

            # fetch for one county at a time
            df = pandas.DataFrame()
            for county_code in sorted(CensusFetcher.BAY_AREA_COUNTY_FIPS.values()):
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
        print(full_df.head())
        print(multi_col_def)
        print(table_cols[1:])
        full_df.columns = pandas.MultiIndex.from_tuples(multi_col_def, names=table_cols)
        print(full_df.head())

        # write it out
        full_df.to_csv(table_cache_file, header=True, index=True)
        print("Wrote {0}".format(table_cache_file))

        return full_df

if __name__ == '__main__':

    cf = CensusFetcher()

    HH_CONTROLS = {
        "MAZ":{
            "num_hh" :("sf1",2010,"H13","block"),
            "hh_size":("sf1",2010,"H13","block"),
        },
        "TAZ":{
            "hh_inc"  :("acs5",2010,"B19001","block group"),
            "hh_wrks" :("acs5",2012,"B08202","tract"),
            "pers_age":("sf1", 2010,"P12",   "block"),
            "hh_kids" :("sf1", 2010,"PCT16", "tract"),
        },
        "COUNTY":{
            "pers_occ":("acs5",2012,"C2401", "tract")
        }
    }
    GQ_CONTROLS = {
        "MAZ":{
            "num_hh":("sf1",2010,"P43","block"),
        }
    }

    for control_geo, control_dict in HH_CONTROLS.iteritems():
        for control_type, control_def in control_dict.iteritems():
            cf.get_census_data(dataset=control_def[0],
                               year   =control_def[1],
                               table  =control_def[2],
                               geo    =control_def[3])

    for control_geo, control_dict in GQ_CONTROLS.iteritems():
        for control_type, control_def in control_dict.iteritems():
            cf.get_census_data(dataset=control_def[0],
                               year   =control_def[1],
                               table  =control_def[2],
                               geo    =control_def[3])


