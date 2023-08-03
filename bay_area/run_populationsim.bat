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
set URBANSIMPATH=L:\Application\Model_One\TransitRecovery\land_use_preprocessing
:: modified version
set BAUS_RUNNUM=census
set OUTPUT_SUFFIX=PBA50Plus_20230803

:: assume argument is year
set YEARS=%1
echo YEARS=[!YEARS!]

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
  if !MODELTYPE!==TM1 (
    set FORECAST=1
    if !YEAR! == 2015 (set FORECAST=0)
    if !YEAR! == 2020 (set FORECAST=0)
    if !YEAR! == 2023 (set FORECAST=0)
    echo FORECAST=!FORECAST!
    if !FORECAST!==0 (
      set RUN_NUM=census
      copy /y "%PETRALEPATH%\applications\travel_model_lu_inputs\!YEAR!\TAZ1454 !YEAR! Popsim Vars.csv"          hh_gq\data\taz_summaries.csv
      copy /y "%PETRALEPATH%\applications\travel_model_lu_inputs\!YEAR!\TAZ1454 !YEAR! Popsim Vars County.csv"   hh_gq\data\county_marginals.csv

      rem Verify that the file copy MUST succeed or we'll run populationsim with the wrong input
      fc /b "%PETRALEPATH%\applications\travel_model_lu_inputs\!YEAR!\TAZ1454 !YEAR! Popsim Vars.csv"         hh_gq\data\taz_summaries.csv > nul
      if errorlevel 1 goto error
      fc /b "%PETRALEPATH%\applications\travel_model_lu_inputs\!YEAR!\TAZ1454 !YEAR! Popsim Vars County.csv"  hh_gq\data\county_marginals.csv > nul
      if errorlevel 1 goto error
    )
    if !FORECAST!==1 (
      rem copy "%URBANSIMPATH%\%BAUS_RUNNUM%_taz_summaries_!YEAR!_UBI.csv" "hh_gq\data\%BAUS_RUNNUM%_taz_summaries_!YEAR!.csv"
      copy /y "%URBANSIMPATH%\%BAUS_RUNNUM%_taz_summaries_!YEAR!.csv"      hh_gq\data\taz_summaries.csv
      copy /y "%URBANSIMPATH%\%BAUS_RUNNUM%_county_marginals_!YEAR!.csv"   hh_gq\data\county_marginals.csv

      rem Verify that the file copy MUST succeed or we'll run populationsim with the wrong input
      fc /b "%URBANSIMPATH%\%BAUS_RUNNUM%_taz_summaries_!YEAR!.csv"     hh_gq\data\taz_summaries.csv > nul
      if errorlevel 1 goto error
      fc /b  "%URBANSIMPATH%\%BAUS_RUNNUM%_county_marginals_!YEAR!.csv" hh_gq\data\county_marginals.csv > nul
      if errorlevel 1 goto error
    )
  )

  if !MODELTYPE!==TM2 (
    if !YEAR!==2015 (
      copy /y "%URBANSIMPATH%\maz_marginals.csv"    hh_gq\data\maz_marginals_2015.csv
      copy /y "%URBANSIMPATH%\taz2_marginals.csv"   hh_gq\data\taz_marginals_2015.csv
      copy /y "%URBANSIMPATH%\county_marginals.csv" hh_gq\data\county_marginals_2015.csv

      rem Verify that the file copy MUST succeed or we'll run populationsim with the wrong input
      fc /b "%URBANSIMPATH%\maz_marginals.csv"    hh_gq\data\maz_marginals_2015.csv > nul
      if errorlevel 1 goto error
      fc /b "%URBANSIMPATH%\taz2_marginals.csv"   hh_gq\data\taz_marginals_2015.csv > nul
      if errorlevel 1 goto error
      fc /b "%URBANSIMPATH%\county_marginals.csv" hh_gq\data\county_marginals_2015.csv > nul
      if errorlevel 1 goto error
    )
  )
  echo RUN_NUM=[!RUN_NUM!]
  rem add combined hh gq columns (e.g. make gq into one-person households)
  python add_hhgq_combined_controls.py --model_type !MODELTYPE!
  if ERRORLEVEL 1 goto error

  rem create the final output directory that populationsim will write to
  set OUTPUT_DIR=hh_gq\output_!OUTPUT_SUFFIX!_!YEAR!!PUMA_SUFFIX!_!BAUS_RUNNUM!
  echo OUTPUT_DIR=[!OUTPUT_DIR!]
  if not exist !OUTPUT_DIR! ( mkdir !OUTPUT_DIR! )

  :: tm2 version will require small changes to the config if using UrbanSim controls 
  rem synthesize households
  python run_populationsim.py --config hh_gq\configs_%MODELTYPE% --output !OUTPUT_DIR! --data hh_gq\data
  if ERRORLEVEL 1 goto error

  goto end
  rem put it together
  python combine_households_gq.py !TEST_PUMA_FLAG! --run_num !RUN_NUM! --model_type !MODELTYPE! --model_year !YEAR!
  if ERRORLEVEL 1 goto error

  move output_!YEAR!!PUMA_SUFFIX!        output_!YEAR!_!OUTPUT_SUFFIX!
  move hh_gq\output_!YEAR!!PUMA_SUFFIX!  hh_gq\output_!YEAR!_!OUTPUT_SUFFIX!

  :: save input also
  if !MODELTYPE!==TM1 (
    copy /Y "hh_gq\data\taz_summaries.csv"       !OUTPUT_DIR!
    copy /Y "hh_gq\data\county_marginals.csv"    !OUTPUT_DIR!
    copy /Y "hh_gq\data\regional_marginals.csv"  !OUTPUT_DIR!
  )
  if !MODELTYPE!==TM2 (
      copy "hh_gq\data\maz_marginals.csv"        !OUTPUT_DIR!
      copy "hh_gq\data\taz_marginals.csv"        !OUTPUT_DIR!
      copy "hh_gq\data\county_marginals.csv"     !OUTPUT_DIR!
  )
)

:success
echo Completed run_populationsim.bat successfully!
goto end

:error
echo An error occurred

:end