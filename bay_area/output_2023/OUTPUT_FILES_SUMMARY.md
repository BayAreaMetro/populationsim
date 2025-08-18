# PopulationSim TM2 Output File Analysis
Generated on: 2025-08-17 09:53:08

## Households Analysis

**File Comparison:**
- Preprocessed: `synthetic_households.csv` - 3,210,365 households
- Postprocessed: `households_2023_tm2.csv` - 3,210,365 households
- Row count change: +0 households

**Column Mapping:**
| Preprocessed Column | Postprocessed Column | Description |
|---------------------|---------------------|-------------|
| unique_hh_id | HHID | Unique Household ID |
| TAZ | TAZ | Travel Analysis Zone |
| MAZ | MAZ | Model Analysis Zone |
| HINCP | HHINCADJ | Household Income (dollars) |
| NP | NP | Number of Persons in Household |
| VEH | VEH | Number of Vehicles |
| TEN | TEN | Tenure (Own/Rent) |
| HHT | HHT | Household/Family Type |
| BLD | BLD | Units in Structure |
| TYPEHUGQ | TYPE | Type of Unit (Housing/Group Quarters) |

**New columns in postprocessed file:**
- `NWRKRS_ESR`: Number of Workers (Employment Status)

**Columns removed in postprocessing:**
- `ACR`: No description
- `ADJINC`: No description
- `HUPAC`: No description
- `NPF`: No description
- `PUMA`: Public Use Microdata Area
- `SERIALNO`: Census Serial Number
- `WGTP`: No description
- `hh_income_2010`: No description
- `hh_income_2023`: No description
- `hh_workers_from_esr`: No description
- `hhgqtype`: Household/Group Quarters Type (0=HH, 1=Univ, 2=Military, 3=Other)
- `integer_weight`: Integer Weight from PopulationSim

### Detailed Household Column Analysis
*Based on 50,000 row samples*

#### Model Analysis Zone
**Preprocessed (`MAZ`):**
- Range: 310024.0 to 334484.0
- Mean: 320186.59, Median: 318377.00
- Unique values: 589
**Postprocessed (`MAZ`):**
- Range: 310024.0 to 334484.0
- Mean: 320186.59, Median: 318377.00
- Unique values: 589

#### Travel Analysis Zone
**Preprocessed (`TAZ`):**
- Range: 300002.0 to 300699.0
- Mean: 300354.09, Median: 300437.00
- Unique values: 69
**Postprocessed (`TAZ`):**
- Range: 300002.0 to 300699.0
- Mean: 300354.09, Median: 300437.00
- Unique values: 69

#### Household/Group Quarters Type (0=HH, 1=Univ, 2=Military, 3=Other)
**Preprocessed (`hhgqtype`):**
- Range: 0.0 to 3.0
- Mean: 0.19, Median: 0.00
- Unique values: 3

#### Number of Persons in Household
**Preprocessed (`NP`):**
- Range: 1.0 to 11.0
- Mean: 2.03, Median: 2.00
- Unique values: 9
**Postprocessed (`NP`):**
- Range: 1.0 to 11.0
- Mean: 2.03, Median: 2.00
- Unique values: 9

#### Number of Vehicles
**Preprocessed (`VEH`):**
- Range: 0.0 to 6.0
- Mean: 1.09, Median: 1.00
- Unique values: 7
**Postprocessed (`VEH`):**
- Range: 0.0 to 6.0
- Mean: 1.09, Median: 1.00
- Unique values: 7

## Persons Analysis

**File Comparison:**
- Preprocessed: `synthetic_persons.csv` - 7,834,673 persons
- Postprocessed: `persons_2023_tm2.csv` - 7,834,673 persons
- Row count change: +0 persons

**Column Mapping:**
| Preprocessed Column | Postprocessed Column | Description |
|---------------------|---------------------|-------------|
| unique_hh_id | HHID | Unique Household ID |
| AGEP | AGEP | Age |
| SEX | SEX | Sex (1=Male, 2=Female) |
| SCHL | SCHL | Educational Attainment |
| occupation | OCCP | Occupation Category |
| WKHP | WKHP | Usual Hours Worked Per Week |
| employed | EMPLOYED | Employed Flag (0/1) |
| ESR | ESR | Employment Status Recode |
| SCHG | SCHG | Grade Level Attending |
| hhgqtype | hhgqtype | Household/Group Quarters Type (0=HH, 1=Univ, 2=Military, 3=Other) |
| person_type | person_type | Person Type Category |

## Key Statistics
*Based on complete datasets - all 3,210,365 households and 7,834,673 persons*

### Age Distribution (Persons)
- 0-4: 381,941 (4.9%)
- 5-17: 1,159,186 (14.8%)
- 18-24: 561,958 (7.2%)
- 25-34: 1,238,432 (15.8%)
- 35-44: 1,212,607 (15.5%)
- 45-54: 1,059,884 (13.5%)
- 55-64: 924,297 (11.8%)
- 65-74: 746,423 (9.5%)
- 75+: 549,945 (7.0%)

### Vehicle Ownership (Households)
- 0 vehicles: 515,414 (16.1%)
- 1 vehicle: 958,802 (29.9%)
- 2 vehicles: 1,069,065 (33.3%)
- 3 vehicles: 428,664 (13.4%)
- 4 vehicles: 155,913 (4.9%)
- 5 vehicles: 52,496 (1.6%)
- 6 vehicles: 30,011 (0.9%)

### Household Size Distribution
- 1 person: 883,421 (27.5%)
- 2 persons: 1,034,162 (32.2%)
- 3 persons: 530,045 (16.5%)
- 4 persons: 615,089 (19.2%)
- 5+ persons: 147,648 (4.6%)
