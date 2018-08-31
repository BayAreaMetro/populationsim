
San Francisco Bay Area (MTC/ABAG) version of populationsim
==========================================================

To run:
```
run_populationsim.bat 2010|2015

```

This will:
1) Create the seed population (persons and housing units) from which to draw via [create_seed_population.py](create_seed_population.py)
2) Create the controls (for 2010 or 2015) using the Census API via [create_baseyear_controls.py](create_baseyear_controls.py)
3) Run populationsim to synthesize households
4) Run populationsim to synthesize group quarters
5) Put the results together via [combine_households_gq.py](combine_households_gq.py)

The [validation.twb](validation.twb) workbook can be used to visualize the final output_[model_year]/summary_melt.csv

Future year populationsim setup TBD.
