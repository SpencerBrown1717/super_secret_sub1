import math
import pydeck as pdk
from pydeck.types import String
from typing import Dict, List, Any, Optional

DEFAULT_COLORS = [
    [255,   0,   0],   # Red
    [  0, 255,   0],   # Green
    [  0,   0, 255],   # Blue
    [255, 255,   0],   # Yellow
    [255,   0, 255],   # Magenta
    [  0, 255, 255],   # Cyan
]

def _safe_path(fdict: Dict[str, Any], key: str) -> List[List[float]]:
    """Return a list-of-lists if present & well-formed, else []"""
    path = fdict.get(key, [])
    # deck.gl expects list of [lon, lat]; make sure we have a list of lists
    if isinstance(path, list) and len(path) and isinstance(path[0], (list, tuple)):
        return path
    return []

def create_map(forecasts: Dict[str, Dict[str, Any]], output_path: Optional[str] = None, /, **_) -> Optional[pdk.Deck]:
    """
    Build a deck.gl map of submarine forecasts.
    *Silently* skips any submarine whose forecast dict is empty / malformed.
    
    Args:
        forecasts: Dictionary mapping submarine IDs to their forecast data
        output_path: Optional path to save the HTML output
        
    Returns:
        pydeck.Deck object if successful, None if no valid forecasts
    """
    if not forecasts:
        print("[viz] WARNING – no forecasts supplied, nothing to draw.")
        return None

    sub_ids = sorted(forecasts.keys())
    color_map = {s: DEFAULT_COLORS[i % len(DEFAULT_COLORS)] for i, s in enumerate(sub_ids)}

    polygon_layers, path_layers = [], []
    scatter_pts, text_labels = [], []
    all_lats, all_lons = [], []

    for sid in sub_ids:
        f = forecasts.get(sid) or {}
        central = _safe_path(f, "central_path")
        cone = _safe_path(f, "cone_polygon")

        # skip if we truly have no positional info
        if not central:
            print(f"[viz] skipping {sid}: no central path")
            continue

        color = color_map[sid]
        lon0, lat0 = central[0]
        all_lons.append(lon0)
        all_lats.append(lat0)

        # --- path layer (dashed) -------------------------------------------------
        if len(central) > 1:
            path_layers.append(
                pdk.Layer(
                    "PathLayer",
                    [{"path": central, "name": sid, "color": color}],
                    get_path="path",
                    get_color="color",
                    width_units="pixels",
                    width_min_pixels=2,
                    width_max_pixels=6,
                    width_scale=1,
                )
            )

        # --- uncertainty polygon -------------------------------------------------
        if len(cone) >= 3:
            polygon_layers.append(
                pdk.Layer(
                    "PolygonLayer",
                    [{"coordinates": cone, "name": sid}],
                    get_polygon="coordinates",
                    get_fill_color=color,
                    get_line_color=color,
                    opacity=0.25,
                    stroked=True,
                    pickable=True,
                )
            )

        # --- current position icon + label --------------------------------------
        scatter_pts.append(
            {
                "position": [lon0, lat0],
                "color": color,
                "radius": 8000,
                "name": sid
            }
        )
        text_labels.append(
            {
                "position": [lon0, lat0],
                "text": sid,
                "color": color
            }
        )

    # Calculate view state if we have points
    if all_lats and all_lons:
        view_state = pdk.ViewState(
            latitude=sum(all_lats) / len(all_lats),
            longitude=sum(all_lons) / len(all_lons),
            zoom=5,
            pitch=0,
            bearing=0
        )
    else:
        # Default to South China Sea if no data
        view_state = pdk.ViewState(
            latitude=18.2133,
            longitude=109.6925,
            zoom=5,
            pitch=0,
            bearing=0
        )

    # Create scatter layer for current positions
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        scatter_pts,
        get_position="position",
        get_fill_color="color",
        get_radius="radius",
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True,
        radius_scale=1,
        radius_min_pixels=3,
        radius_max_pixels=100,
    )

    # Create text layer for labels
    text_layer = pdk.Layer(
        "TextLayer",
        text_labels,
        get_position="position",
        get_text="text",
        get_color="color",
        get_size=16,
        get_angle=0,
        get_text_anchor="middle",
        get_alignment_baseline="center",
    )

    # Combine all layers
    layers = [scatter_layer, text_layer] + path_layers + polygon_layers

    # Create the deck
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/dark-v10",
        tooltip={
            "html": "<b>{name}</b>",
            "style": {
                "backgroundColor": "steelblue",
                "color": "white"
            }
        }
    )

    # Save to HTML if path provided
    if output_path:
        deck.to_html(output_path)

    return deck 