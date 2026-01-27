@echo off
REM PopulationSim TM2 Environment Activation Script
REM Run this before working with the PopulationSim pipeline

echo Activating PopulationSim working environment...

REM Try different common conda installation paths
set CONDA_FOUND=0

if exist "C:\Users\%USERNAME%\AppData\Local\anaconda3\Scripts\activate.bat" (
    call "C:\Users\%USERNAME%\AppData\Local\anaconda3\Scripts\activate.bat" popsim_working
    set CONDA_FOUND=1
    goto :activated
)

if exist "C:\Users\%USERNAME%\miniconda3\Scripts\activate.bat" (
    call "C:\Users\%USERNAME%\miniconda3\Scripts\activate.bat" popsim_working
    set CONDA_FOUND=1
    goto :activated
)

if exist "C:\Anaconda3\Scripts\activate.bat" (
    call "C:\Anaconda3\Scripts\activate.bat" popsim_working
    set CONDA_FOUND=1
    goto :activated
)

if exist "C:\tools\miniconda3\Scripts\activate.bat" (
    call "C:\tools\miniconda3\Scripts\activate.bat" popsim_working
    set CONDA_FOUND=1
    goto :activated
)

:not_found
echo ERROR: Could not find conda installation
echo Please install Anaconda or Miniconda and create the popsim_working environment
echo using: conda env create -f environment_export.yml
goto :end

:activated
if %CONDA_FOUND%==1 (
    echo Environment activated successfully!
    echo Current Python: 
    python --version
    echo.
    echo PopulationSim status:
    python -c "import populationsim; print('PopulationSim available:', populationsim.__file__)"
    echo.
    echo Ready to run PopulationSim pipeline!
    echo Usage: python tm2_pipeline.py full --force
) else (
    goto :not_found
)

:end
