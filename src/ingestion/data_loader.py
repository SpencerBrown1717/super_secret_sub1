import pandas as pd
import requests

# List of the six Jin-class submarine IDs
JIN_CLASS_IDS = ["Jin1", "Jin2", "Jin3", "Jin4", "Jin5", "Jin6"]

def load_csv_data(csv_path: str) -> pd.DataFrame:
    """Load submarine sighting data from a CSV file into a DataFrame."""
    df = pd.read_csv(csv_path)
    # Ensure proper datetime format
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def fetch_api_data(api_url: str) -> pd.DataFrame:
    """Fetch submarine data from an API and return as DataFrame."""
    response = requests.get(api_url)
    data = response.json()  # assuming the API returns JSON
    
    # Convert JSON (list of records) to DataFrame
    df = pd.DataFrame(data)
    
    # Ensure proper datetime format
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    return df

def filter_jin_class_subs(df: pd.DataFrame) -> pd.DataFrame:
    """Filter dataframe to only include Jin-class submarines."""
    # Filter by sub_type if that column exists
    if 'sub_type' in df.columns:
        jin_df = df[df['sub_type'] == 'Type094'].copy()
    # Or filter by sub_id if we have specific IDs
    elif 'sub_id' in df.columns:
        jin_df = df[df['sub_id'].isin(JIN_CLASS_IDS)].copy()
    else:
        raise ValueError("DataFrame must have 'sub_type' or 'sub_id' column")
    
    # Sort by timestamp
    jin_df = jin_df.sort_values('timestamp')
    
    return jin_df

def load_data(source: str) -> pd.DataFrame:
    """
    Load data from a source which can be a CSV file path or API URL.
    Returns a filtered DataFrame containing only Jin-class submarines.
    """
    # Check if source is a file path or URL
    if source.startswith('http'):
        df = fetch_api_data(source)
    else:
        df = load_csv_data(source)
    
    # Filter for Jin-class submarines
    jin_df = filter_jin_class_subs(df)
    
    return jin_df 