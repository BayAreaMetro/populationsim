USAGE="""

Creates dummy population (household and persons file) for the purpose of generating accessiblities logsums
from Travel Model 1.5.

See also https://app.asana.com/0/13098083395690/928542858211542/f

For each TAZ, income category (x4) and vehicle category (x3), the script creates a 2-person household,
including 1 full time worker and 1 part time worker.  See below for attributes.

"""

import collections, os
import pandas

# Set the working directory
USERPROFILE = os.environ["USERPROFILE"]
os.chdir = os.path.join(USERPROFILE,"Documents","GitHub","populationsim","bay_area")   

# household HHID,TAZ,HINC,hworkers,PERSONS,HHT,VEHICL,hinccat1
# persons   HHID,PERID,AGE,SEX,pemploy,pstudent,ptype 

TAZ_DATA_CSV  = os.path.join("X:", "Petrale", "Output", "TAZ1454 2015 Land Use.csv")
OUTPUT_PREFIX = "accessibilities_dummy"

# median of weighted seed_households hh_income_2000; see populationsim\bay_area\households\data\helpful_seed_viewer.twb
#    12878  hh_inc_30
#    35282  hh_inc_30_60
#    61799  hh_inc_60_100
#   122820  hh_inc_100_plus

# https://github.com/BayAreaMetro/modeling-website/wiki/PopSynHousehold
household = collections.OrderedDict([
    ("HINC",       [ 12878, 35282, 61799, 122820]),                     # Median income within each quartile
    ("hworkers",   [ 2,         2,      2,     2]),                     # Two workers
    ("PERSONS",    [ 2,         2,      2,     2]),                     # Two persons
    ("HHT",        [ 1,         1,      1,     1]),                     # Married-couple family household
    ("hinccat1",   [ 1,         2,      3,     4])                      # Income categories
])

# https://github.com/BayAreaMetro/modeling-website/wiki/PopSynPerson
persons = collections.OrderedDict([
    ("PERID",       [  1,  2]),     # Person ID
    ("AGE",         [ 36, 37]),     # 36,37 years old
    ("SEX",         [  1,  1]),     # Male :p
    ("pemploy",     [  1,  2]),     # Full- and part-time employee
    ("pstudent",    [  3,  3]),     # Not attending school
    ("ptype",       [  1,  2]),     # Person type, full- and part-time worker
])


def replicate_df_for_variable(hh_df, var_name, var_values):
    """
    Duplicate the given hh_df for the given variable with the given values and return.
    """
    new_var_df = pandas.DataFrame({var_name: var_values})
    new_var_df["join_key"] = 1
    hh_df["join_key"]      = 1

    ret_hh_df = pandas.merge(left=hh_df, right=new_var_df, how="outer").drop(columns=["join_key"])
    ret_hh_df["HHID"] = ret_hh_df.index + 1
    return ret_hh_df

if __name__ == '__main__':
    pandas.options.display.width    = 180
    pandas.options.display.max_rows = 100

    taz_data_df = pandas.read_csv(TAZ_DATA_CSV)
    print("Read {} rows of {}".format(len(taz_data_df), TAZ_DATA_CSV))
    
    # print(taz_data_df.head())
    taz_list = sorted(taz_data_df["ZONE"].tolist())

    # create the base household df
    household_df = pandas.DataFrame.from_dict(household)
    household_df = replicate_df_for_variable(household_df, "ZONE", taz_list)
    household_df = replicate_df_for_variable(household_df, "VEHICL",  [0,1,2])

    # rename ZONE to TAZ
    household_df.rename(columns={"ZONE":"TAZ"}, inplace=True)
    
    # reorder columns
    household_df = household_df[["HHID","TAZ","HINC","hworkers","PERSONS","HHT","VEHICL","hinccat1"]]
    
    # print(household_df.head(10))
    outfile = "{}_households.csv".format(OUTPUT_PREFIX)
    household_df.to_csv(outfile, index=False)
    print("Wrote {} lines to {}".format(len(household_df), outfile))

    # create persons by duplicating for households
    persons_df   = pandas.DataFrame.from_dict(persons)
    persons_df["join_key"]    = 1
    household_df["join_key"] = 1
    persons_df = pandas.merge(left=persons_df, right=household_df[["HHID","join_key"]], how="outer").drop(columns=["join_key"])
    
    # sort by household ID then person ID
    persons_df = persons_df[["HHID","PERID","AGE","SEX","pemploy","pstudent","ptype"]].sort_values(["HHID","PERID"]).reset_index(drop=True)
    persons_df["PERID"] = persons_df.index + 1
    
    # print(persons_df.head(20))
    outfile = "{}_persons.csv".format(OUTPUT_PREFIX)
    persons_df.to_csv(outfile, index=False)
    print("Wrote {} lines to {}".format(len(persons_df), outfile))