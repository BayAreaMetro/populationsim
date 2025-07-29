# Offline File Setup for Population Sim

This directory contains local copies of network input files for working offline with the population simulation scripts.

## Quick Start

### First Time Setup (Copy Network Files)
```bash
# Copy all network files to local storage
python copy_network_files.py
```

### Switch Between Network and Local Files
```bash
# Use local files (for offline work)
python toggle_files.py local

# Use network files (when connected to MTC network)  
python toggle_files.py network
```

### Check Current Mode
```bash
python -c "from tm2_control_utils.config import USE_LOCAL_FILES; print(f'Using local files: {USE_LOCAL_FILES}')"
```

## File Structure

```
input_2023/
├── copy_status.txt           # Status of last copy operation
├── gis/                      # GIS/geography files
│   ├── blocks_mazs_tazs.csv
│   ├── mazs_tazs_county_tract_PUMA10.csv
│   └── mazs_tazs_all_geog.csv
├── api/                      # Census API key
│   └── api-key.txt
└── census_cache/            # Cached census data tables
    ├── nhgis_*.csv          # NHGIS crosswalk files
    └── *.csv                # Census table cache files
```

## How It Works

The `tm2_control_utils/config.py` file has a `USE_LOCAL_FILES` toggle that automatically switches all file paths between:

- **Local mode** (`USE_LOCAL_FILES = True`): Uses files in `input_2023/` directory
- **Network mode** (`USE_LOCAL_FILES = False`): Uses original network paths on M: drive

## Scripts

- `copy_network_files.py` - Copies all network files to local directory
- `toggle_files.py` - Switches between local and network file modes
- Main scripts automatically detect the mode and verify file availability

## Troubleshooting

### Missing Files Error
If you get missing files errors:
1. Make sure you've run `python copy_network_files.py` first
2. Check that `USE_LOCAL_FILES = True` in `tm2_control_utils/config.py`
3. Verify files exist in the `input_2023/` directory

### Network Access Issues
If you can't access network files:
1. Make sure you're connected to the MTC network
2. Set `USE_LOCAL_FILES = False` using `python toggle_files.py network`

### Re-sync Files
To update local files with latest network versions:
```bash
python copy_network_files.py
```

This will overwrite existing local files with current network versions.
