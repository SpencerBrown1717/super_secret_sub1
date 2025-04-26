import pytest
from datetime import datetime, timedelta
import pandas as pd

@pytest.fixture
def sample_submarine_state():
    """Fixture providing a sample submarine state dictionary."""
    return {
        "Jin1": {
            "last_lat": 15.0,
            "last_lon": 110.0,
            "last_time": datetime.now(),
            "at_sea": True
        }
    }

@pytest.fixture
def sample_forecast_data():
    """Fixture providing sample forecast data."""
    now = datetime.now()
    return {
        "Jin1": [
            {
                "lat": 15.1,
                "lon": 110.1,
                "time": now + timedelta(hours=1),
                "radius_km": 5.0
            },
            {
                "lat": 15.2,
                "lon": 110.2,
                "time": now + timedelta(hours=2),
                "radius_km": 10.0
            }
        ]
    }

@pytest.fixture
def sample_submarine_records():
    """Fixture providing sample submarine records DataFrame."""
    now = datetime.now()
    return pd.DataFrame([
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
            'event_type': None
        }
    ])

@pytest.fixture
def sample_submarine_data():
    """Fixture providing sample submarine data with sub_id and sub_type fields."""
    now = datetime.now()
    return pd.DataFrame([
        {
            'sub_id': 'Jin1',
            'sub_type': 'Type094',
            'latitude': 15.0,
            'longitude': 110.0,
            'timestamp': now - timedelta(hours=2),
            'event_type': 'departure'
        },
        {
            'sub_id': 'Jin2',
            'sub_type': 'Type094',
            'latitude': 15.1,
            'longitude': 110.1,
            'timestamp': now - timedelta(hours=1),
            'event_type': 'sighting'
        },
        {
            'sub_id': 'OtherSub',
            'sub_type': 'Type093',
            'latitude': 15.2,
            'longitude': 110.2,
            'timestamp': now,
            'event_type': 'sighting'
        }
    ]) 