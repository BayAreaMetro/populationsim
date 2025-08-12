# PopulationSim TM2 Environment Setup Guide

## Overview
This guide provides step-by-step instructions to replicate the exact working environment for the PopulationSim TM2 Bay Area pipeline on a new machine.

## Quick Start (Recommended)

### 1. Prerequisites
- Git installed
- Anaconda or Miniconda installed
- Windows 10/11 (tested environment)

### 2. Clone and Setup
```bash
# Clone repository
git clone https://github.com/BayAreaMetro/populationsim.git
cd populationsim
git checkout tm2

# Create exact working environment
conda env create -f bay_area/environment_export.yml

# Activate environment
conda activate popsim_working

# Install PopulationSim in development mode
pip install -e .
```

### 3. Verify Installation
```bash
cd bay_area
python setup_environment.py
```

### 4. Run Pipeline
```bash
python tm2_pipeline.py full --force
```

## Alternative: Windows Batch Script

For Windows users, you can use the provided batch script:

```cmd
cd bay_area
activate_environment.bat
```

This script will:
- Find your conda installation automatically
- Activate the popsim_working environment
- Verify the installation
- Provide usage instructions

## Environment Details

### Tested Configuration
- **OS**: Windows 10/11
- **Python**: 3.8.20 (CRITICAL - do not use 3.12)
- **Conda Environment**: popsim_working
- **PopulationSim**: Development version from this repository

### Key Package Versions
- pandas==2.0.3
- numpy==1.21.0
- activitysim==1.1.0
- geopandas==0.13.2
- ortools==9.12.4544

### File Purposes
- `environment_export.yml` - Exact conda environment specification
- `requirements.txt` - Reference file (use environment_export.yml instead)
- `activate_environment.bat` - Windows activation helper script
- `setup_environment.py` - Environment verification script

## Troubleshooting

### Common Issues

1. **"Python was not found"**
   - Solution: Make sure conda environment is activated
   - Use: `conda activate popsim_working`

2. **"conda: command not found"**
   - Solution: Restart terminal or run conda init
   - Alternative: Use full path to conda executable

3. **Package version conflicts**
   - Solution: Always use `environment_export.yml` 
   - Never mix pip requirements.txt with conda environment

4. **PopulationSim import errors**
   - Solution: Ensure `pip install -e .` was run after environment creation
   - Check: `python -c "import populationsim; print(populationsim.__file__)"`

### Environment Verification
```python
# Run this to verify your environment
import sys
print(f"Python version: {sys.version}")

import pandas as pd
print(f"Pandas version: {pd.__version__}")

import populationsim
print(f"PopulationSim path: {populationsim.__file__}")

print("Environment setup successful!")
```

## Path Dependencies

The pipeline uses these paths with automatic fallbacks:

### External Dependencies (Optional)
- `M:/Data/GIS layers/TM2_maz_taz_v2.2/` - MAZ/TAZ definitions
- `M:/Data/Census/NewCachedTablesForPopulationSimControls/` - Census cache
- `C:/GitHub/tm2py-utils/` - TM2 utilities

### Local Fallbacks (Included)
- `bay_area/local_data/gis/` - Local GIS files
- `bay_area/local_data/census/` - Local census cache
- `bay_area/data_cache/` - Local data cache

## Support

If you encounter issues:
1. Check this README first
2. Verify environment using `setup_environment.py`
3. Ensure all file paths in the error messages exist
4. Check that you're using Python 3.8.20, not 3.12

## Technical Notes

### Why Python 3.8.20?
- ActivitySim 1.1.0 has compatibility issues with newer Python versions
- NumPy 1.21.0 requires specific Python version range
- This version combination is tested and stable

### Development Installation
PopulationSim is installed in development mode (`pip install -e .`) because:
- The pipeline uses custom modifications to the base PopulationSim code
- Changes to the code are immediately available without reinstallation
- This ensures the exact version used in development is replicated
