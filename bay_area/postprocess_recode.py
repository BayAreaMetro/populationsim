USAGE = r"""

Combines synthetic person and housing records for households and group quarters, as well as the melted summary.

Inputs:
(1) [args.directory]/final_summary_[TAZ|COUNTY_N].csv
(2) [args.directory]/synthetic_households.csv
(3) [args.directory]/synthetic_persons.csv
(4) hh_gq/data/geo_cross_walk_tm1.csv

Outputs:
(1) [args.directory]/summary_melt.csv
(2) [args.directory]/synthetic_households_recoded.csv
(3) [args.directory]/synthetic_persons_recoded.csv

Basic functions:
(a) Create control vs result summary, summary_melt.csv
(b) Add PERID to persons
(c) Fills NaN values with -9
(d) subset & rename household/persons columns according to HOUSING_COLUMNS/PERSON_COLUMNS
(e) adds additional columns hinccat1, poverty_income_[year]d, poverty_income_2000d, pct_of_poverty
(f) Downcasts columns to int where possible

"""
import argparse, collections, logging, pathlib, sys
import pandas

# based on: https://github.com/BayAreaMetro/modeling-website/wiki/PopSynHousehold, PopSyn scripts
HOUSING_COLUMNS = {
    'TM1':collections.OrderedDict([
      ("unique_hh_id",        "HHID"), 
      ("TAZ",                 "TAZ"),
     #("hinccat1",            "hinccat1"),  # commented out since this is added after hh+gq combine
      ("hh_income_2000",      "HINC"),
      ("hh_workers_from_esr", "hworkers"),
      ("VEH",                 "VEHICL"),
      ("BLD",                 "BLD"),       # added Feb '23
      ("TEN",                 "TEN"),       # added Feb '23
      ("NP",                  "PERSONS"),
      ("HHT",                 "HHT"),
      ("TYPEHUGQ",            "UNITTYPE")
    ]),
    # http://bayareametro.github.io/travel-model-two/input/#households
    'TM2':collections.OrderedDict([
      ("unique_hh_id",        "HHID"),          # Fixed: use unique_hh_id from PopulationSim
      ("TAZ",                 "TAZ"),
      ("MAZ",                 "MAZ"),
      ("COUNTY",              "MTCCountyID"),   # Maps to county 1-9
      ("hh_income_2010",      "HHINCADJ"),     # 2010 dollars as required by TM2
      ("hh_workers_from_esr", "NWRKRS_ESR"),
      ("VEH",                 "VEH"),
      ("TEN",                 "TEN"),
      ("NP",                  "NP"),
      ("HHT",                 "HHT"),
      ("BLD",                 "BLD"),
      ("TYPEHUGQ",            "TYPE"),          # Fixed: use TYPEHUGQ from PopulationSim
    ]),
  }
  
PERSON_COLUMNS = {
    # based on: https://github.com/BayAreaMetro/modeling-website/wiki/PopSynPerson, PopSyn scripts
    'TM1':collections.OrderedDict([
      ("unique_hh_id",        "HHID"),
      ("PERID",               "PERID"),
      ("AGEP",                "AGE"),
      ("SEX",                 "SEX"),
      ("employ_status",       "pemploy"),
      ("student_status",      "pstudent"),
      ("person_type",         "ptype")
    ]),
    # http://bayareametro.github.io/travel-model-two/input/#persons
    'TM2':collections.OrderedDict([
      ("unique_hh_id",        "HHID"),          # Fixed: use unique_hh_id from PopulationSim
      ("unique_per_id",       "PERID"),         # Fixed: use unique_per_id from PopulationSim
      ("AGEP",                "AGEP"),
      ("SEX",                 "SEX"),
      ("SCHL",                "SCHL"),
      ("occupation",          "OCCP"),
      ("WKHP",                "WKHP"),
      ("WKW",                 "WKW"),
      ("employed",            "EMPLOYED"),
      ("ESR",                 "ESR"),
      ("SCHG",                "SCHG"),
      ("hhgqtype",            "hhgqtype"),      # Added: group quarters type
      ("person_type",         "person_type"),  # Added: employment-based person type
    ])
  }

if __name__ == '__main__':
    pandas.options.display.width    = 180
    pandas.options.display.max_rows = 1000

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, 
        description=USAGE)
    parser.add_argument("--test_PUMA", type=str, help="Pass PUMA to output controls only for geographies relevant to a single PUMA, for testing")
    parser.add_argument("--model_type",type=str, help="Specifies TM1 or TM2", required=True)
    parser.add_argument("--directory", type=str, help="Directory with populationsim output", required=True)
    parser.add_argument("--year",      type=int, help="Model year (used for poverty level calculations)", required=True)
    args = parser.parse_args()

    LOG_FILE = pathlib.Path(args.directory) / "postprocess_recode.log"
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
  
    # read the geo cross walk
    if args.model_type == 'TM1':
      geocrosswalk_df = pandas.read_csv(pathlib.Path("hh_gq/data/geo_cross_walk_tm1.csv"))
      # print(geocrosswalk_df.head())
    if args.model_type == 'TM2':
      # TM2 uses the unified crosswalk from the pipeline
      from unified_tm2_config import UnifiedTM2Config
      config = UnifiedTM2Config()
      geocrosswalk_df = pandas.read_csv(config.CROSSWALK_FILES['popsim_crosswalk'])
      logging.info("Read TM2 crosswalk with {:,} rows".format(len(geocrosswalk_df)))

    # (a) Create control vs result summary, summary_melt.csv

    # Functions for generating unique IDs in TM2
    def add_unique_household_id(households_df):
        """Add unique_hh_id field if it doesn't exist"""
        if 'unique_hh_id' not in households_df.columns:
            if 'SERIALNO' in households_df.columns:
                households_df['unique_hh_id'] = households_df['SERIALNO']
            else:
                households_df['unique_hh_id'] = households_df.index + 1
        return households_df
    
    def add_unique_person_id(persons_df):
        """Add unique_per_id field if it doesn't exist"""
        if 'unique_per_id' not in persons_df.columns:
            if 'SERIALNO' in persons_df.columns and 'SPORDER' in persons_df.columns:
                persons_df['unique_per_id'] = persons_df['SERIALNO'].astype(str) + '_' + persons_df['SPORDER'].astype(str)
            else:
                persons_df['unique_per_id'] = persons_df.index + 1
        return persons_df


        # read the taz and county summaries
    taz_summary_file = pathlib.Path(args.directory) / "final_summary_TAZ.csv"
    taz_summary_df = pandas.read_csv(taz_summary_file)
    logging.info("Read {:,} rows from {}".format(len(taz_summary_df), taz_summary_file))
    logging.debug("taz_summary_df.dtypes():\n{}".format(taz_summary_df.dtypes))

    # melt to columns: geography, id, variable, result, control, diff
    control_vars = []
    for column in list(taz_summary_df.columns):
      if column.endswith("_control"):
        control_vars.append(column[:-8])
    logging.debug("TAZ control_vars = {}".format(control_vars))

    taz_summary_result_melt_df = pandas.melt(
      taz_summary_df, 
      id_vars=['geography','id'],
      value_vars=[var + "_result" for var in control_vars],
      value_name = 'result'
    )
    taz_summary_result_melt_df.variable = taz_summary_result_melt_df.variable.str[:-7] # strip _result
    taz_summary_control_melt_df = pandas.melt(
      taz_summary_df, 
      id_vars=['geography','id'],
      value_vars=[var + "_control" for var in control_vars],
      value_name = 'control'
    )
    taz_summary_control_melt_df.variable = taz_summary_control_melt_df.variable.str[:-8] # strip _control
    summary_melt_df = pandas.merge(
      left=taz_summary_result_melt_df,
      right=taz_summary_control_melt_df,
      on=['geography','id','variable']
    )

    # in the county summary files, columns are named differently
    for county_num in range(1,10):
        county_result_file = pathlib.Path(args.directory) / "final_summary_COUNTY_{}.csv".format(county_num)
        county_result_df = pandas.read_csv(county_result_file, 
                                           usecols=['control_name','control_value','TAZ_integer_weight'])
        county_result_df['geography'] = 'county'
        county_result_df['id'] = county_num
        county_result_df.rename(columns={
           'control_name':'variable',
           'control_value':'control', 
           'TAZ_integer_weight':'result'}, inplace=True)
        
        summary_melt_df = pandas.concat([summary_melt_df, county_result_df])

    # I'll calculate my own diff, thank you
    summary_melt_df['diff'] = summary_melt_df.result - summary_melt_df.control
    logging.debug("summary_melt_df:\n{}".format(summary_melt_df))
    summary_melt_output_file = pathlib.Path(args.directory) / "summary_melt.csv"
    summary_melt_df.to_csv(summary_melt_output_file, index=False)
    logging.info("Wrote {:,} rows to {}".format(len(summary_melt_df), summary_melt_output_file))

    # read households
    household_file = pathlib.Path(args.directory) / "synthetic_households.csv"
    households_df = pandas.read_csv(household_file)
    logging.info("Read {:,} rows from {}".format(len(households_df), household_file))
    logging.debug("households_df.head():\n{}".format(households_df.head()))
    logging.debug("households_df.dtypes:\n{}".format(households_df.dtypes))

    persons_file = pathlib.Path(args.directory) / "synthetic_persons.csv"
    persons_df = pandas.read_csv(persons_file)
    logging.info("Read {:,} rows from {}".format(len(persons_df), persons_file))
    logging.debug("persons_df.head():\n{}".format(persons_df.head()))
    logging.debug("persons_df.dtypes:\n{}".format(persons_df.dtypes))
  
    # (b) Add PERID to persons
    persons_df["PERID"] = persons_df.index + 1 # start from 1
  
    # (c) Fills NaN values with -9
    households_df.fillna(value=-9, inplace=True)
    persons_df.fillna(value=-9, inplace=True)

    # (d) subset & rename household columns according to HOUSING_COLUMNS
    households_df = households_df[HOUSING_COLUMNS[args.model_type].keys()].rename(columns=HOUSING_COLUMNS[args.model_type])

    if args.model_type == 'TM1': 
        # add hinccat1 as variable for tm1, group hh_income_2000 by tm1 income categories
        households_df['hinccat1'] = 0
        households_df.loc[                              (households_df.HINC< 20000), 'hinccat1'] = 1
        households_df.loc[ (households_df.HINC>= 20000)&(households_df.HINC< 50000), 'hinccat1'] = 2
        households_df.loc[ (households_df.HINC>= 50000)&(households_df.HINC<100000), 'hinccat1'] = 3
        households_df.loc[ (households_df.HINC>=100000)                            , 'hinccat1'] = 4
        # recode -9 HHT to 0
        households_df.loc[ households_df.HHT==-9, 'HHT'] = 0

        # add poverty level calculation
        # use model year to translate household income from 2000 dollars into the model year dollars
        # Source: https://github.com/BayAreaMetro/modeling-website/wiki/InflationAssumptions
        DOLLARS_2000_TO_MODELYEAR  = 1.0
        # Source: https://aspe.hhs.gov/topics/poverty-economic-mobility/poverty-guidelines/prior-hhs-poverty-guidelines-federal-register-references
        INC_FIRST_PERSON           = 0
        INC_EACH_ADDITIONAL_PERSON = 0
        if args.year == 2015:
          DOLLARS_2000_TO_MODELYEAR  = 1.43
          INC_FIRST_PERSON           = 11770
          INC_EACH_ADDITIONAL_PERSON = 4160
        elif args.year >= 2023:
          DOLLARS_2000_TO_MODELYEAR  = 1.88
          INC_FIRST_PERSON           = 14580
          INC_EACH_ADDITIONAL_PERSON = 5140
        else:
          raise RuntimeError(f"Model year {args.year} not supported for poverty calculation")
        
        # calculate poverty threshold income in args.year dollars
        households_df[f'poverty_income_{args.year}d'] = INC_FIRST_PERSON + (households_df.PERSONS-1)*INC_EACH_ADDITIONAL_PERSON
        # convert to 2000 dollars
        households_df['poverty_income_2000d'] = round(households_df[f'poverty_income_{args.year}d']/DOLLARS_2000_TO_MODELYEAR)
        # calculate income/poverty_income_2000d
        households_df['pct_of_poverty'] = round(100.0 * (households_df.HINC / households_df.poverty_income_2000d))

    # (f) subset & rename persons columns according to PERSON_COLUMNS
    persons_df = persons_df[PERSON_COLUMNS[args.model_type].keys()].rename(columns=PERSON_COLUMNS[args.model_type])
    # set occp=0 to 999
    if args.model_type == 'TM2':
        persons_df.loc[persons_df.OCCP==0, "OCCP"] = 999

    # (f) Downcasts columns to int where possible
    import create_seed_population
    logger.info("-- clean_types(households_df) --")
    create_seed_population.clean_types(households_df)
    logger.info("-- clean_types(persons_df) --")
    create_seed_population.clean_types(persons_df)

    households_outfile = pathlib.Path(args.directory) /  "synthetic_households_recode.csv"
    logging.info("Writing {:,} rows to {}".format(len(households_df), households_outfile))
    households_df.to_csv(households_outfile, header=True, index=False)
    logging.info("Done")

    persons_outfile = pathlib.Path(args.directory) /  "synthetic_persons_recode.csv"
    logging.info("Writing {:,} rows to {}".format(len(persons_df), persons_outfile))
    persons_df.to_csv(persons_outfile, header=True, index=False)
    logging.info("Done")


