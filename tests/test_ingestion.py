import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.ingestion.data_loader import load_csv_data, fetch_api_data, filter_jin_class_subs, load_data
import os
import tempfile
import requests
from unittest.mock import patch, Mock

def test_load_csv_data():
    """Test loading submarine data from CSV file."""
    # Create a temporary CSV file with test data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("sub_id,sub_type,latitude,longitude,timestamp,event_type\n")
        f.write("Jin1,Type094,15.0,110.0,2024-03-20 10:00:00,departure\n")
        f.write("Jin2,Type094,15.1,110.1,2024-03-20 11:00:00,sighting\n")
        f.write("OtherSub,Type093,15.2,110.2,2024-03-20 12:00:00,sighting\n")
        temp_path = f.name
    
    try:
        df = load_csv_data(temp_path)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert 'timestamp' in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df['timestamp'])
    finally:
        os.unlink(temp_path)

def test_filter_jin_class_subs():
    """Test filtering for Jin-class submarines."""
    # Create test DataFrame
    data = {
        'sub_id': ['Jin1', 'Jin2', 'OtherSub'],
        'sub_type': ['Type094', 'Type094', 'Type093'],
        'latitude': [15.0, 15.1, 15.2],
        'longitude': [110.0, 110.1, 110.2],
        'timestamp': [datetime.now()] * 3
    }
    df = pd.DataFrame(data)
    
    # Test filtering by sub_type
    jin_df = filter_jin_class_subs(df)
    assert len(jin_df) == 2
    assert all(jin_df['sub_type'] == 'Type094')
    
    # Test filtering by sub_id
    df_no_type = df.drop('sub_type', axis=1)
    jin_df = filter_jin_class_subs(df_no_type)
    assert len(jin_df) == 2
    assert all(jin_df['sub_id'].isin(['Jin1', 'Jin2']))

def test_load_data_csv():
    """Test the main load_data function with CSV input."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("sub_id,sub_type,latitude,longitude,timestamp,event_type\n")
        f.write("Jin1,Type094,15.0,110.0,2024-03-20 10:00:00,departure\n")
        f.write("Jin2,Type094,15.1,110.1,2024-03-20 11:00:00,sighting\n")
        temp_path = f.name
    
    try:
        df = load_data(temp_path)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert all(df['sub_type'] == 'Type094')
    finally:
        os.unlink(temp_path)

def test_load_data_api(monkeypatch):
    """Test the main load_data function with API input."""
    # Create a mock response
    mock_response = Mock()
    mock_response.json.return_value = [
        {
            'sub_id': 'Jin1',
            'sub_type': 'Type094',
            'latitude': 15.0,
            'longitude': 110.0,
            'timestamp': '2024-03-20T10:00:00',
            'event_type': 'departure'
        }
    ]
    
    # Create a mock requests.get function
    def mock_get(*args, **kwargs):
        return mock_response
    
    # Apply the monkeypatch
    monkeypatch.setattr(requests, 'get', mock_get)
    
    # Test loading from API
    df = load_data('http://example.com/api/submarines')
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]['sub_id'] == 'Jin1'
    assert df.iloc[0]['sub_type'] == 'Type094'

def test_sentinel2_integration(monkeypatch):
    """Test Sentinel-2 satellite imagery integration."""
    # Create a mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = b'fake_image_data'
    
    # Create a mock requests.get function
    def mock_get(*args, **kwargs):
        return mock_response
    
    # Apply the monkeypatch
    monkeypatch.setattr(requests, 'get', mock_get)
    
    # Test accessing Sentinel-2 imagery
    response = requests.get('https://sentinel-s2-l1c.s3.amazonaws.com/tiles/10/100/100.jpg')
    assert response.status_code == 200
    assert response.content == b'fake_image_data'
