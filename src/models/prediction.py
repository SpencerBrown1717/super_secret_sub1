import pandas as pd
import math
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two lat/lon points in kilometers."""
    R = 6371.0  # Earth radius in km
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = (math.sin(dlat/2)**2 + 
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def predict_path_with_uncertainty(
    lat: float, 
    lon: float, 
    start_time: datetime,
    speed_knots: float = 8.0, 
    heading_deg: float = 90, 
    total_hours: int = 72, 
    interval: int = 12
) -> List[Dict[str, Any]]:
    """
    Predict submarine positions up to total_hours into the future, with uncertainty radii.
    Returns a list of dicts: [{time: ..., lat: ..., lon: ..., radius_km: ...}, ...]
    """
    results = []
    
    # Convert speed from knots to km per hour (1 knot ~ 1.852 km/h)
    speed_kmh = speed_knots * 1.852
    
    # Convert heading to radians for movement calculation
    heading_rad = math.radians(heading_deg)
    
    # Earth radius (for rough degree calculations)
    R = 6371.0  # km
    
    # Starting point
    current_lat = math.radians(lat)
    current_lon = math.radians(lon)
    current_time = start_time
    
    # Add initial position with zero uncertainty
    results.append({
        "time": current_time,
        "lat": lat,
        "lon": lon,
        "radius_km": 0
    })
    
    for h in range(interval, total_hours+1, interval):
        # Simple dead-reckoning: distance = speed * time
        distance = speed_kmh * h  # km traveled in h hours (assuming constant speed)
        
        # Calculate new lat/lon using basic equirectangular approximation
        delta = distance / R  # angular distance in radians
        
        new_lat = math.asin(math.sin(current_lat) * math.cos(delta) + 
                           math.cos(current_lat) * math.sin(delta) * math.cos(heading_rad))
        
        new_lon = current_lon + math.atan2(math.sin(heading_rad) * math.sin(delta) * math.cos(current_lat),
                                          math.cos(delta) - math.sin(current_lat) * math.sin(new_lat))
        
        # Convert back to degrees
        new_lat_deg = math.degrees(new_lat)
        new_lon_deg = math.degrees(new_lon)
        
        # Increase uncertainty radius over time (10 km for every 12h as a simple rule)
        # In reality, this would be based on submarine capabilities and intelligence
        radius_km = 10 * (h / interval)  
        
        # Add to results
        results.append({
            "time": current_time + pd.Timedelta(hours=h),
            "lat": new_lat_deg,
            "lon": new_lon_deg,
            "radius_km": radius_km
        })
    
    return results

def simulate_random_path(lat: float, lon: float, start_time, 
                       speed_range=(5, 12), total_hours=72, interval=6):
    """
    Simulate a random path by jittering speed and heading.
    Returns a list of positions at each time step.
    This is for Monte Carlo simulation to generate multiple possible paths.
    """
    results = []
    
    # Earth radius in km
    R = 6371.0
    
    # Starting position
    current_lat = lat
    current_lon = lon
    current_time = start_time
    
    # Initial random heading and speed
    current_heading = np.random.uniform(0, 360)
    current_speed = np.random.uniform(speed_range[0], speed_range[1])
    
    # Add initial position
    results.append({
        "time": current_time,
        "lat": current_lat,
        "lon": current_lon
    })
    
    # Simulate movement
    for h in range(interval, total_hours+1, interval):
        # Randomly change heading every few intervals
        if h % 12 == 0:
            current_heading += np.random.uniform(-30, 30)  # change course ±30°
            current_speed = np.random.uniform(speed_range[0], speed_range[1])  # vary speed
        
        # Convert to radians
        lat1 = math.radians(current_lat)
        lon1 = math.radians(current_lon)
        brng = math.radians(current_heading)
        
        # Calculate distance moved during this interval
        dist = current_speed * 1.852 * interval  # km
        
        # Calculate new position
        lat2 = math.asin(math.sin(lat1) * math.cos(dist/R) +
                         math.cos(lat1) * math.sin(dist/R) * math.cos(brng))
        
        lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(dist/R) * math.cos(lat1),
                                 math.cos(dist/R) - math.sin(lat1) * math.sin(lat2))
        
        # Update current position
        current_lat = math.degrees(lat2)
        current_lon = math.degrees(lon2)
        current_time = start_time + pd.Timedelta(hours=h)
        
        # Add to results
        results.append({
            "time": current_time,
            "lat": current_lat,
            "lon": current_lon
        })
    
    return results

def generate_monte_carlo_uncertainty(lat: float, lon: float, start_time,
                                   num_simulations=100, total_hours=72, interval=6):
    """
    Generate uncertainty cone using Monte Carlo simulation.
    For each time step, calculates a radius that encompasses most simulated positions.
    Returns a format similar to predict_path_with_uncertainty.
    """
    # Generate many random paths
    simulations = [simulate_random_path(lat, lon, start_time, total_hours=total_hours, interval=interval) 
                  for _ in range(num_simulations)]
    
    # Group positions by time step
    time_steps = {}
    for sim in simulations:
        for point in sim:
            time = point["time"]
            if time not in time_steps:
                time_steps[time] = []
            time_steps[time].append((point["lat"], point["lon"]))
    
    # Calculate mean position and uncertainty radius at each time step
    results = []
    for time, positions in sorted(time_steps.items()):
        positions = np.array(positions)
        mean_lat = np.mean(positions[:, 0])
        mean_lon = np.mean(positions[:, 1])
        
        # Calculate distance from mean to each point
        distances = []
        for lat, lon in positions:
            # Simplified distance calculation using Haversine formula
            dlat = math.radians(lat - mean_lat)
            dlon = math.radians(lon - mean_lon)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(mean_lat)) * math.cos(math.radians(lat)) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance = 6371 * c  # Earth radius * central angle
            distances.append(distance)
        
        # Use 80th percentile as radius (captures 80% of simulations)
        radius_km = np.percentile(distances, 80)
        
        results.append({
            "time": time,
            "lat": mean_lat,
            "lon": mean_lon,
            "radius_km": radius_km
        })
    
    return results

def monte_carlo_simulation(
    lat: float, 
    lon: float, 
    start_time: datetime,
    base_speed_knots: float = 8.0,
    base_heading_deg: float = 90,
    total_hours: int = 72, 
    interval: int = 12,
    num_simulations: int = 100
) -> List[Dict[str, Any]]:
    """
    Run Monte Carlo simulations to generate uncertainty cone.
    Returns forecast points and uncertainty bounds.
    """
    # Array to store all simulated positions at each time step
    all_simulations = []
    time_points = []
    
    # Generate time points
    for h in range(interval, total_hours+1, interval):
        time_points.append(start_time + pd.Timedelta(hours=h))
    
    # Run simulations with random variations
    for _ in range(num_simulations):
        # Randomly vary speed and heading using normal distribution
        speed = np.random.normal(base_speed_knots, 1.5)  # Vary by ±1.5 knots
        heading = np.random.normal(base_heading_deg, 15)  # Vary by ±15 degrees
        
        # Get path for this simulation
        path = predict_path_with_uncertainty(
            lat, lon, start_time, speed, heading, total_hours, interval
        )
        
        all_simulations.append(path)
    
    # Analyze results to create uncertainty regions
    results = []
    for i, time_point in enumerate(time_points):
        # Extract all positions at this time step
        positions = [(sim[i]['lat'], sim[i]['lon']) for sim in all_simulations]
        
        # Calculate center (mean position)
        center_lat = np.mean([p[0] for p in positions])
        center_lon = np.mean([p[1] for p in positions])
        
        # Calculate radius that contains 80% of positions
        distances = [
            haversine_distance(center_lat, center_lon, p[0], p[1]) 
            for p in positions
        ]
        radius_km = np.percentile(distances, 80)
        
        results.append({
            "time": time_point,
            "lat": center_lat,
            "lon": center_lon,
            "radius_km": radius_km
        })
    
    return results
