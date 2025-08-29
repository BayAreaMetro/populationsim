# Control Generation Step: Creating Baseyear Control Files

This step generates the baseyear control files required for the Bay Area PopulationSim model, using ACS 2023 and 2020 Decennial Census data. Controls are produced at the MAZ, TAZ, and county levels, and are used to guide the synthetic population generation process.

## What This Step Does

- **`create_baseyear_controls_23_tm2.py`**:
  - Downloads and caches Census data (ACS 2023, Decennial 2020).
  - Interpolates geographies as needed to match the MAZ/TAZ system.
  - Processes and scales controls at MAZ, TAZ, and county levels, using config-driven definitions.
  - Applies county-level scaling to ensure consistency with ACS 2023 county targets.
  - Validates and harmonizes controls for internal consistency.
  - Outputs all required marginal and summary files for PopulationSim and TM2.

## Inputs

- ACS 2023 5-year and 1-year estimates (tract, block group, county)
- 2020 Decennial Census data (block level)
- Geographic crosswalks (from the crosswalk step)
- Configuration in `unified_tm2_config.py` and `tm2_control_utils/config_census.py`

## Outputs

- `maz_marginals.csv`: MAZ-level controls (households, group quarters, etc.)
- `taz_marginals.csv`: TAZ-level controls (workers, age, household size, income, etc.)
- `county_marginals.csv`: County-level controls and region totals
- `county_summary_2020_2023.csv`: County scaling factors and validation
- `geo_cross_walk_tm2.csv`: Geographic crosswalk (copied from the crosswalk step)
- `maz_data.csv`, `maz_data_withDensity.csv`: Land use and density files for TM2
- `maz_marginals_hhgq.csv`, `taz_marginals_hhgq.csv`: Controls integrating households and group quarters

## How to Run

From the `bay_area` directory, run:

```sh
python create_baseyear_controls_23_tm2.py
```

This will generate all control and summary files in the configured output directory.

## Notes

- The enhanced crosswalk (`geo_cross_walk_tm2_enhanced.csv`) from the crosswalk step is required as input.
- If you update any Census data or crosswalks, you must re-run this step.
- For more details on configuration and file paths, see [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) and [HOW_TO_RUN.md](HOW_TO_RUN.md).

---

*Return to the [main documentation index](README.md) for other pipeline steps.*