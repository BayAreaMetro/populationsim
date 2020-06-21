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
    args = parser.parse_args()

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


    # Problem 1: GQPOP, gq_tot_pop and TOTPOP inconsistency
    # this results in an unreasonably high pop per hh in one zone (in Draft Blueprint Plus Crossing run): TAZ1272 which is "State Medical", a prison
    # GQPOP = 10941
    # gq_type_univ = 0
    # gq_type_mil  = 0
    # gq_type_othnon = 0
    # gq_tot_pop = gq_type_univ +  gq_type_mil  + gq_type_othnon = 0
    # TOTHH = 1
    # TOTPOP = 10941
    # numhh_gq = TOTHH + gq_tot_pop =  1
    # So, TOTPOP / numhh_gq  = unreasonable

    # since we know it's a prison, some specific fixes
    # since the residents don't travel, adjust both numhh_gq and totpop to 0 for this zone
    # (other prison population seems to be treated differently... to be discussed)
    taz_controls_df['numhh_gq']   = numpy.where(taz_controls_df['TAZ']==1272, 0, taz_controls_df["numhh_gq"])
    taz_controls_df['totpop_adj'] = numpy.where(taz_controls_df['TAZ']==1272, 0, taz_controls_df["TOTPOP"])

    # Problem 2: there are more households than people in some zones
    # where households > population, let household numbers take precedence and adjust total population (assume 2 persons per hh)
    taz_controls_df['totpop_adj']  = numpy.where(taz_controls_df['numhh_gq'] > taz_controls_df['TOTPOP'], taz_controls_df['numhh_gq'] * 2, taz_controls_df['TOTPOP'])
    taz_controls_df['AGE0004_adj'] = numpy.where(taz_controls_df['numhh_gq'] > taz_controls_df['TOTPOP'], numpy.where(taz_controls_df['TOTPOP'] > 0, taz_controls_df['AGE0004'] * taz_controls_df['totpop_adj'] / taz_controls_df['TOTPOP'], taz_controls_df['totpop_adj']/5), taz_controls_df['AGE0004'])
    taz_controls_df['AGE0519_adj'] = numpy.where(taz_controls_df['numhh_gq'] > taz_controls_df['TOTPOP'], numpy.where(taz_controls_df['TOTPOP'] > 0, taz_controls_df['AGE0519'] * taz_controls_df['totpop_adj'] / taz_controls_df['TOTPOP'], taz_controls_df['totpop_adj']/5), taz_controls_df['AGE0519'])
    taz_controls_df['AGE2044_adj'] = numpy.where(taz_controls_df['numhh_gq'] > taz_controls_df['TOTPOP'], numpy.where(taz_controls_df['TOTPOP'] > 0, taz_controls_df['AGE2044'] * taz_controls_df['totpop_adj'] / taz_controls_df['TOTPOP'], taz_controls_df['totpop_adj']/5), taz_controls_df['AGE2044'])
    taz_controls_df['AGE4564_adj'] = numpy.where(taz_controls_df['numhh_gq'] > taz_controls_df['TOTPOP'], numpy.where(taz_controls_df['TOTPOP'] > 0, taz_controls_df['AGE4564'] * taz_controls_df['totpop_adj'] / taz_controls_df['TOTPOP'], taz_controls_df['totpop_adj']/5), taz_controls_df['AGE4564'])
    taz_controls_df['AGE65P_adj']  = numpy.where(taz_controls_df['numhh_gq'] > taz_controls_df['TOTPOP'], numpy.where(taz_controls_df['TOTPOP'] > 0, taz_controls_df['AGE65P']  * taz_controls_df['totpop_adj'] / taz_controls_df['TOTPOP'], taz_controls_df['totpop_adj']/5), taz_controls_df['AGE65P'])

    # Problem 3: there are people but no household
    # If non-zero totpop but 0 household, let household numbers take precedence and set totpop to 0.
    taz_controls_df['totpop_adj']  = numpy.where(taz_controls_df["numhh_gq"]==0, 0, taz_controls_df['totpop_adj'])
    taz_controls_df['AGE0004_adj'] = numpy.where(taz_controls_df["numhh_gq"]==0, 0, taz_controls_df['AGE0004_adj'])
    taz_controls_df['AGE0519_adj'] = numpy.where(taz_controls_df["numhh_gq"]==0, 0, taz_controls_df['AGE0519_adj'])
    taz_controls_df['AGE2044_adj'] = numpy.where(taz_controls_df["numhh_gq"]==0, 0, taz_controls_df['AGE2044_adj'])
    taz_controls_df['AGE4564_adj'] = numpy.where(taz_controls_df["numhh_gq"]==0, 0, taz_controls_df['AGE4564_adj'])
    taz_controls_df['AGE65P_adj']  = numpy.where(taz_controls_df["numhh_gq"]==0, 0, taz_controls_df['AGE65P_adj'])



    taz_controls_output = os.path.join("hh_gq", "data", "{}_TAZ_summaries_{}_hhgq.csv".format(args.run_num, args.model_year))
    taz_controls_df.to_csv(taz_controls_output, index=False)
    print("Wrote {}".format(taz_controls_output))
