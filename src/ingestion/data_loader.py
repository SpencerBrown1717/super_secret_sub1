"""
Data ingestion module for Jin-class submarine tracker.
Provides functions to load submarine tracking data from CSV files or APIs.
Supports easy extension to new data sources.
"""
import pandas as pd
import requests

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

def load_csv_data(csv_path: str, target_subs: list = None) -> pd.DataFrame:
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
    
    # Parse timestamps if a timestamp column exists
    if 'timestamp' in df.columns:
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        except Exception as e:
            print(f"Warning: Failed to parse timestamps in {csv_path}: {e}")
    
    # Filter to target submarines if specified
    if target_subs is not None:
        df = df[df['sub_id'].isin(target_subs)]
    
    # Sort by timestamp for each submarine if timestamp exists
    if 'timestamp' in df.columns:
        df = df.sort_values(by=['sub_id', 'timestamp']).reset_index(drop=True)
    else:
        # If no timestamp, just sort by id to group data
        df = df.sort_values(by=['sub_id']).reset_index(drop=True)
    
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

def load_data(source: str, target_subs: list = None) -> pd.DataFrame:
    """
    Load data from a source which can be a CSV file path or API URL.
    Returns a filtered DataFrame containing only Jin-class submarines.
    
    Parameters:
        source (str): Path to CSV file or API URL
        target_subs (list, optional): List of submarine IDs to filter on.
                                      If None, defaults to JIN_CLASS_IDS.
    """
    # Use default Jin-class IDs if no specific targets provided
    if target_subs is None:
        target_subs = JIN_SUBMARINES
    
    # Check if source is a file path or URL
    if source.startswith('http'):
        df = fetch_api_data(source, target_subs=target_subs)
    else:
        df = load_csv_data(source, target_subs=target_subs)
    
    return df 