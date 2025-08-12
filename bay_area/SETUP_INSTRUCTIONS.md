# PopulationSim TM2 Setup Instructions

## For New Machines - WORKING SETUP PROCESS

### 1. Clone Repository
```bash
git clone https://github.com/BayAreaMetro/populationsim.git
cd populationsim
git checkout tm2
```

### 2. Create Environment (TESTED WORKING METHOD)
```bash
# The exact environment export has version conflicts
# Use the simplified environment that works:
cd bay_area
conda env create -f environment_minimal.yml
```

**Note:** The `environment_export.yml` has package version conflicts on current conda channels. The `environment_minimal.yml` uses compatible versions and lets pip handle complex dependencies.

### 3. Verify Environment Creation
```bash
# Check environment was created
conda list -n popsim_working
```

### 4. Use Direct Python Path (PowerShell Activation Issues)
```bash
# PowerShell conda activation doesn't work reliably
# Use direct path to Python executable instead:
C:\Users\[USERNAME]\AppData\Local\anaconda3\envs\popsim_working\python.exe --version
# Should show: Python 3.8.20

# Test PopulationSim import
C:\Users\[USERNAME]\AppData\Local\anaconda3\envs\popsim_working\python.exe -c "import populationsim; print('PopulationSim path:', populationsim.__file__)"
# Should show: C:\GitHub\populationsim\populationsim\__init__.py
```

### 5. Verify Installation
```bash
cd bay_area
C:\Users\[USERNAME]\AppData\Local\anaconda3\envs\popsim_working\python.exe setup_environment.py
```

### 5. Run Pipeline
```bash
python tm2_pipeline.py full --force
```

## CRITICAL NOTES

### Environment Details
- **Python Version**: 3.8.20 (DO NOT use 3.12 - causes compatibility issues)
- **PopulationSim**: Development version from this repository
- **Key Dependencies**: activitysim==1.1.0, pandas==2.0.3, numpy==1.21.0

### Installation Order
1. Create conda environment first
2. Install PopulationSim in development mode second
3. Never install PopulationSim via pip/conda - always use `pip install -e .`

## Key Changes Made (For Reference)

### County System
- Implemented 1-9 county system (instead of FIPS codes)
- Centralized county mapping in `unified_tm2_config.py`
- Counties: 1=SF, 2=San Mateo, 3=Santa Clara, 4=Alameda, 5=Contra Costa, 6=Solano, 7=Napa, 8=Sonoma, 9=Marin

### GQ Controls Fixed
- `gq_pop`: `hhgqtype>=2` (Group Quarters only)
- `gq_university`: Age-based split of GQ institutional
- `numhh_gq`: `hh_id>0` (households using integer IDs)

### Architecture Improvements
- Single source of truth in `unified_tm2_config.py`
- No hardcoded mappings in pipeline files
- Proper fallback paths for different machines

## Path Dependencies

### Required External Paths
- `M:/Data/GIS layers/TM2_maz_taz_v2.2/` - MAZ/TAZ definitions
- `M:/Data/Census/NewCachedTablesForPopulationSimControls/` - Census cache
- `C:/GitHub/tm2py-utils/` - TM2 utilities

### Local Fallbacks
- `bay_area/local_data/gis/` - Local GIS files
- `bay_area/local_data/census/` - Local census cache
- `bay_area/data_cache/` - Local data cache

## Troubleshooting Environment Creation

### Issue: LibMambaUnsatisfiableError with environment_export.yml
**Problem:** Exact package versions from working environment aren't available on current conda channels
**Solution:** Use `environment_minimal.yml` instead - it uses compatible versions and lets pip handle complex dependencies

### Issue: "tables 3.8.0 does not exist" 
**Problem:** PyTables 3.8.0 not available for Python 3.8 in conda channels
**Solution:** Remove tables from conda dependencies, let PopulationSim install it via pip

### Issue: PowerShell conda activate doesn't work
**Problem:** `conda activate popsim_working` doesn't set PATH correctly in PowerShell
**Solution:** Use direct Python executable path: `C:\Users\[USERNAME]\AppData\Local\anaconda3\envs\popsim_working\python.exe`

### Issue: "pip not recognized" after conda activate
**Problem:** PATH not properly set in PowerShell environment
**Solution:** Use `conda run -n popsim_working pip install -e .` OR use direct Python path

### Environment Creation Process That Works:
1. Use `environment_minimal.yml` (not `environment_export.yml`)
2. PopulationSim installs automatically via pip in the minimal environment
3. Use direct Python executable path instead of conda activate
4. Verify with `conda list -n popsim_working` to see installed packages

## Troubleshooting

### Common Issues
1. **Missing M: drive** - Use local fallback paths
2. **PUMS data not found** - Download automatically with `python tm2_pipeline.py pums`
3. **Census API limits** - Use cached data in `data_cache/`
4. **County mismatch** - All county mappings now centralized in config

### Environment Variables
Set these for consistency:
- `POPSIM_PYTHON_EXE` - Python executable path
- `POPULATIONSIM_BASE_DIR` - Base directory path
- `TEST_PUMA` - For testing single PUMA (optional)
