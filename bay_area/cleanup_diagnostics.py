#!/usr/bin/env python3
"""
Cleanup script to remove diagnostic and test files created during GQ debugging
Run this before checking in to GitHub to clean up the workspace
"""

import os
import shutil
from pathlib import Path

def cleanup_files():
    """Remove diagnostic and test files"""
    
    base_dir = Path(".")
    
    # Files to remove
    files_to_remove = [
        "debug_wgtp_gq.py",
        "test_filtering_logic.py", 
        "test_incidence_table.py",
        "debug_data_structure.py",
        "analyze_gq_pipeline.py",
        "check_controls_2_seed.py"
    ]
    
    # Directories to remove
    dirs_to_remove = [
        "gq_test",
        "__pycache__"
    ]
    
    print("🧹 CLEANING UP DIAGNOSTIC FILES")
    print("=" * 50)
    
    # Remove files
    for file_path in files_to_remove:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"🗑️  Removing file: {file_path}")
            full_path.unlink()
        else:
            print(f"⚠️  File not found: {file_path}")
    
    # Remove directories
    for dir_path in dirs_to_remove:
        full_path = base_dir / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"🗑️  Removing directory: {dir_path}")
            shutil.rmtree(full_path)
        else:
            print(f"⚠️  Directory not found: {dir_path}")
    
    print("\n✅ CLEANUP COMPLETE!")
    print("Workspace is now clean for GitHub commit.")

if __name__ == "__main__":
    cleanup_files()
