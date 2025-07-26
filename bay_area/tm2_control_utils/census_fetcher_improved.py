"""
Improved Census Fetcher with DHC data support

This module borrows implementation patterns from the censusdis package
to provide more robust DHC (Demographic and Housing Characteristics) data fetching.

Key improvements:
- Better error handling and exception types
- More robust URL construction for DHC endpoints
- Improved JSON parsing with error detection
- Better handling of computed variables for DHC data
"""

import logging
import os
import time
import traceback
from typing import Dict, List, Optional, Union

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class CensusApiException(Exception):
    """Exception raised when Census API calls fail."""
    pass


class DHCVariableProcessor:
    """Handles DHC computed variables that require aggregation of multiple variables."""
    
    @staticmethod
    def get_military_total(census_data: pd.DataFrame) -> pd.Series:
        """Calculate MILITARY_TOTAL from DHC P18 variables."""
        # Military GQ: P18_011N (male) + P18_062N (female)
        military_cols = ['P18_011N', 'P18_062N']
        available_cols = [col for col in military_cols if col in census_data.columns]
        
        if not available_cols:
            logger.warning("No military GQ variables found in DHC data")
            return pd.Series(0, index=census_data.index)
        
        # Convert to numeric and fill NaN with 0
        military_total = pd.Series(0, index=census_data.index)
        for col in available_cols:
            col_data = pd.to_numeric(census_data[col], errors='coerce').fillna(0)
            military_total += col_data
            
        logger.info(f"Calculated MILITARY_TOTAL from {len(available_cols)} variables: {military_total.sum():,.0f}")
        return military_total
    
    @staticmethod
    def get_university_total(census_data: pd.DataFrame) -> pd.Series:
        """Calculate UNIVERSITY_TOTAL from DHC P18 variables."""
        # University GQ: P18_010N (male) + P18_061N (female)  
        university_cols = ['P18_010N', 'P18_061N']
        available_cols = [col for col in university_cols if col in census_data.columns]
        
        if not available_cols:
            logger.warning("No university GQ variables found in DHC data")
            return pd.Series(0, index=census_data.index)
        
        # Convert to numeric and fill NaN with 0
        university_total = pd.Series(0, index=census_data.index)
        for col in available_cols:
            col_data = pd.to_numeric(census_data[col], errors='coerce').fillna(0)
            university_total += col_data
            
        logger.info(f"Calculated UNIVERSITY_TOTAL from {len(available_cols)} variables: {university_total.sum():,.0f}")
        return university_total


class ImprovedCensusFetcher:
    """
    Improved Census data fetcher with better DHC support.
    
    Borrows patterns from censusdis for robust API interaction.
    """
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = "input_2023/census_cache"):
        """Initialize the fetcher with API key and cache directory."""
        self.api_key = api_key or self._get_api_key()
        self.cache_dir = cache_dir
        self.dhc_processor = DHCVariableProcessor()
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment or file."""
        # Try environment variable first
        api_key = os.environ.get('CENSUS_API_KEY')
        if api_key:
            return api_key
            
        # Try file
        try:
            api_key_file = os.path.join("input_2023", "api", "census_api_key.txt")
            if os.path.exists(api_key_file):
                with open(api_key_file, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            logger.debug(f"Could not read API key file: {e}")
            
        return None
    
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _construct_url(self, dataset: str, year: str, variables: List[str], geography: str) -> tuple:
        """Construct Census API URL and parameters."""
        # Handle DHC dataset special case with correct endpoint format
        if dataset == 'dhc':
            base_url = f"https://api.census.gov/data/{year}/dec/dhc"
        else:
            base_url = f"https://api.census.gov/data/{year}/{dataset}"
        
        params = {
            'get': ','.join(variables),
            'for': geography,
        }
        
        if self.api_key:
            params['key'] = self.api_key
            
        return base_url, params
    
    def _make_request(self, url: str, params: Dict[str, str]) -> pd.DataFrame:
        """Make a request to the Census API with improved error handling."""
        self._rate_limit()
        
        logger.debug(f"Making Census API request: {url}")
        logger.debug(f"Parameters: {params}")
        
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
                error_msg = f"Census API request failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise CensusApiException(error_msg)
                
        except requests.RequestException as e:
            error_msg = f"Network error during Census API request: {e}"
            logger.error(error_msg)
            raise CensusApiException(error_msg) from e
    
    def _parse_census_json(self, json_data) -> pd.DataFrame:
        """Parse Census API JSON response into DataFrame."""
        if not isinstance(json_data, list) or len(json_data) < 1:
            raise CensusApiException(f"Expected JSON data to be a list with at least one row, got {type(json_data)}")
        
        if not isinstance(json_data[0], list):
            raise CensusApiException(f"Expected first row to be a list of column names")
        
        # Extract headers and data
        headers = json_data[0]
        data_rows = json_data[1:]
        
        if not data_rows:
            logger.warning("Census API returned headers but no data rows")
            return pd.DataFrame(columns=headers)
        
        # Create DataFrame with cleaned column names
        cleaned_headers = [
            col.upper()
            .replace(" ", "_")
            .replace("-", "_")
            .replace("/", "_")
            .replace("(", "")
            .replace(")", "")
            for col in headers
        ]
        
        df = pd.DataFrame(data_rows, columns=cleaned_headers)
        
        # Convert numeric columns
        for col in df.columns:
            if col not in ['STATE', 'COUNTY', 'TRACT', 'BLOCK', 'BLOCK_GROUP']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        logger.info(f"Parsed Census data: {len(df)} rows, {len(df.columns)} columns")
        return df
    
    def get_dhc_data_with_computed_variables(self, year: str, geography: str, 
                                           base_variables: List[str], 
                                           computed_variables: List[str]) -> pd.DataFrame:
        """
        Fetch DHC data and compute derived variables.
        
        Args:
            year: Census year (e.g., '2020')
            geography: Geography specification (e.g., 'block:*&in=state:06+county:001')
            base_variables: Base variables to fetch from API
            computed_variables: Variables to compute (e.g., ['MILITARY_TOTAL', 'UNIVERSITY_TOTAL'])
        """
        logger.info(f"Fetching DHC data for {len(base_variables)} base variables and {len(computed_variables)} computed variables")
        
        # Fetch base data
        url, params = self._construct_url('dhc', year, base_variables, geography)
        df = self._make_request(url, params)
        
        if df.empty:
            logger.warning("No DHC data returned from Census API")
            return df
        
        # Add computed variables
        for computed_var in computed_variables:
            if computed_var == 'MILITARY_TOTAL':
                df[computed_var] = self.dhc_processor.get_military_total(df)
            elif computed_var == 'UNIVERSITY_TOTAL':
                df[computed_var] = self.dhc_processor.get_university_total(df)
            else:
                logger.warning(f"Unknown computed variable: {computed_var}")
                df[computed_var] = 0
        
        return df
    
    def get_census_data(self, dataset: str, year: str, table: str, geography: str) -> pd.DataFrame:
        """
        Enhanced census data fetcher with improved DHC support.
        
        Args:
            dataset: Census dataset (e.g., 'acs/acs5', 'dhc', 'pl')
            year: Year (e.g., '2023', '2020')
            table: Table or variable name
            geography: Geography specification
        """
        logger.info(f"Fetching {dataset} data for {table} from {year}")
        
        # Handle DHC computed variables specially
        if dataset == 'dhc' and table in ['MILITARY_TOTAL', 'UNIVERSITY_TOTAL']:
            logger.info(f"Processing DHC computed variable: {table}")
            
            if table == 'MILITARY_TOTAL':
                base_vars = ['P18_011N', 'P18_062N']  # Military GQ male + female
                computed_vars = ['MILITARY_TOTAL']
            elif table == 'UNIVERSITY_TOTAL':
                base_vars = ['P18_010N', 'P18_061N']  # University GQ male + female  
                computed_vars = ['UNIVERSITY_TOTAL']
            else:
                raise ValueError(f"Unknown DHC computed variable: {table}")
            
            return self.get_dhc_data_with_computed_variables(
                year, geography, base_vars, computed_vars
            )
        
        # Handle regular variables
        if isinstance(table, str) and table.startswith(('P', 'H', 'PCT')):
            # Single variable
            variables = [table]
        elif hasattr(table, '__iter__') and not isinstance(table, str):
            # List of variables
            variables = list(table)
        else:
            # Table name - for now just treat as single variable
            variables = [table]
        
        url, params = self._construct_url(dataset, year, variables, geography)
        return self._make_request(url, params)


def test_improved_fetcher():
    """Test the improved fetcher with DHC data."""
    logger.info("Testing improved Census fetcher with DHC data")
    
    fetcher = ImprovedCensusFetcher()
    
    try:
        # Test DHC computed variables
        logger.info("Testing MILITARY_TOTAL computation")
        military_data = fetcher.get_census_data(
            'dhc', '2020', 'MILITARY_TOTAL', 
            'block:*&in=state:06+county:001+tract:400100'  # Small area for testing
        )
        logger.info(f"Military data shape: {military_data.shape}")
        logger.info(f"Military total: {military_data['MILITARY_TOTAL'].sum():,.0f}")
        
        logger.info("Testing UNIVERSITY_TOTAL computation")
        university_data = fetcher.get_census_data(
            'dhc', '2020', 'UNIVERSITY_TOTAL',
            'block:*&in=state:06+county:001+tract:400100'  # Small area for testing
        )
        logger.info(f"University data shape: {university_data.shape}")
        logger.info(f"University total: {university_data['UNIVERSITY_TOTAL'].sum():,.0f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Run test
    success = test_improved_fetcher()
    print(f"Test {'PASSED' if success else 'FAILED'}")
