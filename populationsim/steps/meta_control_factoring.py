
# PopulationSim
# See full license in LICENSE.txt.

import logging
import os
import numpy as np

import pandas as pd

from activitysim.core import pipeline
from activitysim.core import inject

from .helper import get_control_table
from .helper import control_table_name
from .helper import get_weight_table

logger = logging.getLogger(__name__)


def dump_table(table_name, table):

    return

    print("\n%s\n" % table_name, table)


@inject.step()
def meta_control_factoring(settings, control_spec, incidence_table):
    """
    Apply simple factoring to summed household fractional weights based on original
    meta control values relative to summed household fractional weights by meta zone.

    The resulting factored meta control weights will be new meta controls appended as
    additional columns to the seed control table, for final balancing.

    Parameters
    ----------
    settings : dict (settings.yaml as dict)
    control_spec : pipeline table
    incidence_table : pipeline table

    Returns
    -------

    """

    # FIXME - if there is only one seed zone in the meta zone, just copy meta control values?

    incidence_df = incidence_table.to_frame()
    control_spec = control_spec.to_frame()

    geographies = settings.get('geographies')
    seed_geography = settings.get('seed_geography')
    meta_geography = geographies[0]

    # - if there are no meta controls, then we don't have to do anything
    if not (control_spec.geography == meta_geography).any():
        logger.warning("meta_control_factoring: no meta targets so nothing to do")
        return

    meta_controls_df = get_control_table(meta_geography)
    dump_table("meta_controls_df", meta_controls_df)

    # ENHANCED DIAGNOSTICS: Check county control indices
    logger.info(f"DIAGNOSTIC: meta_controls_df shape: {meta_controls_df.shape}")
    logger.info(f"DIAGNOSTIC: meta_controls_df index: {list(meta_controls_df.index)}")
    logger.info(f"DIAGNOSTIC: meta_controls_df columns: {list(meta_controls_df.columns)}")

    # slice control_spec to select only the rows for meta level controls
    meta_controls_spec = control_spec[control_spec.geography == meta_geography]
    meta_control_targets = meta_controls_spec['target']

    logger.info("meta_control_factoring %s targets" % len(meta_control_targets))
    logger.info(f"DIAGNOSTIC: meta_control_targets: {list(meta_control_targets)}")

    dump_table("meta_controls_spec", meta_controls_spec)
    dump_table("meta_control_targets", meta_control_targets)

    # seed level weights of all households (rows aligned with incidence_df rows)
    seed_weights_df = get_weight_table(seed_geography)
    assert len(incidence_df.index) == len(seed_weights_df.index)

    # expand person weights by incidence (incidnece will simply be 1 for household targets)
    hh_level_weights = incidence_df[[seed_geography, meta_geography]].copy()
    for target in meta_control_targets:
        hh_level_weights[target] = \
            incidence_df[target] * seed_weights_df['preliminary_balanced_weight']

    dump_table("hh_level_weights", hh_level_weights)

    # weights of meta targets at seed level
    factored_seed_weights = \
        hh_level_weights.groupby([seed_geography, meta_geography], as_index=False).sum()
    factored_seed_weights.set_index(seed_geography, inplace=True)
    dump_table("factored_seed_weights", factored_seed_weights)

    # weights of meta targets summed from seed level to  meta level
    factored_meta_weights = factored_seed_weights.groupby(meta_geography, as_index=True).sum()
    dump_table("factored_meta_weights", factored_meta_weights)

    # ENHANCED DIAGNOSTICS: Check factored_meta_weights indices
    logger.info(f"DIAGNOSTIC: factored_meta_weights shape: {factored_meta_weights.shape}")
    logger.info(f"DIAGNOSTIC: factored_meta_weights index: {list(factored_meta_weights.index)}")
    logger.info(f"DIAGNOSTIC: factored_meta_weights columns: {list(factored_meta_weights.columns)}")

    # only the meta level controls from meta_controls table
    meta_controls_df = meta_controls_df[meta_control_targets]
    dump_table("meta_controls_df", meta_controls_df)

    # ENHANCED DIAGNOSTICS: Check index alignment
    logger.info(f"DIAGNOSTIC: Counties in meta_controls_df: {sorted(meta_controls_df.index)}")
    logger.info(f"DIAGNOSTIC: Counties in factored_meta_weights: {sorted(factored_meta_weights.index)}")
    
    # Check for index alignment issues
    missing_in_controls = set(factored_meta_weights.index) - set(meta_controls_df.index)
    missing_in_weights = set(meta_controls_df.index) - set(factored_meta_weights.index)
    
    if missing_in_controls:
        logger.error(f"DIAGNOSTIC: Counties in factored_meta_weights but not in meta_controls_df: {missing_in_controls}")
    if missing_in_weights:
        logger.error(f"DIAGNOSTIC: Counties in meta_controls_df but not in factored_meta_weights: {missing_in_weights}")

    # compute the scaling factors to be applied to the seed-level totals:
    meta_factors = pd.DataFrame(index=meta_controls_df.index)
    for target in meta_control_targets:
        logger.info(f"Processing meta control target: {target}")
        
        # Diagnostic: Check for zero denominators before division
        denominator = factored_meta_weights[target]
        zero_mask = (denominator == 0) | (denominator.isna())
        zero_count = zero_mask.sum()
        
        if zero_count > 0:
            logger.warning(f"DIAGNOSTIC: Target '{target}' has {zero_count} zones with zero/NaN seed weights")
            zero_zones = denominator[zero_mask].index.tolist()
            logger.warning(f"DIAGNOSTIC: Zero weight zones for '{target}': {zero_zones}")
            
            # Show corresponding control targets for these zones
            for zone in zero_zones[:5]:  # Show first 5 to avoid log spam
                control_value = meta_controls_df.loc[zone, target] if zone in meta_controls_df.index else "NOT_FOUND"
                logger.warning(f"DIAGNOSTIC: Zone {zone} - Control target: {control_value}, Seed weight: {denominator.loc[zone] if zone in denominator.index else 'NOT_FOUND'}")
        
        # Perform the division
        meta_factors[target] = meta_controls_df[target] / factored_meta_weights[target]
        
        # Check for NaN/infinite results
        nan_count = meta_factors[target].isna().sum()
        inf_count = np.isinf(meta_factors[target]).sum()
        
        if nan_count > 0 or inf_count > 0:
            logger.error(f"DIAGNOSTIC: Target '{target}' produced {nan_count} NaN and {inf_count} infinite factors")
            
    dump_table("meta_factors", meta_factors)

    # compute seed-level controls from meta-level controls
    seed_level_meta_controls = pd.DataFrame(index=factored_seed_weights.index)
    for target in meta_control_targets:
        #  meta level scaling_factor for this meta_control
        scaling_factor = factored_seed_weights[meta_geography].map(meta_factors[target])
        # scale the seed_level_meta_controls by meta_level scaling_factor
        seed_level_meta_controls[target] = factored_seed_weights[target] * scaling_factor
        # FIXME - why round scaled factored seed_weights to int prior to final seed balancing?
        # Diagnostic: Check values before integer conversion
        values_to_convert = seed_level_meta_controls[target].round()
        nan_count = values_to_convert.isna().sum()
        inf_count = np.isinf(values_to_convert).sum()
        
        if nan_count > 0:
            logger.error(f"DIAGNOSTIC: '{target}' has {nan_count} NaN values before integer conversion")
            nan_indices = values_to_convert[values_to_convert.isna()].index.tolist()[:10]
            logger.error(f"DIAGNOSTIC: First 10 NaN indices for '{target}': {nan_indices}")
            
        if inf_count > 0:
            logger.error(f"DIAGNOSTIC: '{target}' has {inf_count} infinite values before integer conversion")
            
        try:
            seed_level_meta_controls[target] = values_to_convert.astype(int)
            logger.info(f"DIAGNOSTIC: Successfully converted '{target}' to integer")
        except Exception as e:
            logger.error(f"DIAGNOSTIC: Failed to convert '{target}' to integer: {e}")
            logger.error(f"DIAGNOSTIC: Value range for '{target}': min={values_to_convert.min()}, max={values_to_convert.max()}")
            logger.error(f"DIAGNOSTIC: Value types: {values_to_convert.dtype}, unique types: {values_to_convert.apply(type).unique()}")
            raise
    dump_table("seed_level_meta_controls", seed_level_meta_controls)

    # create final balancing controls
    # add newly created seed_level_meta_controls to the existing set of seed level controls

    seed_controls_df = get_control_table(seed_geography)

    assert len(seed_controls_df.index) == len(seed_level_meta_controls.index)
    seed_controls_df = pd.concat([seed_controls_df, seed_level_meta_controls], axis=1)

    # ensure columns are in right order for orca-extended table
    seed_controls_df = seed_controls_df[control_spec.target]
    assert (seed_controls_df.columns == control_spec.target).all()

    dump_table("seed_controls_df", seed_controls_df)

    pipeline.replace_table(control_table_name(seed_geography), seed_controls_df)
