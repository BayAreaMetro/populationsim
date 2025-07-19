import os
import pandas as pd
import logging
import requests
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

    def fetch_dhc_data(self, variables, geo_dict, year):
        """
        Custom DHC data fetcher using direct HTTP requests since the census library doesn't support DHC.
        Includes caching to M: drive location for reuse.
        """
        logging.info(f"fetch_dhc_data called with variables={variables}, geo_dict={geo_dict}, year={year}")
        
        # Handle different variable formats
        if isinstance(variables, list) and len(variables) == 1:
            variable_name = variables[0]
        else:
            variable_name = variables
            
        # Check if this is a computed variable
        if variable_name in CENSUS_DEFINITIONS:
            table_def = CENSUS_DEFINITIONS[variable_name]
            if len(table_def) > 1 and len(table_def[1]) > 1:
                # This is a computed variable - sum multiple Census variables
                var_list = table_def[1]
                variables_str = ','.join(var_list)
                logging.info(f"Computed variable {variable_name} using variables: {var_list}")
                is_computed = True
            else:
                # Single variable
                variables_str = table_def[1][0] if isinstance(table_def[1], list) else variable_name
                is_computed = False
        else:
            # Direct variable name
            variables_str = variable_name
            is_computed = False

        # Create cache file name based on the request - use same pattern as regular census files
        for_param = geo_dict.get('for', '')
        in_param = geo_dict.get('in', '')
        
        # Extract geography type from for_param (e.g., "block:*" -> "block")
        geo_type = for_param.split(':')[0] if ':' in for_param else for_param
        
        # Use the same naming convention as regular census files: dataset_year_table_geo.csv
        cache_filename = f"dhc_{year}_{variable_name}_{geo_type}.csv"
        cache_filepath = os.path.join(LOCAL_CACHE_FOLDER, cache_filename)
        
        # Check for cached file first
        if os.path.exists(cache_filepath):
            logging.info(f"Reading DHC data from cache: {cache_filepath}")
            try:
                cached_df = pd.read_csv(cache_filepath)
                # Convert back to records format for consistency
                return cached_df.to_dict('records')
            except Exception as e:
                logging.warning(f"Failed to read DHC cache file {cache_filepath}: {e}")
                # Continue to API fetch if cache read fails

        # Build the API URL
        base_url = f"https://api.census.gov/data/{year}/dec/dhc"
        
        params = {
            'get': variables_str,
            'for': for_param,
            'in': in_param,
            'key': self.CENSUS_API_KEY
        }
        
        logging.info(f"Fetching DHC data from API: {variables_str} for {for_param} in {in_param}")
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Convert to DataFrame-like records
            headers = data[0]
            rows = data[1:]
            
            # Handle computed variables that need summing
            if is_computed:
                table_def = CENSUS_DEFINITIONS[variable_name]
                var_list = table_def[1]
                # Sum the component variables for each row
                records = []
                for row in rows:
                    # Convert row to dict for easier processing
                    row_dict = dict(zip(headers, row))
                    
                    # Sum the variables (convert to float first, handle missing values as 0)
                    total = 0
                    for var in var_list:
                        val = row_dict.get(var, '0')
                        try:
                            total += float(val) if val not in ['', None] else 0
                        except (ValueError, TypeError):
                            total += 0
                    
                    # Create new record with computed total and geography columns
                    new_record = {}
                    # Keep all geography columns (non-variable columns)
                    for col in headers:
                        if col not in var_list:
                            new_record[col] = row_dict[col]
                    # Add computed variable
                    new_record[variable_name] = str(total)
                    records.append(new_record)
            else:
                # Return as list of dicts for consistency with census library
                records = [dict(zip(headers, row)) for row in rows]
                
            # Cache the results for future use
            try:
                os.makedirs(os.path.dirname(cache_filepath), exist_ok=True)
                cache_df = pd.DataFrame(records)
                cache_df.to_csv(cache_filepath, index=False)
                logging.info(f"Wrote DHC data to cache: {cache_filepath}")
            except Exception as e:
                logging.warning(f"Failed to write DHC cache file {cache_filepath}: {e}")
                # Continue even if caching fails
            
            return records
            
        except Exception as e:
            logging.error(f"Failed to fetch DHC data: {e}")
            raise

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

        geo_index = get_geo_index(geo)
        
        # Initialize variables to avoid UnboundLocalError
        geo_cols = []
        data_cols = []
        
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
                    
                # Check for expected header structure
                if len(lines) >= 6 and len(lines[4]) >= 4 and len(lines[0]) >= 5:
                    print(f"[DEBUG] File has expected multi-row header structure")
                    print(f"[DEBUG] lines[0] (data headers): {lines[0]}")
                    print(f"[DEBUG] lines[4] (geo headers): {lines[4]}")
                    print(f"[DEBUG] Total lines in file: {len(lines)}")
                    
                    # Try to detect the correct format - check multiple header rows
                    geo_cols = []
                    data_cols = []
                    
                    # Check if lines[0] contains standard variable headers
                    if 'variable' in lines[0][0] if lines[0] else False:
                        print(f"[DEBUG] Using standard format with variable headers")
                        # Standard format - data headers in row 0, geo info in later rows
                        data_cols = [col for col in lines[0] if col and col != 'variable']
                        
                        # Find geo headers by looking for recognizable geo column names
                        for i in range(1, min(10, len(lines))):
                            row = lines[i]
                            if any(geo_name in str(cell).lower() for cell in row for geo_name in ['state', 'county', 'tract', 'block']):
                                # Extract non-empty cells that look like geo column names
                                potential_geo_cols = [cell for cell in row if cell and str(cell).strip()]
                                if len(potential_geo_cols) >= 2:  # At least state and county
                                    geo_cols = potential_geo_cols[:4]  # Take first 4 potential geo columns
                                    print(f"[DEBUG] Found geo columns in row {i}: {geo_cols}")
                                    break
                        
                        # If still no geo_cols found, use standard defaults
                        if not geo_cols:
                            if geo == 'block':
                                geo_cols = ['state', 'county', 'tract', 'block']
                            elif geo == 'tract':
                                geo_cols = ['state', 'county', 'tract'] 
                            elif geo == 'county':
                                geo_cols = ['state', 'county']
                            else:
                                geo_cols = ['state', 'county', 'tract']
                            print(f"[DEBUG] Using default geo components: {geo_cols}")
                    
                    else:
                        # Alternative format - try to detect from actual data rows
                        print(f"[DEBUG] Using alternative format detection")
                        
                        # Look for a row that has numeric data (skip headers)
                        data_start_row = None
                        for i in range(len(lines)):
                            row = lines[i]
                            try:
                                # Check if row has some numeric values (indicating data)
                                numeric_count = sum(1 for cell in row if cell and str(cell).replace('.', '').replace('-', '').isdigit())
                                if numeric_count >= 3:  # At least 3 numeric columns
                                    data_start_row = i
                                    break
                            except:
                                continue
                        
                        if data_start_row is not None:
                            # Look backwards from data row to find headers
                            for i in range(data_start_row - 1, -1, -1):
                                row = lines[i]
                                if any('variable' in str(cell).lower() or 'B08202' in str(cell) for cell in row):
                                    data_cols = [col for col in row if col and 'B08202' in str(col)]
                                    break
                        
                        # Use standard geo column names for this geography
                        if geo == 'block':
                            geo_cols = ['state', 'county', 'tract', 'block']
                        elif geo == 'tract':
                            geo_cols = ['state', 'county', 'tract'] 
                        elif geo == 'county':
                            geo_cols = ['state', 'county']
                        else:
                            geo_cols = ['state', 'county', 'tract']
                
                if not geo_cols:
                    geo_cols = ['state', 'county', 'tract']  # Default fallback
                    
                if not data_cols:
                    # Extract from first row if it has B-table variables
                    data_cols = [col for col in lines[0] if col and 'B' in str(col) and '_' in str(col)]
                
                print(f"[DEBUG] Using geo_cols from row 5: {geo_cols}")
                print(f"[DEBUG] Using data_cols from row 1: {data_cols}")
                
                # Build column names
                col_names = geo_cols + data_cols
                print(f"[DEBUG] Final col_names: {col_names}")
                
                # Skip header rows and read data
                data_rows = []
                for i, line in enumerate(lines):
                    try:
                        # Skip obvious header rows
                        if i < 5 or not line or len([cell for cell in line if cell]) < len(geo_cols):
                            continue
                            
                        # Try to identify data rows vs header rows
                        if any(keyword in str(cell).lower() for cell in line for keyword in ['variable', 'state', 'county'] if len(str(cell)) > 10):
                            continue
                        
                        # Check if this looks like a data row (has geo codes and numbers)
                        geo_part = line[:len(geo_cols)]
                        data_part = line[len(geo_cols):len(col_names)]
                        
                        if not geo_part or not all(str(cell).strip() for cell in geo_part[:2]):  # At least state and county
                            continue
                            
                        # Build the row with proper length
                        row_data = geo_part + data_part
                        if len(row_data) < len(col_names):
                            row_data.extend([''] * (len(col_names) - len(row_data)))
                        elif len(row_data) > len(col_names):
                            row_data = row_data[:len(col_names)]
                            
                        data_rows.append(row_data)
                        
                    except Exception as e:
                        print(f"[DEBUG] Error processing line {i}: {e}")
                        continue
                
                # Create DataFrame
                df = pd.DataFrame(data_rows, columns=col_names)
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

                # use the new PL endpoint for 2020 decennial, DHC for detailed housing/group quarters, ACS5 for 2023
                if dataset == "pl":
                    api = self.census.pl  # PL 94-171 Redistricting Data
                    records = api.get([census_col[0]], geo_dict, year=year)
                elif dataset == "dhc":
                    # Use custom DHC fetcher since census library doesn't support DHC
                    records = self.fetch_dhc_data([census_col[0]], geo_dict, year)
                    # Convert records to DataFrame with proper indexing for MultiIndex compatibility
                    county_df = pd.DataFrame.from_records(records)
                    if len(county_df) > 0:
                        # Set index to geography columns
                        county_df = county_df.set_index(geo_index)
                        # Ensure data columns are float type for consistency
                        data_cols = [col for col in county_df.columns if col not in geo_index]
                        for col in data_cols:
                            county_df[col] = pd.to_numeric(county_df[col], errors='coerce').fillna(0).astype(float)
                    else:
                        # Handle empty results - create empty DataFrame with proper structure
                        county_df = pd.DataFrame(index=pd.MultiIndex.from_tuples([], names=geo_index), 
                                                columns=[census_col[0]], dtype=float)
                        county_df = county_df.fillna(0).astype(float)
                elif dataset == "acs5":
                    api = self.census.acs5
                    records = api.get([census_col[0]], geo_dict, year=year)
                else:
                    raise ValueError(f"Unsupported dataset: {dataset}")

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
        
        # Return the DataFrame after successful API fetch and cache write
        return full_df
