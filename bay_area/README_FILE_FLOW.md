# PopulationSim TM2 File Flow Documentation

This document provides a comprehensive mapping of all files, their locations, transformations, and movements throughout the entire PopulationSim TM2 workflow.

## Overview of File Flow

```
Census API Data → Raw PUMS Files → Processed Seed Files → PopulationSim Input Files → Synthetic Population
     ↓                ↓                    ↓                      ↓                        ↓
  Downloads     Processing Scripts    File Copying       PopulationSim Engine      Final Outputs
```

## Directory Structure

```
bay_area/
├── input_2023/                           # Census API cache and raw data
│   ├── api/                             # Census API downloaded data
│   ├── census_cache/                    # Cached Census API responses
│   └── NewCachedTablesForPopulationSimControls/  # Pre-cached control data
├── output_2023/                         # Intermediate processing outputs
│   ├── households_2023_raw.csv         # Raw PUMS households (downloaded)
│   ├── persons_2023_raw.csv            # Raw PUMS persons (downloaded)  
│   ├── households_2023_tm2.csv         # Processed households (PopulationSim ready)
│   ├── persons_2023_tm2.csv            # Processed persons (PopulationSim ready)
│   ├── maz_marginals.csv               # MAZ-level control totals
│   ├── taz_marginals.csv               # TAZ-level control totals
│   ├── county_marginals.csv            # County-level control totals
│   ├── geo_cross_walk_tm2.csv          # Geography crosswalk
│   └── populationsim_run/              # Final PopulationSim outputs
│       ├── synthetic_households.csv    # Final synthetic households
│       ├── synthetic_persons.csv       # Final synthetic persons
│       ├── summary_melt.csv            # Summary for validation
│       └── populationsim.log           # Detailed execution log
├── hh_gq/                              # PopulationSim working directory
│   ├── data/                           # PopulationSim input files (copied)
│   │   ├── seed_households.csv         # COPY of households_2023_tm2.csv
│   │   ├── seed_persons.csv            # COPY of persons_2023_tm2.csv
│   │   ├── maz_marginals.csv           # COPY from output_2023/
│   │   ├── taz_marginals.csv           # COPY from output_2023/
│   │   ├── county_marginals.csv        # COPY from output_2023/
│   │   ├── geo_cross_walk_tm2.csv      # COPY from output_2023/
│   │   ├── maz_marginals_hhgq.csv      # Group quarters integrated version
│   │   └── taz_marginals_hhgq.csv      # Group quarters integrated version
│   └── configs_TM2/                    # PopulationSim configuration
│       ├── settings.yaml               # Main configuration file
│       ├── controls.csv                # Control specifications
│       └── logging.yaml                # Logging configuration
└── tm2_control_utils/                  # Control generation utilities
    ├── config.py                       # Control generation configuration
    └── various utility scripts
```

## Detailed File Flow by Step

### Step 1: Seed Population Generation

**Script:** `create_seed_population_tm2.py`

**Input Sources:**
- Census API: ACS 2023 PUMS data for California (downloaded on demand)
- Bay Area PUMAs: 66 specific PUMA codes hardcoded in script

**Intermediate Files:**
```
output_2023/households_2023_raw.csv     # Raw PUMS households (860,550 records)
output_2023/persons_2023_raw.csv        # Raw PUMS persons (1,998,300 records)
```

**Processing:**
1. Downloads raw PUMS data from Census API if not cached
2. Filters to Bay Area PUMAs only
3. Adds required PopulationSim columns:
   - `hhgqtype`: Group quarters type (1=household, 2=group quarters)
   - `COUNTY`: County FIPS codes
   - `hh_income_2023`: CPI-adjusted income to 2023 dollars
   - `hh_income_2010`: Backwards-compatible income
   - `occupation`: SOC occupation codes
   - `employed`: Employment status
   - `unique_hh_id`: Unique household identifier

**Final Outputs:**
```
output_2023/households_2023_tm2.csv     # PopulationSim-ready households (860,550 records)
output_2023/persons_2023_tm2.csv        # PopulationSim-ready persons (1,998,300 records)
```

**File Movement:**
```
output_2023/households_2023_tm2.csv  →  hh_gq/data/seed_households.csv  (COPY)
output_2023/persons_2023_tm2.csv     →  hh_gq/data/seed_persons.csv     (COPY)
```

### Step 2: Control Generation

**Script:** `create_baseyear_controls_23_tm2.py --output_dir hh_gq/data`

**Input Sources:**
- Census API 2020 Decennial PL 94-171 (block-level household counts)
- ACS 2023 5-year estimates (tract and block group demographics)
- ACS 2023 1-year estimates (county-level scaling targets)
- Local cache: `input_2023/NewCachedTablesForPopulationSimControls/`
- Geography: TM2 MAZ/TAZ definitions

**Processing Flow:**

#### MAZ Level Controls:
1. **Block-level data** (2020 Census) → household counts by block
2. **Geography crosswalk** (2020→2010 Census boundaries) → MAZ assignment
3. **County scaling** (ACS 2023 1-year) → scaled to current totals
4. **Group quarters** (2020 Census) → GQ population by type

**Output:**
```
hh_gq/data/maz_marginals.csv            # MAZ controls (14,000+ zones)
Columns: MAZ, num_hh, gq_pop, gq_military, gq_university, gq_other
```

#### TAZ Level Controls:
1. **Tract/Block Group data** (ACS 2023 5-year) → demographic distributions
2. **Income adjustment** → CPI inflation to 2023 dollars  
3. **Geographic aggregation** → TAZ-level summaries
4. **Household characteristics** → size, workers, children, age groups

**Output:**
```
hh_gq/data/taz_marginals.csv            # TAZ controls (1,454 zones)
Columns: TAZ, hh_size_1, hh_size_2, hh_size_3, hh_size_4_plus,
         hh_inc_30, hh_inc_60, hh_inc_100, hh_inc_100_plus,
         hh_workers_0, hh_workers_1, hh_workers_2, hh_workers_3_plus,
         age_0_19, age_20_34, age_35_64, age_65_plus,
         hh_with_children, hh_no_children
```

#### County Level Controls:
1. **ACS occupation data** → major occupation categories
2. **County aggregation** → 9-county Bay Area totals

**Output:**
```
hh_gq/data/county_marginals.csv         # County controls (9 counties)
Columns: COUNTY, mgmt, prof, services, retail, manual, military
```

#### Geography Crosswalk:
1. **MAZ/TAZ definitions** → spatial relationships
2. **Census geography** → block, block group, tract linkages
3. **PUMA assignment** → 66 Bay Area PUMAs

**Output:**
```
hh_gq/data/geo_cross_walk_tm2.csv       # Geography relationships
Columns: MAZ, TAZ, COUNTY, PUMA, TRACT, BLKGRP, BLOCK
```

**No File Movement:** Files are generated directly in `hh_gq/data/` directory

### Step 3: Group Quarters Integration

**Script:** `add_hhgq_combined_controls.py --model_type TM2`

**Input Files:**
```
hh_gq/data/maz_marginals.csv            # Original MAZ controls
hh_gq/data/taz_marginals.csv            # Original TAZ controls
```

**Processing:**
- Treats group quarters residents as single-person households
- Adds GQ population to household counts for PopulationSim balancing
- Maintains separate GQ tracking for post-processing

**Output Files:**
```
hh_gq/data/maz_marginals_hhgq.csv       # MAZ controls with GQ integration
hh_gq/data/taz_marginals_hhgq.csv       # TAZ controls with GQ integration
```

**Key Changes:**
- `num_hh` → `num_hh + gq_pop` (total units to synthesize)
- `hh_size_1` → `hh_size_1 + gq_pop` (GQ residents as 1-person HHs)

### Step 4: PopulationSim Synthesis

**Script:** `run_populationsim.py --config hh_gq/configs_TM2 --output output_2023/populationsim_run --data hh_gq/data`

**Configuration Files:**
```
hh_gq/configs_TM2/settings.yaml         # Main PopulationSim settings
hh_gq/configs_TM2/controls.csv          # Control specifications
hh_gq/configs_TM2/logging.yaml          # Logging configuration
```

**Input Files (from hh_gq/data/):**
```
seed_households.csv                      # Seed households (860,550 records)
seed_persons.csv                         # Seed persons (1,998,300 records)  
geo_cross_walk_tm2.csv                   # Geography relationships
maz_marginals_hhgq.csv                   # MAZ-level targets
taz_marginals_hhgq.csv                   # TAZ-level targets
county_marginals.csv                     # County-level targets
```

**Processing:**
1. **Input validation** → Check all files and columns
2. **Setup data structures** → Build control matrices
3. **Initial balancing** → County level convergence
4. **Iterative balancing** → TAZ and MAZ level convergence
5. **Integerization** → Convert weights to whole households
6. **Final synthesis** → Generate synthetic population

**Intermediate Files (in pipeline cache):**
```
output_2023/populationsim_run/pipeline.h5    # Cached intermediate results
```

**Final Output Files:**
```
output_2023/populationsim_run/synthetic_households.csv    # Synthetic households
output_2023/populationsim_run/synthetic_persons.csv       # Synthetic persons
output_2023/populationsim_run/final_summary_TAZ.csv       # TAZ-level summary
output_2023/populationsim_run/final_summary_MAZ.csv       # MAZ-level summary
output_2023/populationsim_run/final_summary_COUNTY.csv    # County-level summary
output_2023/populationsim_run/populationsim.log           # Detailed execution log
```

### Step 5: Post-Processing

**Script:** `postprocess_recode.py --model_type TM2 --directory output_2023/populationsim_run --year 2023`

**Input Files:**
```
output_2023/populationsim_run/synthetic_households.csv
output_2023/populationsim_run/synthetic_persons.csv
output_2023/populationsim_run/final_summary_*.csv
```

**Processing:**
1. **Variable recoding** → Travel model compatibility
2. **Validation checks** → Compare to control totals
3. **Summary generation** → Create analysis files

**Final Output Files:**
```
output_2023/populationsim_run/summary_melt.csv           # Long-format summary for Tableau
output_2023/populationsim_run/validation.twb             # Tableau workbook (copied)
```

**Archived Input Files (copied for reference):**
```
output_2023/populationsim_run/maz_marginals.csv
output_2023/populationsim_run/taz_marginals.csv
output_2023/populationsim_run/county_marginals.csv
output_2023/populationsim_run/geo_cross_walk_tm2.csv
```

### Step 6: Tableau Data Preparation

**Script:** `prepare_tableau_data.py --output_dir output_2023/populationsim_run --year 2023`

**Input Files:**
```
output_2023/populationsim_run/synthetic_households.csv
output_2023/populationsim_run/synthetic_persons.csv
output_2023/populationsim_run/summary_melt.csv
output_2023/populationsim_run/maz_marginals.csv
output_2023/populationsim_run/taz_marginals.csv
output_2023/populationsim_run/county_marginals.csv
output_2023/populationsim_run/geo_cross_walk_tm2.csv
local_data/gis/                                     # TAZ and PUMA shapefiles
```

**Processing:**
1. **Standardize join fields** → Create consistent TAZ_ID, MAZ_ID, PUMA_ID, COUNTY_ID columns
2. **Prepare spatial data** → Process TAZ and PUMA boundary shapefiles for Tableau
3. **Format marginal data** → Clean control totals for analysis
4. **Create geographic crosswalk** → Tableau-ready geography relationships
5. **Generate documentation** → README for Tableau usage

**Final Output Files:**
```
output_2023/populationsim_run/tableau/taz_boundaries_tableau.shp     # TAZ boundaries with standardized fields
output_2023/populationsim_run/tableau/puma_boundaries_tableau.shp    # PUMA boundaries with standardized fields
output_2023/populationsim_run/tableau/taz_marginals_tableau.csv      # TAZ controls with standardized joins
output_2023/populationsim_run/tableau/maz_marginals_tableau.csv      # MAZ controls with standardized joins
output_2023/populationsim_run/tableau/geo_crosswalk_tableau.csv      # Geography relationships for Tableau
output_2023/populationsim_run/tableau/README_TABLEAU.md              # Usage instructions for Tableau
```

## File Size and Performance Characteristics

### Typical File Sizes:
```
households_2023_raw.csv          ~650 MB    (all PUMS columns)
persons_2023_raw.csv            ~1.4 GB    (all PUMS columns)
households_2023_tm2.csv         ~650 MB    (PopulationSim subset)
persons_2023_tm2.csv            ~1.4 GB    (PopulationSim subset)
seed_households.csv             ~650 MB    (copy of tm2 file)
seed_persons.csv                ~1.4 GB    (copy of tm2 file)
maz_marginals.csv               ~800 KB    (14,000 zones)
taz_marginals.csv               ~350 KB    (1,454 zones)
county_marginals.csv            ~500 bytes (9 counties)
geo_cross_walk_tm2.csv          ~1.2 MB    (geography links)
synthetic_households.csv        ~650 MB    (final households)
synthetic_persons.csv           ~1.4 GB    (final persons)
```

### Processing Times:
```
Step 1 (Seed Generation):        10-15 minutes  (download + processing)
Step 2 (Control Generation):     10-15 minutes  (Census API calls)
Step 3 (HHGQ Integration):       1-2 minutes    (file processing)
Step 4 (PopulationSim):          45-60 minutes  (synthesis algorithm)
Step 5 (Post-processing):        5 minutes      (recoding + validation)
Step 6 (Tableau Preparation):    2-3 minutes    (spatial data processing)
```

## Critical File Dependencies

### PopulationSim Input Requirements:
1. **settings.yaml** must reference correct filenames in `input_table_list`
2. **Seed files** must have `hhgqtype` column (not `gqtype`)
3. **Control files** must use `_hhgq` versions for synthesis
4. **Geography crosswalk** must link all MAZ/TAZ to Census geography
5. **All files** must be in `hh_gq/data/` directory when PopulationSim runs

### Column Requirements:
```
Households: unique_hh_id, hhgqtype, COUNTY, hh_income_2023, NP, [PUMS columns]
Persons: unique_hh_id, hhgqtype, COUNTY, AGEP, occupation, employed, [PUMS columns]
Controls: Geography columns + demographic control totals
Crosswalk: MAZ, TAZ, COUNTY, PUMA, TRACT, BLKGRP
```

## File Movement Summary

### Copies Made During Workflow:
```
output_2023/households_2023_tm2.csv  →  hh_gq/data/seed_households.csv
output_2023/persons_2023_tm2.csv     →  hh_gq/data/seed_persons.csv
validation.twb                       →  output_2023/populationsim_run/validation.twb
hh_gq/data/*.csv                     →  output_2023/populationsim_run/*.csv (archive)
```

### Files That Stay in Place:
```
input_2023/                          # Census cache (permanent)
output_2023/households_2023_raw.csv  # Raw PUMS (intermediate)
output_2023/persons_2023_raw.csv     # Raw PUMS (intermediate)
hh_gq/configs_TM2/                   # Configuration (permanent)
```

### Temporary/Cache Files:
```
output_2023/populationsim_run/pipeline.h5    # Cleared between runs
input_2023/api/                              # API cache (can be cleared)
input_2023/census_cache/                     # Census cache (can be cleared)
```

## Troubleshooting File Issues

### Common File Problems:
1. **Missing hhgqtype column** → Regenerate seed files with updated script
2. **Wrong filenames in settings.yaml** → Update input_table_list
3. **Files in wrong directory** → Check hh_gq/data/ vs output_2023/
4. **Stale pipeline cache** → Delete pipeline.h5 and restart
5. **Permission errors** → Check file locks and VS Code handles

### File Validation Commands:
```python
# Check seed file columns
import pandas as pd
df = pd.read_csv('hh_gq/data/seed_households.csv', nrows=5)
print('hhgqtype' in df.columns)  # Should be True

# Check file sizes
import os
print(f"Households: {os.path.getsize('hh_gq/data/seed_households.csv')/1e6:.1f} MB")
print(f"Persons: {os.path.getsize('hh_gq/data/seed_persons.csv')/1e6:.1f} MB")

# Check record counts
hh_df = pd.read_csv('hh_gq/data/seed_households.csv')
p_df = pd.read_csv('hh_gq/data/seed_persons.csv')
print(f"Households: {len(hh_df):,} records")
print(f"Persons: {len(p_df):,} records")
```

This documentation provides a complete map of all file movements, transformations, and dependencies in the PopulationSim TM2 workflow.
