#!/usr/bin/env python3
"""
Summarize Seed Population Script

This script provides comprehensive analysis of the seed population files to understand:
1. Group quarters composition and distribution
2. Geographic distribution by PUMA/County
3. Key demographic variables
4. Data quality checks

Usage:
    python analysis/summarize_seed_population.py
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

def main():
    print("=" * 80)
    print("SEED POPULATION SUMMARY ANALYSIS")
    print("=" * 80)
    print()
    
    # Define file paths
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "output_2023" / "populationsim_working_dir" / "data"
    
    households_file = data_dir / "seed_households.csv"
    persons_file = data_dir / "seed_persons.csv"
    crosswalk_file = data_dir / "geo_cross_walk_tm2_maz.csv"
    
    # Check if files exist
    if not households_file.exists():
        print(f"❌ Households file not found: {households_file}")
        return
    if not persons_file.exists():
        print(f"❌ Persons file not found: {persons_file}")
        return
    
    print(f"📁 Data location: {data_dir}")
    print(f"📊 Loading seed population data...")
    print()
    
    # Load data
    households = pd.read_csv(households_file)
    persons = pd.read_csv(persons_file)
    
    if crosswalk_file.exists():
        crosswalk = pd.read_csv(crosswalk_file)
    else:
        crosswalk = None
        print("⚠️  Crosswalk file not found - geographic analysis will be limited")
    
    # Basic counts
    print("1. BASIC POPULATION COUNTS")
    print("-" * 40)
    print(f"   Total households: {len(households):,}")
    print(f"   Total persons: {len(persons):,}")
    print(f"   Average household size: {len(persons) / len(households):.2f}")
    print()
    
    # Group quarters analysis
    print("2. GROUP QUARTERS ANALYSIS")
    print("-" * 40)
    
    print("   A. Household-level hhgqtype distribution:")
    hh_gqtype_dist = households['hhgqtype'].value_counts().sort_index()
    for gqtype, count in hh_gqtype_dist.items():
        gq_name = {
            0: "Regular households",
            1: "University group quarters",
            2: "Military group quarters", 
            3: "Other noninstitutional group quarters"
        }.get(gqtype, f"Unknown type {gqtype}")
        pct = (count / len(households)) * 100
        print(f"     {gqtype}: {count:,} ({pct:.1f}%) - {gq_name}")
    
    print()
    print("   B. Person-level hhgqtype distribution:")
    person_gqtype_dist = persons['hhgqtype'].value_counts().sort_index()
    for gqtype, count in person_gqtype_dist.items():
        gq_name = {
            0: "In regular households",
            1: "In university group quarters",
            2: "In military group quarters",
            3: "In other noninstitutional group quarters"
        }.get(gqtype, f"Unknown type {gqtype}")
        pct = (count / len(persons)) * 100
        print(f"     {gqtype}: {count:,} ({pct:.1f}%) - {gq_name}")
    
    print()
    print("   C. TYPEHUGQ (PUMS housing unit type) distribution:")
    if 'TYPEHUGQ' in households.columns:
        typehugq_dist = households['TYPEHUGQ'].value_counts().sort_index()
        for typ, count in typehugq_dist.items():
            type_name = {
                1: "Housing units",
                2: "Institutional group quarters", 
                3: "Noninstitutional group quarters"
            }.get(typ, f"Unknown type {typ}")
            pct = (count / len(households)) * 100
            print(f"     {typ}: {count:,} ({pct:.1f}%) - {type_name}")
    else:
        print("     TYPEHUGQ column not found")
    
    # Geographic distribution
    print()
    print("3. GEOGRAPHIC DISTRIBUTION")
    print("-" * 40)
    
    if 'PUMA' in households.columns:
        print("   A. Distribution by PUMA:")
        puma_dist = households['PUMA'].value_counts().sort_index()
        print(f"     Total PUMAs: {len(puma_dist)}")
        print(f"     PUMA range: {puma_dist.index.min()} to {puma_dist.index.max()}")
        
        # Show top 5 PUMAs by household count
        top_pumas = puma_dist.head()
        print(f"     Top 5 PUMAs by household count:")
        for puma, count in top_pumas.items():
            pct = (count / len(households)) * 100
            print(f"       PUMA {puma}: {count:,} ({pct:.1f}%)")
    
    if 'COUNTY' in households.columns:
        print()
        print("   B. Distribution by County:")
        county_dist = households['COUNTY'].value_counts().sort_index()
        for county, count in county_dist.items():
            pct = (count / len(households)) * 100
            
            # Get county name if crosswalk available
            county_name = "Unknown"
            if crosswalk is not None and 'county_name' in crosswalk.columns:
                county_names = crosswalk[crosswalk['COUNTY'] == county]['county_name'].unique()
                if len(county_names) > 0:
                    county_name = county_names[0]
            
            print(f"     County {county}: {count:,} ({pct:.1f}%) - {county_name}")
    
    # Demographic analysis
    print()
    print("4. KEY DEMOGRAPHIC VARIABLES")
    print("-" * 40)
    
    # Household size distribution
    if 'NP' in households.columns:
        print("   A. Household size distribution (NP):")
        hh_size_dist = households['NP'].value_counts().sort_index()
        for size, count in hh_size_dist.items():
            if size <= 10:  # Only show reasonable household sizes
                pct = (count / len(households)) * 100
                print(f"     {size} person(s): {count:,} ({pct:.1f}%)")
    
    # Age distribution
    if 'AGEP' in persons.columns:
        print()
        print("   B. Age distribution (persons):")
        age_groups = [
            (0, 17, "0-17 years"),
            (18, 34, "18-34 years"),
            (35, 64, "35-64 years"), 
            (65, 150, "65+ years")
        ]
        
        for min_age, max_age, label in age_groups:
            count = ((persons['AGEP'] >= min_age) & (persons['AGEP'] <= max_age)).sum()
            pct = (count / len(persons)) * 100
            print(f"     {label}: {count:,} ({pct:.1f}%)")
    
    # Income distribution (if available)
    income_cols = ['hh_income_2023', 'hh_income_2010', 'HINCP']
    income_col = None
    for col in income_cols:
        if col in households.columns:
            income_col = col
            break
    
    if income_col:
        print()
        print(f"   C. Household income distribution ({income_col}):")
        income_data = households[income_col].dropna()
        if len(income_data) > 0:
            income_brackets = [
                (0, 19999, "Under $20k"),
                (20000, 44999, "$20k-$45k"),
                (45000, 59999, "$45k-$60k"), 
                (60000, 74999, "$60k-$75k"),
                (75000, 99999, "$75k-$100k"),
                (100000, 149999, "$100k-$150k"),
                (150000, 199999, "$150k-$200k"),
                (200000, 999999999, "$200k+")
            ]
            
            for min_inc, max_inc, label in income_brackets:
                count = ((income_data >= min_inc) & (income_data <= max_inc)).sum()
                pct = (count / len(income_data)) * 100
                print(f"     {label}: {count:,} ({pct:.1f}%)")
    
    # Workers distribution
    if 'hh_workers_from_esr' in households.columns:
        print()
        print("   D. Household workers distribution:")
        worker_dist = households['hh_workers_from_esr'].value_counts().sort_index()
        for workers, count in worker_dist.items():
            if workers <= 5:  # Only show reasonable worker counts
                pct = (count / len(households)) * 100
                plural = "worker" if workers == 1 else "workers"
                print(f"     {workers} {plural}: {count:,} ({pct:.1f}%)")
    
    # Data quality checks
    print()
    print("5. DATA QUALITY CHECKS")
    print("-" * 40)
    
    # Check for missing values in key fields
    key_hh_fields = ['unique_hh_id', 'PUMA', 'COUNTY', 'hhgqtype', 'NP']
    key_person_fields = ['unique_hh_id', 'PUMA', 'COUNTY', 'hhgqtype', 'AGEP']
    
    print("   A. Missing values in key household fields:")
    for field in key_hh_fields:
        if field in households.columns:
            missing = households[field].isna().sum()
            pct = (missing / len(households)) * 100
            status = "✓" if missing == 0 else "⚠️"
            print(f"     {status} {field}: {missing:,} missing ({pct:.1f}%)")
        else:
            print(f"     ❌ {field}: Column not found")
    
    print()
    print("   B. Missing values in key person fields:")
    for field in key_person_fields:
        if field in persons.columns:
            missing = persons[field].isna().sum()
            pct = (missing / len(persons)) * 100
            status = "✓" if missing == 0 else "⚠️"
            print(f"     {status} {field}: {missing:,} missing ({pct:.1f}%)")
        else:
            print(f"     ❌ {field}: Column not found")
    
    # Check household-person alignment
    print()
    print("   C. Household-person alignment:")
    hh_ids_in_hh = set(households['unique_hh_id'].dropna())
    hh_ids_in_persons = set(persons['unique_hh_id'].dropna())
    
    orphan_persons = len(hh_ids_in_persons - hh_ids_in_hh)
    empty_households = len(hh_ids_in_hh - hh_ids_in_persons)
    
    print(f"     ✓ Household IDs in households: {len(hh_ids_in_hh):,}")
    print(f"     ✓ Household IDs in persons: {len(hh_ids_in_persons):,}")
    
    if orphan_persons == 0:
        print(f"     ✓ Orphan persons (no matching household): {orphan_persons}")
    else:
        print(f"     ⚠️  Orphan persons (no matching household): {orphan_persons}")
    
    if empty_households == 0:
        print(f"     ✓ Empty households (no persons): {empty_households}")
    else:
        print(f"     ⚠️  Empty households (no persons): {empty_households}")
    
    # Group quarters consistency check
    print()
    print("   D. Group quarters consistency:")
    
    # Check if person hhgqtype matches their household hhgqtype
    persons_with_hh = persons.merge(
        households[['unique_hh_id', 'hhgqtype']], 
        on='unique_hh_id', 
        suffixes=('_person', '_household')
    )
    
    if 'hhgqtype_person' in persons_with_hh.columns and 'hhgqtype_household' in persons_with_hh.columns:
        mismatched = (persons_with_hh['hhgqtype_person'] != persons_with_hh['hhgqtype_household']).sum()
        
        if mismatched == 0:
            print(f"     ✓ Person-household hhgqtype alignment: {mismatched} mismatches")
        else:
            print(f"     ⚠️  Person-household hhgqtype alignment: {mismatched:,} mismatches")
    
    # Summary and recommendations
    print()
    print("6. SUMMARY & RECOMMENDATIONS")
    print("-" * 40)
    
    # Check for the specific convergence issue
    univ_gq_households = (households['hhgqtype'] == 1).sum()
    military_gq_households = (households['hhgqtype'] == 2).sum()
    univ_gq_persons = (persons['hhgqtype'] == 1).sum() 
    military_gq_persons = (persons['hhgqtype'] == 2).sum()
    
    print("   Population synthesis compatibility:")
    
    if univ_gq_persons > 0:
        print(f"     ✓ University GQ available: {univ_gq_persons:,} persons in {univ_gq_households:,} households")
    else:
        print(f"     ⚠️  No university GQ found - may cause convergence issues if controls expect university GQ")
    
    if military_gq_persons > 0:
        print(f"     ✓ Military GQ available: {military_gq_persons:,} persons in {military_gq_households:,} households")
    else:
        print(f"     ⚠️  No military GQ found - may cause convergence issues if controls expect military GQ")
    
    total_gq = (households['hhgqtype'] >= 1).sum()
    print(f"     📊 Total GQ households: {total_gq:,} ({total_gq/len(households)*100:.1f}% of all households)")
    
    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()


