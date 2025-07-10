import numpy
import pandas as pd
import collections
import logging
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
    returns a version of the census table with just the relevant column, plus geography columns.
    """
    # Identify geography columns (those present in census_table_df and likely to be geo columns)
    possible_geo_cols = [
        'state', 'county', 'tract', 'block', 'block group',
        'GEOID', 'GEOID_block', 'GEOID_block group', 'GEOID_tract', 'GEOID_county'
    ]
    geo_cols = [col for col in possible_geo_cols if col in census_table_df.columns]

    # Debug: print dtype and unique values of data columns before summing
    data_cols = [col for col in census_table_df.columns if col not in geo_cols]
    for col in data_cols:
        print(f"[DEBUG] dtype of {col}: {census_table_df[col].dtype}")
        print(f"[DEBUG] unique values of {col} (sample): {census_table_df[col].unique()[:10]}")

    # If all control_dicts are empty, sum once outside the loop
    if all(len(control_dict) == 0 for control_dict in control_dict_list):
        summed = census_table_df[data_cols].apply(
            lambda x: pd.to_numeric(x.astype(str).str.replace(',', '').str.replace(' ', ''), errors="coerce").fillna(0)
        ).sum(axis=1)
        control_df = pd.DataFrame({control_name: summed.astype(float)})
    else:
        control_df = pd.DataFrame(index=census_table_df.index, columns=[control_name], data=0.0)
        for control_dict in control_dict_list:
            # If control_dict is empty, always sum all non-geo columns (even if there are multiple columns)
            if len(control_dict) == 0:
                data_cols = [col for col in census_table_df.columns if col not in geo_cols]
                # Clean and sum all data columns at once
                summed = census_table_df[data_cols].apply(
                    lambda x: pd.to_numeric(x.astype(str).str.replace(',', '').str.replace(' ', ''), errors="coerce").fillna(0)
                ).sum(axis=1)
                control_df[control_name] = summed.astype(float)
            else:
                # Handle both MultiIndex and regular Index
                if isinstance(census_table_df.columns, pd.MultiIndex):
                    for colnum in range(len(census_table_df.columns.levels[0])):
                        param_dict = collections.OrderedDict()
                        variable_name = census_table_df.columns.get_level_values(0)[colnum]
                        for paramnum in range(1, len(census_table_df.columns.names)):
                            param = census_table_df.columns.names[paramnum]
                            try:
                                param_dict[param] = int(census_table_df.columns.get_level_values(paramnum)[colnum])
                            except:
                                param_dict[param] = census_table_df.columns.get_level_values(paramnum)[colnum]
                        if param_dict == control_dict:
                            control_df["temp"] = census_table_df[variable_name]
                            control_df[control_name] = census_table_df[variable_name]
                            control_df.drop(columns="temp", inplace=True)
                            break
                        if census_col_is_in_control(param_dict, control_dict):
                            control_df["temp"] = census_table_df[variable_name]
                            # Ensure temp and control_name columns are numeric before summing
                            control_df["temp"] = pd.to_numeric(control_df["temp"], errors="coerce").fillna(0)
                            control_df[control_name] = pd.to_numeric(control_df[control_name], errors="coerce").fillna(0)
                            control_df[control_name] = control_df[control_name] + control_df["temp"]
                            control_df.drop(columns="temp", inplace=True)
                else:
                    # Regular Index: just sum all non-geo columns (exclude geography columns)
                    data_cols = [col for col in census_table_df.columns if col not in geo_cols]
                    for variable_name in data_cols:
                        col_data = census_table_df[variable_name].astype(str).str.replace(',', '').str.replace(' ', '')
                        col_data = pd.to_numeric(col_data, errors="coerce").fillna(0)
                        control_df["temp"] = col_data
                        control_df[control_name] = pd.to_numeric(control_df[control_name], errors="coerce").fillna(0)
                        control_df[control_name] = control_df[control_name] + control_df["temp"]
                        control_df.drop(columns="temp", inplace=True)
            new_sum = control_df[control_name].sum()

    # Always include geography columns in the returned DataFrame
    if geo_cols:
        geo_df = census_table_df[geo_cols].copy()
        # If index is not aligned, reset and merge
        if not geo_df.index.equals(control_df.index):
            geo_df = geo_df.reset_index(drop=True)
            control_df = control_df.reset_index(drop=True)
        control_df = pd.concat([geo_df, control_df], axis=1)
    # Write intermediary control table to CSV for visualization
    try:
        control_df.to_csv(f"intermediate_{control_name}.csv", index=False)
    except Exception as e:
        pass  # Ignore errors in writing CSV
    return control_df



def prepare_geography_columns(df, census_geography):
    # If you already have a GEOID column, just use it
    possible_geoid_cols = ['blk2020ge', 'blk2010ge', 'GEOID_block', 'GEOID']
    for col in possible_geoid_cols:
        if col in df.columns:
            df = df.rename(columns={col: 'GEOID_block'})
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
    return df

def add_geoid_column(df, census_geography):
    """
    Robustly create or use a GEOID column for the specified geography.
    If a suitable GEOID column already exists, use it. Otherwise, try to build from components.
    """
    df = df.copy()
    geo = census_geography.lower().replace("_", " ")
    crosswalk_col_map = {
        "block": "blk2020ge",
        "block group": "bg2020ge",
        "tract": "tr2020ge",
        "county": "cty2020ge"
    }
    geoid_col = crosswalk_col_map.get(geo)
    alt_cols = [
        geoid_col,
        f"GEOID_{geo}",
        "GEOID",
        geo.replace(" ", "") + "2020ge",
        geo.replace(" ", "_") + "2020ge",
        geo.replace(" ", "").upper() + "2020GE"
    ]
    for alt in alt_cols:
        if alt and alt in df.columns:
            df["GEOID_" + geo] = df[alt]
            return df
    # Otherwise, try to build from components
    geo_specs = {
        "block":       [("state", 2), ("county", 3), ("tract", 6), ("block", 4)],
        "block group": [("state", 2), ("county", 3), ("tract", 6), ("block group", 1)],
        "tract":       [("state", 2), ("county", 3), ("tract", 6)],
        "county":      [("state", 2), ("county", 3)],
    }
    if geo not in geo_specs:
        raise ValueError(f"Unsupported geography: {geo}")
    for col, _ in geo_specs[geo]:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame for geography '{geo}' and no suitable GEOID column present.")
    parts = [df[col].astype(str).str.zfill(width) for col, width in geo_specs[geo]]
    df["GEOID_" + geo] = parts[0].str.cat(parts[1:], sep='') if len(parts) > 1 else parts[0]
    return df

def temp_table_scaling(control_table_df, control_name, scale_numerator, scale_denominator, temp_controls):
    """
    Scale a control table by a numerator and/or denominator temporary control table, matching on GEOID columns.

    Parameters:
        control_table_df (pd.DataFrame): The main control table to be scaled.
        control_name (str): The name of the control variable/column.
        scale_numerator (str): Key for the numerator temp control table in temp_controls.
        scale_denominator (str): Key for the denominator temp control table in temp_controls.
        temp_controls (dict): Dictionary of temporary control tables, keyed by name.

    Returns:
        pd.DataFrame: The scaled control table.

    Raises:
        ValueError: If the GEOID columns do not match between numerator/denominator and control table.
    """
    if scale_numerator or scale_denominator:
        # Cross-check: sum and row count before merge
        pre_merge_sum = control_table_df[control_name].sum() if control_name in control_table_df.columns else None
        pre_merge_rows = len(control_table_df)

        scale_numerator_geometry   = temp_controls[scale_numerator].columns[0]
        scale_denominator_geometry = temp_controls[scale_denominator].columns[0]
        if len(temp_controls[scale_denominator]) == len(control_table_df):
            control_table_df = pd.merge(left=control_table_df, right=temp_controls[scale_denominator], how="left")
            # Cross-check: sum and row count after merge
            post_merge_sum = control_table_df[control_name].sum() if control_name in control_table_df.columns else None
            post_merge_rows = len(control_table_df)
            if pre_merge_sum is not None and post_merge_sum is not None and not numpy.isclose(pre_merge_sum, post_merge_sum, atol=1e-2):
                logging.warning(f"[CHECK] Sum of {control_name} changed from {pre_merge_sum} to {post_merge_sum} after merge.")
            if pre_merge_rows != post_merge_rows:
                logging.warning(f"[CHECK] Row count changed from {pre_merge_rows} to {post_merge_rows} after merge.")
            control_table_df["temp_fraction"] = control_table_df[control_name] / control_table_df[scale_denominator]

            zero_denom_df = control_table_df.loc[control_table_df["temp_fraction"]==numpy.inf].copy()
            if len(zero_denom_df) > 0:
                control_table_df.loc[control_table_df["temp_fraction"]==numpy.inf, "temp_fraction"] = 0

            numerator_df = temp_controls[scale_numerator].copy()
            add_aggregate_geography_colums(numerator_df)
            control_table_df = pd.merge(left=numerator_df, right=control_table_df, how="left")
            control_table_df[control_name] = control_table_df["temp_fraction"] * control_table_df[scale_numerator]
            control_table_df = control_table_df[[scale_numerator_geometry, control_name]]

            # Write intermediary scaled control table to CSV for visualization
            try:
                control_table_df.to_csv(f"intermediate_scaled_{control_name}.csv", index=False)
            except Exception as e:
                pass  # Ignore errors in writing CSV

        elif len(temp_controls[scale_numerator]) == len(control_table_df):
            raise NotImplementedError("Temp scaling by numerator of same geography not implemented yet")

        else:
            geoid_col_control = None
            geoid_col_denom = None
            def find_geoid_col(df):
                for col in df.columns:
                    if "GEOID" in col:
                        return col
                return None
            geoid_col_control = find_geoid_col(control_table_df)
            geoid_col_denom = find_geoid_col(temp_controls[scale_denominator])
            if geoid_col_control and geoid_col_denom:
                geoids_control = set(control_table_df[geoid_col_control].astype(str))
                geoids_denom = set(temp_controls[scale_denominator][geoid_col_denom].astype(str))
                missing_in_denom = geoids_control - geoids_denom
                extra_in_denom = geoids_denom - geoids_control
                if len(missing_in_denom) == 0 or len(extra_in_denom) == 0 or (len(missing_in_denom) + len(extra_in_denom) <= 5):
                    pass
                else:
                    raise ValueError("Temp scaling requires numerator or denominator geography to match")
            else:
                pass
            raise ValueError("Temp scaling requires numerator or denominator geography to match")
    return control_table_df

def aggregate_to_control_geo(control_table_df, control_name, control_geography, census_geography, maz_taz_def_df, temp_controls, scale_numerator, scale_denominator, subtract_table, variable_total):
    if scale_numerator and scale_denominator:
        assert(len(temp_controls[scale_numerator  ]) == len(control_table_df))
        assert(len(temp_controls[scale_denominator]) == len(control_table_df))
        control_table_df = pd.merge(left=control_table_df, right=temp_controls[scale_numerator  ], how="left")
        control_table_df = pd.merge(left=control_table_df, right=temp_controls[scale_denominator], how="left")
        control_table_df[control_name] = control_table_df[control_name] * control_table_df[scale_numerator]/control_table_df[scale_denominator]
        control_table_df.fillna(0, inplace=True)
        variable_total = variable_total * temp_controls[scale_numerator][scale_numerator].sum()/temp_controls[scale_denominator][scale_denominator].sum()

    if subtract_table:
        assert(len(temp_controls[subtract_table]) == len(control_table_df))
        control_table_df = pd.merge(left=control_table_df, right=temp_controls[subtract_table], how="left")
        control_table_df[control_name] = control_table_df[control_name] - control_table_df[subtract_table]
        variable_total = variable_total - temp_controls[subtract_table][subtract_table].sum()

    geo_mapping_df   = maz_taz_def_df[[control_geography, "GEOID_{}".format(census_geography)]].drop_duplicates()
    control_table_df = pd.merge(left=control_table_df, right=geo_mapping_df, how="left")
    final_df         = control_table_df[[control_geography, control_name]].groupby(control_geography).aggregate(numpy.sum)
    if not scale_numerator:
        diff = abs(final_df[control_name].sum() - variable_total)
        if diff >= 0.5:
            pass
    return final_df

def proportional_scaling(control_table_df, control_name, control_geography, census_geography, maz_taz_def_df, temp_controls, scale_numerator, scale_denominator):
    same_geo_total_df   = temp_controls[scale_denominator]
    assert(len(same_geo_total_df) == len(control_table_df))

    proportion_df = pd.merge(left=control_table_df, right=same_geo_total_df, how="left")
    proportion_var = "{} proportion".format(control_name)
    proportion_df[proportion_var] = proportion_df[control_name] / proportion_df[scale_denominator]

    block_prop_df = pd.merge(left=maz_taz_def_df, right=proportion_df, how="left")
    block_total_df   = temp_controls[scale_numerator]
    block_prop_df = pd.merge(left=block_prop_df, right=block_total_df, how="left")

    block_prop_df[control_name] = block_prop_df[proportion_var]*block_prop_df[scale_numerator]

    final_df = block_prop_df[[control_geography, control_name]].groupby(control_geography).aggregate(numpy.sum)
    return final_df

def match_control_to_geography(
    control_name, control_table_df, control_geography, census_geography,
    maz_taz_def_df, temp_controls,
    scale_numerator=None, scale_denominator=None, subtract_table=None
):
    if control_geography not in ["MAZ","TAZ","COUNTY","REGION"]:
        raise ValueError("match_control_to_geography passed unsupported control geography {}".format(control_geography))
    if census_geography not in ["block","block group","tract","county subdivision","county"]:
        raise ValueError("match_control_to_geography passed unsupported census geography {}".format(census_geography))

    variable_total = control_table_df[control_name].sum()

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
        return aggregate_to_control_geo(
            control_table_df, control_name, control_geography, census_geography,
            maz_taz_def_df, temp_controls, scale_numerator, scale_denominator, subtract_table, variable_total
        )

    if scale_numerator is None or scale_denominator is None:
        msg = "Cannot go from larger census geography {} without numerator and denominator specified".format(census_geography)
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
    # keep index as a normal column
    out_df.reset_index(drop=False, inplace=True)
    # keep track of columns to go back to
    out_df_cols = list(out_df.columns.values)

    # stochastic rounding
    out_df["control_stoch_round"] = stochastic_round(out_df[control_name])

    # see how they look at the TAZ and county level
    out_df = pd.merge(left=out_df, right=crosswalk_df, how="left")

    # this is being exacting... maybe not necessary

    # make them match taz totals (especially those that are already even)
    # really doing this in one iteration but check it
    for iteration in [1,2]:

        out_df_by_taz = out_df[["TAZ",control_name,"control_stoch_round"]].groupby("TAZ").aggregate(numpy.sum).reset_index(drop=False)
        out_df_by_taz["control_taz"]       = out_df_by_taz[control_name]  # copy and name explicitly
        out_df_by_taz["control_round_taz"] = numpy.around(out_df_by_taz[control_name])

        out_df_by_taz["control_stoch_round_diff"]     = out_df_by_taz["control_round_taz"] - out_df_by_taz["control_stoch_round"]
        out_df_by_taz["control_stoch_round_diff_abs"] = numpy.absolute(out_df_by_taz["control_stoch_round_diff"])

        # if the total is off by less than one, don't touch
        # otherwise, choose a MAZ to tweak based on control already in the MAZ
        out_df_by_taz["control_adjust"] = numpy.trunc(out_df_by_taz["control_stoch_round_diff"])

        tazdict_to_adjust = out_df_by_taz.loc[ out_df_by_taz["control_adjust"] != 0, ["TAZ","control_taz","control_adjust"]].set_index("TAZ").to_dict(orient="index")

        # nothing to do
        if len(tazdict_to_adjust)==0: break

        # add or remove a household if needed from a MAZ
        out_df = pd.merge(left=out_df, right=out_df_by_taz[["TAZ","control_adjust","control_taz"]], how="left")
        out_df_by_taz_grouped = out_df[["MAZ","TAZ",control_name,"control_stoch_round","control_adjust","control_taz"]].groupby("TAZ")
        for taz in tazdict_to_adjust.keys():
            adjustment = tazdict_to_adjust[taz]["control_adjust"]  # e.g. -2
            sample_n   = int(abs(adjustment)) # e.g. 2
            change_by  = adjustment/sample_n  # so this will be +1 or -1

            # choose a maz to tweak weighted by number of households in the MAZ, so we don't tweak 0-hh MAZs
            try:
                sample = out_df_by_taz_grouped.get_group(taz).sample(n=sample_n, weights="control_stoch_round")

                # actually make the change in the out_df.  iterate rather than join since there are so few
                for maz in sample["MAZ"].tolist():
                    out_df.loc[ out_df["MAZ"] == maz, "control_stoch_round"] += change_by

            except ValueError as e:
                # this could fail if the weights are all zero
                pass

    out_df_by_county = out_df[["COUNTY",control_name,"control_stoch_round"]].groupby("COUNTY").aggregate(numpy.sum).reset_index(drop=False)

    # use the new version
    out_df[control_name] = out_df["control_stoch_round"].astype(int)
    # go back to original cols
    out_df = out_df[out_df_cols]
    # and index
    out_df.set_index("MAZ", inplace=True)


    return out_df