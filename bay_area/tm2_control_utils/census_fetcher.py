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
        Dataset is one of "pl" or "acs5"
        Year is a number for the table
        Geo is one of "block", "block group", "tract", "county subdivision" or "county"
        """

        if geo not in ["block", "block group", "tract", "county subdivision", "county"]:
            raise ValueError(f"get_census_data received unsupported geo {geo}")
        if table not in CENSUS_DEFINITIONS:
            raise ValueError(f"get_census_data received unsupported table {table}")

        table_cache_file = os.path.join(
            LOCAL_CACHE_FOLDER,
            f"{dataset}_{year}_{table}_{geo}.csv"
        )
        logging.info(f"Checking for table cache at {table_cache_file}")

        table_def = CENSUS_DEFINITIONS[table]
        table_cols = table_def[0]  # e.g. ['variable','pers_min','pers_max']

        if geo == "block":
            geo_index = ["state", "county", "tract", "block"]
        elif geo == "block group":
            geo_index = ["state", "county", "tract", "block group"]
        elif geo == "tract":
            geo_index = ["state", "county", "tract"]
        elif geo == "county subdivision":
            geo_index = ["state", "county", "county subdivision"]
        elif geo == "county":
            geo_index = ["state", "county"]

        if os.path.exists(table_cache_file):
            logging.info(f"Reading {table_cache_file}")
            try:
                header_rows = len(table_cols) + 1
                full_header = pd.read_csv(
                    table_cache_file,
                    header=list(range(header_rows)),
                    nrows=0
                )
                all_cols = full_header.columns

                raw_df = pd.read_csv(
                    table_cache_file,
                    dtype={col: object for col in geo_index},
                    skiprows=header_rows,
                    header=None
                )

                geo_part = raw_df.iloc[:, :len(geo_index)].astype(str)
                data_part = raw_df.iloc[:, len(geo_index):]
                data_cols = all_cols[len(geo_index):]
                if data_part.shape[1] != len(data_cols):
                    logging.error(
                        f"Cached CSV has {data_part.shape[1]} data columns, "
                        f"but expected {len(data_cols)} (from header)."
                    )
                    logging.error(f"data_part.columns: {data_part.columns}")
                    logging.error(f"data_cols: {data_cols}")
                    return None
                data_part.columns = data_cols
                data_part.index = pd.MultiIndex.from_frame(geo_part)
                logging.info(f"Successfully read cached table: {table_cache_file} with shape {data_part.shape}")
                return data_part
            except Exception as e:
                logging.error(f"Error reading cached table {table_cache_file}: {e}")
                logging.error(traceback.format_exc())
                return None

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
