#!/usr/bin/env python3
"""
Prepare PopulationSim data for Tableau analysis

This script standardizes join fields across all key data sources to ensure
seamless joins in Tableau:
- TAZ shapefile (geographic boundaries)
- PUMA shapefile (geographic boundaries) 
- TAZ marginals (control data)
- MAZ marginals (control data)
- Geographic crosswalk (zone relationships)

All ID fields are standardized as integers with consistent naming conventions.
Output files are saved with "_tableau" suffix for easy identification.

Usage:
    python prepare_tableau_data.py
"""

import pandas as pd
import geopandas as gpd
import os
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class TableauDataPreparer:
    """Class for preparing PopulationSim data for Tableau analysis."""
    
    def __init__(self, data_dir="output_2023", shapefile_dir=None, output_dir=None):
        """
        Initialize TableauDataPreparer.
        
        Parameters:
        -----------
        data_dir : str
            Directory containing CSV data files
        shapefile_dir : str, optional
            Directory containing shapefiles (will search multiple locations)
        output_dir : str, optional
            Directory for Tableau-ready outputs
        """
        self.data_dir = data_dir
        self.output_dir = output_dir or f"{data_dir}_tableau"
        
        # Shapefile search paths
        self.shapefile_dirs = [
            shapefile_dir,
            r"C:\GitHub\tm2py-utils\tm2py_utils\inputs\maz_taz\shapefiles",
            "local_data/gis",
            "input_2023/gis",
            "../shapefiles"
        ] if shapefile_dir else [
            r"C:\GitHub\tm2py-utils\tm2py_utils\inputs\maz_taz\shapefiles",
            "local_data/gis", 
            "input_2023/gis",
            "../shapefiles"
        ]
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        print("="*80)
        print("PREPARING POPULATIONSIM DATA FOR TABLEAU")
        print("="*80)
        print(f"Input directory: {self.data_dir}")
        print(f"Output directory: {self.output_dir}")
        
    def find_shapefile(self, pattern):
        """Find shapefile matching pattern in search directories."""
        for dir_path in self.shapefile_dirs:
            if dir_path and os.path.exists(dir_path):
                print(f"   Searching: {dir_path}")
                for file_path in Path(dir_path).rglob("*.shp"):
                    filename = file_path.name.lower()
                    if any(p in filename for p in pattern):
                        print(f"   Found: {file_path}")
                        return str(file_path)
        return None
        
    def prepare_taz_shapefile(self):
        """Prepare TAZ shapefile with standardized join fields."""
        print(f"\n🗺️  Processing TAZ shapefile...")
        
        # Find TAZ shapefile
        taz_patterns = ['taz', 'traffic']
        taz_shapefile = self.find_shapefile(taz_patterns)
        
        if not taz_shapefile:
            print(f"   ❌ TAZ shapefile not found")
            return None
            
        # Load shapefile
        taz_gdf = gpd.read_file(taz_shapefile)
        print(f"   Loaded {len(taz_gdf):,} TAZ features")
        print(f"   Original columns: {list(taz_gdf.columns)}")
        
        # Identify TAZ ID field
        taz_id_field = None
        for field in ['TAZ', 'taz', 'TAZ_ID', 'TAZID', 'taz_id']:
            if field in taz_gdf.columns:
                taz_id_field = field
                break
                
        if not taz_id_field:
            # Look for any field with 'taz' in name
            taz_fields = [col for col in taz_gdf.columns if 'taz' in col.lower()]
            if taz_fields:
                taz_id_field = taz_fields[0]
            else:
                print(f"   ❌ No TAZ ID field found")
                return None
                
        print(f"   Using TAZ ID field: {taz_id_field}")
        
        # Standardize TAZ ID field
        taz_gdf['TAZ_ID'] = taz_gdf[taz_id_field].astype(int)
        
        # Keep essential fields for Tableau
        keep_fields = ['TAZ_ID', 'geometry']
        
        # Add any other useful fields (area, name, etc.)
        for field in taz_gdf.columns:
            if field.lower() in ['area', 'name', 'label', 'county', 'district']:
                keep_fields.append(field)
                
        # Select and clean columns
        taz_clean = taz_gdf[keep_fields].copy()
        
        # Add computed fields useful for Tableau
        taz_clean['TAZ_AREA_SQMI'] = taz_clean.geometry.area / (1609.34**2)  # Convert to square miles
        
        # Save to file
        output_path = os.path.join(self.output_dir, 'taz_boundaries_tableau.shp')
        taz_clean.to_file(output_path)
        
        print(f"   ✅ TAZ shapefile saved: {output_path}")
        print(f"   Final columns: {list(taz_clean.columns)}")
        print(f"   TAZ ID range: {taz_clean['TAZ_ID'].min()} - {taz_clean['TAZ_ID'].max()}")
        
        return output_path
        
    def prepare_puma_shapefile(self):
        """Prepare PUMA shapefile with standardized join fields."""
        print(f"\n🗺️  Processing PUMA shapefile...")
        
        # Find PUMA shapefile
        puma_patterns = ['puma', 'puma20']
        puma_shapefile = self.find_shapefile(puma_patterns)
        
        if not puma_shapefile:
            print(f"   ❌ PUMA shapefile not found")
            return None
            
        # Load shapefile
        puma_gdf = gpd.read_file(puma_shapefile)
        print(f"   Loaded {len(puma_gdf):,} PUMA features")
        print(f"   Original columns: {list(puma_gdf.columns)}")
        
        # Filter for California if needed
        if 'STATEFP' in puma_gdf.columns:
            puma_gdf = puma_gdf[puma_gdf['STATEFP'] == '06']
        elif 'STATEFP20' in puma_gdf.columns:
            puma_gdf = puma_gdf[puma_gdf['STATEFP20'] == '06']
            
        print(f"   California PUMAs: {len(puma_gdf):,}")
        
        # Identify PUMA ID field
        puma_id_field = None
        for field in ['PUMACE20', 'PUMACE', 'PUMA20', 'PUMA']:
            if field in puma_gdf.columns:
                puma_id_field = field
                break
                
        if not puma_id_field:
            print(f"   ❌ No PUMA ID field found")
            return None
            
        print(f"   Using PUMA ID field: {puma_id_field}")
        
        # Standardize PUMA ID field
        puma_gdf['PUMA_ID'] = puma_gdf[puma_id_field].astype(str).str.zfill(5)
        puma_gdf['PUMA_ID_INT'] = puma_gdf['PUMA_ID'].astype(int)
        
        # Keep essential fields for Tableau
        keep_fields = ['PUMA_ID', 'PUMA_ID_INT', 'geometry']
        
        # Add name field if available
        name_fields = ['NAME20', 'NAME', 'NAMELSAD20', 'NAMELSAD']
        for field in name_fields:
            if field in puma_gdf.columns:
                keep_fields.append(field)
                break
                
        # Select and clean columns
        puma_clean = puma_gdf[keep_fields].copy()
        
        # Add computed fields useful for Tableau
        puma_clean['PUMA_AREA_SQMI'] = puma_clean.geometry.area / (1609.34**2)  # Convert to square miles
        
        # Save to file
        output_path = os.path.join(self.output_dir, 'puma_boundaries_tableau.shp')
        puma_clean.to_file(output_path)
        
        print(f"   ✅ PUMA shapefile saved: {output_path}")
        print(f"   Final columns: {list(puma_clean.columns)}")
        print(f"   PUMA ID range: {puma_clean['PUMA_ID'].min()} - {puma_clean['PUMA_ID'].max()}")
        
        return output_path
        
    def prepare_taz_marginals(self):
        """Prepare TAZ marginals with standardized join fields."""
        print(f"\n📊 Processing TAZ marginals...")
        
        taz_file = os.path.join(self.data_dir, 'taz_marginals.csv')
        if not os.path.exists(taz_file):
            print(f"   ❌ TAZ marginals not found: {taz_file}")
            return None
            
        # Load data
        taz_df = pd.read_csv(taz_file)
        print(f"   Loaded {len(taz_df):,} TAZ records")
        print(f"   Original columns: {list(taz_df.columns)}")
        
        # Standardize TAZ ID field
        if 'TAZ' in taz_df.columns:
            taz_df['TAZ_ID'] = taz_df['TAZ'].astype(int)
        else:
            print(f"   ❌ No TAZ field found")
            return None
            
        # Ensure all numeric fields are proper types for Tableau
        numeric_cols = []
        for col in taz_df.columns:
            if col not in ['TAZ', 'TAZ_ID']:
                if pd.api.types.is_numeric_dtype(taz_df[col]):
                    # Convert to int if possible (for count data), otherwise float
                    if taz_df[col].notna().all() and (taz_df[col] % 1 == 0).all():
                        taz_df[col] = taz_df[col].astype(int)
                        numeric_cols.append(col)
                    else:
                        taz_df[col] = taz_df[col].astype(float)
                        numeric_cols.append(col)
        
        print(f"   Numeric columns: {len(numeric_cols)}")
        
        # Save to file
        output_path = os.path.join(self.output_dir, 'taz_marginals_tableau.csv')
        taz_df.to_csv(output_path, index=False)
        
        print(f"   ✅ TAZ marginals saved: {output_path}")
        print(f"   TAZ ID range: {taz_df['TAZ_ID'].min()} - {taz_df['TAZ_ID'].max()}")
        
        return output_path
        
    def prepare_maz_marginals(self):
        """Prepare MAZ marginals with standardized join fields."""
        print(f"\n📊 Processing MAZ marginals...")
        
        maz_file = os.path.join(self.data_dir, 'maz_marginals.csv')
        if not os.path.exists(maz_file):
            print(f"   ❌ MAZ marginals not found: {maz_file}")
            return None
            
        # Load data
        maz_df = pd.read_csv(maz_file)
        print(f"   Loaded {len(maz_df):,} MAZ records")
        print(f"   Original columns: {list(maz_df.columns)}")
        
        # Standardize MAZ ID field
        if 'MAZ' in maz_df.columns:
            maz_df['MAZ_ID'] = maz_df['MAZ'].astype(int)
        else:
            print(f"   ❌ No MAZ field found")
            return None
            
        # Ensure all numeric fields are proper types for Tableau
        numeric_cols = []
        for col in maz_df.columns:
            if col not in ['MAZ', 'MAZ_ID']:
                if pd.api.types.is_numeric_dtype(maz_df[col]):
                    # Convert to int if possible (for count data), otherwise float
                    if maz_df[col].notna().all() and (maz_df[col] % 1 == 0).all():
                        maz_df[col] = maz_df[col].astype(int)
                        numeric_cols.append(col)
                    else:
                        maz_df[col] = maz_df[col].astype(float)
                        numeric_cols.append(col)
        
        print(f"   Numeric columns: {len(numeric_cols)}")
        
        # Save to file
        output_path = os.path.join(self.output_dir, 'maz_marginals_tableau.csv')
        maz_df.to_csv(output_path, index=False)
        
        print(f"   ✅ MAZ marginals saved: {output_path}")
        print(f"   MAZ ID range: {maz_df['MAZ_ID'].min()} - {maz_df['MAZ_ID'].max()}")
        
        return output_path
        
    def prepare_geo_crosswalk(self):
        """Prepare geographic crosswalk with standardized join fields."""
        print(f"\n🔗 Processing geographic crosswalk...")
        
        # Try both original and updated crosswalk files
        crosswalk_files = [
            'geo_cross_walk_tm2_updated.csv',
            'geo_cross_walk_tm2.csv'
        ]
        
        crosswalk_file = None
        for filename in crosswalk_files:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                crosswalk_file = filepath
                break
                
        if not crosswalk_file:
            print(f"   ❌ Geographic crosswalk not found")
            return None
            
        # Load data
        geo_df = pd.read_csv(crosswalk_file)
        print(f"   Loaded {len(geo_df):,} crosswalk records")
        print(f"   Using file: {os.path.basename(crosswalk_file)}")
        print(f"   Original columns: {list(geo_df.columns)}")
        
        # Standardize all ID fields
        if 'MAZ' in geo_df.columns:
            geo_df['MAZ_ID'] = geo_df['MAZ'].astype(int)
        if 'TAZ' in geo_df.columns:
            geo_df['TAZ_ID'] = geo_df['TAZ'].astype(int)
        if 'COUNTY' in geo_df.columns:
            geo_df['COUNTY_ID'] = geo_df['COUNTY'].astype(int)
        if 'PUMA' in geo_df.columns:
            # Handle PUMA as both string and integer
            geo_df['PUMA_ID'] = geo_df['PUMA'].astype(str).str.zfill(5)
            geo_df['PUMA_ID_INT'] = geo_df['PUMA_ID'].astype(int)
            
        # Add county name standardization if needed
        if 'county_name' in geo_df.columns:
            geo_df['COUNTY_NAME'] = geo_df['county_name'].astype(str)
            
        # Select final columns for Tableau
        tableau_cols = []
        
        # Always include ID fields if they exist
        id_mapping = {
            'MAZ_ID': 'MAZ',
            'TAZ_ID': 'TAZ', 
            'COUNTY_ID': 'COUNTY',
            'PUMA_ID': 'PUMA',
            'PUMA_ID_INT': 'PUMA',
            'COUNTY_NAME': 'county_name'
        }
        
        for new_col, orig_col in id_mapping.items():
            if new_col in geo_df.columns:
                tableau_cols.append(new_col)
            elif orig_col in geo_df.columns:
                tableau_cols.append(orig_col)
                
        geo_clean = geo_df[tableau_cols].copy()
        
        # Save to file
        output_path = os.path.join(self.output_dir, 'geo_crosswalk_tableau.csv')
        geo_clean.to_csv(output_path, index=False)
        
        print(f"   ✅ Geographic crosswalk saved: {output_path}")
        print(f"   Final columns: {list(geo_clean.columns)}")
        
        # Show unique counts for each geography
        for col in ['MAZ_ID', 'TAZ_ID', 'COUNTY_ID', 'PUMA_ID_INT']:
            if col in geo_clean.columns:
                unique_count = geo_clean[col].nunique()
                min_val = geo_clean[col].min()
                max_val = geo_clean[col].max()
                print(f"   {col}: {unique_count:,} unique values ({min_val} - {max_val})")
        
        return output_path
        
    def create_tableau_readme(self):
        """Create a README file explaining the Tableau-ready data structure."""
        readme_content = """
# PopulationSim Data for Tableau

This directory contains PopulationSim data prepared for Tableau analysis with standardized join fields.

## Files Overview

### Geographic Boundaries
- `taz_boundaries_tableau.shp` - TAZ (Traffic Analysis Zone) boundaries
- `puma_boundaries_tableau.shp` - PUMA (Public Use Microdata Area) boundaries

### Control Data  
- `taz_marginals_tableau.csv` - Population control totals by TAZ
- `maz_marginals_tableau.csv` - Population control totals by MAZ (Micro Analysis Zone)

### Geographic Relationships
- `geo_crosswalk_tableau.csv` - Mapping between MAZ, TAZ, COUNTY, and PUMA geographies

## Standardized Join Fields

All files use consistent field naming and data types for seamless joins:

### TAZ Data
- **TAZ_ID** (Integer) - Traffic Analysis Zone identifier
- Used in: taz_boundaries_tableau.shp, taz_marginals_tableau.csv, geo_crosswalk_tableau.csv

### MAZ Data  
- **MAZ_ID** (Integer) - Micro Analysis Zone identifier
- Used in: maz_marginals_tableau.csv, geo_crosswalk_tableau.csv

### PUMA Data
- **PUMA_ID** (String) - 5-character PUMA code (e.g., "01301")
- **PUMA_ID_INT** (Integer) - PUMA code as integer (e.g., 1301)
- Used in: puma_boundaries_tableau.shp, geo_crosswalk_tableau.csv

### County Data
- **COUNTY_ID** (Integer) - County FIPS code
- **COUNTY_NAME** (String) - County name
- Used in: geo_crosswalk_tableau.csv

## Recommended Tableau Joins

1. **TAZ Analysis**: Join taz_boundaries_tableau.shp with taz_marginals_tableau.csv on TAZ_ID
2. **PUMA Analysis**: Join puma_boundaries_tableau.shp with geo_crosswalk_tableau.csv on PUMA_ID_INT
3. **Cross-Geography Analysis**: Use geo_crosswalk_tableau.csv to aggregate between geography levels

## Data Quality Notes

- All geographic ID fields are validated and cleaned
- Numeric control data is properly typed (integers for counts, floats for rates)
- Missing values are preserved for transparency
- Coordinate reference system: [as original shapefiles]

## Usage Tips

1. Import shapefiles first to establish spatial context
2. Use geo_crosswalk_tableau.csv as the central linking table
3. Filter data by COUNTY_NAME for sub-regional analysis
4. Aggregate MAZ data to TAZ level using geo_crosswalk relationships

Generated on: {timestamp}
PopulationSim Version: TM2
        """.strip()
        
        from datetime import datetime
        readme_content = readme_content.replace('{timestamp}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        readme_path = os.path.join(self.output_dir, 'README_Tableau_Data.md')
        with open(readme_path, 'w') as f:
            f.write(readme_content)
            
        print(f"\n📖 README file created: {readme_path}")
        
    def prepare_all_data(self):
        """Prepare all data files for Tableau."""
        
        results = {}
        
        # Process each data type
        results['taz_shapefile'] = self.prepare_taz_shapefile()
        results['puma_shapefile'] = self.prepare_puma_shapefile()
        results['taz_marginals'] = self.prepare_taz_marginals()
        results['maz_marginals'] = self.prepare_maz_marginals()
        results['geo_crosswalk'] = self.prepare_geo_crosswalk()
        
        # Create documentation
        self.create_tableau_readme()
        
        # Summary
        print(f"\n📋 TABLEAU DATA PREPARATION SUMMARY")
        print("="*50)
        
        successful = 0
        for data_type, result in results.items():
            status = "✅ SUCCESS" if result else "❌ FAILED"
            print(f"{data_type:20} {status}")
            if result:
                successful += 1
                
        print(f"\nSuccessfully prepared: {successful}/{len(results)} data files")
        print(f"Output directory: {self.output_dir}")
        
        if successful > 0:
            print(f"\n🎉 Ready for Tableau! Check the README file for usage instructions.")
        
        return results


def main():
    """Main function to prepare all Tableau data."""
    
    # Initialize data preparer
    preparer = TableauDataPreparer()
    
    # Prepare all data
    results = preparer.prepare_all_data()
    
    return results


if __name__ == "__main__":
    main()
