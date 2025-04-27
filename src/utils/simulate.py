import pandas as pd, numpy as np

def generate_dummy_data():
    """Very small dummy DataFrame used only by unit-tests."""
    now = pd.Timestamp.utcnow()
    return pd.DataFrame(
        {
            "id": ["JIN-TEST"],
            "timestamp": [now],
            "latitude": [18.2],
            "longitude": [109.5],
        }
    ) 