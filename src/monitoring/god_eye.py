import os
import csv
import requests
import pandas as pd
import base64
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import time
import random

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SENTINEL_CONFIG_ID = os.getenv('SENTINEL_CONFIG_ID')

# Validate API keys
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found. Make sure it's in your .env file as OPENAI_API_KEY=your-key")
if not SENTINEL_CONFIG_ID:
    raise ValueError("Sentinel config ID not found. Make sure it's in your .env file as SENTINEL_CONFIG_ID=your-id")

# Create monitoring directory if it doesn't exist
MONITORING_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monitoring")
os.makedirs(MONITORING_DIR, exist_ok=True)

# Function to load submarine base locations from CSV or create from provided data
def get_submarine_bases():
    """
    Load submarine base locations from CSV or create from provided data
    """
    csv_path = os.path.join(MONITORING_DIR, "submarine_bases.csv")
    
    # Check if CSV exists, otherwise create it
    if not os.path.exists(csv_path):
        print(f"Creating {csv_path} from provided data")
        bases_data = [
            {"id": 1, "base_name": "Yulin (Longpo) Naval Base (Hainan)", "latitude": 18.2253, "longitude": 109.5292},
            {"id": 2, "base_name": "Paracel Islands area (SCS)", "latitude": 16.5000, "longitude": 112.0000},
            {"id": 3, "base_name": "Jianggezhuang Submarine Base (Shandong)", "latitude": 36.1108, "longitude": 120.5758},
            {"id": 4, "base_name": "Xiaopingdao Submarine Base (Liaoning)", "latitude": 38.8179, "longitude": 121.4944},
            {"id": 5, "base_name": "Lüshunkou Naval Base (Liaoning)", "latitude": 38.8453, "longitude": 121.2781},
            {"id": 6, "base_name": "Huludao Bohai Shipyard (Liaoning)", "latitude": 40.7153, "longitude": 121.0103}
        ]
        
        df = pd.DataFrame(bases_data)
        df.to_csv(csv_path, index=False)
        print(f"Created {csv_path} with {len(df)} submarine base locations")
    else:
        print(f"Loading submarine base locations from {csv_path}")
    
    return pd.read_csv(csv_path)

# Function to initialize the submarine sightings log file if it doesn't exist
def initialize_sightings_log():
    """
    Initialize the submarine sightings log file if it doesn't exist
    """
    log_path = os.path.join(MONITORING_DIR, "submarine_sightings.csv")
    
    if not os.path.exists(log_path):
        print(f"Creating submarine sightings log file: {log_path}")
        with open(log_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['latitude', 'longitude', 'date'])
        print(f"Created submarine sightings log file")
    else:
        print(f"Submarine sightings log file already exists: {log_path}")
    
    return log_path

# Function to fetch Sentinel-2 imagery for a given location and date
def fetch_sentinel2_imagery(lat, lon, date):
    """
    Fetch Sentinel-2 imagery for a given location and date
    """
    print(f"Fetching Sentinel-2 imagery for location ({lat}, {lon}) on {date}")
    
    image_filename = f"sentinel2_{lat}_{lon}_{date.replace('-', '')}.jpg"
    image_path = os.path.join(MONITORING_DIR, image_filename)
    
    # Check if image already exists
    if os.path.exists(image_path):
        print(f"Image already exists: {image_path}")
        return image_path
    
    # List all jpg images in sample_images
    sample_images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_images")
    sample_images = [f for f in os.listdir(sample_images_dir) if f.endswith('.jpg')]
    
    if sample_images:
        try:
            import shutil
            chosen_image = random.choice(sample_images)
            sample_image_path = os.path.join(sample_images_dir, chosen_image)
            shutil.copy(sample_image_path, image_path)
            print(f"Successfully fetched imagery (simulated) using {chosen_image}")
            return image_path
        except Exception as e:
            print(f"Error copying sample image: {e}")
            return None
    else:
        print(f"No sample imagery available. In production, this would fetch from Sentinel-2 API")
        return None

# Function to analyze imagery using OpenAI's vision model
def analyze_image_with_openai(image_path):
    """
    Analyze the satellite image using OpenAI's Vision API to detect Jin-class submarines
    """
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return {
            "submarines_detected": False,
            "count": 0,
            "confidence": 0.0
        }
    
    try:
        # Read the image file as binary
        with open(image_path, "rb") as image_file:
            # Encode the image as base64
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Prepare the API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this satellite image of a naval base. Identify if there are any Jin-class nuclear submarines present. Jin-class submarines are Chinese Type 094 nuclear-powered ballistic missile submarines (SSBNs), approximately 135-140 meters long with a distinctive missile compartment behind the sail. Respond ONLY with a JSON object with these keys: 'submarines_detected' (boolean), 'count' (integer), and 'confidence' (float between 0 and 1)."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }
        
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response_data = response.json()
        
        if 'error' in response_data:
            print(f"OpenAI API Error: {response_data['error']}")
            return {
                "submarines_detected": False,
                "count": 0,
                "confidence": 0.0
            }
        
        # Extract the response content
        content = response_data['choices'][0]['message']['content']
        print(f"OpenAI response: {content}")
        
        # Try to parse the JSON from the response
        try:
            # Extract JSON from the text (in case it's embedded in explanatory text)
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                print("No JSON found in the response")
                result = {
                    "submarines_detected": False,
                    "count": 0,
                    "confidence": 0.0
                }
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from OpenAI response: {e}")
            result = {
                "submarines_detected": False,
                "count": 0,
                "confidence": 0.0
            }
        
        return result
    
    except Exception as e:
        print(f"Error analyzing image with OpenAI: {e}")
        return {
            "submarines_detected": False,
            "count": 0,
            "confidence": 0.0
        }

# Function to record submarine sightings to the log file
def record_submarine_sighting(log_path, lat, lon, date):
    """
    Record a submarine sighting to the log file (only lat, lon, date)
    """
    try:
        with open(log_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                lat,
                lon,
                date
            ])
        print(f"Recorded sighting: {lat}, {lon} on {date}")
    except Exception as e:
        print(f"Error recording sighting to CSV: {e}")

# Function to generate dates from 2020 to 2024 (can be adjusted as needed)
def generate_dates(start_year=2020, end_year=2024, interval_months=3):
    """
    Generate dates from start_year to end_year with given interval in months
    """
    dates = []
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    
    current_date = end_date
    while current_date >= start_date:
        dates.append(current_date.strftime("%Y-%m-%d"))
        current_date -= timedelta(days=30*interval_months)  # Approximate months
    
    return dates

# Main function
def main():
    try:
        # Get submarine base locations
        bases_df = get_submarine_bases()
        print(f"Loaded {len(bases_df)} submarine base locations")
        
        # Initialize submarine sightings log
        log_path = initialize_sightings_log()
        
        # Generate dates to monitor (from 2024 back to 2020)
        monitoring_dates = generate_dates(2020, 2024, interval_months=3)
        print(f"Generated {len(monitoring_dates)} dates to monitor")
        
        # For each base and date, fetch and analyze imagery
        for _, base in bases_df.iterrows():
            lat = base['latitude']
            lon = base['longitude']
            
            print(f"\nProcessing base: {lat}, {lon}")
            
            for date in monitoring_dates:
                print(f"Processing date: {date}")
                
                try:
                    # Fetch Sentinel-2 imagery
                    image_path = fetch_sentinel2_imagery(lat, lon, date)
                    
                    if image_path and os.path.exists(image_path):
                        # Analyze imagery with OpenAI
                        result = analyze_image_with_openai(image_path)
                        
                        # Check if submarines detected with confidence >= 50%
                        if result['submarines_detected'] and result['confidence'] >= 0.50:
                            # Record the sighting (only lat, lon, date)
                            record_submarine_sighting(
                                log_path,
                                lat,
                                lon,
                                date
                            )
                        else:
                            print(f"No Jin-class submarines detected at {lat}, {lon} on {date} or confidence too low")
                    else:
                        print(f"Failed to fetch imagery for {lat}, {lon} on {date}")
                    
                    # Add delay to avoid API rate limits
                    time.sleep(1)
                except Exception as e:
                    print(f"Error processing {lat}, {lon} on {date}: {e}")
                    continue
    
    except Exception as e:
        print(f"Fatal error in main function: {e}")
        raise

if __name__ == "__main__":
    main()