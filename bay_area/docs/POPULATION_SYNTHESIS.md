# Population Synthesis Step

This step runs the PopulationSim library to generate the synthetic population for the Bay Area, using the harmonized seed, control, and crosswalk files produced in earlier steps. The process is orchestrated via ActivitySim’s pipeline framework and produces the final synthetic households and persons for use in TM2 and other modeling applications.

## What This Step Does

- **`run_populationsim_synthesis.py`**:
  - Configures and launches the PopulationSim pipeline using ActivitySim’s pipeline and configuration system.
  - Tracks and logs detailed progress, including step-by-step timing and memory usage.
  - Handles long-running steps with heartbeat logging for monitoring.
  - Produces the final synthetic population outputs.

## Inputs

- `households.csv` and `persons.csv`: Harmonized seed population files (from the seed step)
- `maz_marginals_hhgq.csv`, `taz_marginals.csv`, `county_marginals.csv`: Control files (from the control generation step)
- `geo_cross_walk_tm2_enhanced.csv`: Enhanced crosswalk file (from the crosswalk step)
- `controls.csv`: PopulationSim control configuration with person-level GQ controls
- Configuration files for PopulationSim and ActivitySim (see `configs/` and `unified_tm2_config.py`)

## Person-Level Group Quarters Controls

**Important**: As of October 2025, PopulationSim uses **person-level group quarters controls** that align directly with Census data structure:

### Control Configuration

The `controls.csv` file defines person-level GQ controls:
- `pers_gq_university`: University GQ persons (persons.gq_type==1)
- `pers_gq_noninstitutional`: Military + other GQ persons (persons.gq_type==2)

### Seed Population Requirements

The seed population must include:
- **Household level**: `hhgqtype` field (0=regular, 1=university, 2=noninstitutional)
- **Person level**: `gq_type` field (0=regular, 1=university, 2=noninstitutional)

### Marginal Files

MAZ marginals (`maz_marginals_hhgq.csv`) contain:
- `numhh_gq`: Total household units (regular households + GQ persons as housing demand)
- `pers_gq_university`: Target university GQ person count (from Census P5_008N)
- `pers_gq_noninstitutional`: Target military+other GQ person count (from Census P5_009N+P5_011N+P5_012N)

This person-level approach eliminates household-level GQ conversion assumptions and ensures direct alignment with Census data structure.

## Outputs

- `final_households.csv`: Synthetic households for the Bay Area
- `final_persons.csv`: Synthetic persons for the Bay Area (with `gq_type` field)
- `populationsim.log`: Detailed log of the synthesis process
- Additional diagnostic and checkpoint files as configured

## How to Run

From the `bay_area` directory, run:

```sh
python run_populationsim_synthesis.py
```

This will execute the full PopulationSim synthesis pipeline and write outputs to the configured output directory.

## Notes

- This step relies on the [PopulationSim](https://github.com/ActivitySim/populationsim) library and [ActivitySim](https://github.com/ActivitySim/activitysim) for pipeline orchestration.
- All input files must be prepared and validated in previous steps.
- For more details on configuration and file paths, see [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) and [HOW_TO_RUN.md](HOW_TO_RUN.md).
- Monitor `populationsim.log` and the console output for progress and troubleshooting.

---

*Return to the [main documentation index](README.md) for other pipeline steps.*
