"""
Jin-class submarine tracker main entry point.
"""
from pathlib import Path
import pandas as pd
import argparse
import sys
import os

# Fix imports by making them absolute instead of relative
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.ingestion.data_loader import load_data
from src.models.submarine import load_submarines_from_csv
from src.models.fleet import FLEET
from src.visualization import leaflet_mapper

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Jin-class submarine tracker")
    parser.add_argument("--input", dest="input_path", help="Input CSV file path", required=True)
    parser.add_argument("--output", dest="output_path", help="Output HTML file path", required=True)
    parser.add_argument("--confidence-rings", type=int, default=3, help="Number of confidence rings to display")
    return parser.parse_args()

def run(input_path: Path, output_path: Path, confidence_rings: int = 3):
    """Main processing function that tests can call directly."""
    # Load data
    df = load_data(input_path)
    
    # Process data
    submarines = load_submarines_from_csv(input_path)
    FLEET.update_from_records(df.to_dict("records"))
    
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate the map
    leaflet_mapper.create_leaflet_map(df, output_path)
    print(f"Map created successfully at {output_path}")

def main(**kw):
    """CLI wrapper that delegates to run() so tests can call with kwargs."""
    args = kw or vars(parse_args())
    
    # Ensure input and output paths are provided
    if not args.get("input_path") or not args.get("output_path"):
        print("Error: Both input and output paths are required.")
        print("Use --input and --output arguments to specify paths.")
        sys.exit(1)
    
    run(
        Path(args["input_path"]), 
        Path(args["output_path"]),
        args.get("confidence_rings", 3)
    )

if __name__ == "__main__":
    main()