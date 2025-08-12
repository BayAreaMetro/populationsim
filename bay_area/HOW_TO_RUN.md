# How to Run TM2 PopulationSim Pipeline

## Quick Start

### 1. Environment Setup
```bash
# Activate conda environment
conda activate popsim_py312

# Navigate to bay_area directory
cd /path/to/populationsim/bay_area

# Check environment setup
python setup_environment.py
```

### 2. Run Full Pipeline
```bash
# Run complete pipeline (recommended)
python tm2_pipeline.py full --force

# Or run individual steps
python tm2_pipeline.py crosswalk --force
python tm2_pipeline.py seed --force  
python tm2_pipeline.py controls --force
python tm2_pipeline.py populationsim --force
```

## File Paths You May Need to Change

### Critical Path Configurations

All file paths are centralized in `unified_tm2_config.py`. Here are the key sections you may need to modify:

#### 1. Python Executable Path
**Location**: `unified_tm2_config.py` lines 25-35
```python
# Python executable (full path to popsim environment)
python_exe_env = os.getenv('POPSIM_PYTHON_EXE')
if python_exe_env:
    self.PYTHON_EXE = Path(python_exe_env)
else:
    # Default to current user's anaconda environment
    self.PYTHON_EXE = Path(f"C:/Users/{os.getenv('USERNAME')}/AppData/Local/anaconda3/envs/popsim/python.exe")
```
**What to change**: Replace with your actual Python executable path if different.

#### 2. External Data Paths
**Location**: `unified_tm2_config.py` lines 85-100
```python
self.EXTERNAL_PATHS = {
    'tm2py_shapefiles': Path("C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles"),
    'tm2py_utils': Path("C:/GitHub/tm2py-utils/tm2py_utils"),
    'network_gis': Path("M:/Data/GIS layers/TM2_maz_taz_v2.2"),
    'network_census_cache': Path("M:/Data/Census/NewCachedTablesForPopulationSimControls"),
    'network_census_api': Path("M:/Data/Census/API/new_key"),
    'pums_current': Path("M:/Data/Census/PUMS_2023_5Year_Crosswalked"),
    'pums_cached': Path("M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23"),
}
```
**What to change**: 
- Replace `C:/GitHub/tm2py-utils/` with your tm2py-utils installation path
- Replace `M:/Data/` paths with your network data locations
- If no M: drive access, the pipeline will use local fallback paths automatically

#### 3. GIS Reference Files
**Location**: `unified_tm2_config.py` lines 110-120
```python
self.GIS_FILES = {
    # Network locations (preferred)
    'maz_taz_def_network': self.EXTERNAL_PATHS['network_gis'] / "blocks_mazs_tazs.csv",
    'maz_taz_all_geog_network': self.EXTERNAL_PATHS['network_gis'] / "mazs_tazs_all_geog.csv",
    # Local fallbacks
    'maz_taz_def_local': self.EXTERNAL_PATHS['local_gis'] / "blocks_mazs_tazs.csv",
    'maz_taz_all_geog_local': self.EXTERNAL_PATHS['local_gis'] / "mazs_tazs_all_geog.csv",
}
```
**What to change**: Usually automatic fallback works, but verify your GIS files are available.

#### 4. Census API Key
**Location**: `unified_tm2_config.py` lines 115-125
```python
'census_api_key_network': self.EXTERNAL_PATHS['network_census_api'] / "api-key.txt",
'census_api_key_local': self.EXTERNAL_PATHS['local_census'] / "api-key.txt"
```
**What to change**: Ensure you have a Census API key file in one of these locations.

## Environment Variables (Alternative to Path Changes)

Instead of editing `unified_tm2_config.py`, you can set environment variables:

```bash
# Windows PowerShell
$env:POPSIM_PYTHON_EXE = "C:/your/path/to/python.exe"
$env:TM2PY_UTILS_PATH = "C:/your/path/to/tm2py-utils"
$env:NETWORK_DATA_PATH = "M:/Data"  # or your network path

# Linux/Mac
export POPSIM_PYTHON_EXE="/your/path/to/python"
export TM2PY_UTILS_PATH="/your/path/to/tm2py-utils"
export NETWORK_DATA_PATH="/your/network/data/path"
```

## Common Path Issues and Solutions

### Issue 1: M: Drive Not Available
**Symptoms**: "Path not found" errors for M: drive locations
**Solution**: Pipeline automatically uses local fallback paths in `bay_area/local_data/`

### Issue 2: TM2py-utils Not Found
**Symptoms**: "Cannot find tm2py-utils" error
**Solution**: 
1. Clone tm2py-utils: `git clone https://github.com/BayAreaMetro/tm2py-utils.git`
2. Update path in `unified_tm2_config.py` or set `TM2PY_UTILS_PATH` environment variable

### Issue 3: Wrong Python Executable
**Symptoms**: "Module not found" errors during pipeline execution
**Solution**: 
1. Check: `which python` or `where python`
2. Update `PYTHON_EXE` path in config or set `POPSIM_PYTHON_EXE` environment variable

### Issue 4: Census API Key Missing
**Symptoms**: Census download failures
**Solution**: 
1. Get free API key from: https://api.census.gov/data/key_signup.html
2. Save to file: `bay_area/local_data/census/api-key.txt`

## Directory Structure Requirements

The pipeline expects this structure (auto-created if missing):
```
bay_area/
├── output_2023/
│   └── populationsim_working_dir/
│       ├── data/           # Input data files
│       ├── configs/        # PopulationSim config files  
│       └── output/         # Synthesis results
├── local_data/             # Local fallback data
│   ├── gis/               # Local GIS files
│   └── census/            # Local census cache
├── hh_gq/                 # Household/GQ config templates
└── scripts/               # Utility scripts
```

## Testing Your Setup

Run the environment checker:
```bash
python setup_environment.py
```

This checks:
- ✓ Python version and environment
- ✓ Required packages installed
- ✓ PopulationSim library accessible
- ✓ External paths available
- ✓ Fallback directories created

## Troubleshooting Commands

```bash
# Check pipeline status
python tm2_pipeline.py status

# Clean outputs and restart
python tm2_pipeline.py clean
python tm2_pipeline.py full --force

# Run single step for debugging
python tm2_pipeline.py crosswalk --force

# Check Python environment
python -c "import populationsim; print(populationsim.__file__)"
```

## Performance Tips

- **Full run**: ~2-4 hours depending on machine
- **Use --fast flag**: For testing (relaxed tolerances)
- **Single PUMA test**: Set `TEST_PUMA=7501` environment variable
- **Parallel processing**: Pipeline uses all available CPU cores

## Getting Help

1. **Check logs**: `output_2023/populationsim_working_dir/output/populationsim.log`
2. **Environment issues**: Run `python setup_environment.py`
3. **Path problems**: Check `unified_tm2_config.py` external paths
4. **Data issues**: Verify input files in `output_2023/populationsim_working_dir/data/`
