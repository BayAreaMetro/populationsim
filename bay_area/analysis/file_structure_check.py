
import sys
sys.path.append('.')
from unified_tm2_config import UnifiedTM2Config
import pandas as pd

config = UnifiedTM2Config(year=2023)
households_file = config.POPSIM_OUTPUT_DIR / 'households_2023_tm2.csv'
persons_file = config.POPSIM_OUTPUT_DIR / 'persons_2023_tm2.csv'

print('Households file:', households_file)
print('Persons file:', persons_file)
print('Files exist:', households_file.exists(), persons_file.exists())

if households_file.exists():
    hh_df = pd.read_csv(households_file)
    print('Households columns:', list(hh_df.columns))
    print('Households shape:', hh_df.shape)

if persons_file.exists():
    pers_df = pd.read_csv(persons_file)
    print('Persons columns:', list(pers_df.columns))
    print('Persons shape:', pers_df.shape)
    if 'PERID' in pers_df.columns:
        print('PERID sample values:', pers_df['PERID'].head(10).tolist())