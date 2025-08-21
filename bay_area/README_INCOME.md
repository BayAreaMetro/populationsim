# Income Dollar-Year Handling in the Bay Area PopulationSim Pipeline

This document describes how household income fields and dollar-years are handled at each stage of the pipeline, from seed generation to final output.

---

## 1. Seed Population (`seed_households.csv`, `seed_persons.csv`)
- **Fields:** Both `hh_income_2010` (2010 dollars) and `hh_income_2023` (2023 dollars) are present.
- **How they're created:** The seed generation script (`create_seed_population_tm2_refactored.py`) computes both fields for each household. The 2023$ value is typically the original ACS/PUMS value, and the 2010$ value is calculated using a CPI conversion.
- **Purpose:** This dual-field approach allows flexibility for control generation and synthesis in either dollar-year.

## 2. Controls (`controls.csv`)
- **Income bin expressions:** All income bin controls use the `households.hh_income_2023` field in their expressions (e.g., `(households.hh_income_2023 >= 45000) & (households.hh_income_2023 <= 59999)`).
- **Bin boundaries:** The bins themselves are defined in 2023 dollars, matching the latest ACS binning and public reporting.
- **How they're created:** The control generation script (`create_baseyear_controls_23_tm2.py`) and config (`config_census.py`) use the 2023$ bins and generate expressions referencing `hh_income_2023`.

## 3. Control Generation Outputs (`taz_marginals.csv`, `maz_marginals.csv`, etc.)
- **Income bins:** All marginal files report household counts in bins defined by 2023$ boundaries, using the `hh_income_2023` field for bin assignment.
- **Purpose:** This ensures that all control totals and marginal files are aligned with current ACS reporting and public data.

## 4. Population Synthesis (PopulationSim)
- **Field used for synthesis:** The synthesizer uses the `hh_income_2023` field from the seed population and the 2023$ bin expressions from the controls.
- **Process:** Households are assigned to bins and synthesized using 2023$ income values throughout the control matching and fitting process.

## 5. Postprocessing/Final Output
- **Conversion:** After synthesis, the final output is converted from 2023$ back to 2010$ using the precomputed `hh_income_2010` field in the seed population.
- **Purpose:** This allows for backward compatibility with legacy TM2 model components and reporting, which expect 2010$.

## 6. Configuration and Mapping (`config_census.py`, `unified_tm2_config.py`)
- **Bin definitions:** `INCOME_BIN_MAPPING` in `config_census.py` defines both 2010$ and 2023$ boundaries for each bin, but the pipeline uses the 2023$ bins for all control and synthesis steps.
- **Paths and workflow:** `unified_tm2_config.py` manages all file paths and ensures consistency across the pipeline.

---

## Summary Table

| Step/File                | Field Used           | Dollar-Year | Notes                                                      |
|--------------------------|---------------------|-------------|------------------------------------------------------------|
| Seed Population          | hh_income_2010, hh_income_2023 | 2010$, 2023$ | Both fields present for each household                     |
| Controls (controls.csv)  | hh_income_2023      | 2023$       | All bin expressions and boundaries use 2023$               |
| Marginals/Outputs        | hh_income_2023      | 2023$       | All binning and reporting in 2023$                         |
| Population Synthesis     | hh_income_2023      | 2023$       | Synthesis and control matching use 2023$                   |
| Final Output/Postprocess | hh_income_2010      | 2010$       | Output converted to 2010$ for legacy compatibility         |

---

All steps are designed to ensure that the pipeline is ACS-aligned and future-proof, while still supporting legacy TM2 model requirements.
