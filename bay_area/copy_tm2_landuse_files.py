
import os
import shutil
from pathlib import Path

# User-editable: source and destination directories
SOURCE_DIR = Path('output_2023')  # or wherever the files are generated
DEST_DIR = Path(r'C:\Box\Modeling and Surveys\Development\Travel Model Two Conversion\Model Inputs\2023-tm22-dev-test\landuse')

# Files to copy
FILES_TO_COPY = [
    'maz_data.csv',
    'maz_data_withDensity.csv',
]

def copy_files(source_dir, dest_dir, files):
    dest_dir.mkdir(parents=True, exist_ok=True)
    for fname in files:
        src = source_dir / fname
        dst = dest_dir / fname
        if src.exists():
            shutil.copy2(src, dst)
            print(f'Copied {src} -> {dst}')
        else:
            print(f'WARNING: Source file not found: {src}')

# PopSyn files (postprocessed)
POPSYN_SOURCE_DIR = Path('output_2023') / 'populationsim_working_dir' / 'output'
POPSYN_DEST_DIR = Path(r'C:\Box\Modeling and Surveys\Development\Travel Model Two Conversion\Model Inputs\2023-tm22-dev-test\popsyn')
POPSYN_FILES = [
    ('households_2023_tm2.csv', 'households.csv'),
    ('persons_2023_tm2.csv', 'persons.csv'),
]

def copy_and_rename_files(source_dir, dest_dir, file_pairs):
    dest_dir.mkdir(parents=True, exist_ok=True)
    for src_name, dst_name in file_pairs:
        src = source_dir / src_name
        dst = dest_dir / dst_name
        if src.exists():
            shutil.copy2(src, dst)
            print(f'Copied {src} -> {dst}')
        else:
            print(f'WARNING: Source file not found: {src}')

if __name__ == '__main__':
    print(f'Copying land use files to {DEST_DIR}')
    copy_files(SOURCE_DIR, DEST_DIR, FILES_TO_COPY)
    print(f'Copying PopSyn files to {POPSYN_DEST_DIR}')
    copy_and_rename_files(POPSYN_SOURCE_DIR, POPSYN_DEST_DIR, POPSYN_FILES)
    # Write README files
    landuse_readme = (
        'This directory contains land use files (maz_data.csv, maz_data_withDensity.csv) copied from the PopulationSim pipeline output.\n'
        'Source: output_2023 directory in the Bay Area PopulationSim repo.\n'
        'Copied and managed by: copy_tm2_landuse_files.py\n'
        'Date: August 26, 2025\n'
    )
    with open(DEST_DIR / "readme_file_source.txt", "w", encoding="utf-8") as f:
        f.write(landuse_readme)

    popsyn_readme = (
        'This directory contains postprocessed synthetic population files (households.csv, persons.csv) copied from the PopulationSim pipeline output.\n'
        'Source: output_2023 directory in the Bay Area PopulationSim repo, files were renamed from households_postprocessed.csv and persons_postprocessed.csv.\n'
        'Copied and managed by: copy_tm2_landuse_files.py\n'
        'Date: August 26, 2025\n'
    )
    with open(POPSYN_DEST_DIR / "readme_file_source.txt", "w", encoding="utf-8") as f:
        f.write(popsyn_readme)

    print('Done.')
