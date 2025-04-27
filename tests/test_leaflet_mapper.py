import os
import tempfile
import json
from src.visualization.leaflet_mapper import create_leaflet_map

def test_create_leaflet_map_creates_html_file():
    """Test that the Leaflet map HTML file is created with correct structure."""
    # Minimal fake forecast data
    forecasts = {
        'Jin1': {
            'central_path': [[110.0, 15.0], [111.0, 16.0]],
            'left_path': [[110.0, 15.0], [111.1, 16.1]],
            'right_path': [[110.0, 15.0], [110.9, 15.9]],
            'forecast_times': [0, 1],
            'cone_polygon': [[110.9, 15.9], [111.1, 16.1], [110.0, 15.0], [110.9, 15.9]]
        }
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, 'test_map.html')
        create_leaflet_map(forecasts, out_path)
        assert os.path.exists(out_path)
        with open(out_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Check for Leaflet-specific elements
        assert 'leaflet.js' in html
        assert 'leaflet.css' in html
        assert 'L.map' in html
        assert 'L.tileLayer' in html
        
        # Check for forecast data
        assert 'window.submarineForecasts' in html
        assert 'Jin1' in html
        assert 'central_path' in html
        assert 'forecast_times' in html
        
        # Check for Leaflet-specific controls and UI elements
        assert 'controls' in html
        assert 'legend' in html
        assert 'submarine-marker' in html
        assert 'source-point' in html

def test_create_leaflet_map_with_multiple_subs():
    """Test creating map with multiple submarines."""
    forecasts = {
        'Jin1': {
            'central_path': [[110.0, 15.0], [111.0, 16.0]],
            'left_path': [[110.0, 15.0], [111.1, 16.1]],
            'right_path': [[110.0, 15.0], [110.9, 15.9]],
            'forecast_times': [0, 1],
            'cone_polygon': [[110.9, 15.9], [111.1, 16.1], [110.0, 15.0], [110.9, 15.9]]
        },
        'Jin2': {
            'central_path': [[112.0, 17.0], [113.0, 18.0]],
            'left_path': [[112.0, 17.0], [113.1, 18.1]],
            'right_path': [[112.0, 17.0], [112.9, 17.9]],
            'forecast_times': [0, 1],
            'cone_polygon': [[112.9, 17.9], [113.1, 18.1], [112.0, 17.0], [112.9, 17.9]]
        }
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, 'test_map.html')
        create_leaflet_map(forecasts, out_path)
        assert os.path.exists(out_path)
        with open(out_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Check both submarines are included
        assert 'Jin1' in html
        assert 'Jin2' in html
        assert 'submarine-marker' in html
        assert 'path-line' in html
        assert 'uncertaintyCones' in html

def test_create_leaflet_map_with_empty_forecasts():
    """Test creating map with empty forecast data."""
    forecasts = {}
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, 'test_map.html')
        create_leaflet_map(forecasts, out_path)
        assert os.path.exists(out_path)
        with open(out_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Check map still initializes correctly
        assert 'L.map' in html
        assert 'L.tileLayer' in html
        assert 'controls' in html
        assert 'legend' in html
        assert 'window.submarineForecasts' in html
        assert '{}' in html  # Empty forecasts JSON 