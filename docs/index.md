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
- **Population**: ~2.5M households, ~7.5M persons across 4,735 TAZs
- **Data Source**: 2023 5-year American Community Survey PUMS
- **Controls**: Household size, workers, income, age, occupation, group quarters

### Quick Navigation

<div class="nav-grid">
  <div class="nav-card">
    <h3><a href="getting-started/">🚀 Getting Started</a></h3>
    <p>Setup environment and run your first synthesis</p>
  </div>
  
  <div class="nav-card">
    <h3><a href="process/">📊 Process Overview</a></h3>
    <p>Understand the synthesis pipeline and data flow</p>
  </div>
  
  <div class="nav-card">
    <h3><a href="guides/">📖 Guides</a></h3>
    <p>Step-by-step guides for each component</p>
  </div>
  
  <div class="nav-card">
    <h3><a href="outputs/">📈 Outputs</a></h3>
    <p>Understanding input fields and output data</p>
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
- **Counties**: SF, San Mateo, Santa Clara, Alameda, Contra Costa, Solano, Napa, Sonoma, Marin
- **TAZs**: 4,735 Traffic Analysis Zones
- **MAZs**: 39,587 Micro Analysis Zones
- **PUMAs**: 104 Public Use Microdata Areas

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

## Documentation Sections

### [Getting Started](getting-started/)
- [Environment Setup](getting-started/environment-setup.html)
- [How to Run](getting-started/how-to-run.html)

### [Process Overview](process/)
- [Overall Process](process/overview.html)
- [File Flow](process/file-flow.html)

### [Guides](guides/)
- [Geographic Crosswalk](guides/geo-crosswalk.html)
- [Seed Population](guides/seed-population.html)
- [Control Generation](guides/control-generation.html)
- [Population Synthesis](guides/population-synthesis.html)
- [Income Handling](guides/income.html)
- [Group Quarters Separation](guides/group-quarters.html)

### [Outputs](outputs/)
- [Input Fields Reference](outputs/input-fields.html)
- [Output Summaries](outputs/summaries.html)
- [TAZ-Level Outputs](outputs/taz-summaries.html)

### [Detailed Reference](reference/)
Complete technical documentation for advanced users and developers.

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
