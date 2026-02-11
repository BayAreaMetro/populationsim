# TM2 PopulationSim Documentation Site Map

```
🏠 Home (index.md)
│   Bay Area PopulationSim Documentation
│   - Quick summary for modelers
│   - Key features and controls
│   - Navigation cards to all sections
│
├─📂 Getting Started (/getting-started/)
│   │
│   ├─ 📄 Environment Setup (environment-setup.md)
│   │   • Prerequisites and installation
│   │   • Conda environment creation
│   │   • Verification and troubleshooting
│   │
│   └─ 📄 How to Run (how-to-run.md)
│       • Quick start guide
│       • Running individual steps
│       • Configuration and paths
│       • Expected outputs
│
├─📂 Process Overview (/process/)
│   │
│   ├─ 📄 Overall Process (overview.md)
│   │   • PUMS data download
│   │   • Geographic crosswalk
│   │   • Seed population creation
│   │   • Control generation
│   │   • Population synthesis
│   │   • Post-processing
│   │
│   └─ 📄 File Flow (file-flow.md)
│       • Input file descriptions
│       • Intermediate files
│       • Output specifications
│       • Data lineage
│
├─📂 Guides (/guides/)
│   │
│   ├─ 📄 Geographic Crosswalk (geo-crosswalk.md)
│   │   • Zone definitions (MAZ, TAZ, PUMA, County)
│   │   • Crosswalk file structure
│   │   • Handling split geographies
│   │
│   ├─ 📄 Seed Population (seed-population.md)
│   │   • PUMS data preparation
│   │   • Variable recoding
│   │   • Record linkage
│   │
│   ├─ 📄 Control Generation (control-generation.md)
│   │   • ACS/Census data sources
│   │   • Control variable definitions
│   │   • Geographic aggregation
│   │
│   ├─ 📄 Population Synthesis (population-synthesis.md)
│   │   • IPF algorithm
│   │   • Integerization methods
│   │   • Convergence criteria
│   │
│   ├─ 📄 Income Handling (income.md)
│   │   • CPI adjustment
│   │   • ADJINC factor
│   │   • Income binning
│   │
│   └─ 📄 Group Quarters (group-quarters.md)
│       • GQ definitions and types
│       • University vs. non-institutional
│       • TAZ assignment
│
├─📂 Outputs (/outputs/)
│   │
│   ├─ 📄 Input Fields Reference (input-fields.md)
│   │   • Household attributes
│   │   • Person attributes
│   │   • Geographic identifiers
│   │   • Weight fields
│   │
│   ├─ 📄 Output Summaries (summaries.md)
│   │   • Regional summaries
│   │   • County aggregations
│   │   • Control vs. result comparisons
│   │
│   └─ 📄 TAZ-Level Outputs (taz-summaries.md)
│       • TAZ summary file structure
│       • Control matching performance
│       • Export formats
│
├─📂 Reference (/reference/)
│   │   Detailed Technical Documentation (350-550 lines each)
│   │
│   ├─ 📄 TM1 vs TM2 Comparison (TM1-TM2-COMPARISON.md) ⭐ NEW
│   │   • Geographic structure differences
│   │   • Control variable comparison
│   │   • Output format differences
│   │   • Refactoring tradeoff analysis
│   │
│   ├─ 📄 TM2 Full Reference (TM2_FULL_REFERENCE.md)
│   ├─ 📄 Detailed Output Guide (DETAILED_OUTPUT_GUIDE.md)
│   ├─ 📄 Detailed Synthesis Guide (DETAILED_SYNTHESIS_GUIDE.md)
│   ├─ 📄 Detailed Input Data Guide (DETAILED_INPUT_DATA_GUIDE.md)
│   ├─ 📄 Detailed Crosswalk Guide (DETAILED_CROSSWALK_GUIDE.md)
│   └─ 📄 Detailed Control Generation Guide (DETAILED_CONTROL_GENERATION_GUIDE.md)
│
└─📂 Images (/images/)
    36 visualization images
    • County-level analysis plots
    • TAZ-level analysis plots
    • Performance summaries
```

---

## Cross-Link Structure

### From Home Page
→ All section index pages

### From Getting Started
→ Process Overview
→ Guides (component-specific)
→ Outputs

### From Process Overview
→ Getting Started (setup)
→ Guides (detailed components)

### From Guides
→ Related guides
→ Process Overview
→ Reference (detailed docs)

### From Outputs
→ Process Overview
→ Guides

### From Reference
→ Home
→ All other sections

---

## Page Hierarchy

```
Level 1: Home
│
├─ Level 2: Section Indexes
│   ├─ Getting Started
│   ├─ Process Overview
│   ├─ Guides
│   ├─ Outputs
│   └─ Reference
│
└─ Level 3: Content Pages
    ├─ getting-started/environment-setup.md
    ├─ getting-started/how-to-run.md
    ├─ process/overview.md
    ├─ process/file-flow.md
    ├─ guides/*.md (6 files)
    ├─ outputs/*.md (3 files)
    └─ reference/*.md (6 files)
```

---

## Content by Size

### Quick Reference (< 100 lines)
- ONE_PAGE_SYNTHESIZER (home page content)
- GEO_CROSSWALK
- SEED_POPULATION
- POPULATION_SYNTHESIS
- README_INCOME
- household_gq_separation

### Standard Guides (100-250 lines)
- HOW_TO_RUN
- ENVIRONMENT_SETUP
- CONTROL_GENERATION
- PROCESS_OVERVIEW
- TM2_OUTPUT_SUMMARIES
- TM2_INPUT_FIELDS
- TM2_OUTPUT_SUMMARIES_TAZ
- FILE_FLOW

### Detailed Reference (350-550 lines)
- DETAILED_CONTROL_GENERATION_GUIDE (356 lines)
- DETAILED_CROSSWALK_GUIDE (405 lines)
- TM2_FULL_REFERENCE (459 lines)
- DETAILED_INPUT_DATA_GUIDE (467 lines)
- DETAILED_SYNTHESIS_GUIDE (533 lines)
- DETAILED_OUTPUT_GUIDE (553 lines)

---

## Navigation Patterns

### Card-Based Navigation
- Home page: 4 quick access cards
- Guides index: 4 category cards
- Section indexes: List-based with descriptions

### Breadcrumb Links
Every page has:
- Parent section link
- Home link
- Related documentation links

### Contextual Links
- Inline links to related topics
- "Next Steps" sections
- "Related Documentation" sections

---

## Theme & Styling

**Theme**: Cayman (GitHub-style clean theme)

**Custom Styling**:
- Navigation card grids
- Hover effects
- Responsive layout
- Consistent typography

**Color Scheme**:
- Links: #0366d6 (GitHub blue)
- Backgrounds: #f9f9f9 (light gray)
- Borders: #ddd (subtle gray)

---

## File Statistics

| Section | Files | Purpose |
|---------|-------|---------|
| Root | 4 | Config, home, setup instructions |
| Getting Started | 3 | Setup and running |
| Process | 3 | Workflow understanding |
| Guides | 7 | Component details |
| Outputs | 4 | Output documentation |
| Reference | 7 | Technical deep-dives |
| Images | 36 | Visualizations |
| **Total** | **64 docs** | Complete site |

---

## URL Structure

```
Base: https://bayareametro.github.io/populationsim/

Pages:
├─ /                                    (Home)
├─ /getting-started/                    (Getting Started index)
├─ /getting-started/environment-setup.html
├─ /getting-started/how-to-run.html
├─ /process/                            (Process index)
├─ /process/overview.html
├─ /process/file-flow.html
├─ /guides/                             (Guides index)
├─ /guides/geo-crosswalk.html
├─ /guides/seed-population.html
├─ /guides/control-generation.html
├─ /guides/population-synthesis.html
├─ /guides/income.html
├─ /guides/group-quarters.html
├─ /outputs/                            (Outputs index)
├─ /outputs/input-fields.html
├─ /outputs/summaries.html
├─ /outputs/taz-summaries.html
├─ /reference/                          (Reference index)
└─ /reference/[detailed docs].html
```

---

## Next Actions

1. ✅ Enable GitHub Pages in repository settings
2. ✅ Set branch to `tm2`, path to `/docs`
3. ✅ Wait 1-2 minutes for build
4. ✅ Visit: https://bayareametro.github.io/populationsim/
5. ✅ Share with team!

**Site is ready to go live!** 🚀
