#!/usr/bin/env python3
"""
Data Validation Utilities for PopulationSim

Provides validation functions for household and person data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class PopulationSimValidator:
    """Validates data for PopulationSim compatibility"""
    
    @staticmethod
    def validate_household_data(df: pd.DataFrame) -> Dict[str, any]:
        """Validate household data for PopulationSim"""
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'summary': {}
        }
        
        # Required fields check
        required_fields = ['unique_hh_id', 'hhgqtype', 'NP', 'WGTP', 'PUMA', 'COUNTY']
        missing_fields = [f for f in required_fields if f not in df.columns]
        if missing_fields:
            results['errors'].append(f"Missing required fields: {missing_fields}")
            results['valid'] = False
        
        # Data type checks
        numeric_fields = ['NP', 'WGTP', 'hhgqtype', 'PUMA', 'COUNTY']
        for field in numeric_fields:
            if field in df.columns and not pd.api.types.is_numeric_dtype(df[field]):
                results['errors'].append(f"Field {field} should be numeric")
                results['valid'] = False
        
        # Value range checks
        if 'hhgqtype' in df.columns:
            invalid_hhgqtype = (~df['hhgqtype'].isin([0, 1, 2, 3])).sum()
            if invalid_hhgqtype > 0:
                results['warnings'].append(f"{invalid_hhgqtype} records with invalid hhgqtype")
        
        if 'NP' in df.columns:
            zero_np = (df['NP'] <= 0).sum()
            if zero_np > 0:
                results['warnings'].append(f"{zero_np} households with NP <= 0")
        
        # Summary statistics
        results['summary'] = {
            'total_households': len(df),
            'household_types': df['hhgqtype'].value_counts().to_dict() if 'hhgqtype' in df.columns else {},
            'avg_household_size': df['NP'].mean() if 'NP' in df.columns else None,
            'puma_count': df['PUMA'].nunique() if 'PUMA' in df.columns else None
        }
        
        return results
    
    @staticmethod
    def validate_person_data(df: pd.DataFrame) -> Dict[str, any]:
        """Validate person data for PopulationSim"""
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'summary': {}
        }
        
        # Required fields check
        required_fields = ['unique_hh_id', 'unique_person_id', 'AGEP', 'PWGTP', 'PUMA', 'COUNTY']
        missing_fields = [f for f in required_fields if f not in df.columns]
        if missing_fields:
            results['errors'].append(f"Missing required fields: {missing_fields}")
            results['valid'] = False
        
        # Data type checks
        numeric_fields = ['AGEP', 'PWGTP', 'PUMA', 'COUNTY']
        for field in numeric_fields:
            if field in df.columns and not pd.api.types.is_numeric_dtype(df[field]):
                results['errors'].append(f"Field {field} should be numeric")
                results['valid'] = False
        
        # Value range checks
        if 'AGEP' in df.columns:
            invalid_age = ((df['AGEP'] < 0) | (df['AGEP'] > 120)).sum()
            if invalid_age > 0:
                results['warnings'].append(f"{invalid_age} persons with invalid age")
        
        # Summary statistics
        results['summary'] = {
            'total_persons': len(df),
            'age_distribution': {
                'under_18': (df['AGEP'] < 18).sum() if 'AGEP' in df.columns else None,
                'working_age': ((df['AGEP'] >= 18) & (df['AGEP'] < 65)).sum() if 'AGEP' in df.columns else None,
                'seniors': (df['AGEP'] >= 65).sum() if 'AGEP' in df.columns else None
            },
            'avg_age': df['AGEP'].mean() if 'AGEP' in df.columns else None,
            'employed': (df['employed'] == 1).sum() if 'employed' in df.columns else None
        }
        
        return results
    
    @staticmethod
    def validate_puma_coverage(df: pd.DataFrame, expected_pumas: List[str]) -> Dict[str, any]:
        """Validate PUMA coverage in data"""
        if 'PUMA' not in df.columns:
            return {'valid': False, 'error': 'PUMA column not found'}
        
        df_pumas = set(df['PUMA'].astype(str).str.zfill(5).unique())
        expected_pumas_set = set(expected_pumas)
        
        missing_pumas = expected_pumas_set - df_pumas
        extra_pumas = df_pumas - expected_pumas_set
        
        results = {
            'valid': len(missing_pumas) == 0,
            'expected_count': len(expected_pumas),
            'actual_count': len(df_pumas),
            'missing_pumas': list(missing_pumas),
            'extra_pumas': list(extra_pumas),
            'coverage_rate': len(df_pumas & expected_pumas_set) / len(expected_pumas_set)
        }
        
        return results
    
    @staticmethod
    def cross_validate_household_person(household_df: pd.DataFrame, person_df: pd.DataFrame) -> Dict[str, any]:
        """Cross-validate household and person data consistency"""
        results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check household-person linkage
        hh_ids_in_households = set(household_df['unique_hh_id'])
        hh_ids_in_persons = set(person_df['unique_hh_id'])
        
        orphan_households = hh_ids_in_households - hh_ids_in_persons
        orphan_persons = hh_ids_in_persons - hh_ids_in_households
        
        if orphan_households:
            results['warnings'].append(f"{len(orphan_households)} households without persons")
        
        if orphan_persons:
            results['errors'].append(f"{len(orphan_persons)} persons without matching households")
            results['valid'] = False
        
        # Check household size consistency
        if 'NP' in household_df.columns:
            person_counts = person_df['unique_hh_id'].value_counts()
            household_sizes = household_df.set_index('unique_hh_id')['NP']
            
            common_hhs = person_counts.index.intersection(household_sizes.index)
            size_mismatches = (person_counts[common_hhs] != household_sizes[common_hhs]).sum()
            
            if size_mismatches > 0:
                results['warnings'].append(f"{size_mismatches} households with size mismatches")
        
        return results

class DataQualityReporter:
    """Generates data quality reports"""
    
    @staticmethod
    def generate_summary_report(household_df: pd.DataFrame, person_df: pd.DataFrame, 
                              expected_pumas: List[str]) -> str:
        """Generate comprehensive data quality report"""
        validator = PopulationSimValidator()
        
        # Individual validations
        hh_results = validator.validate_household_data(household_df)
        person_results = validator.validate_person_data(person_df)
        puma_results = validator.validate_puma_coverage(household_df, expected_pumas)
        cross_results = validator.cross_validate_household_person(household_df, person_df)
        
        # Build report
        report = []
        report.append("=" * 80)
        report.append("POPULATIONSIM DATA VALIDATION REPORT")
        report.append("=" * 80)
        
        # Summary
        report.append(f"\nDATA SUMMARY:")
        report.append(f"  Households: {len(household_df):,}")
        report.append(f"  Persons: {len(person_df):,}")
        report.append(f"  Expected PUMAs: {len(expected_pumas)}")
        report.append(f"  Actual PUMAs: {puma_results.get('actual_count', 'Unknown')}")
        
        # Validation status
        overall_valid = all([
            hh_results['valid'],
            person_results['valid'], 
            puma_results['valid'],
            cross_results['valid']
        ])
        
        report.append(f"\nVALIDATION STATUS: {'PASS' if overall_valid else 'FAIL'}")
        
        # Errors and warnings
        all_errors = (hh_results['errors'] + person_results['errors'] + 
                     cross_results['errors'])
        all_warnings = (hh_results['warnings'] + person_results['warnings'] + 
                       cross_results['warnings'])
        
        if all_errors:
            report.append(f"\nERRORS ({len(all_errors)}):")
            for error in all_errors:
                report.append(f"  - {error}")
        
        if all_warnings:
            report.append(f"\nWARNINGS ({len(all_warnings)}):")
            for warning in all_warnings:
                report.append(f"  - {warning}")
        
        # Detailed summaries
        if hh_results['summary']:
            report.append(f"\nHOUSEHOLD SUMMARY:")
            summary = hh_results['summary']
            report.append(f"  Total: {summary.get('total_households', 'N/A'):,}")
            report.append(f"  Avg Size: {summary.get('avg_household_size', 'N/A'):.2f}")
            
            hh_types = summary.get('household_types', {})
            if hh_types:
                report.append(f"  Types: {dict(sorted(hh_types.items()))}")
        
        if person_results['summary']:
            report.append(f"\nPERSON SUMMARY:")
            summary = person_results['summary']
            report.append(f"  Total: {summary.get('total_persons', 'N/A'):,}")
            report.append(f"  Avg Age: {summary.get('avg_age', 'N/A'):.1f}")
            
            age_dist = summary.get('age_distribution', {})
            if age_dist:
                report.append(f"  Under 18: {age_dist.get('under_18', 'N/A'):,}")
                report.append(f"  Working Age: {age_dist.get('working_age', 'N/A'):,}")
                report.append(f"  Seniors: {age_dist.get('seniors', 'N/A'):,}")
        
        report.append("=" * 80)
        
        return "\n".join(report)
