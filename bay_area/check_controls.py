# runs checks on the the controls generated in create_baseyear_controls.py
# outputs the results to "check_controls_{}.log"

import argparse, os, logging
import numpy, pandas
from operator import itemgetter, attrgetter
import itertools


parser = argparse.ArgumentParser()
parser.add_argument("model_year", type=int)
args = parser.parse_args()

LOG_FILE = "check_controls_{0}.log".format(args.model_year)
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG)


hh_taz_controls = os.path.join("households", "data", "{}_TAZ_controls.csv".format(args.model_year))
hh_maz_controls = os.path.join("households", "data", "{}_MAZ_controls.csv".format(args.model_year))
maz_taz_xwalk = os.path.join("households", "data", "geo_cross_walk.csv")
hh_taz_controls = pandas.read_csv(hh_taz_controls)
hh_maz_controls = pandas.read_csv(hh_maz_controls)
maz_taz_xwalk = pandas.read_csv(maz_taz_xwalk)

# 1) check for zones with very small numbers of households in them, than can cause integerizer to fail
# if there are only a couple of households in a zone, it can be impossible to satisfy the constraints

# check maz hh numbers
for maz in hh_maz_controls.index:
    maz_id = hh_maz_controls['MAZ'][maz]
    if hh_maz_controls['num_hh'][maz] < 5:
        logging.warning("MAZ {}: Less than 5 HHs-- integerizer may fail, impossible to satisfy the constraints".format(maz_id))
# check taz hh numbers
# group MAZs by their TAZ to later get num_hhs for each TAZ
taz_mazs = []
xwalk_taz_sorted = sorted(maz_taz_xwalk.values, key=itemgetter(1))
for taz, maz in itertools.groupby(xwalk_taz_sorted, key=itemgetter(1)):
    taz_mazs.append(list(maz))
for taz in hh_taz_controls.index:
    maz_group = taz_mazs[taz]
    maz_ids = [x[0] for x in maz_group]
    taz_num_hh = []
    for maz in maz_ids:
        num_hh = hh_maz_controls.loc[hh_maz_controls['MAZ'] == maz, 'num_hh'].iloc[0]
        taz_num_hh.append(num_hh)
    taz_total_hhs = sum(taz_num_hh)
    taz_id = hh_taz_controls['TAZ'][taz]
    if taz_total_hhs < 5:
        logging.warning("TAZ {}: Less than 5 HHs-- integerizer may fail, impossible to satisfy the constraints".format(taz_id))


# 2) for each TAZ, check that the number of workers is not greater than the number of persons (based on hh size) 

for taz in hh_taz_controls.index:
    maz_group = taz_mazs[taz]
    maz_ids = [x[0] for x in maz_group]
    taz_hh_persons = []
    for maz in maz_ids:
        hh_size_1 = hh_maz_controls.loc[hh_maz_controls['MAZ'] == maz, 'hh_size_1'].iloc[0]
        hh_size_2 = hh_maz_controls.loc[hh_maz_controls['MAZ'] == maz, 'hh_size_2'].iloc[0]
        hh_size_3 = hh_maz_controls.loc[hh_maz_controls['MAZ'] == maz, 'hh_size_3'].iloc[0]
        hh_size_4 = hh_maz_controls.loc[hh_maz_controls['MAZ'] == maz, 'hh_size_4_plus'].iloc[0]        
        hh_persons = (hh_size_1)*1 + (hh_size_2)*2 + (hh_size_3)*3 + (hh_size_4)*4
        taz_hh_persons.append(hh_persons)
    taz_total_hh_persons = sum(taz_hh_persons)
    taz_total_workers = (hh_taz_controls['hh_wrks_0'][taz])*0 + (hh_taz_controls['hh_wrks_1'][taz])*1 + (hh_taz_controls['hh_wrks_2'][taz])*2 + (hh_taz_controls['hh_wrks_3_plus'][taz])*3
    taz_id = hh_taz_controls['TAZ'][taz]
    if taz_total_workers > taz_total_hh_persons:
        logging.warning("TAZ {}: TAZ total number of workers > TAZ total persons (by hh size)".format(taz_id))


# 3) for each TAZ, check that the number of hhs with/without kids make sense given the number of persons of particular age groups

for taz in hh_taz_controls.index:
    taz_id = hh_taz_controls['TAZ'][taz]
    if hh_taz_controls['hh_kids_yes'][taz] > hh_taz_controls['pers_age_00_19'][taz]:
        logging.warning("TAZ {}: number of HH with kids > persons age 0-19".format(taz_id))
    if hh_taz_controls['hh_kids_no'][taz]  > (hh_taz_controls['pers_age_00_19'][taz] + hh_taz_controls['pers_age_20_34'][taz] + hh_taz_controls['pers_age_35_64'][taz] + hh_taz_controls['pers_age_65_plus'][taz]):
        logging.warning("TAZ {}: number of HH with no kids > persons of all ages".format(taz_id))