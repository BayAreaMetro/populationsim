setlocal EnableDelayedExpansion

:: Run the population simulation for the bay area
set PYTHONPATH=C:\Users\lzorn\Documents\activitysim;C:\Users\lzorn\Documents\populationsim

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
:: for %%Y in (2000 2005 2010 2015) do (
for %%Y in (2010) do (

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