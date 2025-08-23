# This script was renamed from compare_controls_vs_results_by_county.py to compare_controls_vs_results_by_taz.py
# All logic remains the same, but the name now reflects that the comparison is at the TAZ level, not county.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys, os
from pathlib import Path
import logging
logging.basicConfig(level=logging.INFO)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unified_tm2_config import UnifiedTM2Config

# --- CONFIG ---
config = UnifiedTM2Config()
summary_file = config.POPSIM_OUTPUT_DIR / "final_summary_TAZ.csv"
sumdf = pd.read_csv(summary_file)

# --- FIND METRICS ---
metrics = [col[:-7] for col in sumdf.columns if col.endswith('_result')]

# --- SCATTERPLOTS ---
charts_dir = config.OUTPUT_DIR / "charts"
charts_dir.mkdir(exist_ok=True)
for metric in metrics:
    control_col = f"{metric}_control"
    result_col = f"{metric}_result"
    if control_col not in sumdf.columns or result_col not in sumdf.columns:
        continue
    plt.figure(figsize=(6,6))
    ax = sns.regplot(x=sumdf[control_col], y=sumdf[result_col], ci=None, line_kws={'color':'red'})
    plt.xlabel(f"{metric} (Control)")
    plt.ylabel(f"{metric} (Result)")
    plt.title(f"{metric}: Control vs Result (TAZ)")
    # R^2 and regression equation
    mask = sumdf[control_col].notna() & sumdf[result_col].notna()
    if mask.sum() > 1:
        x = sumdf.loc[mask, control_col]
        y = sumdf.loc[mask, result_col]
        coeffs = np.polyfit(x, y, 1)
        m, b = coeffs
        r2 = np.corrcoef(x, y)[0,1] ** 2
        eqn = f"y = {m:.3f}x + {b:.1f}"
        plt.text(0.05, 0.95, f"$R^2$ = {r2:.3f}\n{eqn}", transform=plt.gca().transAxes, fontsize=12, verticalalignment='top')
    plt.tight_layout()
    plt.savefig(charts_dir / f"scatter_{metric}.png")
    plt.close()
