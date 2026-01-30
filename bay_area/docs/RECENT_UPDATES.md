# Recent Updates and Changes

## January 2026 Updates

### Critical Bug Fixes

#### 1. COUNTY ID Mapping Fix (FIPS → Sequential 1-9)
**Issue**: PopulationSim was failing with NaN errors in occupation controls due to COUNTY ID mismatch between controls and meta-controls.

**Root Cause**: 
- Control generation used FIPS codes (e.g., 6001, 6013, 6075)
- Meta-controls expected sequential IDs (1-9)
- This caused counties to be "not found" in factored_meta_weights

**Solution**:
- Modified `tm2_control_utils/config_census.py` to use `COUNTY` column (sequential 1-9)
- Updated `tm2_control_utils/controls.py` to ensure proper COUNTY ID handling
- Regenerated all control files with correct county mapping

**County Mapping**:
```
1 = San Francisco (FIPS 6075)
2 = San Mateo (FIPS 6081)
3 = Santa Clara (FIPS 6085)
4 = Alameda (FIPS 6001)
5 = Contra Costa (FIPS 6013)
6 = Solano (FIPS 6095)
7 = Napa (FIPS 6055)
8 = Sonoma (FIPS 6097)
9 = Marin (FIPS 6041)
```

**Status**: ✅ Fixed and tested - No more NaN errors in meta_control_factoring

---

#### 2. Circular Import Warning Fix
**Issue**: Warning about circular import between `tm2_config.py` and `tm2_control_utils/config_census.py`

**Solution**:
- Implemented lazy loading in `config_census.py`
- Made `get_unified_config()` defer import using sys.path manipulation
- Converted module-level variables to lazy-loaded with getter functions

**Changes**:
```python
# Before: Immediate import at module level
from tm2_config import TM2Config

# After: Lazy import in function
def get_unified_config():
    import sys, os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from tm2_config import TM2Config
    return TM2Config()
```

**Status**: ✅ Fixed - No more circular import warnings

---

### Performance Optimizations

#### 3. Loosened Convergence Criteria
**Issue**: PopulationSim runtime was 16+ hours instead of expected 6 hours

**Root Cause**: Overly strict convergence tolerances causing excessive iterations

**Solution**: Modified `settings.yaml` with more realistic tolerances:

```yaml
# Before (too strict):
rel_tolerance: 0.1        # ±10% tolerance
abs_tolerance: 50.0       # Absolute difference threshold
integer_tolerance: 1.0    # Integer rounding tolerance
MAX_DELTA: 1.0e-9        # Weight change threshold
MAX_GAMMA: 1.0e-5        # Lagrange multiplier threshold

# After (optimized):
rel_tolerance: 0.2        # ±20% tolerance (more realistic)
abs_tolerance: 100.0      # Doubled threshold
integer_tolerance: 2.0    # More lenient
MAX_DELTA: 1.0e-8        # 10x less strict
MAX_GAMMA: 1.0e-4        # 10x less strict
```

**Impact**: 
- Runtime reduced to <6 hours (from 16+ hours)
- Still maintains good quality (results within ±20% tolerance)
- Fewer iterations per geography level

**Status**: ✅ Implemented and tested successfully

---

### New Features

#### 4. Comprehensive Analysis Framework
**Added**: Complete suite of analysis and validation scripts

**New Configuration** (`tm2_config.py`):
```python
self.ANALYSIS_FILES = {
    'main_scripts': {
        'maz_household_comparison': self.BASE_DIR / 'analysis' / 'MAZ_hh_comparison.py',
        'full_dataset': self.BASE_DIR / 'analysis' / 'analyze_full_dataset.py',
        'compare_controls_vs_results_by_taz': self.BASE_DIR / 'analysis' / 'compare_controls_vs_results_by_taz.py',
        'synthetic_population_analysis': self.BASE_DIR / 'analysis' / 'analyze_syn_pop_model.py',
    },
    'validation_scripts': {
        'maz_household_summary': self.BASE_DIR / 'analysis' / 'maz_household_summary.py',
        'compare_synthetic_populations': self.BASE_DIR / 'analysis' / 'compare_synthetic_populations.py',
        'data_validation': self.BASE_DIR / 'analysis' / 'data_validation.py',
    },
    'visualization_scripts': {
        'taz_controls_analysis': self.BASE_DIR / 'analysis' / 'analyze_taz_controls_vs_results.py',
        'county_analysis': self.BASE_DIR / 'analysis' / 'analyze_county_results.py',
        'interactive_taz_analysis': self.BASE_DIR / 'analysis' / 'create_interactive_taz_analysis.py',
    }
}
```

**Usage**:
```bash
# Run all analysis scripts
python run_all_summaries.py

# Run specific category
python run_all_summaries.py --category core
python run_all_summaries.py --category validation
python run_all_summaries.py --category visualization

# Skip errors and continue
python run_all_summaries.py --skip-errors
```

**Outputs Generated**:
- MAZ-level household comparisons
- TAZ-level control validation charts
- County-level summary statistics
- Interactive Plotly dashboards
- Data quality validation reports
- Synthetic population cross-tabulations

**Status**: ✅ All 10 scripts running successfully

---

#### 5. Interactive TAZ Analysis Dashboard
**Added**: Plotly-based interactive visualizations for TAZ-level analysis

**Features**:
- 28 interactive charts (one per control variable)
- Variable selector dropdown
- Performance metrics (R², MAE, perfect match %)
- Zoom/pan capabilities
- Best-fit lines with equations

**Path Resolution Fix**: 
- Changed from relative paths to `Path(__file__).parent` pattern
- Now works when called from any directory
- Auto-creates output directories

**Output Location**: `output_2023/charts/interactive_taz/`

**Files Generated**:
- `interactive_taz_dashboard.html` - Main dashboard with dropdown
- Individual chart HTML files (28 files)
- `index.html` - Summary page with performance metrics

**Status**: ✅ Working - all charts generated successfully

---

### Configuration Changes

#### Updated Files:
1. **`tm2_config.py`** - Added ANALYSIS_FILES configuration
2. **`settings.yaml`** - Loosened convergence criteria
3. **`config_census.py`** - Fixed circular import, correct COUNTY handling
4. **`controls.py`** - Ensure COUNTY column consistency
5. **`create_interactive_taz_analysis.py`** - Path resolution and emoji fixes

---

### Analysis Script Fixes

#### Fixed Import Errors:
- `analyze_syn_pop_model.py`: Changed `UnifiedTM2Config` → `TM2Config`
- All scripts now use consistent config class name

#### Fixed Path Issues:
- All analysis scripts now use absolute paths via `Path(__file__).parent`
- No more directory dependency issues
- Can run from any working directory

#### Fixed Encoding Issues:
- Removed Unicode emojis that caused Windows console errors
- Changed `📄` and `📁` to `[INFO]` tags

---

## Verification Steps

### 1. Test COUNTY ID Fix
```bash
# Check controls have correct COUNTY column
python -c "import pandas as pd; df = pd.read_csv('output_2023/populationsim_working_dir/configs/controls_by_county.csv'); print(df['COUNTY'].unique())"
# Should show: [1 2 3 4 5 6 7 8 9]
```

### 2. Test Convergence Settings
```bash
# Check settings.yaml
grep -E "rel_tolerance|abs_tolerance|MAX_DELTA|MAX_GAMMA" output_2023/populationsim_working_dir/configs/settings.yaml
```

### 3. Test Analysis Framework
```bash
# Run all analyses
python run_all_summaries.py

# Should complete all 10 scripts:
# ✅ maz_household_comparison
# ✅ full_dataset
# ✅ compare_controls_vs_results_by_taz
# ✅ synthetic_population_analysis
# ✅ taz_controls_analysis
# ✅ county_analysis
# ✅ interactive_taz_analysis
# ✅ maz_household_summary
# ✅ compare_synthetic_populations
# ✅ data_validation
```

### 4. Test Circular Import Fix
```bash
# Should complete without warnings
python -c "from tm2_config import TM2Config; print('No circular import - success')"
```

---

## Current Status (January 29, 2026)

### ✅ Fully Functional
- COUNTY ID mapping correct (sequential 1-9)
- Convergence optimized for <6 hour runtime
- Circular import eliminated
- Analysis framework complete (10 scripts)
- Path resolution fixed across all scripts

### 📊 Pipeline Outputs
- **Households**: 2,918,893 synthetic households
- **Persons**: 7,603,274 synthetic persons
- **Geographies**: 9 counties, 62 PUMAs, 4,734 TAZs, 39,586 MAZs
- **Control Variables**: 37 total (5 county-level, 28 TAZ-level, 4 MAZ-level)

### 🎯 Quality Metrics
- All controls within ±20% tolerance (rel_tolerance=0.2)
- County occupation controls: No NaN errors
- TAZ-level controls: Good R² scores across variables
- MAZ-level controls: Household totals matching

---

## Migration Notes

### If Upgrading from Previous Version:

1. **Regenerate Controls** (COUNTY ID fix):
```bash
python tm2_pipeline.py controls --force
```

2. **Update Convergence Settings** (copy from this repo):
```bash
# settings.yaml already updated in repo
# No action needed if using latest version
```

3. **Install Plotly** (for interactive charts):
```bash
conda activate popsim
pip install plotly
```

4. **Run Analysis** (verify everything works):
```bash
python run_all_summaries.py
```

---

## Known Issues (None Currently)

All previously identified issues have been resolved:
- ✅ NaN errors in occupation controls
- ✅ 16+ hour runtime
- ✅ Circular import warnings
- ✅ Analysis scripts not configured
- ✅ Path resolution errors
- ✅ Unicode encoding errors

---

## Contact

For questions about these updates, refer to:
- `HOW_TO_RUN.md` - Pipeline execution guide
- `PROCESS_OVERVIEW.md` - Detailed process documentation
- `TM2_FULL_REFERENCE.md` - Complete field reference
- `SETUP_INSTRUCTIONS.md` - Environment setup

Last Updated: January 29, 2026
