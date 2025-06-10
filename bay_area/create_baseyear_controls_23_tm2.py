USAGE="""
Create baseyear controls for MTC Bay Area populationsim.
THIS IS ALL BEING RE-WRITTEN TO HANDLE THE NEW 2020 CENSUS GEOGRAPHIES
THE MODEL GEOGRAPHIES WILL NO LONGER NEST, AND WE HAVE TO HANDLE THE MANY TO MANY MATCH


This script does the following:

1) Downloads the relevant Census tables to a local cache specified by CensusFetcher.LOCAL_CACHE_FOLDER,
   one table per file in CSV format.  These files are the raw tables at a census geography appropriate
   for the control geographies in this script, although the column headers have additional variables
   that are more descriptive of what the columns mean.

   To re-download the data using the Census API, remove the cache file.

2) It then combines the columns in the Census tables to match the control definitions in the
   CONTROLS structure in the script.

3) Finally, it transforms the control tables from the Census geographies to the desired control
   geography using the MAZ_TAZ_DEF_FILE. The Census geographies and model geographies are many to many,
   so we have to handle the percent of each census geography that falls into each model geography and
   vice versa.



4) Creates a simple file, output_[model_year]/maz_data_hh_pop.csv with 3 columns:
   MAZ,hh,tot_pop for use in the maz_data.csv that will consistent with these controls, where
   these "hh" include the 1-person group quarters households and the tot_pop includes both household
   and group quarter persons.

5) It joins the MAZs and TAZs to the 2020 PUMAs (used in the 2007-2011 PUMS, which is
   used by create_seed_population.py) and saves these crosswalks as well.

   Outputs: households    /data/[model_year]_[maz,taz,county]_controls.csv
            households    /data/geo_cross_walk.csv
            group_quarters/data/[model_year]_maz_controls.csv
            group_quarters/data/geo_cross_walk.csv

            output_[model_year]/maz_data_hh_pop.csv

            create_baseyear_controls_[model_year].log
"""

import argparse, collections, logging, os, sys
import census #, us
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
    API_KEY_FILE = "M:\\Data\\Census\\API\\new_key\\api-key.txt"

    # Store cache of census tables here
    LOCAL_CACHE_FOLDER = "M:\\Data\\Census\\NewCachedTablesForPopulationSimControls"

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
        Dataset is one of "dec or "acs5"
        Year is a number for the table
        Geo is one of "block", "block group", "tract", "county subdivision" or "county"
        """

        if dataset not in ["dec", "acs5"]:
            raise ValueError(f"get_census_data only supports datasets 'dec' and 'acs5'")
        if geo not in ["block", "block group", "tract", "county subdivision", "county"]:
            raise ValueError(f"get_census_data received unsupported geo {geo}")
        if table not in CensusFetcher.CENSUS_DEFINITIONS:
            raise ValueError(f"get_census_data received unsupported table {table}")

        # Build the cache‐filename:
        table_cache_file = os.path.join(
            CensusFetcher.LOCAL_CACHE_FOLDER,
            f"{dataset}_{year}_{table}_{geo}.csv"
        )
        logging.info(f"Checking for table cache at {table_cache_file}")

        # The first row of the CENSUS_DEFINITIONS for this table is the header description
        table_def  = CensusFetcher.CENSUS_DEFINITIONS[table]
        table_cols = table_def[0]  # e.g. ['variable','pers_min','pers_max']

        # Decide which fields form the index, based on geo
        if geo == "block":
            geo_index = ["state", "county", "tract", "block"]
        elif geo == "block group":
            geo_index = ["state", "county", "tract", "block group"]
        elif geo == "tract":
            geo_index = ["state", "county", "tract"]
        elif geo == "county subdivision":
            geo_index = ["state", "county", "county subdivision"]
        elif geo == "county":
            geo_index = ["state", "county"]

        # If the cached CSV exists, read it in two steps:
        if os.path.exists(table_cache_file):
            logging.info(f"Reading {table_cache_file}")

            # We have 3 levels of column‐header (table_cols) + 1 geo‐row
            header_rows = len(table_cols) + 1   # = 4

            # STEP 1: read all 4 header‐rows to get the full list of columns
            full_header = pandas.read_csv(
                table_cache_file,
                header=list(range(header_rows)),  # [0,1,2,3]
                nrows=0
            )
            all_cols = full_header.columns   # e.g. ['state','county','tract','block','H013001',…,'H013008']

            # STEP 2: read the rest of the file as pure data
            raw_df = pandas.read_csv(
                table_cache_file,
                dtype={col: object for col in geo_index},
                skiprows=header_rows,  # now skips 4 lines, not 3
                header=None
            )

            # split into geographic index vs the census columns
            geo_part  = raw_df.iloc[:, :len(geo_index)].astype(str)
            data_part = raw_df.iloc[:, len(geo_index):]

            # pull out just the 8 census columns
            data_cols = all_cols[len(geo_index):]
            if data_part.shape[1] != len(data_cols):
                raise ValueError(
                    f"Cached CSV has {data_part.shape[1]} data columns, "
                    f"but expected {len(data_cols)} (from header)."
                )
            data_part.columns = data_cols

            # set the index and return
            data_part.index = pandas.MultiIndex.from_frame(geo_part)
            return data_part


        #
        # ----------------------------------------------------------
        # If no cache exists, fetch from the Census API & write cache
        # ----------------------------------------------------------
        #
        multi_col_def = []
        full_df       = None

        # If doing county‐level, fetch just once; else loop county by county
        county_codes = CensusFetcher.BAY_AREA_COUNTY_FIPS.values()
        if geo == "county":
            county_codes = ["do_once"]

        for census_col in table_def[1:]:
            # census_col looks like ['H0130001', pers_min, pers_max, …]
            df_list = []

            for county_code in county_codes:
                if geo == "county":
                    geo_dict = {
                        'for': f"{geo}:*",
                        'in' : f"state:{CensusFetcher.CA_STATE_FIPS}"
                    }
                else:
                    geo_dict = {
                        'for': f"{geo}:*",
                        'in' : f"state:{CensusFetcher.CA_STATE_FIPS} county:{county_code}"
                    }

                if dataset == "sf1":
                    county_df = pandas.DataFrame.from_records(
                        self.census.sf1.get(census_col[0], geo_dict, year=year)
                    ).set_index(geo_index)
                else:  # dataset == "acs5"
                    county_df = pandas.DataFrame.from_records(
                        self.census.acs5.get(census_col[0], geo_dict, year=year)
                    ).set_index(geo_index)

                county_df = county_df.astype(float)
                df_list.append(county_df)

            df = pandas.concat(df_list, axis=0)

            if full_df is None:
                full_df = df
            else:
                full_df = full_df.merge(df, left_index=True, right_index=True)

            multi_col_def.append(census_col)

        # If fetched at county level, keep only the Bay Area counties
        if geo == "county":
            county_tuples = [
                (CensusFetcher.CA_STATE_FIPS, x)
                for x in CensusFetcher.BAY_AREA_COUNTY_FIPS.values()
            ]
            full_df = full_df.loc[county_tuples]

        # Assign the MultiIndex column names
        full_df.columns = pandas.MultiIndex.from_tuples(
            multi_col_def,
            names=table_cols
        )

        # Write the CSV out so next time we can read it
        os.makedirs(os.path.dirname(table_cache_file), exist_ok=True)
        full_df.to_csv(table_cache_file, header=True, index=True)
        logging.info(f"Wrote {table_cache_file}")
        return full_df




def add_aggregate_geography_colums(table_df):
    """
    Given a table with column GEOID_block, creates columns for GEOID_[county,tract,block group]
    """
    if "GEOID_block" in table_df.columns:
        table_df["GEOID_county"     ] = table_df["GEOID_block"].str[:5 ]
        table_df["GEOID_tract"      ] = table_df["GEOID_block"].str[:11]
        table_df["GEOID_block group"] = table_df["GEOID_block"].str[:12]

def census_col_is_in_control(param_dict, control_dict):
    """
    param_dict is from  CENSUS_DEFINITIONS,   e.g. OrderedDict([('pers_min',4), ('pers_max', 4)])
    control_dict is from control definitions, e.g. OrderedDict([('pers_min',4), ('pers_max',10)])

    Checks if this census column should be included in the control.
    Returns True or False.
    """
    # assume true unless kicked out
    for control_name, control_val in control_dict.items():
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

        # if there's only one column and no attributes are expected then we're done
        if len(control_dict) == 0 and len(census_table_df.columns.values) == 1:
            variable_name = census_table_df.columns.values[0]
            logging.info("No attributes specified; single column identified: {}".format(variable_name))
            control_df[control_name] = census_table_df[variable_name]

        else:
            logging.info("  Control definition:")
            for cname,cval in control_dict.items(): logging.info("      {:15} {}".format(cname, cval))

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
                    for pname,pval in param_dict.items(): logging.info("      {:15} {}".format(pname, pval))

                    control_df["temp"] = census_table_df[variable_name]
                    control_df[control_name] = census_table_df[variable_name]
                    control_df.drop(columns="temp", inplace=True)
                    break  # stop iterating through columns

                # Otherwise, if it's in the range, add it in
                if census_col_is_in_control(param_dict, control_dict):
                    logging.info("    Adding column [{}]".format(variable_name))
                    for pname,pval in param_dict.items(): logging.info("      {:15} {}".format(pname, pval))

                    control_df["temp"] = census_table_df[variable_name]
                    control_df[control_name] = control_df[control_name] + control_df["temp"]
                    control_df.drop(columns="temp", inplace=True)

        # assume each control dict needs to find *something*
        new_sum = control_df[control_name].sum()
        logging.info("  => Total added: {:,}".format(new_sum - prev_sum))
        assert( new_sum > prev_sum)
        prev_sum = new_sum

    return control_df


"""
IDEA OF WHAT WE HAVE TO DO
import pandas as pd

def match_control_to_geography_many_to_many(control_name: str,
                                            control_df: pd.DataFrame,
                                            lookup_df: pd.DataFrame,
                                            source_geo_col: str,
                                            target_geo_col: str,
                                            pct_source_in_target_col: str,
                                            pct_target_in_source_col: str,
                                            scale_numerator: str = None,
                                            scale_denominator: str = None,
                                            subtract_table: str = None,
                                            full_region: bool = True
                                           ) -> pd.DataFrame:
  
    Apportion 'control_name' from source geographies to target geographies using a many-to-many lookup.

    Parameters
    ----------
    control_name : str
        Column in control_df containing the values to apportion.
    control_df : pd.DataFrame
        DataFrame with one row per source geography, indexed or containing `source_geo_col`.
    lookup_df : pd.DataFrame
        DataFrame with columns [source_geo_col, target_geo_col,
        pct_source_in_target_col, pct_target_in_source_col].
        Each row represents one source–target overlap.
    source_geo_col : str
        Name of the geography column in control_df and lookup_df (e.g. 'GEOID20').
    target_geo_col : str
        Name of the target geography column in lookup_df (e.g. 'MAZ_ID').
    pct_source_in_target_col : str
        In lookup_df, the fraction of each source unit falling in that target.
    pct_target_in_source_col : str
        In lookup_df, the fraction of each target unit covered by that source.
    scale_numerator, scale_denominator, subtract_table : str, optional
        Names of “temp” tables in control_df/lookup_df to scale or subtract. 
        (If you need a complex scaling step, merge them similarly before weighting.)
    full_region : bool
        If True, assert that the total after apportionment matches the original sum.

    Returns
    -------
    pd.DataFrame
        DataFrame indexed by target_geo_col with a column [control_name]
        giving the apportioned totals.


    # 1) Merge control totals onto the lookup
    df = lookup_df.merge(
        control_df[[source_geo_col, control_name]],
        how="left", left_on=source_geo_col, right_on=source_geo_col
    )

    # 2) Optionally apply any scaling or subtraction here, if needed:
    #    e.g. df[control_name] *= df[scale_numerator] / df[scale_denominator]
    #    or df[control_name] -= df[subtract_table]

    # 3) Weight by the fraction of the source within each target
    df['weighted_value'] = df[control_name] * df[pct_source_in_target_col]

    # 4) Aggregate up to the target geography
    result = (
        df
        .groupby(target_geo_col)['weighted_value']
        .sum()
        .reset_index()
        .rename(columns={'weighted_value': control_name})
    )

    # 5) (Optional) Check that totals roughly match
    orig_sum = control_df[control_name].sum()
    new_sum  = result[control_name].sum()
    if full_region and not pd.isclose(orig_sum, new_sum, atol=1e-6):
        raise ValueError(
            f"Apportioned total {new_sum:.2f} "
            f"does not match original {orig_sum:.2f}"
        )

    return result

"""

def match_control_to_geography(control_name, control_table_df, control_geography, census_geography,
                               maz_taz_def_df, temp_controls, full_region,
                               scale_numerator, scale_denominator, subtract_table):
    """
    THIS NEEDS TO BE COMPLETELY UPDATED TO USE MANY TO MANY MERGES
    Given a control table in the given census geography, this method will transform the table to the appropriate
    control geography and return it.

    Pass full_region=False if this is a test subset so the control totals don't need to add up to the census table total.
    Pass scale_numerator and scale_denominator to scale numbers by scale_numerator/scale_denominator, where those are temp tables.
    Or pass subtract_table to subtract out a temp table.
    """
    if control_geography not in ["MAZ","TAZ","COUNTY","REGION"]:
        raise ValueError("match_control_to_geography passed unsupported control geography {}".format(control_geography))
    if census_geography not in ["block","block group","tract","county subdivision","county"]:
        raise ValueError("match_control_to_geography passed unsupported census geography {}".format(census_geography))

    # to verify we kept the totals
    variable_total = control_table_df[control_name].sum()
    logger.debug("Variable_total: {:,}".format(variable_total))

    GEO_HIERARCHY = { 'MAZ'   :['block','MAZ','block group','tract','county subdivision','county'],
                      'TAZ'   :['block',      'TAZ',        'tract','county subdivision','county'],
                      'COUNTY':['block',      'block group','tract','county subdivision','county','COUNTY'],
                      'REGION':['block',      'block group','tract','county subdivision','county','REGION']}

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
    elif census_geography=="county":
        control_table_df["GEOID_county"] = control_table_df["state"] + control_table_df["county"]
    # drop the others
    control_table_df = control_table_df[["GEOID_{}".format(census_geography), control_name]]

    # if this is a temp, don't go further -- we'll use it later
    if control_name.startswith("temp_"):
        logging.info("Temporary Total for {} ({} rows) {:,}".format(control_name, len(control_table_df), control_table_df[control_name].sum()))
        logging.debug("head:\n{}".format(control_table_df.head()))

        if scale_numerator or scale_denominator:
            scale_numerator_geometry   = temp_controls[scale_numerator].columns[0]
            scale_denominator_geometry = temp_controls[scale_denominator].columns[0]
            # join to the one that's the same length
            logging.debug("Temp with numerator {} denominator {}".format(scale_numerator, scale_denominator))
            logging.debug("  {} has geometry {} and  length {}".format(scale_numerator,
                          scale_numerator_geometry, len(temp_controls[scale_numerator])))
            logging.debug("  Head:\n{}".format(temp_controls[scale_numerator].head()))
            logging.debug("  {} has geometry {} and length {}".format(scale_denominator,
                          scale_denominator_geometry, len(temp_controls[scale_denominator])))
            logging.debug("  Head:\n{}".format(temp_controls[scale_denominator].head()))

            # one should match -- try denom
            if len(temp_controls[scale_denominator]) == len(control_table_df):
                control_table_df = pandas.merge(left=control_table_df, right=temp_controls[scale_denominator], how="left")
                control_table_df["temp_fraction"] = control_table_df[control_name] / control_table_df[scale_denominator]

                # if the denom is 0, warn and convert infinite fraction to zero
                zero_denom_df = control_table_df.loc[control_table_df["temp_fraction"]==numpy.inf].copy()
                if len(zero_denom_df) > 0:
                    logging.warn("  DROPPING Inf (sum {}):\n{}".format(zero_denom_df[control_name].sum(), str(zero_denom_df)))
                    control_table_df.loc[control_table_df["temp_fraction"]==numpy.inf, "temp_fraction"] = 0

                logging.debug("Divided by {}  temp_fraction mean:{}  Head:\n{}".format(scale_denominator, control_table_df["temp_fraction"].mean(), control_table_df.head()))

                # but return table at numerator geography
                numerator_df = temp_controls[scale_numerator].copy()
                add_aggregate_geography_colums(numerator_df)
                control_table_df = pandas.merge(left=numerator_df, right=control_table_df, how="left")
                logging.debug("Joined with num ({} rows) :\n{}".format(len(control_table_df), control_table_df.head()))
                control_table_df[control_name] = control_table_df["temp_fraction"] * control_table_df[scale_numerator]
                # keep only geometry column name and control
                control_table_df = control_table_df[[scale_numerator_geometry, control_name]]
                logging.debug("Final Total: {:,}  ({} rows)  Head:\n{}".format(control_table_df[control_name].sum(),
                              len(control_table_df), control_table_df.head()))

            elif len(temp_controls[scale_numerator]) == len(control_table_df):
                raise NotImplementedError("Temp scaling by numerator of same geography not implemented yet")

            else:
                raise ValueError("Temp scaling requires numerator or denominator geography to match")
        return control_table_df

    # if the census geography is smaller than the target geography, this is a simple aggregation
    if census_geo_index >= 0 and census_geo_index < control_geo_index:
        logging.info("Simple aggregation from {} to {}".format(census_geography, control_geography))

        if scale_numerator and scale_denominator:
            assert(len(temp_controls[scale_numerator  ]) == len(control_table_df))
            assert(len(temp_controls[scale_denominator]) == len(control_table_df))
            logging.info("  Scaling by {}/{}".format(scale_numerator,scale_denominator))

            control_table_df = pandas.merge(left=control_table_df, right=temp_controls[scale_numerator  ], how="left")
            control_table_df = pandas.merge(left=control_table_df, right=temp_controls[scale_denominator], how="left")
            control_table_df[control_name] = control_table_df[control_name] * control_table_df[scale_numerator]/control_table_df[scale_denominator]
            control_table_df.fillna(0, inplace=True)

            variable_total = variable_total * temp_controls[scale_numerator][scale_numerator].sum()/temp_controls[scale_denominator][scale_denominator].sum()

        if subtract_table:
            assert(len(temp_controls[subtract_table]) == len(control_table_df))
            logging.info("  Initial total {:,}".format(control_table_df[control_name].sum()))
            logging.info("  Subtracting out {} with sum {:,}".format(subtract_table, temp_controls[subtract_table][subtract_table].sum()))
            control_table_df = pandas.merge(left=control_table_df, right=temp_controls[subtract_table], how="left")
            control_table_df[control_name] = control_table_df[control_name] - control_table_df[subtract_table]

            variable_total = variable_total - temp_controls[subtract_table][subtract_table].sum()

        # we really only need these columns - control geography and the census geography
        geo_mapping_df   = maz_taz_def_df[[control_geography, "GEOID_{}".format(census_geography)]].drop_duplicates()
        control_table_df = pandas.merge(left=control_table_df, right=geo_mapping_df, how="left")

        # aggregate now
        final_df         = control_table_df[[control_geography, control_name]].groupby(control_geography).aggregate(numpy.sum)

        # verify the totals didn't change
        logging.debug("total at the end: {:,}".format(final_df[control_name].sum()))
        if full_region and not scale_numerator: assert(abs(final_df[control_name].sum() - variable_total) < 0.5)

        logging.info("  => Total for {} {:,}".format(control_name, final_df[control_name].sum()))
        return final_df

    # the census geography is larger than the target geography => proportional scaling is required
    # proportion = column / scale_denominator  (these should be at the same geography)
    # and then multiply by the scale_numerator (which should be at a smaller geography)

    # e.g. hh_inc_15_prop = hh_inc_15 / temp_num_hh_bg   (at block group)
    #      then multiply this by the households at the block level to get hh_inc_15 for blocks (these will be floats)
    #      and aggregate to control geo (e.g. TAZ)

    if scale_numerator == None or scale_denominator == None:
        msg = "Cannot go from larger census geography {} without numerator and denominator specified".format(census_geography)
        logging.fatal(msg)
        raise ValueError(msg)

    logging.info("scale_numerator={}  scale_denominator={}".format(scale_numerator, scale_denominator))

    # verify the last one matches our geography
    same_geo_total_df   = temp_controls[scale_denominator]
    assert(len(same_geo_total_df) == len(control_table_df))

    proportion_df = pandas.merge(left=control_table_df, right=same_geo_total_df, how="left")
    proportion_var = "{} proportion".format(control_name)
    proportion_df[proportion_var] = proportion_df[control_name] / proportion_df[scale_denominator]
    logging.info("Create proportion {} at {} geography via {} using {}/{}\n{}".format(
                  proportion_var, control_geography, census_geography,
                  control_name, scale_denominator, proportion_df.head()))
    logging.info("Sums:\n{}".format(proportion_df[[control_name, scale_denominator]].sum()))
    logging.info("Mean:\n{}".format(proportion_df[[proportion_var]].mean()))

    # join this to the maz_taz_definition - it'll be the lowest level
    block_prop_df = pandas.merge(left=maz_taz_def_df, right=proportion_df, how="left")
    # this is the first temp table, our multiplier
    block_total_df   = temp_controls[scale_numerator]
    block_prop_df = pandas.merge(left=block_prop_df, right=block_total_df, how="left")

    # now multiply to get total at block level
    block_prop_df[control_name] = block_prop_df[proportion_var]*block_prop_df[scale_numerator]
    logging.info("Multiplying proportion {}/{} (at {}) x {}\n{}".format(
                  control_name, scale_denominator, census_geography,
                  scale_numerator,  block_prop_df.head()))

    # NOW aggregate
    final_df = block_prop_df[[control_geography, control_name]].groupby(control_geography).aggregate(numpy.sum)
    # this won't be exact but hopefully close
    logging.info("Proportionally-derived Total added: {:,}".format(final_df[control_name].sum()))
    return final_df

def stochastic_round(my_series):
    """
    Performs stochastic rounding of a series and returns it.
    https://en.wikipedia.org/wiki/Rounding#Stochastic_rounding
    """
    numpy.random.seed(32)
    return numpy.floor(my_series + numpy.random.rand(len(my_series)))


def integerize_control(out_df, crosswalk_df, control_name):
    """
    Integerize this control
    """
    logging.debug("integerize_control for {}: out_df head:\n{}".format(control_name, out_df.head()))
    logging.debug("crosswalk_df head:\n{}".format(crosswalk_df.head()))

    # keep index as a normal column
    out_df.reset_index(drop=False, inplace=True)
    # keep track of columns to go back to
    out_df_cols = list(out_df.columns.values)

    # stochastic rounding
    out_df["control_stoch_round"] = stochastic_round(out_df[control_name])

    logging.debug("out_df sum:\n{}".format(out_df.sum()))

    # see how they look at the TAZ and county level
    out_df = pandas.merge(left=out_df, right=crosswalk_df, how="left")

    # this is being exacting... maybe not necessary

    # make them match taz totals (especially those that are already even)
    # really doing this in one iteration but check it
    for iteration in [1,2]:
        logging.debug("Iteration {}".format(iteration))

        out_df_by_taz = out_df[["TAZ",control_name,"control_stoch_round"]].groupby("TAZ").aggregate(numpy.sum).reset_index(drop=False)
        out_df_by_taz["control_taz"]       = out_df_by_taz[control_name]  # copy and name explicitly
        out_df_by_taz["control_round_taz"] = numpy.around(out_df_by_taz[control_name])

        out_df_by_taz["control_stoch_round_diff"]     = out_df_by_taz["control_round_taz"] - out_df_by_taz["control_stoch_round"]
        out_df_by_taz["control_stoch_round_diff_abs"] = numpy.absolute(out_df_by_taz["control_stoch_round_diff"])

        # if the total is off by less than one, don't touch
        # otherwise, choose a MAZ to tweak based on control already in the MAZ
        out_df_by_taz["control_adjust"] = numpy.trunc(out_df_by_taz["control_stoch_round_diff"])

        logging.debug("out_df_by_taz head:\n{}".format(out_df_by_taz.head()))
        logging.debug("out_df_by_taz sum:\n{}".format(out_df_by_taz.sum()))
        logging.debug("out_df_by_taz describe:\n{}".format(out_df_by_taz.describe()))

        tazdict_to_adjust = out_df_by_taz.loc[ out_df_by_taz["control_adjust"] != 0, ["TAZ","control_taz","control_adjust"]].set_index("TAZ").to_dict(orient="index")

        logging.debug("tazdict_to_adjust {} TAZS: {}".format(len(tazdict_to_adjust), tazdict_to_adjust))

        # nothing to do
        if len(tazdict_to_adjust)==0: break

        # add or remove a household if needed from a MAZ
        out_df = pandas.merge(left=out_df, right=out_df_by_taz[["TAZ","control_adjust","control_taz"]], how="left")
        logging.debug("out_df before adjustment:\n{}".format(out_df.head()))

        out_df_by_taz_grouped = out_df[["MAZ","TAZ",control_name,"control_stoch_round","control_adjust","control_taz"]].groupby("TAZ")
        for taz in tazdict_to_adjust.keys():
            # logging.debug("group for taz {} with tazdict_to_adjust {}:\n{}".format(taz, str(tazdict_to_adjust[taz]),
            #               out_df_by_taz_grouped.get_group(taz).head()))
            adjustment = tazdict_to_adjust[taz]["control_adjust"]  # e.g. -2
            sample_n   = int(abs(adjustment)) # e.g. 2
            change_by  = adjustment/sample_n  # so this will be +1 or -1

            # choose a maz to tweak weighted by number of households in the MAZ, so we don't tweak 0-hh MAZs
            try:
                sample = out_df_by_taz_grouped.get_group(taz).sample(n=sample_n, weights="control_stoch_round")
                # logging.debug("sample:\n{}".format(sample))

                # actually make the change in the out_df.  iterate rather than join since there are so few
                for maz in sample["MAZ"].tolist():
                    out_df.loc[ out_df["MAZ"] == maz, "control_stoch_round"] += change_by

            except ValueError as e:
                # this could fail if the weights are all zero
                logging.warn(e)
                logging.warn("group for taz {} with tazdict_to_adjust {}:\n{}".format(taz, str(tazdict_to_adjust[taz]),
                              out_df_by_taz_grouped.get_group(taz).head()))

    out_df_by_county = out_df[["COUNTY",control_name,"control_stoch_round"]].groupby("COUNTY").aggregate(numpy.sum).reset_index(drop=False)
    logging.debug("out_df_by_county head:\n{}".format(out_df_by_county.head()))
    logging.debug("out_df_by_county sum:\n{}".format(out_df_by_county.sum()))
    logging.debug("out_df_by_county describe:\n{}".format(out_df_by_county.describe()))

    # use the new version
    out_df[control_name] = out_df["control_stoch_round"].astype(int)
    # go back to original cols
    out_df = out_df[out_df_cols]
    # and index
    out_df.set_index("MAZ", inplace=True)


    return out_df

if __name__ == '__main__':
    pandas.set_option("display.width", 500)
    pandas.set_option("display.float_format", "{:,.2f}".format)

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=USAGE)
    parser.add_argument("--model_year", type=int)
    parser.add_argument("--test_PUMA", type=str, help="Pass PUMA to output controls only for geographies relevant to a single PUMA, for testing")
    args = parser.parse_args()

    # for now
   # if args.model_year not in [2020, 2023]:
   #     raise ValueError("Model year {} not supported yet".format(args.model_year))

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

    CONTROLS = {
        2020: collections.OrderedDict(),
        2023: collections.OrderedDict()
    }
    # TODO: Could probably make this more readable than a tuple
    # control name ->
    #  ( dataset (e.g. 'dec', 'acs5),
    #    year for dataset,
    #    table name within dataset,
    #    level of geography to use,
    #    columns filter (as an ordered dict),
    #    scale_numerator - name of table to multiply this by
    #    scale_denominator - name of table to divide this by
    #    subtract - name of table to subtract from this
    # )
    CONTROLS[2020]['MAZ'] = collections.OrderedDict([
        ('num_hh',        ('dec/dp',2020,'DP1_HOUSEHOLD_SIZE','block',[collections.OrderedDict([('pers_min',1),('pers_max',NPER_MAX)])])),
        ('hh_size_1',     ('dec/dp',2020,'DP1_HOUSEHOLD_SIZE','block',[collections.OrderedDict([('pers_min',1),('pers_max',1)])])),
        ('hh_size_2',     ('dec/dp',2020,'DP1_HOUSEHOLD_SIZE','block',[collections.OrderedDict([('pers_min',2),('pers_max',2)])])),
        ('hh_size_3',     ('dec/dp',2020,'DP1_HOUSEHOLD_SIZE','block',[collections.OrderedDict([('pers_min',3),('pers_max',3)])])),
        ('hh_size_4_plus',('dec/dp',2020,'DP1_HOUSEHOLD_SIZE','block',[collections.OrderedDict([('pers_min',4),('pers_max',NPER_MAX)])])),
        ('gq_num_hh',     ('dec/dhc',2020,'P5_GROUP_QUARTERS','block',[collections.OrderedDict([('inst','Noninstitutional'),('subcategory','All')])])),
        ('gq_type_univ',  ('dec/dhc',2020,'P5_GROUP_QUARTERS','block',[collections.OrderedDict([('inst','Noninstitutional'),('subcategory','College/University')])])),
        ('gq_type_mil',   ('dec/dhc',2020,'P5_GROUP_QUARTERS','block',[collections.OrderedDict([('inst','Noninstitutional'),('subcategory','Military')])])),
        ('gq_type_othnon',('dec/dhc',2020,'P5_GROUP_QUARTERS','block',[collections.OrderedDict([('inst','Noninstitutional'),('subcategory','Other Noninstitutional')])])),
        ('tot_pop',       ('dec/dp',2020,'DP1_SEX_BY_AGE','block',[collections.OrderedDict([('sex','All'),('age_min',0),('age_max',AGE_MAX)])])),
    ])

    CONTROLS[2023]['MAZ'] = collections.OrderedDict([
        ('temp_base_num_hh_b',   ('dec/dp',2020,'DP1_HOUSEHOLD_SIZE','block',[collections.OrderedDict([('pers_min',1),('pers_max',NPER_MAX)])])),
        ('temp_base_num_hh_bg',  ('dec/dp',2020,'DP1_HOUSEHOLD_SIZE','block group',[collections.OrderedDict([('pers_min',1),('pers_max',NPER_MAX)])])),
        ('temp_num_hh_bg_to_b',  ('acs5',2023,'B11016','block group',[collections.OrderedDict([('pers_min',1),('pers_max',NPER_MAX)])],'temp_base_num_hh_b','temp_base_num_hh_bg')),
        ('temp_num_hhinc',       ('acs5',2023,'B19001','block group',[collections.OrderedDict([('hhinc_min',0),('hhinc_max',HINC_MAX)])])),
        ('hh_inc_30',            ('acs5',2023,'B19001','block group',[collections.OrderedDict([('hhinc_min',0),('hhinc_max',34999)])],'temp_num_hh_bg_to_b','temp_num_hhinc')),
        ('hh_inc_30_60',         ('acs5',2023,'B19001','block group',[collections.OrderedDict([('hhinc_min',35000),('hhinc_max',74999)])],'temp_num_hh_bg_to_b','temp_num_hhinc')),
        ('hh_inc_60_100',        ('acs5',2023,'B19001','block group',[collections.OrderedDict([('hhinc_min',75000),('hhinc_max',124999)])],'temp_num_hh_bg_to_b','temp_num_hhinc')),
        ('hh_inc_100_plus',      ('acs5',2023,'B19001','block group',[collections.OrderedDict([('hhinc_min',125000),('hhinc_max',HINC_MAX)])],'temp_num_hh_bg_to_b','temp_num_hhinc')),
        ('temp_num_hh_wrks',     ('acs5',2023,'B08202','tract',[collections.OrderedDict([('workers_min',0),('workers_max',NWOR_MAX),('persons_min',0),('persons_max',NPER_MAX)])])),
        ('hh_wrks_0',            ('acs5',2023,'B08202','tract',[collections.OrderedDict([('workers_min',0),('workers_max',0),('persons_min',0),('persons_max',NPER_MAX)])],'temp_num_hh_bg_to_b','temp_num_hh_wrks')),
        ('hh_wrks_1',            ('acs5',2023,'B08202','tract',[collections.OrderedDict([('workers_min',1),('workers_max',1),('persons_min',0),('persons_max',NPER_MAX)])],'temp_num_hh_bg_to_b','temp_num_hh_wrks')),
        ('hh_wrks_2',            ('acs5',2023,'B08202','tract',[collections.OrderedDict([('workers_min',2),('workers_max',2),('persons_min',0),('persons_max',NPER_MAX)])],'temp_num_hh_bg_to_b','temp_num_hh_wrks')),
        ('hh_wrks_3_plus',       ('acs5',2023,'B08202','tract',[collections.OrderedDict([('workers_min',3),('workers_max',NWOR_MAX),('persons_min',0),('persons_max',NPER_MAX)])],'temp_num_hh_bg_to_b','temp_num_hh_wrks')),
        ('temp_base_num_pers_hh_b',('dec/dp',2020,'DP1_POPULATION_IN_HOUSEHOLDS','block',[collections.OrderedDict([('age_min',0),('age_max',AGE_MAX)])])),
        ('temp_base_num_pers_hh_bg',('dec/dp',2020,'DP1_POPULATION_IN_HOUSEHOLDS','block group',[collections.OrderedDict([('age_min',0),('age_max',AGE_MAX)])])),
        ('temp_num_pers_hh_bg_to_b',('acs5',2023,'B11002','block group',[collections.OrderedDict([])],'temp_base_num_pers_hh_b','temp_base_num_pers_hh_bg')),
        ('temp_num_pers',         ('acs5',2023,'B01001','block group',[collections.OrderedDict([('sex','All'),('age_min',0),('age_max',AGE_MAX)])])),
        ('pers_age_00_19',        ('acs5',2023,'B01001','block group',[collections.OrderedDict([('age_min',0),('age_max',19)])],'temp_num_pers_hh_bg_to_b','temp_num_pers')),
        ('pers_age_20_34',        ('acs5',2023,'B01001','block group',[collections.OrderedDict([('age_min',20),('age_max',34)])],'temp_num_pers_hh_bg_to_b','temp_num_pers')),
        ('pers_age_35_64',        ('acs5',2023,'B01001','block group',[collections.OrderedDict([('age_min',35),('age_max',64)])],'temp_num_pers_hh_bg_to_b','temp_num_pers')),
        ('pers_age_65_plus',      ('acs5',2023,'B01001','block group',[collections.OrderedDict([('age_min',65),('age_max',AGE_MAX)])],'temp_num_pers_hh_bg_to_b','temp_num_pers')),
        ('temp_num_hh_kids',      ('acs5',2023,'B11005','block group',[collections.OrderedDict([('num_kids_min',0),('num_kids_max',NKID_MAX)])])),
        ('hh_kids_no',            ('acs5',2023,'B11005','block group',[collections.OrderedDict([('num_kids_min',0),('num_kids_max',0)])],'temp_num_hh_bg_to_b','temp_num_hh_kids')),
        ('hh_kids_yes',           ('acs5',2023,'B11005','block group',[collections.OrderedDict([('num_kids_min',1),('num_kids_max',NKID_MAX)])],'temp_num_hh_bg_to_b','temp_num_hh_kids')),
    ])          

    CONTROLS[2020]['COUNTY'] = collections.OrderedDict([
        ('pers_occ_management',   ('acs5',2023,'C24010','tract',
                                [collections.OrderedDict([('occ_cat1','Management, business, science, and arts'),
                                                        ('occ_cat2','Management, business, and financial'),
                                                        ('occ_cat3','Management')])])),
        ('pers_occ_professional', ('acs5',2023,'C24010','tract',
                                [collections.OrderedDict([('occ_cat1','Management, business, science, and arts'),
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
                                                        ('occ_cat3','Health technologists and technicians')])])),

        ('pers_occ_services',     ('acs5',2023,'C24010','tract',
                                [collections.OrderedDict([('occ_cat1','Service'),
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
                                                        ('occ_cat3','All')])])),
        ('pers_occ_retail',       ('acs5',2023,'C24010','tract',
                                [collections.OrderedDict([('occ_cat1','Service'),
                                                        ('occ_cat2','Food preparation and serving related'),
                                                        ('occ_cat3','All')]),
                                collections.OrderedDict([('occ_cat1','Sales and office'),
                                                        ('occ_cat2','Sales and related'),
                                                        ('occ_cat3','All')])])),
        ('pers_occ_manual',       ('acs5',2023,'C24010','tract',
                                [collections.OrderedDict([('occ_cat1','Service'),
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
                                                        ('occ_cat3','All')])])),
        ('temp_gq_type_mil',       ('dec/dhc',2020,'P5_GROUP_QUARTERS','tract',
                                [collections.OrderedDict([('inst','Noninst'),
                                                        ('subcategory','Military')])])),
        ('pers_occ_military',     ('acs5',2023,'B23025','tract',
                                [collections.OrderedDict([('inlaborforce','Yes'),
                                                        ('type','Armed Forces')])],
                                None,None,'temp_gq_type_mil')),
    ])

    CONTROLS[2023]['COUNTY'] = collections.OrderedDict()
    # copy the 2020 controls but use updated acs
    for control_name in ['pers_occ_management',
                         'pers_occ_professional',
                         'pers_occ_services',
                         'pers_occ_retail',
                         'pers_occ_manual']:
        CONTROLS[2023]['COUNTY'][control_name] = list(CONTROLS[2020]['COUNTY'][control_name])
        # update ACS year
        CONTROLS[2023]['COUNTY'][control_name][1] = 2023

    # for military, tally GQ military similar to MAZ version
    # 2020 group quarters military - county level
    CONTROLS[2020]['COUNTY']['temp_base_gq_type_mil_co'] = ('dec/dhc',2020,'P5_GROUP_QUARTERS','county',[collections.OrderedDict([('inst','Noninst'),('subcategory','Military')])])
    CONTROLS[2020]['COUNTY']['temp_base_gq_all_co']     = ('dec/dhc',2020,'P5_GROUP_QUARTERS','county',[collections.OrderedDict([('sex','All'),('inst','All'),('subcategory','All')])])
    CONTROLS[2023]['COUNTY']['temp_gq_type_mil']        = ('acs5',2023,'B26001','county',[collections.OrderedDict([])],'temp_base_gq_type_mil_co','temp_base_gq_all_co')
    CONTROLS[2023]['COUNTY']['pers_occ_military']       = ('acs5',2023,'B23025','county',[collections.OrderedDict([('inlaborforce','Yes'),('type','Armed Forces')])],None,None,'temp_gq_type_mil')

    CONTROLS[2020]['REGION'] = collections.OrderedDict([
        ('gq_num_hh_region','special')  # these are special: just sum from MAZ to be consistent
    ])
    CONTROLS[2023]['REGION'] = collections.OrderedDict([
        ('gq_num_hh_region','special')  # these are special: just sum from MAZ to be consistent
    ])

    maz_taz_def_df = pandas.read_csv(MAZ_TAZ_DEF_FILE)
    # we use MAZ, TAZ not maz,taz; use GEOID_BLOCK
    maz_taz_def_df.rename(columns={"maz":"MAZ", "taz":"TAZ"}, inplace=True)
    maz_taz_def_df["GEOID_block"] = "0" + maz_taz_def_df["GEOID10"].astype(str)
    # add county, tract, block group GEOID
    add_aggregate_geography_colums(maz_taz_def_df)
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

    # this will be the crosswalk
    crosswalk_df = maz_taz_def_df.loc[ maz_taz_def_df["MAZ"] > 0] # drop MAZ=0
    crosswalk_df = crosswalk_df[["MAZ","TAZ","PUMA","COUNTY","county_name","REGION"]].drop_duplicates()
    crosswalk_df.sort_values(by="MAZ", inplace=True)

    cf = CensusFetcher()

    final_control_dfs = {} # control geography => dataframe
    for control_geo, control_dict in CONTROLS[args.model_year].items():
        temp_controls = collections.OrderedDict()

        for control_name, control_def in control_dict.items():
            logging.info("Creating control [{}] for geography [{}]".format(control_name, control_geo))
            logging.info("=================================================================================")

            if control_geo == "REGION" and control_name=="gq_num_hh_region":
                # these are special -- just sum from MAZ
                final_control_dfs[control_geo] = pandas.DataFrame.from_dict(data={'REGION':[1], "gq_num_hh_region":[final_control_dfs["MAZ"]["gq_num_hh"].sum()]}).set_index("REGION")
                logging.debug("\n{}".format(final_control_dfs[control_geo]))
            else:
                # create the controls from census data
               census_table_df = cf.get_census_data(dataset=control_def[0],
                                                    year   =control_def[1],
                                                    table  =control_def[2],
                                                    geo    =control_def[3])

               control_table_df = create_control_table(control_name, control_def[4], control_def[2], census_table_df)

               scale_numerator   = None
               scale_denominator = None
               subtract_table    = None
               if len(control_def) > 5:
                   scale_numerator   = control_def[5]
                   scale_denominator = control_def[6]
               if len(control_def) > 7:
                   subtract_table    = control_def[7]

               final_df = match_control_to_geography(control_name, control_table_df, control_geo, control_def[3],
                                                     maz_taz_def_df, temp_controls, full_region=(args.test_PUMA==None),
                                                     scale_numerator=scale_numerator, scale_denominator=scale_denominator,
                                                     subtract_table=subtract_table)

               # the temp control tables are special -- they're intermediate for matching
               if control_name.startswith("temp_"):
                   temp_controls[control_name] = final_df
                   continue

               # these are total_hh_control numbers -- they need to be integers.  tot_pop is for maz_data
               if control_name in ["num_hh","gq_num_hh","tot_pop"]:
                   final_df = integerize_control(final_df, crosswalk_df, control_name)

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
        logging.info("Preparing final controls files for {}".format(control_geo))
        out_df = final_control_dfs[control_geo].copy()  # easier to reference
        out_df.reset_index(drop=False, inplace=True)

        # First, log and drop control=0 if necessary
        if len(out_df.loc[ out_df[control_geo]==0]) > 0:
            logging.info("Dropping {}=0\n{}".format(control_geo, out_df.loc[ out_df[control_geo]==0,:].T.squeeze()))
            out_df = out_df.loc[out_df[control_geo]>0, :]
        
        if control_geo=="COUNTY":
            # for county, add readable county name
            out_df = pandas.merge(left=COUNTY_RECODE[["COUNTY","county_name"]], right=out_df, how="right")
        elif control_geo=="MAZ":
            # for maz, output a maz_data_hh_pop.csv for maz_data.csv
            maz_df = out_df[["MAZ","num_hh","gq_num_hh","tot_pop"]].copy()
            # gq "household" is 1-person hh; total household is sum of both
            # population already includes group quarters
            maz_df["hh"] = maz_df["num_hh"] + maz_df["gq_num_hh"]

            # check if pop < hh for any maz -- this shouldn't happen
            maz_df["pop_minus_hh"] = maz_df["tot_pop"] - maz_df["hh"]
            # only care if pop < hh (or pop-hh < 0)
            maz_df.loc[ maz_df["pop_minus_hh"] >= 0, "pop_minus_hh"] = 0

            logging.info("pop_minus_hh.sum: {}".format( maz_df["pop_minus_hh"].sum() ))
            logging.info("pop_minus_hh < 0 :\n{}".format( maz_df.loc[ maz_df["pop_minus_hh"] < 0 ]))

            # set pop to at least hh
            maz_df.loc[ maz_df["pop_minus_hh"] < 0, "tot_pop"] = maz_df["hh"]

            # keep only the fields we want
            maz_df = maz_df[["MAZ","hh", "tot_pop"]]

            # write it out
            maz_hh_pop_file = os.path.join("output_{}".format(args.model_year), "maz_data_hh_pop.csv")
            maz_df.to_csv(maz_hh_pop_file, index=False)
            logging.info("Wrote {}".format(maz_hh_pop_file))

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
            hh_control_df.to_csv(hh_control_file, index=False, float_format="%.5f")
            logging.info("Wrote control file {}".format(hh_control_file))

        if len(gq_control_names) > 0:
            gq_control_df   = out_df[[control_geo] + gq_control_names]
            gq_control_file = os.path.join("group_quarters", "data", "{}_{}_controls.csv".format(args.model_year, control_geo))
            gq_control_df.to_csv(gq_control_file, index=False, float_format="%.5f")
            logging.info("Wrote control file {}".format(gq_control_file))


    # finally, save the cross walk file
    for hh_gq in ["households","group_quarters"]:
        crosswalk_file = os.path.join(hh_gq, "data", "geo_cross_walk.csv")
        crosswalk_df.to_csv(crosswalk_file, index=False)
        logging.info("Wrote geographic cross walk file {}".format(crosswalk_file))
