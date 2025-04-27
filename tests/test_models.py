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

def test_update_sub_state():
    """Test the update_sub_state function with a submarine."""
    sub = Submarine("Jin1")
    record = {
        'latitude': 15.0,
        'longitude': 110.0,
        'timestamp': datetime.now(),
        'event_type': 'departure'
    }
    sub.update_from_record(record)
    state = update_sub_state(sub)
    assert state is not None
    assert state["at_sea"]
    assert not state["in_port"]

def test_update_sub_state_empty():
    """Test update_sub_state with empty submarine."""
    sub = Submarine("Jin1")
    state = update_sub_state(sub)
    assert state is None

def test_update_sub_state_no_events():
    """Test update_sub_state with submarine but no events."""
    sub = Submarine("Jin1")
    record = {
        'latitude': 15.0,
        'longitude': 110.0,
        'timestamp': datetime.now()
    }
    sub.update_from_record(record)
    state = update_sub_state(sub)
    assert state is not None
    assert not state["at_sea"]
    assert state["in_port"]
