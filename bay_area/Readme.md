
San Francisco Bay Area (MTC/ABAG) version of populationsim
==========================================================

To run:
```
run_populationsim.bat [year]

```

See [run_populationsim.bat](run_populationsim.bat).  This will:
1) Copy required controls into place.  For forecast years, these are [Bay Area UrbanSim](https://github.com/BayAreaMetro/bayarea_urbansim) output files.  For 2015, this comes from [petrale](https://github.com/BayAreaMetro/petrale/tree/master/applications/travel_model_lu_inputs/2015)
2) Create the seed population (persons and housing units) from which to draw via [create_seed_population.py](create_seed_population.py)
3) Create combined controls for households/group quarters (e.g. make gq into one-person households) via [add_hhgq_combined_controls.py](add_hhgq_combined_controls.py)
4) Run populationsim to synthesize households and group quarters
5) Recode some variables via [postprocess_recode.py](postprocess_recode.py)

The [validation.twb](validation.twb) workbook can be used to visualize the final output_[model_year]/summary_melt.csv

