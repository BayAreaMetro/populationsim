::
:: Batch script to run the population simulation for the bay area
:: Assumes activitysim is cloned to %USERPROFILE%\Documents\activitysim
:: and the YEAR is passed as the argument to this batch script.
::
:: e.g. run_populationsim 2010
::
setlocal EnableDelayedExpansion

:: assume argument is year
set YEARS=%1
echo YEARS=[!YEARS!]

set PYTHONPATH=%USERPROFILE%\Documents\activitysim;%~dp0
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
for %%Y in (%YEARS%) do (

  rem create controls
  python create_baseyear_controls.py !TEST_PUMA_FLAG! %%Y
  if ERRORLEVEL 1 goto error

  rem households
  mkdir households\output_%%Y!PUMA_SUFFIX!
  python run_populationsim.py --model_year %%Y --config households\configs     --output households\output_%%Y!PUMA_SUFFIX!      --data households\data
  if ERRORLEVEL 1 goto error

  rem group_quarters
  mkdir group_quarters\output_%%Y!PUMA_SUFFIX!
  python run_populationsim.py --model_year %%Y --config group_quarters\configs --output group_quarters\output_%%Y!PUMA_SUFFIX!  --data group_quarters\data
  if ERRORLEVEL 1 goto error

  rem put it together
  python combine_households_gq.py !TEST_PUMA_FLAG! %%Y
  if ERRORLEVEL 1 goto error
)

:success
echo Completed run_populationsim.bat successfully!
goto end

:error
echo An error occurred

:end