"""
Visualization module for submarine tracking data.
"""
import os
from .leaflet_mapper import create_leaflet_map

def visualize(forecasts, output_path=None):
    """
    Create a visualization of submarine forecasts.
    
    Args:
        forecasts: Dictionary of submarine forecasts
        output_path: Optional path to save the visualization HTML file.
                    Defaults to data/output/jin_forecast_map.html
    """
    if output_path is None:
        output_path = os.path.join("data", "output", "jin_forecast_map.html")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create the visualization
    create_leaflet_map(forecasts, output_path)
