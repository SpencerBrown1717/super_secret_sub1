"""Jin-class submarine tracking and visualization system."""
import folium
import folium.plugins as plugins
import numpy as np
import pandas as pd
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from shapely.geometry import MultiPoint
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Submarine:
    """Represents a Jin-class submarine with position tracking."""
    
    def __init__(self, sub_id: str):
        self.sub_id = sub_id
        self.positions = []
        self.historical_sightings = []
        
    def add_position(self, latitude: float, longitude: float, timestamp: str, 
                    depth: float = None, speed: float = None) -> None:
        """Add a position record for this submarine."""
        if latitude is None or longitude is None:
            logger.warning(f"Invalid position for {self.sub_id}: lat={latitude}, lon={longitude}")
            return
            
        try:
            position = {
                'sub_id': self.sub_id,
                'latitude': float(latitude),
                'longitude': float(longitude),
                'timestamp': timestamp,
                'depth': float(depth) if depth is not None else None,
                'speed': float(speed) if speed is not None else None
            }
            self.positions.append(position)
            logger.debug(f"Added position for {self.sub_id}: {position}")
        except (ValueError, TypeError) as e:
            logger.warning(f"Error adding position for {self.sub_id}: {e}")
    
    def get_latest_position(self) -> Dict[str, Any]:
        """Get the most recent position for this submarine."""
        if not self.positions:
            return None
        return sorted(self.positions, key=lambda p: p.get('timestamp', ''), reverse=True)[0]
    
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """Get all positions for this submarine."""
        return self.positions
        
    def load_historical_sightings(self, sightings_path: str) -> None:
        """Load historical sightings for this submarine."""
        # In a real implementation, this would load submarine-specific 
        # historical data from a file or database
        logger.info(f"Loading historical sightings for {self.sub_id}")
        
    def get_location(self) -> Tuple[float, float]:
        """Get the latest latitude and longitude."""
        pos = self.get_latest_position()
        if pos:
            return (pos['latitude'], pos['longitude'])
        return (None, None)
        
    def __repr__(self) -> str:
        """String representation of the submarine."""
        pos = self.get_latest_position()
        if pos:
            return f"Submarine(id={self.sub_id}, lat={pos['latitude']:.2f}, lon={pos['longitude']:.2f})"
        return f"Submarine(id={self.sub_id}, no position)"


class Fleet:
    """Represents a fleet of Jin-class submarines."""
    
    def __init__(self):
        self.submarines = {}  # Dictionary of submarine objects by ID
        
    def add_submarine(self, submarine: Submarine) -> None:
        """Add a submarine to the fleet."""
        self.submarines[submarine.sub_id] = submarine
        logger.info(f"Added submarine {submarine.sub_id} to fleet")
        
    def get_submarine(self, sub_id: str) -> Submarine:
        """Get a submarine by ID."""
        return self.submarines.get(sub_id)
        
    def update_from_records(self, records: List[Dict[str, Any]]) -> None:
        """Update fleet from a list of position records."""
        # Group records by sub_id
        grouped_records = {}
        for record in records:
            sub_id = str(record.get('sub_id'))
            if not sub_id:
                logger.warning(f"Record missing sub_id, skipping: {record}")
                continue
                
            # Convert date to timestamp if needed
            timestamp = record.get('timestamp', record.get('date'))
            if timestamp:
                # Convert pandas Timestamp to string if needed
                if hasattr(timestamp, 'strftime'):
                    timestamp = timestamp.strftime('%Y-%m-%d %H:%M')
                elif isinstance(timestamp, str) and ' ' not in timestamp:
                    timestamp = f"{timestamp} 00:00"
            record['timestamp'] = timestamp
                
            if sub_id not in grouped_records:
                grouped_records[sub_id] = []
            grouped_records[sub_id].append(record)
            
        # Update or create submarines
        for sub_id, sub_records in grouped_records.items():
            if sub_id in self.submarines:
                # Update existing submarine
                sub = self.submarines[sub_id]
                for record in sub_records:
                    sub.add_position(
                        latitude=record.get('latitude'),
                        longitude=record.get('longitude'),
                        timestamp=record.get('timestamp'),
                        depth=record.get('depth'),
                        speed=record.get('speed')
                    )
            else:
                # Create new submarine
                sub = Submarine(sub_id=sub_id)
                for record in sub_records:
                    sub.add_position(
                        latitude=record.get('latitude'),
                        longitude=record.get('longitude'),
                        timestamp=record.get('timestamp'),
                        depth=record.get('depth'),
                        speed=record.get('speed')
                    )
                self.add_submarine(sub)
                
        logger.info(f"Updated fleet with {len(records)} records")

    def load_historical_sightings(self, sightings_path: str) -> None:
        """Load historical sightings for all submarines in the fleet."""
        try:
            if not os.path.exists(sightings_path):
                logger.warning(f"Historical sightings file not found: {sightings_path}")
                return
                
            # Load sightings for each submarine
            for sub in self.submarines.values():
                sub.load_historical_sightings(sightings_path)
                
            logger.info(f"Loaded historical sightings for {len(self.submarines)} submarines")
        except Exception as e:
            logger.error(f"Error loading historical sightings: {e}")
        
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """Get all submarine positions as a flat list."""
        positions = []
        for sub in self.submarines.values():
            positions.extend(sub.get_all_positions())
        return positions
        
    def to_dataframe(self) -> 'pd.DataFrame':
        """Convert all positions to a pandas DataFrame."""
        positions = self.get_all_positions()
        if positions:
            return pd.DataFrame(positions)
        return pd.DataFrame()
        
    def __repr__(self) -> str:
        """String representation of the fleet."""
        return f"Fleet(submarines={len(self.submarines)})"


# Create a singleton fleet instance
FLEET = Fleet()


class Predictor:
    """Predicts submarine movement using Monte Carlo simulations."""
    
    def run_monte_carlo_predictions(self, sub: Submarine, n_simulations: int = 500) -> List[Dict[str, Any]]:
        """Run Monte Carlo predictions for submarine movement."""
        import random
        
        # Placeholder implementation - in a real system, this would use actual
        # prediction models with physics, ocean currents, etc.
        results = []
        base_lat, base_lon = sub.get_location()
        
        if base_lat is None or base_lon is None:
            logger.warning(f"Cannot run predictions for {sub.sub_id} - no position data")
            return []
        
        # Generate simulations for different timesteps
        for step in range(1, 7):  # Forecast 6 steps ahead
            for _ in range(n_simulations // 6):
                # More variation as forecast extends further
                lat_variation = random.normalvariate(0, 0.05 * step)
                lon_variation = random.normalvariate(0, 0.05 * step)
                
                results.append({
                    "latitude": base_lat + lat_variation,
                    "longitude": base_lon + lon_variation,
                    "step": step
                })
        
        return results


# Initialize the predictor
PREDICTOR = Predictor()


# Helper functions
def _safe_float(value) -> float:
    """Convert value to float safely, returning NaN for invalid values."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return float('nan')


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate haversine distance between two points in kilometers."""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371.0  # Earth radius in kilometers
    
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance


def _add_mc_heat_and_confidence(layer: folium.FeatureGroup,
                                sub: Submarine,
                                colour: str) -> None:
    """
    Run a Monte-Carlo forecast and draw:
      • a heat-map of all simulated points
      • nested convex-hull polygons – one per forecast step – to mimic the
        "hurricane-style" rings shown in the reference image
      • 50 % / 90 % confidence circles + centre marker (optional)
    """
    # ── 1.  Run the forecast  ──────────────────────────────────────────────
    try:
        sims: list[dict[str, Any]] = PREDICTOR.run_monte_carlo_predictions(
            sub, n_simulations=500
        )
    except TypeError:
        sims = PREDICTOR.run_monte_carlo_predictions(sub, 500)

    if not sims:
        return

    # ── 2.  Organise by timestep  ──────────────────────────────────────────
    # Expect a key like "step" or "timestep" (hours ahead).  If it isn't
    # present we fall back to treating the whole set as a single cloud.
    step_key = "step" if "step" in sims[0] else "timestep" if "timestep" in sims[0] else None
    if step_key:
        steps: dict[int, list[Tuple[float, float]]] = {}
        for p in sims:
            lat, lon = _safe_float(p.get("latitude")), _safe_float(p.get("longitude"))
            if not np.isfinite(lat) or not np.isfinite(lon):
                continue
            steps.setdefault(int(p[step_key]), []).append((lat, lon))
    else:
        # Single bucket – will draw one hull
        steps = {0: [( _safe_float(p["latitude"]), _safe_float(p["longitude"]) )
                     for p in sims
                     if np.isfinite(_safe_float(p["latitude"])) and
                        np.isfinite(_safe_float(p["longitude"]))]}

    if not any(steps.values()):
        return

    # ── 3.  Heat-map of *all* points  (nice background)  ───────────────────
    all_pts = [pt for pts in steps.values() for pt in pts]
    plugins.HeatMap(all_pts, radius=18, blur=12,
                    name=f"{sub.sub_id} – MC heat").add_to(layer)

    # ── 4.  Nested convex-hull polygons  ───────────────────────────────────
    # Draw from *earliest* to *latest* so later steps lie on top & appear darker
    max_step = max(steps)
    for s in sorted(steps):
        pts = steps[s]
        if len(pts) < 3:          # need ≥3 points for a hull
            continue
        hull = MultiPoint([(lon, lat) for lat, lon in pts]).convex_hull
        if hull.geom_type != "Polygon":
            continue
        latlon = [(lat, lon) for lon, lat in hull.exterior.coords]
        # Fade opacity: later (larger-area) hulls are lighter
        opacity = 0.9 * (1.0 - s / (max_step + 1))
        folium.PolyLine(
            latlon,
            color=colour,
            weight=2,
            opacity=opacity,
            dash_array="3,6"  # short dash for clarity
        ).add_to(layer)

    # ── 5.  Optional: centre marker & 50/90 % circles  ─────────────────────
    centre_lat = np.mean([p[0] for p in all_pts])
    centre_lon = np.mean([p[1] for p in all_pts])
    dists = np.array([
        _haversine_km(centre_lat, centre_lon, lat, lon) for lat, lon in all_pts
    ])
    r50, r90 = np.percentile(dists, [50, 90])

    for r_km, opac in [(r90, 0.20), (r50, 0.30)]:
        folium.Circle(
            location=[centre_lat, centre_lon],
            radius=int(r_km * 1_000),
            color=colour,
            weight=2,
            fill=True,
            fill_opacity=opac,
            opacity=0.8
        ).add_to(layer)

    folium.CircleMarker(
        location=[centre_lat, centre_lon],
        radius=5,
        color=colour,
        fill=True,
        fill_color=colour,
        fill_opacity=0.9,
        tooltip=f"{sub.sub_id} forecast centre"
    ).add_to(layer)


def load_data(input_path: Path) -> pd.DataFrame:
    """Load and preprocess submarine tracking data from CSV."""
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} records from {input_path}")
        
        # Basic validation and cleanup
        required_cols = ['sub_id', 'latitude', 'longitude']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' missing from input data")
                
        # Convert latitude/longitude to float
        for col in ['latitude', 'longitude']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        # Drop rows with missing coordinates
        invalid_mask = df['latitude'].isna() | df['longitude'].isna()
        if invalid_mask.any():
            logger.warning(f"Dropping {invalid_mask.sum()} rows with invalid coordinates")
            df = df[~invalid_mask]
            
        return df
    except Exception as e:
        logger.error(f"Error loading data from {input_path}: {e}")
        raise


def load_submarines_from_csv(input_path: Path) -> List[Submarine]:
    """Load submarine objects directly from CSV data."""
    df = pd.read_csv(input_path)
    
    # Group by submarine ID
    submarines = []
    for sub_id, group in df.groupby('sub_id'):
        sub = Submarine(sub_id=str(sub_id))
        for _, row in group.iterrows():
            sub.add_position(
                latitude=row.get('latitude'),
                longitude=row.get('longitude'),
                timestamp=row.get('timestamp', row.get('date')),
                depth=row.get('depth'),
                speed=row.get('speed')
            )
        submarines.append(sub)
        
    logger.info(f"Loaded {len(submarines)} submarines from {input_path}")
    return submarines


def create_leaflet_map(df: pd.DataFrame, output_path: Path, confidence_rings: int = 3, 
                      submarines: List[Submarine] = None) -> None:
    """Create an interactive Leaflet map with submarine positions and forecasts."""
    # Initialize map centered on mean coordinates
    center_lat = df['latitude'].mean()
    center_lon = df['longitude'].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6, 
                  tiles='CartoDB positron')
    
    # Add base layers
    folium.TileLayer('CartoDB dark_matter', name='Dark Map').add_to(m)
    folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(m)
    
    # Add submarine markers and tracks
    sub_layer = folium.FeatureGroup(name="Submarine Positions")
    
    # Use submarines list if provided, otherwise get from FLEET
    if submarines is None:
        submarines = list(FLEET.submarines.values())
        
    # Define colors for each submarine
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'darkblue', 'darkgreen']
    
    for i, sub in enumerate(submarines):
        color = colors[i % len(colors)]
        latest = sub.get_latest_position()
        
        if latest:
            # Add marker for latest position
            folium.Marker(
                location=[latest['latitude'], latest['longitude']],
                tooltip=f"Submarine {sub.sub_id}",
                icon=folium.Icon(color=color, icon='submarine', prefix='fa')
            ).add_to(sub_layer)
            
            # Add line for submarine track
            positions = sub.get_all_positions()
            if len(positions) > 1:
                coordinates = [(p['latitude'], p['longitude']) for p in positions]
                folium.PolyLine(
                    coordinates,
                    color=color,
                    weight=3,
                    opacity=0.8,
                    tooltip=f"Track for {sub.sub_id}"
                ).add_to(sub_layer)
                
            # Add forecast visualization if confidence_rings > 0
            if confidence_rings > 0:
                forecast_layer = folium.FeatureGroup(name=f"{sub.sub_id} Forecast")
                _add_mc_heat_and_confidence(forecast_layer, sub, color)
                forecast_layer.add_to(m)
    
    sub_layer.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save the map
    m.save(str(output_path))
    logger.info(f"Map saved to {output_path}")