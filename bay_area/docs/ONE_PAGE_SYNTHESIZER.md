Title: Bay Area Population Synthesizer — Quick Summary for Modelers

Purpose

This one-page summary highlights the unique design choices in our population synthesizer — intended for modelers who already understand the purpose and mechanics of synthesis. It focuses only on the features that distinguish our pipeline: geographic resolution and crosswalks, the exact control marginals used, and the reference year(s) of source data.

Geographies (how we allocate population)

- County (9-county Bay Area): used for regional controls, reporting, and county-level scaling.
- TAZ_NODE (Traffic Analysis Zones): primary mapping unit used for producing mapping outputs and tableau exports. TAZ-level marginals and results are used for synthesis inputs where available.
- MAZ_NODE (Micro Analysis Zones / parcel-level-like): included in pipelines that support MAZ merges and when MAZ-level marginals are present.
- Group Quarters (GQ) handling: GQ households/persons are assigned to TAZs (and included in hh_size_1 at the TAZ level). The TAZ marginals already include hhgq in the hh_size_1 bucket (source-dependent). GQ counts are also preserved as separate controls: hh_gq_university and hh_gq_noninstitutional.

Exact Controls (the variables fed to the synthesizer)

Household controls (household counts):
- numhh_gq — total households including GQ (used as the canonical total)
- hh_size_1, hh_size_2, hh_size_3, hh_size_4, hh_size_5, hh_size_6_plus
- hh_gq_university, hh_gq_noninstitutional (kept as separate GQ categories)
- hh_wrks_0, hh_wrks_1, hh_wrks_2, hh_wrks_3_plus (household worker count categories)
- hh_kids_yes, hh_kids_no (presence of children)

Person controls (person counts by attribute):
- pers_age_00_19, pers_age_20_34, pers_age_35_64, pers_age_65_plus
- pers_occ_management, pers_occ_professional, pers_occ_services, pers_occ_retail, pers_occ_manual_military (occupation buckets)

Income controls (household income bins):
- inc_lt_20k, inc_20k_45k, inc_45k_60k, inc_60k_75k, inc_75k_100k, inc_100k_150k, inc_150k_200k, inc_200k_plus

Notes on control columns and weight fields

- control_value: the raw marginal supplied (may be unbalanced or sourced from a different dataset). Historically used for reporting and comparisons to external totals.
- COUNTY_balanced_weight / COUNTY_integer_weight: balanced (float) and integerized versions after raking/IPF and integerization; these sum consistently to the final county totals and are suitable when you require exact additive consistency for aggregations.
- TAZ/Taz-node results use distinct columns (e.g., hh_size_1_control, hh_size_1_result) and may include GQ already included in hh_size_1 depending on the marginal source.

Reference year(s) and data sources

- Primary marginal/control years available in the repository: 2010 and 2015 control totals (files: control_totals_maz_year_2010.csv and control_totals_maz_year_2015.csv). The analysis and example runs used 2015 controls for historical comparison; outputs and pipelines have been exercised against 2023-run outputs (folder: output_2023) for the most recent synthesis/testing.
- Person microdata: PUMS / ACS microdata aligned to the same reference year as controls (see project notes). If you need a strict citation (e.g., ACS 2015 5-year PUMS), ask and we’ll insert exact source citations.

Practical guidance for modelers (short)

- If you want additive consistency across aggregations (TAZ → county → region), use the balanced/integer weight columns rather than raw control_value marginals.
- TAZ-level hh_size_1 often already includes group-quarters in our marginals; double-check your input marginals before deciding whether to add GQ separately in the synthesizer input.
- When rerunning synthesis after fixing control sources, verify these three things: (1) the control totals (numhh_gq) at each geography, (2) whether hh_size_1 already contains hhgq in that geography, and (3) that your synthesizer's target file uses integerized/balanced weights or normalized controls depending on the desired comparison semantics.

Contact / follow-up

If you want, I can produce a Word (.docx) version of this page, or expand it into a 2–3 page technical appendix with exact sample CSV column headers and a small checklist for preparing synthesis inputs.

(End of one-page summary)


