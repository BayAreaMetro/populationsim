# TM2 PopulationSim Process Overview

## What is PopulationSim?

PopulationSim is a synthetic population generator that creates realistic household and person records for transportation modeling. The TM2 (Travel Model 2) pipeline synthesizes a population for the 9-county San Francisco Bay Area.

## Overall Process Flow

```
PUMS Data → Geographic Crosswalk → Seed Population → Marginal Controls → PopulationSim → Synthetic Population
```

### 1. Data Inputs
- **PUMS (Public Use Microdata Sample)**: Real anonymized household/person records from US Census
- **Geographic Definitions**: MAZ (Micro Analysis Zones), TAZ (Traffic Analysis Zones), PUMA (Public Use Microdata Areas)
- **Marginal Controls**: Target totals by geography (households by income, persons by age, etc.)

### 2. Geographic Framework
- **Region**: 9-county San Francisco Bay Area
- **Counties**: Sequential numbering 1-9 (SF=1, San Mateo=2, Santa Clara=3, Alameda=4, Contra Costa=5, Solano=6, Napa=7, Sonoma=8, Marin=9)
- **Zones**: ~1,400 TAZs containing ~2,000 MAZs
- **PUMAs**: 104 Public Use Microdata Areas covering the region

## Step-by-Step Process

### Step 1: PUMS Data Download
**Purpose**: Obtain raw household and person microdata from US Census
**Input**: Census API or cached files
**Output**: 
- `households_2023_raw.csv` (~175k Bay Area households)
- `persons_2023_raw.csv` (~400k Bay Area persons)

**What happens**:
- Downloads 2023 5-year American Community Survey PUMS data
- Filters to Bay Area PUMAs only
- Adds inflation adjustment (2023 to 2010 dollars)
- Adds unique identifiers and crosswalk fields

### Step 2: Geographic Crosswalk Creation
**Purpose**: Link geographic zones (MAZ-TAZ-PUMA-County) for population synthesis
**Input**: 
- TM2 zone definition files (`blocks_mazs_tazs.csv`, `mazs_tazs_all_geog.csv`)
- County mapping configuration
**Output**: `geo_cross_walk_tm2_updated.csv`

**What happens**:
- Creates MAZ-to-TAZ-to-PUMA-to-County relationships
- Resolves conflicts (TAZs split across PUMAs)
- Converts FIPS county codes to sequential 1-9 system
- Validates all geographic relationships

### Step 3: Seed Population Generation  
**Purpose**: Process PUMS data into PopulationSim-ready format
**Input**:
- Raw PUMS households/persons files
- Geographic crosswalk
- Income inflation factors
**Output**:
- `seed_households.csv` (households with geographic assignments)
- `seed_persons.csv` (persons linked to households)

**What happens**:
- Assigns households to PUMAs based on their original PUMA
- Links persons to households via unique household IDs
- Applies income inflation from 2023 to 2010 dollars
- Creates PopulationSim-compatible field names and formats
- Handles Group Quarters (GQ) population specially

### Step 4: Marginal Controls Generation
**Purpose**: Create target totals that synthetic population must match
**Input**:
- Census API data (ACS tables)
- Geographic crosswalk
- Control specifications (`controls.csv`)
**Output**:
- `maz_marginals.csv` (MAZ-level targets)
- `taz_marginals.csv` (TAZ-level targets)  
- `county_marginals.csv` (County-level targets)

**What happens**:
- Downloads Census data for all control variables
- Aggregates to appropriate geographic levels
- Handles Group Quarters controls separately
- Creates age-income cross-tabulations
- Ensures control totals are consistent across geographies

### Step 5: PopulationSim Synthesis
**Purpose**: Generate synthetic population matching marginal controls
**Input**:
- Seed households and persons
- Marginal controls at all geographic levels
- PopulationSim configuration files
**Output**:
- `synthetic_households.csv` (final synthetic households)
- `synthetic_persons.csv` (final synthetic persons)
- County summary tables

**What happens**:
- **Balancing**: Adjusts seed population weights to match controls
- **Integerization**: Converts fractional weights to whole households
- **Assignment**: Places households into specific MAZs
- Uses iterative proportional fitting (IPF) algorithm
- Handles multiple geographic levels simultaneously

## Key Algorithms

### Geographic Assignment
1. **PUMA Assignment**: Households stay in their original PUMA
2. **County Assignment**: Based on PUMA-to-county crosswalk
3. **TAZ/MAZ Assignment**: PopulationSim chooses based on controls

### Control Balancing
1. **IPF (Iterative Proportional Fitting)**: Adjusts weights to match marginals
2. **Multi-level convergence**: Ensures consistency across MAZ/TAZ/County
3. **Constraint handling**: Respects geographic and demographic relationships

### Group Quarters Handling
1. **Separate processing**: GQ population handled independently
2. **Institutional split**: University vs. other institutional
3. **MAZ assignment**: Based on special GQ controls

## Data Quality Measures

### Validation Checks
- **Control totals**: Synthetic population matches marginal targets within tolerance
- **Geographic consistency**: All households properly assigned to valid MAZs
- **Demographic realism**: Age/income distributions match Census patterns
- **Household composition**: Realistic household sizes and types

### Key Metrics
- **Convergence**: IPF algorithm convergence to target tolerances
- **Assignment rates**: Percentage of households successfully assigned
- **Control fit**: How closely synthetic matches target marginals
- **Geographic coverage**: All MAZs receive appropriate population

## Technology Stack

### Core Software
- **PopulationSim**: Synthetic population generation engine
- **ActivitySim**: Framework for population synthesis and modeling  
- **Python**: Primary programming language
- **Pandas**: Data manipulation and analysis

### Data Sources
- **US Census Bureau**: PUMS microdata and ACS marginal data
- **Census API**: Automated data download
- **TM2 Model**: Geographic zone definitions
- **MTC/ABAG**: Regional planning agency data

## Output Uses

The synthetic population is used for:
- **Travel demand modeling**: Input to Travel Model 2 (TM2)
- **Transportation planning**: Regional transportation projects
- **Policy analysis**: Impact assessment of transportation policies
- **Scenario planning**: Future year population forecasts

## Quality Assurance

### Automated Validation
- Control total verification
- Geographic consistency checks
- Data type and range validation
- Cross-tabulation comparisons with Census

### Manual Review
- County-level summary comparisons
- Age/income distribution review
- Household size and composition analysis
- Geographic distribution patterns
