import pandas as pd
from ingestion import load_data
from models import update_sub_state, predict_path_with_uncertainty, generate_monte_carlo_uncertainty
from visualize import create_map
import argparse
import os
from datetime import datetime

def main(data_source, output_path, use_monte_carlo=False, simulate=False):
    """
    Main function to run the submarine tracking pipeline.
    
    Args:
        data_source: Path to CSV file or API URL
        output_path: Where to save the output map HTML
        use_monte_carlo: Whether to use Monte Carlo simulation for uncertainty
        simulate: Whether to use simulated data if no real data is available
    """
    # Check if data source exists (if it's a file)
    if not data_source.startswith('http') and not os.path.exists(data_source):
        if simulate:
            print(f"Data source {data_source} not found. Using simulated data.")
            df = create_simulated_data()
        else:
            raise FileNotFoundError(f"Data source {data_source} not found.")
    else:
        # Load and filter data
        print(f"Loading data from {data_source}...")
        df = load_data(data_source)
        print(f"Loaded {len(df)} records for Jin-class submarines.")
    
    # Get latest state for each submarine
    sub_states = {}
    for sub_id, records in df.groupby('sub_id'):
        sub_states[sub_id] = update_sub_state(records)
        if sub_states[sub_id]:
            status = "at sea" if sub_states[sub_id]["at_sea"] else "in port"
            print(f"Submarine {sub_id}: Last seen at {sub_states[sub_id]['last_time']}, {status}")
    
    # Generate forecasts for submarines at sea
    forecasts = {}
    for sub_id, state in sub_states.items():
        if state and state["at_sea"]:
            print(f"Generating forecast for {sub_id}...")
            
            if use_monte_carlo:
                # Use Monte Carlo simulation for uncertainty
                forecasts[sub_id] = generate_monte_carlo_uncertainty(
                    state["last_lat"], 
                    state["last_lon"], 
                    state["last_time"]
                )
            else:
                # Use simple prediction with expanding circles
                forecasts[sub_id] = predict_path_with_uncertainty(
                    state["last_lat"], 
                    state["last_lon"], 
                    state["last_time"]
                )
    
    # Create visualization
    print("Creating map visualization...")
    map_obj = create_map(sub_states, forecasts)
    
    # Save the map
    map_obj.save(output_path)
    print(f"Map saved to {output_path}")

def create_simulated_data():
    """Create simulated data for demonstration purposes."""
    import numpy as np
    
    # Create sample data for the six Jin-class submarines
    sub_ids = ["Jin1", "Jin2", "Jin3", "Jin4", "Jin5", "Jin6"]
    
    # Base locations (roughly around the South China Sea)
    base_lat, base_lon = 18.2, 109.5  # Approximately Yulin Naval Base, Hainan Island
    
    data = []
    
    # Current time
    now = pd.Timestamp.now()
    
    for sub_id in sub_ids:
        # Generate a series of records for each submarine
        num_records = np.random.randint(3, 10)
        
        for i in range(num_records):
            # Time: progressively earlier
            time_offset = pd.Timedelta(days=np.random.randint(1, 30), 
                                      hours=np.random.randint(0, 24))
            timestamp = now - time_offset
            
            # First record is departure from base, last is random position
            if i == 0:
                lat, lon = base_lat, base_lon
                event_type = "departure"
            else:
                # Random position in the South China Sea (rough bounds)
                lat = np.random.uniform(5, 25)
                lon = np.random.uniform(105, 120)
                event_type = "sighting"
            
            data.append({
                "sub_id": sub_id,
                "sub_type": "Type094",
                "latitude": lat,
                "longitude": lon,
                "timestamp": timestamp,
                "event_type": event_type
            })
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    df = df.sort_values("timestamp")
    
    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jin-class Submarine Tracking System")
    parser.add_argument("--data", default="data/input/submarine_tracking.csv", 
                        help="Path to CSV file or API URL")
    parser.add_argument("--output", default="jin_subs_forecast.html",
                        help="Output HTML map file path")
    parser.add_argument("--monte-carlo", action="store_true",
                        help="Use Monte Carlo simulation for uncertainty")
    parser.add_argument("--simulate", action="store_true",
                        help="Use simulated data if no real data available")
    
    args = parser.parse_args()
    
    main(args.data, args.output, args.monte_carlo, args.simulate)