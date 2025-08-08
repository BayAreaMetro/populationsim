# Files Outside Core TM2 Pipeline - Candidates for Removal

## ACCESSIBILITY FILES (Non-Core)
- `accessibilities_dummy_full_households.csv` - Dummy accessibility data
- `accessibilities_dummy_full_indivTours.csv` - Dummy tour data
- `accessibilities_dummy_full_model_households.csv` - Model household accessibility
- `accessibilities_dummy_full_model_persons.csv` - Model person accessibility  
- `accessibilities_dummy_full_persons.csv` - Person accessibility data

## ARCHIVE/LEGACY BATCH FILES
- `archive_populationsim.bat` - Windows batch archive script
- `delete_archived.bat` - Windows batch delete script
- `run_allyearsPBA50.bat` - Legacy PBA50 batch file
- `run_populationsim.bat` - Legacy general batch file
- `run_populationsim_BAUS.bat` - BAUS-specific batch file
- `run_populationsim_PBA50_IP.bat` - PBA50 IP batch file

## DEBUG/DEVELOPMENT FILES
- `debug_seed_creation.py` - Debugging script
- `debug_unicode.py` - Unicode debugging (our recent fix)
- `minimal_test.py` - Test script
- `test_output.txt` - Test output file

## ANALYSIS/DIAGNOSTIC SCRIPTS (Non-Essential)
- `analyze_crosswalk.py` - Crosswalk analysis
- `analyze_puma_distribution.py` - PUMA distribution analysis
- `check_counties.py` - County validation
- `check_crosswalk_pumas.py` - PUMA crosswalk check
- `check_crosswalk_stats.py` - Crosswalk statistics
- `cleanup_audit.py` - Audit cleanup
- `data_validation.py` - General data validation
- `detailed_data_validation.py` - Detailed validation
- `diagnose_county.py` - County diagnostics
- `validate_counties.py` - County validation
- `validate_crosswalk.py` - Crosswalk validation
- `visualize_taz_puma_mapping.py` - Visualization script

## UTILITY/HELPER SCRIPTS (Mixed)
### ⚠️ KEEP - Used by Core Pipeline:
- `pums_downloader.py` - **REQUIRED** by create_seed_population_tm2_refactored.py

### ❌ Safe to Remove:
- `add_county_to_crosswalk.py` - County addition utility
- `cpi_conversion.py` - CPI conversion utility
- `create_density_metrics_only.py` - Density metrics only
- `direct_maz_scaling.py` - MAZ scaling utility
- `download_puma_shapefiles.py` - PUMA shapefile downloader
- `fix_county_mapping.py` - County mapping fix
- `fix_puma_format.py` - PUMA format fix
- `launch_popsim.py` - Alternative launch script
- `prepare_tableau_csv.py` - CSV preparation (vs prepare_tableau_data.py)
- `process_ca_pums.py` - CA PUMS processing
- `process_pums_efficient.py` - Efficient PUMS processing
- `quick_status.py` - Status check utility
- `run_seed_creation_refactored.py` - Alternative seed creation

## R/PROJECT FILES
- `bay_area.Rproj` - R project file
- `quickJoinFixer.R` - R script for joins

## EXAMPLE/REFERENCE DATA
- `census_to_controls_Alameda_example.xlsx` - Alameda example
- `example_controls_2015/` - 2015 example controls directory
- `updated_bay_area_pumas.txt` - PUMA reference list

## OTHER/MISC
- `validation.twb` - Tableau workbook
- `popsyn3_mysql_table_export/` - PopSyn3 MySQL exports
- `scripts/` - General scripts directory
- `__pycache__/` - Python cache (auto-generated)

## LOG FILES (Generated)
- `create_baseyear_controls_2023.log` - Recent log file
- Various other .log files

## RECOMMENDATION
The files above are likely safe to remove as they are:
1. Debugging/development tools
2. Legacy batch files
3. Analysis scripts not part of core workflow  
4. Alternative/backup implementations
5. Example/reference data
6. Generated cache/log files

**CAUTION**: Before deleting, verify that none of these are imported by core scripts!
