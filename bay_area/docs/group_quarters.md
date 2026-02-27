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

## How GQ is Currently Handled

### Seed Population (`create_seed_population.py`)

PUMS records are read as a single file. The `_create_group_quarters_type()` method assigns
`hhgqtype` values:

| `hhgqtype` | Meaning |
|---|---|
| `0` | Regular household (`TYPEHUGQ == 1`) |
| `2` | Non-institutional GQ (university, student housing, etc.) |

Institutional GQ (military, nursing homes, correctional) are **excluded** from the seed
entirely so that PopulationSim does not synthesize them.

### Controls (`create_baseyear_controls.py`)

- `numhh_gq` — total household-record count including non-institutional GQ units (MAZ-level
  marginal control)
- `numhh` — regular households only (`hhgqtype == 0`), used where HH-specific demographic
  controls (size, income, workers, children) are needed
- `gq_pop_region` — regional non-institutional GQ person total (used as a soft constraint)

Household-level demographic controls (size, income, workers, children) in the TAZ controls
file apply to regular households; person-level controls (age, occupation) apply to the full
synthesized population including GQ persons.

### Post-processing (`postprocess_recode.py`)

Both synthetic households and synthetic persons come out of a single PopulationSim run.
`postprocess_recode.py` recodes and renames columns for the target model (TM1 or TM2) and
writes:

- `synthetic_households_recoded.csv` — all household-type records (including GQ units)
- `synthetic_persons_recoded.csv` — all persons; `hhgqtype` is preserved so downstream
  tools can filter to regular-household persons or GQ persons as needed

---

## TM1 vs TM2 Compatibility

The current `tm2` branch uses the unified approach described above and is **not backward
compatible** with the old TM1 separated pipeline (which used a separate `hh_gq/` directory
structure). The `postprocess_recode.py` script retains a `TM1` output-column mapping but the
input data path assumptions differ between the two model versions.

Reconciling the two branches so `tm2` changes can be merged into `develop` without breaking
TM1 functionality is a known open issue.

---

*Last updated: February 2026*

