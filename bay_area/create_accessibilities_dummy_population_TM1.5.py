USAGE="""

Creates dummy population (household and persons file) for the purpose of generating accessiblities logsums
from Travel Model 1.5.

See also https://app.asana.com/0/13098083395690/928542858211542/f

For each TAZ, income category (x4) and vehicle category (x3), the script creates a 2-person household,
including 1 full time worker and 1 part time worker.  See below for attributes.

"""

import collections, os, sys
import numpy, pandas

# household HHID,TAZ,MAZ,MTCCountyID,HHINCADJ,NWRKRS_ESR,VEH,NP,HHT,BLD,TYPE
# persons   HHID,PERID,AGEP,SEX,SCHL,OCCP,WKHP,WKW,EMPLOYED,ESR,SCHG

TM2_BOX       = os.path.join(os.environ["USERPROFILE"], "Box", "Modeling and Surveys", "Development", "Travel Model Two Development")
MAZ_DATA_CSV  = os.path.join(TM2_BOX, "Model Inputs", "2015_revised_mazs", "landuse", "maz_data.csv")
OUTPUT_PREFIX = "accessibilities_dummy"

# https://github.com/BayAreaMetro/modeling-website/wiki/PopSynHousehold
household = collections.OrderedDict([
    ("NWRKRS_ESR",  [2]), # two workers
    ("NP",          [2]), # two persons
    ("HHT",         [1]), # Married-couple family household
    ("BLD",         [2]), # One-family house detached
    ("TYPE",        [1])  # Housing unit (household)
])

persons = collections.OrderedDict([
    ("PERID",     [  1,  2]), # to be updated
    ("AGEP",      [ 36, 37]), # 36,37 years old
    ("SEX",       [  1,  1]), # male :p
    ("SCHL",      [ 13, 12]), # Bachelor's degree, Associate's degree
    ("OCCP",      [  3,  3]), # Services
    ("WKHP",      [ 40, 20]), # 40 hours worked per week, 20 hours per week
    ("WKW",       [  1,  1]), # 50-52 weeks worked during the past 12 months
    ("EMPLOYED",  [  1,  1]), # yes
    ("ESR",       [  1,  1]), # Civilian employed, at work
    ("SCHG",      [ -9, -9])  # not attending school
])

# median of weighted seed_households hh_income_2010; see seed_viewer.twb
median_hh_income_2010 = [
    16255, # hh_inc_30
    44560, # hh_inc_30_60
    78024, # hh_inc_60_100
    155227 # hh_inc_100_plus
]

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

    maz_data_df = pandas.read_csv(MAZ_DATA_CSV)
    print("Read {} rows of {}".format(len(maz_data_df), MAZ_DATA_CSV))
    # print(maz_data_df.head())
    maz_list = sorted(maz_data_df["MAZ_ORIGINAL"].tolist())

    # create the base household df
    household_df = pandas.DataFrame.from_dict(household)
    household_df = replicate_df_for_variable(household_df, "MAZ", maz_list)
    household_df = replicate_df_for_variable(household_df, "VEH",      [0,1,2])
    household_df = replicate_df_for_variable(household_df, "HHINCADJ", median_hh_income_2010)

    # join to maz_data to pick up TAZ, MTCCountyID
    household_df = pandas.merge(left=household_df, right=maz_data_df[["MAZ_ORIGINAL","TAZ_ORIGINAL","CountyID"]], how="left",
                                left_on="MAZ", right_on="MAZ_ORIGINAL")
    household_df.rename(columns={"TAZ_ORIGINAL":"TAZ", "CountyID":"MTCCountyID"}, inplace=True)
    household_df.drop(columns="MAZ_ORIGINAL", inplace=True)
    # reorder columns
    household_df = household_df[["HHID","TAZ","MAZ","MTCCountyID","HHINCADJ","NWRKRS_ESR","VEH","NP","HHT","BLD","TYPE"]]
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
    persons_df = persons_df[["HHID","PERID","AGEP","SEX","SCHL","OCCP","WKHP","WKW","EMPLOYED","ESR","SCHG"]].sort_values(["HHID","PERID"]).reset_index(drop=True)
    persons_df["PERID"] = persons_df.index + 1
    # print(persons_df.head(20))
    outfile = "{}_persons.csv".format(OUTPUT_PREFIX)
    persons_df.to_csv(outfile, index=False)
    print("Wrote {} lines to {}".format(len(persons_df), outfile))