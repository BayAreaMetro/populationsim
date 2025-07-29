::
:: Batch script to run the population simulation for the bay area
:: Pass YEAR as the argument to this batch script.
::
:: e.g. run_populationsim 2010
::
:: Configuration flags - set to 1 to force step execution, 0 to skip if files exist
set FORCE_SEED=1
set FORCE_CONTROLS=0
set FORCE_HHGQ=0
set FORCE_POPULATIONSIM=0
set FORCE_POSTPROCESS=0

echo on
setlocal EnableDelayedExpansion

echo.
echo ==========================================
echo    Bay Area PopulationSim TM2 Workflow
echo ==========================================

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

echo.
echo ===== WORKFLOW STATUS CHECK =====
echo Checking existing files to determine what steps need to run...

:: Check Step 1: Seed Population
if exist "hh_gq\data\seed_households.csv" (
  echo [COMPLETE] Step 1: Seed Population - files exist
) else (
  echo [NEEDED]   Step 1: Seed Population - files missing
)

:: Check Step 2: Control Generation  
set CONTROLS_EXIST=1
if not exist "hh_gq\data\maz_marginals.csv" set CONTROLS_EXIST=0
if not exist "hh_gq\data\taz_marginals.csv" set CONTROLS_EXIST=0
if not exist "hh_gq\data\county_marginals.csv" set CONTROLS_EXIST=0
if not exist "hh_gq\data\geo_cross_walk_tm2.csv" set CONTROLS_EXIST=0
if !CONTROLS_EXIST!==1 (
  echo [COMPLETE] Step 2: Control Generation - all files exist
) else (
  echo [NEEDED]   Step 2: Control Generation - some files missing
)

:: Check Step 3: Group Quarters Integration
if exist "hh_gq\data\maz_marginals_hhgq.csv" (
  echo [COMPLETE] Step 3: Group Quarters Integration - files exist
) else (
  echo [NEEDED]   Step 3: Group Quarters Integration - files missing
)

:: Check Step 4: PopulationSim Synthesis
if exist "!OUTPUT_DIR!\synthetic_households.csv" (
  echo [COMPLETE] Step 4: PopulationSim Synthesis - output exists
) else (
  echo [NEEDED]   Step 4: PopulationSim Synthesis - output missing
)

:: Check Step 5: Post-processing
if exist "!OUTPUT_DIR!\summary_melt.csv" (
  echo [COMPLETE] Step 5: Post-processing - output exists
) else (
  echo [NEEDED]   Step 5: Post-processing - output missing
)

echo.
echo Force flags: SEED=!FORCE_SEED! CONTROLS=!FORCE_CONTROLS! HHGQ=!FORCE_HHGQ! POPSIM=!FORCE_POPULATIONSIM! POST=!FORCE_POSTPROCESS!
echo Press Ctrl+C to stop, or any key to continue...
pause > nul

:create_seed
echo.
echo ===== STEP 1: SEED POPULATION =====
if !FORCE_SEED!==1 (
  echo FORCE_SEED=1: Regenerating seed files...
  echo [%DATE% %TIME%] Starting seed generation with enhanced logging
  echo This process typically takes 10-15 minutes - please be patient...
  "%PYTHON_PATH%" create_seed_population_tm2_verbose.py
  if ERRORLEVEL 1 (
    echo [%DATE% %TIME%] ERROR: Seed generation failed!
    goto error
  ) else (
    echo [%DATE% %TIME%] SUCCESS: Seed generation completed!
  )
) else (
  if not exist hh_gq\data\seed_households.csv (
    echo Seed files missing - creating seed population files...
    echo [%DATE% %TIME%] Starting seed generation with enhanced logging
    echo This process typically takes 10-15 minutes - please be patient...
    "%PYTHON_PATH%" create_seed_population_tm2_verbose.py
    if ERRORLEVEL 1 (
      echo [%DATE% %TIME%] ERROR: Seed generation failed!
      goto error
    ) else (
      echo [%DATE% %TIME%] SUCCESS: Seed generation completed!
    )
  ) else (
    echo Seed files already exist - skipping seed generation
  )
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
    echo.
    echo ===== STEP 2: CONTROL GENERATION =====
    set NEED_CONTROLS=0
    if !FORCE_CONTROLS!==1 set NEED_CONTROLS=1
    if not exist "hh_gq\data\maz_marginals.csv" set NEED_CONTROLS=1
    if not exist "hh_gq\data\taz_marginals.csv" set NEED_CONTROLS=1
    if not exist "hh_gq\data\county_marginals.csv" set NEED_CONTROLS=1
    if not exist "hh_gq\data\geo_cross_walk_tm2.csv" set NEED_CONTROLS=1
    
    if !NEED_CONTROLS!==1 (
      if !FORCE_CONTROLS!==1 (
        echo FORCE_CONTROLS=1: Regenerating control files...
      ) else (
        echo Control files missing - generating TM2 controls for year !YEAR!...
      )
      "%PYTHON_PATH%" create_baseyear_controls_23_tm2.py --output_dir hh_gq\data
      if ERRORLEVEL 1 goto error
      
      rem Rename files to PopulationSim expected names
      if exist "hh_gq\data\geo_cross_walk_tm2_updated.csv" (
        move /y "hh_gq\data\geo_cross_walk_tm2_updated.csv" "hh_gq\data\geo_cross_walk_tm2.csv"
      )
    ) else (
      echo Control files already exist - skipping control generation
    )
  )
  echo RUN_NUM=[!RUN_NUM!]
  
  echo.
  echo ===== STEP 3: GROUP QUARTERS INTEGRATION =====
  set NEED_HHGQ=0
  if !FORCE_HHGQ!==1 set NEED_HHGQ=1
  if not exist "hh_gq\data\maz_marginals_hhgq.csv" set NEED_HHGQ=1
  if not exist "hh_gq\data\taz_marginals_hhgq.csv" set NEED_HHGQ=1
  
  if !NEED_HHGQ!==1 (
    if !FORCE_HHGQ!==1 (
      echo FORCE_HHGQ=1: Regenerating group quarters files...
    ) else (
      echo Group quarters files missing - adding combined hh gq columns...
    )
    "%PYTHON_PATH%" add_hhgq_combined_controls.py --model_type !MODELTYPE!
    if ERRORLEVEL 1 goto error
  ) else (
    echo Group quarters files already exist - skipping HHGQ integration
  )

 

  echo.
  echo ===== STEP 4: POPULATION SYNTHESIS =====
  :: tm2 version will require small changes to the config if using UrbanSim controls
  rem Synthesize households and persons
  rem This will create the following in OUTPUT_DIR
  rem   - synthetic_[households,persons].csv
  rem   - final_expanded_household_ids.csv
  rem   - final_summary_COUNTY_[1-9].csv
  rem   - final_summary_TAZ.csv
  rem   - populationsim.log, timing_log.csv, mem.csv
  rem   - pipeline.h5
  
  set NEED_POPSIM=0
  if !FORCE_POPULATIONSIM!==1 set NEED_POPSIM=1
  if not exist "!OUTPUT_DIR!\synthetic_households.csv" set NEED_POPSIM=1
  
  if !NEED_POPSIM!==1 (
    if !FORCE_POPULATIONSIM!==1 (
      echo FORCE_POPULATIONSIM=1: Re-running PopulationSim synthesis...
    ) else (
      echo PopulationSim output missing - running synthesis...
    )
    "%PYTHON_PATH%" run_populationsim.py --config hh_gq\configs_%MODELTYPE% --output !OUTPUT_DIR! --data hh_gq\data
    if ERRORLEVEL 1 goto error
  ) else (
    echo PopulationSim output already exists - skipping synthesis
  )

  echo.
  echo ===== STEP 5: POST-PROCESSING =====
  set NEED_POSTPROCESS=0
  if !FORCE_POSTPROCESS!==1 set NEED_POSTPROCESS=1
  if not exist "!OUTPUT_DIR!\summary_melt.csv" set NEED_POSTPROCESS=1
  
  if !NEED_POSTPROCESS!==1 (
    if !FORCE_POSTPROCESS!==1 (
      echo FORCE_POSTPROCESS=1: Re-running post-processing...
    ) else (
      echo Post-processing files missing - running postprocess and recode...
    )
    "%PYTHON_PATH%" postprocess_recode.py !TEST_PUMA_FLAG! --model_type !MODELTYPE! --directory !OUTPUT_DIR! --year !YEAR!
    if ERRORLEVEL 1 goto error
    rem Note: this creates OUTPUT_DIR\summary_melt.csv so copy validation.twb into place
    copy /y validation.twb !OUTPUT_DIR!

    :: Archive input files to output directory for reference
    if !MODELTYPE!==TM1 (
      copy /y "hh_gq\data\taz_summaries.csv"       !OUTPUT_DIR!
      copy /y "hh_gq\data\taz_summaries_hhgq.csv"  !OUTPUT_DIR!
      copy /y "hh_gq\data\county_marginals.csv"    !OUTPUT_DIR!
      copy /y "hh_gq\data\regional_marginals.csv"  !OUTPUT_DIR!
    )
    if !MODELTYPE!==TM2 (
      copy /y "hh_gq\data\maz_marginals.csv"        !OUTPUT_DIR!
      copy /y "hh_gq\data\taz_marginals.csv"        !OUTPUT_DIR!
      copy /y "hh_gq\data\county_marginals.csv"     !OUTPUT_DIR!
      copy /y "hh_gq\data\geo_cross_walk_tm2.csv"   !OUTPUT_DIR!
    )
  ) else (
    echo Post-processing files already exist - skipping post-processing
  )
)

:success
echo.
echo ==========================================
echo Completed run_populationsim_tm2.bat successfully!
echo.
echo Final outputs are in: !OUTPUT_DIR!
echo Key files created:
if exist "!OUTPUT_DIR!\synthetic_households.csv" (
  echo   - synthetic_households.csv ^(main output^)
  echo   - synthetic_persons.csv ^(main output^)
)
if exist "!OUTPUT_DIR!\summary_melt.csv" (
  echo   - summary_melt.csv ^(for validation^)
)
echo   - populationsim.log ^(detailed log^)
echo ==========================================
goto end

:error
echo An error occurred

:end
