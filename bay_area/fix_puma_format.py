#!/usr/bin/env python3
"""
Fix PUMA format to 5-digit zero-padded format
"""

import pandas as pd
from pathlib import Path

def fix_puma_format():
    """Fix PUMA format to 5-digit zero-padded format"""
    
    # Load current crosswalk
    crosswalk_path = Path("output_2023/geo_cross_walk_tm2_updated.csv")
    print(f"Loading crosswalk: {crosswalk_path}")
    
    df = pd.read_csv(crosswalk_path)
    print(f"Original PUMA format examples: {df.PUMA.astype(str).head().tolist()}")
    
    # Convert to 5-digit zero-padded format
    df['PUMA'] = df['PUMA'].astype(str).str.zfill(5)
    
    print(f"Fixed PUMA format examples: {df.PUMA.head().tolist()}")
    print(f"Unique PUMAs: {df.PUMA.nunique()}")
    
    # Save updated crosswalk
    df.to_csv(crosswalk_path, index=False)
    
    print(f"✅ Updated crosswalk saved with 5-digit PUMA format")
    
    # Show sample of unique PUMAs
    unique_pumas = sorted(df.PUMA.unique())
    print(f"First 10 PUMAs: {unique_pumas[:10]}")
    print(f"Last 10 PUMAs: {unique_pumas[-10:]}")
    
    return True

if __name__ == "__main__":
    fix_puma_format()
