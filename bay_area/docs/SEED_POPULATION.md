# Seed Population Creation Step

This step generates the synthetic seed population (households and persons) for the Bay Area PopulationSim model, using harmonized and filtered PUMS data. The output is used as the starting point for synthetic population generation and model calibration.

## What This Step Does

- **`create_seed_population_tm2_refactored.py`**:
  - Loads and filters PUMS household and person data for the Bay Area.
  - Harmonizes key variables and recodes fields to match legacy and TM2 requirements.
  - Links persons to households using unique IDs.
  - Handles group quarters, income inflation, and other special cases.
  - Validates and cleans the data for PopulationSim compatibility.
  - Outputs final `households.csv` and `persons.csv` files for use in PopulationSim.

## Inputs

- PUMS household and person files (see `unified_tm2_config.py` for paths)
- Crosswalk files for PUMA and county mapping
- Configuration in `unified_tm2_config.py`

## Outputs

- `households.csv`: Harmonized household records for PopulationSim
- `persons.csv`: Harmonized person records for PopulationSim
- `data_validation_report.txt`: Summary of data quality checks

## How to Run

From the `bay_area` directory, run:

```sh
python create_seed_population_tm2_refactored.py
```

This will generate the seed population files in the configured output directory.

## Notes

- The script uses many configuration values and crosswalks from `unified_tm2_config.py`.
- If you update PUMS data or crosswalks, you must re-run this step.
- For more details on configuration and file paths, see [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) and [HOW_TO_RUN.md](HOW_TO_RUN.md).
- There are many "magic numbers" in the script; future refactoring should move these to a dedicated config file.

---

*Return to the [main documentation index](README.md) for other pipeline steps.*