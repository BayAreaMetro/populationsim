@echo off
REM Dedicated PopulationSim runner with high priority
echo Starting PopulationSim with high priority...
cd /d "C:\GitHub\populationsim_update\bay_area"

REM Use direct Python path to avoid conda activation issues
echo Using Python: C:\Users\schildress\AppData\Local\anaconda3\python.exe
echo Starting PopulationSim synthesis...

REM Set high priority and run PopulationSim
start /HIGH "PopulationSim" "C:\Users\schildress\AppData\Local\anaconda3\python.exe" run_populationsim_tm2.py

echo PopulationSim started in high priority mode in separate window
echo You can monitor progress in the new PopulationSim window
pause
