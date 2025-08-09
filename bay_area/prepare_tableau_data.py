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
Output files are saved with "_tableau" suffix in the output_2023/tableau/ directory.

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

try:
    from unified_tm2_config import UnifiedTM2Config
except ImportError:
    print("⚠️  Warning: unified_tm2_config not found, using fallback paths")
    UnifiedTM2Config = None

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
        # Default to tableau subdirectory within data_dir for consolidated structure
        self.output_dir = output_dir or os.path.join(data_dir, "tableau")
        
        # Use unified config if available
        if UnifiedTM2Config and not shapefile_dir:
            config = UnifiedTM2Config()
            self.shapefile_dirs = [str(config.external_paths['tm2py_shapefiles'])]
        else:
            # Shapefile search paths with updated primary location
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
            
        # Load shapefile with compatibility handling
        try:
            taz_gdf = gpd.read_file(taz_shapefile)
            print(f"   Loaded {len(taz_gdf):,} TAZ features")
            print(f"   Original columns: {list(taz_gdf.columns)}")
        except AttributeError as e:
            if "fiona" in str(e) and "path" in str(e):
                print(f"   ⚠️  Fiona compatibility issue detected. Trying alternative method...")
                try:
                    # Alternative method using direct file path
                    import fiona
                    with fiona.open(taz_shapefile) as src:
                        taz_gdf = gpd.GeoDataFrame.from_features(src.values(), crs=src.crs)
                    print(f"   ✅ Successfully loaded {len(taz_gdf):,} TAZ features using alternative method")
                    print(f"   Original columns: {list(taz_gdf.columns)}")
                except Exception as e2:
                    print(f"   ❌ Failed to load TAZ shapefile: {e2}")
                    return None
            else:
                print(f"   ❌ Failed to load TAZ shapefile: {e}")
                return None
        except Exception as e:
            print(f"   ❌ Failed to load TAZ shapefile: {e}")
            return None
        
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
            
        # Load shapefile with compatibility handling
        try:
            puma_gdf = gpd.read_file(puma_shapefile)
            print(f"   Loaded {len(puma_gdf):,} PUMA features")
            print(f"   Original columns: {list(puma_gdf.columns)}")
        except AttributeError as e:
            if "fiona" in str(e) and "path" in str(e):
                print(f"   ⚠️  Fiona compatibility issue detected. Trying alternative method...")
                try:
                    # Alternative method using direct file path
                    import fiona
                    with fiona.open(puma_shapefile) as src:
                        puma_gdf = gpd.GeoDataFrame.from_features(src.values(), crs=src.crs)
                    print(f"   ✅ Successfully loaded {len(puma_gdf):,} PUMA features using alternative method")
                    print(f"   Original columns: {list(puma_gdf.columns)}")
                except Exception as e2:
                    print(f"   ❌ Failed to load PUMA shapefile: {e2}")
                    return None
            else:
                print(f"   ❌ Failed to load PUMA shapefile: {e}")
                return None
        except Exception as e:
            print(f"   ❌ Failed to load PUMA shapefile: {e}")
            return None
        
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
        """Prepare TAZ marginals with standardized join fields and 2015-2023 comparison."""
        print(f"\n📊 Processing TAZ marginals...")
        
        # Load 2023 data
        taz_file_2023 = os.path.join(self.data_dir, 'taz_marginals.csv')
        if not os.path.exists(taz_file_2023):
            print(f"   ❌ 2023 TAZ marginals not found: {taz_file_2023}")
            return None
            
        taz_2023 = pd.read_csv(taz_file_2023)
        print(f"   Loaded {len(taz_2023):,} TAZ records for 2023")
        
        # Standardize TAZ ID field for 2023
        if 'TAZ' in taz_2023.columns:
            taz_2023['TAZ_ID'] = taz_2023['TAZ'].astype(int)
        else:
            print(f"   ❌ No TAZ field found in 2023 data")
            return None
        
        # Load 2015 data for comparison
        taz_file_2015 = os.path.join('example_controls_2015', 'taz2_marginals.csv')
        if os.path.exists(taz_file_2015):
            print(f"   📅 Loading 2015 TAZ data for comparison...")
            taz_2015 = pd.read_csv(taz_file_2015)
            print(f"   Loaded {len(taz_2015):,} TAZ records for 2015")
            
            # Standardize TAZ ID field for 2015
            if 'TAZ' in taz_2015.columns:
                taz_2015['TAZ_ID'] = taz_2015['TAZ'].astype(int)
            else:
                print(f"   ❌ No TAZ field found in 2015 data")
                taz_2015 = None
        else:
            print(f"   ⚠️  2015 TAZ data not found: {taz_file_2015}")
            taz_2015 = None
        
        # Start with 2023 data
        final_df = taz_2023.copy()
        
        # Add 2015 comparison if available
        if taz_2015 is not None:
            print(f"   🔄 Creating 2015-2023 comparison columns...")
            
            # Find common columns between 2015 and 2023 (excluding TAZ/TAZ_ID)
            cols_2023 = set(taz_2023.columns) - {'TAZ', 'TAZ_ID'}
            cols_2015 = set(taz_2015.columns) - {'TAZ', 'TAZ_ID'}
            common_cols = sorted(cols_2023.intersection(cols_2015))
            
            print(f"   Common data columns: {len(common_cols)}")
            print(f"   Columns for comparison: {common_cols}")
            
            # Join 2015 data to 2023 data
            taz_2015_subset = taz_2015[['TAZ_ID'] + common_cols].copy()
            
            # Add suffix to 2015 columns for clarity
            rename_dict = {col: f"{col}_2015" for col in common_cols}
            taz_2015_subset = taz_2015_subset.rename(columns=rename_dict)
            
            # Merge with 2023 data
            final_df = final_df.merge(taz_2015_subset, on='TAZ_ID', how='left')
            
            # Create difference columns for common indicators
            diff_cols_created = 0
            for col in common_cols:
                col_2023 = col
                col_2015 = f"{col}_2015"
                diff_col = f"{col}_2023-2015_diff"
                
                if col_2023 in final_df.columns and col_2015 in final_df.columns:
                    final_df[diff_col] = final_df[col_2023] - final_df[col_2015]
                    diff_cols_created += 1
            
            print(f"   ✅ Created {diff_cols_created} difference columns")
            
            # Summary of changes
            if diff_cols_created > 0:
                print(f"   📈 Sample changes (TAZ 1):")
                sample_taz = final_df[final_df['TAZ_ID'] == 1].iloc[0] if len(final_df[final_df['TAZ_ID'] == 1]) > 0 else None
                if sample_taz is not None:
                    for col in common_cols[:3]:  # Show first 3 for brevity
                        val_2023 = sample_taz[col]
                        val_2015 = sample_taz[f"{col}_2015"]
                        diff = sample_taz[f"{col}_2023-2015_diff"]
                        print(f"      {col}: 2015={val_2015}, 2023={val_2023}, diff={diff}")
        
        # Ensure all numeric fields are proper types for Tableau
        numeric_cols = []
        for col in final_df.columns:
            if col not in ['TAZ', 'TAZ_ID']:
                if pd.api.types.is_numeric_dtype(final_df[col]):
                    # Convert to int if possible (for count data), otherwise float
                    if final_df[col].notna().all() and (final_df[col] % 1 == 0).all():
                        final_df[col] = final_df[col].astype(int)
                        numeric_cols.append(col)
                    else:
                        final_df[col] = final_df[col].astype(float)
                        numeric_cols.append(col)
        
        print(f"   Numeric columns: {len(numeric_cols)}")
        print(f"   Final columns: {len(final_df.columns)}")
        
        # Save to file
        output_path = os.path.join(self.output_dir, 'taz_marginals_tableau.csv')
        final_df.to_csv(output_path, index=False)
        
        print(f"   ✅ TAZ marginals saved: {output_path}")
        print(f"   TAZ ID range: {final_df['TAZ_ID'].min()} - {final_df['TAZ_ID'].max()}")
        
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
