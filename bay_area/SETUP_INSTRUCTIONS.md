# PopulationSim TM2 Setup Instructions

## For New Machines

### 1. Environment Setup
```bash
# Create conda environment
conda create -n popsim_py312 python=3.12
conda activate popsim_py312

# Install PopulationSim in development mode
cd /path/to/populationsim
pip install -e .

# Install additional requirements
cd bay_area
pip install -r requirements.txt
```

### 2. Verify Installation
```bash
cd bay_area
python setup_environment.py
```

### 3. Run Pipeline
```bash
python tm2_pipeline.py full --force
```

## Key Changes Made (For Reference)

### County System
- Implemented 1-9 county system (instead of FIPS codes)
- Centralized county mapping in `unified_tm2_config.py`
- Counties: 1=SF, 2=San Mateo, 3=Santa Clara, 4=Alameda, 5=Contra Costa, 6=Solano, 7=Napa, 8=Sonoma, 9=Marin

### GQ Controls Fixed
- `gq_pop`: `hhgqtype>=2` (Group Quarters only)
- `gq_university`: Age-based split of GQ institutional
- `numhh_gq`: `unique_hh_id>0` (households in GQ)

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
