
San Francisco Bay Area (MTC/ABAG) version of populationsim
==========================================================

To run:
```
run_populationsim.bat [year]
```

See [run_populationsim.bat](run_populationsim.bat).  This will:
1) Copy required controls into place.  
    1) For base/current years (2015, 2020, 2023), these come from the
   [`travel-model-one` repository](https://github.com/BayAreaMetro/travel-model-one/tree/master/utilities/taz-data-baseyears) under
   `utilities/taz-data-baseyears/[year]/`.
    1) For forecast years, these are
   [Bay Area UrbanSim](https://github.com/BayAreaMetro/bayarea_urbansim) output files.
2) Create the seed population (persons and housing units) from which to draw via [create_seed_population.py](create_seed_population.py)
3) Create combined controls for households/group quarters (e.g. make gq into one-person households) via [add_hhgq_combined_controls.py](add_hhgq_combined_controls.py)
4) Run populationsim to synthesize households and group quarters
5) Recode some variables via [postprocess_recode.py](postprocess_recode.py)

Output is written to `X:\populationsim_outputs\hh_gq\output_[OUTPUT_SUFFIX]_[year]_[BAUS_RUNNUM]\`.

The [validation.twb](validation.twb) workbook can be used to visualize the final `summary_melt.csv` in the output directory.

