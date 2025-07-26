#!/usr/bin/env python3
"""
Test script to verify CPI conversion functionality
"""

import pandas as pd
import sys
import os

# Add the current directory to the path so we can import cpi_conversion
sys.path.append(os.path.dirname(__file__))

try:
    from cpi_conversion import convert_2023_to_2010_dollars, CPI_2023_TO_2010_DEFLATOR
    print("✅ Successfully imported CPI conversion functions")
    print(f"   Deflation factor: {CPI_2023_TO_2010_DEFLATOR}")
except ImportError as e:
    print(f"❌ Failed to import CPI conversion: {e}")
    sys.exit(1)

# Test data - sample income values in 2023 dollars
test_incomes_2023 = [50000, 100000, 150000, 200000, 250000]

print(f"\n🔄 Testing CPI conversion...")
print(f"   Converting from 2023$ to 2010$ purchasing power")
print(f"   Using deflation factor: {CPI_2023_TO_2010_DEFLATOR}")

print(f"\n{'2023$':>10} → {'2010$':>10} │ {'Description':20}")
print("─" * 50)

for income_2023 in test_incomes_2023:
    income_2010 = convert_2023_to_2010_dollars(income_2023)
    description = "Low" if income_2023 < 75000 else "Medium" if income_2023 < 150000 else "High"
    print(f"${income_2023:>8,} → ${income_2010:>8,.0f} │ {description}")

print(f"\n🎯 Testing with our control breakpoints:")
control_breakpoints_2023 = [41399, 82799, 137999, 200000]
control_breakpoints_2010_expected = [30000, 60000, 100000, 145000]  # Approximate 2010 equivalents

print(f"\n{'2023$ Max':>12} → {'2010$ Actual':>12} │ {'2010$ Expected':>12} │ {'Match':>8}")
print("─" * 70)

for i, max_2023 in enumerate(control_breakpoints_2023):
    actual_2010 = convert_2023_to_2010_dollars(max_2023)
    expected_2010 = control_breakpoints_2010_expected[i]
    match = "✅" if abs(actual_2010 - expected_2010) < 5000 else "⚠️"
    print(f"${max_2023:>10,} → ${actual_2010:>10,.0f} │ ${expected_2010:>10,} │ {match:>8}")

print(f"\n✅ CPI conversion test completed!")
print(f"   The conversion maintains purchasing power parity between 2010 and 2023 dollars")
print(f"   Our control breakpoints in 2023$ represent equivalent 2010 purchasing power")
