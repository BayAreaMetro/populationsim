# Group Quarters Handling in the PopulationSim Pipeline

## Decision Summary

A proposal was drafted in October 2025 to implement a fully separated GQ/household pipeline
(10-step plan). After review, the team decided **not to proceed** with that approach. Instead
the pipeline uses a **single unified process** for both regular households and non-institutional
group quarters (GQ) persons.

This document explains the rationale for that decision and how GQ are currently handled.

---

## Why a Unified Process

The core reason the 10-step separation plan was not adopted is that **person totals in TM2
already include both household persons and non-institutional GQ persons**. Splitting synthesis
into two separate passes would have created:

- Redundant complexity with no modeling benefit — both populations flow through the same
  PopulationSim machinery
- Synchronization problems when joining the two output streams
- An additional failure point every run

Keeping everything in a single PopulationSim run means:
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

## What Happened to the October 2025 Separation Proposal

The 10-step plan ("Status: Step 1 Complete - Awaiting approval to proceed") was:

1. Documented (Step 1) ✓
2. Reviewed with stakeholders
3. **Not approved for implementation** — the unified approach was chosen instead

The old proposal document is preserved in version control history if needed for reference.

---

*Last updated: February 2026*  
*Decision: Unified single-process pipeline adopted; separation proposal superseded*

