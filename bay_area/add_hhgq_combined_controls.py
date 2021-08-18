USAGE=r"""
Modify controls slightly for populationsim.

Mostly, this amounts to making group quarters into one-person households.
"""

import argparse, os, sys
import numpy, pandas

if __name__ == '__main__':
    pandas.options.display.width    = 180
    pandas.options.display.max_rows = 1000

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=USAGE)
    parser.add_argument("--run_num",    type=str, required=True, help="Control file prefix")
    parser.add_argument("--model_year", type=int, required=True, help="Model year")
    parser.add_argument("--model_type", choices=['TM1','TM2'],   help="Model type - one of TM1 or TM2")
    args = parser.parse_args()

    if args.model_type == 'TM1':
        # control files are: 
        #  - [run_num]_taz_summaries_[year].csv
        taz_controls_file = os.path.join("hh_gq", "data", "{}_TAZ_summaries_{}.csv".format(args.run_num, args.model_year))
        taz_controls_df   = pandas.read_csv(taz_controls_file)
        print("Read {} controls from {}".format(len(taz_controls_df), taz_controls_file))
        print(taz_controls_df.head())

        # total households: combine actual tothh + gq_tot_pop
        taz_controls_df["numhh_gq"] = taz_controls_df.TOTHH + taz_controls_df.gq_tot_pop
        # GQ are 1-person households
        taz_controls_df["hh_size_1_gq"] = taz_controls_df.hh_size_1 + taz_controls_df.gq_tot_pop

        # note that hh_wrks and hh_inc categories specify households.TYPE==1 so no need to modify those

        taz_controls_output = os.path.join("hh_gq", "data", "{}_TAZ_summaries_{}_hhgq.csv".format(args.run_num, args.model_year))
        taz_controls_df.to_csv(taz_controls_output, index=False)
        print("Wrote {}".format(taz_controls_output))

    elif args.model_type == 'TM2':
        maz_controls_file = os.path.join("hh_gq", "data", "{}_maz_marginals_{}.csv".format(args.run_num, args.model_year))
        maz_controls_df   = pandas.read_csv(maz_controls_file)
        print("Read {} controls from {}".format(len(maz_controls_df), maz_controls_file))
        print(maz_controls_df.head())

        # total households: combine actual tothh + gq_tot_pop
        maz_controls_df["numhh_gq"] = maz_controls_df.num_hh + maz_controls_df.gq_num_hh
        # GQ are 1-person households
        maz_controls_df["hh_size_1_gq"] = maz_controls_df.hh_size_1 + maz_controls_df.gq_num_hh

        # note that hh_wrks and hh_inc categories specify households.TYPE==1 so no need to modify those

        maz_controls_output = os.path.join("hh_gq", "data", "{}_maz_marginals_{}_hhgq.csv".format(args.run_num, args.model_year))
        maz_controls_df.to_csv(maz_controls_output, index=False)
        print("Wrote {}".format(maz_controls_output))
