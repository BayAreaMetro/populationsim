import pandas as pd
import geopandas as gpd
from tm2_control_utils.taz_mapper import TAZMapper

# Create mapper and load data
mapper = TAZMapper()
merged_data = mapper.merge_data()

print("=== MERGE VERIFICATION ===")
print(f"Total records: {len(merged_data)}")
print(f"Records with control data: {len(merged_data.dropna(subset=['hh_inc_30']))}")

# Check available columns
control_columns = [col for col in merged_data.columns if col.startswith(('hh_', 'pers_'))]
print(f"Available control columns: {len(control_columns)}")
print("Control columns:", control_columns)

# Sample data verification
print("\n=== SAMPLE DATA ===")
sample_cols = ['taz', 'TAZ', 'hh_inc_30', 'hh_inc_30_60', 'pers_age_00_19']
available_cols = [col for col in sample_cols if col in merged_data.columns]
print(merged_data[available_cols].head(10))

print(f"\n✅ Dashboard should now show all {len(control_columns)} control variables!")
print("🌐 The dashboard has been updated and should be showing in your browser.")
