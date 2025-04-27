"""Submarine model for Jin-class SSBN tracking."""
import pandas as pd
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional

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
        
    def add_position(self, latitude: float, longitude: float, timestamp: str, 
                    depth: Optional[float] = None, speed: Optional[float] = None):
        """Add a new position record for this submarine."""
        # Validate the position (must be in water or at a base)
        is_valid = self._validate_position(latitude, longitude)
        
        if not is_valid:
            logger.warning(f"Invalid position for {self.name}: ({latitude}, {longitude})")
            # Find nearest valid position
            lat, lon = self._find_nearest_valid_position(latitude, longitude)
            logger.info(f"Adjusted to nearest valid position: ({lat}, {lon})")
            latitude, longitude = lat, lon
            
        position = {
            'latitude': float(latitude),
            'longitude': float(longitude),
            'timestamp': timestamp,
            'sub_id': self.sub_id
        }
        
        if depth is not None:
            position['depth'] = float(depth)
        if speed is not None:
            position['speed'] = float(speed)
            
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
                
        # Simplified check for major landmasses - would need a proper coastline check
        # These are very rough bounding boxes for mainland China
        if (20 < latitude < 45 and 105 < longitude < 124):
            # Check if it's in the Gulf of Tonkin or Bohai Sea
            if (18 < latitude < 21 and 107 < longitude < 109) or \
               (37 < latitude < 41 and 118 < longitude < 122):
                return True
            return False  # Likely on land
            
        # Taiwan rough check
        if (22 < latitude < 25.5 and 120 < longitude < 122):
            return False  # Likely on Taiwan
            
        # Japan rough check
        if (30 < latitude < 46 and 129 < longitude < 146):
            return False  # Likely on Japan
            
        # Philippines rough check
        if (5 < latitude < 19 and 117 < longitude < 127):
            return False  # Likely on Philippines
            
        # By default, assume it's in water (this is very simplified)
        return True
    
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