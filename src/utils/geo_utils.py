import math
from typing import Tuple
from .china_coastal_boundary import clamp_to_china_coastal

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
