"""
build_census_block_maz_cross.py

Creates a crosswalk CSV linking Census blocks, block groups, tracts, MAZ, TAZ, county, and PUMA for use in controls generation.

- Input: blocks_mazs_tazs_2.5.csv from tm2py-utils (should have block, MAZ, TAZ, county, PUMA info)
- Output: geo_cross_walk_blocks.csv (with columns: GEOID_block, GEOID_block_group, GEOID_tract, MAZ, TAZ, COUNTY, PUMA)

This script is intended to be run before controls generation if the crosswalk is missing or needs to be rebuilt.
"""

import pandas as pd
import os
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))
from unified_tm2_config import UnifiedTM2Config

config = UnifiedTM2Config()

# Use config for input and output paths
TM2PY_BLOCKS_FILE = config.EXTERNAL_PATHS['blocks_file']
OUTPUT_BLOCK_CROSSWALK = config.CROSSWALK_FILES['block_crosswalk']
OUTPUT_ALL_GEOG_CROSSWALK = config.CROSSWALK_FILES['all_geog_crosswalk']

# Ensure output directory exists
OUTPUT_BLOCK_CROSSWALK.parent.mkdir(parents=True, exist_ok=True)

# Read the input file
if not TM2PY_BLOCKS_FILE.exists():
    raise FileNotFoundError(f"Input file not found: {TM2PY_BLOCKS_FILE}")

blocks = pd.read_csv(TM2PY_BLOCKS_FILE, dtype=str)


# The input file has columns: GEOID10, maz, taz
blocks.rename(columns={'GEOID10': 'GEOID_block', 'maz': 'MAZ', 'taz': 'TAZ'}, inplace=True)


# Derive block group and tract from block GEOID
blocks['GEOID_block group'] = blocks['GEOID_block'].str[:12]  # Note the space!
blocks['GEOID_tract'] = blocks['GEOID_block'].str[:11]

# Only keep available columns
needed_cols = ['GEOID_block', 'GEOID_block group', 'GEOID_tract', 'MAZ', 'TAZ']
crosswalk = blocks[needed_cols].drop_duplicates()

# Save to both canonical and legacy locations (for compatibility)
crosswalk.to_csv(OUTPUT_BLOCK_CROSSWALK, index=False)
crosswalk.to_csv(OUTPUT_ALL_GEOG_CROSSWALK, index=False)
print(f"Wrote crosswalk: {OUTPUT_BLOCK_CROSSWALK} and {OUTPUT_ALL_GEOG_CROSSWALK} ({len(crosswalk)} rows)")
