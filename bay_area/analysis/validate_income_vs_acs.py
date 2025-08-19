
import pandas as pd
import numpy as np
from unified_tm2_config import UnifiedTM2Config
from tm2_control_utils.config_census import INCOME_BIN_MAPPING

def summarize_income_bins():
    config = UnifiedTM2Config()
    # Get canonical bin columns and bin edges
    bin_cols = [b['control'] for b in INCOME_BIN_MAPPING]
    bin_edges = [b['2010_bin'][0] for b in INCOME_BIN_MAPPING] + [INCOME_BIN_MAPPING[-1]['2010_bin'][1]]

    # --- ACS ---
    acs = pd.read_csv(config.ACS_2010BINS_FILE)
    acs_bin_cols = [col for col in acs.columns if col in bin_cols]
    region_acs_bins = acs[acs_bin_cols].sum()
    region_acs_total = region_acs_bins.sum()
    acs_pct = region_acs_bins / region_acs_total * 100

    # --- TAZ controls ---
    taz = pd.read_csv(config.POPSIM_DATA_DIR / 'taz_marginals.csv')
    region_taz_bins = taz[bin_cols].sum()
    region_taz_total = region_taz_bins.sum()
    taz_pct = region_taz_bins / region_taz_total * 100

    # --- Seed population ---
    try:
        seed = pd.read_csv(config.POPSIM_DATA_DIR / 'seed_households.csv', usecols=['hh_income_2010'])
        seed = seed[seed['hh_income_2010'] > 0]
        seed['income_bin'] = pd.cut(seed['hh_income_2010'], bins=bin_edges, labels=bin_cols, right=False)
        seed_bins = seed['income_bin'].value_counts().sort_index()
        seed_total = seed_bins.sum()
        seed_pct = seed_bins / seed_total * 100
    except Exception as e:
        print(f"[WARNING] Could not load seed households: {e}")
        seed_pct = pd.Series([np.nan]*len(bin_cols), index=bin_cols)

    # --- Synthetic population ---
    try:
        synth = pd.read_csv(config.POPSIM_OUTPUT_DIR / 'households_2023_tm2.csv', usecols=['HHINCADJ'])
        synth = synth[synth['HHINCADJ'] > 0]
        synth['income_bin'] = pd.cut(synth['HHINCADJ'], bins=bin_edges, labels=bin_cols, right=False)
        synth_bins = synth['income_bin'].value_counts().sort_index()
        synth_total = synth_bins.sum()
        synth_pct = synth_bins / synth_total * 100
    except Exception as e:
        print(f"[WARNING] Could not load synthetic households: {e}")
        synth_pct = pd.Series([np.nan]*len(bin_cols), index=bin_cols)

    # --- Print summary table ---
    print("\nRegional Income Distribution by Bin (percent of households)")
    print("Bin           |   ACS   |   TAZ   |  Seed   | Synthetic | 2010$ Range")
    print("-"*70)
    for i, col in enumerate(bin_cols):
        acs_val = acs_pct.get(col, np.nan)
        taz_val = taz_pct.get(col, np.nan)
        seed_val = seed_pct.get(col, np.nan)
        synth_val = synth_pct.get(col, np.nan)
        bin_range = f"${bin_edges[i]:,} - ${bin_edges[i+1]-1:,}"
        print(f"{col:12} | {acs_val:7.2f} | {taz_val:7.2f} | {seed_val:7.2f} | {synth_val:9.2f} | {bin_range}")

    print("\nTotals:")
    print(f"ACS:        {region_acs_total:,.0f}")
    print(f"TAZ:        {region_taz_total:,.0f}")
    print(f"Seed:       {seed_total if 'seed_total' in locals() else 'N/A'}")
    print(f"Synthetic:  {synth_total if 'synth_total' in locals() else 'N/A'}")

if __name__ == "__main__":
    summarize_income_bins()
