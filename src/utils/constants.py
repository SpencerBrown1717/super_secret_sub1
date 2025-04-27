"""
Constants used throughout the submarine tracking system.
"""

# Naval base locations (lat, lon)
NAVAL_BASES = {
    "Yulin": (18.2253, 109.5292),
    "Paracel": (16.5000, 112.0000),
    "Jianggezhuang": (36.1108, 120.5758),
    "Xiaopingdao": (38.8179, 121.4944),
    "Lushunkou": (38.8453, 121.2781),
    "Huludao": (40.7153, 121.0103)
}

# Detection radius around naval bases (in degrees)
BASE_DETECTION_RADIUS = 0.01  # Approximately 1km at the equator 