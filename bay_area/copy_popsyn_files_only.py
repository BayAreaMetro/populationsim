#!/usr/bin/env python3
"""
Copy only the PopSyn household and persons files to Box for model testing
Based on copy_tm2_landuse_files.py but skips the maz files
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# PopSyn files (postprocessed) - source and destination
POPSYN_SOURCE_DIR = Path('output_2023') / 'populationsim_working_dir' / 'output'
POPSYN_DEST_DIR = Path(r'C:\Box\Modeling and Surveys\Development\Travel Model Two Conversion\Model Inputs\2023-tm22-dev-test\popsyn')

# Files to copy and rename
POPSYN_FILES = [
    ('households_2023_tm2.csv', 'households.csv'),
    ('persons_2023_tm2.csv', 'persons.csv'),
]

def copy_and_rename_files(source_dir, dest_dir, file_pairs):
    """Copy files from source to destination with renaming"""
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    for src_name, dst_name in file_pairs:
        src = source_dir / src_name
        dst = dest_dir / dst_name
        
        if src.exists():
            shutil.copy2(src, dst)
            print(f'✅ Copied {src} -> {dst}')
            
            # Show file info
            size_mb = src.stat().st_size / (1024 * 1024)
            print(f'   File size: {size_mb:.1f} MB')
        else:
            print(f'❌ WARNING: Source file not found: {src}')

if __name__ == '__main__':
    print("COPYING POPSYN FILES FOR MODEL TESTING")
    print("="*50)
    print(f'Source: {POPSYN_SOURCE_DIR}')
    print(f'Destination: {POPSYN_DEST_DIR}')
    print()
    
    # Copy PopSyn files
    copy_and_rename_files(POPSYN_SOURCE_DIR, POPSYN_DEST_DIR, POPSYN_FILES)
    
    # Write README file
    current_date = datetime.now().strftime("%B %d, %Y")
    popsyn_readme = f"""PopSyn Files for TM2 Model Testing
Generated: {current_date}

This directory contains postprocessed synthetic population files copied from the PopulationSim pipeline output.

Files:
- households.csv: Synthetic households (renamed from households_2023_tm2.csv)
- persons.csv: Synthetic persons (renamed from persons_2023_tm2.csv)

Source: output_2023/populationsim_working_dir/output/ in the Bay Area PopulationSim repo
Pipeline: TM2 PopulationSim with employment field fixes (WKW mapping, OCCP categories)

Key Fixes Applied:
- WKW mapping corrected (was backwards: 1=50-52 weeks, 6=1-13 weeks)
- OCCP comprehensive category mapping (1-5 categories, no gaps)
- Employment field consistency improvements

Copied by: copy_popsyn_files_only.py
"""
    
    readme_path = POPSYN_DEST_DIR / "readme_file_source.txt"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(popsyn_readme)
    
    print(f'📄 README created: {readme_path}')
    print()
    print('✅ PopSyn files ready for model testing!')
