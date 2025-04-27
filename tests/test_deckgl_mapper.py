import pytest
import pydeck as pdk
from datetime import datetime
from src.visualization.deckgl_mapper import create_map, _safe_path

def test_safe_path_valid():
    """Test _safe_path with valid input."""
    test_data = {"path": [[1.0, 2.0], [3.0, 4.0]]}
    result = _safe_path(test_data, "path")
    assert result == [[1.0, 2.0], [3.0, 4.0]]

def test_safe_path_invalid():
    """Test _safe_path with invalid input."""
    test_data = {"path": [1.0, 2.0]}  # Not a list of lists
    result = _safe_path(test_data, "path")
    assert result == []

def test_safe_path_missing():
    """Test _safe_path with missing key."""
    test_data = {}
    result = _safe_path(test_data, "path")
    assert result == []

def test_create_map_empty_forecasts():
    """Test create_map with empty forecasts."""
    result = create_map({})
    assert result is None

def test_create_map_valid_forecasts():
    """Test create_map with valid forecast data."""
    forecasts = {
        "Jin1": {
            "central_path": [[110.0, 15.0], [111.0, 16.0]],
            "cone_polygon": [[110.0, 15.0], [111.0, 15.5], [111.0, 14.5], [110.0, 15.0]]
        }
    }
    result = create_map(forecasts)
    assert isinstance(result, pdk.Deck)
    assert len(result.layers) > 0

def test_create_map_invalid_central_path():
    """Test create_map with invalid central path."""
    forecasts = {
        "Jin1": {
            "central_path": [],  # Invalid central path
            "cone_polygon": [[110.0, 15.0], [111.0, 15.5], [111.0, 14.5], [110.0, 15.0]]
        }
    }
    result = create_map(forecasts)
    assert isinstance(result, pdk.Deck)
    # Should still create a map but skip the invalid submarine

def test_create_map_multiple_submarines():
    """Test create_map with multiple submarines."""
    forecasts = {
        "Jin1": {
            "central_path": [[110.0, 15.0], [111.0, 16.0]],
            "cone_polygon": [[110.0, 15.0], [111.0, 15.5], [111.0, 14.5], [110.0, 15.0]]
        },
        "Jin2": {
            "central_path": [[112.0, 17.0], [113.0, 18.0]],
            "cone_polygon": [[112.0, 17.0], [113.0, 17.5], [113.0, 16.5], [112.0, 17.0]]
        }
    }
    result = create_map(forecasts)
    assert isinstance(result, pdk.Deck)
    assert len(result.layers) > 0

def test_create_map_with_output_path(tmp_path):
    """Test create_map with output path."""
    forecasts = {
        "Jin1": {
            "central_path": [[110.0, 15.0], [111.0, 16.0]],
            "cone_polygon": [[110.0, 15.0], [111.0, 15.5], [111.0, 14.5], [110.0, 15.0]]
        }
    }
    output_file = tmp_path / "test_map.html"
    result = create_map(forecasts, str(output_file))
    assert isinstance(result, pdk.Deck)
    assert output_file.exists()

def test_create_map_default_view():
    """Test create_map default view state when no valid points."""
    forecasts = {
        "Jin1": {
            "central_path": [],  # No valid points
            "cone_polygon": []
        }
    }
    result = create_map(forecasts)
    assert isinstance(result, pdk.Deck)
    assert result.initial_view_state.latitude == 18.2133
    assert result.initial_view_state.longitude == 109.6925 