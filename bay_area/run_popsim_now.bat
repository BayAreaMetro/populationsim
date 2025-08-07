@echo off
echo Starting PopulationSim TM2 for 2023...
echo Current directory: %CD%
echo.

REM Change to bay_area directory
cd /d "c:\GitHub\populationsim\bay_area"

REM Run PopulationSim with proper Python environment
echo Running: python run_populationsim_tm2.py 2023
python run_populationsim_tm2.py 2023

echo.
echo PopulationSim execution completed.
pause
