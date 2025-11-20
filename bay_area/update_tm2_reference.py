"""
Update TM2_FULL_REFERENCE.md with latest data from new model run.

This script:
1. Reads the existing TM2_FULL_REFERENCE.md
2. Identifies sections with embedded data tables
3. Loads fresh data from output_2023/ directories
4. Replaces old data with new data while preserving structure
5. Saves updated markdown
"""

import pandas as pd
import re
from pathlib import Path
from datetime import datetime

# Base paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output_2023"
DOCS_DIR = BASE_DIR / "docs"
MD_FILE = DOCS_DIR / "TM2_FULL_REFERENCE.md"

def load_csv_snippet(csv_path, n_rows=10, description=""):
    """Load CSV and format as markdown table snippet."""
    try:
        df = pd.read_csv(csv_path)
        
        # Format as markdown table
        lines = [f"\n{description}\n" if description else ""]
        lines.append("```")
        lines.append(df.head(n_rows).to_string(index=False))
        lines.append("```\n")
        
        return "\n".join(lines)
    except Exception as e:
        print(f"Warning: Could not load {csv_path}: {e}")
        return f"\n*Data file not found: {csv_path}*\n"

def extract_summary_stats(output_dir):
    """Extract key summary statistics from output files."""
    stats = {}
    
    # Try to load household and person totals
    try:
        # Check final summary files
        final_summary_files = list((output_dir / "populationsim_working_dir" / "output").glob("final_summary_*.csv"))
        
        if final_summary_files:
            # Load TAZ summary for totals
            taz_summary_path = output_dir / "populationsim_working_dir" / "output" / "final_summary_TAZ_NODE.csv"
            if taz_summary_path.exists():
                df = pd.read_csv(taz_summary_path)
                # Sum up totals from control columns
                if 'numhh_gq_control' in df.columns:
                    stats['total_households'] = int(df['numhh_gq_control'].sum())
                if 'total_persons_control' in df.columns:
                    stats['total_persons'] = int(df['total_persons_control'].sum())
        
        # Try county summary
        county_perf_path = output_dir / "charts" / "county_analysis" / "county_performance_summary.csv"
        if county_perf_path.exists():
            df = pd.read_csv(county_perf_path)
            stats['county_summary'] = df
            
    except Exception as e:
        print(f"Warning: Could not extract summary stats: {e}")
    
    return stats

def update_markdown_section(content, section_header, new_data):
    """Replace data in a specific section of the markdown."""
    # Find section header followed by ```csv code block
    # Pattern: section header, then ```csv, then data, then ```
    pattern = rf"(### {re.escape(section_header)}.*?\n+```csv\n)(.*?)(\n```)"
    
    matches = list(re.finditer(pattern, content, flags=re.DOTALL))
    if matches:
        # Replace the data between code blocks
        content = re.sub(pattern, rf"\1{new_data}\3", content, flags=re.DOTALL, count=1)
        return content, True
    return content, False

def main():
    print("=" * 80)
    print("TM2 FULL REFERENCE UPDATER")
    print("=" * 80)
    print(f"Reading: {MD_FILE}")
    
    # Read current markdown
    with open(MD_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Original file size: {len(content)} characters")
    
    # Extract fresh statistics
    print("\nExtracting fresh statistics from output_2023...")
    stats = extract_summary_stats(OUTPUT_DIR)
    
    # Update key CSV sections
    print("\nUpdating CSV data sections...")
    
    csv_updates = {
        "County performance summary — `output_2023/charts/county_analysis/county_performance_summary.csv`": 
            OUTPUT_DIR / "charts" / "county_analysis" / "county_performance_summary.csv",
        "County detailed results (San Francisco sample rows) — `output_2023/charts/county_analysis/county_detailed_results.csv`": 
            OUTPUT_DIR / "charts" / "county_analysis" / "county_detailed_results.csv",
        "Final TAZ-level summary (header + first row) — `output_2023/populationsim_working_dir/output/final_summary_TAZ_NODE.csv`":
            OUTPUT_DIR / "populationsim_working_dir" / "output" / "final_summary_TAZ_NODE.csv",
        "TAZ analysis summary (header + sample rows)":
            OUTPUT_DIR / "charts" / "taz_analysis" / "taz_analysis_summary.csv",
    }
    
    updated_sections = 0
    for section_title, csv_path in csv_updates.items():
        if csv_path.exists():
            print(f"  - Loading {csv_path.name}...")
            try:
                df = pd.read_csv(csv_path)
                # Format as CSV for the code block (first 10 rows)
                csv_text = df.head(10).to_csv(index=False)
                
                # Update the section
                content, success = update_markdown_section(content, section_title, csv_text)
                
                if success:
                    updated_sections += 1
                    print(f"    ✓ Updated section: {section_title}")
                else:
                    print(f"    ⚠ Section not found: {section_title}")
            except Exception as e:
                print(f"    ✗ Error updating {section_title}: {e}")
        else:
            print(f"  - Skipping {section_title} (file not found: {csv_path})")
    
    # Update county summary sections (final_summary_COUNTY_*.csv)
    print("\nUpdating county detail sections...")
    county_dir = OUTPUT_DIR / "populationsim_working_dir" / "output"
    county_names = ["San Francisco", "San Mateo", "Santa Clara", "Alameda", 
                    "Contra Costa", "Solano", "Napa", "Sonoma", "Marin"]
    
    for county_num in range(1, 10):
        county_file = county_dir / f"final_summary_COUNTY_{county_num}.csv"
        if county_file.exists():
            try:
                df = pd.read_csv(county_file)
                csv_text = df.head(10).to_csv(index=False)
                
                # Find section for this county with proper header format
                county_name = county_names[county_num - 1] if county_num <= len(county_names) else f"County {county_num}"
                pattern = rf"(#### final_summary_COUNTY_{county_num}\.csv \({county_name}\).*?\n+```csv\n)(.*?)(\n```)"
                
                if re.search(pattern, content, re.DOTALL):
                    content = re.sub(pattern, rf"\1{csv_text}\3", content, flags=re.DOTALL)
                    updated_sections += 1
                    print(f"  ✓ Updated COUNTY_{county_num} ({county_name})")
                else:
                    print(f"  ⚠ Pattern not found for COUNTY_{county_num}")
            except Exception as e:
                print(f"  ✗ Error updating COUNTY_{county_num}: {e}")
    
    # Add update timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_note = f"\n\n*Document updated: {timestamp} with data from model run dated 2025-11-10*\n"
    
    # Add timestamp at the beginning after title
    content = content.replace("Executive summary\n\n", f"Executive summary\n\n{timestamp_note}\n")
    
    # Save updated markdown
    backup_file = MD_FILE.with_suffix('.md.backup')
    print(f"\nCreating backup: {backup_file}")
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Saving updated markdown: {MD_FILE}")
    with open(MD_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✓ Updated {updated_sections} data sections")
    print(f"✓ New file size: {len(content)} characters")
    print("\nNext step: Convert to Word using pandoc:")
    print(f'  pandoc "{MD_FILE}" -o "{DOCS_DIR / "TM2_FULL_REFERENCE.docx"}"')
    print("=" * 80)

if __name__ == "__main__":
    main()
