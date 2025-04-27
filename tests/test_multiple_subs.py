import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.models.submarine import Submarine
from src.ingestion.data_loader import JIN_SUBMARINES

def test_track_all_jin_subs():
    """Test tracking all 6 Jin-class submarines simultaneously."""
    # Create a submarine object for each Jin-class sub
    subs = {sub_id: Submarine(sub_id) for sub_id in JIN_SUBMARINES}
    
    # Generate test data for each submarine
    now = datetime.now()
    test_data = []
    
    # Different colors for each submarine
    colors = {
        "Jin1": "red",
        "Jin2": "blue",
        "Jin3": "green",
        "Jin4": "purple",
        "Jin5": "orange",
        "Jin6": "darkred"
    }
    
    # Generate multiple records for each submarine
    for sub_id in JIN_SUBMARINES:
        # Base location (roughly around the South China Sea)
        base_lat, base_lon = 18.2, 109.5
        
        # Generate 3 records for each submarine
        for i in range(3):
            # Time: progressively earlier
            time_offset = timedelta(days=i, hours=i*2)
            timestamp = now - time_offset
            
            # First record is departure from base, others are random positions
            if i == 0:
                lat, lon = base_lat, base_lon
                event_type = "departure"
            else:
                # Random position in the South China Sea (rough bounds)
                lat = base_lat + (i * 0.5)
                lon = base_lon + (i * 0.5)
                event_type = "sighting"
            
            record = {
                'sub_id': sub_id,
                'sub_type': 'Type094',
                'latitude': lat,
                'longitude': lon,
                'timestamp': timestamp,
                'event_type': event_type,
                'color': colors[sub_id]
            }
            test_data.append(record)
    
    # Convert to DataFrame
    df = pd.DataFrame(test_data)
    
    # Update each submarine with its records
    for sub_id, sub in subs.items():
        sub_records = df[df['sub_id'] == sub_id].sort_values('timestamp')
        for _, record in sub_records.iterrows():
            sub.update_from_record(record)
    
    # Verify all submarines are tracked
    assert len(subs) == 6, "Should track all 6 Jin-class submarines"
    
    # Verify each submarine has the correct number of records
    for sub_id, sub in subs.items():
        assert len(sub.history) == 3, f"Submarine {sub_id} should have 3 records"
        assert sub.id == sub_id, f"Submarine ID should match {sub_id}"
        assert sub.color == colors[sub_id], f"Submarine {sub_id} should have color {colors[sub_id]}"
        
        # Verify the last record is the most recent
        last_record = sub.history[-1]
        assert last_record['timestamp'] == max(r['timestamp'] for r in sub.history)
        
        # Verify status is correct based on last event
        if last_record['event_type'] == 'departure':
            assert sub.at_sea, f"Submarine {sub_id} should be at sea"
        else:
            assert not sub.at_sea, f"Submarine {sub_id} should be in port"

def test_simultaneous_tracking():
    """Test that all submarines can be tracked simultaneously with different colors."""
    # Create test data for all submarines
    now = datetime.now()
    test_data = []
    
    # Different colors for each submarine
    colors = {
        "Jin1": "red",
        "Jin2": "blue",
        "Jin3": "green",
        "Jin4": "purple",
        "Jin5": "orange",
        "Jin6": "darkred"
    }
    
    # Generate one record for each submarine at the same time
    for sub_id in JIN_SUBMARINES:
        # Different base locations for each submarine
        base_lat = 18.2 + (JIN_SUBMARINES.index(sub_id) * 0.5)
        base_lon = 109.5 + (JIN_SUBMARINES.index(sub_id) * 0.5)
        
        record = {
            'sub_id': sub_id,
            'sub_type': 'Type094',
            'latitude': base_lat,
            'longitude': base_lon,
            'timestamp': now,
            'event_type': 'sighting',
            'color': colors[sub_id]
        }
        test_data.append(record)
    
    # Convert to DataFrame
    df = pd.DataFrame(test_data)
    
    # Create and update submarines
    subs = {}
    for _, record in df.iterrows():
        sub_id = record['sub_id']
        if sub_id not in subs:
            subs[sub_id] = Submarine(sub_id)
        subs[sub_id].update_from_record(record)
    
    # Verify all submarines are tracked with correct colors
    assert len(subs) == 6, "Should track all 6 Jin-class submarines"
    for sub_id, sub in subs.items():
        assert sub.color == colors[sub_id], f"Submarine {sub_id} should have color {colors[sub_id]}"
        assert len(sub.history) == 1, f"Submarine {sub_id} should have 1 record"
        assert sub.last_lat == 18.2 + (JIN_SUBMARINES.index(sub_id) * 0.5)
        assert sub.last_lon == 109.5 + (JIN_SUBMARINES.index(sub_id) * 0.5) 