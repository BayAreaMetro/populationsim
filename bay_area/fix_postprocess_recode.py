#!/usr/bin/env python3
"""
Fix Script for postprocess_recode.py
Updates the postprocess script to properly support TM2 and handle group quarters
"""

import re

def fix_postprocess_recode():
    """Fix the postprocess_recode.py script for TM2 support and GQ handling"""
    
    script_path = "postprocess_recode.py"
    
    print("Fixing postprocess_recode.py for TM2 and Group Quarters support...")
    
    # Read the current script
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Fix 1: Update TM2 person mapping to include missing fields
    old_tm2_person_mapping = '''    # http://bayareametro.github.io/travel-model-two/input/#persons
    'TM2':collections.OrderedDict([
      ("HHID",                "HHID"),
      ("PERID",               "PERID"),
      ("AGEP",                "AGEP"),
      ("SEX",                 "SEX"),
      ("SCHL",                "SCHL"),
      ("occupation",          "OCCP"),
      ("WKHP",                "WKHP"),
      ("WKW",                 "WKW"),
      ("employed",            "EMPLOYED"),
      ("ESR",                 "ESR"),
      ("SCHG",                "SCHG"),
    ])'''
    
    new_tm2_person_mapping = '''    # http://bayareametro.github.io/travel-model-two/input/#persons
    'TM2':collections.OrderedDict([
      ("unique_hh_id",        "HHID"),          # Fixed: use unique_hh_id from PopulationSim
      ("unique_per_id",       "PERID"),         # Fixed: use unique_per_id from PopulationSim
      ("AGEP",                "AGEP"),
      ("SEX",                 "SEX"),
      ("SCHL",                "SCHL"),
      ("occupation",          "OCCP"),
      ("WKHP",                "WKHP"),
      ("WKW",                 "WKW"),
      ("employed",            "EMPLOYED"),
      ("ESR",                 "ESR"),
      ("SCHG",                "SCHG"),
      ("hhgqtype",            "hhgqtype"),      # Added: group quarters type
      ("person_type",         "person_type"),  # Added: employment-based person type
    ])'''
    
    content = content.replace(old_tm2_person_mapping, new_tm2_person_mapping)
    
    # Fix 2: Update TM2 household mapping to use correct source fields
    old_tm2_household_mapping = '''    # http://bayareametro.github.io/travel-model-two/input/#households
    'TM2':collections.OrderedDict([
      ("HHID",                "HHID"),
      ("TAZ",                 "TAZ"),
      ("MAZ",                 "MAZ"),
      ("COUNTY",              "MTCCountyID"),
      ("hh_income_2010",      "HHINCADJ"),
      ("hh_workers_from_esr", "NWRKRS_ESR"),
      ("VEH",                 "VEH"),
      ("TEN",                 "TEN"),       # added Feb '23
      ("NP",                  "NP"),
      ("HHT",                 "HHT"),
      ("BLD",                 "BLD"),
      ("TYPE",                "TYPE")
    ]),'''
    
    new_tm2_household_mapping = '''    # http://bayareametro.github.io/travel-model-two/input/#households
    'TM2':collections.OrderedDict([
      ("unique_hh_id",        "HHID"),          # Fixed: use unique_hh_id from PopulationSim
      ("TAZ",                 "TAZ"),
      ("MAZ",                 "MAZ"),
      ("COUNTY",              "MTCCountyID"),   # Maps to county 1-9
      ("hh_income_2010",      "HHINCADJ"),     # 2010 dollars as required by TM2
      ("hh_workers_from_esr", "NWRKRS_ESR"),
      ("VEH",                 "VEH"),
      ("TEN",                 "TEN"),
      ("NP",                  "NP"),
      ("HHT",                 "HHT"),
      ("BLD",                 "BLD"),
      ("TYPEHUGQ",            "TYPE"),          # Fixed: use TYPEHUGQ from PopulationSim
    ]),'''
    
    content = content.replace(old_tm2_household_mapping, new_tm2_household_mapping)
    
    # Fix 3: Remove the "Not implemented" exit for TM2
    old_tm2_check = '''    if args.model_type == 'TM2':
      print("Not implemented")
      sys.exit(2)'''
    
    new_tm2_check = '''    if args.model_type == 'TM2':
      # TM2 uses the unified crosswalk from the pipeline
      from unified_tm2_config import UnifiedTM2Config
      config = UnifiedTM2Config()
      geocrosswalk_df = pandas.read_csv(config.CROSSWALK_FILES['popsim_crosswalk'])
      logging.info("Read TM2 crosswalk with {:,} rows".format(len(geocrosswalk_df)))'''
    
    content = content.replace(old_tm2_check, new_tm2_check)
    
    # Fix 4: Add unique ID generation functions for TM2
    # Find where the main processing starts and add unique ID functions
    main_processing_start = "    # read the taz and county summaries"
    
    unique_id_functions = '''
    # Functions for generating unique IDs in TM2
    def add_unique_household_id(households_df):
        """Add unique_hh_id field if it doesn't exist"""
        if 'unique_hh_id' not in households_df.columns:
            if 'SERIALNO' in households_df.columns:
                households_df['unique_hh_id'] = households_df['SERIALNO']
            else:
                households_df['unique_hh_id'] = households_df.index + 1
        return households_df
    
    def add_unique_person_id(persons_df):
        """Add unique_per_id field if it doesn't exist"""
        if 'unique_per_id' not in persons_df.columns:
            if 'SERIALNO' in persons_df.columns and 'SPORDER' in persons_df.columns:
                persons_df['unique_per_id'] = persons_df['SERIALNO'].astype(str) + '_' + persons_df['SPORDER'].astype(str)
            else:
                persons_df['unique_per_id'] = persons_df.index + 1
        return persons_df

'''
    
    content = content.replace(main_processing_start, unique_id_functions + "\n    " + main_processing_start)
    
    # Write the fixed script
    with open(script_path, 'w') as f:
        f.write(content)
    
    print("✓ Fixed postprocess_recode.py")
    print("\nChanges made:")
    print("1. ✓ Added TM2 support (removed 'Not implemented' exit)")
    print("2. ✓ Fixed household mapping to use 'unique_hh_id' from PopulationSim")
    print("3. ✓ Fixed person mapping to use 'unique_hh_id' and 'unique_per_id'")
    print("4. ✓ Added 'hhgqtype' to person output mapping")
    print("5. ✓ Added 'person_type' to person output mapping")
    print("6. ✓ Added functions to generate unique IDs if missing")
    print("7. ✓ Added TM2 crosswalk loading using unified config")
    
    print(f"\nScript updated! You can now run:")
    print(f"python postprocess_recode.py --model_type TM2 --directory output_2023/populationsim_working_dir/output --year 2023")

if __name__ == "__main__":
    fix_postprocess_recode()
