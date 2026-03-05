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
- **Zones**: 5,117 TAZs, 41,434 MAZs
- **PUMAs**: 62 Public Use Microdata Areas covering the region

## Step-by-Step Process

### Step 1: PUMS Data Download
**Purpose**: Obtain raw household and person microdata from US Census
**Input**: Census API or cached files
**Output**: 
- `households_2023_raw.csv` (~150k Bay Area households)
- `persons_2023_raw.csv` (~375k Bay Area persons)

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
- Uses sequential county IDs (1-9) for all processing:
  - 1 = San Francisco, 2 = San Mateo, 3 = Santa Clara, 4 = Alameda
  - 5 = Contra Costa, 6 = Solano, 7 = Napa, 8 = Sonoma, 9 = Marin
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
- `controls_maz.csv` (MAZ-level targets: 4 household variables)
- `controls_taz.csv` (TAZ-level targets: 28 variables)  
- `controls_county.csv` (County-level targets: 5 occupation variables)

**What happens**:
- Downloads Census data for all control variables
- Aggregates to appropriate geographic levels
- Uses sequential COUNTY IDs (1-9) in all control files
- Handles Group Quarters controls separately at person level
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
- County, TAZ, and MAZ summary tables

**What happens**:
- **Balancing**: Adjusts seed population weights to match controls using IPF
- **Integerization**: Converts fractional weights to whole households
- **Assignment**: Places households into specific MAZs
- Operates hierarchically: County → TAZ → MAZ levels
- Converges to tolerances (rel_tolerance=0.2, abs_tolerance=100)
- Typical runtime: ~2-3 hours for full Bay Area

### Step 6: Postprocessing and Analysis
**Purpose**: Convert to TM2 format and validate results
**Input**:
- `synthetic_households.csv`, `synthetic_persons.csv`
**Output**:
- `households_2023_tm2.csv` (2.9M households in TM2 format)
- `persons_2023_tm2.csv` (7.6M persons in TM2 format)
- Analysis charts and validation reports

**What happens**:
- Recodes fields to TM2 specifications
- Runs comprehensive analysis suite (10 scripts):
  - Core analysis: MAZ/TAZ comparisons, full dataset analysis
  - Visualizations: County charts, TAZ charts, interactive dashboards
  - Validation: Data quality checks, population comparisons
- Generates interactive Plotly dashboards for exploration
- Output location: `output_2023/charts/`

## Key Algorithms

### Geographic Assignment
1. **PUMA Assignment**: Households stay in their original PUMA
2. **County Assignment**: Based on PUMA-to-county crosswalk
3. **TAZ/MAZ Assignment**: PopulationSim chooses based on controls

### Control Balancing
1. **IPF (Iterative Proportional Fitting)**: Adjusts weights to match marginals
2. **Multi-level convergence**: Ensures consistency across MAZ/TAZ/County
3. **Constraint handling**: Respects geographic and demographic relationships

### Group Quarters Handling (Updated October 2025)

**Important Approach Change**: PopulationSim now uses **person-level group quarters controls** that align directly with Census data structure.

1. **Person-level controls**: GQ controls count individuals, not households
   - `pers_gq_university`: University GQ persons (Census P5_008N)
   - `pers_gq_noninstitutional`: Military + other GQ persons (Census P5_009N+P5_011N+P5_012N)
2. **Selective institutional inclusion**: 
   - ✅ **INCLUDED**: University/college housing (dorms, student housing)
   - ✅ **INCLUDED**: Military barracks and base housing
   - ✅ **INCLUDED**: Other non-institutional group quarters (group homes, worker housing)
   - ❌ **EXCLUDED**: Nursing homes, prisons, mental health institutions
3. **Two-level structure**: 
   - Household level: `hhgqtype` (0=regular, 1=university, 2=noninstitutional)
   - Person level: `gq_type` (0=regular, 1=university, 2=noninstitutional)  
4. **Direct Census alignment**: Controls use Census person counts without household-level conversion
5. **Travel behavior**: Non-institutional GQ residents participate in regular travel patterns

**Rationale**: Person-level controls eliminate conversion assumptions and ensure direct data consistency with Census P5 series tables while maintaining travel modeling utility.

## Data Quality Measures

### Validation Checks
- **Control totals**: Synthetic population matches marginal targets within tolerance
- **Geographic consistency**: All households properly assigned to valid MAZs
- **Demographic realism**: Age/income distributions match Census patterns
- **Household composition**: Realistic household sizes and types

### Key Metrics
- **Convergence**: IPF algorithm reaches target tolerances (±20% relative, ±100 absolute)
- **Assignment rates**: 100% of households successfully assigned to MAZs
- **Control fit**: Synthetic population matches controls within specified tolerances
- **Geographic coverage**: All 41,434 MAZs receive appropriate population
- **Scale**: 2.9M households, 7.6M persons across 9 counties

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



## Quality Assurance

### Automated Validation (run_all_summaries.py)
The pipeline includes 10 automated analysis scripts:

**Core Analysis:**
- MAZ household comparison against controls
- Full dataset statistical analysis
- TAZ-level control vs result comparison
- Synthetic population cross-tabulations

**Visualizations:**
- County-level summary charts
- TAZ control analysis charts  
- Interactive Plotly dashboards (28 variables)

**Validation:**
- MAZ household summaries
- Synthetic vs seed population comparisons
- Data quality and consistency checks

### Key Validation Metrics
- Control total verification (within ±20% tolerance)
- Geographic consistency (all households in valid MAZs)
- Data type and range validation
- Cross-tabulation comparisons with Census
- Age/income distribution alignment
- Household size and composition realism


