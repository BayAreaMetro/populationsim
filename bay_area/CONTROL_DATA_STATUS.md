# PopulationSim Control Data Status - 2023

This document describes the status of control data for the Bay Area populationsim model, updated for 2023 to reflect changes in Census data availability.

## Available Controls

### MAZ Level
- ✅ `num_hh` - Number of households (from 2020 Census PL 94-171)
- ✅ `hh_size_1` - 1-person households (from ACS 2023 B11016) 
- ✅ `hh_size_2` - 2-person households (from ACS 2023 B11016)
- ✅ `hh_size_3` - 3-person households (from ACS 2023 B11016)
- ✅ `hh_size_4_plus` - 4+ person households (from ACS 2023 B11016)
- ✅ `gq_pop` - Total group quarters population (from 2020 Census PL 94-171)

### TAZ Level  
- ✅ `hh_wrks_0` - Households with 0 workers (from ACS 2023 B08202)
- ✅ `hh_wrks_1` - Households with 1 worker (from ACS 2023 B08202)
- ✅ `hh_wrks_2` - Households with 2 workers (from ACS 2023 B08202)
- ✅ `hh_wrks_3_plus` - Households with 3+ workers (from ACS 2023 B08202)
- ✅ `pers_age_00_19` - Persons age 0-19 (from ACS 2023 B01001)
- ✅ `pers_age_20_34` - Persons age 20-34 (from ACS 2023 B01001)
- ✅ `pers_age_35_64` - Persons age 35-64 (from ACS 2023 B01001)
- ✅ `pers_age_65_plus` - Persons age 65+ (from ACS 2023 B01001)
- ✅ `hh_kids_no` - Households with no children (from ACS 2023 B11003)
- ✅ `hh_kids_yes` - Households with children (from ACS 2023 B11003)

## Missing Controls (No Longer Available)

### MAZ Level - Group Quarters Types
- ❌ `gq_type_univ` - University group quarters (specific GQ types no longer surveyed in detail)
- ❌ `gq_type_mil` - Military group quarters (specific GQ types no longer surveyed in detail)  
- ❌ `gq_type_othnon` - Other non-institutional group quarters (specific GQ types no longer surveyed in detail)

**Status**: Replaced with total `gq_pop`. Specific GQ types are set to 0 in output files.

### TAZ Level - Income Categories
- ❌ `hh_inc_30` - Households with income ≤$30k (tract-level income data no longer reliable)
- ❌ `hh_inc_30_60` - Households with income $30k-$60k (tract-level income data no longer reliable)
- ❌ `hh_inc_60_100` - Households with income $60k-$100k (tract-level income data no longer reliable)
- ❌ `hh_inc_100_plus` - Households with income >$100k (tract-level income data no longer reliable)

**Status**: Census has reduced granularity of income data at tract level. Set to 0 in output files.

### County Level - Occupation Categories
- ❌ `pers_occ_management` - Management occupations (detailed occupation data no longer reliable at tract level)
- ❌ `pers_occ_professional` - Professional occupations (detailed occupation data no longer reliable at tract level)
- ❌ `pers_occ_services` - Service occupations (detailed occupation data no longer reliable at tract level)
- ❌ `pers_occ_retail` - Retail/sales occupations (detailed occupation data no longer reliable at tract level)
- ❌ `pers_occ_manual` - Manual/production occupations (detailed occupation data no longer reliable at tract level)
- ❌ `pers_occ_military` - Military occupations (detailed occupation data no longer reliable at tract level)

**Status**: Census has reduced detail and geographic granularity of occupation data. All set to 0 in output files.

## Impact on PopulationSim

The missing controls will still allow populationsim to run, but with reduced constraint precision:

1. **Group Quarters**: Total GQ population is still controlled, but specific types (university, military, other) will be unconstrained
2. **Income**: Household income distribution will be unconstrained at TAZ level
3. **Occupation**: Worker occupation distribution will be unconstrained at county level

## Alternative Data Sources

For future work, consider:
- **American Community Survey PUMS**: May provide more detailed controls at PUMA level
- **Local Administrative Data**: University enrollment, military base data, etc.
- **Synthetic Data**: Use regional patterns to estimate missing controls

## Files Updated

- `controls_simplified.csv`: Updated controls specification without missing variables
- `tm2_control_utils/config.py`: Updated control definitions with detailed comments
- `create_baseyear_controls_23_tm2.py`: Updated to handle missing controls gracefully
