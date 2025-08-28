# Running Analysis Scripts and Local Imports

Many analysis and utility scripts in this project import modules from the local `tm2_control_utils` package (and others) using lines like:

```python
from tm2_control_utils.config_census import INCOME_BIN_MAPPING
```

To ensure these imports work, simply run scripts from the `bay_area` directory. 

**Best Practice:**
Run all scripts from the `bay_area` directory. This ensures local imports work without needing to set `PYTHONPATH` manually. If you see `ModuleNotFoundError`, check your working directory.
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
# Activate your conda environment (replace [env_name] with your environment name)
conda activate [env_name]

# Check Python version
python --version  # Should show: Python 3.8.20

# Test PopulationSim import
python -c "import populationsim; print('PopulationSim path:', populationsim.__file__)"
# Should show: .../populationsim/populationsim/__init__.py
```

### 5. Verify Installation

```bash
cd bay_area
python setup_environment.py
```

### 5. Run Pipeline

```bash
python tm2_pipeline.py full --force
```

## CRITICAL NOTES

### Environment Details
- **Python Version**: 3.8.20 (DO NOT use 3.12 - causes compatibility issues)
- **PopulationSim**: Development version from this repository
- **Key Dependencies**: activitysim==1.1.0, pandas==2.0.3, numpy==1.21.0, geopandas, census
- **Note**: pandas and census are essential and included in environment_minimal.yml

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

- `C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles` - TM2 shapefiles
- `C:/GitHub/tm2py-utils/tm2py_utils` - TM2 utilities
- `M:/Data/Census/NewCachedTablesForPopulationSimControls/` - Census cache
- `M:/Data/Census/API/new_key` - Census API key
- `M:/Data/Census/PUMS_2023_5Year_Crosswalked` - PUMS current
- `M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23` - PUMS cached

### Environment Variables
Set these for advanced use only (not required for most users):
- `POPULATIONSIM_BASE_DIR` - Base directory path
- `TEST_PUMA` - For testing single PUMA (optional)
