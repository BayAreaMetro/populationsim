"""
Create seed files for MTC Bay Area populationsim from PUMS 2017-2021.

Columns used:
- PUMA (housing and person), to filter to bay area for housing and person records
- ESR (person), Employment Status Recode, to count workers per housing record
- SERIALNO (hh and person), to group persons to housing record, to count workers per housing record
- ADJINC and HINCP (hh), used to adjust household income to 2010 dollars
- NP (housing), to filter out vacant unitsf
- TYPEHUGQ (housing), to filter to households and non-institutional group quarters
- MIL (person), to inform gqtype for group quarters persons
- SCHG (person), to inform gqtype for group quarters persons

New columns in housing records file:
- hh_workers_from_esr: count of employed persons in household
- hh_income_2021     : household income in 2010 dollars, based on HINCP and ADJINC
- unique_hh_id       : integer unique id for housing unit, starting with 1
- hhgqtype           : 0 for non gq, 1 is college student, 2 is military, 3 is other
- PWGT               : for group quarters file only, transfered from person records
New columns in person records file:
- employed           : 0 or 1, based on ESR
- soc                : 2 digit code, based on first two characters of SOCP
- occupation         : 0, 1, 2, 3, 4, 5, 6, based on soc
- WGTP               : from housing record
- unique_hh_id       : from housing record
- gqtype             : f0 is not group quarters, 1 is college student, 2 is military, 3 is other
"""
# pums housing unit columns to keep
PUMS_HOUSING_RECORD_COLUMNS = [
    "RT",                   # Record Type, 'H', or 'P'
    "SERIALNO",             # Housing unit/GQ person serial number; string
    "DIVISION",             # Division code based on 2010 Census definitions
    "PUMA",                 # Public use microdata area code based on 2010 Census definition
    "REGION",               # Region code
    "ST",                   # State code
    "ADJINC",               # Adjustment factor for income and earnings dollar amounts
    "WGTP",                 # Housing unit weight
    "NP",                   # Number of person records associated with this housing record
    "TYPEHUGQ",             # Type of unit
    "BLD",                  # Units in structure
    "HHT",                  # Household/family type (Note: there's also HHT2)
    "HINCP",                # Household income (past 12 months, use ADJINC to adjust HINCP to constant dollars))
    "HUPAC",                # HH presence and age of children
    "NPF",                  # Number of persons in family (unweighted)
    "TEN",                  # Tenure
    "VEH",                  # Vehicles (1 ton or less) available
]
# columns added by this script
NEW_HOUSING_RECORD_COLUMNS = [
    "COUNTY",               # MTC county code
    "hh_workers_from_esr",  # count of employed persons in household
    "hh_income_2010",       # household income in 2010 dollars, based on HINCP and ADJINC
    "unique_hh_id",         # integer unique id for housing unit, starting with 1
    "gqtype",               # group quarters type: 0: household (not gq), 1 college, 2 military, 3 other
    "hh_income_2000",       # household income in 2000 dollars for tm1
]

# pums person record columns to keep
PUMS_PERSON_RECORD_COLUMNS = [
    "RT",                   # Record Type
    "SERIALNO",             # Housing unit/GQ person serial number
    "SPORDER",              # Person number
    "PUMA",                 # Public use microdata area code based on 2010 Census definition
    "ST",                   # State code
    "PWGTP",                # Person weight
    "AGEP",                 # Age
    "COW",                  # Class of worker
    "MAR",                  # Marital status
    "MIL",                  # Military service
    "RELSHIPP",             # Relationship to refernce person
    "SCHG",                 # Grade level attending
    "SCHL",                 # Educational attainment
    "SEX",                  # Sex
    "WKHP",                 # Usual hours worked per week past 12 months
    "WKW",                  # Weeks worked during past 12 months
    "ESR",                  # Employment status recode
    "HISP",                 # Recoded detailed Hispanic origin
    "NAICSP",               # North American Industry Classification System (NAICS) recode for 2018 and later based on 2017 NAICS codes
    "PINCP",                # Total person's income (signed, use ADJINC to adjust to constant dollars)
    "POWPUMA",              # Place of work PUMA based on 2010 Census definitions
    "SOCP",                 # Standard Occupational Classification (SOC) codes for 2018 and later based on 2018 SOC codes
    "INDP",                 # Industry recode for 2018 and later based on 2017 IND codes
    "OCCP",                 # Occupation recode for 2018 and later based on 2018 OCC codes
]

# columns added by this script
NEW_PERSON_RECORD_COLUMNS = [
    "COUNTY",               # MTC county code
    "employed",             # 0 or 1, based on ESR
    "soc",                  # 2 digit code, based on first two characters of socp00 or socp10
    "occupation",           # 0 is N/A, 1 is management, 2 is professional, 3 is services, 4 is retail, 5 is manual, 6 is military. based on socp00 or socp10
    "WGTP",                 # from housing record
    "unique_hh_id",         # from housing record
    "gqtype",               # 0 is non gq person, 1 is college student, 2 is military, 3 is other
    "employ_status",        # employment status for tm1. 1 is full-time worker, 2 is part-time worker, 3 is not in the labor force, 4 is student under 16
    "student_status",       # student status for tm1. 1 is pre-school through grade 12 student, 2 is university/professional school student, 3 is non-student
    "person_type",          # person type for tm1. 1 is full-time worker, 2 is part-time worker, 3 is college student, 4 is non-working adult, 
                            # 5 is retired, 6 is driving-age student, 7 is non-driving age student, 8 is child too young for school
]

import logging, os, pathlib, sys, time
import numpy, pandas

CROSSWALK_FILE      = pathlib.Path("hh_gq/data/geo_cross_walk_tm2.csv")
PUMS_INPUT_DIR      = pathlib.Path("M:/Data/Census/PUMS/PUMS 2017-21")
PUMS_HOUSEHOLD_FILE = "hbayarea1721.csv"
PUMS_PERSON_FILE    = "pbayarea1721.csv"

# First two characters of socp00 or socp10 to occupation code
# occupation: 
#    0: N/A
#    1: management
#    2: professional
#    3: services
#    4: retail
#    5: manual
#    6: military
OCCUPATION = pandas.DataFrame(data=
    {"soc"       :["11","13","15","17","19","21","23","25","27","29","31","33","35","37","39","41","43","45","47","49","51","53","55"],
     "occupation":[   1,   2,   2,   2,   2,   3,   2,   2,   3,   2,   3,   3,   4,   5,   3,   4,   3,   5,   5,   5,   5,   5,   6]})

def clean_types(df):
    """
    Iteates over columns in the given data frame and tries to downcast them to integers.
    If they don't downcast cleanly, then no change is made.
    """
    for colname in list(df.columns.values):
        log_str = "{:20}".format(colname)
        log_str += "{:8d} null values,".format(pandas.isnull(df[colname]).sum())
        log_str += "{:10} dtype, ".format(str(df[colname].dtype))
        log_str += "{:15s} min, ".format(str(df[colname].min()) if df[colname].dtype != object else "n/a")
        log_str += "{:15s} max ".format(str(df[colname].max()) if df[colname].dtype != object else "n/a")
        try:
            new_col = pandas.to_numeric(df[colname], errors="raise", downcast="integer")
            if str(new_col.dtype) != str(df[colname].dtype):
                df[colname] = new_col
                log_str +=  "  => {:10}".format(str(df[colname].dtype))
            else:
                log_str += " no downcast"
        except Exception as e:
            print(e)
        logging.info(log_str)

if __name__ == '__main__':
    pandas.options.display.width    = 180
    pandas.options.display.max_rows = 1000

    NOW = time.strftime("%Y%b%d_%H%M")
    LOG_FILE = pathlib.Path("hh_gq/data") / "create_seed_population_{}.log".format(NOW)
    print("Creating log file {}".format(LOG_FILE))

    # create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
    logger.addHandler(ch)
    # file handler
    fh = logging.FileHandler(LOG_FILE, mode='w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
    logger.addHandler(fh)

    pums_hu_file   = os.path.join(PUMS_INPUT_DIR, PUMS_HOUSEHOLD_FILE)
    pums_hu_df     = pandas.read_csv(pums_hu_file, usecols=PUMS_HOUSING_RECORD_COLUMNS)
    logging.info("Read {:,} housing records from {}".format(len(pums_hu_df), pums_hu_file))
    logging.debug("pums_hu_df.head():\n{}".format(pums_hu_df.head()))
    logging.debug("pums_hu_df.dtypes:\n{}".format(pums_hu_df.dtypes))

    pums_pers_file = os.path.join(PUMS_INPUT_DIR, PUMS_PERSON_FILE)
    pums_pers_df   = pandas.read_csv(pums_pers_file, usecols=PUMS_PERSON_RECORD_COLUMNS)
    logging.info("Read {:,} person  records from {}".format(len(pums_pers_df), pums_pers_file))
    logging.debug("pums_pers_df.head()\n{}".format(pums_pers_df.head()))
    logging.debug("pums_pers_df.dtypes()\n{}".format(pums_pers_df.dtypes))
    # Note: this is already filtered to Bay Area PUMAs

    # add COUNTY
    geo_crosswalk_df = pandas.read_csv(CROSSWALK_FILE)
    PUMA_TO_COUNTY = geo_crosswalk_df[["PUMA","COUNTY"]].drop_duplicates()
    logging.debug("PUMA_TO_COUNTY:\n{}".format(PUMA_TO_COUNTY))
    pums_hu_df   = pandas.merge(left=pums_hu_df,   right=PUMA_TO_COUNTY, how="left")
    pums_pers_df = pandas.merge(left=pums_pers_df, right=PUMA_TO_COUNTY, how="left")

    # compute number of workers in the housing unit
    # ESR: Employment status recode
    #        b .N/A (less than 16 years old)
    #        1 .Civilian employed, at work
    #        2 .Civilian employed, with a job but not at work
    #        3 .Unemployed
    #        4 .Armed forces, at work
    #        5 .Armed forces, with a job but not at work
    #        6 .Not in labor force
    pums_pers_df.loc[ pandas.isnull(pums_pers_df.ESR), 'ESR'] = 0  # code blank as 0
    pums_pers_df['ESR'] = pums_pers_df.ESR.astype(numpy.uint8)
    pums_pers_df['employed'] = 0
    pums_pers_df.loc[ (pums_pers_df.ESR==1)|(pums_pers_df.ESR==2)|(pums_pers_df.ESR==4)|(pums_pers_df.ESR==5), 'employed'] = 1

    pums_workers_df = pums_pers_df[['SERIALNO','employed']].groupby(['SERIALNO']).sum().rename(columns={"employed":"hh_workers_from_esr"})
    pums_hu_df = pandas.merge(
        left       =pums_hu_df,
        right      =pums_workers_df,
        left_on    =['SERIALNO'],
        right_index=True,
        how        ='left')
    pums_hu_df.loc[ pandas.isnull(pums_hu_df.hh_workers_from_esr), 'hh_workers_from_esr'] = 0
    pums_hu_df['hh_workers_from_esr'] = pums_hu_df.hh_workers_from_esr.astype(numpy.uint8)
    del pums_workers_df
    logging.debug("\n{}".format(pums_hu_df.head()))
    logging.debug("\n{}".format(pums_pers_df.head()))

    # WKW: Weeks worked during past 12 months
    #     b .N/A (less than 16 years old/did not work during the past 12 .months)
    #     1 .50 to 52 weeks worked during past 12 months
    #     2 .48 to 49 weeks worked during past 12 months
    #     3 .40 to 47 weeks worked during past 12 months
    #     4 .27 to 39 weeks worked during past 12 month
    #     5 .14 to 26 weeks worked during past 12 months
    #     6 .13 weeks or less worked during past 12 months
    # WKHP: Usual hours worked per week past 12 months
    #     bb .N/A (less than 16 years old/did not work during the past .12 months)
    #     1..98 .1 to 98 usual hours
    #     99 .99 or more usual hours

    # set employment status based on employment status recode, weeks worked per year, and hours worked per week
    pums_pers_df['employ_status'] = 999
    pums_pers_df.loc[ pums_pers_df.employed == 1, 'employ_status'] = 2 # part-time worker
    pums_pers_df.loc[ (pums_pers_df.employed == 1)&
                      ((pums_pers_df.WKW==1)|(pums_pers_df.WKW==2)|(pums_pers_df.WKW==3)|(pums_pers_df.WKW==4))&
                      (pums_pers_df.WKHP>=35), 'employ_status'] = 1 # full-time worker
    pums_pers_df.loc[ (pums_pers_df.ESR==0),   'employ_status'] = 4 # student under 16
    pums_pers_df.loc[ (pums_pers_df.ESR==6)|(pums_pers_df.ESR==3), 'employ_status'] = 3  # not in the labor force

    # SCHG   Grade level attending
    #     bb .N/A (not attending school)
    #     01 .Nursery school/preschool
    #     02 .Kindergarten
    #     03 .Grade 1
    #     04 .Grade 2
    #     05 .Grade 3
    #     06 .Grade 4
    #     07 .Grade 5
    #     08 .Grade 6
    #     09 .Grade 7
    #     10 .Grade 8
    #     11 .Grade 9
    #     12 .Grade 10
    #     13 .Grade 11
    #     14 .Grade 12
    #     15 .College undergraduate years (freshman to senior)
    #     16 .Graduate or professional school beyond a bachelor's degree
    # set student status based on school grade
    pums_pers_df['student_status'] = 3
    pums_pers_df.loc[ (pums_pers_df.SCHG>=1 )&(pums_pers_df.SCHG<=14), 'student_status'] = 1 # pre-school through grade 12 student
    pums_pers_df.loc[ (pums_pers_df.SCHG==15)|(pums_pers_df.SCHG==16), 'student_status'] = 2 # university/professional school student

    # set person type based on employ status, student status, and age
    pums_pers_df['person_type'] = 999
    pums_pers_df['person_type'] = 5 # non-working senior
    pums_pers_df.loc[ (pums_pers_df.AGEP<65), 'person_type'] = 4 # non-working adult
    pums_pers_df.loc[ (pums_pers_df.employ_status==2), 'person_type'] = 2 # part-time worker
    pums_pers_df.loc[ (pums_pers_df.student_status==1), 'person_type'] = 6  # driving-age student
    pums_pers_df.loc[ (pums_pers_df.student_status==2)|((pums_pers_df.AGEP>=20)&(pums_pers_df.student_status==1)), 'person_type'] = 3 # college student
    pums_pers_df.loc[ (pums_pers_df.employ_status==1), 'person_type'] = 1 # full-time worker
    pums_pers_df.loc[ (pums_pers_df.AGEP<=15), 'person_type'] = 7 # non-driving under 16
    pums_pers_df.loc[ (pums_pers_df.AGEP<6)&(pums_pers_df.student_status==3), 'person_type'] = 8 # pre-school

    # put income in constant year dollars
    #
    # From PUMS Data Dictionary (M:\Data\Census\PUMS\PUMS 2017-21\PUMS_Data_Dictionary_2017-2021.pdf):
    #  Adjustment factor for income and earnings dollar amounts (6 implied decimal places)
    #      1117630 .2017 factor (1.011189 * 1.10526316)
    #      1093093 .2018 factor (1.013097 * 1.07896160)
    #      1070512 .2019 factor (1.010145 * 1.05976096)
    #      1053131 .2020 factor (1.006149 * 1.04669465)
    #      1029928 .2021 factor (1.029928 * 1.00000000)
    # From PUMS User Guide (2017_2021ACS_PUMS_User_Guide.pdf):
    #  G. Note on Income and Earnings Inflation Factor (ADJINC)
    #  Divide ADJINC by 1,000,000 to obtain the inflation adjustment factor and multiply it to
    #  the PUMS variable value to adjust it to 2021 dollars. Variables requiring ADJINC on the
    #  Housing Unit file are FINCP and HINCP. Variables requiring ADJINC on the Person
    #  files are: INTP, OIP, PAP, PERNP, PINCP, RETP, SEMP, SSIP, SSP, and WAGP.

    # transfer personal income from persons to households for households without HINCP
    pers_inc_df = pums_pers_df[["SERIALNO","PINCP"]]                            # only want household id, personal income
    pers_inc_df = pers_inc_df.loc[ pandas.notnull(pers_inc_df["PINCP"])].copy() # drop those with null personal income
    pers_inc_df.drop_duplicates(subset="SERIALNO", keep="first", inplace=True)  # only want one per household
    pums_hu_df = pandas.merge(
        left =pums_hu_df,                                 # add it to the housing unit dataframe
        right=pers_inc_df,
        how  ="left")
    pums_hu_df.loc[ pandas.isnull(pums_hu_df["HINCP"]), "HINCP"] = pums_hu_df["PINCP"]  # pick up personal income if household income is null
    pums_hu_df.drop(columns=["PINCP"], inplace=True)                                    # we're done with PINCP

    ONE_MILLION = 1000000
    pums_hu_df['hh_income_2021'] = (pums_hu_df.ADJINC / ONE_MILLION) * pums_hu_df.HINCP

    # add household income in 2000 dollars, by deflating hh_income_2021
    # https://github.com/BayAreaMetro/modeling-website/wiki/InflationAssumptions
    pums_hu_df['hh_income_2000'] = pums_hu_df['hh_income_2021']/1.81

    # extract the occupation code -- first two characters
    pums_pers_df['soc'] = pums_pers_df.SOCP.str[:2]                                   

    # join to OCCUPATION; this adds occupation column
    pums_pers_df = pandas.merge(left=pums_pers_df,
                                right=OCCUPATION,
                                how="left")
    pums_pers_df.loc[ pandas.isnull(pums_pers_df.occupation), 'occupation'] = 0
    pums_pers_df['occupation'] = pums_pers_df.occupation.astype(numpy.uint8)

    # separate group quarters and housing records
    # From PUMS Data Dictionary (M:\Data\Census\PUMS\PUMS 2017-21\PUMS_Data_Dictionary_2017-2021.pdf):
    # WGTP   Housing Unit Weight
    #   0000       .Group Quarter placeholder record
    #   0001..9999 .Integer weight of housing unit
    #
    # NP     Number of persons associated with this housing record
    #            0 .Vacant unit
    #            1 .One person record (one person in household or
    #              .any person in group quarters)
    #        2..20 .Number of person records (number of persons in household)
    #
    # TYPEHUGQ  Type of unit
    #            1 .Housing unit
    #            2 .Institutional group quarters
    #            3 .Noninstitutional group quarters

    # Remove vacant housing units
    pums_hu_df = pums_hu_df.loc[ pums_hu_df.NP != 0, :]
    logging.info("Filtered to {:,} non-vacant housing records".format(len(pums_hu_df)))

    # SERIALNO is never null -- note that it's a string though, not a number
    assert( len(pums_hu_df.loc[   pandas.isnull(pums_hu_df.SERIALNO),   ['SERIALNO','WGTP','NP','TYPEHUGQ']])==0)
    assert( len(pums_pers_df.loc[ pandas.isnull(pums_pers_df.SERIALNO), ['SERIALNO']])==0)
    # note WGTP is never null
    assert( len(pums_hu_df.loc[ pandas.isnull(pums_hu_df.WGTP), ['SERIALNO','WGTP','NP','TYPEHUGQ']])==0)
    # note households (TYPEHUGQ==1) always have non-zero weight
    assert( len(pums_hu_df.loc[ (pums_hu_df.WGTP==0)&(pums_hu_df.TYPEHUGQ==1), ['SERIALNO','WGTP','NP','TYPEHUGQ']])==0)
    # note group quarters (TYPE>1) have zero weight
    assert( len(pums_hu_df.loc[ (pums_hu_df.WGTP>0)&(pums_hu_df.TYPEHUGQ>1), ['SERIALNO','WGTP','NP','TYPEHUGQ']])==0)

    # DON'T SPLIT households (TYPEHUGQ=1) and non institutional group quarters (TYPEHUGQ=3).  Just drop TYPEHUGQ=2 (institional gq).
    # add TYPEHUGQ to pums_pers_df
    pums_pers_df = pandas.merge(
        left  = pums_pers_df,
        right = pums_hu_df[['SERIALNO','TYPEHUGQ']],
        how   = "left")
    pums_hu_df   = pums_hu_df.loc[ (pums_hu_df.TYPEHUGQ != 2), :]
    pums_pers_df = pums_pers_df.loc[ pums_pers_df.TYPEHUGQ != 2, :]
    logging.info("Filtered to {:,} household and non-institutional group quarters housing records".format(len(pums_hu_df)))

    # give households unique id
    pums_hu_df.reset_index(drop=True,inplace=True)
    pums_hu_df['unique_hh_id'] = pums_hu_df.index + 1  # start at 1
    # transfer unique_hh_id and WGTP to person records
    pums_pers_df = pandas.merge(
        left =pums_pers_df,
        right=pums_hu_df[['SERIALNO','WGTP','unique_hh_id']],
        how  ="left")

    # MIL     Military service
    #    b .N/A (less than 17 years old)
    #    1 .Now on active duty
    #    2 .On active duty in the past, but not now
    #    3 .Only on active duty for training in Reserves/National Guard
    #    4 .Never served in the military
    #
    # add gqtype to person: 1 is college student, 2 is military, 3 is other
    pums_pers_df["gqtype"] = 0  # non-gq
    pums_pers_df.loc[ pums_pers_df.TYPEHUGQ==3                                                    , "gqtype"] = 3
    pums_pers_df.loc[ (pums_pers_df.TYPEHUGQ==3)&(pums_pers_df.MIL==1)                            , "gqtype"] = 2
    pums_pers_df.loc[ (pums_pers_df.TYPEHUGQ==3)&((pums_pers_df.SCHG==15)|(pums_pers_df.SCHG==16)), "gqtype"] = 1
    logging.info(pums_pers_df.gqtype.value_counts())
    # add PWGT to housing record temporarily for group quarters folks since they lack housing weights WGTP
    logging.info("before merge: pums_pers_df len {:,} pums_hu_df len {:,}".format(len(pums_pers_df), len(pums_hu_df)))
    pums_hu_df = pandas.merge(
        left =pums_hu_df,
        right=pums_pers_df[['SERIALNO','PWGTP','gqtype']].drop_duplicates(subset=['SERIALNO']),
        how  ="left")
    # for group quarters people, household weight is 0.  Set to person weight for populationsim
    pums_hu_df.loc[ pums_hu_df.TYPEHUGQ==3, "WGTP"] = pums_hu_df.PWGTP
    pums_hu_df.drop(columns=["PWGTP"], inplace=True)
    # rename gqtype to hhgqtype
    pums_hu_df.rename(columns={"gqtype":"hhgqtype"}, inplace=True)
    logging.info("after merge: pums_pers_df len {:,} pums_hu_df len {:,}".format(len(pums_pers_df), len(pums_hu_df)))

    # one last downcast
    logging.info("--- Running clean_types on housing units ---")
    clean_types(pums_hu_df)
    logging.info("--- Running clean_types on persons ---")
    clean_types(pums_pers_df)

    # write combined housing records and person records
    if not os.path.exists(pathlib.Path("hh_gq/data")): os.mkdir(pathlib.Path("hh_gq/data"))
    outfile = pathlib.Path("hh_gq/data/seed_households.csv")
    pums_hu_df.to_csv(outfile, index=False)
    logging.info("Wrote household and group quarters housing records to {}".format(outfile))

    outfile = pathlib.Path("hh_gq/data/seed_persons.csv")
    pums_pers_df.to_csv(outfile, index=False)
    logging.info("Wrote household and group quarters person  records to {}".format(outfile))
