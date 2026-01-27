"""
ACS Data Fetcher - Main module for fetching Census ACS data.
"""
import pandas as pd
from pathlib import Path
from census import Census
from typing import List, Dict, Optional, Union
import time


class ACSDataFetcher:
    """
    Fetcher for American Community Survey (ACS) data via Census API.
    """
    
    def __init__(self, api_key_file: Union[str, Path]):
        """
        Initialize the ACS data fetcher.
        
        Args:
            api_key_file: Path to file containing Census API key
        """
        self.api_key_file = Path(api_key_file)
        self._load_api_key()
    
    def _load_api_key(self):
        """Load Census API key from file."""
        try:
            with open(self.api_key_file) as f:
                self.api_key = f.read().strip()
            self.census = Census(self.api_key)
            print(f"✓ API key loaded from {self.api_key_file}")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"API key file not found: {self.api_key_file}\n"
                "Get a free API key from https://api.census.gov/data/key_signup.html"
            )
        except Exception as e:
            raise Exception(f"Error loading API key: {e}")
    
    def fetch_variables(
        self,
        variables: List[str],
        year: int,
        counties: Dict[str, str],
        state_fips: str = "06",
        dataset: str = "acs1",
        include_geography: bool = True
    ) -> pd.DataFrame:
        """
        Fetch specific ACS variables for multiple counties.
        
        Args:
            variables: List of variable codes (e.g., ['B08006_001E', 'B08006_017E'])
            year: Census year (e.g., 2019, 2023)
            counties: Dict mapping county names to FIPS codes
            state_fips: State FIPS code (default: "06" for California)
            dataset: ACS dataset ('acs1' or 'acs5')
            include_geography: Include NAME field for geographic labels
        
        Returns:
            DataFrame with requested variables for all counties
        """
        print(f"\nFetching {year} ACS {dataset.upper()} data...")
        print(f"  Variables: {', '.join(variables)}")
        
        if include_geography and 'NAME' not in variables:
            variables = variables + ['NAME']
        
        all_data = []
        
        # Select dataset
        if dataset == 'acs1':
            api_dataset = self.census.acs1
        elif dataset == 'acs5':
            api_dataset = self.census.acs5
        else:
            raise ValueError(f"Unknown dataset: {dataset}. Use 'acs1' or 'acs5'")
        
        for county_name, county_fips in counties.items():
            print(f"  Fetching {county_name} County ({county_fips})...")
            
            try:
                data = api_dataset.get(
                    variables,
                    geo={
                        'for': f'county:{county_fips}',
                        'in': f'state:{state_fips}'
                    },
                    year=year
                )
                
                if data:
                    df = pd.DataFrame(data)
                    df['county_name'] = county_name
                    all_data.append(df)
                    print(f"    ✓ Retrieved {len(df)} records")
                else:
                    print(f"    ✗ No data returned")
                    
            except Exception as e:
                print(f"    ✗ Error: {e}")
                continue
            
            # Rate limit: small delay between requests
            time.sleep(0.1)
        
        if not all_data:
            print(f"  ✗ No data retrieved for {year}")
            return None
        
        # Combine all counties
        combined = pd.concat(all_data, ignore_index=True)
        combined['year'] = year
        
        print(f"  ✓ Total records: {len(combined)}")
        
        return combined
    
    def fetch_table(
        self,
        table_code: str,
        years: List[int],
        counties: Dict[str, str],
        state_fips: str = "06",
        dataset: str = "acs1",
        variables: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Fetch an entire ACS table or specific variables for multiple years.
        
        Args:
            table_code: Table code (e.g., 'B08006')
            years: List of years to fetch
            counties: Dict mapping county names to FIPS codes
            state_fips: State FIPS code
            dataset: ACS dataset ('acs1' or 'acs5')
            variables: Specific variables to fetch (if None, attempts common patterns)
        
        Returns:
            Combined DataFrame for all years
        """
        if variables is None:
            # Default to _001E (total) and common variables
            print(f"Note: No variables specified. You may want to specify exact variables.")
            variables = [f'{table_code}_001E']
        
        all_years = []
        
        for year in years:
            df = self.fetch_variables(
                variables=variables,
                year=year,
                counties=counties,
                state_fips=state_fips,
                dataset=dataset
            )
            
            if df is not None:
                all_years.append(df)
        
        if not all_years:
            return None
        
        combined = pd.concat(all_years, ignore_index=True)
        return combined
    
    def calculate_percentage(
        self,
        df: pd.DataFrame,
        numerator_col: str,
        denominator_col: str,
        output_col: str = 'percentage'
    ) -> pd.DataFrame:
        """
        Calculate percentage from two columns.
        
        Args:
            df: Input DataFrame
            numerator_col: Column name for numerator
            denominator_col: Column name for denominator
            output_col: Name for output percentage column
        
        Returns:
            DataFrame with new percentage column
        """
        df = df.copy()
        df[output_col] = (df[numerator_col] / df[denominator_col] * 100).round(2)
        return df
    
    def save_results(
        self,
        df: pd.DataFrame,
        output_path: Union[str, Path],
        print_summary: bool = True
    ):
        """
        Save results to CSV and optionally print summary.
        
        Args:
            df: DataFrame to save
            output_path: Output file path
            print_summary: Whether to print summary statistics
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=False)
        print(f"\n✓ Saved: {output_path}")
        print(f"  {len(df)} records")
        
        if print_summary:
            print("\n  Sample data:")
            print(df.head(3).to_string(index=False))
