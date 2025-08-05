# PopulationSim TM2 File Flow Documentation

This document provides a comprehensive mapping of all files, their locations, transformations, and movements throughout the entire PopulationSim TM2 workflow.

## Overview of File Flow

```
Census API Data → Raw PUMS Files → Processed Seed Files → PopulationSim Input Files → Synthetic Population
     ↓                ↓                    ↓                      ↓                        ↓
  Downloads     Processing Scripts    File Copying       PopulationSim Engine      Final Outputs
```

## Directory Structure (CLEANED UP AS OF 2025)

```
bay_area/
├── output_2023/                         # Main data generation directory
│   ├── maz_marginals.csv               # MAZ-level control totals
│   ├── taz_marginals.csv               # TAZ-level control totals  
│   ├── county_marginals.csv            # County-level control totals
│   ├── geo_cross_walk_tm2_updated.csv  # Geography crosswalk (66 PUMAs)
│   ├── maz_data.csv                    # MAZ employment/density data for TM2
│   ├── maz_data_withDensity.csv        # Enhanced MAZ data with density metrics
│   └── tableau/                        # Tableau-ready outputs
│       ├── *.csv                       # Standardized CSV files
│       └── README_Tableau_Data.md      # Usage instructions
├── hh_gq/                              # PopulationSim execution directory
│   ├── data/                           # PopulationSim input files
│   │   ├── seed_households.csv         # PUMS household seed data
│   │   ├── seed_persons.csv            # PUMS person seed data
│   │   ├── maz_marginals_hhgq.csv      # MAZ controls (HH + GQ integrated)
│   │   ├── taz_marginals_hhgq.csv      # TAZ controls (HH + GQ integrated)
│   │   ├── county_marginals.csv        # County occupation controls
│   │   ├── geo_cross_walk_tm2.csv      # Geography relationships
│   │   ├── controls.csv                # PopulationSim control expressions
│   │   └── maz_data_withDensity.csv    # MAZ employment data (for TM2)
│   └── configs_TM2/                    # PopulationSim configuration
│       ├── settings.yaml               # Main PopulationSim settings
│       └── logging.yaml                # Logging configuration
├── tm2_control_utils/                  # Control generation utilities
│   ├── config.py                       # Control generation configuration  
│   └── other utility modules           # Supporting functions
├── create_baseyear_controls_23_tm2.py  # Main control generation script
├── add_hhgq_combined_controls.py       # Group quarters integration script
└── run_populationsim_tm2.py            # Workflow orchestration script
```

## Key PopulationSim Input Files (Exact Files Used)

**Located in:** `c:\GitHub\populationsim\bay_area\hh_gq\data\`

### Core Required Files:
1. **`seed_households.csv`** - PUMS household records (Bay Area only)
2. **`seed_persons.csv`** - PUMS person records (Bay Area only)
3. **`maz_marginals_hhgq.csv`** - MAZ control totals (households + group quarters)
4. **`taz_marginals_hhgq.csv`** - TAZ control totals (households + group quarters)
5. **`county_marginals.csv`** - County occupation controls
6. **`geo_cross_walk_tm2.csv`** - MAZ↔TAZ↔COUNTY↔PUMA mapping
7. **`controls.csv`** - PopulationSim control expressions
8. **`maz_data_withDensity.csv`** - MAZ employment data (for TM2 compatibility)

### Configuration Files:
- **`configs_TM2/settings.yaml`** - Main PopulationSim configuration
- **`configs_TM2/logging.yaml`** - Logging settings

**Note:** The `data_dir: .` setting in `settings.yaml` means PopulationSim looks for input files in the `hh_gq/data/` directory (relative to the config file location).

## Current File Workflow (2025)

### Step 1: Control Generation
**Script:** `python create_baseyear_controls_23_tm2.py`

**Outputs to:** `output_2023/`
```
maz_marginals.csv                # MAZ control totals (39,726 zones)
taz_marginals.csv                # TAZ control totals (4,735 zones) 
county_marginals.csv             # County occupation controls (9 counties)
geo_cross_walk_tm2_updated.csv   # Geography crosswalk (66 PUMAs)
maz_data.csv                     # MAZ employment data
maz_data_withDensity.csv         # Enhanced MAZ data with density
```

### Step 2: Group Quarters Integration
**Script:** `python add_hhgq_combined_controls.py`

**Processes:** Control files from `output_2023/`
**Outputs to:** `hh_gq/data/`
```
maz_marginals_hhgq.csv           # MAZ controls with GQ integrated
taz_marginals_hhgq.csv           # TAZ controls with GQ integrated
```

### Step 3: PopulationSim Synthesis
**Script:** Run PopulationSim with TM2 configuration

**Working Directory:** `c:\GitHub\populationsim\bay_area\hh_gq\`
**Input Files:** All files in `data/` subdirectory
**Configuration:** `configs_TM2/settings.yaml`

**Current PopulationSim Input Files:**
- `data/seed_households.csv` (PUMS households)
- `data/seed_persons.csv` (PUMS persons)
- `data/maz_marginals_hhgq.csv` (MAZ targets)
- `data/taz_marginals_hhgq.csv` (TAZ targets)
- `data/county_marginals.csv` (County targets)
- `data/geo_cross_walk_tm2.csv` (Geography mapping)
- `data/controls.csv` (Control expressions)
- `data/maz_data_withDensity.csv` (Employment data)
## File Path Clarification

**IMPORTANT:** PopulationSim configuration uses relative paths. The `data_dir: .` setting in `settings.yaml` means:
- PopulationSim runs from: `c:\GitHub\populationsim\bay_area\hh_gq\`
- Data files are in: `c:\GitHub\populationsim\bay_area\hh_gq\data\`
- Config files are in: `c:\GitHub\populationsim\bay_area\hh_gq\configs_TM2\`

**Full Paths for Key Files:**
```
c:\GitHub\populationsim\bay_area\hh_gq\data\seed_households.csv
c:\GitHub\populationsim\bay_area\hh_gq\data\seed_persons.csv
c:\GitHub\populationsim\bay_area\hh_gq\data\maz_marginals_hhgq.csv
c:\GitHub\populationsim\bay_area\hh_gq\data\taz_marginals_hhgq.csv
c:\GitHub\populationsim\bay_area\hh_gq\data\county_marginals.csv
c:\GitHub\populationsim\bay_area\hh_gq\data\geo_cross_walk_tm2.csv
c:\GitHub\populationsim\bay_area\hh_gq\data\controls.csv
c:\GitHub\populationsim\bay_area\hh_gq\configs_TM2\settings.yaml
```

## Legacy Files Cleanup (2025)

### Files Removed/Consolidated:
- Old backup files (`*_backup.csv`, `*_original.csv`)
- Duplicate crosswalk files (kept `geo_cross_walk_tm2.csv`)
- Intermediate processing files (`*_preprocessed.csv`)
- Legacy control files without `_hhgq` suffix

### Files Requiring Both Versions:
- `maz_data.csv` AND `maz_data_withDensity.csv` (different TM2 tools need different versions)
- `maz_marginals.csv` (in output_2023) AND `maz_marginals_hhgq.csv` (in hh_gq/data)

## Troubleshooting the IntCastingNaNError

**Common Issue:** PopulationSim fails during "setup data structures" step with:
```
pandas.errors.IntCastingNaNError: Cannot convert non-finite values (NA or inf) to integer
```

**Root Cause:** Non-finite values in seed data or control files that cannot be converted to integers.

**Debugging Steps:**
1. **Check Control Files:** Verify no NaN/infinite values in marginal files
2. **Check Seed Data:** Verify PUMS data has proper integer types
3. **Check Control Expressions:** Verify expressions in `controls.csv` don't create invalid results
4. **Check GROUP_BY_INCIDENCE_SIGNATURE:** This setting can trigger the error with certain data

**Quick Fix for GROUP_BY_INCIDENCE_SIGNATURE Error:**
```yaml
# In settings.yaml, temporarily disable:
GROUP_BY_INCIDENCE_SIGNATURE: False
```

## File Validation Commands

```python
# Check control files for data quality issues
import pandas as pd
import numpy as np

# MAZ controls check
maz_df = pd.read_csv('hh_gq/data/maz_marginals_hhgq.csv')
print("MAZ NaN values:", maz_df.isnull().sum().sum())
print("MAZ infinite values:", np.isinf(maz_df.select_dtypes(include=[np.number])).sum().sum())

# TAZ controls check  
taz_df = pd.read_csv('hh_gq/data/taz_marginals_hhgq.csv')
print("TAZ NaN values:", taz_df.isnull().sum().sum())
print("TAZ infinite values:", np.isinf(taz_df.select_dtypes(include=[np.number])).sum().sum())

# Seed households check
hh_df = pd.read_csv('hh_gq/data/seed_households.csv', nrows=1000)
critical_fields = ['HUPAC', 'NP', 'hhgqtype', 'hh_workers_from_esr']
for field in critical_fields:
    if field in hh_df.columns:
        print(f"{field}: dtype={hh_df[field].dtype}, NaN={hh_df[field].isnull().sum()}")
```
## Current Status (2025)

### Completed Improvements:
- ✅ **Population Scaling Fixed:** TAZ population scaling from 7,765,399 to target 7,508,799
- ✅ **Hierarchical Consistency Enforced:** TAZ categories sum exactly to MAZ totals  
- ✅ **Control File Cleanup:** Consolidated to essential files only
- ✅ **Tableau Data Preparation:** CSV-based approach to avoid shapefile compatibility issues
- ✅ **66 PUMA Support:** Updated crosswalk includes all current Bay Area PUMAs

### Known Issues:
- ⚠️ **IntCastingNaNError:** PopulationSim fails during incidence processing with GROUP_BY_INCIDENCE_SIGNATURE=True
- ⚠️ **File Organization:** Legacy backup files need cleanup in data directories

### Recommendations:
1. **Regular Cleanup:** Remove `*_backup.csv` and `*_original.csv` files after validation
2. **Consistent Paths:** Use absolute paths in configuration files where possible
3. **Error Monitoring:** Check PopulationSim logs for data quality warnings
4. **Testing:** Validate control mathematical consistency before synthesis

This documentation reflects the cleaned-up file organization as of 2025.
