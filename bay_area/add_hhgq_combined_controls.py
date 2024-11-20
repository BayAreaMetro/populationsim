USAGE=r"""
Modify controls slightly for populationsim.

Mostly, this amounts to making group quarters into one-person households.

For TM1: 
  Input:  hh_gq/data/taz_summaries.csv
  Output: hh_gq/data/taz_summaries_hhgq.csv

For TM2:
  Input:  hh_gq/data/maz_marginals.csv
  Output: hh_gq/data/maz_marginals_hhgq.csv

"""

import argparse, pathlib, sys
import numpy, pandas

if __name__ == '__main__':
    pandas.options.display.width    = 180
    pandas.options.display.max_rows = 1000

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=USAGE)
    parser.add_argument("--model_type", choices=['TM1','TM2'],   help="Model type - one of TM1 or TM2")
    args = parser.parse_args()

    if args.model_type == 'TM1':
        # control files are: 
        #  - [run_num]_taz_summaries_[year].csv
        taz_controls_file = pathlib.Path("hh_gq/data/taz_summaries.csv")
        taz_controls_df   = pandas.read_csv(taz_controls_file)
        print("Read {} controls from {}".format(len(taz_controls_df), taz_controls_file))

        # lowercase these fields
        field_list = ['hh_size_1','hh_size_2','hh_size_3','hh_size_4_plus',
          'hh_wrks_0','hh_wrks_1','hh_wrks_2','hh_wrks_3_plus',
          'gq_type_univ','gq_type_mil','gq_type_othnon','gq_tot_pop'
        ]
        rename_dict = { field.upper():field for field in field_list }
        taz_controls_df.rename(columns=rename_dict, inplace=True)
        print(taz_controls_df.dtypes)

        # total households: combine actual tothh + gq_tot_pop
        taz_controls_df["numhh_gq"] = taz_controls_df.TOTHH + taz_controls_df.gq_tot_pop
        # GQ are 1-person households
        taz_controls_df["hh_size_1_gq"] = taz_controls_df.hh_size_1 + taz_controls_df.gq_tot_pop

        # note that hh_wrks and hh_inc categories specify households.TYPE==1 so no need to modify those

        taz_controls_output = pathlib.Path("hh_gq/data/taz_summaries_hhgq.csv")
        taz_controls_df.to_csv(taz_controls_output, index=False)
        print("Wrote {}".format(taz_controls_output))

        # small update to county controls file
        county_controls_file = pathlib.Path("hh_gq/data/county_marginals.csv")
        county_controls_df   = pandas.read_csv(county_controls_file, index_col=0)
        print(f"Read county controls from {county_controls_file}")
        # print(county_controls_df)
        # for base years, COUNTY is present. for BAUS, county_name is present
        county_col = 'county_name'
        if county_controls_df.index.name == 'COUNTY':
            county_col = 'COUNTY'

        # add COUNTY or county_name depending on which is mmissing
        geo_crosswalk_file = pathlib.Path("hh_gq/data/geo_cross_walk_tm1.csv")
        geo_crosswalk_df   = pandas.read_csv(geo_crosswalk_file)
        geo_crosswalk_df = geo_crosswalk_df[['COUNTY','county_name']].drop_duplicates().reset_index(drop=True)
        # print(geo_crosswalk_df)

        county_controls_df = pandas.merge(
          left = county_controls_df,
          right = geo_crosswalk_df,
          left_index = True,
          right_on = county_col,
          how = 'left'
        )
        # how it has columns, COUNTY and county_name
        print(county_controls_df)
        county_controls_df.to_csv(county_controls_file, index=False)
        print(f"Wrote {county_controls_file}")

    elif args.model_type == 'TM2':
        maz_controls_file = pathlib.Path("hh_gq/data/maz_marginals.csv")
        maz_controls_df   = pandas.read_csv(maz_controls_file)
        print("Read {} controls from {}".format(len(maz_controls_df), maz_controls_file))
        print(maz_controls_df.head())

        # total households: combine actual tothh + gq_tot_pop
        maz_controls_df["numhh_gq"] = maz_controls_df.num_hh + maz_controls_df.gq_num_hh
        # GQ are 1-person households
        maz_controls_df["hh_size_1_gq"] = maz_controls_df.hh_size_1 + maz_controls_df.gq_num_hh

        # note that hh_wrks and hh_inc categories specify households.TYPE==1 so no need to modify those

        maz_controls_output = pathlib.Path("hh_gq/data/maz_marginals_hhgq.csv")
        maz_controls_df.to_csv(maz_controls_output, index=False)
        print("Wrote {}".format(maz_controls_output))
