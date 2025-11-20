---
layout: default
title: Getting Started
---

# Getting Started

Everything you need to set up and run the TM2 PopulationSim pipeline.

## Prerequisites

- Python 3.8+ (recommended: Anaconda/Miniconda)
- Git
- ~5GB disk space for data and outputs
- Windows, macOS, or Linux

## Setup Steps

1. **[Environment Setup](environment-setup.html)** - Install dependencies and configure Python environment
2. **[How to Run](how-to-run.html)** - Run the complete pipeline or individual steps

## Quick Start

```bash
# Activate the environment
conda activate popsim

# Navigate to project directory
cd C:/GitHub/populationsim/bay_area

# Run the full pipeline
python tm2_pipeline.py full
```

## What You'll Get

After running the pipeline, you'll have:
- Synthetic households and persons files
- Control totals by TAZ and MAZ
- Summary reports and validation outputs
- Visualization-ready data files

## Next Steps

- Learn about the [overall process](../process/overview.html)
- Understand the [data flow](../process/file-flow.html)
- Explore the [guides](../guides/) for specific components

---

[← Back to Home](../index.html)
