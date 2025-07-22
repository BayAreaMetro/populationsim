#!/usr/bin/env python3
"""
test_output_structure.py

End-to-end test to validate that the output file structure matches expected format
from the 2015 example controls, accounting for known data changes between 2015 and 2023.

This test ensures:
1. All expected output files are generated
2. Column structures match expected patterns
3. Data types are appropriate 
4. Geography IDs are valid
5. Row counts are reasonable
6. Known changes are properly implemented

Usage:
    python test_output_structure.py [--verbose]
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import logging
from typing import Dict, List, Tuple, Optional, Any

# Add the project directory to sys.path for imports
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from tm2_control_utils.config import (
    get_control_categories_for_geography, 
    get_all_expected_controls_for_geography,
    PRIMARY_OUTPUT_DIR,
    MAZ_MARGINALS_FILE,
    TAZ_MARGINALS_FILE, 
    COUNTY_MARGINALS_FILE
)

class OutputStructureTest:
    """Test class for validating output file structure and content."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.setup_logging()
        
        # Define expected file structure based on 2015 examples with known 2023 changes
        self.expected_files = {
            'maz_marginals.csv': {
                'required_columns': ['MAZ', 'num_hh'],  # Core columns that must exist
                'optional_columns': ['gq_pop', 'gq_military', 'gq_university', 'gq_other'],  # May be present
                'deprecated_columns': ['hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus', 'gq_num_hh', 'gq_type_univ', 'gq_type_mil', 'gq_type_othnon'],  # Moved or renamed
                'index_column': 'MAZ',
                'expected_dtypes': {
                    'MAZ': ['int64', 'float64'],  # Allow both due to potential float conversion
                    'num_hh': ['int64', 'float64'],
                    'gq_pop': ['int64', 'float64'],
                    'gq_military': ['int64', 'float64'],
                    'gq_university': ['int64', 'float64'], 
                    'gq_other': ['int64', 'float64']
                }
            },
            
            'taz_marginals.csv': {
                'required_columns': ['TAZ'],  # Core columns that must exist
                'optional_columns': [
                    'hh_inc_30', 'hh_inc_30_60', 'hh_inc_60_100', 'hh_inc_100_plus',  # Income (may be zero-filled)
                    'hh_wrks_0', 'hh_wrks_1', 'hh_wrks_2', 'hh_wrks_3_plus',  # Workers
                    'pers_age_00_19', 'pers_age_20_34', 'pers_age_35_64', 'pers_age_65_plus',  # Age
                    'hh_kids_no', 'hh_kids_yes',  # Children
                    'hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus'  # Household size (moved from MAZ)
                ],
                'index_column': 'TAZ',
                'expected_dtypes': {
                    'TAZ': ['int64', 'float64'],
                    # All control columns should be numeric
                    'hh_inc_30': ['int64', 'float64'],
                    'hh_inc_30_60': ['int64', 'float64'],
                    'hh_inc_60_100': ['int64', 'float64'],
                    'hh_inc_100_plus': ['int64', 'float64'],
                    'hh_wrks_0': ['int64', 'float64'],
                    'hh_wrks_1': ['int64', 'float64'],
                    'hh_wrks_2': ['int64', 'float64'],
                    'hh_wrks_3_plus': ['int64', 'float64'],
                    'pers_age_00_19': ['int64', 'float64'],
                    'pers_age_20_34': ['int64', 'float64'],
                    'pers_age_35_64': ['int64', 'float64'],
                    'pers_age_65_plus': ['int64', 'float64'],
                    'hh_kids_no': ['int64', 'float64'],
                    'hh_kids_yes': ['int64', 'float64'],
                    'hh_size_1': ['int64', 'float64'],
                    'hh_size_2': ['int64', 'float64'],
                    'hh_size_3': ['int64', 'float64'],
                    'hh_size_4_plus': ['int64', 'float64']
                }
            },
            
            'county_marginals.csv': {
                'required_columns': ['COUNTY'],  # Core columns that must exist
                'optional_columns': [
                    'pers_occ_management', 'pers_occ_professional', 'pers_occ_services',
                    'pers_occ_retail', 'pers_occ_manual', 'pers_occ_military'  # May be zero-filled
                ],
                'deprecated_columns': ['county_name'],  # Not always included in newer versions
                'index_column': 'COUNTY',
                'expected_dtypes': {
                    'COUNTY': ['int64', 'float64'],
                    'pers_occ_management': ['int64', 'float64'],
                    'pers_occ_professional': ['int64', 'float64'],
                    'pers_occ_services': ['int64', 'float64'],
                    'pers_occ_retail': ['int64', 'float64'],
                    'pers_occ_manual': ['int64', 'float64'],
                    'pers_occ_military': ['int64', 'float64']
                }
            }
        }
        
        # Expected row counts (approximate, based on Bay Area geography)
        self.expected_row_counts = {
            'maz_marginals.csv': (39000, 40000),  # Approximate MAZ count
            'taz_marginals.csv': (4700, 4800),    # Approximate TAZ count  
            'county_marginals.csv': (9, 12)       # Bay Area counties
        }
        
        # Geographic ID validation ranges
        self.valid_geo_ranges = {
            'MAZ': (10000, 99999),     # MAZ IDs typically 5-digit
            'TAZ': (1, 9999),          # TAZ IDs typically 1-4 digit
            'COUNTY': (6000, 6999)     # California county FIPS codes
        }

    def setup_logging(self):
        """Set up logging configuration."""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p'
        )
        self.logger = logging.getLogger(__name__)

    def test_file_exists(self, file_path: str) -> bool:
        """Test that a required output file exists."""
        if os.path.exists(file_path):
            self.logger.info(f"✓ File exists: {file_path}")
            return True
        else:
            self.logger.error(f"✗ File missing: {file_path}")
            return False

    def test_file_structure(self, file_path: str, expected_structure: Dict) -> Tuple[bool, Dict[str, Any]]:
        """Test the structure of an output file."""
        results = {
            'file_readable': False,
            'columns_valid': False,
            'dtypes_valid': False,
            'row_count_valid': False,
            'geography_ids_valid': False,
            'issues': []
        }
        
        try:
            # Read the file
            df = pd.read_csv(file_path)
            results['file_readable'] = True
            results['actual_columns'] = list(df.columns)
            results['row_count'] = len(df)
            
            self.logger.info(f"Read {file_path}: {len(df)} rows, {len(df.columns)} columns")
            
            # Test column structure
            required_cols = expected_structure.get('required_columns', [])
            optional_cols = expected_structure.get('optional_columns', [])
            all_expected_cols = required_cols + optional_cols
            
            missing_required = [col for col in required_cols if col not in df.columns]
            unexpected_cols = [col for col in df.columns if col not in all_expected_cols]
            
            if missing_required:
                results['issues'].append(f"Missing required columns: {missing_required}")
                self.logger.error(f"✗ Missing required columns: {missing_required}")
            else:
                results['columns_valid'] = True
                self.logger.info(f"✓ All required columns present")
            
            if unexpected_cols:
                self.logger.warning(f"⚠ Unexpected columns (may be new): {unexpected_cols}")
                results['issues'].append(f"Unexpected columns: {unexpected_cols}")
            
            # Test data types
            expected_dtypes = expected_structure.get('expected_dtypes', {})
            dtype_issues = []
            
            for col, expected_types in expected_dtypes.items():
                if col in df.columns:
                    actual_dtype = str(df[col].dtype)
                    if not any(expected_type in actual_dtype for expected_type in expected_types):
                        dtype_issues.append(f"{col}: got {actual_dtype}, expected one of {expected_types}")
                        
            if dtype_issues:
                results['issues'].append(f"Data type issues: {dtype_issues}")
                self.logger.error(f"✗ Data type issues: {dtype_issues}")
            else:
                results['dtypes_valid'] = True
                self.logger.info(f"✓ Data types valid")
            
            # Test row count
            filename = os.path.basename(file_path)
            if filename in self.expected_row_counts:
                min_rows, max_rows = self.expected_row_counts[filename]
                if min_rows <= len(df) <= max_rows:
                    results['row_count_valid'] = True
                    self.logger.info(f"✓ Row count valid: {len(df)} (expected {min_rows}-{max_rows})")
                else:
                    results['issues'].append(f"Row count {len(df)} outside expected range {min_rows}-{max_rows}")
                    self.logger.error(f"✗ Row count {len(df)} outside expected range {min_rows}-{max_rows}")
            
            # Test geography ID validity
            index_col = expected_structure.get('index_column')
            if index_col and index_col in df.columns:
                geo_type = index_col
                if geo_type in self.valid_geo_ranges:
                    min_id, max_id = self.valid_geo_ranges[geo_type]
                    
                    # Convert to numeric, handling potential float values
                    try:
                        geo_ids = pd.to_numeric(df[index_col], errors='coerce').dropna()
                        valid_ids = ((geo_ids >= min_id) & (geo_ids <= max_id)).sum()
                        total_ids = len(geo_ids)
                        
                        if valid_ids == total_ids and total_ids > 0:
                            results['geography_ids_valid'] = True
                            self.logger.info(f"✓ Geography IDs valid: {valid_ids}/{total_ids} in range [{min_id}, {max_id}]")
                        else:
                            results['issues'].append(f"Invalid geography IDs: {valid_ids}/{total_ids} in valid range")
                            self.logger.error(f"✗ Invalid geography IDs: {valid_ids}/{total_ids} in valid range [{min_id}, {max_id}]")
                            
                            # Log examples of invalid IDs
                            invalid_ids = geo_ids[(geo_ids < min_id) | (geo_ids > max_id)]
                            if len(invalid_ids) > 0:
                                self.logger.error(f"  Invalid ID examples: {invalid_ids.head().tolist()}")
                                
                    except Exception as e:
                        results['issues'].append(f"Error validating geography IDs: {str(e)}")
                        self.logger.error(f"✗ Error validating geography IDs: {str(e)}")
            
        except Exception as e:
            results['issues'].append(f"Error reading file: {str(e)}")
            self.logger.error(f"✗ Error reading {file_path}: {str(e)}")
        
        return all([
            results['file_readable'],
            results['columns_valid'], 
            results['dtypes_valid'],
            results['row_count_valid'],
            results['geography_ids_valid']
        ]), results

    def test_data_consistency(self, output_dir: str) -> Tuple[bool, Dict[str, Any]]:
        """Test data consistency across files."""
        results = {
            'maz_taz_consistency': False,
            'household_consistency': False,
            'totals_reasonable': False,
            'issues': []
        }
        
        try:
            # Read the files
            maz_file = os.path.join(output_dir, 'maz_marginals.csv')
            taz_file = os.path.join(output_dir, 'taz_marginals.csv')
            
            if not (os.path.exists(maz_file) and os.path.exists(taz_file)):
                results['issues'].append("Cannot test consistency - missing input files")
                return False, results
                
            maz_df = pd.read_csv(maz_file)
            taz_df = pd.read_csv(taz_file)
            
            # Test 1: Household size consistency (if household size controls moved to TAZ)
            if all(col in taz_df.columns for col in ['hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus']):
                taz_hh_size_total = taz_df[['hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus']].sum().sum()
                
                if 'num_hh' in maz_df.columns:
                    maz_hh_total = maz_df['num_hh'].sum()
                    
                    # Allow for small differences due to rounding/scaling
                    diff_pct = abs(taz_hh_size_total - maz_hh_total) / maz_hh_total * 100 if maz_hh_total > 0 else 100
                    
                    if diff_pct <= 5.0:  # Allow 5% difference
                        results['household_consistency'] = True
                        self.logger.info(f"✓ Household consistency: TAZ hh_size total ({taz_hh_size_total:,.0f}) ≈ MAZ num_hh total ({maz_hh_total:,.0f}), diff: {diff_pct:.2f}%")
                    else:
                        results['issues'].append(f"Household inconsistency: {diff_pct:.2f}% difference between TAZ hh_size total and MAZ num_hh total")
                        self.logger.error(f"✗ Household inconsistency: {diff_pct:.2f}% difference")
            
            # Test 2: Reasonable totals (compare to known Bay Area demographics)
            if 'num_hh' in maz_df.columns:
                total_households = maz_df['num_hh'].sum()
                
                # Bay Area has roughly 2.7M households (2020 Census)
                if 2000000 <= total_households <= 4000000:
                    results['totals_reasonable'] = True
                    self.logger.info(f"✓ Total households reasonable: {total_households:,.0f}")
                else:
                    results['issues'].append(f"Total households unreasonable: {total_households:,.0f} (expected 2-4M)")
                    self.logger.error(f"✗ Total households unreasonable: {total_households:,.0f}")
            
            # Test 3: MAZ-TAZ relationship (basic count check)
            if len(maz_df) > len(taz_df):
                results['maz_taz_consistency'] = True
                self.logger.info(f"✓ MAZ-TAZ relationship: {len(maz_df)} MAZ > {len(taz_df)} TAZ")
            else:
                results['issues'].append(f"MAZ-TAZ relationship unexpected: {len(maz_df)} MAZ vs {len(taz_df)} TAZ")
                self.logger.error(f"✗ MAZ-TAZ relationship unexpected")
            
        except Exception as e:
            results['issues'].append(f"Error in consistency testing: {str(e)}")
            self.logger.error(f"✗ Error in consistency testing: {str(e)}")
        
        return all([
            results['maz_taz_consistency'],
            results['household_consistency'],
            results['totals_reasonable']
        ]), results

    def test_config_alignment(self, output_dir: str) -> Tuple[bool, Dict[str, Any]]:
        """Test that output files align with control configuration."""
        results = {
            'maz_controls_match': False,
            'taz_controls_match': False,
            'county_controls_match': False,
            'issues': []
        }
        
        try:
            # Test MAZ controls
            maz_file = os.path.join(output_dir, 'maz_marginals.csv')
            if os.path.exists(maz_file):
                maz_df = pd.read_csv(maz_file)
                expected_maz_controls = get_all_expected_controls_for_geography('MAZ')
                
                # Remove geography column from comparison
                actual_maz_controls = [col for col in maz_df.columns if col != 'MAZ']
                
                # Check if expected controls are present or appropriately handled
                missing_controls = [ctrl for ctrl in expected_maz_controls if ctrl not in actual_maz_controls]
                
                if not missing_controls:
                    results['maz_controls_match'] = True
                    self.logger.info(f"✓ MAZ controls match config expectations")
                else:
                    # Check if missing controls were moved to TAZ (expected for household size)
                    moved_to_taz = [ctrl for ctrl in missing_controls if ctrl.startswith('hh_size_')]
                    real_missing = [ctrl for ctrl in missing_controls if not ctrl.startswith('hh_size_')]
                    
                    if not real_missing:
                        results['maz_controls_match'] = True
                        self.logger.info(f"✓ MAZ controls match (household size controls moved to TAZ as expected)")
                    else:
                        results['issues'].append(f"MAZ missing controls: {real_missing}")
                        self.logger.error(f"✗ MAZ missing controls: {real_missing}")
            
            # Test TAZ controls  
            taz_file = os.path.join(output_dir, 'taz_marginals.csv')
            if os.path.exists(taz_file):
                taz_df = pd.read_csv(taz_file)
                expected_taz_controls = get_all_expected_controls_for_geography('TAZ')
                
                # Remove geography column from comparison
                actual_taz_controls = [col for col in taz_df.columns if col != 'TAZ']
                
                # Check coverage
                missing_controls = [ctrl for ctrl in expected_taz_controls if ctrl not in actual_taz_controls]
                
                if not missing_controls:
                    results['taz_controls_match'] = True
                    self.logger.info(f"✓ TAZ controls match config expectations")
                else:
                    # Allow for certain controls to be missing (income data may not be reliable)
                    allowable_missing = [ctrl for ctrl in missing_controls if ctrl.startswith('hh_inc_')]
                    critical_missing = [ctrl for ctrl in missing_controls if not ctrl.startswith('hh_inc_')]
                    
                    if not critical_missing:
                        results['taz_controls_match'] = True
                        self.logger.info(f"✓ TAZ controls match (income controls missing as expected)")
                    else:
                        results['issues'].append(f"TAZ missing critical controls: {critical_missing}")
                        self.logger.error(f"✗ TAZ missing critical controls: {critical_missing}")
            
            # Test County controls
            county_file = os.path.join(output_dir, 'county_marginals.csv')
            if os.path.exists(county_file):
                county_df = pd.read_csv(county_file)
                expected_county_controls = get_all_expected_controls_for_geography('COUNTY')
                
                # Remove geography column from comparison
                actual_county_controls = [col for col in county_df.columns if col != 'COUNTY']
                
                # Check coverage
                missing_controls = [ctrl for ctrl in expected_county_controls if ctrl not in actual_county_controls]
                
                if not missing_controls:
                    results['county_controls_match'] = True
                    self.logger.info(f"✓ County controls match config expectations")
                else:
                    # Allow for occupation controls to be missing (data may not be reliable)
                    allowable_missing = [ctrl for ctrl in missing_controls if ctrl.startswith('pers_occ_')]
                    critical_missing = [ctrl for ctrl in missing_controls if not ctrl.startswith('pers_occ_')]
                    
                    if not critical_missing:
                        results['county_controls_match'] = True
                        self.logger.info(f"✓ County controls match (occupation controls missing as expected)")
                    else:
                        results['issues'].append(f"County missing critical controls: {critical_missing}")
                        self.logger.error(f"✗ County missing critical controls: {critical_missing}")
            
        except Exception as e:
            results['issues'].append(f"Error in config alignment testing: {str(e)}")
            self.logger.error(f"✗ Error in config alignment testing: {str(e)}")
        
        return all([
            results['maz_controls_match'],
            results['taz_controls_match'],
            results['county_controls_match']
        ]), results

    def run_full_test(self, output_dir: str = None) -> bool:
        """Run the complete test suite."""
        if output_dir is None:
            output_dir = PRIMARY_OUTPUT_DIR
        
        self.logger.info("="*80)
        self.logger.info("STARTING OUTPUT STRUCTURE VALIDATION TEST")
        self.logger.info("="*80)
        
        all_tests_passed = True
        test_results = {}
        
        # Test 1: File existence
        self.logger.info("Testing file existence...")
        for filename in self.expected_files.keys():
            file_path = os.path.join(output_dir, filename)
            file_exists = self.test_file_exists(file_path)
            test_results[f"{filename}_exists"] = file_exists
            if not file_exists:
                all_tests_passed = False
        
        # Test 2: File structure
        self.logger.info("\nTesting file structure...")
        for filename, expected_structure in self.expected_files.items():
            file_path = os.path.join(output_dir, filename)
            if os.path.exists(file_path):
                structure_valid, structure_results = self.test_file_structure(file_path, expected_structure)
                test_results[f"{filename}_structure"] = structure_results
                if not structure_valid:
                    all_tests_passed = False
        
        # Test 3: Data consistency
        self.logger.info("\nTesting data consistency...")
        consistency_valid, consistency_results = self.test_data_consistency(output_dir)
        test_results['data_consistency'] = consistency_results
        if not consistency_valid:
            all_tests_passed = False
        
        # Test 4: Config alignment
        self.logger.info("\nTesting config alignment...")
        config_valid, config_results = self.test_config_alignment(output_dir)
        test_results['config_alignment'] = config_results
        if not config_valid:
            all_tests_passed = False
        
        # Summary
        self.logger.info("\n" + "="*80)
        if all_tests_passed:
            self.logger.info("🎉 ALL TESTS PASSED! Output structure is valid.")
        else:
            self.logger.error("❌ SOME TESTS FAILED! Review issues above.")
            
            # Print summary of issues
            all_issues = []
            for test_name, results in test_results.items():
                if isinstance(results, dict) and 'issues' in results:
                    for issue in results['issues']:
                        all_issues.append(f"{test_name}: {issue}")
            
            if all_issues:
                self.logger.error("\nSUMMARY OF ISSUES:")
                for issue in all_issues:
                    self.logger.error(f"  - {issue}")
        
        self.logger.info("="*80)
        
        return all_tests_passed

    def run_all_tests(self, output_dir: str = None) -> Dict[str, Any]:
        """
        Run the complete test suite and return structured results.
        
        Returns:
            Dict with keys:
                - success: bool indicating overall success
                - tests_run: int number of tests executed
                - failures: int number of failed tests  
                - failure_details: List of failure descriptions
                - test_results: Dict of detailed test results
        """
        if output_dir is None:
            output_dir = PRIMARY_OUTPUT_DIR
        
        self.logger.info("="*80)
        self.logger.info("STARTING OUTPUT STRUCTURE VALIDATION TEST")
        self.logger.info("="*80)
        
        results = {
            'success': True,
            'tests_run': 0,
            'failures': 0, 
            'failure_details': [],
            'test_results': {}
        }
        
        # Test 1: File existence
        self.logger.info("Testing file existence...")
        for filename in self.expected_files.keys():
            file_path = os.path.join(output_dir, filename)
            file_exists = self.test_file_exists(file_path)
            results['test_results'][f"{filename}_exists"] = file_exists
            results['tests_run'] += 1
            if not file_exists:
                results['success'] = False
                results['failures'] += 1
                results['failure_details'].append(f"Missing file: {filename}")
        
        # Test 2: File structure
        self.logger.info("\nTesting file structure...")
        for filename, expected_structure in self.expected_files.items():
            file_path = os.path.join(output_dir, filename)
            if os.path.exists(file_path):
                structure_valid, structure_results = self.test_file_structure(file_path, expected_structure)
                results['test_results'][f"{filename}_structure"] = structure_results
                results['tests_run'] += 1
                if not structure_valid:
                    results['success'] = False
                    results['failures'] += 1
                    issues = structure_results.get('issues', [])
                    for issue in issues:
                        results['failure_details'].append(f"{filename} structure: {issue}")
        
        # Test 3: Data consistency
        self.logger.info("\nTesting data consistency...")
        consistency_valid, consistency_results = self.test_data_consistency(output_dir)
        results['test_results']['data_consistency'] = consistency_results
        results['tests_run'] += 1
        if not consistency_valid:
            results['success'] = False
            results['failures'] += 1
            issues = consistency_results.get('issues', [])
            for issue in issues:
                results['failure_details'].append(f"Data consistency: {issue}")
        
        # Test 4: Config alignment
        self.logger.info("\nTesting config alignment...")
        config_valid, config_results = self.test_config_alignment(output_dir)
        results['test_results']['config_alignment'] = config_results
        results['tests_run'] += 1
        if not config_valid:
            results['success'] = False
            results['failures'] += 1
            issues = config_results.get('issues', [])
            for issue in issues:
                results['failure_details'].append(f"Config alignment: {issue}")
        
        # Summary
        self.logger.info("\n" + "="*80)
        if results['success']:
            self.logger.info("🎉 ALL TESTS PASSED! Output structure is valid.")
        else:
            self.logger.error("❌ SOME TESTS FAILED! Review issues above.")
            
            if results['failure_details']:
                self.logger.error("\nSUMMARY OF ISSUES:")
                for issue in results['failure_details']:
                    self.logger.error(f"  - {issue}")
        
        self.logger.info("="*80)
        
        return results


def main():
    """Main function to run the output structure test."""
    parser = argparse.ArgumentParser(description='Test output file structure against expected format')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    parser.add_argument('--output-dir', '-o', type=str, default=None,
                       help='Output directory to test (default: output_2023)')
    
    args = parser.parse_args()
    
    # Create and run the test
    test = OutputStructureTest(verbose=args.verbose)
    success = test.run_full_test(output_dir=args.output_dir)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
