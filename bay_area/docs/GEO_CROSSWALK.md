# Crosswalk Step: Creating the TM2 Geographic Crosswalk

This step prepares the essential geographic crosswalk files used throughout the Bay Area PopulationSim pipeline. The crosswalks map MAZs, TAZs, counties, and other geographies, enabling consistent aggregation and disaggregation of data.

## What This Step Does

- **`create_tm2_crosswalk.py`**:  
  Generates the initial crosswalk between MAZs, TAZs, counties, and other geographies using source shapefiles and lookup tables.
- **`build_complete_crosswalk.py`**:  
  Enhances the initial crosswalk by adding additional attributes, performing data validation, and ensuring all required geographies are represented.  
  **The enhanced crosswalk (`geo_cross_walk_tm2_enhanced.csv`) is a required input for the control generation step (`create_baseyear_controls_23_tm2.py`).**

## Inputs

- MAZ/TAZ shapefiles and definitions
- County and PUMA definitions
- (See `unified_tm2_config.py` for exact paths)

## Outputs

- `geo_cross_walk_tm2.csv`: The initial crosswalk file.
- `geo_cross_walk_tm2_enhanced.csv`: The enhanced crosswalk, **required for and used by the control generation step**.

## How to Run

From the `bay_area` directory, run:

```sh
python create_tm2_crosswalk.py
python build_complete_crosswalk.py
```

These scripts will generate the crosswalk files in the configured output directory.

## Notes

- The enhanced crosswalk is a critical input for generating controls in `create_baseyear_controls_23_tm2.py`.
- If you update any source geography files, you must re-run this step.
- For more details on configuration and file paths, see [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) and [HOW_TO_RUN.md](HOW_TO_RUN.md).

---

*Return to the [main documentation index](README.md) for other pipeline steps.*