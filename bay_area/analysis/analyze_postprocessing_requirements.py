#!/usr/bin/env python3
"""
Post-Processing Analysis Script for PopulationSim TM2 Outputs
Analyzes current PopulationSim outputs against target Travel Model Two requirements
Identifies gaps and issues that need to be addressed in postprocess_recode.py
"""

import pandas as pd
import pathlib
import sys
from collections import OrderedDict
import argparse

class PostProcessAnalyzer:
    def __init__(self):
        self.base_dir = pathlib.Path(__file__).parent
        
        # Current PopulationSim output paths
        self.current_outputs = {
            'households': self.base_dir / "output_2023/populationsim_working_dir/output/households_2023_tm2.csv",
            'persons': self.base_dir / "output_2023/populationsim_working_dir/output/persons_2023_tm2.csv"
        }
        
        # Target model input paths  
        self.target_outputs = {
            'households': self.base_dir / "model_inputs/inputs/households.csv",
            'persons': self.base_dir / "model_inputs/inputs/persons.csv"
        }
        
        # TM2 required columns from documentation
        self.tm2_household_schema = OrderedDict([
            ("HHID", "Unique household ID"),
            ("TAZ", "TAZ of residence"),
            ("MAZ", "MAZ of residence"),
            ("MTCCountyID", "County of residence (1-9)"),
            ("HHINCADJ", "Household income in 2010 dollars"),
            ("NWRKRS_ESR", "Number of workers (employed persons)"),
            ("VEH", "Number of vehicles owned"),
            ("NP", "Number of persons in household"),
            ("HHT", "Household type"),
            ("BLD", "Units in structure"),
            ("TYPE", "Type of unit (housing/GQ)")
        ])
        
        self.tm2_person_schema = OrderedDict([
            ("HHID", "Unique household ID"),
            ("PERID", "Unique person ID"),
            ("AGEP", "Age of person"),
            ("SEX", "Sex of person"),
            ("SCHL", "Education attainment"),
            ("OCCP", "Occupation"),
            ("WKHP", "Usual hours worked per week"),
            ("WKW", "Weeks worked during past 12 months"),
            ("EMPLOYED", "Employment status (0/1)"),
            ("ESR", "Employment status recode"),
            ("SCHG", "Grade level attending")
        ])
        
        # Current postprocess_recode.py mapping (TM2 section)
        self.current_tm2_household_mapping = OrderedDict([
            ("unique_hh_id", "HHID"),
            ("TAZ", "TAZ"),
            ("MAZ", "MAZ"),
            ("COUNTY", "MTCCountyID"),
            ("hh_income_2010", "HHINCADJ"),
            ("hh_workers_from_esr", "NWRKRS_ESR"),
            ("VEH", "VEH"),
            ("NP", "NP"),
            ("HHT", "HHT"),
            ("BLD", "BLD"),
            ("TYPEHUGQ", "TYPE")
        ])
        
        self.current_tm2_person_mapping = OrderedDict([
            ("unique_hh_id", "HHID"), 
            ("unique_per_id", "PERID"),
            ("AGEP", "AGEP"),
            ("SEX", "SEX"),
            ("SCHL", "SCHL"),
            ("occupation", "OCCP"),
            ("WKHP", "WKHP"),
            ("WKW", "WKW"),
            ("employed", "EMPLOYED"),
            ("ESR", "ESR"),
            ("SCHG", "SCHG")
        ])
    
    def load_data_samples(self):
        """Load sample data from current and target outputs"""
        print("Loading data samples...")
        
        data = {}
        
        # Load current PopulationSim outputs (sample)
        try:
            data['current_hh'] = pd.read_csv(self.current_outputs['households'], nrows=1000)
            data['current_per'] = pd.read_csv(self.current_outputs['persons'], nrows=1000)
            print(f"[OK] Loaded current outputs: {len(data['current_hh'])} households, {len(data['current_per'])} persons")
        except Exception as e:
            print(f"[X] Error loading current outputs: {e}")
            data['current_hh'] = pd.DataFrame()
            data['current_per'] = pd.DataFrame()
        
        # Load target outputs (sample) 
        try:
            data['target_hh'] = pd.read_csv(self.target_outputs['households'], nrows=1000)
            data['target_per'] = pd.read_csv(self.target_outputs['persons'], nrows=1000)
            print(f"[OK] Loaded target outputs: {len(data['target_hh'])} households, {len(data['target_per'])} persons")
        except Exception as e:
            print(f"[X] Error loading target outputs: {e}")
            data['target_hh'] = pd.DataFrame()
            data['target_per'] = pd.DataFrame()
            
        return data
    
    def analyze_schema_gaps(self, data):
        """Analyze gaps between current PopulationSim outputs and TM2 requirements"""
        print("\n" + "="*80)
        print("SCHEMA ANALYSIS")
        print("="*80)
        print("="*80)
        # Household schema analysis
        print("\n[SCHEMA] HOUSEHOLD SCHEMA COMPARISON")
        print("-" * 50)
        if not data['current_hh'].empty:
            current_hh_cols = set(data['current_hh'].columns)
            target_hh_cols = set(data['target_hh'].columns) if not data['target_hh'].empty else set()
            required_hh_cols = set(self.tm2_household_schema.keys())
            mapped_hh_cols = set(self.current_tm2_household_mapping.keys())
            print(f"Current PopulationSim columns: {len(current_hh_cols)}")
            print(f"Target TM2 columns: {len(target_hh_cols)}")
            print(f"Required TM2 columns: {len(required_hh_cols)}")
            print(f"Mapped columns in postprocess_recode.py: {len(mapped_hh_cols)}")
            # Check what's missing
            missing_source_cols = mapped_hh_cols - current_hh_cols
            missing_target_cols = required_hh_cols - target_hh_cols if target_hh_cols else set()
            unmapped_source_cols = current_hh_cols - mapped_hh_cols
            if missing_source_cols:
                print(f"\n[X] MISSING SOURCE COLUMNS (need in PopulationSim output):")
                for col in sorted(missing_source_cols):
                    print(f"   - {col}")
            if missing_target_cols:
                print(f"\n[X] MISSING TARGET COLUMNS (not in target file):")
                for col in sorted(missing_target_cols):
                    print(f"   - {col}: {self.tm2_household_schema[col]}")
            if unmapped_source_cols:
                print(f"\n[!] UNMAPPED SOURCE COLUMNS (available but not used):")
                for col in sorted(unmapped_source_cols):
                    print(f"   - {col}")
        # Person schema analysis
        print("\n[SCHEMA] PERSON SCHEMA COMPARISON")
        print("-" * 50)
        if not data['current_per'].empty:
            current_per_cols = set(data['current_per'].columns)
            target_per_cols = set(data['target_per'].columns) if not data['target_per'].empty else set()
            required_per_cols = set(self.tm2_person_schema.keys())
            mapped_per_cols = set(self.current_tm2_person_mapping.keys())
            print(f"Current PopulationSim columns: {len(current_per_cols)}")
            print(f"Target TM2 columns: {len(target_per_cols)}")
            print(f"Required TM2 columns: {len(required_per_cols)}")
            print(f"Mapped columns in postprocess_recode.py: {len(mapped_per_cols)}")
            # Check what's missing
            missing_source_cols = mapped_per_cols - current_per_cols
            missing_target_cols = required_per_cols - target_per_cols if target_per_cols else set()
            unmapped_source_cols = current_per_cols - mapped_per_cols
            if missing_source_cols:
                print(f"\n[X] MISSING SOURCE COLUMNS (need in PopulationSim output):")
                for col in sorted(missing_source_cols):
                    print(f"   - {col}")
            if missing_target_cols:
                print(f"\n[X] MISSING TARGET COLUMNS (not in target file):")
                for col in sorted(missing_target_cols):
                    print(f"   - {col}: {self.tm2_person_schema[col]}")
            if unmapped_source_cols:
                print(f"\n[!] UNMAPPED SOURCE COLUMNS (available but not used):")
                for col in sorted(unmapped_source_cols):
                    print(f"   - {col}")
    
    def analyze_group_quarters(self, data):
        """Analyze group quarters handling"""
        print("\n" + "="*80)
        print("GROUP QUARTERS ANALYSIS")
        print("="*80)
        
        if not data['current_hh'].empty:
            # Check if hhgqtype exists and is populated
            if 'hhgqtype' in data['current_hh'].columns:
                gq_counts = data['current_hh']['hhgqtype'].value_counts().sort_index()
                print(f"\nGROUP QUARTERS TYPE DISTRIBUTION (hhgqtype):")
                gq_mapping = {0: "Household (not GQ)", 1: "College GQ", 2: "Military GQ", 3: "Other GQ"}
                for gq_type, count in gq_counts.items():
                    gq_name = gq_mapping.get(gq_type, f"Unknown ({gq_type})")
                    pct = (count / len(data['current_hh'])) * 100
                    print(f"   {gq_type}: {gq_name} - {count:,} ({pct:.1f}%)")
            else:
                print("[X] hhgqtype column missing from households")
                
        if not data['current_per'].empty:
            # Check if hhgqtype exists in persons (should after our fix)
            if 'hhgqtype' in data['current_per'].columns:
                gq_counts = data['current_per']['hhgqtype'].value_counts().sort_index()
                print(f"\nPERSON GROUP QUARTERS TYPE DISTRIBUTION:")
                gq_mapping = {0: "Household (not GQ)", 1: "College GQ", 2: "Military GQ", 3: "Other GQ"}
                for gq_type, count in gq_counts.items():
                    gq_name = gq_mapping.get(gq_type, f"Unknown ({gq_type})")
                    pct = (count / len(data['current_per'])) * 100
                    print(f"   {gq_type}: {gq_name} - {count:,} ({pct:.1f}%)")
            else:
                print("[X] hhgqtype column missing from persons (this was the bug we found!)")
    
    def analyze_data_quality(self, data):
        """Analyze data quality issues"""
        print("\n" + "="*80)
        print("DATA QUALITY ANALYSIS")
        print("="*80)
        
        # Check households
        if not data['current_hh'].empty:
            print("\nHOUSEHOLD DATA QUALITY:")
            
            # Check for missing values
            null_cols = data['current_hh'].isnull().sum()
            null_cols = null_cols[null_cols > 0]
            if not null_cols.empty:
                print(f"   Columns with null values:")
                for col, count in null_cols.items():
                    pct = (count / len(data['current_hh'])) * 100
                    print(f"     - {col}: {count} ({pct:.1f}%)")
            else:
                print("   [OK] No null values found")
                
            # Check ID uniqueness
            if 'unique_hh_id' in data['current_hh'].columns:
                unique_ids = data['current_hh']['unique_hh_id'].nunique()
                total_rows = len(data['current_hh'])
                if unique_ids == total_rows:
                    print(f"   [OK] Household IDs are unique ({unique_ids:,} unique)")
                else:
                    print(f"   [X] Household ID duplicates: {total_rows - unique_ids} duplicates")
            
            # Check geographic consistency
            if all(col in data['current_hh'].columns for col in ['TAZ', 'MAZ', 'COUNTY']):
                print(f"   Geography: {data['current_hh']['COUNTY'].nunique()} counties, "
                      f"{data['current_hh']['TAZ'].nunique()} TAZs, "
                      f"{data['current_hh']['MAZ'].nunique()} MAZs")
        
        # Check persons
        if not data['current_per'].empty:
            print("\nPERSON DATA QUALITY:")
            
            # Check for missing values
            null_cols = data['current_per'].isnull().sum()
            null_cols = null_cols[null_cols > 0]
            if not null_cols.empty:
                print(f"   Columns with null values:")
                for col, count in null_cols.items():
                    pct = (count / len(data['current_per'])) * 100
                    print(f"     - {col}: {count} ({pct:.1f}%)")
            else:
                print("   [OK] No null values found")
                
            # Check person_type distribution (our fix)
            if 'person_type' in data['current_per'].columns:
                ptype_counts = data['current_per']['person_type'].value_counts().sort_index()
                print(f"   Person Type Distribution:")
                ptype_mapping = {1: "Full-time worker", 2: "Part-time worker", 3: "College student", 4: "Non-working adult"}
                for ptype, count in ptype_counts.items():
                    ptype_name = ptype_mapping.get(ptype, f"Unknown ({ptype})")
                    pct = (count / len(data['current_per'])) * 100
                    print(f"     {ptype}: {ptype_name} - {count:,} ({pct:.1f}%)")
    
    def analyze_postprocess_script(self):
        """Analyze the current postprocess_recode.py script for issues"""
        print("\n" + "="*80)
        print("POSTPROCESS_RECODE.PY ANALYSIS")
        print("="*80)
        
        script_path = self.base_dir / "postprocess_recode.py"
        
        if not script_path.exists():
            print("❌ postprocess_recode.py not found!")
            return
            
        print(f"📄 Analyzing {script_path}")
        
        with open(script_path, 'r') as f:
            content = f.read()
            
        issues = []
        recommendations = []
        
        # Check for TM2 vs TM1 usage
        if "'TM1'" in content and "'TM2'" in content:
            print("[OK] Script supports both TM1 and TM2 modes")
        elif "'TM2'" not in content:
            issues.append("Script may not support TM2 mode properly")
            
        # Check for group quarters handling
        if 'hhgqtype' not in content:
            issues.append("Script may not handle group quarters (hhgqtype) properly")
            recommendations.append("Add hhgqtype to both household and person output mappings")
            
        # Check for person_type handling
        if 'person_type' not in content:
            issues.append("Script may not handle person_type field")
            recommendations.append("Add person_type to person output mapping")
            
        # Check for income year consistency
        if 'hh_income_2010' in content and 'hh_income_2023' in content:
            issues.append("Script has both 2010 and 2023 income fields - may cause confusion")
            recommendations.append("Clarify which income field should be used for TM2 HHINCADJ")
            
        # Check for county field mapping
        if 'MTCCountyID' in content and 'COUNTY' in content:
            print("[OK] Script maps county fields")
        else:
            issues.append("County field mapping may be missing or incorrect")
            
        if issues:
            print(f"\n[X] IDENTIFIED ISSUES:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
                
        if recommendations:
            print(f"\n[!] RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
                
        if not issues:
            print("[OK] No major issues identified in postprocess script")
    
    def generate_recommendations(self):
        """Generate specific recommendations for fixing postprocess_recode.py"""
        print("\n" + "="*80)
        print("RECOMMENDATIONS & ACTION ITEMS")
        print("="*80)
        print("\nIMMEDIATE FIXES NEEDED:")
        print("1. Add 'hhgqtype' to TM2 person column mapping")
        print("2. Add 'person_type' to TM2 person column mapping")
        print("3. Verify county field mapping (COUNTY -> MTCCountyID)")
        print("4. Clarify income field usage (2010 vs 2023)")
        print("5. Test with current group quarters data")
        print("\nUPDATED TM2 MAPPINGS SHOULD BE:")
        print("\nHouseholds:")
        for source, target in self.current_tm2_household_mapping.items():
            print(f"   '{source}' -> '{target}'")
        print("   # Add any missing fields from PopulationSim output")
        print("\nPersons:")
        for source, target in self.current_tm2_person_mapping.items():
            print(f"   '{source}' -> '{target}'")
        print("   'hhgqtype' -> 'hhgqtype'  # ADD THIS")
        print("   'person_type' -> 'person_type'  # ADD THIS")
        print("\nTESTING RECOMMENDATIONS:")
        print("1. Run postprocess_recode.py with current outputs")
        print("2. Compare output schemas with target requirements")
        print("3. Verify group quarters data flows through correctly")
        print("4. Check person_type values are employment-based, not age-based")
        print("5. Validate county numbering (1-9) in output")
    
    def run_analysis(self):
        """Run complete analysis"""
        print("="*80)
        print("POPULATIONSIM TM2 POST-PROCESSING ANALYSIS")
        print("="*80)
        print(f"Analyzing outputs and requirements...")
        print(f"Base directory: {self.base_dir}")
        
        # Load data
        data = self.load_data_samples()
        
        # Run analyses
        self.analyze_schema_gaps(data)
        self.analyze_group_quarters(data)
        self.analyze_data_quality(data)
        self.analyze_postprocess_script()
        self.generate_recommendations()
        
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print("\nNext steps:")
        print("1. Review recommendations above")
        print("2. Update postprocess_recode.py with missing mappings")
        print("3. Test with current PopulationSim outputs") 
        print("4. Verify final outputs match TM2 requirements")

def main():
    parser = argparse.ArgumentParser(description='Analyze PopulationSim post-processing requirements')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    analyzer = PostProcessAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
