#!/usr/bin/env python3
"""
PUMA Consistency Tracker for PopulationSim TM2 Pipeline
Analyzes PUMA IDs and formats at every step to ensure consistency
"""

import pandas as pd
import numpy as np
from pathlib import Path
import os
import yaml
import logging
from typing import Dict, List, Set, Tuple, Any
from datetime import datetime

class PUMATracker:
    """Track PUMA consistency across all pipeline steps"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.output_dir = self.base_dir / "output_2023"
        self.working_dir = self.base_dir / "hh_gq" / "tm2_working_dir"
        self.results = {}
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
    def analyze_file_pumas(self, file_path: Path, description: str, puma_columns: List[str] = None) -> Dict[str, Any]:
        """Analyze PUMA IDs in a specific file"""
        if not file_path.exists():
            return {
                'description': description,
                'file_exists': False,
                'file_path': str(file_path),
                'error': 'File not found'
            }
        
        try:
            # Auto-detect PUMA columns if not specified
            if puma_columns is None:
                puma_columns = ['PUMA', 'puma', 'Puma']
                
            # Read file with appropriate method
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            elif file_path.suffix.lower() in ['.yaml', '.yml']:
                return self.analyze_yaml_pumas(file_path, description)
            else:
                return {
                    'description': description,
                    'file_exists': True,
                    'file_path': str(file_path),
                    'error': f'Unsupported file type: {file_path.suffix}'
                }
            
            # Find PUMA column
            puma_col = None
            for col in puma_columns:
                if col in df.columns:
                    puma_col = col
                    break
                    
            if puma_col is None:
                return {
                    'description': description,
                    'file_exists': True,
                    'file_path': str(file_path),
                    'columns': list(df.columns),
                    'error': f'No PUMA column found. Available columns: {list(df.columns)}'
                }
            
            # Analyze PUMA values
            puma_values = df[puma_col].dropna()
            unique_pumas = sorted(puma_values.unique())
            
            # Determine data type and format
            puma_dtype = str(puma_values.dtype)
            sample_values = list(unique_pumas[:10])
            
            # Check format consistency
            format_analysis = self.analyze_puma_format(unique_pumas)
            
            return {
                'description': description,
                'file_exists': True,
                'file_path': str(file_path),
                'file_size_mb': round(file_path.stat().st_size / (1024*1024), 1),
                'total_records': len(df),
                'puma_column': puma_col,
                'puma_dtype': puma_dtype,
                'unique_pumas_count': len(unique_pumas),
                'unique_pumas': unique_pumas,
                'sample_pumas': sample_values,
                'format_analysis': format_analysis,
                'puma_range': f"{min(unique_pumas)} to {max(unique_pumas)}" if unique_pumas else "No PUMAs",
                'has_missing_pumas': puma_values.isna().any(),
                'missing_puma_count': puma_values.isna().sum()
            }
            
        except Exception as e:
            return {
                'description': description,
                'file_exists': True,
                'file_path': str(file_path),
                'error': f'Error reading file: {str(e)}'
            }
    
    def analyze_yaml_pumas(self, file_path: Path, description: str) -> Dict[str, Any]:
        """Analyze PUMA specifications in YAML files"""
        try:
            with open(file_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Look for PUMA-related configurations
            puma_configs = {}
            
            # Check input table dtypes
            if 'input_table_list' in config:
                for table in config['input_table_list']:
                    if 'dtype' in table and 'PUMA' in table['dtype']:
                        puma_configs[f"{table['tablename']}_dtype"] = table['dtype']['PUMA']
            
            # Check geographies
            if 'geographies' in config:
                puma_configs['geographies'] = config['geographies']
                
            # Check seed geography
            if 'seed_geography' in config:
                puma_configs['seed_geography'] = config['seed_geography']
            
            return {
                'description': description,
                'file_exists': True,
                'file_path': str(file_path),
                'puma_configurations': puma_configs,
                'format_analysis': {'type': 'configuration_file'}
            }
            
        except Exception as e:
            return {
                'description': description,
                'file_exists': True,
                'file_path': str(file_path),
                'error': f'Error reading YAML: {str(e)}'
            }
    
    def analyze_puma_format(self, puma_values: List) -> Dict[str, Any]:
        """Analyze the format of PUMA values"""
        if not puma_values:
            return {'type': 'empty', 'consistent': True}
            
        # Convert to strings for analysis
        str_values = [str(p) for p in puma_values]
        
        # Check if all are numeric
        try:
            numeric_values = [float(p) for p in str_values]
            is_numeric = True
        except:
            is_numeric = False
            
        if is_numeric:
            # Check if integers
            int_values = [int(float(p)) for p in str_values]
            is_integer = all(float(p).is_integer() for p in str_values)
            
            if is_integer:
                # Check format patterns
                has_leading_zeros = any(str(p).startswith('0') and len(str(p)) > 1 for p in str_values)
                lengths = [len(str(int(float(p)))) for p in str_values]
                
                return {
                    'type': 'integer',
                    'consistent': True,
                    'has_leading_zeros': has_leading_zeros,
                    'length_range': f"{min(lengths)}-{max(lengths)} digits",
                    'min_value': min(int_values),
                    'max_value': max(int_values),
                    'example_formats': str_values[:5]
                }
            else:
                return {
                    'type': 'float',
                    'consistent': True,
                    'example_formats': str_values[:5]
                }
        else:
            # String format analysis
            lengths = [len(str(p)) for p in str_values]
            has_consistent_length = len(set(lengths)) == 1
            
            return {
                'type': 'string',
                'consistent': has_consistent_length,
                'length_range': f"{min(lengths)}-{max(lengths)} characters",
                'example_formats': str_values[:5]
            }
    
    def track_all_steps(self) -> Dict[str, Any]:
        """Track PUMA consistency across all pipeline steps"""
        
        print("=" * 80)
        print("PUMA CONSISTENCY TRACKER - PopulationSim TM2 Pipeline")
        print("=" * 80)
        print(f"Analysis started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Base directory: {self.base_dir}")
        print()
        
        # Step 0: Configuration and crosswalk
        print("STEP 0: CONFIGURATION & CROSSWALK")
        print("-" * 50)
        
        # Unified config
        config_file = self.base_dir / "unified_tm2_config.py"
        if config_file.exists():
            self.results['config_unified'] = self.analyze_python_config(config_file, "Unified TM2 Configuration")
        
        # Crosswalk files
        crosswalk_files = [
            (self.base_dir / "hh_gq" / "data" / "geo_cross_walk_tm2_updated.csv", "Primary Crosswalk"),
            (self.output_dir / "geo_cross_walk_tm2_updated.csv", "Reference Crosswalk"),
            (self.working_dir / "data" / "geo_cross_walk_tm2.csv", "PopulationSim Crosswalk")
        ]
        
        for file_path, desc in crosswalk_files:
            key = f"crosswalk_{desc.lower().replace(' ', '_')}"
            self.results[key] = self.analyze_file_pumas(file_path, desc)
            self.print_puma_summary(key, self.results[key])
        
        print()
        
        # Step 1: Seed population
        print("STEP 1: SEED POPULATION")
        print("-" * 50)
        
        seed_files = [
            (self.output_dir / "seed_households.csv", "Seed Households"),
            (self.output_dir / "seed_persons.csv", "Seed Persons"),
            (self.working_dir / "data" / "seed_households.csv", "PopulationSim Seed Households"),
            (self.working_dir / "data" / "seed_persons.csv", "PopulationSim Seed Persons")
        ]
        
        for file_path, desc in seed_files:
            key = f"seed_{desc.lower().replace(' ', '_')}"
            self.results[key] = self.analyze_file_pumas(file_path, desc)
            self.print_puma_summary(key, self.results[key])
            
        print()
        
        # Step 2: Control files
        print("STEP 2: CONTROL FILES")
        print("-" * 50)
        
        control_files = [
            (self.output_dir / "county_marginals.csv", "County Controls"),
            (self.output_dir / "taz_marginals.csv", "TAZ Controls"), 
            (self.output_dir / "maz_marginals.csv", "MAZ Controls"),
            (self.working_dir / "data" / "county_marginals.csv", "PopulationSim County Controls"),
            (self.working_dir / "data" / "taz_marginals_hhgq.csv", "PopulationSim TAZ Controls"),
            (self.working_dir / "data" / "maz_marginals_hhgq.csv", "PopulationSim MAZ Controls")
        ]
        
        for file_path, desc in control_files:
            key = f"controls_{desc.lower().replace(' ', '_')}"
            self.results[key] = self.analyze_file_pumas(file_path, desc, ['COUNTY', 'TAZ', 'MAZ'])
            self.print_puma_summary(key, self.results[key])
            
        print()
        
        # Step 3: PopulationSim configuration
        print("STEP 3: POPULATIONSIM CONFIGURATION")
        print("-" * 50)
        
        popsim_config_files = [
            (self.working_dir / "configs" / "settings.yaml", "PopulationSim Settings"),
            (self.working_dir / "configs" / "controls.csv", "PopulationSim Controls")
        ]
        
        for file_path, desc in popsim_config_files:
            key = f"popsim_config_{desc.lower().replace(' ', '_').replace('populationsim_', '')}"
            self.results[key] = self.analyze_file_pumas(file_path, desc)
            self.print_puma_summary(key, self.results[key])
            
        print()
        
        # Step 4: PopulationSim output (if exists)
        print("STEP 4: POPULATIONSIM OUTPUT")
        print("-" * 50)
        
        popsim_output_files = [
            (self.working_dir / "output" / "synthetic_households.csv", "Synthetic Households"),
            (self.working_dir / "output" / "synthetic_persons.csv", "Synthetic Persons"),
            (self.working_dir / "output" / "populationsim.log", "PopulationSim Log")
        ]
        
        for file_path, desc in popsim_output_files:
            if file_path.suffix == '.log':
                self.results[f"popsim_output_{desc.lower().replace(' ', '_')}"] = self.analyze_log_file(file_path, desc)
            else:
                key = f"popsim_output_{desc.lower().replace(' ', '_')}"
                self.results[key] = self.analyze_file_pumas(file_path, desc)
                self.print_puma_summary(key, self.results[key])
        
        print()
        
        # Generate consistency report
        self.generate_consistency_report()
        
        return self.results
    
    def analyze_python_config(self, file_path: Path, description: str) -> Dict[str, Any]:
        """Analyze PUMA definitions in Python config files"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Look for BAY_AREA_PUMAS definition
            puma_info = {}
            if 'BAY_AREA_PUMAS' in content:
                # Extract the PUMA list (simplified parsing)
                start = content.find('BAY_AREA_PUMAS = [')
                if start != -1:
                    end = content.find(']', start)
                    if end != -1:
                        puma_section = content[start:end+1]
                        # Determine if they're strings or integers
                        if "'" in puma_section or '"' in puma_section:
                            format_type = "string"
                        else:
                            format_type = "integer"
                        
                        puma_info = {
                            'found_definition': True,
                            'format_type': format_type,
                            'definition_snippet': puma_section[:200] + "..." if len(puma_section) > 200 else puma_section
                        }
            
            return {
                'description': description,
                'file_exists': True,
                'file_path': str(file_path),
                'puma_info': puma_info,
                'format_analysis': {'type': 'python_config'}
            }
            
        except Exception as e:
            return {
                'description': description,
                'file_exists': True,
                'file_path': str(file_path),
                'error': f'Error analyzing Python config: {str(e)}'
            }
    
    def analyze_log_file(self, file_path: Path, description: str) -> Dict[str, Any]:
        """Analyze PUMA information in log files"""
        if not file_path.exists():
            return {
                'description': description,
                'file_exists': False,
                'file_path': str(file_path)
            }
            
        try:
            with open(file_path, 'r') as f:
                log_content = f.read()
            
            # Look for PUMA-related log entries
            puma_mentions = []
            for line_no, line in enumerate(log_content.split('\n'), 1):
                if 'PUMA' in line.upper():
                    puma_mentions.append(f"Line {line_no}: {line.strip()}")
            
            return {
                'description': description,
                'file_exists': True,
                'file_path': str(file_path),
                'file_size_mb': round(file_path.stat().st_size / (1024*1024), 1),
                'puma_mentions': puma_mentions[:10],  # First 10 mentions
                'total_puma_mentions': len(puma_mentions),
                'format_analysis': {'type': 'log_file'}
            }
            
        except Exception as e:
            return {
                'description': description,
                'file_exists': True,
                'file_path': str(file_path),
                'error': f'Error reading log: {str(e)}'
            }
    
    def print_puma_summary(self, key: str, result: Dict[str, Any]):
        """Print a summary of PUMA analysis for a single file"""
        if not result.get('file_exists', False):
            print(f"❌ {result['description']}: File not found")
            return
            
        if 'error' in result:
            print(f"⚠️  {result['description']}: {result['error']}")
            return
            
        if result.get('format_analysis', {}).get('type') in ['configuration_file', 'python_config', 'log_file']:
            print(f"📄 {result['description']}: {result.get('format_analysis', {}).get('type', 'Config file')}")
            if 'puma_configurations' in result:
                for config_key, config_val in result['puma_configurations'].items():
                    print(f"   {config_key}: {config_val}")
            return
        
        if 'unique_pumas_count' in result:
            format_info = result.get('format_analysis', {})
            dtype = result.get('puma_dtype', 'unknown')
            
            print(f"✅ {result['description']}:")
            print(f"   📊 {result['unique_pumas_count']} unique PUMAs ({result['total_records']:,} records)")
            print(f"   🔢 Data type: {dtype} | Format: {format_info.get('type', 'unknown')}")
            print(f"   📋 Range: {result['puma_range']}")
            print(f"   🔍 Sample: {result['sample_pumas']}")
            
    def generate_consistency_report(self):
        """Generate a comprehensive consistency report"""
        print("=" * 80)
        print("PUMA CONSISTENCY ANALYSIS REPORT")
        print("=" * 80)
        
        # Collect all PUMA sets
        puma_sets = {}
        data_types = {}
        
        for key, result in self.results.items():
            if result.get('file_exists') and 'unique_pumas' in result:
                puma_sets[key] = set(result['unique_pumas'])
                data_types[key] = result.get('puma_dtype', 'unknown')
        
        if not puma_sets:
            print("❌ No PUMA data found in any files!")
            return
            
        # Check consistency across all files
        print("🔍 PUMA Set Consistency:")
        print("-" * 40)
        
        all_pumas = set()
        for puma_set in puma_sets.values():
            all_pumas.update(puma_set)
        
        print(f"Total unique PUMAs across all files: {len(all_pumas)}")
        print(f"PUMA range: {min(all_pumas)} to {max(all_pumas)}")
        print()
        
        # Compare each file to the union
        for key, puma_set in puma_sets.items():
            missing_pumas = all_pumas - puma_set
            extra_pumas = puma_set - all_pumas
            
            if missing_pumas or extra_pumas:
                print(f"⚠️  {key}:")
                if missing_pumas:
                    print(f"   Missing PUMAs: {sorted(list(missing_pumas))[:10]}...")
                if extra_pumas:
                    print(f"   Extra PUMAs: {sorted(list(extra_pumas))}")
            else:
                print(f"✅ {key}: Complete PUMA set")
        
        print()
        print("🔢 Data Type Consistency:")
        print("-" * 40)
        
        for key, dtype in data_types.items():
            print(f"{key}: {dtype}")
        
        # Check if all data types are consistent
        unique_dtypes = set(data_types.values())
        if len(unique_dtypes) == 1:
            print(f"✅ All files use consistent data type: {list(unique_dtypes)[0]}")
        else:
            print(f"⚠️  Inconsistent data types found: {unique_dtypes}")
        
        print()
        print("📋 RECOMMENDATIONS:")
        print("-" * 40)
        
        if len(unique_dtypes) > 1:
            print("❗ Fix data type inconsistencies - all files should use the same PUMA data type")
        
        # Check for missing files
        expected_files = [
            'crosswalk_primary', 'seed_seed_households', 'seed_seed_persons',
            'popsim_config_settings', 'controls_county_controls'
        ]
        
        missing_files = [f for f in expected_files if f not in self.results or not self.results[f].get('file_exists')]
        if missing_files:
            print(f"❗ Missing expected files: {missing_files}")
        
        if not missing_files and len(unique_dtypes) == 1:
            print("✅ PUMA consistency looks good!")
            
        print()

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Track PUMA consistency across PopulationSim pipeline')
    parser.add_argument('--base_dir', type=str, default=None, 
                        help='Base directory for analysis (default: script directory)')
    parser.add_argument('--output_file', type=str, default=None,
                        help='Save detailed results to JSON file')
    
    args = parser.parse_args()
    
    # Run analysis
    tracker = PUMATracker(args.base_dir)
    results = tracker.track_all_steps()
    
    # Save results if requested
    if args.output_file:
        import json
        with open(args.output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"📁 Detailed results saved to: {args.output_file}")

if __name__ == "__main__":
    main()
