"""
Test switching between network and local file modes
"""

import os
import re

def toggle_file_mode(use_local=None):
    """Toggle between local and network file modes in config.py"""
    
    config_file = "tm2_control_utils/config.py"
    
    # Read current config
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find current setting
    current_match = re.search(r'USE_LOCAL_FILES = (True|False)', content)
    if not current_match:
        print("Could not find USE_LOCAL_FILES setting in config.py")
        return
    
    current_setting = current_match.group(1) == 'True'
    
    if use_local is None:
        # Toggle current setting
        new_setting = not current_setting
    else:
        new_setting = use_local
    
    # Replace the setting
    new_content = re.sub(
        r'USE_LOCAL_FILES = (True|False)',
        f'USE_LOCAL_FILES = {new_setting}',
        content
    )
    
    # Write back to file
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Changed USE_LOCAL_FILES from {current_setting} to {new_setting}")
    return new_setting

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ['local', 'true', '1']:
            toggle_file_mode(True)
        elif sys.argv[1].lower() in ['network', 'false', '0']:
            toggle_file_mode(False)
        else:
            print("Usage: python toggle_files.py [local|network]")
    else:
        # Just toggle
        toggle_file_mode()
