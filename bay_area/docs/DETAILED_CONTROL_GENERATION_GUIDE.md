# Detailed Control Generation Guide for Bay Area PopulationSim

*A comprehensive guide to understanding the control generation process, data sources, geographic processing, and scaling methodologies used in the Bay Area PopulationSim model.*

---

## Table of Contents

1. [Overview and Purpose](#overview-and-purpose)
2. [Data Sources and Census Integration](#data-sources-and-census-integration)
3. [Geographic Framework and Processing](#geographic-framework-and-processing)
4. [Control Categories and Definitions](#control-categories-and-definitions)
5. [Scaling Methodologies](#scaling-methodologies)
6. [Quality Assurance and Validation](#quality-assurance-and-validation)
7. [Output Files and Structure](#output-files-and-structure)
8. [Technical Implementation](#technical-implementation)

---

## Overview and Purpose

The control generation step is the foundation of the Bay Area PopulationSim model, creating the statistical targets that guide synthetic population generation. This process transforms raw Census data into a comprehensive set of marginal controls at multiple geographic levels, ensuring that the synthetic population accurately reflects the demographic, economic, and household characteristics of the Bay Area.

### What Are Controls?

Controls are statistical targets that specify how many people or households in each geographic zone should have specific characteristics. For example, a control might specify that Traffic Analysis Zone (TAZ) 1001 should contain exactly 245 households with incomes between $75,000-$100,000, or that Alameda County should have 118,550 management/professional workers.

### The Three-Tier Geographic Hierarchy

The Bay Area PopulationSim model operates on a three-tier geographic hierarchy, each serving different modeling purposes:

1. **MAZ (Micro Analysis Zones)**: ~41,434 zones - Fine-grained geography for detailed local analysis
2. **TAZ (Traffic Analysis Zones)**: ~5,117 zones - Transportation modeling units for travel demand
3. **COUNTY**: 9 zones - Regional units for labor market and economic analysis

### Multi-Year Data Integration

The system integrates multiple Census data sources to leverage the best available information:

- **2020 Decennial Census**: Provides the most accurate household and population counts at detailed geography
- **ACS 2023 5-Year Estimates**: Offers detailed demographic and economic characteristics with statistical reliability
- **ACS 2023 1-Year Estimates**: Supplies the most current regional totals for validation and scaling

---

## Data Sources and Census Integration

### Primary Data Sources

#### 2020 Decennial Census (Primary Base Data)
- **Geography**: Block level (most detailed available)
- **Key Variables**: 
  - H1_002N: Occupied housing units (households)
  - P5_008N through P5_012N: Group quarters population by type
- **Strengths**: Complete enumeration, high geographic detail, no sampling error
- **Usage**: Foundation for household counts and group quarters at MAZ level

#### ACS 2023 5-Year Estimates (Demographic Detail)
- **Geography**: Tract and block group level
- **Key Variables**:
  - B25001: Housing units and tenure
  - B19001: Household income distribution
  - B23025: Employment status and occupation
  - B01001: Age and sex distribution
- **Strengths**: Detailed demographic characteristics, statistical reliability
- **Usage**: Household size, income, age, and occupation distributions

#### ACS 2023 1-Year Estimates (Current Totals)
- **Geography**: County level only
- **Key Variables**:
  - B25001_001E: Total households by county
  - B01003_001E: Total population by county
- **Strengths**: Most current data, reflects recent demographic changes
- **Usage**: Regional validation targets and scaling factors

### Data Processing Workflow

#### Step 1: Census Data Acquisition
The system automatically downloads and caches Census data using the Census API:

```python
# Example: Downloading household income data
census_data = get_census_data(
    dataset='acs5',
    year=2023,
    table='B19001',  # Household income
    geography='tract',
    state='06',      # California
    county=['001', '013', '041', '055', '075', '081', '085', '095', '097']
)
```

#### Step 2: Geographic Interpolation

Since Census geographies don't perfectly align with MAZ/TAZ boundaries, the system uses sophisticated interpolation:

- **Block-to-MAZ Aggregation**: Uses geographic crosswalks to aggregate 2020 Census blocks to MAZ zones
- **Tract-to-TAZ Interpolation**: Employs areal interpolation weights to distribute tract-level data to TAZ zones
- **Temporal Interpolation**: For geographic boundary changes between 2010 and 2020, uses NHGIS crosswalks

##### Detailed 2020-to-2010 Block Interpolation Process

**Background**: The TM2 MAZ/TAZ system was designed based on **2010 Census block boundaries**. However, the latest demographic data comes from the **2020 Decennial Census**, which has different block boundaries due to:
- Population shifts requiring block splits
- Geographic corrections and boundary adjustments
- Annexations and jurisdiction changes

**Interpolation Methodology**:

1. **Source Data**: 
   - 2020 DHC (Demographic and Housing Characteristics) File at block level
   - NHGIS block-to-block crosswalk (2020 blocks → 2010 blocks)
   - Crosswalk includes areal interpolation weights for split/merged blocks

2. **Interpolation Formula**:
   ```
   For each 2010 block:
       est_2010 = Σ (value_2020_block × weight_2020_to_2010)
   
   Where:
       - value_2020_block = household count or GQ count from 2020 Census
       - weight_2020_to_2010 = interpolation weight from NHGIS crosswalk
       - Sum is over all 2020 blocks that intersect the 2010 block
   ```

3. **Weight Calculation** (performed by NHGIS):
   - Based on geographic overlap area between 2020 and 2010 blocks
   - Assumes uniform population density within source blocks
   - Weights sum to 1.0 for each 2020 block's distribution across 2010 blocks

4. **Specific Census Tables Interpolated**:

| Table | Description | Variables | Universe |
|-------|-------------|-----------|----------|
| H1 | Housing Units | H1_001N (Total), H1_002N (Occupied) | Housing units |
| P5 | Group Quarters Population | P5_008N (University), P5_009N (Military), P5_011N/012N (Other noninst.) | Persons in group quarters |
| H13 | Household Size (if used) | H13_001N through H13_008N | Households |

5. **Validation**:
   - Population conservation: Total 2020 Census = Total interpolated to 2010
   - Check for negative values (none should exist)
   - Compare county totals pre/post interpolation (should match exactly)

6. **Aggregation to MAZ**:
   - After interpolation to 2010 blocks, aggregate using `blocks_mazs_tazs.csv`
   - Simple summation: `MAZ_value = Σ block_value` for all blocks in MAZ
   - No further interpolation needed (MAZs are defined as unions of 2010 blocks)

**Data Flow**:
```
2020 Census (2020 blocks)
    ↓ [NHGIS interpolation weights]
2020 estimates on 2010 blocks
    ↓ [blocks_mazs_tazs.csv aggregation]
MAZ controls (2020 data, 2010 geography)
    ↓ [County scaling to ACS 2023]
Final MAZ controls (scaled to match ACS 2023 county targets)
```

**Geographic File Sources**:
- **MAZ Definitions**: `blocks_mazs_tazs.csv` (from MTC TM2 geography)
- **Full Geography**: `mazs_tazs_all_geog.csv` (MAZ-TAZ-PUMA-County linkages)
- **NHGIS Crosswalk**: `nhgis_blk2020_blk2010_<state>.csv` (from IPUMS NHGIS project)

**Why This Approach**:
- Allows use of latest Census data while maintaining TM2 geographic compatibility
- Preserves fine-scale geographic detail (block-level precision)
- Areal interpolation is reasonable at Census block scale (blocks are small and relatively homogeneous)
- Alternative would require complete remapping of 41,434 MAZs to 2020 geography (infeasible)

#### Step 3: Data Validation and Quality Control
Each data source undergoes rigorous validation:

- **Completeness Checks**: Ensures all required geographic units have data
- **Consistency Validation**: Verifies that totals match expected Census totals
- **Outlier Detection**: Identifies and flags unusual values for manual review

---

## Geographic Framework and Processing

### MAZ (Micro Analysis Zone) Level

MAZs represent the finest geographic resolution in the model, with approximately 41,434 zones covering the 9-county Bay Area.

#### Housing Units vs. Households for MAZ Controls

**Critical Distinction:**

The Census publishes two related but different counts in Table H1:
- **H1_001N**: Total housing units (all structures, occupied + vacant)
- **H1_002N**: Occupied housing units = **Households**

**For PopulationSim MAZ controls, we use H1_002N (Households):**

```python
num_hh = H1_002N  # Occupied housing units = Households
```

**Why we DON'T use H1_001N (Total housing units):**

1. **Vacant units have no people**: Can't synthesize household characteristics (size, income, workers) for empty units
2. **PopulationSim needs occupied units**: The algorithm matches household attributes to people living in them
3. **Travel modeling requirement**: TM2 models travel behavior of people in occupied housing, not empty buildings
4. **Data availability**: Household characteristics (size, income, workers) only exist for occupied units

**Regional Example (Bay Area 2020):**
```
Total housing units (H1_001N):     2,995,998
Occupied units/Households (H1_002N): 2,762,143  ← Used for num_hh control
Vacant units (difference):            233,855   ← Excluded from synthesis
Vacancy rate:                         7.8%
```

**What This Means:**
- The `num_hh` control represents **households** (people living in units)
- This does NOT include ~48K vacant units
- Vacant units are intentionally excluded from population synthesis
- Group quarters persons (university, military) are handled separately (see GQ section)

#### MAZ Control Generation Process:

1. **Base Data**: 2020 Decennial Census at block level
2. **Geographic Aggregation**: Blocks aggregated to MAZ using definitive crosswalk
3. **Control Types Generated**:
   - **Households** (`num_hh`): Direct aggregation of occupied housing units
   - **Population** (`total_pop`): Total persons in households and group quarters
   - **Group Quarters**: Detailed breakdown by institutional type

#### MAZ Group Quarters Processing:

Group quarters represent persons living in institutional or communal arrangements. The system processes three categories:

- **University Group Quarters** (`hh_gq_university`): Dormitories and student housing (P5_008N)
- **Military Group Quarters** (`hh_gq_military`): Military barracks and base housing (P5_009N)
- **Other Noninstitutional** (`hh_gq_other_nonins`): Group homes, religious quarters, worker housing (P5_011N + P5_012N)

**Important Note**: Institutional group quarters (nursing homes, prisons, hospitals) are excluded as they don't participate in the regular housing market.

### TAZ (Traffic Analysis Zone) Level

TAZs serve as the primary geography for transportation modeling, with approximately 5,117 zones.

#### TAZ Control Generation Process:

1. **Base Data**: ACS 2023 5-Year estimates at tract and block group level
2. **Geographic Processing**: Sophisticated interpolation from Census geographies to TAZ
3. **Control Categories**:

   **Household Size Distribution**:
   - `hh_size_1`: Single-person households
   - `hh_size_2`: Two-person households  
   - `hh_size_3`: Three-person households
   - `hh_size_4`: Four-person households
   - `hh_size_5`: Five-person households
   - `hh_size_6_plus`: Six or more person households

   **Household Income Distribution** (in 2023 dollars):
   - `inc_lt_20k`: Less than $20,000
   - `inc_20k_45k`: $20,000 to $44,999
   - `inc_45k_60k`: $45,000 to $59,999
   - `inc_60k_75k`: $60,000 to $74,999
   - `inc_75k_100k`: $75,000 to $99,999
   - `inc_100k_150k`: $100,000 to $149,999
   - `inc_150k_200k`: $150,000 to $199,999
   - `inc_200k_plus`: $200,000 or more

   **Age Distribution**:
   - `pers_age_00_19`: Children and young adults (0-19 years)
   - `pers_age_20_34`: Young adults (20-34 years)
   - `pers_age_35_64`: Middle-aged adults (35-64 years)
   - `pers_age_65_plus`: Seniors (65+ years)

   **Worker Categories**:
   - `hh_wrks_0`: Households with no workers
   - `hh_wrks_1`: Households with one worker
   - `hh_wrks_2`: Households with two workers
   - `hh_wrks_3_plus`: Households with three or more workers

### County Level

Counties provide the regional context for labor market analysis, covering the 9-county Bay Area region.

#### County Control Generation:

**Occupation Categories** (based on ACS occupation classification):

- **Management/Professional** (`pers_occ_management`): 
  - Management, business, and financial operations
  - Includes executives, managers, financial analysts, accountants
  
- **Professional/Technical** (`pers_occ_professional`):
  - Professional and related occupations
  - Includes engineers, teachers, healthcare professionals, lawyers
  
- **Service Workers** (`pers_occ_services`):
  - Service occupations
  - Includes food service, personal care, protective services, building maintenance
  
- **Sales and Office** (`pers_occ_retail`):
  - Sales and office occupations
  - Includes retail salespersons, cashiers, administrative support
  
- **Manual/Production** (`pers_occ_manual_military`):
  - Production, transportation, and material moving
  - Combined with military occupations due to small numbers

---

## Scaling Methodologies

The Bay Area PopulationSim model employs sophisticated scaling methodologies to ensure controls reflect current conditions while maintaining internal consistency.

### Regional ACS Scaling (TAZ Household Categories)

#### Purpose and Methodology

TAZ-level household controls are scaled to match ACS 2023 1-year regional totals, ensuring that synthetic households reflect the most current demographic conditions.

**Target**: 3,031,788 total households (ACS 2023 1-year estimate for 9-county region)

#### Scaling Process:

1. **Category Total Calculation**: Sum all TAZ controls within each category
   ```
   Example - Household Size:
   Original totals: hh_size_1=794,695 + hh_size_2=978,628 + ... = 3,039,990
   Target total: 3,031,788 (from ACS 1-year)
   Scaling factor: 3,031,788 ÷ 3,039,990 = 0.997302
   ```

2. **Proportional Scaling**: Apply scaling factor to preserve relative distributions
   ```
   Scaled values:
   hh_size_1: 794,695 × 0.997302 = 792,933
   hh_size_2: 978,628 × 0.997302 = 976,292
   ```

3. **Integer Rounding**: Convert to whole households while maintaining totals

#### Categories Scaled:
- **Household Income**: 8 income brackets scaled to regional household total
- **Household Size**: 6 size categories scaled to regional household total  
- **Household Workers**: 4 worker categories scaled to regional household total
- **Household Children**: 2 children categories (with/without) scaled to regional household total

### County Household Scaling (Person Occupation Controls)

#### Purpose and Innovation

County occupation controls use a novel scaling approach that leverages household growth patterns as a proxy for worker growth, based on the assumption that worker-to-household ratios by county remain relatively stable between 2020 and 2023.

#### Scaling Factor Derivation:

County household scaling factors are calculated by comparing 2020 Census to 2023 ACS household counts:

| County | 2020 Census HH | 2023 ACS HH | Scaling Factor |
|--------|----------------|-------------|----------------|
| Alameda | 591,636 | 646,309 | 1.0924 |
| Contra Costa | 407,029 | 432,056 | 1.0615 |
| Marin | 104,167 | 112,359 | 1.0786 |
| Napa | 49,738 | 56,046 | 1.1268 |
| San Francisco | 371,851 | 418,143 | 1.1245 |
| San Mateo | 269,417 | 288,325 | 1.0702 |
| Santa Clara | 656,063 | 703,922 | 1.0729 |
| Solano | 155,924 | 165,626 | 1.0622 |
| Sonoma | 187,701 | 209,002 | 1.1135 |

#### Application to Occupation Controls:

```python
# Example for Alameda County
original_management = 118,550
scaled_management = 118,550 × 1.0924 = 129,499
```

This approach recognizes that while we lack current occupation data at the county level, household growth patterns provide a reasonable proxy for economic and demographic change.

### Validation and Quality Control

#### Pre-Scaling Validation:
- **Category Consistency**: Ensure all household categories sum to similar totals
- **Geographic Coverage**: Verify all zones have reasonable control values
- **Historical Comparison**: Compare to previous model years for reasonableness

#### Post-Scaling Validation:
- **Target Achievement**: Verify scaled totals match ACS 1-year targets within 0.1%
- **Distribution Preservation**: Ensure scaling doesn't distort relative distributions
- **County Validation**: Confirm county totals align with expected demographic trends

---

## Quality Assurance and Validation

### Multi-Level Validation Framework

#### Level 1: Data Integrity Checks
- **Completeness**: Every geographic zone has controls for all required categories
- **Non-negativity**: No negative values in any control
- **Reasonableness**: Values fall within expected demographic ranges

#### Level 2: Geographic Consistency
- **Hierarchical Consistency**: MAZ totals aggregate properly to TAZ and county levels
- **Boundary Validation**: Controls respect geographic boundaries and relationships
- **Crosswalk Validation**: Geographic aggregations preserve total counts

#### Level 3: Temporal Consistency  
- **Trend Analysis**: Current values align with historical demographic trends
- **Growth Patterns**: Population and household growth follows expected patterns
- **Economic Indicators**: Occupation and income distributions reflect regional economy

#### Level 4: Cross-Category Validation
- **Internal Consistency**: Different household categories yield similar total household counts
- **Demographic Logic**: Age, income, and household size relationships are reasonable
- **Economic Logic**: Worker and occupation distributions align with local economy

### Error Detection and Resolution

#### Automated Quality Checks:
```python
# Example validation check
if abs(total_households_income - total_households_size) / total_households_income > 0.01:
    logger.warning(f"Household category totals differ by {pct_diff:.1f}%")
    apply_harmonization()
```

#### Manual Review Triggers:
- Geographic zones with unusually high or low control values
- Categories where scaling factors exceed ±20%
- Counties with occupation distributions that differ significantly from regional patterns

---

## Output Files and Structure

### Primary PopulationSim Input Files

#### MAZ Controls: `maz_marginals_hhgq.csv`
```csv
MAZ_NODE,numhh_gq,gq_type_univ,gq_type_noninst
10001,185,0,0
10002,221,0,3
10003,181,0,0
...
```

**Structure**:
- **Geographic Identifier**: `MAZ_NODE` (matches crosswalk files)
- **Household + GQ**: `numhh_gq` combines households and group quarters for person synthesis
- **GQ Categories**: Separate counts for university and other noninstitutional group quarters

#### TAZ Controls: `taz_marginals_hhgq.csv`
```csv
TAZ_NODE,inc_lt_20k,inc_20k_45k,inc_45k_60k,...,hh_size_1_gq
301001,23,45,31,...,156
301002,45,67,42,...,203
...
```

**Structure**:
- **Household Characteristics**: Income, size, workers, children categories
- **Person Characteristics**: Age distributions
- **HHGQ Integration**: `hh_size_1_gq` combines single-person households with group quarters

#### County Controls: `county_marginals.csv` 
```csv
COUNTY,pers_occ_management,pers_occ_professional,pers_occ_services,pers_occ_retail,pers_occ_manual_military
1,129499,378541,201345,123456,98765
2,94523,267834,145678,87654,76543
...
```

**Structure**:
- **Geographic Identifier**: `COUNTY` (1-9 for Bay Area counties)
- **Occupation Categories**: Worker counts by major occupation group
- **Scaled Values**: Adjusted using county household scaling factors

### Supporting Files

#### Geographic Crosswalk: `geo_cross_walk_tm2_maz.csv`
Essential for linking different geographic levels:
```csv
MAZ_NODE,TAZ_NODE,COUNTY,county_name,PUMA
333453,301054,1,Alameda,112
334567,301055,1,Alameda,112
...
```

#### Validation Files

**County Summary: `county_summary_2020_2023.csv`**
Documents scaling factors and validation statistics:
```csv
county_fips,county_name,hh_2020_census,hh_2023_acs,scaling_factor
001,Alameda,591636,646309,1.0924
013,Contra Costa,407029,432056,1.0615
...
```

**County Targets: `county_targets_2023.csv`**
Regional validation targets:
```csv
geography,variable,total
regional,households,3031788
regional,population,7508799
001,households,646309
...
```

---

## Technical Implementation

### System Architecture

#### Modular Design
The control generation system is built with modular components:

- **Data Acquisition Module**: Handles Census API interactions and caching
- **Geographic Processing Module**: Manages interpolation and aggregation
- **Scaling Module**: Implements regional and county scaling methodologies  
- **Validation Module**: Performs quality assurance checks
- **Output Module**: Generates final control files

#### Configuration-Driven Processing
All control definitions are specified in configuration files:

```python
# Example from unified_tm2_config.py
HOUSEHOLD_INCOME_CONTROLS = {
    'inc_lt_20k': {'min': 0, 'max': 19999},
    'inc_20k_45k': {'min': 20000, 'max': 44999},
    # ... additional categories
}
```

#### Error Handling and Logging
Comprehensive logging tracks every step:
- Data download and caching operations
- Geographic processing and validation
- Scaling calculations and results
- Quality assurance outcomes

### Performance Optimizations

#### Caching Strategy
- **Census Data**: Downloaded once and cached locally
- **Geographic Crosswalks**: Processed once and reused
- **Intermediate Results**: Cached for debugging and reprocessing

#### Parallel Processing  
Where possible, the system uses parallel processing:
- Multiple geographic zones processed simultaneously
- Independent control categories calculated in parallel
- Validation checks run concurrently

### Future Enhancements

#### Planned Improvements
- **Dynamic Scaling**: Ability to incorporate new data sources automatically
- **Machine Learning Integration**: Use ML to improve interpolation accuracy
- **Real-time Validation**: Continuous quality monitoring during processing
- **Enhanced Visualization**: Better tools for examining control distributions

#### Research Opportunities
- **Alternative Scaling Methods**: Explore other approaches to temporal scaling
- **Uncertainty Quantification**: Better understanding of control accuracy
- **Behavioral Integration**: Incorporate behavioral data into control generation

---

## Conclusion

The Bay Area PopulationSim control generation system represents a sophisticated approach to creating statistical targets for synthetic population generation. By integrating multiple Census data sources, employing advanced geographic processing, and implementing rigorous quality controls, the system produces high-quality controls that accurately reflect the Bay Area's complex demographic and economic landscape.

The system's strength lies in its ability to balance accuracy, currency, and geographic detail while maintaining internal consistency across multiple levels of geography and demographic categories. The innovative county scaling methodology demonstrates how creative approaches can overcome data limitations to produce more accurate models.

As the Bay Area continues to evolve rapidly, this robust control generation framework provides the foundation for synthetic populations that can accurately represent the region's diverse communities and support informed planning and policy decisions.

---

*For technical details on running the control generation system, see [CONTROL_GENERATION.md](CONTROL_GENERATION.md). For environment setup, see [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md).*

