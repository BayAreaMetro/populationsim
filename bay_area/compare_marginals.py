USAGE = """

 Compare two sets of marginals and create long form combined version for Tableau visualization.

"""

import argparse, os, sys
import numpy, pandas

if __name__ == '__main__':

    pandas.options.display.width    = 180
    pandas.options.display.max_rows = 1000

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=USAGE)
    parser.add_argument("--model_type", choices=['TM1','TM2'],   help="Model type - one of TM1 or TM2")
    parser.add_argument("--geography",  choices=['MAZ','TAZ'],   help="Geography - one of MAZ, TAZ")
    parser.add_argument("file1",        help="Marginal file 1")
    parser.add_argument("version1",     help="Version label for file 1")
    parser.add_argument("file2",        help="Marginal file 2")
    parser.add_argument("version2",     help="Version label for file 2")
    parser.add_argument("--file2b",     help="Marginal file 2")
    args = parser.parse_args()

    print(args)
    if args.model_type == 'TM1':
        print("Not supported")

    CROSSWALK_FILE = "X:\\populationsim\\bay_area\\hh_gq\\data\\geo_cross_walk_tm2.csv"
    crosswalk_df   = pandas.read_csv(CROSSWALK_FILE)
    print("Read {} head:\n{}".format(CROSSWALK_FILE, crosswalk_df.head()))

    if args.geography=="TAZ":
        # remove maz and dedupe
        crosswalk_df.drop("MAZ", axis="columns", inplace=True)
        crosswalk_df.drop_duplicates(inplace=True)
        print("Dropped MAZ from crosswalk_df; length is now {}; head:\n{}".format(len(crosswalk_df), crosswalk_df.head()))

    marginals1_df = pandas.read_csv(args.file1)
    print("Read {} columns:{} head:\n{}".format(args.file1, marginals1_df.columns, marginals1_df.head()))
    marginals2_df = pandas.read_csv(args.file2)
    print("Read {} columns: {} head:\n{}".format(args.file2, marginals2_df.columns, marginals2_df.head()))

    if args.file2b:
        marginals2b_df = pandas.read_csv(args.file2b)
        print("Read {} head:\n{}".format(args.file2b, marginals2b_df.head()))

        marginals2_df = pandas.merge(left=marginals2_df, right=marginals2b_df, how='left', on=args.geography)
        print("marginals2_df head:\n{}".format(marginals2_df.head()))

    if args.geography == "MAZ":
        marginal_groups = {
            'hh_size':['hh_size_1','hh_size_2','hh_size_3','hh_size_4_plus'],
            'gq_type':['gq_type_univ','gq_type_mil','gq_type_othnon']
        }
    else:
        marginal_groups = {
            'hh_inc'  :['hh_inc_30','hh_inc_30_60','hh_inc_60_100','hh_inc_100_plus'],
            'hh_wrks' :['hh_wrks_0','hh_wrks_1','hh_wrks_2','hh_wrks_3_plus'],
            'pers_age':['pers_age_00_19','pers_age_20_34','pers_age_35_64','pers_age_65_plus'],
            'hh_kids' :['hh_kids_no','hh_kids_yes']
        }    

    # create mapping of marginal -> group plus list of marginals
    marg_to_group = {}
    marginals = []
    for marginal_group in marginal_groups.keys():
        marginals = marginals + marginal_groups[marginal_group]
        for m in marginal_groups[marginal_group]:
            marg_to_group[m] = marginal_group
    print(marginals)
    print(marg_to_group)

    # columns: MAZ, version, marginal group (e.g. hh_size), marginal (e.g. hh_size_1), value
    marginals1_df = marginals1_df[[args.geography] + marginals]
    marginals1_df['version'] = args.version1
    print(marginals1_df.head())

    marginals2_df = marginals2_df[[args.geography] + marginals]
    marginals2_df['version'] = args.version2
    print(marginals2_df.head())

    # put them together
    marginals_df = pandas.concat([marginals1_df, marginals2_df], axis='index')
    print("marginals_df head:\n{}\ntail:\n{}".format(marginals_df.head(),marginals_df.tail()))

    # melt it
    marginals_long_df = pandas.melt(marginals_df, id_vars=[args.geography, 'version'], var_name='marginal')
    marginals_long_df['marginal group'] = marginals_long_df['marginal'].replace(to_replace=marg_to_group)
    print("marginals_long_df.head():\n{}".format(marginals_long_df.head()))

    # add more geography info
    marginals_long_df = pandas.merge(left=marginals_long_df, right=crosswalk_df, how="left", on=args.geography)
    print("marginals_long_df.head():\n{}".format(marginals_long_df.head()))

    # write it
    OUTPUT_FILE = "compare_marginals_{}_{}_vs_{}.csv".format(args.geography, args.version1, args.version2)
    marginals_long_df.to_csv(OUTPUT_FILE, index=False)
    print("Wrote {}".format(OUTPUT_FILE))