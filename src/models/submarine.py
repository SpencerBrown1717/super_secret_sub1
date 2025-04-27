"""
Submarine tracking model with data quality improvements.
"""
import enum
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)

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
        """Clamp coordinates to valid ranges."""
        try:
            lat, lon = float(lat), float(lon)
        except (TypeError, ValueError):
            logger.error(f"Invalid coordinate types: lat={type(lat)}, lon={type(lon)}")
            raise ValueError("Coordinates must be numeric")

        # ✅ boundary values (±90 / ±180) are valid
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            logger.error(f"Coordinates out of range: lat={lat}, lon={lon}")
            raise ValueError("Coordinates out of valid range")
            
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
