#!/usr/bin/env python3
"""
Enhanced Group Quarters Analysis for PopulationSim TM2 Output
Provides detailed analysis of Group Quarters distribution and validation.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from unified_tm2_config import UnifiedTM2Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_group_quarters(config):
    """Detailed Group Quarters analysis"""
    
    logger.info("Starting Group Quarters analysis...")
    
    # Define GQ labels at the top level
    gq_labels = {
        0: 'Regular Households',
        1: 'University Group Quarters', 
        2: 'Military Group Quarters',
        3: 'Other Institutional Group Quarters'
    }
    
    # Load full datasets (we'll sample for memory efficiency)
    hh_file = config.POPSIM_OUTPUT_DIR / "households_2023_tm2.csv"
    pp_file = config.POPSIM_OUTPUT_DIR / "persons_2023_tm2.csv"
    
    # Load samples for analysis
    logger.info("Loading household sample...")
    hh_df = pd.read_csv(hh_file, nrows=200000)  # Larger sample for GQ analysis
    
    logger.info("Loading person sample...")  
    pp_df = pd.read_csv(pp_file, nrows=500000)
    
    summary = []
    summary.append("# Group Quarters Analysis - PopulationSim TM2")
    summary.append(f"Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary.append("")
    summary.append("*Analysis based on sample data for memory efficiency*")
    summary.append("")
    
    # === HOUSEHOLD-LEVEL GQ ANALYSIS ===
    if 'hhgqtype' in hh_df.columns:
        summary.append("## Household-Level Group Quarters Distribution")
        summary.append("")
        
        gq_dist = hh_df['hhgqtype'].value_counts().sort_index()
        total_hh = len(hh_df)
        
        summary.append("| GQ Type | Count | Percentage | Description |")
        summary.append("|---------|-------|------------|-------------|")
        
        for gq_type in sorted(gq_dist.index):
            count = gq_dist[gq_type]
            pct = (count / total_hh) * 100
            label = gq_labels.get(gq_type, f'Unknown GQ Type {gq_type}')
            summary.append(f"| {gq_type} | {count:,} | {pct:.2f}% | {label} |")
        
        summary.append("")
        summary.append(f"**Total Sample Households:** {total_hh:,}")
        summary.append(f"**Regular Households:** {gq_dist.get(0, 0):,} ({(gq_dist.get(0, 0)/total_hh)*100:.1f}%)")
        summary.append(f"**Group Quarters Units:** {(total_hh - gq_dist.get(0, 0)):,} ({((total_hh - gq_dist.get(0, 0))/total_hh)*100:.1f}%)")
        summary.append("")
    
    # === PERSON-LEVEL GQ ANALYSIS ===
    if 'hhgqtype' in pp_df.columns:
        summary.append("## Person-Level Group Quarters Distribution")
        summary.append("")
        
        pp_gq_dist = pp_df['hhgqtype'].value_counts().sort_index()
        total_pp = len(pp_df)
        
        summary.append("| GQ Type | Count | Percentage | Description |")
        summary.append("|---------|-------|------------|-------------|")
        
        for gq_type in sorted(pp_gq_dist.index):
            count = pp_gq_dist[gq_type]
            pct = (count / total_pp) * 100
            label = gq_labels.get(gq_type, f'Unknown GQ Type {gq_type}')
            summary.append(f"| {gq_type} | {count:,} | {pct:.2f}% | {label} |")
        
        summary.append("")
        summary.append(f"**Total Sample Persons:** {total_pp:,}")
        summary.append(f"**Persons in Regular Households:** {pp_gq_dist.get(0, 0):,} ({(pp_gq_dist.get(0, 0)/total_pp)*100:.1f}%)")
        summary.append(f"**Persons in Group Quarters:** {(total_pp - pp_gq_dist.get(0, 0)):,} ({((total_pp - pp_gq_dist.get(0, 0))/total_pp)*100:.1f}%)")
        summary.append("")
    
    # === GQ DEMOGRAPHIC ANALYSIS ===
    if 'hhgqtype' in pp_df.columns and 'AGEP' in pp_df.columns:
        summary.append("## Group Quarters Demographics")
        summary.append("")
        
        # Age analysis by GQ type
        for gq_type in sorted(pp_df['hhgqtype'].unique()):
            gq_persons = pp_df[pp_df['hhgqtype'] == gq_type]
            if len(gq_persons) > 0:
                gq_label = gq_labels.get(gq_type, f'GQ Type {gq_type}')
                
                summary.append(f"### {gq_label}")
                summary.append(f"**Count:** {len(gq_persons):,} persons")
                
                if 'AGEP' in gq_persons.columns:
                    age_stats = gq_persons['AGEP'].describe()
                    summary.append(f"**Age Statistics:**")
                    summary.append(f"- Mean age: {age_stats['mean']:.1f} years")
                    summary.append(f"- Median age: {age_stats['50%']:.0f} years") 
                    summary.append(f"- Age range: {age_stats['min']:.0f} - {age_stats['max']:.0f} years")
                    
                    # Age groups
                    age_bins = [0, 18, 25, 35, 50, 65, 100]
                    age_labels = ['0-17', '18-24', '25-34', '35-49', '50-64', '65+']
                    gq_persons['age_group'] = pd.cut(gq_persons['AGEP'], bins=age_bins, labels=age_labels, right=False)
                    age_dist = gq_persons['age_group'].value_counts().sort_index()
                    
                    summary.append("**Age Distribution:**")
                    for age_group, count in age_dist.items():
                        pct = (count / len(gq_persons)) * 100
                        summary.append(f"- {age_group}: {count:,} ({pct:.1f}%)")
                
                if 'SEX' in gq_persons.columns:
                    sex_dist = gq_persons['SEX'].value_counts()
                    summary.append("**Gender Distribution:**")
                    sex_labels = {1: 'Male', 2: 'Female'}
                    for sex_code, count in sex_dist.items():
                        pct = (count / len(gq_persons)) * 100
                        sex_label = sex_labels.get(sex_code, f'Sex {sex_code}')
                        summary.append(f"- {sex_label}: {count:,} ({pct:.1f}%)")
                
                summary.append("")
    
    # === GEOGRAPHIC DISTRIBUTION ===
    if 'hhgqtype' in hh_df.columns and 'MTCCountyID' in hh_df.columns:
        summary.append("## Group Quarters Geographic Distribution")
        summary.append("")
        
        county_names = {
            1: 'San Francisco',
            2: 'San Mateo', 
            3: 'Santa Clara',
            4: 'Alameda',
            5: 'Contra Costa',
            6: 'Solano',
            7: 'Napa',
            8: 'Sonoma',
            9: 'Marin'
        }
        
        # GQ by county
        gq_only = hh_df[hh_df['hhgqtype'] > 0]  # Exclude regular households
        if len(gq_only) > 0:
            county_gq_dist = gq_only.groupby(['MTCCountyID', 'hhgqtype']).size().unstack(fill_value=0)
            
            summary.append("| County | University GQ | Military GQ | Other GQ | Total GQ |")
            summary.append("|--------|---------------|-------------|----------|----------|")
            
            for county_id in sorted(county_gq_dist.index):
                county_name = county_names.get(county_id, f'County {county_id}')
                univ = county_gq_dist.loc[county_id, 1] if 1 in county_gq_dist.columns else 0
                mil = county_gq_dist.loc[county_id, 2] if 2 in county_gq_dist.columns else 0
                other = county_gq_dist.loc[county_id, 3] if 3 in county_gq_dist.columns else 0
                total = univ + mil + other
                summary.append(f"| {county_name} | {univ:,} | {mil:,} | {other:,} | {total:,} |")
            
            summary.append("")
    
    # === DATA QUALITY CHECKS ===
    summary.append("## Data Quality Validation")
    summary.append("")
    
    # Check for missing values
    missing_checks = []
    
    if 'hhgqtype' in hh_df.columns:
        hh_missing = hh_df['hhgqtype'].isna().sum()
        missing_checks.append(f"- Household hhgqtype missing: {hh_missing:,} ({(hh_missing/len(hh_df))*100:.2f}%)")
    
    if 'hhgqtype' in pp_df.columns:
        pp_missing = pp_df['hhgqtype'].isna().sum()
        missing_checks.append(f"- Person hhgqtype missing: {pp_missing:,} ({(pp_missing/len(pp_df))*100:.2f}%)")
    
    # Check for consistency between household and person records
    if 'hhgqtype' in hh_df.columns and 'hhgqtype' in pp_df.columns and 'HHID' in pp_df.columns:
        # Sample check for consistency
        sample_hh = hh_df[['HHID', 'hhgqtype']].head(10000)  
        sample_pp = pp_df[pp_df['HHID'].isin(sample_hh['HHID'])][['HHID', 'hhgqtype']].head(20000)
        
        if not sample_pp.empty:
            merged = sample_pp.merge(sample_hh, on='HHID', suffixes=('_person', '_household'))
            consistency_check = (merged['hhgqtype_person'] == merged['hhgqtype_household']).all()
            missing_checks.append(f"- Household-Person GQ consistency: {'✓ PASS' if consistency_check else '✗ FAIL'}")
    
    for check in missing_checks:
        summary.append(check)
    
    summary.append("")
    summary.append("---")
    summary.append("*Analysis based on samples from full datasets for memory efficiency*")
    summary.append(f"*Household sample: {len(hh_df):,} out of 3,210,365 total*")
    summary.append(f"*Person sample: {len(pp_df):,} out of 7,834,673 total*")
    
    # Write enhanced summary
    output_file = config.OUTPUT_DIR / "GROUP_QUARTERS_ANALYSIS.md"
    with open(output_file, 'w') as f:
        f.write('\n'.join(summary))
    
    logger.info(f"Group Quarters analysis complete! Summary written to: {output_file}")
    print(f"\n✓ Group Quarters analysis complete! Summary written to: {output_file}")

if __name__ == "__main__":
    config = UnifiedTM2Config()
    analyze_group_quarters(config)
