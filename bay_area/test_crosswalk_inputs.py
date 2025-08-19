import pandas as pd
from pathlib import Path
from unified_tm2_config import config

# 1. Check columns and a few rows of each input file
BLOCKS_FILE = config.EXTERNAL_PATHS['blocks_file']
print(f"\n[BLOCKS FILE] {BLOCKS_FILE}")
blocks = pd.read_csv(BLOCKS_FILE, dtype=str)
print(blocks.head())
print("Columns:", list(blocks.columns))

# 2. Test merge logic on a small sample

# Use actual column names from the blocks file
maz_col = 'maz' if 'maz' in blocks.columns else 'MAZ'
taz_col = 'taz' if 'taz' in blocks.columns else 'TAZ'
maz_sample = blocks[[maz_col]].drop_duplicates().head(10)

# Simulate a small MAZ/TAZ/PUMA/COUNTY DataFrame
maz_with_counties = pd.DataFrame({
    maz_col: maz_sample[maz_col],
    taz_col: [str(i) for i in range(10)],
    'PUMA': [str(1000 + i) for i in range(10)],
    'COUNTY_FIPS': [str(1 + i) for i in range(10)],
    'COUNTY_NAME': [f"County_{i}" for i in range(10)]
})

merge_test = pd.merge(
    blocks.head(20),
    maz_with_counties,
    on=maz_col,
    how='left'
)
print("\n[MERGE TEST SAMPLE]")
print(merge_test.head())

# 3. Validate output crosswalk for missing/null values
OUTPUT_CROSSWALK = config.CROSSWALK_FILES['main_crosswalk']
if Path(OUTPUT_CROSSWALK).exists():
    crosswalk = pd.read_csv(OUTPUT_CROSSWALK, dtype=str)
    print(f"\n[OUTPUT CROSSWALK] {OUTPUT_CROSSWALK}")
    print(crosswalk.head())
    print("Columns:", list(crosswalk.columns))
    print("\nMissing values by column:")
    print(crosswalk.isnull().sum())
else:
    print(f"\n[OUTPUT CROSSWALK] {OUTPUT_CROSSWALK} does not exist yet.")
