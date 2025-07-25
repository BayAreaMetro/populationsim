#!/usr/bin/env python3
"""
CPI conversion utilities for PopulationSim Bay Area
Converts between different dollar years using Consumer Price Index inflation factors
"""

import pandas as pd
import numpy as np

# CPI-U inflation factors based on Bureau of Labor Statistics data
# Source: https://www.bls.gov/cpi/
# These represent relative price levels (2023 = 1.00 baseline)
CPI_FACTORS = {
    # Relative price levels (2023 = 1.00 baseline)
    2000: 0.483,  # 2000$ purchasing power relative to 2023$ (deflation factor ~0.483)
    2010: 0.725,  # 2010$ purchasing power relative to 2023$ (deflation factor ~0.725)
    2015: 0.833,  # 2015$ purchasing power relative to 2023$ (approximate)
    2020: 0.909,  # 2020$ purchasing power relative to 2023$ (approximate)
    2023: 1.000,  # 2023$ purchasing power (baseline)
}

def convert_income_cpi(income_series, from_year, to_year):
    """
    Convert income from one dollar year to another using CPI-U inflation factors.
    
    Parameters:
    -----------
    income_series : pd.Series or np.array
        Income values to convert
    from_year : int
        Source dollar year (e.g., 2023)
    to_year : int
        Target dollar year (e.g., 2010)
        
    Returns:
    --------
    pd.Series or np.array
        Income values converted to target dollar year
        
    Example:
    --------
    # Convert 2023 dollars to 2010 purchasing power
    income_2010 = convert_income_cpi(income_2023, from_year=2023, to_year=2010)
    
    # Convert 2010 dollars to 2023 dollars
    income_2023 = convert_income_cpi(income_2010, from_year=2010, to_year=2023)
    """
    
    if from_year not in CPI_FACTORS:
        raise ValueError(f"From year {from_year} not supported. Available years: {list(CPI_FACTORS.keys())}")
    
    if to_year not in CPI_FACTORS:
        raise ValueError(f"To year {to_year} not supported. Available years: {list(CPI_FACTORS.keys())}")
    
    if from_year == to_year:
        return income_series
    
    # Convert from source year to 2023, then from 2023 to target year
    # Formula: income_target = income_source * (factor_target / factor_source)
    # Where factors represent purchasing power relative to 2023
    conversion_factor = CPI_FACTORS[to_year] / CPI_FACTORS[from_year]
    
    return income_series * conversion_factor

def convert_2023_to_2010_dollars(income_2023):
    """
    Convert 2023 dollars to 2010 purchasing power equivalents.
    
    This is specifically for PUMS seed population where we receive income in 2023$
    but need to convert to 2010$ for consistency with control file breakpoints.
    
    Parameters:
    -----------
    income_2023 : pd.Series or np.array
        Income values in 2023 dollars
        
    Returns:
    --------
    pd.Series or np.array
        Income values in 2010 purchasing power
        
    Example:
    --------
    # PUMS gives us adjusted income in 2023$
    pums_hu_df['hh_income_2023'] = (pums_hu_df.ADJINC / 1000000) * pums_hu_df.HINCP
    
    # Convert to 2010 purchasing power for PopulationSim
    pums_hu_df['hh_income_2010'] = convert_2023_to_2010_dollars(pums_hu_df['hh_income_2023'])
    """
    return convert_income_cpi(income_2023, from_year=2023, to_year=2010)

def convert_2010_to_2023_dollars(income_2010):
    """
    Convert 2010 dollars to 2023 dollar equivalents.
    
    Parameters:
    -----------
    income_2010 : pd.Series or np.array
        Income values in 2010 dollars
        
    Returns:
    --------
    pd.Series or np.array
        Income values in 2023 dollars
    """
    return convert_income_cpi(income_2010, from_year=2010, to_year=2023)

def get_deflation_factor(from_year, to_year):
    """
    Get the deflation/inflation factor between two years.
    
    Parameters:
    -----------
    from_year : int
        Source dollar year
    to_year : int
        Target dollar year
        
    Returns:
    --------
    float
        Conversion factor (multiply source income by this to get target income)
        
    Example:
    --------
    # Get factor to convert 2023$ to 2010$
    factor = get_deflation_factor(2023, 2010)
    print(f"2023$ to 2010$ factor: {factor:.3f}")  # Should be ~0.725
    """
    return CPI_FACTORS[to_year] / CPI_FACTORS[from_year]

# Commonly used factors as constants
FACTOR_2023_TO_2010 = get_deflation_factor(2023, 2010)  # ~0.725
FACTOR_2010_TO_2023 = get_deflation_factor(2010, 2023)  # ~1.38
FACTOR_2023_TO_2000 = get_deflation_factor(2023, 2000)  # ~0.483 (for legacy compatibility)

if __name__ == "__main__":
    # Test the conversion functions
    print("CPI Conversion Utility Test")
    print("=" * 40)
    
    # Test sample incomes
    test_incomes = pd.Series([30000, 60000, 100000, 150000])
    print(f"Original 2023$: {test_incomes.tolist()}")
    
    # Convert to 2010$
    income_2010 = convert_2023_to_2010_dollars(test_incomes)
    print(f"Converted 2010$: {income_2010.round().astype(int).tolist()}")
    
    # Round trip test
    income_2023_back = convert_2010_to_2023_dollars(income_2010)
    print(f"Round trip 2023$: {income_2023_back.round().astype(int).tolist()}")
    
    print(f"\nConversion factors:")
    print(f"2023$ to 2010$: {FACTOR_2023_TO_2010:.3f}")
    print(f"2010$ to 2023$: {FACTOR_2010_TO_2023:.3f}")
    print(f"2023$ to 2000$: {FACTOR_2023_TO_2000:.3f}")
    
    # Show income breakpoint conversions
    print(f"\nIncome breakpoint conversions:")
    breakpoints_2023 = [41399, 82799, 137999]
    breakpoints_2010 = [round(x * FACTOR_2023_TO_2010) for x in breakpoints_2023]
    print(f"2023$ breakpoints: {breakpoints_2023}")
    print(f"2010$ breakpoints: {breakpoints_2010}")
