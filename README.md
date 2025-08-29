# Bay Area PopulationSim Pipeline

This repository generates synthetic population and land use inputs for the Bay Area’s Travel Model Two (TM2), using PUMS and census data.

## Quick Start

1. **Set up your environment:**  
   See [bay_area/docs/ENVIRONMENT_SETUP.md](bay_area/docs/ENVIRONMENT_SETUP.md)

2. **Run the pipeline:**  
   ```sh
   python tm2_pipeline.py
   ```

3. **Review outputs:**  
   See [bay_area/docs/FILE_FLOW.md](bay_area/docs/FILE_FLOW.md) for details on output files and their locations.

## Pipeline Step Documentation

- [Crosswalk Step (Geographic Crosswalk Creation)](bay_area/docs/CROSSWALK_STEP.md)
- [Control Generation Step](bay_area/docs/CONTROL_GENERATION_STEP.md)
- [Seed Population Creation Step](bay_area/docs/SEED_POPULATION_STEP.md)
- [Population Synthesis Step](bay_area/docs/POPULATION_SYNTHESIS.md)

## Full Documentation

Full documentation is in the [`bay_area/docs/`](bay_area/docs/) folder:

- [How to Run the Pipeline](bay_area/docs/HOW_TO_RUN.md)
- [Environment Setup](bay_area/docs/ENVIRONMENT_SETUP.md)
- [File Flow and Outputs](bay_area/docs/FILE_FLOW.md)
- [Setup Instructions](bay_area/docs/SETUP_INSTRUCTIONS.md)

## Support

For questions or issues, please open an issue or consult the documentation.

---

*See the [`bay_area/docs/`](bay_area/docs/) folder for full details on configuration, usage, and troubleshooting.*

---

PopulationSim
=============

[![Build Status](https://travis-ci.org/activitysim/populationsim.svg?branch=master)](https://travis-ci.org/ActivitySim/populationsim) [![Coverage Status](https://coveralls.io/repos/ActivitySim/populationsim/badge.png?branch=master)](https://coveralls.io/r/ActivitySim/populationsim?branch=master)<a href="https://medium.com/zephyrfoundation/populationsim-the-synthetic-commons-670e17383048"><img src="https://github.com/ZephyrTransport/zephyr-website/blob/gh-pages/img/badging/project_pages/populationsim/PopulationSim.png" width="72.6" height="19.8"></a>

PopulationSim is an open platform for population synthesis.  It emerged
from Oregon DOT's desire to build a shared, open, platform that could be
easily adapted for statewide, regional, and urban transportation planning
needs.  PopulationSim is implemented in the
[ActivitySim](https://github.com/activitysim/activitysim) framework.

## Documentation

https://activitysim.github.io/populationsim/