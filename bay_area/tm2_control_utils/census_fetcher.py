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


class DHCVariableProcessor:
    """Handles DHC computed variables that require aggregation of multiple variables."""
    
    @staticmethod
    def get_military_total(census_data: pd.DataFrame) -> pd.Series:
        """Calculate MILITARY_TOTAL from DHC P18 variables."""
        # Military GQ: P18_011N (male) + P18_062N (female)
        military_cols = ['P18_011N', 'P18_062N']
        available_cols = [col for col in military_cols if col in census_data.columns]
        
        if not available_cols:
            logging.warning("No military GQ variables found in DHC data")
            return pd.Series(0, index=census_data.index)
        
        # Convert to numeric and fill NaN with 0
        military_total = pd.Series(0, index=census_data.index)
        for col in available_cols:
            col_data = pd.to_numeric(census_data[col], errors='coerce').fillna(0)
            military_total += col_data
            
        logging.info(f"Calculated MILITARY_TOTAL from {len(available_cols)} variables: {military_total.sum():,.0f}")
        return military_total
    
    @staticmethod
    def get_university_total(census_data: pd.DataFrame) -> pd.Series:
        """Calculate UNIVERSITY_TOTAL from DHC P18 variables."""
        # University GQ: P18_010N (male) + P18_061N (female)  
        university_cols = ['P18_010N', 'P18_061N']
        available_cols = [col for col in university_cols if col in census_data.columns]
        
        if not available_cols:
            logging.warning("No university GQ variables found in DHC data")
            return pd.Series(0, index=census_data.index)
        
        # Convert to numeric and fill NaN with 0
        university_total = pd.Series(0, index=census_data.index)
        for col in available_cols:
            col_data = pd.to_numeric(census_data[col], errors='coerce').fillna(0)
            university_total += col_data
            
        logging.info(f"Calculated UNIVERSITY_TOTAL from {len(available_cols)} variables: {university_total.sum():,.0f}")
        return university_total


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
        self.dhc_processor = DHCVariableProcessor()
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
        """Parse ACS5 format: Multi-row header with metadata and geography."""
        if len(lines) < 6:
            return None
            
        # ACS5 format typically has:
        # Multiple header rows with variable names, metadata
        # Then data rows starting with geography codes
        
        # Find the first data row by looking for rows that start with "06" (California state code)
        data_start_row = None
        for i, line in enumerate(lines):
            cells = [cell.strip() for cell in line.split(delimiter)]
            if len(cells) >= 2 and cells[0] == '06' and cells[1].isdigit():
                data_start_row = i
                break
        
        if data_start_row is None:
            logging.warning("Could not find data rows starting with '06' in ACS5 file")
            return None
        
        logging.info(f"Found ACS5 data starting at row {data_start_row}")
        
        # Find variable definitions row (contains B-table variables)
        variable_row = None
        for i in range(data_start_row):  # Only check header rows
            cells = [cell.strip() for cell in lines[i].split(delimiter)]
            # Look for cells with B-table format (e.g., B19001_001E, B08202_001E)
            b_vars = [cell for cell in cells if cell and 'B' in cell and '_' in cell and 'E' in cell]
            if len(b_vars) >= 3:  # Need at least a few variables
                variable_row = i
                logging.info(f"Found variable row {i} with {len(b_vars)} B-variables")
                break
        
        if variable_row is None:
            logging.warning("Could not identify variable row in ACS5 file")
            return None
        
        # Extract variable columns from the variable row
        var_cells = lines[variable_row].split(delimiter)
        data_cols = []
        for cell in var_cells:
            cell = cell.strip()
            if cell and 'B' in cell and '_' in cell and 'E' in cell:
                data_cols.append(cell)
        
        logging.info(f"Found {len(data_cols)} data columns: {data_cols[:5]}...")
        
        # Use standard geography columns based on geography level
        geo_cols = geo_index.copy() if geo_index else ['state', 'county']
        
        # Build complete column list
        all_cols = geo_cols + data_cols
        
        # Parse data rows starting from data_start_row
        data_rows = []
        for i in range(data_start_row, len(lines)):
            line = lines[i].strip()
            if line:
                row_values = [val.strip() for val in line.split(delimiter)]
                if len(row_values) >= len(geo_cols):
                    # Take first len(geo_cols) as geography, then data columns
                    geo_part = row_values[:len(geo_cols)]
                    data_part = row_values[len(geo_cols):len(geo_cols) + len(data_cols)]
                    
                    # Ensure we have enough data values
                    while len(data_part) < len(data_cols):
                        data_part.append('0')
                    
                    # Combine geo and data parts
                    full_row = geo_part + data_part[:len(data_cols)]
                    data_rows.append(full_row)
        
        if not data_rows:
            logging.warning("No data rows found in ACS5 file")
            return None
            
        logging.info(f"Parsed {len(data_rows)} data rows")
        
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
        
        logging.info(f"Parsed ACS5 format: {len(df)} rows, {len(df.columns)} columns")
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

    def get_dhc_data_with_computed_variables(self, variables: list, geo_dict: dict, year: str) -> pd.DataFrame:
        """
        Fetch DHC data and compute derived variables like MILITARY_TOTAL and UNIVERSITY_TOTAL.
        
        Args:
            variables: List of variables including computed ones
            geo_dict: Geography specification
            year: Census year (e.g., '2020')
        """
        logging.info(f"Fetching DHC data with computed variables: {variables}")
        
        # Separate base variables from computed variables
        base_variables = []
        computed_variables = []
        
        for var in variables:
            if var in ['MILITARY_TOTAL', 'UNIVERSITY_TOTAL']:
                computed_variables.append(var)
                # Add the component variables we need
                if var == 'MILITARY_TOTAL':
                    base_variables.extend(['P18_011N', 'P18_062N'])  # Military GQ male + female
                elif var == 'UNIVERSITY_TOTAL':
                    base_variables.extend(['P18_010N', 'P18_061N'])  # University GQ male + female
            else:
                base_variables.append(var)
        
        # Remove duplicates while preserving order
        base_variables = list(dict.fromkeys(base_variables))
        
        # Construct the DHC API URL with correct endpoint format
        base_url = f"https://api.census.gov/data/{year}/dec/dhc"
        
        # Build geography string
        geo_parts = []
        for key, value in geo_dict.items():
            if key == 'for':
                geo_parts.append(f"for={value}")
            elif key == 'in':
                geo_parts.append(f"in={value}")
        
        params = {
            'get': ','.join(base_variables),
            'key': self.CENSUS_API_KEY
        }
        
        # Add geography parameters
        for key, value in geo_dict.items():
            if key not in ['get', 'key']:
                params[key] = value
        
        # Fetch base data
        df = self._make_robust_dhc_request(base_url, params)
        
        if df.empty:
            logging.warning("No DHC data returned from Census API")
            return df
        
        # Add computed variables
        for computed_var in computed_variables:
            if computed_var == 'MILITARY_TOTAL':
                df[computed_var] = self.dhc_processor.get_military_total(df)
            elif computed_var == 'UNIVERSITY_TOTAL':
                df[computed_var] = self.dhc_processor.get_university_total(df)
            else:
                logging.warning(f"Unknown computed variable: {computed_var}")
                df[computed_var] = 0
        
        return df

    def fetch_dhc_data(self, variables, geo_dict, year):
        """
        Enhanced DHC data fetcher with support for computed variables.
        Includes caching to M: drive location for reuse.
        """
        logging.info(f"fetch_dhc_data called with variables={variables}, geo_dict={geo_dict}, year={year}")
        
        # Handle different variable formats
        if isinstance(variables, list):
            variable_list = variables
        else:
            variable_list = [variables]
            
        # Check if any variables are computed variables that need special handling
        needs_computed_handling = any(var in ['MILITARY_TOTAL', 'UNIVERSITY_TOTAL'] for var in variable_list)
        
        if needs_computed_handling:
            logging.info("Using enhanced computed variable handling for DHC data")
            return self.get_dhc_data_with_computed_variables(variable_list, geo_dict, year)
        
        # Original logic for regular DHC variables
        if len(variable_list) == 1:
            variable_name = variable_list[0]
        else:
            variable_name = variable_list[0]  # Take first for naming
            
        # Check if this is a computed variable in the old format
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
            if len(variable_list) == 1:
                variables_str = variable_name
            else:
                variables_str = ','.join(variable_list)
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
