# Bay Area PopulationSim TM2 Pipeline - Core Files Documentation

## CORE PIPELINE FILES (DO NOT DELETE)

### 1. Main Workflow Scripts
- `tm2_workflow_orchestrator.py` - **PRIMARY WORKFLOW** - Main 6-step orchestration script
- `run_populationsim_synthesis.py` - **STEP 4 RUNNER** - PopulationSim synthesis execution
- `config_tm2.py` - Configuration settings and file paths
- `tm2_config_refactored.py` - Alternative configuration (backup)

### 2. Essential Utility Modules
- `tm2_control_utils/` - **CRITICAL DIRECTORY** - Core utility functions
  - Contains data processing, crosswalk, and validation functions

### 3. Data Processing Scripts (Core Pipeline Steps)
- `build_crosswalk_focused.py` - Step 0: PUMA/MAZ/TAZ crosswalk creation
- `create_seed_population_tm2_refactored.py` - Step 1: Seed population generation  
- `pums_downloader.py` - **DEPENDENCY** - Required by seed population creation
- `create_baseyear_controls_23_tm2.py` - Step 2: Control totals generation
- `add_hhgq_combined_controls.py` - Step 3: Group quarters integration
- `postprocess_recode.py` - Step 5: Post-processing and recoding
- `prepare_tableau_data.py` - Step 6: Tableau visualization preparation

### 4. Essential Data Directories
- `hh_gq/` - **CRITICAL** - Contains PopulationSim configuration files
  - `configs_TM2/` - TM2-specific configuration
- `output_2023/` - **ACTIVE OUTPUT** - Current run outputs
- `tm2_control_utils/` - **CRITICAL** - Utility functions

### 5. Geographic and Control Data
- `geo_cross_walk_tm2_updated.csv` - Geographic crosswalk (if exists)
- Control files in `output_2023/` directory

## PIPELINE EXECUTION FLOW
1. **Step 0**: Crosswalk Creation (`build_crosswalk_focused.py`)
2. **Step 1**: Seed Population (`create_seed_population_tm2_refactored.py`) 
3. **Step 2**: Control Generation (`create_baseyear_controls_23_tm2.py`)
4. **Step 3**: Group Quarters (`add_hhgq_combined_controls.py`)
5. **Step 4**: PopulationSim Synthesis (external PopulationSim tool)
6. **Step 5**: Post-processing (`postprocess_recode.py`)
7. **Step 6**: Tableau Prep (`prepare_tableau_data.py`)

## FORCE FLAGS
- CROSSWALK=False/True - Force regenerate crosswalk
- SEED=False/True - Force regenerate seed population  
- CONTROLS=False/True - Force regenerate controls
- HHGQ=False/True - Force regenerate group quarters
- POPSIM=True/False - Force run PopulationSim synthesis
- POST=True/False - Force run post-processing
- TABLEAU=False/True - Force generate Tableau files

## KEY DEPENDENCIES
- Python environment: popsim conda environment
- PopulationSim tool (external)
- Geographic crosswalk data
- Census PUMS data
- Control total specifications
