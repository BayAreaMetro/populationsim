#!/usr/bin/env python3
"""
PUMS Data Downloader for PopulationSim

Handles downloading and extracting PUMS data from Census Bureau
"""

import pandas as pd
import os
import zipfile
import requests
from urllib3.exceptions import InsecureRequestWarning
import warnings
from pathlib import Path
from typing import List, Optional, Tuple
import logging

warnings.filterwarnings('ignore', category=InsecureRequestWarning)

logger = logging.getLogger(__name__)

class PUMSDownloader:
    """Downloads PUMS data for specified PUMAs"""
    
    def __init__(self, year: int = 2023, state: str = "06"):
        self.year = year
        self.state = state
        self.base_url = f"https://www2.census.gov/programs-surveys/acs/data/pums/{year}/1-Year/"
        
    def download_pums_data(self, pumas: List[str], output_dir: Path) -> Tuple[Path, Path]:
        """
        Download PUMS data for specified PUMAs
        
        Returns:
            Tuple of (household_file_path, person_file_path)
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Download files
        hh_file = self._download_household_file(output_dir)
        person_file = self._download_person_file(output_dir)
        
        # Filter to Bay Area PUMAs
        hh_filtered = self._filter_to_pumas(hh_file, pumas, "household")
        person_filtered = self._filter_to_pumas(person_file, pumas, "person")
        
        return hh_filtered, person_filtered
    
    def _download_household_file(self, output_dir: Path) -> Path:
        """Download household PUMS file"""
        filename = f"psam_h{self.state}.csv"
        url = f"{self.base_url}{filename}"
        output_path = output_dir / f"households_{self.year}_raw.csv"
        
        if output_path.exists():
            logger.info(f"Household file already exists: {output_path}")
            return output_path
        
        logger.info(f"Downloading household data from {url}...")
        self._download_file(url, output_path)
        return output_path
    
    def _download_person_file(self, output_dir: Path) -> Path:
        """Download person PUMS file"""
        filename = f"psam_p{self.state}.csv"
        url = f"{self.base_url}{filename}"
        output_path = output_dir / f"persons_{self.year}_raw.csv"
        
        if output_path.exists():
            logger.info(f"Person file already exists: {output_path}")
            return output_path
            
        logger.info(f"Downloading person data from {url}...")
        self._download_file(url, output_path)
        return output_path
    
    def _download_file(self, url: str, output_path: Path) -> None:
        """Download file with progress tracking"""
        try:
            response = requests.get(url, stream=True, verify=False)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            raise
    
    def _filter_to_pumas(self, file_path: Path, pumas: List[str], data_type: str) -> Path:
        """Filter data to specified PUMAs"""
        logger.info(f"Filtering {data_type} data to {len(pumas)} Bay Area PUMAs...")
        
        # Read in chunks to handle large files
        chunks = []
        chunk_size = 50000
        
        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            # Filter to Bay Area PUMAs
            puma_str = chunk['PUMA'].astype(str).str.zfill(5)
            bay_area_mask = puma_str.isin(pumas)
            filtered_chunk = chunk[bay_area_mask].copy()
            
            if len(filtered_chunk) > 0:
                chunks.append(filtered_chunk)
        
        if not chunks:
            raise ValueError(f"No {data_type} records found for specified PUMAs")
        
        # Combine chunks
        df = pd.concat(chunks, ignore_index=True)
        
        # Create unique identifiers
        if data_type == "household":
            df['unique_hh_id'] = df['SERIALNO'].astype(str) + '_' + df['PUMA'].astype(str)
        elif data_type == "person":
            df['unique_hh_id'] = df['SERIALNO'].astype(str) + '_' + df['PUMA'].astype(str)
            df['unique_person_id'] = df['unique_hh_id'] + '_' + df['SPORDER'].astype(str)
        
        logger.info(f"Filtered {data_type} data: {len(df):,} records")
        return df
