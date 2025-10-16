# Military Group Quarters Re-enablement Change Log

## Change Summary

**Date**: October 16, 2025  
**Issue**: Military group quarters (gq_military) was excluded from TM2 synthetic population  
**Resolution**: Re-enabled military GQ while maintaining exclusion of other institutional types  
**Impact**: Military personnel now properly included in travel demand modeling  

## Background

Originally, all institutional group quarters were excluded from TM2, including military housing. This blanket exclusion was implemented to avoid modeling populations with limited travel mobility (nursing homes, prisons, etc.). However, military personnel have regular travel patterns and should be included in transportation modeling.

## Technical Implementation

### Configuration Changes
- **File**: `tm2_control_utils/config_census.py`
- **Change**: Re-enabled `gq_military` control using Census P5_009N variable
- **Location**: Added back to MAZ controls OrderedDict

### Processing Logic Updates
- **File**: `create_baseyear_controls_23_tm2.py`
- **Function**: `write_outputs()`
- **Change**: Updated GQ calculation to: `gq_pop = gq_university + gq_military + gq_other`
- **Documentation**: Added extensive comments explaining selective institutional inclusion

### Validation Updates
- **Function**: `validate_group_quarters_controls()`
- **Change**: Added specific validation for gq_military column existence
- **Purpose**: Ensures military GQ is properly processed and included in final output

## Group Quarters Policy Matrix

| GQ Type | Included in TM2 | Rationale |
|---------|----------------|-----------|
| Military barracks/housing | ✅ **YES** | Regular travel patterns (commuting, shopping, recreation) |
| University/college dorms | ✅ **YES** | Student travel for classes, work, activities |
| Group homes | ✅ **YES** | Residents participate in community activities |
| Worker dormitories | ✅ **YES** | Workers commute and travel for daily needs |
| Religious group quarters | ✅ **YES** | Community-based living with normal mobility |
| Nursing homes | ❌ **NO** | Limited mobility, specialized transportation |
| Prisons/correctional | ❌ **NO** | Restricted movement, no regular travel |
| Mental health institutions | ❌ **NO** | Limited community travel participation |

## Results Validation

### Successful Implementation Indicators
- ✅ `gq_military` column appears in final MAZ marginals
- ✅ Military GQ population: 1,684 people regionwide
- ✅ Component validation: `gq_pop = gq_university + gq_military + gq_other`
- ✅ Total GQ reduced from ~200K (all types) to ~162K (non-institutional only)

### Test Results (October 16, 2025)
```
Group Quarters Breakdown:
- University GQ: 50,694 people (31.2%)
- Military GQ: 1,684 people (1.0%) *** RE-ENABLED ***
- Other non-institutional GQ: 109,838 people (67.7%)
- Total modeled GQ: 162,216 people
- [EXCLUDED] Institutional GQ: ~38,000 people (estimated)
```

## Impact Assessment

### Travel Demand Modeling
- **Benefit**: Military personnel now contribute to travel demand forecasts
- **Accuracy**: Better representation of commuting patterns near military installations
- **Base/Housing Coverage**: Travis AFB, Presidio, other Bay Area military facilities

### Data Quality
- **Population Coverage**: More complete synthetic population
- **Geographic Accuracy**: MAZ-level military housing properly populated
- **Demographic Balance**: Military age/income demographics included

## Files Modified

1. **tm2_control_utils/config_census.py**
   - Re-enabled gq_military control definition
   - Added P5_009N Census variable processing

2. **create_baseyear_controls_23_tm2.py**
   - Updated docstring with military GQ policy explanation
   - Modified write_outputs() function with detailed change log
   - Enhanced validate_group_quarters_controls() function
   - Added comprehensive inline documentation

3. **docs/CONTROL_GENERATION.md**
   - Added "Group Quarters Processing" section
   - Documented inclusion/exclusion policy
   - Explained final GQ structure

4. **docs/PROCESS_OVERVIEW.md**
   - Updated "Group Quarters Handling" section
   - Added policy rationale and travel behavior explanation

## Verification Steps

To verify military GQ is properly included:

1. **Check MAZ marginals file**:
   ```bash
   head -1 output_2023/populationsim_working_dir/data/maz_marginals.csv
   # Should show: MAZ_NODE,num_hh,total_pop,gq_university,gq_military,gq_other,gq_pop
   ```

2. **Validate military GQ totals**:
   ```python
   import pandas as pd
   df = pd.read_csv('output_2023/populationsim_working_dir/data/maz_marginals.csv')
   print(f"Military GQ total: {df['gq_military'].sum():,}")
   # Should show: Military GQ total: 1,684
   ```

3. **Component sum validation**:
   ```python
   df['gq_calc'] = df['gq_university'] + df['gq_military'] + df['gq_other']
   diff = abs(df['gq_pop'] - df['gq_calc']).max()
   print(f"Max component difference: {diff}")
   # Should show: Max component difference: 0.0
   ```

## Future Considerations

- **Monitoring**: Track military GQ totals in future data updates
- **Validation**: Ensure P5_009N variable remains available in Census data
- **Documentation**: Keep change rationale documented for future team members
- **Policy Review**: Periodic review of institutional vs. non-institutional classification

---

**Prepared by**: GitHub Copilot  
**Review Status**: Implemented and Validated  
**Next Review**: Annual with Census data updates