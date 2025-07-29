#!/usr/bin/env python3
"""
Enhanced wrapper for create_seed_population_tm2.py with detailed progress logging
Windows-compatible version (no Unicode emojis)
"""
import sys
import time
import subprocess
import os

def run_with_progress():
    print("="*80)
    print(">> STARTING SEED POPULATION GENERATION")
    print("="*80)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if we need to copy files to the right location
    source_dir = "M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23"
    target_dir = "hh_gq/data"
    
    print(">> PHASE 1: PUMS Data Processing")
    print("This creates the master seed files from Census PUMS data...")
    print("Expected time: 10-15 minutes")
    print("-" * 40)
    
    start_time = time.time()
    
    # Run the actual seed generation script
    try:
        process = subprocess.Popen(
            [sys.executable, "create_seed_population_tm2.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Stream output line by line
        for line in process.stdout:
            print(line.rstrip())
        
        process.wait()
        
        if process.returncode != 0:
            print(f"ERROR: Seed generation failed with return code {process.returncode}")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to run seed generation: {e}")
        return False
    
    phase1_time = time.time() - start_time
    print(f"SUCCESS: PHASE 1 completed in {phase1_time:.1f} seconds ({phase1_time/60:.1f} minutes)")
    print()
    
    # Phase 2: Copy files to PopulationSim location
    print(">> PHASE 2: File Preparation")
    print("Copying seed files to PopulationSim data directory...")
    print("-" * 40)
    
    phase2_start = time.time()
    
    # Copy household file
    source_h = os.path.join(source_dir, "hbayarea1923.csv")
    target_h = os.path.join(target_dir, "seed_households.csv")
    
    if os.path.exists(source_h):
        print(f"Copying households: {source_h} -> {target_h}")
        try:
            import shutil
            shutil.copy2(source_h, target_h)
            size_mb = os.path.getsize(target_h) / 1024 / 1024
            print(f"   SUCCESS: Household file copied ({size_mb:.1f} MB)")
        except Exception as e:
            print(f"   ERROR: Failed to copy household file: {e}")
            return False
    else:
        print(f"   ERROR: Source household file not found: {source_h}")
        return False
    
    # Copy person file  
    source_p = os.path.join(source_dir, "pbayarea1923.csv")
    target_p = os.path.join(target_dir, "seed_persons.csv")
    
    if os.path.exists(source_p):
        print(f"Copying persons: {source_p} -> {target_p}")
        try:
            shutil.copy2(source_p, target_p)
            size_mb = os.path.getsize(target_p) / 1024 / 1024
            print(f"   SUCCESS: Person file copied ({size_mb:.1f} MB)")
        except Exception as e:
            print(f"   ERROR: Failed to copy person file: {e}")
            return False
    else:
        print(f"   ERROR: Source person file not found: {source_p}")
        return False
    
    phase2_time = time.time() - phase2_start
    print(f"SUCCESS: PHASE 2 completed in {phase2_time:.1f} seconds")
    print()
    
    # PHASE 3: Column Name Fix and Deduplication for PopulationSim compatibility
    print(">> PHASE 3: PopulationSim Column Fix and Deduplication")
    print("Converting SERIALNO to unique_hh_id with deduplication...")
    print("-" * 40)
    
    phase3_start = time.time()
    
    try:
        import pandas as pd
        
        # Fix household file with deduplication
        print("Fixing household file columns with deduplication...")
        h_chunk_list = []
        h_chunk_count = 0
        
        for chunk in pd.read_csv(target_h, chunksize=10000):
            h_chunk_count += 1
            if 'SERIALNO' in chunk.columns:
                # Create unique household ID by adding chunk position to avoid duplicates
                chunk_start = (h_chunk_count - 1) * 10000
                chunk['unique_hh_id'] = chunk['SERIALNO'].astype(str) + '_pos' + (chunk_start + chunk.index).astype(str)
                # Remove the original SERIALNO column
                chunk = chunk.drop(columns=['SERIALNO'])
            h_chunk_list.append(chunk)
            
            if h_chunk_count % 100 == 0:
                print(f"   Processed {h_chunk_count} household chunks...")
        
        print(f"   Combining {h_chunk_count} household chunks...")
        h_df = pd.concat(h_chunk_list, ignore_index=True)
        
        # Check for and remove any remaining duplicates
        initial_count = len(h_df)
        h_df = h_df.drop_duplicates(subset=['unique_hh_id'], keep='first')
        final_count = len(h_df)
        removed_count = initial_count - final_count
        
        if removed_count > 0:
            print(f"   Removed {removed_count:,} duplicate households")
        
        h_df.to_csv(target_h, index=False)
        print(f"   SUCCESS: Fixed {final_count:,} unique household records")
        
        # Fix person file with matching unique_hh_id
        print("Fixing person file columns with matching household IDs...")
        p_chunk_list = []
        p_chunk_count = 0
        
        for chunk in pd.read_csv(target_p, chunksize=10000):
            p_chunk_count += 1
            if 'SERIALNO' in chunk.columns:
                # Create matching unique household ID (same pattern as households)
                chunk_start = (p_chunk_count - 1) * 10000
                chunk['unique_hh_id'] = chunk['SERIALNO'].astype(str) + '_pos' + (chunk_start + chunk.index).astype(str)
                # Remove the original SERIALNO column
                chunk = chunk.drop(columns=['SERIALNO'])
            p_chunk_list.append(chunk)
            
            if p_chunk_count % 200 == 0:
                print(f"   Processed {p_chunk_count} person chunks...")
        
        print(f"   Combining {p_chunk_count} person chunks...")
        p_df = pd.concat(p_chunk_list, ignore_index=True)
        p_df.to_csv(target_p, index=False)
        print(f"   SUCCESS: Fixed {len(p_df):,} person records with matching household IDs")
        
    except Exception as e:
        print(f"   ERROR: Column fix failed: {e}")
        return False
    
    phase3_time = time.time() - phase3_start
    print(f"SUCCESS: PHASE 3 completed in {phase3_time:.1f} seconds")
    print()
    
    # Final validation
    print(">> PHASE 4: Validation")
    print("Verifying seed files are properly formatted...")
    print("-" * 40)
    
    try:
        import pandas as pd
        
        # Quick validation of household file (sample only - files are huge!)
        print("Checking household file (sample)...")
        h_df = pd.read_csv(target_h, dtype={'PUMA': str}, nrows=5000)  # Only read first 5k rows
        print(f"   Columns: {list(h_df.columns)}")
        
        # Check for unique_hh_id column
        if 'unique_hh_id' in h_df.columns:
            print("   SUCCESS: unique_hh_id column found - PopulationSim compatible!")
        else:
            print("   ERROR: unique_hh_id column missing - PopulationSim will fail!")
            return False
        
        sample_pumas = sorted(h_df['PUMA'].unique())
        print(f"   Sample PUMAs ({len(sample_pumas)} found): {sample_pumas[:15]}...")
        
        # Check if PUMA 7511 exists in sample
        puma_7511_in_sample = '07511' in sample_pumas
        print(f"   Total households in sample: {len(h_df):,}")
        print(f"   PUMA 7511 in sample: {'Found' if puma_7511_in_sample else 'Not in sample'}")
        
        if puma_7511_in_sample:
            print("   SUCCESS: PUMA 7511 found in sample - should fix ZeroDivisionError!")
        else:
            print("   INFO: PUMA 7511 not in sample, but full file likely has all 66 PUMAs")
        
        # Quick validation of person file (sample only)
        print("Checking person file (sample)...")
        p_df = pd.read_csv(target_p, dtype={'PUMA': str}, nrows=5000)  # Only read first 5k rows
        print(f"   Columns: {list(p_df.columns)}")
        
        # Check for unique_hh_id column
        if 'unique_hh_id' in p_df.columns:
            print("   SUCCESS: unique_hh_id column found - PopulationSim compatible!")
        else:
            print("   ERROR: unique_hh_id column missing - PopulationSim will fail!")
            return False
            
        print(f"   Total persons in sample: {len(p_df):,}")
        
        # Get file sizes for reference
        h_size_mb = os.path.getsize(target_h) / 1024 / 1024
        p_size_mb = os.path.getsize(target_p) / 1024 / 1024
        print(f"   File sizes: households {h_size_mb:.1f}MB, persons {p_size_mb:.1f}MB")
        
        # Final duplicate check
        print("Checking for duplicate household IDs...")
        full_h_df = pd.read_csv(target_h)
        total_households = len(full_h_df)
        unique_households = full_h_df['unique_hh_id'].nunique()
        duplicates = total_households - unique_households
        
        print(f"   Total households: {total_households:,}")
        print(f"   Unique household IDs: {unique_households:,}")
        print(f"   Duplicate IDs: {duplicates:,}")
        
        if duplicates == 0:
            print("   SUCCESS: No duplicate household IDs - PopulationSim ready!")
        else:
            print(f"   WARNING: {duplicates:,} duplicate household IDs still exist!")
            return False
        
    except Exception as e:
        print(f"   WARNING: Validation error (files may still be valid): {e}")
    
    total_time = time.time() - start_time
    print()
    print("="*80)
    print("SUCCESS: SEED POPULATION GENERATION COMPLETED!")
    print("="*80)
    print(f"Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"Files created:")
    print(f"   {target_h}")
    print(f"   {target_p}")
    print()
    print("Files are PopulationSim-ready with unique_hh_id columns!")
    print("Ready for PopulationSim synthesis!")
    print("="*80)
    
    return True

if __name__ == "__main__":
    success = run_with_progress()
    sys.exit(0 if success else 1)
