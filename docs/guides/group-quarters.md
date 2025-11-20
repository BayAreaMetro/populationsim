# PopulationSim Regular Households vs Group Quarters Separation Project

## Overview

This document outlines a comprehensive approach to properly separate regular households from group quarters (GQ) population throughout the PopulationSim pipeline, ensuring accurate demographic controls and synthesis results.

## Background

### Current Issue
The existing PopulationSim implementation mixes regular households with group quarters in household-level controls, leading to:
- Inconsistent control totals where household size categories don't sum properly
- Group quarters persons being counted as "1-person households" 
- Difficulty in separating regular household demographics from institutional populations
- Confusion in downstream analysis and validation

### ACS Definition Context
- **Household**: "All the people who occupy a housing unit" (excludes GQ)
- **Group Quarters**: Dormitories, nursing homes, military barracks, correctional facilities, etc.
- **Key Principle**: GQ populations should be tracked separately from conventional households

## Proposed Solution Architecture

### Core Principles
1. **Separate Control Targets**: Create distinct control totals for regular households (`numhh`) vs total including GQ (`numhh_gq`)
2. **Clean Household Controls**: All household-level demographic controls (size, income, workers, children) apply only to regular households (`hhgqtype==0`)
3. **Separate GQ Tracking**: Group quarters population controlled and synthesized independently
4. **Proper Factoring**: Household size categories sum to regular household total, not GQ-inclusive total
5. **Separate Summaries**: Downstream analysis treats regular households and GQ as distinct populations

### Geographic Control Structure
- **MAZ Level**: 
  - `numhh_gq` (total household records including GQ)
  - `numhh` (regular households only - NEW)
  - GQ person counts by type (university, non-institutional)
- **TAZ Level**: 
  - All household demographic controls (size, income, workers, children) for regular households only
  - Person-level controls (age, occupation) for all population
- **County Level**: 
  - Employment/occupation controls for all working population

## Implementation Plan (10 Steps)

### Step 1: Documentation ✓
Document the approach, rationale, and implementation plan in `docs/household_gq_separation.md`

### Step 2: Control Generation - Add numhh Target
- Modify `create_baseyear_controls_23_tm2.py` to create `numhh` control at MAZ level
- Ensure `numhh` represents only regular households (`hhgqtype==0`)
- Validate that `numhh + gq_persons = numhh_gq`

### Step 3: Control Generation - Update TAZ Household Controls  
- Add `& (households.hhgqtype==0)` to all household-level control expressions
- Ensure factoring targets sum to `numhh` not `numhh_gq`
- Update required column lists and validation

### Step 4: Update controls.csv Configuration
- Add new `numhh` target with proper expression
- Update all household-level target expressions to exclude GQ
- Validate expression syntax and logic

### Step 5: MAZ Marginals File Updates
- Generate updated `maz_marginals_hhgq.csv` with `numhh` column
- Ensure GQ person counts are accurate and separate
- Validate control totals balance correctly

### Step 6: TAZ Marginals File Updates  
- Regenerate `taz_marginals_hhgq.csv` with clean household controls
- Remove `hh_size_1_gq` concept, use pure `hh_size_1` for regular households
- Ensure all household categories sum to proper totals

### Step 7: PopulationSim Configuration Testing
- Test synthesis with updated control files
- Validate that factoring works correctly
- Check that household size categories sum properly
- Verify GQ population is handled appropriately

### Step 8: Update Summary Scripts
- Modify scripts in `run_all_summaries.py` to handle separated populations
- Create separate summaries for regular households vs GQ
- Update validation and comparison scripts

### Step 9: Update Analysis and Visualization
- Modify `create_marginal_controls_visualizations.py` for new structure
- Update validation dashboards and reports
- Ensure documentation reflects new approach

### Step 10: Testing and Validation
- Run full synthesis with new controls
- Compare results against Census/ACS benchmarks
- Validate that regular household demographics are accurate
- Confirm GQ population tracking is correct

## Expected Benefits

1. **Accurate Control Totals**: Household size categories will sum to correct regular household totals
2. **Clean Demographics**: Household income, size, worker distributions will reflect actual households, not GQ-contaminated data
3. **Separate GQ Analysis**: Group quarters population can be analyzed independently
4. **Better Validation**: Easier to validate against Census/ACS household vs GQ statistics
5. **Clearer Documentation**: Unambiguous separation between population types

## Risk Mitigation

- **Backwards Compatibility**: Maintain `numhh_gq` for existing validation scripts
- **Incremental Testing**: Test each step independently before proceeding
- **Documentation**: Clear documentation of changes for future maintenance
- **Validation**: Extensive validation against known benchmarks at each step

## Next Steps

1. **Get Approval**: Review this approach with project stakeholders
2. **Begin Step 2**: Implement `numhh` control generation in MAZ controls
3. **Iterative Development**: Complete each step with validation before proceeding

---

*Document created: October 29, 2025*  
*Author: PopulationSim Bay Area Team*  
*Status: Step 1 Complete - Awaiting approval to proceed*

