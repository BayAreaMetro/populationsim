---
layout: default
title: Guides
---

# Guides

Step-by-step guides for each component of the TM2 PopulationSim pipeline.

## Core Components

### [Geographic Crosswalk](geo-crosswalk.html)
Learn how geographic zones (MAZ, TAZ, PUMA, County) are linked together.

**Topics:**
- Zone definitions and relationships
- Crosswalk file structure
- Handling split geographies
- Validation procedures

### [Seed Population](seed-population.html)
Understand how the base microdata sample is created from PUMS data.

**Topics:**
- PUMS data download and filtering
- Variable recoding and mapping
- Household and person record linkage
- Quality checks

### [Control Generation](control-generation.html)
Learn how marginal control totals are created for each geography.

**Topics:**
- Data sources (ACS, Census)
- Control variable definitions
- Geographic aggregation
- Balancing procedures

### [Population Synthesis](population-synthesis.html)
Understand the core synthesis algorithm and configuration.

**Topics:**
- Iterative Proportional Fitting (IPF)
- Integerization methods
- Control balancing
- Convergence criteria

## Special Topics

### [Income Handling](income.html)
Detailed explanation of income adjustments, inflation, and binning.

**Topics:**
- CPI adjustment (2023 → 2010 dollars)
- ADJINC factor usage
- Income bin definitions
- Household vs. person income

### [Group Quarters Separation](group-quarters.html)
How group quarters (GQ) households are handled separately from traditional households.

**Topics:**
- GQ definition and types
- University vs. non-institutional GQ
- Control integration (hh_size_1)
- TAZ assignment

## Navigation

<div class="guide-nav">
  <div class="guide-card">
    <h4>📍 Geography</h4>
    <ul>
      <li><a href="geo-crosswalk.html">Geographic Crosswalk</a></li>
    </ul>
  </div>
  
  <div class="guide-card">
    <h4>📊 Data Preparation</h4>
    <ul>
      <li><a href="seed-population.html">Seed Population</a></li>
      <li><a href="control-generation.html">Control Generation</a></li>
    </ul>
  </div>
  
  <div class="guide-card">
    <h4>⚙️ Synthesis</h4>
    <ul>
      <li><a href="population-synthesis.html">Population Synthesis</a></li>
    </ul>
  </div>
  
  <div class="guide-card">
    <h4>🔍 Special Topics</h4>
    <ul>
      <li><a href="income.html">Income Handling</a></li>
      <li><a href="group-quarters.html">Group Quarters</a></li>
    </ul>
  </div>
</div>

---

[← Back to Home](../index.html)

<style>
.guide-nav {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin: 30px 0;
}

.guide-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  background: #f9f9f9;
}

.guide-card h4 {
  margin-top: 0;
  color: #0366d6;
}

.guide-card ul {
  margin: 0;
  padding-left: 20px;
}

.guide-card li {
  margin: 5px 0;
}
</style>
