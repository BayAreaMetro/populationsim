import os
import pandas as pd
import logging
import requests
import time
from census import Census
from tm2_control_utils.config import (
    CENSUS_API_KEY_FILE,
    LOCAL_CACHE_FOLDER,
    CA_STATE_FIPS,
    BAY_AREA_COUNTY_FIPS,
    CENSUS_DEFINITIONS,
)
import traceback


class CensusApiException(Exception):
    """Exception raised when Census API calls fail."""
    pass


class PLVariableProcessor:
    """Handles PL 94-171 Redistricting dataset variables for group quarters."""
    
    @staticmethod
    def get_bay_area_pl_data(variables: list, geo_dict: dict, year: str, api_key: str) -> pd.DataFrame:
        """
        Fetch Bay Area block-level data from PL 94-171 dataset.
        
        Args:
            variables: List of PL variables (e.g., ['P5_001N', 'P5_008N', 'P5_009N'])
            geo_dict: Geography specification (should be block level)
            year: Census year (e.g., '2020')
            api_key: Census API key
        
        Returns:
            pd.DataFrame: Combined block-level data for all Bay Area counties
        """
        logging.info(f"Fetching PL data for variables: {variables}")
        
        # PL dataset endpoint
        base_url = f"https://api.census.gov/data/{year}/dec/pl"
        
        all_blocks_data = []
        
        for county_name, county_fips in BAY_AREA_COUNTY_FIPS.items():
            logging.info(f"Fetching PL blocks for {county_name} County ({county_fips})...")
            
            try:
                # Build API URL
                var_list = ",".join(variables)
                api_url = f"{base_url}?get=NAME,{var_list}&for=block:*&in=state:{CA_STATE_FIPS}&in=county:{county_fips}&key={api_key}"
                
                response = requests.get(api_url, timeout=120)
                
                if response.status_code == 200:
                    json_data = response.json()
                    
                    if json_data and len(json_data) > 1:
                        # Convert to DataFrame
                        county_df = pd.DataFrame(json_data[1:], columns=json_data[0])
                        
                        # Add county name for easier identification
                        county_df['county_name'] = county_name
                        
                        # Convert numeric columns
                        for var in variables:
                            county_df[var] = pd.to_numeric(county_df[var], errors='coerce')
                        
                        logging.info(f"  {county_name}: {len(county_df):,} blocks retrieved")
                        all_blocks_data.append(county_df)
                
                else:
                    logging.error(f"  {county_name}: PL API request failed with status {response.status_code}")
                    
            except Exception as e:
                logging.error(f"  {county_name}: Error fetching PL data - {e}")
            
            # Small delay to be respectful to Census API
            time.sleep(0.2)
        
        if not all_blocks_data:
            logging.error("No PL block data retrieved for any county!")
            return pd.DataFrame()
        
        # Combine all county data
        combined_df = pd.concat(all_blocks_data, ignore_index=True)
        
        total_blocks = len(combined_df)
        logging.info(f"Combined PL data: {total_blocks:,} blocks from {len(all_blocks_data)} counties")
        
        return combined_df





class CensusFetcher:
    """
    Class to fetch the census data needed for these controls and cache them.

    Uses the census python package (https://pypi.org/project/census/)
    Enhanced with improved DHC support and error handling.
    """

    def __init__(self):
        """
        Read the census api key and instantiate the census object.
        """
        with open(CENSUS_API_KEY_FILE) as f:
            self.CENSUS_API_KEY = f.read().strip()
        self.census = Census(self.CENSUS_API_KEY)
       
        self.pl_processor = PLVariableProcessor()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        logging.debug("census object instantiated with DHC and PL support")

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _make_robust_dhc_request(self, url: str, params: dict) -> pd.DataFrame:
        """Make a robust DHC request with better error handling."""
        self._rate_limit()
        
        logging.debug(f"Making DHC API request: {url}")
        logging.debug(f"Parameters: {params}")
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                try:
                    json_data = response.json()
                    return self._parse_census_json(json_data)
                except requests.exceptions.JSONDecodeError as e:
                    if "You included a key with this request, however, it is not valid." in response.text:
                        raise CensusApiException(f"Census API key is invalid") from e
                    else:
                        raise CensusApiException(f"Unable to parse Census API response as JSON: {response.text}") from e
            else:
                error_msg = f"DHC API request failed with status {response.status_code}: {response.text}"
                logging.error(error_msg)
                raise CensusApiException(error_msg)
                
        except requests.RequestException as e:
            error_msg = f"Network error during DHC API request: {e}"
            logging.error(error_msg)
            raise CensusApiException(error_msg) from e

    def _parse_census_json(self, json_data) -> pd.DataFrame:
        """Parse Census API JSON response into DataFrame with better error handling."""
        if not isinstance(json_data, list) or len(json_data) < 1:
            raise CensusApiException(f"Expected JSON data to be a list with at least one row, got {type(json_data)}")
        
        if not isinstance(json_data[0], list):
            raise CensusApiException(f"Expected first row to be a list of column names")
        
        # Extract headers and data
        headers = json_data[0]
        data_rows = json_data[1:]
        
        if not data_rows:
            logging.warning("Census API returned headers but no data rows")
            return pd.DataFrame(columns=headers)
        
        df = pd.DataFrame(data_rows, columns=headers)
        
        # Convert numeric columns (avoid geography columns)
        for col in df.columns:
            if col not in ['state', 'county', 'tract', 'block', 'block group']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        logging.info(f"Parsed DHC data: {len(df)} rows, {len(df.columns)} columns")
        return df

    def _parse_cached_census_file(self, file_path: str, dataset: str, table: str, geo: str, geo_index: list) -> pd.DataFrame:
        """
        Robust parser for different census cached file formats.
        
        Args:
            file_path: Path to cached CSV file
            dataset: Dataset type ('acs1', 'acs5', 'pl')
            table: Table name (e.g., 'B01003', 'H1_002N')
            geo: Geography level ('county', 'tract', 'block', etc.)
            geo_index: Expected geography column names
            
        Returns:
            pd.DataFrame: Parsed data with proper columns
        """
        logging.info(f"Parsing cached file: {file_path} (dataset: {dataset}, table: {table}, geo: {geo})")
        
        try:
            # Read raw file content
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read().strip()
            
            if not content:
                logging.error(f"Empty file: {file_path}")
                return None
                
            lines = content.split('\n')
            if len(lines) < 2:
                logging.error(f"File has fewer than 2 lines: {file_path}")
                return None
            
            # Detect delimiter
            delimiter = '\t' if '\t' in lines[0] else ','
            
            # Parse based on dataset type
            if dataset == 'acs1':
                return self._parse_acs1_format(lines, delimiter, geo_index)
            elif dataset == 'acs5':
                return self._parse_acs5_format(lines, delimiter, geo_index)
            elif dataset == 'pl':
                return self._parse_pl_format(lines, delimiter, geo_index)
            else:
                # Try simple CSV format
                return self._parse_simple_csv(lines, delimiter, geo_index)
                
        except Exception as e:
            logging.error(f"Error parsing {file_path}: {e}")
            logging.error(traceback.format_exc())
            return None

    def _parse_acs1_format(self, lines: list, delimiter: str, geo_index: list) -> pd.DataFrame:
        """Parse ACS1 format: 2-row header with variables and geography."""
        if len(lines) < 3:
            return None
            
        # ACS1 format:
        # Row 1: variable[delim][empty][delim]variable_code (e.g., "variable,,B25001_001E")
        # Row 2: geo_col1[delim]geo_col2[delim][empty] (e.g., "state,county,")
        # Row 3+: geo_data[delim]geo_data[delim]value (e.g., "06,001,646309.0")
        
        # Parse header row to get variable names
        header_parts = lines[0].split(delimiter)
        data_cols = []
        for part in header_parts:
            part = part.strip()
            if part and part != 'variable' and ('B' in part or 'P' in part or 'H' in part):
                data_cols.append(part)
        
        # Parse geography row to get geo column names  
        geo_parts = lines[1].split(delimiter)
        geo_cols = []
        for part in geo_parts:
            part = part.strip()
            if part and part in ['state', 'county', 'tract', 'block', 'block group']:
                geo_cols.append(part)
        
        # If we don't have proper geo columns, use the expected ones
        if not geo_cols:
            geo_cols = geo_index.copy() if geo_index else ['state', 'county']
        
        logging.info(f"ACS1 parsing: geo_cols={geo_cols}, data_cols={data_cols}")
        
        # Build complete column list
        all_cols = geo_cols + data_cols
        
        # Parse data rows (starting from row 3)
        data_rows = []
        for line in lines[2:]:
            line = line.strip()
            if line:
                row_values = [val.strip() for val in line.split(delimiter)]
                # Remove empty trailing values
                while row_values and not row_values[-1]:
                    row_values.pop()
                    
                if len(row_values) >= len(geo_cols):
                    # Ensure row has correct length
                    while len(row_values) < len(all_cols):
                        row_values.append('0')
                    data_rows.append(row_values[:len(all_cols)])
        
        if not data_rows:
            logging.warning("No data rows found in ACS1 file")
            return None
            
        logging.info(f"Parsed {len(data_rows)} ACS1 data rows")
        
        # Create DataFrame
        df = pd.DataFrame(data_rows, columns=all_cols)
        
        # Convert data columns to numeric
        for col in data_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Ensure geography columns are strings  
        for col in geo_cols:
            if col in df.columns:
                df[col] = df[col].astype(str)
        
        # Rename geography columns to match expected names if needed
        if len(geo_cols) == len(geo_index):
            rename_dict = dict(zip(geo_cols, geo_index))
            df.rename(columns=rename_dict, inplace=True)
            logging.info(f"Renamed geo columns: {rename_dict}")
        
        logging.info(f"Parsed ACS1 format: {len(df)} rows, {len(df.columns)} columns")
        return df

    def _parse_acs5_format(self, lines: list, delimiter: str, geo_index: list) -> pd.DataFrame:
        """Parse ACS5 format: Multi-row header with metadata and geography (variable, sex, age_min, age_max)."""
        if len(lines) < 6:
            return None

        # Find the header row with 'variable' as the first cell
        header_row = None
        for i, line in enumerate(lines[:6]):
            cells = [cell.strip() for cell in line.split(delimiter)]
            if cells and cells[0].lower() == 'variable':
                header_row = i
                break

        if header_row is None or header_row + 4 > len(lines):
            logging.warning("Could not find expected ACS5 multi-row header block")
            return None

        # The next three rows are metadata: sex, age_min, age_max
        # The row after that is the first data row
        meta_rows = lines[header_row:header_row+4]
        variable_names = [cell.strip() for cell in meta_rows[0].split(delimiter)]
        geo_cols = geo_index.copy() if geo_index else ['state', 'county']
        data_cols = variable_names[len(geo_cols):]  # skip geo columns

        # Data starts after the metadata rows
        data_start_row = header_row + 4
        data_rows = []
        for i in range(data_start_row, len(lines)):
            line = lines[i].strip()
            if line:
                row_values = [val.strip() for val in line.split(delimiter)]
                if len(row_values) >= len(geo_cols):
                    geo_part = row_values[:len(geo_cols)]
                    data_part = row_values[len(geo_cols):len(geo_cols) + len(data_cols)]
                    while len(data_part) < len(data_cols):
                        data_part.append('0')
                    full_row = geo_part + data_part[:len(data_cols)]
                    data_rows.append(full_row)

        if not data_rows:
            logging.warning("No data rows found in ACS5 file")
            return None

        all_cols = geo_cols + data_cols
        df = pd.DataFrame(data_rows, columns=all_cols)

        # Convert data columns to numeric
        for col in data_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Ensure geography columns are strings
        for col in geo_cols:
            if col in df.columns:
                df[col] = df[col].astype(str)

        logging.info(f"Parsed ACS5 format (multi-row header): {len(df)} rows, {len(df.columns)} columns")
        return df

    def _parse_pl_format(self, lines: list, delimiter: str, geo_index: list) -> pd.DataFrame:
        """Parse PL format: Simple single-header format."""
        if len(lines) < 2:
            return None
            
        # PL format is simple: header row + data rows
        header = [col.strip() for col in lines[0].split(delimiter)]
        
        data_rows = []
        for line in lines[1:]:
            if line.strip():
                row_values = [val.strip() for val in line.split(delimiter)]
                if len(row_values) == len(header):
                    data_rows.append(row_values)
        
        if not data_rows:
            return None
            
        df = pd.DataFrame(data_rows, columns=header)
        
        # Convert appropriate columns to numeric (keep geography as strings)
        for col in df.columns:
            if col not in geo_index:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        logging.info(f"Parsed PL format: {len(df)} rows, {len(df.columns)} columns")
        return df

    def _parse_simple_csv(self, lines: list, delimiter: str, geo_index: list) -> pd.DataFrame:
        """Parse as simple CSV with header row."""
        if len(lines) < 2:
            return None
            
        # Try to find a reasonable header row
        header_row = 0
        for i, line in enumerate(lines[:5]):
            cells = [cell.strip() for cell in line.split(delimiter)]
            # Look for a row that has reasonable column names
            if len(cells) >= 3 and not all(cell.isdigit() for cell in cells[:3]):
                header_row = i
                break
        
        header = [col.strip() for col in lines[header_row].split(delimiter)]
        
        data_rows = []
        for line in lines[header_row + 1:]:
            if line.strip():
                row_values = [val.strip() for val in line.split(delimiter)]
                if len(row_values) >= len(geo_index):  # At least enough for geography
                    # Pad or trim to match header length
                    while len(row_values) < len(header):
                        row_values.append('0')
                    data_rows.append(row_values[:len(header)])
        
        if not data_rows:
            return None
            
        df = pd.DataFrame(data_rows, columns=header)
        
        # Convert numeric columns
        for col in df.columns:
            if col not in geo_index:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        logging.info(f"Parsed simple CSV: {len(df)} rows, {len(df.columns)} columns")
        return df

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

        # Special handling for PL variables 
        if dataset == 'pl':
            logging.info(f"Processing PL variable: {table}")
            
            # Check for cached PL data first
            if os.path.exists(table_cache_file):
                logging.info(f"Reading PL data from cache: {table_cache_file}")
                try:
                    cached_df = pd.read_csv(table_cache_file)
                    # Set proper index
                    cached_df = cached_df.set_index(geo_index)
                    logging.info(f"Loaded PL cached data: {len(cached_df)} rows")
                    print(f"[DEBUG] EXIT get_census_data (PL cached): df.columns: {list(cached_df.columns)}")
                    return cached_df
                except Exception as e:
                    logging.warning(f"Failed to read PL cache file {table_cache_file}: {e}")
            
            # Fetch fresh PL data
            pl_variables = [table]  # PL variables are direct (e.g., P5_001N)
            
            # Build geo_dict for PL API call (block level only for group quarters)
            geo_dict = {}
            if geo == 'block':
                geo_dict['for'] = 'block:*'
                geo_dict['in'] = f'state:{CA_STATE_FIPS} county:*'
            else:
                raise ValueError(f"PL group quarters data only available at block level, not {geo}")
            
            # Use PL processor to get Bay Area data
            result_df = self.pl_processor.get_bay_area_pl_data(pl_variables, geo_dict, year, self.CENSUS_API_KEY)
            
            if not result_df.empty:
                # Keep only the requested variable and geography columns
                keep_cols = geo_index + [table]
                available_cols = [col for col in keep_cols if col in result_df.columns]
                result_df = result_df[available_cols]
                
                # Set proper index
                result_df = result_df.set_index(geo_index)
                
                # Cache the results
                try:
                    os.makedirs(os.path.dirname(table_cache_file), exist_ok=True)
                    # Reset index for saving to CSV 
                    save_df = result_df.reset_index()
                    save_df.to_csv(table_cache_file, index=False)
                    logging.info(f"Wrote PL data to cache: {table_cache_file}")
                except Exception as e:
                    logging.warning(f"Failed to write PL cache file {table_cache_file}: {e}")
                
                logging.info(f"Successfully fetched PL {table}: {len(result_df)} rows, total value: {result_df[table].sum():,.0f}")
                print(f"[DEBUG] EXIT get_census_data (PL): df.columns: {list(result_df.columns)}")
                return result_df
            else:
                logging.warning(f"No PL data returned for variable {table}")
                return pd.DataFrame(index=pd.MultiIndex.from_tuples([], names=geo_index))

        # Special handling for DHC computed variables
        if dataset == 'dhc' and table in ['MILITARY_TOTAL', 'UNIVERSITY_TOTAL']:
            logging.info(f"Processing DHC computed variable: {table}")
            
            # Build geo_dict for DHC API call
            geo_dict = {}
            if geo == 'block':
                geo_dict['for'] = 'block:*'
                geo_dict['in'] = f'state:{CA_STATE_FIPS} county:*'
            elif geo == 'tract':
                geo_dict['for'] = 'tract:*'
                geo_dict['in'] = f'state:{CA_STATE_FIPS} county:*'
            elif geo == 'county':
                geo_dict['for'] = 'county:*'
                geo_dict['in'] = f'state:{CA_STATE_FIPS}'
            else:
                raise ValueError(f"Unsupported geography for DHC computed variables: {geo}")
            
            # Use the enhanced DHC fetcher for computed variables
            result_df = self.get_dhc_data_with_computed_variables([table], geo_dict, year)
            
            if not result_df.empty:
                # Set proper index
                result_df = result_df.set_index(geo_index)
                # Create MultiIndex columns if needed
                if table in result_df.columns:
                    result_df = result_df[[table]]  # Keep only the computed variable column
                logging.info(f"Successfully computed {table}: {len(result_df)} rows, total value: {result_df[table].sum():,.0f}")
                print(f"[DEBUG] EXIT get_census_data (computed): df.columns: {list(result_df.columns)}")
                return result_df
            else:
                logging.warning(f"No data returned for computed variable {table}")
                return pd.DataFrame(index=pd.MultiIndex.from_tuples([], names=geo_index))

        table_def = CENSUS_DEFINITIONS[table]
        table_cols = table_def[0]  # e.g. ['variable','pers_min','pers_max']

        if os.path.exists(table_cache_file):
            logging.info(f"Reading {table_cache_file}")
            try:
                # Robust parser for different census file formats
                df = self._parse_cached_census_file(table_cache_file, dataset, table, geo, geo_index)
                if df is not None:
                    return df
                    
                # Fallback to simple CSV read if custom parser fails
                logging.warning(f"Custom parser failed for {table_cache_file}, trying simple CSV read")
                df = pd.read_csv(table_cache_file)
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
                elif dataset == "acs1":
                    api = self.census.acs1
                    records = api.get([census_col[0]], geo_dict, year=year)
                else:
                    raise ValueError(f"Unsupported dataset: {dataset}")

                # For non-DHC datasets, use the standard DataFrame creation
                if dataset != "dhc":
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

        # Create MultiIndex columns - handle computed variables differently
        if dataset == "dhc" and table in CENSUS_DEFINITIONS:
            table_def = CENSUS_DEFINITIONS[table]
            if len(table_def) > 1 and len(table_def[1]) > 1:
                # This is a computed variable - use simpler column naming
                # The computed variable should already have the correct column name
                # No need for MultiIndex in this case
                logging.info(f"DHC computed variable {table} - keeping simple column structure")
                pass  # Keep existing column structure
            else:
                # Single DHC variable - use MultiIndex 
                full_df.columns = pd.MultiIndex.from_tuples(
                    multi_col_def,
                    names=table_cols
                )
        else:
            # Regular MultiIndex for non-DHC or non-computed variables
            full_df.columns = pd.MultiIndex.from_tuples(
                multi_col_def,
                names=table_cols
            )
            
        os.makedirs(os.path.dirname(table_cache_file), exist_ok=True)
        full_df.to_csv(table_cache_file, header=True, index=True)
        logging.info(f"Wrote {table_cache_file}")
        
        # Return the DataFrame after successful API fetch and cache write
        return full_df
