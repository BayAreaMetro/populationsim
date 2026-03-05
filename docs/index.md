---
layout: default
title: Home
---

# Bay Area PopulationSim Documentation

Welcome to the TM2 (Travel Model 2) Population Synthesizer documentation for the San Francisco Bay Area.

## Quick Summary for Modelers

This population synthesizer creates realistic household and person records for transportation modeling in the 9-county Bay Area. It uses Census PUMS microdata and applies controls to match known demographic totals at the TAZ (Traffic Analysis Zone) level.

### Key Features

- **Geographic Resolution**: County → TAZ → MAZ (Micro Analysis Zones)
- **Population**: 2,958,470 households, 7,563,557 persons across 5,117 TAZs
- **Data Source**: 2023 5-year American Community Survey PUMS
- **Controls**: Household size, workers, income, age, occupation, group quarters

### Quick Navigation

<div class="nav-grid">
  <div class="nav-card">
    <h3>🚀 Getting Started</h3>
    <ul>
      <li><a href="getting-started/environment-setup.html">Environment Setup</a></li>
      <li><a href="getting-started/how-to-run.html">How to Run</a></li>
    </ul>
  </div>
  
  <div class="nav-card">
    <h3>📊 Process</h3>
    <ul>
      <li><a href="process/overview.html">Process Overview</a></li>
      <li><a href="process/file-flow.html">File Flow</a></li>
    </ul>
  </div>
  
  <div class="nav-card">
    <h3>📖 Guides</h3>
    <ul>
      <li><a href="guides/geo-crosswalk.html">Geographic Crosswalk</a></li>
      <li><a href="guides/seed-population.html">Seed Population</a></li>
      <li><a href="guides/control-generation.html">Control Generation</a></li>
      <li><a href="guides/population-synthesis.html">Population Synthesis</a></li>
      <li><a href="guides/income.html">Income Handling</a></li>
      <li><a href="guides/group-quarters.html">Group Quarters</a></li>
    </ul>
  </div>
  
  <div class="nav-card">
    <h3>📈 Outputs</h3>
    <ul>
      <li><a href="outputs/input-fields.html">Input Fields</a></li>
      <li><a href="outputs/summaries.html">Output Summaries</a></li>
      <li><a href="outputs/taz-summaries.html">TAZ Summaries</a></li>
    </ul>
  </div>
  
  <div class="nav-card">
    <h3>📚 Reference</h3>
    <ul>
      <li><a href="https://github.com/BayAreaMetro/populationsim/blob/tm2/bay_area/docs/TM1_TM2_DUAL_MODE_PLAN.md">TM1+TM2 Merge Plan</a></li>
      <li><a href="reference/TM2_FULL_REFERENCE.html">TM2 Full Reference</a></li>
    </ul>
  </div>
</div>

---

## What is PopulationSim?

PopulationSim is a synthetic population generator that creates realistic household and person records for transportation modeling. The TM2 pipeline synthesizes a population for the 9-county San Francisco Bay Area.

### Overall Process Flow

```
PUMS Data → Geographic Crosswalk → Seed Population → 
Marginal Controls → PopulationSim → Synthetic Population
```

### Geographic Framework

- **Region**: 9-county San Francisco Bay Area
- **Counties**: San Francisco, San Mateo, Santa Clara, Alameda, Contra Costa, Solano, Napa, Sonoma, Marin
- **TAZs**: 5,117 Traffic Analysis Zones
- **MAZs**: 41,434 Micro Analysis Zones
- **PUMAs**: 62 Public Use Microdata Areas

### Exact Controls Used

**Household Controls:**
- Total households (including group quarters)
- Household size (1, 2, 3, 4, 5, 6+ persons)
- Workers per household (0, 1, 2, 3+ workers)
- Presence of children (yes/no)
- Group quarters (university, non-institutional)

**Person Controls:**
- Age groups (0-19, 20-34, 35-64, 65+)
- Occupation categories (management, professional, services, retail, manual/military)

**Income Controls:**
- 8 income bins from <$20k to $200k+

---

## Detailed Reference Documentation

For advanced users and developers, comprehensive technical guides are available:

- [TM2 Full Reference](reference/TM2_FULL_REFERENCE.html) - Complete technical reference
- [Detailed Output Guide](reference/DETAILED_OUTPUT_GUIDE.html) - All output files and formats
- [Detailed Synthesis Guide](reference/DETAILED_SYNTHESIS_GUIDE.html) - IPF algorithm details
- [Detailed Input Data Guide](reference/DETAILED_INPUT_DATA_GUIDE.html) - Data sources and preparation
- [Detailed Crosswalk Guide](reference/DETAILED_CROSSWALK_GUIDE.html) - Geographic relationships
- [Detailed Control Generation Guide](reference/DETAILED_CONTROL_GENERATION_GUIDE.html) - Control marginals

---

## Quick Links

- **Source Repository**: [BayAreaMetro/populationsim](https://github.com/BayAreaMetro/populationsim)
- **Branch**: tm2
- **Questions?** Open an issue on GitHub

---

<style>
.nav-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin: 30px 0;
}

.nav-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  background: #f9f9f9;
  transition: transform 0.2s, box-shadow 0.2s;
}

.nav-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.nav-card h3 {
  margin-top: 0;
  font-size: 1.3em;
}

.nav-card a {
  text-decoration: none;
  color: #0366d6;
}

.nav-card p {
  color: #666;
  margin-bottom: 0;
}
</style>
