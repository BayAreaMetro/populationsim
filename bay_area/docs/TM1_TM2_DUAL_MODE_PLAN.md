# TM1 + TM2 Dual-Mode Pipeline Plan

**Strategy (updated March 2026):** There are two sequential goals:

1. **Merge `tm2` into `master`** — bring the modernized Python pipeline to master without breaking existing TM1 production runs. The git merge itself has only one conflict (the BAT file), but two functional blockers must be fixed on `tm2` first: the PopulationSim runner was renamed (G9) and `create_seed_population.py` has no TM1 PUMA support (G10).
2. **Add TM1 support to the Python pipeline** — so `tm2_pipeline.py` can run TM1 synthesis, replacing the BAT file long-term.

This document covers both: the merge plan (Phase 0) and the TM1 porting work (Phases 1–7).

---

## Gaps Checklist

| # | Gap | Status |
|---|-----|--------|
| G1 | `add_hhgq_combined_controls.py` — cherry-pick from `master` | ✅ done (commit `fd124cd`) |
| G2 | `hh_gq/configs_TM1/` directory — cherry-pick from `master` | ✅ done (commit `fd124cd`) |
| G3 | `geo_cross_walk_tm1.csv` — cherry-pick from `master` | ✅ done (commit `fd124cd`) |
| G4 | PUMA vintage mismatch — [team decision required](#g4--puma-vintage-mismatch-seed-population) | ✅ decided: Option A (2017–2021 PUMS for TM1) |
| G5 | `tm2_pipeline.py` has no `--model_type` argument | ☐ not started |
| G6 | `run_all_summaries.py` hardcodes TM2 filenames | ☐ not started |
| G8 | TM1 control generation lives in R (`travel-model-one`) — not portable | ☐ future phase |
| G9 | `run_populationsim.py` renamed to `run_populationsim_synthesis.py` on `tm2` — BAT breaks at this call | ✅ fixed: renamed back to `run_populationsim.py` |
| G10 | `create_seed_population.py` on `tm2` has no TM1/PUMA vintage support — TM1 BAT run produces wrong PUMA codes | ✅ fixed: `--model_type` arg added; TM1 uses 2017–2021 PUMS (`PUMS_2021_5Year_Crosswalked`) and `geo_cross_walk_tm1.csv`; TM1 income → `hh_income_2000` (CPI 2021→2000 = 172.2/258.8) |

## Implementation Checklist

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Merge `tm2` → `master` | ✅ ready — G9 and G10 are the only blockers, both fixed |
| 1 | Git cherry-picks — configs, crosswalks *(already on `tm2`)* | ✅ complete |
| 2 | Port `add_hhgq_combined_controls.py` *(already on `tm2`)* | ✅ complete |
| 3 | PUMA vintage design decision (G4) | ✅ decided: Option A — use 2017–2021 PUMS for TM1 |
| 4 | Wire `--model_type` into `tm2_pipeline.py` (`create_seed_population.py` ✅ done) | ⏸ `tm2_pipeline.py` still pending |
| 5 | Fix Python 3.x bugs in `master` | ☐ independent, do before merge |
| 6 | End-to-end TM1 test run | ⏸ blocked on Phase 4 |
| 7 | Port TM1 control generation from R to Python (G8) | ☐ future — not blocking |

> Phase 3 decision: **Option A** (download 2017–2021 PUMS for TM1) or **Option B** (rebuild TM1 crosswalk with 2020 PUMAs). See [§4 G4](#g4--puma-vintage-mismatch-seed-population) and [§11 Phase 3](#phase-3--design-decision-puma-vintage-g4) for full detail.

---

## 1. Repository Ownership

The pipeline spans **two repositories**:

| Repo | Path | Role |
|------|------|------|
| `travel-model-one` | `utilities/taz-data-baseyears/` | Creates TM1 base-year TAZ controls from Census (R scripts) |
| `populationsim/bay_area` | (this repo, `tm2` branch) | PUMS seed creation, PopulationSim run, postprocessing |

**TM2 controls are created entirely within this repo** (`create_baseyear_controls.py`).  
**TM1 controls for base years are created in `travel-model-one`** and copied in. This is a fundamental architectural difference.

| Branch | Focus | Entry point | Status |
|--------|-------|-------------|--------|
| `master` | **TM1-default** production runs via BAT; no Python pipeline | `run_populationsim.bat` | Active TM1 production use |
| `tm2` | **TM2-only** Python pipeline; modernized 2023 vintage | `tm2_pipeline.py` | Goal: merge into master, then add TM1 support |

---

## 2. Full Pipeline — Step by Step

### TM1 Pipeline

```
[travel-model-one repo]
Step T1-A  Create TAZ Popsim Vars (R script — NOT in this repo)
     ↓
[this repo — PUMS assumed pre-downloaded to M:\Data\Census\]
Step T1-B  add_hhgq_combined_controls.py      combines GQ + HH controls into taz_summaries_hhgq.csv
     ↓
Step T1-C  create_seed_population.py          PUMS → seed_households.csv, seed_persons.csv
     ↓
Step T1-D  run_populationsim.py               PopulationSim library (TAZ geography)
               pre-steps: prepare_populationsim_data(), fix_crosswalk_multi_puma()
     ↓
Step T1-E  postprocess_recode.py --model_type TM1
     ↓
Step T1-F  run_all_summaries.py --model_type TM1   (TAZ-compatible scripts only)
     ↓
Step T1-G  summarize_synthpop_by_TAZ.py            (validation)
```

### TM2 Pipeline

```
[this repo]
Step T2-A  download_2023_5year_pums.py        1-time download → M:\Data\Census\PUMS_2023_5Year_Crosswalked\
     ↓
Step T2-B  create_seed_population.py          PUMS → seed_households.csv, seed_persons.csv
     ↓
Step T2-C  create_baseyear_controls.py        Census API → MAZ / PUMA / county controls
               inline: add_hhgq_combined_controls equivalent
     ↓
Step T2-D  run_populationsim.py               PopulationSim library (MAZ geography)
               pre-steps: prepare_populationsim_data(), fix_crosswalk_multi_puma()
     ↓
Step T2-E  postprocess_recode.py --model_type TM2
     ↓
Step T2-F  run_all_summaries.py --model_type TM2   (MAZ + TAZ scripts)
     ↓
Step T2-G  run_analysis_scripts()                   validation, visualization, Tableau
```

---

## 3. Step-by-Step Detail

---

### Step T1-A — Create TM1 Base-Year TAZ Controls

**Repo:** `travel-model-one/utilities/taz-data-baseyears/`  
**This step does NOT exist in the `populationsim/bay_area` repo.**

#### Scripts

| Year | Script |
|------|--------|
| 2015 | `2015/ACS 2013-2017 create TAZ data for 2015.R` |
| 2020, 2023 | `create_tazdata_2020_and_after.R --year YYYY` (also uses `common.R`) |

#### Data Sources

| Variable group | Source | ACS Table |
|----------------|--------|-----------|
| Total HH, income quartiles | ACS 5-year | B19001 (rebinned to 2000-dollar thresholds) |
| HH size | ACS 5-year | B25009 |
| Workers per HH | ACS 5-year | B08202 |
| Age groups | ACS 5-year | B01001 |
| Group quarters (type) | **2020 Decennial** | PCT19 |
| Employment | LEHD LODES WAC | (not used by PopulationSim but in same output file) |
| CPI deflation | BLS CPI | ACS nominal → 2000 dollars |

#### Income Bins (2000 dollars, used directly as PopulationSim controls)

| Column | Threshold |
|--------|-----------|
| `HHINCQ1` | < $30,000 |
| `HHINCQ2` | $30,000 – $60,000 |
| `HHINCQ3` | $60,000 – $100,000 |
| `HHINCQ4` | > $100,000 |

The R script converts ACS nominal income bins to 2000 dollars using CPI ratio before binning.

#### Outputs (copied into this repo's `hh_gq/data/`)

| File | Destination | Content |
|------|-------------|---------|
| `TAZ1454 YYYY Popsim Vars.csv` | `hh_gq/data/taz_summaries.csv` | Per-TAZ controls: `TAZ, TOTHH, hh_size_1..4_plus, hh_wrks_0..3_plus, HHINCQ1..4, AGE0004..65P, gq_tot_pop, gq_type_univ/mil/othnon` |
| `TAZ1454 YYYY Popsim Vars County.csv` | `hh_gq/data/county_marginals.csv` | County-level summary (currently commented out in settings.yaml) |

#### Column Names in `taz_summaries.csv`

```
TAZ, TOTHH, TOTPOP, hh_own, hh_rent,
hh_size_1, hh_size_2, hh_size_3, hh_size_4_plus,
hh_wrks_0, hh_wrks_1, hh_wrks_2, hh_wrks_3_plus,
hh_kids_no, hh_kids_yes,
HHINCQ1, HHINCQ2, HHINCQ3, HHINCQ4,
AGE0004, AGE0519, AGE2044, AGE4564, AGE65P,
gq_tot_pop, gq_type_univ, gq_type_mil, gq_type_othnon,
(+ employment cols not used by popsim)
```

Note the uppercase column names (`HH_SIZE_1` → lowercase in `taz_summaries.csv` is done by `add_hhgq_combined_controls.py`).

---

### Step T1-B — add_hhgq_combined_controls.py (TM1 mode)

**Script:** `add_hhgq_combined_controls.py` (currently on `master` only, not in `tm2` branch)

**Inputs:**
- `hh_gq/data/taz_summaries.csv` (from Step T1-A)
- `hh_gq/data/geo_cross_walk_tm1.csv`

**Processing:**
1. Lowercases certain uppercase column names from the R output (`HH_SIZE_1` → `hh_size_1`, etc.)
2. Creates `numhh_gq = TOTHH + gq_tot_pop` (GQ treated as 1-person households for PopulationSim)
3. Creates `hh_size_1_gq = hh_size_1 + gq_tot_pop`
4. Writes `hh_gq/data/taz_summaries_hhgq.csv`

**Output:** `hh_gq/data/taz_summaries_hhgq.csv`

**Status:** ✅ Done — ported from `master` (Phase 2, commit `fd124cd`).

---

### Step T1-C / T2-A — create_seed_population.py

**Script:** `create_seed_population.py` (exists in both branches, but differs in vintage)

#### TM1 seed requirements

| Item | `master` branch | `tm2` branch with `--model_type TM1` |
|------|-----------------|--------------------------------------|
| PUMS vintage | 2017–2021 5-year | ✅ 2017–2021 5-year (`PUMS_2021_5Year_Crosswalked`) |
| PUMA definitions | 2010 Census | ✅ 2010 Census (aligns with `geo_cross_walk_tm1.csv`) |
| Crosswalk file | `geo_cross_walk_tm1.csv` | ✅ `geo_cross_walk_tm1.csv` |
| `hh_income_2000` | Yes — `hh_income_2021 / 1.81` | ✅ Yes — CPI factor `172.2/258.8` |
| `TYPEHUGQ` | Set on seed HHs | ✅ Already set |
| `hh_workers_from_esr` | Set on seed HHs | ✅ Already set |
| `gqtype` on persons | Set (1=univ, 2=mil, 3=othnon) | ✅ Already set |
| Age groups | Set via AGEP | ✅ Already set |

> **Status (March 2026):** ✅ Done — `--model_type TM1` added (G10 fix, commit `aece8f1`). Selects 2017–2021 PUMS, reads `geo_cross_walk_tm1.csv`, produces `hh_income_2000`. All TM1-required fields present.

#### Crosswalk files needed

| Mode | File | Columns | PUMA vintage |
|------|------|---------|--------------|
| TM1 | `hh_gq/data/geo_cross_walk_tm1.csv` | `TAZ, PUMA, COUNTY, county_name, REGION` | 2000 Census PUMAs |
| TM2 | `hh_gq/data/geo_cross_walk_tm2_maz.csv` | `MAZ, TAZ, PUMA, COUNTY, county_name, REGION` | 2020 Census PUMAs |

**Decision: Option A** — `create_seed_population.py --model_type TM1` loads 2017–2021 PUMS (2010-vintage PUMA codes), which align with `geo_cross_walk_tm1.csv`. Implemented in commit `aece8f1`.

#### Seed outputs

| File | Description |
|------|-------------|
| `hh_gq/data/seed_households.csv` | One row per PUMS housing unit/GQ; includes `unique_hh_id, WGTP, NP, PUMA, COUNTY, TYPEHUGQ, hh_income_2000, hh_income_2010, hh_income_2021, VEH, BLD, TEN, HHT, hh_workers_from_esr` |
| `hh_gq/data/seed_persons.csv` | One row per PUMS person; includes `unique_hh_id, AGEP, SEX, employ_status, student_status, person_type, gqtype, occupation, employed, ESR, SCHL, SCHG, WKHP, WKW` |

---

### Step T1-D / T2-D — run_populationsim.py

**Script:** `run_populationsim.py` (PopulationSim library wrapper)

**Invocation:**
- TM1: `python run_populationsim.py --config hh_gq/configs_TM1 --output <OUTPUT_DIR> --data hh_gq/data`
- TM2: `python run_populationsim.py --config hh_gq/configs_TM2 --output <OUTPUT_DIR> --data hh_gq/data`

The config directory fully determines which geography hierarchy and controls are used.

#### TM1 config (`hh_gq/configs_TM1/`)

| Setting | Value |
|---------|-------|
| `geographies` | `[COUNTY, PUMA, TAZ]` — no MAZ |
| `seed_geography` | `PUMA` |
| `geo_cross_walk` | `geo_cross_walk_tm1.csv` |
| `TAZ_control_data` | `taz_summaries_hhgq.csv` |
| County controls | Commented out |

#### TM1 control variables (from `hh_gq/configs_TM1/controls.csv`)

| Control | Geography | Seed table | Seed expression |
|---------|-----------|------------|-----------------|
| `num_hh` (= `numhh_gq`) | TAZ | households | `WGTP > 0` |
| `hh_size_1_gq` | TAZ | households | `NP == 1` |
| `hh_size_2` | TAZ | households | `NP == 2` |
| `hh_size_3` | TAZ | households | `NP == 3` |
| `hh_size_4_plus` | TAZ | households | `NP >= 4` |
| `hh_inc_30` (= `HHINCQ1`) | TAZ | households | `TYPEHUGQ==1 & hh_income_2000 <= 30000` |
| `hh_inc_30_60` (= `HHINCQ2`) | TAZ | households | `30000 < hh_income_2000 <= 60000` |
| `hh_inc_60_100` (= `HHINCQ3`) | TAZ | households | `60000 < hh_income_2000 <= 100000` |
| `hh_inc_100_plus` (= `HHINCQ4`) | TAZ | households | `hh_income_2000 > 100000` |
| `hh_wrks_0..3_plus` | TAZ | households | `TYPEHUGQ==1 & hh_workers_from_esr == N` |
| `pers_age_00_04..65_plus` | TAZ | persons | `AGEP` ranges |
| `gq_type_univ/mil/othnon` | TAZ | persons | `gqtype == 1/2/3` |

Note: 5 age bins for TM1, vs 4 age bins for TM2.

#### TM2 config (`hh_gq/configs_TM2/`)

| Setting | Value |
|---------|-------|
| `geographies` | `[COUNTY, PUMA, TAZ, MAZ]` |
| `seed_geography` | `PUMA` |
| `geo_cross_walk` | `geo_cross_walk_tm2_maz.csv` |
| `MAZ_control_data` | `maz_marginals_hhgq.csv` |

#### PopulationSim outputs (written to `--output` dir)

```
synthetic_households.csv
synthetic_persons.csv
final_expanded_household_ids.csv
final_summary_TAZ.csv
final_summary_COUNTY_1.csv  … final_summary_COUNTY_9.csv
populationsim.log
timing_log.csv
pipeline.h5
```

---

### Step T1-E / T2-E — postprocess_recode.py

**Script:** `postprocess_recode.py` (exists in both branches; `tm2` branch version handles both modes)

**Invocation:**
- TM1: `python postprocess_recode.py --model_type TM1 --directory <OUTPUT_DIR> --year YYYY`
- TM2: `python postprocess_recode.py --model_type TM2 --directory <OUTPUT_DIR> --year YYYY`

#### TM1 household column mapping

| PopulationSim field | Output field | Notes |
|---------------------|-------------|-------|
| `unique_hh_id` | `HHID` | |
| `TAZ` | `TAZ` | |
| `hh_income_2000` | `HINC` | 2000 dollars |
| `hh_workers_from_esr` | `hworkers` | |
| `VEH` | `VEHICL` | |
| `BLD` | `BLD` | |
| `TEN` | `TEN` | |
| `NP` | `PERSONS` | |
| `HHT` | `HHT` | |
| `TYPEHUGQ` | `UNITTYPE` | |
| *(derived)* | `hinccat1` | 1–4 from HINC; thresholds $20k/$50k/$100k (2000$) |
| *(derived)* | `poverty_income_YYYYd` | HHS poverty threshold in model-year dollars |
| *(derived)* | `poverty_income_2000d` | Poverty threshold deflated to 2000 dollars |
| *(derived)* | `pct_of_poverty` | `100 * HINC / poverty_income_2000d` |

#### TM1 person column mapping

| PopulationSim field | Output field |
|---------------------|-------------|
| `unique_hh_id` | `HHID` |
| `PERID` *(generated)* | `PERID` |
| `AGEP` | `AGE` |
| `SEX` | `SEX` |
| `employ_status` | `pemploy` |
| `student_status` | `pstudent` |
| `person_type` | `ptype` |

#### TM1 output files

```
synthetic_households_recode.csv   (HHID, TAZ, HINC, hworkers, VEHICL, BLD, TEN, PERSONS, HHT, UNITTYPE, hinccat1, poverty_income_*, pct_of_poverty)
synthetic_persons_recode.csv      (HHID, PERID, AGE, SEX, pemploy, pstudent, ptype)
summary_melt.csv                  (control vs result comparison by TAZ and county)
```

> **Status:** The `tm2` branch `postprocess_recode.py` **already supports** `--model_type TM1` with
> the correct column mappings and poverty calculations. No changes required here.

---

### Step T1-F — summarize_synthpop_by_TAZ.py (Optional Validation)

**Script:** `summarize_synthpop_by_TAZ.py` (on `master` only, not in `tm2` branch)

Reads `synthetic_households_recode.csv` + `synthetic_persons_recode.csv`, summarizes `pemploy`, `pstudent`, `UNITTYPE` counts by TAZ, writes `popsyn_taz_summary.csv`.

---

### Step T2-B — create_baseyear_controls.py (TM2 only)

**Script:** `create_baseyear_controls.py` (~4,400 lines; `tm2` branch only)

Fetches controls entirely from Census API:
- 2020 Decennial PL 94-171: block-level GQ and housing counts → MAZ aggregation
- 2023 ACS 5-year: household size, workers, income, age at block group/tract → MAZ aggregation

Writes:
```
hh_gq/data/maz_marginals.csv
hh_gq/data/taz_marginals.csv
hh_gq/data/county_marginals.csv
```

**No TM1 equivalent in this repo.** TM1 controls come from `travel-model-one` R scripts.

---

## 4. Gap Analysis

### G1 — `add_hhgq_combined_controls.py` ✅ Done

Ported from `master` (commit `fd124cd`). Logic: rename uppercase R columns, derive `numhh_gq = TOTHH + gq_tot_pop` and `hh_size_1_gq = hh_size_1 + gq_tot_pop`.

### G2 — `hh_gq/configs_TM1/` directory ✅ Done

Cherry-picked from `master` (commit `fd124cd`).

### G3 — `hh_gq/data/geo_cross_walk_tm1.csv` ✅ Done

Cherry-picked from `master` (commit `fd124cd`). Columns: `TAZ, PUMA, COUNTY, county_name, REGION`. Uses 2000-vintage PUMA codes.

### G4 — PUMA Vintage Mismatch ✅ Resolved

**Decision: Option A** — 2017–2021 PUMS (2010-vintage PUMA codes) for TM1; 2019–2023 PUMS (2020-vintage) for TM2. The `geo_cross_walk_tm1.csv` 2000-vintage PUMA codes align closely enough with 2010-vintage codes for Bay Area geography. Implemented in `create_seed_population.py --model_type TM1` (commit `aece8f1`); `tm2_config.py` routes to `PUMS_2021_5Year_Crosswalked` when `model_type == "TM1"`.

> Note: `master`'s crosswalk (2000-vintage) was never perfectly aligned with its own 2017–2021 PUMS (2010-vintage). Bay Area PUMA boundary changes between 2000 and 2010 are minor enough that this has not caused problems in practice.

### G5 — `tm2_pipeline.py` — No TM1 Support

**Status:** `tm2_pipeline.py` is TM2-only. All steps are hardcoded to TM2 paths and configs.  
**Action:** Add `--model_type TM1|TM2` argument that:
- Skips `create_baseyear_controls.py` (TM1 controls come externally)
- Calls `add_hhgq_combined_controls.py --model_type TM1` instead
- Passes `hh_gq/configs_TM1` to `run_populationsim.py`
- Passes `--model_type TM1` to `postprocess_recode.py`

### G6 — `summarize_synthpop_by_TAZ.py`

**Status:** Missing from `tm2` branch.  
**Action:** Port from `master` (optional; validation tool only).

### G7 — External Input Handling

**Status:** No mechanism in `tm2_pipeline.py` to accept externally-provided TAZ controls.

For TM1, the user must manually copy (or script the copy of):
```
TAZ1454 YYYY Popsim Vars.csv → hh_gq/data/taz_summaries.csv
```

**Action:** Add a validation step to `tm2_pipeline.py` (TM1 mode) that checks for the existence of
`hh_gq/data/taz_summaries.csv` before proceeding, and provides a clear error message pointing to the
`travel-model-one` repo if it is missing.

---

### G8 — TM1 Control Generation in R (Future Transition)

**Status:** Not blocking. Long-term gap.

TM1 base-year controls are generated by R scripts in a completely separate repo (`travel-model-one/utilities/taz-data-baseyears/`). This means a user who only has the `populationsim` repo cannot generate TM1 controls — they must run the R pipeline first and copy the output in manually.

By contrast, TM2 is fully self-contained: `create_baseyear_controls.py` fetches Census data and produces `taz_summaries.csv` (or `maz_marginals.csv`) with no external dependency.

**What a transition would involve:**

| Task | Detail |
|------|--------|
| Port ACS pulls | Replace R `tidycensus` calls with Python `requests` to Census API (same tables: B19001, B25009, B08202, B01001) |
| Re-implement CPI deflation | Convert nominal ACS income bins → 2000 dollars using BLS CPI ratio |
| Port GQ pull | Replace R Decennial PCT19 pull with Python Census API call |
| Port income rebinning | Replicate the R logic that maps ACS income categories to HHINCQ1–4 thresholds |
| Integrate into pipeline | Add `--model_type TM1` path in `create_baseyear_controls.py` that writes `taz_summaries.csv` (same format `add_hhgq_combined_controls.py` expects) |

**Result:** `python tm2_pipeline.py full --model_type TM1 --year 2023` would become a single-command, fully self-contained run — no R, no manual file copy.

**Dependency:** Complete Phases 1–6 first. This is a standalone improvement once the end-to-end test (Phase 6) passes.

---

## 5. Input/Output Summary by Mode

### TM1 Inputs Required (before running this repo)

| File | Source | Notes |
|------|--------|-------|
| `hh_gq/data/taz_summaries.csv` | `travel-model-one` R script output | `TAZ1454 YYYY Popsim Vars.csv` renamed |
| PUMS housing CSV | Census Bureau or M: drive | 5-year ACS PUMS, CA state file |
| PUMS persons CSV | Census Bureau or M: drive | 5-year ACS PUMS, CA state file |
| `hh_gq/data/geo_cross_walk_tm1.csv` | This repo (committed) | PUMA→TAZ→COUNTY crosswalk |

### TM1 Outputs Produced (by this repo)

| File | Location |
|------|----------|
| `seed_households.csv` | `hh_gq/data/` |
| `seed_persons.csv` | `hh_gq/data/` |
| `taz_summaries_hhgq.csv` | `hh_gq/data/` |
| `synthetic_households.csv` | `<OUTPUT_DIR>/` |
| `synthetic_persons.csv` | `<OUTPUT_DIR>/` |
| `final_summary_TAZ.csv` | `<OUTPUT_DIR>/` |
| `final_summary_COUNTY_[1-9].csv` | `<OUTPUT_DIR>/` |
| `synthetic_households_recode.csv` | `<OUTPUT_DIR>/` |
| `synthetic_persons_recode.csv` | `<OUTPUT_DIR>/` |
| `summary_melt.csv` | `<OUTPUT_DIR>/` |

### TM1 Final Household Fields

```
HHID, TAZ, HINC, hworkers, VEHICL, BLD, TEN, PERSONS, HHT, UNITTYPE,
hinccat1, poverty_income_YYYYd, poverty_income_2000d, pct_of_poverty
```

### TM1 Final Person Fields

```
HHID, PERID, AGE, SEX, pemploy, pstudent, ptype
```

---

## 6. Implementation Order

Suggested order to implement TM1 support in the `tm2` branch, from lowest to highest effort:

| Priority | Gap | Effort | Notes |
|----------|-----|--------|-------|
| 1 | G2 — Copy `configs_TM1/` from master | Trivial | `git checkout master -- hh_gq/configs_TM1` |
| 2 | G3 — Copy `geo_cross_walk_tm1.csv` from master | Trivial | `git checkout master -- hh_gq/data/geo_cross_walk_tm1.csv` |
| 3 | G1 — Add `add_hhgq_combined_controls.py` | Small | Port 30-line TM1 block from master |
| 4 | G7 — Add input validation in pipeline | Small | Check `taz_summaries.csv` exists; error with helpful message |
| 5 | G5 — Add `--model_type` to `tm2_pipeline.py` | Medium | Routing logic to switch between TM1/TM2 steps |
| 6 | G6 — Port `summarize_synthpop_by_TAZ.py` | Small | Optional validation tool |
| 7 | G4 — PUMA vintage decision | **Design decision** | Choose Option A or B; requires team discussion |

---

## 7. Key Differences Between TM1 and TM2 (Summary)

| Dimension | TM1 | TM2 |
|-----------|-----|-----|
| **Finest geography** | TAZ (1,454 zones) | MAZ (~27,500 zones) |
| **Geographies in popsim** | COUNTY → PUMA → TAZ | COUNTY → PUMA → TAZ → MAZ |
| **Controls source (base year)** | R scripts in `travel-model-one` repo | `create_baseyear_controls.py` (Census API) |
| **Controls source (forecast)** | BAUS `taz_summaries_YYYY.csv` | BAUS `maz_marginals_YYYY.csv` |
| **PUMA vintage** | 2000 (in existing crosswalk) | 2020 |
| **PUMS vintage** | 2017–2021 5-year (master) | 2019–2023 5-year (tm2 branch) |
| **Income field** | `hh_income_2000` (2000 dollars) | `hh_income_2010` (2010 dollars) |
| **Income bins** | $30k / $60k / $100k (2000 dollars) | Continuous (no discrete bins in controls) |
| **Age bins** | 5: 0–4, 5–19, 20–44, 45–64, 65+ | 4: 0–17, 18–64, 65+ (varies) |
| **HH field name** | `UNITTYPE` | `TYPE` |
| **Income field name** | `HINC` | `HHINCADJ` |
| **Vehicle field name** | `VEHICL` | `VEH` |
| **Persons field name** | `PERSONS` | `NP` |
| **Workers field name** | `hworkers` | `NWRKRS_ESR` |
| **TM1-specific outputs** | `hinccat1`, `pct_of_poverty`, `poverty_income_*` | Not produced |
| **GQ handling** | GQ collapsed to 1-person HH with `numhh_gq` | Same approach |

---

## 8. Reference: TM1 Control Column Names vs. Crosswalk

### `taz_summaries.csv` → `taz_summaries_hhgq.csv` column transformations

| R output column | After `add_hhgq_combined_controls.py` | Used in popsim controls.csv as |
|-----------------|---------------------------------------|-------------------------------|
| `TOTHH` | unchanged | — |
| `HH_SIZE_1` → `hh_size_1` | renamed | — |
| `HH_SIZE_2` → `hh_size_2` | renamed | `hh_size_2` |
| `HH_SIZE_3` → `hh_size_3` | renamed | `hh_size_3` |
| `HH_SIZE_4_PLUS` → `hh_size_4_plus` | renamed | `hh_size_4_plus` |
| `GQ_TOT_POP` → `gq_tot_pop` | renamed | — |
| `GQ_TYPE_UNIV` → `gq_type_univ` | renamed | `gq_type_univ` |
| `GQ_TYPE_MIL` → `gq_type_mil` | renamed | `gq_type_mil` |
| `GQ_TYPE_OTHNON` → `gq_type_othnon` | renamed | `gq_type_othnon` |
| `HH_WRKS_0` → `hh_wrks_0` | renamed | `hh_wrks_0` |
| `HH_WRKS_1` → `hh_wrks_1` | renamed | `hh_wrks_1` |
| `HH_WRKS_2` → `hh_wrks_2` | renamed | `hh_wrks_2` |
| `HH_WRKS_3_PLUS` → `hh_wrks_3_plus` | renamed | `hh_wrks_3_plus` |
| `HHINCQ1` | unchanged | `HHINCQ1` |
| `HHINCQ2` | unchanged | `HHINCQ2` |
| `HHINCQ3` | unchanged | `HHINCQ3` |
| `HHINCQ4` | unchanged | `HHINCQ4` |
| `AGE0004` | unchanged | `AGE0004` |
| `AGE0519` | unchanged | `AGE0519` |
| `AGE2044` | unchanged | `AGE2044` |
| `AGE4564` | unchanged | `AGE4564` |
| `AGE65P` | unchanged | `AGE65P` |
| *(derived)* `numhh_gq` | `TOTHH + gq_tot_pop` | `numhh_gq` (→ `num_hh` control) |
| *(derived)* `hh_size_1_gq` | `hh_size_1 + gq_tot_pop` | `hh_size_1_gq` |

> **Note:** The actual `taz_summaries.csv` column names from the 2023 R output are already lowercase
> (confirmed from file header). The rename step in `add_hhgq_combined_controls.py` handles the case
> where older R outputs used uppercase names.

---

## 9. What Each Mode Is in the `master` Branch

`master` is a **shared pipeline** that runs synthesis for both TM1 and TM2 by switching a single variable at the top of `run_populationsim.bat`:

```bat
set MODELTYPE=TM1   ← change to TM2 to run TM2 synthesis
```

| Aspect | `MODELTYPE=TM1` | `MODELTYPE=TM2` |
|---|---|---|
| PopulationSim config | `hh_gq/configs_TM1/` | `hh_gq/configs_TM2/` |
| Geographies | `[COUNTY, PUMA, TAZ]` | `[COUNTY, PUMA, TAZ, MAZ]` |
| Controls source (base year) | R scripts in `travel-model-one` → `TAZ1454 YEAR Popsim Vars.csv` | `create_baseyear_controls.py` (Census API) |
| Controls source (forecast year) | BAUS outputs | BAUS outputs |
| Geo crosswalk | `geo_cross_walk_tm1.csv` (TAZ→PUMA→COUNTY) | `geo_cross_walk_tm2.csv` (MAZ→TAZ→PUMA→COUNTY) |
| Finest control geography | TAZ | MAZ |
| Income field | `hh_income_2000` (2000 dollars) | `hh_income_2010` (2010 dollars) |
| Unit type field | `TYPEHUGQ` | `TYPE` |
| PUMA definitions | 2000 vintage (crosswalk `geo_cross_walk_tm1.csv`) | **2000 vintage** (crosswalk built from `puma2000.dbf`) — ⚠️ mismatched with 2017–2021 PUMS which uses 2010 PUMAs |
| Census/ACS vintage | 2010 SF1 + 2016 ACS5 | 2010 SF1 + 2016 ACS5 |
| PUMS vintage | 2017–2021 | 2017–2021 |
| Seed population | Shared `create_seed_population.py` | Shared `create_seed_population.py` |

Key implication: **`create_baseyear_controls.py` is used only for TM2 mode**. TM1 mode never calls it — it gets controls from R scripts in the separate `travel-model-one` repository. Any Python bugs in `create_baseyear_controls.py` only affect TM2 legacy mode.

### Script and File Inventory: `master` vs `tm2` Branch

| Script / Directory | `master` branch | `tm2` branch |
|---|---|---|
| **Entry point** | `run_populationsim.bat` (BAT file; switches `MODELTYPE=TM1\|TM2`) | `tm2_pipeline.py` (Python orchestrator) |
| `add_hhgq_combined_controls.py` | ✓ handles **both TM1 and TM2** | ✗ **missing** — Gap G1 |
| `create_seed_population.py` | ✓ 2017–2021 PUMS, 2010-vintage PUMAs | ✓ 2019–2023 PUMS, 2020-vintage PUMAs |
| `create_baseyear_controls.py` | ✓ **TM2-only** — ~1,245-line older version | ✓ **TM2-only** — ~4,414-line modernized version |
| `run_populationsim.py` | ✓ bare PopulationSim runner | ✓ renamed `run_populationsim_synthesis.py` (+ progress logging) |
| `postprocess_recode.py` | ✓ handles **both TM1 and TM2** | ✓ handles **both TM1 and TM2** |
| `summarize_synthpop_by_TAZ.py` | ✓ TM1 TAZ-level validation | ✗ missing |
| `check_controls.py` | ✓ | ✓ |
| `compare_marginals.py` | ✓ | ✗ |
| `download_2023_5year_pums.py` | ✗ | ✓ |
| `run_all_summaries.py` | ✗ | ✓ |
| `utils/` directory | ✗ | ✓ (`census_fetcher.py`, `config_census.py`, `tm2_utils.py`, …) |
| `analysis/` directory | ✗ | ✓ |
| `hh_gq/configs_TM1/` | ✓ | ✗ **missing** — Gap G2 |
| `hh_gq/configs_TM2/` | ✓ older configs | ✓ modernized configs |
| `geo_cross_walk_tm1.csv` | ✓ 2000-vintage PUMAs | ✗ **missing** — Gap G3 |
| `geo_cross_walk_tm2.csv` | ✓ 2000-vintage PUMAs | ✓ 2020-vintage PUMAs |

---

## 10. Porting `tm2` Improvements Back to `master`

### 10.1 Quick Decision Summary

The relevant comparison is **`master` legacy TM2 mode vs `tm2` branch**.

| Category | Port to `master`? | Effort | Risk |
|---|---|---|---|
| Python 3.x fixes (`df.append`, `iteritems`, `logging.warn`) | **Yes — must fix** | Low (find/replace) | None |
| Census API rate limiting (100ms) | **Yes** | Low (~10 lines) | None |
| Census API JSON / N/A error handling | **Yes** | Medium (~30 lines) | None |
| Census API `timeout=30` | **Yes** | Trivial (1 line) | None |
| Hardcoded `M:\` paths → config dict | **Yes** | Low (~20 lines) | None |
| Census table definitions (CENSUS_DEFINITIONS) | **No significant differences found** | N/A | N/A |
| Income bins (4→8, 2000$→2010$) | **TM2-only** — do not change TM1 mode | N/A | N/A |
| Age bins (5→4) | **TM2-only** — do not change TM1 mode | N/A | N/A |
| Children control (B11005) | TM2-only | N/A | N/A |
| MAZ-level hierarchy | TM2-only | N/A | N/A |
| 2020 Census / 2019–2023 PUMS vintage | TM2-only by design | High | High |
| `postprocess_recode.py` unification | **Already done** — `tm2` version handles both modes | — | — |
| `create_seed_population.py` TM1 fields | **Already done** — `tm2` version computes all TM1 fields | — | — |

---

### 10.2 Vintage Gap in `master`'s TM2 Mode

`create_baseyear_controls.py` runs only for `MODELTYPE=TM2` on `master`. Its data sources are significantly out of date:

| Data source | `master` (legacy TM2) | `tm2` (modernized TM2) |
|---|---|---|
| MAZ block-level base | 2010 Decennial SF1 (`H13`, `P43`, `P12`) | 2020 Decennial PL 94-171 |
| ACS vintage | 2016 ACS5 (block group scaling) | 2023 ACS5 |
| PUMA definitions in crosswalk | **2000** (`puma2000` in the `.dbf` filename) | 2020 |
| PUMS vintage | 2017–2021 | 2019–2023 |
| Model years supported | 2010 and 2015 only (hard `ValueError` otherwise) | 2023 |

The 2000-vintage PUMA codes in the crosswalk combined with 2017–2021 PUMS data (which uses 2010 PUMA definitions) means the crosswalk is already one generation behind the PUMS in `master`. Moving `master` to 2019–2023 PUMS without rebuilding the crosswalk with 2020 PUMA definitions would cause silent geographic misassignment. Fully upgrading `master`'s TM2 controls pipeline to match `tm2` is essentially the scope of the `tm2` branch itself.

---

### 10.3 Python 3.x Compatibility Bugs

These affect `master`. TM1 `create_seed_population.py` is affected by 10.3.1 and 10.3.2. TM2 `create_baseyear_controls.py` is affected by all three.

#### 10.3.1 `df.append()` removed in pandas 2.0

```python
# master — BROKEN in pandas >= 2.0:
df = pandas.DataFrame()
for county_code in county_codes:
    county_df = pandas.DataFrame.from_records(...)
    df = df.append(county_df)
```

```python
# tm2 fix:
all_county_dfs = []
for county_code in county_codes:
    county_df = pd.DataFrame(...)
    all_county_dfs.append(county_df)
combined_df = pd.concat(all_county_dfs, ignore_index=True)
```

**Action:** Replace every `df = df.append(...)` with `pd.concat([df, new_df], ignore_index=True)` in `create_baseyear_controls.py` and `create_seed_population.py`.

#### 10.3.2 `dict.iteritems()` removed in Python 3

```python
# master — Python 2 only:
for control_name, control_val in control_dict.iteritems():
    ...
```

**Action:** Search-and-replace `iteritems()` → `items()` throughout `master`.

#### 10.3.3 `logging.warn()` removed in Python 3.12

```python
# master — deprecated:
logging.warn("  DROPPING Inf (sum {}):\n{}".format(...))
```

**Action:** Search-and-replace `logging.warn(` → `logging.warning(` throughout `master`.

---

### 10.4 Census API Robustness (TM2 mode on `master` only)

#### 10.4.1 Rate Limiting

`master` fires requests in a tight county loop with no delay. The Census API throttles at ~500 req/min.

```python
# tm2 utils/census_fetcher.py:
self.min_request_interval = 0.1  # 100ms between requests

def _rate_limit(self):
    elapsed = time.time() - self.last_request_time
    if elapsed < self.min_request_interval:
        time.sleep(self.min_request_interval - elapsed)
    self.last_request_time = time.time()
```

**Action:** Add `import time` and a 2-line rate-limit helper inside `CensusFetcher.get_census_data()`.

#### 10.4.2 JSON Error / `"N/A"` Value / Invalid API Key Handling

`master` uses `county_df.astype(float)` which crashes on Census-returned `"N/A"` strings (suppressed cells) and on HTML error responses (invalid API key).

```python
# tm2 fix — safe conversion:
for col in df.columns:
    if col not in ['state', 'county', 'tract', 'block', 'block group']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# tm2 also detects invalid API key:
if "You included a key with this request, however, it is not valid." in response.text:
    raise CensusApiException("Census API key is invalid")
```

`tm2` also adds `timeout=30` to every `requests.get()` call so a hung Census API call doesn't block the script forever.

**Action:**
1. Replace `county_df.astype(float)` with `pd.to_numeric(..., errors='coerce')` per column.
2. Add `timeout=30` to any direct `requests.get()` calls.
3. Check for `"N/A"` strings before aggregation.

---

### 10.5 Hardcoded `M:\` Paths in `master`

```python
# create_baseyear_controls.py:
MAZ_TAZ_DEF_FILE  = "M:\\Data\\GIS layers\\TM2_maz_taz_v2.2\\blocks_mazs_tazs.csv"
API_KEY_FILE       = "M:\\Data\\Census\\API\\api-key.txt"
LOCAL_CACHE_FOLDER = "M:\\Data\\Census\\CachedTablesForPopulationSimControls"

# create_seed_population.py:
PUMS_INPUT_DIR      = pathlib.Path("M:/Data/Census/PUMS/PUMS 2017-21")
PUMS_HOUSEHOLD_FILE = "hbayarea1721.csv"
PUMS_PERSON_FILE    = "pbayarea1721.csv"
```

**Recommended minimal fix** — collect at top of each file:

```python
# ==== CONFIGURATION ====
# Update these to match your local environment
CONFIG = {
    "MAZ_TAZ_DEF_FILE":    r"M:\Data\GIS layers\TM2_maz_taz_v2.2\blocks_mazs_tazs.csv",
    "CENSUS_API_KEY_FILE": r"M:\Data\Census\API\api-key.txt",
    "CENSUS_CACHE_FOLDER": r"M:\Data\Census\CachedTablesForPopulationSimControls",
    "PUMS_INPUT_DIR":      r"M:\Data\Census\PUMS\PUMS 2017-21",
}
# =======================
```

No logic changes — purely a maintainability improvement.

---

### 10.6 Census Table Definitions

The raw Census variable codes in `master`'s inline `CENSUS_DEFINITIONS` dict were compared against `tm2`'s `utils/config_census.py` for all shared tables (B01001, B08202, B11016, B19001, C24010). **No data-quality corrections were found.** The definitions are functionally identical; `tm2` simply stores them in a separate file.

**Tables in `tm2` not used by `master` TM2 mode:**

| Table | TM2 Usage | Notes |
|-------|-----------|-------|
| `B11005` | `hh_kids_yes/no` controls at TAZ | Would require new controls.csv entry |
| `B25003` | County-level HH scaling (ACS 1-yr) | County marginals approach differs |
| `H1_002N` (PL 2020) | MAZ `num_hh` base | 2020 Decennial only |
| `P1_001N` (PL 2020) | MAZ `total_pop` | 2020 Decennial only |
| `P5_008N/009N/010N` (PL 2020) | MAZ GQ by type | 2020 Decennial only |

---

### 10.7 `postprocess_recode.py`

The `tm2` branch version already handles **both TM1 and TM2** via `--model_type TM1` or `--model_type TM2`, with explicit `HOUSING_COLUMNS['TM1']` and `HOUSING_COLUMNS['TM2']` dicts, `hinccat1` calculation, and poverty level fields.

**Action:** `master` should adopt the `tm2` branch version — it is already backward-compatible with TM1.

---

### 10.8 `create_seed_population.py` — Scale and Compatibility

| Metric | `master` | `tm2` branch |
|--------|----------|--------------|
| Lines of code | ~660 | ~1,297 |
| Architecture | Procedural script | Classes + config |
| PUMS data year | 2017–2021 | 2019–2023 |
| PUMA geography | 2010 PUMAs | 2020 PUMAs |

- The `tm2` version already computes all TM1-required fields: `hh_income_2000`, `employ_status`, `student_status`, `person_type`, `gqtype`.
- The Python 3.x bugs from §10.3 also appear in `master`'s seed script.
- `tm2` uses `TM2Config` for paths and includes a `PUMSDownloader` class that can fetch PUMS data automatically from the Census Bureau. `master` uses hardcoded `M:\` paths.
- PUMA vintage mismatch: `master` crosswalk uses 2000-vintage PUMA codes; 2017–2021 PUMS uses 2010 definitions — they were never fully aligned even in `master`. See §10.2.

---

### 10.9 Prioritized Actions

**Priority 1 — Must Fix (Bugs)**  
Affect `master` across both TM1 and TM2 modes via `create_seed_population.py`; TM2 mode also via `create_baseyear_controls.py`.

1. Replace `df.append()` with `pd.concat()` everywhere
2. Replace `.iteritems()` with `.items()`
3. Replace `logging.warn()` with `logging.warning()`

Estimated effort: 2–3 hours. Risk: zero.

**Priority 2 — Should Do (robustness for TM2 mode on `master`)**

4. `pd.to_numeric(..., errors='coerce')` instead of `astype(float)` in `create_baseyear_controls.py`
5. Rate limiting (100ms) in Census API county loop
6. `timeout=30` on HTTP requests
7. Centralize hardcoded `M:\` paths to top-of-file config block

Estimated effort: 4–6 hours. Risk: low.

**Priority 3 — Consider**

8. Adopt `tm2` branch `postprocess_recode.py` in `master` (already handles both modes)
9. Evaluate retiring `master`'s TM2 mode in favor of the `tm2` branch for any work requiring updated Census vintages

**Do Not Port**
- Income bin changes (4→8, 2000$→2010$)
- Age bin restructuring (5→4 bins)
- Children controls (B11005)
- MAZ-level controls or 4-level geography hierarchy
- Any architectural complexity from `tm2_config.py` / `tm2_pipeline.py`

---

### 10.10 File-by-File Action Checklist

#### `create_baseyear_controls.py` (TM2 mode only)

- [ ] `df = df.append(county_df)` → `pd.concat([df, county_df])`
- [ ] All `.iteritems()` → `.items()`
- [ ] All `logging.warn(` → `logging.warning(`
- [ ] `county_df = county_df.astype(float)` → `pd.to_numeric` per column with `errors='coerce'`
- [ ] Add rate limiting (100ms) inside `get_census_data` county loop
- [ ] Move hardcoded path constants to top-of-file `CONFIG = {}` dict

#### `create_seed_population.py` (both TM1 and TM2 modes)

- [ ] Any `df.append()` → `pd.concat()`
- [ ] Any `.iteritems()` → `.items()`
- [ ] Move PUMS path constants to top-of-file `CONFIG = {}` dict

#### `postprocess_recode.py`

- [ ] Adopt `tm2` branch version (already handles both TM1 and TM2 modes)

---

## 11. Workplan

---

### Phase 0 — Merge `tm2` into `master`

**Goal:** Master gets the full modernized Python pipeline (`tm2_pipeline.py`, all analysis scripts, new docs, updated `create_baseyear_controls.py`, `create_seed_population.py`, `postprocess_recode.py`) without disrupting existing TM1 production runs.

**Merge mechanics (the easy part):**
- The merge produces only **one git conflict**: `run_populationsim.bat`, which `tm2` deleted but master kept modifying. Resolution: keep master's version.
- All other files are auto-resolved: master never touched the Python scripts after the branch split, so git takes `tm2`'s versions without conflict.
- A dry-run merge (`git merge --no-commit --no-ff tm2`) confirms: 412 files added, 10 modified, 57 deleted, **1 conflict** (the BAT).

**Pre-merge blockers G9 and G10 are both fixed.** All four BAT scripts are now TM1-safe.

**Execute:**

| Task | Command / action |
|------|------------------|
| 0a | ✅ G9: renamed `run_populationsim_synthesis.py` → `run_populationsim.py` (commit `9205914`) |
| 0b | ✅ G10: `--model_type TM1` added to `create_seed_population.py` (commit `aece8f1`) |
| 0c | `git checkout master` |
| 0d | `git merge tm2` |
| 0e | Resolve conflict: `bay_area/run_populationsim.bat` — `git checkout master -- bay_area/run_populationsim.bat` |
| 0f | `git add bay_area/run_populationsim.bat && git commit -m "Merge tm2 into master"` |
| 0g | Smoke-test TM1 BAT: run a single base year with `set MODELTYPE=TM1`; verify all 4 scripts run |
| 0h | Smoke-test TM2 Python: `python tm2_pipeline.py full --year 2023`; verify no regressions |

**What master gains from the merge (once safe):**
- `tm2_pipeline.py` — modern Python orchestration
- `run_all_summaries.py` — post-synthesis summary runner
- `create_baseyear_controls.py` — updated Census API pulls, Python 3 compatible
- `create_seed_population.py` — 2023 vintage, cleaner income/GQ handling
- `postprocess_recode.py` — already handles both `--model_type TM1` and `TM2`
- `analysis/` — all new analysis scripts
- `hh_gq/configs_TM1/` — already ported (Phase 1)
- `add_hhgq_combined_controls.py` — already ported (Phase 2)
- Updated docs

---

### ✅ Phase 1 — Git Cherry-Picks (complete)

| Task | Command | Gap closed |
|------|---------|------------|
| 1a | `git checkout master -- bay_area/hh_gq/configs_TM1` | G2 |
| 1b | `git checkout master -- bay_area/hh_gq/data/geo_cross_walk_tm1.csv` | G3 |
| 1c | `git checkout master -- bay_area/hh_gq/data/geo_cross_walk_tm2.csv` | G3 |

---

### ✅ Phase 2 — Port `add_hhgq_combined_controls.py` (complete)

`git checkout master -- bay_area/add_hhgq_combined_controls.py`. Test: `python add_hhgq_combined_controls.py --model_type TM1` with a real `taz_summaries.csv` (e.g. `C:\GitHub\travel-model-one\utilities\taz-data-baseyears\2023\TAZ1454 2023 Popsim Vars.csv`).

---

### ✅ Phase 3 — Design Decision: PUMA Vintage (G4) — **decided: Option A**

Option A: 2017–2021 PUMS (2010-vintage PUMAs) for TM1; 2019–2023 PUMS (2020-vintage) for TM2. Uses existing `geo_cross_walk_tm1.csv` without change; valid for any base year (2015, 2020, 2023). Implemented in `create_seed_population.py --model_type TM1` (commit `aece8f1`).

---

### Phase 4 — Add `--model_type` to `tm2_pipeline.py`

`create_seed_population.py` is done (commit `aece8f1`). Wire up the TM1 path in the pipeline.

#### 4a — Add `--model_type` argument

In `tm2_pipeline.py`, add a top-level argument:

```python
parser.add_argument("--model_type", choices=["TM1", "TM2"], default="TM2",
                    help="TM1 (TAZ geography) or TM2 (MAZ geography)")
```

Pass it through to `TM2Pipeline.__init__()` and store on `self.config`.

#### 4b — Guard the controls step

```python
def run_controls(self):
    if self.model_type == "TM1":
        # Controls come from travel-model-one; validate they exist
        taz_summaries = Path("hh_gq/data/taz_summaries.csv")
        if not taz_summaries.exists():
            raise FileNotFoundError(
                f"TM1 requires {taz_summaries}.\n"
                "Copy from: travel-model-one/utilities/taz-data-baseyears/YYYY/"
                "'TAZ1454 YYYY Popsim Vars.csv'"
            )
        self.run_command(
            [sys.executable, "add_hhgq_combined_controls.py", "--model_type", "TM1"],
            "add_hhgq_combined_controls (TM1)"
        )
    else:
        # existing TM2 path
        self.run_command([sys.executable, "create_baseyear_controls.py", ...], ...)
```

#### 4c — Switch PopulationSim config directory

```python
config_dir = f"hh_gq/configs_{self.model_type}"   # configs_TM1 or configs_TM2
self.run_command(
    [sys.executable, "run_populationsim.py",
     "--config", config_dir, "--output", str(output_dir), "--data", "hh_gq/data"],
    "populationsim"
)
```

#### 4d — Pass `--model_type` to `postprocess_recode.py`

```python
self.run_command(
    [sys.executable, "postprocess_recode.py",
     "--model_type", self.model_type, "--directory", str(output_dir), "--year", str(self.year)],
    "postprocess_recode"
)
```

**Note:** `postprocess_recode.py` on the `tm2` branch already handles both modes — no changes needed there.

#### ✅ 4e — `create_seed_population.py` (done)

`--model_type TM1` added. Selects 2017–2021 PUMS, reads `geo_cross_walk_tm1.csv`, converts income to `hh_income_2000` (CPI 2021→2000 = 172.2/258.8). Commit `aece8f1`.

#### 4f — Update `run_all_summaries.py` for TM1

`run_all_summaries.py` currently hardcodes TM2 output filenames and launches MAZ-specific scripts that do not apply to TM1. Changes needed:

1. **Required-files check** — the script checks for `households_{year}_tm2.csv` and `persons_{year}_tm2.csv`. Parameterize to use the correct suffix based on `--model_type`:
   ```python
   suffix = args.model_type.lower()   # "tm1" or "tm2"
   required_files = [
       output_dir / "populationsim_working_dir" / "output" / f"households_{args.year}_{suffix}.csv",
       ...
   ]
   ```

2. **Skip MAZ-only scripts for TM1** — the following scripts assume MAZ geography and should be skipped when `--model_type TM1`:
   - `MAZ_hh_comparison.py`
   - `maz_household_summary.py`
   - `create_interactive_taz_analysis.py` (uses MAZ data)
   - `analyze_taz_controls_vs_results.py` (currently references MAZ controls)

3. **TAZ-appropriate scripts to run for TM1:**
   - `analyze_syn_pop_model.py --model_type TM1` ✓ (already passes `--model_type`)
   - `analyze_full_dataset.py`
   - `compare_controls_vs_results_by_taz.py`
   - `compare_synthetic_populations.py`
   - `data_validation.py`

**Dependency:** Phases 1, 2, 3 complete.

---

### Phase 5 — Fix Bugs in `master`

These are bugs in the `master` branch. They do not affect the `tm2` branch (which already uses correct patterns). Can be done on a feature branch off `master` at any point, independent of the other phases.

| Task | File(s) | Change |
|------|---------|--------|
| 5a | `create_baseyear_controls.py`, `create_seed_population.py` | `df.append()` → `pd.concat()` |
| 5b | `create_baseyear_controls.py` | `.iteritems()` → `.items()` |
| 5c | `create_baseyear_controls.py` | `logging.warn(` → `logging.warning(` |
| 5d | `create_baseyear_controls.py` | `astype(float)` → `pd.to_numeric(..., errors='coerce')` |
| 5e | `create_baseyear_controls.py` | Add 100ms rate limiting in Census API loop |
| 5f | `create_baseyear_controls.py` | Add `timeout=30` to `requests.get()` |
| 5g | `create_baseyear_controls.py`, `create_seed_population.py` | Move `M:\` paths to top-of-file `CONFIG = {}` dict |
| 5h | `master` `postprocess_recode.py` | Replace with `tm2` branch version (already handles both modes) |

---

### Phase 6 — End-to-End TM1 Test Run

Validate the full TM1 pipeline on the `tm2` branch for the 2023 base year.

| Task | Command / action |
|------|-----------------|
| 6a | Copy `TAZ1454 2023 Popsim Vars.csv` from `travel-model-one` → `hh_gq/data/taz_summaries.csv` |
| 6b | `python tm2_pipeline.py full --model_type TM1 --year 2023` |
| 6c | Check `hh_gq/data/taz_summaries_hhgq.csv` — verify `numhh_gq` and `hh_size_1_gq` columns |
| 6d | Check `hh_gq/data/seed_households.csv` — verify `hh_income_2000` column populated |
| 6e | Verify PopulationSim runs with `configs_TM1` without error |
| 6f | Inspect `synthetic_households_recode.csv` — verify `HINC`, `UNITTYPE`, `VEHICL`, `PERSONS`, `hinccat1` |
| 6g | Inspect `synthetic_persons_recode.csv` — verify `AGE`, `SEX`, `pemploy`, `pstudent`, `ptype` |
| 6h | Run `python run_all_summaries.py --model_type TM1 --year 2023` — verify no crash on file-not-found for MAZ scripts |
| 6i | Run `summarize_synthpop_by_TAZ.py` on outputs; compare totals to `taz_summaries.csv` input |

**Key validation checks:**
- Regional household total from synthesis ≈ total from `taz_summaries.csv`
- `hinccat1` distribution matches expected income quartile shares
- No TAZs with `UNITTYPE` = NaN
- GQ persons in output match `gq_tot_pop` from controls
- `run_all_summaries.py` skips MAZ scripts gracefully and runs TAZ-compatible scripts without error

**Dependency:** Phases 1–4 complete.

---

### Phase 7 — Port TM1 Control Generation from R to Python *(future, independent)*

Currently TM1 controls are generated by R scripts in `travel-model-one` and copied in manually (see G8). This phase makes TM1 fully self-contained, matching TM2's `create_baseyear_controls.py` pattern.

| Task | Action |
|------|--------|
| 7a | Add `--model_type TM1` branch to `create_baseyear_controls.py` (or a new `create_tm1_controls.py`) |
| 7b | Pull ACS B19001 (income), B25009 (HH size), B08202 (workers), B01001 (age) via Census API |
| 7c | Fetch BLS CPI series for the target year; compute deflator to 2000 dollars |
| 7d | Rebin ACS income categories to `HHINCQ1–4` ($30k / $60k / $100k in 2000 dollars) |
| 7e | Pull Decennial PCT19 (GQ by type) for group quarters counts |
| 7f | Aggregate from block-group / tract to TAZ using the TM1 TAZ–block crosswalk |
| 7g | Write `hh_gq/data/taz_summaries.csv` in the same column format `add_hhgq_combined_controls.py` already expects |
| 7h | Remove the manual-copy step from `tm2_pipeline.py` TM1 mode; replace with the new Python call |
| 7i | Validate: compare Python output vs. R output for a known year (2023) column by column |

**Result:** `python tm2_pipeline.py full --model_type TM1 --year 2023` runs end-to-end with no R dependency and no manual file copy.

**Dependency:** Phase 6 passing. Otherwise independent of all other phases.
