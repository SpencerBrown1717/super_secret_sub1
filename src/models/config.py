"""Configuration constants for the submarine tracking system."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

# ────────────────────────────────────────────────────────────────────
#  Data paths and loading
# ────────────────────────────────────────────────────────────────────
BASES_CSV_PATH = "data/input/submarine_bases.csv"
LOCATION_CSV_PATH = "data/input/submarine_location.csv"

# Load submarine bases data (global, so only loaded once)
try:
    _bases_df = pd.read_csv(BASES_CSV_PATH)
    NAVAL_BASES = {row['id']: (row['latitude'], row['longitude']) for _, row in _bases_df.iterrows()}
except Exception:
    NAVAL_BASES = {}

# ────────────────────────────────────────────────────────────────────
#  Submarine Configuration
# ────────────────────────────────────────────────────────────────────
# List of Jin-class submarines
JIN_SUBMARINES = ["Jin1", "Jin2", "Jin3", "Jin4", "Jin5", "Jin6"]

# Map submarine IDs to their home base ID (Yulin for Jin1-4)
SUB_HOME_BASE = {
    "Jin1": 1,
    "Jin2": 1,
    "Jin3": 1,
    "Jin4": 1,
    # Add more mappings as needed
}

# Speed limits for submarines (in knots)
MIN_SPEED_KNOTS = 5.0  # Minimum patrol speed
MAX_SPEED_KNOTS = 10.0  # Maximum patrol speed
KNOTS_TO_KMH = 1.852  # Conversion factor from knots to km/h

# ────────────────────────────────────────────────────────────────────
#  Geographic Constants
# ────────────────────────────────────────────────────────────────────
# Earth's radius in kilometers (for distance/bearing calculations)
EARTH_RADIUS_KM = 6371.0

# Bathymetry model parameters
BATHY_LON_MIN = -180.0
BATHY_LON_MAX = 180.0
BATHY_LAT_MIN = -90.0
BATHY_LAT_MAX = 90.0
BATHY_CELL = 0.01  # Grid cell size in degrees
BATHY_NX = int((BATHY_LON_MAX - BATHY_LON_MIN) / BATHY_CELL)
BATHY_NY = int((BATHY_LAT_MAX - BATHY_LAT_MIN) / BATHY_CELL)

# Initialize bathymetry mask
BATHY_MASK = np.ones((BATHY_NY, BATHY_NX), dtype=bool)

# Add land masses (1 = water, 0 = land)
def _add_land_rectangle(lat_min, lat_max, lon_min, lon_max):
    i_min = int((lon_min - BATHY_LON_MIN) / BATHY_CELL)
    i_max = int((lon_max - BATHY_LON_MIN) / BATHY_CELL)
    j_min = int((lat_min - BATHY_LAT_MIN) / BATHY_CELL)
    j_max = int((lat_max - BATHY_LAT_MIN) / BATHY_CELL)
    BATHY_MASK[j_min:j_max, i_min:i_max] = False

# North America
_add_land_rectangle(15, 85, -170, -50)

# South America
_add_land_rectangle(-60, 15, -85, -35)

# Europe/Asia/Africa
_add_land_rectangle(0, 75, -10, 180)
_add_land_rectangle(-35, 0, 10, 50)

# Coastal buffer for land/water detection (≈25 km)
COAST_BUFFER = 0.22

# Naval base detection radius (in degrees, ~2km at equator)
BASE_DETECTION_RADIUS = 0.02

# ────────────────────────────────────────────────────────────────────
#  Monte Carlo Simulation Parameters
# ────────────────────────────────────────────────────────────────────
DEFAULT_NUM_SIMULATIONS = 1000
DEFAULT_HEADING_SIGMA = 5.0  # degrees per step (Gaussian)
DEFAULT_SPEED_SIGMA = 0.05  # 5% per step
DEFAULT_HOURS_AHEAD = 24
DEFAULT_STEP_HOURS = 1 