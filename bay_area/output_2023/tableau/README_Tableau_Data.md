# PopulationSim Data for Tableau

This directory contains PopulationSim data prepared for Tableau analysis with standardized join fields.

## Files Overview

### Geographic Boundaries
- `taz_boundaries_tableau.shp` - TAZ (Traffic Analysis Zone) boundaries
- `puma_boundaries_tableau.shp` - PUMA (Public Use Microdata Area) boundaries

### Control Data  
- `taz_marginals_tableau.csv` - Population control totals by TAZ
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
- Coordinate reference system: [as original shapefiles]

## Usage Tips

1. Import shapefiles first to establish spatial context
2. Use geo_crosswalk_tableau.csv as the central linking table
3. Filter data by COUNTY_NAME for sub-regional analysis
4. Aggregate MAZ data to TAZ level using geo_crosswalk relationships

Generated on: 2025-07-29 16:47:50
PopulationSim Version: TM2