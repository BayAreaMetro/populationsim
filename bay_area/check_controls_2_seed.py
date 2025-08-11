#!/usr/bin/env python3
"""
Comprehensive validation script to check encoding consistency between seed population and controls.
This addresses the infinite loop issue in PopulationSim synthesis (Step 4) caused by encoding mismatches.

CRITICAL: PopulationSim requires EXACT encoding consistency between seed data and control definitions.
Any mismatch causes infinite loops during balancing/synthesis.

Author: Generated to fix TM2 workflow encoding issues
Date: 2024
"""
import os
import sys
import pandas as pd
import numpy as np
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    print("[WARNING]  PyYAML not available - settings.yaml validation will be skipped")
    YAML_AVAILABLE = False
    yaml = None
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class SeedControlsValidator:
    """Comprehensive validator for seed population vs control encoding consistency"""
    
    def __init__(self, base_dir=None, test_county=None):
        if base_dir is None:
            self.base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.base_dir = Path(base_dir)
        
        self.output_dir = self.base_dir / "output_2023"
        self.issues = []
        self.warnings = []
        self.test_county = test_county
        
        # Load configuration files first to get county info
        self._load_configurations()
        
        # Set test county from config if not provided
        if self.test_county is None and self.unified_config:
            # Use the first county from the unified config
            if hasattr(self.unified_config, 'BAY_AREA_COUNTIES'):
                self.test_county = self.unified_config.BAY_AREA_COUNTIES[0]
                print(f"[TARGET] Using test county from config: {self.test_county}")
            else:
                self.test_county = 1  # Default to Alameda (county code 1)
                print(f"[TARGET] Using default test county: {self.test_county}")
        elif self.test_county is not None:
            print(f"[TARGET] Using specified test county: {self.test_county}")
        
        # Define expected seed-to-control mappings from analysis
        self._define_expected_mappings()
    
    def _load_configurations(self):
        """Load PopulationSim configuration files"""
        print("[CONFIG] Loading configuration files...")
        print(f"   Base directory: {self.base_dir}")
        
    def _load_configurations(self):
        """Load PopulationSim configuration files"""
        print("[CONFIG] Loading configuration files...")
        print(f"   Base directory: {self.base_dir}")
        
        # Try multiple locations for settings.yaml
        settings_paths = [
            self.base_dir / "settings.yaml",
            self.base_dir / "hh_gq" / "tm2_working_dir" / "configs" / "settings.yaml",
            self.base_dir / "hh_gq" / "configs_TM2" / "settings.yaml"
        ]
        
        settings_loaded = False
        for settings_path in settings_paths:
            print(f"   Checking for settings.yaml at: {settings_path}")
            try:
                if not YAML_AVAILABLE:
                    print(f"[WARNING]  PyYAML not available - skipping settings.yaml")
                    self.warnings.append(f"[WARNING]  PyYAML not available - skipping settings.yaml")
                    self.settings = {}
                    break
                else:
                    with open(settings_path, 'r') as f:
                        self.settings = yaml.safe_load(f)
                    print(f"[SUCCESS] Loaded settings.yaml successfully from {settings_path}")
                    print(f"   Settings keys: {list(self.settings.keys())}")
                    settings_loaded = True
                    break
            except Exception as e:
                print(f"[ERROR] Cannot load settings.yaml: {e}")
                continue
        
        if not settings_loaded:
            self.issues.append(f"[ERROR] Cannot load settings.yaml from any location")
            self.settings = {}
        
        # Try multiple locations for controls.csv
        controls_paths = [
            self.base_dir / "controls.csv",
            self.base_dir / "hh_gq" / "tm2_working_dir" / "configs" / "controls.csv",
            self.base_dir / "hh_gq" / "configs_TM2" / "controls.csv"
        ]
        
        controls_loaded = False
        for controls_path in controls_paths:
            print(f"   Checking for controls.csv at: {controls_path}")
            try:
                self.controls_df = pd.read_csv(controls_path)
                print(f"[SUCCESS] Loaded controls.csv with {len(self.controls_df)} control definitions from {controls_path}")
                print(f"   Controls columns: {list(self.controls_df.columns)}")
                controls_loaded = True
                break
            except Exception as e:
                print(f"[ERROR] Cannot load controls.csv: {e}")
                continue
        
        if not controls_loaded:
            self.issues.append(f"[ERROR] Cannot load controls.csv from any location")
            self.controls_df = pd.DataFrame()
        
        # Load tm2_control_utils config
        print(f"   Attempting to load tm2_control_utils config...")
        try:
            from tm2_control_utils.config_census import CONTROLS
            self.control_config = CONTROLS
            # CONTROL_TYPES doesn't exist, so just set empty
            self.control_types = {}
            print(f"[SUCCESS] Loaded tm2_control_utils config with {len(self.control_config)} control categories")
            print(f"   Control config keys: {list(self.control_config.keys())}")
        except Exception as e:
            print(f"[ERROR] Cannot load tm2_control_utils config: {e}")
            self.issues.append(f"[ERROR] Cannot load tm2_control_utils config: {e}")
            self.control_config = {}
            self.control_types = {}
        
        # Load unified config if available
        print(f"   Attempting to load unified TM2 config...")
        try:
            from unified_tm2_config import UnifiedTM2Config
            self.unified_config = UnifiedTM2Config()
            print(f"[SUCCESS] Loaded unified TM2 config")
        except Exception as e:
            print(f"[WARNING]  Cannot load unified TM2 config: {e}")
            self.warnings.append(f"[WARNING]  Cannot load unified TM2 config: {e}")
            self.unified_config = None
    
    def _define_expected_mappings(self):
        """Define expected encoding mappings based on analysis of existing code"""
        
        # Occupation mapping from create_seed_population_tm2_refactored.py
        self.occupation_seed_mapping = {
            0: "Not applicable / Unemployed",
            1: "Management (OCCP 10-950)",
            2: "Professional (OCCP 1005-3540)", 
            3: "Services (OCCP 3601-4650)",
            4: "Sales/Office (OCCP 4700-5940)",
            5: "Manual (OCCP 6005-9750)",
            6: "UNKNOWN (fallback category)"
        }
        
        # Income mapping (typical household income categories)
        self.income_seed_mapping = {
            "continuous": "Dollar amounts in seed",
            "categories": {
                "hh_inc_30": "Under $30,000",
                "hh_inc_30_60": "$30,000-$59,999", 
                "hh_inc_60_100": "$60,000-$99,999",
                "hh_inc_100_plus": "$100,000+"
            }
        }
        
        # Age categories (typical person age groups)
        self.age_seed_mapping = {
            "continuous": "Age in years in seed",
            "categories": {
                "age_0_17": "Under 18",
                "age_18_34": "18-34",
                "age_35_54": "35-54", 
                "age_55_64": "55-64",
                "age_65_plus": "65+"
            }
        }
        
        # Worker categories
        self.worker_seed_mapping = {
            0: "0 workers",
            1: "1 worker",
            2: "2 workers", 
            3: "3+ workers"
        }
        
        # Household size categories
        self.hhsize_seed_mapping = {
            1: "1 person",
            2: "2 persons",
            3: "3 persons",
            4: "4+ persons"
        }
        
        # HHGQTYPE mapping
        self.hhgqtype_seed_mapping = {
            0: "Household",
            1: "Institutional GQ",
            2: "Non-institutional GQ",
            3: "Group Quarters"
        }
    
    def load_seed_data(self):
        """Load seed population data"""
        print("\n" + "="*80)
        print("LOADING SEED POPULATION DATA")
        print("="*80)
        
        # Load seed households with optimization for large files
        hh_path = self.output_dir / "seed_households.csv"
        print(f"[SEARCH] Looking for seed households at: {hh_path}")
        try:
            print(f"   File exists: {hh_path.exists()}")
            if hh_path.exists():
                file_size = hh_path.stat().st_size / (1024*1024)  # MB
                print(f"   File size: {file_size:.1f} MB")
                
            # For large files and county filtering, use chunked loading for efficiency
            if self.test_county is not None and hh_path.exists() and file_size > 100:
                print(f"   Loading large file in chunks for county {self.test_county} filtering...")
                chunks = []
                chunk_size = 25000  # Smaller chunks for better progress
                total_processed = 0
                
                print(f"   Processing in {chunk_size:,} row chunks...")
                for i, chunk in enumerate(pd.read_csv(hh_path, chunksize=chunk_size)):
                    total_processed += len(chunk)
                    if i % 10 == 0:  # Progress every 10 chunks
                        print(f"   Processed {total_processed:,} rows...")
                        
                    if 'COUNTY' in chunk.columns:
                        filtered_chunk = chunk[chunk['COUNTY'] == self.test_county]
                        if len(filtered_chunk) > 0:
                            chunks.append(filtered_chunk)
                    else:
                        chunks.append(chunk)  # Keep all if no COUNTY column
                
                if chunks:
                    self.seed_households = pd.concat(chunks, ignore_index=True)
                    print(f"[SUCCESS] Loaded {len(self.seed_households):,} seed households (county {self.test_county} only)")
                else:
                    self.seed_households = pd.DataFrame()
                    print(f"[WARNING]  No households found for county {self.test_county}")
            else:
                # Load normally for smaller files or no filtering
                self.seed_households = pd.read_csv(hh_path)
                print(f"[SUCCESS] Loaded {len(self.seed_households):,} seed households (all counties)")
                
                # Filter by test county if specified
                if self.test_county is not None and 'COUNTY' in self.seed_households.columns:
                    original_count = len(self.seed_households)
                    self.seed_households = self.seed_households[self.seed_households['COUNTY'] == self.test_county]
                    print(f"[TARGET] Filtered to county {self.test_county}: {len(self.seed_households):,} households ({len(self.seed_households)/original_count*100:.1f}%)")
            
            print(f"   Household columns: {len(self.seed_households.columns)} total")
            
            # Show key demographic columns
            key_hh_cols = [col for col in self.seed_households.columns 
                          if col.lower() in ['county', 'puma', 'hhgqtype', 'income', 'workers', 'hhsize', 'hh_income_2023']]
            print(f"   Key household columns found: {key_hh_cols}")
            
            # Show first few column names
            print(f"   First 10 columns: {list(self.seed_households.columns[:10])}")
            
        except Exception as e:
            print(f"[ERROR] Cannot load seed households: {e}")
            self.issues.append(f"[ERROR] Cannot load seed households: {e}")
            self.seed_households = pd.DataFrame()
        
        # Load seed persons with optimization for large files
        pers_path = self.output_dir / "seed_persons.csv"
        print(f"\n[SEARCH] Looking for seed persons at: {pers_path}")
        try:
            print(f"   File exists: {pers_path.exists()}")
            if pers_path.exists():
                file_size = pers_path.stat().st_size / (1024*1024)  # MB
                print(f"   File size: {file_size:.1f} MB")
                
            # For large files and county filtering, use chunked loading for efficiency
            if self.test_county is not None and pers_path.exists() and file_size > 100:
                print(f"   Loading large file in chunks for county {self.test_county} filtering...")
                chunks = []
                chunk_size = 25000  # Smaller chunks for better progress
                total_processed = 0
                
                print(f"   Processing in {chunk_size:,} row chunks...")
                for i, chunk in enumerate(pd.read_csv(pers_path, chunksize=chunk_size)):
                    total_processed += len(chunk)
                    if i % 10 == 0:  # Progress every 10 chunks
                        print(f"   Processed {total_processed:,} rows...")
                        
                    if 'COUNTY' in chunk.columns:
                        filtered_chunk = chunk[chunk['COUNTY'] == self.test_county]
                        if len(filtered_chunk) > 0:
                            chunks.append(filtered_chunk)
                    else:
                        chunks.append(chunk)  # Keep all if no COUNTY column
                
                if chunks:
                    self.seed_persons = pd.concat(chunks, ignore_index=True)
                    print(f"[SUCCESS] Loaded {len(self.seed_persons):,} seed persons (county {self.test_county} only)")
                else:
                    self.seed_persons = pd.DataFrame()
                    print(f"[WARNING]  No persons found for county {self.test_county}")
            else:
                # Load normally for smaller files or no filtering
                self.seed_persons = pd.read_csv(pers_path)
                print(f"[SUCCESS] Loaded {len(self.seed_persons):,} seed persons (all counties)")
                
                # Filter by test county if specified
                if self.test_county is not None and 'COUNTY' in self.seed_persons.columns:
                    original_count = len(self.seed_persons)
                    self.seed_persons = self.seed_persons[self.seed_persons['COUNTY'] == self.test_county]
                    print(f"[TARGET] Filtered to county {self.test_county}: {len(self.seed_persons):,} persons ({len(self.seed_persons)/original_count*100:.1f}%)")
            
            print(f"   Person columns: {len(self.seed_persons.columns)} total")
            
            # Show key demographic columns
            key_pers_cols = [col for col in self.seed_persons.columns 
                           if col.lower() in ['county', 'puma', 'hhgqtype', 'occupation', 'agep', 'age', 'esr', 'occp']]
            print(f"   Key person columns found: {key_pers_cols}")
            
            # Show first few column names
            print(f"   First 10 columns: {list(self.seed_persons.columns[:10])}")
            
        except Exception as e:
            print(f"[ERROR] Cannot load seed persons: {e}")
            self.issues.append(f"[ERROR] Cannot load seed persons: {e}")
            self.seed_persons = pd.DataFrame()
    
    def load_control_data(self):
        """Load control/marginal data"""
        print("\n" + "="*80)
        print("LOADING CONTROL DATA")
        print("="*80)
        
        # Load MAZ marginals
        maz_path = self.output_dir / "maz_marginals.csv"
        print(f"[SEARCH] Looking for MAZ marginals at: {maz_path}")
        try:
            print(f"   File exists: {maz_path.exists()}")
            self.maz_marginals = pd.read_csv(maz_path)
            print(f"[SUCCESS] Loaded {len(self.maz_marginals):,} MAZ marginals (all counties)")
            
            # Filter by test county if specified
            if self.test_county is not None and 'COUNTY' in self.maz_marginals.columns:
                original_count = len(self.maz_marginals)
                self.maz_marginals = self.maz_marginals[self.maz_marginals['COUNTY'] == self.test_county]
                print(f"[TARGET] Filtered to county {self.test_county}: {len(self.maz_marginals):,} MAZ marginals ({len(self.maz_marginals)/original_count*100:.1f}%)")
            
            maz_control_cols = [col for col in self.maz_marginals.columns if col not in ['MAZ', 'TAZ', 'COUNTY']]
            print(f"   MAZ control columns: {len(maz_control_cols)} found")
            print(f"   Sample MAZ control columns: {maz_control_cols[:10]}")
        except Exception as e:
            print(f"[ERROR] Cannot load MAZ marginals: {e}")
            self.issues.append(f"[ERROR] Cannot load MAZ marginals: {e}")
            self.maz_marginals = pd.DataFrame()
        
        # Load TAZ marginals
        taz_path = self.output_dir / "taz_marginals.csv"
        print(f"\n[SEARCH] Looking for TAZ marginals at: {taz_path}")
        try:
            print(f"   File exists: {taz_path.exists()}")
            self.taz_marginals = pd.read_csv(taz_path)
            print(f"[SUCCESS] Loaded {len(self.taz_marginals):,} TAZ marginals (all counties)")
            
            # Filter by test county if specified
            if self.test_county is not None and 'COUNTY' in self.taz_marginals.columns:
                original_count = len(self.taz_marginals)
                self.taz_marginals = self.taz_marginals[self.taz_marginals['COUNTY'] == self.test_county]
                print(f"[TARGET] Filtered to county {self.test_county}: {len(self.taz_marginals):,} TAZ marginals ({len(self.taz_marginals)/original_count*100:.1f}%)")
            
            taz_control_cols = [col for col in self.taz_marginals.columns if col not in ['TAZ', 'COUNTY']]
            print(f"   TAZ control columns: {len(taz_control_cols)} found")
            print(f"   Sample TAZ control columns: {taz_control_cols[:10]}")
        except Exception as e:
            print(f"[ERROR] Cannot load TAZ marginals: {e}")
            self.issues.append(f"[ERROR] Cannot load TAZ marginals: {e}")
            self.taz_marginals = pd.DataFrame()
        
        # Load County marginals
        county_path = self.output_dir / "county_marginals.csv"
        print(f"\n[SEARCH] Looking for County marginals at: {county_path}")
        try:
            print(f"   File exists: {county_path.exists()}")
            self.county_marginals = pd.read_csv(county_path)
            print(f"[SUCCESS] Loaded {len(self.county_marginals):,} County marginals (all counties)") 
            
            # Filter by test county if specified
            if self.test_county is not None and 'COUNTY' in self.county_marginals.columns:
                original_count = len(self.county_marginals)
                self.county_marginals = self.county_marginals[self.county_marginals['COUNTY'] == self.test_county]
                print(f"[TARGET] Filtered to county {self.test_county}: {len(self.county_marginals):,} County marginals ({len(self.county_marginals)/original_count*100:.1f}%)")
            
            county_control_cols = [col for col in self.county_marginals.columns if col not in ['COUNTY']]
            print(f"   County control columns: {len(county_control_cols)} found")
            print(f"   Sample County control columns: {county_control_cols[:10]}")
        except Exception as e:
            print(f"[ERROR] Cannot load County marginals: {e}")
            self.issues.append(f"[ERROR] Cannot load County marginals: {e}")
            self.county_marginals = pd.DataFrame()
    
    def check_occupation_encoding(self):
        """Check occupation encoding consistency - CRITICAL for synthesis"""
        print("\n" + "="*80)
        print("1. OCCUPATION ENCODING VALIDATION")
        print("="*80)
        
        if self.seed_persons.empty:
            self.issues.append("[ERROR] No seed persons data to check occupation encoding")
            return
        
        # Check seed occupation values
        if 'occupation' in self.seed_persons.columns:
            occ_values = self.seed_persons['occupation'].value_counts().sort_index()
            print(f"Seed occupation distribution:")
            for occ, count in occ_values.items():
                pct = count / len(self.seed_persons) * 100
                desc = self.occupation_seed_mapping.get(occ, "UNKNOWN")
                print(f"  {occ}: {count:,} persons ({pct:.1f}%) - {desc}")
            
            # Check for out-of-range values
            valid_occs = set(self.occupation_seed_mapping.keys())
            invalid_occs = set(occ_values.index) - valid_occs
            if invalid_occs:
                self.issues.append(f"[ERROR] Invalid occupation codes in seed: {invalid_occs}")
        else:
            self.issues.append("[ERROR] No 'occupation' column found in seed persons")
        
        # Check control expressions for occupation
        if not self.controls_df.empty:
            # Check if 'expression' column exists
            expression_col = None
            for col in ['expression', 'expr', 'formula', 'control_expression']:
                if col in self.controls_df.columns:
                    expression_col = col
                    break
            
            if expression_col:
                occ_controls = self.controls_df[self.controls_df[expression_col].str.contains('occupation', na=False)]
                if not occ_controls.empty:
                    print(f"\nControl expressions using occupation ({len(occ_controls)} found):")
                    for _, row in occ_controls.iterrows():
                        target_col = 'target' if 'target' in row else 'control'
                        print(f"  {row.get(target_col, 'unknown')}: {row[expression_col]}")
                        
                        # Extract occupation values from expressions
                        import re
                        matches = re.findall(r'occupation\s*==\s*(\d+)', row[expression_col])
                        for match in matches:
                            occ_val = int(match)
                            if occ_val not in self.occupation_seed_mapping:
                                self.issues.append(f"[ERROR] Control {row.get(target_col, 'unknown')} uses invalid occupation {occ_val}")
            else:
                print(f"\n[WARNING]  No expression column found in controls.csv. Available columns: {list(self.controls_df.columns)}")
        else:
            print(f"\n[WARNING]  No controls.csv loaded - checking county control columns instead")
            
            # Check county control occupation columns
            if not self.county_marginals.empty:
                occ_cols = [col for col in self.county_marginals.columns if 'occ_' in col.lower()]
                print(f"Occupation control columns in county marginals: {occ_cols}")
                
                # Map control names to seed occupation codes
                expected_mapping = {
                    'pers_occ_management': 1,
                    'pers_occ_professional': 2, 
                    'pers_occ_services': 3,
                    'pers_occ_retail': 4,  # Sales/Office
                    'pers_occ_manual': 5,
                    'pers_occ_military': 5,  # Military is combined with manual in seed (code 5)
                    'pers_occ_manual_military': 5  # Combined manual+military control maps to seed code 5
                }
                
                print(f"\nOccupation control mapping analysis:")
                for col in occ_cols:
                    expected_code = expected_mapping.get(col, "UNKNOWN")
                    seed_desc = self.occupation_seed_mapping.get(expected_code, "UNKNOWN SEED CODE")
                    print(f"  {col} -> expects seed code {expected_code} ({seed_desc})")
                    
                    if expected_code == "UNKNOWN":
                        self.warnings.append(f"[WARNING]  Unexpected occupation control column: {col}")
                    elif expected_code not in self.occupation_seed_mapping:
                        self.issues.append(f"[ERROR] Control {col} expects seed occupation {expected_code} which doesn't exist in seed")
        
        # Check complex occupation control definitions
        if 'occupation' in self.control_config:
            print(f"\nComplex occupation control definitions found:")
            occ_config = self.control_config['occupation']
            for category, definition in occ_config.items():
                print(f"  {category}: {definition}")
                # This is where the mismatch likely occurs - complex hierarchical definitions
                # vs simple 1-6 numeric codes in seed
                self.warnings.append(f"[WARNING]  Complex occupation definition '{category}' may not match simple numeric seed codes")
    
    def check_income_encoding(self):
        """Check income encoding consistency"""
        print("\n" + "="*80)
        print("2. INCOME ENCODING VALIDATION")
        print("="*80)
        
        if self.seed_households.empty:
            self.issues.append("[ERROR] No seed households data to check income encoding")
            return
        
        # Check for income columns in seed
        income_cols = [col for col in self.seed_households.columns 
                      if 'income' in col.lower()]
        print(f"Income columns in seed households: {income_cols}")
        
        if income_cols:
            for col in income_cols:
                income_data = self.seed_households[col].dropna()
                if len(income_data) > 0:
                    print(f"\n{col} distribution:")
                    print(f"  Min: ${income_data.min():,.0f}")
                    print(f"  Max: ${income_data.max():,.0f}")
                    print(f"  Mean: ${income_data.mean():,.0f}")
                    print(f"  Median: ${income_data.median():,.0f}")
                    
                    # Show income ranges
                    ranges = [(0, 30000), (30000, 60000), (60000, 100000), (100000, float('inf'))]
                    for i, (min_inc, max_inc) in enumerate(ranges):
                        if max_inc == float('inf'):
                            count = len(income_data[income_data >= min_inc])
                            label = f"${min_inc:,}+"
                        else:
                            count = len(income_data[(income_data >= min_inc) & (income_data < max_inc)])
                            label = f"${min_inc:,}-${max_inc:,}"
                        pct = count / len(income_data) * 100
                        print(f"  {label}: {count:,} households ({pct:.1f}%)")
        
        # Check income controls
        if not self.taz_marginals.empty:
            income_control_cols = [col for col in self.taz_marginals.columns if 'inc' in col.lower()]
            print(f"\nIncome control columns in TAZ marginals: {income_control_cols}")
            
            if income_control_cols:
                total_controls = self.taz_marginals[income_control_cols].sum()
                print(f"Control income distribution:")
                for col in income_control_cols:
                    count = total_controls[col]
                    pct = count / total_controls.sum() * 100 if total_controls.sum() > 0 else 0
                    print(f"  {col}: {count:,.0f} ({pct:.1f}%)")
    
    def check_age_encoding(self):
        """Check age encoding consistency"""
        print("\n" + "="*80)
        print("3. AGE ENCODING VALIDATION")
        print("="*80)
        
        if self.seed_persons.empty:
            self.issues.append("[ERROR] No seed persons data to check age encoding")
            return
        
        # Check for age columns in seed
        age_cols = [col for col in self.seed_persons.columns 
                   if col.lower() in ['age', 'agep']]
        print(f"Age columns in seed persons: {age_cols}")
        
        if age_cols:
            for col in age_cols:
                age_data = self.seed_persons[col].dropna()
                if len(age_data) > 0:
                    print(f"\n{col} distribution:")
                    print(f"  Min: {age_data.min():.0f}")
                    print(f"  Max: {age_data.max():.0f}")
                    print(f"  Mean: {age_data.mean():.1f}")
                    print(f"  Median: {age_data.median():.0f}")
                    
                    # Show age ranges
                    ranges = [(0, 18), (18, 35), (35, 55), (55, 65), (65, 150)]
                    for min_age, max_age in ranges:
                        count = len(age_data[(age_data >= min_age) & (age_data < max_age)])
                        pct = count / len(age_data) * 100
                        if max_age == 150:
                            label = f"{min_age}+"
                        else:
                            label = f"{min_age}-{max_age-1}"
                        print(f"  Age {label}: {count:,} persons ({pct:.1f}%)")
        
        # Check age controls
        if not self.taz_marginals.empty:
            age_control_cols = [col for col in self.taz_marginals.columns if 'age' in col.lower()]
            print(f"\nAge control columns in TAZ marginals: {age_control_cols}")
    
    def check_puma_encoding(self):
        """Check PUMA encoding consistency"""
        print("\n" + "="*80)
        print("4. PUMA ENCODING VALIDATION")
        print("="*80)
        
        # Check PUMA in households
        if not self.seed_households.empty and 'PUMA' in self.seed_households.columns:
            puma_hh = self.seed_households['PUMA'].value_counts().sort_index()
            print(f"PUMA distribution in seed households ({len(puma_hh)} unique):")
            for puma, count in puma_hh.head(10).items():
                pct = count / len(self.seed_households) * 100
                print(f"  PUMA {puma}: {count:,} households ({pct:.1f}%)")
            if len(puma_hh) > 10:
                print(f"  ... and {len(puma_hh)-10} more PUMAs")
        
        # Check PUMA in persons  
        if not self.seed_persons.empty and 'PUMA' in self.seed_persons.columns:
            puma_pers = self.seed_persons['PUMA'].value_counts().sort_index()
            print(f"\nPUMA distribution in seed persons ({len(puma_pers)} unique):")
            for puma, count in puma_pers.head(10).items():
                pct = count / len(self.seed_persons) * 100
                print(f"  PUMA {puma}: {count:,} persons ({pct:.1f}%)")
            if len(puma_pers) > 10:
                print(f"  ... and {len(puma_pers)-10} more PUMAs")
        
        # Check against configured PUMAs
        if self.unified_config and hasattr(self.unified_config, 'BAY_AREA_PUMAS'):
            config_pumas = set(self.unified_config.BAY_AREA_PUMAS)
            if not self.seed_households.empty and 'PUMA' in self.seed_households.columns:
                # Convert seed PUMAs to same format as config (5-digit zero-padded strings)
                seed_pumas = set(self.seed_households['PUMA'].astype(str).str.zfill(5).unique())
                missing_pumas = config_pumas - seed_pumas
                extra_pumas = seed_pumas - config_pumas
                
                # Show PUMA format comparison
                print(f"\nPUMA Format Comparison:")
                sample_seed_pumas = list(self.seed_households['PUMA'].unique())[:3]
                sample_config_pumas = list(config_pumas)[:3] if config_pumas else []
                print(f"  Sample seed PUMAs (raw): {sample_seed_pumas}")
                print(f"  Sample config PUMAs: {sample_config_pumas}")
                print(f"  Sample seed PUMAs (formatted): {[str(p).zfill(5) for p in sample_seed_pumas]}")
                
                # Check PUMA consistency
                missing_in_config = seed_pumas - config_pumas
                missing_in_seed = config_pumas - seed_pumas
                
                if missing_in_config or missing_in_seed:
                    print(f"[WARNING]  PUMA MISMATCH DETECTED:")
                    if missing_in_config:
                        print(f"    PUMAs in seed but not in config: {sorted(missing_in_config)}")
                    if missing_in_seed:
                        print(f"    PUMAs in config but not in seed: {sorted(missing_in_seed)}")
                else:
                    print(f"[SUCCESS] PUMA sets match! ({len(seed_pumas)} PUMAs)")
                    
                # Show PUMA format status
                raw_seed_pumas = self.seed_households['PUMA'].unique()
                if any(isinstance(p, str) and len(str(p)) == 5 and str(p).startswith('0') for p in raw_seed_pumas):
                    print(f"[SUCCESS] Seed PUMAs are already in proper string format")
                else:
                    print(f"[WARNING]  Seed PUMAs need format conversion (currently: {type(raw_seed_pumas[0]).__name__})")
                
                print(f"   Config PUMAs (total): {len(config_pumas)} (sample: {sorted(list(config_pumas))[:5]})")
                print(f"   Seed PUMAs (filtered): {len(seed_pumas)} (sample: {sorted(list(seed_pumas))[:5]})")
                
                if missing_pumas and self.test_county is None:
                    # Only warn about missing PUMAs if not in test county mode
                    self.warnings.append(f"[WARNING]  Missing PUMAs in seed: {sorted(list(missing_pumas))[:5]}...")
                elif missing_pumas and self.test_county is not None:
                    print(f"   Note: {len(missing_pumas)} PUMAs missing (expected when testing county {self.test_county} only)")
                    print(f"   Missing PUMAs: {sorted(list(missing_pumas))[:10]}... (showing first 10)")
                    
                if extra_pumas:
                    print(f"   Warning: Unexpected PUMAs in seed: {sorted(list(extra_pumas))}")
                    if self.test_county is None:  # Only treat as warning if not in test mode
                        self.warnings.append(f"[WARNING]  Extra PUMAs in seed: {sorted(list(extra_pumas))[:5]}...")
    
    def check_county_encoding(self):
        """Check County encoding consistency"""
        print("\n" + "="*80)
        print("5. COUNTY ENCODING VALIDATION")
        print("="*80)
        
        # Check county in households
        if not self.seed_households.empty and 'COUNTY' in self.seed_households.columns:
            county_hh = self.seed_households['COUNTY'].value_counts().sort_index()
            print(f"County distribution in seed households ({len(county_hh)} unique):")
            for county, count in county_hh.items():
                pct = count / len(self.seed_households) * 100
                print(f"  County {county}: {count:,} households ({pct:.1f}%)")
        
        # Check county controls
        if not self.county_marginals.empty:
            if 'COUNTY' in self.county_marginals.columns:
                control_counties = set(self.county_marginals['COUNTY'].unique())
                print(f"\nCounties in control data: {sorted(control_counties)}")
                
                if not self.seed_households.empty and 'COUNTY' in self.seed_households.columns:
                    seed_counties = set(self.seed_households['COUNTY'].unique())
                    missing = control_counties - seed_counties
                    extra = seed_counties - control_counties
                    
                    if missing:
                        self.issues.append(f"[ERROR] Counties in controls but not seed: {missing}")
                    if extra:
                        self.issues.append(f"[ERROR] Counties in seed but not controls: {extra}")
    
    def check_household_demographics(self):
        """Check household demographic encoding (workers, size, etc.)"""
        print("\n" + "="*80)
        print("6. HOUSEHOLD DEMOGRAPHICS VALIDATION")
        print("="*80)
        
        if self.seed_households.empty:
            self.issues.append("[ERROR] No seed households data to check demographics")
            return
        
        # Check workers
        if 'hh_workers_from_esr' in self.seed_households.columns:
            workers = self.seed_households['hh_workers_from_esr'].value_counts().sort_index()
            print(f"Workers distribution in seed households:")
            for w, count in workers.items():
                pct = count / len(self.seed_households) * 100
                print(f"  {w} workers: {count:,} households ({pct:.1f}%)")
        
        # Check household size (derived from persons per household)
        if not self.seed_persons.empty and 'unique_hh_id' in self.seed_persons.columns:
            hhsize = self.seed_persons['unique_hh_id'].value_counts()
            hhsize_dist = hhsize.value_counts().sort_index()
            total_households = hhsize_dist.sum()
            print(f"\nHousehold size distribution (derived from persons):")
            for size, count in hhsize_dist.items():
                pct = count / total_households * 100
                print(f"  Size {size}: {count:,} households ({pct:.1f}%)")
        
        # Check hhgqtype
        if 'hhgqtype' in self.seed_households.columns:
            hhgq = self.seed_households['hhgqtype'].value_counts().sort_index()
            print(f"\nHHGQTYPE distribution in seed households:")
            for gq, count in hhgq.items():
                pct = count / len(self.seed_households) * 100
                desc = self.hhgqtype_seed_mapping.get(gq, "UNKNOWN")
                print(f"  {gq}: {count:,} households ({pct:.1f}%) - {desc}")
    
    def check_control_expressions(self):
        """Check control expressions for encoding issues"""
        print("\n" + "="*80)
        print("7. CONTROL EXPRESSION VALIDATION")
        print("="*80)
        
        if self.controls_df.empty:
            print("[WARNING]  No controls.csv data available - analyzing marginal column names instead")
            
            # Analyze control column patterns from marginal files
            all_control_cols = []
            
            if not self.taz_marginals.empty:
                taz_cols = [col for col in self.taz_marginals.columns if col not in ['TAZ', 'COUNTY']]
                all_control_cols.extend(taz_cols)
                print(f"TAZ control columns ({len(taz_cols)}): {taz_cols}")
            
            if not self.county_marginals.empty:
                county_cols = [col for col in self.county_marginals.columns if col not in ['COUNTY']]
                all_control_cols.extend(county_cols)
                print(f"County control columns ({len(county_cols)}): {county_cols}")
            
            if not self.maz_marginals.empty:
                maz_cols = [col for col in self.maz_marginals.columns if col not in ['MAZ', 'TAZ', 'COUNTY']]
                all_control_cols.extend(maz_cols)
                print(f"MAZ control columns ({len(maz_cols)}): {maz_cols}")
            
            # Analyze patterns
            categories = {
                'occupation': ['occ_', 'occupation'],
                'income': ['inc_', 'income'],
                'age': ['age_'],
                'workers': ['wrks_', 'workers'],
                'size': ['size_', 'hhsize'],
                'household': ['hh_', 'num_hh'],
                'population': ['pop_', 'pers_'],
                'gq': ['gq_']
            }
            
            print(f"\nControl category analysis:")
            for cat_name, patterns in categories.items():
                matching_cols = [col for col in all_control_cols 
                               if any(pattern in col.lower() for pattern in patterns)]
                if matching_cols:
                    print(f"  {cat_name.title()}: {len(matching_cols)} controls")
                    for col in matching_cols[:5]:  # Show first 5
                        print(f"    {col}")
                    if len(matching_cols) > 5:
                        print(f"    ... and {len(matching_cols)-5} more")
            
            return
        
        print(f"Analyzing {len(self.controls_df)} control expressions...")
        
        # Check if 'expression' column exists, otherwise look for similar columns
        expression_col = None
        for col in ['expression', 'expr', 'formula', 'control_expression']:
            if col in self.controls_df.columns:
                expression_col = col
                break
        
        if expression_col is None:
            print(f"[WARNING]  No expression column found. Available columns: {list(self.controls_df.columns)}")
            return
        
        # Group by geography level if available
        if 'geography' in self.controls_df.columns:
            geo_groups = self.controls_df.groupby('geography')
            for geo, group in geo_groups:
                print(f"\n{geo.upper()} level controls ({len(group)} controls):")
                
                # Check for demographic categories
                categories = {
                    'occupation': 'occupation',
                    'income': 'income|inc',
                    'age': 'age',
                    'workers': 'workers|wrks',
                    'size': 'size|hhsize',
                    'county': 'county',
                    'puma': 'puma'
                }
                
                for cat_name, pattern in categories.items():
                    cat_controls = group[group[expression_col].str.contains(pattern, case=False, na=False)]
                    if not cat_controls.empty:
                        print(f"  {cat_name.title()}: {len(cat_controls)} controls")
                        for _, row in cat_controls.head(3).iterrows():
                            target_col = 'target' if 'target' in row else row.index[0]
                            print(f"    {row.get('target', 'unknown')}: {row[expression_col]}")
                        if len(cat_controls) > 3:
                            print(f"    ... and {len(cat_controls)-3} more")
    
    def check_settings_consistency(self):
        """Check settings.yaml consistency with data"""
        print("\n" + "="*80)
        print("8. SETTINGS CONFIGURATION VALIDATION")
        print("="*80)
        
        if not self.settings:
            self.issues.append("[ERROR] No settings.yaml loaded")
            return
        
        # Check input table definitions
        if 'input_tables' in self.settings:
            print("Input table definitions:")
            for table_name, table_def in self.settings['input_tables'].items():
                print(f"  {table_name}:")
                if 'filename' in table_def:
                    print(f"    File: {table_def['filename']}")
                if 'columns' in table_def:
                    print(f"    Columns: {len(table_def['columns'])} defined")
                    
                    # Check if files exist
                    file_path = self.output_dir / table_def['filename']
                    if not file_path.exists():
                        self.issues.append(f"[ERROR] Input file not found: {table_def['filename']}")
        
        # Check output table definitions
        if 'output_tables' in self.settings:
            print(f"\nOutput table definitions: {len(self.settings['output_tables'])} tables")
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("\n" + "="*80)
        print("VALIDATION SUMMARY REPORT")
        print("="*80)
        
        print(f"\n[STATS] VALIDATION STATISTICS:")
        print(f"   Issues found: {len(self.issues)}")
        print(f"   Warnings: {len(self.warnings)}")
        
        if self.issues:
            print(f"\n[CRITICAL] CRITICAL ISSUES (must fix for PopulationSim to work):")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
        
        if self.warnings:
            print(f"\n[WARNING]  WARNINGS (potential issues):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
        
        if not self.issues and not self.warnings:
            print(f"\n[SUCCESS] NO ISSUES FOUND - Seed and control encodings appear consistent!")
        
        print(f"\n[CONFIG] RECOMMENDATIONS:")
        if self.issues:
            print(f"   1. Fix all critical issues before running PopulationSim")
            print(f"   2. Verify that seed data encoding matches control definitions exactly")
            print(f"   3. Check occupation categories - this is the most common mismatch")
            print(f"   4. Ensure income/age categories are properly binned")
        else:
            print(f"   1. Encodings look good - try running PopulationSim synthesis")
            print(f"   2. Monitor synthesis step for any remaining issues")
        
        print(f"\n[DATA] DATA SUMMARY (County {self.test_county if self.test_county else 'All'}):")
        if hasattr(self, 'seed_households') and not self.seed_households.empty:
            print(f"   Seed households: {len(self.seed_households):,}")
        if hasattr(self, 'seed_persons') and not self.seed_persons.empty:
            print(f"   Seed persons: {len(self.seed_persons):,}")
        if hasattr(self, 'maz_marginals') and not self.maz_marginals.empty:
            print(f"   MAZ controls: {len(self.maz_marginals):,}")
        if hasattr(self, 'taz_marginals') and not self.taz_marginals.empty:
            print(f"   TAZ controls: {len(self.taz_marginals):,}")
        if hasattr(self, 'county_marginals') and not self.county_marginals.empty:
            print(f"   County controls: {len(self.county_marginals):,}")

    def run_validation(self, skip_seed_loading=False):
        """Run complete validation check"""
        print("=" * 80)
        print("POPULATIONSIM SEED-TO-CONTROL ENCODING VALIDATOR")
        print("=" * 80)
        print("This script checks for encoding mismatches that cause infinite loops")
        print("in PopulationSim synthesis (Step 4).")
        if self.test_county:
            print(f"[TARGET] RUNNING IN TEST MODE - County {self.test_county} only")
        if skip_seed_loading or (hasattr(self, 'seed_households') and len(self.seed_households) == 0):
            print("[QUICK] QUICK MODE - Skipping seed data loading")
        print("=" * 80)
        
        try:
            # Load data (skip seed if in quick mode)
            if not skip_seed_loading and not (hasattr(self, 'seed_households') and len(self.seed_households) == 0):
                self.load_seed_data()
            else:
                print("\n[QUICK] Skipping seed data loading in quick mode")
                self.seed_households = pd.DataFrame()
                self.seed_persons = pd.DataFrame()
                
            self.load_control_data()
            
            # Run all validation checks
            self.check_occupation_encoding()
            self.check_income_encoding()
            self.check_age_encoding()
            self.check_puma_encoding()
            self.check_county_encoding()
            self.check_household_demographics()
            self.check_control_expressions()
            self.check_settings_consistency()
            
            # Generate final report
            self.generate_summary_report()
            
        except Exception as e:
            print(f"\n[ERROR] VALIDATION FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return len(self.issues) == 0

def main():
    """Main execution"""
    print("Starting comprehensive seed-to-control validation...")
    
    # Parse command line arguments
    test_county = None
    quick_mode = False
    
    for arg in sys.argv[1:]:
        if arg == "--quick":
            quick_mode = True
            print("[QUICK] Quick mode enabled - skipping large seed file loading")
        elif arg.startswith("--county="):
            try:
                test_county = int(arg.split("=")[1])
                print(f"Using command line test county: {test_county}")
            except ValueError:
                print(f"[WARNING]  Invalid county value: {arg}")
        elif arg.isdigit():
            try:
                test_county = int(arg)
                print(f"Using command line test county: {test_county}")
            except ValueError:
                print(f"[WARNING]  Invalid county code: {arg}, using config default")
    
    validator = SeedControlsValidator(test_county=test_county)
    
    # Skip seed loading in quick mode  
    success = validator.run_validation(skip_seed_loading=quick_mode)
    
    if success:
        print(f"\n[SUCCESS] VALIDATION PASSED - No critical issues found")
        sys.exit(0)
    else:
        print(f"\n[ERROR] VALIDATION FAILED - Critical issues must be resolved")
        sys.exit(1)

if __name__ == "__main__":
    main()
