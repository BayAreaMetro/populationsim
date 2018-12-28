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
#USERPROFILE = os.environ["USERPROFILE"]
#os.chdir = os.path.join(USERPROFILE,"Documents","GitHub","populationsim","bay_area")   

# household HHID,TAZ,HINC,hworkers,PERSONS,HHT,VEHICL,hinccat1
# persons   HHID,PERID,AGE,SEX,pemploy,pstudent,ptype 

#TAZ_DATA_CSV  = os.path.join("X:", "Petrale", "Output", "TAZ1454 2015 Land Use.csv")
TAZ_DATA_CSV  = "tazData.csv"
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
    ("person_num",  [  0,  1]),     # Person number
    ("AGE",         [ 36, 37]),     # 36,37 years old
    ("SEX",         [  1,  1]),     # Male :p
    ("pemploy",     [  1,  2]),     # Full- and part-time employee
    ("pstudent",    [  3,  3]),     # Not attending school
    ("ptype",       [  1,  2])      # Person type, full- and part-time worker
])

individualTours = collections.OrderedDict([
    ("person_num",          [ 0,            1]),                            # person number
    ("tour_id",             [ 0,            0]),                            # Tour ID     
    ("tour_id",             [ 0,            0]),                            # Tour ID     
    ("tour_category",       ["MANDATORY",   "INDIVIDUAL_NON_MANDATORY"]),   # Category   
    ("tour_purpose",        ["work",        "shopping"]),                   # purpose     
    ("dest_taz",            [0,             0]),                            # destination unknown 
    ("dest_walk_segment",   [0,             0]),                            # destination unknown 
    ("start_hour",          [0,             0]),                            # start hour unknown           
    ("end_hour",            [0,             0]),                            # end hour unknown 
    ("tour_mode",           [0,             0]),                            # tour mode unknown 
    ("atWork_freq",         [0,             0]),                            # no at-work subtours
    ("num_ob_stops",        [0,             0]),                            # no outbound stops
    ("num_ib_stops",        [0,             0]),                            # no inbound stops
    ("avAvailable",         [0,             0])                             # no AVs available?        
])

def replicate_df_for_variable(hh_df, var_name, var_values):
    """
    Duplicate the given hh_df for the given variable with the given values and return.
    """
    new_var_df = pandas.DataFrame({var_name: var_values})
    new_var_df["join_key"] = 1
    hh_df["join_key"]      = 1

    ret_hh_df = pandas.merge(left=hh_df, right=new_var_df, how="outer").drop(columns=["join_key"])
    return ret_hh_df

if __name__ == '__main__':
    pandas.options.display.width    = 180
    pandas.options.display.max_rows = 100

    taz_data_df = pandas.read_csv(TAZ_DATA_CSV)
    print("Read {} rows of {}".format(len(taz_data_df), TAZ_DATA_CSV))
    
    # print(taz_data_df.head())
    taz_list = sorted(taz_data_df["ZONE"].tolist())

    #############################################################################################################
    # create the base household df
    #############################################################################################################
    household_df = pandas.DataFrame.from_dict(household)
    household_df = replicate_df_for_variable(household_df, "ZONE", taz_list)
    household_df = replicate_df_for_variable(household_df, "VEHICL",  [0,1,2])
    household_df = replicate_df_for_variable(household_df, "AV_AVAIL",[0,1])
    household_df = household_df[((household_df.AV_AVAIL==0) & (household_df.VEHICL==0))|(household_df.VEHICL>0)]
    household_df = household_df.sort_values(by=["ZONE","hinccat1","VEHICL","AV_AVAIL"])
    household_df = household_df.reset_index(drop=True)
    household_df["HHID"] = household_df.index + 1

    # rename ZONE to TAZ
    household_df.rename(columns={"ZONE":"TAZ"}, inplace=True)
    
    # reorder columns
    household_df = household_df[["HHID","TAZ","HINC","hworkers","PERSONS","HHT","VEHICL","hinccat1","AV_AVAIL"]]
    
    # print(household_df.head(10))
    outfile = "{}_households.csv".format(OUTPUT_PREFIX)
    household_df.to_csv(outfile, index=False)
    print("Wrote {} lines to {}".format(len(household_df), outfile))
    
    #############################################################################################################
    # create model output household file from input household file dataframe
    #############################################################################################################
    household_model_df = household_df.copy()
    household_model_df = household_model_df.drop(columns=["HHT","hinccat1"])
    household_model_df = household_model_df.rename({"HHID": "hh_id", "TAZ": "taz","HINC":"income","PERSONS":"size","hworkers":"workers","VEHICL":"autos","AV_AVAIL":"autonomousVehicles"}, axis="columns")
    household_model_df["walk_subzone"] = 1
    household_model_df["cdap_pattern"] = "MN"
    household_model_df["jtf_pattern"] = "0_tours"
    household_model_df["humanVehicles"] = household_model_df["autos"] - household_model_df["autonomousVehicles"]
    outfile = "{}_model_households.csv".format(OUTPUT_PREFIX)
    household_model_df.to_csv(outfile, index=False)
    print("Wrote {} lines to {}".format(len(household_model_df), outfile))

    #############################################################################################################
    # create persons by duplicating for households
    #############################################################################################################
    persons_df   = pandas.DataFrame.from_dict(persons)
    persons_df["join_key"]    = 1
    household_df["join_key"] = 1
    persons_df = pandas.merge(left=persons_df, right=household_df[["HHID","join_key","HINC"]], how="outer").drop(columns=["join_key"])
    persons_df["value_of_time"] = persons_df["HINC"]/2080 * 0.5
    
    # sort by household ID then person ID
    persons_df = persons_df[["HHID","person_num","AGE","SEX","pemploy","pstudent","ptype","value_of_time"]].sort_values(["HHID","person_num"]).reset_index(drop=True)
    persons_df["PERID"] = persons_df.index + 1
    
    # print(persons_df.head(20))
    outfile = "{}_persons.csv".format(OUTPUT_PREFIX)
    persons_df.to_csv(outfile, index=False)
    print("Wrote {} lines to {}".format(len(persons_df), outfile))
    
    #############################################################################################################
    # create model output person file from input person file dataframe
    #############################################################################################################
    persons_model_df = persons_df.copy()
    persons_model_df = persons_model_df.rename(columns={"HHID":"hh_id","PERID":"person_id","AGE":"age","SEX":"gender","ptype":"type"})
    
    # convert gender to text
    genderDict = {1: "m", 2: "f"}
    persons_model_df = persons_model_df.replace({"gender": genderDict})    
    
    # convert person type to text
    typeDict = {1:"Full-time worker",2:"Part-time worker",3:"University student",4:"Non-worker",5:"Retired",6:"Student of driving age",
        7:"Student of non-driving age",8:"Child too young for school"}
    persons_model_df = persons_model_df.replace({"type": typeDict})    

    # set up model choices for person based on person number (0 is FT worker with work activity, 1 is PT worker with non-mandatory activity)
    persons_model_df["activity_pattern"] = "M"
    persons_model_df.loc[persons_model_df.person_num==1, "activity_pattern"] = "N"
    persons_model_df["imf_choice"] = 1
    persons_model_df.loc[persons_model_df.person_num==1, "imf_choice"] = 0
    persons_model_df["inmf_choice"] = 1
    persons_model_df.loc[persons_model_df.person_num==0, "inmf_choice"] = 0
  
    # print
    outfile = "{}_model_persons.csv".format(OUTPUT_PREFIX)
    persons_model_df.to_csv(outfile, index=False)
    print("Wrote {} lines to {}".format(len(persons_model_df), outfile))

    #############################################################################################################
    # create individual tours
    #############################################################################################################
    individualTours_df = pandas.DataFrame.from_dict(individualTours)

    # duplicate for all persons
    perid_list = sorted(persons_df["PERID"].tolist())
    individualTours_df = replicate_df_for_variable(individualTours_df, "PERID", perid_list)

    # merge person file
    individualTours_df = pandas.merge(left=individualTours_df, right=persons_df, on="PERID", how="outer").drop(columns=["person_num_y"])
    individualTours_df = individualTours_df.rename(columns={"HHID_x":"HHID","person_num_x":"person_num"})
    
    # keep mandatory tours for FT workers and non-mandatory tours for PT workers
    individualTours_df = individualTours_df[((individualTours_df.pemploy==1) & (individualTours_df.tour_category=="MANDATORY"))|
        ((individualTours_df.pemploy==2) & (individualTours_df.tour_category=="INDIVIDUAL_NON_MANDATORY"))]
    
    # merge household file so that we can set origin zone
    individualTours_df = pandas.merge(left=individualTours_df, right=household_df, on="HHID",how="outer")
    print individualTours_df.columns
    individualTours_df["orig_taz"] = individualTours_df["TAZ"]
    individualTours_df["orig_walk_segment"] = 0
    individualTours_df["avAvailable"] = individualTours_df["AV_AVAIL"]
    
    # drop household and person variable fields
    individualTours_df = individualTours_df.drop(columns=["join_key","AGE","SEX","pemploy","pstudent","TAZ","HINC","hworkers","PERSONS","HHT","hinccat1"])
    individualTours_df = individualTours_df.rename(columns={"HHID":"hh_id","ptype":"person_type","PERID":"person_id"})
    individualTours_df = individualTours_df.sort_values(by=["person_id"])
    
    # reorder columns
    individualTours_df = individualTours_df[["hh_id","person_id","person_num","person_type","tour_id","tour_category",
        "tour_purpose","orig_taz","orig_walk_segment","dest_taz","dest_walk_segment","start_hour","end_hour","tour_mode","atWork_freq","num_ob_stops","num_ib_stops",      
        "avAvailable"]]

    
    outfile = "{}_indivTours.csv".format(OUTPUT_PREFIX)
    individualTours_df.to_csv(outfile, index=False)
    print("Wrote {} lines to {}".format(len(individualTours_df), outfile))
