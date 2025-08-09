#!/usr/bin/env python3
"""
DEPRECATED: This file has been replaced by unified_tm2_config.py

Please use the new unified configuration system:

OLD (deprecated):
    from config_tm2 import PopulationSimConfig
    config = PopulationSimConfig()

NEW (recommended):
    from unified_tm2_config import config
    paths = config.get_control_paths()  # or other appropriate method

The unified system provides:
- Single source of truth for all paths
- No more hardcoded values
- Intelligent fallback logic
- Environment adaptability

See HARDCODE_ELIMINATION_SUMMARY.md for migration guide.
"""

# Legacy import for backward compatibility (TEMPORARY)
import warnings
warnings.warn(
    "config_tm2.py is deprecated. Please migrate to unified_tm2_config.py. "
    "See HARDCODE_ELIMINATION_SUMMARY.md for migration guide.",
    DeprecationWarning,
    stacklevel=2
)

# Keep the old class for now to avoid breaking existing scripts
from pathlib import Path
import os

class PopulationSimConfig:
    """DEPRECATED: Legacy config class for backward compatibility"""
    
    def __init__(self, base_dir=None):
        warnings.warn(
            "PopulationSimConfig is deprecated. Use unified_tm2_config instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Basic compatibility - minimal implementation
        self.BASE_DIR = Path(__file__).parent.absolute() if base_dir is None else Path(base_dir)
        self.MODEL_TYPE = "TM2"
        self.YEAR = 2023
        self.OUTPUT_DIR = self.BASE_DIR / f"output_{self.YEAR}"
        self.HH_GQ_DIR = self.BASE_DIR / "hh_gq"
        self.HH_GQ_DATA_DIR = self.HH_GQ_DIR / "data"
        
        # Minimal file definitions for compatibility
        self.CROSSWALK_FILES = {
            'geo_cross_walk': self.OUTPUT_DIR / "geo_cross_walk_tm2_updated.csv"
        }

# Default instance for backward compatibility
config = PopulationSimConfig()
