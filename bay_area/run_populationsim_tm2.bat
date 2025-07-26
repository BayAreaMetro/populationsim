::
:: Batch script to run the population simulation for the bay area
:: Pass YEAR as the argument to this batch script.
::
:: e.g. run_populationsim 2010
::
echo on
setlocal EnableDelayedExpansion

:: Set up PopulationSim conda environment
set CONDA_PATH=C:\Users\schildress\AppData\Local\anaconda3
set POPSIM_ENV=popsim
set PYTHON_PATH=%CONDA_PATH%\envs\%POPSIM_ENV%\python.exe

:: should be TM1 or TM2
set MODELTYPE=TM2
set YEAR=2023

:: for a forecast, copies marginals from         "%URBANSIMPATH%\travel_model_summaries\%BAUS_RUNNUM%_xxx_summaries_!YEAR!.csv"
:: for past/current year, copies marginals from  "%TMPATH%\!YEAR!""
set TMPATH=output_2023
::set URBANSIMPATH=M:\urban_modeling\baus\PBA50Plus\PBA50Plus_FinalBlueprint\PBA50Plus_Final_Blueprint_v65
:: used in OUTPUT_SUFFIX as well; use "census" for non-BAUS-based run
::set BAUS_RUNNUM=BAUS_RUNNUM=PBA50Plus_Final_Blueprint_v65
:: OUTPUT DIR will be X:\populationsim_outputs\hh_gq\output_!OUTPUT_SUFFIX!_!YEAR!!PUMA_SUFFIX!_!BAUS_RUNNUM!
::set OUTPUT_SUFFIX=FBP_20250522

rem create the final output directory that populationsim will write to
set OUTPUT_DIR=output_2023\populationsim_run
echo OUTPUT_DIR=[!OUTPUT_DIR!]
if not exist !OUTPUT_DIR! ( mkdir !OUTPUT_DIR! )

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
  echo Creating seed population files...
  "%PYTHON_PATH%" create_seed_population.py
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
      copy /y "%TMPATH%\!YEAR!\TAZ1454 !YEAR! Popsim Vars.csv"          hh_gq\data\taz_summaries.csv
      copy /y "%TMPATH%\!YEAR!\TAZ1454 !YEAR! Popsim Vars County.csv"   hh_gq\data\county_marginals.csv

      rem Verify that the file copy MUST succeed or we'll run populationsim with the wrong input
      fc /b "%TMPATH%\!YEAR!\TAZ1454 !YEAR! Popsim Vars.csv"         hh_gq\data\taz_summaries.csv > nul
      if errorlevel 1 goto error
      fc /b "%TMPATH%\!YEAR!\TAZ1454 !YEAR! Popsim Vars County.csv"  hh_gq\data\county_marginals.csv > nul
      if errorlevel 1 goto error
    )
    if !FORECAST!==1 (
      rem copy "%URBANSIMPATH%\travel_model_summaries\%BAUS_RUNNUM%_taz_summaries_!YEAR!_UBI.csv" "hh_gq\data\%BAUS_RUNNUM%_taz_summaries_!YEAR!.csv"
      copy /y "%URBANSIMPATH%\travel_model_summaries\%BAUS_RUNNUM%_taz1_summary_!YEAR!.csv"     hh_gq\data\taz_summaries.csv
      copy /y "%URBANSIMPATH%\travel_model_summaries\%BAUS_RUNNUM%_county_marginals_!YEAR!.csv" hh_gq\data\county_marginals.csv

      rem Verify that the file copy MUST succeed or we'll run populationsim with the wrong input
      fc /b "%URBANSIMPATH%\travel_model_summaries\%BAUS_RUNNUM%_taz1_summary_!YEAR!.csv"       hh_gq\data\taz_summaries.csv > nul
      if errorlevel 1 goto error
      fc /b  "%URBANSIMPATH%\travel_model_summaries\%BAUS_RUNNUM%_county_marginals_!YEAR!.csv"  hh_gq\data\county_marginals.csv > nul
      if errorlevel 1 goto error
    )
  )

  if !MODELTYPE!==TM2 (
    if !YEAR!==2015 (
      copy /y "%TMPATH%\maz_marginals.csv"    hh_gq\data\maz_marginals.csv
      copy /y "%TMPATH%\taz2_marginals.csv"   hh_gq\data\taz_marginals.csv
      copy /y "%TMPATH%\county_marginals.csv" hh_gq\data\county_marginals.csv
      copy /y "%TMPATH%\geo_cross_walk_tm2.csv" hh_gq\data\geo_cross_walk_tm2.csv

      rem Verify that the file copy MUST succeed or we'll run populationsim with the wrong input
      fc /b "%TMPATH%\maz_marginals.csv"    hh_gq\data\maz_marginals.csv > nul
      if errorlevel 1 goto error
      fc /b "%TMPATH%\taz2_marginals.csv"   hh_gq\data\taz_marginals.csv > nul
      if errorlevel 1 goto error
      fc /b "%TMPATH%\county_marginals.csv" hh_gq\data\county_marginals.csv > nul
      if errorlevel 1 goto error
      fc /b "%TMPATH%\geo_cross_walk_tm2.csv" hh_gq\data\geo_cross_walk_tm2.csv > nul
      if errorlevel 1 goto error

    )
    if !YEAR!==2023 (
      copy /y "%TMPATH%\maz_marginals.csv"    hh_gq\data\maz_marginals.csv
      copy /y "%TMPATH%\taz_marginals.csv"   hh_gq\data\taz_marginals.csv
      copy /y "%TMPATH%\county_marginals.csv" hh_gq\data\county_marginals.csv
      copy /y "%TMPATH%\geo_cross_walk_tm2_filtered.csv" hh_gq\data\geo_cross_walk_tm2.csv

      rem Verify that the file copy MUST succeed or we'll run populationsim with the wrong input
      fc /b "%TMPATH%\maz_marginals.csv"    hh_gq\data\maz_marginals.csv > nul
      if errorlevel 1 goto error
      fc /b "%TMPATH%\taz_marginals.csv"   hh_gq\data\taz_marginals.csv > nul
      if errorlevel 1 goto error
      fc /b "%TMPATH%\county_marginals.csv" hh_gq\data\county_marginals.csv > nul
      if errorlevel 1 goto error
      fc /b "%TMPATH%\geo_cross_walk_tm2_filtered.csv" hh_gq\data\geo_cross_walk_tm2.csv > nul
      if errorlevel 1 goto error

    )
  )
  echo RUN_NUM=[!RUN_NUM!]
  rem add combined hh gq columns (e.g. make gq into one-person households)
  "%PYTHON_PATH%" add_hhgq_combined_controls.py --model_type !MODELTYPE!
  if ERRORLEVEL 1 goto error

 

  :: tm2 version will require small changes to the config if using UrbanSim controls
  rem Synthesize households and persons
  rem This will create the following in OUTPUT_DIR
  rem   - synthetic_[households,persons].csv
  rem   - final_expanded_household_ids.csv
  rem   - final_summary_COUNTY_[1-9].csv
  rem   - final_summary_TAZ.csv
  rem   - populationsim.log, timing_log.csv, mem.csv
  rem   - pipeline.h5
  :: skip if ran already
  if exist !OUTPUT_DIR!\synthetic_households.csv (
    echo poputionsim output files exist in !OUTPUT_DIR! already.
  )
  if not exist !OUTPUT_DIR!\synthetic_households.csv (
    "%PYTHON_PATH%" run_populationsim.py --config hh_gq\configs_%MODELTYPE% --output !OUTPUT_DIR! --data hh_gq\data
    if ERRORLEVEL 1 goto error
  )

  rem Postprocess and recode
  "%PYTHON_PATH%" postprocess_recode.py !TEST_PUMA_FLAG! --model_type !MODELTYPE! --directory !OUTPUT_DIR! --year !YEAR!
  if ERRORLEVEL 1 goto error
  rem Note: this creates OUTPUT_DIR\summary_melt.csv so copy validation.twb into place
  copy /y validation.twb !OUTPUT_DIR!

  :: save input also
  if !MODELTYPE!==TM1 (
    move /y "hh_gq\data\taz_summaries.csv"       !OUTPUT_DIR!
    move /y "hh_gq\data\taz_summaries_hhgq.csv"  !OUTPUT_DIR!
    move /y "hh_gq\data\county_marginals.csv"    !OUTPUT_DIR!
    move /y "hh_gq\data\regional_marginals.csv"  !OUTPUT_DIR!
  )
  if !MODELTYPE!==TM2 (
    move /y "hh_gq\data\maz_marginals.csv"        !OUTPUT_DIR!
    move /y "hh_gq\data\taz_marginals.csv"        !OUTPUT_DIR!
    move /y "hh_gq\data\county_marginals.csv"     !OUTPUT_DIR!
  )
)

:success
echo Completed run_populationsim_tm2.bat successfully!
goto end

:error
echo An error occurred

:end
