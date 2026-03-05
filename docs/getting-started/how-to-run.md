---
layout: default
title: How to Run
nav_order: 2
parent: Getting Started
---

# How to Run the TM2 PopulationSim Pipeline

Complete instructions for executing the population synthesis pipeline.

## Prerequisites

Before running the pipeline:

1. ✓ [Environment setup](environment-setup.html) completed
2. ✓ Conda environment activated (`conda activate popsim`)
3. ✓ Geographic crosswalk files generated (see below)

---

## Quick Start

### 1. Activate Environment

```bash
# Activate conda environment
conda activate popsim

# Verify Python version (should be 3.8.20)
python --version

# Navigate to project directory
cd C:/GitHub/populationsim/bay_area

# Verify environment
python setup_environment.py
```

### 2. Generate Geographic Crosswalk (Required)

**IMPORTANT**: The pipeline requires pre-generated crosswalk files. These must be created from the separate `tm2py-utils` repository:

```bash
# Navigate to tm2py-utils repository
cd C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz

# Generate crosswalk files
python standalone_tm2_crosswalk_creator.py

# This creates:
# - geo_cross_walk_tm2_maz.csv
# - geo_cross_walk_tm2_block10.csv
```

These files will be output to your PopulationSim `data/` directory. See [Geographic Crosswalk Guide](../guides/geo-crosswalk.html) for more details.

### 3. Run Full Pipeline

```bash
# Run complete pipeline (recommended)
python tm2_pipeline.py full --force

# Estimated runtime: 2-3 hours total
# - PUMS data processing: ~5-10 min
# - Seed population: ~5 min
# - Control generation: ~15 min
# - Population synthesis (IPF): ~45-90 min
# - Post-processing: ~10 min
# - Summary analysis: ~15-20 min
```

---

## Running Individual Steps

You can run pipeline steps individually for debugging or iterative development:

```bash
# Step 1: Download and process PUMS data
python tm2_pipeline.py pums --force

# Step 2: Create seed population from PUMS data
python tm2_pipeline.py seed --force

# Step 3: Generate control totals from Census data
python tm2_pipeline.py controls --force

# Step 4: Run population synthesis (longest step)
python tm2_pipeline.py populationsim --force

# Step 5: Post-process and format outputs for TM2
python tm2_pipeline.py postprocess --force

# Step 6: Generate summary reports and visualizations
python tm2_pipeline.py summary_analysis --force

# Step 7: Run detailed analysis scripts
python tm2_pipeline.py analysis --force

# Step 8: Validate income distributions
python tm2_pipeline.py validate_income --force
```

### Step Status Checking

```bash
# Check which steps have been completed
python tm2_pipeline.py status

# Output shows:
# ✓ seed_population - COMPLETE
# ✓ control_generation - COMPLETE  
# ○ population_synthesis - NOT STARTED
# ○ postprocessing - NOT STARTED
```

---

## Command-Line Options

### Full Pipeline

```bash
python tm2_pipeline.py full [--force]
```

**Options**:
- `--force` - Rerun steps even if already completed

### Check Status

```bash
python tm2_pipeline.py status
```

Shows completion status of all pipeline steps.

### Individual Steps

```bash
python tm2_pipeline.py <step> [--force]
```

**Available steps**:

| Command | Description | Typical Runtime |
|---------|-------------|-----------------|
| `status` | Show current pipeline status | Instant |
| `pums` | Download/process PUMS data | 5-10 min |
| `seed` | Create seed population | 2-5 min |
| `controls` | Generate control totals | 10-15 min |
| `populationsim` | Run IPF synthesis | 45-90 min |
| `postprocess` | Format outputs for TM2 | 5-10 min |
| `summary_analysis` | Generate summary reports | 15-20 min |
| `analysis` | Run detailed analysis scripts | 10-15 min |
| `validate_income` | Validate income distributions | 2-5 min |
| `full` | Run complete pipeline | 2-3 hours |
| `clean` | Remove all outputs (fresh start) | Instant |

---

## Configuration

### Path Configuration

All file paths are centralized in `unified_tm2_config.py`. Key configurations:

#### External Data Paths

```python
# Network data locations (edit if different)
self.EXTERNAL_PATHS = {
    'network_census_cache': Path("M:/Data/Census/..."),
    'network_census_api': Path("M:/Data/Census/API/..."),
    'pums_current': Path("M:/Data/Census/PUMS_2023_5Year_Crosswalked"),
}
```

**Note**: Pipeline automatically falls back to local data if network paths are unavailable.

#### Census API Key

Required for downloading control data. Place your API key in:
- Network: `M:/Data/Census/API/new_key/api-key.txt`
- Local: `bay_area/data/api-key.txt`

Get a free API key: [https://api.census.gov/data/key_signup.html](https://api.census.gov/data/key_signup.html)

#### GIS Reference Files

Required zone definition files:
- `blocks_mazs_tazs.csv` - MAZ-TAZ mappings
- `mazs_tazs_all_geog.csv` - Complete geography definitions

These should be available from network or local GIS directories.

---

## Expected Outputs

After successful pipeline execution:

### Output Directory Structure

```
bay_area/
├── output_2023/
│   ├── populationsim_working_dir/
│   │   ├── output/
│   │   │   ├── synthetic_households.csv
│   │   │   ├── synthetic_persons.csv
│   │   │   └── summary_*_taz.csv
│   │   └── diagnostics/
│   │       └── [validation plots and reports]
│   └── tm2_outputs/
│       ├── households_taz_*.csv
│       ├── persons_taz_*.csv
│       └── [formatted export files]
└── logs/
    └── [pipeline execution logs]
```

### Key Output Files

| File | Description |
|------|-------------|
| `synthetic_households.csv` | Final synthetic household records |
| `synthetic_persons.csv` | Final synthetic person records |
| `summary_*_taz.csv` | TAZ-level control vs. result summaries |
| `households_taz_*.csv` | TAZ-aggregated household data |
| `persons_taz_*.csv` | TAZ-aggregated person data |

See [Outputs Documentation](../outputs/) for complete field definitions.

---

## Troubleshooting

### "Crosswalk files not found"

**Problem**: Missing `geo_cross_walk_tm2_maz.csv` or `geo_cross_walk_tm2_block10.csv`

**Solution**: Generate crosswalk files first (see step 2 above)

### "No module named 'dask'"

**Problem**: Missing required dependency

**Solution**:
```bash
conda activate popsim
conda install -c conda-forge dask
```

### "FileNotFoundError: Census API key"

**Problem**: Missing Census API key file

**Solution**: 
1. Get API key from [Census website](https://api.census.gov/data/key_signup.html)
2. Save to `bay_area/data/api-key.txt`

### Pipeline hangs during synthesis

**Problem**: PopulationSim IPF not converging

**Solution**:
- Check log files in `logs/` directory
- Review control totals for inconsistencies
- See [Population Synthesis Guide](../guides/population-synthesis.html) for convergence tips

### Memory errors

**Problem**: System runs out of memory during synthesis

**Solution**:
- Close other applications
- Ensure at least 16GB RAM available
- Consider processing fewer geographies at once

---

## Next Steps

After successful pipeline execution:

1. **Validate Results**: Review [Output Summaries](../outputs/summaries.html)
2. **Understand the Process**: Read [Process Overview](../process/overview.html)
3. **Explore Components**: Check individual [Guides](../guides/)

---

## Related Documentation

- [Environment Setup](environment-setup.html) - Initial setup
- [Process Overview](../process/overview.html) - Pipeline architecture
- [Geographic Crosswalk](../guides/geo-crosswalk.html) - Crosswalk details
- [Population Synthesis](../guides/population-synthesis.html) - Synthesis algorithm
- [Outputs](../outputs/) - Understanding results

---

[← Back to Getting Started](index.html) | [Home](../index.html)
