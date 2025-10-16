# Comprehensive MAZ/TAZ ID Column Usage Inventory

**Analysis Date:** October 14, 2025  
**Purpose:** Complete inventory of MAZ and TAZ ID usage across all Python files in bay_area directory  
**Context:** Identifying column naming conventions for tm2py-utils integration

## Summary of Findings

### Critical Issue Identified
**Source files in tm2py-utils use different column conventions:**
- `blocks_mazs_tazs_2.5.csv`: Uses `maz`, `taz` (lowercase)
- `mazs_tazs_county_tract_PUMA_2.5.csv`: Uses `MAZ_NODE`, `MAZ_SEQ`, `TAZ_NODE`, `TAZ_SEQ`  
- PopulationSim expects: `MAZ`, `TAZ` (standard uppercase)

**Impact:** Multiple scripts expect different column naming conventions, requiring updates for compatibility.

---

## File-by-File Analysis

### 🔴 HIGH PRIORITY - Core Pipeline Files

#### 1. `unified_tm2_config.py`
**Role:** Central configuration hub for all file paths and settings
**MAZ/TAZ Usage:**
- **Input File Paths:**
  - `blocks_file`: `blocks_mazs_tazs_2.5.csv` (expects `maz`, `taz`)
  - `maz_id_file`: `maz_id_lookups.csv` (expects `MAZ`, `TAZ`, `MAZ_ORIGINAL`, `TAZ_ORIGINAL`)
  - `maz_shapefile`: `mazs_TM2_2_5.shp` (unknown column names)
  - `taz_shapefile`: `tazs_TM2_2_5.shp` (unknown column names)

- **Output File Names:**
  - `maz_marginals.csv`, `taz_marginals.csv`
  - `maz_data.csv`, `maz_data_withDensity.csv`
  - Various other MAZ/TAZ output files

**Required Updates:**
- Add column detection logic for different naming conventions
- Implement mapping between `maz`→`MAZ`, `taz`→`TAZ`
- Handle `MAZ_NODE`/`MAZ_SEQ` vs `MAZ`/`TAZ` variations

#### 2. `create_tm2_crosswalk.py`
**Role:** Creates geographic crosswalk from shapefiles (CRITICAL DEPENDENCY)
**MAZ/TAZ Usage:**
- **Input:** Reads MAZ shapefile (expects `MAZ`, `TAZ` columns)
- **Output:** Creates `geo_cross_walk_tm2.csv` with standard columns
- **Dependencies:** Must work correctly or entire pipeline fails

**Column Expectations:**
```python
# Expected from shapefile reading:
maz_gdf = gpd.read_file(maz_shapefile)
# Likely expects: 'MAZ', 'TAZ' columns
```

**Required Updates:**
- Update to handle new shapefile column names if they differ
- Ensure output crosswalk uses standard `MAZ`, `TAZ` format

#### 3. `create_baseyear_controls_23_tm2.py`
**Role:** Generates PopulationSim control files
**MAZ/TAZ Usage:**
- **Uses crosswalk files to aggregate controls by geography**
- **Expects standard `MAZ`, `TAZ`, `PUMA`, `COUNTY` columns**
- **Outputs:** `maz_marginals.csv`, `taz_marginals.csv` with ID columns

**Column Dependencies:**
- Reads crosswalk: `MAZ`, `TAZ`, `PUMA`, `COUNTY`
- Geographic aggregation functions expect standard naming

#### 4. `create_seed_population_tm2_refactored.py`
**Role:** Creates PUMS seed population for synthesis
**MAZ/TAZ Usage:**
- **Reads crosswalk to determine Bay Area PUMAs**
- **No direct MAZ/TAZ column usage in PUMS data**
- **Comment reference:** "Bay Area PUMAs - 2020 definitions (62 PUMAs with actual MAZ coverage)"

#### 5. `postprocess_recode.py`
**Role:** Post-processing of PopulationSim outputs with geographic recoding
**MAZ/TAZ Usage:**
- **Input Files:**
  - `final_summary_TAZ.csv` (expects `TAZ` column)
  - MAZ ID lookup file (expects `MAZ`, `TAZ`, `MAZ_ORIGINAL`, `TAZ_ORIGINAL`)

- **Output Columns:**
  - Standard: `MAZ`, `TAZ`
  - Remapping: `MAZ_ORIGINAL`, `TAZ_ORIGINAL`

- **Critical Operations:**
  - Geographic remapping between old and new ID systems
  - County assignment via `MAZ` lookup
  - TAZ/MAZ validation and cleanup

**Column Usage Pattern:**
```python
required_cols = ['MAZ', 'TAZ', 'MAZ_ORIGINAL', 'TAZ_ORIGINAL']
households_df['TAZ_ORIGINAL'] = households_df['TAZ']
households_df['MAZ_ORIGINAL'] = households_df['MAZ']
```

---

### 🟡 MEDIUM PRIORITY - Support and Analysis Files

#### 6. `tm2_control_utils/geog_utils.py`
**Role:** Geographic data loading and preparation utilities
**MAZ/TAZ Usage:**
- **Loads MAZ/TAZ definition files**
- **Handles column name standardization:**
  ```python
  maz_taz_def_df.rename(columns={"maz": "MAZ", "taz": "TAZ"}, inplace=True)
  ```
- **Crosswalk operations:** `MAZ`, `TAZ`, `PUMA`, `COUNTY` columns

**Current Handling:**
- ✅ Already handles `maz`→`MAZ`, `taz`→`TAZ` conversion
- ❌ Needs update for `MAZ_NODE`/`MAZ_SEQ` conventions

#### 7. `tm2_pipeline.py`
**Role:** Complete TM2 pipeline orchestration
**MAZ/TAZ Usage:**
- **Crosswalk validation and fixing**
- **Multi-PUMA TAZ resolution**
- **File validation:** `maz_marginals.csv`, `taz_marginals.csv`

**Critical Operations:**
```python
# TAZ-PUMA relationship validation
taz_puma_counts = crosswalk.groupby('TAZ')['PUMA'].nunique()
multi_puma_tazs = taz_puma_counts[taz_puma_counts > 1].index.tolist()
```

---

### 🟢 LOW PRIORITY - Analysis and Utilities

#### 8. Analysis Scripts (`analysis/` directory)
- `prepare_tableau_data.py`: Uses TAZ/PUMA shapefiles for visualization
- `visualize_taz_puma_mapping.py`: Geographic visualization tools

**Usage:** Post-processing visualization only, not critical for core pipeline

---

## Input File Column Requirements

### Source Files Expected Column Names:

#### From tm2py-utils:
1. **`blocks_mazs_tazs_2.5.csv`**
   - Current: `maz`, `taz` (lowercase)
   - Required: Convert to `MAZ`, `TAZ`

2. **`mazs_tazs_county_tract_PUMA_2.5.csv`**
   - Current: `MAZ_NODE`, `MAZ_SEQ`, `TAZ_NODE`, `TAZ_SEQ`
   - Required: Map to `MAZ`, `TAZ` (TBD: which to use?)

3. **`maz_id_lookups.csv`**
   - Expected: `MAZ`, `TAZ`, `MAZ_ORIGINAL`, `TAZ_ORIGINAL`
   - Status: Unknown if exists or column names

4. **Shapefiles:**
   - `mazs_TM2_2_5.shp`: `MAZ_NODE`, `MAZ_SEQ`, `TAZ_NODE` (+ geometry columns)
   - `tazs_TM2_2_5.shp`: `TAZ_NODE`, `TAZ_SEQ` (+ geometry columns)

---

## Required Updates by Priority

### 🔴 CRITICAL (Must fix before pipeline runs):

1. **`create_tm2_crosswalk.py`**
   - Update shapefile column detection
   - Ensure proper MAZ/TAZ column mapping
   - Validate output crosswalk format

2. **`unified_tm2_config.py`**
   - Add column mapping utilities
   - Handle different input file conventions
   - Provide fallback detection logic

### 🟡 HIGH (Pipeline stability):

3. **`tm2_control_utils/geog_utils.py`**
   - Extend column name conversion
   - Add `MAZ_NODE`/`MAZ_SEQ` handling
   - Validate geographic data consistency

4. **`postprocess_recode.py`**
   - Verify MAZ ID lookup file compatibility
   - Ensure remapping logic works with new conventions

### 🟢 MEDIUM (Validation and debugging):

5. **`tm2_pipeline.py`**
   - Update validation logic for new column names
   - Enhance error reporting for column mismatches

---

## Decision Points Needed

### 1. MAZ_NODE vs MAZ_SEQ Selection
**RESOLVED:** Shapefile analysis shows:

**MAZ Shapefile (`mazs_TM2_2_5.shp`):**
- `MAZ_NODE`: Range 10001 to 814506 (original MAZ IDs)
- `MAZ_SEQ`: Range 1 to 39586 (sequential numbering)
- `TAZ_NODE`: Range 1 to 800210 (original TAZ IDs from MAZ file)

**TAZ Shapefile (`tazs_TM2_2_5.shp`):**
- `TAZ_NODE`: Range 1 to 800210 (original TAZ IDs)
- `TAZ_SEQ`: Range 1 to 4734 (sequential numbering)

**Current PopulationSim Crosswalk Format:**
```
MAZ,TAZ,COUNTY,county_name,PUMA
10001,56,1,San Francisco,7511
```
The crosswalk uses **original MAZ_NODE values** (10001) and **original TAZ_NODE values** (56).

**Decision:** 
- `MAZ_NODE` → `MAZ` (use original MAZ IDs, not sequential)
- `TAZ_NODE` → `TAZ` (use original TAZ IDs, not sequential)

### 2. Column Detection Strategy
**Options:**
- A) Dynamic detection with fallback mapping
- B) Configuration-based column mapping
- C) File-specific handling logic

**Recommendation:** Dynamic detection with configuration override

### 3. Implementation Order
**Current blocking issue:** Crosswalk creation likely fails with current naming
**Suggested order:**
1. Fix `create_tm2_crosswalk.py` shapefile reading
2. Update `unified_tm2_config.py` column detection
3. Test with basic pipeline run
4. Update remaining files as needed

---

## Implementation Strategy

### Phase 1: Immediate Fixes (Blocking Issues)
- Investigate actual shapefile column names
- Update crosswalk creation to handle new naming
- Test crosswalk generation

### Phase 2: Column Standardization
- Implement dynamic column detection utilities
- Update all file readers to use standard mapping
- Add validation and error handling

### Phase 3: Testing and Validation
- Run complete pipeline with new naming
- Validate output file formats
- Ensure downstream compatibility

---

**Next Action Required:** ✅ **RESOLVED** - Shapefile analysis complete. Ready to implement column mapping fixes.

## IMMEDIATE IMPLEMENTATION NEEDED:

### 🔴 **CRITICAL:** Update `create_tm2_crosswalk.py`
The script currently expects `MAZ` and `TAZ` columns but shapefiles have:
- `MAZ_NODE` (should map to `MAZ`)  
- `TAZ_NODE` (should map to `TAZ`)

**Required Fix:**
```python
# Current assumption:
# maz_gdf expects columns: 'MAZ', 'TAZ'

# ACTUAL columns available:
# maz_gdf columns: 'MAZ_NODE', 'TAZ_NODE', 'MAZ_SEQ', etc.

# Need to add mapping:
maz_gdf = maz_gdf.rename(columns={'MAZ_NODE': 'MAZ', 'TAZ_NODE': 'TAZ'})
```

This is the **blocking issue** that prevents crosswalk generation.