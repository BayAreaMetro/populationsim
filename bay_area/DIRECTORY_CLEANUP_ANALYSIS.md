# Bay Area PopulationSim Directory Cleanup Analysis

## Current Directory Structure Analysis

Based on the unified workflow (`unified_tm2_config.py` and `unified_tm2_workflow.py`), here's what directories are actually needed vs deprecated:

## ✅ REQUIRED DIRECTORIES (Keep)

### Core Workflow Directories
1. **`output_2023/`** - Main output directory (configured as `OUTPUT_DIR`)
2. **`hh_gq/tm2_working_dir/`** - PopulationSim working directory (configured as `POPSIM_WORKING_DIR`)
   - `hh_gq/tm2_working_dir/data/` - PopulationSim data directory
   - `hh_gq/tm2_working_dir/configs/` - PopulationSim config directory  
   - `hh_gq/tm2_working_dir/output/` - PopulationSim output directory
3. **`analysis/`** - Analysis and utility scripts (created during cleanup)
4. **`tm2_control_utils/`** - Control generation utilities

## ❌ DEPRECATED DIRECTORIES (Remove)

### 1. `hh_gq/configs_BAUS/` - BAUS-specific configs (not used in TM2)
Contains:
- controls.csv
- logging.yaml  
- settings.yaml

**Reason**: The unified workflow uses TM2-specific configs in `tm2_working_dir/configs/`

### 2. `hh_gq/configs_TM2/` - Old TM2 configs (replaced)
Contains:
- county_marginals.csv
- maz_marginals_hhgq.csv
- taz_marginals_hhgq.csv

**Reason**: These files are now generated in `tm2_working_dir/data/` by the workflow

### 3. `hh_gq/data/` - Intermediate data storage (redundant)
Contains:
- Various CSV files that duplicate files in `output_2023/` and `tm2_working_dir/data/`

**Reason**: The unified config handles file syncing between `output_2023/` and `tm2_working_dir/data/`

### 4. `output_2023/populationsim_run/` and `output_2023/populationsim_test/` - Old log directories
Contains:
- Old log files from manual runs

**Reason**: PopulationSim now runs in `tm2_working_dir/` and logs there

### 5. `scripts/` - Archive and cleanup scripts (no longer needed)
Contains:
- `archive/` - Old archived scripts
- `cleanup/` - Cleanup scripts (analysis tools moved to `analysis/`)

**Reason**: Core scripts are now in root, analysis tools in `analysis/`

### 6. `output_2023_tableau/` - Duplicate tableau output
**Reason**: Tableau files are generated in `output_2023/tableau/` by the workflow

## 🧹 CLEANUP ACTIONS

### Phase 1: Safe Removal (No data dependencies)
```powershell
Remove-Item "hh_gq\configs_BAUS" -Recurse -Force
Remove-Item "hh_gq\configs_TM2" -Recurse -Force  
Remove-Item "output_2023\populationsim_run" -Recurse -Force
Remove-Item "output_2023\populationsim_test" -Recurse -Force
Remove-Item "scripts" -Recurse -Force
Remove-Item "output_2023_tableau" -Recurse -Force
```

### Phase 2: Data Consolidation (Check for duplicates first)
```powershell
# Move any unique files from hh_gq/data to appropriate locations, then remove
Remove-Item "hh_gq\data" -Recurse -Force
```

## 📁 FINAL CLEAN STRUCTURE

```
bay_area/
├── analysis/                    # Analysis and utility scripts
├── hh_gq/
│   └── tm2_working_dir/        # PopulationSim working directory
│       ├── configs/            # PopulationSim configs
│       ├── data/               # PopulationSim input data
│       └── output/             # PopulationSim output
├── output_2023/                # Main output directory
│   └── tableau/                # Tableau output
├── tm2_control_utils/          # Control utilities
├── [10 core workflow scripts]  # Core Python scripts
└── [documentation files]       # README, config files, etc.
```

## 🎯 BENEFITS

1. **Eliminated Redundancy**: No more duplicate config directories
2. **Clear Data Flow**: Single path from output_2023 → tm2_working_dir
3. **Simplified Structure**: Only necessary directories remain
4. **Better Organization**: Related files grouped logically
5. **Easier Maintenance**: Clear ownership of each directory

This cleanup will eliminate ~6 deprecated directories and consolidate the data flow!
