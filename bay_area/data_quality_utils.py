import numpy as np
import logging
from typing import Tuple
import pandas as pd

def count_nan_inf(df: pd.DataFrame, col: str) -> Tuple[int, int]:
    """Count NaN and infinite values in a column of a DataFrame."""
    nan_count = df[col].isna().sum() if col in df.columns else 0
    inf_count = np.isinf(df[col]).sum() if col in df.columns else 0
    return nan_count, inf_count


def log_nan_inf_summary(household_df: pd.DataFrame, person_df: pd.DataFrame, logger: logging.Logger) -> None:
    """Log summary of NaN/inf values for HINCP, ADJINC, VEH in household and person data."""
    logger.info("[SUMMARY] Checking for NaN/inf in HINCP, ADJINC, VEH before filtering...")
    for col in ["HINCP", "ADJINC", "VEH"]:
        hh_nan, hh_inf = count_nan_inf(household_df, col)
        logger.info(f"  Households: {col}: {hh_nan} NaN, {hh_inf} inf")
    for col in ["HINCP", "ADJINC", "VEH"]:
        if col in person_df.columns:
            p_nan, p_inf = count_nan_inf(person_df, col)
            logger.info(f"  Persons: {col}: {p_nan} NaN, {p_inf} inf")


def filter_invalid_households_and_persons(household_df: pd.DataFrame, person_df: pd.DataFrame, logger: logging.Logger) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Remove households and persons where HINCP, ADJINC, or VEH are NaN or infinite."""
    invalid_mask = (
        household_df['HINCP'].isna() | household_df['ADJINC'].isna() |
        np.isinf(household_df['HINCP']) | np.isinf(household_df['ADJINC'])
    )
    if 'VEH' in household_df.columns:
        invalid_mask = invalid_mask | household_df['VEH'].isna() | np.isinf(household_df['VEH'])
    invalid_hh_ids = set(household_df.loc[invalid_mask, 'unique_hh_id'])
    n_invalid = len(invalid_hh_ids)
    if n_invalid > 0:
        logger.warning(f"Dropping {n_invalid} households (and their persons) due to NaN or infinite HINCP, ADJINC, or VEH")
    household_df = household_df[~household_df['unique_hh_id'].isin(invalid_hh_ids)].copy()
    person_df = person_df[~person_df['unique_hh_id'].isin(invalid_hh_ids)].copy()
    return household_df, person_df
