"""
Geographic utility functions for submarine tracking.
"""
import math
import numpy as np

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.
    Returns distance in kilometers.
    """
    R = 6371  # Earth's radius in kilometers
    
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate initial bearing between two points.
    Returns bearing in degrees (0-360).
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Calculate bearing
    dlon = lon2 - lon1
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    bearing = math.atan2(y, x)
    
    # Convert to degrees and normalize
    bearing_deg = math.degrees(bearing)
    return (bearing_deg + 360) % 360

def move_point(lat: float, lon: float, bearing: float, distance: float) -> tuple[float, float]:
    """
    Calculate new point given starting point, bearing and distance.
    bearing: degrees (0-360)
    distance: kilometers
    Returns: (new_lat, new_lon)
    """
    R = 6371  # Earth's radius in kilometers
    
    # Convert to radians
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    bearing = math.radians(bearing)
    
    # Calculate new position
    d = distance / R
    lat2 = math.asin(math.sin(lat1) * math.cos(d) + 
                     math.cos(lat1) * math.sin(d) * math.cos(bearing))
    lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(d) * math.cos(lat1),
                            math.cos(d) - math.sin(lat1) * math.sin(lat2))
    
    # Convert back to degrees
    lat2 = math.degrees(lat2)
    lon2 = math.degrees(lon2)
    
    # Normalize longitude
    lon2 = ((lon2 + 180) % 360) - 180
    
    return lat2, lon2

def calculate_current_drift(lat: float, lon: float) -> tuple[float, float]:
    """
    Calculate ocean current drift at a given point.
    Returns: (x_drift, y_drift) in degrees per hour
    """
    # Simplified model - actual implementation would use real ocean current data
    base_drift = 0.001  # ~0.1 km/h at equator
    
    # Add some spatial variation
    x_drift = base_drift * math.sin(math.radians(lat * 2))
    y_drift = base_drift * math.cos(math.radians(lon * 2))
    
    return x_drift, y_drift

def is_water(lat: float, lon: float) -> bool:
    """Check if a point is in water (not land)."""
    # This is a placeholder - actual implementation would use coastline data
    return True

def is_land(lat: float, lon: float) -> bool:
    """Check if a point is on land."""
    return not is_water(lat, lon) 