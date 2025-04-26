import pytest
import folium
from datetime import datetime
from src.visualization.folium_mapper import create_map, create_monte_carlo_viz

def test_create_map_basic(sample_submarine_state):
    """Test basic map creation with minimal input."""
    m = create_map(sample_submarine_state)
    assert isinstance(m, folium.Map)
    assert m.location == [15.0, 110.0]  # Should center on the submarine
    # Check zoom level through the options dictionary
    assert m.options['zoom'] == 5

def test_create_map_with_forecasts(sample_submarine_state, sample_forecast_data):
    """Test map creation with forecast data."""
    m = create_map(sample_submarine_state, sample_forecast_data)
    assert isinstance(m, folium.Map)
    # Check that the map has the expected layers
    assert len(m._children) >= 3  # Base map + satellite layer + layer control

def test_create_map_custom_center(sample_submarine_state):
    """Test map creation with custom center coordinates."""
    custom_center = (20.0, 120.0)
    m = create_map(sample_submarine_state, center=custom_center)
    assert m.location == list(custom_center)

def test_create_map_no_data():
    """Test map creation with no submarine data."""
    m = create_map({})
    assert isinstance(m, folium.Map)
    assert m.location == [18.2133, 109.6925]  # Should use Hainan Island as default center

def test_marker_cluster(sample_submarine_state):
    """Test that markers are properly clustered."""
    m = create_map(sample_submarine_state)
    # Check for MarkerCluster in the map's children
    marker_clusters = [child for child in m._children.values() 
                      if isinstance(child, folium.plugins.MarkerCluster)]
    assert len(marker_clusters) == 1

def test_satellite_layer(sample_submarine_state):
    """Test that satellite imagery layer is added."""
    m = create_map(sample_submarine_state)
    # Check for TileLayer with Sentinel-2 URL
    satellite_layers = [child for child in m._children.values() 
                       if isinstance(child, folium.TileLayer) and 
                       'sentinel-s2-l1c' in child.tiles]
    assert len(satellite_layers) == 1

def test_layer_control(sample_submarine_state):
    """Test that layer control is added."""
    m = create_map(sample_submarine_state)
    # Check for LayerControl in the map's children
    layer_controls = [child for child in m._children.values() 
                     if isinstance(child, folium.LayerControl)]
    assert len(layer_controls) == 1

def test_submarine_markers(sample_submarine_state):
    """Test that submarines have correct markers."""
    m = create_map(sample_submarine_state)
    # Get the marker cluster
    marker_cluster = next(child for child in m._children.values() 
                         if isinstance(child, folium.plugins.MarkerCluster))
    # Get markers from the cluster
    markers = [child for child in marker_cluster._children.values() 
              if isinstance(child, folium.Marker)]
    assert len(markers) == 1
    
    # Check marker location
    marker = markers[0]
    assert marker.location == [15.0, 110.0]
    assert isinstance(marker.icon, folium.Icon)

def test_popup_content(sample_submarine_state):
    """Test that popups contain correct information."""
    m = create_map(sample_submarine_state)
    # Get the marker cluster
    marker_cluster = next(child for child in m._children.values() 
                         if isinstance(child, folium.plugins.MarkerCluster))
    # Get markers from the cluster
    markers = [child for child in marker_cluster._children.values() 
              if isinstance(child, folium.Marker)]
    assert len(markers) == 1
    
    # Check marker has correct location and options
    marker = markers[0]
    assert marker.location == [15.0, 110.0]
    assert marker.icon is not None
    assert marker.options.get('options', {}).get('tooltip') == "Jin1 - Last Known Position"

def test_multiple_submarines():
    """Test map with multiple submarines."""
    sub_states = {
        "Jin1": {
            "last_lat": 15.0,
            "last_lon": 110.0,
            "last_time": datetime.now(),
            "at_sea": True
        },
        "Jin2": {
            "last_lat": 16.0,
            "last_lon": 111.0,
            "last_time": datetime.now(),
            "at_sea": False
        }
    }
    
    m = create_map(sub_states)
    # Get the marker cluster
    marker_cluster = next(child for child in m._children.values() 
                         if isinstance(child, folium.plugins.MarkerCluster))
    # Get markers from the cluster
    markers = [child for child in marker_cluster._children.values() 
              if isinstance(child, folium.Marker)]
    assert len(markers) == 2
    
    # Check marker locations
    locations = {tuple(marker.location) for marker in markers}
    expected_locations = {(15.0, 110.0), (16.0, 111.0)}
    assert locations == expected_locations

@pytest.mark.skip(reason="Monte Carlo simulation requires numpy and is tested in models")
def test_create_monte_carlo_viz():
    """Test Monte Carlo visualization creation."""
    sub_id = "Jin1"
    lat, lon = 15.0, 110.0
    start_time = datetime.now()
    
    m = create_monte_carlo_viz(sub_id, lat, lon, start_time, num_simulations=5)
    assert isinstance(m, folium.Map)
    assert m.location == [lat, lon]
    assert len(m._children) >= 2  # Base map + at least one path
