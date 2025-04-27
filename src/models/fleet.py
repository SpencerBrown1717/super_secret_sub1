"""
Fleet management for submarine tracking.
"""
from typing import Dict, List, Optional, Any
import pandas as pd
import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try both relative and absolute imports to handle different execution contexts
try:
    from .submarine import Submarine, update_sub_state
except ImportError:
    try:
        # Add parent directory to path if running as a script
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.models.submarine import Submarine, update_sub_state
    except ImportError:
        logger.error("Failed to import Submarine class. Creating a minimal implementation.")
        
        # Define a minimal Submarine class if import fails
        class Submarine:
            def __init__(self, sub_id: str):
                self.id = sub_id
                self.name = f"Submarine {sub_id}"
                self.sub_type = "Unknown"
                self.history = []
                self.last_lat = None
                self.last_lon = None
                self.last_timestamp = None
                self.course = None
                self.speed = None
                
            def update_from_record(self, record: Dict[str, Any]) -> None:
                """Update submarine state from a data record."""
                # Extract location data
                if "latitude" in record and "longitude" in record:
                    self.last_lat = float(record["latitude"])
                    self.last_lon = float(record["longitude"])
                
                # Extract timestamp if available
                if "timestamp" in record:
                    self.last_timestamp = record["timestamp"]
                
                # Extract submarine type if available
                if "sub_type" in record:
                    self.sub_type = record["sub_type"]
                
                # Add record to history
                self.history.append(record)
        
        def update_sub_state(sub: Submarine) -> Dict[str, bool]:
            """Determine submarine state (at sea or in port)."""
            # Simple implementation - if we have position data, assume at sea
            if sub.last_lat is not None and sub.last_lon is not None:
                return {"at_sea": True, "in_port": False}
            return {"at_sea": False, "in_port": True}

class Fleet:
    """Manage a collection of submarines and their states."""
    
    def __init__(self, name: str = "Jin-class Fleet"):
        """Initialize a fleet with a name."""
        self.name = name
        self.subs: Dict[str, Submarine] = {}  # tests expect this attr
        
    def add_sub(self, sub: Submarine) -> None:
        """
        Add a submarine to the fleet.
        
        Args:
            sub: Submarine object to add
            
        Raises:
            ValueError: If submarine with same ID already exists
        """
        if sub.id in self.subs:
            raise ValueError(f"Submarine {sub.id} already in fleet")
        self.subs[sub.id] = sub
        
    def __getitem__(self, sub_id: str) -> Submarine:
        """Allow dictionary-style access to submarines."""
        if sub_id not in self.subs:
            raise KeyError(f"Submarine {sub_id} not found in fleet")
        return self.subs[sub_id]
        
    def get_all(self) -> List[Submarine]:
        """Get all submarines in the fleet."""
        return list(self.subs.values())
        
    def get_at_sea(self) -> List[Submarine]:
        """Get all submarines currently at sea."""
        result = []
        for sub in self.subs.values():
            try:
                if update_sub_state(sub)["at_sea"]:
                    result.append(sub)
            except Exception as e:
                logger.warning(f"Error checking at_sea status for {sub.id}: {e}")
        return result
        
    def get_in_port(self) -> List[Submarine]:
        """Get all submarines currently in port."""
        result = []
        for sub in self.subs.values():
            try:
                if update_sub_state(sub)["in_port"]:
                    result.append(sub)
            except Exception as e:
                logger.warning(f"Error checking in_port status for {sub.id}: {e}")
        return result
        
    def update_from_records(self, records: List[Dict]) -> None:
        """
        Update submarine states from a list of records.
        
        Args:
            records: List of dictionaries containing submarine data
        """
        if not records:
            logger.warning("Empty records list provided to update_from_records")
            return
            
        for record in records:
            if not isinstance(record, dict):
                logger.warning(f"Skipping non-dictionary record: {record}")
                continue
                
            sub_id = record.get("sub_id")
            if not sub_id:
                # Try alternative field names
                sub_id = record.get("id") or record.get("submarine_id") or record.get("name")
                if not sub_id:
                    logger.warning(f"Record missing submarine ID: {record}")
                    continue
                
            # Create submarine if it doesn't exist
            if sub_id not in self.subs:
                logger.info(f"Creating new submarine: {sub_id}")
                self.subs[sub_id] = Submarine(sub_id)
                
            # Update submarine with record data
            try:
                self.subs[sub_id].update_from_record(record)
            except Exception as e:
                logger.error(f"Error updating submarine {sub_id}: {e}")
                
    def load_from_csv(self, csv_path: str) -> None:
        """
        Load submarine data from a CSV file.
        
        Args:
            csv_path: Path to the CSV file
        """
        try:
            if not os.path.exists(csv_path):
                logger.error(f"CSV file not found: {csv_path}")
                return
                
            df = pd.read_csv(csv_path)
            records = df.to_dict("records")
            self.update_from_records(records)
            logger.info(f"Loaded {len(records)} records from {csv_path}")
        except Exception as e:
            logger.error(f"Error loading CSV file {csv_path}: {e}")
                
    def get_status_report(self) -> Dict:
        """Get a summary of fleet status."""
        total = len(self.subs)
        at_sea_count = len(self.get_at_sea())
        return {
            "total_subs": total,
            "at_sea": at_sea_count,
            "in_port": total - at_sea_count,
            "submarine_ids": list(self.subs.keys())
        }

# Global fleet instance for compatibility
FLEET = Fleet()

# Add convenience function for external usage
def get_fleet() -> Fleet:
    """Get the global fleet instance."""
    return FLEET