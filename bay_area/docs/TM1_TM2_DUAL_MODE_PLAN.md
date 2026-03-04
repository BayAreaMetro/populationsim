# TM1 + TM2 Dual-Mode Pipeline Plan



This document specifies every step in the population synthesis pipeline for both TM1 and TM2,
documents the exact inputs and outputs at each step, and identifies the gaps that must be closed
to make the `tm2` branch code support TM1 synthesis as well as TM2.

---

## Gaps Checklist

| # | Gap | Status |
|---|-----|--------|
| G1 | `add_hhgq_combined_controls.py` — cherry-pick from `master` | ✅ done (commit `fd124cd`) |
| G2 | `hh_gq/configs_TM1/` directory — cherry-pick from `master` | ✅ done (commit `fd124cd`) |
| G3 | `geo_cross_walk_tm1.csv` — cherry-pick from `master` | ✅ done (commit `fd124cd`) |
| G4 | PUMA vintage mismatch — [team decision required](#g4--puma-vintage-mismatch-seed-population) | ⏸ blocked |
| G5 | `tm2_pipeline.py` has no `--model_type` argument | ☐ not started |
| G6 | `run_all_summaries.py` hardcodes TM2 filenames | ☐ not started |

## Implementation Checklist

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Git cherry-picks — configs, crosswalks | ✅ complete |
| 2 | Port `add_hhgq_combined_controls.py` | ✅ complete |
| 3 | PUMA vintage design decision (G4) | ⏸ blocked — team decision |
| 4 | Wire `--model_type` into `tm2_pipeline.py` | ⏸ blocked on Phase 3 |
| 5 | Fix Python 3.x bugs in `master` | ☐ independent, not started |
| 6 | End-to-end TM1 test run | ⏸ blocked on Phase 4 |

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
| `master` | **TM1-default**, but also runs TM2 (older vintage) via `set MODELTYPE=TM2` | `run_populationsim.bat` (BAT file) | Active production use for TM1 |
| `tm2` | **TM2-only** currently; goal of this plan is to add TM1 support | `tm2_pipeline.py` (Python) | Modernized 2023 vintage; missing TM1 configs + scripts |

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
Step T1-D  run_populationsim_synthesis.py     PopulationSim library (TAZ geography)
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
Step T2-D  run_populationsim_synthesis.py     PopulationSim library (MAZ geography)
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

**Gap:** This script does not exist in the `tm2` branch. It must be added or its logic incorporated elsewhere.

---

### Step T1-C / T2-A — create_seed_population.py

**Script:** `create_seed_population.py` (exists in both branches, but differs in vintage)

#### TM1 seed requirements

| Item | `master` branch | `tm2` branch (current) |
|------|-----------------|------------------------|
| PUMS vintage | 2017–2021 5-year | 2019–2023 5-year |
| PUMA definitions | 2010 Census (labeled "2010" in master's code) | 2020 Census |
| Crosswalk file | `geo_cross_walk_tm1.csv` (PUMA→COUNTY, 2000-vintage PUMAs) | `geo_cross_walk_tm2_maz.csv` |
| `hh_income_2000` | Yes — `hh_income_2021 / 1.81` | **Already computed** (tm2 branch computes both) |
| `TYPEHUGQ` | Set on seed HHs | **Already set** |
| `hh_workers_from_esr` | Set on seed HHs | **Already set** |
| `gqtype` on persons | Set (1=univ, 2=mil, 3=othnon) | **Already set** |
| Age groups | Set via AGEP | **Already set** |

> **Key finding:** The `tm2` branch `create_seed_population.py` already computes `hh_income_2000`,
> `TYPEHUGQ`, `hh_workers_from_esr`, `gqtype`, and all person-type fields needed by TM1 controls.
> The main gap is the **PUMA vintage** and **crosswalk file**.

#### Crosswalk files needed

| Mode | File | Columns | PUMA vintage |
|------|------|---------|--------------|
| TM1 | `hh_gq/data/geo_cross_walk_tm1.csv` | `TAZ, PUMA, COUNTY, county_name, REGION` | 2000 Census PUMAs |
| TM2 | `hh_gq/data/geo_cross_walk_tm2_maz.csv` | `MAZ, TAZ, PUMA, COUNTY, county_name, REGION` | 2020 Census PUMAs |

The seed population is filtered to Bay Area PUMAs using whichever crosswalk is active. Using 2020 PUMS+2020 PUMAs for TM1 synthesis means the PUMA definitions will not match the `geo_cross_walk_tm1.csv` PUMA codes (2000 vintage). **This is the principal PUMA vintage mismatch.**

**Options:**
- A) Build a **separate TM1 seed** from 2017–2021 PUMS + 2000-vintage PUMA filter
- B) Build a **2020-PUMA to TAZ crosswalk** for TM1 (updated PUMA definitions applied to TM1 TAZ geography)
- C) (Simplest for now) Add `--model_type` flag to `create_seed_population.py` and swap the crosswalk file

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

## 4. Gap Analysis — What Must Be Added to `tm2` Branch

### G1 — `add_hhgq_combined_controls.py`

**Status:** Missing from `tm2` branch entirely.  
**Action:** Port this script from `master` or integrate its TM1 logic into `tm2_pipeline.py`.

The TM1 logic is simple (≈30 lines):
1. Rename uppercase R-output columns to lowercase
2. `numhh_gq = TOTHH + gq_tot_pop`
3. `hh_size_1_gq = hh_size_1 + gq_tot_pop`

### G2 — `hh_gq/configs_TM1/` directory

**Status:** Missing from `tm2` branch (confirmed: `git ls-tree -r HEAD --name-only | grep hh_gq` returns no config files).  
**Action:** Copy `configs_TM1/settings.yaml`, `configs_TM1/controls.csv`, `configs_TM1/logging.yaml` from `master` branch.

### G3 — `hh_gq/data/geo_cross_walk_tm1.csv`

**Status:** Missing from `tm2` branch.  
**Action:** Copy from `master` branch. Columns: `TAZ, PUMA, COUNTY, county_name, REGION`.  
**PUMA vintage note:** The file uses 2000-vintage PUMA codes. The tm2 branch PUMS
uses 2020-vintage PUMA codes. See G4.

### G4 — PUMA Vintage Mismatch (Seed Population)

**Status:** Critical design decision required.

#### Why PUMA vintage matters

PUMA is not merely a filter used by `create_seed_population.py` — it is the **`seed_geography`** in the TM1 PopulationSim config:

```yaml
# hh_gq/configs_TM1/settings.yaml
geographies: [COUNTY, PUMA, TAZ]
seed_geography: PUMA
```

PopulationSim uses PUMA codes to match each seed household to its set of eligible TAZs during balancing. If the PUMA code in a seed household record does not match any PUMA code in `geo_cross_walk_tm1.csv`, that household cannot be placed and will be dropped or cause errors.

#### Where each PUMA code comes from

| Component | PUMA vintage | Source / evidence |
|-----------|-------------|-------------------|
| `geo_cross_walk_tm1.csv` | **2000** | Built from `mazs_TM2_v2_2_intersect_puma2000.dbf`; code comments in `create_baseyear_controls.py` say `# NOTE these are PUMA 2000` and doc says "joins MAZs and TAZs to the **2000 PUMAs** (used in the 2007–2011 PUMS)" |
| `master` PUMS (`create_seed_population.py`, 2017–2021) | **2010** | `PUMA` column in 2017–2021 PUMS follows 2010 Census PUMA definitions |
| `tm2` branch PUMS (2019–2023) | **2020** | `PUMA` column in 2019–2023 PUMS follows 2020 Census PUMA definitions |

#### Master already has a latent mismatch

The `master` branch crosswalk uses 2000-vintage PUMAs, but the PUMS it reads (2017–2021) uses 2010-vintage PUMA codes. These are **not the same**. Whether this has caused silent errors in past runs, or whether Bay Area PUMA boundary changes between 2000 and 2010 were small enough not to matter in practice, is unknown. The `tm2` branch introduces an additional shift to 2020-vintage PUMAs, which redefined boundaries more substantially.

The 2000-vintage short codes (e.g. `7503`, `101`, `8512`) are immediately distinguishable from 2010/2020 five-digit codes (e.g. `01101`, `07503`). PopulationSim would fail to match any seed household to the crosswalk if the vintage codes do not align.

The 2000-vintage PUMAs in `geo_cross_walk_tm1.csv` will not match the 2020-vintage PUMA codes in the 2019–2023 PUMS used by `create_seed_population.py` on the `tm2` branch.

**Options (choose one):**

| Option | Description | Tradeoff |
|--------|-------------|----------|
| **A — Dual-vintage PUMS** | Download both 2017–2021 PUMS (2010 PUMAs) and 2019–2023 PUMS (2020 PUMAs); use different vintage by `--model_type` | Most accurate; methodologically correct for any base year; larger data footprint |
| **B — Updated TM1 crosswalk** | Create a new `geo_cross_walk_tm1_2020puma.csv` mapping 2020 PUMAs to TM1 TAZs (GIS work) | No additional PUMS download; valid for 2023 base year only — **not valid for 2015** |

For a 2023 base year, Option B is simpler (no extra PUMS download). For a 2015 base year, Option A is required.

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

### 10.11 Files Examined During This Analysis

| File | `master` lines | `tm2` lines | Notes |
|---|---|---|---|
| `create_baseyear_controls.py` | 1,245 | 4,414 | Full `master`; key `tm2` functions |
| `create_seed_population.py` | ~660 | ~1,297 | Full `master`; columns + harmonize fn |
| `postprocess_recode.py` | 233 | 233 | Same structure, both modes present |
| `utils/census_fetcher.py` | N/A | 690 | `tm2` only |
| `utils/config_census.py` | N/A | 1,401 | `tm2` only |
| `hh_gq/configs_TM1/settings.yaml` | — | — | Confirmed TAZ geography |
| `hh_gq/configs_TM2/settings.yaml` | — | — | Confirmed MAZ geography |
| `hh_gq/configs_TM1/controls.csv` | — | — | Full TM1 control list |
| `hh_gq/configs_TM2/controls.csv` | — | — | Full TM2 control list |
| `run_populationsim.bat` | — | — | Confirmed MODELTYPE switch mechanism |

---

## 11. Workplan: Implementing Dual-Mode TM1 + TM2 Support

---

### ✅ Phase 1 — Git Cherry-Picks (complete)

These files exist in `master` and just need to be brought into the `tm2` branch.

| Task | Command | Gap closed |
|------|---------|------------|
| 1a | `git checkout master -- bay_area/hh_gq/configs_TM1` | G2 |
| 1b | `git checkout master -- bay_area/hh_gq/data/geo_cross_walk_tm1.csv` | G3 |
| 1c | `git checkout master -- bay_area/hh_gq/data/geo_cross_walk_tm2.csv` | G3 |

After: verify both crosswalk files look correct; check PUMA codes in `geo_cross_walk_tm1.csv` match expected 2000-vintage format (`7503`, `02204`, etc., **not** 5-digit 2020 codes like `00101`).

**Dependency:** None. Do this first.

---

### ✅ Phase 2 — Port `add_hhgq_combined_controls.py`  (complete)

This script exists on `master` handling both TM1 and TM2. Port it to the `tm2` branch.

| Task | Action | Gap closed |
|------|--------|------------|
| 2a | `git checkout master -- bay_area/add_hhgq_combined_controls.py` | G1 |
| 2b | Test the TM1 path in isolation: run `python add_hhgq_combined_controls.py --model_type TM1` with a real `taz_summaries.csv` | G1 |

The TM1 logic (~35 lines) does:
- Lowercase rename of any uppercase R output columns
- `numhh_gq = TOTHH + gq_tot_pop`
- `hh_size_1_gq = hh_size_1 + gq_tot_pop`
- Write `hh_gq/data/taz_summaries_hhgq.csv`

A real `taz_summaries.csv` for testing is at:
```
C:\GitHub\travel-model-one\utilities\taz-data-baseyears\2023\TAZ1454 2023 Popsim Vars.csv
```
Copy it to `hh_gq/data/taz_summaries.csv` to test.

**Dependency:** Needs Phase 1 (for crosswalk); otherwise independent.

---

### Phase 3 — Design Decision: PUMA Vintage (G4)

**This is the critical team decision that gates Phase 4.**

The `tm2` branch `create_seed_population.py` uses 2019–2023 PUMS with **2020-vintage PUMA codes**. The TM1 crosswalk `geo_cross_walk_tm1.csv` uses **2000-vintage PUMA codes**. These two PUMA systems are incompatible — 2020 PUMA codes cannot be looked up in the 2000-vintage crosswalk.

**Three options (choose one):**

| Option | Description | What it takes | Best for |
|--------|-------------|---------------|----------|
| **A — Dual-vintage PUMS** | Download 2017–2021 PUMS (2010-vintage PUMAs) separately for TM1; keep 2019–2023 PUMS for TM2 | ~4 GB additional download; branching in `create_seed_population.py` on `--model_type` | Any base year (2015, 2020, 2023); methodologically cleanest |
| **B — New TM1 crosswalk with 2020 PUMAs** | Build `geo_cross_walk_tm1_2020puma.csv` mapping 2020-vintage PUMA codes to TM1 TAZs (GIS work); use single PUMS download | GIS overlay of 2020 PUMA boundaries with TM1 TAZ boundaries | 2023 base year only — **not valid for 2015** |

**For a 2023 base year:** Option B avoids a separate PUMS download. The 2020 PUMA → TM1 TAZ crosswalk can be derived from the existing TM2 crosswalk (TM2 already maps `PUMA 2020 → TAZ`; TM1 TAZs are a subset of the same system).  
**For a 2015 base year:** Option A is required — 2019–2023 PUMS do not represent 2015 conditions.

**Decision needed from team before Phase 4 can begin.**

---

### Phase 4 — Add `--model_type` to `tm2_pipeline.py`

Once the PUMA vintage decision (Phase 3) is made, wire up the TM1 path in the pipeline.

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

#### 4e — Handle `create_seed_population.py`

Depending on Phase 3 decision:
- **Option A:** Add `--model_type` flag to `create_seed_population.py` to pick between 2017–2021 PUMS (TM1) and 2019–2023 PUMS (TM2).
- **Option B:** Add `--crosswalk` flag (or derive from `--model_type`) to point to the correct crosswalk file.

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
