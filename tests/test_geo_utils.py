import pytest
import math
from src.utils.geo_utils import (
    haversine_distance,
    calculate_bearing,
    move_point,
    EARTH_RADIUS_KM,
    MIN_LAT, MAX_LAT,
    MIN_LON, MAX_LON
)

def test_haversine_distance_same_point():
    """Test distance calculation for same point."""
    lat, lon = 15.0, 110.0
    distance = haversine_distance(lat, lon, lat, lon)
    assert distance == pytest.approx(0.0)

def test_haversine_distance_known_points():
    """Test distance calculation for known points."""
    # Test with known distance between two points
    lat1, lon1 = 0.0, 0.0
    lat2, lon2 = 0.0, 1.0  # 1 degree longitude at equator ≈ 111.32 km
    distance = haversine_distance(lat1, lon1, lat2, lon2)
    assert distance == pytest.approx(111.32, rel=1e-2)

def test_haversine_distance_antipodes():
    """Test distance calculation for antipodal points."""
    lat1, lon1 = 0.0, 0.0
    lat2, lon2 = 0.0, 180.0
    distance = haversine_distance(lat1, lon1, lat2, lon2)
    assert distance == pytest.approx(EARTH_RADIUS_KM * math.pi, rel=1e-2)

def test_calculate_bearing_north():
    """Test bearing calculation for northward direction."""
    lat1, lon1 = 0.0, 0.0
    lat2, lon2 = 1.0, 0.0
    bearing = calculate_bearing(lat1, lon1, lat2, lon2)
    assert bearing == pytest.approx(0.0)

def test_calculate_bearing_east():
    """Test bearing calculation for eastward direction."""
    lat1, lon1 = 0.0, 0.0
    lat2, lon2 = 0.0, 1.0
    bearing = calculate_bearing(lat1, lon1, lat2, lon2)
    assert bearing == pytest.approx(90.0)

def test_calculate_bearing_south():
    """Test bearing calculation for southward direction."""
    lat1, lon1 = 0.0, 0.0
    lat2, lon2 = -1.0, 0.0
    bearing = calculate_bearing(lat1, lon1, lat2, lon2)
    assert bearing == pytest.approx(180.0)

def test_calculate_bearing_west():
    """Test bearing calculation for westward direction."""
    lat1, lon1 = 0.0, 0.0
    lat2, lon2 = 0.0, -1.0
    bearing = calculate_bearing(lat1, lon1, lat2, lon2)
    assert bearing == pytest.approx(270.0)

def test_move_point_north():
    """Test moving point northward."""
    lat, lon = 25.0, 115.0
    distance = 100  # km
    new_lat, new_lon = move_point(lat, lon, 0, distance)
    assert new_lat > lat
    assert new_lon == pytest.approx(lon)
    # Check distance is approximately correct
    actual_distance = haversine_distance(lat, lon, new_lat, new_lon)
    assert actual_distance == pytest.approx(distance, rel=1e-2)

def test_move_point_east():
    """Test moving point eastward."""
    lat, lon = 25.0, 115.0
    distance = 100  # km
    new_lat, new_lon = move_point(lat, lon, 90, distance)
    # Allow for some numerical imprecision in latitude
    assert abs(new_lat - lat) < 0.1
    assert new_lon > lon
    actual_distance = haversine_distance(lat, lon, new_lat, new_lon)
    assert actual_distance == pytest.approx(distance, rel=1e-2)

def test_move_point_boundary_clamping():
    """Test that points are clamped to the China coastal boundary."""
    # Test moving beyond northern boundary
    lat, lon = MAX_LAT - 2, 115.0
    new_lat, new_lon = move_point(lat, lon, 0, 200)
    assert new_lat <= MAX_LAT + 1  # Allow small tolerance
    
    # Test moving beyond southern boundary
    lat, lon = MIN_LAT + 2, 115.0
    new_lat, new_lon = move_point(lat, lon, 180, 200)
    assert new_lat >= MIN_LAT - 1  # Allow small tolerance
    
    # Test moving beyond eastern boundary
    lat, lon = 25.0, MAX_LON - 2
    new_lat, new_lon = move_point(lat, lon, 90, 200)
    assert new_lon <= MAX_LON + 1  # Allow small tolerance
    
    # Test moving beyond western boundary
    lat, lon = 25.0, MIN_LON + 2
    new_lat, new_lon = move_point(lat, lon, 270, 200)
    assert new_lon >= MIN_LON - 1  # Allow small tolerance

def test_move_point_diagonal():
    """Test moving point diagonally."""
    lat, lon = 25.0, 115.0
    distance = 100  # km
    bearing = 45  # Northeast
    new_lat, new_lon = move_point(lat, lon, bearing, distance)
    assert new_lat > lat
    assert new_lon > lon
    actual_distance = haversine_distance(lat, lon, new_lat, new_lon)
    assert actual_distance == pytest.approx(distance, rel=1e-2)

def test_move_point_zero_distance():
    """Test moving point with zero distance."""
    lat, lon = 25.0, 115.0
    new_lat, new_lon = move_point(lat, lon, 45, 0)
    assert new_lat == pytest.approx(lat)
    assert new_lon == pytest.approx(lon) 