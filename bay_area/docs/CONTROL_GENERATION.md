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

## Group Quarters Processing (Updated October 2025)

**Important Change**: Group quarters controls use **person-level controls** aligned with Census data structure to ensure data consistency and improve PopulationSim convergence.

### Background

Census provides group quarters data at the **person level** (P5 series tables), while PopulationSim can handle both household-level and person-level controls. The system now uses person-level GQ controls to directly match Census data structure, eliminating conversion assumptions and improving accuracy.

### Person-Level Group Quarters Approach

**Control Structure (Person Level):**

- `pers_gq_university`: University GQ persons (persons.gq_type==1)
- `pers_gq_noninstitutional`: Military + other GQ persons combined (persons.gq_type==2)

**Census Data Sources:**
- University GQ: Census P5_008N (College/university student housing persons)
- Noninstitutional GQ: Census P5_009N + P5_011N + P5_012N (Military quarters + other noninstitutional GQ persons)

### Final Group Quarters Inclusion Policy

- **✅ INCLUDED**: University/college housing (dorms, student housing) - P5_008N
- **✅ INCLUDED**: Military barracks and base housing - P5_009N
- **✅ INCLUDED**: Other non-institutional group quarters (group homes, worker dormitories, religious quarters) - P5_011N, P5_012N
- **❌ EXCLUDED**: Nursing homes and long-term care facilities - P5_010N
- **❌ EXCLUDED**: Correctional institutions and prisons - P5_002N to P5_007N
- **❌ EXCLUDED**: Mental health institutions - P5_002N to P5_007N
- **❌ EXCLUDED**: Other institutional care facilities - P5_002N to P5_007N

### Person-Level Control Structure

Person-level controls count individuals directly from Census data:
- `pers_gq_university`: Count of persons in university GQ (P5_008N)
- `pers_gq_noninstitutional`: Count of persons in military + other noninstitutional GQ (P5_009N + P5_011N + P5_012N)

### Household Count Integration

The `numhh_gq` control combines:
- Regular households (`num_hh` from Census H1_002N)
- GQ persons treated as household units (person counts as housing demand proxy)

This approach treats each GQ person as representing potential housing demand while maintaining person-level control accuracy.

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
