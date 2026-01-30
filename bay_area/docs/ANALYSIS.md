# PopulationSim Analysis and Validation

## Overview

The TM2 PopulationSim pipeline includes a comprehensive analysis framework with 10 automated scripts that validate results, generate visualizations, and produce quality reports.

## Quick Start

### Run All Analysis Scripts
```bash
cd bay_area
python run_all_summaries.py
```

This executes all 10 analysis scripts organized into three categories:
- **Core** (4 scripts): Primary analysis and comparisons
- **Visualization** (3 scripts): Charts and interactive dashboards
- **Validation** (3 scripts): Quality checks and verification

**Runtime**: ~6-8 minutes for complete analysis suite

**Output Location**: `output_2023/charts/`

### Run Specific Categories
```bash
# Run only core analysis
python run_all_summaries.py --category core

# Run only visualizations
python run_all_summaries.py --category visualization

# Run only validation
python run_all_summaries.py --category validation

# Skip errors and continue
python run_all_summaries.py --skip-errors
```

## Analysis Scripts

### Core Analysis Scripts

#### 1. MAZ Household Comparison (`MAZ_hh_comparison.py`)
**Purpose**: Compare synthetic household counts vs controls at MAZ level

**Outputs**:
- `maz_household_comparison_scatter.png` - Scatter plot of control vs result
- `maz_household_residuals.png` - Residual analysis
- Summary statistics (R², MAE, perfect match %)

**Key Metrics**:
- R² score (how well results match controls)
- Mean Absolute Error (average difference per MAZ)
- Percentage of MAZs with perfect match

**What to Look For**: R² > 0.95 indicates excellent fit

---

#### 2. Full Dataset Analysis (`analyze_full_dataset.py`)
**Purpose**: Comprehensive statistical analysis of synthetic population

**Outputs**:
- `full_dataset_summary.txt` - Detailed statistics
- Distribution charts for all demographic variables
- Cross-tabulation tables

**Includes**:
- Household size distribution
- Income distribution by county
- Age distribution by county
- Worker distribution
- Person type breakdown

**What to Look For**: Distributions should closely match Census patterns

---

#### 3. TAZ Controls vs Results (`compare_controls_vs_results_by_taz.py`)
**Purpose**: Compare all 28 TAZ-level control variables

**Outputs**:
- `taz_comparison_summary.csv` - Statistical comparison for each variable
- Scatter plots for each variable (28 charts)
- Correlation metrics

**Variables Analyzed**:
- Household totals (numhh, numhh_gq)
- Household size (hh_size_1 through hh_size_6_plus)
- Workers (hh_wrks_0, hh_wrks_1, hh_wrks_2, hh_wrks_3_plus)
- Age groups (pers_age_00_19, pers_age_20_34, pers_age_35_64, pers_age_65_plus)
- Children (hh_kids_yes, hh_kids_no)
- Income brackets (inc_lt_20k through inc_200k_plus)
- Group quarters (hh_gq_university, hh_gq_noninstitutional)

**What to Look For**: R² > 0.80 for most variables

---

#### 4. Synthetic Population Analysis (`analyze_syn_pop_model.py`)
**Purpose**: Cross-tabulation analysis of synthetic population characteristics

**Outputs**:
- County-level cross-tabulations
- Household type by income analysis
- Person characteristics by household type
- Education level analysis

**What to Look For**: Realistic combinations (e.g., high income correlates with higher education)

---

### Visualization Scripts

#### 5. TAZ Controls Analysis (`analyze_taz_controls_vs_results.py`)
**Purpose**: Detailed TAZ-level visualization with multiple chart types

**Outputs**:
- Scatter plots with best-fit lines (28 variables)
- Residual plots showing over/under prediction
- County-specific breakdowns

**Features**:
- Color-coded by county
- Best-fit equation shown
- Performance metrics annotated

**What to Look For**: Points clustered near diagonal line (perfect match)

---

#### 6. County Analysis (`analyze_county_results.py`)
**Purpose**: County-level summary charts and comparisons

**Outputs**:
- `county_totals_comparison.png` - Household/person totals by county
- `county_occupation_distribution.png` - Occupation breakdown
- `county_income_distribution.png` - Income distribution
- County summary table

**What to Look For**: Totals should match county controls, distributions should be realistic

---

#### 7. Interactive TAZ Analysis (`create_interactive_taz_analysis.py`)
**Purpose**: Interactive Plotly dashboards for detailed exploration

**Outputs** (`output_2023/charts/interactive_taz/`):
- `interactive_taz_dashboard.html` - Main dashboard with variable dropdown
- Individual HTML charts (28 files, one per variable)
- `index.html` - Summary page with performance rankings

**Features**:
- **Interactive**: Zoom, pan, hover for details
- **Variable selector**: Dropdown to switch between 28 variables
- **Performance metrics**: R², MAE, perfect match % displayed
- **Best-fit lines**: Linear regression with equation
- **TAZ identification**: Hover to see TAZ number and exact values

**How to Use**:
1. Open `interactive_taz_dashboard.html` in web browser
2. Use dropdown menu to select variable
3. Zoom into regions of interest
4. Hover over points for TAZ details
5. Click index.html to see ranked performance

**What to Look For**: 
- High R² values (> 0.80)
- Points near diagonal line
- Low MAE (< 10% of mean)
- High perfect match percentage (> 20%)

---

### Validation Scripts

#### 8. MAZ Household Summary (`maz_household_summary.py`)
**Purpose**: Summarize MAZ-level household distribution

**Outputs**:
- `maz_household_summary.csv` - Summary statistics per MAZ
- Distribution histogram
- Outlier identification

**What to Look For**: No MAZs with impossible values (e.g., negative households)

---

#### 9. Compare Synthetic Populations (`compare_synthetic_populations.py`)
**Purpose**: Compare synthetic population against seed population

**Outputs**:
- Demographic distribution comparisons
- Scaling factor analysis
- Geographic distribution comparison

**What to Look For**: Synthetic should expand seed proportionally across all demographics

---

#### 10. Data Validation (`data_validation.py`)
**Purpose**: Quality checks on final synthetic population

**Outputs**:
- `data_validation_report.txt` - Comprehensive validation report
- Error/warning log

**Checks Performed**:
- No missing values in required fields
- All IDs are unique
- All households have at least one person
- All persons belong to valid households
- Geographic IDs are valid (MAZ, TAZ, COUNTY in valid ranges)
- Demographic values in valid ranges

**What to Look For**: Zero errors, minimal warnings

---

## Output File Structure

```
output_2023/
└── charts/
    ├── core/                      # Core analysis outputs
    │   ├── maz_household_comparison_scatter.png
    │   ├── full_dataset_summary.txt
    │   ├── taz_comparison_summary.csv
    │   └── synthetic_population_crosstabs.csv
    │
    ├── visualization/             # Visualization outputs
    │   ├── county_totals_comparison.png
    │   ├── county_occupation_distribution.png
    │   ├── taz_controls_scatter_*.png (28 files)
    │   └── taz_residuals_*.png (28 files)
    │
    ├── validation/                # Validation outputs
    │   ├── maz_household_summary.csv
    │   ├── population_comparison.csv
    │   └── data_validation_report.txt
    │
    └── interactive_taz/           # Interactive dashboards
        ├── interactive_taz_dashboard.html  ⭐ Main dashboard
        ├── index.html                      # Summary page
        └── taz_*.html (28 individual charts)
```

## Interpretation Guide

### Understanding R² (R-squared)
- **> 0.95**: Excellent fit
- **0.90 - 0.95**: Very good fit
- **0.80 - 0.90**: Good fit
- **< 0.80**: Review for issues

### Understanding MAE (Mean Absolute Error)
- Compare to mean control value
- MAE < 10% of mean: Excellent
- MAE 10-20% of mean: Good
- MAE > 20% of mean: Review variable

### Understanding Perfect Match %
- **> 30%**: Excellent (many zones match exactly)
- **20-30%**: Very good
- **10-20%**: Good
- **< 10%**: Expected for large-value controls

## Common Patterns

### Expected Results
- **numhh**: Should have R² > 0.98 (primary control)
- **Income variables**: R² typically 0.85-0.95
- **Age variables**: R² typically 0.90-0.95
- **Group quarters**: Lower R² acceptable (sparse data)

### Red Flags
- **R² < 0.70** for major variables → Check control generation
- **Large systematic bias** (all points above/below line) → Check control totals
- **Outliers** far from trend → Check specific TAZ controls
- **Missing data** in validation → Pipeline error

## Troubleshooting

### Issue: Low R² for a variable
**Check**:
1. Control file has valid data for that variable
2. Variable is being used in PopulationSim settings
3. Convergence tolerance isn't too loose
4. Seed population has variation in that variable

### Issue: Systematic over/under prediction
**Check**:
1. Control totals are correct (not scaled incorrectly)
2. Geographic crosswalk assigns all zones
3. No missing counties or TAZs in controls

### Issue: Analysis script fails
**Check**:
1. Output files exist in expected locations
2. File paths are correct (use `Path(__file__).parent`)
3. Required packages installed (pandas, matplotlib, plotly)
4. Sufficient memory for large datasets

## Integration with Pipeline

The analysis step can be run as part of the full pipeline:

```bash
# Full pipeline including analysis
python tm2_pipeline.py full --force

# Or run analysis separately after synthesis
python tm2_pipeline.py analysis --force
```

The pipeline automatically:
1. Checks if required output files exist
2. Runs all 10 analysis scripts
3. Reports success/failure for each
4. Continues even if individual scripts fail (with --skip-errors)

## Best Practices

1. **Always run analysis** after synthesis to validate results
2. **Review interactive dashboard** for detailed TAZ-level exploration
3. **Check data validation report** for any errors
4. **Compare county totals** against known Census totals
5. **Investigate outliers** in scatter plots
6. **Save analysis outputs** with synthesis results for documentation

## Requirements

### Python Packages
```bash
# Core packages (should already be installed)
pandas
numpy
matplotlib
seaborn

# Additional for interactive dashboards
plotly
```

### Install Missing Packages
```bash
conda activate popsim
pip install plotly  # If not already installed
```

## Advanced Usage

### Custom Analysis
You can create custom analysis scripts following the pattern:

```python
from pathlib import Path
from tm2_config import TM2Config

def analyze_custom():
    config = TM2Config()
    
    # Get paths from config
    output_dir = config.POPSIM_WORKING_DIR / "output"
    
    # Load data
    hh_df = pd.read_csv(output_dir / "households_2023_tm2.csv")
    
    # Your analysis here
    ...
    
    # Save results
    chart_dir = config.BASE_DIR / "output_2023" / "charts" / "custom"
    chart_dir.mkdir(parents=True, exist_ok=True)
```

### Adding to run_all_summaries.py
Edit `tm2_config.py` to add your script to `ANALYSIS_FILES` dictionary.

---

Last Updated: January 29, 2026
