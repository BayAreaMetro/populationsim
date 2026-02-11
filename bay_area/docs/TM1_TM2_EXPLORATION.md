# TM1 vs TM2 PopulationSim Exploration Plan

**Created:** February 11, 2026  
**Purpose:** Enumerate differences between TM1 and TM2 population synthesis approaches to inform potential refactoring

---

## Executive Summary

This document compares the **TM1** (Travel Model One) and **TM2** (Travel Model Two) implementations of PopulationSim for the MTC Bay Area region. Both models target a **2023 base year**, but have substantially different geographic structures, control hierarchies, and output requirements.

### Key Differences at a Glance

| Aspect | TM1 (master branch) | TM2 (tm2 branch) |
|--------|---------------------|------------------|
| **Smallest Geography** | TAZ only | MAZ (within TAZ) |
| **Geographic Zones** | ~1,454 TAZs | ~39,726 MAZs in ~5,000 TAZs |
| **Control Levels** | COUNTY → PUMA → TAZ | COUNTY → PUMA → TAZ_NODE → MAZ_NODE |
| **Income Year Dollars** | 2000$ | 2010$ (with 2023$ also available) |
| **County Coding** | 1-9 (different order) | 1-9 (SF=1, SM=2, etc.) |
| **Code Structure** | Simpler, legacy scripts | Modular config/pipeline |

---

## 1. Geographic Structure

### 1.1 TM1 Geographies (master branch)

**File:** `bay_area/hh_gq/data/geo_cross_walk_tm1.csv`

```csv
TAZ,PUMA,COUNTY,county_name,REGION
1,7503,1,San Francisco,1
2,7503,1,San Francisco,1
...
```

- **Columns:** `TAZ`, `PUMA`, `COUNTY`, `county_name`, `REGION`
- **Zones:** ~1,454 TAZs (no MAZ subdivision)
- **Hierarchy:** COUNTY → PUMA → TAZ
- **PopulationSim geographies setting:** `geographies: [COUNTY, PUMA, TAZ]`

### 1.2 TM2 Geographies (tm2 branch)

**File:** `output_2023/populationsim_working_dir/data/geo_cross_walk_tm2_maz.csv`

```csv
MAZ_NODE,TAZ_NODE,COUNTY,county_name,PUMA,...
10001,56,1,San Francisco,2204
10002,56,1,San Francisco,2204
...
```

- **Columns:** `MAZ_NODE`, `TAZ_NODE`, `COUNTY`, `county_name`, `PUMA`, plus block/tract GEOIDs
- **Zones:** ~39,726 MAZs across ~5,000 TAZs
- **Hierarchy:** COUNTY → PUMA → TAZ_NODE → MAZ_NODE
- **PopulationSim geographies setting:** `geographies: [COUNTY, PUMA, TAZ_NODE, MAZ_NODE]`

### 1.3 County Coding Differences

**TM1 County Codes (master branch):**
| COUNTY | Name |
|--------|------|
| 1 | San Francisco |
| 2 | San Mateo |
| 3 | Santa Clara |
| 4 | Alameda |
| 5 | Contra Costa |
| 6 | Solano |
| 7 | Napa |
| 8 | Sonoma |
| 9 | Marin |

**TM2 County Codes (tm2 branch) - uses FIPS-based coding:**
| COUNTY | GEOID_county | Name |
|--------|--------------|------|
| 1 | 06001 | Alameda |
| 13 | 06013 | Contra Costa |
| 41 | 06041 | Marin |
| 55 | 06055 | Napa |
| 75 | 06075 | San Francisco |
| 81 | 06081 | San Mateo |
| 85 | 06085 | Santa Clara |
| 95 | 06095 | Solano |
| 97 | 06097 | Sonoma |

**⚠️ Key Issue:** TM1 and TM2 use completely different county numbering schemes.

---

## 2. Control Variables (PopulationSim Marginals)

### 2.1 TM1 Controls

**File:** `bay_area/hh_gq/configs_TM1/controls.csv`

| Control | Geography | Description |
|---------|-----------|-------------|
| `num_hh` | TAZ | Total households (including GQ as 1-person HH) |
| `hh_size_1_gq` | TAZ | 1-person households (includes GQ) |
| `hh_size_2` | TAZ | 2-person households |
| `hh_size_3` | TAZ | 3-person households |
| `hh_size_4_plus` | TAZ | 4+ person households |
| `hh_inc_30` | TAZ | Income ≤$30k (**2000$**) |
| `hh_inc_30_60` | TAZ | Income $30-60k (**2000$**) |
| `hh_inc_60_100` | TAZ | Income $60-100k (**2000$**) |
| `hh_inc_100_plus` | TAZ | Income >$100k (**2000$**) |
| `hh_wrks_0` | TAZ | 0 workers |
| `hh_wrks_1` | TAZ | 1 worker |
| `hh_wrks_2` | TAZ | 2 workers |
| `hh_wrks_3_plus` | TAZ | 3+ workers |
| `pers_age_00_04` | TAZ | Persons age 0-4 |
| `pers_age_05_19` | TAZ | Persons age 5-19 |
| `pers_age_20_44` | TAZ | Persons age 20-44 |
| `pers_age_45_64` | TAZ | Persons age 45-64 |
| `pers_age_65_plus` | TAZ | Persons age 65+ |
| `gq_type_univ` | TAZ | University GQ persons |
| `gq_type_mil` | TAZ | Military GQ persons |
| `gq_type_othnon` | TAZ | Other non-institutional GQ persons |

**Key Notes:**
- All controls at TAZ level (no MAZ)
- Income bins in **2000 dollars**
- Age bins: 0-4, 5-19, 20-44, 45-64, 65+
- No children in household control
- No occupation controls (commented out)

### 2.2 TM2 Controls (Current Implementation)

**MAZ-Level Controls (`maz_marginals_hhgq.csv`):**
| Control | Description |
|---------|-------------|
| `numhh_gq` | Total households + GQ (person-as-household approach) |
| `total_pop` | Total population |
| `hh_gq_university` | University GQ (each person = 1 household) |
| `hh_gq_military` | Military GQ (each person = 1 household) |
| `hh_gq_other_nonins` | Other non-institutional GQ |

**TAZ-Level Controls (`taz_marginals_hhgq.csv`):**
| Control | Description |
|---------|-------------|
| `inc_lt_20k` | Income <$20k (**2023$**) |
| `inc_20k_45k` | Income $20-45k (**2023$**) |
| `inc_45k_60k` | Income $45-60k (**2023$**) |
| `inc_60k_75k` | Income $60-75k (**2023$**) |
| `inc_75k_100k` | Income $75-100k (**2023$**) |
| `inc_100k_150k` | Income $100-150k (**2023$**) |
| `inc_150k_200k` | Income $150-200k (**2023$**) |
| `inc_200k_plus` | Income >$200k (**2023$**) |
| `hh_wrks_0` through `hh_wrks_3_plus` | Workers in household |
| `pers_age_00_19` | Persons age 0-19 |
| `pers_age_20_34` | Persons age 20-34 |
| `pers_age_35_64` | Persons age 35-64 |
| `pers_age_65_plus` | Persons age 65+ |
| `hh_kids_no` | Households without children |
| `hh_kids_yes` | Households with children |
| `hh_size_1` through `hh_size_6_plus` | Household size distribution |

**COUNTY-Level Controls (`county_marginals.csv`):**
| Control | Description |
|---------|-------------|
| `pers_occ_management` | Management occupations |
| `pers_occ_professional` | Professional occupations |
| `pers_occ_services` | Service occupations |
| `pers_occ_retail` | Retail/sales occupations |
| `pers_occ_manual` | Manual/production occupations |
| `pers_occ_military` | Military occupations |

### 2.3 Control Differences Summary

| Aspect | TM1 | TM2 |
|--------|-----|-----|
| **Finest Geography** | TAZ | MAZ |
| **Income Bins** | 4 bins ($30k, $60k, $100k) in 2000$ | 8 bins (aligned to ACS B19001) in 2023$ |
| **Age Bins** | 0-4, 5-19, 20-44, 45-64, 65+ | 0-19, 20-34, 35-64, 65+ |
| **Household Size** | At TAZ | At TAZ (moved from MAZ) |
| **Children** | Not controlled | `hh_kids_yes/no` at TAZ |
| **Occupation** | Disabled | Active at COUNTY |
| **GQ Approach** | Person counts at TAZ | Person-as-household at MAZ |

---

## 3. ACS/Census Tables Used

### 3.1 Common Tables (Both Models)

| Table | Description | Usage |
|-------|-------------|-------|
| **B01001** | Sex by Age | Age distribution controls |
| **B08202** | Workers in Household | Worker controls |
| **B11016** | Household Size | Household size controls |
| **B19001** | Household Income | Income distribution controls |

### 3.2 TM2-Specific Tables

| Table | Description | Usage |
|-------|-------------|-------|
| **B11005** | Children in Household | `hh_kids_yes/no` controls |
| **C24010** | Sex by Occupation | Occupation controls at county |
| **B23025** | Employment Status | Military occupation proxy |
| **B25003** | Tenure (ACS 1-year) | County-level HH scaling targets |
| **B01003** | Total Population (ACS 1-year) | County-level pop scaling |
| **P1, H1** (Decennial 2020) | Population/Housing counts | Block-level MAZ controls |
| **P5** (Decennial 2020 PL) | Group Quarters by Type | GQ controls |

### 3.3 Census Geographies Required

| Source | TM1 | TM2 |
|--------|-----|-----|
| **Block (2020)** | Not used | MAZ controls base |
| **Block Group (ACS)** | Yes - aggregated to TAZ | Yes - aggregated to MAZ/TAZ |
| **Tract (ACS)** | Yes - aggregated to TAZ | Yes - aggregated to TAZ |
| **County (ACS 1-yr)** | Not clear | Scaling targets |

---

## 4. Output Files

### 4.1 Household Output Comparison

**TM1 Households (`synthetic_households_recode.csv`):**
| Column | Source | Description |
|--------|--------|-------------|
| `HHID` | `unique_hh_id` | Household ID |
| `TAZ` | `TAZ` | TAZ location |
| `hinccat1` | Derived | Income category 1-4 |
| `HINC` | `hh_income_2000` | Income in **2000 dollars** |
| `hworkers` | `hh_workers_from_esr` | Number of workers |
| `VEHICL` | `VEH` | Vehicles |
| `BLD` | `BLD` | Building type |
| `TEN` | `TEN` | Tenure |
| `PERSONS` | `NP` | Number of persons |
| `HHT` | `HHT` | Household type |
| `UNITTYPE` | `TYPEHUGQ` | Unit type (HH vs GQ) |
| `poverty_income_*` | Derived | Poverty calculations |
| `pct_of_poverty` | Derived | Poverty percentage |

**TM2 Households (`households_2023_tm2.csv`):**
| Column | Source | Description |
|--------|--------|-------------|
| `HHID` | `unique_hh_id` | Household ID |
| `TAZ_NODE` | `TAZ_NODE` | TAZ location |
| `MAZ_NODE` | `MAZ_NODE` | MAZ location |
| `MTCCountyID` | `COUNTY` | County 1-9 |
| `HHINCADJ` | `hh_income_2010` | Income in **2010 dollars** |
| `NWRKRS_ESR` | `hh_workers_from_esr` | Number of workers |
| `VEH` | `VEH` | Vehicles |
| `TEN` | `TEN` | Tenure |
| `NP` | `NP` | Number of persons |
| `HHT` | `HHT` | Household type |
| `BLD` | `BLD` | Building type |
| `TYPE` | `TYPEHUGQ` | Unit type |

### 4.2 Person Output Comparison

**TM1 Persons (`synthetic_persons_recode.csv`):**
| Column | Source | Description |
|--------|--------|-------------|
| `HHID` | `unique_hh_id` | Household ID |
| `PERID` | Index + 1 | Person ID |
| `AGE` | `AGEP` | Age |
| `SEX` | `SEX` | Sex |
| `pemploy` | `employ_status` | Employment status (1-4) |
| `pstudent` | `student_status` | Student status (1-3) |
| `ptype` | `person_type` | Person type (1-8) |

**TM2 Persons (`persons_2023_tm2.csv`):**
| Column | Source | Description |
|--------|--------|-------------|
| `HHID` | `unique_hh_id` | Household ID |
| `PERID` | `unique_per_id` | Person ID |
| `AGEP` | `AGEP` | Age |
| `SEX` | `SEX` | Sex |
| `SCHL` | `SCHL` | Educational attainment |
| `OCCP` | `occupation` | Occupation code |
| `WKHP` | `WKHP` | Hours worked per week |
| `WKW` | `WKW` | Weeks worked per year |
| `EMPLOYED` | `employed` | Employment flag 0/1 |
| `ESR` | `ESR` | Employment status recode |
| `SCHG` | `SCHG` | Grade level attending |
| `hhgqtype` | `hhgqtype` | Group quarters type |
| `person_type` | `person_type` | Person type |

### 4.3 Key Output Differences

| Aspect | TM1 | TM2 |
|--------|-----|-----|
| **Geography Columns** | TAZ only | MAZ_NODE, TAZ_NODE, MAZ_SEQ, TAZ_SEQ |
| **Income Dollar Year** | 2000$ | 2010$ |
| **Person Type Definition** | Full CT-RAMP compatible (1-8) | Simplified (employment-based) |
| **Occupation** | Not in output | OCCP code included |
| **Education** | Not in output | SCHL, SCHG included |
| **Work Hours/Weeks** | Not in output | WKHP, WKW included |

---

## 5. Code Architecture Differences

### 5.1 TM1 Code Structure (master branch)

```
bay_area/
├── create_baseyear_controls.py    # Monolithic control generation
├── create_seed_population.py      # PUMS seed data prep
├── postprocess_recode.py          # Output formatting
├── run_populationsim.py           # Execution script
├── hh_gq/
│   ├── configs_TM1/
│   │   ├── controls.csv           # Control definitions
│   │   └── settings.yaml          # PopulationSim config
│   └── data/
│       ├── geo_cross_walk_tm1.csv # Geographic crosswalk
│       └── seed_households.csv    # PUMS seed data
```

### 5.2 TM2 Code Structure (tm2 branch)

```
bay_area/
├── tm2_config.py                  # Unified configuration
├── tm2_pipeline.py                # Full pipeline orchestration
├── create_baseyear_controls.py    # Control generation (uses config)
├── create_seed_population.py      # PUMS seed data prep
├── postprocess_recode.py          # Output formatting
├── utils/
│   ├── config_census.py           # Census table definitions, CONTROLS dict
│   ├── census_fetcher.py          # Census API client
│   ├── controls.py                # Control processing utilities
│   ├── geog_utils.py              # Geography utilities
│   └── tm2_utils.py               # Pipeline utilities
├── output_2023/
│   └── populationsim_working_dir/
│       ├── configs/
│       │   ├── controls.csv       # Generated control definitions
│       │   └── settings.yaml      # PopulationSim config
│       └── data/
│           ├── geo_cross_walk_tm2_maz.csv
│           ├── maz_marginals_hhgq.csv
│           ├── taz_marginals_hhgq.csv
│           └── county_marginals.csv
```

### 5.3 Key Architectural Differences

| Aspect | TM1 | TM2 |
|--------|-----|-----|
| **Configuration** | Inline in scripts | Centralized `tm2_config.py` |
| **Control Definition** | Static `controls.csv` | Programmatic `config_census.py` |
| **Pipeline** | Manual script execution | Orchestrated `tm2_pipeline.py` |
| **Census Fetching** | Inline `CensusFetcher` class | Separate `census_fetcher.py` |
| **Geography** | Hardcoded paths | Configurable via config |

---

## 6. PUMS Seed Data

Both models use PUMS data, but with different processing:

### 6.1 TM1 PUMS Processing

- Uses 2019-2023 5-year PUMS (crosswalked to 2010 PUMAs)
- Income converted to **2000 dollars** using `hh_income_2000` field
- Person types computed to match CT-RAMP person type (1-8)
- Employment/student status computed for TM1 compatibility

### 6.2 TM2 PUMS Processing

- Uses 2019-2023 5-year PUMS (crosswalked to 2020 PUMAs)
- Income available in **2010$ and 2023$** (`hh_income_2010`, `hh_income_2023`)
- Additional fields: occupation, education, work hours/weeks
- Group quarters handled as "person-as-household" at MAZ level

---

## 7. Questions for Stakeholders

Before proceeding with refactoring, these questions need answers:

### Geography
1. **TM1 TAZ Definition:** What is the source of TM1's ~1,454 TAZs? Are they a subset of TM2's TAZs, or an entirely different geography?
2. **Cross-Model Consistency:** Should TM1 TAZs be compatible with TM2 TAZ aggregation (i.e., some MAZs aggregate to each TAZ)?

### Controls
3. **TM1 Income Bins:** Should TM1 income bins remain in 2000 dollars, or be updated to 2023 dollars with different breakpoints?
4. **TM1 Age Bins:** The current 0-4, 5-19, 20-44, 45-64, 65+ bins differ from TM2. Is this intentional?
5. **Children Control:** Should TM1 add `hh_kids_yes/no` controls like TM2?
6. **Occupation Controls:** TM1 has occupation controls commented out. Should they be enabled?

### Outputs
7. **Person Type:** TM1 uses a full 8-category person type. TM2 uses a simpler classification. Which should be standardized?
8. **Poverty Calculations:** TM1 adds poverty income fields. Should TM2 also include these?

### Process
9. **Unified Codebase:** Is the goal a single codebase with `--model_type TM1|TM2` switch, or separate branches?
10. **Testing:** What validation metrics should be used to verify TM1 output matches historical expectations?

---

## 8. Refactoring Tradeoff Analysis

### 8.1 When Unification is Worth It

1. **TM1 is still actively used for projects** and won't be sunset in 2-3 years
   - Future Census updates (2028 5-year ACS) would benefit from shared infrastructure
   - Investment pays off over multiple update cycles

2. **The "shortcuts" in TM1's current 2023 data are causing problems**
   - If TM1's approach has quality issues that need fixing anyway
   - You'd be improving data quality AND modernizing at once

3. **You want a single source of truth for Census data processing**
   - ACS table definitions, CPI conversions, county codes in one place
   - When new Census data arrives, update once instead of twice

4. **Staff knows TM2 code, not TM1**
   - If maintaining legacy TM1 code is becoming a knowledge gap issue
   - Unified codebase = unified team expertise

### 8.2 When Unification is NOT Worth It

1. **TM1 is being retired** in favor of TM2 within ~2 years
   - Just maintain TM1 as-is until sunset

2. **TM1 current outputs are "good enough"** and nobody is complaining
   - "If it ain't broke, don't fix it" has value

3. **The geographic differences make code sharing minimal**
   - 1,454 TAZs vs 39,726 MAZs means most TM2 complexity (MAZ controls, hierarchical consistency) doesn't apply to TM1
   - You'd likely maintain two control generation paths anyway

### 8.3 Code Sharing Assessment

**Shareable components (~40-50%):**
- Census API fetching (`census_fetcher.py`)
- ACS table definitions (`CENSUS_DEFINITIONS`)
- PUMS download and processing (with dollar-year adjustments)
- Some postprocessing logic

**Non-shareable components (~50-60%):**
- Control generation (TAZ-only vs MAZ→TAZ→COUNTY hierarchy)
- Geographic crosswalks (completely different structures)
- Control variable sets (different income bins, age bins)
- Output column mappings (different dollar years, person type definitions)

### 8.4 Recommendation: Lighter-Weight Approach

Rather than full refactoring, a more pragmatic approach:

1. **Extract shared utilities** into a common module both branches can use:
   - Census API client
   - CPI conversion factors  
   - PUMS download/processing

2. **Keep TM1 and TM2 as separate control generation paths** but using shared utilities

3. **Don't try to unify what's fundamentally different** (geography, control variables)

**Benefit:** ~30-40% of unification benefit for ~20% of the effort.

### 8.5 Bottom Line

Unless TM1 has at least 3+ years of active use ahead AND the current 2023 data quality is problematic, **full unification is likely not worth the investment**. The geographic and control differences are substantial enough that much of the code cannot be meaningfully shared.

---

## 9. Proposed Exploration Tasks

### Phase 1: Deep Dive (This Document)
- [x] Document geographic differences
- [x] Catalog control variables
- [x] Map ACS tables to controls
- [x] Compare output file formats
- [x] Document code structure

### Phase 2: Gap Analysis
- [ ] Identify which TM2 components can be reused for TM1
- [ ] Identify TM1-specific code that must be preserved
- [ ] Map PUMS variable differences
- [ ] Document CPI/dollar-year conversion requirements

### Phase 3: Architecture Decision
- [ ] Decide: unified codebase vs separate branches
- [ ] If unified: design model_type abstraction layer
- [ ] Define shared configuration schema
- [ ] Design test harness for both models

### Phase 4: Implementation
- [ ] Create TM1 configuration module (parallel to `tm2_config.py`)
- [ ] Adapt control generation for TAZ-only geography
- [ ] Create TM1+TM2 compatible crosswalk generation
- [ ] Implement TM1 postprocessing (dollar year conversion, person types)
- [ ] Validate outputs against historical TM1 runs

---

## 10. Files to Review

### TM1 (master branch)
- `bay_area/create_baseyear_controls.py` - Control generation logic
- `bay_area/postprocess_recode.py` - Output column mapping
- `bay_area/create_seed_population.py` - PUMS processing
- `bay_area/hh_gq/configs_TM1/settings.yaml` - PopulationSim config
- `bay_area/hh_gq/configs_TM1/controls.csv` - Control definitions

### TM2 (tm2 branch)
- `bay_area/tm2_config.py` - Centralized configuration
- `bay_area/tm2_pipeline.py` - Pipeline orchestration
- `bay_area/utils/config_census.py` - Census/control definitions
- `bay_area/postprocess_recode.py` - Output processing
- `bay_area/output_2023/populationsim_working_dir/configs/settings.yaml`

---

## Appendix A: ACS Table Variable Mapping

### B19001 - Household Income (TM2 Mapping)

| Control | ACS Variables | 2023$ Range |
|---------|---------------|-------------|
| `inc_lt_20k` | B19001_002E, 003E, 004E | $0-19,999 |
| `inc_20k_45k` | B19001_005E, 006E, 007E, 008E, 009E | $20,000-44,999 |
| `inc_45k_60k` | B19001_010E, 011E | $45,000-59,999 |
| `inc_60k_75k` | B19001_012E | $60,000-74,999 |
| `inc_75k_100k` | B19001_013E | $75,000-99,999 |
| `inc_100k_150k` | B19001_014E, 015E | $100,000-149,999 |
| `inc_150k_200k` | B19001_016E | $150,000-199,999 |
| `inc_200k_plus` | B19001_017E | $200,000+ |

### B01001 - Sex by Age

Both models use this table but aggregate to different age bins.

### B08202 - Workers in Household

Both models use the same worker categories (0, 1, 2, 3+).

---

## Appendix B: Dollar Year Conversion Factors

For converting between income dollar years:

| From | To | Factor | Source |
|------|-----|--------|--------|
| 2000$ | 2010$ | 1.264 | CPI-U |
| 2000$ | 2023$ | 1.880 | CPI-U |
| 2010$ | 2023$ | 1.487 | CPI-U |

Note: TM2's `config_census.py` contains `INCOME_BIN_MAPPING` with both 2010$ and 2023$ bin definitions.
