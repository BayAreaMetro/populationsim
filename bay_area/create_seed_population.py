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
- gqtype             : 0 for non gq, 1 is college student, 2 is military, 3 is other
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
    "hh_workers_from_esr",  # count of employed persons in household
    "hh_income_2010",       # household income in 2010 dollars, based on HINCP and ADJINC
    "unique_hh_id",         # integer unique id for housing unit, starting with 1
    "gqtype",               # group quarters type: 0: household (not gq), 1 college, 2 militar, 3 other
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
    "employed",             # 0 or 1, based on ESR
    "soc",                  # 2 digit code, based on first two characters of socp00 or socp10
    "occupation",           # 0 is N/A, 1 is management, 2 is professional, 3 is services, 4 is retail, 5 is manual, 6 is military. based on socp00 or socp10
    "WGTP",                 # from housing record
    "unique_hh_id",         # from housing record
    "gqtype",               # 0 is non gq person, 1 is college student, 2 is military, 3 is other
]

import os, sys
import numpy, pandas

PUMS_INPUT_DIR      = "M:\Data\Census\PUMS\PUMS 2007-11\CSV"
PUMS_HOUSEHOLD_FILE = "ss11hca.csv"
PUMS_PERSON_FILE    = "ss11pca.csv"
# these are PUMS 2000
BAY_AREA_PUMA5CE00  = [
    1000, 1101, 1102, 1103, 1201, 1202, 1301, 1302, 1303, 2101,
    2102, 2103, 2104, 2105, 2106, 2107, 2108, 2201, 2202, 2203,
    2204, 2205, 2206, 2207, 2301, 2302, 2303, 2304, 2305, 2306,
    2401, 2402, 2403, 2404, 2405, 2406, 2407, 2408, 2409, 2410,
    2701, 2702, 2703, 2704, 2705, 2706, 2707, 2708, 2709, 2710,
    2711, 2712, 2713, 2714
]

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
        # print("%10s: min:%10.2f  max:%10.2f  null count:%6d  dtype:%s" % (colname, df[colname].min(), df[colname].max(),
        #                                                                   len(pandas.isnull(df[colname])), str(df[colname].dtype)) )
        print "%20s:" % colname,
        print "%8d null values," % pandas.isnull(df[colname]).sum(),
        print "%10s dtype, " %  str(df[colname].dtype),
        print "%10s min, " % str(df[colname].min()),
        print "%10s max " % str(df[colname].max()),
        try:
            new_col = pandas.to_numeric(df[colname], errors="raise", downcast="integer")
            if str(new_col.dtype) != str(df[colname].dtype):
                df[colname] = new_col
                print "  => %10s" % str(df[colname].dtype)
            else:
                print " no downcast"
        except Exception, e:
            print e

if __name__ == '__main__':
    pandas.options.display.width    = 180
    pandas.options.display.max_rows = 1000

    pums_hu_file   = os.path.join(PUMS_INPUT_DIR, PUMS_HOUSEHOLD_FILE)
    pums_hu_df     = pandas.read_csv(pums_hu_file)
    pums_hu_df     = pums_hu_df[PUMS_HOUSING_RECORD_COLUMNS]
    print "Read %7d housing records from %s" % (len(pums_hu_df), pums_hu_file)
    print pums_hu_df.head()
    # print pums_hu_df.dtypes

    pums_pers_file = os.path.join(PUMS_INPUT_DIR, PUMS_PERSON_FILE)
    pums_pers_df   = pandas.read_csv(pums_pers_file)
    pums_pers_df   = pums_pers_df[PUMS_PERSON_RECORD_COLUMNS]
    print "Read %7d person  records from %s" % (len(pums_pers_df), pums_pers_file)
    print pums_pers_df.head()
    # print pums_pers_df.dtypes

    # filter to bay area
    pums_hu_df   = pums_hu_df.loc[pums_hu_df.PUMA.isin(BAY_AREA_PUMA5CE00), :]
    print "Filtered to %7d housing records in the bay area" % len(pums_hu_df)
    pums_pers_df = pums_pers_df.loc[pums_pers_df.PUMA.isin(BAY_AREA_PUMA5CE00), :]
    print "Filtered to %7d person  records in the bay area" % len(pums_pers_df)

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
    print pums_hu_df.head()
    print pums_pers_df.head()


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

    pums_hu_df['hh_income_2010'] = 999
    pums_hu_df.loc[ pums_hu_df.ADJINC==1102938, 'hh_income_2010'] = pums_hu_df.HINCP/1.0 * 1.016787 * 1.08472906/1.03154279
    pums_hu_df.loc[ pums_hu_df.ADJINC==1063801, 'hh_income_2010'] = pums_hu_df.HINCP/1.0 * 1.018389 * 1.04459203/1.03154279
    pums_hu_df.loc[ pums_hu_df.ADJINC==1048026, 'hh_income_2010'] = pums_hu_df.HINCP/1.0 * 0.999480 * 1.04857143/1.03154279
    pums_hu_df.loc[ pums_hu_df.ADJINC==1039407, 'hh_income_2010'] = pums_hu_df.HINCP/1.0 * 1.007624 * 1.03154279/1.03154279
    pums_hu_df.loc[ pums_hu_df.ADJINC==1018237, 'hh_income_2010'] = pums_hu_df.HINCP/1.0 * 1.018237 * 1.00000000/1.03154279

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
    print "Filtered to %7d non-vacant housing record" % len(pums_hu_df)

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

    # split -- households (TYPE=1) and non institutional group quarters (TYPE=3).  Dropping TYPE=2.
    pums_hu_hh_df = pums_hu_df.loc[ pums_hu_df.TYPE == 1, :].copy()
    pums_hu_gq_df = pums_hu_df.loc[ pums_hu_df.TYPE == 3, :].copy()
    # and persons -- add TYPE to pums_pers_df
    pums_pers_df = pandas.merge(left  = pums_pers_df,
                                right = pums_hu_df[['SERIALNO','TYPE']],
                                how   = "left")
    pums_pers_hh_df = pums_pers_df.loc[ pums_pers_df.TYPE == 1, :].copy()
    pums_pers_gq_df = pums_pers_df.loc[ pums_pers_df.TYPE == 3, :].copy()
    pums_pers_hh_df["gqtype"] = 0
    print "Split housing records into %d households and %d non-institutional group quarters" % (len(pums_hu_hh_df  ), len(pums_hu_gq_df  ))
    print "Split person  records into %d households and %d non-institutional group quarters" % (len(pums_pers_hh_df), len(pums_pers_gq_df))

    # give households unique id
    pums_hu_hh_df.reset_index(drop=True,inplace=True)
    pums_hu_hh_df['unique_hh_id'] = pums_hu_hh_df.index + 1  # start at 1
    # transfer unique_hh_id and WGTP to person records
    pums_pers_hh_df = pandas.merge(left =pums_pers_hh_df,
                                   right=pums_hu_hh_df[['SERIALNO','WGTP','unique_hh_id']],
                                   how  ="left")
    # one last downcast
    clean_types(pums_hu_hh_df)
    clean_types(pums_pers_hh_df)

    # write households - housing records and person records
    if not os.path.exists(os.path.join("households","data")): os.mkdir(os.path.join("households","data"))
    outfile = os.path.join("households","data","seed_households.csv")
    pums_hu_hh_df.to_csv(outfile, index=False)
    print "Wrote household housing records to %s" % outfile

    outfile = os.path.join("households","data","seed_persons.csv")
    pums_pers_hh_df.to_csv(outfile, index=False)
    print "Wrote household person  records to %s" % outfile

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
    pums_pers_gq_df["gqtype"] = 3
    pums_pers_gq_df.loc[ (pums_pers_gq_df.MIL==1)                           , "gqtype"] = 2
    pums_pers_gq_df.loc[ (pums_pers_gq_df.SCHG==6)|(pums_pers_gq_df.SCHG==7), "gqtype"] = 1
    print pums_pers_gq_df.gqtype.value_counts()
    # add gqtype, PWGT to housing record
    pums_hu_gq_df = pandas.merge(left =pums_hu_gq_df,
                                 right=pums_pers_gq_df[['SERIALNO','gqtype','PWGTP']],
                                 how  ="left")

    # give households unique id
    pums_hu_gq_df.reset_index(drop=True,inplace=True)
    pums_hu_gq_df['unique_hh_id'] = pums_hu_gq_df.index + 1  # start at 1
    # transfer unique_hh_id to person records
    pums_pers_gq_df = pandas.merge(left =pums_pers_gq_df,
                                   right=pums_hu_gq_df[['SERIALNO','unique_hh_id']],
                                   how  ="left")
    # one last downcast
    clean_types(pums_hu_gq_df)
    clean_types(pums_pers_gq_df)

    # write group quarters - housing records and person records
    if not os.path.exists(os.path.join("group_quarters","data")): os.mkdir(os.path.join("group_quarters","data"))
    outfile = os.path.join("group_quarters","data","seed_households.csv")
    pums_hu_gq_df.to_csv(outfile, index=False)
    print "Wrote group quarters housing records to %s" % outfile

    outfile = os.path.join("group_quarters","data","seed_persons.csv")
    pums_pers_gq_df.to_csv(outfile, index=False)
    print "Wrote group quarters person  records to %s" % outfile
