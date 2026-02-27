# TM2 PopulationSim Documentation

## Quick Start
**New to TM2 PopulationSim?** Start here:
1. 📖 [Quick Reference Guide](QUICK_REFERENCE.md) - Commands, settings, troubleshooting
2. 🚀 [How to Run](HOW_TO_RUN.md) - Step-by-step execution guide
3. 📊 [Analysis Guide](ANALYSIS.md) - Understanding and validating results

## Documentation Index

### Getting Started
- **[Quick Reference](QUICK_REFERENCE.md)** - One-page reference for common tasks
- **[How to Run](HOW_TO_RUN.md)** - Complete pipeline execution guide
- **[Environment Setup](ENVIRONMENT_SETUP.md)** - Installing and configuring environment
- **[Setup Instructions](SETUP_INSTRUCTIONS.md)** - Detailed setup walkthrough

### Process Documentation
- **[Process Overview](PROCESS_OVERVIEW.md)** - High-level workflow and algorithms
- **[Detailed Synthesis Guide](DETAILED_SYNTHESIS_GUIDE.md)** - In-depth synthesis documentation
- **[Control Generation](CONTROL_GENERATION.md)** - How controls are created
- **[Seed Population](SEED_POPULATION.md)** - PUMS data processing
- **[Geographic Crosswalk](GEO_CROSSWALK.md)** - MAZ-TAZ-PUMA-County mapping

### Analysis and Validation
- **[Analysis Guide](ANALYSIS.md)** - Comprehensive analysis framework (10 scripts)
- **[TM2 Output Summaries](TM2_OUTPUT_SUMMARIES.md)** - Output file reference
- **[Recent Updates](RECENT_UPDATES.md)** - Latest improvements and fixes

### Technical Reference
- **[TM2 Full Reference](TM2_FULL_REFERENCE.md)** - Complete field documentation
- **[TM2 Input Fields](TM2_INPUT_FIELDS.md)** - Input data specifications
- **[TM2 Output Summaries TAZ](TM2_OUTPUT_SUMMARIES_TAZ.md)** - TAZ-level outputs

### Specialized Guides
- **[Income Documentation](README_INCOME.md)** - Income field handling
- **[Group Quarters](group_quarters.md)** - Group quarters methodology
- **[File Flow](FILE_FLOW.md)** - Data flow through pipeline

## Current Status (February 2026)

### ✅ Fully Operational
- **Scale**: 2,958,470 households, 7,563,557 persons
- **Geography**: 9 counties, 62 PUMAs, 5,117 TAZs, 41,434 MAZs
- **Data Source**: 2023 5-Year ACS PUMS
- **Runtime**: ~2-3 hours for full synthesis
- **Quality**: All controls within ±20% tolerance
- **Analysis**: 10 automated validation scripts

### Recent Improvements
- County ID system: Sequential 1-9 (not FIPS)
- Optimized convergence: 2-3 hours (was 6+ hours)
- Interactive dashboards: 28 Plotly visualizations
- Comprehensive analysis: Core, validation, visualization scripts

## Key Concepts

### Geographic Hierarchy
```
9 Counties (1-9 sequential)
  → 62 PUMAs
    → 5,117 TAZs
      → 41,434 MAZs
```

### Control Levels
- **County**: 5 occupation variables
- **TAZ**: 28 demographic/household variables
- **MAZ**: 4 household total variables

### Process Flow
```
PUMS Data → Seed Population → Controls → PopulationSim → Postprocess → Analysis
```

## Quick Commands

```bash
# Run everything
python tm2_pipeline.py full --force

# Run analysis only
python run_all_summaries.py

# Check status
python tm2_pipeline.py status

# View interactive results
start output_2023/charts/interactive_taz/interactive_taz_dashboard.html
```

## File Organization

```
bay_area/
├── tm2_pipeline.py               # Main controller
├── run_all_summaries.py          # Analysis runner
├── tm2_config.py                 # Central configuration
├── docs/                         # This documentation
│   ├── QUICK_REFERENCE.md       ⭐ Start here
│   ├── HOW_TO_RUN.md            
│   ├── ANALYSIS.md              
│   └── ...
├── output_2023/
│   ├── populationsim_working_dir/
│   │   ├── data/                # Inputs
│   │   ├── configs/             # Settings
│   │   └── output/              # Results
│   └── charts/                  # Analysis outputs
│       ├── core/
│       ├── visualization/
│       ├── validation/
│       └── interactive_taz/     ⭐ Interactive dashboards
└── analysis/                    # Analysis scripts
```

## Troubleshooting

### Common Issues
- **NaN errors**: Check COUNTY IDs are 1-9 (not FIPS)
- **Long runtime**: Normal is ~2-3 hours; check memory/CPU
- **Missing charts**: Install plotly (`pip install plotly`)
- **Import errors**: Activate environment (`conda activate popsim`)

### Getting Help
1. Check [Quick Reference](QUICK_REFERENCE.md) troubleshooting section
2. Review log: `output_2023/populationsim_working_dir/output/populationsim.log`
3. Verify setup: `python setup_environment.py`
4. Check validation: `output_2023/charts/validation/data_validation_report.txt`

## Documentation Conventions

- 📖 = General documentation
- 🚀 = How-to guides
- 📊 = Analysis and validation
- ⭐ = Recommended starting point
- ✅ = Confirmed working
- ❌ = Known limitation

## Version Information

**Current Branch**: tm2  
**Last Updated**: January 29, 2026  
**PopulationSim Version**: 0.5.1  
**Python Version**: 3.8.20  
**Status**: Production-ready

---

For the most current information, always check [RECENT_UPDATES.md](RECENT_UPDATES.md)
