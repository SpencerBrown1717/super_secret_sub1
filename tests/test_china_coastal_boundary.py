import pytest
from src.utils.china_coastal_boundary import (
    is_in_china_coastal,
    clamp_to_china_coastal,
    CHINA_COASTAL_BOUNDARY
)

def test_is_in_china_coastal_inside_points():
    """Test points that should be inside the coastal boundary."""
    inside_points = [
        (30.0, 120.0),  # Near Shanghai
        (25.0, 119.0),  # Near Fuzhou
        (23.0, 115.0),  # Near Shantou
        (22.0, 113.0),  # Near Hong Kong
        (35.0, 122.0),  # Yellow Sea
    ]
    for lat, lon in inside_points:
        assert is_in_china_coastal(lat, lon), f"Point ({lat}, {lon}) should be inside"

def test_is_in_china_coastal_outside_points():
    """Test points that should be outside the coastal boundary."""
    outside_points = [
        (40.0, 120.0),  # Too far north
        (19.0, 115.0),  # Too far south
        (25.0, 126.0),  # Too far east
        (25.0, 106.0),  # Too far west
        (0.0, 0.0),     # Far away
    ]
    for lat, lon in outside_points:
        assert not is_in_china_coastal(lat, lon), f"Point ({lat}, {lon}) should be outside"

def test_is_in_china_coastal_boundary_points():
    """Test points near the boundary."""
    # Test points slightly inside from each vertex
    for lon, lat in CHINA_COASTAL_BOUNDARY[:-1]:  # Skip last point as it's duplicate of first
        # Test point slightly inside
        inside_lat = lat - 0.01
        inside_lon = lon - 0.01
        assert is_in_china_coastal(inside_lat, inside_lon), f"Point near boundary ({inside_lat}, {inside_lon}) should be inside"

def test_is_in_china_coastal_edge_cases():
    """Test edge cases for the point-in-polygon algorithm."""
    # Test points near horizontal edges
    assert is_in_china_coastal(38.9, 121.0), "Point near horizontal edge should be inside"
    
    # Test points near vertical edges
    assert is_in_china_coastal(34.0, 124.9), "Point near vertical edge should be inside"
    
    # Test points very close to vertices
    for lon, lat in CHINA_COASTAL_BOUNDARY[:-1]:  # Skip last point as it's duplicate of first
        # Test points slightly inside from vertex
        assert is_in_china_coastal(lat - 0.1, lon - 0.1), "Point near vertex should be inside"

def test_clamp_to_china_coastal_inside():
    """Test clamping for points already inside the boundary."""
    lat, lon = 30.0, 120.0
    clamped_lat, clamped_lon = clamp_to_china_coastal(lat, lon)
    assert clamped_lat == lat
    assert clamped_lon == lon

def test_clamp_to_china_coastal_outside():
    """Test clamping for points outside the boundary."""
    # For now, the function returns the original coordinates
    # This test documents the current behavior
    lat, lon = 0.0, 0.0
    clamped_lat, clamped_lon = clamp_to_china_coastal(lat, lon)
    assert clamped_lat == lat
    assert clamped_lon == lon

def test_clamp_to_china_coastal_boundary():
    """Test clamping for points on the boundary."""
    # Test each vertex of the boundary
    for lon, lat in CHINA_COASTAL_BOUNDARY:
        clamped_lat, clamped_lon = clamp_to_china_coastal(lat, lon)
        assert clamped_lat == lat
        assert clamped_lon == lon

def test_is_in_china_coastal_extreme_values():
    """Test the function with extreme coordinate values."""
    extreme_points = [
        (90.0, 180.0),   # North pole region
        (-90.0, -180.0), # South pole region
        (0.0, 180.0),    # International date line
        (0.0, -180.0),   # International date line (other side)
    ]
    for lat, lon in extreme_points:
        # Should handle extreme values without raising exceptions
        result = is_in_china_coastal(lat, lon)
        assert not result, f"Extreme point ({lat}, {lon}) should be outside"

def test_polygon_closure():
    """Test that the boundary polygon is properly closed."""
    assert CHINA_COASTAL_BOUNDARY[0] == CHINA_COASTAL_BOUNDARY[-1], "Polygon should be closed"

def test_polygon_coordinates():
    """Test that the boundary polygon coordinates are within valid ranges."""
    for lon, lat in CHINA_COASTAL_BOUNDARY:
        assert -180 <= lon <= 180, f"Invalid longitude: {lon}"
        assert -90 <= lat <= 90, f"Invalid latitude: {lat}" 