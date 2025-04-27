import pytest
import os
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from src.main import main, create_simulated_data

@pytest.fixture
def mock_args():
    """Mock command line arguments."""
    class Args:
        input = "data/input/submarine_tracking.csv"  # Changed to match main.py default
        output = "data/output/test_map.html"
        hours_ahead = 48
        step_hours = 6
        heading_var = 15.0
        monte_carlo = False
        simulate = False
        num_simulations = 100  # Changed from runs to num_simulations
    return Args()

@pytest.fixture
def sample_submarine_data():
    """Create sample submarine tracking data."""
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
            'sub_id': 'Jin1',
            'sub_type': 'Type094',
            'latitude': 15.1,
            'longitude': 110.1,
            'timestamp': now - timedelta(hours=1),
            'event_type': 'sighting'
        }
    ])

@pytest.fixture(autouse=True)
def setup_test_files(tmp_path):
    """Setup test files and directories."""
    # Create test directories
    os.makedirs("data/input", exist_ok=True)
    os.makedirs("data/output", exist_ok=True)
    
    # Create a test CSV file
    test_data = pd.DataFrame({
        'sub_id': ['Jin1'],
        'sub_type': ['Type094'],
        'latitude': [15.0],
        'longitude': [110.0],
        'timestamp': [datetime.now()],
        'event_type': ['departure']
    })
    test_data.to_csv("data/input/submarine_tracking.csv", index=False)
    
    yield
    
    # Cleanup
    try:
        os.remove("data/input/submarine_tracking.csv")
    except:
        pass

def test_create_simulated_data():
    """Test creation of simulated data."""
    df = create_simulated_data()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert all(col in df.columns for col in ['sub_id', 'sub_type', 'latitude', 'longitude', 'timestamp', 'event_type'])
    assert all(df['sub_type'] == 'Type094')
    assert len(df['sub_id'].unique()) == 6  # Six Jin-class submarines

@patch('argparse.ArgumentParser.parse_args')
@patch('src.ingestion.load_data')
@patch('src.visualization.leaflet_mapper.create_leaflet_map')
def test_main_with_csv_input(mock_create_map, mock_load_data, mock_parse_args, mock_args, sample_submarine_data):
    """Test main function with CSV input."""
    # Setup mocks
    mock_parse_args.return_value = mock_args
    mock_load_data.return_value = sample_submarine_data
    mock_create_map.return_value = Mock()
    
    # Run main
    main()
    
    # Verify calls
    mock_load_data.assert_called_once_with(mock_args.input)
    mock_create_map.assert_called_once()

@patch('argparse.ArgumentParser.parse_args')
@patch('src.visualization.leaflet_mapper.create_leaflet_map')
def test_main_with_simulated_data(mock_create_map, mock_parse_args, mock_args):
    """Test main function with simulated data."""
    # Setup mocks
    mock_args.simulate = True
    mock_args.input = "nonexistent.csv"  # Force simulation
    mock_parse_args.return_value = mock_args
    mock_create_map.return_value = Mock()
    
    # Run main
    main()
    
    # Verify that create_map was called
    mock_create_map.assert_called_once()

@patch('argparse.ArgumentParser.parse_args')
@patch('src.ingestion.load_data')
@patch('src.models.prediction.monte_carlo_simulation')
@patch('src.visualization.leaflet_mapper.create_leaflet_map')
def test_main_with_monte_carlo(mock_create_map, mock_monte_carlo, mock_load_data, mock_parse_args, mock_args, sample_submarine_data):
    """Test main function with Monte Carlo simulation."""
    # Setup mocks
    mock_args.monte_carlo = True
    mock_parse_args.return_value = mock_args
    mock_load_data.return_value = sample_submarine_data
    mock_monte_carlo.return_value = {
        'central_path': [[110.1, 15.1], [110.2, 15.2]],
        'left_path': [[110.0, 15.0], [110.1, 15.1]],
        'right_path': [[110.2, 15.2], [110.3, 15.3]],
        'forecast_times': [0, 6],
        'cone_polygon': [[110.0, 15.0], [110.3, 15.3], [110.1, 15.1]]
    }
    mock_create_map.return_value = Mock()
    
    # Run main
    main()
    
    # Verify calls
    mock_load_data.assert_called_once_with(mock_args.input)
    mock_monte_carlo.assert_called_once()
    mock_create_map.assert_called_once()

@patch('argparse.ArgumentParser.parse_args')
@patch('src.ingestion.load_data')
def test_main_with_empty_data(mock_load_data, mock_parse_args, mock_args):
    """Test main function with empty data."""
    # Setup mocks
    mock_parse_args.return_value = mock_args
    mock_load_data.return_value = pd.DataFrame()
    
    # Run main
    main()
    
    # Verify no further processing occurred
    mock_load_data.assert_called_once_with(mock_args.input)

@patch('argparse.ArgumentParser.parse_args')
@patch('src.ingestion.load_data')
def test_main_with_load_error(mock_load_data, mock_parse_args, mock_args):
    """Test main function with data loading error."""
    # Setup mocks
    mock_parse_args.return_value = mock_args
    mock_load_data.side_effect = Exception("Failed to load data")
    
    # Run main
    main()
    
    # Verify error handling
    mock_load_data.assert_called_once_with(mock_args.input) 