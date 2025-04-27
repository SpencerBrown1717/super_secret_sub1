import pytest
from datetime import datetime, timedelta
from src.fleet import SubmarineFleet
from src.models.submarine import Submarine

@pytest.fixture
def sample_submarines():
    """Create sample submarines for testing."""
    return [
        Submarine("Jin1"),
        Submarine("Jin2"),
        Submarine("Jin3")
    ]

@pytest.fixture
def sample_records():
    """Create sample records for testing."""
    now = datetime.now()
    return [
        {
            'sub_id': 'Jin1',
            'sub_type': 'Type094',
            'latitude': 15.0,
            'longitude': 110.0,
            'timestamp': now,
            'event_type': 'departure',
            'color': 'red'
        },
        {
            'sub_id': 'Jin2',
            'sub_type': 'Type094',
            'latitude': 16.0,
            'longitude': 111.0,
            'timestamp': now,
            'event_type': 'sighting',
            'color': 'blue'
        }
    ]

def test_fleet_initialization(sample_submarines):
    """Test fleet initialization with submarines."""
    fleet = SubmarineFleet(sample_submarines)
    assert len(fleet.get_all()) == 3
    assert fleet["Jin1"].id == "Jin1"
    assert fleet["Jin2"].id == "Jin2"
    assert fleet["Jin3"].id == "Jin3"

def test_fleet_add_sub():
    """Test adding a new submarine to the fleet."""
    fleet = SubmarineFleet()
    sub = Submarine("Jin1")
    fleet.add_sub(sub)
    assert len(fleet.get_all()) == 1
    assert fleet["Jin1"] == sub

def test_fleet_add_duplicate_sub():
    """Test adding a duplicate submarine raises error."""
    fleet = SubmarineFleet()
    sub1 = Submarine("Jin1")
    sub2 = Submarine("Jin1")
    fleet.add_sub(sub1)
    with pytest.raises(ValueError):
        fleet.add_sub(sub2)

def test_fleet_update_from_records(sample_records):
    """Test updating submarines from records."""
    fleet = SubmarineFleet()
    fleet.update_from_records(sample_records)
    
    assert len(fleet.get_all()) == 2
    assert fleet["Jin1"].at_sea
    assert not fleet["Jin2"].at_sea
    assert fleet["Jin1"].color == "red"
    assert fleet["Jin2"].color == "blue"

def test_fleet_get_at_sea(sample_records):
    """Test getting submarines at sea."""
    fleet = SubmarineFleet()
    fleet.update_from_records(sample_records)
    at_sea = fleet.get_at_sea()
    assert len(at_sea) == 1
    assert at_sea[0].id == "Jin1"

def test_fleet_get_in_port(sample_records):
    """Test getting submarines in port."""
    fleet = SubmarineFleet()
    fleet.update_from_records(sample_records)
    in_port = fleet.get_in_port()
    assert len(in_port) == 1
    assert in_port[0].id == "Jin2"

def test_fleet_status_report(sample_records):
    """Test generating status report."""
    fleet = SubmarineFleet()
    fleet.update_from_records(sample_records)
    report = fleet.get_status_report()
    
    assert report["total_subs"] == 2
    assert report["at_sea"] == 1
    assert report["in_port"] == 1
    assert "Jin1" in report["submarines"]
    assert "Jin2" in report["submarines"]
    assert report["submarines"]["Jin1"]["status"] == "at sea"
    assert report["submarines"]["Jin2"]["status"] == "in port"

def test_fleet_handles_bad_records():
    """Test fleet handles bad records gracefully."""
    bad_records = [
        {'sub_id': 'Jin1', 'latitude': 91.0},  # Invalid latitude
        {'sub_id': 'Jin2', 'longitude': 181.0},  # Invalid longitude
        {'sub_id': 'Jin3', 'timestamp': 'not-a-date'},  # Invalid timestamp
        {'sub_id': 'Jin4', 'event_type': 'unknown'},  # Invalid event type
    ]
    
    fleet = SubmarineFleet()
    fleet.update_from_records(bad_records)  # Should not raise exceptions
    
    # Verify fleet state is unchanged
    assert len(fleet.get_all()) == 0

def test_fleet_handles_missing_sub_id():
    """Test fleet handles records with missing sub_id."""
    records = [
        {'latitude': 15.0, 'longitude': 110.0},  # Missing sub_id
        {'sub_id': None, 'latitude': 16.0, 'longitude': 111.0},  # None sub_id
    ]
    
    fleet = SubmarineFleet()
    fleet.update_from_records(records)  # Should not raise exceptions
    
    # Verify fleet state is unchanged
    assert len(fleet.get_all()) == 0 