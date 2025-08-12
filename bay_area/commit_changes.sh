# Git commit to track our changes
git add -A
git commit -m "Implement 1-9 county system and fix GQ controls

Changes:
- Move FIPS-to-sequential mapping from tm2_pipeline.py to unified_tm2_config.py
- Add get_fips_to_sequential_mapping() method to config
- Fix GQ control expressions in controls.csv 
- Update settings.yaml for 1-9 county summaries
- Add portable environment setup scripts

This ensures the TM2 pipeline works consistently across machines."
