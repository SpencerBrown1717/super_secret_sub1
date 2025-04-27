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
from src.models.submarine import Submarine

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Filter out Pydantic AliasGenerator warning
warnings.filterwarnings(
    "ignore",
    message="cannot import name 'AliasGenerator' from 'pydantic'",
)

def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Jin-class submarine tracker")
    parser.add_argument("--input", type=str, default="data/input/submarine_tracking.csv")
    parser.add_argument("--output", type=str, default="data/output/jin_forecast_map.html")
    parser.add_argument("--simulate", action="store_true", help="Use simulated data instead of loading from file")
    parser.add_argument("--num-subs", type=int, default=6)
    parser.add_argument("--num-simulations", type=int, default=100)
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    log.info("Starting submarine tracker with args: %s", args)
    
    # ---------- data ingest ----------
    if getattr(args, "simulate", False):
        log.info("Using simulated data")
        fleet_df = create_simulated_data(getattr(args, "num_subs", 6))
    else:
        try:
            log.info("Loading data from %s", args.input)
            load_data = importlib.import_module("src.ingestion").load_data
            fleet_df = load_data(args.input)
            log.info("Loaded %d records", len(fleet_df))
        except Exception as exc:
            log.error("Data load failed: %s", exc)
            return

    # ---------- submarine state validation ----------
    # Build Submarine objects and validated histories
    subs = {}
    for record in fleet_df.to_dict("records"):
        sub_id = record.get("sub_id") or record.get("id") or "Unknown"
        if sub_id not in subs:
            subs[sub_id] = Submarine(sub_id)
        try:
            subs[sub_id].update_from_record(record)
        except Exception as e:
            log.error(f"Skipping invalid record for {sub_id}: {e}")
    
    log.info("Processed %d submarines", len(subs))
    
    # Prepare validated histories for prediction
    validated_histories = []
    for sub in subs.values():
        for rec in sub.history:
            # Ensure all required fields are present for prediction
            rec = rec.copy()
            rec["latitude"] = sub.last_lat if rec.get("latitude") is None else rec["latitude"]
            rec["longitude"] = sub.last_lon if rec.get("longitude") is None else rec["longitude"]
            rec["timestamp"] = sub.last_time if rec.get("timestamp") is None else rec["timestamp"]
            validated_histories.append(rec)
    
    log.info("Prepared %d validated records for prediction", len(validated_histories))

    # ---------- analytics ----------
    forecast_all_subs = importlib.import_module("src.models").forecast_all_subs
    try:
        forecasts = forecast_all_subs(validated_histories)
        log.info("Generated forecasts for %d submarines", len(forecasts))
    except Exception as e:
        log.error("Forecast generation failed: %s", e)
        return

    # ---------- build combined data for visualization ----------
    # Group histories by sub_id
    histories_by_sub = {}
    for rec in validated_histories:
        sub_id = rec.get("sub_id") or rec.get("id") or rec.get("name")
        if sub_id is None:
            continue
        histories_by_sub.setdefault(sub_id, []).append(rec)
    # Build combined dict
    viz_data = {}
    for sub_id, forecast in forecasts.items():
        # Get historical path for this sub
        history = histories_by_sub.get(sub_id, [])
        history_path = [[r["longitude"], r["latitude"]] for r in history]
        # Forecast path: skip the first point (last historical)
        forecast_path = forecast["central_path"][1:] if len(forecast["central_path"]) > 1 else []
        viz_data[sub_id] = {
            **forecast,
            "history_path": history_path,
            "forecast_path": forecast_path,
        }

    # ---------- visualization ----------
    try:
        log.info("Creating visualization at %s", args.output)
        visualize = importlib.import_module("src.visualization").visualize
        visualize(viz_data, args.output)
        log.info("Visualization completed successfully")
    except Exception as e:
        log.error("Visualization failed: %s", e)
        return

    log.info("Processing completed successfully")

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