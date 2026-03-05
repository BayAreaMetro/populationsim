# Group Quarters Handling in the PopulationSim Pipeline

## Overview

The pipeline uses a **single unified process** for both regular households and non-institutional
group quarters (GQ) persons. Because person totals in TM2 include both household persons and
non-institutional GQ persons, running them through a single PopulationSim pass is simpler and
keeps control totals internally consistent.

A single PopulationSim run means:
- All person records come out of one synthesis step
- Control totals are internally consistent by construction
- The `hhgqtype` field on each record already carries the information needed to distinguish
  regular households from GQ in any downstream analysis

---

## `hhgqtype` Values

| `hhgqtype` | Meaning |
|---|---|
| `0` | Regular household (`TYPEHUGQ == 1`) |
| `1` | University / college GQ (noninstitutional, identified by college enrollment `SCHG 15–16`) |
| `2` | Military barracks, group homes, and other noninstitutional GQ |

Institutional GQ (`TYPEHUGQ == 2`: nursing homes, correctional facilities, etc.) are **excluded
from the seed entirely** and never synthesized.

---

## Implementation Details

### 1. Seed Population (`create_seed_population.py`)

**Household-level pass** — `_create_group_quarters_type()`:

1. All records with `TYPEHUGQ == 2` (institutional GQ) are dropped.
2. All remaining noninstitutional GQ records (`TYPEHUGQ == 3`) are assigned `hhgqtype = 2`
   as a placeholder.
3. Regular housing units (`TYPEHUGQ == 1`) are assigned `hhgqtype = 0`.

**Person-level refinement** — done during person processing:

- Persons in a GQ household who are enrolled in college (`SCHG` 15 or 16) are reclassified to
  `hhgqtype = 1` (university GQ).
- All other noninstitutional GQ persons remain `hhgqtype = 2`.

This two-pass design is necessary because university GQ identification requires person-level
enrollment data that is not available at the household record level.

### 2. Controls (`create_baseyear_controls.py`)

Three GQ-related controls are generated:

| Control | Geography | Covers |
|---|---|---|
| `numhh_gq` | MAZ | All synthesized household records, including noninstitutional GQ units |
| `numhh` | MAZ | Regular households only (`hhgqtype == 0`) |
| `gq_pop_region` | Region | Non-institutional GQ persons (soft constraint; ~85% of ACS total to exclude institutional) |

Household-level demographic controls (size, income, workers, children) are computed against
`numhh` (regular households only). Person-level controls (age, occupation) apply to the full
synthesized population, including GQ persons.

### 3. Post-processing (`postprocess_recode.py`)

Both synthetic households and synthetic persons come out of a single PopulationSim run.
`postprocess_recode.py` recodes and renames columns and writes:

- `synthetic_households_recoded.csv` — all household-type records (including GQ units)
- `synthetic_persons_recoded.csv` — all persons; `hhgqtype` is preserved so downstream
  tools can filter to regular-household persons or GQ persons as needed

---

*Last updated: February 2026*

