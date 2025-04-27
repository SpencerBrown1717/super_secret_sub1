"""
Submarine tracking model with data quality improvements.
"""
import enum
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
import requests
import os
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────
#  Ultra-light Ocean / Bathymetry model (≈2 km resolution mask)
#  Any point whose depth < 150 m or is on land is forbidden.
#  For production, swap this with ETOPO1, GEBCO, or Naval bathymetry.
# ────────────────────────────────────────────────────────────────────
_LON_MIN, _LON_MAX =  90.0, 140.0
_LAT_MIN, _LAT_MAX =   5.0,  45.0
_CELL   = 0.02                    # ≈2.2 km at the equator
_Nx     = int((_LON_MAX-_LON_MIN)/_CELL) + 1
_Ny     = int((_LAT_MAX-_LAT_MIN)/_CELL) + 1
_bathy  = np.full((_Ny, _Nx), True, dtype=bool)  # True  = water&deep

# Hard-coded rectangles for land + shelves (<150 m)
# Mainland China
_bathy[0:100, 0:100] = False  # Mainland China
_bathy[0:50, 100:150] = False  # Taiwan
_bathy[50:100, 100:150] = False  # Philippines
_bathy[100:150, 0:50] = False  # Vietnam
_bathy[100:150, 50:100] = False  # Malaysia

def _is_on_land(lat: float, lon: float) -> bool:
    """Check if a point is on land using the bathymetry mask."""
    if not (_LAT_MIN <= lat <= _LAT_MAX and _LON_MIN <= lon <= _LON_MAX):
        return True  # Outside our region of interest is considered land
        
    # Convert lat/lon to grid indices
    x = int((lon - _LON_MIN) / _CELL)
    y = int((lat - _LAT_MIN) / _CELL)
    
    # Check if point is in our grid
    if 0 <= x < _Nx and 0 <= y < _Ny:
        return not _bathy[y, x]
    return True  # Outside grid is considered land

class Status(enum.Enum):
    """Submarine operational status."""
    AT_SEA = "AT_SEA"
    IN_PORT = "IN_PORT"
    UNKNOWN = "UNKNOWN"

class Submarine:
    """Class to represent a Jin-class submarine and its state."""
    # Events explicitly accepted by every layer (Fleet + tests)
    VALID_EVENTS = {"departure", "arrival", "sighting"}

    def __init__(self, sub_id: str):
        self.id = sub_id
        self.last_lat: Optional[float] = None
        self.last_lon: Optional[float] = None
        self.last_time: Optional[datetime] = None
        self.status = Status.IN_PORT  # Default to in port
        self.history: List[Dict] = []
        self.color: Optional[str] = None
        
    def _clamp_coordinates(self, lat: float, lon: float) -> Tuple[float, float]:
        """Clamp coordinates to valid ranges and check if on land."""
        try:
            lat, lon = float(lat), float(lon)
        except (TypeError, ValueError):
            logger.error(f"Invalid coordinate types: lat={type(lat)}, lon={type(lon)}")
            raise ValueError("Coordinates must be numeric")

        # ✅ boundary values (±90 / ±180) are valid
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            logger.error(f"Coordinates out of range: lat={lat}, lon={lon}")
            raise ValueError("Coordinates out of valid range")
            
        # Check if point is on land
        if _is_on_land(lat, lon):
            logger.error(f"Coordinates on land: lat={lat}, lon={lon}")
            raise ValueError("Coordinates indicate submarine is on land")
            
        return lat, lon
        
    def _validate_timestamp(self, timestamp) -> datetime:
        """Validate and convert timestamp to datetime."""
        if isinstance(timestamp, str):
            try:
                return pd.to_datetime(timestamp)
            except Exception as e:
                logger.error(f"Invalid timestamp format: {timestamp}")
                raise ValueError(f"Invalid timestamp format: {timestamp}") from e
        elif isinstance(timestamp, datetime):
            return timestamp
        else:
            raise ValueError(f"Invalid timestamp type: {type(timestamp)}")
            
    def _push(self, record: Dict) -> None:
        """Update position and timestamp from a record without changing status."""
        if 'latitude' in record and 'longitude' in record:
            lat, lon = self._clamp_coordinates(
                float(record['latitude']),
                float(record['longitude'])
            )
            self.last_lat = lat
            self.last_lon = lon
            
        if 'timestamp' in record:
            self.last_time = self._validate_timestamp(record['timestamp'])
            
        if 'color' in record:
            self.color = record['color']
            
        self.history.append(record)
        
    def update_from_record(self, record: Dict) -> None:
        """
        Update submarine state from a new record with data validation.
        
        Args:
            record: Dictionary containing submarine data
            
        Raises:
            ValueError: If required data is missing or invalid
        """
        try:
            # Update status based on event type
            if 'event_type' in record:
                event_type = record['event_type'].lower()
                if event_type not in Submarine.VALID_EVENTS:
                    raise ValueError(f"Unknown event type: {event_type!r}")

                # "sighting" = position update only
                if event_type == "sighting":
                    self._push(record)
                    return
                    
                if event_type == 'departure':
                    self.status = Status.AT_SEA
                elif event_type == 'arrival':
                    self.status = Status.IN_PORT
                    
            # Update position and other fields
            self._push(record)
            
        except Exception as e:
            logger.error(f"Error updating submarine {self.id}: {e}")
            raise
            
    @property
    def at_sea(self) -> bool:
        """Check if submarine is at sea."""
        return self.status == Status.AT_SEA
        
    def __str__(self) -> str:
        """String representation of submarine state."""
        status = self.status.value.lower().replace('_', ' ')
        color_info = f", color: {self.color}" if self.color else ""
        position = f"({self.last_lat}, {self.last_lon})" if self.last_lat and self.last_lon else "unknown"
        time = self.last_time.isoformat() if self.last_time else "unknown"
        return f"Submarine {self.id}: Last seen at {position} at {time}, {status}{color_info}"

    def state_flags(self) -> Dict[str, bool]:
        """Return boolean flags in the shape legacy tests expect."""
        return {
            "at_sea": self.status == Status.AT_SEA,
            "in_port": self.status == Status.IN_PORT
        }

def update_sub_state(sub: Submarine) -> dict[str, bool] | None:
    """
    Update submarine state based on records with data validation.
    
    Args:
        sub: Submarine object to update
        
    Returns:
        Dictionary with submarine's current state or None if no history
    """
    # Legacy contract: return None if the boat has no events yet
    if not sub.history:
        return None
    return sub.state_flags()

def load_submarines_from_csv(csv_path: str) -> Dict[str, 'Submarine']:
    """Load submarine histories from a CSV file (e.g., location.csv or bases.csv)."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    subs: Dict[str, Submarine] = {}
    # Try to infer the sub id column
    sub_id_col = None
    for candidate in ["sub_id", "id", "name"]:
        if candidate in df.columns:
            sub_id_col = candidate
            break
    if sub_id_col is None:
        raise ValueError("No submarine ID column found in CSV.")
    for record in df.to_dict("records"):
        sub_id = record.get(sub_id_col)
        if not sub_id:
            continue
        if sub_id not in subs:
            subs[sub_id] = Submarine(sub_id)
        try:
            subs[sub_id].update_from_record(record)
        except Exception as e:
            logger.error(f"Skipping invalid record for {sub_id}: {e}")
    return subs

def load_submarines_from_api(api_url: str) -> Dict[str, 'Submarine']:
    """Fetch submarine data from a generic API endpoint and build Submarine objects."""
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"API fetch failed: {e}")
        return {}
    subs: Dict[str, Submarine] = {}
    # Assume data is a list of dicts
    for record in data:
        sub_id = record.get("sub_id") or record.get("id") or record.get("name")
        if not sub_id:
            continue
        if sub_id not in subs:
            subs[sub_id] = Submarine(sub_id)
        try:
            subs[sub_id].update_from_record(record)
        except Exception as e:
            logger.error(f"Skipping invalid API record for {sub_id}: {e}")
    return subs

def load_submarines(source: str, is_api: bool = False) -> Dict[str, 'Submarine']:
    """Unified loader: from CSV or API, returns dict of Submarine objects."""
    if is_api:
        return load_submarines_from_api(source)
    else:
        return load_submarines_from_csv(source)

def build_submarines_with_bases_and_locations(
    location_csv: str = "../data/input/submarine_location.csv",
    bases_csv: str = "../data/input/submarine_bases.csv",
    sub_home_base: dict = None
) -> Dict[str, Submarine]:
    """
    Build submarine objects from location and base CSVs, using base as fallback for subs with no location history.
    sub_home_base: dict mapping sub_id to base_id (as str or int)
    """
    # Load movement histories
    subs = load_submarines_from_csv(location_csv)
    # Load bases
    bases_df = pd.read_csv(bases_csv)
    base_records = {str(row['id']): row for _, row in bases_df.iterrows()}
    # Default mapping if not provided
    if sub_home_base is None:
        sub_home_base = {
            "Jin1": "1",
            "Jin2": "1",
            "Jin3": "1",
            "Jin4": "1",
            # Add more as needed
        }
    # Add base as dummy history for subs with no location history
    for sub_id, base_id in sub_home_base.items():
        if sub_id not in subs or not subs[sub_id].history:
            base = base_records.get(str(base_id))
            if base:
                dummy_record = {
                    "sub_id": sub_id,
                    "latitude": base["latitude"],
                    "longitude": base["longitude"],
                    "timestamp": pd.Timestamp.now(),  # or a default/earliest time
                    "event_type": "base_origin"
                }
                if sub_id not in subs:
                    subs[sub_id] = Submarine(sub_id)
                subs[sub_id].update_from_record(dummy_record)
    # Ensure all timestamps in all histories are pd.Timestamp
    for sub in subs.values():
        for rec in sub.history:
            if isinstance(rec.get("timestamp"), str):
                try:
                    rec["timestamp"] = pd.to_datetime(rec["timestamp"])
                except Exception:
                    pass
    return subs

def get_all_histories(subs: Dict[str, Submarine], verbose: bool = True) -> list:
    """Return a flat list of all records for all subs, and print counts if verbose."""
    histories = []
    for sub_id, sub in subs.items():
        if verbose:
            print(f"{sub_id}: {len(sub.history)} records")
        histories.extend(sub.history)
    return histories

if __name__ == "__main__":
    # Test: build and print submarine histories
    subs = build_submarines_with_bases_and_locations()
    get_all_histories(subs, verbose=True)
