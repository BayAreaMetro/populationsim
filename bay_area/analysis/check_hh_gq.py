import pandas as pd

# Load TAZ summary
f = 'output_2023/populationsim_working_dir/output/final_summary_TAZ_NODE.csv'
print('Loading', f)
df = pd.read_csv(f)
cols = ['hh_size_1_control','hh_size_1_result','hh_gq_university_control','hh_gq_noninstitutional_control','numhh_gq_control','numhh_gq_result']
for c in cols:
    if c in df.columns:
        print(f'{c}: {int(df[c].sum()):,}')
    else:
        print(f'{c}: MISSING')

# Load MAZ marginals hhgq
f2 = 'output_2023/populationsim_working_dir/data/maz_marginals_hhgq.csv'
print('\nLoading', f2)
mdf = pd.read_csv(f2)
if 'numhh_gq' in mdf.columns:
    print('MAZ numhh_gq total:', int(mdf['numhh_gq'].sum()))
else:
    print('MAZ numhh_gq: MISSING')

# TAZ marginals hhgq if exists
f3 = 'output_2023/populationsim_working_dir/data/taz_marginals_hhgq.csv'
print('\nChecking', f3)
import os
if os.path.exists(f3):
    tdf = pd.read_csv(f3)
    if 'numhh_gq' in tdf.columns:
        print('TAZ numhh_gq total:', int(tdf['numhh_gq'].sum()))
    else:
        print('TAZ numhh_gq: MISSING')
else:
    print('TAZ marginals not found')
