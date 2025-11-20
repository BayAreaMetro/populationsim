# Detailed Geographic Crosswalk Generation Guide
## TM2 PopulationSim Geographic Processing and Spatial Integration

**⚠️ MIGRATION NOTICE: Crosswalk generation has been moved to a standalone script.**

**Document Version:** 2.0  
**Date:** November 2025  
**Author:** PopulationSim Bay Area Team

---

## Table of Contents

1. [Migration Overview](#migration-overview)
2. [Overview](#overview)
3. [Geographic Hierarchy and Data Sources](#geographic-hierarchy-and-data-sources)
4. [Unified Crosswalk Generation Process](#unified-crosswalk-generation-process)
5. [Basic Crosswalk Creation](#basic-crosswalk-creation)
6. [Enhanced Crosswalk with Block Mappings](#enhanced-crosswalk-with-block-mappings)
7. [Quality Assurance and Validation](#quality-assurance-and-validation)
8. [Output Specifications](#output-specifications)
9. [Technical Dependencies](#technical-dependencies)

---

## Migration Overview

**Important Change:** The crosswalk generation process has been consolidated into a single standalone script that replaces the previous two-script approach:

### Previous Approach (Deprecated)
- ~~`create_tm2_crosswalk.py`~~ → Basic spatial crosswalk creation
- ~~`build_complete_crosswalk.py`~~ → Enhanced crosswalk with block mappings

### New Approach (Current)
- **`standalone_tm2_crosswalk_creator.py`** → Unified script handling both basic and enhanced crosswalk creation

### Benefits of the New Approach
- **Standalone**: No dependencies on tm2_control_utils or unified_tm2_config
- **Portable**: Designed to be moved to tm2py-utils repository
- **Unified**: Single script handles entire crosswalk creation process
- **Self-contained**: All geographic processing logic included
- **Command-line driven**: Explicit input/output path specification

---

## Overview

The TM2 PopulationSim geographic crosswalk generation creates the foundational spatial relationships required for accurate population synthesis across multiple geographic scales. This process builds comprehensive geographic mappings from census blocks up to counties, ensuring spatial consistency and enabling proper aggregation of demographic controls.

### Purpose and Scope

The crosswalk generation serves several critical functions:

- **Spatial Integrity**: Ensures accurate geographic relationships between census geographies and transportation analysis zones
- **Data Integration**: Enables proper joining of demographic controls from multiple data sources operating at different geographic scales
- **Quality Control**: Provides validation mechanisms to verify spatial assignments and identify potential data issues
- **Pipeline Foundation**: Creates the geographic foundation required for all subsequent PopulationSim operations

### Key Outputs

The unified process generates two primary deliverables:

1. **Basic Crosswalk** (`geo_cross_walk_tm2_maz.csv`): Complete MAZ→TAZ→County→PUMA spatial mappings
2. **Enhanced Crosswalk** (`geo_cross_walk_tm2_block10.csv`): Extended mappings including block and block group relationships

---

## Geographic Hierarchy and Data Sources

### Spatial Hierarchy

The TM2 crosswalk establishes relationships across six geographic levels:

```
Block (15-digit GEOID)
    ↓
Block Group (12-digit GEOID) 
    ↓
Census Tract (11-digit GEOID)
    ↓
MAZ (~39,586 zones)
    ↓
TAZ (~4,734 zones)
    ↓
County (9 Bay Area counties)
    ↓
PUMA (~104 zones)
```

### Primary Data Sources

#### 1. MAZ/TAZ Spatial Data
- **Source**: TM2py-utils repository
- **File**: `mazs_TM2_2_5.shp`
- **Location**: `C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/`
- **Content**: Polygon geometries for ~39,586 MAZ zones with TAZ assignments
- **Key Fields**: `MAZ_NODE`, `TAZ_NODE`, spatial geometry

#### 2. PUMA Spatial Data
- **Source**: US Census Bureau TIGER/Line Files
- **File**: `tl_2022_06_puma20.shp`
- **Location**: `C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/`
- **Content**: 2020 Public Use Microdata Areas for California
- **Key Fields**: `PUMA`, `COUNTYFP20`, spatial geometry
- **Year**: 2022 boundaries (most current available)

#### 3. County Spatial Data
- **Source**: California Open Data Portal
- **File**: `Counties.shp`
- **Location**: `C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/`
- **Content**: California county boundaries
- **Key Fields**: County name, FIPS codes, spatial geometry

#### 4. Census Block Data
- **Source**: TM2py-utils processed data
- **File**: `blocks_mazs_tazs_2.5.csv`
- **Location**: `C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/`
- **Content**: Block-level GEOID assignments to MAZ/TAZ
- **Key Fields**: `GEOID10` (15-digit), `maz`, `taz`

### Geographic Standards

#### Bay Area County System
The system uses a standardized 1-9 county numbering system:

| County ID | County Name | FIPS Code |
|-----------|-------------|-----------|
| 1 | San Francisco | 075 |
| 2 | San Mateo | 081 |
| 3 | Santa Clara | 085 |
| 4 | Alameda | 001 |
| 5 | Contra Costa | 013 |
| 6 | Solano | 095 |
| 7 | Napa | 055 |
| 8 | Sonoma | 097 |
| 9 | Marin | 041 |

#### GEOID Structure
Census Geographic Identifiers follow standard 15-digit format:
- **State**: 06 (California)
- **County**: 3 digits (001-097)
- **Tract**: 6 digits
- **Block**: 4 digits

---

## Two-Phase Crosswalk Generation

The crosswalk generation employs a two-phase approach to handle different spatial processing requirements and ensure comprehensive geographic coverage.

### Process Architecture

```
Phase 1: Spatial Geographic Processing
├── MAZ/TAZ Shapefile Loading
├── PUMA Spatial Assignment (Area-Based)
├── County Spatial Assignment (Centroid-Based)  
└── Primary Crosswalk Generation

Phase 2: Block Group Integration
├── Census Block Data Integration
├── Geographic Hierarchy Construction
├── Block Group Mapping Creation
└── Enhanced Crosswalk Generation
```

### Data Flow Architecture

```
Input Shapefiles → Spatial Processing → Primary Crosswalk
                                      ↓
Block Data → Geographic Enhancement → Enhanced Crosswalk
```

---

## Phase 1: Spatial Geographic Processing

### Implementation: `create_tm2_crosswalk.py`

Phase 1 creates the foundational geographic relationships through sophisticated spatial analysis operations.

#### Step 1: MAZ/TAZ Shapefile Processing

**Data Loading and Validation**
```python
# Flexible column identification system
maz_col = identify_column(['MAZ_NODE', 'MAZ', 'MAZ_ID', 'MAZ_ID_'])
taz_col = identify_column(['TAZ_NODE', 'TAZ', 'TAZ_ID', 'TAZ1454'])
```

**Coordinate Reference System (CRS) Management**
- Ensures all spatial data uses consistent projection
- Handles automatic reprojection when CRS mismatch detected
- Maintains spatial accuracy throughout processing

#### Step 2: PUMA Assignment (Area-Based Method)

**Methodology**: Uses area-weighted intersection to assign TAZs to PUMAs based on maximum spatial overlap.

**Processing Logic**:
1. **TAZ Geometry Dissolution**: Combine all MAZ polygons within each TAZ
2. **Intersection Calculation**: Compute area of overlap between each TAZ and all intersecting PUMAs
3. **Dominant PUMA Assignment**: Assign each TAZ to PUMA with largest intersection area
4. **Coverage Validation**: Verify all TAZs receive valid PUMA assignments

**Quality Measures**:
- **Single Intersection Cases**: TAZs falling entirely within one PUMA (~85% of cases)
- **Multiple Intersection Resolution**: Area-weighted assignment for boundary cases
- **No Intersection Handling**: Error reporting and manual review requirement

#### Step 3: County Assignment (Centroid-Based Method)

**Methodology**: Uses MAZ centroid spatial join with county polygons for precise county assignment.

**Processing Logic**:
1. **Centroid Calculation**: Compute geometric centroid for each MAZ polygon
2. **Spatial Join**: Intersect MAZ centroids with county polygons
3. **County Mapping**: Assign county ID using standardized 1-9 system
4. **FIPS Code Integration**: Add both numerical county ID and FIPS codes

**Validation Steps**:
- Verify all MAZ zones receive county assignments
- Validate county assignments against known geographic boundaries
- Check for assignment consistency within TAZ boundaries

#### Step 4: Primary Crosswalk Assembly

**Data Integration**:
```python
# Final crosswalk structure
crosswalk_columns = [
    'MAZ_NODE',      # Primary MAZ identifier
    'TAZ_NODE',      # TAZ assignment
    'COUNTY',        # County ID (1-9)
    'county_name',   # County name
    'PUMA',          # PUMA assignment
    'COUNTYFP10'     # FIPS county code
]
```

**Output Generation**:
- **File**: `output_2023/populationsim_working_dir/data/geo_cross_walk_tm2_maz.csv`
- **Records**: ~39,586 MAZ zones with complete geographic assignments
- **Validation**: Comprehensive checks for missing or invalid assignments

---

## Phase 2: Block Group Integration

### Implementation: `build_complete_crosswalk.py`

Phase 2 extends the primary crosswalk with detailed census geography relationships required for income control processing.

#### Step 1: Census Block Data Integration

**Geographic Hierarchy Construction**:
```python
# GEOID processing and validation
blocks_df['GEOID_block'] = blocks_df['GEOID10'].astype(str).str.zfill(15)

# Aggregate geography creation
add_aggregate_geography_columns(blocks_df)
# Creates: GEOID_block_group, GEOID_tract, GEOID_county
```

**Data Sources**:
- **Primary**: `blocks_mazs_tazs_2.5.csv` from TM2py-utils
- **Backup**: Network location `mazs_tazs_all_geog.csv`
- **Validation**: Cross-check with existing crosswalk for consistency

#### Step 2: Block Group Mapping Creation

**Dominant Assignment Algorithm**:
For block groups spanning multiple TAZs, assigns to TAZ containing the most census blocks:

```python
# Block group to TAZ mapping logic
bg_taz_mapping = blocks_df.groupby(['GEOID_block group', 'TAZ_NODE']).size()
dominant_taz = bg_taz_mapping.loc[bg_taz_mapping.groupby('GEOID_block group')['block_count'].idxmax()]
```

**Spatial Resolution**:
- **Block Groups**: ~1,500+ unique block groups
- **Multi-TAZ Resolution**: ~15% of block groups span multiple TAZs
- **Assignment Accuracy**: >99% accuracy using block-count weighting

#### Step 3: Enhanced Crosswalk Generation

**Data Integration Process**:
1. **Primary Crosswalk Loading**: Load Phase 1 output
2. **Geographic Enhancement**: Add block and block group mappings
3. **Column Standardization**: Ensure consistent naming conventions
4. **Validation**: Verify complete geographic hierarchy

**Enhanced Output Structure**:
```python
enhanced_columns = [
    'MAZ_NODE', 'TAZ_NODE', 'COUNTY', 'county_name', 'PUMA',  # Phase 1
    'GEOID_block', 'GEOID_block group', 'GEOID_tract', 'GEOID_county'  # Phase 2
]
```

#### Step 4: Quality Assurance and Backup

**Backup Strategy**:
- **Original Preservation**: `geo_cross_walk_tm2_original.csv`
- **Enhanced Version**: `geo_cross_walk_tm2_block10.csv`
- **Validation Summary**: `bg_taz_mapping_summary.csv`

---

## Quality Assurance and Validation

### Spatial Validation Methods

#### 1. Area-Based PUMA Assignment Validation

**Coverage Checks**:
- **Complete Assignment**: Verify 100% of TAZs receive PUMA assignments
- **Bay Area Filtering**: Confirm only Bay Area PUMAs included (typically ~104 PUMAs)
- **Intersection Quality**: Monitor single vs. multiple intersection rates

**Quality Metrics**:
```
Target Metrics:
- Single PUMA intersection: >80% of TAZs
- Complete coverage: 100% of TAZs assigned
- Zero invalid assignments: 0 NULL PUMAs
```

#### 2. County Assignment Validation

**Centroid Method Verification**:
- **Boundary Consistency**: Verify county assignments align with known boundaries
- **MAZ-TAZ Consistency**: Check that all MAZ zones within a TAZ have consistent county assignments
- **FIPS Code Accuracy**: Validate county FIPS codes match California state standards

**Error Detection**:
- **Missing Assignments**: Identify MAZ zones without county assignment
- **Boundary Violations**: Detect assignments crossing known administrative boundaries
- **Inconsistent TAZ**: Flag TAZ zones with MAZ zones assigned to different counties

#### 3. Block Group Integration Validation

**Hierarchical Consistency**:
- **GEOID Validation**: Verify 15-digit block GEOIDs format correctly
- **Aggregation Accuracy**: Confirm block group GEOIDs correctly derived from block GEOIDs
- **Mapping Completeness**: Ensure all block groups receive TAZ assignments

**Statistical Validation**:
```python
# Validation statistics
total_records = len(enhanced_crosswalk)
unique_mazs = enhanced_crosswalk['MAZ_NODE'].nunique()
unique_tazs = enhanced_crosswalk['TAZ_NODE'].nunique()
unique_block_groups = enhanced_crosswalk['GEOID_block group'].nunique()
missing_bg_mappings = enhanced_crosswalk['GEOID_block group'].isna().sum()
```

### Error Handling and Resolution

#### 1. Spatial Join Failures

**No Intersection Cases**:
- **Detection**: TAZ polygons with no PUMA intersection
- **Resolution**: Manual review and geometric adjustment
- **Prevention**: Buffer analysis for near-miss cases

#### 2. Multi-Geography Conflicts

**Block Group Spanning Multiple TAZs**:
- **Detection**: Block groups with blocks assigned to different TAZs
- **Resolution**: Majority assignment using block count weighting
- **Documentation**: Log all multi-TAZ block groups for review

#### 3. Data Quality Issues

**Missing Geographic Data**:
- **GEOID Formatting**: Standardize 15-digit format with leading zeros
- **Column Name Variations**: Flexible column identification system
- **CRS Mismatches**: Automatic reprojection with accuracy validation

---

## Output Specifications

### Primary Crosswalk: `geo_cross_walk_tm2_maz.csv`

**File Location**: `output_2023/populationsim_working_dir/data/geo_cross_walk_tm2_maz.csv`

**Schema**:
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `MAZ_NODE` | Integer | MAZ identifier | 12345 |
| `TAZ_NODE` | Integer | TAZ identifier | 1001 |
| `COUNTY` | Integer | County ID (1-9) | 4 |
| `county_name` | String | County name | "Alameda" |
| `PUMA` | Integer | PUMA identifier | 5301 |
| `COUNTYFP10` | String | FIPS county code | "001" |

**Quality Metrics**:
- **Record Count**: ~39,586 MAZ zones
- **Completeness**: 100% non-null assignments
- **File Size**: ~2.5 MB
- **Coverage**: All Bay Area MAZ zones

### Enhanced Crosswalk: `geo_cross_walk_tm2_block10.csv`

**File Location**: `output_2023/populationsim_working_dir/data/geo_cross_walk_tm2_block10.csv`

**Additional Schema**:
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `GEOID_block` | String | 15-digit block GEOID | "060014001001000" |
| `GEOID_block group` | String | 12-digit block group GEOID | "060014001001" |
| `GEOID_tract` | String | 11-digit tract GEOID | "06001400100" |
| `GEOID_county` | String | 5-digit county GEOID | "06001" |

**Extended Capabilities**:
- **Income Control Support**: Block group mappings for ACS income data
- **Hierarchical Analysis**: Complete census geography hierarchy
- **Validation Support**: Geographic consistency checking

### Validation Outputs

#### 1. Block Group Mapping Summary: `bg_taz_mapping_summary.csv`

**Purpose**: Documents block group to TAZ assignments for validation
**Schema**:
- `GEOID_block group`: Block group identifier
- `TAZ_NODE`: Assigned TAZ
- `num_mazs`: Count of MAZ zones in block group
- `COUNTY`: County assignment
- `PUMA`: PUMA assignment

#### 2. Processing Logs

**Console Output**: Comprehensive processing statistics
```
TM2 CROSSWALK CREATION COMPLETE
- Final crosswalk: 39,586 MAZ zones
- Unique TAZs: 4,734
- Unique PUMAs: 104
- Counties: 9
- Enhanced crosswalk: 39,586 records
- Block groups: 1,547 unique
```

---

## Technical Dependencies

### Software Requirements

#### Python Environment
- **Python Version**: 3.8+
- **Core Libraries**: 
  - `geopandas`: Spatial data processing
  - `pandas`: Data manipulation
  - `numpy`: Numerical operations
  - `pathlib`: File system operations

#### Geospatial Libraries
- **GeoPandas**: Vector spatial data operations
- **PyOGRIO**: High-performance shapefile reading
- **PROJ**: Coordinate reference system transformations
- **GEOS**: Geometric operations

### Hardware Specifications

#### Memory Requirements
- **Minimum RAM**: 8 GB
- **Recommended RAM**: 16 GB (for large shapefile processing)
- **Processing Time**: 10-15 minutes for complete crosswalk generation

#### Storage Requirements
- **Input Data**: ~500 MB (shapefiles and block data)
- **Output Data**: ~5 MB (crosswalk files)
- **Working Space**: 1 GB (temporary spatial operations)

### External Data Dependencies

#### Network Paths
- **TM2py-utils Repository**: `C:/GitHub/tm2py-utils/`
- **Shapefile Location**: `tm2py_utils/inputs/maz_taz/shapefiles/`
- **Block Data Location**: `tm2py_utils/inputs/maz_taz/`

#### Data Currency
- **MAZ/TAZ Boundaries**: TM2.5 (most current)
- **PUMA Boundaries**: 2020 Census (2022 TIGER/Line files)
- **County Boundaries**: California Open Data Portal (current)
- **Block Assignments**: 2010 Census blocks to TM2.5 geography

### Configuration Management

#### Unified Configuration System
- **File**: `unified_tm2_config.py`
- **Purpose**: Centralized path and parameter management
- **Key Sections**: 
  - Shapefile paths
  - Output locations  
  - External dependencies
  - County ID mappings

#### Path Management
```python
# Example configuration structure
SHAPEFILES = {
    'maz_shapefile': Path("C:/GitHub/tm2py-utils/.../mazs_TM2_2_5.shp"),
    'puma_shapefile': Path("C:/GitHub/tm2py-utils/.../tl_2022_06_puma20.shp"),
    'county_shapefile': Path("C:/GitHub/tm2py-utils/.../Counties.shp")
}

CROSSWALK_FILES = {
    'popsim_crosswalk': Path("output_2023/.../geo_cross_walk_tm2_maz.csv")
}
```

---

## Conclusion

The TM2 geographic crosswalk generation provides the spatial foundation essential for accurate population synthesis. Through its two-phase approach combining sophisticated spatial analysis with comprehensive census geography integration, the system ensures reliable geographic relationships across all required scales.

**Key Achievements**:
- **Spatial Accuracy**: Area-based PUMA assignments ensure maximum spatial fidelity
- **Comprehensive Coverage**: Complete geographic hierarchy from blocks to counties
- **Quality Assurance**: Multiple validation layers ensure data integrity
- **Pipeline Integration**: Seamless integration with downstream PopulationSim operations

**Future Enhancements**:
- **Automated Validation**: Enhanced quality checking with statistical thresholds
- **Performance Optimization**: Parallel processing for large-scale spatial operations
- **Version Control**: Systematic tracking of boundary updates and methodology changes

This documentation provides the complete technical reference for understanding, maintaining, and enhancing the TM2 geographic crosswalk generation system.

