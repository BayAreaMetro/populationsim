USAGE = r"""

  Combines synthetic person and housing records for households and group quarters, as well as the melted summary.

  Inputs:
  (1) hh_gq/output_[model_year]/synthetic_households.csv
  (2) hh_gq/output_[model_year]/synthetic_persons.csv
  (3) hh_gq/output_[model_year]/summary_melt.csv
  (4) group_quarters/data/geo_cross_walk.csv
  (5) hh_gq/data/[model_year]_COUNTY_controls.csv

  Outputs:
  (1) output_[model_year]/synthetic_households.csv
  (2) output_[model_year]/synthetic_persons.csv
  (3) output_[model_year]/summary_melt.csv

  Basic functions:
  (a) Concatenates person and housing records for households and group quarters, creating a
      unique HHID and PERID.
  (b) Add TAZ to group quarters from MAZ (it's not there since there are no TAZ level controls)
  (c) Add MTCCountyID to all
  (c) Fills NaN values with -9
  (d) Downcasts columns to int
  (e) Adds county-level household summaries to summary_melt since they're not there.

"""


import argparse, collections, os, sys
import pandas

# based on: https://github.com/BayAreaMetro/modeling-website/wiki/PopSynHousehold, PopSyn scripts
HOUSING_COLUMNS = {
  'TM1':collections.OrderedDict([
    ("HHID",                "HHID"), 
    ("TAZ",                 "TAZ"),
   #("hinccat1",            "hinccat1"),  # commented out since this is added after hh+gq combine
    ("hh_income_2000",      "HINC"),
    ("hh_workers_from_esr", "hworkers"),
    ("VEH",                 "VEHICL"),
    ("BLD",                 "BLD"),       # added Feb '23
    ("TEN",                 "TEN"),       # added Feb '23
    ("NP",                  "PERSONS"),
    ("HHT",                 "HHT"),
    ("TYPE",                "UNITTYPE")
  ]),
  # http://bayareametro.github.io/travel-model-two/input/#households
  'TM2':collections.OrderedDict([
    ("HHID",                "HHID"),
    ("TAZ",                 "TAZ"),
    ("MAZ",                 "MAZ"),
    ("COUNTY",              "MTCCountyID"),
    ("hh_income_2010",      "HHINCADJ"),
    ("hh_workers_from_esr", "NWRKRS_ESR"),
    ("VEH",                 "VEH"),
    ("TEN",                 "TEN"),       # added Feb '23
    ("NP",                  "NP"),
    ("HHT",                 "HHT"),
    ("BLD",                 "BLD"),
    ("TYPE",                "TYPE")
  ]),
}

PERSON_COLUMNS = {
  # based on: https://github.com/BayAreaMetro/modeling-website/wiki/PopSynPerson, PopSyn scripts
  'TM1':collections.OrderedDict([
    ("HHID",                "HHID"),
    ("PERID",               "PERID"),
    ("AGEP",                "AGE"),
    ("SEX",                 "SEX"),
    ("employ_status",       "pemploy"),
    ("student_status",      "pstudent"),
    ("person_type",         "ptype")
  ]),
  # http://bayareametro.github.io/travel-model-two/input/#persons
  'TM2':collections.OrderedDict([
    ("HHID",                "HHID"),
    ("PERID",               "PERID"),
    ("AGEP",                "AGEP"),
    ("SEX",                 "SEX"),
    ("SCHL",                "SCHL"),
    ("occupation",          "OCCP"),
    ("WKHP",                "WKHP"),
    ("WKW",                 "WKW"),
    ("employed",            "EMPLOYED"),
    ("ESR",                 "ESR"),
    ("SCHG",                "SCHG"),
  ])
}

if __name__ == '__main__':
  pandas.options.display.width    = 180

  parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, 
    description=USAGE)
  parser.add_argument("--model_type", type=str, help="Specifies TM1 or TM2")
  parser.add_argument("--model_year", type=int)
  parser.add_argument("--test_PUMA", type=str, help="Pass PUMA to output controls only for geographies relevant to a single PUMA, for testing")
  parser.add_argument("--run_num",    help="Prefix for control filename")
  args = parser.parse_args()

  # create output dir if needed
  COMBINED_OUT_DIR = "output_%d" % args.model_year
  if args.test_PUMA: COMBINED_OUT_DIR = "%s_puma%s" % (COMBINED_OUT_DIR, args.test_PUMA)

  if not os.path.exists(COMBINED_OUT_DIR):
    os.mkdir(COMBINED_OUT_DIR)
    print "Created %s" % COMBINED_OUT_DIR

  # read the geo cross walk
  if args.model_type == 'TM1':
    geocrosswalk_df = pandas.read_csv(os.path.join("hh_gq","data","geo_cross_walk_tm1.csv"))
    print(geocrosswalk_df.head())
  if args.model_type == 'TM2':
    geocrosswalk_df = pandas.read_csv(os.path.join("group_quarters","data","geo_cross_walk_tm2.csv"))
    print(geocrosswalk_df.head())

  hh_counties_df = None

  for filename in ["synthetic_households.csv", "synthetic_persons.csv", "summary_melt.csv"]:
    table_hhgq = pandas.read_csv(os.path.join("hh_gq", COMBINED_OUT_DIR, filename))

    print table_hhgq.head()
    print table_hhgq.columns

    if filename=="synthetic_households.csv":
      # add HHID
      table_hhgq["HHID"] = table_hhgq.unique_hh_id  # this already starts from 1

      if args.model_type == 'TM1': 
        # the households don't have county so get county from crosswalk
        table_hhgq = pandas.merge(left=table_hhgq, right=geocrosswalk_df[["TAZ","COUNTY"]], how="left")

      if args.model_type == 'TM2':
        # the households don't have county so get county from crosswalk
        table_hhgq = pandas.merge(left=table_hhgq, right=geocrosswalk_df[["MAZ","COUNTY"]], how="left")

      # save for creating county summaries
      hh_counties_df = table_hhgq[["HHID","COUNTY"]]

    elif filename=="synthetic_persons.csv":
      # add HHID
      table_hhgq["HHID"]  = table_hhgq.unique_hh_id 
      table_hhgq["PERID"] = table_hhgq.index + 1 # start from 1

      # create county summaries - only want employed (see controls.csv)
      pers_county_occ_summary = pandas.merge(left  =table_hhgq.loc[ table_hhgq["employed"] == 1, ["HHID","PERID","occupation"]], 
                                             right =hh_counties_df,
                                             how   ="left",
                                             on    ="HHID")
      pers_county_occ_summary = pers_county_occ_summary.groupby(["COUNTY","occupation"]).agg("count").reset_index()

      pers_county_occ_summary.rename(columns={"COUNTY":"id", "occupation":"variable", "PERID":"result"}, inplace=True)
      pers_county_occ_summary.drop(columns="HHID",inplace=True)
      pers_county_occ_summary["geography"] = "COUNTY"
      pers_county_occ_summary["type"]      = "households"
      pers_county_occ_summary.replace(to_replace={"variable":  # recode variable
                                         {1:"pers_occ_management",
                                          2:"pers_occ_professional",
                                          3:"pers_occ_services",
                                          4:"pers_occ_retail",
                                          5:"pers_occ_manual",
                                          6:"pers_occ_military"}}, inplace=True)
      print(pers_county_occ_summary.head())

    elif filename=="summary_melt.csv" and False:
      # add county summaries
      county_controls_filename = os.path.join("hh_gq","data","{}_county_marginals_{}.csv".format(args.run_num, args.model_year))
      county_controls_df = pandas.read_csv(county_controls_filename)
      county_controls_df = county_controls_df[["COUNTY","pers_occ_management",
        "pers_occ_professional","pers_occ_services","pers_occ_retail","pers_occ_manual","pers_occ_military"]]
      county_controls_df = county_controls_df.melt(id_vars=["COUNTY"], var_name="variable", value_name="control")
      county_controls_df.rename(columns={"COUNTY":"id"}, inplace=True)
      # print(county_controls_df.head())

      county_controls_df = pandas.merge(left=county_controls_df, right=pers_county_occ_summary, how="left")
      county_controls_df.fillna(value={"geography":"COUNTY", "type":"households", "result":0}, inplace=True)
      county_controls_df["diff"] = county_controls_df["result"] - county_controls_df["control"]
      # print(county_controls_df.head())

      county_controls_df = county_controls_df[ list(table_hhgq.columns) ]  # reorder columns to match
      table_hhgq = pandas.concat([table_hhgq, county_controls_df])

    # concatenate the household and group quarters tables
    table_hhgq.fillna(value=-9, inplace=True)

    if filename=="synthetic_households.csv":
      # fix the columns up
      table_hhgq = table_hhgq[HOUSING_COLUMNS[args.model_type].keys()].rename(columns=HOUSING_COLUMNS[args.model_type])

      if args.model_type == 'TM1': 
        # add hinccat1 as variable for tm1, group hh_income_2000 by tm1 income categories
        table_hhgq['hinccat1'] = 0
        table_hhgq.loc[                           (table_hhgq.HINC< 20000), 'hinccat1'] = 1
        table_hhgq.loc[ (table_hhgq.HINC>= 20000)&(table_hhgq.HINC< 50000), 'hinccat1'] = 2
        table_hhgq.loc[ (table_hhgq.HINC>= 50000)&(table_hhgq.HINC<100000), 'hinccat1'] = 3
        table_hhgq.loc[ (table_hhgq.HINC>=100000)                           , 'hinccat1'] = 4
        # recode -9 HHT to 0
        table_hhgq.loc[ table_hhgq.HHT==-9, 'HHT'] = 0

    elif filename=="synthetic_persons.csv":
      # fix the columns up
      table_hhgq = table_hhgq[PERSON_COLUMNS[args.model_type].keys()].rename(columns=PERSON_COLUMNS[args.model_type])
      # set occp=0 to 999
      if args.model_type == 'TM2':
        table_hhgq.loc[table_hhgq.OCCP==0, "OCCP"] = 999
    elif filename=="summary_melt.csv":
      # perfect
      pass

    # downcast the floats that don't need to be floats
    import create_seed_population
    create_seed_population.clean_types(table_hhgq)

    print table_hhgq.head(20)
    print table_hhgq.tail(20)
    outfile = os.path.join(COMBINED_OUT_DIR, filename)
    table_hhgq.to_csv(outfile, header=True, index=False)
    print "Wrote %s" % outfile


