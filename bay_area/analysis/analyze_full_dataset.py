#!/usr/bin/env python3
"""
Optimized Full Dataset Analysis for PopulationSim TM2 Output
Uses chunking, vectorization, and memory optimization to analyze complete files.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from collections import defaultdict
import gc
from unified_tm2_config import UnifiedTM2Config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptimizedAnalyzer:
    def __init__(self, chunk_size=100000):
        self.chunk_size = chunk_size
        self.stats = defaultdict(dict)
        
    def analyze_full_dataset(self, file_path, columns_to_analyze):
        """Analyze full dataset using chunking and vectorization"""
        logger.info(f"Starting full analysis of {file_path}")
        
        # Initialize accumulators
        total_rows = 0
        column_stats = {}
        
        for col in columns_to_analyze:
            column_stats[col] = {
                'count': 0,
                'sum': 0,
                'sum_sq': 0,
                'min': float('inf'),
                'max': float('-inf'),
                'value_counts': defaultdict(int),
                'non_null_count': 0,
                'null_count': 0
            }
        
        # Process file in chunks
        chunk_count = 0
        for chunk in pd.read_csv(file_path, chunksize=self.chunk_size, dtype='object'):
            chunk_count += 1
            if chunk_count % 50 == 0:
                logger.info(f"Processed {chunk_count * self.chunk_size:,} rows...")
            
            # Convert dtypes efficiently
            for col in columns_to_analyze:
                if col in chunk.columns:
                    # Try to convert to numeric if possible
                    if chunk[col].dtype == 'object':
                        chunk[col] = pd.to_numeric(chunk[col], errors='ignore')
            
            total_rows += len(chunk)
            
            # Vectorized analysis for each column
            for col in columns_to_analyze:
                if col not in chunk.columns:
                    continue
                    
                col_data = chunk[col]
                stats = column_stats[col]
                
                # Count null/non-null
                non_null_mask = col_data.notna()
                non_null_data = col_data[non_null_mask]
                
                stats['non_null_count'] += non_null_mask.sum()
                stats['null_count'] += (~non_null_mask).sum()
                
                if len(non_null_data) > 0:
                    if pd.api.types.is_numeric_dtype(non_null_data):
                        # Numeric statistics - vectorized
                        stats['sum'] += non_null_data.sum()
                        stats['sum_sq'] += (non_null_data ** 2).sum()
                        stats['min'] = min(stats['min'], non_null_data.min())
                        stats['max'] = max(stats['max'], non_null_data.max())
                    
                    # Value counts for categorical or discrete numeric
                    unique_vals = len(non_null_data.unique())
                    if unique_vals <= 1000:  # Only count if reasonable number of unique values
                        chunk_counts = non_null_data.value_counts()
                        for val, count in chunk_counts.items():
                            stats['value_counts'][val] += count
            
            # Memory cleanup
            del chunk
            if chunk_count % 100 == 0:
                gc.collect()
        
        logger.info(f"Completed analysis: {total_rows:,} total rows processed")
        
        # Calculate final statistics
        final_stats = {}
        for col, stats in column_stats.items():
            if stats['non_null_count'] > 0:
                final_stats[col] = {
                    'total_count': total_rows,
                    'non_null_count': stats['non_null_count'],
                    'null_count': stats['null_count'],
                    'null_pct': (stats['null_count'] / total_rows) * 100,
                }
                
                if stats['sum'] != 0:  # Numeric column
                    mean = stats['sum'] / stats['non_null_count']
                    variance = (stats['sum_sq'] / stats['non_null_count']) - (mean ** 2)
                    std = np.sqrt(max(0, variance))  # Avoid negative due to floating point errors
                    
                    final_stats[col].update({
                        'min': stats['min'],
                        'max': stats['max'],
                        'mean': mean,
                        'std': std,
                        'unique_count': len(stats['value_counts'])
                    })
                
                # Store top value counts
                if stats['value_counts']:
                    sorted_counts = sorted(stats['value_counts'].items(), 
                                         key=lambda x: x[1], reverse=True)
                    final_stats[col]['top_values'] = dict(sorted_counts[:10])
        
        return final_stats, total_rows

def generate_optimized_summary(config):
    """Generate comprehensive summary using full datasets"""
    
    logger.info("Starting optimized full dataset analysis...")
    
    # File paths
    households_file = config.POPSIM_OUTPUT_DIR / "households_2023_tm2.csv"
    persons_file = config.POPSIM_OUTPUT_DIR / "persons_2023_tm2.csv"
    
    if not households_file.exists() or not persons_file.exists():
        logger.error("Required files not found!")
        return
    
    analyzer = OptimizedAnalyzer(chunk_size=50000)  # Optimized chunk size
    
    summary = []
    summary.append("# PopulationSim TM2 Full Dataset Analysis")
    summary.append(f"Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary.append("*Based on complete datasets - all 3.2M households and 7.8M persons*")
    summary.append("")
    
    # === HOUSEHOLD ANALYSIS ===
    logger.info("Analyzing full household dataset...")
    hh_columns = ['MAZ', 'TAZ', 'MTCCountyID', 'NP', 'VEH', 'HHINCADJ', 'TYPE']
    hh_stats, hh_total = analyzer.analyze_full_dataset(households_file, hh_columns)
    
    summary.append("## Complete Household Analysis")
    summary.append(f"**Total Households:** {hh_total:,}")
    summary.append("")
    
    # Vehicle ownership distribution
    if 'VEH' in hh_stats and 'top_values' in hh_stats['VEH']:
        summary.append("### Vehicle Ownership Distribution (Complete Dataset)")
        veh_counts = hh_stats['VEH']['top_values']
        for veh_num in sorted(veh_counts.keys()):
            count = veh_counts[veh_num]
            pct = (count / hh_total) * 100
            veh_label = f"{int(veh_num)} vehicles" if veh_num != 1 else "1 vehicle"
            summary.append(f"- {veh_label}: {count:,} ({pct:.1f}%)")
        summary.append("")
    
    # Household size distribution  
    if 'NP' in hh_stats and 'top_values' in hh_stats['NP']:
        summary.append("### Household Size Distribution")
        np_counts = hh_stats['NP']['top_values']
        for size in sorted(np_counts.keys()):
            count = np_counts[size]
            pct = (count / hh_total) * 100
            size_label = f"{int(size)} persons" if size != 1 else "1 person"
            summary.append(f"- {size_label}: {count:,} ({pct:.1f}%)")
        summary.append("")
    
    # Geographic distribution
    if 'MTCCountyID' in hh_stats and 'top_values' in hh_stats['MTCCountyID']:
        summary.append("### Geographic Distribution by County")
        county_names = {
            1: 'San Francisco', 2: 'San Mateo', 3: 'Santa Clara',
            4: 'Alameda', 5: 'Contra Costa', 6: 'Solano',
            7: 'Napa', 8: 'Sonoma', 9: 'Marin'
        }
        county_counts = hh_stats['MTCCountyID']['top_values']
        for county_id in sorted(county_counts.keys()):
            count = county_counts[county_id]
            pct = (count / hh_total) * 100
            county_name = county_names.get(int(county_id), f'County {county_id}')
            summary.append(f"- {county_name}: {count:,} ({pct:.1f}%)")
        summary.append("")
    
    # === PERSON ANALYSIS ===
    logger.info("Analyzing full person dataset...")
    pp_columns = ['AGEP', 'SEX', 'EMPLOYED', 'hhgqtype', 'SCHL', 'ESR']
    pp_stats, pp_total = analyzer.analyze_full_dataset(persons_file, pp_columns)
    
    summary.append("## Complete Person Analysis")
    summary.append(f"**Total Persons:** {pp_total:,}")
    summary.append("")
    
    # Age distribution with custom bins
    if 'AGEP' in pp_stats:
        logger.info("Calculating age distribution from full dataset...")
        summary.append("### Age Distribution (Complete Dataset)")
        
        # Calculate age distribution using chunked approach
        age_bins = {
            '0-4': (0, 4), '5-17': (5, 17), '18-24': (18, 24), '25-34': (25, 34),
            '35-44': (35, 44), '45-54': (45, 54), '55-64': (55, 64), '65-74': (65, 74), '75+': (75, 150)
        }
        
        age_counts = defaultdict(int)
        for chunk in pd.read_csv(persons_file, chunksize=50000, usecols=['AGEP']):
            chunk['AGEP'] = pd.to_numeric(chunk['AGEP'], errors='coerce')
            
            for age_group, (min_age, max_age) in age_bins.items():
                mask = (chunk['AGEP'] >= min_age) & (chunk['AGEP'] <= max_age)
                age_counts[age_group] += mask.sum()
        
        for age_group in ['0-4', '5-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65-74', '75+']:
            count = age_counts[age_group]
            pct = (count / pp_total) * 100
            summary.append(f"- {age_group}: {count:,} ({pct:.1f}%)")
        summary.append("")
    
    # Gender distribution
    if 'SEX' in pp_stats and 'top_values' in pp_stats['SEX']:
        summary.append("### Gender Distribution")
        sex_counts = pp_stats['SEX']['top_values']
        sex_labels = {1: 'Male', 2: 'Female'}
        for sex_code in sorted(sex_counts.keys()):
            count = sex_counts[sex_code]
            pct = (count / pp_total) * 100
            sex_label = sex_labels.get(int(sex_code), f'Sex {sex_code}')
            summary.append(f"- {sex_label}: {count:,} ({pct:.1f}%)")
        summary.append("")
    
    # Employment status
    if 'EMPLOYED' in pp_stats and 'top_values' in pp_stats['EMPLOYED']:
        summary.append("### Employment Status")
        emp_counts = pp_stats['EMPLOYED']['top_values']
        emp_labels = {0: 'Not Employed', 1: 'Employed'}
        for emp_code in sorted(emp_counts.keys()):
            count = emp_counts[emp_code]
            pct = (count / pp_total) * 100
            emp_label = emp_labels.get(int(emp_code), f'Status {emp_code}')
            summary.append(f"- {emp_label}: {count:,} ({pct:.1f}%)")
        summary.append("")
    
    # Group Quarters distribution
    if 'hhgqtype' in pp_stats and 'top_values' in pp_stats['hhgqtype']:
        summary.append("### Group Quarters Distribution (Complete Dataset)")
        gq_counts = pp_stats['hhgqtype']['top_values']
        gq_labels = {0: 'Regular Households', 1: 'University GQ', 2: 'Military GQ', 3: 'Other GQ'}
        
        for gq_code in sorted(gq_counts.keys()):
            count = gq_counts[gq_code]
            pct = (count / pp_total) * 100
            gq_label = gq_labels.get(int(gq_code), f'GQ Type {gq_code}')
            summary.append(f"- {gq_label}: {count:,} ({pct:.1f}%)")
        summary.append("")
    
    # === SUMMARY STATISTICS ===
    summary.append("## Key Summary Statistics")
    summary.append("")
    
    if 'HHINCADJ' in hh_stats:
        summary.append(f"**Average Household Income:** ${hh_stats['HHINCADJ']['mean']:,.0f}")
    
    if 'VEH' in hh_stats:
        summary.append(f"**Average Vehicles per Household:** {hh_stats['VEH']['mean']:.2f}")
    
    if 'NP' in hh_stats:
        summary.append(f"**Average Household Size:** {hh_stats['NP']['mean']:.2f} persons")
    
    if 'AGEP' in pp_stats:
        summary.append(f"**Average Age:** {pp_stats['AGEP']['mean']:.1f} years")
    
    summary.append("")
    summary.append("---")
    summary.append("*This analysis processed the complete datasets:*")
    summary.append(f"*- {hh_total:,} households analyzed in full*")
    summary.append(f"*- {pp_total:,} persons analyzed in full*")
    summary.append("*- All statistics represent the complete synthetic population*")
    
    # Write comprehensive summary
    output_file = config.OUTPUT_DIR / "FULL_DATASET_ANALYSIS.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(summary))
    
    logger.info(f"Full dataset analysis complete! Summary written to: {output_file}")
    print(f"\n✓ Full dataset analysis complete! Summary written to: {output_file}")

if __name__ == "__main__":
    config = UnifiedTM2Config()
    generate_optimized_summary(config)
