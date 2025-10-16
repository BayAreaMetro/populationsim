# MAZ/TAZ File Usage Inventory for PopulationSim TM2

## Overview
This document catalogs all MAZ/TAZ file usage across the PopulationSim project to support the transition to explicit `MAZ_NODE/MAZ_SEQ` and `TAZ_NODE/TAZ_SEQ` naming conventions.

## Source Files in tm2py-utils (C:\GitHub\tm2py-utils\tm2py_utils\inputs\maz_taz\)

### Current Column Names in Source Files:
1. **blocks_mazs_tazs_2.5.csv**: `"GEOID10","maz","taz"` (lowercase, old convention)
2. **mazs_tazs_county_tract_PUMA_2.5.csv**: `MAZ_NODE,MAZ_SEQ,TAZ_NODE,TAZ_SEQ,COUNTY,county_name,COUNTYFP10,TRACTCE10,PUMA10,DistID,DistName,MAZ_X,MAZ_Y` (NEW convention)
3. **tazs_county_tract_PUMA_2.5.csv**: `TAZ_NODE,TAZ_SEQ,COUNTY,county_name,COUNTYFP10,TRACTCE10,PUMA10,DistID,DistName,TAZ_X,TAZ_Y` (NEW convention)

---

## PopulationSim Files Using MAZ/TAZ Data

### 1. **unified_tm2_config.py**
**Purpose**: Central configuration file defining paths to MAZ/TAZ input files

**File References**:
- `'blocks_file'`: `C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/blocks_mazs_tazs_2.5.csv`
- `'crosswalk_file'`: `C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/mazs_tazs_county_tract_PUMA_2.5.csv`
- `'maz_id_file'`: `C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/crosswalks/maz_id_lookups.csv`

**Expected Column Usage**:
- From blocks file: `maz`, `taz` (lowercase, old)
- From crosswalk: Expected `MAZ`, `TAZ` but source has `MAZ_NODE,MAZ_SEQ,TAZ_NODE,TAZ_SEQ`

**Update Required**: YES - Column mapping logic needs updating

---

### 2. **create_tm2_crosswalk.py**
**Purpose**: Creates geographic crosswalk files for PopulationSim

**File References**:
- Reads MAZ shapefiles (contains TAZ relationships)
- Creates output: `geo_cross_walk_tm2.csv` with columns `MAZ,TAZ,COUNTY,county_name,PUMA`

**Current Column Detection Logic**:
```python
for col in maz_gdf.columns:
    if col.upper() in ['MAZ', 'MAZ_ID', 'MAZ_ID_']:
        maz_col = col
    elif col.upper() in ['TAZ', 'TAZ_ID', 'TAZ1454']:
        taz_col = col
```

**Update Required**: YES - Add `MAZ_NODE`, `MAZ_SEQ`, `TAZ_NODE`, `TAZ_SEQ` to detection logic

---

### 3. **create_baseyear_controls_23_tm2.py**
**Purpose**: Creates control files for PopulationSim synthesis

**File References**:
- Reads: `blocks_mazs_tazs_2.5.csv` 
- Creates: `maz_marginals.csv`, `taz_marginals.csv`, `maz_data.csv`

**Column Usage**:
- Expected: `MAZ`, `TAZ`, `COUNTY` columns for geographic mapping
- Used in functions: `apply_county_scaling()`, `process_block_distribution_control()`

**Update Required**: YES - Geographic crosswalk and aggregation logic

---

### 4. **tm2_control_utils/config_census.py**
**Purpose**: Census data configuration and file paths

**File References**:
- `NETWORK_MAZ_TAZ_DEF_FILE`: `C:\GitHub\tm2py-utils\tm2py_utils\inputs\maz_taz\blocks_mazs_tazs_2.5.csv`
- `BLOCKS_MAZ_TAZ_FILE`: Same file path

**Column Usage**: Relies on `maz`, `taz` columns from blocks file

**Update Required**: YES - File path and column references

---

### 5. **tm2_control_utils/geog_utils.py**
**Purpose**: Geographic utility functions

**File References**:
- Reads `MAZ_TAZ_ALL_GEOG_FILE` or `MAZ_TAZ_DEF_FILE`

**Column Usage**: Expected `MAZ`, `TAZ` columns for geographic operations

**Update Required**: YES - Column references in utility functions

---

### 6. **postprocess_recode.py**
**Purpose**: Post-processing of PopulationSim output

**File References**:
- Reads crosswalk files: `geo_cross_walk_tm2.csv`
- Reads MAZ lookup: From `config.CONTROL_FILES['maz_id_file']`

**Column Usage**:
- Current: `MAZ`, `TAZ`, `MAZ_ORIGINAL`, `TAZ_ORIGINAL`
- Used for: County assignment, geographic remapping

**Update Required**: MAYBE - Depends on intermediate file column names

---

### 7. **Analysis Scripts** (analysis/ directory)
**Purpose**: Various analysis and validation scripts

**Files**:
- `analyze_corrected_populationsim_performance.py`
- `prepare_tableau_data.py`
- Others

**Column Usage**: Read `maz_marginals.csv`, `taz_marginals.csv` files

**Update Required**: MINIMAL - These use output files, not source files

---

## Update Strategy by Priority

### **Priority 1: Core Configuration Files**
1. **unified_tm2_config.py**: Update file paths and column mapping logic
2. **tm2_control_utils/config_census.py**: Update file references
3. **create_tm2_crosswalk.py**: Add new column detection logic

### **Priority 2: Control Generation**
4. **create_baseyear_controls_23_tm2.py**: Update geographic aggregation logic
5. **tm2_control_utils/geog_utils.py**: Update utility functions

### **Priority 3: Post-processing**
6. **postprocess_recode.py**: Verify compatibility with new column names

### **Priority 4: Analysis Scripts**
7. Various analysis scripts: Minimal changes, mostly use output files

---

## Required Code Changes

### **1. Column Detection Logic Updates**
```python
# OLD:
if col.upper() in ['MAZ', 'MAZ_ID', 'MAZ_ID_']:
    maz_col = col

# NEW: 
if col.upper() in ['MAZ', 'MAZ_ID', 'MAZ_ID_', 'MAZ_NODE', 'MAZ_SEQ']:
    maz_col = col
```

### **2. Column Mapping Logic**
```python
# For files with both MAZ_NODE and MAZ_SEQ, decide which to use:
# Option A: Use MAZ_NODE (sequential 1-39587)
# Option B: Use MAZ_SEQ (node IDs 10001-814506)
# Recommendation: Use MAZ_SEQ for consistency with existing numbering
```

### **3. Crosswalk Creation**
```python
# Update crosswalk output to include both conventions:
crosswalk_df.columns = ['MAZ_SEQ', 'TAZ_SEQ', 'PUMA']
crosswalk_df.rename(columns={'MAZ_SEQ': 'MAZ', 'TAZ_SEQ': 'TAZ'}, inplace=True)
```

---

## Validation Requirements

### **1. Assert Statements (as suggested)**
```python
# Validate MAZ/TAZ ranges to ensure correct column selection
assert(df['MAZ_SEQ'].max() > 100_000), "MAZ_SEQ should be node IDs (>100k)"
assert(df['MAZ_NODE'].max() < 100_000), "MAZ_NODE should be sequential (<100k)"
assert(df['TAZ_SEQ'].max() > 100_000), "TAZ_SEQ should be node IDs (>100k)" 
assert(df['TAZ_NODE'].max() < 100_000), "TAZ_NODE should be sequential (<100k)"
```

### **2. Column Existence Checks**
```python
required_cols = ['MAZ_NODE', 'MAZ_SEQ', 'TAZ_NODE', 'TAZ_SEQ']
missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    raise ValueError(f"Missing required columns: {missing_cols}")
```

---

## Implementation Notes

1. **Backward Compatibility**: Consider maintaining support for old column names during transition
2. **Documentation**: Update all docstrings and comments to reflect new naming convention
3. **Testing**: Validate that geographic aggregations produce identical results
4. **Error Handling**: Add clear error messages when column detection fails

---

## Files Requiring Updates (Summary)

| File | Update Type | Priority | Notes |
|------|-------------|----------|-------|
| `unified_tm2_config.py` | Critical | 1 | Core config, file paths |
| `create_tm2_crosswalk.py` | Critical | 1 | Column detection logic |
| `tm2_control_utils/config_census.py` | Critical | 1 | File references |
| `create_baseyear_controls_23_tm2.py` | Major | 2 | Geographic aggregation |
| `tm2_control_utils/geog_utils.py` | Major | 2 | Utility functions |
| `postprocess_recode.py` | Minor | 3 | Uses output files mostly |
| Analysis scripts | Minimal | 4 | Use output files |

This inventory provides the roadmap for updating the PopulationSim project to use the new explicit MAZ/TAZ naming convention.