"""
Debug the merge issue between household size controls and gq_pop.
"""
import os
import sys
import pandas as pd
import numpy as np

# Add the current directory to path so we can import from tm2_control_utils
sys.path.insert(0, os.getcwd())

# Remove the import, we don't need it for this test

def simulate_hh_size_processing():
    """Simulate what happens when household size controls are processed."""
    print("=== SIMULATING HOUSEHOLD SIZE CONTROL PROCESSING ===")
    
    # Create a simple MAZ dataframe with some example MAZs
    mazs = [1, 2, 3, 4, 5]
    
    # Simulate household size control results (6 columns for 1-person, 2-person, etc.)
    hh_size_data = {
        'MAZ': mazs,
        'hh_size_1': [100, 150, 200, 120, 180],
        'hh_size_2': [80, 120, 160, 100, 140],
        'hh_size_3': [60, 90, 120, 75, 105],
        'hh_size_4': [40, 60, 80, 50, 70],
        'hh_size_5': [20, 30, 40, 25, 35],
        'hh_size_6+': [10, 15, 20, 12, 18]
    }
    
    hh_df = pd.DataFrame(hh_size_data).set_index('MAZ')
    print(f"Household size control DataFrame:")
    print(hh_df)
    print(f"Index: {hh_df.index.tolist()}")
    print(f"Shape: {hh_df.shape}")
    return hh_df

def simulate_gq_pop_processing():
    """Simulate what happens when gq_pop control is processed."""
    print("\n=== SIMULATING GQ_POP CONTROL PROCESSING ===")
    
    # Simulate gq_pop results - note this might have different MAZs!
    mazs = [1, 2, 3, 4, 5, 6, 7]  # More MAZs than household size
    gq_data = {
        'MAZ': mazs,
        'gq_pop': [89, 106, 83, 133, 108, 45, 67]
    }
    
    gq_df = pd.DataFrame(gq_data).set_index('MAZ')
    print(f"GQ population control DataFrame:")
    print(gq_df)
    print(f"Index: {gq_df.index.tolist()}")
    print(f"Shape: {gq_df.shape}")
    return gq_df

def test_merge_behavior(hh_df, gq_df):
    """Test what happens when we merge these DataFrames."""
    print("\n=== TESTING MERGE BEHAVIOR ===")
    
    # Simulate the merge that happens in the actual code
    print("Method 1: pd.merge with how='left', left_index=True, right_index=True")
    merged1 = pd.merge(
        left=hh_df,
        right=gq_df,
        how="left",
        left_index=True,
        right_index=True
    )
    print("Result:")
    print(merged1)
    print(f"gq_pop values: {merged1['gq_pop'].tolist()}")
    
    print("\nMethod 2: What if we use how='outer'?")
    merged2 = pd.merge(
        left=hh_df,
        right=gq_df,
        how="outer",
        left_index=True,
        right_index=True
    )
    print("Result:")
    print(merged2)
    print(f"gq_pop values: {merged2['gq_pop'].tolist()}")
    
    print("\nMethod 3: Simple concat (what should probably happen)")
    concat_result = pd.concat([hh_df, gq_df], axis=1)
    print("Result:")
    print(concat_result)
    print(f"gq_pop values: {concat_result['gq_pop'].tolist()}")
    
    return merged1, merged2, concat_result

if __name__ == "__main__":
    # Run the simulation
    hh_df = simulate_hh_size_processing()
    gq_df = simulate_gq_pop_processing()
    merged1, merged2, concat_result = test_merge_behavior(hh_df, gq_df)
    
    print("\n=== ANALYSIS ===")
    print("The issue is likely that when household size controls are processed first,")
    print("they create a DataFrame with a specific set of MAZ indices.")
    print("When gq_pop is processed later and has a different set of MAZ indices,")
    print("the pd.merge with how='left' only keeps rows that exist in the left DataFrame.")
    print("This means gq_pop values for MAZs not in household size controls get dropped!")
