import logging
import numpy
import pandas as pd
import collections
from tm2_control_utils.geog_utils import add_aggregate_geography_colums


def census_col_is_in_control(param_dict, control_dict):
    """
    param_dict is from  CENSUS_DEFINITIONS,   e.g. OrderedDict([('pers_min',4), ('pers_max', 4)])
    control_dict is from control definitions, e.g. OrderedDict([('pers_min',4), ('pers_max',10)])

    Checks if this census column should be included in the control.
    Returns True or False.
    """
    # assume true unless kicked out
    for control_name, control_val in control_dict.items():
        if control_name not in param_dict:
            pass # later

        # if the value is a string, require exact match
        if isinstance(control_val, str):
            if control_dict[control_name] != param_dict[control_name]:
                return False
            continue

        # otherwise, check the min/max ranges
        if control_name.endswith('_min') and param_dict[control_name] < control_dict[control_name]:
            # census includes values less than control allows
            return False

        if control_name.endswith('_max') and param_dict[control_name] > control_dict[control_name]:
            # census includes values greater than control allows
            return False

    return True

def create_control_table(control_name, control_dict_list, census_table_name, census_table_df):
    """
    Given a control list of ordered dictionary (e.g. [{"pers_min":1, "pers_max":NPER_MAX}]) for a specific control,
    returns a version of the census table with just the relevant column.
    """
    logging.info("Creating control table for {}".format(control_name))
    logging.debug("\n{}".format(census_table_df.head()))

    # construct a new dataframe to return with same index as census_table_df
    control_df = pd.DataFrame(index=census_table_df.index, columns=[control_name], data=0)
    # logging.debug control_df.head()

    # logging.debug(census_table_df.columns.names)
    # [u'variable', u'pers_min', u'pers_max']

    # logging.debug(census_table_df.columns.get_level_values(0))
    # Index([u'H0130001', u'H0130002', u'H0130003', u'H0130004', u'H0130005', u'H0130006', u'H0130007', u'H0130008'], dtype='object', name=u'variable')

    # logging.debug(census_table_df.columns.get_level_values(1))
    # Index([u'1', u'1', u'2', u'3', u'4', u'5', u'6', u'7'], dtype='object', name=u'pers_min')

    # logging.debug(census_table_df.columns.get_level_values(2))
    # Index([u'10', u'1', u'2', u'3', u'4', u'5', u'6', u'10'], dtype='object', name=u'pers_max')

    # the control_dict_list is a list of dictionaries -- iterate through them
    prev_sum = 0
    for control_dict in control_dict_list:

        # if there's only one column and no attributes are expected then we're done
        if len(control_dict) == 0 and len(census_table_df.columns.values) == 1:
            variable_name = census_table_df.columns.values[0]
            logging.info("No attributes specified; single column identified: {}".format(variable_name))
            control_df[control_name] = census_table_df[variable_name]

        else:
            logging.info("  Control definition:")
            for cname,cval in control_dict.items(): logging.info("      {:15} {}".format(cname, cval))

            # find the relevant column, if there is one
            for colnum in range(len(census_table_df.columns.levels[0])):
                param_dict = collections.OrderedDict()
                # level 0 is the Census variable name, e.g. H0130001
                variable_name = census_table_df.columns.get_level_values(0)[colnum]

                for paramnum in range(1, len(census_table_df.columns.names)):
                    param = census_table_df.columns.names[paramnum]
                    try: # assume this is an int but fall back if it's nominal
                        param_dict[param] = int(census_table_df.columns.get_level_values(paramnum)[colnum])
                    except:
                        param_dict[param] = census_table_df.columns.get_level_values(paramnum)[colnum]
                # logging.debug(param_dict)

                # Is this single column sufficient?
                if param_dict == control_dict:
                    logging.info("    Found a single matching column: [{}]".format(variable_name))
                    for pname,pval in param_dict.items(): logging.info("      {:15} {}".format(pname, pval))

                    control_df["temp"] = census_table_df[variable_name]
                    control_df[control_name] = census_table_df[variable_name]
                    control_df.drop(columns="temp", inplace=True)
                    break  # stop iterating through columns

                # Otherwise, if it's in the range, add it in
                if census_col_is_in_control(param_dict, control_dict):
                    logging.info("    Adding column [{}]".format(variable_name))
                    for pname,pval in param_dict.items(): logging.info("      {:15} {}".format(pname, pval))

                    control_df["temp"] = census_table_df[variable_name]
                    control_df[control_name] = control_df[control_name] + control_df["temp"]
                    control_df.drop(columns="temp", inplace=True)

        # assume each control dict needs to find *something*
        new_sum = control_df[control_name].sum()
        logging.info("  => Total added: {:,}".format(new_sum - prev_sum))
        assert( new_sum > prev_sum)
        prev_sum = new_sum

    return control_df



def prepare_geography_columns(df, census_geography):
    # If you already have a GEOID column, just use it
    possible_geoid_cols = ['blk2020ge', 'blk2010ge', 'GEOID_block', 'GEOID']
    for col in possible_geoid_cols:
        if col in df.columns:
            df = df.rename(columns={col: 'GEOID_block'})
            print("Using existing GEOID column:", col)
            return df
    # Otherwise, try to build from state/county/tract/block
    geo_col_map = {
        "block":       ['state', 'county', 'tract', 'block'],
        "block group": ['state', 'county', 'tract', 'block group'],
        "tract":       ['state', 'county', 'tract'],
        "county":      ['state', 'county']
    }
    expected_cols = geo_col_map.get(census_geography)
    if expected_cols and all(col in df.columns for col in expected_cols):
        df['GEOID_block'] = df['state'] + df['county'] + df['tract'] + df['block']
        print("Constructed GEOID_block from columns:", expected_cols)
    else:
        print("WARNING: Could not find expected columns to construct GEOID. Columns are:", df.columns)
    return df

def add_geoid_column(df, census_geography):
    # If GEOID_block already exists, do nothing
    if census_geography == "block" and "GEOID_block" in df.columns:
        return df
    # Otherwise, try to build it (legacy fallback)
    if census_geography == "block":
        df["GEOID_block"] = df["state"] + df["county"] + df["tract"] + df["block"]
    elif census_geography == "block group":
        df["GEOID_block group"] = df["state"] + df["county"] + df["tract"] + df["block group"]
    elif census_geography == "tract":
        df["GEOID_tract"] = df["state"] + df["county"] + df["tract"]
    elif census_geography == "county":
        df["GEOID_county"] = df["state"] + df["county"]
    return df

def temp_table_scaling(control_table_df, control_name, scale_numerator, scale_denominator, temp_controls):
    logger = logging.getLogger()
    logger.info("Temporary Total for {} ({} rows) {:,}".format(control_name, len(control_table_df), control_table_df[control_name].sum()))
    logger.debug("head:\n{}".format(control_table_df.head()))

    if scale_numerator or scale_denominator:
        scale_numerator_geometry   = temp_controls[scale_numerator].columns[0]
        scale_denominator_geometry = temp_controls[scale_denominator].columns[0]
        logger.debug("Temp with numerator {} denominator {}".format(scale_numerator, scale_denominator))
        logger.debug("  {} has geometry {} and  length {}".format(scale_numerator,
                      scale_numerator_geometry, len(temp_controls[scale_numerator])))
        logger.debug("  Head:\n{}".format(temp_controls[scale_numerator].head()))
        logger.debug("  {} has geometry {} and length {}".format(scale_denominator,
                      scale_denominator_geometry, len(temp_controls[scale_denominator])))
        logger.debug("  Head:\n{}".format(temp_controls[scale_denominator].head()))

        if len(temp_controls[scale_denominator]) == len(control_table_df):
            control_table_df = pd.merge(left=control_table_df, right=temp_controls[scale_denominator], how="left")
            control_table_df["temp_fraction"] = control_table_df[control_name] / control_table_df[scale_denominator]

            zero_denom_df = control_table_df.loc[control_table_df["temp_fraction"]==numpy.inf].copy()
            if len(zero_denom_df) > 0:
                logger.warn("  DROPPING Inf (sum {}):\n{}".format(zero_denom_df[control_name].sum(), str(zero_denom_df)))
                control_table_df.loc[control_table_df["temp_fraction"]==numpy.inf, "temp_fraction"] = 0

            logger.debug("Divided by {}  temp_fraction mean:{}  Head:\n{}".format(scale_denominator, control_table_df["temp_fraction"].mean(), control_table_df.head()))

            numerator_df = temp_controls[scale_numerator].copy()
            add_aggregate_geography_colums(numerator_df)
            control_table_df = pd.merge(left=numerator_df, right=control_table_df, how="left")
            logger.debug("Joined with num ({} rows) :\n{}".format(len(control_table_df), control_table_df.head()))
            control_table_df[control_name] = control_table_df["temp_fraction"] * control_table_df[scale_numerator]
            control_table_df = control_table_df[[scale_numerator_geometry, control_name]]
            logger.debug("Final Total: {:,}  ({} rows)  Head:\n{}".format(control_table_df[control_name].sum(),
                          len(control_table_df), control_table_df.head()))

        elif len(temp_controls[scale_numerator]) == len(control_table_df):
            raise NotImplementedError("Temp scaling by numerator of same geography not implemented yet")

        else:
            raise ValueError("Temp scaling requires numerator or denominator geography to match")
    return control_table_df

def aggregate_to_control_geo(control_table_df, control_name, control_geography, census_geography, maz_taz_def_df, temp_controls, scale_numerator, scale_denominator, subtract_table, variable_total):
    logger = logging.getLogger()
    if scale_numerator and scale_denominator:
        assert(len(temp_controls[scale_numerator  ]) == len(control_table_df))
        assert(len(temp_controls[scale_denominator]) == len(control_table_df))
        logger.info("  Scaling by {}/{}".format(scale_numerator,scale_denominator))

        control_table_df = pd.merge(left=control_table_df, right=temp_controls[scale_numerator  ], how="left")
        control_table_df = pd.merge(left=control_table_df, right=temp_controls[scale_denominator], how="left")
        control_table_df[control_name] = control_table_df[control_name] * control_table_df[scale_numerator]/control_table_df[scale_denominator]
        control_table_df.fillna(0, inplace=True)

        variable_total = variable_total * temp_controls[scale_numerator][scale_numerator].sum()/temp_controls[scale_denominator][scale_denominator].sum()

    if subtract_table:
        assert(len(temp_controls[subtract_table]) == len(control_table_df))
        logger.info("  Initial total {:,}".format(control_table_df[control_name].sum()))
        logger.info("  Subtracting out {} with sum {:,}".format(subtract_table, temp_controls[subtract_table][subtract_table].sum()))
        control_table_df = pd.merge(left=control_table_df, right=temp_controls[subtract_table], how="left")
        control_table_df[control_name] = control_table_df[control_name] - control_table_df[subtract_table]

        variable_total = variable_total - temp_controls[subtract_table][subtract_table].sum()

    geo_mapping_df   = maz_taz_def_df[[control_geography, "GEOID_{}".format(census_geography)]].drop_duplicates()
    control_table_df = pd.merge(left=control_table_df, right=geo_mapping_df, how="left")

    final_df         = control_table_df[[control_geography, control_name]].groupby(control_geography).aggregate(numpy.sum)

    logger.debug("total at the end: {:,}".format(final_df[control_name].sum()))
    if not scale_numerator:
        diff = abs(final_df[control_name].sum() - variable_total)
        if diff >= 0.5:
            logger.warning(f"Control total differs from variable_total by {diff}")
    logger.info("  => Total for {} {:,}".format(control_name, final_df[control_name].sum()))
    return final_df

def proportional_scaling(control_table_df, control_name, control_geography, census_geography, maz_taz_def_df, temp_controls, scale_numerator, scale_denominator):
    logger = logging.getLogger()
    same_geo_total_df   = temp_controls[scale_denominator]
    assert(len(same_geo_total_df) == len(control_table_df))

    proportion_df = pd.merge(left=control_table_df, right=same_geo_total_df, how="left")
    proportion_var = "{} proportion".format(control_name)
    proportion_df[proportion_var] = proportion_df[control_name] / proportion_df[scale_denominator]
    logger.info("Create proportion {} at {} geography via {} using {}/{}\n{}".format(
                  proportion_var, control_geography, census_geography,
                  control_name, scale_denominator, proportion_df.head()))
    logger.info("Sums:\n{}".format(proportion_df[[control_name, scale_denominator]].sum()))
    logger.info("Mean:\n{}".format(proportion_df[[proportion_var]].mean()))

    block_prop_df = pd.merge(left=maz_taz_def_df, right=proportion_df, how="left")
    block_total_df   = temp_controls[scale_numerator]
    block_prop_df = pd.merge(left=block_prop_df, right=block_total_df, how="left")

    block_prop_df[control_name] = block_prop_df[proportion_var]*block_prop_df[scale_numerator]
    logger.info("Multiplying proportion {}/{} (at {}) x {}\n{}".format(
                  control_name, scale_denominator, census_geography,
                  scale_numerator,  block_prop_df.head()))

    final_df = block_prop_df[[control_geography, control_name]].groupby(control_geography).aggregate(numpy.sum)
    logger.info("Proportionally-derived Total added: {:,}".format(final_df[control_name].sum()))
    return final_df

def match_control_to_geography(
    control_name, control_table_df, control_geography, census_geography,
    maz_taz_def_df, temp_controls,
    scale_numerator=None, scale_denominator=None, subtract_table=None
):
    logger = logging.getLogger()
    if control_geography not in ["MAZ","TAZ","COUNTY","REGION"]:
        raise ValueError("match_control_to_geography passed unsupported control geography {}".format(control_geography))
    if census_geography not in ["block","block group","tract","county subdivision","county"]:
        raise ValueError("match_control_to_geography passed unsupported census geography {}".format(census_geography))

    variable_total = control_table_df[control_name].sum()
    logger.debug("Variable_total: {:,}".format(variable_total))

    GEO_HIERARCHY = { 'MAZ'   :['block','MAZ','block group','tract','county subdivision','county'],
                      'TAZ'   :['block',      'TAZ',        'tract','county subdivision','county'],
                      'COUNTY':['block',      'block group','tract','county subdivision','county','COUNTY'],
                      'REGION':['block',      'block group','tract','county subdivision','county','REGION']}

    control_geo_index = GEO_HIERARCHY[control_geography].index(control_geography)
    try:
        census_geo_index = GEO_HIERARCHY[control_geography].index(census_geography)
    except:
        census_geo_index = -1

    control_table_df = prepare_geography_columns(control_table_df, census_geography)
    control_table_df = add_geoid_column(control_table_df, census_geography)
    control_table_df = control_table_df[["GEOID_{}".format(census_geography), control_name]]

    if control_name.startswith("temp_"):
        return temp_table_scaling(control_table_df, control_name, scale_numerator, scale_denominator, temp_controls)

    if census_geo_index >= 0 and census_geo_index < control_geo_index:
        logger.info("Simple aggregation from {} to {}".format(census_geography, control_geography))

        return aggregate_to_control_geo(
            control_table_df, control_name, control_geography, census_geography,
            maz_taz_def_df, temp_controls, scale_numerator, scale_denominator, subtract_table, variable_total
        )

    if scale_numerator is None or scale_denominator is None:
        msg = "Cannot go from larger census geography {} without numerator and denominator specified".format(census_geography)
        logger.fatal(msg)
        raise ValueError(msg)

    return proportional_scaling(
        control_table_df, control_name, control_geography, census_geography,
        maz_taz_def_df, temp_controls, scale_numerator, scale_denominator
    )

def stochastic_round(my_series):
    """
    Performs stochastic rounding of a series and returns it.
    https://en.wikipedia.org/wiki/Rounding#Stochastic_rounding
    """
    numpy.random.seed(32)
    return numpy.floor(my_series + numpy.random.rand(len(my_series)))


def integerize_control(out_df, crosswalk_df, control_name):
    """
    Integerize this control
    """
    logging.debug("integerize_control for {}: out_df head:\n{}".format(control_name, out_df.head()))
    logging.debug("crosswalk_df head:\n{}".format(crosswalk_df.head()))

    # keep index as a normal column
    out_df.reset_index(drop=False, inplace=True)
    # keep track of columns to go back to
    out_df_cols = list(out_df.columns.values)

    # stochastic rounding
    out_df["control_stoch_round"] = stochastic_round(out_df[control_name])

    logging.debug("out_df sum:\n{}".format(out_df.sum()))

    # see how they look at the TAZ and county level
    out_df = pd.merge(left=out_df, right=crosswalk_df, how="left")

    # this is being exacting... maybe not necessary

    # make them match taz totals (especially those that are already even)
    # really doing this in one iteration but check it
    for iteration in [1,2]:
        logging.debug("Iteration {}".format(iteration))

        out_df_by_taz = out_df[["TAZ",control_name,"control_stoch_round"]].groupby("TAZ").aggregate(numpy.sum).reset_index(drop=False)
        out_df_by_taz["control_taz"]       = out_df_by_taz[control_name]  # copy and name explicitly
        out_df_by_taz["control_round_taz"] = numpy.around(out_df_by_taz[control_name])

        out_df_by_taz["control_stoch_round_diff"]     = out_df_by_taz["control_round_taz"] - out_df_by_taz["control_stoch_round"]
        out_df_by_taz["control_stoch_round_diff_abs"] = numpy.absolute(out_df_by_taz["control_stoch_round_diff"])

        # if the total is off by less than one, don't touch
        # otherwise, choose a MAZ to tweak based on control already in the MAZ
        out_df_by_taz["control_adjust"] = numpy.trunc(out_df_by_taz["control_stoch_round_diff"])

        logging.debug("out_df_by_taz head:\n{}".format(out_df_by_taz.head()))
        logging.debug("out_df_by_taz sum:\n{}".format(out_df_by_taz.sum()))
        logging.debug("out_df_by_taz describe:\n{}".format(out_df_by_taz.describe()))

        tazdict_to_adjust = out_df_by_taz.loc[ out_df_by_taz["control_adjust"] != 0, ["TAZ","control_taz","control_adjust"]].set_index("TAZ").to_dict(orient="index")

        logging.debug("tazdict_to_adjust {} TAZS: {}".format(len(tazdict_to_adjust), tazdict_to_adjust))

        # nothing to do
        if len(tazdict_to_adjust)==0: break

        # add or remove a household if needed from a MAZ
        out_df = pd.merge(left=out_df, right=out_df_by_taz[["TAZ","control_adjust","control_taz"]], how="left")
        logging.debug("out_df before adjustment:\n{}".format(out_df.head()))

        out_df_by_taz_grouped = out_df[["MAZ","TAZ",control_name,"control_stoch_round","control_adjust","control_taz"]].groupby("TAZ")
        for taz in tazdict_to_adjust.keys():
            # logging.debug("group for taz {} with tazdict_to_adjust {}:\n{}".format(taz, str(tazdict_to_adjust[taz]),
            #               out_df_by_taz_grouped.get_group(taz).head()))
            adjustment = tazdict_to_adjust[taz]["control_adjust"]  # e.g. -2
            sample_n   = int(abs(adjustment)) # e.g. 2
            change_by  = adjustment/sample_n  # so this will be +1 or -1

            # choose a maz to tweak weighted by number of households in the MAZ, so we don't tweak 0-hh MAZs
            try:
                sample = out_df_by_taz_grouped.get_group(taz).sample(n=sample_n, weights="control_stoch_round")
                # logging.debug("sample:\n{}".format(sample))

                # actually make the change in the out_df.  iterate rather than join since there are so few
                for maz in sample["MAZ"].tolist():
                    out_df.loc[ out_df["MAZ"] == maz, "control_stoch_round"] += change_by

            except ValueError as e:
                # this could fail if the weights are all zero
                logging.warn(e)
                logging.warn("group for taz {} with tazdict_to_adjust {}:\n{}".format(taz, str(tazdict_to_adjust[taz]),
                              out_df_by_taz_grouped.get_group(taz).head()))

    out_df_by_county = out_df[["COUNTY",control_name,"control_stoch_round"]].groupby("COUNTY").aggregate(numpy.sum).reset_index(drop=False)
    logging.debug("out_df_by_county head:\n{}".format(out_df_by_county.head()))
    logging.debug("out_df_by_county sum:\n{}".format(out_df_by_county.sum()))
    logging.debug("out_df_by_county describe:\n{}".format(out_df_by_county.describe()))

    # use the new version
    out_df[control_name] = out_df["control_stoch_round"].astype(int)
    # go back to original cols
    out_df = out_df[out_df_cols]
    # and index
    out_df.set_index("MAZ", inplace=True)


    return out_df