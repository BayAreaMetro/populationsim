# Comprehensive Raw Input Data Guide
## TM2 PopulationSim Data Sources and Dependencies

**Document Version:** 1.0  
**Date:** December 2024  
**Author:** PopulationSim Bay Area Team

---

## Table of Contents

1. [Overview](#overview)
2. [Census and ACS Data Sources](#census-and-acs-data-sources)
3. [Geographic and Spatial Data](#geographic-and-spatial-data)
4. [PUMS Seed Population Data](#pums-seed-population-data)
5. [Network and Infrastructure Data](#network-and-infrastructure-data)
6. [Configuration and Control Files](#configuration-and-control-files)
7. [External Dependencies](#external-dependencies)
8. [Data Quality and Validation](#data-quality-and-validation)

---

## Overview

The TM2 PopulationSim pipeline requires comprehensive input data from multiple authoritative sources to generate accurate synthetic populations. This guide documents all raw data inputs, their sources, specifications, update frequencies, and quality requirements essential for successful population synthesis operations.

### Input Data Categories

The system integrates eight primary categories of input data:

1. **Census/ACS Data**: Demographic controls from US Census Bureau
2. **Geographic Data**: Spatial boundaries and geographic relationships
3. **PUMS Data**: Seed population records from Public Use Microdata Sample
4. **Network Data**: Transportation analysis zones and geographic definitions
5. **Configuration Data**: System parameters and control specifications
6. **Cache Data**: Downloaded and processed data stored for efficiency
7. **External Dependencies**: Third-party data sources and API access
8. **Validation Data**: Reference data for quality assurance

### Data Flow Architecture

```
External Sources → Data Cache → Processing Pipeline → PopulationSim Engine
     ↓              ↓              ↓                    ↓
- Census API    - ACS Tables   - Control Generation - Synthesis
- PUMS Files    - PUMS Data    - Geographic Processing - Validation  
- Shapefiles    - Crosswalks   - Seed Population    - Outputs
- TM2py-utils   - Config Files - Quality Assurance
```

### Critical Success Factors

**Data Currency**: Most datasets require annual updates to maintain accuracy
**Geographic Consistency**: All spatial data must align with TM2.5 geography definitions  
**API Availability**: Census API access essential for control data generation
**Network Connectivity**: External data sources require reliable internet access

---

## Census and ACS Data Sources

### American Community Survey (ACS) Data

The primary demographic control data comes from the US Census Bureau's American Community Survey, accessed via the Census API.

#### ACS 2023 1-Year Estimates

**Source**: US Census Bureau API  
**Access URL**: `https://api.census.gov/data/2023/acs/acs1`  
**Update Frequency**: Annual (September release)  
**Geographic Coverage**: Counties, PUMAs (limited to areas with 65,000+ population)

**Key Data Tables**:

| Table ID | Description | Variables Used | Control Purpose |
|----------|-------------|----------------|-----------------|
| `B25001` | Housing Units | `B25001_001E` | Total household counts |
| `B01003` | Total Population | `B01003_001E` | Regional population totals |
| `B19001` | Household Income | `B19001_002E` - `B19001_017E` | Income distribution by TAZ |
| `B08202` | Workers by Geography | `B08202_001E` - `B08202_005E` | Worker counts by occupation |
| `B11016` | Household Size | `B11016_001E` - `B11016_008E` | Household size categories |
| `B01001` | Age and Sex | `B01001_001E` - `B01001_049E` | Age distribution controls |
| `B23025` | Employment Status | `B23025_002E` - `B23025_007E` | Employment categories |

#### ACS 2023 5-Year Estimates  

**Source**: US Census Bureau API  
**Access URL**: `https://api.census.gov/data/2023/acs/acs5`  
**Update Frequency**: Annual (December release)  
**Geographic Coverage**: All geographies including block groups and tracts

**Primary Use Cases**:
- Block group level income controls (where 1-year unavailable)
- Small area estimation for demographic categories
- Cross-validation against 1-year estimates

#### Income Control Specification

**ACS Table B19001 - Household Income Distribution**:

```python
# Income bins aligned with ACS categories (2023 dollars)
INCOME_BIN_MAPPING = [
    {
        'control': 'inc_lt_20k',
        'acs_vars': ['B19001_002E', 'B19001_003E', 'B19001_004E'],
        '2023_bin': (0, 19999),
        'acs_categories': ['<$10k', '$10k-15k', '$15k-20k']
    },
    {
        'control': 'inc_20k_45k', 
        'acs_vars': ['B19001_005E', 'B19001_006E', 'B19001_007E', 'B19001_008E', 'B19001_009E'],
        '2023_bin': (20000, 44999),
        'acs_categories': ['$20k-25k', '$25k-30k', '$30k-35k', '$35k-40k', '$40k-45k']
    },
    # ... continues for all 8 income categories
]
```

#### Data Access Configuration

**API Key**: Required for Census Bureau API access  
**Key File**: `M:/Data/Census/API/new_key`  
**Rate Limits**: 500 requests per IP per day  
**Retry Logic**: Automatic retry with exponential backoff for API failures

### PL 94-171 Redistricting Data

**Source**: US Census Bureau Redistricting Data  
**Access URL**: `https://api.census.gov/data/2020/dec/pl`  
**Update Frequency**: Decennial (post-Census release)  
**Geographic Coverage**: Block-level data for group quarters

**Key Variables**:
- `P5_001N`: Total group quarters population
- `P5_008N`: University/college housing
- `P5_009N`: Other noninstitutional group quarters

### Data Cache Management

**Cache Location**: `M:/Data/Census/NewCachedTablesForPopulationSimControls/`  
**Cache Strategy**: Store downloaded data to minimize API calls  
**Cache Validation**: Automatic staleness detection and refresh  
**Cache Organization**: Organized by dataset, year, and geography level

---

## Geographic and Spatial Data

### Transportation Analysis Zones (TAZ/MAZ)

#### MAZ (Micro Analysis Zones) Shapefile

**Source**: TM2py-utils repository  
**File**: `mazs_TM2_2_5.shp`  
**Location**: `C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/`  
**Zone Count**: ~41,434 MAZ zones  
**Coordinate System**: NAD83 / California Albers (EPSG:3310)

**Key Attributes**:
- `MAZ_NODE`: Unique MAZ identifier
- `TAZ_NODE`: Parent TAZ assignment  
- `COUNTY`: County assignment
- Geometry: Polygon boundaries

#### TAZ (Transportation Analysis Zones) Shapefile

**Source**: TM2py-utils repository  
**File**: `tazs_TM2_2_5.shp`  
**Location**: `C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/shapefiles/`  
**Zone Count**: ~5,117 TAZ zones  
**Purpose**: Aggregated transportation analysis units

### Census Geographic Boundaries

#### PUMA (Public Use Microdata Areas) Shapefile

**Source**: US Census Bureau TIGER/Line Files  
**File**: `tl_2022_06_puma20.shp`  
**Download URL**: `https://www2.census.gov/geo/tiger/TIGER2022/PUMA/`  
**Zone Count**: ~104 Bay Area PUMAs  
**Year**: 2020 PUMA boundaries (current standard)

**Geographic Coverage**: 9 Bay Area counties
- PUMA codes: 5301-5355 (covering all Bay Area geography)
- Population threshold: 100,000+ residents per PUMA
- Purpose: Seed geography for PUMS data linkage

#### County Boundaries Shapefile

**Source**: California Open Data Portal  
**File**: `Counties.shp`  
**URL**: `https://gis.data.ca.gov/datasets/CDEGIS::california-counties-3/`  
**Counties**: 9 Bay Area counties with FIPS codes

| County | FIPS | PopulationSim ID |
|--------|------|------------------|
| Alameda | 001 | 4 |
| Contra Costa | 013 | 5 |
| Marin | 041 | 9 |
| Napa | 055 | 7 |
| San Francisco | 075 | 1 |
| San Mateo | 081 | 2 |
| Santa Clara | 085 | 3 |
| Solano | 095 | 6 |
| Sonoma | 097 | 8 |

### Block-Level Geographic Mappings

#### Blocks to MAZ/TAZ Assignment

**Source**: TM2py-utils processed data  
**File**: `blocks_mazs_tazs_2.5.csv`  
**Location**: `C:/GitHub/tm2py-utils/tm2py_utils/inputs/maz_taz/`  
**Record Count**: ~230,000 census blocks

**Schema**:
```csv
GEOID10,maz,taz
060014001001000,12345,1001
060014001001001,12345,1001
...
```

**Data Sources**:
- **GEOID10**: 2010 Census 15-digit block identifiers
- **MAZ Assignment**: Spatial allocation to micro-analysis zones
- **TAZ Assignment**: Aggregation to transportation analysis zones

---

## PUMS Seed Population Data

### 2023 5-Year PUMS Files

**Source**: US Census Bureau Public Use Microdata Sample  
**Data Years**: 2019-2023 (5-year pooled sample)  
**Geographic**: California statewide, filtered to Bay Area PUMAs

#### Household File

**Source URL**: `https://www2.census.gov/programs-surveys/acs/data/pums/2023/5-Year/csv_hca.zip`  
**Extracted File**: `psam_h06.csv` (California households)  
**Output File**: `bay_area_households_2019_2023_crosswalked.csv`  
**Record Count**: ~96,000 Bay Area household records

**Key Variables**:
```python
HOUSEHOLD_VARIABLES = {
    'SERIALNO': 'Household serial number (unique identifier)',
    'WGTP': 'Housing unit weight',
    'PUMA': 'Public use microdata area code',
    'NP': 'Number of persons in household',
    'TYPE': 'Housing unit/group quarters type',
    'BLD': 'Building type',
    'TEN': 'Tenure (owned/rented)',
    'VEH': 'Vehicle availability',
    'HINCP': 'Household income (2023 dollars)',
    'HHT': 'Household type'
}
```

#### Person File

**Source URL**: `https://www2.census.gov/programs-surveys/acs/data/pums/2023/5-Year/csv_pca.zip`  
**Extracted File**: `psam_p06.csv` (California persons)  
**Output File**: `bay_area_persons_2019_2023_crosswalked.csv`  
**Record Count**: ~230,000 Bay Area person records

**Key Variables**:
```python
PERSON_VARIABLES = {
    'SERIALNO': 'Household serial number (links to household)',
    'SPORDER': 'Person number within household',
    'PWGTP': 'Person weight',
    'AGEP': 'Age',
    'SEX': 'Sex',
    'SCHL': 'Educational attainment',
    'ESR': 'Employment status recode',
    'WKHP': 'Hours worked per week',
    'WKW': 'Weeks worked per year',
    'OCCP': 'Occupation code',
    'SCHG': 'School grade attending'
}
```

### PUMS Data Processing

#### Bay Area Filtering

**Geographic Filter**: PUMA codes 5301-5355 (2020 boundaries)  
**Quality Checks**: Remove records with invalid weights or missing critical variables  
**Crosswalk Integration**: 2020 PUMA boundaries automatically integrated in 2023 5-year files

#### Weight Adjustments

**Base Weights**: Use WGTP (household) and PWGTP (person) from Census Bureau  
**Regional Scaling**: Adjust weights to match ACS 1-year regional totals  
**Validation**: Ensure weighted totals align with control data

---

## Network and Infrastructure Data

### TM2py-utils Repository Data

**Repository**: `C:/GitHub/tm2py-utils/`  
**Purpose**: Authoritative source for TM2.5 geographic definitions  
**Update Frequency**: As needed for model updates  
**Maintenance**: Travel Model Two development team

#### Geographic Definition Files

**MAZ/TAZ Definitions**:
- `mazs_TM2_2_5.shp`: MAZ polygon boundaries
- `tazs_TM2_2_5.shp`: TAZ polygon boundaries  
- `blocks_mazs_tazs_2.5.csv`: Block to zone assignments

**Crosswalk Files**:
- `maz_id_lookups.csv`: MAZ identifier conversions
- Various crosswalk files for geographic relationships

### Network Geographic Cache

**Network Location**: `M:/Data/Census/NewCachedTablesForPopulationSimControls/`  
**Purpose**: Centralized storage for processed geographic data  
**Access**: Network drive with team access permissions

**Contents**:
- Processed MAZ/TAZ geographic files
- NHGIS crosswalk files for temporal geography changes
- Block group and tract boundary definitions

---

## Configuration and Control Files

### PopulationSim Configuration

#### Settings Configuration (`settings.yaml`)

```yaml
# Core PopulationSim parameters
geographies: [COUNTY, PUMA, TAZ_NODE, MAZ_NODE]
seed_geography: PUMA
household_weight_col: WGTP
household_id_col: unique_hh_id
total_hh_control: numhh_gq

# Algorithm configuration
INTEGERIZE_WITH_BACKSTOPPED_CONTROLS: True
SUB_BALANCE_WITH_FLOAT_SEED_WEIGHTS: True
GROUP_BY_INCIDENCE_SIGNATURE: False
USE_SIMUL_INTEGERIZER: True
max_expansion_factor: 50

# Convergence criteria
rel_tolerance: 0.05
abs_tolerance: 20.0
integer_tolerance: 0.5
```

#### Control Specification (`controls.csv`)

**Purpose**: Defines which demographic controls to use at each geographic level  
**Record Count**: 32 control categories  
**Format**: CSV with target, geography, importance, and expression columns

```csv
target,geography,seed_table,importance,control_field,expression
numhh_gq,MAZ_NODE,households,100000,numhh_gq,households.unique_hh_id > 0
hh_size_1,TAZ_NODE,households,10000,hh_size_1_gq,households.NP == 1
pers_age_00_19,TAZ_NODE,persons,100000,pers_age_00_19,(persons.AGEP >= 0) & (persons.AGEP <= 19)
inc_lt_20k,TAZ_NODE,households,10000,inc_lt_20k,(households.hh_income_2023 >= 0) & (households.hh_income_2023 <= 19999)
```

### Control Data Files

#### Generated Control Files

**MAZ Controls** (`maz_marginals_hhgq.csv`):
- Total households by MAZ zone (~41,434 records)
- Group quarters by type (university, non-institutional)
- Source: ACS block group data aggregated to MAZ

**TAZ Controls** (`taz_marginals_hhgq.csv`):
- Household demographics by TAZ zone (~5,117 records)  
- Age, income, size, worker categories
- Source: ACS tract data aggregated to TAZ

**County Controls** (`county_marginals.csv`):
- Occupation categories by county (9 records)
- Regional validation totals
- Source: ACS 1-year county data

### Configuration Management

#### Unified Configuration System

**File**: `unified_tm2_config.py`  
**Purpose**: Single source of truth for all file paths and parameters  
**Benefits**: Eliminates hardcoded paths, enables environment flexibility

**Key Configuration Sections**:
```python
# External data paths
EXTERNAL_PATHS = {
    'tm2py_shapefiles': Path("C:/GitHub/tm2py-utils/..."),
    'network_census_cache': Path("M:/Data/Census/..."),
    'pums_current': Path("M:/Data/Census/PUMS_2023_5Year_Crosswalked"),
}

# File templates
FILE_TEMPLATES = {
    'seed_households': "seed_households.csv",
    'maz_marginals': "maz_marginals_hhgq.csv",
    'geo_crosswalk_base': "geo_cross_walk_tm2_maz.csv"
}
```

---

## External Dependencies

### Census Bureau API Access

#### API Configuration

**Base URL**: `https://api.census.gov/data/`  
**Authentication**: API key required (stored in `M:/Data/Census/API/new_key`)  
**Rate Limits**: 500 requests per IP per day  
**Retry Strategy**: Exponential backoff for failed requests

**Datasets Accessed**:
- ACS 1-Year Estimates (primary demographic controls)
- ACS 5-Year Estimates (small area controls)  
- PL 94-171 Redistricting Data (group quarters)
- Economic Census (employment data)

#### API Reliability Considerations

**Downtime**: Census API occasionally experiences maintenance outages  
**Version Changes**: API endpoints may change with new data releases  
**Data Availability**: New data releases follow Census Bureau schedule

### NHGIS Geographic Crosswalks

**Source**: National Historical Geographic Information System  
**URL**: `https://www.nhgis.org/geographic-crosswalks`  
**Purpose**: Handle geographic boundary changes between Census years

**Files Used**:
```python
NHGIS_CROSSWALK_PATHS = {
    ("block", 2020, 2010): "nhgis_blk2020_blk2010_06.csv",
    ("block group", 2020, 2010): "nhgis_bg2020_bg2010_06.csv", 
    ("tract", 2020, 2010): "nhgis_tr2020_tr2010_06.csv"
}
```

### Network Drive Dependencies

#### Shared Data Storage

**Primary Location**: `M:/Data/Census/`  
**Purpose**: Centralized data cache accessible to team members  
**Requirements**: Network connectivity and appropriate permissions

**Directory Structure**:
```
M:/Data/Census/
├── NewCachedTablesForPopulationSimControls/
│   ├── ACS_2023_1year/
│   ├── ACS_2023_5year/
│   ├── PUMS_2019-23/
│   └── NHGIS_crosswalks/
├── PUMS_2023_5Year_Crosswalked/
└── API/
    └── new_key
```

---

## Data Quality and Validation

### Input Data Validation

#### Completeness Checks

**Geographic Coverage**:
- Verify all Bay Area counties represented in datasets
- Ensure complete MAZ/TAZ coverage without gaps
- Validate PUMA coverage for seed geography

**Temporal Consistency**:
- Confirm data years align across all sources
- Validate inflation adjustments for income data
- Check boundary consistency across geographic files

#### Data Quality Metrics

**Census API Data**:
```python
# Quality validation checks
def validate_census_data(df):
    # Check for missing values
    missing_pct = df.isnull().sum() / len(df) * 100
    
    # Validate geographic identifiers
    valid_counties = df['county'].isin(BAY_AREA_COUNTY_FIPS.values()).all()
    
    # Check for reasonable value ranges
    income_range_valid = (df['median_income'] > 0) & (df['median_income'] < 500000)
    
    return {
        'missing_data': missing_pct.max() < 5.0,  # <5% missing allowed
        'geographic_coverage': valid_counties,
        'value_ranges': income_range_valid.all()
    }
```

**PUMS Data**:
- Weight validation: Ensure weights sum to expected population totals
- Geographic consistency: Verify PUMA assignments match boundaries
- Demographic plausibility: Check age, income, and household size distributions

### Error Handling and Recovery

#### Cache Management

**Stale Data Detection**:
```python
def is_cache_stale(file_path, max_age_days=30):
    """Check if cached data needs refresh"""
    if not file_path.exists():
        return True
    
    file_age = (datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)).days
    return file_age > max_age_days
```

**Automatic Refresh**: System automatically refreshes stale cache files  
**Fallback Sources**: Multiple data source options for critical inputs  
**Manual Override**: Force refresh capability for data quality issues

#### API Failure Handling

**Retry Logic**: Exponential backoff with maximum retry limits  
**Rate Limit Management**: Automatic throttling to respect API limits  
**Error Logging**: Comprehensive logging for troubleshooting failed requests

### Data Lineage and Documentation

#### Source Tracking

**Metadata Preservation**:
- Record download timestamps for all external data
- Track Census API version and dataset identifiers  
- Document processing steps and transformations applied

**Version Control**:
- Git tracking for all configuration files
- Automated backup of processed data files
- Documentation of data source changes over time

#### Quality Assurance Reports

**Automated Validation**:
```python
# Generate data quality report
quality_report = {
    'census_api_status': check_census_api_availability(),
    'data_completeness': validate_input_completeness(),
    'geographic_consistency': verify_geographic_alignment(),
    'temporal_consistency': check_data_currency(),
    'cache_status': assess_cache_health()
}
```

**Manual Review Process**:
- Annual review of all external data sources
- Validation against alternative data sources where available  
- Quality assessment documentation for each data source

---

## Conclusion

The TM2 PopulationSim system relies on a comprehensive ecosystem of authoritative data sources to generate accurate synthetic populations. Success depends on careful management of eight categories of input data, from Census Bureau APIs to local geographic definitions.

**Critical Success Factors**:

**Data Currency**: Annual updates essential for demographic accuracy
- Census API access for latest ACS releases
- PUMS data updates with new 5-year files
- Geographic boundary updates as transportation zones evolve

**Quality Assurance**: Multi-layered validation ensures data integrity  
- Automated validation of all input data sources
- Cross-validation between different data sources
- Comprehensive error handling and recovery procedures

**Infrastructure Dependencies**: Reliable access to external systems
- Census Bureau API availability and rate limit management  
- Network drive access for cached data and team collaboration
- TM2py-utils repository maintenance for geographic definitions

**Documentation and Lineage**: Complete traceability of all data sources
- Metadata preservation for all external data downloads
- Version control for configuration and processing scripts
- Quality assurance documentation and validation reports

This comprehensive input data framework ensures the PopulationSim pipeline can reliably generate high-quality synthetic populations while maintaining transparency, reproducibility, and quality control throughout the entire process.

