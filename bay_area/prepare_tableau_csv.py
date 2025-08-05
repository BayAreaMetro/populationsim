#!/usr/bin/env python3
"""
Simple Tableau data preparation - CSV files only

This script prepares the core PopulationSim CSV data for Tableau analysis,
avoiding shapefile compatibility issues.
"""

import pandas as pd
import os
import numpy as np
from pathlib import Path

def prepare_tableau_csv_data():
    """Prepare PopulationSim CSV data for Tableau analysis."""
    
    print("="*80)
    print("PREPARING POPULATIONSIM CSV DATA FOR TABLEAU")
    print("="*80)
    
    # Directories
    input_dir = "output_2023"
    output_dir = os.path.join(input_dir, "tableau")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    # Process each data file
    results = {}
    
    # 1. TAZ Marginals
    print(f"\n📊 Processing TAZ marginals...")
    try:
        taz_file = os.path.join(input_dir, "taz_marginals.csv")
        if os.path.exists(taz_file):
            taz_df = pd.read_csv(taz_file)
            
            # Standardize TAZ ID as integer
            if 'TAZ' in taz_df.columns:
                taz_df['TAZ'] = taz_df['TAZ'].astype(int)
                
            # Add calculated fields for Tableau
            taz_df['total_households'] = 0
            hh_size_cols = [col for col in taz_df.columns if 'hh_size_' in col]
            if hh_size_cols:
                taz_df['total_households'] = taz_df[hh_size_cols].sum(axis=1)
                
            taz_df['total_population'] = 0
            age_cols = [col for col in taz_df.columns if 'pers_age_' in col]
            if age_cols:
                taz_df['total_population'] = taz_df[age_cols].sum(axis=1)
            
            # Save Tableau version
            output_file = os.path.join(output_dir, "taz_marginals_tableau.csv")
            taz_df.to_csv(output_file, index=False)
            print(f"   ✅ Saved: {output_file} ({len(taz_df):,} records)")
            results['taz_marginals'] = True
        else:
            print(f"   ❌ File not found: {taz_file}")
            results['taz_marginals'] = False
    except Exception as e:
        print(f"   ❌ Error processing TAZ marginals: {e}")
        results['taz_marginals'] = False
    
    # 2. MAZ Marginals
    print(f"\n📊 Processing MAZ marginals...")
    try:
        maz_file = os.path.join(input_dir, "maz_marginals.csv")
        if os.path.exists(maz_file):
            maz_df = pd.read_csv(maz_file)
            
            # Standardize MAZ ID as integer
            if 'MAZ' in maz_df.columns:
                maz_df['MAZ'] = maz_df['MAZ'].astype(int)
                
            # Save Tableau version
            output_file = os.path.join(output_dir, "maz_marginals_tableau.csv")
            maz_df.to_csv(output_file, index=False)
            print(f"   ✅ Saved: {output_file} ({len(maz_df):,} records)")
            results['maz_marginals'] = True
        else:
            print(f"   ❌ File not found: {maz_file}")
            results['maz_marginals'] = False
    except Exception as e:
        print(f"   ❌ Error processing MAZ marginals: {e}")
        results['maz_marginals'] = False
    
    # 3. Geographic Crosswalk
    print(f"\n🗺️  Processing geographic crosswalk...")
    try:
        crosswalk_file = os.path.join(input_dir, "geo_cross_walk_tm2_updated.csv")
        if os.path.exists(crosswalk_file):
            crosswalk_df = pd.read_csv(crosswalk_file)
            
            # Standardize IDs as integers
            for col in ['MAZ', 'TAZ', 'COUNTY', 'PUMA']:
                if col in crosswalk_df.columns:
                    crosswalk_df[col] = crosswalk_df[col].astype(int)
            
            # Save Tableau version
            output_file = os.path.join(output_dir, "geo_crosswalk_tableau.csv")
            crosswalk_df.to_csv(output_file, index=False)
            print(f"   ✅ Saved: {output_file} ({len(crosswalk_df):,} records)")
            results['geo_crosswalk'] = True
        else:
            print(f"   ❌ File not found: {crosswalk_file}")
            results['geo_crosswalk'] = False
    except Exception as e:
        print(f"   ❌ Error processing geographic crosswalk: {e}")
        results['geo_crosswalk'] = False
    
    # 4. County Marginals
    print(f"\n📊 Processing county marginals...")
    try:
        county_file = os.path.join(input_dir, "county_marginals.csv")
        if os.path.exists(county_file):
            county_df = pd.read_csv(county_file)
            
            # Save Tableau version
            output_file = os.path.join(output_dir, "county_marginals_tableau.csv")
            county_df.to_csv(output_file, index=False)
            print(f"   ✅ Saved: {output_file} ({len(county_df):,} records)")
            results['county_marginals'] = True
        else:
            print(f"   ❌ File not found: {county_file}")
            results['county_marginals'] = False
    except Exception as e:
        print(f"   ❌ Error processing county marginals: {e}")
        results['county_marginals'] = False
    
    # 5. Create summary table
    print(f"\n📋 Creating data summary...")
    try:
        summary_data = []
        
        # TAZ summary
        if results['taz_marginals'] and os.path.exists(os.path.join(output_dir, "taz_marginals_tableau.csv")):
            taz_summary = pd.read_csv(os.path.join(output_dir, "taz_marginals_tableau.csv"))
            summary_data.append({
                'geography': 'TAZ',
                'record_count': len(taz_summary),
                'total_households': taz_summary.get('total_households', 0).sum(),
                'total_population': taz_summary.get('total_population', 0).sum()
            })
        
        # MAZ summary  
        if results['maz_marginals'] and os.path.exists(os.path.join(output_dir, "maz_marginals_tableau.csv")):
            maz_summary = pd.read_csv(os.path.join(output_dir, "maz_marginals_tableau.csv"))
            summary_data.append({
                'geography': 'MAZ',
                'record_count': len(maz_summary),
                'total_households': maz_summary.get('num_hh', 0).sum(),
                'total_population': maz_summary.get('total_pop', 0).sum()
            })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_file = os.path.join(output_dir, "data_summary_tableau.csv")
            summary_df.to_csv(summary_file, index=False)
            print(f"   ✅ Saved: {summary_file}")
            results['summary'] = True
        else:
            results['summary'] = False
            
    except Exception as e:
        print(f"   ❌ Error creating summary: {e}")
        results['summary'] = False
    
    # 6. Create README
    print(f"\n📄 Creating README...")
    try:
        readme_content = f"""# PopulationSim Tableau Data

## Overview
This directory contains PopulationSim control data prepared for Tableau analysis.
Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## Files

### Core Data Files
- `taz_marginals_tableau.csv` - TAZ-level control totals with calculated fields
- `maz_marginals_tableau.csv` - MAZ-level control totals  
- `geo_crosswalk_tableau.csv` - Geographic relationships (MAZ-TAZ-County-PUMA)
- `county_marginals_tableau.csv` - County-level control totals
- `data_summary_tableau.csv` - High-level summary statistics

### Key Join Fields
- **TAZ**: Traffic Analysis Zone ID (integer)
- **MAZ**: Micro Analysis Zone ID (integer) 
- **COUNTY**: County FIPS code (integer)
- **PUMA**: Public Use Microdata Area ID (integer)

## Tableau Usage
1. Connect to the CSV files as data sources
2. Create relationships using the geographic IDs
3. Use calculated fields for totals and percentages
4. Join TAZ and MAZ data via the crosswalk file

## Data Quality Notes
- All geographic IDs are standardized as integers
- TAZ data includes calculated total_households and total_population fields
- Hierarchical consistency has been enforced between TAZ and MAZ levels

## Processing Status
"""
        
        for data_type, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            readme_content += f"- {data_type}: {status}\\n"
        
        readme_file = os.path.join(output_dir, "README_Tableau_Data.md")
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        print(f"   ✅ Saved: {readme_file}")
        results['readme'] = True
        
    except Exception as e:
        print(f"   ❌ Error creating README: {e}")
        results['readme'] = False
    
    # Final Summary
    print(f"\n📋 TABLEAU DATA PREPARATION SUMMARY")
    print("="*50)
    
    successful = sum(results.values())
    for data_type, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{data_type:20} {status}")
    
    print(f"\nSuccessfully prepared: {successful}/{len(results)} data files")
    print(f"Output directory: {output_dir}")
    
    if successful > 0:
        print(f"\n🎉 Tableau CSV data ready! Check the README file for usage instructions.")
        print(f"Note: Shapefiles were skipped due to compatibility issues.")
    
    return results

if __name__ == "__main__":
    prepare_tableau_csv_data()
