::
:: Configuration script for PopulationSim TM2 workflow
:: This script allows you to easily set which steps should be forced to run
::

@echo off
setlocal EnableDelayedExpansion

echo.
echo ==========================================
echo   PopulationSim TM2 Configuration
echo ==========================================
echo.
echo This script helps you configure which workflow steps to force.
echo By default, steps are skipped if their output files already exist.
echo.

set OUTPUT_DIR=output_2023\populationsim_run

echo Current file status:
echo.

:: Check Step 1: Seed Population
if exist "hh_gq\data\seed_households.csv" (
  echo [EXISTS] Step 1: Seed Population
  set SEED_STATUS=EXISTS
) else (
  echo [MISSING] Step 1: Seed Population  
  set SEED_STATUS=MISSING
)

:: Check Step 2: Control Generation  
set CONTROLS_EXIST=1
if not exist "hh_gq\data\maz_marginals.csv" set CONTROLS_EXIST=0
if not exist "hh_gq\data\taz_marginals.csv" set CONTROLS_EXIST=0
if not exist "hh_gq\data\county_marginals.csv" set CONTROLS_EXIST=0
if not exist "hh_gq\data\geo_cross_walk_tm2.csv" set CONTROLS_EXIST=0
if !CONTROLS_EXIST!==1 (
  echo [EXISTS] Step 2: Control Generation
  set CONTROLS_STATUS=EXISTS
) else (
  echo [MISSING] Step 2: Control Generation
  set CONTROLS_STATUS=MISSING
)

:: Check Step 3: Group Quarters Integration
if exist "hh_gq\data\maz_marginals_hhgq.csv" (
  echo [EXISTS] Step 3: Group Quarters Integration
  set HHGQ_STATUS=EXISTS
) else (
  echo [MISSING] Step 3: Group Quarters Integration
  set HHGQ_STATUS=MISSING
)

:: Check Step 4: PopulationSim Synthesis
if exist "%OUTPUT_DIR%\synthetic_households.csv" (
  echo [EXISTS] Step 4: PopulationSim Synthesis
  set POPSIM_STATUS=EXISTS
) else (
  echo [MISSING] Step 4: PopulationSim Synthesis
  set POPSIM_STATUS=MISSING
)

:: Check Step 5: Post-processing
if exist "%OUTPUT_DIR%\summary_melt.csv" (
  echo [EXISTS] Step 5: Post-processing
  set POST_STATUS=EXISTS
) else (
  echo [MISSING] Step 5: Post-processing
  set POST_STATUS=MISSING
)

echo.
echo ==========================================
echo Configuration Options:
echo.
echo 1. Run normal workflow (skip steps with existing files)
echo 2. Force regenerate all steps
echo 3. Force only PopulationSim synthesis (step 4)
echo 4. Force only from PopulationSim onwards (steps 4-5)
echo 5. Custom configuration
echo 6. Just show status and exit
echo.

set /p CHOICE="Enter your choice (1-6): "

if "%CHOICE%"=="1" (
  echo Running normal workflow...
  call run_populationsim_tm2.bat 2023
)

if "%CHOICE%"=="2" (
  echo Force regenerating all steps...
  :: Create temporary batch file with force flags
  (
    echo set FORCE_SEED=1
    echo set FORCE_CONTROLS=1
    echo set FORCE_HHGQ=1
    echo set FORCE_POPULATIONSIM=1
    echo set FORCE_POSTPROCESS=1
    echo call run_populationsim_tm2.bat 2023
  ) > temp_force_all.bat
  call temp_force_all.bat
  del temp_force_all.bat
)

if "%CHOICE%"=="3" (
  echo Force only PopulationSim synthesis...
  (
    echo set FORCE_SEED=0
    echo set FORCE_CONTROLS=0
    echo set FORCE_HHGQ=0
    echo set FORCE_POPULATIONSIM=1
    echo set FORCE_POSTPROCESS=0
    echo call run_populationsim_tm2.bat 2023
  ) > temp_force_popsim.bat
  call temp_force_popsim.bat
  del temp_force_popsim.bat
)

if "%CHOICE%"=="4" (
  echo Force from PopulationSim onwards...
  (
    echo set FORCE_SEED=0
    echo set FORCE_CONTROLS=0
    echo set FORCE_HHGQ=0
    echo set FORCE_POPULATIONSIM=1
    echo set FORCE_POSTPROCESS=1
    echo call run_populationsim_tm2.bat 2023
  ) > temp_force_end.bat
  call temp_force_end.bat
  del temp_force_end.bat
)

if "%CHOICE%"=="5" (
  echo.
  echo Custom Configuration:
  echo.
  
  set /p FORCE_SEED="Force seed generation? (0/1, current status: %SEED_STATUS%): "
  set /p FORCE_CONTROLS="Force control generation? (0/1, current status: %CONTROLS_STATUS%): "
  set /p FORCE_HHGQ="Force group quarters integration? (0/1, current status: %HHGQ_STATUS%): "
  set /p FORCE_POPULATIONSIM="Force PopulationSim synthesis? (0/1, current status: %POPSIM_STATUS%): "
  set /p FORCE_POSTPROCESS="Force post-processing? (0/1, current status: %POST_STATUS%): "
  
  (
    echo set FORCE_SEED=%FORCE_SEED%
    echo set FORCE_CONTROLS=%FORCE_CONTROLS%
    echo set FORCE_HHGQ=%FORCE_HHGQ%
    echo set FORCE_POPULATIONSIM=%FORCE_POPULATIONSIM%
    echo set FORCE_POSTPROCESS=%FORCE_POSTPROCESS%
    echo call run_populationsim_tm2.bat 2023
  ) > temp_custom.bat
  call temp_custom.bat
  del temp_custom.bat
)

if "%CHOICE%"=="6" (
  echo Current status shown above. Exiting.
)

echo.
echo Done.
pause
