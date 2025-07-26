"""
Comprehensive analysis to find all missing PUMAs that should be included in Bay Area seed population
"""
import pandas as pd
import requests
import time

def find_all_missing_pumas():
    """Find all PUMAs in crosswalk that should be added to seed population"""
    
    print("=" * 80)
    print("COMPREHENSIVE BAY AREA PUMA ANALYSIS")
    print("=" * 80)
    
    # Current seed population PUMAs
    CURRENT_SEED_PUMAS = [
        '00101', '00111', '00112', '00113', '00114', '00115', '00116', '00117', '00118', '00119',
        '00120', '00121', '00122', '00123', '01301', '01305', '01308', '01309', '01310', '01311',
        '01312', '01313', '01314', '04103', '04104', '05303', '05500', '07507', '07508', '07509',
        '07510', '07511', '07512', '07513', '07514', '08101', '08102', '08103', '08104', '08105',
        '08106', '08505', '08506', '08507', '08508', '08510', '08511', '08512', '08515', '08516',
        '08517', '08518', '08519', '08520', '08521', '08522', '08701', '09501', '09502', '09503',
        '09702', '09704', '09705', '09706', '11301'
    ]
    
    print(f"📊 Current seed population: {len(CURRENT_SEED_PUMAS)} PUMAs")
    
    # Load updated crosswalk to find all PUMAs
    print(f"🔍 Loading updated crosswalk...")
    crosswalk = pd.read_csv('output_2023/geo_cross_walk_tm2_updated.csv', dtype={'PUMA': str})
    
    all_crosswalk_pumas = sorted(crosswalk['PUMA'].unique())
    missing_pumas = [p for p in all_crosswalk_pumas if p not in CURRENT_SEED_PUMAS]
    
    print(f"📋 All PUMAs in crosswalk: {len(all_crosswalk_pumas)}")
    print(f"🚨 PUMAs missing from seed population: {len(missing_pumas)}")
    print(f"   Missing PUMAs: {missing_pumas}")
    
    # Check population for each missing PUMA
    print(f"\\n🔍 Checking Census population data for missing PUMAs...")
    
    puma_analysis = []
    
    for puma in missing_pumas:
        print(f"\\n   Checking PUMA {puma}...")
        
        try:
            # Try 2022 ACS data first
            url = "https://api.census.gov/data/2022/acs/acs5"
            params = {
                'get': 'B01003_001E,B25001_001E,B25003_001E,NAME',
                'for': f'public use microdata area:{puma}',
                'in': 'state:06'  # California
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if len(data) > 1:  # Headers + data
                    values = data[1]
                    pop_total = values[0] if values[0] != 'null' else '0'
                    housing_total = values[1] if values[1] != 'null' else '0'
                    housing_occupied = values[2] if values[2] != 'null' else '0'
                    name = values[3]
                    
                    # Count MAZs in this PUMA
                    maz_count = len(crosswalk[crosswalk['PUMA'] == puma])
                    
                    analysis = {
                        'PUMA': puma,
                        'Name': name,
                        'Population': int(pop_total) if pop_total.isdigit() else 0,
                        'Housing_Units': int(housing_total) if housing_total.isdigit() else 0,
                        'Occupied_Units': int(housing_occupied) if housing_occupied.isdigit() else 0,
                        'MAZ_Count': maz_count
                    }
                    
                    puma_analysis.append(analysis)
                    
                    print(f"      Population: {analysis['Population']:,}")
                    print(f"      Occupied Housing: {analysis['Occupied_Units']:,}")
                    print(f"      MAZs: {analysis['MAZ_Count']}")
                    
                    # Classify significance
                    if analysis['Population'] >= 100000:
                        print(f"      🚨 CRITICAL - Must include!")
                    elif analysis['Population'] >= 50000:
                        print(f"      ⚠️  HIGH - Should include")
                    elif analysis['Population'] >= 20000:
                        print(f"      📊 MODERATE - Consider including")
                    else:
                        print(f"      ✅ LOW - Acceptable to exclude")
                        
                else:
                    print(f"      ❌ No data returned")
                    puma_analysis.append({
                        'PUMA': puma,
                        'Name': 'No data',
                        'Population': 0,
                        'Housing_Units': 0,
                        'Occupied_Units': 0,
                        'MAZ_Count': len(crosswalk[crosswalk['PUMA'] == puma])
                    })
            else:
                print(f"      ❌ API error: {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
            
        # Small delay to be respectful to Census API
        time.sleep(0.5)
    
    # Create summary DataFrame
    if puma_analysis:
        df_analysis = pd.DataFrame(puma_analysis)
        df_analysis = df_analysis.sort_values('Population', ascending=False)
        
        print(f"\\n📊 MISSING PUMA ANALYSIS SUMMARY:")
        print("="*100)
        
        for _, row in df_analysis.iterrows():
            pop = row['Population']
            name = row['Name'][:50] + "..." if len(row['Name']) > 50 else row['Name']
            
            if pop >= 100000:
                priority = "🚨 CRITICAL"
            elif pop >= 50000:
                priority = "⚠️  HIGH"
            elif pop >= 20000:
                priority = "📊 MODERATE"
            else:
                priority = "✅ LOW"
                
            print(f"{row['PUMA']} | {priority:12} | {pop:8,} | {row['Occupied_Units']:6,} | {row['MAZ_Count']:4} | {name}")
        
        # Generate recommended PUMA list
        critical_pumas = df_analysis[df_analysis['Population'] >= 100000]['PUMA'].tolist()
        high_pumas = df_analysis[df_analysis['Population'] >= 50000]['PUMA'].tolist()
        moderate_pumas = df_analysis[df_analysis['Population'] >= 20000]['PUMA'].tolist()
        
        print(f"\\n💡 RECOMMENDATIONS:")
        print("="*50)
        
        if critical_pumas:
            print(f"🚨 MUST ADD (≥100k population): {critical_pumas}")
        if high_pumas and len(high_pumas) > len(critical_pumas):
            additional_high = [p for p in high_pumas if p not in critical_pumas]
            print(f"⚠️  SHOULD ADD (≥50k population): {additional_high}")
        if moderate_pumas and len(moderate_pumas) > len(high_pumas):
            additional_moderate = [p for p in moderate_pumas if p not in high_pumas]
            print(f"📊 CONSIDER ADDING (≥20k population): {additional_moderate}")
        
        # Generate updated PUMA list
        recommended_additions = high_pumas  # Include all ≥50k population
        new_seed_pumas = sorted(CURRENT_SEED_PUMAS + recommended_additions)
        
        print(f"\\n🎯 UPDATED BAY AREA PUMA LIST:")
        print("="*50)
        print(f"Original count: {len(CURRENT_SEED_PUMAS)}")
        print(f"Recommended additions: {len(recommended_additions)}")
        print(f"New total: {len(new_seed_pumas)}")
        print(f"\\nNew PUMA list:")
        print(new_seed_pumas)
        
        # Save analysis to file
        analysis_file = 'missing_puma_analysis.csv'
        df_analysis.to_csv(analysis_file, index=False)
        print(f"\\n💾 Analysis saved to: {analysis_file}")
        
        # Save updated PUMA list
        with open('updated_bay_area_pumas.txt', 'w') as f:
            f.write("# Updated Bay Area PUMA List\\n")
            f.write(f"# Original: {len(CURRENT_SEED_PUMAS)} PUMAs\\n")
            f.write(f"# Added: {len(recommended_additions)} PUMAs\\n")
            f.write(f"# Total: {len(new_seed_pumas)} PUMAs\\n\\n")
            f.write("BAY_AREA_PUMAS = [\\n")
            for i, puma in enumerate(new_seed_pumas):
                if i % 10 == 0 and i > 0:
                    f.write("\\n")
                f.write(f"    '{puma}',")
                if (i + 1) % 10 == 0:
                    f.write("  # {}-{}".format(new_seed_pumas[i-9:i+1][0], new_seed_pumas[i-9:i+1][-1]))
                f.write("\\n" if (i + 1) % 10 == 0 else " ")
            f.write("\\n]\\n")
        
        print(f"💾 Updated PUMA list saved to: updated_bay_area_pumas.txt")
        
        return new_seed_pumas, recommended_additions
    
    else:
        print("❌ No analysis data available")
        return None, None

if __name__ == "__main__":
    find_all_missing_pumas()
