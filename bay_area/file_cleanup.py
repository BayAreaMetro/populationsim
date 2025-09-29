#!/usr/bin/env python3
"""
File Cleanup Script for PopulationSim Analysis

This script organizes and cleans up the analysis files created during the 
household size distribution investigation and pipeline debugging session.

Options:
1. Move analysis files to an 'analysis_archive' folder
2. Delete temporary analysis files
3. Keep only essential fixed files

Author: PopulationSim Cleanup
Date: 2024
"""

import os
import shutil
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def identify_analysis_files():
    """Identify all files created during the analysis session."""
    
    analysis_files = {
        "Analysis Scripts": [
            "household_size_comparison_2015_vs_2023.py",
            "diagnose_household_size_issue.py", 
            "fix_household_size_controls.py",
            "comprehensive_population_comparison.py",
            "households_children_analysis.py"
        ],
        
        "Pipeline Fix Scripts": [
            "fix_household_size_pipeline.py",
            "analyze_pipeline_impact.py"
        ],
        
        "Generated Images": [
            "synthetic_population_comparison_2015_vs_2023.png",
            "households_with_children_comparison.png", 
            "household_size_comparison_2015_vs_2023.png"
        ],
        
        "Cleanup Scripts": [
            "file_cleanup.py"  # This script itself
        ]
    }
    
    return analysis_files

def check_file_existence(analysis_files):
    """Check which analysis files actually exist."""
    
    existing_files = {}
    total_size = 0
    
    logger.info("Checking for analysis files...")
    
    for category, files in analysis_files.items():
        existing_files[category] = []
        
        for file_name in files:
            file_path = Path(file_name)
            if file_path.exists():
                file_size = file_path.stat().st_size
                total_size += file_size
                existing_files[category].append({
                    'name': file_name,
                    'size': file_size,
                    'size_mb': file_size / (1024 * 1024)
                })
                
        if existing_files[category]:
            logger.info(f"Found {len(existing_files[category])} files in {category}")
    
    logger.info(f"Total size of analysis files: {total_size / (1024 * 1024):.2f} MB")
    return existing_files, total_size

def display_cleanup_options(existing_files):
    """Display cleanup options to the user."""
    
    print("\\n" + "="*70)
    print("POPULATIONSIM ANALYSIS FILE CLEANUP")
    print("="*70)
    
    # Show existing files
    for category, files in existing_files.items():
        if files:
            print(f"\\n{category}:")
            for file_info in files:
                print(f"  • {file_info['name']} ({file_info['size_mb']:.2f} MB)")
    
    print("\\n" + "="*70)
    print("CLEANUP OPTIONS")
    print("="*70)
    
    options = {
        "1": {
            "title": "Archive Analysis Files",
            "description": "Move all analysis files to 'analysis_archive/' folder",
            "action": "preserve_in_archive"
        },
        "2": {
            "title": "Delete Analysis Scripts Only", 
            "description": "Delete .py analysis scripts, keep images and core files",
            "action": "delete_scripts_only"
        },
        "3": {
            "title": "Delete All Analysis Files",
            "description": "Delete all analysis files (CANNOT BE UNDONE)",
            "action": "delete_all"
        },
        "4": {
            "title": "Keep Everything",
            "description": "No cleanup - keep all files as they are",
            "action": "keep_all"
        }
    }
    
    for key, option in options.items():
        print(f"\\n{key}. {option['title']}")
        print(f"   {option['description']}")
    
    return options

def archive_analysis_files(existing_files):
    """Move analysis files to archive folder."""
    
    archive_dir = Path("analysis_archive")
    archive_dir.mkdir(exist_ok=True)
    
    logger.info(f"Creating archive directory: {archive_dir}")
    
    moved_count = 0
    
    for category, files in existing_files.items():
        if category != "Cleanup Scripts":  # Don't archive the cleanup script itself
            for file_info in files:
                source_path = Path(file_info['name'])
                dest_path = archive_dir / file_info['name']
                
                if source_path.exists():
                    shutil.move(str(source_path), str(dest_path))
                    logger.info(f"Moved: {source_path} → {dest_path}")
                    moved_count += 1
    
    print(f"\\n✅ Archived {moved_count} files to {archive_dir}/")
    print(f"📁 You can restore files from the archive if needed")

def delete_scripts_only(existing_files):
    """Delete only Python analysis scripts, keep images."""
    
    deleted_count = 0
    kept_count = 0
    
    for category, files in existing_files.items():
        for file_info in files:
            file_path = Path(file_info['name'])
            
            # Delete .py files but keep images and cleanup script
            if (file_path.suffix == '.py' and 
                category != "Cleanup Scripts" and
                file_path.exists()):
                
                file_path.unlink()
                logger.info(f"Deleted: {file_path}")
                deleted_count += 1
            else:
                logger.info(f"Kept: {file_path}")
                kept_count += 1
    
    print(f"\\n🗑️ Deleted {deleted_count} Python analysis scripts")
    print(f"📄 Kept {kept_count} files (images and core files)")

def delete_all_analysis_files(existing_files):
    """Delete all analysis files."""
    
    deleted_count = 0
    
    for category, files in existing_files.items():
        if category != "Cleanup Scripts":  # Don't delete the cleanup script itself
            for file_info in files:
                file_path = Path(file_info['name'])
                
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted: {file_path}")
                    deleted_count += 1
    
    print(f"\\n🗑️ Deleted {deleted_count} analysis files")
    print("⚠️  This action cannot be undone")

def main():
    """Main cleanup function."""
    
    logger.info("Starting PopulationSim analysis file cleanup...")
    
    # Identify analysis files
    analysis_files = identify_analysis_files()
    
    # Check which files exist
    existing_files, total_size = check_file_existence(analysis_files)
    
    # Display options
    options = display_cleanup_options(existing_files)
    
    # Get user choice
    print("\\n" + "="*70)
    choice = input("Enter your choice (1-4): ").strip()
    
    if choice in options:
        action = options[choice]["action"]
        
        print(f"\\nExecuting: {options[choice]['title']}")
        print(f"Description: {options[choice]['description']}")
        
        # Confirm destructive actions
        if action in ["delete_scripts_only", "delete_all"]:
            confirm = input("\\n⚠️  This will permanently delete files. Continue? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("❌ Cleanup cancelled")
                return
        
        # Execute chosen action
        if action == "preserve_in_archive":
            archive_analysis_files(existing_files)
        elif action == "delete_scripts_only":
            delete_scripts_only(existing_files)
        elif action == "delete_all":
            delete_all_analysis_files(existing_files)
        elif action == "keep_all":
            print("\\n📁 No files modified - keeping everything as is")
        
        print("\\n✅ Cleanup completed!")
        
    else:
        print("❌ Invalid choice - no cleanup performed")

if __name__ == "__main__":
    main()