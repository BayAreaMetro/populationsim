# Bay Area PopulationSim TM2 Workflow - Clean Directory Structure

## Current Status: CLEANED UP ✅

This directory now contains only the **core workflow files** needed for the TM2 PopulationSim process.

## Core Workflow Files (10 files)

### Primary Workflow
1. **unified_tm2_workflow.py** - Main workflow orchestrator
2. **unified_tm2_config.py** - Single source of truth for all configuration

### Step-by-Step Workflow Scripts
3. **build_crosswalk_focused.py** - Step 0: Geographic crosswalk creation
4. **create_seed_population_tm2_refactored.py** - Step 1: Seed population generation  
5. **create_baseyear_controls_23_tm2.py** - Step 2: Control generation
6. **add_hhgq_combined_controls.py** - Step 3: Group quarters integration
7. **run_populationsim_synthesis.py** - Step 4: PopulationSim synthesis
8. **postprocess_recode.py** - Step 5: Post-processing
9. **prepare_tableau_data.py** - Step 6: Tableau preparation

### Supporting Utilities
10. **cpi_conversion.py** - CPI conversion utility

## Cleanup Actions Completed

### Files Moved to `/analysis/` (23 files)
All analysis, debugging, validation, and utility files have been moved to the `analysis/` subdirectory:
- Data analysis scripts (5 files)
- Checking/validation scripts (8 files) 
- Debug utilities (3 files)
- Fix/utility scripts (4 files)
- Test files (1 file)
- One-off scripts (2 files)

### Files Removed (Previously Deprecated)
- Old configuration files
- Old workflow orchestrators
- Duplicate/alternative implementations
- Migration scripts (no longer needed)

## Directory Structure
```
bay_area/
├── analysis/                    # Analysis and utility files
│   ├── README.md               # Documentation of analysis files
│   └── *.py                    # 23 analysis/utility scripts
├── hh_gq/                      # Group quarters data and configs
├── output_2023/                # Main output directory
├── scripts/                    # Additional utility scripts
├── tm2_control_utils/          # Control generation utilities
├── unified_tm2_workflow.py     # 🔥 MAIN WORKFLOW
├── unified_tm2_config.py       # 🔥 MAIN CONFIG
└── [8 other core scripts]      # Core workflow steps
```

## How to Run the Workflow

```bash
# Run the complete workflow
python unified_tm2_workflow.py

# Run from a specific step (e.g., start from controls)
python unified_tm2_workflow.py --start_step 2

# Force regeneration of all files
python unified_tm2_workflow.py --force_all_steps
```

## Benefits of Cleanup

1. **Clear Structure**: Only essential files visible in main directory
2. **Easy Maintenance**: No confusion about which files are current
3. **Better Understanding**: New users can quickly identify core workflow
4. **Organized Analysis**: All debugging/analysis tools in dedicated folder
5. **Future-Proof**: Clean foundation for future development

The workflow is now much easier to understand and maintain! 🎉
