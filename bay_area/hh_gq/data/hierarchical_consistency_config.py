#!/usr/bin/env python3
"""
Hierarchical Control Consistency Configuration

This module defines the hierarchical relationships between control categories
that must be enforced for PopulationSim to work correctly.

The principle: TOTALS FLOW UP, DISTRIBUTIONS FLOW DOWN
- MAZ level: Base totals from 2020 Census block data
- TAZ level: Category distributions that must sum to MAZ totals
- COUNTY level: Scaling targets that must sum to TAZ totals
"""

from collections import OrderedDict

# ============================================================================
# HIERARCHICAL CONTROL CONSISTENCY RULES
# ============================================================================

# Define which control categories must sum to which totals at each geography level
HIERARCHICAL_CONSISTENCY_RULES = {
    
    # MAZ → TAZ Household Consistency
    'households_maz_to_taz': {
        'description': 'TAZ household categories must sum to MAZ household totals within each TAZ',
        'base_geography': 'MAZ',
        'base_control': 'numhh_gq',  # From MAZ marginals
        'target_geography': 'TAZ', 
        'target_controls': ['hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus'],
        'tolerance_pct': 2.0,  # Allow 2% difference for rounding
        'priority': 'HIGH',
        'action': 'SCALE_PROPORTIONALLY'  # Scale TAZ categories to match MAZ total
    },
    
    # MAZ → TAZ Population Consistency  
    'population_maz_to_taz': {
        'description': 'TAZ age categories must sum to MAZ population totals within each TAZ',
        'base_geography': 'MAZ',
        'base_control': 'total_pop',  # From MAZ marginals (needs to be added)
        'target_geography': 'TAZ',
        'target_controls': ['pers_age_00_19', 'pers_age_20_34', 'pers_age_35_64', 'pers_age_65_plus'],
        'tolerance_pct': 2.0,
        'priority': 'HIGH', 
        'action': 'SCALE_PROPORTIONALLY'
    },
    
    # TAZ Internal Consistency - Household Workers
    'taz_workers_internal': {
        'description': 'TAZ worker categories must sum to TAZ household total',
        'base_geography': 'TAZ',
        'base_control': 'numhh_gq',
        'target_geography': 'TAZ',
        'target_controls': ['hh_wrks_0', 'hh_wrks_1', 'hh_wrks_2', 'hh_wrks_3_plus'],
        'tolerance_pct': 1.0,
        'priority': 'MEDIUM',
        'action': 'SCALE_PROPORTIONALLY'
    },
    
    # TAZ Internal Consistency - Household Kids
    'taz_kids_internal': {
        'description': 'TAZ kids categories must sum to TAZ household total', 
        'base_geography': 'TAZ',
        'base_control': 'numhh_gq',
        'target_geography': 'TAZ',
        'target_controls': ['hh_kids_yes', 'hh_kids_no'],
        'tolerance_pct': 1.0,
        'priority': 'MEDIUM',
        'action': 'SCALE_PROPORTIONALLY'
    },
    
    # TAZ Internal Consistency - Household Income
    'taz_income_internal': {
        'description': 'TAZ income categories must sum to TAZ household total',
        'base_geography': 'TAZ', 
        'base_control': 'numhh_gq',
        'target_geography': 'TAZ',
        'target_controls': ['hh_inc_30', 'hh_inc_30_60', 'hh_inc_60_100', 'hh_inc_100_plus'],
        'tolerance_pct': 1.0,
        'priority': 'MEDIUM',
        'action': 'SCALE_PROPORTIONALLY'
    },
    
    # TAZ → COUNTY Consistency (if county controls exist)
    'taz_to_county_households': {
        'description': 'County household totals must equal sum of TAZ households within county',
        'base_geography': 'TAZ',
        'base_control': 'numhh_gq',
        'target_geography': 'COUNTY',
        'target_controls': ['total_households'],  # If this exists in county controls
        'tolerance_pct': 5.0,  # More tolerance for county level
        'priority': 'LOW',
        'action': 'VALIDATE_ONLY'  # Don't modify, just check
    }
}

# ============================================================================
# CONTROL SCALING PRIORITY
# ============================================================================

# Define the order in which controls should be scaled to maintain consistency
# Higher priority controls are fixed, lower priority controls are adjusted
SCALING_PRIORITY = [
    # 1. MAZ totals are NEVER changed (base truth from Census)
    ('MAZ', ['numhh_gq', 'total_pop', 'gq_pop', 'gq_military', 'gq_university']),
    
    # 2. TAZ totals that must match MAZ sums (highest priority TAZ controls)
    ('TAZ', ['numhh_gq']),  # This should equal sum of MAZ numhh_gq within TAZ
    
    # 3. TAZ major categories (scale these to match totals)
    ('TAZ', ['hh_size_1', 'hh_size_2', 'hh_size_3', 'hh_size_4_plus']),
    ('TAZ', ['pers_age_00_19', 'pers_age_20_34', 'pers_age_35_64', 'pers_age_65_plus']),
    
    # 4. TAZ detailed categories (scale these to match household totals)
    ('TAZ', ['hh_wrks_0', 'hh_wrks_1', 'hh_wrks_2', 'hh_wrks_3_plus']),
    ('TAZ', ['hh_kids_yes', 'hh_kids_no']),
    ('TAZ', ['hh_inc_30', 'hh_inc_30_60', 'hh_inc_60_100', 'hh_inc_100_plus']),
    
    # 5. County controls (validate only, don't modify)
    ('COUNTY', ['all'])
]

# ============================================================================
# SCALING METHODS
# ============================================================================

SCALING_METHODS = {
    'SCALE_PROPORTIONALLY': {
        'description': 'Scale all target controls proportionally to match base total',
        'preserve_ratios': True,
        'minimum_value': 0
    },
    
    'SCALE_WITH_CONSTRAINTS': {
        'description': 'Scale target controls with minimum/maximum constraints',
        'preserve_ratios': True,
        'minimum_value': 1,  # Ensure no zero controls
        'maximum_scaling_factor': 2.0  # Don't scale by more than 200%
    },
    
    'VALIDATE_ONLY': {
        'description': 'Check consistency but do not modify values',
        'preserve_ratios': True,
        'modify': False
    }
}

# ============================================================================
# MISSING CONTROL REQUIREMENTS 
# ============================================================================

# Controls that must be added to ensure hierarchical consistency
REQUIRED_MISSING_CONTROLS = {
    'MAZ': {
        'total_pop': {
            'source': '2020 Census P1_001N (Total Population)',
            'geography': 'block',
            'aggregation': 'sum',
            'description': 'Total population at MAZ level - essential for age control consistency',
            'priority': 'CRITICAL'
        }
    },
    
    'CONTROLS_CSV': {
        'total_pop': {
            'target': 'total_pop',
            'geography': 'MAZ', 
            'seed_table': 'persons',
            'importance': 10000000,
            'control_field': 'total_pop',
            'expression': '(persons.PWGTP > 0) & (persons.PWGTP < np.inf)',
            'description': 'Total population control for hierarchical consistency'
        }
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_consistency_rules_by_priority(priority_level=None):
    """Get consistency rules filtered by priority level"""
    if priority_level is None:
        return HIERARCHICAL_CONSISTENCY_RULES
    
    return {
        rule_name: rule_config 
        for rule_name, rule_config in HIERARCHICAL_CONSISTENCY_RULES.items()
        if rule_config['priority'] == priority_level
    }

def get_scaling_order():
    """Get the order in which controls should be processed for scaling"""
    return SCALING_PRIORITY

def get_required_controls():
    """Get controls that must be added for hierarchical consistency"""
    return REQUIRED_MISSING_CONTROLS

def validate_rule_completeness(available_controls):
    """Check if all controls needed for hierarchical consistency are available"""
    missing_controls = []
    
    for rule_name, rule_config in HIERARCHICAL_CONSISTENCY_RULES.items():
        base_control = rule_config['base_control']
        target_controls = rule_config['target_controls']
        
        # Check if all required controls exist
        all_required = [base_control] + target_controls
        for control in all_required:
            if control not in available_controls:
                missing_controls.append({
                    'rule': rule_name,
                    'missing_control': control,
                    'geography': rule_config.get('base_geography', rule_config.get('target_geography'))
                })
    
    return missing_controls

if __name__ == "__main__":
    print("HIERARCHICAL CONTROL CONSISTENCY CONFIGURATION")
    print("=" * 60)
    
    print(f"\nDefined {len(HIERARCHICAL_CONSISTENCY_RULES)} consistency rules:")
    for rule_name, rule_config in HIERARCHICAL_CONSISTENCY_RULES.items():
        print(f"  {rule_name}: {rule_config['description']}")
    
    print(f"\nScaling priority levels: {len(SCALING_PRIORITY)}")
    print(f"Required missing controls: {len(REQUIRED_MISSING_CONTROLS)}")
