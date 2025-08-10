#!/usr/bin/env python3
"""
Test the updated seed population configuration
"""
import sys
sys.path.append('.')

from create_seed_population_tm2_refactored import SeedPopulationConfig

try:
    config = SeedPopulationConfig()
    print('✅ Configuration loaded successfully')
    print(f'Bay Area PUMAs count: {len(config.bay_area_pumas)}')
    print(f'PUMA format: {type(config.bay_area_pumas[0])}')
    print(f'Sample PUMAs: {config.bay_area_pumas[:10]}')
    
    # Test the county mapping
    from create_seed_population_tm2_refactored import PUMACountyMapper
    mapper = PUMACountyMapper()
    county_map = mapper.get_county_mapping()
    print(f'County mapping entries: {len(county_map)}')
    print(f'Sample mapping: {list(county_map.items())[:5]}')
    
except Exception as e:
    print(f'❌ Error: {e}')
