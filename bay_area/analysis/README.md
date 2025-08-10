# Analysis and Utility Files

This folder contains analysis, debugging, validation, and utility files that are not part of the core TM2 PopulationSim workflow.

## Data Analysis Files
- `analyze_puma_data_mismatch.py` - Analyzes mismatches between PUMA data
- `analyze_zero_weight_zones.py` - Analyzes zones with zero weights
- `data_validation.py` - General data validation scripts
- `detailed_data_validation.py` - Detailed data validation analysis
- `visualize_taz_puma_mapping.py` - Creates visualizations of TAZ-PUMA mapping
- `cleanup_audit.py` - Audits cleanup operations

## Checking/Validation Files
- `check_category_mapping.py` - Validates category mappings
- `check_county_codes.py` - Validates county code consistency
- `check_crosswalk_stats.py` - Checks geographic crosswalk statistics
- `check_puma_codes.py` - Validates PUMA codes
- `check_puma_county_occupations.py` - Checks PUMA-county occupation consistency
- `check_seed_occupations.py` - Validates seed population occupations
- `quick_occupation_check.py` - Quick occupation data validation

## Debug Files
- `debug_unicode.py` - Debugs Unicode encoding issues
- `find_impossible_combinations.py` - Finds impossible data combinations
- `find_zero_controls.py` - Finds controls with zero values

## Fix/Utility Files
- `fix_county_codes.py` - Fixes county code issues
- `fix_maz_num_hh.py` - Fixes MAZ household number issues
- `fix_occupation_controls.py` - Fixes occupation control data
- `fix_puma_mismatch.py` - Fixes PUMA mismatch issues

## Test Files
- `minimal_test.py` - Minimal test scripts

## One-off/Special Purpose Scripts
- `add_meta_control_diagnostics.py` - Adds diagnostic information to meta controls
- `pums_downloader.py` - Downloads PUMS data

## Usage Note
These files are not part of the main TM2 workflow (`unified_tm2_workflow.py`) but may be useful for:
- Debugging data issues
- Validating input/output data
- One-time data fixes
- Analysis and reporting

Most of these scripts can be run independently when needed for analysis or debugging purposes.
