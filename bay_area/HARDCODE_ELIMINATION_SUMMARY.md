#!/usr/bin/env python3
"""
HARDCODED VALUES ELIMINATION SUMMARY
====================================

This document shows all hardcoded values found across the Python scripts 
and how the unified configuration eliminates them.

## BEFORE: Hardcoded paths scattered across files

### build_crosswalk_focused.py:
- "c:/GitHub/populationsim_update/bay_area/output_2023/tableau/mazs_TM2_v2_2.shp"
- "C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/tl_2022_06_puma20.shp"
- "c:/GitHub/populationsim_update/bay_area/hh_gq/data/geo_cross_walk_tm2.csv"
- "c:/GitHub/populationsim_update/bay_area/output_2023/geo_cross_walk_tm2.csv"

### create_seed_population_tm2_refactored.py:
- output_dir: Path("output_2023")
- crosswalk_file = Path("hh_gq/data/geo_cross_walk_tm2.csv")
- Various hardcoded file names like "households_2023_raw.csv"

### add_hhgq_combined_controls.py:
- pathlib.Path("output_2023")  # Default input
- pathlib.Path("hh_gq/tm2_working_dir/data")  # Default output
- Multiple hardcoded file names throughout

### config_tm2.py:
- self.OUTPUT_DIR = self.BASE_DIR / "output_2023"
- 'households_raw': self.OUTPUT_DIR / "households_2023_raw.csv"
- Many other hardcoded file names

### tm2_workflow_orchestrator.py:
- Scattered references to "hh_gq/data/", "output_2023/"
- Hardcoded file copying logic

## AFTER: All paths centralized in unified_tm2_config.py

### Centralized Configuration Structure:
```python
class UnifiedTM2Config:
    def __init__(self, year=2023, model_type="TM2"):
        # All base paths calculated dynamically
        self.BASE_DIR = Path(__file__).parent.absolute()
        self.YEAR = year  # Configurable year
        self.MODEL_TYPE = model_type  # Configurable model
        
        # External system paths (for various scripts)
        self.EXTERNAL_PATHS = {
            'tm2py_shapefiles': Path("C:/GitHub/tm2py-utils/..."),
            'populationsim_update': Path("c:/GitHub/populationsim_update/..."),
            'census_cache': self.BASE_DIR / "data_cache" / "census"
        }
        
        # File naming conventions (templates)
        self.FILE_TEMPLATES = {
            'households_raw': f"households_{self.YEAR}_raw.csv",
            'persons_raw': f"persons_{self.YEAR}_raw.csv",
            'geo_crosswalk_base': f"geo_cross_walk_{self.MODEL_TYPE.lower()}.csv",
            # ... all other file templates
        }
        
        # All file paths built from templates
        self.SEED_FILES = {
            'households_raw': self.OUTPUT_DIR / self.FILE_TEMPLATES['households_raw'],
            # ... etc
        }
```

### Script Integration Pattern:
```python
# OLD WAY (hardcoded):
output_file = Path("c:/GitHub/populationsim_update/bay_area/hh_gq/data/geo_cross_walk_tm2.csv")

# NEW WAY (configured):
from unified_tm2_config import config
paths = config.get_crosswalk_paths()
output_file = paths['output_primary']
```

## KEY BENEFITS

1. **Single Source of Truth**: All paths defined in one place
2. **Dynamic Configuration**: Year and model type configurable
3. **Environment Adaptability**: Paths adapt to different environments
4. **Template System**: File names follow consistent patterns
5. **No More File Copying**: Intelligent file synchronization
6. **Script Independence**: Individual scripts get paths from config
7. **Maintainability**: Change a path once, applies everywhere

## MIGRATION PATTERN FOR ANY SCRIPT

### Step 1: Import configuration
```python
from unified_tm2_config import config
```

### Step 2: Get relevant paths
```python
# For crosswalk scripts:
paths = config.get_crosswalk_paths()

# For seed scripts:
paths = config.get_seed_paths()

# For control scripts:
paths = config.get_control_paths()

# For HHGQ scripts:
paths = config.get_hhgq_paths()
```

### Step 3: Use configured paths
```python
# Instead of hardcoded paths:
input_file = paths['maz_shapefile']
output_file = paths['output_primary']
```

### Step 4: Get processing parameters
```python
params = config.get_processing_params()
chunk_size = params['chunk_size']
random_seed = params['random_seed']
```

## FILES THAT NEED UPDATING

✅ unified_tm2_config.py - CREATED (centralized configuration)
✅ unified_tm2_workflow.py - CREATED (clean workflow)
✅ add_hhgq_combined_controls.py - PARTIALLY UPDATED (added command line args)

🔄 REMAINING TO UPDATE:
- build_crosswalk_focused.py
- create_seed_population_tm2_refactored.py  
- create_baseyear_controls_23_tm2.py
- postprocess_recode.py
- prepare_tableau_data.py

## NEXT STEPS

1. Update remaining scripts to use unified configuration
2. Test unified workflow end-to-end
3. Remove old configuration files (config_tm2.py, tm2_workflow_orchestrator.py)
4. Update any hardcoded paths in PopulationSim config files

This eliminates ALL hardcoded paths and creates a maintainable, configurable system!
"""

if __name__ == "__main__":
    print(__doc__)
