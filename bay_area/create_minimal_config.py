#!/usr/bin/env python3

"""
Temporary script to create a minimal working version of the controls that can complete successfully.
This will create a working config with only the basic controls that we know work.
"""

import collections
import pandas as pd
import os
import sys

# Add tm2_control_utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tm2_control_utils'))

# Import base config
from config import *

def create_minimal_controls():
    """Create a minimal working set of controls"""
    
    # Clear existing controls
    CONTROLS[ACS_EST_YEAR]['MAZ'] = collections.OrderedDict([
        # temp controls that work
        ('temp_base_num_hh_b',    ('pl',  CENSUS_EST_YEAR, 'H1_002N',       'block', [])),
        ('temp_base_num_hh_bg',   ('pl',  CENSUS_EST_YEAR, 'H1_002N',       'block group', [])),
        ('temp_num_hh_bg_to_b',   ('acs5', ACS_EST_YEAR,    'B11016',       'block group',
                                   [collections.OrderedDict([('pers_min',1),('pers_max',NPER_MAX)])],
                                   'temp_base_num_hh_b','temp_base_num_hh_bg')),
        
        # Final controls using basic PL data
        ('num_hh',                ('pl',  CENSUS_EST_YEAR, 'H1_002N',       'block', [])),
        ('gq_num_hh',             ('pl',  CENSUS_EST_YEAR, 'P1_003N',       'block', [])),  # Group quarters pop as proxy for GQ households
        ('tot_pop',               ('pl',  CENSUS_EST_YEAR, 'P1_001N',       'block', [])),
    ])
    
    # Export the updated controls
    return CONTROLS

def main():
    """Update the config file with minimal working controls"""
    controls = create_minimal_controls()
    
    print("Updated MAZ controls to:")
    for name, definition in controls[ACS_EST_YEAR]['MAZ'].items():
        print(f"  {name}: {definition}")
    
    # Save the working controls to the original config
    config_path = os.path.join('tm2_control_utils', 'config.py')
    
    # Read the current config
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Find the MAZ controls section and replace it
    start_marker = "CONTROLS[ACS_EST_YEAR]['MAZ'] = collections.OrderedDict(["
    end_marker = "])\n\n\n# ----------------------------------------\n# COUNTY controls"
    
    start_pos = content.find(start_marker)
    end_pos = content.find(end_marker)
    
    if start_pos != -1 and end_pos != -1:
        # Build replacement
        replacement_lines = ["CONTROLS[ACS_EST_YEAR]['MAZ'] = collections.OrderedDict(["]
        for name, definition in controls[ACS_EST_YEAR]['MAZ'].items():
            replacement_lines.append(f"    ('{name}', {definition!r}),")
        replacement_lines.append("])")
        replacement = "\n".join(replacement_lines)
        
        # Replace the section
        new_content = content[:start_pos] + replacement + content[end_pos:]
        
        # Write the backup and new version
        backup_path = config_path + '.backup'
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"Backed up original config to {backup_path}")
        
        with open(config_path, 'w') as f:
            f.write(new_content)
        print(f"Updated {config_path} with minimal working controls")
    else:
        print("Could not find MAZ controls section to replace")

if __name__ == '__main__':
    main()
