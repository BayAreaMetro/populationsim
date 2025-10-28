TM2 Input Fields — Seed and Synthetic Files

Purpose

This file documents the canonical input (seed) and synthetic output CSV field names and short descriptions. It is intended as a quick reference for engineers and modelers who need to map fields to PopulationSim or TM2 loader expectations.

1) Seed files (produced by `create_seed_population`)

- `seed_households.csv` (common fields expected)
  - HHID / unique_hh_id: Unique household identifier (string/int) – primary key linking to persons
  - PUMA: PUMA code for seed household origin (2020 PUMA)
  - SERIALNO: Original PUMS household serial number (keeps traceability)
  - WGTP: PUMS weight (float)
  - ADJINC / HHINCADJ: Household income adjusted to 2010 dollars (int/float)
  - hh_income_2023: original PUMS reported household income in 2023$
  - hh_income_2010: CPI-adjusted household income in 2010$
  - NP / NPERS: Number of persons in household
  - VEH: Number of vehicles
  - HHT: Household type code (PUMS-derived)
  - BLD: Units-in-structure code
  - TYPE / TYPEHUGQ: Unit type (1 = housing unit, 2 = institutional GQ, 3 = non-institutional GQ)
  - NWRKRS_ESR / hh_workers_from_esr: Number of workers derived from persons
  - TEN: Tenure (owner/renter)
  - hhgqtype: group quarters type indicator (0 = housing unit, >0 GQ categories)
  - integer_weight or initial_weight: seed weight used by PopulationSim (may be fractional before balancing)

- `seed_persons.csv` (common fields expected)
  - PERID / unique person id: Unique person identifier within household
  - HHID / unique_hh_id: Link to household
  - SERIALNO: PUMS household serial number
  - SPORDER: Person order in household
  - PWGTP / PWGTP: person weight
  - AGEP / AGE: age in years
  - SEX: Sex (1=Male,2=Female)
  - ESR / EMPLOYED: employment status
  - SCHL / SCHG: educational attainment codes
  - OCCP: occupation code (recoded to OCCP categories used in TM2)
  - WKHP: usual hours worked per week
  - WKW / WKWN: weeks worked code
  - HISP: Hispanic origin indicator
  - PINCP: personal income (if present)
  - person_type: derived person classification used by CT-RAMP
  - hhgqtype: group quarters indicator to match household GQ handling

Notes
- Seed files are created programmatically; field names and exact columns depend on the seed script used (`create_seed_population_tm2_refactored.py` vs `create_seed_population.py`). The fields above are the canonical expected names; check your seed CSV header for exact names.

2) Final synthetic files (PopulationSim outputs)

We extracted exact headers from the final `synthetic_households.csv` and `synthetic_persons.csv` produced by the latest run — see `docs/sample_synthetic_households.csv` and `docs/sample_synthetic_persons.csv` (also embedded in the main TM2 outputs doc). The canonical column lists and descriptions are below.

- `synthetic_households.csv` (header from current outputs)
  - unique_hh_id: unique key for household (used in TM2 loaders)
  - PUMA: PUMA origin
  - TAZ_NODE: assigned TAZ
  - MAZ_NODE: assigned MAZ
  - integer_weight: integerized household count (final weight used as count of identical households)
  - SERIALNO: PUMS SERIALNO for traceability
  - ADJINC: adjusted income (raw field name variation exists)
  - WGTP: PUMS weight
  - NP: number of persons
  - TYPEHUGQ: housing type / GQ flag
  - ACR: units in structure or acreage (varies)
  - BLD: building type code
  - HHT: household type code
  - HINCP: household income category (PUMS field)
  - HUPAC: household characteristics placeholder (varies)
  - NPF: placeholder field used by pipeline (varies by seed)
  - TEN: tenure
  - VEH: vehicles
  - hh_workers_from_esr: derived number of workers
  - hh_income_2023: income in 2023$
  - hhgqtype: group quarters type
  - hh_income_2010: income in 2010$

- `synthetic_persons.csv` (header from current outputs)
  - PUMA: PUMA origin
  - TAZ_NODE: assigned TAZ
  - MAZ_NODE: assigned MAZ
  - integer_weight: integerized weight
  - unique_hh_id: household foreign key
  - SERIALNO: PUMS serialno
  - SPORDER: person order in household
  - PWGTP: person weight (PUMS)
  - AGEP: age
  - COW: class of worker
  - MIL: military indicator
  - SCHG, SCHL: school grade / education codes
  - SEX: sex
  - WKHP: usual hours worked per week
  - WKWN: weeks worked
  - ESR: employment status recode
  - HISP: Hispanic origin
  - PINCP: personal income
  - POWPUMA / PUMA workplace (if available)
  - INDP: industry code (if included)
  - OCCP: occupation recode used by TM2
  - occupation: occupation text or recode
  - employed: boolean derived from ESR
  - employ_status: textual employ status
  - student_status: derived student flag
  - person_type: model person type used by CT-RAMP
  - hhgqtype: group quarters indicator

Where to find the definitive headers
- Current outputs (sample files): `docs/sample_synthetic_households.csv`, `docs/sample_synthetic_persons.csv`.
- For full seed headers, open the seed outputs in your `output_2023` folder or re-run the small streaming script `scripts/extract_samples_tm2.py` (already added to the repo).

Next steps to fully document ALL I/O fields
- I can iterate over all generated summary CSVs (MAZ / TAZ / County / final_summary files) and auto-extract headers and first-row samples, then create a per-file markdown section with per-field descriptions. Confirm if you want me to automatically generate those sections for every CSV under `output_2023/populationsim_working_dir/data/` and `.../output/` and I'll run it and commit the generated docs.