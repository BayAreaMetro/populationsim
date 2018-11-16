::
:: Batch script to run the population simulation for the bay area
:: Assumes activitysim is cloned to %USERPROFILE%\Documents\activitysim
:: and the YEAR is passed as the argument to this batch script.
::
:: e.g. run_populationsim 2010
::
setlocal EnableDelayedExpansion

:: should be TM1 or TM2
set MODELTYPE=TM1

:: should be the urbansim run number from the control files
set BAUS_RUNNUM=run19 

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
python create_seed_population.py
if ERRORLEVEL 1 goto error

:year_loop
for %%Y in (!YEARS!) do (
  set YEAR=%%Y

  rem create the final output directory
  if not exist output_!YEAR!!PUMA_SUFFIX! ( mkdir output_!YEAR!!PUMA_SUFFIX! )

:: turned OFF while using UrbanSim controls instead of census data
::  rem create controls
::  python create_baseyear_controls.py !TEST_PUMA_FLAG! --model_year !YEAR!
::  if ERRORLEVEL 1 goto error

  :: tm2 version can be updated to use UrbanSim (not census) controls
  rem check controls
  python check_controls.py --model_year !YEAR! --model_type !MODELTYPE! --run_num !BAUS_RUNNUM!
  if ERRORLEVEL 1 goto error

  :: tm2 version will require small changes to the config if using UrbanSim controls 
  rem synthesize households
  mkdir households\output_!YEAR!!PUMA_SUFFIX!
  python run_populationsim.py --run_num !BAUS_RUNNUM! --model_year !YEAR!  --config households\configs_%MODELTYPE%     --output households\output_!YEAR!!PUMA_SUFFIX!      --data households\data
  if ERRORLEVEL 1 goto error

  :: tm2 version will require small changes to the config if if using UrbanSim controls
  rem synthesize group_quarters
  mkdir group_quarters\output_!YEAR!!PUMA_SUFFIX!
  python run_populationsim.py --run_num !BAUS_RUNNUM! --model_year !YEAR!  --config group_quarters\configs_%MODELTYPE% --output group_quarters\output_!YEAR!!PUMA_SUFFIX!  --data group_quarters\data
  if ERRORLEVEL 1 goto error

  rem put it together
  python combine_households_gq.py !TEST_PUMA_FLAG! --model_type !MODELTYPE! --model_year !YEAR!
  if ERRORLEVEL 1 goto error
)

:success
echo Completed run_populationsim.bat successfully!
goto end

:error
echo An error occurred

:end