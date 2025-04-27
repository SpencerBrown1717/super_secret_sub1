"""
Helpers for checking whether a point lies in China's "close" coastal waters.

⚠️  CHINA_COASTAL_BOUNDARY is (lon, lat) because Leaflet wants that.
    All public helpers still accept the friendlier (lat, lon) signature.
"""

from typing import List, Tuple
import math

# (lon, lat)
CHINA_COASTAL_BOUNDARY: List[Tuple[float, float]] = [
    (120.0, 39.0), (122.5, 38.8), (124.0, 37.5), (125.0, 35.0),
    (123.0, 32.0), (122.0, 30.0), (122.0, 28.0), (121.0, 25.0),
    (119.0, 23.0), (117.0, 21.0), (110.0, 20.0), (108.0, 21.0),
    (107.0, 23.0), (108.0, 25.0), (110.0, 28.0), (115.0, 32.0),
    (120.0, 39.0),  # close polygon
]

EPS     = 1e-9          # numerical wiggle room
BUFFER  = 0.5           # deg – points this close to the boundary count as "inside"


# ──────────────────────────────────────────────────────────────────────────────
#  Geometry helpers
# ──────────────────────────────────────────────────────────────────────────────
def _point_segment_distance(px: float, py: float,
                            x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Shortest great-circle *approximation* distance (deg) from (px, py) to
    the segment [(x1,y1) – (x2,y2)].  Euclidean is fine at this granularity.
    """
    vx, vy = x2 - x1, y2 - y1
    wx, wy = px - x1, py - y1
    c1     = vx * wx + vy * wy
    if c1 <= 0:
        return math.hypot(wx, wy)
    c2 = vx * vx + vy * vy
    if c2 <= c1:
        return math.hypot(px - x2, py - y2)
    b   = c1 / c2
    bx  = x1 + b * vx
    by  = y1 + b * vy
    return math.hypot(px - bx, py - by)


def _point_in_polygon(px: float, py: float,
                      polygon: List[Tuple[float, float]]) -> bool:
    """Even–odd rule (ray-casting) with the standard vertex-handling guard."""
    inside = False
    n      = len(polygon)
    j      = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if (yi > py) != (yj > py):                    # edge straddles scan-line
            xinters = (xj - xi) * (py - yi) / (yj - yi) + xi
            if px < xinters - EPS:                   # strictly to the right
                inside = not inside
        j = i
    return inside


# ──────────────────────────────────────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────────────────────────────────────
def is_in_china_coastal(lat: float, lon: float) -> bool:
    """
    True if (lat, lon) lies inside – or within `BUFFER` degrees of – the
    polygon approximating China's close coastal waters.
    """
    x, y = lon, lat

    # 1.  "On or near" the boundary?
    for (x1, y1), (x2, y2) in zip(CHINA_COASTAL_BOUNDARY,
                                  CHINA_COASTAL_BOUNDARY[1:]):
        if _point_segment_distance(x, y, x1, y1, x2, y2) <= BUFFER:
            return True

    # 2.  Strict interior?
    return _point_in_polygon(x, y, CHINA_COASTAL_BOUNDARY)


def clamp_to_china_coastal(lat: float, lon: float) -> Tuple[float, float]:
    """
    Identity for now – kept as a hook for snapping to the nearest boundary.
    """
    return lat, lon 