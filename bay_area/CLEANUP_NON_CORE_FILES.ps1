# Safe File Removal Script for TM2 Pipeline Cleanup
# Review this list before executing any deletions!

# ACCESSIBILITY FILES (Safe to remove - dummy data)
Remove-Item "accessibilities_dummy_full_households.csv" -ErrorAction SilentlyContinue
Remove-Item "accessibilities_dummy_full_indivTours.csv" -ErrorAction SilentlyContinue  
Remove-Item "accessibilities_dummy_full_model_households.csv" -ErrorAction SilentlyContinue
Remove-Item "accessibilities_dummy_full_model_persons.csv" -ErrorAction SilentlyContinue
Remove-Item "accessibilities_dummy_full_persons.csv" -ErrorAction SilentlyContinue

# LEGACY BATCH FILES (Safe to remove - we use Python now)
Remove-Item "archive_populationsim.bat" -ErrorAction SilentlyContinue
Remove-Item "delete_archived.bat" -ErrorAction SilentlyContinue
Remove-Item "run_allyearsPBA50.bat" -ErrorAction SilentlyContinue
Remove-Item "run_populationsim.bat" -ErrorAction SilentlyContinue  
Remove-Item "run_populationsim_BAUS.bat" -ErrorAction SilentlyContinue
Remove-Item "run_populationsim_PBA50_IP.bat" -ErrorAction SilentlyContinue

# DEBUG/TEST FILES (Safe to remove - development only)
Remove-Item "debug_seed_creation.py" -ErrorAction SilentlyContinue
Remove-Item "debug_unicode.py" -ErrorAction SilentlyContinue
Remove-Item "minimal_test.py" -ErrorAction SilentlyContinue
Remove-Item "test_output.txt" -ErrorAction SilentlyContinue

# ANALYSIS SCRIPTS (Safe to remove - not part of core workflow)
Remove-Item "analyze_crosswalk.py" -ErrorAction SilentlyContinue
Remove-Item "analyze_puma_distribution.py" -ErrorAction SilentlyContinue
Remove-Item "check_counties.py" -ErrorAction SilentlyContinue
Remove-Item "check_crosswalk_pumas.py" -ErrorAction SilentlyContinue
Remove-Item "check_crosswalk_stats.py" -ErrorAction SilentlyContinue
Remove-Item "cleanup_audit.py" -ErrorAction SilentlyContinue
Remove-Item "data_validation.py" -ErrorAction SilentlyContinue
Remove-Item "detailed_data_validation.py" -ErrorAction SilentlyContinue
Remove-Item "diagnose_county.py" -ErrorAction SilentlyContinue
Remove-Item "validate_counties.py" -ErrorAction SilentlyContinue
Remove-Item "validate_crosswalk.py" -ErrorAction SilentlyContinue
Remove-Item "visualize_taz_puma_mapping.py" -ErrorAction SilentlyContinue

# UTILITY SCRIPTS (Safe to remove - not used by core pipeline)
Remove-Item "add_county_to_crosswalk.py" -ErrorAction SilentlyContinue
Remove-Item "cpi_conversion.py" -ErrorAction SilentlyContinue
Remove-Item "create_density_metrics_only.py" -ErrorAction SilentlyContinue
Remove-Item "direct_maz_scaling.py" -ErrorAction SilentlyContinue
Remove-Item "download_puma_shapefiles.py" -ErrorAction SilentlyContinue
Remove-Item "fix_county_mapping.py" -ErrorAction SilentlyContinue
Remove-Item "fix_puma_format.py" -ErrorAction SilentlyContinue
Remove-Item "launch_popsim.py" -ErrorAction SilentlyContinue
Remove-Item "prepare_tableau_csv.py" -ErrorAction SilentlyContinue
Remove-Item "process_ca_pums.py" -ErrorAction SilentlyContinue
Remove-Item "process_pums_efficient.py" -ErrorAction SilentlyContinue
Remove-Item "quick_status.py" -ErrorAction SilentlyContinue
Remove-Item "run_seed_creation_refactored.py" -ErrorAction SilentlyContinue

# R/PROJECT FILES (Safe to remove if not using R)
Remove-Item "bay_area.Rproj" -ErrorAction SilentlyContinue
Remove-Item "quickJoinFixer.R" -ErrorAction SilentlyContinue

# EXAMPLE/REFERENCE DATA (Safe to remove - examples only)
Remove-Item "census_to_controls_Alameda_example.xlsx" -ErrorAction SilentlyContinue
Remove-Item "updated_bay_area_pumas.txt" -ErrorAction SilentlyContinue
Remove-Item -Recurse "example_controls_2015/" -ErrorAction SilentlyContinue

# TABLEAU FILE (Safe to remove if not using this specific workbook)
Remove-Item "validation.twb" -ErrorAction SilentlyContinue

# LEGACY EXPORTS (Safe to remove - old PopSyn3 data)
Remove-Item -Recurse "popsyn3_mysql_table_export/" -ErrorAction SilentlyContinue

# PYTHON CACHE (Safe to remove - auto-regenerated)
Remove-Item -Recurse "__pycache__/" -ErrorAction SilentlyContinue

# LOG FILES (Generated files - safe to remove)
Remove-Item "create_baseyear_controls_2023.log" -ErrorAction SilentlyContinue

Write-Host "File cleanup completed! Check the workspace for remaining files."
Write-Host "Core pipeline files should remain intact."
