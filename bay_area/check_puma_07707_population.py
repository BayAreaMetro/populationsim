"""
Check Census population data for PUMA 07707 to understand if it should have households
"""
import pandas as pd
import requests
import json

def check_puma_07707_population():
    """Check Census ACS population data for PUMA 07707"""
    
    print("=" * 70)
    print("CHECKING CENSUS POPULATION DATA FOR PUMA 07707")
    print("=" * 70)
    
    # Census API for ACS 5-year estimates
    # We'll check 2019-2023 (most recent) and compare with 2015-2019
    
    print("🔍 Checking ACS 2019-2023 population data for PUMA 07707...")
    
    # ACS API endpoint for PUMA-level data
    # B01003_001E = Total Population
    # B25001_001E = Total Housing Units
    # B25003_001E = Total Occupied Housing Units
    
    try:
        # Check 2022 ACS 5-year estimates (most recent available)
        url_2022 = "https://api.census.gov/data/2022/acs/acs5"
        params_2022 = {
            'get': 'B01003_001E,B25001_001E,B25003_001E,NAME',
            'for': 'public use microdata area:07707',
            'in': 'state:06'  # California
        }
        
        print(f"   Requesting 2022 ACS data for PUMA 07707...")
        response_2022 = requests.get(url_2022, params=params_2022, timeout=30)
        
        if response_2022.status_code == 200:
            data_2022 = response_2022.json()
            print(f"   ✅ 2022 ACS Response received")
            
            if len(data_2022) > 1:  # First row is headers
                headers = data_2022[0]
                values = data_2022[1]
                
                pop_total = values[0] if values[0] != 'null' else 'N/A'
                housing_total = values[1] if values[1] != 'null' else 'N/A'
                housing_occupied = values[2] if values[2] != 'null' else 'N/A'
                name = values[3]
                
                print(f"   📊 2022 ACS Data for {name}:")
                print(f"      Total Population: {pop_total}")
                print(f"      Total Housing Units: {housing_total}")
                print(f"      Occupied Housing Units: {housing_occupied}")
                
                # Calculate if this should have PUMS households
                if pop_total != 'N/A' and pop_total != '0':
                    pop_int = int(pop_total)
                    print(f"   📈 Analysis:")
                    print(f"      Population: {pop_int:,}")
                    if pop_int > 50000:
                        print(f"      🚨 SIGNIFICANT POPULATION - Should appear in PUMS!")
                    elif pop_int > 10000:
                        print(f"      ⚠️  Moderate population - Might appear in PUMS")
                    else:
                        print(f"      ✅ Low population - Normal to be absent from PUMS")
            else:
                print(f"   ❌ No data returned for PUMA 07707 in 2022")
        else:
            print(f"   ❌ Failed to get 2022 data: {response_2022.status_code}")
    
    except Exception as e:
        print(f"   ❌ Error getting 2022 data: {e}")
    
    # Also check 2021 data in case 2022 isn't available
    try:
        print(f"\n   Trying 2021 ACS data...")
        url_2021 = "https://api.census.gov/data/2021/acs/acs5"
        params_2021 = {
            'get': 'B01003_001E,B25001_001E,B25003_001E,NAME',
            'for': 'public use microdata area:07707',
            'in': 'state:06'
        }
        
        response_2021 = requests.get(url_2021, params=params_2021, timeout=30)
        
        if response_2021.status_code == 200:
            data_2021 = response_2021.json()
            print(f"   ✅ 2021 ACS Response received")
            
            if len(data_2021) > 1:
                headers = data_2021[0]
                values = data_2021[1]
                
                pop_total = values[0] if values[0] != 'null' else 'N/A'
                housing_total = values[1] if values[1] != 'null' else 'N/A'
                housing_occupied = values[2] if values[2] != 'null' else 'N/A'
                name = values[3]
                
                print(f"   📊 2021 ACS Data for {name}:")
                print(f"      Total Population: {pop_total}")
                print(f"      Total Housing Units: {housing_total}")
                print(f"      Occupied Housing Units: {housing_occupied}")
        else:
            print(f"   ❌ Failed to get 2021 data: {response_2021.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error getting 2021 data: {e}")
    
    # Check our PUMS data to see if we missed it
    print(f"\n🔍 Checking our PUMS 2019-2023 data for any 07707 records...")
    try:
        # Check both the processed and original PUMS files
        pums_files = [
            "M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23/households_final.csv",
            "M:/Data/Census/NewCachedTablesForPopulationSimControls/PUMS_2019-23/persons_final.csv"
        ]
        
        for file_path in pums_files:
            try:
                print(f"   Checking {file_path.split('/')[-1]}...")
                df = pd.read_csv(file_path)
                
                if 'PUMA' in df.columns:
                    puma_07707_records = df[df['PUMA'] == '07707']
                    print(f"      Records with PUMA 07707: {len(puma_07707_records)}")
                    
                    if len(puma_07707_records) > 0:
                        print(f"      🎯 FOUND PUMA 07707 in our data!")
                        print(f"      Sample records:")
                        print(puma_07707_records.head())
                else:
                    print(f"      No PUMA column found")
                    
            except Exception as e:
                print(f"      Error reading {file_path}: {e}")
                
    except Exception as e:
        print(f"   ❌ Error checking PUMS files: {e}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"   1. If PUMA 07707 has significant population (>50k), we should investigate")
    print(f"   2. Check if our PUMS filtering criteria accidentally excluded it")
    print(f"   3. Verify our Bay Area PUMA list is complete")
    print(f"   4. Consider whether transportation model region boundaries are correct")

if __name__ == "__main__":
    check_puma_07707_population()
