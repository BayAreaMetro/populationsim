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

## Column Naming Standards

### Geographic Column Naming Convention

**Standardized Column Names:**

- `MAZ_NODE`: Standardized MAZ identifier used throughout all crosswalk files
- `TAZ_NODE`: Standardized TAZ identifier used throughout all crosswalk files
- `COUNTY`: County identifier (numeric, e.g., 1-9 for Bay Area counties)
- `county_name`: County name (text, e.g., "Alameda", "San Francisco")
- `PUMA`: Public Use Microdata Area identifier

**Legacy Column Names (Deprecated):**

- `MAZ`: Old MAZ column name (replaced by `MAZ_NODE`)
- `TAZ`: Old TAZ column name (replaced by `TAZ_NODE`)

### Control File Column Structure

**MAZ Controls (`maz_marginals.csv` and `maz_marginals_hhgq.csv`):**

- `MAZ_NODE`: MAZ identifier (matches `MAZ_NODE` from crosswalk)
- `num_hh`: Number of households (Census H1_002N)
- `total_pop`: Total population
- `hh_gq_university`: University group quarters persons (P5_008N)
- `hh_gq_military`: Military group quarters persons (P5_009N) [combined into other]
- `hh_gq_other_nonins`: Other noninstitutional group quarters persons (P5_011N, P5_012N)
- `numhh_gq`: Combined household + GQ count (for PopulationSim person-as-household approach)

**TAZ Controls (`taz_marginals.csv` and `taz_marginals_hhgq.csv`):**

- `TAZ_NODE`: TAZ identifier (matches `TAZ_NODE` from crosswalk)
- `num_hh`: Number of households
- `hh_size_1` through `hh_size_4plus`: Household size categories
- `hh_inc_0_30k` through `hh_inc_200kplus`: Income categories
- `pers_age_00_17` through `pers_age_65plus`: Age categories
- `pers_workers_0` through `pers_workers_3plus`: Worker categories
- `hh_size_1_gq`: Size-1 households + GQ persons (for HHGQ integration)

**County Controls (`county_marginals.csv`):**

- `COUNTY`: County identifier (1-9)
- `pers_occ_management`: Management/business/finance workers
- `pers_occ_professional`: Professional/technical workers
- `pers_occ_services`: Service workers
- `pers_occ_retail`: Sales and office workers
- `pers_occ_manual_military`: Manual/production + military workers (combined)

**Geographic Crosswalk (`geo_cross_walk_tm2_maz.csv`):**

- `MAZ_NODE`: MAZ identifier
- `TAZ_NODE`: TAZ identifier
- `COUNTY`: County code (1-9)
- `county_name`: County name
- `PUMA`: PUMA identifier

### Column Naming Migration (October 2025)

**What Changed:**
The system was updated to use consistent `MAZ_NODE`/`TAZ_NODE` naming throughout all geographic crosswalk files. The `rebuild_maz_taz_all_geog_file()` function in `tm2_control_utils/config_census.py` was updated to ensure consistent column naming.

**Migration Impact:**

- All geographic aggregation operations now use standardized column names
- Census geographic matching uses consistent `MAZ_NODE`/`TAZ_NODE` references
- Control validation and hierarchical consistency checks work with unified naming
- PopulationSim input files use the standardized column structure

**Validation:**
The `mazs_tazs_all_geog.csv` crosswalk file was rebuilt with 109,228 records using the new naming convention, ensuring all geographic operations use consistent identifiers.

### Group Quarters Control Integration (October 2025)

**Military GQ Combination:**
As of October 2025, military group quarters persons are automatically combined into the "other noninstitutional" category to match the seed population encoding structure:

- **Before combination**: Separate `hh_gq_military` and `hh_gq_other_nonins` columns
- **After combination**: Military persons (1,684) combined into `hh_gq_other_nonins` (final total: 76,071)
- **File cleanup**: Intermediate `maz_marginals.csv` automatically removed, leaving only `maz_marginals_hhgq.csv`

**Processing Steps:**

1. Generate separate military and other noninstitutional GQ controls from Census P5 data
2. Validate each control category individually  
3. Combine military into other noninstitutional to match seed population structure
4. Create HHGQ-integrated files for PopulationSim consumption
5. Clean up intermediate files to maintain organized workflow

This ensures the control structure exactly matches the seed population GQ encoding while preserving the underlying Census data accuracy.

### Column Naming Quick Reference

| Geography Level | File | Key ID Column | Standard Name | Legacy Name |
|----------------|------|---------------|---------------|-------------|
| MAZ | `maz_marginals_hhgq.csv` | MAZ identifier | `MAZ` | `MAZ` |
| TAZ | `taz_marginals_hhgq.csv` | TAZ identifier | `TAZ` | `TAZ` |  
| County | `county_marginals.csv` | County identifier | `COUNTY` | N/A |
| Crosswalk | `geo_cross_walk_tm2_maz.csv` | MAZ identifier | `MAZ_NODE` | `MAZ` |
| Crosswalk | `geo_cross_walk_tm2_maz.csv` | TAZ identifier | `TAZ_NODE` | `TAZ` |

**Important**: 
- Control files (`*_marginals_hhgq.csv`) use `MAZ`/`TAZ` as geography identifiers
- Crosswalk files (`geo_cross_walk_tm2_maz.csv`) use `MAZ_NODE`/`TAZ_NODE` as geography identifiers
- PopulationSim config files (`controls.csv`) must use `MAZ`/`TAZ` to match the control file structure
- The system handles this mapping automatically during geographic aggregation operations

## Inputs

### Census Data Sources

- **ACS 2023 5-year estimates**: Tract and block group level demographic data
- **ACS 2023 1-year estimates**: County-level household totals for scaling targets
- **2020 Decennial Census data (DHC)**: Block-level household and group quarters counts
- **Geographic crosswalks**: MAZ-TAZ definitions and 2020-to-2010 Census block interpolation weights

### MAZ Control Data Source Details

**Source**: MAZ controls originate from **Santa Clara County VTA (Valley Transportation Authority)** and MTC's MAZ/TAZ geography system, which defines approximately 39,587 MAZs for the 9-county Bay Area.

**Geographic Foundation**:
- MAZ/TAZ system is built on **2010 Census block boundaries**
- MAZ definitions provided in `blocks_mazs_tazs.csv` (TM2 version 2.2+)
- Each MAZ is a union of one or more 2010 Census blocks

**Data Interpolation Process**:

1. **2020 Census Data Collection**: Download DHC (Demographic and Housing Characteristics) block-level counts from 2020 Census:
   - Table H1: Occupied housing units (households)
   - Table P5: Group quarters population by type

2. **Geographic Interpolation (2020→2010 blocks)**: 
   - Uses NHGIS (National Historical Geographic Information System) block-to-block crosswalk
   - Applies areal interpolation weights when 2020 block boundaries differ from 2010 blocks
   - Maintains population conservation (total 2020 counts = total interpolated counts)
   - Formula: `est_2010_block = sum(2020_block_value × interpolation_weight)` for all intersecting 2020 blocks

3. **Aggregation to MAZ**:
   - Sum interpolated 2010-geography blocks to MAZ using `blocks_mazs_tazs.csv` crosswalk
   - Direct aggregation (no further interpolation needed since MAZs are defined as unions of 2010 blocks)

4. **County Scaling**:
   - Scale MAZ totals to match ACS 2023 1-year county household targets
   - Ensures consistency between 2020 Census base + growth and current ACS estimates

**Specific Census Tables Used for MAZ Controls**:

| Control Variable | Census Table | Universe | Geographic Level |
|-----------------|--------------|----------|------------------|
| `num_hh` | 2020 DHC H1_002N | Occupied housing units | Block (interpolated to 2010 blocks) |
| `pers_gq_university` | 2020 DHC P5_008N | Persons in college/university GQ | Block (interpolated to 2010 blocks) |
| `pers_gq_noninstitutional` | 2020 DHC P5_009N + P5_011N + P5_012N | Persons in military + other noninstitutional GQ | Block (interpolated to 2010 blocks) |

**Why Interpolation is Necessary**:
- Census block boundaries changed between 2010 and 2020 Censuses
- TM2 MAZ/TAZ system was built on 2010 Census geography and cannot be easily remapped
- Interpolation allows use of latest 2020 Census data while maintaining compatibility with TM2 geography
- Areal interpolation assumes uniform population density within blocks (reasonable at small block scale)

### Configuration Files

- `unified_tm2_config.py`: File paths and execution settings
- `tm2_control_utils/config_census.py`: Control variable definitions and Census table specifications

## Outputs

### PopulationSim Input Files (Primary)

- `maz_marginals_hhgq.csv`: MAZ-level controls with integrated households and group quarters
- `taz_marginals_hhgq.csv`: TAZ-level controls with HHGQ integration  
- `county_marginals.csv`: County-level occupation controls

### Supporting Files

- `geo_cross_walk_tm2_maz.csv`: Geographic crosswalk with standardized MAZ_NODE/TAZ_NODE columns
- `maz_data.csv`, `maz_data_withDensity.csv`: Land use and density files for TM2
- `county_summary_2020_2023.csv`: County scaling factors and validation statistics
- `county_targets_2023.csv`: Target totals for validation

### File Processing Notes

- **Intermediate files**: `maz_marginals.csv` and `taz_marginals.csv` are generated during processing but automatically removed after HHGQ integration
- **Final structure**: PopulationSim uses only the `*_hhgq.csv` files which contain the integrated household+GQ controls
- **File naming**: All output files use the standardized `MAZ_NODE`/`TAZ_NODE` column naming convention

## How to Run

From the `bay_area` directory, run:

```sh
python create_baseyear_controls_23_tm2.py
```

This will generate all control and summary files in the configured output directory.

## Notes

- The enhanced crosswalk (`geo_cross_walk_tm2_block10.csv`) from the crosswalk step is required as input.
- If you update any Census data or crosswalks, you must re-run this step.
- For more details on configuration and file paths, see [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) and [HOW_TO_RUN.md](HOW_TO_RUN.md).

---

*Return to the [main documentation index](README.md) for other pipeline steps.*


