"""Submarine model for Jin-class SSBN tracking."""
import pandas as pd
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Naval bases coordinates (Jin-class submarines are only stationed at these bases)
NAVAL_BASES = {
    "Yulin": (18.229, 109.706),  # Yulin Naval Base on Hainan Island
    "Qingdao": (36.071, 120.418),
    "Ningbo": (29.868, 122.108),
    "Xiamen": (24.455, 118.082),
    "Xiaopingdao": (38.822, 121.536)
}

class Submarine:
    """Represents a Jin-class (Type 094) nuclear submarine."""
    
    def __init__(self, sub_id: str, name: Optional[str] = None):
        self.sub_id = sub_id
        self.name = name or f"Jin-{sub_id}"
        self.positions = []  # List of recorded positions (lat, long, timestamp)
        self.predicted_positions = []  # Predicted future positions
        self.confidence_intervals = []  # Confidence intervals for predictions
        self.historical_sightings = []  # Historical sightings from monitoring
        
    def add_position(self, latitude: float, longitude: float, timestamp: str, 
                    depth: Optional[float] = None, speed: Optional[float] = None,
                    is_historical: bool = False, is_simulated: bool = False,
                    is_prediction: bool = False):
        """Add a new position record for this submarine."""
        # Validate the position (must be in water or at a base)
        is_valid = self._validate_position(latitude, longitude)
        
        if not is_valid:
            logger.warning(f"Invalid position for {self.name}: ({latitude}, {longitude})")
            # Find nearest valid position
            lat, lon = self._find_nearest_valid_position(latitude, longitude)
            logger.info(f"Adjusted to nearest valid position: ({lat}, {lon})")
            latitude, longitude = lat, lon
            
        # Convert timestamp to standard format if needed
        try:
            if isinstance(timestamp, str):
                # Split into date and time parts
                if ' ' in timestamp:
                    date_part, time_part = timestamp.split(' ', 1)
                else:
                    date_part = timestamp
                    time_part = "00:00"

                # Handle incomplete dates (e.g., "2024-06-0")
                date_parts = date_part.split('-')
                if len(date_parts) == 3:
                    year = date_parts[0]
                    month = date_parts[1].zfill(2)
                    day = date_parts[2].zfill(2)
                    # Remove any time component that might be in the day part
                    day = day.split(' ')[0].split(':')[0]
                    date_part = f"{year}-{month}-{day}"

                # Handle time part
                if ':' in time_part:
                    time_parts = time_part.split(':')
                    if len(time_parts) >= 2:
                        hour = time_parts[0].zfill(2)
                        minute = time_parts[1].zfill(2)
                        time_part = f"{hour}:{minute}"
                    else:
                        time_part = "00:00"
                else:
                    time_part = "00:00"

                # Combine date and time
                timestamp_str = f"{date_part} {time_part}"
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M')
            elif isinstance(timestamp, pd.Timestamp):
                timestamp = timestamp.to_pydatetime()
            elif isinstance(timestamp, datetime):
                pass
            else:
                raise ValueError(f"Invalid timestamp type: {type(timestamp)}")
                
            # Convert back to string in standard format
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M')
        except Exception as e:
            logger.warning(f"Invalid timestamp format for {self.name}: {timestamp} - {str(e)}")
            timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M')
            
        position = {
            'latitude': float(latitude),
            'longitude': float(longitude),
            'timestamp': timestamp_str,
            'sub_id': self.sub_id,
            'is_historical': is_historical,
            'is_simulated': is_simulated,
            'is_prediction': is_prediction
        }
        
        if depth is not None:
            position['depth'] = float(depth)
        if speed is not None:
            position['speed'] = float(speed)
            
        if is_historical:
            self.historical_sightings.append(position)
        elif is_prediction:
            self.predicted_positions.append(position)
        else:
            self.positions.append(position)
        return position
    
    def _validate_position(self, latitude: float, longitude: float) -> bool:
        """
        Validate if a position is in water or at a naval base.
        This is a simplified version - a real implementation would use a coastline dataset.
        """
        # Check if position is at a naval base
        for base_name, (base_lat, base_lon) in NAVAL_BASES.items():
            # If within 5km of a naval base, consider it valid
            if self._haversine_distance(latitude, longitude, base_lat, base_lon) < 5:
                return True
                
        # Basic bounds check for the region of interest
        if (0 <= latitude <= 45 and 105 <= longitude <= 130):
            return True
            
        # If outside the region of interest, consider it invalid
        return False
    
    def _find_nearest_valid_position(self, latitude: float, longitude: float):
        """Find the nearest valid position in water or at a naval base."""
        # First check if near a naval base
        nearest_base = None
        min_distance = float('inf')
        
        for base_name, (base_lat, base_lon) in NAVAL_BASES.items():
            dist = self._haversine_distance(latitude, longitude, base_lat, base_lon)
            if dist < min_distance:
                min_distance = dist
                nearest_base = (base_lat, base_lon)
                
        # If very close to a base, return the base location
        if min_distance < 50:  # 50km
            return nearest_base
            
        # Otherwise, make small adjustments until in water
        # This is simplified; a real implementation would use coastline data
        # Try points in a spiral pattern around the original point
        for radius in range(1, 20):  # Try up to 20km away
            for angle in range(0, 360, 45):  # 8 directions
                # Calculate new point
                new_lat, new_lon = self._move_point(latitude, longitude, radius, angle)
                
                # Check if valid
                if self._validate_position(new_lat, new_lon):
                    return new_lat, new_lon
                    
        # If all else fails, return nearest naval base
        return nearest_base
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance between two points on earth."""
        from math import radians, sin, cos, sqrt, atan2
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        r = 6371  # Radius of earth in kilometers
        
        return c * r
    
    def _move_point(self, lat: float, lon: float, distance: float, bearing: float) -> tuple:
        """Move a point by a distance (km) in a direction (degrees)."""
        from math import radians, sin, cos, asin, atan2, degrees
        
        # Convert to radians
        lat1 = radians(lat)
        lon1 = radians(lon)
        bearing = radians(bearing)
        
        # Earth radius in km
        R = 6371.0
        
        # Calculate new position
        lat2 = asin(sin(lat1) * cos(distance/R) + cos(lat1) * sin(distance/R) * cos(bearing))
        lon2 = lon1 + atan2(sin(bearing) * sin(distance/R) * cos(lat1), 
                            cos(distance/R) - sin(lat1) * sin(lat2))
        
        # Convert back to degrees
        return degrees(lat2), degrees(lon2)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert submarine data to dictionary for serialization."""
        return {
            'sub_id': self.sub_id,
            'name': self.name,
            'positions': self.positions,
            'predicted_positions': self.predicted_positions,
            'confidence_intervals': self.confidence_intervals
        }
        
    def __repr__(self) -> str:
        """String representation of the submarine."""
        return f"Submarine(id={self.sub_id}, name={self.name}, positions={len(self.positions)})"

    def load_historical_sightings(self, sightings_path: str) -> None:
        """Load historical sightings from the monitoring CSV file."""
        try:
            if not os.path.exists(sightings_path):
                logger.warning(f"Historical sightings file not found: {sightings_path}")
                return
            
            df = pd.read_csv(sightings_path)
            for _, row in df.iterrows():
                self.add_position(
                    latitude=row['latitude'],
                    longitude=row['longitude'],
                    timestamp=row['date'],
                    is_historical=True
                )
            logger.info(f"Loaded {len(df)} historical sightings for submarine {self.sub_id}")
        except Exception as e:
            logger.error(f"Error loading historical sightings: {e}")

    def get_all_positions(self) -> List[Dict[str, Any]]:
        """Get all positions including historical sightings."""
        return self.positions + self.historical_sightings

def load_submarines_from_csv(file_path: Path) -> List[Submarine]:
    """Load submarine data from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        
        # Get unique submarine IDs
        sub_ids = df['sub_id'].unique()
        
        submarines = []
        for sub_id in sub_ids:
            # Create submarine object
            sub = Submarine(sub_id=str(sub_id))
            
            # Add positions
            sub_data = df[df['sub_id'] == sub_id].sort_values('timestamp')
            for _, row in sub_data.iterrows():
                sub.add_position(
                    latitude=row['latitude'],
                    longitude=row['longitude'],
                    timestamp=row['timestamp'],
                    depth=row.get('depth'),
                    speed=row.get('speed')
                )
                
            submarines.append(sub)
            
        logger.info(f"Loaded {len(submarines)} submarines from {file_path}")
        return submarines
        
    except Exception as e:
        logger.error(f"Error loading submarines from {file_path}: {e}")
        return []