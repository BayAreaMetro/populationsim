USAGE = r"""

  Combines synthetic person and housing records for households and group quarters, as well as the melted summary.

  Inputs:
  (1) [households,group_quarters]/output_[model_year]/synthetic_households.csv
  (2) [households,group_quarters]/output_[model_year]/synthetic_persons.csv
  (3) [households,group_quarters]/output_[model_year]/summary_melt.csv
  (4) group_quarters/data/geo_cross_walk.csv
  (5) households/data/[model_year]_COUNTY_controls.csv

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
# http://bayareametro.github.io/travel-model-two/input/#households
HOUSING_COLUMNS = collections.OrderedDict([
  ("HHID",                "HHID"),
  ("TAZ",                 "TAZ"),
  ("MAZ",                 "MAZ"),
  ("COUNTY",              "MTCCountyID"),
  ("hh_income_2010",      "HHINCADJ"),
  ("hh_workers_from_esr", "NWRKRS_ESR"),
  ("VEH",                 "VEH"),
  ("NP",                  "NP"),
  ("HHT",                 "HHT"),
  ("BLD",                 "BLD"),
  ("TYPE",                "TYPE")
])

# http://bayareametro.github.io/travel-model-two/input/#persons
PERSON_COLUMNS = collections.OrderedDict([
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


if __name__ == '__main__':
  pandas.options.display.width    = 180

  parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, 
    description=USAGE)
  parser.add_argument("model_year", type=int)
  parser.add_argument("--test_PUMA", type=str, help="Pass PUMA to output controls only for geographies relevant to a single PUMA, for testing")
  args = parser.parse_args()

  # create output dir if needed
  COMBINED_OUT_DIR = "output_%d" % args.model_year
  if args.test_PUMA: COMBINED_OUT_DIR = "%s_puma%s" % (COMBINED_OUT_DIR, args.test_PUMA)

  if not os.path.exists(COMBINED_OUT_DIR):
    os.mkdir(COMBINED_OUT_DIR)
    print "Created %s" % COMBINED_OUT_DIR

  # read the geo cross walk
  geocrosswalk_df = pandas.read_csv(os.path.join("group_quarters","data","geo_cross_walk.csv"))
  print(geocrosswalk_df.head())

  hh_counties_df = None

  for filename in ["synthetic_households.csv", "synthetic_persons.csv", "summary_melt.csv"]:
    table_hh = pandas.read_csv(os.path.join("households",     COMBINED_OUT_DIR, filename))
    table_gq = pandas.read_csv(os.path.join("group_quarters", COMBINED_OUT_DIR, filename))

    print table_hh.head()
    print table_gq.head()

    if filename=="synthetic_households.csv":
      # add HHID
      table_hh["HHID"] = table_hh.unique_hh_id  # this already starts from 1
      max_hhid = table_hh.HHID.max()
      print "Max housing record HHID: %d" % max_hhid
      table_gq["HHID"] = table_gq.unique_hh_id + max_hhid # start from max_hhid + 1

      # the group quarters doesn't have taz so get taz from crosswalk
      table_gq = pandas.merge(left=table_gq, right=geocrosswalk_df[["MAZ","TAZ"]], how="left")

      # the households doesn't have county so get county from crosswalk
      table_hh = pandas.merge(left=table_hh, right=geocrosswalk_df[["MAZ","COUNTY"]], how="left")

      # save for creating county summaries
      hh_counties_df = table_hh[["HHID","COUNTY"]]

    elif filename=="synthetic_persons.csv":
      # add HHID
      table_hh["HHID"] = table_hh.unique_hh_id
      table_gq["HHID"] = table_gq.unique_hh_id + max_hhid
      table_hh["PERID"] = table_hh.index + 1 # start from 1
      max_perid = table_hh.PERID.max()
      print "Max housing record PERID: %d" % max_perid
      table_gq["PERID"] = table_gq.index + 1 + max_perid # start from max_perid + 1

      # create county summaries - only want employed (see controls.csv)
      hh_pers_county_occ_summary = pandas.merge(left  =table_hh.loc[ table_hh["employed"] == 1, ["HHID","PERID","occupation"]],
                                                right =hh_counties_df,
                                                how   ="left",
                                                on    ="HHID")
      hh_pers_county_occ_summary = hh_pers_county_occ_summary.groupby(["COUNTY","occupation"]).agg("count").reset_index()

      hh_pers_county_occ_summary.rename(columns={"COUNTY":"id", "occupation":"variable", "PERID":"result"}, inplace=True)
      hh_pers_county_occ_summary.drop(columns="HHID",inplace=True)
      hh_pers_county_occ_summary["geography"] = "COUNTY"
      hh_pers_county_occ_summary["type"]      = "households"
      hh_pers_county_occ_summary.replace(to_replace={"variable":  # recode variable
                                         {1:"pers_occ_management",
                                          2:"pers_occ_professional",
                                          3:"pers_occ_services",
                                          4:"pers_occ_retail",
                                          5:"pers_occ_manual",
                                          6:"pers_occ_military"}}, inplace=True)
      print(hh_pers_county_occ_summary.head())

    elif filename=="summary_melt.csv":
      # just add a column for type
      table_hh["type"] = "households"
      table_gq["type"] = "group_quarters"
      # add county summaries
      county_hh_controls_df = pandas.read_csv(os.path.join("households","data","{}_COUNTY_controls.csv".format(args.model_year)))
      county_hh_controls_df = county_hh_controls_df[["COUNTY","pers_occ_management",
        "pers_occ_professional","pers_occ_services","pers_occ_retail","pers_occ_manual","pers_occ_military"]]
      county_hh_controls_df = county_hh_controls_df.melt(id_vars=["COUNTY"], var_name="variable", value_name="control")
      county_hh_controls_df.rename(columns={"COUNTY":"id"}, inplace=True)
      print(county_hh_controls_df.head())
      county_hh_controls_df = pandas.merge(left=county_hh_controls_df, right=hh_pers_county_occ_summary, how="left")
      county_hh_controls_df["diff"] = county_hh_controls_df["result"] - county_hh_controls_df["control"]
      print(county_hh_controls_df.head())

      county_hh_controls_df = county_hh_controls_df[ list(table_hh.columns) ]  # reorder columns to match
      table_hh = pandas.concat([table_hh, county_hh_controls_df])

    concat_table = pandas.concat([table_hh, table_gq])
    concat_table.fillna(value=-9, inplace=True)

    if filename=="synthetic_households.csv":
      # fix the columns up
      concat_table = concat_table[HOUSING_COLUMNS.keys()].rename(columns=HOUSING_COLUMNS)
    elif filename=="synthetic_persons.csv":
      # fix the columns up
      concat_table = concat_table[PERSON_COLUMNS.keys()].rename(columns=PERSON_COLUMNS)
      # set occp=0 to 999
      concat_table.loc[concat_table.OCCP==0, "OCCP"] = 999
    elif filename=="summary_melt.csv":
      # perfect
      pass

    # downcast the floats that don't need to be floats
    import create_seed_population
    create_seed_population.clean_types(concat_table)

    print concat_table.head(20)
    print concat_table.tail(20)
    outfile = os.path.join(COMBINED_OUT_DIR, filename)
    concat_table.to_csv(outfile, header=True, index=False)
    print "Wrote %s" % outfile


