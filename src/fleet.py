"""
Central registry and coordinator for tracking multiple submarines.
"""
from collections import defaultdict
from typing import Dict, Iterable, List, Optional
from datetime import datetime, timezone
import logging
import pandas as pd

from .models.submarine import Submarine

# Configure logging
logger = logging.getLogger(__name__)

class SubmarineFleet:
    """Central registry & coordinator for any number of submarines."""
    def __init__(self, subs: Optional[Iterable[Submarine]] = None) -> None:
        """Initialize the fleet with optional initial submarines."""
        self._subs: Dict[str, Submarine] = {sub.id: sub for sub in (subs or [])}
        logger.info(f"Initialized fleet with {len(self._subs)} submarines")

    # ---------- CRUD Operations ----------
    def add_sub(self, sub: Submarine) -> None:
        """Add a new submarine to the fleet."""
        if sub.id in self._subs:
            raise ValueError(f"Submarine {sub.id} already tracked")
        self._subs[sub.id] = sub
        logger.info(f"Added submarine {sub.id} to fleet")

    def __getitem__(self, sub_id: str) -> Submarine:
        """Get a submarine by its ID."""
        try:
            return self._subs[sub_id]
        except KeyError:
            logger.error(f"Submarine {sub_id} not found in fleet")
            raise

    def get_all(self) -> List[Submarine]:
        """Get all submarines in the fleet."""
        return list(self._subs.values())

    def get_at_sea(self) -> List[Submarine]:
        """Get all submarines currently at sea."""
        return [sub for sub in self._subs.values() if sub.at_sea]

    def get_in_port(self) -> List[Submarine]:
        """Get all submarines currently in port."""
        return [sub for sub in self._subs.values() if not sub.at_sea]

    # ---------- Batch Operations ----------
    def update_from_records(self, records: Iterable[dict]) -> None:
        """
        Update multiple submarines from a batch of records.
        
        Args:
            records: Iterable of record dictionaries containing submarine data
            
        Note:
            Records for unknown submarines are logged but don't raise exceptions
        """
        REQUIRED = ("sub_id", "latitude", "longitude")
        bad_records: defaultdict[str, list[dict]] = defaultdict(list)
        
        for record in records:
            # --- 1. ensure required fields present and non-blank ---
            if any(record.get(k) in ("", None) for k in REQUIRED):
                logger.warning(f"Record missing required field: {record}")
                continue

            sub_id = record["sub_id"]  # we know it exists and is non-empty

            # --- 2. numeric lat/lon within inclusive bounds ---
            try:
                lat = float(record["latitude"])
                lon = float(record["longitude"])
            except ValueError as e:
                bad_records[sub_id].append(record)
                logger.warning(f"Invalid coordinates for submarine {sub_id}: {e}")
                continue

            if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                bad_records[sub_id].append(record)
                logger.warning(f"Coordinates out of range: lat={lat}, lon={lon}")
                continue

            # --- 3. build the submarine entry – ignore optional blanks ---
            try:
                # Convert timestamp if present and non-empty
                if record.get("timestamp"):
                    try:
                        ts = pd.to_datetime(record["timestamp"])
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                        record["timestamp"] = ts
                    except Exception:
                        # Don't fail - timestamp is optional
                        logger.warning(f"Invalid timestamp for submarine {sub_id}, ignoring")
                        record.pop("timestamp", None)

                # Create/update submarine with validated record
                if sub_id not in self._subs:
                    sub = Submarine(sub_id)
                    sub.update_from_record(record)
                    self._subs[sub_id] = sub
                    logger.info(f"Created new submarine {sub_id}")
                else:
                    self._subs[sub_id].update_from_record(record)
                    logger.info(f"Updated submarine {sub_id}")

            except Exception as e:
                bad_records[sub_id].append(record)
                logger.error(f"Error processing record for {sub_id}: {e}")
        
        if bad_records:
            logger.warning(f"Failed to process records for submarines: {list(bad_records.keys())}")

    # ---------- Status Reporting ----------
    def get_status_report(self) -> dict:
        """Generate a status report for all submarines."""
        return {
            "total_subs": len(self._subs),
            "at_sea": len(self.get_at_sea()),
            "in_port": len(self.get_in_port()),
            "submarines": {
                sub_id: {
                    "status": "at sea" if sub.at_sea else "in port",
                    "last_seen": sub.last_time.isoformat() if sub.last_time else None,
                    "position": (sub.last_lat, sub.last_lon) if sub.last_lat and sub.last_lon else None,
                    "color": sub.color
                }
                for sub_id, sub in self._subs.items()
            }
        } 