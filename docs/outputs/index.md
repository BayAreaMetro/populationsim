---
layout: default
title: Outputs
---

# Outputs

Documentation for input fields, output files, and summary reports.

## Output Documentation

### [Input Fields Reference](input-fields.html)
Complete reference for all input fields in the seed population and control files.

**Covered fields:**
- Household attributes (size, income, workers, etc.)
- Person attributes (age, sex, occupation, etc.)
- Geographic identifiers
- Weight fields

### [Output Summaries](summaries.html)
Overview of the summary reports and aggregated outputs produced by the pipeline.

**Topics:**
- Regional summaries
- County-level aggregations
- Control vs. result comparisons
- Validation metrics

### [TAZ-Level Outputs](taz-summaries.html)
Detailed documentation of TAZ-level synthetic population outputs.

**Topics:**
- TAZ summary file structure
- Household and person counts by TAZ
- Control matching performance
- Export formats

## Key Output Files

### Synthetic Population Files
- `synthetic_households.csv` - Final household records
- `synthetic_persons.csv` - Final person records
- `tm2_outputs/households_taz_*.csv` - TAZ-aggregated household data
- `tm2_outputs/persons_taz_*.csv` - TAZ-aggregated person data

### Summary Reports
- `summary_*_taz.csv` - TAZ-level control vs. result summaries
- `county_summary.csv` - County-level aggregations
- `regional_summary.csv` - Regional totals

### Validation Outputs
- `diagnostics/` - Diagnostic plots and reports
- `incidence_table.csv` - Household-control incidence matrix
- `convergence_log.csv` - IPF convergence tracking

## File Formats

All output files use UTF-8 encoding with comma-separated values (CSV).

### Standard Columns

**Household Files:**
- `household_id` - Unique household identifier
- `TAZ`, `MAZ`, `COUNTY` - Geographic identifiers
- `hhsize` - Household size
- `hhincome` - Household income (2010 dollars)
- `hhwkrs` - Number of workers
- `hhgq` - Group quarters flag

**Person Files:**
- `person_id` - Unique person identifier
- `household_id` - Parent household ID
- `age` - Age in years
- `sex` - Sex (1=Male, 2=Female)
- `occup` - Occupation code
- `esr` - Employment status

## Quick Access

| File Type | Location | Description |
|-----------|----------|-------------|
| Synthetic Population | `output/` | Final household and person files |
| Summaries | `tm2_outputs/` | Aggregated summaries by geography |
| Diagnostics | `diagnostics/` | Validation plots and reports |
| Logs | `*.log` | Pipeline execution logs |

---

[← Back to Home](../index.html)
