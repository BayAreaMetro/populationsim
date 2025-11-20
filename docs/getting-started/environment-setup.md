---
layout: default
title: Environment Setup
nav_order: 1
parent: Getting Started
---

# Environment Setup Guide

Step-by-step instructions to set up the PopulationSim TM2 environment on your machine.

## Prerequisites

- Git installed
- Anaconda or Miniconda installed
- Windows 10/11, macOS, or Linux
- ~5GB disk space

## Quick Setup

### 1. Clone Repository

```bash
# Clone repository
git clone https://github.com/BayAreaMetro/populationsim.git
cd populationsim
git checkout tm2
```

### 2. Create Conda Environment

```bash
# Create environment from minimal specification
conda env create -f bay_area/environment_minimal.yml

# Activate environment
conda activate popsim

# Verify Python version (should be 3.8.20)
python --version
```

> **Important**: Python 3.8 is required. Do not use Python 3.12 due to compatibility issues with PopulationSim dependencies.

### 3. Verify Installation

```bash
cd bay_area

# Test PopulationSim import
python -c "import populationsim; print('PopulationSim installed:', populationsim.__file__)"

# Run environment verification
python setup_environment.py
```

### 4. You're Ready!

Proceed to [How to Run](how-to-run.html) to execute the pipeline.

---

## Alternative: Windows Batch Script

For Windows users, use the provided activation script:

```cmd
cd bay_area
activate_environment.bat
```

This script will:
- Find your conda installation automatically
- Activate the popsim environment
- Verify the installation
- Display usage instructions

---

## Environment Details

### Tested Configuration

| Component | Version/Details |
|-----------|----------------|
| **OS** | Windows 10/11, macOS, Linux |
| **Python** | 3.8.20 (REQUIRED) |
| **Conda Env** | popsim |
| **PopulationSim** | Development version from repo |

### Key Package Versions

- pandas==2.0.3
- numpy==1.21.0
- activitysim==1.1.0
- geopandas==0.13.2
- ortools==9.12.4544
- dask (required for PopulationSim)

### Environment Files

| File | Purpose |
|------|---------|
| `environment_minimal.yml` | Recommended environment specification |
| `environment_export.yml` | Complete exact environment |
| `environment_exact.txt` | Pip-format package list |
| `requirements.txt` | Legacy pip requirements (use .yml instead) |
| `activate_environment.bat` | Windows activation helper |
| `setup_environment.py` | Environment verification script |

---

## Troubleshooting

### Common Issues

#### "Python was not found"
**Solution**: Make sure conda environment is activated
```bash
conda activate popsim
python --version
```

#### "conda: command not found"
**Solutions**:
- Restart terminal or run `conda init`
- Use full path to conda: `C:\Users\[USERNAME]\AppData\Local\anaconda3\condabin\conda.bat`

#### Package version conflicts
**Solution**: Always use `environment_minimal.yml`
```bash
# Remove old environment
conda env remove -n popsim

# Recreate fresh
conda env create -f bay_area/environment_minimal.yml
```

#### "No module named 'dask'"
**Solution**: Install dask in the environment
```bash
conda activate popsim
conda install -c conda-forge dask
```

#### PopulationSim import errors
**Solution**: Ensure development install was completed
```bash
cd populationsim
pip install -e .

# Verify
python -c "import populationsim; print(populationsim.__file__)"
```

### Environment Verification Script

Run this Python snippet to verify your setup:

```python
import sys
print(f"Python version: {sys.version}")

import pandas as pd
print(f"Pandas version: {pd.__version__}")

import populationsim
print(f"PopulationSim path: {populationsim.__file__}")

import dask
print(f"Dask version: {dask.__version__}")

print("\n✓ Environment setup successful!")
```

---

## Related Documentation

- **Next**: [How to Run](how-to-run.html) - Run the pipeline
- [Process Overview](../process/overview.html) - Understand the workflow
- [File Flow](../process/file-flow.html) - Data inputs and outputs

---

[← Back to Getting Started](index.html) | [Home](../index.html)
