def print_column_summary(jobs, maz_data, maz_density):
    jobs_cols = set(jobs.columns)
    maz_data_cols = set(maz_data.columns)
    maz_density_cols = set(maz_density.columns)

    print("\n--- COLUMN SUMMARY ---")
    print(f"jobs_maz_2023_v1.csv columns: {sorted(jobs_cols)}")
    print(f"maz_data.csv columns: {sorted(maz_data_cols)}")
    print(f"maz_data_withDensity.csv columns: {sorted(maz_density_cols)}")

    # Columns in all three
    all_three = jobs_cols & maz_data_cols & maz_density_cols    # Fix serv_per -> serv_pers column naming issue
    print("\n=== FIXING EMPLOYMENT COLUMN NAMING ===")
    if 'serv_per' in jobs.columns:
        print("✅ Found serv_per column - copying to serv_pers and dropping serv_per")
        jobs['serv_pers'] = jobs['serv_per']
        jobs = jobs.drop(columns=['serv_per'])
        print("✅ serv_pers now contains serv_per data, serv_per column dropped")
    elif 'serv_pers' in jobs.columns:
        print("✅ serv_pers column already exists (no serv_per found)")
    else:
        print("⚠️ Neither serv_per nor serv_pers found in jobs data")(f"\nColumns in ALL THREE files: {sorted(all_three)}")

    # Pairwise intersections
    jobs_maz_data = jobs_cols & maz_data_cols
    jobs_maz_density = jobs_cols & maz_density_cols
    maz_data_maz_density = maz_data_cols & maz_density_cols

    print(f"\nColumns in BOTH jobs_maz_2023_v1.csv and maz_data.csv: {sorted(jobs_maz_data)}")
    print(f"Columns in BOTH jobs_maz_2023_v1.csv and maz_data_withDensity.csv: {sorted(jobs_maz_density)}")
    print(f"Columns in BOTH maz_data.csv and maz_data_withDensity.csv: {sorted(maz_data_maz_density)}")

    # Unique columns
    print(f"\nColumns UNIQUE to jobs_maz_2023_v1.csv: {sorted(jobs_cols - maz_data_cols - maz_density_cols)}")
    print(f"Columns UNIQUE to maz_data.csv: {sorted(maz_data_cols - jobs_cols - maz_density_cols)}")
    print(f"Columns UNIQUE to maz_data_withDensity.csv: {sorted(maz_density_cols - jobs_cols - maz_data_cols)}")

def check_employment_consistency(df, filename, emp_subcategories):
    """Check and log employment data consistency issues that cause ExplicitTelecommute crashes"""
    print(f"\n--- EMPLOYMENT CONSISTENCY CHECK: {filename} ---")
    
    # Check which employment columns are actually present
    available_emp_cols = [col for col in emp_subcategories if col in df.columns]
    missing_emp_cols = [col for col in emp_subcategories if col not in df.columns]
    
    print(f"Available employment subcategories ({len(available_emp_cols)}): {available_emp_cols}")
    if missing_emp_cols:
        print(f"⚠️ Missing employment subcategories ({len(missing_emp_cols)}): {missing_emp_cols}")
    
    if not available_emp_cols:
        print("❌ ERROR: No employment subcategories found for consistency check")
        return df, 0, 0
    
    if 'emp_total' not in df.columns:
        print("❌ ERROR: emp_total column not found")
        return df, 0, 0
    
    # Calculate sum of subcategories
    df['emp_sum_calculated'] = df[available_emp_cols].sum(axis=1)
    
    # Find mismatches
    tolerance = 0.01  # Allow small floating point differences
    mismatches = abs(df['emp_total'] - df['emp_sum_calculated']) > tolerance
    n_mismatches = mismatches.sum()
    
    print(f"Employment total mismatches: {n_mismatches:,} / {len(df):,} ({100*n_mismatches/len(df):.2f}%)")
    
    if n_mismatches > 0:
        print("⚠️ CRITICAL: Employment mismatches found - this causes ExplicitTelecommute crashes!")
        
        # Find problematic cases
        mismatch_df = df[mismatches].copy()
        mismatch_df['emp_diff'] = mismatch_df['emp_total'] - mismatch_df['emp_sum_calculated']
        
        # Cases where emp_total = 0 but subcategories > 0 (division by zero in telecommute model)
        zero_total_nonzero_subs = mismatch_df[(mismatch_df['emp_total'] == 0) & (mismatch_df['emp_sum_calculated'] > 0)]
        if len(zero_total_nonzero_subs) > 0:
            print(f"❌ CRITICAL: {len(zero_total_nonzero_subs)} MAZs have emp_total=0 but subcategories>0")
            print("   This causes division by zero in ExplicitTelecommute model!")
            maz_col = 'MAZ' if 'MAZ' in zero_total_nonzero_subs.columns else 'maz'
            if maz_col in zero_total_nonzero_subs.columns:
                sample_mazs = zero_total_nonzero_subs[maz_col].head(10).tolist()
                print(f"   Sample problematic MAZs: {sample_mazs}")
        
        # Show worst mismatches
        print("Top 5 largest positive differences (emp_total > emp_sum):")
        maz_col = 'MAZ' if 'MAZ' in mismatch_df.columns else 'maz'
        cols_to_show = [maz_col, 'emp_total', 'emp_sum_calculated', 'emp_diff'] if maz_col in mismatch_df.columns else ['emp_total', 'emp_sum_calculated', 'emp_diff']
        print(mismatch_df.nlargest(5, 'emp_diff')[cols_to_show])
        
        print("Top 5 largest negative differences (emp_total < emp_sum):")
        print(mismatch_df.nsmallest(5, 'emp_diff')[cols_to_show])
    
    # Fix employment totals
    old_total = df['emp_total'].sum()
    df['emp_total'] = df['emp_sum_calculated']
    new_total = df['emp_total'].sum()
    
    print(f"✅ Fixed emp_total: {old_total:,.0f} -> {new_total:,.0f}")
    print(f"   Using {len(available_emp_cols)} employment subcategories")
    
    # Clean up temporary column
    df = df.drop('emp_sum_calculated', axis=1)
    
    return df, n_mismatches, len(zero_total_nonzero_subs) if 'zero_total_nonzero_subs' in locals() else 0

def validate_telecommute_safety(df, filename):
    """Validate that the data won't cause ExplicitTelecommute crashes"""
    print(f"\n--- TELECOMMUTE CRASH VALIDATION: {filename} ---")
    
    # CRITICAL FIX: Include serv_pers instead of serv_per to match UEC expressions
    emp_subcategories = ['ag', 'art_rec', 'constr', 'eat', 'ed_high', 'ed_k12', 'ed_oth', 'fire', 'gov', 'health',
                        'hotel', 'info', 'lease', 'logis', 'man_bio', 'man_hvy', 'man_lgt', 'man_tech', 'natres', 
                        'prof', 'ret_loc', 'ret_reg', 'serv_bus', 'serv_pers', 'serv_soc', 'transp', 'util']
    
    available_emp_cols = [col for col in emp_subcategories if col in df.columns]
    
    if not available_emp_cols or 'emp_total' not in df.columns:
        print("❌ Cannot validate - missing employment columns")
        return False
    
    # Calculate what empTotal would be in the UEC expressions
    df_temp = df.copy()
    df_temp['emp_sum_for_validation'] = df_temp[available_emp_cols].sum(axis=1)
    
    # Find cases where sum of subcategories > 0 but would cause division by zero
    # (This is what the UEC expressions calculate as empTotal)
    problematic = df_temp[df_temp['emp_sum_for_validation'] == 0]
    has_employment_but_zero_total = df_temp[
        (df_temp[available_emp_cols] > 0).any(axis=1) & 
        (df_temp['emp_sum_for_validation'] == 0)
    ]
    
    print(f"MAZs with zero calculated empTotal: {len(problematic):,}")
    print(f"MAZs with employment but zero total (would crash): {len(has_employment_but_zero_total):,}")
    
    # Verify emp_total matches sum of subcategories
    total_mismatch = abs(df_temp['emp_total'] - df_temp['emp_sum_for_validation']) > 0.01
    
    if total_mismatch.sum() == 0:
        print("✅ PASS: emp_total matches sum of subcategories")
    else:
        print(f"❌ FAIL: {total_mismatch.sum():,} MAZs still have emp_total mismatches")
        return False
    
    if len(has_employment_but_zero_total) == 0:
        print("✅ PASS: No MAZs would cause ExplicitTelecommute division by zero crashes")
        return True
    else:
        print(f"❌ FAIL: {len(has_employment_but_zero_total):,} MAZs would still cause crashes")
        return False

def check_coordinate_validity(df, filename):
    """Check and fix coordinate issues that could cause Stop Location Choice crashes"""
    print(f"\n--- COORDINATE VALIDATION: {filename} ---")
    
    coord_issues = 0
    
    # Check for coordinate columns
    coord_x_col = None
    coord_y_col = None
    
    for col in df.columns:
        if 'MAZ_X' in col.upper():
            coord_x_col = col
        elif 'MAZ_Y' in col.upper():
            coord_y_col = col
        elif '_X' in col.upper() and not coord_x_col:
            coord_x_col = col
        elif '_Y' in col.upper() and not coord_y_col:
            coord_y_col = col
    
    if not coord_x_col or not coord_y_col:
        print(f"⚠️ No coordinate columns found (looked for MAZ_X/MAZ_Y or _X/_Y)")
        return 0
    
    print(f"Using coordinate columns: {coord_x_col}, {coord_y_col}")
    
    # Check for invalid coordinates (-1, -1)
    invalid_x = (df[coord_x_col] == -1).sum()
    invalid_y = (df[coord_y_col] == -1).sum()
    invalid_both = ((df[coord_x_col] == -1) | (df[coord_y_col] == -1)).sum()
    
    print(f"MAZs with invalid coordinates (-1): {invalid_both:,} / {len(df):,}")
    
    if invalid_both > 0:
        # Check impact on stop alternatives
        should_be_available = (df['emp_total'] > 0) | (df['HH'] > 0) if 'HH' in df.columns else (df['emp_total'] > 0)
        invalid_coords_mask = (df[coord_x_col] == -1) | (df[coord_y_col] == -1)
        
        stop_alternatives_with_invalid_coords = should_be_available & invalid_coords_mask
        affected_stops = stop_alternatives_with_invalid_coords.sum()
        
        print(f"⚠️ CRITICAL: {affected_stops:,} potential stop locations have invalid coordinates!")
        print("   This could cause Stop Location Choice distance calculations to fail")
        
        if affected_stops > 0:
            # Show sample of affected MAZs
            problematic = df[stop_alternatives_with_invalid_coords]
            maz_col = 'MAZ' if 'MAZ' in problematic.columns else 'maz'
            
            if maz_col in problematic.columns:
                sample_cols = [maz_col, 'emp_total']
                if 'HH' in problematic.columns:
                    sample_cols.append('HH')
                sample_cols.extend([coord_x_col, coord_y_col])
                
                print(f"\nSample MAZs with invalid coordinates but employment/households:")
                print(problematic[sample_cols].head(10))
            
            # For now, we'll mark these as unavailable for stops
            # by setting both emp_total and HH to 0 if coordinates are invalid
            print(f"\n🔧 APPLYING FIX: Setting emp_total=0 and HH=0 for MAZs with invalid coordinates")
            print("   This prevents them from being selected as stop alternatives")
            
            # Apply the fix
            invalid_mask = (df[coord_x_col] == -1) | (df[coord_y_col] == -1)
            
            # Count what we're fixing
            emp_zeroed = (df.loc[invalid_mask, 'emp_total'] > 0).sum()
            hh_zeroed = (df.loc[invalid_mask, 'HH'] > 0).sum() if 'HH' in df.columns else 0
            
            # Zero out employment and households for MAZs with invalid coordinates
            df.loc[invalid_mask, 'emp_total'] = 0
            if 'HH' in df.columns:
                df.loc[invalid_mask, 'HH'] = 0
            
            # Also zero out all employment subcategories
            emp_subcategories = ['ag', 'art_rec', 'constr', 'eat', 'ed_high', 'ed_k12', 'ed_oth', 'fire', 'gov', 'health',
                                'hotel', 'info', 'lease', 'logis', 'man_bio', 'man_hvy', 'man_lgt', 'man_tech', 'natres', 
                                'prof', 'ret_loc', 'ret_reg', 'serv_bus', 'serv_pers', 'serv_soc', 'transp', 'util']
            
            emp_cols_zeroed = 0
            for emp_col in emp_subcategories:
                if emp_col in df.columns:
                    emp_cols_zeroed += (df.loc[invalid_mask, emp_col] > 0).sum()
                    df.loc[invalid_mask, emp_col] = 0
            
            print(f"✅ Fixed {invalid_both:,} MAZs with invalid coordinates:")
            print(f"   - Zeroed emp_total for {emp_zeroed:,} MAZs")
            print(f"   - Zeroed HH for {hh_zeroed:,} MAZs")
            print(f"   - Zeroed employment subcategories for {emp_cols_zeroed:,} entries")
            print("   - These MAZs will now be excluded from stop location choice sets")
            
            coord_issues = invalid_both
    else:
        print("✅ All MAZs have valid coordinates")
    
    # Check coordinate ranges for remaining valid coordinates
    valid_coords = df[(df[coord_x_col] != -1) & (df[coord_y_col] != -1)]
    
    if len(valid_coords) > 0:
        print(f"\nValid coordinates summary:")
        print(f"  X range: {valid_coords[coord_x_col].min():.3f} to {valid_coords[coord_x_col].max():.3f}")
        print(f"  Y range: {valid_coords[coord_y_col].min():.3f} to {valid_coords[coord_y_col].max():.3f}")
        
        # Check for extreme outliers that might cause distance calculation issues
        x_std = valid_coords[coord_x_col].std()
        y_std = valid_coords[coord_y_col].std()
        x_mean = valid_coords[coord_x_col].mean()
        y_mean = valid_coords[coord_y_col].mean()
        
        # Flag coordinates more than 5 standard deviations from mean
        extreme_x = abs(valid_coords[coord_x_col] - x_mean) > 5 * x_std
        extreme_y = abs(valid_coords[coord_y_col] - y_mean) > 5 * y_std
        extreme_coords = (extreme_x | extreme_y).sum()
        
        if extreme_coords > 0:
            print(f"⚠️ {extreme_coords:,} MAZs have extreme coordinates (>5σ from mean)")
        else:
            print("✅ No extreme coordinate outliers detected")
    
    return coord_issues

def check_density_consistency(df, filename):
    """Check density field consistency"""
    print(f"\n--- DENSITY CONSISTENCY CHECK: {filename} ---")
    
    density_issues = 0
    
    # Check EmpDen >= RetEmpDen
    if 'EmpDen' in df.columns and 'RetEmpDen' in df.columns:
        invalid_density = df['EmpDen'] < df['RetEmpDen']
        n_invalid = invalid_density.sum()
        
        print(f"EmpDen < RetEmpDen violations: {n_invalid:,} / {len(df):,} ({100*n_invalid/len(df):.2f}%)")
        
        if n_invalid > 0:
            print("⚠️ WARNING: Employment density less than retail employment density found")
            invalid_df = df[invalid_density].copy()
            invalid_df['density_diff'] = invalid_df['EmpDen'] - invalid_df['RetEmpDen']
            
            maz_col = 'MAZ' if 'MAZ' in invalid_df.columns else 'maz'
            cols_to_show = [maz_col, 'EmpDen', 'RetEmpDen', 'density_diff'] if maz_col in invalid_df.columns else ['EmpDen', 'RetEmpDen', 'density_diff']
            
            print("Top 5 worst violations (most negative EmpDen - RetEmpDen):")
            print(invalid_df.nsmallest(5, 'density_diff')[cols_to_show])
            
            density_issues += n_invalid
    else:
        print("EmpDen and/or RetEmpDen columns not found - skipping density consistency check")
    
    return density_issues

def check_population_synthesis_compatibility():
    """Check and fix compatibility issues between population synthesis and land use data"""
    print(f"\n--- POPULATION SYNTHESIS COMPATIBILITY CHECK ---")
    
    # Load population synthesis files to check for compatibility issues
    popsyn_dir = r"E:\TM2_2023_LU_Test3\inputs\popsyn"
    landuse_path = OUTPUT_MAZ_DENSITY  # Use our updated land use file
    
    try:
        # Load our updated land use data
        if not os.path.exists(landuse_path):
            print(f"⚠️ Updated land use file not found: {landuse_path}")
            print("   Skipping population synthesis compatibility check")
            return 0
            
        landuse_df = pd.read_csv(landuse_path)
        print(f"Loaded updated land use data: {len(landuse_df):,} MAZ records")
        
        # Get valid MAZ IDs from land use data
        if 'MAZ_ORIGINAL' in landuse_df.columns:
            valid_maz_original = set(landuse_df['MAZ_ORIGINAL'].dropna())
            print(f"Valid MAZ_ORIGINAL IDs: {len(valid_maz_original):,}")
        else:
            print("⚠️ No MAZ_ORIGINAL column in land use data - cannot check compatibility")
            return 0
        
        # Check population synthesis files
        if not os.path.exists(popsyn_dir):
            print(f"⚠️ Population synthesis directory not found: {popsyn_dir}")
            return 0
            
        popsyn_files = [f for f in os.listdir(popsyn_dir) if f.endswith('.csv') and 'household' in f.lower()]
        
        total_issues_fixed = 0
        
        for popsyn_file in popsyn_files:
            if 'dummy' in popsyn_file.lower():
                continue  # Skip dummy files
                
            popsyn_path = os.path.join(popsyn_dir, popsyn_file)
            print(f"\n--- Checking {popsyn_file} ---")
            
            try:
                # Load population synthesis file
                popsyn_df = pd.read_csv(popsyn_path)
                print(f"Loaded {len(popsyn_df):,} household records")
                
                # Check for MAZ_ORIGINAL compatibility
                if 'MAZ_ORIGINAL' in popsyn_df.columns:
                    popsyn_maz_original = set(popsyn_df['MAZ_ORIGINAL'].dropna())
                    
                    # Find mismatched MAZ_ORIGINAL IDs
                    missing_in_landuse = popsyn_maz_original - valid_maz_original
                    
                    if missing_in_landuse:
                        print(f"❌ {len(missing_in_landuse):,} MAZ_ORIGINAL IDs in {popsyn_file} not found in land use data")
                        print(f"   Sample missing IDs: {sorted(list(missing_in_landuse))[:10]}")
                        
                        # Check if households are using these problematic MAZ_ORIGINAL values
                        problematic_households = popsyn_df[popsyn_df['MAZ_ORIGINAL'].isin(missing_in_landuse)]
                        
                        if len(problematic_households) > 0:
                            print(f"   {len(problematic_households):,} households affected")
                            
                            # Strategy: Map problematic MAZ_ORIGINAL to nearby valid MAZ_ORIGINAL
                            # For now, we'll flag this as needing manual review
                            print(f"⚠️  MANUAL REVIEW NEEDED: These households reference non-existent MAZ_ORIGINAL IDs")
                            print("   Suggested fixes:")
                            print("   1. Update population synthesis to use current MAZ_ORIGINAL IDs")
                            print("   2. Create MAZ ID mapping table (old -> new)")
                            print("   3. Remove/relocate affected households")
                            
                            total_issues_fixed += len(problematic_households)
                    else:
                        print(f"✅ All MAZ_ORIGINAL IDs in {popsyn_file} exist in land use data")
                
                # Check regular MAZ compatibility (should be fine since we saw this works)
                if 'MAZ' in popsyn_df.columns:
                    valid_maz = set(landuse_df['MAZ'].dropna()) if 'MAZ' in landuse_df.columns else set()
                    popsyn_maz = set(popsyn_df['MAZ'].dropna())
                    
                    missing_maz = popsyn_maz - valid_maz
                    if missing_maz:
                        print(f"❌ {len(missing_maz):,} MAZ IDs in {popsyn_file} not found in land use data")
                        total_issues_fixed += len(popsyn_df[popsyn_df['MAZ'].isin(missing_maz)])
                    else:
                        print(f"✅ All MAZ IDs in {popsyn_file} exist in land use data")
                
            except Exception as e:
                print(f"❌ Error checking {popsyn_file}: {e}")
        
        if total_issues_fixed > 0:
            print(f"\n⚠️ POPULATION SYNTHESIS ISSUES FOUND:")
            print(f"   - {total_issues_fixed:,} household records reference non-existent MAZ IDs")
            print(f"   - These could cause model crashes when households try to make tours")
            print(f"   - RECOMMENDATION: Update population synthesis files before running model")
        else:
            print(f"\n✅ Population synthesis files are compatible with land use data")
        
        return total_issues_fixed
        
    except Exception as e:
        print(f"❌ Error checking population synthesis compatibility: {e}")
        import traceback
        traceback.print_exc()
        return 0

def create_maz_id_mapping_report():
    """Create a report of MAZ ID mappings for troubleshooting"""
    print(f"\n--- CREATING MAZ ID MAPPING REPORT ---")
    
    try:
        # Load coordinate reference file
        coord_file = COORD_FILE
        if not os.path.exists(coord_file):
            print(f"⚠️ Coordinate file not found: {coord_file}")
            return
            
        coords_df = pd.read_csv(coord_file)
        
        # Load our updated land use file
        landuse_path = OUTPUT_MAZ_DENSITY
        if not os.path.exists(landuse_path):
            print(f"⚠️ Updated land use file not found: {landuse_path}")
            return
            
        landuse_df = pd.read_csv(landuse_path)
        
        # Create mapping report
        mapping_report_path = os.path.join(TARGET_DIR, "maz_id_mapping_report.csv")
        
        # Combine coordinate and land use data to show MAZ ID relationships
        if 'MAZ' in coords_df.columns and 'MAZ_ORIGINAL' in landuse_df.columns:
            mapping_df = pd.merge(
                coords_df[['MAZ', 'TAZ', 'MAZ_X', 'MAZ_Y']],
                landuse_df[['MAZ', 'MAZ_ORIGINAL', 'TAZ', 'emp_total', 'HH']],
                left_on='MAZ',
                right_on='MAZ_ORIGINAL',
                how='outer',
                suffixes=('_coord', '_landuse')
            )
            
            # Add status flags
            mapping_df['in_coordinates'] = mapping_df['MAZ'].notna()
            mapping_df['in_landuse'] = mapping_df['MAZ_ORIGINAL'].notna()
            mapping_df['status'] = 'unknown'
            
            mapping_df.loc[mapping_df['in_coordinates'] & mapping_df['in_landuse'], 'status'] = 'matched'
            mapping_df.loc[mapping_df['in_coordinates'] & ~mapping_df['in_landuse'], 'status'] = 'coord_only'
            mapping_df.loc[~mapping_df['in_coordinates'] & mapping_df['in_landuse'], 'status'] = 'landuse_only'
            
            # Save report
            mapping_df.to_csv(mapping_report_path, index=False)
            
            # Print summary
            status_counts = mapping_df['status'].value_counts()
            print(f"MAZ ID mapping report saved: {mapping_report_path}")
            print("Status summary:")
            for status, count in status_counts.items():
                print(f"  {status}: {count:,}")
            
        else:
            print("⚠️ Cannot create mapping report - missing required columns")
            
    except Exception as e:
        print(f"❌ Error creating MAZ ID mapping report: {e}")

# This is how we are supposed to do this: https://github.com/BayAreaMetro/travel-model-two/blob/master/model-files/scripts/preprocess/createMazDensityFile.py

import os
import pandas as pd

# Paths to files
TARGET_DIR = r"C:\Box\Modeling and Surveys\Development\Travel Model Two Conversion\Model Inputs\2023-tm22-dev-version-05\landuse"
JOBS_FILE = os.path.join(TARGET_DIR, "jobs_maz_2023_v1.csv")
MAZ_DATA_FILE = os.path.join(TARGET_DIR, "maz_data.csv")
MAZ_DENSITY_FILE = os.path.join(TARGET_DIR, "maz_data_withDensity.csv")
COORD_FILE = r"C:\GitHub\tm2py-utils\tm2py_utils\inputs\maz_taz\mazs_tazs_county_tract_PUMA_2.5.csv"
OUTPUT_MAZ_DATA = os.path.join(TARGET_DIR, "maz_data_UPDATED.csv")
OUTPUT_MAZ_DENSITY = os.path.join(TARGET_DIR, "maz_data_withDensity_UPDATED.csv")

# Columns to update from jobs file (customize as needed)
JOBS_MAZ_COL = "maz"

def load_csv(path):
    try:
        df = pd.read_csv(path)
        return df
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None

def merge_and_update():
    # ...existing code...
    # Print column summary
    
    # Load data
    jobs = load_csv(JOBS_FILE)
    maz_data = load_csv(MAZ_DATA_FILE)
    maz_density = load_csv(MAZ_DENSITY_FILE)
    coords = load_csv(COORD_FILE)
    
    # Detect MAZ column naming convention
    MAZ_DATA_MAZ_COL = None
    if 'MAZ_NODE' in maz_data.columns:
        MAZ_DATA_MAZ_COL = 'MAZ_NODE'
    elif 'MAZ_ORIGINAL' in maz_data.columns:
        MAZ_DATA_MAZ_COL = 'MAZ_ORIGINAL'
    else:
        print("ERROR: Cannot find MAZ_NODE or MAZ_ORIGINAL in maz_data.csv")
        return
    
    MAZ_DENSITY_MAZ_COL = None
    if 'MAZ_NODE' in maz_density.columns:
        MAZ_DENSITY_MAZ_COL = 'MAZ_NODE'
    elif 'MAZ_ORIGINAL' in maz_density.columns:
        MAZ_DENSITY_MAZ_COL = 'MAZ_ORIGINAL'
    elif 'MAZ' in maz_density.columns:
        MAZ_DENSITY_MAZ_COL = 'MAZ'
    else:
        print("ERROR: Cannot find MAZ_NODE, MAZ_ORIGINAL, or MAZ in maz_data_withDensity.csv")
        return
    
    print(f"Using MAZ columns: maz_data={MAZ_DATA_MAZ_COL}, maz_density={MAZ_DENSITY_MAZ_COL}")

    print_column_summary(jobs, maz_data, maz_density)

    if jobs is None or maz_data is None or maz_density is None:
        print("\nOne or more input files could not be loaded. Exiting script.")
        return
        
    if coords is None:
        print("\nWarning: Coordinate file could not be loaded. Proceeding without coordinates.")
    else:
        print(f"\nLoaded coordinate data: {len(coords)} rows")
        print(f"Coordinate file columns: {sorted(coords.columns)}")

    # Fix serv_per -> serv_pers column naming issue
    print("\n=== FIXING EMPLOYMENT COLUMN NAMING ===")
    if 'serv_per' in jobs.columns and 'serv_pers' not in jobs.columns:
        print("✅ Copying serv_per data to serv_pers column")
        jobs['serv_pers'] = jobs['serv_per']
        jobs = jobs.drop(columns=['serv_per'])
        print("✅ Dropped serv_per column")
    elif 'serv_per' in jobs.columns and 'serv_pers' in jobs.columns:
        print("⚠️  Both serv_per and serv_pers exist - merging data")
        jobs['serv_pers'] = jobs['serv_pers'] + jobs['serv_per']
        jobs = jobs.drop(columns=['serv_per'])
        print("✅ Merged serv_per into serv_pers and dropped serv_per")
    elif 'serv_pers' in jobs.columns:
        print("✅ serv_pers column already exists correctly")
    else:
        print("⚠️  Neither serv_per nor serv_pers found in jobs data")

    # Identify job columns to merge (all except maz)
    job_cols = [col for col in jobs.columns if col != JOBS_MAZ_COL]

    # Print column summary
    print_column_summary(jobs, maz_data, maz_density)

    # --- Update maz_data.csv ---
    maz_data_merged = pd.merge(
        maz_data,
        jobs,
        left_on=MAZ_DATA_MAZ_COL,
        right_on=JOBS_MAZ_COL,
        how="right"  # include all jobs MAZs
    )
    # Zero out columns from maz_data that are NaN due to new MAZs
    for col in maz_data.columns:
        if col != MAZ_DATA_MAZ_COL and col in maz_data_merged.columns:
            maz_data_merged[col] = maz_data_merged[col].fillna(0)


    # Keep jobs columns in case of conflict: drop _x, rename _y to original
    cols_to_drop = [col for col in maz_data_merged.columns if col.endswith('_x') and col[:-2] + '_y' in maz_data_merged.columns]
    maz_data_merged = maz_data_merged.drop(columns=cols_to_drop)
    maz_data_merged.columns = [col[:-2] if col.endswith('_y') else col for col in maz_data_merged.columns]

    # --- Add coordinates to maz_data if missing ---
    coord_cols = [col for col in maz_data_merged.columns if any(spatial in col.upper() for spatial in ['_X', '_Y'])]
    if not coord_cols and coords is not None:
        print("\nAdding coordinates to maz_data...")
        # Prepare coordinate subset - coordinate file has MAZ_NODE matching our maz_data MAZ_NODE
        coord_maz_col = 'MAZ_NODE' if 'MAZ_NODE' in coords.columns else 'MAZ'
        coord_subset = coords[[coord_maz_col, 'MAZ_X', 'MAZ_Y']].rename(columns={coord_maz_col: MAZ_DATA_MAZ_COL})
        coord_subset = coord_subset.drop_duplicates()
        
        # Merge coordinates
        maz_data_merged = pd.merge(
            maz_data_merged,
            coord_subset,
            on=MAZ_DATA_MAZ_COL,
            how='left'
        )
        
        # Fill missing coordinates with -1
        maz_data_merged['MAZ_X'] = maz_data_merged['MAZ_X'].fillna(-1)
        maz_data_merged['MAZ_Y'] = maz_data_merged['MAZ_Y'].fillna(-1)
        
        # Check success
        missing_coords = (maz_data_merged[['MAZ_X', 'MAZ_Y']] == -1).any(axis=1).sum()
        if missing_coords == 0:
            print(f"✅ Successfully added coordinates to maz_data")
        else:
            print(f"✅ Added coordinates to maz_data ({missing_coords} MAZs marked with -1 for missing coords)")

    # Recalculate emp_total to match sum of employment subcategories
    # CRITICAL FIX: Include serv_pers instead of serv_per to match UEC expressions and prevent crashes
    emp_subcategories = ['ag', 'art_rec', 'constr', 'eat', 'ed_high', 'ed_k12', 'ed_oth', 'fire', 'gov', 'health',
                        'hotel', 'info', 'lease', 'logis', 'man_bio', 'man_hvy', 'man_lgt', 'man_tech', 'natres', 
                        'prof', 'ret_loc', 'ret_reg', 'serv_bus', 'serv_pers', 'serv_soc', 'transp', 'util']
    
    # Check and fix employment consistency for maz_data
    maz_data_merged, mismatch_count, critical_count = check_employment_consistency(
        maz_data_merged, "maz_data.csv", emp_subcategories
    )

    # Save updated file
    maz_data_merged.to_csv(OUTPUT_MAZ_DATA, index=False)
    
    # Validate the fix worked for maz_data
    maz_data_validation = validate_telecommute_safety(maz_data_merged, "maz_data.csv")

    # --- Update maz_data_withDensity.csv ---
    print("\nmaz_density columns before merge:", list(maz_density.columns))
    print("jobs columns before merge:", list(jobs.columns))
        # Use detected MAZ column name for maz_data_withDensity
    if MAZ_DENSITY_MAZ_COL not in maz_density.columns:
        raise KeyError(f"No {MAZ_DENSITY_MAZ_COL} column found in maz_data_withDensity for merging.")
    maz_density_merged = pd.merge(
        maz_density,
        jobs,
        left_on=MAZ_DENSITY_MAZ_COL,
        right_on=JOBS_MAZ_COL,
        how="left"  # preserve maz_density structure including MAZ_NODE
    )
    for col in maz_density.columns:
        if col != MAZ_DENSITY_MAZ_COL and col in maz_density_merged.columns:
            maz_density_merged[col] = maz_density_merged[col].fillna(0)



    # --- Ensure only a single MAZ column is carried forward ---
    # Print columns after merge to debug
    print(f"Columns after merge: {list(maz_density_merged.columns)}")
    print(f"{MAZ_DENSITY_MAZ_COL} in merged data: {MAZ_DENSITY_MAZ_COL in maz_density_merged.columns}")
    
    # Acceptable variants: 'MAZ', 'MAZ_x', 'MAZ_y', 'maz' (but NOT MAZ_ORIGINAL!)
    maz_variants = [col for col in maz_density_merged.columns if (col.lower() == 'maz' or col.lower().startswith('maz_')) and col != 'MAZ_ORIGINAL']
    # Prefer 'MAZ', then 'MAZ_x', then 'maz', then 'MAZ_y'
    keep_maz = None
    for candidate in ['MAZ', 'MAZ_x', 'maz', 'MAZ_y']:
        if candidate in maz_density_merged.columns:
            keep_maz = candidate
            break
    if keep_maz:
        maz_density_merged = maz_density_merged.rename(columns={keep_maz: 'MAZ'})
    # Drop all other MAZ variants (but keep MAZ_ORIGINAL)
    drop_maz = [col for col in maz_variants if col != keep_maz and col != 'MAZ' and col != 'MAZ_ORIGINAL']
    if drop_maz:
        maz_density_merged = maz_density_merged.drop(columns=drop_maz)
        print(f"Dropped MAZ variants: {drop_maz}")

    # Keep jobs columns in case of conflict: drop _x (old density data), rename _y (new jobs data) to original
    print(f"Before employment column cleanup: {len(maz_density_merged.columns)} columns")
    
    # Find all _x/_y pairs
    x_cols = [col for col in maz_density_merged.columns if col.endswith('_x')]
    y_cols = [col for col in maz_density_merged.columns if col.endswith('_y')]
    
    print(f"_x columns (old density data to drop): {x_cols}")
    print(f"_y columns (new jobs data to keep): {y_cols}")
    
    # Drop _x columns where there's a corresponding _y column (except coordinate columns)
    cols_to_drop = []
    for x_col in x_cols:
        base_name = x_col[:-2]  # Remove '_x'
        y_col = base_name + '_y'
        # Only drop if there's a corresponding _y column and it's not a coordinate column
        if y_col in maz_density_merged.columns and not any(spatial in x_col.upper() for spatial in ['MAZ_X', 'MAZ_Y']):
            cols_to_drop.append(x_col)
    
    if cols_to_drop:
        maz_density_merged = maz_density_merged.drop(columns=cols_to_drop)
        print(f"Dropped old density columns: {cols_to_drop}")
    
    # Rename _y columns to original names (new jobs data becomes the main data)
    rename_cols = {}
    for col in maz_density_merged.columns:
        if col.endswith('_y') and not any(spatial in col.upper() for spatial in ['MAZ_X', 'MAZ_Y']):
            original_name = col[:-2]  # Remove '_y'
            rename_cols[col] = original_name
    
    if rename_cols:
        maz_density_merged = maz_density_merged.rename(columns=rename_cols)
        print(f"Renamed jobs columns: {list(rename_cols.values())}")
    
    print(f"After employment column cleanup: {len(maz_density_merged.columns)} columns")

    # Recalculate emp_total to match sum of employment subcategories
    # CRITICAL FIX: Include serv_pers instead of serv_per to match UEC expressions and prevent crashes
    emp_subcategories = ['ag', 'art_rec', 'constr', 'eat', 'ed_high', 'ed_k12', 'ed_oth', 'fire', 'gov', 'health',
                        'hotel', 'info', 'lease', 'logis', 'man_bio', 'man_hvy', 'man_lgt', 'man_tech', 'natres', 
                        'prof', 'ret_loc', 'ret_reg', 'serv_bus', 'serv_pers', 'serv_soc', 'transp', 'util']
    
    # Check and fix employment consistency for maz_data_withDensity
    maz_density_merged, density_mismatch_count, density_critical_count = check_employment_consistency(
        maz_density_merged, "maz_data_withDensity.csv", emp_subcategories
    )



    # --- Overwrite EmpDen, RetEmpDen, PopDen columns with new calculations ---
    sq_mi_acre = 1 / 640  # 1 acre = 1/640 square miles
    if "emp_total" in maz_density_merged.columns and "ACRES" in maz_density_merged.columns:
        maz_density_merged["EmpDen"] = maz_density_merged["emp_total"] / maz_density_merged["ACRES"].replace(0, pd.NA)
    if "ret_loc" in maz_density_merged.columns and "ret_reg" in maz_density_merged.columns and "ACRES" in maz_density_merged.columns:
        maz_density_merged["RetEmpDen"] = (maz_density_merged["ret_loc"] + maz_density_merged["ret_reg"]) / maz_density_merged["ACRES"].replace(0, pd.NA)
    if "POP" in maz_density_merged.columns and "ACRES" in maz_density_merged.columns:
        maz_density_merged["PopDen"] = maz_density_merged["POP"] / maz_density_merged["ACRES"].replace(0, pd.NA)
    # Calculate PopEmpDenPerMi = (POP+emp_total)/(10*ACRES*sq_mi_acre)
    if all(col in maz_density_merged.columns for col in ["POP", "emp_total", "ACRES"]):
        maz_density_merged["PopEmpDenPerMi"] = (maz_density_merged["POP"] + maz_density_merged["emp_total"]) / maz_density_merged["ACRES"].replace(0, pd.NA)

    # Check density consistency BEFORE calculating bins
    density_issues = check_density_consistency(maz_density_merged, "maz_data_withDensity.csv")
    
    # Check coordinate validity and fix issues that could cause Stop Location Choice crashes
    coord_issues = check_coordinate_validity(maz_density_merged, "maz_data_withDensity.csv")

    # Define empdenbin: [0-10)=1, [10-30)=2, 30+=3
    if "EmpDen" in maz_density_merged.columns:
        bins = [0, 10, 30, float('inf')]
        labels = [1, 2, 3]
        empden_numeric = pd.to_numeric(maz_density_merged["EmpDen"], errors="coerce")
    maz_density_merged["EmpDenBin"] = pd.cut(empden_numeric, bins=bins, labels=labels, right=False)
    maz_density_merged["EmpDenBin"] = maz_density_merged["EmpDenBin"].fillna(1)



    # Calculate DUDen as HH / ACRES
    if "HH" in maz_density_merged.columns and "ACRES" in maz_density_merged.columns:
        maz_density_merged["DUDen"] = maz_density_merged["HH"] / maz_density_merged["ACRES"].replace(0, pd.NA)

    # Define DuDenBin: [0-5)=1, [5-10)=2, 10+=3
    if "DUDen" in maz_density_merged.columns:
        du_bins = [0, 5, 10, float('inf')]
        du_labels = [1, 2, 3]
        duden_numeric = pd.to_numeric(maz_density_merged["DUDen"], errors="coerce")
        maz_density_merged["DuDenBin"] = pd.cut(duden_numeric, bins=du_bins, labels=du_labels, right=False)
        maz_density_merged["DuDenBin"] = maz_density_merged["DuDenBin"].fillna(1)

    # --- Add coordinate data and clean up columns ---
    if coords is not None:
        print("\nMerging coordinate data...")
        # Identify coordinate columns (MAZ_X, MAZ_Y, etc.)
        coord_cols = [col for col in coords.columns if any(spatial in col.upper() for spatial in ['_X', '_Y', 'LONGITUDE', 'LATITUDE'])]
        
        print(f"Available coordinate columns: {coord_cols}")
        print(f"Coordinate file has columns: {list(coords.columns)}")
        
        # The coordinate file has 'MAZ' which corresponds to 'MAZ_NODE' or 'MAZ_ORIGINAL' in our density file
        maz_node_col = 'MAZ_NODE' if 'MAZ_NODE' in maz_density_merged.columns else 'MAZ_ORIGINAL'
        if 'MAZ' in coords.columns and maz_node_col in maz_density_merged.columns:
            # Prepare coordinate subset with MAZ + coordinate columns
            coord_cols_to_merge = ['MAZ'] + coord_cols
            coords_subset = coords[coord_cols_to_merge].drop_duplicates()
            
            # Rename MAZ to match the density file's column name
            coords_subset = coords_subset.rename(columns={'MAZ': maz_node_col})
            
            # Merge coordinates
            maz_density_merged = pd.merge(
                maz_density_merged,
                coords_subset,
                on=maz_node_col,
                how='left'
            )
            
            # Fill missing coordinates with -1
            for coord_col in coord_cols:
                if coord_col in maz_density_merged.columns:
                    maz_density_merged[coord_col] = maz_density_merged[coord_col].fillna(-1)
            
            missing_coords = (maz_density_merged[coord_cols] == -1).any(axis=1).sum()
            if missing_coords == 0:
                print(f"✅ Successfully merged {len(coord_cols)} coordinate columns")
            else:
                print(f"✅ Successfully merged {len(coord_cols)} coordinate columns ({missing_coords} MAZs marked with -1 for missing coords)")
        else:
            print(f"Warning: Cannot merge coordinates")
            print(f"  - Coordinate file has MAZ: {'MAZ' in coords.columns}")
            print(f"  - Density file has MAZ_NODE or MAZ_ORIGINAL: {maz_node_col in maz_density_merged.columns}")
    
    # --- Clean up duplicate MAZ/TAZ columns ---
    print("\nCleaning up duplicate columns...")
    
    # Remove unwanted index columns first
    unwanted_cols = [col for col in maz_density_merged.columns if col.startswith('Unnamed:')]
    if unwanted_cols:
        maz_density_merged = maz_density_merged.drop(columns=unwanted_cols)
        print(f"Dropped unwanted index columns: {unwanted_cols}")
    
    # Ensure we have the core columns: MAZ, TAZ, MAZ_ORIGINAL, TAZ_ORIGINAL
    required_cols = ['MAZ', 'TAZ']
    optional_cols = ['MAZ_ORIGINAL', 'TAZ_ORIGINAL']
    
    # Handle MAZ variants - keep sequential MAZ as 'MAZ'
    maz_variants = [col for col in maz_density_merged.columns if col.upper() in ['MAZ', 'MAZ_X', 'MAZ_Y'] and not any(spatial in col.upper() for spatial in ['_X', '_Y'])]
    if 'MAZ' not in maz_variants and len(maz_variants) > 0:
        # Rename first available MAZ variant to MAZ
        maz_density_merged = maz_density_merged.rename(columns={maz_variants[0]: 'MAZ'})
        maz_variants[0] = 'MAZ'
    
    # Handle TAZ variants - keep sequential TAZ as 'TAZ'  
    taz_variants = [col for col in maz_density_merged.columns if col.upper() in ['TAZ', 'TAZ_X', 'TAZ_Y'] and not any(spatial in col.upper() for spatial in ['_X', '_Y'])]
    if 'TAZ' not in taz_variants and len(taz_variants) > 0:
        # Rename first available TAZ variant to TAZ
        maz_density_merged = maz_density_merged.rename(columns={taz_variants[0]: 'TAZ'})
        taz_variants[0] = 'TAZ'
    
    # Drop remaining duplicates (keep MAZ, TAZ, MAZ_ORIGINAL, TAZ_ORIGINAL + spatial)
    cols_to_drop = []
    for col in maz_density_merged.columns:
        if col in ['maz', 'taz'] and col.upper() in [c.upper() for c in maz_density_merged.columns]:
            # Drop lowercase if uppercase exists
            if col.upper() in maz_density_merged.columns:
                cols_to_drop.append(col)
        elif col.endswith('_x') and not any(spatial in col.upper() for spatial in ['_X', '_Y']):
            # Drop merge artifacts like MAZ_x, TAZ_x (but preserve coordinate columns like MAZ_X, MAZ_Y)
            cols_to_drop.append(col)
    
    if cols_to_drop:
        maz_density_merged = maz_density_merged.drop(columns=cols_to_drop)
        print(f"Dropped duplicate columns: {cols_to_drop}")
    
    # Verify we have core columns
    missing_core = [col for col in required_cols if col not in maz_density_merged.columns]
    present_optional = [col for col in optional_cols if col in maz_density_merged.columns]
    
    if missing_core:
        print(f"Warning: Missing core columns: {missing_core}")
    else:
        print(f"✅ All core columns present: {required_cols}")
    
    if present_optional:
        print(f"✅ Optional columns present: {present_optional}")
    
    # Check for coordinate columns
    spatial_cols = [col for col in maz_density_merged.columns if any(spatial in col.upper() for spatial in ['_X', '_Y'])]
    if spatial_cols:
        print(f"✅ Coordinate columns present: {spatial_cols}")
    else:
        print("⚠️ No coordinate columns found")
    
    print(f"Final column count: {len(maz_density_merged.columns)}")
    print(f"Final columns: {sorted(maz_density_merged.columns)}")

    # Save updated file
    maz_density_merged.to_csv(OUTPUT_MAZ_DENSITY, index=False)
    
    # Validate the fix worked for maz_data_withDensity
    density_validation = validate_telecommute_safety(maz_density_merged, "maz_data_withDensity.csv")
    
    # Final summary of all fixes and issues
    print(f"\n{'='*60}")
    print("FINAL SUMMARY - DATA QUALITY FIXES")
    print(f"{'='*60}")
    print(f"maz_data.csv:")
    print(f"  - Employment mismatches fixed: {mismatch_count:,}")
    print(f"  - Critical zero-total cases fixed: {critical_count:,}")
    print(f"  - Validation passed: {'✅ YES' if maz_data_validation else '❌ NO'}")
    print(f"maz_data_withDensity.csv:")  
    print(f"  - Employment mismatches fixed: {density_mismatch_count:,}")
    print(f"  - Critical zero-total cases fixed: {density_critical_count:,}")
    print(f"  - Density consistency issues: {density_issues:,}")
    print(f"  - Validation passed: {'✅ YES' if density_validation else '❌ NO'}")
    
    total_critical_fixes = critical_count + density_critical_count
    if total_critical_fixes > 0:
        print(f"\n🎯 CRITICAL: Fixed {total_critical_fixes:,} MAZs that would have caused ExplicitTelecommute crashes")
        print("   (emp_total=0 but employment subcategories>0 causing division by zero)")
    else:
        print(f"\n✅ No critical ExplicitTelecommute crash-causing issues found")
    
    overall_success = maz_data_validation and density_validation
    if overall_success:
        print(f"\n🎉 SUCCESS: All employment data consistency issues resolved!")
        print("   ExplicitTelecommute model should no longer crash on these households.")
    else:
        print(f"\n⚠️ WARNING: Some validation checks failed - review output above")
    
    print('TO DO: Figure out what IntDenBin is, and update.')

def rename_final_files():
    """Rename files to final naming convention"""
    import os
    
    # Use the same TARGET_DIR as the rest of the script
    box_dir = TARGET_DIR
    
    # Define file mappings: current_name -> new_name
    file_renames = {
        'maz_data.csv': 'maz_data_old.csv',
        'maz_data_withDensity.csv': 'maz_data_withDensity_old.csv',
        'maz_data_UPDATED.csv': 'maz_data.csv',
        'maz_data_withDensity_UPDATED.csv': 'maz_data_withDensity.csv'
    }
    
    print("\n--- FINAL FILE RENAMING ---")
    for old_name, new_name in file_renames.items():
        old_path = os.path.join(box_dir, old_name)
        new_path = os.path.join(box_dir, new_name)
        
        if os.path.exists(old_path):
            try:
                # If target exists, remove it first (for _old files, this overwrites any previous _old version)
                if os.path.exists(new_path):
                    os.remove(new_path)
                    print(f"Removed existing: {new_name}")
                
                os.rename(old_path, new_path)
                print(f"✅ Renamed: {old_name} -> {new_name}")
            except Exception as e:
                print(f"❌ Error renaming {old_name}: {e}")
        else:
            print(f"⚠️ File not found: {old_name}")
    
    print("Final files:")
    print("- maz_data.csv (current version)")
    print("- maz_data_withDensity.csv (current version)")
    print("- maz_data_old.csv (previous version)")
    print("- maz_data_withDensity_old.csv (previous version)")

def copy_files_to_box():
    """Copy final files to Box destination for TM2 model"""
    import shutil
    from pathlib import Path
    
    print("\n--- COPYING FILES TO BOX ---")
    
    # Source: where our script saves the files
    source_dir = Path(TARGET_DIR)
    
    # Destination: Box location for TM2 model (same as source in this case, but keeping for clarity)
    dest_dir = Path(r'E:\Box\Modeling and Surveys\Development\Travel Model Two Conversion\Model Inputs\2023-tm22-dev-test\landuse')
    
    # Files to copy
    files_to_copy = [
        'maz_data.csv',
        'maz_data_withDensity.csv'
    ]
    
    # Ensure destination directory exists
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    for fname in files_to_copy:
        src = source_dir / fname
        dst = dest_dir / fname
        
        if src.exists():
            try:
                shutil.copy2(src, dst)
                print(f"✅ Copied: {fname} -> {dest_dir}")
            except Exception as e:
                print(f"❌ Error copying {fname}: {e}")
        else:
            print(f"⚠️ Source file not found: {src}")
    
    print("Box sync complete!")

if __name__ == "__main__":
    merge_and_update()
    rename_final_files()
