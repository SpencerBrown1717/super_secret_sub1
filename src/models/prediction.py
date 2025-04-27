"""Prediction engine for Jin-class submarine tracking."""
import random
import numpy as np
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def monte_carlo_simulation(history: List[Dict], num_simulations: int = 500, 
                          hours_ahead: int = 48, step_hours: int = 3) -> Dict:
    """
    Perform Monte Carlo simulation to predict submarine movement.
    
    Args:
        history: List of historical position records
        num_simulations: Number of simulations to run
        hours_ahead: How many hours ahead to predict
        step_hours: Time step for predictions in hours
        
    Returns:
        Dictionary with prediction results
    """
    if not history or len(history) < 2:
        logger.warning("Insufficient history for prediction")
        return {
            'central_path': [],
            'forecast_path': [],
            'forecast_times': [],
            'confidence_rings': [],
            'simulated_points': []
        }
    
    # Sort history by timestamp
    history = sorted(history, key=lambda x: x['timestamp'])
    
    # Calculate historical movement patterns
    speeds = []
    bearings = []
    
    for i in range(1, len(history)):
        prev = history[i-1]
        curr = history[i]
        
        # Calculate speed and bearing
        speed, bearing = _calculate_movement(
            prev['latitude'], prev['longitude'],
            curr['latitude'], curr['longitude'],
            _time_diff_hours(prev['timestamp'], curr['timestamp'])
        )
        
        speeds.append(speed)
        bearings.append(bearing)
    
    # Calculate mean and standard deviation of speed and bearing
    mean_speed = np.mean(speeds) if speeds else 5.0  # Default 5 knots if no data
    std_speed = np.std(speeds) if len(speeds) > 1 else 2.0
    
    # For bearing, we need to handle circular statistics
    sin_bearings = np.sin(np.radians(bearings))
    cos_bearings = np.cos(np.radians(bearings))
    mean_bearing_rad = np.arctan2(np.mean(sin_bearings), np.mean(cos_bearings))
    mean_bearing = np.degrees(mean_bearing_rad) % 360
    
    # Concentration parameter for von Mises distribution (approximation)
    bearing_concentration = 1.0 / (np.std(bearings) if len(bearings) > 1 else 30.0)
    
    # Starting point for prediction
    last_pos = history[-1]
    start_lat = last_pos['latitude']
    start_lon = last_pos['longitude']
    
    # Generate time steps
    time_steps = list(range(step_hours, hours_ahead + 1, step_hours))
    
    # Run Monte Carlo simulations
    all_simulations = []
    
    for _ in range(num_simulations):
        path = [(start_lon, start_lat)]  # Start with the last known position
        curr_lat, curr_lon = start_lat, start_lon
        
        for _ in time_steps:
            # Sample speed from normal distribution
            speed = max(0, np.random.normal(mean_speed, std_speed))
            
            # Sample bearing from von Mises distribution (approximation)
            bearing = (np.random.normal(mean_bearing, 360 / (2 * np.pi * bearing_concentration))) % 360
            
            # Move the submarine
            curr_lat, curr_lon = _move_point(curr_lat, curr_lon, speed * step_hours, bearing)
            
            # Ensure the point is in water (simplified check)
            while not _is_in_water(curr_lat, curr_lon):
                # Adjust bearing and try again
                bearing = (bearing + 45) % 360
                curr_lat, curr_lon = _move_point(curr_lat, curr_lon, speed * step_hours, bearing)
            
            path.append((curr_lon, curr_lat))
        
        all_simulations.append(path)
    
    # Calculate the central (most likely) path
    central_path = [(start_lon, start_lat)]
    
    for i in range(1, len(time_steps) + 1):
        # Get all positions at this time step from all simulations
        positions = [sim[i] for sim in all_simulations]
        
        # Calculate centroid
        avg_lon = sum(p[0] for p in positions) / len(positions)
        avg_lat = sum(p[1] for p in positions) / len(positions)
        
        central_path.append((avg_lon, avg_lat))
    
    # Calculate confidence rings and collect simulated points
    confidence_rings = []
    simulated_points = []
    
    for i in range(1, len(time_steps) + 1):
        positions = np.array([sim[i] for sim in all_simulations])
        
        # 67% confidence radius
        radius_67 = _calculate_confidence_radius(positions, 0.67)
        
        # 90% confidence radius
        radius_90 = _calculate_confidence_radius(positions, 0.90)
        
        confidence_rings.append({
            'center': central_path[i],
            'radius_67': radius_67,
            'radius_90': radius_90
        })
        
        # Store all simulated points for this step
        simulated_points.append(positions.tolist())
    
    # Return prediction results
    return {
        'central_path': central_path,
        'forecast_path': central_path[1:],  # Exclude starting point
        'forecast_times': time_steps,
        'confidence_rings': confidence_rings,
        'simulated_points': simulated_points
    }

def _calculate_movement(lat1: float, lon1: float, lat2: float, lon2: float, 
                       hours: float) -> Tuple[float, float]:
    """Calculate speed (knots) and bearing (degrees) between two points."""
    from math import radians, sin, cos, atan2, sqrt, degrees
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula for distance
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance_km = 6371 * c  # Earth radius in km
    
    # Convert to nautical miles
    distance_nm = distance_km / 1.852
    
    # Calculate speed in knots (nautical miles per hour)
    speed = distance_nm / hours if hours > 0 else 0
    
    # Calculate bearing
    y = sin(dlon) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
    bearing = (degrees(atan2(y, x)) + 360) % 360
    
    return speed, bearing

def _time_diff_hours(time1: str, time2: str) -> float:
    """Calculate time difference in hours between two timestamps."""
    try:
        # Convert pandas Timestamp to string if needed
        if hasattr(time1, 'strftime'):
            time1 = time1.strftime('%Y-%m-%d %H:%M:%S')
        if hasattr(time2, 'strftime'):
            time2 = time2.strftime('%Y-%m-%d %H:%M:%S')
            
        # Try different formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d"
        ]
        
        dt1 = None
        dt2 = None
        
        for fmt in formats:
            try:
                dt1 = datetime.strptime(time1, fmt)
                break
            except ValueError:
                continue
                
        for fmt in formats:
            try:
                dt2 = datetime.strptime(time2, fmt)
                break
            except ValueError:
                continue
        
        if dt1 and dt2:
            diff = dt2 - dt1
            return diff.total_seconds() / 3600
        else:
            logger.warning(f"Could not parse timestamps: {time1}, {time2}")
            return 1.0  # Default to 1 hour difference
    except Exception as e:
        logger.error(f"Error calculating time difference: {e}")
        return 1.0

def _move_point(lat: float, lon: float, distance_nm: float, bearing: float) -> Tuple[float, float]:
    """Move a point by a distance (nautical miles) in a direction (degrees)."""
    from math import radians, sin, cos, asin, atan2, degrees
    
    # Convert to radians
    lat1 = radians(lat)
    lon1 = radians(lon)
    bearing = radians(bearing)
    
    # Convert nautical miles to km
    distance_km = distance_nm * 1.852
    
    # Earth radius in km
    R = 6371.0
    
    # Calculate new position
    lat2 = asin(sin(lat1) * cos(distance_km/R) + cos(lat1) * sin(distance_km/R) * cos(bearing))
    lon2 = lon1 + atan2(sin(bearing) * sin(distance_km/R) * cos(lat1), 
                        cos(distance_km/R) - sin(lat1) * sin(lat2))
    
    # Convert back to degrees
    return degrees(lat2), degrees(lon2)

def _is_in_water(lat: float, lon: float) -> bool:
    """
    Check if a point is in water (simplified).
    This should be replaced with a proper check using coastline data.
    """
    # Simplified check for major landmasses - would need a proper coastline check
    # These are very rough bounding boxes for mainland China
    if (20 < lat < 45 and 105 < lon < 124):
        # Check if it's in the Gulf of Tonkin or Bohai Sea
        if (18 < lat < 21 and 107 < lon < 109) or \
           (37 < lat < 41 and 118 < lon < 122):
            return True
        return False  # Likely on land
        
    # Taiwan rough check
    if (22 < lat < 25.5 and 120 < lon < 122):
        return False  # Likely on Taiwan
        
    # Japan rough check
    if (30 < lat < 46 and 129 < lon < 146):
        return False  # Likely on Japan
        
    # Philippines rough check
    if (5 < lat < 19 and 117 < lon < 127):
        return False  # Likely on Philippines
        
    # By default, assume it's in water (this is very simplified)
    return True

def _calculate_confidence_radius(positions: np.ndarray, confidence: float) -> float:
    """
    Calculate radius for a given confidence level using distance from centroid.
    
    Args:
        positions: Array of (lon, lat) positions
        confidence: Confidence level (0-1)
        
    Returns:
        Radius in kilometers for the given confidence level
    """
    # Calculate centroid
    centroid = np.mean(positions, axis=0)
    
    # Calculate distances from centroid
    distances = []
    for pos in positions:
        lon1, lat1 = centroid
        lon2, lat2 = pos
        distances.append(_haversine_distance(lat1, lon1, lat2, lon2))
    
    # Sort distances
    distances.sort()
    
    # Get the index for the desired confidence level
    idx = int(len(distances) * confidence)
    
    # Return the radius
    return distances[idx]

def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on earth."""
    from math import radians, sin, cos, sqrt, atan2
    
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    r = 6371  # Radius of earth in kilometers
    
    return c * r