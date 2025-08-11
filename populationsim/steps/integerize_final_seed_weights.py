
# PopulationSim
# See full license in LICENSE.txt.

import logging
import os

import pandas as pd

from activitysim.core import inject

from ..integerizer import do_integerizing
from .helper import get_control_table
from .helper import weight_table_name
from .helper import get_weight_table
from activitysim.core.config import setting

logger = logging.getLogger(__name__)


@inject.step()
def integerize_final_seed_weights(settings, crosswalk, control_spec, incidence_table):
    """
    Final balancing for each seed (puma) zone with aggregated low and mid-level controls and
    distributed meta-level controls.

    Adds integer_weight column to seed-level weight table

    Parameters
    ----------
    settings : dict (settings.yaml as dict)
    crosswalk : pipeline table
    control_spec : pipeline table
    incidence_table : pipeline table

    Returns
    -------

    """

    if setting('NO_INTEGERIZATION_EVER', False):
        logger.warning("skipping integerize_final_seed_weights: NO_INTEGERIZATION_EVER")
        return

    crosswalk_df = crosswalk.to_frame()
    incidence_df = incidence_table.to_frame()
    control_spec = control_spec.to_frame()

    seed_geography = settings.get('seed_geography')
    seed_controls_df = get_control_table(seed_geography)

    # DIAGNOSTIC: Examine the control table structure
    logger.info(f"DIAGNOSTIC: seed_controls_df shape: {seed_controls_df.shape}")
    logger.info(f"DIAGNOSTIC: seed_controls_df columns: {list(seed_controls_df.columns)}")
    logger.info(f"DIAGNOSTIC: seed_controls_df index sample: {list(seed_controls_df.index[:5])}")
    
    # Check for NaN values in control table
    nan_summary = seed_controls_df.isna().sum()
    nan_controls = nan_summary[nan_summary > 0]
    if len(nan_controls) > 0:
        logger.error(f"DIAGNOSTIC: Control table has NaN values!")
        for control, count in nan_controls.items():
            pct = 100 * count / len(seed_controls_df)
            logger.error(f"  {control}: {count}/{len(seed_controls_df)} ({pct:.1f}%) NaN values")
            
        # Show sample of first few zones for problematic controls
        sample_controls = list(nan_controls.index[:3])
        logger.error(f"DIAGNOSTIC: Sample values for first 3 controls with NaN:")
        for control in sample_controls:
            sample_values = seed_controls_df[control].head(5)
            logger.error(f"  {control}: {list(sample_values)}")
    else:
        logger.info("DIAGNOSTIC: No NaN values found in control table")

    seed_weights_df = get_weight_table(seed_geography)

    # FIXME - I assume we want to integerize using meta controls too?
    control_cols = control_spec.target
    assert (seed_controls_df.columns == control_cols).all()

    # determine master_control_index if specified in settings
    total_hh_control_col = setting('total_hh_control')

    # run balancer for each seed geography
    weight_list = []

    seed_ids = crosswalk_df[seed_geography].unique()
    total_seeds = len(seed_ids)
    
    logger.info(f"Starting integerization for {total_seeds} {seed_geography} zones")
    
    for i, seed_id in enumerate(seed_ids, 1):
        
        # Add timestamp and detailed timing logging
        import time
        seed_start_time = time.time()
        logger.info(f"SEED {i}/{total_seeds} START: Processing seed {seed_id} at {time.strftime('%H:%M:%S')}")

        # Progress logging every 5 seeds  
        if i % 5 == 0 or i == 1 or i == total_seeds:
            logger.info(f"PROGRESS: Integerizing seed {i}/{total_seeds} ({100*i/total_seeds:.1f}% complete)")

        logger.info(f"integerize_final_seed_weights seed {i}/{total_seeds}: {seed_geography} {seed_id}")
        logger.info(f"  STEP 1: Getting incidence data for seed {seed_id}")

        # slice incidence rows for this seed geography
        seed_incidence = incidence_df[incidence_df[seed_geography] == seed_id]
        logger.info(f"  STEP 1 COMPLETE: Found {len(seed_incidence)} households for seed {seed_id}")

        logger.info(f"  STEP 2: Getting balanced weights for seed {seed_id}")
        balanced_seed_weights = \
            seed_weights_df.loc[seed_weights_df[seed_geography] == seed_id, 'balanced_weight']
        logger.info(f"  STEP 2 COMPLETE: Retrieved {len(balanced_seed_weights)} balanced weights")

        # Log details about this seed before integerization
        logger.info(f"  Seed {seed_id}: {len(seed_incidence)} households, "
                   f"total balanced weight: {balanced_seed_weights.sum():.2f}")
        
        logger.info(f"  STEP 3: Getting control totals for seed {seed_id}")
        # Log control totals for this seed
        seed_controls = seed_controls_df.loc[seed_id]
        logger.info(f"  STEP 3 COMPLETE: Retrieved {len(seed_controls)} controls")
        
        logger.info(f"  Seed {seed_id} control totals:")
        for control_name, control_value in seed_controls.items():
            if pd.isna(control_value):
                logger.warning(f"    {control_name}: nan (MISSING DATA - will be set to 0)")
            elif abs(control_value - round(control_value)) > 1e-6:
                logger.warning(f"    {control_name}: {control_value:.10f} (NON-INTEGER!)")
            else:
                logger.debug(f"    {control_name}: {control_value:.2f}")

        logger.info(f"  STEP 4: Cleaning control data for seed {seed_id}")
        # CRITICAL FIX: Fill nan values with 0 before passing to integerizer
        # This prevents the assertion error in the integerizer
        seed_controls_clean = seed_controls.fillna(0)
        
        nan_count = seed_controls.isna().sum()
        if nan_count > 0:
            logger.warning(f"  Seed {seed_id}: Fixed {nan_count} nan control values by setting them to 0")
            logger.warning(f"  Controls that were nan: {list(seed_controls[seed_controls.isna()].index)}")

        trace_label = "%s_%s" % (seed_geography, seed_id)
        logger.info(f"  STEP 4 COMPLETE: Data prepared for integerization")

        logger.info(f"  STEP 5: Calling do_integerizing for seed {seed_id}")
        integerizer_start_time = time.time()
        try:
            integer_weights, status = do_integerizing(
                trace_label=trace_label,
                control_spec=control_spec,
                control_totals=seed_controls_clean,
                incidence_table=seed_incidence[control_cols],
                float_weights=balanced_seed_weights,
                total_hh_control_col=total_hh_control_col
            )
            
            integerizer_time = time.time() - integerizer_start_time
            logger.info(f"  STEP 5 COMPLETE: Seed {seed_id} integerization completed successfully in {integerizer_time:.2f}s")
            logger.info(f"  Seed {seed_id} status: {status}")
        
        except Exception as e:
            integerizer_time = time.time() - integerizer_start_time
            logger.error(f"  STEP 5 FAILED: Error in integerization after {integerizer_time:.2f}s")
            logger.error(f"  FAILED integerizing seed {seed_id} ({seed_geography})")
            logger.error(f"  Error: {str(e)}")
            logger.error(f"  Error type: {type(e).__name__}")
            
            # Log additional debug info for this problematic seed
            logger.error(f"  Seed {seed_id} debug info:")
            logger.error(f"    Households: {len(seed_incidence)}")
            logger.error(f"    Balanced weight sum: {balanced_seed_weights.sum():.6f}")
            logger.error(f"    Control totals problematic values:")
            for control_name, control_value in seed_controls.items():
                if abs(control_value - round(control_value)) > 1e-6:
                    logger.error(f"      {control_name}: {control_value:.10f}")
            
            # Re-raise the exception to stop execution and show the full traceback
            raise

        seed_total_time = time.time() - seed_start_time
        logger.info(f"SEED {i}/{total_seeds} COMPLETE: Processed seed {seed_id} in {seed_total_time:.2f}s")
        
        weight_list.append(integer_weights)

    # bulk concat all seed level results
    integer_seed_weights = pd.concat(weight_list)

    inject.add_column(weight_table_name(seed_geography), 'integer_weight', integer_seed_weights)
