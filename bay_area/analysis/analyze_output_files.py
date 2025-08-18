#!/usr/bin/env python3
"""
Analyze PopulationSim Output Files
Generates comprehensive summary of households and persons tables with human-readable descriptions
and distributional analysis comparing preprocessed vs postprocessed files.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from unified_tm2_config import UnifiedTM2Config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_column_descriptions():
    """Human-readable descriptions for all columns"""
    return {
        # Household columns (preprocessed)
        'unique_hh_id': 'Unique Household ID',
        'SERIALNO': 'Census Serial Number',
        'MAZ': 'Model Analysis Zone',
        'TAZ': 'Travel Analysis Zone', 
        'PUMA': 'Public Use Microdata Area',
        'COUNTY': 'MTC County Code',
        'HINCP': 'Household Income (dollars)',
        'NP': 'Number of Persons in Household',
        'TYPE': 'Housing Unit Type',
        'VEH': 'Number of Vehicles',
        'WIF': 'Workers in Family',
        'WKHP': 'Usual Hours Worked Per Week',
        'WKW': 'Weeks Worked During Past Year',
        'TYPEHUGQ': 'Type of Unit (Housing/Group Quarters)',
        'TEN': 'Tenure (Own/Rent)',
        'BLD': 'Units in Structure',
        'HHT': 'Household/Family Type',
        'hhgqtype': 'Household/Group Quarters Type (0=HH, 1=Univ, 2=Military, 3=Other)',
        'integer_weight': 'Integer Weight from PopulationSim',
        
        # Household columns (postprocessed TM2)
        'HHID': 'Household ID (TM2)',
        'MTCCountyID': 'MTC County ID',
        'HHINCADJ': 'Adjusted Household Income',
        'NWRKRS_ESR': 'Number of Workers (Employment Status)',
        'poverty_income_2023d': 'Poverty Income Threshold (2023 dollars)',
        'poverty_income_2000d': 'Poverty Income Threshold (2000 dollars)', 
        'pct_of_poverty': 'Percent of Poverty Level',
        'hinccat1': 'Income Category 1 (TM1 compatible)',
        
        # Person columns (preprocessed)
        'SPORDER': 'Person Number in Household',
        'AGEP': 'Age',
        'SEX': 'Sex (1=Male, 2=Female)',
        'HISP': 'Hispanic Origin',
        'ESR': 'Employment Status Recode',
        'SCHG': 'Grade Level Attending',
        'SCHL': 'Educational Attainment',
        'OCCP': 'Occupation Recode',
        'INDP': 'Industry Recode',
        'COW': 'Class of Worker',
        'MIL': 'Military Service',
        'PINCP': 'Person Income (dollars)',
        'POWPUMA': 'Place of Work PUMA',
        'PWGTP': 'Person Weight',
        'employ_status': 'Employment Status Category',
        'employed': 'Employed Flag (0/1)',
        'student_status': 'Student Status Category',
        'occupation': 'Occupation Category',
        'person_type': 'Person Type Category',
        
        # Person columns (postprocessed TM2)
        'PERID': 'Person ID (TM2)',
        'unique_per_id': 'Unique Person ID',
        'EMPLOYED': 'Employment Status (TM2)',
    }

def analyze_column_distribution(df, col_name, sample_size=100000):
    """Analyze distribution of a column with memory-efficient sampling"""
    if len(df) > sample_size:
        # Sample for large datasets
        sample_df = df.sample(n=sample_size, random_state=42)
        col_data = sample_df[col_name]
        note = f" (sampled {sample_size:,} rows)"
    else:
        col_data = df[col_name]
        note = ""
    
    result = {
        'dtype': str(col_data.dtype),
        'non_null_count': int(col_data.notna().sum()),
        'null_count': int(col_data.isna().sum()),
        'null_pct': float(col_data.isna().mean() * 100),
        'sample_note': note
    }
    
    if pd.api.types.is_numeric_dtype(col_data):
        result.update({
            'min': float(col_data.min()) if col_data.notna().any() else None,
            'max': float(col_data.max()) if col_data.notna().any() else None,
            'mean': float(col_data.mean()) if col_data.notna().any() else None,
            'median': float(col_data.median()) if col_data.notna().any() else None,
            'std': float(col_data.std()) if col_data.notna().any() else None,
            'unique_count': int(col_data.nunique())
        })
    else:
        # For categorical/text data
        result.update({
            'unique_count': int(col_data.nunique()),
            'most_common': col_data.value_counts().head(5).to_dict() if col_data.notna().any() else {}
        })
    
    return result

def compare_files_summary(config):
    """Generate comprehensive comparison summary"""
    
    logger.info("Starting file analysis...")
    
    # File paths
    preprocessed_hh = config.POPSIM_OUTPUT_DIR / "synthetic_households.csv"
    preprocessed_pp = config.POPSIM_OUTPUT_DIR / "synthetic_persons.csv"
    postprocessed_hh = config.POPSIM_OUTPUT_DIR / "households_2023_tm2.csv"
    postprocessed_pp = config.POPSIM_OUTPUT_DIR / "persons_2023_tm2.csv"
    
    column_descriptions = get_column_descriptions()
    
    # Check file existence
    for file_path in [preprocessed_hh, preprocessed_pp, postprocessed_hh, postprocessed_pp]:
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return
    
    summary = []
    summary.append("# PopulationSim TM2 Output File Analysis")
    summary.append(f"Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary.append("")
    
    # === HOUSEHOLDS ANALYSIS ===
    logger.info("Analyzing households files...")
    summary.append("## Households Analysis")
    summary.append("")
    
    # Load household file info (just headers and basic stats first)
    hh_pre_info = pd.read_csv(preprocessed_hh, nrows=1)
    hh_post_info = pd.read_csv(postprocessed_hh, nrows=1)
    
    # Get full row counts
    hh_pre_count = sum(1 for _ in open(preprocessed_hh)) - 1  # subtract header
    hh_post_count = sum(1 for _ in open(postprocessed_hh)) - 1
    
    summary.append(f"**File Comparison:**")
    summary.append(f"- Preprocessed: `synthetic_households.csv` - {hh_pre_count:,} households")
    summary.append(f"- Postprocessed: `households_2023_tm2.csv` - {hh_post_count:,} households")
    summary.append(f"- Row count change: {hh_post_count - hh_pre_count:+,} households")
    summary.append("")
    
    summary.append("**Column Mapping:**")
    hh_pre_cols = list(hh_pre_info.columns)
    hh_post_cols = list(hh_post_info.columns)
    
    summary.append("| Preprocessed Column | Postprocessed Column | Description |")
    summary.append("|---------------------|---------------------|-------------|")
    
    # Map columns between files
    column_mapping = {
        'unique_hh_id': 'HHID',
        'TAZ': 'TAZ', 
        'MAZ': 'MAZ',
        'COUNTY': 'MTCCountyID',
        'HINCP': 'HHINCADJ',
        'NP': 'NP',
        'VEH': 'VEH',
        'TEN': 'TEN',
        'HHT': 'HHT',
        'BLD': 'BLD',
        'TYPEHUGQ': 'TYPE'
    }
    
    for pre_col, post_col in column_mapping.items():
        if pre_col in hh_pre_cols and post_col in hh_post_cols:
            desc = column_descriptions.get(pre_col, 'No description')
            summary.append(f"| {pre_col} | {post_col} | {desc} |")
    
    # Show new columns in postprocessed
    new_cols = set(hh_post_cols) - set(column_mapping.values())
    if new_cols:
        summary.append("")
        summary.append("**New columns in postprocessed file:**")
        for col in sorted(new_cols):
            desc = column_descriptions.get(col, 'No description')
            summary.append(f"- `{col}`: {desc}")
    
    # Show removed columns
    removed_cols = set(hh_pre_cols) - set(column_mapping.keys())
    if removed_cols:
        summary.append("")
        summary.append("**Columns removed in postprocessing:**")
        for col in sorted(removed_cols):
            desc = column_descriptions.get(col, 'No description')
            summary.append(f"- `{col}`: {desc}")
    
    summary.append("")
    
    # === DETAILED HOUSEHOLD COLUMN ANALYSIS ===
    logger.info("Loading household samples for detailed analysis...")
    
    # Load samples for detailed analysis
    hh_pre_sample = pd.read_csv(preprocessed_hh, nrows=50000)  # Sample size
    hh_post_sample = pd.read_csv(postprocessed_hh, nrows=50000)
    
    summary.append("### Detailed Household Column Analysis")
    summary.append("*Based on 50,000 row samples*")
    summary.append("")
    
    # Analyze key columns
    key_hh_columns = ['MAZ', 'TAZ', 'hhgqtype', 'NP', 'VEH'] if 'hhgqtype' in hh_pre_sample.columns else ['MAZ', 'TAZ', 'NP', 'VEH']
    
    for col in key_hh_columns:
        if col in hh_pre_sample.columns:
            summary.append(f"#### {column_descriptions.get(col, col)}")
            
            dist = analyze_column_distribution(hh_pre_sample, col, sample_size=50000)
            summary.append(f"**Preprocessed (`{col}`):**")
            
            if 'mean' in dist:
                summary.append(f"- Range: {dist['min']} to {dist['max']}")
                summary.append(f"- Mean: {dist['mean']:.2f}, Median: {dist['median']:.2f}")
                summary.append(f"- Unique values: {dist['unique_count']:,}")
            else:
                summary.append(f"- Unique values: {dist['unique_count']:,}")
                if dist['most_common']:
                    summary.append("- Most common values:")
                    for val, count in list(dist['most_common'].items())[:5]:
                        summary.append(f"  - {val}: {count:,} occurrences")
            
            # Check if column exists in postprocessed (might be renamed)
            post_col = column_mapping.get(col, col)
            if post_col in hh_post_sample.columns:
                post_dist = analyze_column_distribution(hh_post_sample, post_col, sample_size=50000)
                summary.append(f"**Postprocessed (`{post_col}`):**")
                if 'mean' in post_dist:
                    summary.append(f"- Range: {post_dist['min']} to {post_dist['max']}")
                    summary.append(f"- Mean: {post_dist['mean']:.2f}, Median: {post_dist['median']:.2f}")
                    summary.append(f"- Unique values: {post_dist['unique_count']:,}")
                else:
                    summary.append(f"- Unique values: {post_dist['unique_count']:,}")
                    if post_dist['most_common']:
                        summary.append("- Most common values:")
                        for val, count in list(post_dist['most_common'].items())[:5]:
                            summary.append(f"  - {val}: {count:,} occurrences")
            
            summary.append("")
    
    # === PERSONS ANALYSIS ===
    logger.info("Analyzing persons files...")
    summary.append("## Persons Analysis")
    summary.append("")
    
    # Load person file info
    pp_pre_info = pd.read_csv(preprocessed_pp, nrows=1)
    pp_post_info = pd.read_csv(postprocessed_pp, nrows=1)
    
    # Get full row counts
    pp_pre_count = sum(1 for _ in open(preprocessed_pp)) - 1
    pp_post_count = sum(1 for _ in open(postprocessed_pp)) - 1
    
    summary.append(f"**File Comparison:**")
    summary.append(f"- Preprocessed: `synthetic_persons.csv` - {pp_pre_count:,} persons")
    summary.append(f"- Postprocessed: `persons_2023_tm2.csv` - {pp_post_count:,} persons")
    summary.append(f"- Row count change: {pp_post_count - pp_pre_count:+,} persons")
    summary.append("")
    
    # Person column analysis
    pp_pre_cols = list(pp_pre_info.columns)
    pp_post_cols = list(pp_post_info.columns)
    
    summary.append("**Column Mapping:**")
    summary.append("| Preprocessed Column | Postprocessed Column | Description |")
    summary.append("|---------------------|---------------------|-------------|")
    
    person_column_mapping = {
        'unique_hh_id': 'HHID',
        'unique_per_id': 'PERID',
        'AGEP': 'AGEP',
        'SEX': 'SEX',
        'SCHL': 'SCHL',
        'occupation': 'OCCP',
        'WKHP': 'WKHP',
        'WKW': 'WKW',
        'employed': 'EMPLOYED',
        'ESR': 'ESR',
        'SCHG': 'SCHG',
        'hhgqtype': 'hhgqtype',
        'person_type': 'person_type'
    }
    
    for pre_col, post_col in person_column_mapping.items():
        if pre_col in pp_pre_cols and post_col in pp_post_cols:
            desc = column_descriptions.get(pre_col, 'No description')
            summary.append(f"| {pre_col} | {post_col} | {desc} |")
    
    summary.append("")
    
    # === KEY STATISTICS ===
    logger.info("Generating key statistics...")
    summary.append("## Key Statistics")
    summary.append("")
    
    # Load small samples for quick stats
    hh_sample = pd.read_csv(postprocessed_hh, nrows=10000)
    pp_sample = pd.read_csv(postprocessed_pp, nrows=10000)
    
    if 'hhgqtype' in hh_sample.columns:
        summary.append("### Group Quarters Distribution (Households)")
        gq_dist = hh_sample['hhgqtype'].value_counts().sort_index()
        gq_labels = {0: 'Regular Households', 1: 'University GQ', 2: 'Military GQ', 3: 'Other GQ'}
        
        for gq_type, count in gq_dist.items():
            label = gq_labels.get(gq_type, f'GQ Type {gq_type}')
            pct = (count / len(hh_sample)) * 100
            summary.append(f"- {label}: {count:,} ({pct:.1f}%)")
        summary.append("")
    
    if 'AGEP' in pp_sample.columns:
        summary.append("### Age Distribution (Persons)")
        age_bins = [0, 18, 35, 50, 65, 100]
        age_labels = ['0-17', '18-34', '35-49', '50-64', '65+']
        pp_sample['age_group'] = pd.cut(pp_sample['AGEP'], bins=age_bins, labels=age_labels, right=False)
        age_dist = pp_sample['age_group'].value_counts().sort_index()
        
        for age_group, count in age_dist.items():
            pct = (count / len(pp_sample)) * 100
            summary.append(f"- {age_group}: {count:,} ({pct:.1f}%)")
        summary.append("")
    
    if 'VEH' in hh_sample.columns:
        summary.append("### Vehicle Ownership (Households)")
        veh_dist = hh_sample['VEH'].value_counts().sort_index()
        for vehicles, count in veh_dist.items():
            pct = (count / len(hh_sample)) * 100
            veh_label = f"{vehicles} vehicles" if vehicles != 1 else "1 vehicle"
            summary.append(f"- {veh_label}: {count:,} ({pct:.1f}%)")
        summary.append("")
    
    # Write summary to file
    output_file = config.OUTPUT_DIR / "OUTPUT_FILES_SUMMARY.md"
    with open(output_file, 'w') as f:
        f.write('\n'.join(summary))
    
    logger.info(f"Analysis complete! Summary written to: {output_file}")
    print(f"\n✓ Analysis complete! Summary written to: {output_file}")

if __name__ == "__main__":
    config = UnifiedTM2Config()
    compare_files_summary(config)
