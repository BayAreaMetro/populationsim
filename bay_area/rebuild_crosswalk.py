#!/usr/bin/env python3
"""
Quick script to rebuild the mazs_tazs_all_geog.csv file with correct column naming.
"""

from tm2_control_utils.config_census import rebuild_maz_taz_all_geog_file

if __name__ == "__main__":
    print("Rebuilding mazs_tazs_all_geog.csv with MAZ_NODE/TAZ_NODE columns...")
    success = rebuild_maz_taz_all_geog_file()
    
    if success:
        print("✓ Successfully rebuilt geography file")
    else:
        print("✗ Failed to rebuild geography file")