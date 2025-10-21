# Population Synthesis for Regional Travel Modeling
*Regional Model Working Group Presentation Notes*

## What is Population Synthesis?

Population synthesis is the process of creating a disaggregate synthetic population that matches known aggregate demographic and socioeconomic characteristics at multiple geographic levels. For travel modeling, we need individual households and persons with detailed attributes to feed into activity-based models.

### Why Do We Need It?
- **Privacy Protection**: Census provides aggregate data, not individual records
- **Geographic Precision**: Need household-level data at small geographies (MAZ/TAZ level)
- **Model Requirements**: Activity-based models require individual agents with full demographic profiles
- **Policy Analysis**: Evaluate impacts on specific population segments

### Key Challenge
Create realistic individuals and households that:
- Match Census aggregate controls at multiple geographic levels
- Preserve realistic demographic relationships and correlations
- Provide sufficient sample size for small-area analysis

## PopulationSim Overview

PopulationSim is an open-source population synthesis tool developed by RSG for regional transportation planning. It uses **Iterative Proportional Fitting (IPF)** and **Combinatorial Optimization** to create synthetic populations.

### Core Architecture
- **Two-Stage Process**: First synthesize households, then assign persons
- **Multi-Geographic Fitting**: Simultaneously fits controls at PUMA, County, TAZ, and MAZ levels
- **Probabilistic Selection**: Uses weights to randomly draw from seed population

## The Population Synthesis Process

### Step 1: Seed Population Preparation
**What it is:** Representative sample of households and persons from American Community Survey Public Use Microdata Sample (ACS PUMS)

**Key Characteristics:**
- Real demographic relationships preserved
- Geographic detail at PUMA level (100,000+ population areas)
- Full attribute detail for all household and person characteristics

*[Analysis Space: Seed Population Composition]*
- Distribution of household sizes, incomes, age structures
- Geographic coverage and representativeness
- Adequacy for rare demographic combinations

### Step 2: Control Total Development  
**What it is:** Aggregate demographic targets from Census/ACS at multiple geographic levels

**Control Categories:**
- **Household Controls**: Total households, household size, income, presence of children
- **Person Controls**: Age groups, race/ethnicity, worker status
- **Geographic Constraints**: Population and household totals by geography

*[Analysis Space: Control Total Patterns]*
- Spatial distribution of demographic characteristics
- Control total maps showing demographic concentrations
- Cross-geographic consistency validation

### Step 3: Geographic Crosswalk
**What it is:** Mapping between Census geographies (PUMA) and model geographies (TAZ/MAZ)

**Critical Function:**
- Distributes PUMA-level seed records to smaller geographies
- Maintains demographic realism while achieving geographic precision
- Handles split PUMAs across multiple model zones

*[Analysis Space: Geographic Distribution]*
- PUMA to TAZ/MAZ allocation patterns
- Geographic fragmentation analysis
- Cross-boundary demographic flows

### Step 4: Iterative Proportional Fitting (IPF)
**What it is:** Statistical process that adjusts household weights to match control totals

**Algorithm:**
1. Start with equal weights for all seed households
2. Iteratively adjust weights to match each control category
3. Repeat until convergence or maximum iterations reached
4. Balance competing demographic constraints

*[Analysis Space: Convergence Analysis]*
- Control fitting quality by geography and demographic category
- Convergence diagnostics and constraint trade-offs
- Areas with challenging demographic combinations

### Step 5: Household Selection and Expansion
**What it is:** Random draw of households from weighted seed population

**Process:**
- Use IPF weights as selection probabilities
- Draw households to match target household totals
- Assign unique IDs and geographic locations
- Preserve household-person relationships

*[Analysis Space: Selection Quality]*
- How well synthetic households match intended distributions
- Preservation of demographic correlations
- Geographic assignment validation

### Step 6: Group Quarters (GQ) Integration
**What it is:** Special handling for non-household population (college dorms, military barracks, nursing homes)

**Our Approach:**
- **Person-as-Household**: Treat each GQ person as a one-person household
- Separate controls for institutional vs non-institutional GQ
- Integration with household synthesis for complete population coverage

*[Analysis Space: GQ Population Characteristics]*
- GQ population distribution and facility locations
- Integration quality with household population
- Special demographic characteristics of GQ residents

## Specific Design Choices for Bay Area

### Person-as-Household GQ Architecture
- Each group quarters person becomes a synthetic "household" of size 1
- Maintains individual-level detail for travel modeling
- Allows standard PopulationSim algorithms to handle GQ population

### Control Hierarchy and Importance Weights
- **Geographic Controls**: Highest importance (maintain spatial precision)
- **Demographic Controls**: Moderate importance (allow flexibility for convergence)
- **Detailed Categories**: Lower importance (preserve overall patterns while allowing local variation)

### Geographic Resolution
- **Primary**: PUMA → TAZ → MAZ allocation
- **Secondary**: County and regional consistency checks
- **Target**: ~150,000 households across 1,454 TAZs and 4,688 MAZs

*[Analysis Space: Design Choice Impacts]*
- Trade-offs between geographic precision and demographic accuracy
- Sensitivity to importance weight settings
- Convergence patterns by area type (urban/suburban/rural)

## Synthetic Population Analysis Framework

### High-Level Population Validation
*[Analysis Space: Regional Demographics]*
- Population totals and distributions by major demographic categories
- Comparison with Census estimates and trends
- Regional demographic patterns and spatial clustering

### Geographic Distribution Analysis  
*[Analysis Space: Spatial Patterns]*
- Population density maps and distributions
- Demographic clustering by geography type
- Transportation-relevant spatial patterns (workers, seniors, families)

### Demographic Realism Assessment
*[Analysis Space: Correlation Preservation]*
- Household size vs income relationships
- Age structure within households
- Worker status and commute patterns
- Comparison with observed survey data

## What the Synthetic Population Really Means

### Individual Level Reality
The synthetic population represents **realistic but artificial** individuals and households:

**Example Household Profile:**
- Household ID: 12847
- Location: TAZ 432, MAZ 1823 (Downtown Oakland)
- Household: 2 adults, 1 child, $95,000 income, rent apartment
- Person 1: 34-year-old female, college graduate, works full-time
- Person 2: 36-year-old male, college graduate, works full-time  
- Person 3: 8-year-old child, attends school

*[Analysis Space: Individual Stories]*
- Sample household profiles across different demographics
- Person-level attribute distributions and combinations
- Household formation patterns and lifecycle representation

### Disaggregate Applications
**For Travel Modeling:**
- Each synthetic person generates daily activity patterns
- Household interactions (joint trips, car allocation)
- Demographics drive trip generation and mode choice

**For Policy Analysis:**
- Equity analysis by income and race/ethnicity
- Transit accessibility by demographic group
- Environmental justice assessments

*[Analysis Space: Policy Applications]*
- Demographic targeting for transportation investments
- Equity impacts of pricing and service changes
- Access to opportunities by population segments

## Presentation Structure for Working Group

### Part 1: Technical Overview (15 minutes)
- PopulationSim concept and methodology
- Bay Area implementation approach
- Data sources and processing steps

### Part 2: Process Deep-Dive (20 minutes)
- Step-by-step walkthrough with analysis
- Control development and validation
- Convergence analysis and quality assessment

### Part 3: Synthetic Population Analysis (20 minutes)
- Regional demographic patterns
- Geographic distribution validation
- Individual-level realism demonstration

### Part 4: Applications and Next Steps (5 minutes)
- Travel model integration
- Policy analysis capabilities
- Future enhancements and collaboration

---

*Document framework prepared for Regional Model Working Group presentation - October 20, 2025*