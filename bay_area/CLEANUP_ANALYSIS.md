# Bay Area PopulationSim File Cleanup Analysis

## Core Workflow Files (DO NOT DELETE)

Based on `unified_tm2_workflow.py` and `unified_tm2_config.py`, these files are ESSENTIAL:

### Primary Workflow Files
1. **unified_tm2_workflow.py** - Main workflow orchestrator
2. **unified_tm2_config.py** - Single source of truth for all configuration
3. **build_crosswalk_focused.py** - Step 0: Geographic crosswalk creation
4. **create_seed_population_tm2_refactored.py** - Step 1: Seed population generation
5. **create_baseyear_controls_23_tm2.py** - Step 2: Control generation
6. **add_hhgq_combined_controls.py** - Step 3: Group quarters integration
7. **run_populationsim_synthesis.py** - Step 4: PopulationSim synthesis
8. **postprocess_recode.py** - Step 5: Post-processing
9. **prepare_tableau_data.py** - Step 6: Tableau preparation

### Supporting Files
10. **cpi_conversion.py** - CPI conversion utility (referenced in config)

## Files Marked as DEPRECATED/OBSOLETE (SAFE TO DELETE)

### Explicitly Deprecated
1. **config_tm2_deprecated.py** - Marked as deprecated in the file itself
2. **config_tm2.py** - Old config system (replaced by unified_tm2_config.py)
3. **tm2_workflow_orchestrator.py** - Old workflow orchestrator
4. **run_populationsim_tm2.py** - Old TM2 runner

### Migration/Transition Files
5. **migrate_config.py** - One-time migration script (no longer needed)

### Duplicate/Alternative Crosswalk Files
6. **build_crosswalk_focused_clean.py** - Alternative version (workflow uses focused.py)
7. **build_crosswalk_unified_example.py** - Example/test version

### Modification/Patch Files (Project-specific, could be archived)
8. **modify_installed_populationsim.py** - Modifies installed PopulationSim
9. **patch_meta_control_factoring.py** - One-time patch

## Analysis/Debug Files (COULD BE MOVED TO ANALYSIS FOLDER)

### Data Analysis Files
1. **analyze_puma_data_mismatch.py**
2. **analyze_zero_weight_zones.py**
3. **data_validation.py**
4. **detailed_data_validation.py**
5. **visualize_taz_puma_mapping.py**
6. **cleanup_audit.py**

### Checking/Validation Files
7. **check_category_mapping.py**
8. **check_county_codes.py**
9. **check_crosswalk_stats.py**
10. **check_puma_codes.py**
11. **check_puma_county_occupations.py**
12. **check_seed_occupations.py**
13. **quick_occupation_check.py**

### Debug Files
14. **debug_unicode.py**
15. **find_impossible_combinations.py**
16. **find_zero_controls.py**

### Utility/Fix Files
17. **fix_county_codes.py**
18. **fix_maz_num_hh.py**
19. **fix_occupation_controls.py**
20. **fix_puma_mismatch.py**

### Test Files
21. **minimal_test.py**

### One-off Scripts
22. **add_meta_control_diagnostics.py**
23. **pums_downloader.py**

## Recommendation Summary

### DELETE (9 files):
- config_tm2_deprecated.py
- config_tm2.py  
- tm2_workflow_orchestrator.py
- run_populationsim_tm2.py
- migrate_config.py
- build_crosswalk_focused_clean.py
- build_crosswalk_unified_example.py
- modify_installed_populationsim.py
- patch_meta_control_factoring.py

### MOVE TO ANALYSIS FOLDER (23 files):
Create `bay_area/analysis/` and move all the analysis, check, debug, fix, and test files there.

### KEEP IN ROOT (10 files):
- unified_tm2_workflow.py
- unified_tm2_config.py
- build_crosswalk_focused.py
- create_seed_population_tm2_refactored.py
- create_baseyear_controls_23_tm2.py
- add_hhgq_combined_controls.py
- run_populationsim_synthesis.py
- postprocess_recode.py
- prepare_tableau_data.py
- cpi_conversion.py

This will leave a clean bay_area directory with only core workflow files, making it much easier to understand and maintain.
