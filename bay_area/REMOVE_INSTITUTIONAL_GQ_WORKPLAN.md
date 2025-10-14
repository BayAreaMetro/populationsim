# Work Plan: Remove Institutional Group Quarters from TM2 Synthetic Population

## Overview
This work plan details the steps needed to modify the TM2 synthetic population generation process to exclude institutional group quarters, aligning with the master branch approach that only includes non-institutional group quarters (universities, military barracks, and other non-institutional facilities).

## Background
Currently, the TM2 branch includes ALL group quarters (institutional + non-institutional), while the master branch excludes institutional group quarters (nursing homes, correctional facilities, etc.). This work plan will modify TM2 to match the master branch approach.

---

## Phase 1: Seed Population Modifications
**File: `create_seed_population_tm2_refactored.py`**

### 1.1 Modify `_create_group_quarters_type()` method
- **Location**: Line ~336-350
- **Changes**:
  - Keep: `df.loc[df['TYPEHUGQ'] == 3, 'hhgqtype'] = 1` (non-institutional → university)
  - **REMOVE**: Call to `_split_institutional_gq()` method
  - **ADD**: Filter to exclude `TYPEHUGQ == 2` records entirely
  
```python
def _create_group_quarters_type(self, df: pd.DataFrame) -> pd.DataFrame:
    """Create PopulationSim-compatible group quarters type - NON-INSTITUTIONAL ONLY"""
    # Based on TYPEHUGQ: 1=household, 2=institutional GQ (EXCLUDE), 3=noninstitutional GQ  
    # PopulationSim expects: 0=household, 1=university GQ, 2=military GQ, 3=other GQ
    
    # EXCLUDE institutional GQ (TYPEHUGQ == 2) entirely
    institutional_gq_count = (df['TYPEHUGQ'] == 2).sum()
    if institutional_gq_count > 0:
        logger.info(f"EXCLUDING {institutional_gq_count:,} institutional GQ records (nursing homes, correctional facilities, etc.)")
        df = df[df['TYPEHUGQ'] != 2].copy()
    
    df['hhgqtype'] = 0  # Default to household
    df.loc[df['TYPEHUGQ'] == 3, 'hhgqtype'] = 1  # Noninstitutional GQ → university
    
    # NO institutional GQ splitting - they're excluded
    return df
```

### 1.2 Remove or modify `_split_institutional_gq()` method
- **Action**: Delete this method entirely OR comment out with explanation
- **Rationale**: No institutional GQ to split

### 1.3 Add institutional GQ filtering
- **Location**: Before final household/person output
- **Purpose**: Ensure no institutional GQ records remain in final seed files

---

## Phase 2: Control Generation Modifications  
**File: `create_baseyear_controls_23_tm2.py`**

### 2.1 Update MAZ-level GQ controls in config
**File: `tm2_control_utils/config_census.py`**

Current:
```python
('gq_pop',        ('pl', 2020, 'P5_001N', 'block', [])),        # ALL GQ
('gq_military',   ('pl', 2020, 'P5_009N', 'block', [])),        # Military 
('gq_university', ('pl', 2020, 'P5_008N', 'block', [])),        # University
```

**Change to**:
```python
# Use P5 subcategories for NON-INSTITUTIONAL only
('gq_pop',        ('pl', 2020, 'P5_003N', 'block', [])),        # Non-institutional GQ total
('gq_military',   ('pl', 2020, 'P5_009N', 'block', [])),        # Military (non-inst)
('gq_university', ('pl', 2020, 'P5_008N', 'block', [])),        # College/University (non-inst)
```

### 2.2 Update regional controls
- **Location**: Special handling for `gq_num_hh_region`
- **Current**: `gq_pop_value = 155065` (includes institutional)
- **Change to**: Recalculate using non-institutional GQ only from ACS B26001
- **Estimate**: Reduce by ~80% to exclude institutional GQ (~31,000 non-institutional)

### 2.3 Remove institutional GQ from data processing
- **Location**: Any logic that processes institutional vs non-institutional splits
- **Action**: Remove or modify to handle non-institutional only

---

## Phase 3: PopulationSim Control Configuration
**File: `output_2023/populationsim_working_dir/configs/controls.csv`**

### 3.1 Modify GQ person controls

**Current**:
```csv
gq_pop,MAZ,persons,10000000,gq_pop,persons.hhgqtype>=2
gq_military,MAZ,persons,1000000,gq_military,persons.hhgqtype==2
gq_university,MAZ,persons,1000000,gq_university,(persons.hhgqtype >= 2) & (persons.AGEP >= 18) & (persons.AGEP <= 25)
gq_other,MAZ,persons,1000000,gq_other,(persons.hhgqtype >= 2) & ((persons.AGEP < 18) | (persons.AGEP > 25))
```

**Change to**:
```csv
# Add TYPEHUGQ filter to exclude institutional GQ
gq_pop,MAZ,persons,10000000,gq_pop,(persons.hhgqtype>=2) & (persons.TYPEHUGQ==3)
gq_military,MAZ,persons,1000000,gq_military,(persons.hhgqtype==2) & (persons.TYPEHUGQ==3)
gq_university,MAZ,persons,1000000,gq_university,(persons.hhgqtype >= 2) & (persons.TYPEHUGQ==3) & (persons.AGEP >= 18) & (persons.AGEP <= 25)
gq_other,MAZ,persons,1000000,gq_other,(persons.hhgqtype >= 2) & (persons.TYPEHUGQ==3) & ((persons.AGEP < 18) | (persons.AGEP > 25))
```

### 3.2 Verify household controls unchanged
- All household controls using `households.hhgqtype==0` should remain unchanged
- Income and worker controls should not be affected

---

## Phase 4: Geographic Crosswalk Updates
**File: `create_tm2_crosswalk.py` or control generation scripts**

### 4.1 Recalculate control totals
- **Purpose**: Ensure MAZ-level totals exclude institutional GQ
- **Files to regenerate**:
  - `maz_marginals.csv`
  - `maz_marginals_hhgq.csv` 
  - Any pre-calculated control files

### 4.2 Update control validation
- **Check**: Geographic distribution of remaining GQ makes sense
- **Validate**: Totals align with non-institutional targets

---

## Phase 5: Configuration Alignment

### 5.1 Census table mapping updates
**File: `tm2_control_utils/config_census.py`**
- **Update**: P5 table subcategory selections
- **Remove**: Any institutional GQ category mappings
- **Align**: With master branch control definitions

### 5.2 Settings review
**File: `output_2023/populationsim_working_dir/configs/settings.yaml`**
- **Review**: Whether convergence tolerances need adjustment
- **Consider**: If smaller GQ population affects convergence behavior

---

## Phase 6: Data Validation & Testing

### 6.1 Create validation scripts
```python
# Validation checks to implement:
def validate_no_institutional_gq(households_df, persons_df):
    """Ensure no institutional GQ in final synthetic population"""
    inst_hh = households_df[households_df.get('TYPEHUGQ', 0) == 2]
    inst_persons = persons_df[persons_df.get('TYPEHUGQ', 0) == 2]
    
    assert len(inst_hh) == 0, f"Found {len(inst_hh)} institutional GQ households"
    assert len(inst_persons) == 0, f"Found {len(inst_persons)} institutional GQ persons"
    
    print("✓ No institutional GQ found in synthetic population")

def compare_gq_totals_with_master():
    """Compare GQ distributions between modified TM2 and master branch"""
    # Implementation to compare final GQ type distributions
    pass
```

### 6.2 Cross-reference with master branch
- **Compare**: GQ type distributions (university, military, other)
- **Validate**: Age distributions in GQ categories
- **Check**: Geographic distribution patterns

---

## Phase 7: Documentation & Cleanup

### 7.1 Update code documentation
- **File**: `create_seed_population_tm2_refactored.py`
  - Update docstrings to reflect non-institutional only approach
  - Add comments explaining institutional GQ exclusion

### 7.2 Update process documentation
- **Create/Update**: README files explaining GQ handling approach
- **Document**: Rationale for excluding institutional GQ
- **Align**: Documentation with master branch approach

### 7.3 Code cleanup
- **Remove**: Unused institutional GQ processing methods
- **Clean**: Hardcoded institutional GQ targets/ratios
- **Simplify**: GQ type assignment logic

---

## Additional Considerations

### Post-processing validation
- **File**: `postprocess_recode.py` - Check for GQ-specific recoding
- **Verify**: Downstream scripts don't expect institutional GQ
- **Test**: Final output file validation

### Backup and rollback strategy
- **Create**: Branch backup before modifications
- **Document**: Rollback procedures if issues arise
- **Test**: Validation suite before deployment

---

## Implementation Priority

### Phase 1 (Critical): Seed Population
Start here - this is the foundation. No institutional GQ should enter the synthesis process.

### Phase 2 (Critical): Control Generation  
Controls must align with seed population data to avoid convergence issues.

### Phase 3 (Critical): PopulationSim Configuration
Synthesis controls must match available seed population.

### Phase 4-6 (Important): Validation & Testing
Can be done in parallel with Phases 1-3 for iterative testing.

### Phase 7 (Cleanup): Documentation
Final step after validation confirms approach works.

---

## Expected Outcomes

### Population Changes
- **Reduction**: ~80% decrease in total GQ population
- **Geographic shift**: Areas with nursing homes/prisons will show larger decreases
- **Age distribution**: Older adult institutional populations removed

### Alignment with Master
- **Consistency**: GQ handling approach identical to master branch
- **Validation**: Similar non-institutional GQ distributions
- **Compatibility**: Seed population structure matches master approach

### Process Improvements
- **Simplified**: No complex institutional GQ splitting logic
- **Robust**: More straightforward GQ type assignment
- **Maintainable**: Aligned with established master branch approach

---

## Success Criteria

- [ ] Zero institutional GQ households in final synthetic population
- [ ] Zero institutional GQ persons in final synthetic population  
- [ ] GQ type distributions similar to master branch
- [ ] PopulationSim converges successfully with modified controls
- [ ] Geographic GQ distribution makes sense (universities, military bases)
- [ ] Age distributions appropriate for non-institutional GQ types
- [ ] Total population aligns with non-institutional control targets

---

*This work plan ensures the TM2 branch will handle group quarters identically to the master branch approach: **non-institutional group quarters only**.*