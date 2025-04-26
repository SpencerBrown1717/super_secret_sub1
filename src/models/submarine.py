import pandas as pd

class Submarine:
    """Class to represent a Jin-class submarine and its state."""
    def __init__(self, sub_id: str):
        self.id = sub_id
        self.last_lat = None
        self.last_lon = None
        self.last_time = None
        self.at_sea = False
        self.history = []
        
    def update_from_record(self, record):
        """Update submarine state from a new record."""
        self.last_lat = record['latitude']
        self.last_lon = record['longitude']
        self.last_time = record['timestamp']
        
        # Update at_sea status if event type is available
        if 'event_type' in record:
            if record['event_type'].lower() == 'departure':
                self.at_sea = True
            elif record['event_type'].lower() == 'arrival':
                self.at_sea = False
        
        # Add to history
        self.history.append(record)
    
    def __str__(self):
        status = "at sea" if self.at_sea else "in port"
        return f"Submarine {self.id}: Last seen at ({self.last_lat}, {self.last_lon}) at {self.last_time}, {status}"

def update_sub_state(records: pd.DataFrame) -> dict:
    """
    Update submarine state based on records.
    Returns a dictionary with the submarine's current state.
    """
    if len(records) == 0:
        return None
    
    # Sort records by timestamp to ensure we get latest
    records = records.sort_values('timestamp')
    last_record = records.iloc[-1]
    
    # Determine if submarine is at sea
    at_sea = False
    if 'event_type' in records.columns:
        # Filter to just event_type records and get the most recent
        events = records[records['event_type'].notna()].sort_values('timestamp')
        if len(events) > 0:
            last_event = events.iloc[-1]['event_type'].lower()
            at_sea = last_event == 'departure'
    
    return {
        "last_lat": last_record['latitude'],
        "last_lon": last_record['longitude'],
        "last_time": last_record['timestamp'],
        "at_sea": at_sea,
        "history": records
    }
