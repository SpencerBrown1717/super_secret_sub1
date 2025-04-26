import folium
from folium.plugins import MarkerCluster
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

def create_map(sub_states: Dict[str, Any], forecasts: Optional[Dict[str, List[Dict[str, Any]]]] = None, 
              center: Optional[Tuple[float, float]] = None, zoom_start: int = 5) -> folium.Map:
    """
    Create a map visualization of submarine positions and forecasts.
    
    Args:
        sub_states: Dictionary mapping submarine IDs to their current state.
        forecasts: Dictionary mapping submarine IDs to their forecast path.
        center: (lat, lon) tuple for map center. If None, will center on data.
        zoom_start: Initial zoom level.
        
    Returns:
        Folium Map object.
    """
    # If center not specified, calculate it from the data
    if center is None:
        lats = [info["last_lat"] for _, info in sub_states.items() if info and info["last_lat"] is not None]
        lons = [info["last_lon"] for _, info in sub_states.items() if info and info["last_lon"] is not None]
        
        if lats and lons:
            center = [sum(lats) / len(lats), sum(lons) / len(lons)]
        else:
            # Default to South China Sea if no data
            center = [18.2133, 109.6925]  # Hainan Island coordinates
    
    # Create the map
    m = folium.Map(location=center, zoom_start=zoom_start)
    
    # Add AWS Sentinel-2 imagery layer
    folium.TileLayer(
        tiles='https://sentinel-s2-l1c.s3.amazonaws.com/tiles/{z}/{x}/{y}.jpg',
        attr='Sentinel-2',
        name='Sentinel-2 Satellite',
        overlay=True,
        control=True
    ).add_to(m)
    
    # Add OpenStreetMap as base layer
    folium.TileLayer(
        tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attr='OpenStreetMap',
        name='OpenStreetMap',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Create a MarkerCluster for submarine positions
    marker_cluster = MarkerCluster().add_to(m)
    
    # Create a color map for submarines
    sub_colors = {
        "Jin1": "red", "Jin2": "blue", "Jin3": "green", 
        "Jin4": "purple", "Jin5": "orange", "Jin6": "darkred"
    }
    
    # Plot each submarine's latest position
    for sub_id, info in sub_states.items():
        if info is None or info["last_lat"] is None:
            continue
            
        lat, lon = info["last_lat"], info["last_lon"]
        last_time = info["last_time"].strftime('%Y-%m-%d %H:%M')
        status = "At Sea" if info["at_sea"] else "In Port"
        color = sub_colors.get(sub_id, "blue")
        
        # Enhanced popup with HTML formatting
        popup_text = f"""
        <b>{sub_id}</b><br>
        Last seen: {last_time}<br>
        Status: {status}<br>
        Position: {lat:.4f}, {lon:.4f}
        """
        
        folium.Marker(
            [lat, lon], 
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color=color, icon="ship", prefix="fa"),
            options={'tooltip': f"{sub_id} - Last Known Position"}
        ).add_to(marker_cluster)
    
    # Plot forecasts if provided
    if forecasts:
        for sub_id, forecast in forecasts.items():
            if not forecast:
                continue
                
            color = sub_colors.get(sub_id, "blue")
            
            # Draw forecast center line
            coords = [(pt["lat"], pt["lon"]) for pt in forecast]
            folium.PolyLine(
                coords, 
                color=color, 
                weight=2, 
                dash_array="5,5",
                tooltip=f"{sub_id} - Predicted Path"
            ).add_to(m)
            
            # Draw uncertainty circles and forecast points
            for pt in forecast:
                # Only draw circles for future points (not the starting point)
                if pt["radius_km"] > 0:
                    folium.Circle(
                        location=(pt["lat"], pt["lon"]), 
                        radius=pt["radius_km"]*1000,  # Convert km to meters
                        color=color, 
                        fill=True, 
                        fill_opacity=0.1,
                        tooltip=f"{sub_id} - {pt['time'].strftime('%Y-%m-%d %H:%M')} - Uncertainty: {pt['radius_km']:.1f} km"
                    ).add_to(m)
                    
                    # Add small marker for forecast point
                    folium.CircleMarker(
                        location=(pt["lat"], pt["lon"]),
                        radius=3,
                        color=color,
                        fill=True,
                        fill_opacity=0.6,
                        tooltip=f"{sub_id} - Forecast for {pt['time'].strftime('%Y-%m-%d %H:%M')}"
                    ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m

def create_monte_carlo_viz(sub_id, lat, lon, start_time, num_simulations=10):
    """
    Create a visualization of Monte Carlo simulations for a submarine.
    Shows multiple possible paths the submarine might take.
    
    Args:
        sub_id: Submarine identifier
        lat, lon: Starting position
        start_time: Starting time
        num_simulations: Number of random paths to simulate
        
    Returns:
        Folium Map object.
    """
    from src.models.prediction import simulate_random_path
    
    # Create the map centered on starting position
    m = folium.Map(location=[lat, lon], zoom_start=6)
    
    # Add marker for starting position
    folium.Marker(
        [lat, lon],
        popup=f"{sub_id} Starting Position",
        icon=folium.Icon(color="red", icon="ship", prefix="fa")
    ).add_to(m)
    
    # Generate and plot multiple random paths
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 
              'lightred', 'darkblue', 'cadetblue', 'darkpurple']
    
    for i in range(num_simulations):
        path = simulate_random_path(lat, lon, start_time)
        coords = [(pt["lat"], pt["lon"]) for pt in path]
        
        # Choose color (cycle through colors list)
        color = colors[i % len(colors)]
        
        # Plot path
        folium.PolyLine(
            coords,
            color=color,
            weight=2,
            opacity=0.7,
            popup=f"Simulated Path {i+1}"
        ).add_to(m)
    
    return m
