"""
Water and bathymetry utility functions.
"""
import numpy as np

def _is_water(lat: float, lon: float) -> bool:
    """
    Check if a point is in water using simplified bathymetry model.
    Returns True if point is in deep enough water for submarine operation.
    """
    # Simplified model - actual implementation would use bathymetry data
    # For now, assume most points are water except near known landmasses
    
    # Rough boundaries for major landmasses
    if 20 <= lat <= 45 and 100 <= lon <= 123:  # Mainland China
        return False
    if 18 <= lat <= 20 and 108.5 <= lon <= 111:  # Hainan Island
        return False
    if 8 <= lat <= 23 and 102 <= lon <= 110:  # Vietnam
        return False
    if 5 <= lat <= 19 and 117 <= lon <= 127:  # Philippines
        return False
    if 21 <= lat <= 26 and 119 <= lon <= 123:  # Taiwan
        return False
        
    return True

def _is_on_land(lat: float, lon: float) -> bool:
    """Check if a point is on land."""
    return not _is_water(lat, lon) 