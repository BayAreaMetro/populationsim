#!/usr/bin/env python3
"""
Simple comparison between seed population PUMAs and crosswalk PUMAs.
"""

import pandas as pd

def main():
    print("=" * 60)
    print("PUMA COMPARISON: SEED vs CROSSWALK")
    print("=" * 60)
    
    # Get PUMAs from seed population
    seed_df = pd.read_csv("seed_households.csv")
    seed_pumas = set(seed_df['PUMA'].unique())
    print(f"Seed population PUMAs: {len(seed_pumas)}")
    print(f"Seed PUMAs: {sorted(seed_pumas)}")
    
    # Get PUMAs from our crosswalk
    crosswalk_df = pd.read_csv("geo_cross_walk_tm2_updated.csv")
    crosswalk_pumas = set(crosswalk_df['PUMA'].unique())
    print(f"\nCrosswalk PUMAs: {len(crosswalk_pumas)}")
    print(f"Crosswalk PUMAs: {sorted(crosswalk_pumas)}")
    
    # Find missing PUMAs (in seed but not in crosswalk)
    missing_pumas = seed_pumas - crosswalk_pumas
    print(f"\n🔍 MISSING PUMAs (in seed but NOT in crosswalk): {len(missing_pumas)}")
    if missing_pumas:
        print(f"Missing PUMA IDs: {sorted(missing_pumas)}")
    else:
        print("No missing PUMAs!")
    
    # Find extra PUMAs (in crosswalk but not in seed)
    extra_pumas = crosswalk_pumas - seed_pumas
    print(f"\n➕ EXTRA PUMAs (in crosswalk but NOT in seed): {len(extra_pumas)}")
    if extra_pumas:
        print(f"Extra PUMA IDs: {sorted(extra_pumas)}")
    else:
        print("No extra PUMAs!")
    
    # Summary
    print(f"\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Seed population PUMAs: {len(seed_pumas)}")
    print(f"Crosswalk PUMAs: {len(crosswalk_pumas)}")
    print(f"Missing from crosswalk: {len(missing_pumas)}")
    print(f"Extra in crosswalk: {len(extra_pumas)}")
    
    if missing_pumas:
        print(f"\n🗺️  MISSING PUMA IDs FOR MAP ANALYSIS:")
        for puma in sorted(missing_pumas):
            print(f"   {puma}")

if __name__ == "__main__":
    main()
