import pandas as pd
from tm2_control_utils.config_census import INCOME_BIN_MAPPING

# Load TAZ marginals
TAZ_FILE = 'output_2023/populationsim_working_dir/data/taz_marginals.csv'
taz = pd.read_csv(TAZ_FILE)

# Load ACS summary
ACS_FILE = 'output_2023/populationsim_working_dir/output/bay_area_income_acs_2023_2010bins.csv'
acs = pd.read_csv(ACS_FILE)

# Get bin columns from config
bin_cols = [b['control'] for b in INCOME_BIN_MAPPING]

# Sum TAZ bins regionally
region_taz_bins = taz[bin_cols].sum()
region_taz_total = region_taz_bins.sum()

print('TAZ Regional Income Bin Sums:')
print(region_taz_bins)
print(f'TAZ Total Households (sum of bins): {region_taz_total:,}')

# Sum ACS bins regionally
acs_bin_cols = [col for col in acs.columns if col in bin_cols]
region_acs_bins = acs[acs_bin_cols].sum()
region_acs_total = region_acs_bins.sum()

print('\nACS Regional Income Bin Sums:')
print(region_acs_bins)
print(f'ACS Total Households (sum of bins): {region_acs_total:,}')

# Compare each bin
print('\nBin-by-bin comparison:')
for col in bin_cols:
    taz_val = region_taz_bins.get(col, 0)
    acs_val = region_acs_bins.get(col, 0)
    diff = taz_val - acs_val
    pct_diff = 100 * diff / acs_val if acs_val else float('nan')
    print(f'{col:15} | TAZ: {taz_val:8,.0f} | ACS: {acs_val:8,.0f} | Diff: {diff:8,.0f} | %Diff: {pct_diff:7.2f}%')

# Print total difference
total_diff = region_taz_total - region_acs_total
pct_total_diff = 100 * total_diff / region_acs_total if region_acs_total else float('nan')
print(f'\nTOTAL | TAZ: {region_taz_total:,.0f} | ACS: {region_acs_total:,.0f} | Diff: {total_diff:,.0f} | %Diff: {pct_total_diff:.2f}%')
