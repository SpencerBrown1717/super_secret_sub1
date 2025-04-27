"""submarine_predictor.py  ✨
A crisp, self‑contained prediction engine for submarine movements
(beautifully formatted, typing‑strict, and ready for unit tests).
"""
from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Tuple, TypedDict

import numpy as np
import pandas as pd
from shapely.geometry import Point

# ────────────────────────────────────────────────────────────────────────────────
# External domain models (kept as *Any* to avoid circular imports)
# ────────────────────────────────────────────────────────────────────────────────
Submarine = Any  # forward‑decl for type checkers

# ────────────────────────────────────────────────────────────────────────────────
# Logging
# ────────────────────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ────────────────────────────────────────────────────────────────────────────────
# Helper types & constants
# ────────────────────────────────────────────────────────────────────────────────

EARTH_RADIUS_KM = 6_371.0088  # mean Earth radius

class Position(TypedDict):
    latitude: float
    longitude: float
    timestamp: datetime  # ALWAYS store as *datetime* inside the predictor
    depth: float | None
    speed: float | None  # knots
    sub_id: str
    is_historical: bool
    source: str


# ────────────────────────────────────────────────────────────────────────────────
# Maths helpers
# ────────────────────────────────────────────────────────────────────────────────

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great‑circle distance between two WGS‑84 points (in km)."""
    φ1, φ2 = map(math.radians, (lat1, lat2))
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)
    a = math.sin(Δφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _destination_point(lat: float, lon: float, bearing_deg: float, dist_km: float) -> Tuple[float, float]:
    """Project a point *dist_km* away at *bearing_deg* (0° = north)."""
    φ1 = math.radians(lat)
    λ1 = math.radians(lon)
    θ = math.radians(bearing_deg)
    δ = dist_km / EARTH_RADIUS_KM

    φ2 = math.asin(math.sin(φ1) * math.cos(δ) + math.cos(φ1) * math.sin(δ) * math.cos(θ))
    λ2 = λ1 + math.atan2(math.sin(θ) * math.sin(δ) * math.cos(φ1), math.cos(δ) - math.sin(φ1) * math.sin(φ2))

    return math.degrees(φ2), (math.degrees(λ2) + 540) % 360 - 180  # normalise to ‑180…180°


# ────────────────────────────────────────────────────────────────────────────────
# Core predictor class
# ────────────────────────────────────────────────────────────────────────────────

def _sanitize_positions(positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sanitize position data by removing invalid entries and ensuring proper types."""
    sanitized = []
    for pos in positions:
        try:
            # Ensure required fields exist and are valid
            if not all(k in pos for k in ['latitude', 'longitude', 'timestamp']):
                logger.warning("Position missing required fields: %s", pos)
                continue
                
            # Convert timestamp to datetime if it's a string
            if isinstance(pos['timestamp'], str):
                pos['timestamp'] = pd.to_datetime(pos['timestamp'])
                
            # Ensure coordinates are valid numbers
            lat = float(pos['latitude'])
            lon = float(pos['longitude'])
            
            # Validate coordinate ranges
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                logger.warning("Invalid coordinates: lat=%f, lon=%f", lat, lon)
                continue
                
            # Check for NaN or infinite values
            if np.isnan(lat) or np.isnan(lon) or np.isinf(lat) or np.isinf(lon):
                logger.warning("NaN or infinite coordinates: lat=%f, lon=%f", lat, lon)
                continue
                
            sanitized.append(pos)
        except (ValueError, TypeError) as e:
            logger.warning("Error sanitizing position: %s", e)
            continue
            
    return sanitized

@dataclass
class SubmarinePredictor:
    """Predict future positions for a *single* submarine.

    A single instance can be reused for many subs — the internal weights update
    with reinforcement‑style feedback whenever *update_weights* is called.
    """

    learning_rate: float = 0.1
    prediction_horizon_days: int = 30
    historical_weight: float = 0.7
    current_weight: float = 0.3

    # Monte‑Carlo defaults
    mc_simulations: int = 1_000
    mc_sigma_km: float = 15  # lateral scatter per step

    rng: random.Random = field(default_factory=random.Random, repr=False, init=False)

    # ────────────────────────────────────────────────────────────────────────
    # Public API
    # ────────────────────────────────────────────────────────────────────────

    def predict_next_position(self, submarine: Submarine) -> Position | None:
        """Fast, single‑shot prediction used by the UI (central path)."""
        history = _sanitize_positions(submarine.get_all_positions())
        if not history:
            logger.warning("No positions for %s", getattr(submarine, "sub_id", "<unknown>"))
            return None

        latest = max(history, key=lambda p: p["timestamp"])
        patterns = self._movement_patterns(history)

        # Est. speed (knots) → km/day (~ *24* * 1.852)
        speed_kn = patterns.get("avg_speed", 6)
        dist_days_km = speed_kn * 1.852 * self.prediction_horizon_days * self.current_weight

        # Choose bearing: keep previous heading if available else random
        bearing = patterns.get("avg_bearing", self.rng.uniform(0, 360))
        lat, lon = _destination_point(latest["latitude"], latest["longitude"], bearing, dist_days_km)

        # Snap towards frequent historical hot‑spots
        if patterns["frequent_locations"]:
            hot_lat, hot_lon = min(
                patterns["frequent_locations"],
                key=lambda pt: _haversine_km(lat, lon, *pt),
            )
            lat = self.historical_weight * hot_lat + self.current_weight * lat
            lon = self.historical_weight * hot_lon + self.current_weight * lon

        return Position(
            latitude=lat,
            longitude=lon,
            timestamp=latest["timestamp"] + timedelta(days=self.prediction_horizon_days),
            depth=None,
            speed=None,
            sub_id=getattr(submarine, "sub_id", "unknown"),
            is_historical=False,
            source="predictor|central",
        )

    # ‑‑ Monte‑Carlo ‑‑

    def run_monte_carlo_predictions(self, submarine: Submarine | Iterable[Position], n_simulations: int | None = None) -> List[Dict[str, Any]]:
        """Generate a point‑cloud of possible future positions for probabilistic mapping."""
        try:
            history = _sanitize_positions(list(submarine) if not hasattr(submarine, "get_all_positions") else submarine.get_all_positions())
            if not history:
                logger.warning("No valid positions for Monte Carlo simulation")
                return []

            latest = max(history, key=lambda p: p["timestamp"])
            patterns = self._movement_patterns(history)

            # Validate simulation count
            sim_count = n_simulations or self.mc_simulations
            if sim_count <= 0:
                logger.warning("Invalid simulation count: %d", sim_count)
                return []

            predictions: list[dict[str, Any]] = []

            for _ in range(sim_count):
                try:
                    # Sample params with validation
                    speed_kn = max(3, self.rng.normalvariate(patterns.get("avg_speed", 6), 1))
                    bearing = self.rng.normalvariate(patterns.get("avg_bearing", self.rng.uniform(0, 360)), 20)
                    horizon = self.rng.randint(int(self.prediction_horizon_days * 0.5), int(self.prediction_horizon_days * 1.5))

                    # Calculate distance and new position
                    dist_km = speed_kn * 1.852 * horizon
                    lat, lon = _destination_point(latest["latitude"], latest["longitude"], bearing, dist_km)

                    # Validate new position
                    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                        logger.warning("Invalid predicted position: lat=%f, lon=%f", lat, lon)
                        continue

                    # Add lateral scatter with validation
                    lat_scatter = self.rng.normalvariate(0, self.mc_sigma_km / 110)
                    lon_scatter = self.rng.normalvariate(0, self.mc_sigma_km / (111 * math.cos(math.radians(lat))))
                    
                    lat += lat_scatter
                    lon += lon_scatter

                    # Final position validation
                    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                        logger.warning("Invalid scattered position: lat=%f, lon=%f", lat, lon)
                        continue

                    predictions.append({
                        "latitude": lat,
                        "longitude": lon,
                        "timestamp": latest["timestamp"] + timedelta(days=horizon),
                        "step": horizon,  # days ahead
                        "sub_id": getattr(submarine, "sub_id", "unknown"),
                    })
                except Exception as e:
                    logger.warning("Error in Monte Carlo simulation: %s", e)
                    continue

            return predictions
        except Exception as e:
            logger.error("Fatal error in Monte Carlo predictions: %s", e)
            return []

    # ‑‑ Reinforcement update ‑‑

    def update_weights(self, actual: Position, predicted: Position | None) -> None:
        if predicted is None:
            return
        error_km = _haversine_km(actual["latitude"], actual["longitude"], predicted["latitude"], predicted["longitude"])
        factor = 1 + self.learning_rate if error_km < 100 else 1 - self.learning_rate
        self.historical_weight *= factor
        self.current_weight *= 2 - factor
        # normalise
        s = self.historical_weight + self.current_weight
        self.historical_weight /= s
        self.current_weight /= s
        logger.info("Weights updated → hist=%.2f  curr=%.2f", self.historical_weight, self.current_weight)

    # ────────────────────────────────────────────────────────────────────
    # Internals
    # ────────────────────────────────────────────────────────────────────

    def _movement_patterns(self, positions: list[Position]) -> Dict[str, Any]:
        """Extract naïve statistics from *positions* to guide forecasts."""
        try:
            if not positions:
                logger.warning("No positions provided for movement pattern analysis")
                return {}

            df = pd.DataFrame(positions)
            if len(df) < 1:
                logger.warning("Empty DataFrame after conversion")
                return {}

            df.sort_values("timestamp", inplace=True)

            # basic kinematics (assuming sorted timestamps)
            if len(df) >= 2:
                try:
                    # avoid divide‑by‑zero on identical times
                    deltas = (
                        df[["latitude", "longitude", "timestamp"]]
                        .assign(ts=lambda d: d["timestamp"].astype("int64") / 1e9)  # seconds
                        .diff()
                        .dropna()
                    )
                    
                    if len(deltas) < 1:
                        logger.warning("No valid time deltas found")
                        return {"avg_speed": 6, "avg_bearing": random.uniform(0, 360), "frequent_locations": []}

                    dist_km = _haversine_km(
                        df.iloc[:-1]["latitude"].values,
                        df.iloc[:-1]["longitude"].values,
                        df.iloc[1:]["latitude"].values,
                        df.iloc[1:]["longitude"].values
                    )
                    
                    hours = deltas["ts"].values / 3600
                    if np.any(hours == 0):
                        logger.warning("Zero time delta found, using default speed")
                        speed_knots = np.array([6.0])
                    else:
                        speed_knots = dist_km / hours / 1.852
                    
                    avg_speed = float(np.nanmean(speed_knots)) if speed_knots.size else 6
                    
                    # compute bearings
                    bearings = np.degrees(np.arctan2(deltas["longitude"], deltas["latitude"])) % 360
                    avg_bearing = float(np.nanmean(bearings)) if bearings.size else random.uniform(0, 360)
                except Exception as e:
                    logger.warning("Error calculating kinematics: %s", e)
                    avg_speed, avg_bearing = 6, random.uniform(0, 360)
            else:
                avg_speed, avg_bearing = 6, random.uniform(0, 360)

            # hot spots (rounded to 2 dp ≈ 1 km)
            try:
                rounded = df[["latitude", "longitude"]].round(2)
                frequent = (
                    rounded.value_counts()
                    .nlargest(3)
                    .index.to_list()
                )
            except Exception as e:
                logger.warning("Error calculating hotspots: %s", e)
                frequent = []

            return {
                "avg_speed": avg_speed,
                "avg_bearing": avg_bearing,
                "frequent_locations": frequent,
            }
        except Exception as e:
            logger.error("Fatal error in movement pattern analysis: %s", e)
            return {"avg_speed": 6, "avg_bearing": random.uniform(0, 360), "frequent_locations": []}


# ────────────────────────────────────────────────────────────────────────────────
# Utility – convert any raw CSV (timestamp string) into *Position* records
# ────────────────────────────────────────────────────────────────────────────────

def load_detections_csv(csv_path: str, *, sub_id_col: str = "sub_id") -> list[Position]:
    df = pd.read_csv(csv_path)
    if "timestamp" not in df.columns:
        raise ValueError("CSV missing 'timestamp' column")

    records: list[Position] = []
    for _, row in df.iterrows():
        try:
            records.append(
                Position(
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    timestamp=pd.to_datetime(row["timestamp"]),
                    depth=float(row.get("depth", float("nan")) if "depth" in row else float("nan")),
                    speed=float(row.get("speed", float("nan")) if "speed" in row else float("nan")),
                    sub_id=str(row[sub_id_col]),
                    is_historical=True,
                    source="csv",
                )
            )
        except Exception as exc:
            logger.debug("Skipping bad row: %s", exc, exc_info=False)
    return records


# ────────────────────────────────────────────────────────────────────────────────
# Singleton (import‑time safe)
# ────────────────────────────────────────────────────────────────────────────────
PREDICTOR = SubmarinePredictor()
