USAGE = r"""

  Combines synthetic person and housing records for households and group quarters, as well as the melted summary.

  Inputs:
  (1) [households,group_quarters]/output_[model_year]/synthetic_households.csv
  (2) [households,group_quarters]/output_[model_year]/synthetic_persons.csv
  (3) [households,group_quarters]/output_[model_year]/summary_melt.csv

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

"""

import argparse, os, sys
import pandas

# these are the columns in the current households input:
HOUSING_COLUMNS = [
  # "tempId",         # do we need this?
  "MTCCountyID",
  "PUMA",
  "taz",
  "maz",
  "WGTP",
  # "finalPumsId",    # what's this? do we need this?
  # "finalweight",    # what's this? do we need this?
  "serialno",
  "np",
  "hincp",
  "ten",
  "bld",
  "nwrkrs_esr",
  "hhincAdj",
  "adjinc",
  "veh",
  "hht",
  "type",
  "npf",              # do we need this?  it's similar to np
  "hupac",
  "GQFlag",           # do we need this?  isn't type enough?
  "GQType",           # do we need this?  similar to type
  "HHID",
  # "n"               # what's this?  do we need it?
]

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

    elif filename=="synthetic_persons.csv":
      # add HHID
      table_hh["HHID"] = table_hh.unique_hh_id
      table_gq["HHID"] = table_gq.unique_hh_id + max_hhid
      table_hh["PERID"] = table_hh.index + 1 # start from 1
      max_perid = table_hh.PERID.max()
      print "Max housing record PERID: %d" % max_perid
      table_gq["PERID"] = table_gq.index + 1 + max_perid # start from max_perid + 1

    elif filename=="summary_melt.csv":
      # just add a column for type
      table_hh["type"] = "households"
      table_gq["type"] = "group_quarters"

    concat_table = pandas.concat([table_hh, table_gq])
    concat_table.fillna(value=-9, inplace=True)

    # downcast the floats that don't need to be floats
    import create_seed_population
    create_seed_population.clean_types(concat_table)

    if filename=="synthetic_households.csv":
      # fix the columns up
      pass
    elif filename=="synthetic_persons.csv":
      # fix the columns up
      pass
    elif filename=="summary_melt.csv":
      # perfect
      pass

    print concat_table.head()
    print concat_table.tail()
    outfile = os.path.join(COMBINED_OUT_DIR, filename)
    concat_table.to_csv(outfile, header=True, index=False)
    print "Wrote %s" % outfile

