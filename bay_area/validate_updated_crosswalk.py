"""
Validate that the updated geography crosswalk matches our seed population PUMAs
"""
import pandas as pd
import os

# Define the 54 2020 PUMAs from our seed population
SEED_PUMAS = [
    '00101', '00111', '00112', '00113', '00114', '00115', '00116', '00117', '00118', '00119',
    '00120', '00121', '00122', '00123', '01301', '01305', '01308', '01309', '01310', '01311',
    '01312', '01313', '01314', '04103', '04104', '05303', '05500', '07507', '07508', '07509',
    '07510', '07511', '07512', '07513', '07514', '08101', '08102', '08103', '08104', '08105',
    '08106', '08505', '08506', '08507', '08508', '08510', '08511', '08512', '08515', '08516',
    '08517', '08518', '08519', '08520', '08521', '08522', '08701', '09501', '09502', '09503',
    '09702', '09704', '09705', '09706', '11301'
]

def validate_crosswalk():
    """Validate the updated crosswalk matches our seed population"""
    
    print("=" * 60)
    print("VALIDATING UPDATED GEOGRAPHY CROSSWALK")
    print("=" * 60)
    
    # Load updated crosswalk
    crosswalk_file = 'output_2023/geo_cross_walk_tm2_updated.csv'
    if not os.path.exists(crosswalk_file):
        print(f"❌ Error: Updated crosswalk not found: {crosswalk_file}")
        return False
    
    crosswalk = pd.read_csv(crosswalk_file, dtype={'PUMA': str})
    print(f"📊 Loaded crosswalk: {len(crosswalk):,} records")
    
    # Get unique PUMAs from crosswalk
    crosswalk_pumas = sorted(crosswalk['PUMA'].unique())
    seed_pumas = sorted(SEED_PUMAS)
    
    print(f"\n📈 PUMA Counts:")
    print(f"   Seed population PUMAs: {len(seed_pumas)}")
    print(f"   Crosswalk PUMAs: {len(crosswalk_pumas)}")
    
    # Check for exact match
    if set(crosswalk_pumas) == set(seed_pumas):
        print(f"\n✅ PERFECT MATCH!")
        print(f"   All {len(seed_pumas)} PUMAs match between seed population and crosswalk")
        return True
    
    # Check if all seed PUMAs are in crosswalk (most important)
    missing_in_crosswalk = set(seed_pumas) - set(crosswalk_pumas)
    extra_in_crosswalk = set(crosswalk_pumas) - set(seed_pumas)
    
    if not missing_in_crosswalk:
        print(f"\n✅ SEED POPULATION FULLY COVERED!")
        print(f"   All {len(seed_pumas)} seed PUMAs are in the crosswalk")
        if extra_in_crosswalk:
            print(f"   Note: {len(extra_in_crosswalk)} additional PUMAs in crosswalk (acceptable)")
        return True
    
    # If not exact match, show differences
    print(f"\n❌ MISMATCH DETECTED:")
    
    # PUMAs in seed but not in crosswalk
    missing_in_crosswalk = set(seed_pumas) - set(crosswalk_pumas)
    if missing_in_crosswalk:
        print(f"\n⚠️  PUMAs in seed population but NOT in crosswalk ({len(missing_in_crosswalk)}):")
        for puma in sorted(missing_in_crosswalk):
            print(f"   {puma}")
    
    # PUMAs in crosswalk but not in seed
    extra_in_crosswalk = set(crosswalk_pumas) - set(seed_pumas)
    if extra_in_crosswalk:
        print(f"\n⚠️  PUMAs in crosswalk but NOT in seed population ({len(extra_in_crosswalk)}):")
        for puma in sorted(extra_in_crosswalk):
            print(f"   {puma}")
    
    # Show PUMA distribution
    print(f"\n📊 PUMA Record Distribution (top 10):")
    puma_counts = crosswalk['PUMA'].value_counts().head(10)
    for puma, count in puma_counts.items():
        print(f"   {puma}: {count:,} MAZs")
    
    return False

if __name__ == "__main__":
    validate_crosswalk()
