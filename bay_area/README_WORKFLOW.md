# Bay Area PopulationSim TM2 Workflow

This document explains the complete workflow for running PopulationSim for the Bay Area using TM2 geography with 2023 ACS data.

## Overview

The PopulationSim workflow creates synthetic household and person data for the Bay Area using Census and ACS data sources. The process involves generating control totals at different geographic levels (MAZ, TAZ, County) and using these to synthesize a population that matches demographic targets.

## Quick Start

For a complete run with default settings:

```batch
.\run_populationsim_tm2.bat 2023
```

For interactive configuration (recommended for development):

```batch
.\run_populationsim_tm2_config.bat
```

The workflow automatically detects existing files and skips completed steps. This means:
- If seed files exist, seed generation is skipped
- If control files exist, control generation is skipped  
- If PopulationSim output exists, synthesis is skipped
- If post-processing output exists, post-processing is skipped

### Force Flags

You can force specific steps to run by editing the configuration flags at the top of `run_populationsim_tm2.bat`:

```batch
set FORCE_SEED=1           :: Force seed generation even if files exist
set FORCE_CONTROLS=1       :: Force control generation even if files exist
set FORCE_HHGQ=1          :: Force group quarters integration even if files exist
set FORCE_POPULATIONSIM=1 :: Force PopulationSim synthesis even if files exist
set FORCE_POSTPROCESS=1   :: Force post-processing even if files exist
```

### Common Usage Patterns

1. **First run:** `.\run_populationsim_tm2.bat 2023` (all steps will run)
2. **Debugging PopulationSim:** Set `FORCE_POPULATIONSIM=1` to re-run only synthesis
3. **Update controls:** Set `FORCE_CONTROLS=1` and `FORCE_HHGQ=1` to regenerate inputs
4. **Clean rebuild:** Set all force flags to 1 to regenerate everything

## Detailed Workflow

### 1. Seed Population Generation

**Script:** `create_seed_population_tm2.py`
**Output:** `hh_gq/data/seed_households.csv`, `hh_gq/data/seed_persons.csv`

Creates PUMS-based seed files for all 66 Bay Area PUMAs, providing the template households and persons that PopulationSim will replicate and modify to match control totals.

### 2. Control Generation (Simplified Workflow)

**Script:** `create_baseyear_controls_23_tm2.py --output_dir hh_gq/data`
**Output Directory:** `hh_gq/data/`

Generates control totals directly in the PopulationSim data directory:

- **MAZ Level:** `maz_marginals.csv`
  - Household counts (`num_hh`) from 2020 Census blocks
  - Group quarters population by type
  - County-level scaling applied using ACS 2023 1-year estimates

- **TAZ Level:** `taz_marginals.csv`
  - Household income distribution (4 categories, inflation-adjusted to 2023 dollars)
  - Workers per household (0, 1, 2, 3+)
  - Person age groups (0-19, 20-34, 35-64, 65+)
  - Households with/without children
  - Household size distribution (1, 2, 3, 4+ persons)

- **County Level:** `county_marginals.csv`
  - Person occupation categories (management, professional, services, retail, manual, military)

- **Geography Crosswalk:** `geo_cross_walk_tm2.csv`
  - Links MAZ/TAZ geography to Census blocks, block groups, and tracts
  - Includes all 66 Bay Area PUMAs

**Key Features:**
- Uses household weight improvements for better geographic interpolation
- Applies 2020→2010 Census geography crosswalks via NHGIS
- County-level scaling ensures totals match ACS 2023 1-year estimates
- Handles missing data and edge cases gracefully

### 3. Group Quarters Integration

**Script:** `add_hhgq_combined_controls.py --model_type TM2`
**Input:** Files from step 2
**Output:** `*_hhgq.csv` versions of control files

Modifies control files to treat group quarters residents as single-person households, allowing PopulationSim to synthesize them properly.

### 4. Population Synthesis

**Script:** `run_populationsim.py --config hh_gq/configs_TM2 --output output_2023/populationsim_run --data hh_gq/data`
**Output Directory:** `output_2023/populationsim_run/`

Runs the PopulationSim balancing algorithm to create:
- `synthetic_households.csv` - Synthetic household records
- `synthetic_persons.csv` - Synthetic person records  
- `final_summary_*.csv` - Summary statistics by geography
- `populationsim.log` - Detailed execution log

### 5. Post-Processing

**Script:** `postprocess_recode.py --model_type TM2 --directory output_2023/populationsim_run --year 2023`

Final processing and validation:
- Recodes variables for travel model compatibility
- Creates summary files for validation
- Generates `summary_melt.csv` for Tableau analysis

## File Locations

### Input Data Sources
- **Network Drive:** `M:\Data\Census\` (Census API cache)
- **Local Cache:** `input_2023/NewCachedTablesForPopulationSimControls/`
- **Geography:** `M:\Data\GIS layers\TM2_maz_taz_v2.2\`

### Working Directory Structure
```
bay_area/
├── hh_gq/
│   ├── data/                    # PopulationSim input files
│   └── configs_TM2/            # PopulationSim configuration
├── output_2023/
│   └── populationsim_run/      # Final outputs
├── tm2_control_utils/          # Control generation utilities
└── *.py                        # Main scripts
```

### Key Files
- **Controls:** `hh_gq/data/maz_marginals.csv`, `taz_marginals.csv`, `county_marginals.csv`
- **Geography:** `hh_gq/data/geo_cross_walk_tm2.csv`
- **Seed Data:** `hh_gq/data/seed_households.csv`, `seed_persons.csv`
- **Outputs:** `output_2023/populationsim_run/synthetic_*.csv`

## Configuration

### Key Settings (in `tm2_control_utils/config.py`)

- **Data Years:** 2020 Census blocks, 2023 ACS estimates
- **Geography:** 2010 Census boundaries (MAZ/TAZ compatibility)
- **Income Categories:** Inflation-adjusted to 2023 purchasing power
- **Control Categories:** Simplified for current Census data availability

### Customization Options

- **Test Mode:** Set `TEST_PUMA=02402` in batch script for single PUMA
- **Output Directory:** Modify `OUTPUT_DIR` in batch script
- **Local Data:** Configure local cache paths in config file

## Data Sources

### Census Data (via API)
- **2020 Decennial Census PL 94-171:** Block-level household counts and group quarters
- **ACS 2023 5-year:** Tract and block group demographics  
- **ACS 2023 1-year:** County-level scaling targets

### Geography Data
- **NHGIS Crosswalks:** 2020→2010 Census geography interpolation
- **TM2 Geography:** MAZ/TAZ definitions and relationships

## Validation

### Automated Checks
- Control total validation against source data
- Geographic coverage verification
- Missing data identification

### Manual Review
- Compare `final_summary_*.csv` with source Census data
- Review `populationsim.log` for convergence issues
- Use `validation.twb` Tableau workbook for visualization

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   - Install: `pip install census beautifulsoup4`

2. **Network Drive Access**
   - Verify M: drive connectivity
   - Use local cache if network unavailable

3. **Memory Issues**
   - Run single PUMA first (`TEST_PUMA=02402`)
   - Monitor memory usage during synthesis

4. **Convergence Problems**
   - Check for zero household zones in MAZ controls
   - Review control total reasonableness
   - Examine balancing algorithm logs

### Error Locations
- **Control Generation:** Check `create_baseyear_controls_2023.log`
- **PopulationSim:** Check `output_2023/populationsim_run/populationsim.log`
- **Post-processing:** Check console output during `postprocess_recode.py`

## Performance

### Typical Runtime
- Control Generation: ~10-15 minutes
- PopulationSim: ~45-60 minutes (full region)
- Post-processing: ~5 minutes

### Resource Requirements
- RAM: 8GB+ recommended (16GB for full region)
- Disk: ~2GB for outputs
- Network: Required for Census API and M: drive access

## Recent Improvements

### Configurable Workflow (2025)
- Added intelligent step detection based on existing files
- Each workflow step can be forced to re-run via configuration flags
- Interactive configuration script (`run_populationsim_tm2_config.bat`) for easy setup
- Status checking shows what steps are complete vs. needed
- Eliminates redundant work during development and debugging

### Simplified Workflow (2025)
- Controls generated directly in PopulationSim data directory
- Eliminated confusing file copying between directories
- Clearer separation of input generation vs. synthesis
- Reduced opportunities for file handling errors

### Household Weight Improvements
- Enhanced geographic interpolation using household-level weights
- Better handling of tract→block group disaggregation
- Improved accuracy for areas with non-uniform population density

## Contact

For questions about this workflow:
- Check existing documentation in `tm2_control_utils/`
- Review configuration files for parameter explanations
- Examine log files for detailed execution information
