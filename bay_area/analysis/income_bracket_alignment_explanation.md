# Income Bracket Alignment Analysis: 2023 Data → 2010 Dollar Synthetic Population

## Executive Summary

The PopulationSim TM2 pipeline uses **2023 ACS data** to create a **synthetic population with 2010-dollar income values** for downstream travel modeling work. This creates a complex income bracket alignment challenge that requires careful handling of dollar year conversions.

## The Challenge: Multi-Year Dollar Alignment

| Component | Dollar Year | Purpose | Example Income Brackets |
|-----------|-------------|---------|------------------------|
| **ACS 2023 Source Data** | 2023 dollars | Census reference for population characteristics | $0-10K, $10K-15K, $15K-20K, etc. |
| **TAZ Controls (Current)** | 2023 dollars | Aggregated controls for PopulationSim | $0-40K, $40K-75K, $75K-125K, $125K+ |
| **PUMS 2023 Seed Data** | 2023 dollars | Individual household records for synthesis | Actual household incomes in 2023 $ |
| **Synthetic Population (Target)** | **2010 dollars** | Final output for travel modeling | Households with incomes inflated back to 2010 $ |

## Current Status: TAZ Controls vs ACS Reference

| Income Category | TAZ Controls (2023$) | ACS Reference (2023$) | Match Quality |
|-----------------|---------------------|----------------------|---------------|
| **Low Income** | 0-$40K (15.3%) | 0-$41K (15.6%) | ✅ Excellent (-0.4pp) |
| **Low-Mid Income** | $40K-75K (13.7%) | $41K-83K (16.5%) | ⚠️ Partial overlap |
| **Mid-High Income** | $75K-125K (18.1%) | $83K-138K (19.2%) | ⚠️ Partial overlap |
| **High Income** | $125K+ (52.9%) | $138K+ (48.7%) | ✅ Good (+4.3pp) |

## Why the Analysis Shows "Dollar Year Mismatch"

The analysis detected potential issues because:

1. **Bracket Naming Convention**: TAZ control variables are named `hh_inc_30`, `hh_inc_30_60`, etc., suggesting 2010 dollars
2. **Actual Bracket Values**: But the brackets are defined as $0-40K, $40K-75K, etc. (2023 dollars)
3. **Comparison Logic**: The analysis expected 2010-dollar brackets but found 2023-dollar brackets

This is **not actually a problem** - it's the intended design for the multi-step conversion process.

## The Conversion Pipeline

```
ACS 2023 Data (2023$) 
    ↓
TAZ Controls (2023$) ← We are here
    ↓
PopulationSim Synthesis (2023$)
    ↓
Income Inflation to 2010$ ← Final step
    ↓
Synthetic Population (2010$) ← Target for travel modeling
```

## Validation Results

| Metric | Value | Status |
|--------|--------|--------|
| **Total Households** | 3,037,458 | ✅ Regional total validated |
| **Geographic Coverage** | 4,734 TAZs, 9 Counties | ✅ Complete coverage |
| **Low Income Alignment** | TAZ 15.3% vs ACS 15.6% | ✅ Within 0.4pp |
| **County Rollups** | All counties properly mapped | ✅ No missing mappings |

## Income Distribution by County (TAZ Controls - 2023$)

| County | Total HH | 0-40K | 40K-75K | 75K-125K | 125K+ |
|--------|----------|-------|---------|----------|-------|
| San Francisco | 451,203 | 18.6% | 11.7% | 15.3% | 54.5% |
| San Mateo | 271,524 | 12.0% | 12.9% | 16.2% | 58.9% |
| Santa Clara | 694,486 | 12.2% | 11.3% | 16.4% | 60.1% |
| Alameda | 671,299 | 16.8% | 13.8% | 17.9% | 51.4% |
| Contra Costa | 417,744 | 14.9% | 14.7% | 20.1% | 50.4% |
| Solano | 160,125 | 17.5% | 19.1% | 25.3% | 38.0% |
| Napa | 50,119 | 17.2% | 17.4% | 21.4% | 44.0% |
| Sonoma | 192,921 | 17.1% | 18.8% | 23.8% | 40.3% |
| Marin | 128,037 | 14.0% | 14.4% | 17.8% | 53.8% |

## Next Steps

1. **✅ COMPLETE**: TAZ controls generation with ACS-aligned brackets
2. **🔄 PENDING**: PopulationSim synthesis using 2023$ controls and PUMS data  
3. **🔄 PENDING**: Final income conversion from 2023$ to 2010$ for synthetic households
4. **🔄 PENDING**: Validation of vehicle ownership distribution with properly aligned income controls

## Technical Notes

- The "dollar year mismatch" warning in the analysis is expected behavior
- TAZ controls correctly use 2023-dollar brackets aligned with ACS B19001 table structure
- Final 2010-dollar conversion happens during or after PopulationSim synthesis
- Current low-income alignment (15.3% vs 15.6%) is excellent and should improve vehicle ownership modeling

---
*Generated: August 17, 2025*  
*Analysis: TAZ Controls Rollup Validation*
