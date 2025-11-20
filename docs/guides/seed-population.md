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

## Group Quarters Handling

**Important Policy Change:** As of October 2025, this script implements a **person-level group quarters approach** with two-stage assignment and person-level `gq_type` field for PopulationSim person-level controls.

### TYPEHUGQ-Based Exclusion Policy

The script uses the PUMS `TYPEHUGQ` variable for group quarters classification:

- **TYPEHUGQ = 1**: Housing units (households) → **INCLUDED**
- **TYPEHUGQ = 2**: Institutional GQ (nursing homes, prisons, etc.) → **EXCLUDED**  
- **TYPEHUGQ = 3**: Noninstitutional GQ (university dorms, military barracks, group homes) → **INCLUDED**

### Two-Stage GQ Assignment Process

Due to PUMS data limitations, we use a sophisticated two-stage approach:

**Stage 1 - Household Level Processing:**
- All noninstitutional GQ households (TYPEHUGQ = 3) initially assigned to **hhgqtype = 2**
- Cannot distinguish university vs. military at household level due to PUMS aggregation

**Stage 2 - Person Level Refinement:**
- University students identified using college enrollment status (SCHG 15-16, any age)
- University students reassigned to **hhgqtype = 1** 
- Their households also updated to **hhgqtype = 1** for consistency
- Military and other GQ remain as **hhgqtype = 2**

### Person-Level gq_type Field

For PopulationSim person-level controls, a `gq_type` field is created on each person record:
- **gq_type = 0**: Regular household persons (from hhgqtype = 0 households)
- **gq_type = 1**: University GQ persons (from hhgqtype = 1 households)  
- **gq_type = 2**: Noninstitutional GQ persons (from hhgqtype = 2 households)

This field enables PopulationSim to use person-level control expressions like `persons.gq_type==1` that directly match Census person-level GQ data structure.

### Final PopulationSim Structure

For PopulationSim balancing:
- **Household level**: `hhgqtype` (0=regular, 1=university, 2=noninstitutional)
- **Person level**: `gq_type` (0=regular, 1=university, 2=noninstitutional)

### Output TYPE Field Creation

For travel model compatibility, a collapsed `TYPEHUGQ` field is created:
- **TYPEHUGQ = 1**: Housing units (hhgqtype = 0)
- **TYPEHUGQ = 3**: All noninstitutional GQ (hhgqtype = 1 or 2)

This ensures the final `TYPE` field in travel model outputs correctly represents the original PUMS categories while allowing person-level detailed balancing during synthesis.

**Rationale**: This approach uses person-level controls that align directly with Census P5 series data structure, eliminating household-level conversion assumptions while maintaining PopulationSim convergence and travel model compatibility.

## Notes

- The script uses many configuration values and crosswalks from `unified_tm2_config.py`.
- If you update PUMS data or crosswalks, you must re-run this step.
- For more details on configuration and file paths, see [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) and [HOW_TO_RUN.md](HOW_TO_RUN.md).
- There are many "magic numbers" in the script; future refactoring should move these to a dedicated config file.

---

*Return to the [main documentation index](README.md) for other pipeline steps.*


