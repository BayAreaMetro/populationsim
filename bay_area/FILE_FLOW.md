# TM2 PopulationSim File Flow

## File Flow Overview

This document describes how data flows through the TM2 PopulationSim pipeline, from input sources to final synthetic population.

```
[External Data] → [Pipeline Steps] → [Intermediate Files] → [Final Outputs]
```

## Input Data Sources

### Census Bureau Data
- **PUMS Microdata**: `households_2023_raw.csv`, `persons_2023_raw.csv`
- **ACS Tables**: Downloaded via Census API for marginal controls
- **Source**: US Census Bureau 2023 5-year American Community Survey

### Geographic Reference Data
- **MAZ/TAZ Definitions**: `blocks_mazs_tazs.csv`, `mazs_tazs_all_geog.csv`
- **PUMA Boundaries**: TM2 model geographic framework
- **Source**: MTC/ABAG Travel Model 2

### Configuration Files
- **Control Specifications**: `hh_gq/controls.csv`
- **PopulationSim Settings**: `hh_gq/settings.yaml`
- **Pipeline Configuration**: `unified_tm2_config.py`

## Step-by-Step File Flow

### Step 1: PUMS Download
```
External → Pipeline → Output
Census API → download_2023_5year_pums.py → households_2023_raw.csv
                                        → persons_2023_raw.csv
```

**Process**:
1. Queries Census API for Bay Area PUMAs (104 PUMAs)
2. Downloads household and person records
3. Applies inflation adjustment (2023→2010 dollars)
4. Saves raw microdata files

**Key Files**:
- Input: Census API
- Output: `output_2023/PUMS_2023_5Year/households_2023_raw.csv` (~175k records)
- Output: `output_2023/PUMS_2023_5Year/persons_2023_raw.csv` (~400k records)

### Step 2: Geographic Crosswalk
```
Reference Data → Pipeline → Output
blocks_mazs_tazs.csv → create_tm2_crosswalk.py → geo_cross_walk_tm2_updated.csv
mazs_tazs_all_geog.csv
```

**Process**:
1. Loads TM2 zone definition files
2. Creates MAZ-TAZ-PUMA-County relationships
3. Resolves multi-PUMA TAZs (assigns to dominant PUMA)
4. Converts FIPS county codes to sequential 1-9 system

**Key Files**:
- Input: `M:/Data/GIS layers/TM2_maz_taz_v2.2/blocks_mazs_tazs.csv`
- Input: `M:/Data/GIS layers/TM2_maz_taz_v2.2/mazs_tazs_all_geog.csv`
- Output: `output_2023/populationsim_working_dir/data/geo_cross_walk_tm2_updated.csv`

### Step 3: Seed Population
```
PUMS Data + Crosswalk → Pipeline → Seed Files
households_2023_raw.csv → create_seed_population_tm2_refactored.py → seed_households.csv
persons_2023_raw.csv                                               → seed_persons.csv
geo_cross_walk_tm2_updated.csv
```

**Process**:
1. Assigns households to PUMAs (keeps original assignment)
2. Links persons to households via unique IDs
3. Adds geographic fields (PUMA, county)
4. Handles Group Quarters population
5. Creates PopulationSim-compatible formats

**Key Files**:
- Input: `output_2023/PUMS_2023_5Year/households_2023_raw.csv`
- Input: `output_2023/PUMS_2023_5Year/persons_2023_raw.csv`
- Input: `output_2023/populationsim_working_dir/data/geo_cross_walk_tm2_updated.csv`
- Output: `output_2023/populationsim_working_dir/data/seed_households.csv`
- Output: `output_2023/populationsim_working_dir/data/seed_persons.csv`

### Step 4: Marginal Controls
```
Census API + Config → Pipeline → Control Files
ACS Tables → create_baseyear_controls_23_tm2.py → maz_marginals.csv
controls.csv                                    → taz_marginals.csv
settings.yaml                                   → county_marginals.csv
```

**Process**:
1. Downloads ACS table data via Census API
2. Processes control specifications from `controls.csv`
3. Aggregates to MAZ, TAZ, and County levels
4. Handles Group Quarters controls separately
5. Creates age-income cross-tabulations

**Key Files**:
- Input: `hh_gq/controls.csv` (control variable definitions)
- Input: Census API (ACS tables)
- Input: `output_2023/populationsim_working_dir/data/geo_cross_walk_tm2_updated.csv`
- Output: `output_2023/populationsim_working_dir/data/maz_marginals.csv`
- Output: `output_2023/populationsim_working_dir/data/taz_marginals.csv`
- Output: `output_2023/populationsim_working_dir/data/county_marginals.csv`

### Step 5: PopulationSim Synthesis
```
Seed + Controls + Config → PopulationSim → Synthetic Population
seed_households.csv → run_populationsim_synthesis.py → synthetic_households.csv
seed_persons.csv                                     → synthetic_persons.csv
*_marginals.csv                                      → summary_*.csv
settings.yaml
```

**Process**:
1. Loads seed population and marginal controls
2. Runs iterative proportional fitting (IPF) algorithm
3. Balances household weights to match controls
4. Integerizes weights to whole households
5. Assigns households to specific MAZs

**Key Files**:
- Input: `output_2023/populationsim_working_dir/data/seed_households.csv`
- Input: `output_2023/populationsim_working_dir/data/seed_persons.csv`
- Input: `output_2023/populationsim_working_dir/data/*_marginals.csv`
- Input: `hh_gq/settings.yaml`
- Output: `output_2023/populationsim_working_dir/output/synthetic_households.csv`
- Output: `output_2023/populationsim_working_dir/output/synthetic_persons.csv`
- Output: `output_2023/populationsim_working_dir/output/summary_COUNTY_*.csv` (9 files)

## Directory Structure and File Organization

### Working Directory Structure
```
bay_area/
└── output_2023/
    ├── PUMS_2023_5Year/              # Raw PUMS downloads
    │   ├── households_2023_raw.csv
    │   └── persons_2023_raw.csv
    └── populationsim_working_dir/    # PopulationSim workspace
        ├── data/                     # Input data for synthesis
        │   ├── geo_cross_walk_tm2_updated.csv
        │   ├── seed_households.csv
        │   ├── seed_persons.csv
        │   ├── maz_marginals.csv
        │   ├── taz_marginals.csv
        │   └── county_marginals.csv
        ├── configs/                  # PopulationSim configuration
        │   ├── controls.csv
        │   └── settings.yaml
        └── output/                   # Final synthesis results
            ├── synthetic_households.csv
            ├── synthetic_persons.csv
            ├── summary_COUNTY_1.csv
            ├── summary_COUNTY_2.csv
            └── ... (through COUNTY_9)
```

### Configuration Files
```
bay_area/
├── unified_tm2_config.py           # Master configuration
├── tm2_pipeline.py                 # Pipeline orchestrator
└── hh_gq/                         # PopulationSim templates
    ├── controls.csv               # Control variable definitions
    └── settings.yaml              # PopulationSim settings
```

## File Dependencies and Data Flow

### Critical Dependencies
1. **Geographic Consistency**: All files must use same geographic definitions
2. **County Mapping**: 1-9 sequential system throughout pipeline
3. **PUMA Definitions**: Consistent Bay Area PUMA list (104 PUMAs)
4. **Control Variables**: Matching between controls.csv and marginal files

### Data Transformations

#### County Code Conversion
```
FIPS Codes → Sequential IDs
06001 (Alameda) → 4
06013 (Contra Costa) → 5
06041 (Marin) → 9
06055 (Napa) → 7
06075 (San Francisco) → 1
06081 (San Mateo) → 2
06085 (Santa Clara) → 3
06095 (Solano) → 6
06097 (Sonoma) → 8
```

#### Income Inflation
```
2023 ACS Dollars → 2010 Model Dollars
CPI Adjustment Factor: 0.7969
Example: $100,000 (2023) → $79,690 (2010)
```

#### Group Quarters Handling
```
HHGQTYPE Values:
1 = Household population
2 = Institutional group quarters (non-university)
3 = Institutional group quarters (university)
4 = Non-institutional group quarters

Control Expressions:
gq_pop: hhgqtype >= 2 (all GQ)
gq_university: hhgqtype == 3 AND age between 18-24
gq_other: hhgqtype == 2 OR hhgqtype == 4
```

## File Validation and Quality Checks

### Automated Checks
- **Row counts**: Verify expected number of records
- **Geographic coverage**: All MAZs/TAZs represented
- **Control totals**: Marginals sum to expected values
- **Data types**: Proper numeric/string formatting

### Manual Validation
- **County summaries**: Compare to Census estimates
- **Age distributions**: Realistic population pyramids
- **Income distributions**: Reasonable by geography
- **Household sizes**: Match regional patterns

## Troubleshooting File Issues

### Common File Problems
1. **Missing files**: Check path configurations in `unified_tm2_config.py`
2. **Format errors**: Verify CSV structure and data types
3. **Geographic mismatches**: Ensure consistent zone definitions
4. **Control total issues**: Check marginal calculations

### Debug Commands
```bash
# Check file existence
python tm2_pipeline.py status

# Validate individual steps
python tm2_pipeline.py crosswalk --force
python tm2_pipeline.py seed --force

# Check file row counts
wc -l output_2023/populationsim_working_dir/data/*.csv
```

## Performance and Timing

### Typical File Sizes
- **Raw PUMS**: ~100MB (households + persons)
- **Crosswalk**: ~2MB (MAZ-level records)
- **Seed files**: ~120MB (processed PUMS)
- **Marginals**: ~50MB total (all control files)
- **Synthetic output**: ~150MB (final population)

### Processing Times
- **PUMS download**: 10-30 minutes (depending on network)
- **Crosswalk creation**: 2-5 minutes
- **Seed generation**: 15-30 minutes
- **Controls creation**: 20-45 minutes (Census API dependent)
- **PopulationSim synthesis**: 60-180 minutes (main processing)
