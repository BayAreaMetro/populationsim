import os
import pandas as pd
import logging
from census import Census
from tm2_control_utils.config import (
    CENSUS_API_KEY_FILE,
    LOCAL_CACHE_FOLDER,
    CA_STATE_FIPS,
    BAY_AREA_COUNTY_FIPS,
    CENSUS_DEFINITIONS,
)
import traceback


class CensusFetcher:
    """
    Class to fetch the census data needed for these controls and cache them.

    Uses the census python package (https://pypi.org/project/census/)
    """

    def __init__(self):
        """
        Read the census api key and instantiate the census object.
        """
        with open(CENSUS_API_KEY_FILE) as f:
            self.CENSUS_API_KEY = f.read().strip()
        self.census = Census(self.CENSUS_API_KEY)
        logging.debug("census object instantiated")

    def get_census_data(self, dataset, year, table, geo):
        """
        Robustly load census data from a cached CSV, handling multi-row headers and ensuring correct column names.
        Returns a DataFrame with geography columns and census variable columns.
        Handles files where geo headers are in row 5 and data headers in row 1, as well as fallback to standard single-row header.
        """
        print(f"[DEBUG] ENTER get_census_data: dataset={dataset}, year={year}, table={table}, geo={geo}")
        def get_geo_index(geo):
            if geo == "block":
                return ["state", "county", "tract", "block"]
            elif geo == "block group":
                return ["state", "county", "tract", "block group"]
            elif geo == "tract":
                return ["state", "county", "tract"]
            elif geo == "county subdivision":
                return ["state", "county", "county subdivision"]
            elif geo == "county":
                return ["state", "county"]
            else:
                return []

        table_cache_file = os.path.join(
            LOCAL_CACHE_FOLDER,
            f"{dataset}_{year}_{table}_{geo}.csv"
        )
        logging.info(f"Checking for table cache at {table_cache_file}")

        table_def = CENSUS_DEFINITIONS[table]
        table_cols = table_def[0]  # e.g. ['variable','pers_min','pers_max']

        if os.path.exists(table_cache_file):
            logging.info(f"Reading {table_cache_file}")
            try:
                # Read all lines to find the correct header and variable code row
                with open(table_cache_file, 'r', encoding='utf-8-sig') as f:
                    lines = [line.strip().split(',') for line in f.readlines()]
                geo_index = get_geo_index(geo)
                # Check for expected header structure
                if len(lines) >= 6 and len(lines[4]) >= 4 and len(lines[0]) >= 5:
                    geo_cols = lines[4][:4]
                    data_cols = lines[0][4:]
                    col_names = geo_cols + data_cols
                    print(f"[DEBUG] Using geo_cols from row 5: {geo_cols}")
                    print(f"[DEBUG] Using data_cols from row 1: {data_cols}")
                    print(f"[DEBUG] Final col_names: {col_names}")
                    # Data starts on row 6 (index 5)
                    df = pd.read_csv(
                        table_cache_file,
                        header=None,
                        skiprows=5,
                        names=col_names
                    )
                    # Map first four columns to standard names for downstream compatibility
                    if len(geo_cols) == len(geo_index):
                        rename_dict = {old: new for old, new in zip(geo_cols, geo_index)}
                        df.rename(columns=rename_dict, inplace=True)
                        print(f"[DEBUG] Renamed geo columns: {rename_dict}")
                    else:
                        print(f"[DEBUG] geo_cols and geo_index length mismatch: {geo_cols} vs {geo_index}")
                    # Ensure geography columns are string type
                    for col in geo_index:
                        if col in df.columns:
                            df[col] = df[col].astype(str)
                    df = df.reset_index(drop=True)
                    # Check that the sum of numeric columns is reasonable and non-zero
                    numeric_cols = df.select_dtypes(include='number').columns
                    for col in numeric_cols:
                        col_sum = df[col].sum()
                        print(f"[CHECK] Sum of column '{col}': {col_sum}")
                        if col_sum == 0 or pd.isna(col_sum):
                            logging.warning(f"Column '{col}' in {table_cache_file} sums to zero or NaN. Check data integrity.")
                        elif col_sum < 100:
                            logging.warning(f"Column '{col}' in {table_cache_file} has a suspiciously low sum: {col_sum}")
                    print(f"[DEBUG] EXIT get_census_data: df.columns: {list(df.columns)}")
                    print(f"[DEBUG] df.head():\n{df.head()}")
                    logging.info(f"Read correct header cached table: {table_cache_file} with shape {df.shape}")
                    return df
                else:
                    # Fallback: try reading as standard single-row header
                    print(f"[DEBUG] Unexpected file format for {table_cache_file}. Attempting fallback read.")
                    df = pd.read_csv(table_cache_file)
                    numeric_cols = df.select_dtypes(include='number').columns
                    for col in numeric_cols:
                        col_sum = df[col].sum()
                        print(f"[CHECK] Sum of column '{col}': {col_sum}")
                        if col_sum == 0 or pd.isna(col_sum):
                            logging.warning(f"Column '{col}' in {table_cache_file} sums to zero or NaN. Check data integrity.")
                        elif col_sum < 100:
                            logging.warning(f"Column '{col}' in {table_cache_file} has a suspiciously low sum: {col_sum}")
                    return df
            except Exception as e:
                logging.error(f"Error reading cached table {table_cache_file}: {e}")
                logging.error(traceback.format_exc())
                raise RuntimeError(f"Failed to read census cached table: {table_cache_file}")

        # If no cache exists, fetch from the Census API & write cache
        multi_col_def = []
        full_df = None


        county_codes = BAY_AREA_COUNTY_FIPS.values()  # iterate all Bay Area counties

        for census_col in table_def[1:]:
            df_list = []
            for county_code in county_codes:
                if geo == "county":
                    geo_dict = {
                        'for': f"county:{county_code}",
                        'in':  f"state:{CA_STATE_FIPS}"
                    }
                else:
                    geo_dict = {
                        'for': f"{geo}:*",
                        'in':  f"state:{CA_STATE_FIPS} county:{county_code}"
                    }

                # use the new PL endpoint for 2020 decennial, ACS5 for 2023
                if dataset == "pl":
                    api = self.census.pl  # or whatever your CensusFetcher uses for PL 94-171
                elif dataset == "acs5":
                    api = self.census.acs5
                else:
                    raise ValueError(f"Unsupported dataset: {dataset}")
                
                records = api.get([census_col[0]], geo_dict, year=year)

                county_df = (
                    pd.DataFrame.from_records(records)
                    .set_index(geo_index)
                    .astype(float)
                )
                df_list.append(county_df)

            df = pd.concat(df_list, axis=0)
            if full_df is None:
                full_df = df
            else:
                full_df = full_df.merge(df, left_index=True, right_index=True)

            multi_col_def.append(census_col)

        if geo == "county":
            county_tuples = [
                (CA_STATE_FIPS, code)
                for code in BAY_AREA_COUNTY_FIPS.values()
            ]
            full_df = full_df.loc[county_tuples]

        full_df.columns = pd.MultiIndex.from_tuples(
            multi_col_def,
            names=table_cols
        )
        os.makedirs(os.path.dirname(table_cache_file), exist_ok=True)
        full_df.to_csv(table_cache_file, header=True, index=True)
        logging.info(f"Wrote {table_cache_file}")
