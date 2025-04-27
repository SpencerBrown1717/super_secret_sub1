import math
from typing import Tuple
from .china_coastal_boundary import clamp_to_china_coastal
from datetime import datetime
import numpy as np

EARTH_RADIUS_KM = 6371.0

# Bounding box for the China coastal polygon (approximate)
MIN_LAT, MAX_LAT = 20.0, 39.0
MIN_LON, MAX_LON = 107.0, 125.0

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth using the Haversine formula.
    Return distance in kilometers.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = EARTH_RADIUS_KM * c
    return distance

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the bearing (heading) from point (lat1, lon1) to (lat2, lon2).
    Bearing is returned in degrees from North (0-360, clockwise).
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)
    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing_rad = math.atan2(y, x)
    bearing_deg = (math.degrees(bearing_rad) + 360) % 360
    return bearing_deg

def move_point(lat: float, lon: float, bearing: float, distance_km: float) -> Tuple[float, float]:
    """
    Move a point from the given lat, lon by a distance (km) along a bearing (deg).
    Returns the new latitude and longitude, clamped to the China coastal boundary.
    """
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    bearing_rad = math.radians(bearing)
    frac = distance_km / EARTH_RADIUS_KM
    lat2 = math.asin(math.sin(lat1) * math.cos(frac) + math.cos(lat1) * math.sin(frac) * math.cos(bearing_rad))
    lon2 = lon1 + math.atan2(math.sin(bearing_rad) * math.sin(frac) * math.cos(lat1), math.cos(frac) - math.sin(lat1) * math.sin(lat2))
    new_lat = math.degrees(lat2)
    new_lon = math.degrees(lon2)
    new_lon = (new_lon + 180) % 360 - 180
    return clamp_to_china_coastal(new_lat, new_lon)

def calculate_current_drift(lat, lon, month=None):
    """Calculate the current drift based on latitude and longitude.
    
    This function models a simplified version of ocean currents, with:
    - Stronger currents near the equator (Equatorial Counter Current)
    - Weaker seasonal variations
    - Very reduced effect at higher latitudes
    - More variable current directions
    
    Args:
        lat (float or np.ndarray): Latitude in degrees
        lon (float or np.ndarray): Longitude in degrees
        month (int, optional): Month of the year (1-12). Defaults to current month.
    
    Returns:
        tuple: (x_drift, y_drift) in km/h
    """
    if month is None:
        month = datetime.now().month
    
    # Convert inputs to numpy arrays if they aren't already
    lat = np.array(lat)
    lon = np.array(lon)
    
    # Reduced base strength (0.15 km/h maximum)
    base_strength = 0.15
    
    # Weaker seasonal factor (only 20% variation)
    seasonal_factor = 0.8 + 0.2 * np.abs(np.cos(2 * np.pi * (month - 1) / 12))
    
    # Sharper latitude factor (stronger decay away from equator)
    # Using σ=10° instead of 15° for faster decay
    lat_factor = np.exp(-((lat - 0) ** 2) / (2 * 10 ** 2))
    
    # Additional latitude-dependent factor to further reduce drift at higher latitudes
    high_lat_reduction = 1.0 / (1.0 + (np.abs(lat) / 20.0) ** 2)
    
    # Calculate base drift strength
    strength = base_strength * seasonal_factor * lat_factor * high_lat_reduction
    
    # Make drift direction more latitude-dependent
    # Near equator: mostly eastward
    # Higher latitudes: more variable direction
    eastward_ratio = np.exp(-((np.abs(lat) - 0) ** 2) / (2 * 5 ** 2))  # Peaks at equator
    
    # Calculate drift components with more variation
    x_drift = strength * (0.7 * eastward_ratio + 0.3)  # Minimum 30% eastward component
    y_drift = strength * 0.15 * np.sign(lat)  # Reduced meridional component
    
    return x_drift, y_drift
