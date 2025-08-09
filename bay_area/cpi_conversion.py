#!/usr/bin/env python3
"""
CPI Conversion Module for PopulationSim TM2
Converts income values between different base years using Consumer Price Index
"""

def convert_2023_to_2010_dollars(income_2023):
    """
    Convert 2023 dollar amounts to 2010 dollars using CPI
    
    Parameters:
    -----------
    income_2023 : float or array-like
        Income values in 2023 dollars
        
    Returns:
    --------
    float or array-like
        Income values converted to 2010 dollars
    """
    # CPI conversion factor from 2023 to 2010
    # Based on Bureau of Labor Statistics Consumer Price Index
    # CPI-U 2010 annual average: 218.056
    # CPI-U 2023 estimated: ~310 (approximate)
    cpi_2010 = 218.056
    cpi_2023 = 310.0  # Approximate 2023 CPI
    
    conversion_factor = cpi_2010 / cpi_2023
    
    try:
        # Handle pandas Series/DataFrame
        import pandas as pd
        if isinstance(income_2023, (pd.Series, pd.DataFrame)):
            return income_2023 * conversion_factor
    except ImportError:
        pass
    
    try:
        # Handle numpy arrays
        import numpy as np
        if isinstance(income_2023, np.ndarray):
            return income_2023 * conversion_factor
    except ImportError:
        pass
    
    # Handle scalar values or lists
    if hasattr(income_2023, '__iter__') and not isinstance(income_2023, str):
        return [x * conversion_factor if x is not None else None for x in income_2023]
    else:
        return income_2023 * conversion_factor if income_2023 is not None else None


def convert_2010_to_2023_dollars(income_2010):
    """
    Convert 2010 dollar amounts to 2023 dollars using CPI
    
    Parameters:
    -----------
    income_2010 : float or array-like
        Income values in 2010 dollars
        
    Returns:
    --------
    float or array-like
        Income values converted to 2023 dollars
    """
    # CPI conversion factor from 2010 to 2023
    cpi_2010 = 218.056
    cpi_2023 = 310.0  # Approximate 2023 CPI
    
    conversion_factor = cpi_2023 / cpi_2010
    
    try:
        # Handle pandas Series/DataFrame
        import pandas as pd
        if isinstance(income_2010, (pd.Series, pd.DataFrame)):
            return income_2010 * conversion_factor
    except ImportError:
        pass
    
    try:
        # Handle numpy arrays
        import numpy as np
        if isinstance(income_2010, np.ndarray):
            return income_2010 * conversion_factor
    except ImportError:
        pass
    
    # Handle scalar values or lists
    if hasattr(income_2010, '__iter__') and not isinstance(income_2010, str):
        return [x * conversion_factor if x is not None else None for x in income_2010]
    else:
        return income_2010 * conversion_factor if income_2010 is not None else None


if __name__ == "__main__":
    # Test the conversion functions
    test_income_2023 = 100000
    test_income_2010 = convert_2023_to_2010_dollars(test_income_2023)
    print(f"$100,000 in 2023 dollars = ${test_income_2010:,.0f} in 2010 dollars")
    
    # Test reverse conversion
    converted_back = convert_2010_to_2023_dollars(test_income_2010)
    print(f"${test_income_2010:,.0f} in 2010 dollars = ${converted_back:,.0f} in 2023 dollars")
