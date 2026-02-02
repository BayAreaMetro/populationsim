TM2 Output Summaries — Primary Marginals and Crosswalks

Purpose

This file documents the primary marginal/summary CSVs produced by the control-generation and postprocessing pipeline. Each section includes the exact header (as detected in the current outputs) and a field-by-field short description.

1) MAZ marginals — `maz_marginals_hhgq.csv`

Header (current):
```
MAZ_NODE,numhh_gq,gq_type_univ,gq_type_noninst
```
Field descriptions
- MAZ_NODE: micro-zone identifier (2010-block based MAZ id)
- numhh_gq: number of household-equivalents = authoritative MAZ household count plus any GQ-as-1-person conversions; used for PopulationSim person-as-household handling
- gq_type_univ: university group quarters person count assigned to MAZ (from 2020 PL P5_008N)
- gq_type_noninst: combined non-institutional GQ counts (other non-institutional categories)

2) TAZ marginals — `taz_marginals_hhgq.csv`

Header (current):
```
TAZ_NODE,inc_lt_20k,inc_20k_45k,inc_45k_60k,inc_60k_75k,inc_75k_100k,inc_100k_150k,inc_150k_200k,inc_200k_plus,hh_wrks_0,hh_wrks_1,hh_wrks_2,hh_wrks_3_plus,pers_age_00_19,pers_age_20_34,pers_age_35_64,pers_age_65_plus,hh_kids_yes,hh_kids_no,hh_size_1,hh_size_2,hh_size_3,hh_size_4,hh_size_5,hh_size_6_plus,hh_size_1_gq
```
Field descriptions (abridged)
- TAZ_NODE: traffic analysis zone id
- inc_*: household counts by income bins (2023$ ranges as defined in `INCOME_BIN_MAPPING`)
- hh_wrks_*: households by worker-count buckets (0,1,2,3+)
- pers_age_*: person totals in specified age buckets
- hh_kids_yes / hh_kids_no: household counts with/without children
- hh_size_*: household size buckets (1..6+)
- hh_size_1_gq: TAZ-level size-1 bucket that includes GQ conversions (used for hh-size + GQ apples-to-apples comparisons)

3) County marginals — `county_marginals.csv`

Header (current):
```
COUNTY,pers_occ_management,pers_occ_professional,pers_occ_services,pers_occ_retail,pers_occ_manual_military
```
Field descriptions
- COUNTY: local county numeric code (MTC ordering)
- pers_occ_*: occupational group totals derived from ACS (C24010) aggregated to county; categories are management, professional, services, retail/sales, and manual/military combined

4) Geography crosswalk — `geo_cross_walk_tm2_maz.csv` (canonical)

Header (current):
```
MAZ_NODE,TAZ_NODE,COUNTY,county_name,PUMA
```
Field descriptions
- MAZ_NODE: MAZ id (2010-block based)
- TAZ_NODE: TAZ id
- COUNTY: county numeric code
- county_name: full county name
- PUMA: PUMA id of the block (used for PUMS mapping)

5) Final synthetic outputs (reference)
- `synthetic_households.csv` and `synthetic_persons.csv` — see `docs/TM2_INPUT_FIELDS.md` for exact current headers and descriptions. Sample rows are embedded in the main `docs/TM2_OUTPUTS.md`.

Next steps toward documenting ALL output summaries
- I can enumerate every CSV under `output_2023/populationsim_working_dir/data/` and `.../output/`, extract headers and the first data row, and auto-generate a section per file in this doc. That will produce a comprehensive `docs/TM2_OUTPUT_SUMMARIES.md` that documents every generated summary file. Shall I generate that full enumeration now? If yes, I will run it and commit the generated doc.

Notes
- Where a field name is ambiguous or historically inconsistent (several files use slightly different names like `num_hh` vs `numhh_gq` or `integer_weight` vs `integerized_weight`), I will also add a short "equivalent names" note to help mapping between runs.
 
## TAZ Analysis Summaries

*Updated: 2026-02-02 from latest synthesis run*

Below are the TAZ-level summary CSV snapshots created by `analysis/analyze_taz_controls_vs_results.py`. These summaries compare the marginal controls (targets) against the synthesized population results.

### Regional Summary Statistics

| Metric | Value |
|--------|-------|
| Total TAZs analyzed | 4,925 |
| Total households (control) | 2,957,345 |
| Total households (result) | 2,958,534 |
| Regional difference | +1,189 (+0.04%) |
| Households with GQ matching perfectly | 99.88% of TAZs |

### taz_analysis_summary.csv (regional variable summary)

This file contains per-variable statistics across all TAZs, including control totals, result totals, differences, and fit metrics (R², RMSE, MAPE).

```csv
variable,total_control,total_result,total_diff,total_diff_pct,mae,rmse,mape,r_squared,perfect_matches,perfect_pct,taz_count
numhh,2830328.0,2847491,17163.0,0.61,6.54,50.08,37.72,0.9848,2991,60.73,4925
numhh_gq,2957345.0,2958534,1189.0,0.04,0.24,12.19,0.01,0.9992,4919,99.88,4925
hh_gq_university,51581.0,44249,-7332.0,-14.21,2.72,49.48,13.61,0.8887,4720,95.84,4925
hh_gq_noninstitutional,75242.0,66794,-8448.0,-11.23,3.98,14.40,20.79,0.9511,3067,62.27,4925
hh_size_1,985683.0,725206,-260477.0,-26.43,69.78,163.78,33.18,0.4801,129,2.62,4925
hh_size_2,1241147.0,902409,-338738.0,-27.29,87.24,206.01,29.77,0.3112,61,1.24,4925
hh_size_3,642739.0,478294,-164445.0,-25.59,45.13,93.75,34.28,0.4223,182,3.70,4925
hh_size_4,557472.0,430251,-127221.0,-22.82,41.96,84.12,38.37,0.4757,260,5.28,4925
hh_size_5,225861.0,185827,-40034.0,-17.73,18.15,35.37,40.59,0.5853,966,19.61,4925
hh_size_6_plus,145322.0,125504,-19818.0,-13.64,12.68,28.10,38.94,0.6480,1704,34.60,4925
hh_wrks_0,788304.0,602086,-186218.0,-23.62,50.35,92.49,31.52,0.5359,73,1.48,4925
hh_wrks_1,1426200.0,1040016,-386184.0,-27.08,99.67,228.12,30.31,0.3181,46,0.93,4925
hh_wrks_2,1230988.0,924433,-306555.0,-24.90,88.40,207.16,30.03,0.2769,65,1.32,4925
hh_wrks_3_plus,352746.0,280956,-71790.0,-20.35,25.50,51.18,33.82,0.5208,246,5.00,4925
pers_age_00_19,1685880.0,1672647,-13233.0,-0.78,63.38,111.30,30.79,0.8820,51,1.04,4925
pers_age_20_34,1565155.0,1572738,7583.0,0.48,59.85,126.27,32.09,0.8192,41,0.83,4925
pers_age_35_64,3080520.0,3077790,-2730.0,-0.09,103.55,152.80,35.33,0.8990,20,0.41,4925
pers_age_65_plus,1247140.0,1244776,-2364.0,-0.19,41.52,60.19,43.06,0.9165,56,1.14,4925
hh_kids_yes,1138532.0,925019,-213513.0,-18.75,75.03,155.97,33.85,0.4782,106,2.15,4925
hh_kids_no,2659700.0,1922472,-737228.0,-27.72,190.73,415.46,33.09,0.2648,25,0.51,4925
inc_lt_20k,283464.0,216791,-66673.0,-23.52,18.98,46.34,27.64,0.6179,885,17.97,4925
inc_20k_45k,343505.0,266739,-76766.0,-22.35,21.67,46.92,30.09,0.6031,533,10.82,4925
inc_45k_60k,211193.0,165023,-46170.0,-21.86,13.32,30.77,28.02,0.6433,978,19.86,4925
inc_60k_75k,216096.0,167591,-48505.0,-22.45,13.96,30.08,29.00,0.6442,953,19.35,4925
inc_75k_100k,343679.0,267857,-75822.0,-22.06,21.54,44.42,29.89,0.6070,498,10.11,4925
inc_100k_150k,601172.0,459980,-141192.0,-23.49,39.03,82.66,31.35,0.4617,201,4.08,4925
inc_150k_200k,484672.0,359885,-124787.0,-25.75,33.85,85.12,33.08,0.3666,322,6.54,4925
inc_200k_plus,1314471.0,941178,-373293.0,-28.40,96.98,243.10,33.41,0.4115,193,3.92,4925
```

### Key Performance Metrics Interpretation

- **R² (R-squared)**: Coefficient of determination; values closer to 1.0 indicate better fit
- **RMSE**: Root Mean Square Error; lower values indicate better per-TAZ accuracy
- **MAPE**: Mean Absolute Percentage Error; lower values indicate better relative accuracy
- **perfect_pct**: Percentage of TAZs where control exactly matches result

### taz_population_summary.csv (per-TAZ population summary)
Header + first rows (current):

```csv
id,total_pop_control,total_pop_result,total_pop_diff,total_pop_pct_error
1,1387.0,1075,-312.0,-22.49459264599856
2,2109.0,2241,132.0,6.258890469416785
3,2562.0,2527,-35.0,-1.366120218579235
4,1377.0,2130,753.0,54.68409586056645
5,1398.0,1387,-11.0,-0.7868383404864091
6,1064.0,473,-591.0,-55.545112781954884
7,907.0,1117,210.0,23.15325248070562
8,902.0,881,-21.0,-2.328159645232816
9,940.0,1028,88.0,9.361702127659575
10,1051.0,1126,75.0,7.1360608943863
11,1306.0,899,-407.0,-31.16385911179173
12,849.0,818,-31.0,-3.651354534746761
13,1882.0,2029,147.0,7.810839532412326
14,1404.0,1664,260.0,18.51851851851852
15,987.0,1142,155.0,15.704154002026344
16,1850.0,1969,119.0,6.432432432432432
17,2241.0,2406,165.0,7.362784471218206
18,1790.0,2223,433.0,24.18994413407821
19,1718.0,1622,-96.0,-5.587892898719441
20,1437.0,1280,-157.0,-10.925539318023661
21,1061.0,1348,287.0,27.04995287464656
22,758.0,636,-122.0,-16.094986807387862
23,773.0,904,131.0,16.946959896507117
24,995.0,1044,49.0,4.924623115577889
25,1119.0,1444,325.0,29.0437890974084
26,532.0,669,137.0,25.75187969924812
27,4388.0,5035,647.0,14.744758432087512
28,1664.0,1239,-425.0,-25.540865384615387
29,929.0,885,-44.0,-4.736275565123789
30,417.0,641,224.0,53.71702637889688
31,922.0,1678,756.0,81.99566160520607
32,844.0,866,22.0,2.6066350710900474
33,1201.0,1434,233.0,19.40049958368027
34,1385.0,1351,-34.0,-2.454873646209386
35,2431.0,2466,35.0,1.439736733854381
36,2258.0,2336,78.0,3.454384410983171
37,1528.0,1805,277.0,18.1282722513089
38,3147.0,3483,336.0,10.676835081029552
39,1178.0,1038,-140.0,-11.884550084889643
40,1512.0,1833,321.0,21.23015873015873
41,962.0,1274,312.0,32.432432432432435
42,2262.0,2140,-122.0,-5.393457117595048
43,1120.0,1373,253.0,22.589285714285715
44,955.0,2117,1162.0,121.67539267015708
45,1252.0,1270,18.0,1.4376996805111821
46,811.0,1101,290.0,35.75832305795315
47,1144.0,1099,-45.0,-3.9335664335664338
48,867.0,751,-116.0,-13.379469434832755
49,784.0,1154,370.0,47.19387755102041
50,1181.0,1233,52.0,4.403048264182896
51,1222.0,877,-345.0,-28.23240589198036
52,844.0,909,65.0,7.701421800947868
````



