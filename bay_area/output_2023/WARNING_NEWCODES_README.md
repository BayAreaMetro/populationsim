# WARNING: New PUMS Recodes and Data Handling (2023+)

This file documents important changes and caveats regarding the recoding and processing of synthetic population data using the new (2023+) PUMS data and refactored pipeline scripts.

## Key Recodes and Changes

- **Person Type and Student Status**: The logic for `person_type` and `student_status` has been harmonized with legacy (TM1) definitions, but is now based on updated PUMS fields and codes. See the pipeline code for details.
- **Employment and Occupation**: Employment status and occupation categories are recoded using updated PUMS codes. Some categories may not align perfectly with previous model versions.
- **Group Quarters**: Group quarters types are assigned using new logic to match PopulationSim and Bay Area modeling needs, but may differ from previous approaches.
- **NaN/inf Handling**: Households and persons with missing or infinite values in key fields (HINCP, ADJINC, VEH) are dropped early in the pipeline. All other missing values are left as-is until postprocessing, where they are filled with -9 for compatibility.
- **Unique IDs**: Household and person IDs are generated using new, robust logic to ensure correct linkage and uniqueness.

## Cautions and Next Steps

- **Model Compatibility**: Some recoded fields may not match the exact expectations of downstream modeling tools. Additional validation and adjustment may be needed.
- **Data Quality**: The new pipeline is more transparent about missing or problematic data. If errors arise, investigate the logs and consider updating recoding logic or adding targeted data cleaning.
- **Ongoing Review**: As the 2023+ PUMS data and modeling requirements evolve, further changes to recoding logic and data handling may be necessary. Please review outputs and summary logs carefully.

---

## Reference: Required Output Codes for Synthetic Population

Below are the expected codes and value ranges for key columns in the synthetic population outputs, as required by the HouseholdDataManager and downstream modeling tools. Please ensure all recodes match these definitions.

### Households
| Column Name   | Description | Codes/Range |
|--------------|-------------|-------------|
| HHID         | Unique household ID | Integer |
| TAZ          | TAZ of residence | Integer |
| MAZ          | MAZ of residence | Integer |
| MTCCountyID  | County of residence | Integer |
| HHINCADJ     | Household income in 2010 dollars | Integer |
| NWRKRS_ESR   | Number of workers (EMPLOYED persons in household) | 0–20 |
| VEH          | Vehicles owned | 0–6 (6=6+), -9=N/A for GQ |
| NP           | Number of persons | 1–20 |
| HHT          | Household type | 1–7 (see below), -9=N/A for GQ |
| BLD          | Units in structure | 1–10 (see below), -9=N/A for GQ |
| TYPE         | Unit type | 1=Housing, 2=Institutional GQ (should not appear), 3=Noninstitutional GQ |

**HHT Codes:**
1=Married-couple family household
2=Other family, Male, no wife
3=Other family, Female, no husband
4=Nonfamily, Male, alone
5=Nonfamily, Male, not alone
6=Nonfamily, Female, alone
7=Nonfamily, Female, not alone
-9=N/A for GQ

**BLD Codes:**
1=Mobile home/trailer
2=One-family detached
3=One-family attached
4=2 Apartments
5=3-4 Apartments
6=5-9 Apartments
7=10-19 Apartments
8=20-49 Apartments
9=50+ Apartments
10=Boat, RV, van, etc.
-9=N/A for GQ

### Persons
| Column Name   | Description | Codes/Range |
|--------------|-------------|-------------|
| HHID         | Unique household ID | Integer |
| PERID        | Unique person ID | Integer |
| AGEP         | Age | 0–99 |
| SEX          | Sex | 1=Male, 2=Female |
| SCHL         | Education attainment | 1–16 (see below), -9=N/A for <3yo |
| OCCP         | Occupation | 1–6 (see below), -999=N/A |
| WKHP         | Usual hours worked/week | 1–99, -9=N/A |
| WKW          | Weeks worked/year | 1–6 (see below), -9=N/A |
| EMPLOYED     | 1=Employed (ESR in [1,2,4,5]), 0=Unemployed |
| ESR          | Employment status | 0–6 (see below) |
| SCHG         | Grade level attending | 1–7 (see below), -9=N/A |

**SCHL Codes:**
-9=N/A for <3yo
1=No schooling completed
2=Nursery to grade 4
3=Grade 5 or 6
4=Grade 7 or 8
5=Grade 9
6=Grade 10
7=Grade 11
8=12th grade, no diploma
9=High school graduate
10=Some college, <1 year
11=1+ years college, no degree
12=Associate's degree
13=Bachelor's degree
14=Master's degree
15=Professional degree
16=Doctorate degree

**OCCP Codes:**
-999=N/A
1=Management
2=Professional
3=Services
4=Retail
5=Manual
6=Military

**WKW Codes:**
-9=N/A
1=50–52 weeks
2=48–49 weeks
3=40–47 weeks
4=27–39 weeks
5=14–26 weeks
6=13 weeks or less

**ESR Codes:**
0=N/A (<16yo)
1=Civilian employed, at work
2=Civilian employed, not at work
3=Unemployed
4=Armed forces, at work
5=Armed forces, not at work
6=Not in labor force

**SCHG Codes:**
-9=N/A (not attending)
1=Nursery/preschool
2=Kindergarten
3=Grade 1–4
4=Grade 5–8
5=Grade 9–12
6=College undergrad
7=Graduate/professional school

---

## Code Review Note (August 2025)

The pipeline and this README have been reviewed for alignment with the required codes for all household and person fields. All fields match the expected codes and value ranges, except for WKW (weeks worked per year), which has now been updated to match the 1–6 codes as required:

- WKW: Now recoded in postprocess_recode.py so that all employed persons are assigned WKW=1 (50–52 weeks). N/A is -9. If more detailed data on weeks worked becomes available, further refinement can be added to assign codes 2–6 as appropriate.

All other fields (HHT, BLD, VEH, TYPE, SCHL, OCCP, WKHP, EMPLOYED, ESR, SCHG, etc.) are mapped and recoded as specified in the documentation above. NaN values are filled with -9 at the postprocessing step. Please review this file and the code for any future changes or additional validation needs.

For questions or to report issues, contact the pipeline maintainers or review the code in `create_seed_population_tm2_refactored.py` and `postprocess_recode.py`.
