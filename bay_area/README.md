# TM2 Population Synthesis Pipeline

This repository contains the complete TM2 (Travel Model 2) population synthesis pipeline for the San Francisco Bay Area. The pipeline uses PopulationSim to generate synthetic households and persons that match control totals from the Census and American Community Survey.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Setup and Configuration](#setup-and-configuration)
- [Running the Pipeline](#running-the-pipeline)
- [Pipeline Overview](#pipeline-overview)
- [File Structure](#file-structure)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- **Python 3.8+** with PopulationSim environment
- **Anaconda/Miniconda** (recommended for environment management)
- **Git** for version control
- **Windows** (paths are currently Windows-specific)

### Required Data Access
- **M: Drive Access** - The pipeline requires access to cached Census data on the M: drive:
  - `M:\Data\Census\PUMS_2023_5Year_Crosswalked\`
  - `M:\Data\Census\NewCachedTablesForPopulationSimControls\`
  - `M:\Data\GIS layers\TM2_maz_taz_v2.2\`

### External Dependencies
- **tm2py-utils repository** - Must be cloned to `C:\GitHub\tm2py-utils\`
  - Contains required shapefiles and geographic data
  - Clone from: [tm2py-utils repository location]

## Setup and Configuration

### 1. Python Environment Setup

The pipeline requires a specific Python environment with PopulationSim installed. 

**Important**: You must update the Python path in `unified_tm2_config.py`:

```python
# In unified_tm2_config.py, line ~30
self.PYTHON_EXE = Path(r"C:\Users\[YOUR_USERNAME]\AppData\Local\anaconda3\envs\popsim\python.exe")
```

Replace `[YOUR_USERNAME]` with your actual Windows username.

### 2. Environment Variables (Optional)

You can override the Python executable using an environment variable:

```powershell
$env:POPSIM_PYTHON_EXE = "C:\path\to\your\python.exe"
```

### 3. Directory Structure

The pipeline expects this directory structure:
```
bay_area/
├── tm2_pipeline.py              # Main pipeline script
├── unified_tm2_config.py        # Central configuration
├── create_tm2_crosswalk.py      # Step 1: Crosswalk creation
├── create_seed_population_tm2_refactored.py  # Step 2: Seed population
├── create_baseyear_controls_23_tm2.py        # Step 3: Control totals
├── run_populationsim_synthesis.py           # Step 4: PopulationSim
├── output_2023/                 # Generated output directory
│   └── populationsim_working_dir/
│       ├── data/               # Input data for PopulationSim
│       ├── configs/            # PopulationSim configuration files
│       └── output/             # PopulationSim results
└── example_controls_2015/       # Reference data for employment/land use
```

## Running the Pipeline

### Quick Start

1. **Check Status**:
   ```powershell
   python tm2_pipeline.py status
   ```

2. **Run Full Pipeline**:
   ```powershell
   python tm2_pipeline.py full
   ```

3. **Run with Force (regenerate all outputs)**:
   ```powershell
   python tm2_pipeline.py full --force
   ```

### Individual Steps

You can run individual pipeline steps:

```powershell
# Step 1: Create geographic crosswalk
python tm2_pipeline.py crosswalk

# Step 2: Create seed population
python tm2_pipeline.py seed

# Step 3: Generate control totals
python tm2_pipeline.py controls

# Step 4: Run PopulationSim synthesis
python tm2_pipeline.py populationsim
```

### Advanced Options

- **Start from specific step**:
  ```powershell
  python tm2_pipeline.py full --start seed
  ```

- **Run specific range**:
  ```powershell
  python tm2_pipeline.py full --start crosswalk --end controls
  ```

- **Offline mode** (skip PUMS download):
  ```powershell
  python tm2_pipeline.py full --offline
  ```

- **Quiet mode** (reduce output):
  ```powershell
  python tm2_pipeline.py full --quiet
  ```

- **Test with single PUMA**:
  ```powershell
  $env:TEST_PUMA = "7502"
  python tm2_pipeline.py full
  ```

## Pipeline Overview

The TM2 population synthesis pipeline consists of four main steps:

### Step 1: Crosswalk Creation (`crosswalk`)
**Script**: `create_tm2_crosswalk.py`
**Purpose**: Creates geographic relationships between MAZ, TAZ, and PUMA zones
**Inputs**: 
- MAZ shapefile from tm2py-utils
- PUMA shapefile from tm2py-utils
**Outputs**:
- `geo_cross_walk_tm2_updated.csv` - Geographic crosswalk file
**Duration**: ~2-3 minutes

### Step 2: Seed Population (`seed`)
**Script**: `create_seed_population_tm2_refactored.py`
**Purpose**: Processes PUMS data to create seed households and persons
**Inputs**:
- PUMS household data (M: drive)
- PUMS person data (M: drive)
- Geographic crosswalk from Step 1
**Outputs**:
- `seed_households.csv` - Processed household data
- `seed_persons.csv` - Processed person data
**Duration**: ~5-10 minutes

### Step 3: Control Totals (`controls`)
**Script**: `create_baseyear_controls_23_tm2.py` 
**Purpose**: Generates control totals at MAZ, TAZ, and County levels
**Inputs**:
- Cached Census/ACS data (M: drive)
- Geographic crosswalk
- Reference MAZ data for employment
**Outputs**:
- `maz_marginals.csv` - MAZ-level control totals
- `taz_marginals.csv` - TAZ-level control totals  
- `county_marginals.csv` - County-level control totals
- `maz_data.csv` & `maz_data_withDensity.csv` - MAZ characteristics
**Duration**: ~30-60 minutes

### Step 4: PopulationSim Synthesis (`populationsim`)
**Script**: `run_populationsim_synthesis.py`
**Purpose**: Runs PopulationSim to generate synthetic population
**Inputs**:
- Seed population from Step 2
- Control totals from Step 3
- PopulationSim configuration files
**Outputs**:
- `synthetic_households.csv` - Final synthetic households
- `synthetic_persons.csv` - Final synthetic persons
- `summary_melt.csv` - Summary statistics
**Duration**: ~2-6 hours (depending on integerization complexity)

## File Structure

### Input Data Locations
- **PUMS Data**: `M:\Data\Census\PUMS_2023_5Year_Crosswalked\`
- **Census Controls**: `M:\Data\Census\NewCachedTablesForPopulationSimControls\`
- **Shapefiles**: `C:\GitHub\tm2py-utils\tm2py_utils\inputs\maz_taz\shapefiles\`
- **Reference Data**: `bay_area/example_controls_2015/`

### Output Data Structure
```
output_2023/
├── populationsim_working_dir/
│   ├── data/                    # PopulationSim input data
│   │   ├── seed_households.csv
│   │   ├── seed_persons.csv
│   │   ├── geo_cross_walk_tm2_updated.csv
│   │   ├── maz_marginals.csv
│   │   ├── taz_marginals.csv
│   │   ├── county_marginals.csv
│   │   └── maz_data_withDensity.csv
│   ├── configs/                 # PopulationSim configuration
│   │   ├── settings.yaml
│   │   ├── logging.yaml
│   │   └── controls.csv
│   └── output/                  # PopulationSim results
│       ├── synthetic_households.csv
│       ├── synthetic_persons.csv
│       ├── summary_melt.csv
│       └── populationsim.log
└── [other intermediate files]
```

### Configuration Files
- **`unified_tm2_config.py`**: Central configuration for all paths and settings
- **`settings.yaml`**: PopulationSim algorithm settings
- **`logging.yaml`**: PopulationSim logging configuration
- **`controls.csv`**: PopulationSim control specification

## Monitoring Progress

### Real-time Monitoring
The pipeline provides detailed progress logging:

- **Step Progress**: Each step shows start/completion status
- **File Operations**: Input/output file operations are logged
- **PopulationSim Progress**: Enhanced monitoring with heartbeat logs every 5 minutes
- **Memory Usage**: Memory consumption tracking
- **Error Handling**: Detailed error messages and tracebacks

### Log Files
- **Console Output**: Real-time progress in terminal
- **PopulationSim Log**: `output_2023/populationsim_working_dir/output/populationsim.log`

### Expected Runtimes
- **Full Pipeline**: 3-7 hours total
- **Crosswalk**: 2-3 minutes
- **Seed Population**: 5-10 minutes  
- **Controls**: 30-60 minutes
- **PopulationSim**: 2-6 hours (integerization is the longest step)

## Troubleshooting

### Common Issues

1. **Python Path Error**
   ```
   FileNotFoundError: PopulationSim Python environment not found
   ```
   **Solution**: Update the Python path in `unified_tm2_config.py`

2. **M: Drive Access Error**
   ```
   FileNotFoundError: PUMS files not found
   ```
   **Solution**: Ensure you have access to the M: drive and required directories

3. **Shapefile Not Found**
   ```
   ERROR: MAZ shapefile not found
   ```
   **Solution**: Clone tm2py-utils repository to `C:\GitHub\tm2py-utils\`

4. **PopulationSim Configuration Error**
   ```
   Settings file 'settings.yaml' not found
   ```
   **Solution**: This should be fixed by the working directory handling in the updated script

5. **Memory Issues**
   ```
   MemoryError during large data processing
   ```
   **Solution**: Close other applications, consider running on a machine with more RAM

### Recovery Options

- **Resume from specific step**: Use `--start` parameter to skip completed steps
- **Force regeneration**: Use `--force` to regenerate all outputs
- **Check status**: Use `status` command to see which steps completed
- **Clean outputs**: Use `clean` command to remove specific step outputs

### Getting Help

1. **Check pipeline status**: `python tm2_pipeline.py status`
2. **Review log files**: Check console output and PopulationSim logs
3. **Validate file paths**: Ensure all required directories and files exist
4. **Test with single PUMA**: Use `TEST_PUMA` environment variable for faster testing

## Advanced Configuration

### Environment Variables
- `POPSIM_PYTHON_EXE`: Override Python executable path
- `TEST_PUMA`: Run with single PUMA for testing (e.g., "7502")
- `FORCE_*`: Force regeneration of specific steps (CROSSWALK, SEED, CONTROLS, etc.)

### File Path Customization
All paths are centralized in `unified_tm2_config.py`. Key paths include:
- `PYTHON_EXE`: Python executable
- `EXTERNAL_PATHS`: M: drive and external data locations
- `POPSIM_WORKING_DIR`: PopulationSim working directory
- `OUTPUT_DIR`: Main output directory

### PopulationSim Settings
PopulationSim behavior can be customized via `configs/settings.yaml`:
- Algorithm parameters
- Convergence tolerances  
- Integerization settings
- Balancing options

## Data Outputs

The pipeline produces several key outputs:

### Final Synthetic Population
- **`synthetic_households.csv`**: Synthetic households with all attributes
- **`synthetic_persons.csv`**: Synthetic persons with all attributes
- **Geographic Assignment**: Each household/person assigned to specific MAZ/TAZ/PUMA

### Quality Assurance
- **`summary_melt.csv`**: Detailed control vs. synthetic comparisons
- **Control Conservation**: Validates that totals are preserved
- **Geographic Coverage**: Ensures all zones have appropriate population

### Intermediate Data
- **Seed Population**: Processed PUMS data
- **Control Totals**: Census/ACS marginal distributions
- **Geographic Crosswalk**: Zone relationship mappings

---

**Last Updated**: August 2025  
**Pipeline Version**: TM2 2023  
**PopulationSim Version**: Compatible with ActivitySim framework
