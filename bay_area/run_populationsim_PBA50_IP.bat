::
:: Run PopulationSim for PBA50's Incremental Progress analysis
:: 
::
echo on
setlocal EnableDelayedExpansion

:: should be TM1 or TM2
set MODELTYPE=TM1

:: should be the urbansim run number from the control files
set YEAR=2035
set BAUS_RUNNUM=IP
set OUTPUT_SUFFIX=PBA50_20200323_%BAUS_RUNNUM%

:: Need to be able to import activitysim and populationsim
:: Assume activitysim is cloned to %USERPROFILE%\Documents\GitHub
set PYTHONPATH=%USERPROFILE%\Documents\GitHub\activitysim;%~dp0\..
echo PYTHONPATH=[%PYTHONPATH%]

:create_seed
if not exist hh_gq\data\seed_households.csv (
  python create_seed_population.py
  if ERRORLEVEL 1 goto error
)

copy "\\tsclient\M\Application\Model One\RTP2021\IncrementalProgress\Landuse\tazData_%YEAR%_%BAUS_RUNNUM%.csv" "hh_gq\data\%BAUS_RUNNUM%_taz_summaries_%YEAR%.csv"

rem add combined hh gq columns (e.g. make gq into one-person households)
python add_hhgq_combined_controls.py --model_year %YEAR% --run_num %BAUS_RUNNUM%
if ERRORLEVEL 1 goto error

rem create the final output directory
if not exist output_%YEAR% ( mkdir output_%YEAR% )

rem synthesize households
mkdir hh_gq\output_%YEAR%
python run_populationsim.py --run_num %BAUS_RUNNUM% --model_year %YEAR%  --config hh_gq\configs_TM1 --output hh_gq\output_%YEAR% --data hh_gq\data
if ERRORLEVEL 1 goto error

rem put it together
python combine_households_gq.py --run_num %BAUS_RUNNUM% --model_type TM1 --model_year %YEAR%
if ERRORLEVEL 1 goto error

move output_%YEAR%        output_%YEAR%_%OUTPUT_SUFFIX%
move hh_gq\output_%YEAR%  hh_gq\output_%YEAR%_%OUTPUT_SUFFIX%
:: save input also
copy /Y "hh_gq\data\%BAUS_RUNNUM%_taz_summaries_%YEAR%.csv"      "hh_gq\data\taz_summaries_%OUTPUT_SUFFIX%_%YEAR%.csv"
copy /Y "hh_gq\data\%BAUS_RUNNUM%_regional_marginals_%YEAR%.csv" "hh_gq\data\regional_marginals_%OUTPUT_SUFFIX%_%YEAR%.csv"


:success
echo Completed run_populationsim.bat successfully%
goto end

:error
echo An error occurred

:end