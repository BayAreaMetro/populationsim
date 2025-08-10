#!/usr/bin/env python3
"""
Track PUMA IDs and formats throughout the entire TM2 PopulationSim pipeline.
This script summarizes exactly what PUMA IDs are used in each step,
including the PopulationSim itself, and matches up the PUMAs as the steps run.
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from typing import Dict, Set, List, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PUMAPipelineTracker:
    """Track PUMA IDs and formats throughout the TM2 pipeline"""
    
    def __init__(self):
        self.puma_summary = {}
        self.base_dir = Path(__file__).parent.parent
        
    def analyze_file_pumas(self, file_path: str, description: str, puma_columns: List[str] = None) -> Dict:
        """Analyze PUMA IDs in a file"""
        results = {
            'file_path': file_path,
            'description': description,
            'exists': False,
            'puma_count': 0,
            'puma_format': 'unknown',
            'puma_values': set(),
            'data_type': 'unknown',
            'sample_values': [],
            'error': None
        }
        
        full_path = self.base_dir / file_path if not os.path.isabs(file_path) else Path(file_path)
        
        if not full_path.exists():
            results['error'] = f"File not found: {full_path}"
            return results
            
        results['exists'] = True
        
        try:
            # Try to read file with different methods based on extension
            if full_path.suffix.lower() == '.csv':
                df = pd.read_csv(full_path)
            else:
                results['error'] = f"Unsupported file format: {full_path.suffix}"
                return results
                
            # Find PUMA columns
            if puma_columns is None:
                puma_cols = [col for col in df.columns if 'puma' in col.lower()]
            else:
                puma_cols = [col for col in puma_columns if col in df.columns]
                
            if not puma_cols:
                results['error'] = "No PUMA columns found"
                return results
                
            # Use first PUMA column found
            puma_col = puma_cols[0]
            puma_data = df[puma_col].dropna()
            
            if len(puma_data) == 0:
                results['error'] = "PUMA column is empty"
                return results
                
            results['puma_count'] = len(puma_data.unique())
            results['puma_values'] = set(puma_data.unique())
            results['data_type'] = str(puma_data.dtype)
            results['sample_values'] = list(puma_data.head(5))
            
            # Determine format
            if puma_data.dtype == 'object':
                # String format - check if zero-padded
                string_vals = puma_data.astype(str)
                if string_vals.str.match(r'^\d{5}$').all():
                    results['puma_format'] = 'zero_padded_string'
                elif string_vals.str.match(r'^\d{1,4}$').all():
                    results['puma_format'] = 'integer_string'
                else:
                    results['puma_format'] = 'mixed_string'
            elif puma_data.dtype in ['int64', 'int32']:
                results['puma_format'] = 'integer'
            else:
                results['puma_format'] = 'other'
                
        except Exception as e:
            results['error'] = str(e)
            
        return results
    
    def check_unified_config(self) -> Dict:
        """Check PUMA configuration in unified_tm2_config.py"""
        results = {
            'description': 'Unified TM2 Configuration',
            'exists': False,
            'puma_count': 0,
            'puma_format': 'unknown',
            'puma_values': set(),
            'error': None
        }
        
        try:
            sys.path.insert(0, str(self.base_dir))
            from unified_tm2_config import UnifiedTM2Config
            
            config = UnifiedTM2Config()
            pumas = config.BAY_AREA_PUMAS
            
            results['exists'] = True
            results['puma_count'] = len(pumas)
            results['puma_values'] = set(pumas)
            
            if isinstance(pumas[0], str):
                if pumas[0].isdigit() and len(pumas[0]) == 5:
                    results['puma_format'] = 'zero_padded_string'
                elif pumas[0].isdigit():
                    results['puma_format'] = 'integer_string'
                else:
                    results['puma_format'] = 'string'
            elif isinstance(pumas[0], int):
                results['puma_format'] = 'integer'
            else:
                results['puma_format'] = 'other'
                
        except Exception as e:
            results['error'] = str(e)
            
        return results
    
    def track_all_pipeline_steps(self) -> Dict[str, Dict]:
        """Track PUMAs through all pipeline steps"""
        
        pipeline_steps = {
            'step_0_config': {
                'description': 'Unified Configuration',
                'checker': self.check_unified_config
            },
            'step_1_crosswalk': {
                'description': 'Geographic Crosswalk',
                'file_path': 'hh_gq/data/geo_cross_walk_tm2.csv',
                'puma_columns': ['PUMA']
            },
            'step_2_raw_households': {
                'description': 'Raw PUMS Households (M: drive)',
                'file_path': 'M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23/hbayarea1923.csv',
                'puma_columns': ['PUMA']
            },
            'step_3_raw_persons': {
                'description': 'Raw PUMS Persons (M: drive)',
                'file_path': 'M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23/pbayarea1923.csv',
                'puma_columns': ['PUMA']
            },
            'step_4_processed_households': {
                'description': 'Processed Households (TM2)',
                'file_path': 'output_2023/households_2023_tm2.csv',
                'puma_columns': ['PUMA']
            },
            'step_5_processed_persons': {
                'description': 'Processed Persons (TM2)',
                'file_path': 'output_2023/persons_2023_tm2.csv',
                'puma_columns': ['PUMA']
            },
            'step_6_seed_households': {
                'description': 'Seed Households (PopulationSim Input)',
                'file_path': 'hh_gq/data/seed_households.csv',
                'puma_columns': ['PUMA']
            },
            'step_7_seed_persons': {
                'description': 'Seed Persons (PopulationSim Input)',
                'file_path': 'hh_gq/data/seed_persons.csv',
                'puma_columns': ['PUMA']
            },
            'step_8_controls_county': {
                'description': 'County Controls',
                'file_path': 'hh_gq/tm2_working_dir/data/county_marginals.csv',
                'puma_columns': ['PUMA']
            },
            'step_9_controls_taz': {
                'description': 'TAZ Controls',
                'file_path': 'hh_gq/tm2_working_dir/data/taz_marginals.csv',
                'puma_columns': ['PUMA']
            },
            'step_10_popsim_settings': {
                'description': 'PopulationSim Settings',
                'file_path': 'hh_gq/tm2_working_dir/configs/settings.yaml',
                'puma_columns': None  # YAML file - special handling needed
            },
            'step_11_popsim_output_hh': {
                'description': 'PopulationSim Output Households',
                'file_path': 'hh_gq/tm2_working_dir/output/final_households.csv',
                'puma_columns': ['PUMA']
            },
            'step_12_popsim_output_persons': {
                'description': 'PopulationSim Output Persons',
                'file_path': 'hh_gq/tm2_working_dir/output/final_persons.csv',
                'puma_columns': ['PUMA']
            }
        }
        
        results = {}
        
        logger.info("Tracking PUMAs through TM2 PopulationSim pipeline...")
        logger.info("=" * 80)
        
        for step_id, step_config in pipeline_steps.items():
            logger.info(f"\nAnalyzing {step_config['description']}...")
            
            if 'checker' in step_config:
                # Special checker function
                step_results = step_config['checker']()
            else:
                # Standard file analysis
                step_results = self.analyze_file_pumas(
                    step_config['file_path'],
                    step_config['description'],
                    step_config.get('puma_columns')
                )
            
            results[step_id] = step_results
            
            # Log results
            if step_results.get('error'):
                logger.warning(f"  ❌ {step_results['error']}")
            elif step_results.get('exists', True):
                logger.info(f"  ✅ Found {step_results['puma_count']} PUMAs ({step_results['puma_format']})")
                if step_results['puma_count'] > 0:
                    sample_pumas = sorted(list(step_results['puma_values']))[:5]
                    logger.info(f"     Sample PUMAs: {sample_pumas}")
            else:
                logger.warning(f"  ⚠️  File not found")
        
        return results
    
    def generate_puma_consistency_report(self, results: Dict[str, Dict]) -> None:
        """Generate a comprehensive PUMA consistency report"""
        
        logger.info("\n" + "=" * 80)
        logger.info("PUMA CONSISTENCY ANALYSIS REPORT")
        logger.info("=" * 80)
        
        # Extract all PUMA sets for comparison
        puma_sets = {}
        formats = {}
        
        for step_id, step_data in results.items():
            if step_data.get('puma_values') and not step_data.get('error'):
                puma_sets[step_id] = step_data['puma_values']
                formats[step_id] = step_data['puma_format']
        
        if not puma_sets:
            logger.error("No valid PUMA data found in any step!")
            return
        
        # Find reference set (preferably crosswalk)
        reference_step = 'step_1_crosswalk' if 'step_1_crosswalk' in puma_sets else list(puma_sets.keys())[0]
        reference_pumas = puma_sets[reference_step]
        
        logger.info(f"\n📊 REFERENCE PUMA SET: {results[reference_step]['description']}")
        logger.info(f"   Count: {len(reference_pumas)}")
        logger.info(f"   Format: {formats[reference_step]}")
        logger.info(f"   Sample: {sorted(list(reference_pumas))[:10]}")
        
        # Compare all steps to reference
        logger.info(f"\n🔍 CONSISTENCY CHECK (vs {reference_step}):")
        consistent_steps = []
        inconsistent_steps = []
        
        for step_id, step_pumas in puma_sets.items():
            if step_id == reference_step:
                continue
                
            # Convert both sets to integers for comparison (handle format differences)
            ref_ints = self._normalize_puma_set(reference_pumas)
            step_ints = self._normalize_puma_set(step_pumas)
            
            if ref_ints == step_ints:
                consistent_steps.append(step_id)
                logger.info(f"   ✅ {results[step_id]['description']}: CONSISTENT")
            else:
                inconsistent_steps.append(step_id)
                missing = ref_ints - step_ints
                extra = step_ints - ref_ints
                logger.warning(f"   ❌ {results[step_id]['description']}: INCONSISTENT")
                if missing:
                    logger.warning(f"      Missing PUMAs: {sorted(list(missing))[:10]}")
                if extra:
                    logger.warning(f"      Extra PUMAs: {sorted(list(extra))[:10]}")
        
        # Format consistency check
        logger.info(f"\n📝 FORMAT CONSISTENCY:")
        format_groups = {}
        for step_id, fmt in formats.items():
            if fmt not in format_groups:
                format_groups[fmt] = []
            format_groups[fmt].append(step_id)
        
        for fmt, steps in format_groups.items():
            logger.info(f"   {fmt}: {len(steps)} steps")
            for step_id in steps:
                logger.info(f"      - {results[step_id]['description']}")
        
        # Summary and recommendations
        logger.info(f"\n📋 SUMMARY:")
        logger.info(f"   Total pipeline steps analyzed: {len(results)}")
        logger.info(f"   Steps with valid PUMA data: {len(puma_sets)}")
        logger.info(f"   Consistent with reference: {len(consistent_steps)}")
        logger.info(f"   Inconsistent steps: {len(inconsistent_steps)}")
        logger.info(f"   Format variations: {len(format_groups)}")
        
        if inconsistent_steps:
            logger.warning(f"\n⚠️  RECOMMENDATIONS:")
            logger.warning(f"   1. Fix PUMA mismatches in {len(inconsistent_steps)} inconsistent steps")
            logger.warning(f"   2. Ensure seed population creation filters PUMAs using crosswalk")
            logger.warning(f"   3. Verify PopulationSim input files match crosswalk PUMAs")
        
        if len(format_groups) > 1:
            logger.warning(f"   4. Standardize PUMA format across pipeline (recommend: integer)")
        
        if not inconsistent_steps and len(format_groups) == 1:
            logger.info(f"\n✅ PIPELINE PUMA CONSISTENCY: EXCELLENT")
            logger.info(f"   All steps have consistent PUMAs and format!")
    
    def _normalize_puma_set(self, puma_set: Set) -> Set[int]:
        """Normalize PUMA set to integers for comparison"""
        normalized = set()
        for puma in puma_set:
            try:
                if isinstance(puma, str):
                    # Remove leading zeros and convert to int
                    normalized.add(int(puma.lstrip('0')))
                else:
                    normalized.add(int(puma))
            except (ValueError, TypeError):
                continue
        return normalized
    
    def run_full_analysis(self) -> None:
        """Run complete PUMA pipeline tracking analysis"""
        logger.info("Starting comprehensive PUMA pipeline tracking...")
        
        results = self.track_all_pipeline_steps()
        self.generate_puma_consistency_report(results)
        
        # Save detailed results to file
        self._save_detailed_results(results)
        
        logger.info(f"\n🎯 Analysis complete! Check puma_pipeline_report.txt for detailed results.")
    
    def _save_detailed_results(self, results: Dict[str, Dict]) -> None:
        """Save detailed results to a text file"""
        output_file = self.base_dir / "analysis" / "puma_pipeline_report.txt"
        
        with open(output_file, 'w') as f:
            f.write("PUMA PIPELINE TRACKING REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            for step_id, step_data in results.items():
                f.write(f"STEP: {step_data['description']}\n")
                f.write(f"Step ID: {step_id}\n")
                
                if 'file_path' in step_data:
                    f.write(f"File: {step_data['file_path']}\n")
                
                f.write(f"Exists: {step_data.get('exists', 'N/A')}\n")
                f.write(f"PUMA Count: {step_data.get('puma_count', 0)}\n")
                f.write(f"Format: {step_data.get('puma_format', 'unknown')}\n")
                
                if step_data.get('error'):
                    f.write(f"Error: {step_data['error']}\n")
                elif step_data.get('puma_values'):
                    sorted_pumas = sorted(list(step_data['puma_values']))
                    f.write(f"All PUMAs: {sorted_pumas}\n")
                
                f.write("\n" + "-" * 40 + "\n\n")

if __name__ == "__main__":
    tracker = PUMAPipelineTracker()
    tracker.run_full_analysis()
