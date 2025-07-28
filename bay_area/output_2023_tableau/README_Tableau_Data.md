# PopulationSim Data for Tableau

This directory contains PopulationSim data prepared for Tableau analysis with standardized join fields.

## Files Overview

### Geographic Boundaries
- `taz_boundaries_tableau.shp` - TAZ (Traffic Analysis Zone) boundaries
- `puma_boundaries_tableau.shp` - PUMA (Public Use Microdata Area) boundaries

### Control Data  
- `taz_marginals_tableau.csv` - Population control totals by TAZ with 2015-2023 comparison
- `maz_marginals_tableau.csv` - Population control totals by MAZ (Micro Analysis Zone)

### Geographic Relationships
- `geo_crosswalk_tableau.csv` - Mapping between MAZ, TAZ, COUNTY, and PUMA geographies

## Standardized Join Fields

All files use consistent field naming and data types for seamless joins:

### TAZ Data
- **TAZ_ID** (Integer) - Traffic Analysis Zone identifier
- Used in: taz_boundaries_tableau.shp, taz_marginals_tableau.csv, geo_crosswalk_tableau.csv

### MAZ Data  
- **MAZ_ID** (Integer) - Micro Analysis Zone identifier
- Used in: maz_marginals_tableau.csv, geo_crosswalk_tableau.csv

### PUMA Data
- **PUMA_ID** (String) - 5-character PUMA code (e.g., "01301")
- **PUMA_ID_INT** (Integer) - PUMA code as integer (e.g., 1301)
- Used in: puma_boundaries_tableau.shp, geo_crosswalk_tableau.csv

### County Data
- **COUNTY_ID** (Integer) - County FIPS code
- **COUNTY_NAME** (String) - County name
- Used in: geo_crosswalk_tableau.csv

## Recommended Tableau Joins

1. **TAZ Analysis**: Join taz_boundaries_tableau.shp with taz_marginals_tableau.csv on TAZ_ID
2. **PUMA Analysis**: Join puma_boundaries_tableau.shp with geo_crosswalk_tableau.csv on PUMA_ID_INT
3. **Cross-Geography Analysis**: Use geo_crosswalk_tableau.csv to aggregate between geography levels

## Data Quality Notes

- All geographic ID fields are validated and cleaned
- Numeric control data is properly typed (integers for counts, floats for rates)
- Missing values are preserved for transparency

## 2015-2023 Comparison Features

The TAZ marginals file includes comprehensive comparison between 2015 and 2023 control data:

### Column Structure
- **2023 data**: Current year control totals (19 columns)
- **2015 data**: Historical baseline with "_2015" suffix (14 columns) 
- **Difference columns**: Change from 2015 to 2023 with "_2023-2015_diff" suffix (14 columns)

### Key Comparisons Available
- **Income Distribution**: Changes in household income brackets
- **Age Demographics**: Population shifts across age groups
- **Household Composition**: Changes in household size and worker patterns
- **Children Presence**: Households with/without children

### Sample Regional Trends (2015→2023)
- High-income households (>$100K): **+86.3%** (+641,851 households)
- Low-income households (<$30K): **-34.4%** (-242,804 households) 
- Senior population (65+): **+32.9%** (+310,250 persons)
- Youth population (0-19): **-10.4%** (-197,804 persons)

### Tableau Analysis Tips
- Use difference columns to identify areas of significant change
- Join with TAZ boundaries to map demographic shifts spatially
- Filter by large positive/negative differences to find growth/decline hotspots
- Create calculated fields for percentage changes: `[field_2023-2015_diff] / [field_2015]`
- Coordinate reference system: [as original shapefiles]

## Usage Tips

1. Import shapefiles first to establish spatial context
2. Use geo_crosswalk_tableau.csv as the central linking table
3. Filter data by COUNTY_NAME for sub-regional analysis
4. Aggregate MAZ data to TAZ level using geo_crosswalk relationships

Generated on: 2025-07-26 09:14:58
PopulationSim Version: TM2