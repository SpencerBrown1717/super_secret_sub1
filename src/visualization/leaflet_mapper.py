import folium
from folium import plugins
import pandas as pd
from pathlib import Path
import numpy as np
from shapely.geometry import MultiPoint
from typing import Any, Dict, List, Tuple
from src.models.submarine import Submarine
from src.models.prediction import PREDICTOR, _haversine_km
from src.models.config import _safe_float

def create_leaflet_map(df: pd.DataFrame, output_path: Path, confidence_rings: int = 3, submarines: List[Submarine] = None) -> None:
    """Create an interactive map showing submarine positions and predictions."""
    # Initialize the map centered on the South China Sea
    m = folium.Map(location=[18.0, 115.0], zoom_start=5)
    
    # Create layer groups
    actual_layer = folium.FeatureGroup(name='Actual Tracks')
    monte_carlo_layer = folium.FeatureGroup(name='Monte Carlo Probability')
    
    # Group by submarine ID
    for sub_id, group in df.groupby('sub_id'):
        # Sort by timestamp
        group = group.sort_values('timestamp')
        
        # Create a path for this submarine
        path = []
        for _, row in group.iterrows():
            point = [row['latitude'], row['longitude']]
            path.append(point)
            folium.CircleMarker(
                location=point,
                radius=5,
                color='green',
                fill=True,
                fill_color='green',
                popup=f"Submarine: {sub_id}<br>Date: {str(row['timestamp'])}",
                tooltip=f"Submarine {sub_id}"
            ).add_to(actual_layer)
        
        # Add path line
        if len(path) > 1:
            folium.PolyLine(
                locations=path,
                color='green',
                weight=2,
                opacity=0.5
            ).add_to(actual_layer)
        
        # Add Monte Carlo predictions if submarine object is available
        if submarines:
            sub = next((s for s in submarines if s.sub_id == str(sub_id)), None)
            if sub:
                _add_mc_heat_and_confidence(monte_carlo_layer, sub, 'blue')
    
    # Add layers and layer control
    m.add_child(actual_layer)
    m.add_child(monte_carlo_layer)
    m.add_child(folium.LayerControl())
    
    # Save the map
    m.save(str(output_path))

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
