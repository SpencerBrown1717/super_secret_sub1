import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.models.submarine import Submarine, update_sub_state

def test_submarine_initialization():
    """Test submarine class initialization."""
    sub = Submarine("Jin1")
    assert sub.id == "Jin1"
    assert sub.last_lat is None
    assert sub.last_lon is None
    assert sub.last_time is None
    assert not sub.at_sea
    assert len(sub.history) == 0

def test_submarine_update_from_record():
    """Test updating submarine state from a record."""
    sub = Submarine("Jin1")
    record = {
        'latitude': 15.0,
        'longitude': 110.0,
        'timestamp': datetime.now(),
        'event_type': 'departure'
    }
    
    sub.update_from_record(record)
    assert sub.last_lat == 15.0
    assert sub.last_lon == 110.0
    assert sub.last_time == record['timestamp']
    assert sub.at_sea
    assert len(sub.history) == 1
    assert sub.history[0] == record

def test_submarine_update_from_record_no_event():
    """Test updating submarine state from a record without event type."""
    sub = Submarine("Jin1")
    record = {
        'latitude': 15.0,
        'longitude': 110.0,
        'timestamp': datetime.now()
    }
    
    sub.update_from_record(record)
    assert sub.last_lat == 15.0
    assert sub.last_lon == 110.0
    assert sub.last_time == record['timestamp']
    assert not sub.at_sea  # Should remain False without event type

def test_update_sub_state(sample_submarine_records):
    """Test the update_sub_state function with a DataFrame."""
    state = update_sub_state(sample_submarine_records)
    assert state is not None
    assert state["last_lat"] == 15.1
    assert state["last_lon"] == 110.1
    assert state["at_sea"]  # Should be at sea due to departure event
    assert len(state["history"]) == 2

def test_update_sub_state_empty():
    """Test update_sub_state with empty DataFrame."""
    records = pd.DataFrame(columns=['latitude', 'longitude', 'timestamp', 'event_type'])
    state = update_sub_state(records)
    assert state is None

def test_update_sub_state_no_events():
    """Test update_sub_state with records but no events."""
    now = datetime.now()
    records = pd.DataFrame([
        {
            'latitude': 15.0,
            'longitude': 110.0,
            'timestamp': now - timedelta(hours=1),
            'event_type': None
        }
    ])
    
    state = update_sub_state(records)
    assert state is not None
    assert not state["at_sea"]  # Should be False without any events
