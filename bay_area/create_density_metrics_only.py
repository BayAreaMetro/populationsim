#!/usr/bin/env python3
"""
Extract only density metrics for Tableau mapping with dropdown selection

This script creates clean CSV files containing only the density metrics (per square mile)
from the prepared Tableau data, making it easy to create dropdown parameter controls
in Tableau for metric selection.

Usage:
    python create_density_metrics_only.py
"""

import pandas as pd
import os
import numpy as np

def get_custom_metric_order():
    """
    Define custom order for metrics in Tableau dropdown.
    Edit this list to change the order of metrics in your dropdown.
    """
    # TAZ metrics in desired display order
    taz_metric_order = [
        # Population and Demographics (most common)
        'total_pop_per_sqmi',           # Total Population
        'pers_age_00_19_per_sqmi',      # Children/Teens (0-19)
        'pers_age_20_34_per_sqmi',      # Young Adults (20-34)
        'pers_age_35_64_per_sqmi',      # Middle Age (35-64)
        'pers_age_65_plus_per_sqmi',    # Seniors (65+)
        
        # Households (second priority)
        'num_hh_per_sqmi',              # Total Households
        'hh_size_1_per_sqmi',           # Single Person Households
        'hh_size_2_per_sqmi',           # 2-Person Households
        'hh_size_3_per_sqmi',           # 3-Person Households
        'hh_size_4_plus_per_sqmi',      # Large Households (4+)
        
        # Family Structure
        'hh_kids_no_per_sqmi',          # Households without Kids
        'hh_kids_yes_per_sqmi',         # Households with Kids
        
        # Income (economic indicators)
        'hh_inc_30_per_sqmi',           # Low Income (<$30K)
        'hh_inc_30_60_per_sqmi',        # Lower Middle Income ($30-60K)
        'hh_inc_60_100_per_sqmi',       # Upper Middle Income ($60-100K)
        'hh_inc_100_plus_per_sqmi',     # High Income ($100K+)
        
        # Employment
        'hh_wrks_0_per_sqmi',           # No Workers
        'hh_wrks_1_per_sqmi',           # 1 Worker
        'hh_wrks_2_per_sqmi',           # 2 Workers
        'hh_wrks_3_plus_per_sqmi',      # 3+ Workers
    ]
    
    # MAZ metrics in desired display order
    maz_metric_order = [
        'total_pop_per_sqmi',           # Total Population
        'num_hh_per_sqmi',              # Total Households
        'gq_pop_per_sqmi',              # Group Quarters Population
        'gq_university_per_sqmi',       # University Group Quarters
        'gq_military_per_sqmi',         # Military Group Quarters
        'gq_other_per_sqmi',            # Other Group Quarters
    ]
    
    return taz_metric_order, maz_metric_order

def create_custom_metric_names():
    """
    Define custom display names for metrics.
    Edit these names to change how they appear in Tableau dropdown.
    """
    metric_display_names = {
        # Population Demographics
        'total_pop_per_sqmi': 'Total Population',
        'pers_age_00_19_per_sqmi': 'Population: Children & Teens (Age 0-19)',
        'pers_age_20_34_per_sqmi': 'Population: Young Adults (Age 20-34)',
        'pers_age_35_64_per_sqmi': 'Population: Middle Age (Age 35-64)',
        'pers_age_65_plus_per_sqmi': 'Population: Seniors (Age 65+)',
        
        # Household Counts
        'num_hh_per_sqmi': 'Total Households',
        'hh_size_1_per_sqmi': 'Households: Single Person',
        'hh_size_2_per_sqmi': 'Households: 2 People',
        'hh_size_3_per_sqmi': 'Households: 3 People',
        'hh_size_4_plus_per_sqmi': 'Households: 4+ People',
        
        # Family Structure
        'hh_kids_no_per_sqmi': 'Households: No Children',
        'hh_kids_yes_per_sqmi': 'Households: With Children',
        
        # Income Categories
        'hh_inc_30_per_sqmi': 'Households: Low Income (Under $30K)',
        'hh_inc_30_60_per_sqmi': 'Households: Lower Middle Income ($30-60K)',
        'hh_inc_60_100_per_sqmi': 'Households: Upper Middle Income ($60-100K)',
        'hh_inc_100_plus_per_sqmi': 'Households: High Income ($100K+)',
        
        # Employment
        'hh_wrks_0_per_sqmi': 'Households: No Workers',
        'hh_wrks_1_per_sqmi': 'Households: 1 Worker',
        'hh_wrks_2_per_sqmi': 'Households: 2 Workers',
        'hh_wrks_3_plus_per_sqmi': 'Households: 3+ Workers',
        
        # Group Quarters (MAZ specific)
        'gq_pop_per_sqmi': 'Group Quarters: Total Population',
        'gq_university_per_sqmi': 'Group Quarters: University',
        'gq_military_per_sqmi': 'Group Quarters: Military',
        'gq_other_per_sqmi': 'Group Quarters: Other',
        
        # Technical fields (usually not needed for display)
        'TAZ_per_sqmi': 'TAZ Density (Technical)',
        'MAZ_per_sqmi': 'MAZ Density (Technical)',
        'hh_from_maz_per_sqmi': 'Households from MAZ (Technical)',
    }
    
    return metric_display_names

def extract_density_metrics():
    """Extract only density metrics from prepared Tableau data."""
    
    tableau_dir = "output_2023/tableau"
    
    print("="*80)
    print("EXTRACTING DENSITY METRICS FOR TABLEAU DROPDOWN")
    print("="*80)
    
    # Get custom metric ordering and display names
    taz_metric_order, maz_metric_order = get_custom_metric_order()
    metric_display_names = create_custom_metric_names()
    
    # Process TAZ density metrics
    print("\n📊 Processing TAZ density metrics...")
    taz_file = os.path.join(tableau_dir, 'taz_marginals_tableau.csv')
    
    if os.path.exists(taz_file):
        taz_df = pd.read_csv(taz_file)
        print(f"   Loaded {len(taz_df):,} TAZ records")
        
        # Find all density columns (ending with _per_sqmi)
        available_density_cols = [col for col in taz_df.columns if col.endswith('_per_sqmi')]
        print(f"   Found {len(available_density_cols)} total density metrics")
        
        # Use custom order, but only include metrics that actually exist
        density_cols = []
        for ordered_col in taz_metric_order:
            if ordered_col in available_density_cols:
                density_cols.append(ordered_col)
        
        # Add any remaining metrics not in our custom order (in case new ones were added)
        for col in available_density_cols:
            if col not in density_cols:
                density_cols.append(col)
        
        # Create clean metric names using custom display names
        metric_names = []
        for col in density_cols:
            if col in metric_display_names:
                clean_name = metric_display_names[col]
            else:
                # Fallback to automatic naming for any new metrics
                clean_name = col.replace('_per_sqmi', '').replace('_', ' ').title()
            metric_names.append(clean_name)
        
        print(f"   Ordered density metrics:")
        for i, (col, name) in enumerate(zip(density_cols, metric_names)):
            print(f"      {i+1:2d}. {name}")
            print(f"          Code: {col}")
        
        # Create the density-only dataset
        keep_cols = ['TAZ_ID', 'TAZ_AREA_SQMI'] + density_cols
        taz_density = taz_df[keep_cols].copy()
        
        # Reshape data for Tableau dropdown (long format)
        # This creates one row per TAZ per metric
        taz_long = pd.melt(
            taz_density, 
            id_vars=['TAZ_ID', 'TAZ_AREA_SQMI'],
            value_vars=density_cols,
            var_name='Metric_Code',
            value_name='Density_Per_SqMi'
        )
        
        # Add clean metric names using our custom mapping
        metric_mapping = dict(zip(density_cols, metric_names))
        taz_long['Metric_Name'] = taz_long['Metric_Code'].map(metric_mapping)
        
        # Reorder columns
        taz_long = taz_long[['TAZ_ID', 'Metric_Name', 'Metric_Code', 'Density_Per_SqMi', 'TAZ_AREA_SQMI']]
        
        # Save long format for dropdown
        output_file = os.path.join(tableau_dir, 'taz_density_metrics_dropdown.csv')
        taz_long.to_csv(output_file, index=False)
        print(f"   ✅ TAZ density metrics saved: {output_file}")
        print(f"   Format: {len(taz_long):,} rows (TAZ × Metrics)")
        
        # Also save wide format for reference
        output_file_wide = os.path.join(tableau_dir, 'taz_density_metrics_wide.csv')
        taz_density.to_csv(output_file_wide, index=False)
        print(f"   ✅ TAZ density metrics (wide) saved: {output_file_wide}")
        
        taz_results = {
            'long_format': output_file,
            'wide_format': output_file_wide,
            'metrics_count': len(density_cols),
            'records_count': len(taz_df)
        }
    else:
        print(f"   ❌ TAZ marginals file not found: {taz_file}")
        taz_results = None
    
    # Process MAZ density metrics
    print("\n📊 Processing MAZ density metrics...")
    maz_file = os.path.join(tableau_dir, 'maz_marginals_tableau.csv')
    
    if os.path.exists(maz_file):
        maz_df = pd.read_csv(maz_file)
        print(f"   Loaded {len(maz_df):,} MAZ records")
        
        # Find all density columns (ending with _per_sqmi)
        available_density_cols = [col for col in maz_df.columns if col.endswith('_per_sqmi')]
        print(f"   Found {len(available_density_cols)} total density metrics")
        
        # Use custom order, but only include metrics that actually exist
        density_cols = []
        for ordered_col in maz_metric_order:
            if ordered_col in available_density_cols:
                density_cols.append(ordered_col)
        
        # Add any remaining metrics not in our custom order
        for col in available_density_cols:
            if col not in density_cols:
                density_cols.append(col)
        
        # Create clean metric names using custom display names
        metric_names = []
        for col in density_cols:
            if col in metric_display_names:
                clean_name = metric_display_names[col]
            else:
                # Fallback to automatic naming for any new metrics
                clean_name = col.replace('_per_sqmi', '').replace('_', ' ').title()
            metric_names.append(clean_name)
        
        print(f"   Ordered density metrics:")
        for i, (col, name) in enumerate(zip(density_cols, metric_names)):
            print(f"      {i+1:2d}. {name}")
            print(f"          Code: {col}")
        
        # Create the density-only dataset
        keep_cols = ['MAZ_ID', 'MAZ_AREA_SQMI'] + density_cols
        maz_density = maz_df[keep_cols].copy()
        
        # Reshape data for Tableau dropdown (long format)
        # This creates one row per MAZ per metric
        maz_long = pd.melt(
            maz_density, 
            id_vars=['MAZ_ID', 'MAZ_AREA_SQMI'],
            value_vars=density_cols,
            var_name='Metric_Code',
            value_name='Density_Per_SqMi'
        )
        
        # Add clean metric names using our custom mapping
        metric_mapping = dict(zip(density_cols, metric_names))
        maz_long['Metric_Name'] = maz_long['Metric_Code'].map(metric_mapping)
        
        # Reorder columns
        maz_long = maz_long[['MAZ_ID', 'Metric_Name', 'Metric_Code', 'Density_Per_SqMi', 'MAZ_AREA_SQMI']]
        
        # Save long format for dropdown
        output_file = os.path.join(tableau_dir, 'maz_density_metrics_dropdown.csv')
        maz_long.to_csv(output_file, index=False)
        print(f"   ✅ MAZ density metrics saved: {output_file}")
        print(f"   Format: {len(maz_long):,} rows (MAZ × Metrics)")
        
        # Also save wide format for reference
        output_file_wide = os.path.join(tableau_dir, 'maz_density_metrics_wide.csv')
        maz_density.to_csv(output_file_wide, index=False)
        print(f"   ✅ MAZ density metrics (wide) saved: {output_file_wide}")
        
        maz_results = {
            'long_format': output_file,
            'wide_format': output_file_wide,
            'metrics_count': len(density_cols),
            'records_count': len(maz_df)
        }
    else:
        print(f"   ❌ MAZ marginals file not found: {maz_file}")
        maz_results = None
    
    # Create a metrics reference list
    print("\n📋 Creating metrics reference...")
    if taz_results or maz_results:
        # Use TAZ metrics as the master list (MAZ should have similar metrics)
        if taz_results:
            ref_file = os.path.join(tableau_dir, 'taz_marginals_tableau.csv')
            ref_df = pd.read_csv(ref_file)
        else:
            ref_file = os.path.join(tableau_dir, 'maz_marginals_tableau.csv')
            ref_df = pd.read_csv(ref_file)
        
        density_cols = [col for col in ref_df.columns if col.endswith('_per_sqmi')]
        
        # Create metrics reference dataframe
        metrics_ref = []
        for col in density_cols:
            clean_name = col.replace('_per_sqmi', '').replace('_', ' ').title()
            
            # Calculate some basic stats for context
            values = ref_df[col].dropna()
            if len(values) > 0:
                min_val = values.min()
                max_val = values.max()
                median_val = values.median()
                
                metrics_ref.append({
                    'Metric_Name': clean_name,
                    'Metric_Code': col,
                    'Min_Value': round(min_val, 2),
                    'Median_Value': round(median_val, 2),
                    'Max_Value': round(max_val, 2),
                    'Data_Type': 'Density per Square Mile'
                })
        
        metrics_df = pd.DataFrame(metrics_ref)
        metrics_file = os.path.join(tableau_dir, 'density_metrics_reference.csv')
        metrics_df.to_csv(metrics_file, index=False)
        
        print(f"   ✅ Metrics reference saved: {metrics_file}")
        print(f"   Contains {len(metrics_df)} density metrics with statistics")
    
    # Create Tableau usage guide
    create_tableau_usage_guide(tableau_dir, taz_results, maz_results)
    
    # Summary
    print(f"\n📋 DENSITY METRICS EXTRACTION SUMMARY")
    print("="*50)
    
    if taz_results:
        print(f"TAZ Metrics:     ✅ {taz_results['metrics_count']} metrics, {taz_results['records_count']:,} records")
    else:
        print(f"TAZ Metrics:     ❌ Failed")
    
    if maz_results:
        print(f"MAZ Metrics:     ✅ {maz_results['metrics_count']} metrics, {maz_results['records_count']:,} records")
    else:
        print(f"MAZ Metrics:     ❌ Failed")
    
    print(f"\nOutput directory: {tableau_dir}")
    print(f"\n🎯 Ready for Tableau dropdown mapping!")
    
    return {'taz': taz_results, 'maz': maz_results}

def create_tableau_usage_guide(output_dir, taz_results, maz_results):
    """Create usage guide for Tableau dropdown implementation."""
    
    guide_content = """
# Tableau Dropdown Mapping Guide

## Files for Dropdown Implementation

### TAZ (Traffic Analysis Zone) Mapping
- **Main Data**: `taz_density_metrics_dropdown.csv` - Long format for dropdown parameter
- **Reference**: `taz_density_metrics_wide.csv` - Wide format for reference
- **Shapefile**: `taz_boundaries_tableau.shp` - Geographic boundaries

### MAZ (Micro Analysis Zone) Mapping  
- **Main Data**: `maz_density_metrics_dropdown.csv` - Long format for dropdown parameter
- **Reference**: `maz_density_metrics_wide.csv` - Wide format for reference
- **Shapefile**: `maz_boundaries_tableau.shp` - Geographic boundaries

### Reference
- **Metrics List**: `density_metrics_reference.csv` - All available metrics with statistics

## Tableau Implementation Steps

### Step 1: Connect Data Sources
1. Open Tableau Desktop
2. Connect to `taz_density_metrics_dropdown.csv` (or MAZ version)
3. Connect to corresponding shapefile (`taz_boundaries_tableau.shp`)
4. Join on TAZ_ID (or MAZ_ID) field

### Step 2: Create Parameter for Metric Selection
1. Right-click in Data pane → Create Parameter
2. Name: "Select Metric"
3. Data type: String
4. Allowable values: List
5. Add values from the "Metric_Name" field (e.g., "Total Population", "Total Households", etc.)

### Step 3: Create Calculated Field for Dynamic Mapping
```
// Calculated Field: Selected Metric Value
IF [Parameters].[Select Metric] = [Metric_Name] 
THEN [Density_Per_SqMi] 
END
```

### Step 4: Build the Map
1. Drag geographic field (from shapefile) to the map
2. Drag "Selected Metric Value" calculated field to Color
3. Show parameter control for "Select Metric"
4. Add filters as needed (geography, value ranges, etc.)

### Step 5: Format and Style
- Adjust color palette for density values
- Add tooltips showing metric name and value
- Include title that updates with selected metric
- Consider logarithmic color scaling for wide value ranges

## Data Structure

### Long Format Files (for dropdown)
```
TAZ_ID | Metric_Name        | Metric_Code           | Density_Per_SqMi | TAZ_AREA_SQMI
1      | Total Population   | total_pop_per_sqmi    | 1234.56          | 2.45
1      | Total Households   | total_hh_per_sqmi     | 456.78           | 2.45
2      | Total Population   | total_pop_per_sqmi    | 2345.67          | 1.88
2      | Total Households   | total_hh_per_sqmi     | 789.01           | 1.88
```

### Wide Format Files (for reference)
```
TAZ_ID | total_pop_per_sqmi | total_hh_per_sqmi | ... | TAZ_AREA_SQMI
1      | 1234.56           | 456.78            | ... | 2.45
2      | 2345.67           | 789.01            | ... | 1.88
```

## Advanced Tips

### Multiple Geography Analysis
- Create separate data sources for TAZ and MAZ
- Use same parameter across both worksheets
- Create dashboard with geography selector

### Comparative Analysis
- Use wide format files for side-by-side metric comparison
- Create scatter plots of different density metrics
- Build correlation analysis between metrics

### Performance Optimization
- Use data extracts for large datasets
- Filter to specific counties or regions if needed
- Consider aggregating very detailed MAZ data to TAZ level for overview maps

## Troubleshooting

### Common Issues
1. **Parameter not working**: Ensure parameter values exactly match Metric_Name values
2. **Missing data**: Check that join between CSV and shapefile is working correctly
3. **Color scale issues**: Use appropriate color palette and consider data distribution

### Data Quality
- All density values are per square mile for consistent comparison
- Missing/null values are handled appropriately
- Very small geographic areas (<0.001 sq mi) may have extreme density values

Generated: {timestamp}
    """.strip()
    
    from datetime import datetime
    guide_content = guide_content.replace('{timestamp}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    guide_path = os.path.join(output_dir, 'TABLEAU_DROPDOWN_GUIDE.md')
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)
        
    print(f"\n📖 Tableau usage guide created: {guide_path}")

def main():
    """Main function to extract density metrics."""
    return extract_density_metrics()

if __name__ == "__main__":
    main()
