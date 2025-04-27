"""
Data ingestion module for Jin-class submarine tracker.
Provides functions to load submarine tracking data from CSV files or APIs.
Supports easy extension to new data sources.
"""
from datetime import datetime
import pandas as pd
import logging
import json
import requests
from pathlib import Path
from typing import Union, List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- constants ---------------------------------------------------------------
JIN_SUBMARINES = ["Jin1", "Jin2", "Jin3", "Jin4", "Jin5", "Jin6"]

# --- helper used by tests ----------------------------------------------------
def filter_jin_class_subs(df):
    """
    Keep only Jin-class rows.  Accept either `id` or `sub_id` column and/or
    a 'sub_type' marker containing '094'.
    """
    # Handle column name differences
    if "id" in df.columns and "sub_id" not in df.columns:
        df = df.rename(columns={"id": "sub_id"})
    elif "submarine_id" in df.columns and "sub_id" not in df.columns:
        df = df.rename(columns={"submarine_id": "sub_id"})
    
    # Filter by type if available
    if "sub_type" in df.columns:
        mask_type = df["sub_type"].str.contains("094", case=False, na=False)
    else:
        mask_type = True
        
    # Filter by submarine ID
    mask_id = df["sub_id"].isin(JIN_SUBMARINES)
    
    return df[mask_type & mask_id].reset_index(drop=True)

def load_csv_data(csv_path: str, target_subs: list = None, simulation_year: int = None) -> pd.DataFrame:
    """
    Load submarine position data from a CSV file.
    
    The CSV is expected to have columns such as:
    - 'sub_id': identifier of the submarine
    - 'timestamp': timestamp of the observation (ISO format or any parseable date)
    - 'latitude': latitude of the submarine position
    - 'longitude': longitude of the submarine position
    Additional columns are allowed and will be preserved.
    
    Parameters:
        csv_path (str): Path to the CSV file.
        target_subs (list, optional): List of submarine IDs to filter on.
                                      If provided, only data for those IDs will be returned.
                                      If None, all subs in the file are returned.
        simulation_year (int, optional): Year to use for timestamp generation if CSV has no timestamps.
                                      If None and no timestamps exist, current year is used.
                                      
    Returns:
        pd.DataFrame: DataFrame containing the submarine data (filtered if target_subs specified).
    """
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read CSV file {csv_path}: {e}")
    
    # Standardize column names if needed
    if 'submarine_id' in df.columns and 'sub_id' not in df.columns:
        df.rename(columns={'submarine_id': 'sub_id'}, inplace=True)
    if 'id' in df.columns and 'sub_id' not in df.columns:
        df.rename(columns={'id': 'sub_id'}, inplace=True)
    if 'lat' in df.columns and 'latitude' not in df.columns:
        df.rename(columns={'lat': 'latitude'}, inplace=True)
    if 'lon' in df.columns and 'longitude' not in df.columns:
        df.rename(columns={'lon': 'longitude'}, inplace=True)
    if 'time' in df.columns and 'timestamp' not in df.columns:
        df.rename(columns={'time': 'timestamp'}, inplace=True)
    
    # Handle missing timestamps
    if 'timestamp' not in df.columns:
        # Generate timestamps based on simulation year
        year = simulation_year if simulation_year is not None else datetime.now().year
        df['timestamp'] = pd.date_range(
            start=f'{year}-01-01',
            periods=len(df),
            freq='D'
        )
        df['is_simulated'] = True
    else:
        df['is_simulated'] = False
    
    # Parse timestamps if they exist
    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    except Exception as e:
        print(f"Warning: Failed to parse timestamps in {csv_path}: {e}")
    
    # Filter to target submarines if specified
    if target_subs is not None:
        df = df[df['sub_id'].isin(target_subs)]
    
    # Sort by timestamp for each submarine
    df = df.sort_values(by=['sub_id', 'timestamp']).reset_index(drop=True)
    
    return df

def fetch_api_data(api_url: str, params: dict = None, target_subs: list = None) -> pd.DataFrame:
    """
    Fetch submarine position data from an API endpoint.
    
    Assumes the API returns data in a JSON format that can be directly converted 
    into a tabular structure, similar to the CSV structure. For example, the API 
    might return a list of records with 'sub_id', 'latitude', 'longitude', and 'timestamp'.
    
    Parameters:
        api_url (str): URL of the API endpoint.
        params (dict, optional): Dictionary of query parameters to pass to the API call.
        target_subs (list, optional): List of submarine IDs to filter on.
        
    Returns:
        pd.DataFrame: DataFrame containing the submarine data (filtered if target_subs specified).
    """
    try:
        response = requests.get(api_url, params=params or {})
        if response.status_code != 200:
            raise RuntimeError(f"API request failed with status {response.status_code}")
        data = response.json()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch data from API {api_url}: {e}")
    
    # Convert JSON data to DataFrame
    try:
        df = pd.DataFrame(data)
    except Exception as e:
        raise RuntimeError(f"API data could not be loaded into DataFrame: {e}")
    
    # Parse timestamps and filter subs, similar to CSV
    if 'timestamp' in df.columns:
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        except Exception as e:
            print(f"Warning: Failed to parse timestamps from API data: {e}")
    
    if target_subs is not None:
        df = df[df['sub_id'].isin(target_subs)]
    
    if 'timestamp' in df.columns:
        df = df.sort_values(by=['sub_id', 'timestamp']).reset_index(drop=True)
    else:
        df = df.sort_values(by=['sub_id']).reset_index(drop=True)
    
    return df

def load_data(file_path: Path) -> pd.DataFrame:
    """Load submarine tracking data from CSV file."""
    try:
        df = pd.read_csv(file_path)
        required_columns = ['sub_id', 'timestamp', 'latitude', 'longitude']
        
        # Validate required columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
            
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Sort by submarine ID and timestamp
        df = df.sort_values(['sub_id', 'timestamp'])
        
        logger.info(f"Loaded {len(df)} records from {file_path}")
        return df
        
    except Exception as e:
        logger.error(f"Error loading data from {file_path}: {str(e)}")
        raise 