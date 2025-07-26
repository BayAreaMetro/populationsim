import pandas as pd
import geopandas as gpd
from tm2_control_utils.taz_mapper import TAZMapper

# Load the data
mapper = TAZMapper()
taz_data = mapper.load_taz_data()
taz_shapes = mapper.load_taz_shapes()

# Find TAZ 500267
target_taz = 500267
print(f"=== ANALYZING TAZ {target_taz} ===")

# Check if this TAZ exists in our data
taz_row = taz_data[taz_data['TAZ'] == target_taz]
if len(taz_row) == 0:
    print(f"TAZ {target_taz} not found in control data!")
    # Let's see what TAZ values we have around that range
    nearby_tazs = taz_data[(taz_data['TAZ'] >= target_taz - 10) & (taz_data['TAZ'] <= target_taz + 10)]
    print(f"TAZ values near {target_taz}: {sorted(nearby_tazs['TAZ'].tolist())}")
else:
    print("CONTROL DATA:")
    print(taz_row.to_string())
    
    # Get household size breakdown
    hh_size_cols = ['hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus']
    hh_sizes = taz_row[hh_size_cols].iloc[0]
    total_hh = hh_sizes.sum()
    
    print(f"\nHOUSEHOLD SIZE BREAKDOWN:")
    for col, value in hh_sizes.items():
        size_label = col.replace('hh_size_', '').replace('_plus', '+')
        pct = (value / total_hh * 100) if total_hh > 0 else 0
        print(f"  Size {size_label}: {value:,} households ({pct:.1f}%)")
    print(f"  Total households: {total_hh:,}")
    
    # Other characteristics
    print(f"\nOTHER CHARACTERISTICS:")
    print(f"  Age 00-19: {taz_row['pers_age_00_19'].iloc[0]:,}")
    print(f"  Age 20-34: {taz_row['pers_age_20_34'].iloc[0]:,}")
    print(f"  Age 35-64: {taz_row['pers_age_35_64'].iloc[0]:,}")
    print(f"  Age 65+: {taz_row['pers_age_65_plus'].iloc[0]:,}")
    
    income_cols = ['hh_inc_30', 'hh_inc_30_60', 'hh_inc_60_100', 'hh_inc_100_plus']
    print(f"\nINCOME DISTRIBUTION:")
    for col, value in taz_row[income_cols].iloc[0].items():
        income_label = col.replace('hh_inc_', '$').replace('_', 'k-')
        if 'plus' in income_label:
            income_label = income_label.replace('-plus', 'k+')
        else:
            income_label += 'k'
        print(f"  {income_label}: {value:,} households")

# Check shapefile data for geographic context
print(f"\n=== GEOGRAPHIC CONTEXT ===")
shape_row = taz_shapes[taz_shapes['taz'] == target_taz]
if len(shape_row) > 0:
    print("SHAPEFILE DATA:")
    for col in ['taz', 'ALAND10', 'AWATER10', 'blockcount', 'mazcount', 'acres']:
        if col in shape_row.columns:
            value = shape_row[col].iloc[0]
            if col == 'ALAND10':
                print(f"  Land area: {value:,} sq meters ({value/4047:.1f} acres)")
            elif col == 'AWATER10':
                print(f"  Water area: {value:,} sq meters")
            elif col == 'acres':
                print(f"  Total acres: {value:.1f}")
            else:
                print(f"  {col}: {value}")
else:
    print(f"TAZ {target_taz} not found in shapefile!")

# Compare to regional averages
print(f"\n=== COMPARISON TO REGIONAL AVERAGES ===")
regional_avg = taz_data[hh_size_cols].mean()
if len(taz_row) > 0:
    taz_values = taz_row[hh_size_cols].iloc[0]
    print("Household Size Distribution:")
    for col in hh_size_cols:
        size_label = col.replace('hh_size_', '').replace('_plus', '+')
        taz_val = taz_values[col]
        reg_avg = regional_avg[col]
        ratio = taz_val / reg_avg if reg_avg > 0 else 0
        print(f"  Size {size_label}: TAZ={taz_val:,}, Regional Avg={reg_avg:.1f}, Ratio={ratio:.1f}x")

# Find other TAZs with high single-person household counts
print(f"\n=== OTHER HIGH SINGLE-PERSON HOUSEHOLD TAZs ===")
top_single_hh = taz_data.nlargest(10, 'hh_size_1')[['TAZ', 'hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus']]
print("Top 10 TAZs by single-person households:")
print(top_single_hh.to_string(index=False))
