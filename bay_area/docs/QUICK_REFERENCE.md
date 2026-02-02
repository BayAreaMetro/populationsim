# TM2 PopulationSim Quick Reference Guide

## Overview
TM2 PopulationSim generates a synthetic population of 2,958,470 households and 7,563,557 persons for the San Francisco Bay Area, matched to Census controls at County, TAZ, and MAZ levels using 2023 5-Year ACS PUMS data.

## Quick Commands

### Run Complete Pipeline
```bash
cd bay_area
conda activate popsim
python tm2_pipeline.py full --force
```

**Runtime**: ~2-3 hours total
- PUMS processing: ~5-10 min
- Seed population: ~5 min
- Controls generation: ~15 min  
- PopulationSim synthesis: ~45-90 min
- Postprocessing: ~10 min
- Summary analysis: ~15-20 min

### Run Analysis Only
```bash
python run_all_summaries.py
```

**Outputs**: `output_2023/charts/` (10 scripts, core/visualization/validation)

### Check Status
```bash
python tm2_pipeline.py status
```

## Geographic Framework

### Counties (Sequential IDs 1-9)
```
1 = San Francisco      6 = Solano
2 = San Mateo          7 = Napa
3 = Santa Clara        8 = Sonoma
4 = Alameda            9 = Marin
5 = Contra Costa
```

**Important**: All control files and outputs use sequential 1-9 (NOT FIPS codes)

### Geographic Hierarchy
```
9 Counties
  → 62 PUMAs  
    → 5,117 TAZs
      → 41,434 MAZs (finest level)
```

## Control Variables

### County Level (5 variables)
- Occupation categories: management, professional, services, retail, manual/military

### TAZ Level (28 variables)
- Household totals (numhh, numhh_gq)
- Group quarters (hh_gq_university, hh_gq_noninstitutional)
- Household size (hh_size_1 through hh_size_6_plus)
- Workers (hh_wrks_0, hh_wrks_1, hh_wrks_2, hh_wrks_3_plus)
- Age groups (pers_age_00_19, pers_age_20_34, pers_age_35_64, pers_age_65_plus)
- Children (hh_kids_yes, hh_kids_no)
- Income (inc_lt_20k through inc_200k_plus, 8 bins)

### MAZ Level (4 variables)
- numhh_gq (total households + GQ)
- gq_type_univ (university GQ persons)
- gq_type_noninst (non-institutional GQ persons)
- Group quarters handled at person level

## Key Configuration Settings

### Convergence Parameters (`settings.yaml`)
```yaml
rel_tolerance: 0.2         # ±20% relative tolerance
abs_tolerance: 100.0       # ±100 absolute difference
integer_tolerance: 2.0     # ±2 for integerization
MAX_DELTA: 1.0e-8         # Weight change threshold
MAX_GAMMA: 1.0e-4         # Lagrange multiplier threshold
```

**Rationale**: Optimized for speed/quality balance. Tighter tolerances increase runtime to 16+ hours with minimal quality improvement.

### Algorithm Settings
```yaml
USE_SIMUL_INTEGERIZER: True
USE_CVXPY: False  # Uses CBC solver
GROUP_BY_INCIDENCE_SIGNATURE: False  # Memory optimization
max_expansion_factor: 50
```

## Output Files

### Primary Outputs
```
output_2023/populationsim_working_dir/output/
├── households_2023_tm2.csv      # 2.9M households, TM2 format
├── persons_2023_tm2.csv         # 7.6M persons, TM2 format
├── synthetic_households.csv     # Raw PopulationSim output
├── synthetic_persons.csv        # Raw PopulationSim output
└── final_summary_*.csv          # County/TAZ summaries
```

### Analysis Outputs
```
output_2023/charts/
├── core/                        # Analysis & comparisons
├── visualization/               # Static charts
├── validation/                  # Quality reports
└── interactive_taz/            # Interactive dashboards ⭐
    ├── interactive_taz_dashboard.html  # Main dashboard
    ├── index.html                      # Summary page
    └── taz_*.html (28 charts)
```

## Quality Metrics

### Expected Performance
- **numhh**: R² > 0.98 (primary control, excellent fit)
- **Income variables**: R² typically 0.85-0.95
- **Age variables**: R² typically 0.90-0.95  
- **Group quarters**: Lower R² acceptable (sparse data)

### Red Flags
- R² < 0.70 for major variables
- Large systematic bias in scatter plots
- Errors in data_validation_report.txt
- Missing or extreme outlier MAZs

## Common Tasks

### View Interactive Results
```bash
# Open in default browser
start output_2023/charts/interactive_taz/interactive_taz_dashboard.html
```

### Check Specific Variable
1. Open interactive dashboard
2. Use dropdown to select variable
3. Zoom into regions of interest
4. Hover for TAZ-specific details

### Debug Issues
```bash
# Check logs
Get-Content output_2023/populationsim_working_dir/output/populationsim.log -Tail 50

# Verify environment
python setup_environment.py

# Test Python import
python -c "import populationsim; print(populationsim.__file__)"
```

### Regenerate Specific Step
```bash
python tm2_pipeline.py controls --force    # Regenerate controls only
python tm2_pipeline.py postprocess --force # Rerun postprocessing
python tm2_pipeline.py analysis --force    # Rerun analysis only
```

## File Locations

### Configuration
- `tm2_config.py` - Central configuration
- `output_2023/populationsim_working_dir/configs/settings.yaml` - PopulationSim settings
- `environment_minimal.yml` - Python environment

### Documentation
- `docs/HOW_TO_RUN.md` - Detailed run instructions
- `docs/PROCESS_OVERVIEW.md` - Process flow and algorithms
- `docs/ANALYSIS.md` - Analysis framework guide
- `docs/TM2_FULL_REFERENCE.md` - Complete field reference
- `docs/RECENT_UPDATES.md` - Recent changes and fixes

### Scripts
- `tm2_pipeline.py` - Main pipeline controller
- `run_all_summaries.py` - Analysis runner
- `create_seed_population_tm2_refactored.py` - Seed generation
- `tm2_control_utils/controls.py` - Control generation
- `postprocess_recode.py` - TM2 formatting

## Troubleshooting

### Runtime Too Long (> 8 hours)
**Issue**: Convergence taking too long
**Solution**: Settings are already optimized (~2-3 hours). If much longer, check:
- Memory available (need 16GB+)
- No other heavy processes running
- Check logs for stuck iterations

### NaN Errors in Controls
**Issue**: Counties not matching between files
**Solution**: All control files use sequential COUNTY 1-9 (not FIPS). Regenerate controls:
```bash
python tm2_pipeline.py controls --force
```

### Missing Analysis Outputs
**Issue**: Charts not generated
**Solution**: 
```bash
# Install plotly if missing
pip install plotly

# Rerun analysis
python run_all_summaries.py
```

### Import Errors
**Issue**: Module not found errors
**Solution**:
```bash
# Verify environment
conda activate popsim
conda list

# Reinstall if needed
pip install populationsim activitysim
```

## Best Practices

1. **Always run analysis** after synthesis to validate results
2. **Check interactive dashboard** for detailed exploration
3. **Review data_validation_report.txt** for errors (should be zero)
4. **Save complete output directory** for reproducibility
5. **Document any manual interventions** in run notes

## Package Requirements

### Core
- Python 3.8.20
- populationsim
- activitysim >= 1.0, < 2.0
- pandas, numpy
- dask (required)

### Analysis  
- matplotlib, seaborn
- plotly (for interactive dashboards)

### Optional
- census (Census API access)
- geopandas (geographic operations)

## Performance Optimization

### Speed Up Synthesis
✅ **Already optimized**: Convergence settings balance speed/quality
❌ **Don't**: Make tolerances stricter (minimal quality gain, 3x slower)
✅ **Do**: Ensure 16GB+ RAM, close other applications

### Reduce Memory Usage
- GROUP_BY_INCIDENCE_SIGNATURE: False (already set)
- Run on machine with adequate RAM
- Close browser tabs and other memory-intensive apps

## Support and Resources

### Check First
1. Pipeline status: `python tm2_pipeline.py status`
2. Log files: `output_2023/populationsim_working_dir/output/populationsim.log`
3. Data validation: `output_2023/charts/validation/data_validation_report.txt`

### Documentation
- Start with: `docs/HOW_TO_RUN.md`
- Process details: `docs/PROCESS_OVERVIEW.md`
- Field reference: `docs/TM2_FULL_REFERENCE.md`
- Analysis guide: `docs/ANALYSIS.md`

### Common Questions

**Q: How long should synthesis take?**
A: ~2-3 hours for full Bay Area (2.96M households)

**Q: What if R² is low for a variable?**
A: Check control file has valid data, variable is in settings, and seed has variation

**Q: Can I run just one county?**
A: Not easily - system is designed for full region due to PUMA-County interactions

**Q: How do I know if results are good?**
A: Check interactive dashboard (R² > 0.80), data validation report (zero errors), and county totals match

---

Last Updated: January 29, 2026
Version: TM2 Branch (optimized convergence, comprehensive analysis)
