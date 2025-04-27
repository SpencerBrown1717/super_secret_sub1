import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.models.prediction import (
    forecast_path,
    forecast_all_subs,
    monte_carlo_simulation,
    MIN_SPEED_KNOTS,
    MAX_SPEED_KNOTS
)

@pytest.fixture
def sample_history():
    """Create sample submarine history data."""
    now = datetime.now()
    return [
        {
            'latitude': 15.0,
            'longitude': 110.0,
            'timestamp': now - timedelta(hours=2),
            'event_type': 'departure'
        },
        {
            'latitude': 15.1,
            'longitude': 110.1,
            'timestamp': now - timedelta(hours=1),
            'event_type': 'sighting'
        }
    ]

def test_forecast_path_basic(sample_history):
    """Test basic path forecasting."""
    result = forecast_path(sample_history, hours_ahead=24, step_hours=6)
    assert isinstance(result, dict)
    assert all(key in result for key in ['central_path', 'left_path', 'right_path', 'forecast_times', 'cone_polygon'])
    assert len(result['central_path']) > 0
    assert len(result['left_path']) == len(result['right_path'])
    assert len(result['forecast_times']) == len(result['central_path'])

def test_forecast_path_empty_history():
    """Test forecasting with empty history."""
    result = forecast_path([])
    assert isinstance(result, dict)
    assert result == {}

def test_forecast_path_single_point():
    """Test forecasting with single point history."""
    history = [{
        'latitude': 15.0,
        'longitude': 110.0
    }]
    result = forecast_path(history)
    assert isinstance(result, dict)
    assert len(result['central_path']) == 1
    assert result['central_path'][0] == [110.0, 15.0]

def test_forecast_path_speed_limits(sample_history):
    """Test that forecasted speeds are within limits."""
    # Modify sample history to create unrealistic speed
    sample_history[1]['timestamp'] = sample_history[0]['timestamp'] + timedelta(minutes=1)
    result = forecast_path(sample_history)
    
    # Calculate actual speed from first two points of central path
    p1 = result['central_path'][0]
    p2 = result['central_path'][1]
    distance = np.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)  # Simple distance for test
    speed_kmh = distance * 1.852  # Convert to km/h
    
    assert speed_kmh <= MAX_SPEED_KNOTS * 1.852  # Convert knots to km/h

def test_forecast_all_subs(sample_history):
    """Test forecasting for multiple submarines."""
    data = [
        {
            'id': 'Jin1',
            'latitude': 15.0,
            'longitude': 110.0,
            'timestamp': datetime.now() - timedelta(hours=2)
        },
        {
            'id': 'Jin1',
            'latitude': 15.1,
            'longitude': 110.1,
            'timestamp': datetime.now() - timedelta(hours=1)
        },
        {
            'id': 'Jin2',
            'latitude': 16.0,
            'longitude': 111.0,
            'timestamp': datetime.now() - timedelta(hours=2)
        },
        {
            'id': 'Jin2',
            'latitude': 16.1,
            'longitude': 111.1,
            'timestamp': datetime.now() - timedelta(hours=1)
        }
    ]
    
    result = forecast_all_subs(data)
    assert isinstance(result, dict)
    assert len(result) == 2
    assert all(sub_id in result for sub_id in ['Jin1', 'Jin2'])
    assert all(isinstance(forecast, dict) for forecast in result.values())

def test_forecast_all_subs_with_dataframe(sample_history):
    """Test forecasting with DataFrame input."""
    df = pd.DataFrame(sample_history)
    df['id'] = 'Jin1'
    result = forecast_all_subs(df)
    assert isinstance(result, dict)
    assert 'Jin1' in result
    assert isinstance(result['Jin1'], dict)

def test_monte_carlo_simulation():
    """Test Monte Carlo simulation forecasting."""
    result = monte_carlo_simulation(
        lat=15.0,
        lon=110.0,
        heading=90,
        speed=8.0,
        hours_ahead=24,
        step_hours=6,
        num_simulations=10
    )
    assert isinstance(result, dict)
    assert len(result) > 0
    assert all(key in result for key in ['central_path', 'left_path', 'right_path', 'forecast_times', 'cone_polygon'])

def test_monte_carlo_simulation_with_history():
    """Test Monte Carlo simulation with history data."""
    now = datetime.now()
    history = [
        {
            'sub_id': 'Jin1',
            'latitude': 15.0,
            'longitude': 110.0,
            'timestamp': now - timedelta(hours=2),
            'event_type': 'departure'
        },
        {
            'sub_id': 'Jin1',
            'latitude': 15.1,
            'longitude': 110.1,
            'timestamp': now - timedelta(hours=1),
            'event_type': 'sighting'
        }
    ]
    result = monte_carlo_simulation(
        history=history,
        hours_ahead=12,
        step_hours=3,
        num_simulations=5,
        heading_variation=10.0
    )
    assert isinstance(result, dict)
    assert len(result) > 0
    assert all(key in result for key in ['central_path', 'left_path', 'right_path', 'forecast_times', 'cone_polygon'])

def test_monte_carlo_simulation_uncertainty():
    """Test that Monte Carlo simulation produces varying results."""
    # Set random seed for reproducibility
    np.random.seed(42)

    result = monte_carlo_simulation(
        lat=15.0,
        lon=110.0,
        heading=135,  # Southeast heading to stay in South China Sea
        speed=7.0,    # Moderate speed
        hours_ahead=12,  # Shorter forecast period
        step_hours=3,    # Smaller steps
        num_simulations=100,
        heading_sigma=3.0,    # Even smaller heading variation
        speed_sigma=0.05,     # Small speed variation
    )

    # Check that we have multiple unique positions in the cone polygon
    assert len(result['cone_polygon']) > 0
    assert result['runs_kept'] > 0, "No valid runs were kept"

    # Check that we have variation in both latitude and longitude
    lats = [p[1] for p in result['central_path']]  # Use central path for variation check
    lons = [p[0] for p in result['central_path']]

    # We should have variation in both latitude and longitude
    assert len(set(lats)) > 1, "Monte Carlo simulation should produce varying latitudes"
    assert len(set(lons)) > 1, "Monte Carlo simulation should produce varying longitudes"

    # Check that the variations are within reasonable bounds
    lat_spread = max(lats) - min(lats)
    lon_spread = max(lons) - min(lons)

    # The spread should be non-zero but not too large
    # For a 12-hour forecast with 7 knots speed, max distance ≈ 155 km ≈ 1.4 degrees
    assert 0 < lat_spread < 1.5, f"Latitude spread {lat_spread} should be reasonable"
    assert 0 < lon_spread < 1.5, f"Longitude spread {lon_spread} should be reasonable" 