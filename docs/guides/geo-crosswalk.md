# Crosswalk Step: Creating the TM2 Geographic Crosswalk

**⚠️ IMPORTANT: Crosswalk creation has been moved to the tm2py-utils repository.**

This step prepares the essential geographic crosswalk files used throughout the Bay Area PopulationSim pipeline. The crosswalks map MAZs, TAZs, counties, and other geographies, enabling consistent aggregation and disaggregation of data.

## What This Step Does

- **`standalone_tm2_crosswalk_creator.py`** (located in tm2py-utils repository):  
  A unified standalone script that generates both basic and enhanced crosswalks without dependencies on this repository's configuration files.
  - Creates the initial crosswalk between MAZs, TAZs, counties, and PUMAs using source shapefiles
  - Enhances the crosswalk by adding block/block group mappings for census data integration
  - Performs data validation and quality checks
  - **The enhanced crosswalk (`geo_cross_walk_tm2_block10.csv`) is a required input for the control generation step.**

## Script Location

The crosswalk creator script is now located in:
```
C:\GitHub\tm2py-utils\tm2py_utils\inputs\maz_taz\standalone_tm2_crosswalk_creator.py
```

See the README_crosswalk_creator.md file in that directory for complete usage instructions.

## Pipeline Integration

### Expected File Locations

The PopulationSim pipeline expects crosswalk files to be located in:
```
populationsim/bay_area/output_2023/populationsim_working_dir/data/
```

### Required Files
- `geo_cross_walk_tm2_maz.csv` (basic crosswalk)
- `geo_cross_walk_tm2_block10.csv` (enhanced crosswalk)

### Workflow
1. Run the standalone crosswalk creator script from tm2py-utils repository
2. Copy the generated files to the pipeline data directory, or use `--pipeline-mode` for automatic placement
3. Proceed with control generation and population synthesis

## Migration Notice

**Previous scripts deprecated:**
- ~~`create_tm2_crosswalk.py`~~ (functionality moved to standalone script)
- ~~`build_complete_crosswalk.py`~~ (functionality moved to standalone script)
- ~~`standalone_tm2_crosswalk_creator.py`~~ (moved to tm2py-utils repository)

**New unified approach:**
- Single standalone script handles both basic and enhanced crosswalk creation
- No dependencies on tm2_control_utils or unified_tm2_config
- Located in tm2py-utils repository for better organization

## Inputs

- MAZ/TAZ shapefiles with spatial geometries
- PUMA shapefile (US Census TIGER/Line)
- California counties shapefile
- Blocks CSV file with MAZ assignments
- (All paths specified as command-line arguments)

## Outputs

- `geo_cross_walk_tm2_maz.csv`: The basic crosswalk file (MAZ-TAZ-PUMA-COUNTY)
- `geo_cross_walk_tm2_block10.csv`: The enhanced crosswalk with block/block group mappings
- Summary validation files

## How to Run

**New standalone approach:**

```sh
python standalone_tm2_crosswalk_creator.py \
  --maz-shapefile /path/to/maz_shapefile.shp \
  --puma-shapefile /path/to/puma_shapefile.shp \
  --county-shapefile /path/to/county_shapefile.shp \
  --blocks-file /path/to/blocks.csv \
  --output-dir /path/to/output/directory \
  --verbose
```

**Example with typical paths:**

```sh
python standalone_tm2_crosswalk_creator.py \
  --maz-shapefile "C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/TM2_MAZ_TAZ_Bounds/TM2_MAZ_TAZ_Bounds.shp" \
  --puma-shapefile "C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/tl_2020_06_puma10.shp" \
  --county-shapefile "C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/california_counties.shp" \
  --blocks-file "C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/tm2py_mazs_blocks_23.csv" \
  --output-dir "output_2023/populationsim_working_dir/data" \
  --verbose
```

## Notes

- **Migration Required**: Update your workflow to use the new standalone script
- The enhanced crosswalk is a critical input for generating controls in `create_baseyear_controls.py`
- If you update any source geography files, you must re-run this step
- The standalone script is designed to be self-contained and portable
- For more details on configuration and file paths, see [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) and [HOW_TO_RUN.md](HOW_TO_RUN.md)

---

*Return to the [main documentation index](README.md) for other pipeline steps.*

---

*Return to the [main documentation index](README.md) for other pipeline steps.*

