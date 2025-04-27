"""
Main script to orchestrate data ingestion, forecasting, and visualization for Jin-class submarine tracker.
"""
import os
import argparse
from datetime import datetime
import pandas as pd
import warnings
import importlib
import random
import logging

# Configure logging
log = logging.getLogger(__name__)

# Filter out Pydantic AliasGenerator warning
warnings.filterwarnings(
    "ignore",
    message="cannot import name 'AliasGenerator' from 'pydantic'",
)

def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Jin-class Submarine Tracker")
    parser.add_argument("-i", "--input", type=str, default="data/input/submarine_tracking.csv",
                        help="Path to input CSV file or API URL for submarine positions")
    parser.add_argument("-o", "--output", type=str, default="data/output/jin_forecast_map.html",
                        help="Path to save the output map HTML")
    parser.add_argument("--hours_ahead", type=int, default=48, 
                        help="Total hours into the future to forecast")
    parser.add_argument("--step_hours", type=int, default=6,
                        help="Time step interval in hours for forecasting")
    parser.add_argument("--heading_var", type=float, default=15.0,
                        help="Heading variation in degrees for uncertainty cone width")
    parser.add_argument("--monte-carlo", action="store_true",
                        help="Use Monte Carlo simulation for uncertainty")
    parser.add_argument("--simulate", action="store_true",
                        help="Use simulated data if no real data available")
    parser.add_argument("--num-subs", type=int, default=6)
    parser.add_argument("--runs", type=int, default=100)   # tests use .runs
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    
    # ---------- data ingest ----------
    if getattr(args, "simulate", False):
        fleet_df = create_simulated_data(getattr(args, "num_subs", 6))
    else:
        try:
            load_data = importlib.import_module("src.ingestion").load_data
            fleet_df = load_data(args.input)
        except Exception as exc:
            log.error("Data load failed: %s", exc)
            return

    # ---------- analytics ----------
    if getattr(args, "monte_carlo", False):
        mc_sim = importlib.import_module(
            "src.models.prediction"
        ).monte_carlo_simulation
        forecasts = mc_sim(
            fleet_df,
            runs=getattr(args, "runs", 100)
        )
    else:
        forecast_all_subs = importlib.import_module("src.models").forecast_all_subs
        forecasts = forecast_all_subs(fleet_df)

    # ---------- visualization ----------
    create_map = importlib.import_module(
        "src.visualization.deckgl_mapper"
    ).create_map
    create_map(forecasts, getattr(args, "output", "map.html"))

def create_simulated_data(num_subs: int = 6) -> pd.DataFrame:
    """Return a DataFrame with a single 'departure' row per simulated sub."""
    rows = []
    for i in range(num_subs):
        rows.append(
            {
                "sub_id": f"Jin{i+1}",
                "sub_type": "Type094",
                "latitude": random.uniform(10.0, 20.0),
                "longitude": random.uniform(105.0, 115.0),
                "timestamp": datetime.utcnow(),
                "event_type": "departure",
            }
        )
    return pd.DataFrame(rows)

if __name__ == "__main__":
    main()