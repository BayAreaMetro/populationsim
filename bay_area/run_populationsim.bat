::
:: Batch script to run the population simulation for the bay area
:: Assumes activitysim is cloned to %USERPROFILE%\Documents\GitHub
:: and the YEAR is passed as the argument to this batch script.
::
:: e.g. run_populationsim 2010
::
echo on
setlocal EnableDelayedExpansion

:: should be TM1 or TM2
set MODELTYPE=TM1

:: should be the urbansim run number from the control files
set PETRALEPATH=X:\petrale
set URBANSIMPATH=\\tsclient\C\Users\ftsang\Box\Modeling and Surveys\Urban Modeling\Bay Area UrbanSim\PBA50\EIR runs\Alt2 (s28) runs\Alt2_v1
set BAUS_RUNNUM=run374
set OUTPUT_SUFFIX=PBA50EIRalt2_20210311_!BAUS_RUNNUM!

:: assume argument is year
set YEARS=%1
echo YEARS=[!YEARS!]

:: Need to be able to import activitysim and populationsim
:: Assume activitysim is cloned to %USERPROFILE%\Documents\GitHub
set PYTHONPATH=%USERPROFILE%\Documents\GitHub\activitysim;%~dp0\..
echo PYTHONPATH=[!PYTHONPATH!]

set TEST_PUMA=
:: set TEST_PUMA=02402
if "%TEST_PUMA%"=="" (
  echo No TEST_PUMA set -- running full region.
  set TEST_PUMA_FLAG=
  set PUMA_SUFFIX=
)
if "%TEST_PUMA%" NEQ "" (
  echo Using TEST_PUMA [%TEST_PUMA%]
  set TEST_PUMA_FLAG=--test_PUMA %TEST_PUMA%
  set PUMA_SUFFIX=_puma%TEST_PUMA%
)

:create_seed
if not exist hh_gq\data\seed_households.csv (
  python create_seed_population.py
  if ERRORLEVEL 1 goto error
)

:year_loop
for %%Y in (!YEARS!) do (
  set YEAR=%%Y
  echo YEAR=[!YEAR!]

  rem Use UrbanSim run number except for base year -- then use census
  set RUN_NUM=!BAUS_RUNNUM!
  if !YEAR!==2015 (
    set RUN_NUM=census
    copy "%PETRALEPATH%\applications\travel_model_lu_inputs\2015\TAZ1454 2015 Popsim Vars.csv"          hh_gq\data\census_taz_summaries_2015.csv
    copy "%PETRALEPATH%\applications\travel_model_lu_inputs\2015\TAZ1454 2015 Popsim Vars County.csv"   hh_gq\data\census_county_marginals_2015.csv
    copy "%PETRALEPATH%\applications\travel_model_lu_inputs\2015\TAZ1454 2015 Popsim Vars Region.csv"   hh_gq\data\census_regional_marginals_2015.csv
   )
  if !YEAR! GTR 2015 (
    rem copy "%URBANSIMPATH%\%BAUS_RUNNUM%_taz_summaries_!YEAR!_UBI.csv" "hh_gq\data\%BAUS_RUNNUM%_taz_summaries_!YEAR!.csv"
    copy "%URBANSIMPATH%\%BAUS_RUNNUM%_taz_summaries_!YEAR!.csv"      hh_gq\data
    copy "%URBANSIMPATH%\%BAUS_RUNNUM%_county_marginals_!YEAR!.csv"   hh_gq\data
    copy "%URBANSIMPATH%\%BAUS_RUNNUM%_regional_marginals_!YEAR!.csv" hh_gq\data
  )
  echo RUN_NUM=[!RUN_NUM!]
  rem add combined hh gq columns (e.g. make gq into one-person households)
  python add_hhgq_combined_controls.py --model_year !YEAR! --run_num !RUN_NUM!
  if ERRORLEVEL 1 goto error

  rem create the final output directory
  if not exist output_!YEAR!!PUMA_SUFFIX! ( mkdir output_!YEAR!!PUMA_SUFFIX! )

  :: tm2 version can be updated to use UrbanSim (not census) controls
  rem check controls
  :: python check_controls.py --model_year !YEAR! --model_type !MODELTYPE! --run_num !RUN_NUM!
  :: if ERRORLEVEL 1 goto error

  :: tm2 version will require small changes to the config if using UrbanSim controls 
  rem synthesize households
  mkdir hh_gq\output_!YEAR!!PUMA_SUFFIX!
  python run_populationsim.py --run_num !RUN_NUM! --model_year !YEAR!  --config hh_gq\configs_%MODELTYPE% --output hh_gq\output_!YEAR!!PUMA_SUFFIX! --data hh_gq\data
  if ERRORLEVEL 1 goto error

  rem put it together
  python combine_households_gq.py !TEST_PUMA_FLAG! --run_num !RUN_NUM! --model_type !MODELTYPE! --model_year !YEAR!
  if ERRORLEVEL 1 goto error

  move output_!YEAR!        output_!YEAR!_!OUTPUT_SUFFIX!
  move hh_gq\output_!YEAR!  hh_gq\output_!YEAR!_!OUTPUT_SUFFIX!
  :: save input also
  copy /Y "hh_gq\data\%BAUS_RUNNUM%_taz_summaries_!YEAR!.csv"      "hh_gq\data\taz_summaries_!OUTPUT_SUFFIX!_!YEAR!.csv"
  copy /Y "hh_gq\data\%BAUS_RUNNUM%_regional_marginals_!YEAR!.csv" "hh_gq\data\regional_marginals_!OUTPUT_SUFFIX!_!YEAR!.csv"
)

:success
echo Completed run_populationsim.bat successfully!
goto end

:error
echo An error occurred

:end