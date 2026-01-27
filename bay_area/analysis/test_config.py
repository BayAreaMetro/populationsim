#!/usr/bin/env python3
"""
Test script to debug the VALUE_LABELS issue
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tm2_config import TM2Config

try:
    print("Creating config...")
    config = TM2Config(year=2023)
    
    print("Config created successfully")
    print(f"Has VALUE_LABELS attribute: {hasattr(config, 'VALUE_LABELS')}")
    
    if hasattr(config, 'VALUE_LABELS'):
        print(f"VALUE_LABELS type: {type(config.VALUE_LABELS)}")
        print(f"Number of variables with labels: {len(config.VALUE_LABELS)}")
        print(f"Variable names: {list(config.VALUE_LABELS.keys())}")
    else:
        print("VALUE_LABELS attribute not found!")
        print(f"Available attributes: {[attr for attr in dir(config) if not attr.startswith('_')]}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()



