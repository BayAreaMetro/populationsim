# Analysis and Utility Files

This folder contains analysis, debugging, validation, and utility files that are not part of the core TM2 PopulationSim workflow.

## 🎉 NEW: Comprehensive Analysis Framework (January 2026)

Run all analysis scripts with a single command:
```bash
python run_all_summaries.py
```

This executes 10 analysis scripts organized into three categories:

### Core Analysis Scripts
- `MAZ_hh_comparison.py` - Compare MAZ household results vs controls
- `analyze_full_dataset.py` - Full dataset analysis and validation
- `compare_controls_vs_results_by_taz.py` - TAZ-level control comparison
- `analyze_syn_pop_model.py` - Synthetic population cross-tabulations

### Visualization Scripts
- `analyze_taz_controls_vs_results.py` - TAZ control charts
- `analyze_county_results.py` - County-level summary charts
- `create_interactive_taz_analysis.py` - Interactive Plotly dashboards (28 charts)

### Validation Scripts
- `maz_household_summary.py` - MAZ household validation
- `compare_synthetic_populations.py` - Compare synthetic populations
- `data_validation.py` - General data quality checks

**Output Location**: `output_2023/charts/`

**See**: `docs/RECENT_UPDATES.md` for details on the analysis framework

---

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


