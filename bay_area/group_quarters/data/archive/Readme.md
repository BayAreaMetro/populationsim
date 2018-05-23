# Control Files

* 20[00,05,10,15]_regionData.csv
* 20[00,05,10,15]_mazData.csv
  * Exported from PopSyn3 mysql database tables `control_totals_[meta,maz]_gq_year_20[00,05,10,15]`
  * Created by [`popsyn3\scripts\buildControls2010.R`](https://github.com/BayAreaMetro/popsyn3/blob/master/scripts/buildControls2010.R) and [`popsyn3\scripts\Step 03 Controls to Database.R`](https://github.com/BayAreaMetro/popsyn3/blob/master/scripts/Step%2003%20Controls%20to%20Database.R)
  * Note that the popsyn3 setup uses counties rather than PUMAs as the seed geography but calls them counties so the 20[00,05,10,15]_mazData.csv has the PUMA column renamed to COUNTY and a new *real* PUMA column added

# Geographic Crosswalk

* geographicCWalk.csv
  * Copied from popsyn3 crosswalk (https://mtcdrive.app.box.com/file/284232947138)
  * MAZ, TAZ deleted, MAZ_ORIGINAL and TAZ_ORIGINAL renamed to MAZ,TAZ

# Seed Table Files

* seed_households.csv
* seed_persons.csv
  * Created by [`create_seed_population.py`](..\..\create_seed_population.py)
  * These are large so they're not checked in.
