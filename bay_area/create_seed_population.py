"""
Create seed files for MTC Bay Area populationsim.

Based on https://github.com/BayAreaMetro/popsyn3/blob/master/scripts/Step%2001%20PUMS%20to%20Database.R
Results differ from the data tables produced by that process in that:
- The R/mysql process appears to fill in blanks.  This script does not, but pandas does make those columns
  into floats, so they'll show decimals even if all the values are integers.
- I did not replace the GQ PUMA with another encoding of the PUMA since I'm not sure what the purpose is,
  and naming that column PUMA when it's not the same is confusing to me.

Columns used:
- PUMA (housing and person), to filter to bay area for housing and person records
- ESR (person), Employment Status Recode, to count workers per housing record
- SERIALNO (hh and person), to group persons to housing record, to count workers per housing record
- ADJINC and HINCP (hh), used to adjust household income to 2010 dollars
- NP (housing), to filter out vacant unitsf
- TYPE (housing), to filter to households and non-institutional group quarters
- MIL (person), to inform gqtype for group quarters persons
- SCHG (person), to inform gqtype for group quarters persons

New columns in housing records file:
- hh_workers_from_esr: count of employed persons in household
- hh_income_2010     : household income in 2010 dollars, based on HINCP and ADJINC
- unique_hh_id       : integer unique id for housing unit, starting with 1
- hhgqtype           : 0 for non gq, 1 is college student, 2 is military, 3 is other
- PWGT               : for group quarters file only, transfered from person records
New columns in person records file:
- employed           : 0 or 1, based on ESR
- soc                : 2 digit code, based on first two characters of socp00 or socp10
- occupation         : 0, 1, 2, 3, 4, 5, 6, based on socp00 or socp10
- WGTP               : from housing record
- unique_hh_id       : from housing record
- gqtype             : for group quarters file only, 1 is college student, 2 is military, 3 is other
"""
# pums housing unit columns to keep
PUMS_HOUSING_RECORD_COLUMNS = [
    "RT",                   # Record Type
    "SERIALNO",             # Housing unit/GQ person serial number
    "DIVISION",             # Division code
    "PUMA",                 # Public use microdata area code
    "REGION",               # Region code
    "ST",                   # State code
    "ADJINC",               # Adjustment factor for income and earnings dollar amounts
    "WGTP",                 # Housing weight
    "NP",                   # Number of person records following this housing record
    "TYPE",                 # Type of unit
    "BLD",                  # Units in structure
    "HHT",                  # Household/family type
    "HINCP",                # Household income (past 12 months)
    "HUPAC",                # HH presence and age of children
    "NPF",                  # Number of persons in family (unweighted)
    "TEN",                  # Tenure
    "VEH",                  # Vehicles available
]
# columns added by this script
NEW_HOUSING_RECORD_COLUMNS = [
    "COUNTY",               # MTC county code
    "hh_workers_from_esr",  # count of employed persons in household
    "hh_income_2010",       # household income in 2010 dollars, based on HINCP and ADJINC
    "unique_hh_id",         # integer unique id for housing unit, starting with 1
    "gqtype",               # group quarters type: 0: household (not gq), 1 college, 2 militar, 3 other
    "hh_income_2000",       # household income in 2000 dollars for tm1
]

# pums person record columns to keep
PUMS_PERSON_RECORD_COLUMNS = [
    "RT",                   # Record Type
    "SERIALNO",             # Housing unit/GQ person serial number
    "SPORDER",              # Person number
    "PUMA",                 # Public use microdata area code
    "ST",                   # State code
    "PWGTP",                # Person's weight
    "AGEP",                 # Age
    "COW",                  # Class of worker
    "MAR",                  # Marital status
    "MIL",                  # Military service
    "RELP",                 # Relationship
    "SCHG",                 # Grade level attending
    "SCHL",                 # Educational attainment
    "SEX",                  # Sex
    "WKHP",                 # Usual hours worked per week past 12 months
    "WKW",                  # Weeks worked during past 12 months
    "ESR",                  # Employment status recode
    "HISP",                 # Recoded detailed Hispanic origin
    "naicsp07",             # NAICS 2007 Industry code
    "PINCP",                # Total person's income (signed)
    "POWPUMA",              # Place of work PUMA
    "socp00",               # SOC 2000 Occupation code
    "socp10",               # SOC 2010 Occupation code
    "indp02",               # Industry 2002 recode
    "indp07",               # Industry 2007 recode
    "occp02",               # Occupation 2002 recode
    "occp10",               # Occupation 2010 recode
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

import logging, os, sys, time
import numpy, pandas

PUMS_INPUT_DIR      = "M:\Data\Census\PUMS\PUMS 2007-11\CSV"
PUMS_HOUSEHOLD_FILE = "ss11hca.csv"
PUMS_PERSON_FILE    = "ss11pca.csv"

BAY_AREA_PUMA2000_COUNTY = pandas.DataFrame([
    {"PUMA":1000, "COUNTY":7, "county_name":"Napa"         },
    {"PUMA":1101, "COUNTY":8, "county_name":"Sonoma"       },
    {"PUMA":1102, "COUNTY":8, "county_name":"Sonoma"       },
    {"PUMA":1103, "COUNTY":8, "county_name":"Sonoma"       },
    {"PUMA":1201, "COUNTY":9, "county_name":"Marin"        },
    {"PUMA":1202, "COUNTY":9, "county_name":"Marin"        },
    {"PUMA":1301, "COUNTY":6, "county_name":"Solano"       },
    {"PUMA":1302, "COUNTY":6, "county_name":"Solano"       },
    {"PUMA":1303, "COUNTY":6, "county_name":"Solano"       },
    {"PUMA":2101, "COUNTY":5, "county_name":"Contra Costa" },
    {"PUMA":2102, "COUNTY":5, "county_name":"Contra Costa" },
    {"PUMA":2103, "COUNTY":5, "county_name":"Contra Costa" },
    {"PUMA":2104, "COUNTY":5, "county_name":"Contra Costa" },
    {"PUMA":2105, "COUNTY":5, "county_name":"Contra Costa" },
    {"PUMA":2106, "COUNTY":5, "county_name":"Contra Costa" },
    {"PUMA":2107, "COUNTY":5, "county_name":"Contra Costa" },
    {"PUMA":2108, "COUNTY":5, "county_name":"Contra Costa" },
    {"PUMA":2201, "COUNTY":1, "county_name":"San Francisco"},
    {"PUMA":2202, "COUNTY":1, "county_name":"San Francisco"},
    {"PUMA":2203, "COUNTY":1, "county_name":"San Francisco"},
    {"PUMA":2204, "COUNTY":1, "county_name":"San Francisco"},
    {"PUMA":2205, "COUNTY":1, "county_name":"San Francisco"},
    {"PUMA":2206, "COUNTY":1, "county_name":"San Francisco"},
    {"PUMA":2207, "COUNTY":1, "county_name":"San Francisco"},
    {"PUMA":2301, "COUNTY":2, "county_name":"San Mateo"    },
    {"PUMA":2302, "COUNTY":2, "county_name":"San Mateo"    },
    {"PUMA":2303, "COUNTY":2, "county_name":"San Mateo"    },
    {"PUMA":2304, "COUNTY":2, "county_name":"San Mateo"    },
    {"PUMA":2305, "COUNTY":2, "county_name":"San Mateo"    },
    {"PUMA":2306, "COUNTY":2, "county_name":"San Mateo"    },
    {"PUMA":2401, "COUNTY":4, "county_name":"Alameda"      },
    {"PUMA":2402, "COUNTY":4, "county_name":"Alameda"      },
    {"PUMA":2403, "COUNTY":4, "county_name":"Alameda"      },
    {"PUMA":2404, "COUNTY":4, "county_name":"Alameda"      },
    {"PUMA":2405, "COUNTY":4, "county_name":"Alameda"      },
    {"PUMA":2406, "COUNTY":4, "county_name":"Alameda"      },
    {"PUMA":2407, "COUNTY":4, "county_name":"Alameda"      },
    {"PUMA":2408, "COUNTY":4, "county_name":"Alameda"      },
    {"PUMA":2409, "COUNTY":4, "county_name":"Alameda"      },
    {"PUMA":2410, "COUNTY":4, "county_name":"Alameda"      },
    {"PUMA":2701, "COUNTY":3, "county_name":"Santa Clara"  },
    {"PUMA":2702, "COUNTY":3, "county_name":"Santa Clara"  },
    {"PUMA":2703, "COUNTY":3, "county_name":"Santa Clara"  },
    {"PUMA":2704, "COUNTY":3, "county_name":"Santa Clara"  },
    {"PUMA":2705, "COUNTY":3, "county_name":"Santa Clara"  },
    {"PUMA":2706, "COUNTY":3, "county_name":"Santa Clara"  },
    {"PUMA":2707, "COUNTY":3, "county_name":"Santa Clara"  },
    {"PUMA":2708, "COUNTY":3, "county_name":"Santa Clara"  },
    {"PUMA":2709, "COUNTY":3, "county_name":"Santa Clara"  },
    {"PUMA":2710, "COUNTY":3, "county_name":"Santa Clara"  },
    {"PUMA":2711, "COUNTY":3, "county_name":"Santa Clara"  },
    {"PUMA":2712, "COUNTY":3, "county_name":"Santa Clara"  },
    {"PUMA":2713, "COUNTY":3, "county_name":"Santa Clara"  },
    {"PUMA":2714, "COUNTY":3, "county_name":"Santa Clara"  }])


# First two characters of socp00 or socp10 to occupation code
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
    LOG_FILE = "create_seed_population_{}.log".format(NOW)
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
    logging.info("Read {:7d} housing records from {}".format(len(pums_hu_df), pums_hu_file))
    logging.debug("pums_hu_df.head():\n{}".format(pums_hu_df.head()))
    logging.debug("pums_hu_df.dtypes:\n{}".format(pums_hu_df.dtypes))

    pums_pers_file = os.path.join(PUMS_INPUT_DIR, PUMS_PERSON_FILE)
    pums_pers_df   = pandas.read_csv(pums_pers_file, usecols=PUMS_PERSON_RECORD_COLUMNS)
    logging.info("Read {:7d} person  records from {}".format(len(pums_pers_df), pums_pers_file))
    logging.debug("pums_pers_df.head()\n{}".format(pums_pers_df.head()))
    logging.debug("pums_pers_df.dtypes()\n{}".format(pums_pers_df.dtypes))

    # filter to bay area
    local_pumas  = BAY_AREA_PUMA2000_COUNTY.PUMA.tolist()
    pums_hu_df   = pums_hu_df.loc[pums_hu_df.PUMA.isin(local_pumas), :]
    logging.info("Filtered to {:7d} housing records in the bay area".format(len(pums_hu_df)))
    pums_pers_df = pums_pers_df.loc[pums_pers_df.PUMA.isin(local_pumas), :]
    logging.info("Filtered to {:7d} person  records in the bay area".format(len(pums_pers_df)))

    # add COUNTY
    pums_hu_df   = pandas.merge(left=pums_hu_df,   right=BAY_AREA_PUMA2000_COUNTY[["PUMA","COUNTY"]], how="left")
    pums_pers_df = pandas.merge(left=pums_pers_df, right=BAY_AREA_PUMA2000_COUNTY[["PUMA","COUNTY"]], how="left")

    # compute number of workers in the housing unit
    # Employment status recode
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
    pums_hu_df = pandas.merge(left       =pums_hu_df,    right      =pums_workers_df,
                              left_on    =['SERIALNO'],  right_index=True,
                              how        ='left')
    pums_hu_df.loc[ pandas.isnull(pums_hu_df.hh_workers_from_esr), 'hh_workers_from_esr'] = 0
    pums_hu_df['hh_workers_from_esr'] = pums_hu_df.hh_workers_from_esr.astype(numpy.uint8)
    del pums_workers_df
    logging.debug("\n{}".format(pums_hu_df.head()))
    logging.debug("\n{}".format(pums_pers_df.head()))

    # Employment status recode
    #        b .N/A (less than 16 years old)
    #        1 .Civilian employed, at work
    #        2 .Civilian employed, with a job but not at work
    #        3 .Unemployed
    #        4 .Armed forces, at work
    #        5 .Armed forces, with a job but not at work
    #        6 .Not in labor force

    # set employment status based on emplotment status recode, weeks worked per year, and hours worked per week
    pums_pers_df['employ_status'] = 999
    pums_pers_df.loc[ (pums_pers_df.ESR==1)|(pums_pers_df.ESR==2)|(pums_pers_df.ESR==4)|(pums_pers_df.ESR==5), 'employ_status'] = 2 # part-time worker
    pums_pers_df.loc[ ((pums_pers_df.ESR==1)|(pums_pers_df.ESR==2)|(pums_pers_df.ESR==4)|(pums_pers_df.ESR==5))&((pums_pers_df.WKW==1)|(pums_pers_df.WKW==2)|(pums_pers_df.WKW==3)|(pums_pers_df.WKW==4))&
                      (pums_pers_df.WKHP>=35), 'employ_status'] = 1 # full-time worker
    pums_pers_df.loc[ (pums_pers_df.ESR==0), 'employ_status'] = 4 # student under 16
    pums_pers_df.loc[ (pums_pers_df.ESR==6)|(pums_pers_df.ESR==3), 'employ_status'] = 3  # not in the labor force

    # SCHG   Grade level attending
    #      b .N/A (not attending school)
    #      1 .Nursery school/preschool
    #      2 .Kindergarten
    #      3 .Grade 1 to grade 4
    #      4 .Grade 5 to grade 8
    #      5 .Grade 9 to grade 12
    #      6 .College undergraduate
    #      7 .Graduate or professional school  

    # set student status based on school grade
    pums_pers_df['student_status'] = 999
    pums_pers_df.loc[ (pums_pers_df.SCHG==1)|(pums_pers_df.SCHG==2)|(pums_pers_df.SCHG==3)|(pums_pers_df.SCHG==4)|(pums_pers_df.SCHG==5), 'student_status'] = 1 # pre-school through grade 12 student
    pums_pers_df.loc[ (pums_pers_df.SCHG==6)|(pums_pers_df.SCHG==7), 'student_status'] = 2 # university/professional school student
    pums_pers_df.loc[ pandas.isnull(pums_pers_df.SCHG), 'student_status'] = 3 # non-student

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

    # put income in constant year dollars (SQL says reported income * rolling reference factor * inflation adjustment)
    #
    # From PUMS Data Dictionary (M:\Data\Census\PUMS\PUMS 2007-11\PUMS_Data_Dictionary_2007-2011.pdf):
    # Adjustment factor for income and earnings dollar amounts (6 implied decimal places)
    #   1102938 .2007 factor (1.016787 * 1.08472906)
    #   1063801 .2008 factor (1.018389 * 1.04459203)
    #   1048026 .2009 factor (0.999480 * 1.04857143)
    #   1039407 .2010 factor (1.007624 * 1.03154279)
    #   1018237 .2011 factor (1.018237 * 1.00000000)
    # Note: The values of ADJINC inflation-adjusts reported income to 2011 dollars.
    # ADJINC incorporates an adjustment that annualizes the different rolling reference
    # periods for reported income (as done in the single-year data using the variable
    # ADJUST) and an adjustment to inflation-adjust the annualized income to 2011
    # dollars.  ADJINC applies to variables FINCP and HINCP in the housing record, and
    # variables INTP, OIP, PAP, PERNP, PINCP, RETP, SEMP, SSIP, SSP, and WAGP in the
    # person record.

    # transfer personal income from persons to households for households without HINCP
    pers_inc_df = pums_pers_df[["SERIALNO","PINCP"]]                            # only want household id, personal income
    pers_inc_df = pers_inc_df.loc[ pandas.notnull(pers_inc_df["PINCP"])].copy() # drop those with null personal income
    pers_inc_df.drop_duplicates(subset="SERIALNO", keep="first", inplace=True)  # only want one per household
    pums_hu_df = pandas.merge(left =pums_hu_df,                                 # add it to the housing unit dataframe
                              right=pers_inc_df,
                              how  ="left")
    pums_hu_df.loc[ pandas.isnull(pums_hu_df["HINCP"]), "HINCP"] = pums_hu_df["PINCP"]  # pick up personal income if household income is null
    pums_hu_df.drop(columns=["PINCP"], inplace=True)                                    # we're done with PINCP

    pums_hu_df['hh_income_2010'] = 999
    pums_hu_df.loc[ pums_hu_df.ADJINC==1102938, 'hh_income_2010'] = pums_hu_df.HINCP/1.0 * 1.016787 * 1.08472906/1.03154279
    pums_hu_df.loc[ pums_hu_df.ADJINC==1063801, 'hh_income_2010'] = pums_hu_df.HINCP/1.0 * 1.018389 * 1.04459203/1.03154279
    pums_hu_df.loc[ pums_hu_df.ADJINC==1048026, 'hh_income_2010'] = pums_hu_df.HINCP/1.0 * 0.999480 * 1.04857143/1.03154279
    pums_hu_df.loc[ pums_hu_df.ADJINC==1039407, 'hh_income_2010'] = pums_hu_df.HINCP/1.0 * 1.007624 * 1.03154279/1.03154279
    pums_hu_df.loc[ pums_hu_df.ADJINC==1018237, 'hh_income_2010'] = pums_hu_df.HINCP/1.0 * 1.018237 * 1.00000000/1.03154279

    # add household income in 2000 dollars, by deflating hh_income_2010 
    pums_hu_df['hh_income_2000'] = pums_hu_df['hh_income_2010']*.79219238

    # extract the occupation code -- first two characters
    pums_pers_df['soc'] = pums_pers_df.socp00                                   # start with SOC 2000
    pums_pers_df.loc[ pums_pers_df.soc == "N.A.//", 'soc'] = pums_pers_df.socp10 # use SOC 2010 if SOC 2000 is not available
    pums_pers_df['soc'] = pums_pers_df.soc.str[:2]                              # first two characters

    # join to OCCUPATION; this adds occupation column
    pums_pers_df = pandas.merge(left=pums_pers_df,
                                right=OCCUPATION,
                                how="left")
    pums_pers_df.loc[ pandas.isnull(pums_pers_df.occupation), 'occupation'] = 0
    pums_pers_df['occupation'] = pums_pers_df.occupation.astype(numpy.uint8)

    # separate group quarters and housing records
    # From PUMS Data Dictionary (M:\Data\Census\PUMS\PUMS 2007-11\PUMS_Data_Dictionary_2007-2011.pdf):
    # WGTP   Housing Weight
    #   0000       .Group Quarter placeholder record
    #   0001..9999 .Integer weight of housing unit
    #
    # NP     Number of person records following this housing record
    #           00 .Vacant unit
    #           01 .One person record (one person in household or
    #              .any person in group quarters)
    #       02..20 .Number of person records (number of persons in
    #              .household)
    #
    # TYPE  Type of unit
    #            1 .Housing unit
    #            2 .Institutional group quarters
    #            3 .Noninstitutional group quarters

    # Remove vacant housing units
    pums_hu_df = pums_hu_df.loc[ pums_hu_df.NP != 0, :]
    logging.info("Filtered to {:7d} non-vacant housing records".format(len(pums_hu_df)))

    # SERIALNO is never null
    assert( len(pums_hu_df.loc[   pandas.isnull(pums_hu_df.SERIALNO),   ['SERIALNO','WGTP','NP','TYPE']])==0)
    assert( len(pums_pers_df.loc[ pandas.isnull(pums_pers_df.SERIALNO), ['SERIALNO']])==0)
    pums_hu_df['SERIALNO']   = pums_hu_df.SERIALNO.astype(numpy.uint64)
    pums_pers_df['SERIALNO'] = pums_pers_df.SERIALNO.astype(numpy.uint64)
    # note WGTP is never null
    assert( len(pums_hu_df.loc[ pandas.isnull(pums_hu_df.WGTP), ['SERIALNO','WGTP','NP','TYPE']])==0)
    # note households (TYPE==1) always have non-zero weight
    assert( len(pums_hu_df.loc[ (pums_hu_df.WGTP==0)&(pums_hu_df.TYPE==1), ['SERIALNO','WGTP','NP','TYPE']])==0)
    # note group quarters (TYPE>1) have zero weight
    assert( len(pums_hu_df.loc[ (pums_hu_df.WGTP>0)&(pums_hu_df.TYPE>1), ['SERIALNO','WGTP','NP','TYPE']])==0)

    # DON'T SPLIT households (TYPE=1) and non institutional group quarters (TYPE=3).  Just drop TYPE=2 (institional gq).
    # add TYPE to pums_pers_df
    pums_pers_df = pandas.merge(left  = pums_pers_df,
                                right = pums_hu_df[['SERIALNO','TYPE']],
                                how   = "left")
    pums_hu_df   = pums_hu_df.loc[ (pums_hu_df.TYPE != 2), :]
    pums_pers_df = pums_pers_df.loc[ pums_pers_df.TYPE != 2, :]
    logging.info("Filtered to {:7d} household and non-institutional group quarters housing records".format(len(pums_hu_df)))

    # give households unique id
    pums_hu_df.reset_index(drop=True,inplace=True)
    pums_hu_df['unique_hh_id'] = pums_hu_df.index + 1  # start at 1
    # transfer unique_hh_id and WGTP to person records
    pums_pers_df = pandas.merge(left =pums_pers_df,
                                right=pums_hu_df[['SERIALNO','WGTP','unique_hh_id']],
                                how  ="left")

    # SCHG   Grade level attending
    #      b .N/A (not attending school)
    #      1 .Nursery school/preschool
    #      2 .Kindergarten
    #      3 .Grade 1 to grade 4
    #      4 .Grade 5 to grade 8
    #      5 .Grade 9 to grade 12
    #      6 .College undergraduate
    #      7 .Graduate or professional school
    #
    # MIL     Military service
    #      b .N/A (less than 17 years old)
    #      1 .Yes, now on active duty
    #      2 .Yes, on active duty during the last 12 months, but not now
    #      3 .Yes, on active duty in the past, but not during the last 12
    #        .months
    #      4 .No, training for Reserves/National Guard only
    #      5 .No, never served in the military
    #
    # add gqtype to person: 1 is college student, 2 is military, 3 is other
    pums_pers_df["gqtype"] = 0  # non-gq
    pums_pers_df.loc[ pums_pers_df.TYPE==3                                                  , "gqtype"] = 3
    pums_pers_df.loc[ (pums_pers_df.TYPE==3)&(pums_pers_df.MIL==1)                          , "gqtype"] = 2
    pums_pers_df.loc[ (pums_pers_df.TYPE==3)&((pums_pers_df.SCHG==6)|(pums_pers_df.SCHG==7)), "gqtype"] = 1
    logging.info(pums_pers_df.gqtype.value_counts())
    # add PWGT to housing record temporarily for group quarters folks since they lack housing weights WGTP
    logging.info("before merge: pums_pers_df len {} pums_hu_df len {}".format(len(pums_pers_df), len(pums_hu_df)))
    pums_hu_df = pandas.merge(left =pums_hu_df,
                              right=pums_pers_df[['SERIALNO','PWGTP','gqtype']].drop_duplicates(subset=['SERIALNO']),
                              how  ="left")
    # for group quarters people, household weight is 0.  Set to person weight for populationsim
    pums_hu_df.loc[ pums_hu_df.TYPE==3, "WGTP"] = pums_hu_df.PWGTP
    pums_hu_df.drop(columns=["PWGTP"], inplace=True)
    # rename gqtype to hhgqtype
    pums_hu_df.rename(columns={"gqtype":"hhgqtype"}, inplace=True)
    logging.info("after merge: pums_pers_df len {} pums_hu_df len {}".format(len(pums_pers_df), len(pums_hu_df)))

    # one last downcast
    clean_types(pums_hu_df)
    clean_types(pums_pers_df)

    # write combined housing records and person records
    if not os.path.exists(os.path.join("hh_gq","data")): os.mkdir(os.path.join("hh_gq","data"))
    outfile = os.path.join("hh_gq","data","seed_households.csv")
    pums_hu_df.to_csv(outfile, index=False)
    logging.info("Wrote household and group quarters housing records to {}".format(outfile))

    outfile = os.path.join("hh_gq","data","seed_persons.csv")
    pums_pers_df.to_csv(outfile, index=False)
    logging.info("Wrote household and group quarters person  records to {}".format(outfile))
